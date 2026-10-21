"""
tamil.py (Content)
------------------
Content Builder for Samacheer Kalvi Tamil — Class 6 (grade_67)

v0.1 — Oct 2026

ONE SHARED BUILDER for all five lesson types (branches on
metadata["lesson_type"]); a type-specific file next to this one would
override a single type without touching this file.

DESIGN — the book text never passes through the model
  Python  → normalise the text (safety net; upstream already does it),
            split it into teaching / book exercises / unit-end
  Python  → render the TEACHING part straight from the text: headings,
            paragraphs, poem and kural lines, boxes, நூல்வெளி,
            சொல்லும் பொருளும் — every line copied exactly, HTML-escaped
  Call(s) → Exercise Converter (JSON) — one call for the book exercises,
            one for the unit-end sections (when the lesson has them).
            The model only CLASSIFIES each item (MCQ / fill / match / short
            answer …), copies its wording and gives the answer.
  Python  → validates every item, snaps copied wording back to the source
            line, checks that every exercise line of the book is covered,
            renders the interactive HTML with the shared assembler's class
            names, numbers data-question-id q1..qN on every <textarea>

LANGUAGE (TL decision): book text verbatim; labels and explanations in
Tamil; answers in book Tamil; English only as key-term support.
Unit-end sections stay on Content pages (they are book exercises).

MARKUP CONTRACT (from the real assembler pages + site JS)
  - exercise-section / exercise-title / ex-badge, mcq-item / mcq-options,
    answer-box (+ long), blank-input, true-false-item / tf-btn, match-table,
    exercise-table, section-heading, intro-box, content-note, do-you-know /
    dyk-title, glossary-section, bookback-controls, section-note
  - <textarea data-question-id="qN"> — read by lesson-viewer.js
    initAnswerTracker (the ONLY data-* attribute used)
  - show-answer-btn onclick="toggleAnswer(this)" immediately followed by
    <div class="answer-reveal" style="display:none;"> (helpers.js uses
    nextElementSibling; inline display:none because no <style> is allowed)
  - no <style>, <script>, id attributes; body HTML only — the wrapper adds
    the shell, Noto Sans Tamil, lang="ta", the Tamil title and meta line

BACKEND CONTRACT: generate(text, metadata) -> str | None ; never raises;
streaming; mid-stream retries; no per-run state on self.
"""

import difflib
import html as html_lib
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import anthropic
import httpx

from .....config import settings
from ...base import (
    CONTENT_LABELS,
    LESSON_TYPE_NAMES,
    normalize_source_text,
    split_lesson_parts,
    normalize_lesson_type,
    normalize_tamil,
    get_display_title,
    get_meta_line,
    strip_cjk,
    parse_json_response,
)

C = CONTENT_LABELS


# ============================================================================
# TUNABLES
# ============================================================================

MAX_TOKENS_EXERCISES = 20000
REQUEST_TIMEOUT_S = 900.0
SDK_MAX_RETRIES = 3
STREAM_RETRY_BACKOFF_S = (10, 30, 60)

MIN_COVERAGE = 0.85        # share of book exercise lines that must appear on the page
SNAP_MIN_RATIO = 0.80
VERSE_MAX_CHARS = 60       # a "short line" for poem / kural grouping

# Headings that may arrive WITHOUT ### in the extracted text
SECTION_HEADINGS = ["பாடலின் பொருள்", "தெரிந்து தெளிவோம்"]
BOX_HEADINGS = ["நூல்வெளி", "நூல் வெளி", "சொல்லும் பொருளும்"]
INTRO_HEADINGS = ["நுழையும் முன்", "நுழையும்முன்"]


# ============================================================================
# TAMIL CONTENT BUILDER
# ============================================================================

