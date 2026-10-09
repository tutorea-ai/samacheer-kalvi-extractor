"""
builder.py
----------
Generates Flash Cards from a deployed LP (one card per LP day + a Chapter
Recap). Titles, sections and card types come from lp_parser (deterministic);
the model writes only: recall prompt, 4-5 bullets, formula, exam tip.

Output is enforced through tool use (JSON schema), so responses are always
valid JSON. Cards are validated; invalid ones get up to 2 retries with
feedback, then are skipped with a warning.

Notation: Unicode where it exists (q₁, r², ε₀, 10⁻¹⁹); otherwise "_" for
subscripts (v_d, R_eq) and "^" for superscripts — the renderer converts
these to real <sub>/<sup>.
"""

import re
import time
from datetime import datetime
from typing import Optional

import anthropic
import httpx

from ...config import settings
from .lp_parser import load_lp, TAMIL_RE
from .card_types import types_for, allowed_keys


BATCH_SIZE        = 6
MAX_TEXT_PER_DAY  = 3500
MAX_BOARD_PER_DAY = 2500
MAX_BULLET_WORDS  = 18     # hard limit (target 10-12)
MAX_PROMPT_WORDS  = 22
MAX_TIP_WORDS     = 25
MAX_BACK_CHARS    = 560    # bullets + formula + tip must fit one phone screen
MAX_RECAP_BACK_CHARS = 720     # recap has 5–6 bullets, so it needs more room
CARD_RETRIES      = 2
API_RETRIES       = 2

# A question word that STARTS a clause: at the start, after , or ;, or after and/or.
# Two or more of these means two or more questions.
# which/when/where are excluded — they're common as relative pronouns inside
# ONE question (e.g. "...a point, which lies on the axis, vary?") and would
# false-positive constantly in Physics phrasing.
QWORD_CLAUSE_RE = re.compile(
    r"(?:^|[,;]\s*(?:and\s+|or\s+)?|\b(?:and|or)\s+)(what|how|why)\b",
    re.IGNORECASE,
)

def _is_compound(prompt: str) -> bool:
    return len(QWORD_CLAUSE_RE.findall(prompt.strip())) > 1

SYSTEM_PROMPT = """You write revision flash cards for Tamil Nadu State Board (Samacheer Kalvi)
students preparing for SSLC / HSC board examinations.

The student is revising, often the night before an exam, and may be tired and anxious.
Write calm, clear, exam-ready points. Every fact must come from the material given.

English only. Plain text only: no HTML, no LaTeX, no markdown.
Notation: use Unicode where it exists (×, ÷, ², ³, ⁻¹, ₀, ₁, ₂, √, π, ε, μ, Ω, Δ, →, q₁, ε₀, 10⁻¹⁹).
For a subscript with no Unicode form write an underscore: v_d, R_eq, ε_eq, I_g, r_min.
For a superscript with no Unicode form write a caret: x^n."""

TYPE_GUIDE = {
    "concept":     "definitions, properties, key statements, important distinctions",
    "formula":     "the law or relation, what each symbol means with SI units, the common numerical trick",
    "derivation":  "the starting idea, the key steps in order, and the final result",
    "device":      "principle, key parts / construction, how it works, what it is used for",
    "application": "where and how it is used, with the reason",
    "fact":        "key facts most likely to be asked",
    "term":        "key terms with one-line meanings",
}

