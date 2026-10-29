"""
Beyond the Book: card builder.

LP days -> one "why this matters" card per teaching day, plus one
Big Why opener for the whole lesson, via Claude tool calls.
Knows nothing about subjects: audience, hints, connections and limits
all come from the SubjectProfile.
"""
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional

import anthropic
import httpx

from ...config import settings
from .lp_parser import load_lp, TAMIL_RE
from .subjects import get_profile
from .subjects.base import SubjectProfile

MAX_RETRIES = 2          # re-asks for days whose cards fail the checks
REVIEW_FAILED = "not fact-checked (review call failed)"
HARD_FACTOR = 1.25       # up to 25% over a limit = warning only; beyond = retry
BUILDING_HINT = ("replace where_you_see_it with something students have actually seen or "
                 "used (the review above may suggest one); use connection '{key}' with "
                 "where_you_see_it empty only if nothing honest exists")
API_ATTEMPTS = 3         # attempts per API call on overload / network errors
API_BACKOFF = 30         # seconds between those attempts

TEXT_FIELDS = ("hook", "link", "where_you_see_it", "beyond_school", "try_this")
LONG_FIELDS = ("link", "where_you_see_it", "beyond_school")

# Filler that makes a card sound like every textbook. Subject-neutral.
GENERIC_PHRASES = (
    "in daily life", "in our daily life", "many industries", "various fields",
    "very important", "plays a vital role", "plays an important role",
    "in many ways", "modern world", "wide range of applications",
)

# Counting ideas ("16 formulas", "five rules") instead of explaining them.
COUNT_RE = re.compile(
    r"\b(\d+|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|"
    r"fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)\s+(\w+\s+)?"
    r"(formulas?|formulae|rules?|laws?|ideas?|relationships?|concepts?|equations?|"
    r"topics?|lessons?|principles?)\b", re.I)

SYSTEM_TEMPLATE = """You write "Beyond the Book" cards for {audience}.
A card shows a student WHY one day's lesson matters in their own life.
Write like a teacher who grew up in {local_context}: your examples are things
these students see, use or hear about at home, on the road, in their town or
in the news.

Rules:
- Subject facts must come from the lesson text you are given. Never add a
  formula, value, law or definition the lesson does not state. Use at most
  one formula per card, and say what it means in words.
- Every real-world claim must be true and widely known. Say a device or
  place uses this idea only if a teacher of this subject would agree without
  looking it up. If you are not sure, choose a different example.
- The hook's premise must be true. Never ask why something happens if it
  does not actually happen.
- Never invent statistics, numbers, dates, prices, records ("the first",
  "the largest") or claims about named companies or brands.
- Be specific, not generic: "the bus you take to school", never "transport
  systems" or "used in many industries".
- where_you_see_it must be something a student in {local_context} has
  personally seen or used: at home, at school, on the street, in a shop.
  Factories, power plants and labs they have only heard of belong in
  beyond_school. The lab apparatus used to teach this lesson never counts:
  that is the book, not beyond it.
- If a day's idea has no honest everyday link, do not force one. Use the
  connection "{building}", leave where_you_see_it as "", and let
  beyond_school say what this idea makes possible and who depends on it.
  An honest "{building}" card is better than a forced everyday example.
- try_this must show THIS day's idea, safely: never touching anything hot or
  switched on, never wall sockets, mains electricity, fire, chemicals, sharp
  tools or heights. When unsure, write "".
- tamil_line carries the card's hook or its why, not a definition.
- Ignore classroom instructions in the lesson text (pair work, timings,
  questions the teacher asks the class).
- Plain English a 16-year-old reads in 20 seconds. No hype, no exclamation
  marks.{extra_rules}"""

REVIEW_TEMPLATE = """You are a strict {subject} teacher in {local_context}, checking
"Beyond the Book" cards before students see them. Flag only real problems:
- a {subject} statement that is wrong, or that contradicts the lesson text
- a real-world claim that is false, doubtful or not widely known
  (a device that does not actually use this idea, an invented use, or
  workers said to use a method or instrument they do not actually use)
- a hook whose premise is false
- an invented number, statistic, date, record or brand claim
- a try_this that is unsafe, or that does not show this day's idea
- a tamil_line whose meaning is wrong or differs from the card
- a where_you_see_it the student would not have personally seen or used
- a where_you_see_it that is only the lab apparatus used to teach this lesson
Do not flag style, length or wording (Tamil fluency is checked by teachers). For each problem, say in one sentence
what is wrong and what is true.
Do your thinking in notes. List in problems only errors you are sure of;
if you conclude a field is fine, do not list it.
An empty where_you_see_it is correct on a "{building}" card."""

