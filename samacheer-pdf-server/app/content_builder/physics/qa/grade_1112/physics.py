"""
physics.py (QA)
---------------
QA Builder for Samacheer Kalvi Physics — Class 11 & 12

v1.0 — Oct 2026

PATTERN (confirmed with the teachers):
  Part I   — MCQ                  1 mark   × 40   Q1–Q40
  Part II  — Very short answers   2 marks  × 25   Q41–Q65
  Part III — Short answers        3 marks  × 20   Q66–Q85
  Part IV  — Long answers         5 marks  × 15   Q86–Q100   (SVG where needed)

EXACTLY 100 — HOW IT IS GUARANTEED
  The Biology bulk run left lessons at 96/98 because each tier was one large
  call with a tight max_tokens, and a short result was kept after one retry.
  Here:
    1. Small batches (20+20, 13+12, 10+10, 5+5+5) with generous max_tokens
    2. The model returns JSON; Python validates each question, drops broken or
       duplicate ones, numbers Q1–Q100 and renders the HTML itself
    3. Truncated output is salvaged — every complete question is kept
    4. Top-up calls request exactly the missing number (+2 spare), with the
       questions already asked, up to MAX_TOPUPS times per part
    5. If any part still cannot reach its count, generate() returns None —
       a short bank is NEVER returned (the backend's size-only deploy check
       would otherwise mark it done)

OTHER CONTRACT POINTS
  - generate(text, metadata) -> str | None ; never raises
  - qa_only mode passes RAW text → clean_noise(text, subject="physics") here
  - Streaming calls; the chapter text block is prompt-cached across batches
  - SDK retries before a stream starts; we retry mid-stream drops (10/30/60 s)
  - No per-run state on self (singleton serves parallel requests)
  - Markup = existing QA frontend pattern (qa-section, show-section-btn,
    toggleSectionAnswers, answer-reveal) — same as Biology / SS
  - Book-back questions from the chapter's Evaluation section are included
    and marked "Book-back"
"""

import html as html_lib
import re
import time
from typing import Dict, List, Optional, Tuple

import anthropic
import httpx                    # installed with the anthropic SDK

from .....config import settings
from ...base import (
    PHYS_QA_SYSTEM_PROMPT,
    QA_PARTS,
    QA_TOTAL_QUESTIONS,
    get_qa_header,
    get_display_title,
    extract_question_objects,
    sanitize_answer_html,
    sanitize_svg,
    normalize_stem,
    is_near_duplicate,
)

try:
    from .....services.section_detector import clean_noise
except Exception:  # pragma: no cover
    clean_noise = None


# ============================================================================
# TUNABLES
# ============================================================================

MAX_TOPUPS = 3                       # extra calls per part if still short
TOPUP_SPARE = 2                      # ask for a couple more than missing
REQUEST_TIMEOUT_S = 900.0
SDK_MAX_RETRIES = 3                  # failures BEFORE a stream starts
STREAM_RETRY_BACKOFF_S = (10, 30, 60)  # drops DURING a stream
MAX_TEXT_CHARS = 220000
USED_STEMS_IN_PROMPT = 120           # cap on "already asked" list length


# ============================================================================
# PHYSICS QA BUILDER
# ============================================================================

