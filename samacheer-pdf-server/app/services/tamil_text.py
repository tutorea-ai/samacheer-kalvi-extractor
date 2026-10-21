"""
tamil_text.py
-------------
Tamil source-text normaliser — moved from the prompt team's
app/content_builder/tamil/base/__init__.py (21 Oct 2026) into the extraction
layer, so it runs ONCE for every page type. Logic unchanged; only two
character ranges are written as \\u escapes so they survive copy/paste.
Builders may keep their own copy as a safety check (running it twice changes nothing).

Sections:
  - SOURCE TEXT — undo the read-aloud EPUB spellings   (normalize_source_text)
  - SOURCE TEXT — split a lesson into parts              (split_lesson_parts,
                                                          lp_source_text,
                                                          list_hash_headings)
  - TAMIL-SAFE TEXT COMPARISON                           (normalize_tamil,
                                                          is_near_duplicate)
Standalone: needs only the Python standard library.
"""

import json
import re
import unicodedata
from typing import Dict, List, Optional, Tuple


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
# be tuned on real lessons.

_TA = "\u0b80-\u0bff"                                        # Tamil Unicode block
_ZW_RE = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")      # zero-width characters

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
_LIST_MARK_RE = re.compile(rf"^\s*(?:#{{1,6}}\s*)?(?:\d{{1,2}}[.),]?|[அஆஇஈ][),.]|[-•*])\s+")
# read-aloud MCQ option labels: "அ, அமுது + என்று" is printed "அ) அமுது + என்று"
_OPTION_LABEL_RE = re.compile(r"(?m)^([ \t]*(?:#{1,6}[ \t]*)?)([அஆஇஈ]),(?=[ \t])")
# a chain followed by என்பதனை/என்பதை is always a symbol chain
# ("நிலவு கூட்டல் என்று என்பதனைச் சேர்த்தெழுதக் கிடைக்கும் சொல்")
# …and "X + Y என்று பெயர்" (word-origin sentences: "தால் + ஆட்டு என்று பெயர் பெற்றது")
_CHAIN_FOLLOWER_RE = re.compile(r"^\s*(?:என்பத(?:னை|ை)|என்று\s+பெயர்)")
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
    # MCQ option running on the question line: "… கிடைப்பது ________ அ, பொறுமை கூட்டல் உடமை"
    if re.search(r"(?:^|\s)[அஆஇஈ][,)]\s*$", line[: m.start()]):
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