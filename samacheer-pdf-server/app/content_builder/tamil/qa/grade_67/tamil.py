"""
tamil.py (QA)
-------------
QA Builder for Samacheer Kalvi Tamil — Classes 6–7 (grade_67)

v0.1 — Oct 2026

PATTERN (agreed 21 Oct 2026) — EXACTLY 100 questions, see base.get_qa_parts():
  with memorisation units : I MCQ 1m × 40 | II 2m × 30 | III 3m × 20 | IV மனப்பாடம் × 10
  without                 : I MCQ 1m × 45 | II 2m × 35 | III 3m × 20
  Part IV is built in PYTHON from the printed memorisation lines (no model):
  write the lines / complete a line / the next line / fill the missing word.
  If fewer than 10 can be built, the shortfall moves to Part I.

EXACTLY 100 — same engine as Physics QA:
  1. small batches, generous max_tokens; the model returns JSON, Python
     validates, de-duplicates (Tamil-safe), numbers and renders
  2. truncated output is salvaged (every complete question kept)
  3. top-ups ask for exactly the missing number (+2), with the stems already
     asked; up to MAX_TOPUPS per part
  4. any part still short → generate() returns None (never ship a short bank)
  5. final check counts rendered qa-item blocks

TAMIL SPECIFICS
  - options labelled அ) ஆ) இ) ஈ); the model may answer "ஆ", "b" or the text
  - MCQ answer positions balanced in Python; book-back MCQs and options that
    refer to other options ("இரண்டும்", "அ, ஆ") keep their order
  - book-back items first in their part, copied exactly, badge "பாடநூல் வினா"
  - the lesson text (with its exercises and unit-end sections) is the only
    source; it is prompt-cached across all batches

CONTRACT: generate(text, metadata) -> str | None ; never raises; streaming;
mid-stream retries; no per-run state on self. Markup = the shared QA pattern
(qa-section, show-section-btn → toggleSectionAnswers, answer-reveal).
"""

import html as html_lib
import re
import time
from typing import Dict, List, Optional, Tuple

import anthropic
import httpx

from .....config import settings
from ...base import (
    QA_LABELS,
    QA_TOTAL_QUESTIONS,
    QA_MEMORISE_COUNT,
    TAMIL_QA_SYSTEM_PROMPT,
    get_qa_parts,
    get_qa_header,
    get_display_title,
    get_meta_line,
    normalize_source_text,
    split_lesson_parts,
    normalize_lesson_type,
    normalize_tamil,
    is_near_duplicate,
    extract_question_objects,
    sanitize_answer_html,
    strip_cjk,
)

try:  # qa_only may send raw text; v2 text from the Python team is already clean
    from .....services.section_detector import clean_noise
except Exception:  # pragma: no cover
    clean_noise = None

Q = QA_LABELS


# ============================================================================
# TUNABLES
# ============================================================================

MAX_TOPUPS = 3
TOPUP_SPARE = 2
REQUEST_TIMEOUT_S = 900.0
SDK_MAX_RETRIES = 3
STREAM_RETRY_BACKOFF_S = (10, 30, 60)
USED_STEMS_IN_PROMPT = 120

LETTERS = ["அ", "ஆ", "இ", "ஈ"]
_LETTER_TO_IDX = {"அ": 0, "ஆ": 1, "இ": 2, "ஈ": 3, "a": 0, "b": 1, "c": 2, "d": 3}

# which book-back items belong to which part
BOOK_BACK_BY_PART = {
    "mcq":   "the book's சரியான விடையைத் தேர்ந்தெடுத்து எழுதுக items (with their printed options)",
    "mark2": "the book's குறுவினா items, and its short items such as பொருத்துக / கோடிட்ட இடம் "
             "நிரப்புக / சொற்களைச் சொந்தத் தொடரில் அமைத்து எழுதுக turned into one question each",
    "mark3": "the book's சிறுவினா and சிந்தனை வினா items",
}


