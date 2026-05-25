"""
section_detector.py

Three responsibilities:
1. detect_sections()   — what sections exist in the lesson
2. split_into_zones()  — split raw text into clean focused zones
3. clean_noise()       — remove pdf2htmlEX noise

Key fix: exercise types now detected IN ORDER of appearance in text.
"""

import re
from typing import Dict, List, Optional


# ============================================================================
# EXERCISE TYPE MAPPING
# Maps exercise heading keywords → exercise type identifier
# ============================================================================

EXERCISE_KEYWORD_MAP = [
    # (regex pattern, exercise_type)
    (r'choose\s+the\s+correct|choose\s+the\s+best|choose\s+the\s+right|select\s+the\s+correct', 'mcq'),
    (r'fill\s+in\s+the\s+blank|complete\s+the\s+following\s+with|fill\s+in\s+with', 'fill_blank'),
    (r'true\s+or\s+false|state\s+whether', 'true_false'),
    (r'identify\s+the\s+(character|speaker)|name\s+the\s+speaker|who\s+said', 'identify_speaker'),
    (r'match\s+the\s+following|match\s+the\s+column', 'match'),
    (r'rearrange\s+the\s+following|put\s+the\s+following\s+in|arrange\s+the\s+following', 'rearrange'),
    (r'answer\s+the\s+following\s+questions\s+in\s+one\s+or\s+two'
     r'|answer\s+in\s+one\s+or\s+two'
     r'|answer\s+briefly'
     r'|answer\s+the\s+following\s+in\s+one', 'short_answer'),
    (r'answer\s+the\s+questions\s+in\s+a\s+paragraph'
     r'|answer\s+in\s+detail'
     r'|write\s+a\s+detailed'
     r'|100\s*[–-]\s*150\s+words'
     r'|paragraph\s+of\s+about'
     r'|answer\s+in\s+about', 'long_answer'),
]


# ============================================================================
# SECTION DETECTION
# ============================================================================

def detect_sections(text: str, lesson_type: str = "prose") -> Dict:
    """
    Analyzes raw lesson text and returns what sections exist.
    Exercise types are returned IN ORDER of appearance in text.
    """
    lower = text.lower()

    has_about_author = bool(re.search(r'about\s+the\s+author', lower))
    has_about_poet   = bool(re.search(r'about\s+the\s+poet', lower))
    has_do_you_know  = bool(re.search(r'do\s+you\s+know\??', lower))
    has_ict_corner   = bool(re.search(r'ict\s+corner', lower))

    has_glossary_heading = bool(re.search(r'glossary', lower))
    has_glossary_pattern = len(re.findall(
        r'\b\w+\s*\([nvadj\.]+\)\s*[–\-]', text
    )) >= 3
    has_glossary = has_glossary_heading or has_glossary_pattern

    has_grammar = False
    if lesson_type.lower() == "prose":
        grammar_matches = [m.start() for m in re.finditer(r'\bgrammar\b', lower)]
        ict_start = lower.find('ict corner')
        for pos in grammar_matches:
            if ict_start == -1 or pos < ict_start - 50:
                has_grammar = True
                break

    # ── KEY FIX: detect exercise types IN ORDER of appearance ────────────────
    exercise_types = _detect_exercise_types_ordered(text)
    has_exercises  = len(exercise_types) > 0

    hash_codes    = re.findall(r'\[[A-Za-z0-9]{4,12}\]', text)
    footer_noise  = re.findall(r'\d+th\s+English_Unit_\d+\.indd', text)
    noise_detected    = len(hash_codes) > 0 or len(footer_noise) > 0
    overflow_detected = bool(re.search(
        r'unit\s*[-–]\s*[2-9]|unit\s*[2-9]\s*unit', lower
    ))

    return {
        "has_about_author":  has_about_author,
        "has_about_poet":    has_about_poet,
        "has_do_you_know":   has_do_you_know,
        "has_ict_corner":    has_ict_corner,
        "has_glossary":      has_glossary,
        "has_grammar":       has_grammar,
        "has_exercises":     has_exercises,
        "exercise_types":    exercise_types,
        "noise_detected":    noise_detected,
        "overflow_detected": overflow_detected,
        "lesson_type":       lesson_type,
    }


