"""
biology_router.py
------------------
Router for all Biology LP and QA generation.

Reads:
    metadata["class"]      → maps to grade group (currently only 1112)
    metadata["discipline"] → maps to discipline builder (botany/zoology)
    mode                   → "lp" or "qa"

Returns:
    Combined HTML string from the correct builder, or None on failure.

Grade group mapping:
    class 11, 12 → grade_1112

Adding a new grade group:
    1. Create folder:  biology/lp/grade_X/ (and biology/qa/grade_X/)
    2. Build builders: biology/lp/grade_X/biology.py etc.
    3. Add mapping:    _get_grade_group() below

Adding a new discipline:
    (Botany and Zoology already share one file per team decision —
    see biology/lp/grade_1112/biology.py module docstring. A genuinely
    new discipline, e.g. a future subject split, would get its own
    builder file and an import branch below, same pattern as SS.)

STATUS (Sept 2026):
    LP  — implemented (botany_lp_1112_builder, zoology_lp_1112_builder)
    QA  — implemented (botany_qa_1112_builder, zoology_qa_1112_builder),
          4-call mark-tier pattern (MCQ/2-mark/3-mark/5-mark+diagram).
          _get_qa_builder() mirrors _get_lp_builder()'s try/import
          pattern — no more special-cased short-circuit.
"""

from typing import Optional


# ============================================================================
# GRADE GROUP MAPPING
# ============================================================================

def _get_grade_group(class_num: int) -> Optional[str]:
    """Map class number to grade group string."""
    if class_num in [11, 12]:
        return "grade_1112"
    else:
        print(f"      [Biology Router] ❌ Unknown class: {class_num}")
        return None


# ============================================================================
# LP BUILDER ROUTER
# ============================================================================

def _get_lp_builder(grade_group: str, discipline: str):
    """
    Return the correct LP builder instance for grade group + discipline.
    Returns None if builder not yet implemented.
    """
    try:
        if grade_group == "grade_1112":
            if discipline == "botany":
                from .lp.grade_1112.biology import botany_lp_1112_builder
                return botany_lp_1112_builder
            elif discipline == "zoology":
                from .lp.grade_1112.biology import zoology_lp_1112_builder
                return zoology_lp_1112_builder
            else:
                print(f"      [Biology Router] ❌ Unknown discipline: {discipline}")
                return None

        else:
            print(f"      [Biology Router] ❌ Unknown grade group: {grade_group}")
            return None

    except ImportError as e:
        print(f"      [Biology Router] ⏳ Builder not yet implemented: {grade_group}/{discipline} — {e}")
        return None


# ============================================================================
# QA BUILDER ROUTER
#
# QA builders now exist (Sept 2026) — biology/qa/grade_1112/biology.py.
# Same mechanics as _get_lp_builder: try the import, catch ImportError
# if the file isn't in place yet at the expected path.
# ============================================================================

def _get_qa_builder(grade_group: str, discipline: str):
    """
    Return the correct QA builder instance for grade group + discipline.
    Returns None if builder not yet implemented.
    """
    try:
        if grade_group == "grade_1112":
            if discipline == "botany":
                from .qa.grade_1112.biology import botany_qa_1112_builder
                return botany_qa_1112_builder
            elif discipline == "zoology":
                from .qa.grade_1112.biology import zoology_qa_1112_builder
                return zoology_qa_1112_builder
            else:
                print(f"      [Biology Router] ❌ Unknown discipline: {discipline}")
                return None

        else:
            print(f"      [Biology Router] ❌ Unknown grade group: {grade_group}")
            return None

    except ImportError as e:
        print(f"      [Biology Router] ⏳ QA builder not yet implemented: {grade_group}/{discipline} — {e}")
        return None


# ============================================================================
# PUBLIC API
# ============================================================================

def generate_lp(text: str, metadata: dict) -> Optional[str]:
    """
    Generate LP HTML for a Biology chapter.

    Args:
        text:     Clean chapter text from EPUB extractor
        metadata: Dict with class, unit, lesson_title, discipline etc.

    Returns:
        Combined LP HTML string, or None on failure.
    """
    class_num  = int(metadata.get("class", 0))
    discipline = metadata.get("discipline", "").lower().strip()

    print(f"      [Biology Router] LP request — Class {class_num} | {discipline.title()}")

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_lp_builder(grade_group, discipline)
    if not builder:
        print(f"      [Biology Router] ❌ No LP builder available for {grade_group}/{discipline}")
        return None

    print(f"      [Biology Router] → {grade_group}/{discipline} LP builder")
    return builder.generate(text, metadata)


def generate_qa(text: str, metadata: dict) -> Optional[str]:
    """
    Generate QA HTML for a Biology chapter.

    Args:
        text:     Clean chapter text from EPUB extractor
        metadata: Dict with class, unit, lesson_title, discipline etc.

    Returns:
        Combined QA HTML string, or None on failure.
    """
    class_num  = int(metadata.get("class", 0))
    discipline = metadata.get("discipline", "").lower().strip()

    print(f"      [Biology Router] QA request — Class {class_num} | {discipline.title()}")

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_qa_builder(grade_group, discipline)
    if not builder:
        print(f"      [Biology Router] ❌ No QA builder available for {grade_group}/{discipline}")
        return None

    print(f"      [Biology Router] → {grade_group}/{discipline} QA builder")
    return builder.generate(text, metadata)