CARD_PROMPT = """Create one flash card for EACH lesson-plan day below.
Class {class_num} {subject_label} — {lesson_title}

For each day:
- prompt: ONE short question about ONE thing only. Never join questions
  with commas or "and" (bad: "What is X, what is its unit, and how does Y…?";
  good: "How does drift velocity depend on the electric field?").
- The question must cover the day's WHOLE main idea, so that every bullet
  helps answer it. If the day teaches two linked things, name both in one
  question (good: "What are the key facts about electric current and drift
  velocity?"). Never ask about one detail while the bullets cover more.
- bullets: 4 or 5 facts (aim for 10-12 words each, never more than {max_words}).
  Bullets are FACTS only — no exam advice in bullets.
- formula: the single most important formula for that day, or "" if none.
- exam_tip: ONE sentence of board-exam advice (max {max_tip} words) — what to state first,
  a unit to convert, a diagram to draw, a common mistake. It must NOT repeat a bullet.

Focus by card type:
{type_guide}

Rules:
- Use ONLY facts from the material. Do not add outside facts.
- Ignore classroom instructions (teacher says, activities, timings, checks for understanding).
- Keep each card's bullets + formula + exam_tip under about {max_back} characters.
- Every bullet must be about THIS day's topic only. If a fact belongs to a
  different day's lesson, leave it out, even if it appears in the text.
- For a derivation card: the bullets are the derivation steps in order, and
  the last bullet is the final result. No side facts or extra formulas.

Save the cards with the save_flashcards tool.

Lesson-plan days:
{days_block}"""

RECAP_PROMPT = """Create the final "Chapter Recap" flash card for Class {class_num} {subject_label} — {lesson_title}.
It must help a student revise the WHOLE chapter in two minutes.

- prompt: "Can you explain the whole chapter in two minutes?"
- bullets: 5 or 6 points, ONE idea per bullet — never merge different topics into one bullet
  (aim for 10-12 words each, never more than {max_words}). Include the key formula where one exists.
- formula: ""
- exam_tip: ONE sentence of board-exam advice for this chapter (max {max_tip} words).

Use ONLY the material below. Save it with the save_recap tool.

Cards in this chapter (title — key formula):
{card_index}

Revision day material:
{recap_material}"""

CARD_FIELDS = {
    "prompt":   {"type": "string"},
    "bullets":  {"type": "array", "items": {"type": "string"}},
    "formula":  {"type": "string"},
    "exam_tip": {"type": "string"},
}

CARD_TOOL = {
    "name": "save_flashcards",
    "description": "Save one flash card per lesson-plan day.",
    "input_schema": {
        "type": "object",
        "properties": {
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"day": {"type": "integer"}, **CARD_FIELDS},
                    "required": ["day", "prompt", "bullets", "formula", "exam_tip"],
                },
            }
        },
        "required": ["cards"],
    },
}

RECAP_TOOL = {
    "name": "save_recap",
    "description": "Save the Chapter Recap flash card.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recap": {
                "type": "object",
                "properties": CARD_FIELDS,
                "required": ["prompt", "bullets", "formula", "exam_tip"],
            }
        },
        "required": ["recap"],
    },
}


def _words(s: str) -> int:
    return len(s.split())


def _overlap(a: str, b: str) -> float:
    wa = set(re.findall(r"\w+", a.lower()))
    wb = set(re.findall(r"\w+", b.lower()))
    return len(wa & wb) / max(1, min(len(wa), len(wb)))


class FlashcardBuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Flashcard Builder initialized — model: {self.model}")

    # ── public ────────────────────────────────────────────────────────────────

    def generate(self, lp_path: str, meta: dict) -> Optional[dict]:
        """
        meta: {"class": 12, "subject": "physics", "unit": 2, "title": "Current Electricity"}
        Returns the deck dict (Phase 0 schema) or None on failure.
        """
        lp = load_lp(lp_path)
        if not lp["days"]:
            print(f"      [Flashcards] ❌ No LP days found in {lp_path}")
            return None

        subject      = (meta.get("subject") or "").lower()
        content_days = [d for d in lp["days"] if not d["is_recap"]]
        recap_day    = next((d for d in lp["days"] if d["is_recap"]), None)

        print(f"      [Flashcards] {meta.get('title')} — {len(content_days)} days"
              f"{' + recap' if recap_day else ''}, batches of {BATCH_SIZE}")

        cards, skipped = {}, []
        for i in range(0, len(content_days), BATCH_SIZE):
            pending, feedback = content_days[i:i + BATCH_SIZE], ""
            for attempt in range(CARD_RETRIES + 1):
                got, bad = self._batch(pending, meta, feedback)
                cards.update(got)
                if not bad:
                    break
                if attempt < CARD_RETRIES:
                    print(f"         🔁 Retry {attempt + 1}: days {[d['day'] for d, _ in bad]}")
                    pending  = [d for d, _ in bad]
                    feedback = "\n".join(f"Day {d['day']}: {why}" for d, why in bad)
                else:
                    for d, why in bad:
                        skipped.append(d["day"])
                        print(f"         ⚠️  Day {d['day']} skipped — {why}")

        ordered = []
        for d in content_days:
            c = cards.get(d["day"])
            if c:
                ordered.append({
                    "day": d["day"], "section": d["section"], "type": d["card_type"],
                    "title": d["title"], **c,
                })

        recap = self._recap(ordered, recap_day, meta) if recap_day else None

        print(f"      [Flashcards] ✅ {len(ordered)} cards"
              f"{' + recap' if recap else ''}"
              f"{f' | ⚠️ skipped days {skipped}' if skipped else ''}")

        if not ordered:
            return None

        return {
            "lesson":       {k: meta.get(k) for k in ("class", "subject", "unit", "title")},
            "source_lp":    lp["source_lp"],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "model":        self.model,
            "types":        [{"key": k, "label": l} for k, l in types_for(subject)],
            "cards":        ordered,
            "recap":        recap,
            "skipped_days": skipped,
        }

    # ── batches ───────────────────────────────────────────────────────────────

    def _batch(self, days, meta, feedback: str = ""):
        types_in_batch = sorted({d["card_type"] for d in days if d["card_type"]})
        prompt = CARD_PROMPT.format(
            class_num=meta.get("class"), subject_label=(meta.get("subject") or "").title(),
            lesson_title=meta.get("title"), max_words=MAX_BULLET_WORDS,
            max_prompt=MAX_PROMPT_WORDS, max_tip=MAX_TIP_WORDS, max_back=MAX_BACK_CHARS,
            type_guide="\n".join(f"- {t}: {TYPE_GUIDE.get(t, '')}" for t in types_in_batch),
            days_block="\n\n".join(self._day_block(d) for d in days),
        )
        if feedback:
            prompt += f"\n\nYour previous attempt had these problems — fix them:\n{feedback}"

        data   = self._call_tool(prompt, CARD_TOOL, max_tokens=4000)
        by_day = {c.get("day"): c for c in (data or {}).get("cards", []) if isinstance(c, dict)}
        got, bad = {}, []
        for d in days:
            c   = by_day.get(d["day"])
            why = self._validate(c) if c else "missing from response"
            if why:
                bad.append((d, why))
            else:
                got[d["day"]] = self._tidy(c)
        return got, bad

    def _recap(self, cards, recap_day, meta) -> Optional[dict]:
        index    = "\n".join(f"- {c['title']} — {c['formula'] or '—'}" for c in cards)
        material = ("\n".join(recap_day["objectives"]) + "\n" +
                    "\n".join(recap_day["board_work"]))[:MAX_BOARD_PER_DAY + 1500]
        base = RECAP_PROMPT.format(
            class_num=meta.get("class"), subject_label=(meta.get("subject") or "").title(),
            lesson_title=meta.get("title"), max_words=MAX_BULLET_WORDS, max_tip=MAX_TIP_WORDS,
            card_index=index, recap_material=material,
        )
        prompt = base
        for attempt in range(CARD_RETRIES + 1):
            data = self._call_tool(prompt, RECAP_TOOL, max_tokens=1500)
            r    = (data or {}).get("recap")
            why  = self._validate(r, min_b=5, max_b=6, check_prompt=False, max_back=MAX_RECAP_BACK_CHARS) if r else "missing recap"
            if not why:
                return {"title": "Chapter Recap", **self._tidy(r)}
            print(f"         ⚠️  Recap attempt {attempt + 1} invalid — {why}")
            prompt = base + f"\n\nYour previous attempt had this problem — fix it: {why}"
        return None

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _day_block(d) -> str:
        parts = [f"### Day {d['day']} — {d['title']}",
                 f"Textbook section: {d['section'] or '—'} | Card type: {d['card_type']}"]
        if d["objectives"]:
            parts.append("Learning objectives:\n" + "\n".join(f"- {o}" for o in d["objectives"]))
        if d["board_work"]:
            parts.append("Board work:\n" + "\n---\n".join(d["board_work"])[:MAX_BOARD_PER_DAY])
        parts.append("Lesson explanation (excerpt):\n" + d["text"][:MAX_TEXT_PER_DAY])
        return "\n".join(parts)

    @staticmethod
    def _validate(c, min_b=4, max_b=5, check_prompt=True, max_back=MAX_BACK_CHARS) -> str:
        if not isinstance(c, dict):
            return "not an object"
        prompt  = (c.get("prompt") or "").strip()
        bullets = c.get("bullets")
        tip     = (c.get("exam_tip") or "").strip()
        formula = (c.get("formula") or "").strip()

        if not prompt:
            return "empty prompt"
        if check_prompt:
            if prompt.count("?") != 1:
                return "prompt must be exactly one question with one '?'"
            if _is_compound(prompt):
                return (f"prompt asks more than one question (\"{prompt[:90]}\") — "
                        f"ask ONE question that covers the whole day's idea")
            if _words(prompt) > MAX_PROMPT_WORDS:
                return f"prompt too long ({_words(prompt)} words, max {MAX_PROMPT_WORDS})"
        if not isinstance(bullets, list) or not (min_b <= len(bullets) <= max_b):
            return f"needs {min_b}-{max_b} bullets, got {len(bullets) if isinstance(bullets, list) else 0}"
        for b in bullets:
            if not isinstance(b, str) or not b.strip():
                return "empty bullet"
            if _words(b) > MAX_BULLET_WORDS:
                return f"bullet too long ({_words(b)} words, max {MAX_BULLET_WORDS}): '{b[:50]}…'"
        if not tip:
            return "empty exam_tip"
        if _words(tip) > MAX_TIP_WORDS:
            return f"exam_tip too long ({_words(tip)} words, max {MAX_TIP_WORDS}) — one sentence"
        if any(_overlap(tip, b) > 0.7 for b in bullets):
            return "exam_tip repeats a bullet — make the tip different advice"
        back = sum(len(b) for b in bullets) + len(formula) + len(tip)
        if back > max_back:
            return f"card back too long ({back} chars, limit {max_back}) — shorten bullets"
        joined = " ".join([prompt, tip, formula, *bullets])
        if TAMIL_RE.search(joined):
            return "contains Tamil text"
        if re.search(r"<[a-z/][^>]*>|\\\(|\\\[|\$\$|\*\*", joined):
            return "contains HTML, LaTeX or markdown"
        return ""

    @staticmethod
    def _tidy(c) -> dict:
        return {
            "prompt":   c["prompt"].strip(),
            "bullets":  [b.strip() for b in c["bullets"]],
            "formula":  (c.get("formula") or "").strip(),
            "exam_tip": c["exam_tip"].strip(),
        }

    def _call_tool(self, prompt: str, tool: dict, max_tokens: int) -> Optional[dict]:
        for attempt in range(API_RETRIES + 1):
            try:
                resp = self.client.messages.create(
                    model=self.model, max_tokens=max_tokens, system=SYSTEM_PROMPT,
                    tools=[tool], tool_choice={"type": "tool", "name": tool["name"]},
                    messages=[{"role": "user", "content": prompt}],
                )
                if resp.stop_reason == "max_tokens":
                    print(f"         ⚠️  Output cut off at max_tokens — response may be incomplete")
                for block in resp.content:
                    if block.type == "tool_use":
                        return block.input
                print(f"         ❌ No tool output in response")
                return None
            except (httpx.HTTPError, anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
                wait = 10 * (attempt + 1)
                print(f"         ⚠️  API connection error ({type(e).__name__}) — retry in {wait}s")
                time.sleep(wait)
            except anthropic.APIStatusError as e:
                if e.status_code in (429, 529) and attempt < API_RETRIES:
                    wait = 30 * (attempt + 1)
                    print(f"         ⚠️  API busy ({e.status_code}) — retry in {wait}s")
                    time.sleep(wait)
                    continue
                print(f"         ❌ API error: {e}")
                return None
        print(f"         ❌ API failed after {API_RETRIES + 1} attempts")
        return None


flashcard_builder = FlashcardBuilder()