def _detect_exercise_types_ordered(text: str) -> List[str]:
    """
    Detects exercise types IN ORDER of appearance in the text.

    Scans for exercise headings like:
      A. Choose the correct answer
      B. Identify the speaker
      C. Answer in one or two sentences
      D. Answer in a paragraph
      E. Rearrange the following

    Returns exercise types in the exact order they appear.
    """
    # Pattern to find exercise letter headings A. B. C. D. E. F.
    heading_pattern = r'\n([A-F])\.\s+(.+)'

    found = []  # list of (position, exercise_type)
    seen_types = set()  # avoid duplicates

    matches = re.finditer(heading_pattern, text, re.IGNORECASE)

    for m in matches:
        heading_text = m.group(2).lower().strip()
        position     = m.start()

        # Match heading text against exercise keyword map
        for pattern, ex_type in EXERCISE_KEYWORD_MAP:
            if re.search(pattern, heading_text, re.IGNORECASE):
                if ex_type not in seen_types:
                    found.append((position, ex_type))
                    seen_types.add(ex_type)
                break  # stop at first match for this heading

    # Sort by position — guarantees textbook order
    found.sort(key=lambda x: x[0])

    ordered_types = [ex_type for _, ex_type in found]

    if ordered_types:
        print(f"         [Detector] Exercise order: {ordered_types}")

    return ordered_types


# ============================================================================
# ZONE SPLITTING
# ============================================================================

def split_into_zones(text: str) -> Dict[str, str]:
    """
    Splits raw lesson text into logical zones.
    Each zone is passed to the correct extractor.

    Returns:
    {
        story_zone:    clean story/poem text only
        exercise_zone: all exercises text
        glossary_zone: word definitions text
        author_zone:   about the author/poet text
        ict_zone:      ICT corner text
        full_text:     original full text (fallback)
    }
    """
    zones = {
        "story_zone":    text,
        "exercise_zone": text,
        "glossary_zone": text,
        "author_zone":   text,
        "ict_zone":      text,
        "full_text":     text,
    }

    lower = text.lower()

    # ── Find boundaries ───────────────────────────────────────────────────────
    ict_pos    = _find_pattern(lower, [r'ict\s+corner'])
    author_pos = _find_pattern(lower, [
        r'about\s+the\s+author',
        r'about\s+the\s+poet',
    ])

    glossary_pos = _find_pattern(lower, [r'glossary'])
    if glossary_pos is None:
        match = re.search(r'\b\w+\s*\([nvadj\.]+\)\s*[–\-]', text)
        if match:
            line_start   = text.rfind('\n', 0, match.start())
            glossary_pos = line_start if line_start != -1 else match.start()

    exercise_pos = _find_pattern(text, [
        r'\nA\.\s+Choose', r'\nA\.\s+Fill',   r'\nA\.\s+Answer',
        r'\nA\.\s+Match',  r'\nA\.\s+Identify',r'\nA\.\s+Rearrange',
        r'\nA\.\s+True',   r'\nA\.\s+Read',    r'\nA\.\s+Write',
        r'\nA\.\s+Select', r'\nA\.\s+Put',     r'\nA\.\s+Arrange',
        r'\nA\.\s+Name',   r'\nA\.\s+Find',    r'\nA\.\s+Complete',
        r'\nA\.\s+Give',   r'\nA\.\s+State',
    ], use_lower=False)

    # ── Story zone ────────────────────────────────────────────────────────────
    story_end_candidates = [p for p in [
        exercise_pos, glossary_pos, author_pos
    ] if p is not None]

    if story_end_candidates:
        story_end  = min(story_end_candidates)
        story_zone = text[:story_end].strip()
        if len(story_zone) > 200:
            zones["story_zone"] = story_zone
            print(f"         [Zones] Story zone: {len(story_zone)} chars")
        else:
            print(f"         [Zones] Story zone too short — using full text fallback")

    # ── Exercise zone ─────────────────────────────────────────────────────────
    if exercise_pos is not None:
        exercise_end = ict_pos if ict_pos is not None else len(text)
        if author_pos is not None and author_pos > exercise_pos:
            exercise_end = min(exercise_end, author_pos)
        exercise_zone = text[exercise_pos:exercise_end].strip()
        if len(exercise_zone) > 100:
            zones["exercise_zone"] = exercise_zone
            print(f"         [Zones] Exercise zone: {len(exercise_zone)} chars")

    # ── Glossary zone ─────────────────────────────────────────────────────────
    if glossary_pos is not None:
        glossary_end_candidates = [p for p in [
            exercise_pos, author_pos, ict_pos
        ] if p is not None and p > glossary_pos]
        glossary_end  = min(glossary_end_candidates) if glossary_end_candidates else len(text)
        glossary_zone = text[glossary_pos:glossary_end].strip()
        if len(glossary_zone) > 50:
            zones["glossary_zone"] = glossary_zone
            print(f"         [Zones] Glossary zone: {len(glossary_zone)} chars")

    # ── Author zone ───────────────────────────────────────────────────────────
    if author_pos is not None:
        author_end_candidates = [p for p in [
            glossary_pos, exercise_pos, ict_pos
        ] if p is not None and p > author_pos]
        author_end  = min(author_end_candidates) if author_end_candidates else len(text)
        author_zone = text[author_pos:author_end].strip()
        if len(author_zone) > 50:
            zones["author_zone"] = author_zone
            print(f"         [Zones] Author zone: {len(author_zone)} chars")

    # ── ICT zone ──────────────────────────────────────────────────────────────
    if ict_pos is not None:
        ict_zone = text[ict_pos:].strip()
        overflow = re.search(r'unit\s*[-–]\s*[2-9]', ict_zone, re.IGNORECASE)
        if overflow:
            ict_zone = ict_zone[:overflow.start()].strip()
        if len(ict_zone) > 50:
            zones["ict_zone"] = ict_zone
            print(f"         [Zones] ICT zone: {len(ict_zone)} chars")

    return zones