# ============================================================================
# TAMIL QA BUILDER
# ============================================================================

class TamilQA67Builder:

    discipline = "tamil"

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            max_retries=SDK_MAX_RETRIES,
            timeout=REQUEST_TIMEOUT_S,
        )
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Tamil QA Builder (67) v0.1 initialized — model: {self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """Never raises. Returns QA body HTML with exactly 100 questions, or None."""
        try:
            return self._generate(text, metadata or {})
        except Exception as e:
            print(f"❌ [Tamil QA] Unexpected error — returning None: {type(e).__name__}: {e}")
            return None

    def _generate(self, text: str, metadata: dict) -> Optional[str]:
        t0 = time.time()
        if not text or not text.strip():
            print("❌ [Tamil QA] Empty lesson text — aborting")
            return None
        if not metadata.get("tamil_text_version") and clean_noise is not None:
            text = clean_noise(text, subject="tamil")      # raw qa_only text only

        norm, report = normalize_source_text(text)          # idempotent safety net
        parts_text = split_lesson_parts(norm)
        memorise = metadata.get("memorise_blocks") or report["memorise_blocks"]
        memorise = [[str(l).strip() for l in b if str(l).strip()]
                    for b in memorise if isinstance(b, (list, tuple))]

        run = {
            "text": norm,
            "exercises": (parts_text["exercises"] + "\n\n" + parts_text["unit_end"]).strip(),
            "title": get_display_title(metadata),
            "meta_line": get_meta_line(metadata),
            "class_num": metadata.get("class", 6),
            "lesson_type": normalize_lesson_type(metadata.get("lesson_type")),
            "used_stems": [],
        }

        mem_items = self._build_memorise(memorise)
        qa_parts = get_qa_parts(len(mem_items))
        print(f"      [Tamil QA] Generating: {run['meta_line']} — {run['title']} ({len(norm)} chars, "
              f"{len(memorise)} memorisation unit(s) → {len(mem_items)} Part IV items)")
        print("         · plan: " + " | ".join(f"{p['key']} {p['count']}" for p in qa_parts))

        sections = [get_qa_header(run["title"], metadata)]
        total = 0
        for part in qa_parts:
            if part["kind"] == "memorise":
                questions = mem_items[: part["count"]]
            else:
                print(f"      [Tamil QA] {part['title']} — need {part['count']}")
                questions = self._generate_part(run, part)
            if len(questions) != part["count"]:
                print(f"         ❌ {part['title']}: only {len(questions)}/{part['count']} "
                      f"after top-ups — returning None (never ship a short bank)")
                return None
            sections.append(self._render_section(part, questions))
            total += len(questions)
            print(f"         ✅ {part['title']}: {len(questions)}/{part['count']}")

        html = "\n\n".join(sections)
        html, n_cjk = strip_cjk(html)
        n_items = html.count('<div class="qa-item">')
        if total != QA_TOTAL_QUESTIONS or n_items != QA_TOTAL_QUESTIONS:
            print(f"         ❌ Final count check failed: {n_items} rendered / {total} collected")
            return None
        if html.count("<div") != html.count("</div>"):
            print("         ❌ Final check failed: unbalanced divs")
            return None
        print(f"      [Tamil QA] ✅ Complete — {n_items} questions, {len(html)} chars, "
              f"{(time.time() - t0) / 60:.1f} min")
        return html

    # ==================================================================
    # PART IV — memorisation, built in Python from the printed lines
    # ==================================================================

    @staticmethod
    def _split_punct(word: str) -> Tuple[str, str]:
        m = re.match(r"^(.*?)([,.;:!?”\"’']*)$", word)
        return m.group(1), m.group(2)

    def _build_memorise(self, blocks: List[List[str]]) -> List[dict]:
        """
        Up to QA_MEMORISE_COUNT questions in four styles, taken round-robin over
        the memorisation units so every unit is used. Every line is the printed
        line; answers are the printed lines.
        """
        per_block = []
        for b in blocks:
            if not b:
                continue
            cands = []
            first_words = " ".join(b[0].split()[:2])
            cands.append({"q": f"{Q['write_lines']} “{first_words} …”",
                          "answer_html": "<br/>".join(html_lib.escape(l, quote=False) for l in b)})
            for l1, l2 in zip(b, b[1:]):
                cands.append({"q": f"{Q['next_line']} “{l1}”",
                              "answer_html": html_lib.escape(l2, quote=False)})
            for l in b[1:]:            # line 1's opening is already the "write the lines" prompt
                w = l.split()
                if len(w) >= 3:
                    half = " ".join(w[: (len(w) + 1) // 2])
                    cands.append({"q": f"{Q['complete']} “{half} …”",
                                  "answer_html": html_lib.escape(l, quote=False)})
            for l in b:
                w = l.split()
                for i in list(range(1, len(w))) + [0]:       # middle words first
                    word = w[i]
                    core, punct = self._split_punct(word)
                    if len(re.findall(r"[஀-௿]", core)) < 3:
                        continue
                    blanked = " ".join(w[:i] + ["______" + punct] + w[i + 1:])
                    cands.append({"q": f"{Q['fill_word']} “{blanked}”",
                                  "answer_html": html_lib.escape(core, quote=False)})
            per_block.append(cands)

        out, seen, k = [], set(), 0
        while len(out) < QA_MEMORISE_COUNT and any(k < len(c) for c in per_block):
            for cands in per_block:
                if k < len(cands) and len(out) < QA_MEMORISE_COUNT:
                    c = cands[k]
                    key = normalize_tamil(c["q"])
                    if key not in seen:
                        seen.add(key)
                        out.append(dict(c, book_back=False))
            k += 1
        return out

    # ==================================================================
    # PARTS I–III — batches, validation, dedupe, top-ups
    # ==================================================================

    def _generate_part(self, run: dict, part: dict) -> List[dict]:
        accepted: List[dict] = []
        for b_idx, size in enumerate(part["batches"]):
            label = f"{part['key']} batch {b_idx + 1}/{len(part['batches'])}"
            new = self._request(run, part, size, label, include_book_back=(b_idx == 0))
            added = self._accept(run, part, new, accepted, limit=part["count"])
            print(f"         · {label}: asked {size}, accepted {added} (total {len(accepted)})")

        for attempt in range(1, MAX_TOPUPS + 1):
            missing = part["count"] - len(accepted)
            if missing <= 0:
                break
            label = f"{part['key']} top-up {attempt}/{MAX_TOPUPS}"
            # short Tamil lessons repeat more as the bank fills — ask generously
            spare = max(TOPUP_SPARE, missing // 2)
            new = self._request(run, part, missing + spare, label,
                                include_book_back=False, topup=True)
            added = self._accept(run, part, new, accepted, limit=part["count"])
            print(f"         ↻ {label}: missing {missing}, accepted {added} (total {len(accepted)})")

        accepted.sort(key=lambda q: 0 if q.get("book_back") else 1)
        accepted = accepted[: part["count"]]
        if part["kind"] == "mcq":
            self._balance_mcq_answers(accepted)
        return accepted

    # Options that refer to other options must keep their order
    _OPTION_REF_RE = re.compile(
        r"இரண்டும்|அனைத்தும்|எதுவுமில்லை|எதுவும் இல்லை|மேற்கண்ட|இவை அனைத்தும்|"
        r"[அஆஇஈ]\s*(?:,|மற்றும்|உம்|அல்லது)\s*[அஆஇஈ]|"
        r"\b(?:both|neither|all|none|above)\b|\(\s*[a-dஅஆஇஈ]\s*\)",
        re.IGNORECASE)

    @classmethod
    def _balance_mcq_answers(cls, questions: List[dict]) -> None:
        counts = [0, 0, 0, 0]
        eligible = []
        for q in questions:
            if q.get("book_back") or any(cls._OPTION_REF_RE.search(o) for o in q["options"]):
                counts[q["answer"]] += 1
            else:
                eligible.append(q)
        for q in eligible:
            target = min(range(4), key=lambda i: (counts[i], i))
            i = q["answer"]
            q["options"][i], q["options"][target] = q["options"][target], q["options"][i]
            q["answer"] = target
            counts[target] += 1
        print("         · MCQ answer spread: " + " ".join(f"{LETTERS[i]}={counts[i]}" for i in range(4)))

    def _accept(self, run: dict, part: dict, new: List[dict],
                accepted: List[dict], limit: int) -> int:
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
        r"\s*[\(\[]\s*(பாடநூல்[^\)\]]{0,20}|book[\s-]*back[^\)\]]{0,30}|மதிப்பீடு[^\)\]]{0,20})[\)\]]\s*",
        re.IGNORECASE)
    _OPT_PREFIX_RE = re.compile(r"^\s*\(?\s*([அஆஇஈ]|[a-dA-D])\s*[).:]\s*")
    _BANNED_OPT_RE = re.compile(r"^(மேற்கண்ட\s*)?(அனைத்தும்|எதுவுமில்லை|எதுவும் இல்லை)$")

    @staticmethod
    def _plain(s) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(s or ""))).strip()

    @classmethod
    def _clean_stem(cls, stem: str) -> str:
        stem = re.sub(r"^\s*\d{1,3}\s*[.)]\s*", "", stem)          # model-added numbers
        return re.sub(r"\s{2,}", " ", cls._STEM_LABEL_RE.sub(" ", stem)).strip()

    @classmethod
    def _validate_mcq(cls, raw: dict) -> Optional[dict]:
        if not isinstance(raw, dict):
            return None
        stem = cls._plain(raw.get("q") or raw.get("question"))
        opts = raw.get("options")
        if not stem or not isinstance(opts, list) or len(opts) != 4:
            return None
        opts = [cls._OPT_PREFIX_RE.sub("", cls._plain(o)).strip() for o in opts]
        if any(not o for o in opts) or len({normalize_tamil(o) for o in opts}) != 4:
            return None
        book_back = bool(raw.get("book_back"))
        if not book_back and any(cls._BANNED_OPT_RE.match(normalize_tamil(o)) for o in opts):
            return None
        # answer as a letter ("ஆ", "ஆ) …", "b") or as the option's own text
        a = cls._plain(raw.get("answer")).strip("(). ")
        m = re.match(r"^([அஆஇஈ]|[a-dA-D])(?:[^\w஀-௿].*)?$", a)
        if m:
            idx = _LETTER_TO_IDX[m.group(1).lower() if m.group(1).isascii() else m.group(1)]
        else:
            hits = [i for i, o in enumerate(opts) if normalize_tamil(o) == normalize_tamil(a)]
            if len(hits) != 1:
                return None
            idx = hits[0]
        return {"q": cls._clean_stem(stem), "options": opts, "answer": idx,
                "explanation": cls._plain(raw.get("explanation")), "book_back": book_back}

    @classmethod
    def _validate_descriptive(cls, raw: dict, part: dict) -> Optional[dict]:
        if not isinstance(raw, dict):
            return None
        stem = cls._plain(raw.get("q") or raw.get("question"))
        ans = str(raw.get("answer_html") or raw.get("answer") or "").strip()
        min_len = {2: 15, 3: 40}.get(part["marks"], 15)        # Tamil characters
        if not stem or len(cls._plain(ans)) < min_len:
            return None
        return {"q": cls._clean_stem(stem), "answer_html": ans, "book_back": bool(raw.get("book_back"))}

    # ==================================================================
    # PROMPTS
    # ==================================================================

    def _request(self, run: dict, part: dict, n: int, label: str,
                 include_book_back: bool, topup: bool = False) -> List[dict]:
        prompt = self._build_prompt(run, part, n, include_book_back, topup)
        raw, stop = self._call(run, prompt, part["max_tokens"], label)
        if raw is None:
            return []
        if stop == "max_tokens":
            print(f"         ⚠️ {label}: cut off at max_tokens — keeping complete questions")
        return extract_question_objects(raw)

    def _build_prompt(self, run: dict, part: dict, n: int,
                      include_book_back: bool, topup: bool) -> str:
        used = run["used_stems"][-USED_STEMS_IN_PROMPT:]
        used_block = "\n".join(f"- {s[:140]}" for s in used) if used else "(none yet)"
        if part["kind"] == "mcq":
            schema = """{
  "questions": [
    {"q": "question in book Tamil", "options": ["option", "option", "option", "option"],
     "answer": "ஆ", "explanation": "one line in book Tamil — why", "book_back": false}
  ]
}"""
        else:
            schema = """{
  "questions": [
    {"q": "question in book Tamil", "answer_html": "complete answer in book Tamil", "book_back": false}
  ]
}"""
        if include_book_back and run["exercises"]:
            book_back_rule = (
                f"- FIRST include {BOOK_BACK_BY_PART[part['key']]} that are not already asked, "
                "copied exactly from BOOK EXERCISES below, with \"book_back\": true and your "
                "complete answer. Then fill the rest with new questions (\"book_back\": false).\n")
            ex_block = f"\nBOOK EXERCISES (exactly as in the lesson text):\n---\n{run['exercises']}\n---\n"
        else:
            book_back_rule = "- Write NEW questions (\"book_back\": false).\n"
            ex_block = ""
        marks = f"{part['marks']} {Q['mark']}"
        return f"""Generate questions for {part['title']} ({marks} each) of the question bank for
the Class {run['class_num']} Tamil lesson: {run['title']} ({run['meta_line']}).

Generate EXACTLY {n} questions.

WHAT TO ASK:
{part['guidance']}

ANSWER FORMAT:
{part['answer_rule']}

RULES:
{book_back_rule}- Spread questions across the WHOLE lesson — every part, its boxes, exercises
  and unit-end sections, not just the start.
- Do NOT repeat or rephrase any question already asked (list below).
- Copy book words and lines exactly. Answers only from the lesson text above.
{ex_block}
ALREADY ASKED (do not repeat or rephrase):
{used_block}

Return ONLY this JSON object (no prose, no code fences):
{schema}"""

    # ==================================================================
    # API CALL — streaming, cached system + lesson text, mid-stream retries
    # ==================================================================

    def _call(self, run: dict, prompt: str, max_tokens: int,
              label: str) -> Tuple[Optional[str], Optional[str]]:
        attempts = len(STREAM_RETRY_BACKOFF_S) + 1
        for attempt in range(1, attempts + 1):
            text, stop, retryable = self._call_once(run, prompt, max_tokens, label)
            if text is not None or not retryable:
                return text, stop
            if attempt < attempts:
                wait = STREAM_RETRY_BACKOFF_S[attempt - 1]
                print(f"         ↻ {label}: transient failure — retry {attempt}/{attempts - 1} in {wait}s")
                time.sleep(wait)
        print(f"❌ [Tamil QA] {label}: still failing after {attempts - 1} retries")
        return None, None

    @staticmethod
    def _is_transient(e: Exception) -> bool:
        if isinstance(e, (anthropic.APIConnectionError, httpx.TransportError)):
            return True
        if isinstance(e, anthropic.APIStatusError):
            code = getattr(e, "status_code", 0) or 0
            return code == 429 or code >= 500 or "overloaded" in str(e).lower()
        return False

    def _call_once(self, run: dict, prompt: str, max_tokens: int,
                   label: str) -> Tuple[Optional[str], Optional[str], bool]:
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=[{"type": "text", "text": TAMIL_QA_SYSTEM_PROMPT,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": [
                    {"type": "text",
                     "text": f"LESSON TEXT (the only source of content):\n---\n{run['text']}\n---",
                     "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": prompt},
                ]}],
            ) as stream:
                msg = stream.get_final_message()
            text = "".join(getattr(b, "text", "") for b in msg.content
                           if getattr(b, "type", "") == "text")
            usage = getattr(msg, "usage", None)
            if usage is not None:
                print(f"         · {label}: in={getattr(usage, 'input_tokens', '?')} "
                      f"cache_write={getattr(usage, 'cache_creation_input_tokens', 0) or 0} "
                      f"cached={getattr(usage, 'cache_read_input_tokens', 0) or 0} "
                      f"out={getattr(usage, 'output_tokens', '?')} stop={msg.stop_reason}")
            return text, msg.stop_reason, False
        except Exception as e:
            transient = self._is_transient(e)
            print(f"❌ [Tamil QA] {label} {'transient ' if transient else ''}error: "
                  f"{type(e).__name__}: {e}")
            return None, None, transient

    # ==================================================================
    # RENDERING — shared QA frontend markup
    # ==================================================================

    @staticmethod
    def _inline(s: str) -> str:
        return sanitize_answer_html(s).replace("<p>", "").replace("</p>", " ").strip()

    def _render_section(self, part: dict, questions: List[dict]) -> str:
        sid = part["section_id"]
        badge = (f"{part['marks']} {Q['mark']}" if part["marks"] else Q["memorise"])
        items = []
        for i, q in enumerate(questions):
            num = part["start"] + i
            bb = f' <span class="mark-badge">{Q["book_back"]}</span>' if q.get("book_back") else ""
            head = (f'<p class="question"><strong>{num}.</strong> {html_lib.escape(q["q"], quote=False)} '
                    f'<span class="mark-badge">({badge})</span>{bb}</p>')
            if part["kind"] == "mcq":
                opts = "\n".join(f"    <span>{LETTERS[j]}) {html_lib.escape(o, quote=False)}</span>"
                                 for j, o in enumerate(q["options"]))
                correct = q["options"][q["answer"]]
                expl = (f"<br/><em>{html_lib.escape(q['explanation'], quote=False)}</em>"
                        if q.get("explanation") else "")
                items.append(
                    f'<div class="qa-item">\n  {head}\n'
                    f'  <div class="mcq-options">\n{opts}\n  </div>\n'
                    f'  <div class="answer-reveal" style="display:none;">\n'
                    f'    <p class="answer"><strong>{Q["answer"]}:</strong> {LETTERS[q["answer"]]}) '
                    f'{html_lib.escape(correct, quote=False)}{expl}</p>\n'
                    f'  </div>\n</div>')
            else:
                ans = (q["answer_html"] if part["kind"] == "memorise"
                       else sanitize_answer_html(q["answer_html"]))
                items.append(
                    f'<div class="qa-item">\n  {head}\n'
                    f'  <div class="answer-reveal" style="display:none;">\n'
                    f'    <div class="answer"><strong>{Q["answer"]}:</strong> {ans}</div>\n'
                    f'  </div>\n</div>')
        return (
            f'<div class="qa-section" id="{sid}">\n'
            f'  <div class="section-header">\n'
            f'    <h2>{html_lib.escape(part["title"])}</h2>\n'
            f'    <button class="show-section-btn"\n'
            f'            onclick="toggleSectionAnswers(this, \'{sid}\')"\n'
            f'            style="background:#2563eb; color:#fff; font-weight:700;\n'
            f'                   border:none; border-radius:6px; padding:6px 18px;\n'
            f'                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">\n'
            f'      {Q["show_answers"]}\n'
            f'    </button>\n'
            f'  </div>\n'
            f'  <p class="section-note"><em>{html_lib.escape(part["note"])}</em></p>\n\n'
            + "\n\n".join(items) +
            "\n</div>"
        )


# ============================================================================
# Singleton — imported by the Tamil router
# ============================================================================

tamil_qa_67_builder = TamilQA67Builder()