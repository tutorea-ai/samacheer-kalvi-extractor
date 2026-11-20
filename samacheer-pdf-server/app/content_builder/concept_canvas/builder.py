"""Concept Canvas: storyboard builder.

LP days -> one JSON storyboard per day (contract v1, see schema.py).
Writer (Claude, tool use) -> code checks (schema.validate_day) -> reviewer
(a second Claude as a strict teacher) -> retries with feedback -> fail closed:
a day that cannot be confirmed goes to skipped_days, never into the deck.

API plumbing (client, backoff, tolerant parsing) follows Homework's builder.
"""
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import anthropic
import httpx

from ...config import settings
from .lp_parser import load_lp
from .schema import (
    CONTRACT_VERSION, DAY_LIMITS, MODULE, STEP_LIMITS, TEMPLATE_DAY_FIELDS,
    TEMPLATE_STEP_FIELDS, allowed_icons, validate_day,
)
from .subjects import get_profile
from .subjects.base import SubjectProfile

MAX_RETRIES = 2          # re-asks for days that fail checks or review
REVIEW_FAILED = "not checked (review call failed)"
# A day list that arrives as a JSON *string* may hold LaTeX with single backslashes
# (\frac, \begin): \f and \b are JSON escapes, \m is invalid. Double every lone
# backslash (keep \\ pairs and \") before decoding.
# A LaTeX command (\frac, \begin) behind an odd number of backslashes means the string
# holds raw LaTeX, not JSON escapes: then every backslash is literal (\\ = matrix row break).
_RAW_LATEX = re.compile(r'(?<!\\)(?:\\\\)*\\[A-Za-z]{2,}')


def _loads_latex_safe(s: str):
    if _RAW_LATEX.search(s):
        try:
            return json.loads(re.sub(r'\\(?!")', r'\\\\', s))
        except ValueError:
            pass
    try:
        return json.loads(s)
    except ValueError:
        return None


NOT_ERROR_RE = re.compile(r"(\bno (confirmed )?(factual )?error( here)?|\bnot (an|a confirmed) error"
                          r"|\bwithdraw(n|ing)|\bthis is correct)\W*$", re.I)
API_ATTEMPTS = 3
API_BACKOFF = 30

TEMPLATE_GUIDE = {
    "step_build": "step_build: the idea builds up piece by piece (a definition, a quantity, a formula's parts)",
    "process_flow": "process_flow: A then B then C, each causing the next (a mechanism, a procedure)",
    "cycle": "cycle: stages that return to the start (a repeating loop)",
    "compare": "compare: two cases side by side, point against point (needs left_title, right_title, and side on every step)",
    "timeline": "timeline: events in time order (needs time on every step)",
    "concept_map": "concept_map: one central idea with related branches (needs center)",
    "punnett": ("punnett: a genetic cross drawn as a Punnett square (needs parent_1, parent_2, gametes_1 "
                "(columns), gametes_2 (rows), grid, phenotypes, ratio, and exactly 4 steps with phase "
                "parents, gametes, grid, ratio in that order; the ratio step is the highlight). "
                "parent_1 and parent_2 are the two plants crossed IN THIS GRID, genotype only "
                "(for an F₂ ratio both are the F₁ hybrids); put their names in parent_1_label / "
                "parent_2_label (for example \"Tall F₁\")"),
}

SYSTEM_TEMPLATE = """You design Concept Canvas storyboards for {audience}.
A storyboard turns one Lesson Plan day into an animated visual: 3 to 6 short steps revealed one at a time, like a teacher building a picture on the board. Our renderer draws it from your data; you never write HTML or SVG.

For each day:
- Find the day's ONE central concept and show how it builds up, step by step. A student should understand the idea from the visual alone.
- Leaving out the day's other topics, side points, special cases and secondary formulas is intended: the visual shows one idea well, not the whole day.
- Pick the template that fits the idea's shape:
{templates}
- Keep it short; the visual is read at a glance on a phone:
  title: the concept's name, at most 5 words.
  caption: the one-line takeaway, at most 14 words.
  label: at most 3 words (a name or quantity).
  text: at most 10 words, a short phrase, not a full sentence; one fact per step.
- Fewer, sharper steps beat many: show only what builds the central idea (usually 3 or 4 steps).
- Mark at most one step "highlight": true, the key takeaway. In step_build and process_flow it is the last step: nothing comes after it.
- icon is optional: only when it shows the actual thing in the step (a battery, a meter, an electron); never as decoration (check, idea, star, question). Never the same icon on two steps in a row.
{formula_rule}
- Use only what the day's lesson text teaches; never add facts, numbers or examples it does not contain.
- English only. Plain text in title, caption, label and text: no LaTeX, no $ signs, no markdown, and no equations: every equation goes in formula, text is words only (never an = sign).
- If a day honestly has no concept that can be shown visually, skip it: "skip": true with a short "skip_reason".
Subject rules:{extra_rules}"""

