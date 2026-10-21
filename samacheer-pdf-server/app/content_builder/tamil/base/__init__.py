"""
tamil/base/__init__.py
----------------------
Shared constants and helpers for the Tamil LP and QA builders (grade_67).

Imported by:
    tamil/lp/grade_67/tamil.py   (tamil_lp_67_builder)
    tamil/qa/grade_67/tamil.py   (tamil_qa_67_builder)   — QA helpers added later

DO NOT add API calls or builder classes here. This file holds ONLY:
    - fixed Tamil labels and prompt constants
    - pure helper functions (source-text normalisation, cleaning, validation,
      repair, JSON parsing)

DECOUPLING NOTE (team convention):
Tamil keeps its own copy of clean() / balance_divs() etc. Nothing here is
imported from ss/base, biology/base or physics/base.

SOURCE OF TRUTH FOR TEACHING STYLE:
Manual LP "Class 6 Tamil · Term 1 · Unit 1 தமிழ்த்தேன்" (26 periods), used as a
content-agnostic TEMPLATE for every Class 6 Tamil lesson, plus the TL
decisions of 20 Oct 2026:
    1. Language: spoken Tamil for teacher talk; book content in written Tamil
       exactly as in the extracted text; English only as support (glosses on
       the hook, the main explanation of a new idea and task instructions;
       key-term English once, on the word wall). Neutral classroom Tamil, no
       dialect, no slang, no Tamil in English letters. All fixed labels Tamil.
    2. One CFU per period inside சரிபார்த்தலும் நிறைவும் (two oral questions with
       expected answers in book Tamil). CCQs only in கற்கண்டு (grammar)
       lessons: one per new grammar term.
    3. நிறைவு வினா (exit slip) every period; homework once, at the end of the
       lesson, taken only from the book's own exercises.
    4. Teach textbook content as printed; the teacher adds no religious
       examples of their own.
    5. LP plans only the lesson itself: unit-end sections are cut off.
    6. About 6–10 lines per block; exact teacher lines for the hook and every
       question, with expected answers.

PERIOD SHAPE (manual LP "The 30-minute period"):
    ஆர்வமூட்டல் 0–4 | கற்பித்தல் 4–13 | செயல்பாடு 13–23 | சரிபார்த்தலும் நிறைவும் 23–30
    mapped to lp-section-opening / -main / -student-task / -closing
    (lp-section-intro is not used).

WEB CONTRACT (from ai_converter._wrap_html + lesson-viewer.js):
    - Every period starts with EXACTLY  <div class="lp-day-block">
    - The period title lives INSIDE the day block
    - One top-level  <div class="assessment-block">  AFTER the last period
    - Only classes that exist in content-styles.css (see ALLOWED_CLASSES)
    - Tables: maximum 3 columns

v0.1 — Oct 2026
"""

import json
import re
import unicodedata
from typing import Dict, List, Optional, Tuple


# ============================================================================
# MARKERS (backend searches for these to find lessons needing a re-run)
# ============================================================================

LP_DAY_FAILED_MARKER    = "<!-- LP_DAY_FAILED -->"
LP_DAY_TRUNCATED_MARKER = "<!-- LP_DAY_TRUNCATED -->"

DAY_BLOCK_OPEN        = '<div class="lp-day-block">'
ASSESSMENT_BLOCK_OPEN = '<div class="assessment-block">'

PERIOD_MINUTES = 30


# ============================================================================
# FIXED TAMIL LABELS — one list, used by prompts AND checks
# (TL decision 1: all fixed LP labels in Tamil, no English beside them)
# ============================================================================

LABELS: Dict[str, str] = {
    # --- approved by TL, 20 Oct 2026 ---
    "period":          "பாடவேளை",               # "பாடவேளை 1 / 4 — [தலைப்பு]"
    "hook":            "ஆர்வமூட்டல்",
    "teach":           "கற்பித்தல்",
    "do":              "செயல்பாடு",
    "close":           "சரிபார்த்தலும் நிறைவும்",
    "exit_slip":       "நிறைவு வினா",
    "objectives":      "கற்றல் நோக்கங்கள்",
    "word_wall":       "சொல் சுவர்",
    "materials":       "துணைக்கருவிகள்",
    "homework":        "வீட்டுப்பாடம்",
    "assessment":      "மதிப்பீட்டுக் குறிப்புகள்",
    "teacher":         "ஆசிரியர்",
    "assessment_tab":  "மதிப்பீடு",              # tab text is set by _wrap_html (Python team)

    # --- PROPOSED, awaiting TL "ok" (needed by the markup) ---
    "cfu":             "சரிபார்ப்பு வினாக்கள்",
    "question":        "வினா",
    "expected_answer": "எதிர்பார்க்கும் விடை",
    "ccq":             "கருத்துச் சரிபார்ப்பு",
    "book_lines":      "பாடநூல் வரிகள்",
    "minutes":         "நிமி",
    "cfu_wait":        "முடிவு செய்யுங்கள்: அடுத்த பாடவேளைக்குச் செல்லலாமா, மீண்டும் கற்பிக்கலாமா?",
    "ccq_wait":        "தவறாக இருந்தால்: இந்த ஒரு கருத்தை உடனே மீண்டும் விளக்குங்கள்.",
    "next_period":     "அடுத்த பாடவேளை",
    "part":            "பகுதி",
}

# Preamble part titles (PROPOSED, awaiting TL "ok")
PREAMBLE_TITLES: Dict[str, str] = {
    "overview":  "பாடம் ஒரு பார்வை",
    "objectives": LABELS["objectives"],
    "word_wall":  LABELS["word_wall"],
    "plan":       "பாடவேளை வாரியான திட்டம்",
    "approach":   "கற்பிக்கும் முறை",
    "materials":  LABELS["materials"],
}

# Assessment block headings (PROPOSED, awaiting TL "ok")
ASSESSMENT_TITLES: Dict[str, str] = {
    "answers":      "சரியான விடைகள்",
    "short":        "குறுவினா — மாதிரி விடைகள்",
    "thinking":     "சிந்தனை வினா — ஏற்கத்தக்க விடைகள்",
    "recitation":   "ஒப்புவித்தல் சரிபார்ப்பு",
    "rule_example": "விதிக்கு ஓர் எடுத்துக்காட்டு",
    "diff":         "வேறுபடுத்திக் கற்பித்தல்",
    "diff_support": "கூடுதல் உதவி தேவைப்படுவோர்",
    "diff_stretch": "கூடுதல் சவால்",
    "check_note":   "ஆசிரியர் கையேட்டுடன் சரிபார்க்கவும்.",
}


