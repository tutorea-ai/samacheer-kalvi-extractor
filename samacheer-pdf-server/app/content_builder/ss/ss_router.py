"""
ss_router.py
------------
Router for all Social Science LP and QA generation.

Reads:
    metadata["class"]      → maps to grade group (67, 8, 910)
    metadata["discipline"] → maps to discipline builder
    mode                   → "lp" or "qa"

Returns:
    Combined HTML string from the correct builder, or None on failure.

Grade group mapping:
    class 6, 7  → grade_67
    class 8     → grade_8
    class 9, 10 → grade_910

Adding a new grade group:
    1. Create folder:  ss/lp/grade_X/
    2. Build builders: ss/lp/grade_X/history.py etc.
    3. Add mapping:    GRADE_MAP below

Adding a new discipline:
    1. Build file:  ss/lp/grade_910/new_discipline.py
    2. Add import:  in _get_lp_builder() below
"""

from typing import Optional


# ============================================================================
# GRADE GROUP MAPPING
# ============================================================================

def _get_grade_group(class_num: int) -> Optional[str]:
    """Map class number to grade group string."""
    if class_num in [6, 7]:
        return "grade_67"
    elif class_num == 8:
        return "grade_8"
    elif class_num in [9, 10]:
        return "grade_910"
    else:
        print(f"      [SS Router] ❌ Unknown class: {class_num}")
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
        if grade_group == "grade_910":
            if discipline == "history":
                from .lp.grade_910.history import history_lp_910_builder
                return history_lp_910_builder
            elif discipline == "civics":
                from .lp.grade_910.civics import civics_lp_910_builder
                return civics_lp_910_builder
            elif discipline == "geography":
                from .lp.grade_910.geography import geography_lp_910_builder
                return geography_lp_910_builder
            elif discipline == "economics":
                from .lp.grade_910.economics import economics_lp_910_builder
                return economics_lp_910_builder
            else:
                print(f"      [SS Router] ❌ Unknown discipline: {discipline}")
                return None

        elif grade_group == "grade_8":
            if discipline == "history":
                from .lp.grade_8.history import history_lp_8_builder
                return history_lp_8_builder
            elif discipline == "civics":
                from .lp.grade_8.civics import civics_lp_8_builder
                return civics_lp_8_builder
            elif discipline == "geography":
                from .lp.grade_8.geography import geography_lp_8_builder
                return geography_lp_8_builder
            elif discipline == "economics":
                from .lp.grade_8.economics import economics_lp_8_builder
                return economics_lp_8_builder
            else:
                print(f"      [SS Router] ❌ Unknown discipline: {discipline}")
                return None

        elif grade_group == "grade_67":
            if discipline == "history":
                from .lp.grade_67.history import history_lp_67_builder
                return history_lp_67_builder
            elif discipline == "civics":
                from .lp.grade_67.civics import civics_lp_67_builder
                return civics_lp_67_builder
            elif discipline == "geography":
                from .lp.grade_67.geography import geography_lp_67_builder
                return geography_lp_67_builder
            elif discipline == "economics":
                from .lp.grade_67.economics import economics_lp_67_builder
                return economics_lp_67_builder
            else:
                print(f"      [SS Router] ❌ Unknown discipline: {discipline}")
                return None

        else:
            print(f"      [SS Router] ❌ Unknown grade group: {grade_group}")
            return None

    except ImportError as e:
        print(f"      [SS Router] ⏳ Builder not yet implemented: {grade_group}/{discipline} — {e}")
        return None


# ============================================================================
# QA BUILDER ROUTER
# ============================================================================

def _get_qa_builder(grade_group: str, discipline: str):
    """
    Return the correct QA builder instance for grade group + discipline.
    Returns None if builder not yet implemented.
    """
    try:
        if grade_group == "grade_910":
            if discipline == "history":
                from .qa.grade_910.history import history_qa_910_builder
                return history_qa_910_builder
            elif discipline == "civics":
                from .qa.grade_910.civics import civics_qa_910_builder
                return civics_qa_910_builder
            elif discipline == "geography":
                from .qa.grade_910.geography import geography_qa_910_builder
                return geography_qa_910_builder
            elif discipline == "economics":
                from .qa.grade_910.economics import economics_qa_910_builder
                return economics_qa_910_builder
            else:
                print(f"      [SS Router] ❌ Unknown discipline: {discipline}")
                return None

        elif grade_group == "grade_8":
            if discipline == "history":
                from .qa.grade_8.history import history_qa_8_builder
                return history_qa_8_builder
            else:
                print(f"      [SS Router] ⏳ QA builder not yet implemented: {grade_group}/{discipline}")
                return None

        elif grade_group == "grade_67":
            if discipline == "history":
                from .qa.grade_67.history import history_qa_67_builder
                return history_qa_67_builder
            else:
                print(f"      [SS Router] ⏳ QA builder not yet implemented: {grade_group}/{discipline}")
                return None

        else:
            print(f"      [SS Router] ❌ Unknown grade group: {grade_group}")
            return None

    except ImportError as e:
        print(f"      [SS Router] ⏳ QA builder not yet implemented: {grade_group}/{discipline} — {e}")
        return None


# ============================================================================
# PUBLIC API
# ============================================================================

def generate_lp(text: str, metadata: dict) -> Optional[str]:
    """
    Generate LP HTML for a Social Science chapter.

    Args:
        text:     Clean chapter text from EPUB extractor
        metadata: Dict with class, unit, lesson_title, discipline etc.

    Returns:
        Combined LP HTML string, or None on failure.
    """
    class_num  = int(metadata.get("class", 0))
    discipline = metadata.get("discipline", "").lower().strip()

    print(f"      [SS Router] LP request — Class {class_num} | {discipline.title()}")

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_lp_builder(grade_group, discipline)
    if not builder:
        print(f"      [SS Router] ❌ No LP builder available for {grade_group}/{discipline}")
        return None

    print(f"      [SS Router] → {grade_group}/{discipline} LP builder")
    return builder.generate(text, metadata)


def generate_qa(text: str, metadata: dict) -> Optional[str]:
    """
    Generate QA HTML for a Social Science chapter.

    Args:
        text:     Clean chapter text from EPUB extractor
        metadata: Dict with class, unit, lesson_title, discipline etc.

    Returns:
        Combined QA HTML string, or None on failure.
    """
    class_num  = int(metadata.get("class", 0))
    discipline = metadata.get("discipline", "").lower().strip()

    print(f"      [SS Router] QA request — Class {class_num} | {discipline.title()}")

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_qa_builder(grade_group, discipline)
    if not builder:
        print(f"      [SS Router] ❌ No QA builder available for {grade_group}/{discipline}")
        return None

    print(f"      [SS Router] → {grade_group}/{discipline} QA builder")
    return builder.generate(text, metadata)