FORMULA_ON = ("- formula is optional, for a step whose key idea is an equation: bare LaTeX as KaTeX renders it "
              "(for example I = \\frac{q}{t}, R = \\rho \\frac{l}{A}, v_d), no $ signs. "
              "Copy the lesson's formula exactly; never invent one. A formula is always a relation "
              "(=, \\propto, <, >), never a symbol alone or words.")
FORMULA_OFF = "- Never use the formula field."

SHORTEN_SYSTEM = ("You fix short texts for a school visual. Keep the meaning, the facts and every "
                  "symbol exactly; drop filler words. Never add anything. English, plain text, no LaTeX, "
                  "no equations: name a relation in words instead (for example \"Ohm's law\", not \"V = IR\").")
SHORTEN_ROUNDS = 2       # cheap shorten calls before a length-only day falls back to a full retry

REVIEW_TEMPLATE = """You are a strict {subject} teacher checking Concept Canvas storyboards for {audience}.
A storyboard shows ONE central idea of a Lesson Plan day in 3 to 6 short visual steps. Leaving out the day's other topics, side points, special cases and secondary formulas is intended: never flag an omission, unless the central idea itself is missing or wrong.
Compare each day with its lesson text and flag only confirmed errors:
- a statement that is wrong, or not supported by the lesson text
- a formula that differs from the lesson's (symbols, subscripts, powers, units)
- an illogical order (a step uses something not yet shown); an order that merely differs from the lesson's is fine
- a step that explains nothing
- a template that does not fit the idea shown (for example a cycle for something that is not a loop)
- a caption that is wrong, or about a different idea than the steps show
- compare: points on the two sides that do not correspond
Do not flag icons, wording, length, style, omissions, or a choice that is merely different from yours.
List only real errors in the storyboard. Never flag errors in the lesson text itself. Never include a note that concludes "no error" or that you withdraw: if a check passes, leave it out. Every problem carries "confirmed": true only for a real error you stand by; if on reflection it is not an error, set "confirmed": false.
Subject rules the writer followed (never flag what they allow):{extra_rules}{review_rules}
Return one review per day; an empty problems list when the day is correct."""