# ============================================================================
# LESSON TYPES — printed section names (TL: meta line uses the book's words)
# ============================================================================

LESSON_TYPE_NAMES: Dict[str, str] = {
    "poem":          "கவிதைப்பேழை",
    "prose":         "உரைநடை உலகம்",
    "supplementary": "விரிவானம்",
    "grammar":       "கற்கண்டு",
    "thirukural":    "வாழ்வியல்",
}

_LESSON_TYPE_ALIASES = {
    "poetry": "poem", "kavithai": "poem",
    "supplementary_reader": "supplementary", "supplementary reading": "supplementary",
    "thirukkural": "thirukural", "kural": "thirukural",
}

DEFAULT_LESSON_TYPE = "prose"


def normalize_lesson_type(value) -> str:
    """Map metadata['lesson_type'] (English key or printed Tamil name) to a key."""
    raw = str(value or "").strip()
    key = raw.lower().replace("-", "_")
    if key in LESSON_TYPE_NAMES:
        return key
    if key in _LESSON_TYPE_ALIASES:
        return _LESSON_TYPE_ALIASES[key]
    nraw = re.sub(r"\s+", "", unicodedata.normalize("NFC", raw))
    for k, name in LESSON_TYPE_NAMES.items():
        if nraw and nraw == re.sub(r"\s+", "", name):
            return k
    return DEFAULT_LESSON_TYPE


def get_meta_line(metadata: dict) -> str:
    """'வகுப்பு 6 | தமிழ் | இயல் 1 | கவிதைப்பேழை' (TL format, book's own words)."""
    md = metadata or {}
    ltype = normalize_lesson_type(md.get("lesson_type"))
    parts = [f"வகுப்பு {md.get('class', 6)}", "தமிழ்"]
    if md.get("unit") not in (None, ""):
        parts.append(f"இயல் {md.get('unit')}")
    parts.append(LESSON_TYPE_NAMES[ltype])
    return " | ".join(parts)


def get_display_title(metadata: dict) -> str:
    """
    Prefer metadata['display_title'] (Tamil title from the curriculum JSON).
    The filename-style lesson_title cannot be turned into a Tamil title, so
    the fallback is a safe generic one.
    """
    title = (metadata or {}).get("display_title")
    if title and str(title).strip():
        return re.sub(r"[<>]", "", str(title).strip())
    return "தமிழ்ப் பாடம்"


# ============================================================================
# CSS CLASSES THAT ARE ACTUALLY STYLED — use ONLY these
# ============================================================================

ALLOWED_CLASSES = [
    "lp-day-block", "lp-day-title", "lp-day-meta",
    "lp-section-opening", "lp-section-main",
    "lp-section-student-task", "lp-section-closing",
    "lp-section-label", "lp-time",
    "lp-teacher-says",
    "cfu-block", "ccq-block", "cfu-wait-note",
    "board-work", "formula-box", "common-mistakes",
    "vocab-block", "diff-block", "diff-table",
    "assessment-block",
]


# ============================================================================
# SOURCE TEXT — undo the read-aloud EPUB spellings (deterministic, in Python)
# ============================================================================
#
# The EPUB is an accessibility version: some printed symbols arrive as words.
#   டேஷ்                          -> ________ (a blank)
#   கூட்டல் / பெருக்கல் / கழித்தல் / வகுத்தல் / சமம்   -> + × − ÷ =
#        ONLY where they sit between numbers or word parts like a symbol,
#        never when they are ordinary words in a sentence
#   "<line> மனப்பாடப் பகுதி"        -> label removed, line recorded as memorise
#   பெட்டிச் செய்தி ஆரம்பம் … முடிவு  -> [பெட்டிச் செய்தி] … [/பெட்டிச் செய்தி]
#   செயல்பாடு ஆரம்பம் … முடிவு       -> [செயல்பாடு] … [/செயல்பாடு]
#   "1," at the start of a line   -> "1."
#
# Ambiguous symbol words are LEFT AS THEY ARE and reported, so the rules can
# be tuned on real lessons (see tamil_text_check.py).

_TA = "஀-௿"
_ZW_RE = re.compile("[​‌‍⁠﻿]")

SYMBOL_WORDS: Dict[str, str] = {
    "கூட்டல்":  "+",
    "பெருக்கல்": "×",
    "கழித்தல்":  "−",
    "வகுத்தல்":  "÷",
    "சமம்":     "=",
}
_SYM_ALT = "|".join(map(re.escape, SYMBOL_WORDS))

_DASH_RE = re.compile(rf"(?<![{_TA}])டேஷ்(?![{_TA}])")
# number  WORD  number   (always a symbol)
_NUM_SYM_RE = re.compile(rf"(\d)\s*({_SYM_ALT})\s*(?=\d)")
# a chain  tok (WORD tok)+  of single tokens
_TOKEN = r"[^\s()\[\]{}.,;:!?\"'“”‘’]+"
_CHAIN_RE = re.compile(
    rf"(?<![^\s(\[]){_TOKEN}(?:\s+(?:{_SYM_ALT})\s+{_TOKEN})+(?![^\s)\].,;:!?])")
_LIST_MARK_RE = re.compile(rf"^\s*(?:\d{{1,2}}[.),]?|[அஆஇஈ][),.]|[-•*])\s+")
# read-aloud MCQ option labels: "அ, அமுது + என்று" is printed "அ) அமுது + என்று"
_OPTION_LABEL_RE = re.compile(r"(?m)^([ \t]*)([அஆஇஈ]),(?=[ \t])")
# a chain followed by என்பதனை/என்பதை is always a symbol chain
# ("நிலவு கூட்டல் என்று என்பதனைச் சேர்த்தெழுதக் கிடைக்கும் சொல்")
_CHAIN_FOLLOWER_RE = re.compile(r"^\s*என்பத(?:னை|ை)")
# read-aloud spelling of a pulli consonant inside a symbol chain:
# "இக் + அ = க" is printed "க் + அ = க"
_PULLI_READ_RE = re.compile(rf"(?<![^\s(\[])இ([க-ஹ]்)(?![{_TA}])")

