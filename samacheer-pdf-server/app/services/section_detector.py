"""
section_detector.py

Two responsibilities:
1. detect_sections()   — what sections exist in the lesson
2. split_into_zones()  — split raw text into clean focused zones
3. clean_noise()       — remove pdf2htmlEX noise

Used by assembler.py before any extractor call.
"""

import re
from typing import Dict, List


# ============================================================================
# SECTION DETECTION
# ============================================================================

def detect_sections(text: str, lesson_type: str = "prose") -> Dict:
    """
    Analyzes raw lesson text and returns what sections exist.
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

    exercise_types = _detect_exercise_types(text, lower)
    has_exercises  = len(exercise_types) > 0

    hash_codes   = re.findall(r'\[[A-Za-z0-9]{4,12}\]', text)
    footer_noise = re.findall(r'\d+th\s+English_Unit_\d+\.indd', text)
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


def _detect_exercise_types(text: str, lower: str) -> List[str]:
    found = []
    if re.search(r'choose\s+the\s+correct|choose\s+the\s+best|choose\s+the\s+right', lower):
        found.append("mcq")
    if re.search(r'fill\s+in\s+the\s+blank|complete\s+the\s+following\s+with', lower):
        found.append("fill_blank")
    if re.search(r'true\s+or\s+false|state\s+whether\s+true\s+or\s+false', lower):
        found.append("true_false")
    if re.search(
        r'answer\s+the\s+following\s+questions\s+in\s+one\s+or\s+two'
        r'|answer\s+in\s+one\s+or\s+two'
        r'|answer\s+briefly',
        lower
    ):
        found.append("short_answer")
    if re.search(
        r'answer\s+the\s+questions\s+in\s+a\s+paragraph'
        r'|answer\s+in\s+detail'
        r'|write\s+a\s+detailed'
        r'|100\s*[–-]\s*150\s+words'
        r'|paragraph\s+of\s+about',
        lower
    ):
        found.append("long_answer")
    if re.search(
        r'rearrange\s+the\s+following\s+sentences'
        r'|put\s+the\s+following\s+in\s+(correct\s+)?order'
        r'|arrange\s+the\s+following',
        lower
    ):
        found.append("rearrange")
    if re.search(
        r'identify\s+the\s+(character|speaker)'
        r'|name\s+the\s+speaker'
        r'|who\s+said',
        lower
    ):
        found.append("identify_speaker")
    if re.search(r'match\s+the\s+following|match\s+the\s+column', lower):
        found.append("match")
    return found


# ============================================================================
# ZONE SPLITTING — NEW
# Splits raw text into clean focused zones before extraction.
# Python finds boundaries — no Claude needed.
# ============================================================================

def split_into_zones(text: str) -> Dict[str, str]:
    """
    Splits raw lesson text into logical zones.
    Each zone is passed to the correct extractor.
    
    Returns:
    {
        "story_zone":    clean story/poem text only
        "exercise_zone": all exercises text
        "glossary_zone": word definitions text
        "author_zone":   about the author/poet text
        "ict_zone":      ICT corner text
        "full_text":     original full text (fallback)
    }
    
    If a zone boundary is not found — returns full text as fallback.
    Extractor still works, just less efficiently.
    """

    zones = {
        "story_zone":    text,   # fallback = full text
        "exercise_zone": text,   # fallback = full text
        "glossary_zone": text,   # fallback = full text
        "author_zone":   text,   # fallback = full text
        "ict_zone":      text,   # fallback = full text
        "full_text":     text,
    }

    lower = text.lower()

    # ── Find ICT Corner boundary ──────────────────────────────────────────────
    ict_pos = _find_pattern(lower, [
        r'ict\s+corner',
    ])

    # ── Find About Author boundary ────────────────────────────────────────────
    author_pos = _find_pattern(lower, [
        r'about\s+the\s+author',
        r'about\s+the\s+poet',
    ])

    # ── Find Glossary boundary ────────────────────────────────────────────────
    # Glossary starts with first "word (n/v/adj) –" pattern
    glossary_pos = _find_pattern(lower, [
        r'glossary',
    ])
    # If no explicit heading, find first word definition pattern
    if glossary_pos is None:
        match = re.search(r'\b\w+\s*\([nvadj\.]+\)\s*[–\-]', text)
        if match:
            # Go back to start of that line
            line_start = text.rfind('\n', 0, match.start())
            glossary_pos = line_start if line_start != -1 else match.start()

    # ── Find Exercise boundary ────────────────────────────────────────────────
    # Exercises always start with "A." or "A " followed by exercise instruction
    exercise_pos = _find_pattern(text, [
        r'\nA\.\s+Choose',
        r'\nA\.\s+Fill',
        r'\nA\.\s+Answer',
        r'\nA\.\s+Match',
        r'\nA\.\s+Identify',
        r'\nA\.\s+Rearrange',
        r'\nA\.\s+True',
        r'\nA\.\s+Read',
        r'\nA\.\s+Write',
        r'\nA\.\s+Select',
    ], use_lower=False)

    # ── Build zones based on found boundaries ─────────────────────────────────

    # Story zone — everything before exercises OR glossary OR author
    # (whichever comes first)
    story_end_candidates = [p for p in [
        exercise_pos, glossary_pos, author_pos
    ] if p is not None]

    if story_end_candidates:
        story_end = min(story_end_candidates)
        story_zone = text[:story_end].strip()
        if len(story_zone) > 200:  # sanity check — must have real content
            zones["story_zone"] = story_zone
            print(f"         [Zones] Story zone: {len(story_zone)} chars")
        else:
            print(f"         [Zones] Story zone too short — using full text fallback")

    # Exercise zone — from exercise start to ICT Corner or end
    if exercise_pos is not None:
        exercise_end = ict_pos if ict_pos is not None else len(text)
        # Also stop at author if author comes after exercises
        if author_pos is not None and author_pos > exercise_pos:
            exercise_end = min(exercise_end, author_pos)
        exercise_zone = text[exercise_pos:exercise_end].strip()
        if len(exercise_zone) > 100:
            zones["exercise_zone"] = exercise_zone
            print(f"         [Zones] Exercise zone: {len(exercise_zone)} chars")

    # Glossary zone — from glossary start to exercise start or author
    if glossary_pos is not None:
        glossary_end_candidates = [p for p in [
            exercise_pos, author_pos, ict_pos
        ] if p is not None and p > glossary_pos]
        glossary_end = min(glossary_end_candidates) if glossary_end_candidates else len(text)
        glossary_zone = text[glossary_pos:glossary_end].strip()
        if len(glossary_zone) > 50:
            zones["glossary_zone"] = glossary_zone
            print(f"         [Zones] Glossary zone: {len(glossary_zone)} chars")

    # Author zone — from author start to glossary or exercise or ICT
    if author_pos is not None:
        author_end_candidates = [p for p in [
            glossary_pos, exercise_pos, ict_pos
        ] if p is not None and p > author_pos]
        author_end = min(author_end_candidates) if author_end_candidates else len(text)
        author_zone = text[author_pos:author_end].strip()
        if len(author_zone) > 50:
            zones["author_zone"] = author_zone
            print(f"         [Zones] Author zone: {len(author_zone)} chars")

    # ICT zone — from ICT start to end
    if ict_pos is not None:
        ict_zone = text[ict_pos:].strip()
        # Remove next unit overflow if present
        overflow = re.search(r'unit\s*[-–]\s*[2-9]', ict_zone, re.IGNORECASE)
        if overflow:
            ict_zone = ict_zone[:overflow.start()].strip()
        if len(ict_zone) > 50:
            zones["ict_zone"] = ict_zone
            print(f"         [Zones] ICT zone: {len(ict_zone)} chars")

    return zones


def _find_pattern(text: str, patterns: list,
                  use_lower: bool = True) -> int | None:
    """
    Finds the earliest match position for any of the given patterns.
    Returns None if no pattern matches.
    """
    search_text = text.lower() if use_lower else text
    earliest = None
    for pattern in patterns:
        match = re.search(pattern, search_text)
        if match:
            if earliest is None or match.start() < earliest:
                earliest = match.start()
    return earliest


# ============================================================================
# NOISE CLEANING
# ============================================================================

def clean_noise(text: str) -> str:
    """
    Removes pdf2htmlEX noise before any processing.
    - Hash codes like [AAxqOpqdnT]
    - PDF footer lines
    - Next unit overflow
    """
    # Remove hash codes
    text = re.sub(r'\[[A-Za-z0-9]{4,12}\]', '', text)

    # Remove PDF footer lines
    text = re.sub(
        r'\d+th\s+English_Unit_\d+\.indd\s+\d+\s+\d{2}-\d{2}-\d{4}\s+[\d:]+',
        '', text
    )

    # Remove next unit overflow
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

    # Clean up extra blank lines
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
        print("ORIGINAL:", len(raw), "chars")
        print()

        cleaned = clean_noise(raw)
        print("CLEANED:", len(cleaned), "chars")
        print()

        sections = detect_sections(cleaned, "supplementary")
        print("SECTIONS:")
        for k, v in sections.items():
            print(f"  {k}: {v}")
        print()

        print("ZONES:")
        zones = split_into_zones(cleaned)
        for k, v in zones.items():
            if k != "full_text":
                print(f"  {k}: {len(v)} chars")
                print(f"    First 100: {v[:100].strip()}")
                print()
    else:
        print("Usage: python section_detector.py <path_to_txt_file>")