class ConceptCanvasBuilder:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self.usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
        print(f"✅ Concept Canvas Builder initialized — model: {self.model}")

    # ── Prompts and tools ────────────────────────────────────
    def _system(self, p: SubjectProfile) -> str:
        return SYSTEM_TEMPLATE.format(
            audience=p.audience or "school students",
            templates="\n".join(f"  {TEMPLATE_GUIDE[t]}" for t in p.allowed_templates),
            formula_rule=FORMULA_ON if p.formulas else FORMULA_OFF,
            extra_rules=p.extra_rules or " none",
        )

    def _writer_tool(self, p: SubjectProfile) -> dict:
        step = {
            "label": {"type": "string"},
            "text": {"type": "string"},
            "icon": {"type": "string", "enum": list(allowed_icons(p))},
            "highlight": {"type": "boolean"},
            "side": {"type": "string", "enum": ["left", "right"]},
            "time": {"type": "string"},
        }
        if p.formulas:
            step["formula"] = {"type": "string"}
        if "punnett" in p.allowed_templates:
            step["phase"] = {"type": "string", "enum": ["parents", "gametes", "grid", "ratio"]}
        day = {
            "day": {"type": "integer"},
            "skip": {"type": "boolean"},
            "skip_reason": {"type": "string"},
            "title": {"type": "string"},
            "template": {"type": "string", "enum": list(p.allowed_templates)},
            "caption": {"type": "string"},
            "left_title": {"type": "string"},
            "right_title": {"type": "string"},
            "center": {"type": "string"},
            "steps": {"type": "array", "items": {
                "type": "object", "properties": step, "required": ["label", "text"]}},
        }
        if "punnett" in p.allowed_templates:
            gametes = {"type": "array", "items": {"type": "string"}}
            day.update({
                "parent_1": {"type": "string"},
                "parent_1_label": {"type": "string"},
                "parent_2": {"type": "string"},
                "parent_2_label": {"type": "string"},
                "gametes_1": gametes,
                "gametes_2": gametes,
                "grid": {"type": "array", "items": gametes},
                "phenotypes": {"type": "object", "additionalProperties": {"type": "string"}},
                "ratio": {"type": "string"},
            })
        return {
            "name": "save_storyboards",
            "description": "Save one storyboard (or a skip) per lesson day.",
            "input_schema": {"type": "object", "required": ["days"], "properties": {
                "days": {"type": "array", "items": {
                    "type": "object", "properties": day, "required": ["day"]}}}},
        }

    @staticmethod
    def _review_tool() -> dict:
        return {
            "name": "save_reviews",
            "description": "Save one review per day.",
            "input_schema": {"type": "object", "required": ["reviews"], "properties": {
                "reviews": {"type": "array", "items": {
                    "type": "object", "required": ["day", "problems"], "properties": {
                        "day": {"type": "integer"},
                        "problems": {"type": "array", "items": {
                            "type": "object", "required": ["problem", "confirmed"], "properties": {
                                "field": {"type": "string"},
                                "problem": {"type": "string"},
                                "confirmed": {"type": "boolean"}}}}}}}}},
        }

    @staticmethod
    def _days_prompt(batch: List[Dict], feedback: Dict[int, List[str]],
                     notes: Dict[int, str]) -> str:
        parts = [f"Design storyboards for these {len(batch)} days. Return one entry per day."]
        for d in batch:
            note = notes.get(d["day"])
            ask = f"\nInstruction for this day (follow it): {note}" if note else ""
            fb = feedback.get(d["day"])
            fix = ("\nYour previous storyboard for this day had these problems; fix them:\n- "
                   + "\n- ".join(fb)) if fb else ""
            parts.append(f"\n=== DAY {d['day']}: {d['title']} ===\nDay type: {d['day_type'] or '-'}"
                         f"{ask}{fix}\nLesson text:\n{d['text']}")
        return "\n".join(parts)

    # ── Parsing ──────────────────────────────────────────────
    @staticmethod
    def _list_from(data, key: str) -> list:
        raw = (data or {}).get(key, [])
        if isinstance(raw, str):
            raw = _loads_latex_safe(raw)
        return raw if isinstance(raw, list) else []

    def _days_from(self, data) -> Dict[int, dict]:
        out: Dict[int, dict] = {}
        for h in self._list_from(data, "days"):
            if not isinstance(h, dict):
                continue
            try:
                n = int(h.get("day"))
            except (TypeError, ValueError):
                continue
            h["day"] = n
            out[n] = h
        return out

    @staticmethod
    def _contract_only(h: dict) -> dict:
        """Keep only the contract's fields, in contract order."""
        tpl = h["template"]
        keys = ("day", "title", "template", "caption") + TEMPLATE_DAY_FIELDS[tpl]
        out = {k: h[k] for k in keys if k in h}
        step_keys = ("label", "text", "icon", "formula", "highlight") + TEMPLATE_STEP_FIELDS.get(tpl, ())
        out["steps"] = [{k: s[k] for k in step_keys if k in s} for s in h["steps"]]
        return out

    # ── Shorten (length-only problems) ───────────────────────
    @staticmethod
    def _length_only(probs: List[str]) -> bool:
        """Problems a text-only fix can solve: length (not formulas) and equations in text."""
        return bool(probs) and all(("too long (" in x and "formula" not in x)
                                   or "contains an equation" in x for x in probs)

    def _shorten(self, boards: Dict[int, dict]) -> None:
        """One small call: shorten every over-long string in place. No lesson text sent."""
        items, where = [], {}
        for n, h in boards.items():
            for f, lim in DAY_LIMITS.items():
                v = h.get(f)
                if isinstance(v, str) and (len(v) > lim or "=" in v):
                    key = f"d{n}.{f}"
                    items.append({"id": key, "limit": lim, "text": v})
                    where[key] = (h, f)
            for i, s in enumerate(h.get("steps") or []):
                if not isinstance(s, dict):
                    continue
                for f, lim in STEP_LIMITS.items():
                    v = s.get(f)
                    if isinstance(v, str) and (len(v) > lim or "=" in v):
                        key = f"d{n}.s{i}.{f}"
                        items.append({"id": key, "limit": lim, "text": v})
                        where[key] = (s, f)
        if not items:
            return
        prompt = ("Rewrite each text to at most its limit in characters (aim about 10% under), "
                  "words only with no = sign. Return every id.\n"
                  + "\n".join(json.dumps(x, ensure_ascii=False) for x in items))
        tool = {"name": "save_shortened", "description": "Save the shortened texts.",
                "input_schema": {"type": "object", "required": ["items"], "properties": {
                    "items": {"type": "array", "items": {"type": "object", "required": ["id", "text"],
                              "properties": {"id": {"type": "string"}, "text": {"type": "string"}}}}}}}
        data = self._call_tool(SHORTEN_SYSTEM, prompt, tool, 2000)
        for r in self._list_from(data, "items"):
            if isinstance(r, dict) and r.get("id") in where and isinstance(r.get("text"), str) and r["text"].strip():
                obj, f = where[r["id"]]
                obj[f] = r["text"].strip()

    # ── Review ───────────────────────────────────────────────
    def _review(self, days: List[Dict], boards: Dict[int, dict],
                p: SubjectProfile) -> Dict[int, List[str]]:
        if not days:
            return {}
        system = REVIEW_TEMPLATE.format(
            subject=p.display_name or p.key, audience=p.audience or "school students",
            extra_rules=p.extra_rules or " none", review_rules=p.review_rules)
        parts = [f"Check the storyboards for these {len(days)} days. Return one review per day."]
        for d in days:
            parts.append(f"\n=== DAY {d['day']}: {d['title']} ===\nStoryboard:\n"
                         + json.dumps(self._contract_only(boards[d["day"]]), ensure_ascii=False, indent=1)
                         + "\nLesson text:\n" + d["text"])
        data = self._call_tool(system, "\n".join(parts), self._review_tool(), 4000)
        if data is None:
            print("      ⚠️  Review call failed — storyboards sent back, not accepted unchecked")
            return {d["day"]: [REVIEW_FAILED] for d in days}
        out: Dict[int, List[str]] = {}
        seen = set()
        for r in self._list_from(data, "reviews"):
            if not isinstance(r, dict):
                continue
            try:
                n = int(r.get("day"))
            except (TypeError, ValueError):
                continue
            seen.add(n)
            probs = [f"[{x.get('field', '?')}] {x['problem']}" for x in (r.get("problems") or [])
                     if isinstance(x, dict) and x.get("problem")
                     and x.get("confirmed") is not False
                     and not NOT_ERROR_RE.search(x["problem"])]
            if probs:
                out[n] = probs
        for d in days:
            if d["day"] not in seen:
                out[d["day"]] = [REVIEW_FAILED]
        return out

    # ── Generation ───────────────────────────────────────────
    def _generate_days(self, days: List[Dict], p: SubjectProfile,
                       notes: Optional[Dict[int, str]] = None) -> Tuple[Dict[int, dict], List[Dict]]:
        notes = notes or {}
        system, tool = self._system(p), self._writer_tool(p)
        pending = {d["day"]: d for d in days}
        done: Dict[int, dict] = {}
        skipped: List[Dict] = []
        last: Dict[int, List[str]] = {}
        drafts: Dict[int, dict] = {}
        feedback: Dict[int, List[str]] = {}

        for attempt in range(MAX_RETRIES + 1):
            todo = [pending[k] for k in sorted(pending)]
            if not todo:
                break
            if attempt:
                print(f"   🔁 Retry {attempt}: days {[d['day'] for d in todo]}")
            for i in range(0, len(todo), p.batch_size):
                batch = todo[i:i + p.batch_size]
                data = self._call_tool(system, self._days_prompt(batch, feedback, notes), tool, 8000)
                got = self._days_from(data)
                if not got:
                    raw_path = f"/tmp/cc_raw_{int(time.time())}.json"
                    with open(raw_path, "w", encoding="utf-8") as fh:
                        fh.write(json.dumps(data, ensure_ascii=False, default=str))
                    print(f"      ⚠️  Writer returned no usable days for {[d['day'] for d in batch]}"
                          f" — raw reply saved to {raw_path}")

                checked: Dict[int, Tuple[dict, List[str], List[str]]] = {}
                for d in batch:
                    n = d["day"]
                    h = got.get(n)
                    if h is None:
                        last[n] = feedback[n] = ["the storyboard was missing — write it"]
                        continue
                    if h.get("skip"):
                        reason = h.get("skip_reason") or "no visual concept"
                        print(f"      day {n} — skipped by writer: {reason}")
                        skipped.append({"day": n, "reasons": [f"writer: {reason}"]})
                        pending.pop(n, None)
                        continue
                    probs, warns = validate_day(h, p)
                    checked[n] = (h, probs, warns)

                # Length-only days: cheap shorten calls (no lesson text), then check again.
                for _ in range(SHORTEN_ROUNDS):
                    short = {n: v[0] for n, v in checked.items() if self._length_only(v[1])}
                    if not short:
                        break
                    print(f"      ✂️  Shortening days {sorted(short)}")
                    self._shorten(short)
                    for n, h in short.items():
                        probs, warns = validate_day(h, p)
                        checked[n] = (h, probs, checked[n][2] + warns)

                clean =[d for d in batch if d["day"] in checked and not checked[d["day"]][1]]
                verdicts = self._review(clean, {n: v[0] for n, v in checked.items()}, p)
                for n, rprobs in verdicts.items():
                    checked[n][1].extend(f"review: {x}" for x in rprobs)

                for n, (h, probs, warns) in checked.items():
                    if probs:
                        last[n] = probs
                        drafts[n] = h
                        fb = [x for x in probs if REVIEW_FAILED not in x]
                        if fb:
                            feedback[n] = fb
                        else:
                            feedback.pop(n, None)
                        print(f"      day {n} — {'; '.join(probs)}")
                    else:
                        board = self._contract_only(h)
                        if warns:
                            print(f"      day {n} — fixed: {'; '.join(warns)}")
                        done[n] = board
                        pending.pop(n, None)
                        feedback.pop(n, None)

        for n in sorted(pending):
            entry = {"day": n, "reasons": last.get(n, ["no storyboard returned"])}
            if n in drafts:
                entry["draft"] = drafts[n]       # last failed attempt, for diagnosis only
            skipped.append(entry)
        return done, skipped

    def generate(self, lp_path: str, lesson: Dict, only_days: Optional[List[int]] = None,
                 notes: Optional[Dict[int, str]] = None) -> Dict:
        """lesson = {"class": 12, "subject": "physics", "slug": "...", "title": "..."}"""
        p = get_profile(lesson["subject"])
        lp = load_lp(lp_path, lesson["subject"])
        days = [d for d in lp["days"] if not only_days or d["day"] in only_days]
        self.usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
        print(f"[Concept Canvas] {lesson['title']} — {len(days)} days (profile: {p.key})")

        skipped: List[Dict] = []
        todo = []
        for d in days:
            if d["truncated"]:
                print(f"      ⚠️  day {d['day']} text CUT at the profile limit")
            if d["is_review"] and p.skip_review_days:
                skipped.append({"day": d["day"], "reasons": ["review day (skip_review_days)"]})
            else:
                todo.append(d)

        done, more = self._generate_days(todo, p, notes)
        skipped = sorted(skipped + more, key=lambda s: s["day"])
        print(f"   ✅ {len(done)} storyboards, {len(skipped)} skipped — "
              f"{self.usage['calls']} calls, {self.usage['input_tokens']} in / "
              f"{self.usage['output_tokens']} out tokens")
        return {
            "module": MODULE,
            "version": 2 if any(done[n]["template"] == "punnett" for n in done) else CONTRACT_VERSION,
            "subject": p.key,
            "class": lesson["class"],
            "lesson": lesson["slug"],
            "lesson_title": lesson["title"],
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "days": [done[n] for n in sorted(done)],
            "skipped_days": skipped,
            "model": self.model,
            "usage": dict(self.usage),
            **({"notes": {str(k): v for k, v in notes.items()}} if notes else {}),
        }

    # ── API ──────────────────────────────────────────────────
    def _call_tool(self, system: str, prompt: str, tool: dict, max_tokens: int) -> Optional[dict]:
        for attempt in range(1, API_ATTEMPTS + 1):
            try:
                resp = self.client.messages.create(
                    model=self.model, max_tokens=max_tokens, system=system,
                    tools=[tool], tool_choice={"type": "tool", "name": tool["name"]},
                    messages=[{"role": "user", "content": prompt}],
                )
                self.usage["calls"] += 1
                self.usage["input_tokens"] += resp.usage.input_tokens
                self.usage["output_tokens"] += resp.usage.output_tokens
                if resp.stop_reason == "max_tokens":
                    print("         ⚠️  Output cut off at max_tokens — response may be incomplete")
                for block in resp.content:
                    if block.type == "tool_use":
                        return block.input
                return None
            except (httpx.HTTPError, anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
                print(f"         ⚠️  Network error (attempt {attempt}): {e}")
            except anthropic.APIStatusError as e:
                if e.status_code not in (429, 500, 502, 503, 529):
                    raise
                print(f"         ⚠️  API {e.status_code} (attempt {attempt})")
            if attempt < API_ATTEMPTS:
                time.sleep(API_BACKOFF)
        return None


concept_canvas_builder = ConceptCanvasBuilder()