MEMORISE_LABEL = "மனப்பாடப் பகுதி"
_MEMORISE_RE = re.compile(r"\s*[\(\[]?\s*மனப்பாடப்\s*பகுதி\s*[\)\]]?\s*[.:]?\s*$")

_BOX_MARKERS = [
    (re.compile(r"பெட்டிச்\s*செய்தி\s*ஆரம்பம்"), "\n[பெட்டிச் செய்தி]\n"),
    (re.compile(r"பெட்டிச்\s*செய்தி\s*முடிவு"),  "\n[/பெட்டிச் செய்தி]\n"),
    (re.compile(r"செயல்பாடு\s*ஆரம்பம்"),        "\n[செயல்பாடு]\n"),
    (re.compile(r"செயல்பாடு\s*முடிவு"),         "\n[/செயல்பாடு]\n"),
]
_LINE_NUM_COMMA_RE = re.compile(r"(?m)^([ \t]*(?:#{1,6}[ \t]*)?\d{1,2}),(?=\s)")


def _convert_chain(chain: str) -> str:
    for w, s in SYMBOL_WORDS.items():
        chain = re.sub(rf"(?<!\S){re.escape(w)}(?!\S)", s, chain)
    return _PULLI_READ_RE.sub(r"\1", chain)


def _chain_is_symbolic(line: str, m: "re.Match") -> bool:
    """
    A chain like 'அ கூட்டல் மு கூட்டல் து சமம் அமுது' is a symbol chain when:
      - it is the whole line (ignoring list markers, brackets, end punctuation), or
      - it sits inside brackets, or
      - it is followed by என்பதனை / என்பதை (book-back "join the words" stems), or
      - it has two or more symbol words (பாகு + அல் + காய்), or
      - it contains சமம் after another symbol word (an equation)
    """
    chain = m.group(0)
    if _CHAIN_FOLLOWER_RE.match(line[m.end():]):
        return True
    if sum(1 for t in chain.split() if t in SYMBOL_WORDS) >= 2:
        return True
    rest = (line[: m.start()] + line[m.end():])
    rest = _LIST_MARK_RE.sub("", rest)
    # whole-line rule: MCQ option lines ("அ, அமுது கூட்டல் தென்று") never end in
    # . ! ? — a short SENTENCE does ("எண்களைக் கூட்டல் செய்."), so skip those
    ends_sentence = bool(re.search(r"[.!?]\s*$", line))
    if not ends_sentence and not re.sub(r"[\s()\[\].,;:!?\"'“”‘’=+×−÷-]", "", rest):
        return True
    before, after = line[: m.start()], line[m.end():]
    if before.rstrip().endswith(("(", "[")) and after.lstrip().startswith((")", "]")):
        return True
    words = [t for t in chain.split() if t in SYMBOL_WORDS]
    if "சமம்" in words and any(w != "சமம்" for w in words):
        return True
    return False


def normalize_source_text(text: str) -> Tuple[str, dict]:
    """
    Restore printed symbols in the extracted lesson text.
    Returns (normalized_text, report). The report lists what was converted
    and what was left alone because it looked like an ordinary word.
    """
    report = {
        "dash": 0, "symbols_number": 0, "symbols_chain": 0,
        "symbol_ambiguous": [], "memorise_lines": [], "memorise_blocks": [],
        "boxes": 0, "line_numbers": 0, "option_labels": 0,
    }
    if not text:
        return text or "", report

    t = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")

    t, n = _DASH_RE.subn("________", t)
    report["dash"] = n

    for rx, rep in _BOX_MARKERS:
        t, n = rx.subn(rep, t)
        report["boxes"] += n

    t, n = _LINE_NUM_COMMA_RE.subn(r"\1.", t)
    report["line_numbers"] = n

    t, n = _OPTION_LABEL_RE.subn(r"\1\2)", t)
    report["option_labels"] = n

    out_lines: List[str] = []
    for line in t.split("\n"):
        # memorisation label: same line, or alone on the next line.
        # In the real lessons it follows the SECOND line of a couplet / kural,
        # so the memorised unit is that line plus the line before it.
        if _MEMORISE_RE.search(line):
            stripped = _MEMORISE_RE.sub("", line).rstrip()
            prev = [l.strip() for l in out_lines if l.strip()]
            if stripped.strip():
                end, before = stripped.strip(), (prev[-1] if prev else "")
                line = stripped
            else:
                end, before = (prev[-1] if prev else ""), (prev[-2] if len(prev) > 1 else "")
            if end:
                report["memorise_lines"].append(end)
                report["memorise_blocks"].append([b for b in (before, end) if b])
            if not stripped.strip():
                continue

        # numbers on both sides: always a symbol
        new, n = _NUM_SYM_RE.subn(lambda m: f"{m.group(1)} {SYMBOL_WORDS[m.group(2)]} ", line)
        if n:
            report["symbols_number"] += n
            line = re.sub(r"[ \t]{2,}", " ", new)

        # word-part chains
        if re.search(_SYM_ALT, line):
            pieces, pos = [], 0
            for m in _CHAIN_RE.finditer(line):
                pieces.append(line[pos: m.start()])
                if _chain_is_symbolic(line, m):
                    pieces.append(_convert_chain(m.group(0)))
                    report["symbols_chain"] += 1
                else:
                    pieces.append(m.group(0))
                    amb = line.strip()[:160]
                    if amb not in report["symbol_ambiguous"]:
                        report["symbol_ambiguous"].append(amb)
                pos = m.end()
            pieces.append(line[pos:])
            line = "".join(pieces)

        out_lines.append(line)

    # trim every line (box markers leave stray spaces); keep line breaks —
    # poem and kural lines arrive one per line and are copied exactly
    t = "\n".join(l.strip() for l in "\n".join(out_lines).split("\n"))
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip(), report


# ============================================================================
# SOURCE TEXT — split a lesson into teaching / book exercises / unit-end
# ============================================================================

def _heading_re(names: List[str]) -> re.Pattern:
    """Line-start heading (optional ### and **) matching any of `names`."""
    alts = "|".join(r"\s*".join(map(re.escape, n.split())) for n in names)
    return re.compile(rf"(?m)^[ \t]*(?:#{{1,6}}[ \t]*)?(?:\*\*)?[ \t]*(?:{alts})")


# Book exercises at the end of every lesson (used by the LP's last period,
# the homework rule and the assessment pointers)
EXERCISE_HEADINGS = ["கற்பவை கற்றபின்", "மதிப்பீடு"]