class TamilContent67Builder:

    discipline = "tamil"

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            max_retries=SDK_MAX_RETRIES,
            timeout=REQUEST_TIMEOUT_S,
        )
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Tamil Content Builder (67) v0.1 initialized — model: {self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """Never raises. Returns Content body HTML, or None on failure."""
        try:
            return self._generate(text, metadata or {})
        except Exception as e:
            print(f"❌ [Tamil Content] Unexpected error — returning None: {type(e).__name__}: {e}")
            return None

    def _generate(self, text: str, metadata: dict) -> Optional[str]:
        t0 = time.time()
        if not text or not text.strip():
            print("❌ [Tamil Content] Empty lesson text — aborting")
            return None

        norm, report = normalize_source_text(text)        # idempotent safety net
        parts = split_lesson_parts(norm)
        memorise = metadata.get("memorise_blocks") or report["memorise_blocks"]
        run: Dict[str, Any] = {
            "lesson_type": normalize_lesson_type(metadata.get("lesson_type")),
            "title": get_display_title(metadata),
            "meta_line": get_meta_line(metadata),
            "full_text": norm,
            "parts": parts,
            "memorise": [[str(l).strip() for l in b] for b in memorise if b],
            "qid": 0,            # data-question-id counter (per run, never on self)
            "mcq": 0,            # radio-group counter
        }
        print(f"      [Tamil Content] Generating: {run['meta_line']} — {run['title']} "
              f"(teaching {len(parts['teaching'])}, exercises {len(parts['exercises'])}, "
              f"unit-end {len(parts['unit_end'])} chars; text v{metadata.get('tamil_text_version', '?')}, "
              f"{len(report['symbol_ambiguous'])} ambiguous)")

        html_parts = [self._render_teaching(run, parts["teaching"])]

        exercise_blocks = [("exercises", parts["exercises"]), ("unit_end", parts["unit_end"])]
        rendered_any = False
        for key, block in exercise_blocks:
            if not block.strip():
                continue
            print(f"      [Tamil Content] Exercises: {key} ({len(block)} chars)...")
            sections = self._convert_exercises(run, block, key)
            if sections is None:
                print(f"         ❌ {key}: exercise conversion failed — aborting")
                return None
            if not rendered_any:
                html_parts.append(self._answer_controls())
                rendered_any = True
            html_parts.append(self._render_sections(run, sections))

        body = "\n\n".join(p for p in html_parts if p)
        body, n_cjk = strip_cjk(body)
        if n_cjk:
            print(f"      ⚠️ [Tamil Content] Removed {n_cjk} CJK character(s)")

        problems = self._contract_problems(body)
        if problems:
            print(f"         ❌ Contract check failed: {'; '.join(problems)}")
            return None

        mins = (time.time() - t0) / 60
        print(f"      [Tamil Content] ✅ Complete — {len(body)} chars, "
              f"{run['qid']} answer boxes, {run['mcq']} MCQs, {mins:.1f} min")
        return body

    # ==================================================================
    # TEACHING PART — rendered by Python, line by line
    # ==================================================================

    @staticmethod
    def _esc(s: Any) -> str:
        return html_lib.escape(str(s if s is not None else ""), quote=False)

    @staticmethod
    def _is_heading_line(line: str) -> Tuple[bool, str]:
        m = re.match(r"^\s*#{1,6}\s*(.*)$", line)
        if m:
            return True, m.group(1).strip().strip("*").strip()
        return False, line.strip()

    @staticmethod
    def _matches(line: str, names: List[str]) -> bool:
        n = re.sub(r"\s+", "", line)
        return any(n == re.sub(r"\s+", "", x) for x in names)

    def _is_verse_line(self, line: str) -> bool:
        s = line.strip()
        if not s or len(s) > VERSE_MAX_CHARS:
            return False
        if re.match(r"^(\d{1,2}[.)]|[அஆஇஈ]\))\s", s):
            return False
        return not s.endswith(":")

    def _textarea(self, run: dict, long: bool = False, rows: int = 0) -> str:
        """Every textarea carries data-question-id (lesson-viewer.js answer tracker)."""
        run["qid"] += 1
        ph = C["write_long"] if long else C["write_here"]
        rows_attr = f' rows="{rows}"' if rows else ""
        cls = "answer-box long" if long else "answer-box"
        return (f'<div class="{cls}"><textarea data-question-id="q{run["qid"]}" '
                f'placeholder="{ph}"{rows_attr}></textarea></div>')

    def _drop_title_lines(self, run: dict, lines: List[str]) -> List[str]:
        """The wrapper prints the title and meta line — drop the book's own title lines at the top."""
        drop_names = [run["title"], LESSON_TYPE_NAMES[run["lesson_type"]]]
        out, checked = [], 0
        for l in lines:
            if checked < 6 and l.strip():
                checked += 1
                _, t = self._is_heading_line(l)
                if (not t or re.match(r"^இயல்\s*\S+$", t) or self._matches(t, drop_names)
                        or re.match(r"^இயல்\s*\S+\s+", t) and self._matches(re.sub(r"^இயல்\s*\S+\s+", "", t), drop_names)):
                    continue
            out.append(l)
        return out

    def _render_teaching(self, run: dict, text: str) -> str:
        lines = self._drop_title_lines(run, (text or "").split("\n"))
        mem_lines = {normalize_tamil(l) for b in run["memorise"] for l in b}
        mem_ends = {normalize_tamil(b[-1]) for b in run["memorise"] if b}
        verse_ok = run["lesson_type"] in ("poem", "thirukural")

        out: List[str] = []
        box: Optional[str] = None          # open content-note / do-you-know / activity
        intro_open = False
        verse: List[str] = []

        def flush_verse():
            nonlocal verse
            if not verse:
                return
            if len(verse) == 1:
                out.append(f"<p>{self._esc(verse[0])}</p>")
            else:
                rendered = []
                for v in verse:
                    t = self._esc(v)
                    if normalize_tamil(v) in mem_ends:
                        t += f" <em>({C['memorise']})</em>"
                    rendered.append(t)
                out.append('<div class="content-note"><p>' + "<br/>".join(rendered) + "</p></div>")
            verse = []

        def close_box():
            nonlocal box, intro_open
            flush_verse()
            if box == "activity":
                out.append(self._textarea(run, long=True, rows=6))
            if box or intro_open:
                out.append("</div>")
            box, intro_open = None, False

        pending_box_title = False
        for raw in lines:
            line = raw.strip()
            if not line:
                flush_verse()
                continue
            is_h, h = self._is_heading_line(line)
            if is_h and not h:
                continue

            # box tags from the normaliser
            if line in ("[பெட்டிச் செய்தி]", "[செயல்பாடு]"):
                close_box()
                if line == "[செயல்பாடு]":
                    box = "activity"
                    out.append('<div class="exercise-section activity"><div class="exercise-title">'
                               f'<span class="ex-badge">{C["activity_badge"]}</span></div>')
                else:
                    box = "dyk"
                    out.append('<div class="do-you-know">')
                    pending_box_title = True
                continue
            if line in ("[/பெட்டிச் செய்தி]", "[/செயல்பாடு]"):
                close_box()
                continue

            if box == "dyk" and pending_box_title:
                pending_box_title = False
                if len(h) <= 40 and not h.endswith("."):
                    out.append(f'<div class="dyk-title">{self._esc(h)}</div>')
                    continue

            # headings
            if self._matches(h, INTRO_HEADINGS):
                close_box()
                out.append(f'<div class="intro-box"><p><strong>{self._esc(h)}</strong></p>')
                intro_open = True
                continue
            if self._matches(h, BOX_HEADINGS):
                close_box()
                out.append(f'<div class="content-note"><h3>{self._esc(h)}</h3>')
                box = "note"
                continue
            if is_h or self._matches(h, SECTION_HEADINGS):
                if box in ("dyk", "activity"):
                    flush_verse()
                    out.append(f"<p><strong>{self._esc(h)}</strong></p>")
                    continue
                close_box()
                out.append(f'<div class="section-heading"><h2>{self._esc(h)}</h2></div>')
                continue

            # body lines
            if verse_ok and self._is_verse_line(line) and box is None and not intro_open:
                verse.append(line)
                continue
            flush_verse()
            p = self._esc(line)
            if normalize_tamil(line) in mem_lines and normalize_tamil(line) in mem_ends:
                p += f" <em>({C['memorise']})</em>"
            out.append(f"<p>{p}</p>")
            if intro_open and box is None:
                # intro box holds the நுழையும் முன் paragraph only
                out.append("</div>")
                intro_open = False

        close_box()
        return "\n".join(out)

    # ==================================================================
    # EXERCISES — model classifies and answers, Python renders
    # ==================================================================

    _EX_SYSTEM = (
        "You convert Samacheer Kalvi Class 6 Tamil book exercises into structured JSON. "
        "Copy every heading, question, option and item EXACTLY as in the text — never "
        "correct spellings, never paraphrase, never skip an item, never add one. Answers "
        "are in book (written) Tamil and come only from the lesson text. Return ONLY valid "
        "JSON starting with {. No markdown, no code fences, no CJK characters, no Tamil "
        "written in English letters."
    )

    def _exercise_prompt(self, run: dict, block: str, key: str) -> str:
        where = ("the book exercises at the end of the lesson (கற்பவை கற்றபின், மதிப்பீடு …)"
                 if key == "exercises" else
                 "the unit-end sections (மொழியை ஆள்வோம், மொழியோடு விளையாடு, செயல் திட்டம், "
                 "நிற்க அதற்குத் தக, என் பொறுப்புகள், glossary …)")
        return f"""Convert {where} of this lesson into JSON for an interactive page.

Lesson : {run['title']}
Meta   : {run['meta_line']}

The text is already cleaned: ________ is a blank to fill, + and = are printed
symbols, அ) ஆ) இ) ஈ) are MCQ options, [பெட்டிச் செய்தி] … [/பெட்டிச் செய்தி] is
a boxed note, [செயல்பாடு] … [/செயல்பாடு] an activity box.

ITEM TYPES — choose one for every item:
- "mcq"      : a question with printed options (அ ஆ இ ஈ). "options" = the option
               texts WITHOUT their letters; "answer" = "அ" | "ஆ" | "இ" | "ஈ".
- "fill"     : a sentence with ________ blank(s). "answer" = the word(s) for
               the blank(s), separated by " / " if more than one.
- "word"     : a one-word or one-line answer without a printed blank (join /
               split words, opposite word, a word from the poem …). "answer" = it.
- "match"    : match the following. "pairs" = [[left, right], …] AS PRINTED
               (right column in its printed order); "answer" = "1 - ஆ, 2 - அ, …".
- "truefalse": "answer" = "சரி" or "தவறு" (+ the corrected sentence if தவறு).
- "short"    : குறுவினா / short written answer (1-3 sentences). "answer" =
               a model answer in book Tamil.
- "long"     : சிறுவினா / longer written answer. "answer" = model answer
               (4-6 sentences) in book Tamil.
- "thinking" : சிந்தனை வினா / open question. "answer" = what kinds of answers to
               accept (1-2 sentences).
- "activity" : a task to do, speak, draw, collect, write freely (கற்பவை கற்றபின்,
               செயல் திட்டம், speak for a minute, write a letter …). "answer" = "".
- "text"     : lines that are not questions (instructions, pledges like
               நிற்க அதற்குத் தக, என் பொறுப்புகள், a model letter, a word list
               that is only for reading). Put the lines in "lines". "answer" = "".
- "glossary" : a word list with meanings (e.g. Tamil – English). "pairs" =
               [[word, meaning], …] exactly as printed.

RULES:
- "heading": the section heading EXACTLY as printed (e.g. "சரியான விடையைத்
  தேர்ந்தெடுத்து எழுதுக."). "group": the top heading it belongs to
  (e.g. "மதிப்பீடு", "கற்பவை கற்றபின்", "மொழியை ஆள்வோம்") — same text for all
  its sub-sections.
- "num": the item's number or letter as printed ("1.", "அ.") or "".
- "q": the question / item text EXACTLY as printed, without its number.
- Every printed item appears ONCE, in book order. Do not skip items.
- If the lesson text does not settle an answer, write "ஆசிரியர் கையேட்டுடன்
  சரிபார்க்கவும்." as the answer.

Return ONLY this JSON:
{{
  "sections": [
    {{
      "group": "மதிப்பீடு",
      "heading": "...",
      "items": [
        {{"type": "mcq", "num": "1.", "q": "...", "options": ["...", "...", "...", "..."], "answer": "ஆ"}},
        {{"type": "fill", "num": "2.", "q": "... ________ ...", "answer": "..."}},
        {{"type": "match", "num": "", "q": "", "pairs": [["...", "..."]], "answer": "1 - ஆ, 2 - அ"}},
        {{"type": "text", "num": "", "q": "", "lines": ["...", "..."], "answer": ""}}
      ]
    }}
  ]
}}

TEXT TO CONVERT:
---
{block}
---"""

    def _convert_exercises(self, run: dict, block: str, key: str) -> Optional[List[dict]]:
        prompt = self._exercise_prompt(run, block, key)
        feedback = ""
        best: Optional[List[dict]] = None
        best_cov = -1.0
        for attempt in (1, 2):
            raw, stop = self._call(self._EX_SYSTEM, run, prompt + feedback,
                                   MAX_TOKENS_EXERCISES, f"Exercises {key} #{attempt}")
            if raw is None:
                return best
            if stop == "max_tokens":
                print(f"         ⚠️ {key}: cut off at max_tokens")
                feedback = ("\n\nIMPORTANT: Your previous answer was cut off. Keep model "
                            "answers SHORT (one sentence) so the whole JSON fits. Never "
                            "shorten copied book text.")
                continue
            try:
                data = parse_json_response(raw)
            except ValueError as e:
                print(f"         ⚠️ {key}: invalid JSON ({e}) — retrying once")
                feedback = ("\n\nIMPORTANT: Your previous answer was not valid JSON. Return "
                            "ONLY one valid JSON object — double quotes, no trailing commas.")
                continue
            sections = self._validate_sections(run, data, block)
            if not sections:
                feedback = "\n\nIMPORTANT: Your previous answer had no usable sections."
                continue
            cov, missing = self._coverage(run, sections, block)
            print(f"         · {key}: {sum(len(s['items']) for s in sections)} items in "
                  f"{len(sections)} sections, coverage {cov:.0%}")
            if cov > best_cov:
                best, best_cov = sections, cov
            if cov >= MIN_COVERAGE:
                return sections
            print(f"         ⚠️ {key}: {len(missing)} book line(s) missing, e.g. {missing[:2]} — retrying")
            feedback = ("\n\nIMPORTANT: Your previous answer SKIPPED these printed lines. "
                        "Include every item:\n" + "\n".join(f"- {m}" for m in missing[:25]))
        if best is not None:
            print(f"         ⚠️ {key}: keeping best attempt (coverage {best_cov:.0%})")
        return best

    # ---------- validation ----------

    @staticmethod
    def _str(x) -> str:
        s = re.sub(r"<[^>]+>", "", str(x if x is not None else ""))
        return html_lib.unescape(re.sub(r"\s+", " ", s)).strip()

    def _snap(self, text: str, src_lines: List[str]) -> str:
        """Use the source's own version of a copied line when it is a near match."""
        if not text:
            return text
        n = normalize_tamil(text)
        cores = [re.sub(r"^(\d{1,2}[.)]|[அஆஇஈ]\))\s*", "",
                        re.sub(r"^#{1,6}\s*", "", s).strip("*").strip())
                 for s in src_lines]
        for core in cores:
            if normalize_tamil(core) == n:
                return core
        best = difflib.get_close_matches(text, cores, n=1, cutoff=SNAP_MIN_RATIO)
        return best[0] if best else text

    _TYPES = {"mcq", "fill", "word", "match", "truefalse", "short", "long",
              "thinking", "activity", "text", "glossary"}
    _LETTERS = ["அ", "ஆ", "இ", "ஈ", "உ"]

    def _validate_sections(self, run: dict, data: Any, block: str) -> List[dict]:
        if not isinstance(data, dict) or not isinstance(data.get("sections"), list):
            return []
        src_lines = [l.strip() for l in block.split("\n") if l.strip()]
        out = []
        for s in data["sections"]:
            if not isinstance(s, dict):
                continue
            items = []
            for it in s.get("items") or []:
                if not isinstance(it, dict):
                    continue
                t = self._str(it.get("type")).lower()
                if t not in self._TYPES:
                    t = "short"
                q = self._snap(self._str(it.get("q")), src_lines)
                item = {"type": t, "num": self._str(it.get("num")), "q": q,
                        "answer": self._str(it.get("answer"))}
                if t == "mcq":
                    opts = [self._snap(re.sub(r"^\s*[அஆஇஈஉa-dA-D][).]\s*", "", self._str(o)), src_lines)
                            for o in (it.get("options") or []) if self._str(o)]
                    if not (2 <= len(opts) <= 5):
                        item["type"] = "short"          # keep the item, lose the radios
                    else:
                        item["options"] = opts
                        a = item["answer"].strip("() .")
                        if a[:1] in self._LETTERS[:len(opts)]:
                            item["answer_idx"] = self._LETTERS.index(a[:1])
                        else:
                            hits = [i for i, o in enumerate(opts) if normalize_tamil(o) == normalize_tamil(a)]
                            item["answer_idx"] = hits[0] if len(hits) == 1 else None
                if t in ("match", "glossary"):
                    pairs = []
                    lab = r"^\s*(\d{1,2}|[அஆஇஈஉ])[.)]\s*"
                    for p in it.get("pairs") or []:
                        if isinstance(p, list) and len(p) >= 2:
                            pairs.append([self._snap(re.sub(lab, "", self._str(p[0])), src_lines),
                                          self._snap(re.sub(lab, "", self._str(p[1])), src_lines)])
                    if not pairs:
                        item["type"] = "text"
                        item["lines"] = [q] if q else []
                    item["pairs"] = pairs
                if t == "text" or item["type"] == "text":
                    lines = it.get("lines") or ([q] if q else [])
                    item["lines"] = [self._snap(self._str(l), src_lines) for l in lines if self._str(l)]
                if item["type"] not in ("text", "glossary", "match") and not item["q"]:
                    continue
                if item["type"] == "text" and not item.get("lines"):
                    continue
                items.append(item)
            if items:
                out.append({"group": self._str(s.get("group")),
                            "heading": self._snap(self._str(s.get("heading")), src_lines),
                            "items": items})
        return out

    def _coverage(self, run: dict, sections: List[dict], block: str) -> Tuple[float, List[str]]:
        """Share of the book's exercise lines (2+ words) that appear in the converted items."""
        parts = []
        for s in sections:
            parts += [s["group"], s["heading"]]
            for it in s["items"]:
                parts += [it["num"], it["q"]] + it.get("options", []) + it.get("lines", [])
                for p in it.get("pairs", []):
                    parts += p
        page = normalize_tamil(" ".join(parts))
        page_words = set(page.split())
        lines, missing = [], []
        for l in block.split("\n"):
            l = l.strip()
            if l.startswith("[") and l.endswith("]"):
                continue
            core = re.sub(r"^(#{1,6}\s*)?(\d{1,2}[.)]|[அஆஇஈ]\))?\s*", "", l)
            # match lines print both columns: "விளைவுக்கு அ) பால்" — drop inline labels
            core = re.sub(r"\s(\d{1,2}|[அஆஇஈஉ])[.)]\s", " ", core)
            n = normalize_tamil(core)
            words = n.split()
            if len(words) < 2:
                continue
            lines.append(n)
            if n in page:
                continue
            if sum(w in page_words for w in words) / len(words) >= 0.9:
                continue                    # same words, split across fields
            missing.append(core[:80])
        if not lines:
            return 1.0, []
        return (len(lines) - len(missing)) / len(lines), missing

    # ---------- rendering ----------

    def _answer_controls(self) -> str:
        return ('<div class="bookback-controls">'
                f'<button onclick="showAllAnswers()">{C["show_all"]}</button>'
                f'<button onclick="hideAllAnswers()">{C["hide_all"]}</button>'
                "</div>\n"
                f'<p class="section-note"><em>{C["answers_note"]}</em></p>')

    def _reveal(self, answer: str) -> str:
        if not answer:
            return ""
        return (f'<button class="show-answer-btn" onclick="toggleAnswer(this)">{C["show_answer"]}</button>'
                f'<div class="answer-reveal" style="display:none;"><p><strong>{C["answer"]}:</strong> '
                f"{self._esc(answer)}</p></div>")

    def _stem(self, it: dict) -> str:
        num = f"{self._esc(it['num'])} " if it["num"] else ""
        return f"<strong>{num}</strong>{self._esc(it['q'])}" if num else self._esc(it["q"])

    def _with_blanks(self, text: str) -> str:
        """Replace printed blanks (____) with inputs; escape the rest."""
        pieces = re.split(r"_{3,}", text)
        inp = (f'<input class="blank-input" type="text" placeholder="{C["blank"]}" '
               f'style="width:120px;">')
        return inp.join(self._esc(p) for p in pieces)

    def _render_item(self, run: dict, it: dict) -> str:
        t = it["type"]
        if t == "mcq":
            run["mcq"] += 1
            name = f"m{run['mcq']}"
            opts = "\n".join(
                f'<label><input type="radio" name="{name}" value="{i}"> '
                f'{self._LETTERS[i]}) {self._esc(o)}</label>'
                for i, o in enumerate(it["options"]))
            ans = it["answer"]
            if it.get("answer_idx") is not None:
                ans = f"{self._LETTERS[it['answer_idx']]}) {it['options'][it['answer_idx']]}"
            return (f'<div class="mcq-item"><p>{self._stem(it)}</p>\n'
                    f'<div class="mcq-options">\n{opts}\n</div>\n{self._reveal(ans)}</div>')
        if t == "fill":
            num = f"<strong>{self._esc(it['num'])}</strong> " if it["num"] else ""
            body = self._with_blanks(it["q"])
            if "blank-input" not in body:
                body += (f' <input class="blank-input" type="text" placeholder="{C["blank"]}" '
                         f'style="width:120px;">')
            return f'<div style="margin-bottom:20px;"><p>{num}{body}</p>{self._reveal(it["answer"])}</div>'
        if t == "word":
            return (f'<div style="margin-bottom:20px;"><p>{self._stem(it)} '
                    f'<input class="blank-input" type="text" placeholder="{C["blank"]}" '
                    f'style="width:160px;"></p>{self._reveal(it["answer"])}</div>')
        if t == "truefalse":
            return (f'<div class="true-false-item"><span>{self._stem(it)}</span>'
                    f'<button class="tf-btn true-btn">{C["true"]}</button>'
                    f'<button class="tf-btn false-btn">{C["false"]}</button></div>'
                    f'{self._reveal(it["answer"])}')
        if t == "match":
            rows = "\n".join(
                f"<tr><td>{i}. {self._esc(l)}</td><td>{self._LETTERS[i - 1] if i <= 5 else i}) {self._esc(r)}</td>"
                f'<td><input class="blank-input" type="text" placeholder="{C["match_here"]}" '
                f'style="width:120px;"></td></tr>'
                for i, (l, r) in enumerate(it["pairs"], start=1))
            head = f"<p>{self._stem(it)}</p>" if it["q"] else ""
            return f'{head}<table class="match-table">\n{rows}\n</table>{self._reveal(it["answer"])}'
        if t == "glossary":
            rows = "\n".join(f"<tr><td>{self._esc(a)}</td><td>{self._esc(b)}</td></tr>"
                             for a, b in it["pairs"])
            return (f'<table class="exercise-table">\n<tr><th>{C["glossary_ta"]}</th>'
                    f'<th>{C["glossary_en"]}</th></tr>\n{rows}\n</table>')
        if t == "text":
            return "\n".join(f"<p>{self._esc(l)}</p>" for l in it["lines"])
        if t == "activity":
            return (f'<div style="margin-bottom:20px;"><p>{self._stem(it)}</p>'
                    f'{self._textarea(run, long=True, rows=6)}</div>')
        long = t == "long"
        return (f'<div style="margin-bottom:20px;"><p>{self._stem(it)}</p>'
                f'{self._textarea(run, long=long, rows=6 if long else 0)}'
                f'{self._reveal(it["answer"])}</div>')

    def _render_sections(self, run: dict, sections: List[dict]) -> str:
        out, group = [], None
        for s in sections:
            if s["group"] and s["group"] != group:
                group = s["group"]
                out.append(f'<div class="section-heading"><h2>{self._esc(group)}</h2></div>')
            kinds = {it["type"] for it in s["items"]}
            is_activity = kinds <= {"activity", "text"} and "activity" in kinds
            if kinds == {"glossary"}:
                out.append(f'<div class="glossary-section"><h3>{self._esc(s["heading"] or group)}</h3>\n'
                           + "\n".join(self._render_item(run, it) for it in s["items"]) + "\n</div>")
                continue
            if kinds == {"text"}:            # pledges, instructions, model letters: not an exercise
                head = (f"<h3>{self._esc(s['heading'])}</h3>\n"
                        if s["heading"] and s["heading"] != group else "")
                out.append('<div class="content-note">\n' + head
                           + "\n".join(self._render_item(run, it) for it in s["items"]) + "\n</div>")
                continue
            badge = C["activity_badge"] if is_activity else C["exercise_badge"]
            cls = "exercise-section activity" if is_activity else "exercise-section"
            title = self._esc(s["heading"]) if s["heading"] and s["heading"] != group else ""
            out.append(f'<div class="{cls}">\n<div class="exercise-title">'
                       f'<span class="ex-badge">{badge}</span> {title}</div>\n'
                       + "\n".join(self._render_item(run, it) for it in s["items"])
                       + "\n</div>")
        return "\n".join(out)

    # ---------- final checks ----------

    def _contract_problems(self, body: str) -> List[str]:
        problems = []
        if re.search(r"<(style|script|html|head|body)\b", body, re.IGNORECASE):
            problems.append("forbidden tag")
        if re.search(r'\sid\s*=', body):
            problems.append("id attribute")
        bad_data = set(re.findall(r"\s(data-[\w-]+)\s*=", body)) - {"data-question-id"}
        if bad_data:
            problems.append(f"unexpected data-* {sorted(bad_data)}")
        if body.count("<div") != body.count("</div>"):
            problems.append(f"divs {body.count('<div')}/{body.count('</div>')}")
        n_btn, n_rev = body.count('class="show-answer-btn"'), body.count('class="answer-reveal"')
        if n_btn != n_rev:
            problems.append(f"{n_btn} answer buttons vs {n_rev} answer blocks")
        qids = re.findall(r'data-question-id="q(\d+)"', body)
        if qids != [str(i) for i in range(1, len(qids) + 1)]:
            problems.append("data-question-id not q1..qN in order")
        if re.search(r"<textarea(?![^>]*data-question-id)", body):
            problems.append("textarea without data-question-id")
        return problems

    # ==================================================================
    # API CALLS — streaming, cached system + lesson text, mid-stream retries
    # ==================================================================

    def _call(self, system: str, run: dict, prompt: str, max_tokens: int,
              label: str) -> Tuple[Optional[str], Optional[str]]:
        attempts = len(STREAM_RETRY_BACKOFF_S) + 1
        for attempt in range(1, attempts + 1):
            text, stop, retryable = self._call_once(system, run, prompt, max_tokens, label)
            if text is not None or not retryable:
                return text, stop
            if attempt < attempts:
                wait = STREAM_RETRY_BACKOFF_S[attempt - 1]
                print(f"         ↻ {label}: transient failure — retry {attempt}/{attempts - 1} in {wait}s")
                time.sleep(wait)
        print(f"❌ [Tamil Content] {label}: still failing after {attempts - 1} retries")
        return None, None

    @staticmethod
    def _is_transient(e: Exception) -> bool:
        if isinstance(e, (anthropic.APIConnectionError, httpx.TransportError)):
            return True
        if isinstance(e, anthropic.APIStatusError):
            code = getattr(e, "status_code", 0) or 0
            return code == 429 or code >= 500 or "overloaded" in str(e).lower()
        return False

    def _call_once(self, system: str, run: dict, prompt: str, max_tokens: int,
                   label: str) -> Tuple[Optional[str], Optional[str], bool]:
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=[{"type": "text", "text": system,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": [
                    {"type": "text",
                     "text": f"FULL LESSON TEXT (for answers only):\n---\n{run['full_text']}\n---",
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
            print(f"❌ [Tamil Content] {label} {'transient ' if transient else ''}error: "
                  f"{type(e).__name__}: {e}")
            return None, None, transient


# ============================================================================
# Singleton — imported by the Tamil router
# ============================================================================

tamil_content_67_builder = TamilContent67Builder()