REVIEW_TOOL = {
    "name": "review_cards",
    "description": "Return one review per card.",
    "input_schema": {
        "type": "object",
        "properties": {"reviews": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "day": {"type": "integer"},
                "notes": {"type": "string", "description":
                          "Your working, 2–4 short sentences: check each field against the "
                          "lesson and the real world. Think here, never in problems."},
                "problems": {"type": "array", "description":
                             "Only confirmed errors. Empty when the card is correct.",
                             "items": {"type": "object", "properties": {
                                 "field": {"type": "string",
                                           "enum": list(TEXT_FIELDS) + ["tamil_line"]},
                                 "problem": {"type": "string", "description":
                                             "One sentence: what is wrong and what is true."},
                             }, "required": ["field", "problem"]}},
            },
            "required": ["day", "notes", "problems"],
        }}},
        "required": ["reviews"],
    },
}


def _words(s: str) -> int:
    return len((s or "").split())


class BeyondBuilder:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Beyond the Book Builder initialized — model: {self.model}")

    # ── Prompt pieces ────────────────────────────────────────
    def _system(self, p: SubjectProfile) -> str:
        audience = p.audience or f"{p.display_name or p.key} students"
        return SYSTEM_TEMPLATE.format(audience=audience,
                                      local_context=p.local_context,
                                      building=p.building_key,
                                      extra_rules=p.extra_rules)

    def _card_tool(self, p: SubjectProfile) -> dict:
        props = {
            "day": {"type": "integer"},
            "hook": {"type": "string", "description":
                     f"A question the student has wondered about or would want answered. "
                     f"Max {p.limit('MAX_HOOK_WORDS')} words, ends with '?'."},
            "link": {"type": "string", "description":
                     f"How this day's idea answers the hook. Max {p.limit('MAX_FIELD_WORDS')} words."},
            "where_you_see_it": {"type": "string", "description":
                     f"One specific thing the student has personally seen or used in "
                     f"{p.local_context} (home, school, street, shop) where this idea is at work. "
                     f"Use \"\" only when connection is \"{p.building_key}\". "
                     f"Max {p.limit('MAX_FIELD_WORDS')} words."},
            "beyond_school": {"type": "string", "description":
                     f"A job, technology or bigger use that depends on this idea. "
                     f"Max {p.limit('MAX_FIELD_WORDS')} words."},
            "try_this": {"type": "string", "description":
                     f"A safe 30-second observation at home that shows THIS day's idea, "
                     f"max {p.limit('MAX_TRY_WORDS')} words, or \"\" if none is honest and safe. "
                     f"Never touching anything hot or switched on; never wall sockets, mains "
                     f"electricity, fire, chemicals, sharp tools or heights."},
            "connection": {"type": "string", "enum": [k for k, _ in p.connections]},
        }
        if not p.try_this:
            props.pop("try_this")
        if p.tamil_line:
            props["tamil_line"] = {"type": "string", "description":
                     f"The card's hook or its why (not a definition), written as "
                     f"{p.tamil_style}. Max {p.limit('MAX_TAMIL_CHARS')} characters."}
        return {
            "name": "write_cards",
            "description": "Return one Beyond the Book card per lesson day.",
            "input_schema": {
                "type": "object",
                "properties": {"cards": {"type": "array", "items": {
                    "type": "object", "properties": props, "required": list(props)}}},
                "required": ["cards"],
            },
        }

    def _big_why_tool(self, p: SubjectProfile) -> dict:
        props = {
            "question": {"type": "string", "description":
                     f"The one question this whole lesson answers for the student's life. "
                     f"Max {p.limit('MAX_HOOK_WORDS')} words, ends with '?'."},
            "story": {"type": "string", "description":
                     f"Why this whole lesson matters, tying together the strongest card ideas. "
                     f"Max {p.limit('MAX_BIGWHY_WORDS')} words."},
        }
        if p.tamil_line:
            props["tamil_line"] = {"type": "string", "description":
                     f"The lesson's big idea, written as {p.tamil_style}. "
                     f"Max {p.limit('MAX_TAMIL_CHARS')} characters."}
        return {"name": "write_big_why", "description": "The lesson's opening card.",
                "input_schema": {"type": "object", "properties": props, "required": list(props)}}

    def _cards_prompt(self, batch: List[Dict], feedback: Dict[int, List[str]],
                      used: Optional[List[str]] = None) -> str:
        parts = [f"Write one card for each of these {len(batch)} lesson days. "
                 f"Use each day's number as the card's day."]
        if used:
            parts.append("Other days of this lesson already have these cards. Do not repeat "
                         "their idea, hook or example; find what is new in each day below:\n"
                         + "\n".join(f"- {u}" for u in used))
        for d in batch:
            block = [f"\n=== DAY {d['day']}: {d['title']} ===",
                     f"Day type: {d['day_type'] or '-'}"]
            if d["hint"]:
                block.append(f"Connection hint: {d['hint']}")
            if d["day"] in feedback:
                block.append("Your previous card for this day had problems — fix them: "
                             + "; ".join(feedback[d["day"]]))
            block.append("Lesson text:\n" + d["text"])
            parts.append("\n".join(block))
        return "\n".join(parts)

    # ── Checks ───────────────────────────────────────────────
    def _check(self, c: dict, p: SubjectProfile) -> List[str]:
        """Returns hard problems. Small length overflows go to c['warnings'] instead."""
        probs: List[str] = []
        warns: List[str] = []

        def length(field: str, n: int, limit: int, unit: str = "words"):
            if n > limit * HARD_FACTOR:
                probs.append(f"{field} too long ({n} {unit}, max {limit})")
            elif n > limit:
                warns.append(f"{field} slightly long ({n} {unit}, max {limit})")

        building = c.get("connection") == p.building_key
        hook = (c.get("hook") or "").strip()
        if not hook.endswith("?"):
            probs.append("hook must be one question ending with '?'")
        length("hook", _words(hook), p.limit("MAX_HOOK_WORDS"))
        for f in LONG_FIELDS:
            v = (c.get(f) or "").strip()
            if not v:
                if not (f == "where_you_see_it" and building):
                    probs.append(f"{f} is empty")
            else:
                length(f, _words(v), p.limit("MAX_FIELD_WORDS"))
        length("try_this", _words(c.get("try_this")), p.limit("MAX_TRY_WORDS"))
        if p.tamil_line:
            tl = (c.get("tamil_line") or "").strip()
            if not TAMIL_RE.search(tl):
                probs.append("tamil_line must be written in Tamil")
            else:
                length("tamil_line", len(tl), p.limit("MAX_TAMIL_CHARS"), "chars")
        c["warnings"] = warns
        if c.get("connection") not in {k for k, _ in p.connections}:
            probs.append("connection must be one of the allowed values")
        text = " ".join(str(c.get(f) or "") for f in TEXT_FIELDS).lower()
        for g in GENERIC_PHRASES:
            if g in text:
                probs.append(f'generic phrase "{g}" — name a specific thing instead')
        return probs

    def _review(self, days: List[Dict], cards: Dict[int, dict],
                p: SubjectProfile) -> Dict[int, List[str]]:
        """Fact-check cards against the lesson. Returns {day: [problems]} for flagged days."""
        if not days:
            return {}
        subject = p.display_name or p.key
        system = REVIEW_TEMPLATE.format(subject=subject, local_context=p.local_context,
                                        building=p.building_key)
        parts = [f"Check these {len(days)} cards. Return one review per card."]
        for d in days:
            fields = (tuple(f for f in TEXT_FIELDS if p.try_this or f != "try_this")
                      + (("tamil_line",) if p.tamil_line else ()))
            card = {f: cards[d["day"]].get(f, "") for f in fields}
            parts.append(f"\n=== DAY {d['day']}: {d['title']} ===\nCard:\n"
                         + json.dumps(card, ensure_ascii=False, indent=1)
                         + "\nLesson text:\n" + d["text"])
        data = self._call_tool(system, "\n".join(parts), REVIEW_TOOL, 8000)
        if data is None:
            # Fail closed: unchecked cards go back for another attempt, never straight out.
            print("      ⚠️  Review call failed — cards sent back, not accepted unchecked")
            return {d["day"]: [REVIEW_FAILED] for d in days}
        out: Dict[int, List[str]] = {}
        seen = set()
        for r in data.get("reviews", []):
            if not isinstance(r, dict):
                continue
            try:
                n = int(r.get("day"))
            except (TypeError, ValueError):
                continue
            seen.add(n)
            probs = [f"[{x.get('field', '?')}] {x['problem']}"
                     for x in (r.get("problems") or [])
                     if isinstance(x, dict) and x.get("problem")]
            if probs:
                out[n] = probs
        # A day the reviewer left out was never checked: send it back, never pass it.
        for d in days:
            if d["day"] not in seen:
                out[d["day"]] = [REVIEW_FAILED]
        return out

    @staticmethod
    def _is_try_this(problem: str) -> bool:
        return problem.startswith("try_this too long") or problem.startswith("review: [try_this]")

    @staticmethod
    def _soft(probs: List[str]) -> bool:
        """Only length or wording issues: still usable after the last retry."""
        return all(("too long" in x) or ("generic phrase" in x) for x in probs)

    # ── Generation ───────────────────────────────────────────
    def _generate_cards(self, days: List[Dict], p: SubjectProfile):
        system, tool = self._system(p), self._card_tool(p)
        pending = {d["day"]: d for d in days}
        done: Dict[int, dict] = {}
        last: Dict[int, tuple] = {}
        feedback: Dict[int, List[str]] = {}

        for attempt in range(MAX_RETRIES + 1):
            todo = [pending[k] for k in sorted(pending)]
            if not todo:
                break
            if attempt:
                print(f"   🔁 Retry {attempt}: days {[d['day'] for d in todo]}")
            for i in range(0, len(todo), p.batch_size):
                batch = todo[i:i + p.batch_size]
                in_batch = {d["day"] for d in batch}
                used = [f"Day {n}: {c.get('hook', '')} | seen in: {c.get('where_you_see_it') or '-'}"
                        for n, c in sorted(done.items()) if n not in in_batch]
                data = self._call_tool(system, self._cards_prompt(batch, feedback, used), tool, 6000)
                got = {c.get("day"): c for c in (data or {}).get("cards", []) if isinstance(c, dict)}
                checked: Dict[int, tuple] = {}
                for d in batch:
                    n = d["day"]
                    c = got.get(n)
                    if c is None:
                        feedback[n] = ["the card was missing — write it"]
                        continue
                    if p.building_mode == "skip" and c.get("connection") == p.building_key:
                        # Left out later in generate(): spend no review or retries on it.
                        done[n] = c
                        pending.pop(n, None)
                        feedback.pop(n, None)
                        continue
                    checked[n] = (c, self._check(c, p))

                # Fact check every card whose only issues are length or wording.
                to_review = [d for d in batch
                             if d["day"] in checked and self._soft(checked[d["day"]][1])]
                verdicts = self._review(to_review, {n: v[0] for n, v in checked.items()}, p)
                for n, rprobs in verdicts.items():
                    if n in checked:
                        checked[n][1].extend(f"review: {x}" for x in rprobs)

                for n, (c, probs) in checked.items():
                    # A failing try_this is dropped, not retried: no demo beats a forced one.
                    if probs and all(self._is_try_this(x) for x in probs):
                        print(f"      day {n} — try_this dropped: {'; '.join(probs)}")
                        c["try_this"] = ""
                        c["warnings"] = ([w for w in c.get("warnings", [])
                                          if not w.startswith("try_this")]
                                         + [f"try_this dropped: {'; '.join(probs)}"])
                        probs = []
                    last[n] = (c, probs)
                    if probs:
                        # A failed review call is not the card's fault: retry without blaming it.
                        fb = [x for x in probs if REVIEW_FAILED not in x]
                        if any(x.startswith("review: [where_you_see_it]") for x in fb):
                            fb.append(BUILDING_HINT.format(key=p.building_key))
                        if fb:
                            feedback[n] = fb
                        else:
                            feedback.pop(n, None)
                        print(f"      day {n} — {'; '.join(probs)}")
                    else:
                        done[n] = c
                        pending.pop(n, None)
                        feedback.pop(n, None)

        skipped = []
        for n in sorted(pending):
            c, probs = last.get(n, (None, ["no card returned"]))
            if c is not None and self._soft(probs):
                c["warnings"] = c.get("warnings", []) + probs
                done[n] = c
            else:
                skipped.append({"day": n, "reasons": probs})

        cards = []
        for d in days:
            if d["day"] in done:
                c = done[d["day"]]
                if not p.try_this:
                    c.pop("try_this", None)
                c["day"] = d["day"]
                c["title"] = d["title"]
                cards.append(c)
        return cards, skipped

    def _generate_big_why(self, title: str, cards: List[dict],
                          recap_days: List[Dict], p: SubjectProfile) -> Optional[dict]:
        if not cards:
            return None
        lines = [f"Lesson: {title}", "", "The day cards already written:"]
        for c in cards:
            lines.append(f"- Day {c['day']} ({c['title']}): {c['hook']} {c['link']}")
        if recap_days:
            lines += ["", "The lesson's revision day (for the overall picture):",
                      recap_days[0]["text"][:4000]]
        lines += ["", "Write the opening card for the whole lesson: the one question it answers "
                      "for the student's life, and why the whole lesson matters. Build it from "
                      "the strongest, most specific card ideas above. Never count things "
                      "(no \"16 formulas\", no \"five rules\")."]
        tool = self._big_why_tool(p)
        feedback: List[str] = []
        for _ in range(MAX_RETRIES + 1):
            prompt = "\n".join(lines)
            fb = [x for x in feedback if REVIEW_FAILED not in x]
            if fb:
                prompt += "\n\nYour previous opening card had problems — fix them: " + "; ".join(fb)
            data = self._call_tool(self._system(p), prompt, tool, 1500)
            if not data:
                feedback = []
                continue
            feedback = self._check_big_why(data, p) or self._review_big_why(data, title, recap_days, p)
            if not feedback:
                return data
            print(f"      big why — {'; '.join(feedback)}")
        print("      ⚠️  Big Why skipped — no opening card passed the checks")
        return None

    def _check_big_why(self, b: dict, p: SubjectProfile) -> List[str]:
        probs: List[str] = []
        q = (b.get("question") or "").strip()
        s = (b.get("story") or "").strip()
        tl = (b.get("tamil_line") or "").strip()
        if not q.endswith("?"):
            probs.append("question must end with '?'")
        if _words(q) > p.limit("MAX_HOOK_WORDS") * HARD_FACTOR:
            probs.append(f"question too long (max {p.limit('MAX_HOOK_WORDS')} words)")
        if not s:
            probs.append("story is empty")
        elif _words(s) > p.limit("MAX_BIGWHY_WORDS") * HARD_FACTOR:
            probs.append(f"story too long ({_words(s)} words, max {p.limit('MAX_BIGWHY_WORDS')})")
        if p.tamil_line and not TAMIL_RE.search(tl):
            probs.append("tamil_line must be written in Tamil")
        if COUNT_RE.search(f"{q} {s}"):
            probs.append('no counts like "16 formulas" or "five rules" — describe ideas, '
                         'do not count them')
        low = f"{q} {s}".lower()
        for g in GENERIC_PHRASES:
            if g in low:
                probs.append(f'generic phrase "{g}" — name a specific thing instead')
        return probs

    def _review_big_why(self, b: dict, title: str, recap_days: List[Dict],
                        p: SubjectProfile) -> List[str]:
        subject = p.display_name or p.key
        system = REVIEW_TEMPLATE.format(subject=subject, local_context=p.local_context,
                                        building=p.building_key)
        card = {"hook": b.get("question", ""), "link": b.get("story", "")}
        if p.tamil_line:
            card["tamil_line"] = b.get("tamil_line", "")
        text = recap_days[0]["text"][:6000] if recap_days else ""
        prompt = (f"Check this 1 card: the opening card of the lesson \"{title}\". Its hook is the "
                  f"lesson's question and its link is why the lesson matters. Return one review "
                  f"with day 0.\n\n=== DAY 0: {title} ===\nCard:\n"
                  + json.dumps(card, ensure_ascii=False, indent=1)
                  + "\nLesson text:\n" + text)
        data = self._call_tool(system, prompt, REVIEW_TOOL, 2000)
        if data is None:
            return [REVIEW_FAILED]
        reviews = [r for r in data.get("reviews", []) if isinstance(r, dict)]
        if not reviews:
            return [REVIEW_FAILED]
        probs: List[str] = []
        for r in reviews:
            for x in r.get("problems") or []:
                if isinstance(x, dict) and x.get("problem"):
                    probs.append(f"review: {x['problem']}")
        return probs

    def generate(self, lp_path: str, lesson: Dict, only_days: Optional[List[int]] = None) -> Dict:
        p = get_profile(lesson.get("subject", ""))
        lp = load_lp(lp_path, lesson.get("subject", ""))
        days = lp["days"]
        if only_days:
            days = [d for d in days if d["day"] in only_days]
        title = lesson.get("title", "")
        print(f"[Beyond] {title} — {len(days)} days (profile: {p.key})")

        cards, skipped = self._generate_cards(days, p)
        left_out: List[Dict] = []
        if p.building_mode == "skip":
            left_out = [{"day": c["day"], "title": c["title"]}
                        for c in cards if c.get("connection") == p.building_key]
            cards = [c for c in cards if c.get("connection") != p.building_key]
            if left_out:
                print(f"   ⏭  Left out (no honest real-life link): days {[d['day'] for d in left_out]}")
        big_why = self._generate_big_why(title, cards, lp["recap_days"], p)

        used = {c["connection"] for c in cards}
        return {
            "lesson": lesson,
            "subject": p.key,
            "connections": [{"key": k, "label": l} for k, l in p.connections if k in used],
            "big_why": big_why,
            "cards": cards,
            "skipped_days": skipped,
            "left_out_days": left_out,
            "model": self.model,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
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


beyond_builder = BeyondBuilder()