def _find_pattern(text: str, patterns: list,
                  use_lower: bool = True) -> Optional[int]:
    """Finds earliest match position for any pattern. Returns None if not found."""
    search_text = text.lower() if use_lower else text
    earliest    = None
    for pattern in patterns:
        match = re.search(pattern, search_text)
        if match:
            if earliest is None or match.start() < earliest:
                earliest = match.start()
    return earliest


# ============================================================================
# NOISE CLEANING
# ============================================================================

def clean_noise(text: str, subject: str = "english") -> str:
    """Removes pdf2htmlEX noise before any processing."""
    text = re.sub(r'\[[A-Za-z0-9]{4,12}\]', '', text)
    text = re.sub(
        r'\d+th\s+English_Unit_\d+\.indd\s+\d+\s+\d{2}-\d{2}-\d{4}\s+[\d:]+',
        '', text
    )

    # Overflow truncation — English/Tamil ONLY.
    # SS/Science/Maths units naturally contain "Unit – 2" in headings,
    # so running this truncation for those subjects destroys their content.
    if subject.lower() in ["english", "tamil"]:
        overflow_patterns = [
            r'unit\s*[-–]\s*[2-9]',
            r'\d+th\s+English_Unit_[2-9]',
        ]
        earliest = len(text)
        for pattern in overflow_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m and m.start() < earliest:
                earliest = m.start()
        if earliest < len(text):
            text = text[:earliest]

    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ============================================================================
# QUICK TEST
# ============================================================================

if __name__ == "__main__":
    import sys
    test_file = sys.argv[1] if len(sys.argv) > 1 else None
    if test_file:
        with open(test_file, "r", encoding="utf-8") as f:
            raw = f.read()

        print("=" * 60)
        cleaned  = clean_noise(raw)
        sections = detect_sections(cleaned, "supplementary")

        print("SECTIONS:")
        for k, v in sections.items():
            print(f"  {k}: {v}")
        print()

        print("ZONES:")
        zones = split_into_zones(cleaned)
        for k, v in zones.items():
            if k != "full_text":
                print(f"  {k}: {len(v)} chars | First 80: {v[:80].strip()}")
                print()
    else:
        print("Usage: python section_detector.py <path_to_txt_file>")