class PhysicsQA1112Builder:

    discipline = "physics"

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            max_retries=SDK_MAX_RETRIES,
            timeout=REQUEST_TIMEOUT_S,
        )
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Physics QA Builder (1112) v1.0 initialized — model: {self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """Never raises. Returns QA body HTML with exactly 100 questions, or None."""
        try:
            return self._generate(text, metadata or {})
        except Exception as e:
            print(f"❌ [Physics QA] Unexpected error — returning None: {type(e).__name__}: {e}")
            return None

    def _generate(self, text: str, metadata: dict) -> Optional[str]:
        t0 = time.time()
        if not text or not text.strip():
            print("❌ [Physics QA] Empty chapter text — aborting")
            return None
        if clean_noise is not None:
            text = clean_noise(text, subject="physics")   # qa_only sends raw text

        run = {
            "text": text[:MAX_TEXT_CHARS],
            "title": get_display_title(metadata),
            "class_num": metadata.get("class", ""),
            "unit": metadata.get("unit", ""),
            "used_stems": [],          # every accepted stem so far (all parts)
        }
        print(f"      [Physics QA] Generating: Class {run['class_num']} Unit {run['unit']} "
              f"— {run['title']} ({len(text)} chars)")

        sections_html = [get_qa_header(run["title"], run["class_num"], run["unit"])]
        total = 0
        for part in QA_PARTS:
            print(f"      [Physics QA] {part['title']} — need {part['count']}")
            questions = self._generate_part(run, part)
            if len(questions) != part["count"]:
                print(f"         ❌ {part['title']}: only {len(questions)}/{part['count']} "
                      f"after top-ups — returning None (never ship a short bank)")
                return None
            sections_html.append(self._render_section(part, questions))
            total += len(questions)
            print(f"         ✅ {part['title']}: {len(questions)}/{part['count']}")

        html = "\n\n".join(sections_html)

        # Final guarantee — count rendered items, not just list lengths
        n_items = html.count('<div class="qa-item">')
        if total != QA_TOTAL_QUESTIONS or n_items != QA_TOTAL_QUESTIONS:
            print(f"         ❌ Final count check failed: {n_items} rendered / {total} collected")
            return None

        mins = (time.time() - t0) / 60
        print(f"      [Physics QA] ✅ Complete — {n_items} questions, {len(html)} chars, {mins:.1f} min")
        return html

    # ==================================================================
    # PART GENERATION — batches, validation, dedupe, top-ups
    # ==================================================================

    def _generate_part(self, run: dict, part: dict) -> List[dict]:
        accepted: List[dict] = []

        # Planned batches
        for b_idx, size in enumerate(part["batches"]):
            label = f"{part['key']} batch {b_idx + 1}/{len(part['batches'])}"
            first_batch = b_idx == 0
            new = self._request(run, part, size, label, include_book_back=first_batch)
            added = self._accept(run, part, new, accepted, limit=part["count"])
            print(f"         · {label}: asked {size}, accepted {added} (total {len(accepted)})")

        # Top-ups until the part is full
        for attempt in range(1, MAX_TOPUPS + 1):
            missing = part["count"] - len(accepted)
            if missing <= 0:
                break
            label = f"{part['key']} top-up {attempt}/{MAX_TOPUPS}"
            new = self._request(run, part, missing + TOPUP_SPARE, label,
                                include_book_back=False, topup=True)
            added = self._accept(run, part, new, accepted, limit=part["count"])
            print(f"         ↻ {label}: missing {missing}, accepted {added} (total {len(accepted)})")

        # Book-back questions first, then the rest, capped at the part count
        accepted.sort(key=lambda q: 0 if q.get("book_back") else 1)
        accepted = accepted[: part["count"]]
        if part["kind"] == "mcq":
            self._balance_mcq_answers(accepted)
        return accepted

    # Options that refer to other options must keep their order
    _OPTION_REF_RE = re.compile(
        r"\b(both|neither|all|none|above)\b|\(\s*[a-d]\s*\)|\b[a-d]\s*(and|&|or)\s*[a-d]\b",
        re.IGNORECASE)

    @classmethod
    def _balance_mcq_answers(cls, questions: List[dict]) -> None:
        """
        Spread correct answers evenly over a/b/c/d. Models favour one letter
        (Unit 2 first run: b was correct 23/40 times). For each eligible MCQ,
        the correct option is swapped into the least-used position so far.
        Book-back MCQs keep the textbook order; MCQs whose options refer to
        each other ("both (a) and (b)") are left untouched.
        """
        counts = {l: 0 for l in "abcd"}
        eligible = []
        for q in questions:
            if q.get("book_back") or any(cls._OPTION_REF_RE.search(o) for o in q["options"]):
                counts[q["answer"]] += 1
            else:
                eligible.append(q)
        for q in eligible:
            target = min("abcd", key=lambda l: (counts[l], "abcd".index(l)))
            i, j = "abcd".index(q["answer"]), "abcd".index(target)
            q["options"][i], q["options"][j] = q["options"][j], q["options"][i]
            q["answer"] = target
            counts[target] += 1
        print(f"         · MCQ answer spread: " + " ".join(f"{l}={counts[l]}" for l in "abcd"))

    def _accept(self, run: dict, part: dict, new: List[dict],
                accepted: List[dict], limit: int) -> int:
        """Validate, normalize and de-duplicate; append to `accepted`."""
        added = 0
        for raw in new:
            if len(accepted) >= limit:
                break
            q = (self._validate_mcq(raw) if part["kind"] == "mcq"
                 else self._validate_descriptive(raw, part))
            if q is None:
                continue
            if any(is_near_duplicate(q["q"], s) for s in run["used_stems"]):
                continue
            accepted.append(q)
            run["used_stems"].append(q["q"])
            added += 1
        return added

    # ---------- validators ----------

    _STEM_LABEL_RE = re.compile(
        r"\s*[\(\[]\s*(book[\s-]*back|textbook|evaluation)[^\)\]]{0,40}[\)\]]\s*",
        re.IGNORECASE)

    @classmethod
    def _clean_stem(cls, stem: str) -> str:
        """Remove '(Book-back Long Answer 1)'-style labels — the badge already shows it."""
        return re.sub(r"\s{2,}", " ", cls._STEM_LABEL_RE.sub(" ", stem)).strip()

    @staticmethod
    def _validate_mcq(raw: dict) -> Optional[dict]:
        if not isinstance(raw, dict):
            return None
        stem = str(raw.get("q") or raw.get("question") or "").strip()
        opts = raw.get("options")
        if not stem or not isinstance(opts, list) or len(opts) != 4:
            return None
        opts = [re.sub(r"^\s*\(?[a-dA-D][).:]\s*", "", str(o)).strip() for o in opts]
        if any(not o for o in opts) or len({normalize_stem(o) for o in opts}) != 4:
            return None
        ans = str(raw.get("answer", "")).strip().lower().strip("().: ")
        if ans not in ("a", "b", "c", "d"):
            # accept the option text itself
            hits = [i for i, o in enumerate(opts) if normalize_stem(o) == normalize_stem(ans)]
            if len(hits) != 1:
                return None
            ans = "abcd"[hits[0]]
        bad = ("all of the above", "none of the above")
        if any(normalize_stem(o) in bad for o in opts):
            return None
        return {
            "q": PhysicsQA1112Builder._clean_stem(stem),
            "options": opts,
            "answer": ans,
            "explanation": str(raw.get("explanation", "")).strip(),
            "book_back": bool(raw.get("book_back")),
        }

    @staticmethod
    def _validate_descriptive(raw: dict, part: dict) -> Optional[dict]:
        if not isinstance(raw, dict):
            return None
        stem = str(raw.get("q") or raw.get("question") or "").strip()
        ans = str(raw.get("answer_html") or raw.get("answer") or "").strip()
        min_len = {2: 25, 3: 60, 5: 150}.get(part["marks"], 25)
        if not stem or len(re.sub(r"<[^>]+>", "", ans)) < min_len:
            return None
        return {
            "q": PhysicsQA1112Builder._clean_stem(stem),
            "answer_html": ans,
            "diagram_svg": str(raw.get("diagram_svg", "") or ""),
            "type": str(raw.get("type", "")).strip().lower(),
            "book_back": bool(raw.get("book_back")),
        }

    # ==================================================================
    # PROMPTS
    # ==================================================================

    def _request(self, run: dict, part: dict, n: int, label: str,
                 include_book_back: bool, topup: bool = False) -> List[dict]:
        prompt = self._build_prompt(run, part, n, include_book_back, topup)
        raw, stop = self._call(run["text"], prompt, part["max_tokens"], label)
        if raw is None:
            return []
        if stop == "max_tokens":
            print(f"         ⚠️ {label}: cut off at max_tokens — keeping complete questions")
        return extract_question_objects(raw)

    def _build_prompt(self, run: dict, part: dict, n: int,
                      include_book_back: bool, topup: bool) -> str:
        used = run["used_stems"][-USED_STEMS_IN_PROMPT:]
        used_block = ("\n".join(f"- {re.sub(r'<[^>]+>', '', s)[:140]}" for s in used)
                      if used else "(none yet)")

        if part["kind"] == "mcq":
            schema = """{
  "questions": [
    {
      "q": "question text (plain HTML formatting only)",
      "options": ["option text", "option text", "option text", "option text"],
      "answer": "b",
      "explanation": "one line — why this option is correct",
      "book_back": false
    }
  ]
}"""
        else:
            diagram_rule = ""
            if part["marks"] == 5:
                diagram_rule = """
DIAGRAMS: when a diagram genuinely helps (derivation set-up, field lines,
circuit, apparatus, ray/vector diagram), put a simple labelled inline SVG in
"diagram_svg": start with <svg viewBox="0 0 400 260" ...>, use only line,
circle, rect, path, polygon, text and marker/defs elements, black strokes on a
white background, readable labels (font-size 12-14), every part the answer
mentions labelled. Leave "diagram_svg" as "" when no diagram is needed.
Keep each SVG under 4000 characters."""
            schema = f"""{{
  "questions": [
    {{
      "q": "question text",
      "answer_html": "complete answer using only the allowed tags",
      "type": "definition | law | reason | distinguish | derivation | working | numerical",
      "book_back": false,
      "diagram_svg": ""
    }}
  ]
}}{diagram_rule}"""

        numerical_rule = ""
        if part["min_numerical"] and not topup:
            numerical_rule = (f"- At least {min(part['min_numerical'], n)} of these {n} must be "
                              f"numericals (type \"numerical\").\n")

        book_back_rule = (
            "- FIRST include the chapter's own book-back (Evaluation section) "
            f"questions of this type that are not already asked, copied exactly, "
            "with \"book_back\": true and your complete answer. Then fill the rest "
            "with new questions.\n"
            if include_book_back else
            "- Write NEW questions (\"book_back\": false).\n"
        )

        return f"""Generate questions for {part['title']} ({part['marks']} mark{'s' if part['marks'] > 1 else ''} each)
of the Physics question bank for: Unit {run['unit']}: {run['title']} (Class {run['class_num']}).

Generate EXACTLY {n} questions.

WHAT TO ASK:
{part['guidance']}

ANSWER FORMAT:
{part['answer_rule']}

RULES:
{book_back_rule}{numerical_rule}- Spread questions across the WHOLE chapter — every major section, not just the start.
- Do NOT repeat or rephrase any question already asked (list below).
- Every answer must be complete and correct; numerical answers carry units.
- Use the chapter text provided above as the only source of content.

ALREADY ASKED (do not repeat or rephrase):
{used_block}

Return ONLY this JSON object (no prose, no code fences):
{schema}"""

    # ==================================================================
    # API CALL — streaming, cached chapter text, mid-stream retries
    # ==================================================================

    def _call(self, chapter_text: str, prompt: str, max_tokens: int,
              label: str) -> Tuple[Optional[str], Optional[str]]:
        attempts = len(STREAM_RETRY_BACKOFF_S) + 1
        for attempt in range(1, attempts + 1):
            text, stop, retryable = self._call_once(chapter_text, prompt, max_tokens, label)
            if text is not None or not retryable:
                return text, stop
            if attempt < attempts:
                wait = STREAM_RETRY_BACKOFF_S[attempt - 1]
                print(f"         ↻ {label}: transient failure — retry {attempt}/{attempts - 1} in {wait}s")
                time.sleep(wait)
        print(f"❌ [Physics QA] {label}: still failing after {attempts - 1} retries")
        return None, None

    @staticmethod
    def _is_transient(e: Exception) -> bool:
        if isinstance(e, (anthropic.APIConnectionError, httpx.TransportError)):
            return True
        if isinstance(e, anthropic.APIStatusError):
            code = getattr(e, "status_code", 0) or 0
            return code == 429 or code >= 500 or "overloaded" in str(e).lower()
        return False

    def _call_once(self, chapter_text: str, prompt: str, max_tokens: int,
                   label: str) -> Tuple[Optional[str], Optional[str], bool]:
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=[{"type": "text", "text": PHYS_QA_SYSTEM_PROMPT,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{
                    "role": "user",
                    "content": [
                        {   # identical for every batch of this chapter → cached
                            "type": "text",
                            "text": f"CHAPTER TEXT (the only source of content):\n---\n{chapter_text}\n---",
                            "cache_control": {"type": "ephemeral"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }],
            ) as stream:
                msg = stream.get_final_message()
            text = "".join(getattr(b, "text", "") for b in msg.content
                           if getattr(b, "type", "") == "text")
            usage = getattr(msg, "usage", None)
            if usage is not None:
                print(f"         · {label}: in={getattr(usage, 'input_tokens', '?')} "
                      f"cached={getattr(usage, 'cache_read_input_tokens', 0) or 0} "
                      f"out={getattr(usage, 'output_tokens', '?')} stop={msg.stop_reason}")
            return text, msg.stop_reason, False
        except Exception as e:
            transient = self._is_transient(e)
            print(f"❌ [Physics QA] {label} {'transient ' if transient else ''}error: "
                  f"{type(e).__name__}: {e}")
            return None, None, transient

    # ==================================================================
    # RENDERING — existing QA frontend markup (same as Biology / SS)
    # ==================================================================

    @staticmethod
    def _inline(s: str) -> str:
        """Question / option text: allowed inline tags only."""
        return sanitize_answer_html(s).replace("<p>", "").replace("</p>", " ").strip()

    def _render_section(self, part: dict, questions: List[dict]) -> str:
        sid = part["section_id"]
        badge = f'{part["marks"]} mark{"s" if part["marks"] > 1 else ""}'
        items = []
        for i, q in enumerate(questions):
            num = part["start"] + i
            bb = ' <span class="mark-badge">Book-back</span>' if q.get("book_back") else ""
            head = (f'<p class="question"><strong>Q{num}.</strong> {self._inline(q["q"])} '
                    f'<span class="mark-badge">({badge})</span>{bb}</p>')
            if part["kind"] == "mcq":
                opts = "\n".join(f"    <span>{l}) {self._inline(o)}</span>"
                                 for l, o in zip("abcd", q["options"]))
                correct = q["options"]["abcd".index(q["answer"])]
                expl = (f'\n    <p class="answer-explanation"><em>{self._inline(q["explanation"])}</em></p>'
                        if q.get("explanation") else "")
                items.append(
                    f'<div class="qa-item">\n  {head}\n'
                    f'  <div class="mcq-options">\n{opts}\n  </div>\n'
                    f'  <div class="answer-reveal" style="display:none;">\n'
                    f'    <p class="answer"><strong>Answer:</strong> {q["answer"]}) {self._inline(correct)}</p>{expl}\n'
                    f'  </div>\n</div>'
                )
            else:
                svg = sanitize_svg(q.get("diagram_svg")) if part["marks"] == 5 else ""
                diagram = f'\n    <div class="qa-diagram">{svg}</div>' if svg else ""
                items.append(
                    f'<div class="qa-item">\n  {head}\n'
                    f'  <div class="answer-reveal" style="display:none;">\n'
                    f'    <div class="answer"><strong>Answer:</strong> {sanitize_answer_html(q["answer_html"])}</div>{diagram}\n'
                    f'  </div>\n</div>'
                )

        return (
            f'<div class="qa-section" id="{sid}">\n'
            f'  <div class="section-header">\n'
            f'    <h2>{html_lib.escape(part["title"])}</h2>\n'
            f'    <button class="show-section-btn"\n'
            f'            onclick="toggleSectionAnswers(this, \'{sid}\')"\n'
            f'            style="background:#2563eb; color:#fff; font-weight:700;\n'
            f'                   border:none; border-radius:6px; padding:6px 18px;\n'
            f'                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">\n'
            f'      📋 Show Answers\n'
            f'    </button>\n'
            f'  </div>\n'
            f'  <p class="section-note"><em>{html_lib.escape(part["note"])}</em></p>\n\n'
            + "\n\n".join(items) +
            "\n</div>"
        )


# ============================================================================
# Singleton — imported by physics_router
# ============================================================================

physics_qa_1112_builder = PhysicsQA1112Builder()