# Unit-end sections in the last lesson of each இயல் (TL decision 5: LP skips them)
UNIT_END_HEADINGS = [
    "மொழியை ஆள்வோம்", "மொழியோடு விளையாடு", "செயல் திட்டம்",
    "நிற்க அதற்குத் தக", "என் பொறுப்புகள்",
    "படிப்போம் பயன்படுத்துவோம்", "கலைச்சொல் அறிவோம்", "கலைச்சொற்கள்",
]

_EXERCISE_RE = _heading_re(EXERCISE_HEADINGS)
_UNIT_END_RE = _heading_re(UNIT_END_HEADINGS)


def split_lesson_parts(text: str, min_fraction: float = 0.3) -> Dict[str, str]:
    """
    Split normalized lesson text into
        teaching   : from the start to the first book-exercise heading
        exercises  : கற்பவை கற்றபின் / மதிப்பீடு … up to the unit-end block
        unit_end   : மொழியை ஆள்வோம் … glossary (last lesson of an இயல் only)
    Headings found in the first `min_fraction` of the text are ignored
    (an intro may mention them in passing).
    """
    text = text or ""
    floor = int(len(text) * min_fraction)

    def first_after(rx):
        for m in rx.finditer(text):
            if m.start() >= floor:
                return m.start()
        return None

    u = first_after(_UNIT_END_RE)
    body, unit_end = (text[:u], text[u:]) if u is not None else (text, "")

    e = None
    for m in _EXERCISE_RE.finditer(body):
        if m.start() >= floor:
            e = m.start()
            break
    teaching, exercises = (body[:e], body[e:]) if e is not None else (body, "")

    return {
        "teaching":  teaching.strip(),
        "exercises": exercises.strip(),
        "unit_end":  unit_end.strip(),
    }


def lp_source_text(text: str) -> Tuple[str, dict]:
    """
    The text the LP builder plans from: normalized, with the unit-end
    sections removed (TL decision 5). Returns (text, info).
    """
    norm, report = normalize_source_text(text)
    parts = split_lesson_parts(norm)
    lp_text = (parts["teaching"] + "\n\n" + parts["exercises"]).strip()
    info = {
        "report": report,
        "chars_in": len(text or ""),
        "chars_lp": len(lp_text),
        "chars_unit_end_dropped": len(parts["unit_end"]),
        "has_exercises": bool(parts["exercises"]),
        "parts": parts,
    }
    return lp_text, info


def list_hash_headings(text: str) -> List[str]:
    """
    Every non-empty ### line (headings AND short bold lines — not all are
    sub-headings, and some real sub-headings arrive WITHOUT ###, e.g.
    புதுமை மொழி in வளர்தமிழ். Never count periods from this list alone.)
    """
    out = []
    for l in (text or "").split("\n"):
        if re.match(r"^\s*#{1,6}", l):
            h = re.sub(r"^\s*#{1,6}\s*", "", l).strip().strip("*").strip()
            if h:
                out.append(h)
    return out


# ============================================================================
# TAMIL-SAFE TEXT COMPARISON (verbatim checks, duplicate detection)
# ============================================================================

def normalize_tamil(s: str) -> str:
    """
    Comparable form of Tamil / mixed text: tags removed, NFC, zero-width
    joiners dropped, lower-case Latin; keeps the Tamil block (letters, vowel
    signs, pulli), a–z and digits; everything else becomes a single space.
    (The Physics normalize_stem() deleted every Tamil character.)
    """
    t = re.sub(r"<[^>]+>", " ", str(s or ""))
    t = unicodedata.normalize("NFC", t)
    t = _ZW_RE.sub("", t).lower()
    t = re.sub(rf"[^{_TA}a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


normalize_stem = normalize_tamil   # name used by the QA helpers


def is_near_duplicate(a: str, b: str, threshold: float = 0.85) -> bool:
    """
    Exact repeat, or word-set Jaccard >= threshold when both stems have at
    least 4 words (Tamil is agglutinative: fewer, longer words than English).
    Conservative on purpose — an eager filter stops a QA part from filling.
    """
    na, nb = normalize_tamil(a), normalize_tamil(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    wa, wb = set(na.split()), set(nb.split())
    if len(wa) < 4 or len(wb) < 4:
        return False
    return len(wa & wb) / len(wa | wb) >= threshold


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

L = LABELS

TAMIL_LP_SYSTEM_PROMPT = f"""You are an experienced Samacheer Kalvi Tamil teacher for Class 6 (children
aged 10–11) in Tamil Nadu. You write lesson plans so clear that a brand-new
teacher can walk into class and teach a confident 30-minute period just by
following the plan.

═══════════════════════════════════════════════════════
LANGUAGE — THREE LAYERS (approved by the TL; never break this)
═══════════════════════════════════════════════════════
1. TEACHER TALK = SPOKEN TAMIL. Hooks, explanations, questions, instructions
   and group-work prompts are written the way a teacher really speaks in a
   Tamil Nadu classroom: இருக்கு, புரிஞ்சுதா, சொல்லுங்க, பாருங்க.
   Neutral classroom Tamil only: no strong regional dialect, no slang, and
   NEVER Tamil written in English letters (no "sollunga", no "puriyudha").
   An English word used inside a Tamil sentence is written in TAMIL script
   (கிரிக்கெட், போன், டீச்சர்) — Latin letters appear ONLY inside the
   bracketed English glosses.
2. BOOK CONTENT = WRITTEN TAMIL, EXACTLY AS IN THE LESSON TEXT. Poem lines,
   kural lines, grammar terms, headings and the answers children write are
   copied character for character from the lesson text given to you.
   Never correct a spelling, never modernise a word, never paraphrase a line,
   even if the source looks wrong. A reviewer handles those cases.
3. ENGLISH = SUPPORT ONLY. A short English gloss in brackets ONLY after:
     (a) the hook question,
     (b) the main explanation of a NEW idea,
     (c) task instructions to students.
   NOT after every teacher line, NOT after check questions, praise or
   closing lines. Key-term English words appear once, on the word wall
   (built separately) — do not repeat them in every period.
   ✅ நான் ஒரு தடவை பாடுறேன். நீங்களும் அப்படியே திருப்பிப் பாடுங்க. (I'll sing once; you sing it back.)
   ❌ புரிஞ்சுதா? (Did you understand?)   ← no gloss on a check line
Order in every period: Tamil first, picture or action second, English last.
Children may answer in any language (English is welcome for "why" answers);
the teacher then says the answer back in Tamil, using the key Tamil term.

═══════════════════════════════════════════════════════
HOW TAMIL IS TAUGHT IN THIS PLAN
═══════════════════════════════════════════════════════
- Read in three steps: the teacher reads or sings first, the class echoes,
  then pairs read. Never ask a child to read cold.
- One small chunk per period. Picture, object or action for every new word.
- Think, pair, share: children first talk in their strongest language, then
  share in Tamil.
- Sentence frames in spoken Tamil (e.g. தமிழ் ___ மாதிரி, ஏன்னா ___.)
- Poems and kurals: tune or rhythm, echo, then meaning; memorisation by
  erasing words from the board a few at a time.
- Teacher talk at most about half the period. Never more than 3 minutes of
  teacher talk without a student response.

═══════════════════════════════════════════════════════
CONTENT ACCURACY — STRICTLY ENFORCE
═══════════════════════════════════════════════════════
- Teach ONLY what is in the lesson text provided. No outside facts, no
  extra poems, no extra kurals, no invented author details or dates.
- Names, numbers and facts (authors, books, counts such as 12, 18, 216):
  only as they appear in the lesson text.
- WORD MEANINGS come from the book's own சொல்லும் பொருளும் and பாடலின் பொருள்
  (or the lesson's own explanation). Say them in spoken Tamil; do not add
  your own background to a word.
- RELIGION AND MYTHOLOGY: teach textbook content as printed, explained by its
  meaning. The teacher adds NO religious examples, stories, rituals, gods,
  devas, heaven or myths of their own (e.g. never "அமுது = தேவர்கள் குடிக்கும்
  பானம்" unless the book says so), and no comparisons between religions.
  Festivals are taught as the book presents them, as culture.
- GRAMMAR AND POETIC FEATURES (இயைபு, எதுகை, மோனை, மாத்திரை …): use the book's
  own definition and the book's / the lines' own examples. Never state a
  general rule of your own (e.g. "they all end in ல் or ன்").
- No page numbers. Refer to content by its heading in the lesson text.
- No real student names. Use "ஒரு மாணவர்", "இணை", "குழு". Names of people
  that appear in the lesson text itself may be used.

═══════════════════════════════════════════════════════
CRITICAL OUTPUT RULES
═══════════════════════════════════════════════════════
- ⚠️ NEVER output Japanese, Chinese, Korean or ANY CJK character.
- Output ONLY raw HTML body content. No <html>, <head>, <body>, <style>,
  <script>. No markdown, no code fences, no backticks, no text before or
  after the HTML. Start directly with an HTML tag.
- Every fixed label is the Tamil label given in the template — copy it
  exactly. No English beside any label.
- Time labels use Arabic digits: "0–4 {L['minutes']}".
- No markdown syntax inside HTML (no **bold**, no # headings, no - lists).

═══════════════════════════════════════════════════════
ALLOWED CSS CLASSES — USE ONLY THESE
═══════════════════════════════════════════════════════
{", ".join(ALLOWED_CLASSES)}
Do NOT invent any other class name. No id attributes. No style attributes.
TABLES: maximum 3 columns, always inside <div class="vocab-block">, with
<thead> and <tbody>.

═══════════════════════════════════════════════════════
⚠️ HTML DIV RULES — NEVER VIOLATE
═══════════════════════════════════════════════════════
- Every <div> you open MUST be closed with </div>.
- Close each lp-section-* div before opening the next one.
- Never put a <div> inside a <p>.
- Before finishing: opened divs must equal closed divs.
"""


# ============================================================================
# REUSABLE INSTRUCTION BLOCKS (inserted into period prompts)
# ============================================================================

BOOK_LINES_INSTRUCTION = f"""
═══════════════════════════════════════════════════════
BOOK LINES (poem / kural / printed examples) — COPY EXACTLY
═══════════════════════════════════════════════════════
Whenever the period shows lines from the book, put them in ONE board-work
block, one line per <br/>, copied character for character from the lesson
text (same spelling, same punctuation):
<div class="board-work">
  <strong>{L['book_lines']}</strong><br/>
  [line 1 exactly as in the lesson text]<br/>
  [line 2 exactly as in the lesson text]
</div>
Python checks every line in this block against the lesson text.
Do not put your own sentences in this block.
"""

CFU_INSTRUCTION = f"""
═══════════════════════════════════════════════════════
CFU — ONE PER PERIOD, INSIDE {L['close']}
═══════════════════════════════════════════════════════
Two oral questions on today's chunk, asked to the whole class (cold-call
2–3 children, show of hands, or pairs check). Each question has its expected
answer in BOOK Tamil (written Tamil, as the child would write it).
MARKUP — exactly this:
<div class="cfu-block">
  <div class="lp-teacher-says">
    <strong>{L['cfu']}</strong><br/>
    <strong>{L['question']} 1:</strong> [spoken-Tamil question]<br/>
    <strong>{L['expected_answer']}:</strong> [answer in book Tamil]<br/>
    <strong>{L['question']} 2:</strong> [spoken-Tamil question]<br/>
    <strong>{L['expected_answer']}:</strong> [answer in book Tamil]
  </div>
  <p class="cfu-wait-note">{L['cfu_wait']}</p>
</div>
❌ Never "புரிஞ்சுதா?"-style questions as a CFU. ❌ No English gloss in the CFU.
"""

CCQ_GRAMMAR_INSTRUCTION = f"""
═══════════════════════════════════════════════════════
CCQ — கற்கண்டு (GRAMMAR) LESSONS ONLY: ONE PER NEW GRAMMAR TERM
═══════════════════════════════════════════════════════
Right after each new grammar term is taught (inside {L['teach']}), ask one
small closed question with ONE right answer, best as "X-ஆ, Y-ஆ?". It checks
the idea, not the definition.
  ✅ "ஆ — குறிலா, நெடிலா?"   (நெடில்)
  ❌ "நெடில்னா என்ன?"
MARKUP — exactly this:
<div class="ccq-block">
  <div class="lp-teacher-says">
    <strong>{L['ccq']}:</strong> [closed question]<br/>
    <strong>{L['expected_answer']}:</strong> [short answer]
  </div>
  <p class="cfu-wait-note">{L['ccq_wait']}</p>
</div>
"""

NO_CCQ_INSTRUCTION = """
- Do NOT use ccq-block in this lesson (CCQs are only for கற்கண்டு lessons).
"""

EXIT_SLIP_INSTRUCTION = f"""
═══════════════════════════════════════════════════════
{L['exit_slip']} — EVERY PERIOD (last item of {L['close']})
═══════════════════════════════════════════════════════
One line each child writes in Tamil (an English word is allowed if a Tamil
word is missing), on today's chunk, with the expected answer in brackets for
the teacher. Then one spoken line linking to the next period.
MARKUP:
<div class="board-work"><strong>{L['exit_slip']}:</strong><br/>[one-line task] ([expected answer])</div>
"""

HOMEWORK_INSTRUCTION = f"""
═══════════════════════════════════════════════════════
{L['homework']} — LAST PERIOD OF THE LESSON ONLY
═══════════════════════════════════════════════════════
- ONE homework task, placed at the end of {L['close']} in the LAST period.
- Taken ONLY from the book's own exercises listed below (மதிப்பீடு, சிந்தனை வினா,
  கற்பவை கற்றபின்). Copy the item's wording; never invent a task.
- About 15 minutes. Doable without internet, extra materials or a parent's help.
MARKUP:
<div class="board-work"><strong>{L['homework']}:</strong><br/>[the book item, exactly as in the lesson text]</div>
"""

NO_HOMEWORK_INSTRUCTION = f"""
- Do NOT give {L['homework']} in this period (homework is only in the last period).
"""


# ============================================================================
# STATIC PREAMBLE TABLES (from the manual LP — same for every lesson,
# built in Python so they cannot drift)
# ============================================================================

def _table(head: List[str], rows: List[List[str]]) -> str:
    th = "".join(f"<th>{_esc(h)}</th>" for h in head)
    body = "\n".join("<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in r) + "</tr>"
                     for r in rows)
    return (f'<div class="vocab-block">\n<table>\n<thead><tr>{th}</tr></thead>\n'
            f"<tbody>\n{body}\n</tbody>\n</table>\n</div>")


def _esc(s) -> str:
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


SPOKEN_WRITTEN_ROWS = [
    ["புரிஞ்சுது", "புரிந்தது"],
    ["இருக்கு", "இருக்கிறது"],
    ["சொல்றாங்க", "சொல்கிறார்கள்"],
    ["பாடுறேன்", "பாடுகிறேன்"],
    ["ஏன்னா", "ஏனெனில்"],
    ["மாதிரி", "போன்று"],
]

CLASSROOM_TAMIL_ROWS = [
    ["நல்லாக் கவனிங்க.", "Listen carefully."],
    ["என் கூடச் சேர்ந்து சொல்லுங்க.", "Say it with me."],
    ["இன்னொரு தடவை சொல்லுங்க.", "Say it once more."],
    ["பக்கத்துல இருக்கிறவங்க கிட்டப் பேசுங்க.", "Talk to your partner."],
    ["உங்க குரூப்ல பேசிக்கோங்க.", "Discuss in your group."],
    ["பதிலை எழுதுங்க.", "Write the answer."],
    ["யார் சொல்றீங்க? கை தூக்குங்க.", "Who will answer? Raise your hand."],
    ["ஏன் அப்படிச் சொல்றீங்க?", "Why do you say so?"],
    ["தெரியலைனா பரவாயில்ல, இங்கிலீஷ்ல சொல்லுங்க.", "It's fine if you don't know; say it in English."],
    ["சூப்பர்! சரியாச் சொன்னீங்க!", "Super! You said it correctly!"],
    ["அமைதியா உட்காருங்க.", "Sit quietly."],
]


def static_language_tables_html() -> str:
    """Spoken → written bridge + classroom Tamil (fixed, from the manual LP)."""
    return (
        "<h3>பேச்சுத் தமிழும் எழுத்துத் தமிழும்</h3>\n"
        + _table(["பேச்சு", "எழுத்து (பாடநூல்)"], SPOKEN_WRITTEN_ROWS)
        + "\n<h3>வகுப்பறைத் தமிழ்</h3>\n"
        + _table(["பேச்சுத் தமிழ்", "English"], CLASSROOM_TAMIL_ROWS)
    )


# ============================================================================
# HELPER — clean raw AI output
# ============================================================================

_CJK_RE = re.compile(
    "["
    "぀-ヿ"   # Hiragana, Katakana
    "㐀-䶿"   # CJK Ext A
    "一-鿿"   # CJK Unified
    "가-힯"   # Hangul syllables
    "ᄀ-ᇿ"   # Hangul Jamo
    "豈-﫿"   # CJK compatibility
    "＀-￯"   # Half/full-width forms
    "]+"
)


def strip_cjk(text: str) -> Tuple[str, int]:
    """Remove any CJK characters (Tamil U+0B80–U+0BFF is never touched)."""
    if not text:
        return text, 0
    removed = sum(len(m) for m in _CJK_RE.findall(text))
    return (_CJK_RE.sub("", text), removed) if removed else (text, 0)


def clean(raw: str) -> str:
    """
    Strip markdown fences, <style>/<script>, document tags, prose before the
    first tag / after the last tag and CJK characters; NFC-normalise; let
    BeautifulSoup repair unclosed non-div tags. Divs are repaired separately
    by normalize_day_html() / normalize_assessment_html().
    """
    if not raw:
        return raw
    text = unicodedata.normalize("NFC", raw.strip())
    text = re.sub(r"```(?:html|HTML)?", "", text).strip()
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"</?(?:html|head|body)\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s(?:id|data-[\w-]+)\s*=\s*(\"[^\"]*\"|'[^']*')", "", text)

    first_tag = re.search(r"<(?:div|h[1-6]|section|p|table|ul|ol)\b", text)
    if first_tag and first_tag.start() > 0:
        if not text[: first_tag.start()].strip().startswith("<"):
            text = text[first_tag.start():]

    last_close = None
    for m in re.finditer(r"</[a-zA-Z0-9]+\s*>|<!--.*?-->", text, flags=re.DOTALL):
        last_close = m
    if last_close:
        tail = text[last_close.end():].strip()
        if tail and "<" not in tail:
            text = text[: last_close.end()]

    text, n_cjk = strip_cjk(text)
    if n_cjk:
        print(f"      ⚠️ [Tamil LP] Removed {n_cjk} CJK character(s) from output")

    from bs4 import BeautifulSoup
    text = str(BeautifulSoup(text, "html.parser"))
    return text.strip()


# ============================================================================
# HELPER — div balancing (comment-aware)
# ============================================================================

_DIV_TOKEN_RE = re.compile(
    r"(<!--.*?-->)|(<div\b[^>]*>)|(</div\s*>)",
    flags=re.DOTALL | re.IGNORECASE,
)


def balance_divs(fragment: str) -> str:
    """Drop surplus </div>, append missing </div>. Comments are ignored."""
    if not fragment:
        return fragment
    out, depth, pos, dropped = [], 0, 0, 0
    for m in _DIV_TOKEN_RE.finditer(fragment):
        out.append(fragment[pos:m.start()])
        pos = m.end()
        if m.group(1):
            out.append(m.group(1))
        elif m.group(2):
            depth += 1
            out.append(m.group(2))
        else:
            if depth == 0:
                dropped += 1
                continue
            depth -= 1
            out.append(m.group(3))
    out.append(fragment[pos:])
    result = "".join(out)
    if depth > 0:
        result += "</div>" * depth
    if dropped or depth:
        print(f"      ⚠️ [Tamil LP] Div repair: dropped {dropped} stray </div>, "
              f"added {depth} missing </div>")
    return result


def _matching_close_index(html: str, open_end: int) -> Optional[Tuple[int, int]]:
    depth = 1
    for m in _DIV_TOKEN_RE.finditer(html, open_end):
        if m.group(1):
            continue
        if m.group(2):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return m.start(), m.end()
    return None


def _class_open_re(cls: str) -> re.Pattern:
    return re.compile(
        rf"""<div\b[^>]*\bclass\s*=\s*["'][^"']*\b{re.escape(cls)}\b[^"']*["'][^>]*>""",
        flags=re.IGNORECASE,
    )


_DAY_OPEN_RE = _class_open_re("lp-day-block")
_ASSESS_OPEN_RE = _class_open_re("assessment-block")


def _wrap_single_block(html: str, open_re: re.Pattern, exact_open: str,
                       label: str) -> str:
    """Guarantee exactly ONE wrapper div opened with `exact_open`, all content inside."""
    html = (html or "").strip()
    matches = list(open_re.finditer(html))
    if not matches:
        print(f"      ⚠️ [Tamil LP] No {label} wrapper found — wrapping output")
        return exact_open + "\n" + balance_divs(html) + "\n</div>"

    if len(matches) > 1:
        print(f"      ⚠️ [Tamil LP] {len(matches) - 1} extra {label} opening(s) demoted")
        first = matches[0]
        html = html[: first.end()] + open_re.sub("<div>", html[first.end():])
        matches = [first]

    first = matches[0]
    prefix = html[: first.start()].strip()
    body = html[first.end():]
    full = exact_open + balance_divs(exact_open + body)[len(exact_open):]

    close = _matching_close_index(full, len(exact_open))
    if close is None:
        full += "</div>"
        close = (len(full) - 6, len(full))

    inner = full[len(exact_open): close[0]]
    suffix = full[close[1]:].strip()
    if prefix:
        inner = "\n" + prefix + "\n" + inner
    if suffix:
        inner = inner + "\n" + suffix + "\n"
    return exact_open + inner + "</div>"


def remove_blocks(html: str, cls: str) -> Tuple[str, int]:
    """Remove every <div class="... cls ..."> block (with its content)."""
    rx = _class_open_re(cls)
    removed = 0
    while True:
        m = rx.search(html or "")
        if not m:
            break
        close = _matching_close_index(html, m.end())
        end = close[1] if close else len(html)
        html = html[: m.start()] + html[end:]
        removed += 1
    return html, removed


def normalize_day_html(html: str, lesson_type: str = "") -> str:
    """
    Enforce the day-block contract on ONE generated period:
      - exactly one <div class="lp-day-block">, everything inside it
      - no assessment-block inside a period
      - ccq-blocks removed unless the lesson is கற்கண்டு (TL decision 2)
      - balanced divs
    """
    html = re.sub(r"\bassessment-block\b", "lp-section-closing", html or "")
    if normalize_lesson_type(lesson_type) != "grammar":
        html, n = remove_blocks(html, "ccq-block")
        if n:
            print(f"      ⚠️ [Tamil LP] Removed {n} CCQ block(s) — CCQs are for கற்கண்டு only")
    return _wrap_single_block(html, _DAY_OPEN_RE, DAY_BLOCK_OPEN, "lp-day-block")


def normalize_assessment_html(html: str) -> str:
    html = _DAY_OPEN_RE.sub("<div>", html or "")
    return _wrap_single_block(html, _ASSESS_OPEN_RE, ASSESSMENT_BLOCK_OPEN, "assessment-block")


def normalize_preamble_html(html: str) -> str:
    html = _DAY_OPEN_RE.sub("<div>", html or "")
    html = _ASSESS_OPEN_RE.sub("<div>", html)
    return balance_divs(html)


# ============================================================================
# HELPER — structural and language checks (decide on a retry)
# ============================================================================

_REQUIRED_DAY_PARTS = [
    ("lp-section-opening",      f"{L['hook']} section"),
    ("lp-section-main",         f"{L['teach']} section"),
    ("lp-section-student-task", f"{L['do']} section"),
    ("lp-section-closing",      f"{L['close']} section"),
    ("cfu-block",               "the CFU"),
]

# English labels that must not appear outside brackets (TL: Tamil labels only)
_ENGLISH_LABEL_RE = re.compile(
    r"\b(Hook|Teach|Do|Check and close|Exit (?:slip|ticket)|Homework|CFU|CCQ|"
    r"Objectives|Word wall|Materials|Assessment|Teacher says|Period \d)\b")

_BRACKET_RE = re.compile(r"\(([^()]*)\)")


def _visible_text(html: str) -> str:
    t = re.sub(r"<!--.*?-->", " ", html or "", flags=re.DOTALL)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def _is_english_gloss(s: str) -> bool:
    latin = len(re.findall(r"[A-Za-z]", s))
    tamil = len(re.findall(rf"[{_TA}]", s))
    return latin >= 3 and latin >= 2 * tamil


def count_glosses(html: str) -> int:
    """Bracketed English glosses in a period (TL: hook, new idea, instructions only)."""
    return sum(1 for m in _BRACKET_RE.finditer(_visible_text(html)) if _is_english_gloss(m.group(1)))


def latin_outside_glosses(html: str) -> List[str]:
    """Latin words outside bracketed glosses — Tanglish or English leaking in."""
    text = _BRACKET_RE.sub(lambda m: " " if _is_english_gloss(m.group(1)) else m.group(0),
                           _visible_text(html))
    return re.findall(r"[A-Za-z]{2,}", text)


def check_time_labels(html: str, total: int = PERIOD_MINUTES) -> Optional[str]:
    """Time labels must run 0 → 30 contiguously, in order."""
    ranges = [(int(a), int(b)) for a, b in re.findall(
        r'class="lp-time">\s*(\d+)\s*[–—-]\s*(\d+)', html or "")]
    if not ranges:
        return None
    issues = []
    if ranges[0][0] != 0:
        issues.append(f"starts at {ranges[0][0]}")
    if ranges[-1][1] != total:
        issues.append(f"ends at {ranges[-1][1]}")
    for (a1, b1), (a2, b2) in zip(ranges, ranges[1:]):
        if a2 != b1:
            issues.append(f"{a1}–{b1} then {a2}–{b2}")
    return ("time labels not contiguous (" + "; ".join(issues[:4]) + ")") if issues else None


def check_day_structure(html: str, lesson_type: str = "",
                        is_last_period: bool = False) -> List[str]:
    """Problems in a normalized period fragment. Empty list = fine."""
    if not html:
        return ["empty output"]
    problems = []
    ltype = normalize_lesson_type(lesson_type)

    n_open = html.count(DAY_BLOCK_OPEN)
    if n_open != 1:
        problems.append(f"expected 1 day opening, found {n_open}")

    for cls, label in _REQUIRED_DAY_PARTS:
        if cls not in html:
            problems.append(f"missing {label} ({cls})")

    n_cfu = html.count('class="cfu-block"')
    if n_cfu > 1:
        problems.append(f"minor: {n_cfu} CFU blocks (expected 1)")
    if ltype == "grammar" and "ccq-block" not in html:
        problems.append("missing CCQ for the new grammar term (ccq-block)")

    if L["exit_slip"] not in html:
        problems.append(f"missing exit slip ({L['exit_slip']})")

    has_hw = L["homework"] in html
    if is_last_period and not has_hw:
        problems.append(f"missing homework ({L['homework']}) in the last period")
    if has_hw and not is_last_period:
        problems.append(f"minor: homework in a period that is not the last")

    timing = check_time_labels(html)
    if timing:
        problems.append("minor: " + timing)

    leaks = _ENGLISH_LABEL_RE.findall(
        _BRACKET_RE.sub(" ", _visible_text(html)))
    if leaks:
        problems.append(f"minor: English label(s) outside glosses: {sorted(set(leaks))[:5]}")

    latin = latin_outside_glosses(html)
    if len(latin) > 3:
        problems.append(f"minor: {len(latin)} Latin words outside glosses "
                        f"(e.g. {' '.join(latin[:5])})")

    n_gloss = count_glosses(html)
    if n_gloss > 8:
        problems.append(f"minor: {n_gloss} English glosses (only hook, new idea, instructions)")

    return problems


def is_critical(problems: List[str]) -> bool:
    """Problems serious enough to justify one retry of the period call."""
    return any(not p.startswith("minor:") for p in problems)


def check_book_lines(html: str, source_text: str) -> List[str]:
    """
    Lines inside 'பாடநூல் வரிகள்' board-work blocks that do NOT appear in the
    lesson text (compared after whitespace/punctuation normalisation).
    Logged for the reviewer — never auto-corrected (TL decision 1).
    """
    src = normalize_tamil(source_text)
    bad = []
    rx = re.compile(r'<div class="board-work">(.*?)</div>', re.DOTALL)
    for m in rx.finditer(html or ""):
        block = m.group(1)
        if L["book_lines"] not in block:
            continue
        block = block.split(L["book_lines"], 1)[1]
        for line in re.split(r"<br\s*/?>", block):
            n = normalize_tamil(line)
            if len(n.split()) < 2:
                continue
            if n not in src:
                bad.append(re.sub(r"<[^>]+>", "", line).strip()[:120])
    return bad


def count_day_blocks(html: str) -> int:
    return (html or "").count('<div class="lp-day-block"')


def count_assessment_blocks(html: str) -> int:
    return (html or "").count('<div class="assessment-block"')


# ============================================================================
# HELPER — placeholders / markers
# ============================================================================

def failed_day_block(day_num: int, total_days: int, title: str = "",
                     reason: str = "") -> str:
    """Visible placeholder that keeps tab numbering correct when a period fails."""
    safe_title = re.sub(r"[<>]", "", title or "")
    safe_reason = re.sub(r"[<>]", "", reason or "generation error")
    return (
        f"{DAY_BLOCK_OPEN}\n"
        f"{LP_DAY_FAILED_MARKER}\n"
        f'<h3 class="lp-day-title">{L["period"]} {day_num} / {total_days}'
        f'{" — " + safe_title if safe_title else ""}</h3>\n'
        f'<div class="common-mistakes">\n'
        f"  <strong>⚠️ இந்தப் பாடவேளையை உருவாக்க முடியவில்லை.</strong>\n"
        f"  <p>இந்தப் பாடத்திட்டத்தை மீண்டும் உருவாக்கவும். ({safe_reason})</p>\n"
        f"</div>\n"
        f"</div>"
    )


def mark_truncated(day_html: str) -> str:
    if LP_DAY_TRUNCATED_MARKER in day_html:
        return day_html
    if day_html.startswith(DAY_BLOCK_OPEN):
        return DAY_BLOCK_OPEN + "\n" + LP_DAY_TRUNCATED_MARKER + day_html[len(DAY_BLOCK_OPEN):]
    return LP_DAY_TRUNCATED_MARKER + "\n" + day_html


# ============================================================================
# HELPER — JSON parsing
# ============================================================================

def parse_json_response(raw: str) -> dict:
    """Parse the outermost {...} of model output. Raises json.JSONDecodeError."""
    if raw is None:
        raise json.JSONDecodeError("empty response", "", 0)
    text = re.sub(r"```(?:json|JSON)?", "", raw).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise json.JSONDecodeError("no JSON object found", text, 0)
    text, _ = strip_cjk(unicodedata.normalize("NFC", text[start: end + 1]))
    return json.loads(text)