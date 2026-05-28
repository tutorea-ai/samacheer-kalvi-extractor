"""
science_router.py
-----------------
Router for all Science LP and QA generation.

Reads:
    metadata["class"]      → maps to grade group (67, 8, 910)
    metadata["discipline"] → maps to discipline builder
    mode                   → "lp" or "qa"

Grade group mapping:
    class 6, 7  → grade_67
    class 8     → grade_8  (same as grade_910 builders for now)
    class 9, 10 → grade_910

Discipline mapping:
    physics          → physics.py
    chemistry        → chemistry.py
    biology          → biology.py
    computer_science → computer_science.py
"""

from typing import Optional


# ============================================================================
# GRADE GROUP MAPPING
# ============================================================================

def _get_grade_group(class_num: int) -> Optional[str]:
    if class_num in [6, 7]:
        return "grade_67"
    elif class_num in [8, 9, 10]:
        return "grade_910"
    else:
        print(f"      [Science Router] ❌ Unknown class: {class_num}")
        return None


# ============================================================================
# DISCIPLINE NORMALISATION
# ============================================================================

def _normalise_discipline(discipline: str) -> Optional[str]:
    """Normalise discipline string to internal key."""
    d = discipline.lower().strip().replace(" ", "_").replace("-", "_")
    mapping = {
        "physics":          "physics",
        "chemistry":        "chemistry",
        "biology":          "biology",
        "computer_science": "computer_science",
        "computer":         "computer_science",
        "cs":               "computer_science",
    }
    result = mapping.get(d)
    if not result:
        print(f"      [Science Router] ❌ Unknown discipline: '{discipline}'")
    return result


# ============================================================================
# LP BUILDER ROUTER
# ============================================================================

def _get_lp_builder(grade_group: str, discipline: str):
    try:
        if grade_group == "grade_910":
            if discipline == "physics":
                from .lp.grade_910.physics import physics_lp_910_builder
                return physics_lp_910_builder
            elif discipline == "chemistry":
                from .lp.grade_910.chemistry import chemistry_lp_910_builder
                return chemistry_lp_910_builder
            elif discipline == "biology":
                from .lp.grade_910.biology import biology_lp_910_builder
                return biology_lp_910_builder
            elif discipline == "computer_science":
                from .lp.grade_910.computer_science import computer_science_lp_910_builder
                return computer_science_lp_910_builder
            else:
                print(f"      [Science Router] ❌ Unknown discipline: {discipline}")
                return None

        elif grade_group == "grade_67":
            if discipline == "physics":
                from .lp.grade_67.physics import physics_lp_67_builder
                return physics_lp_67_builder
            elif discipline == "chemistry":
                from .lp.grade_67.chemistry import chemistry_lp_67_builder
                return chemistry_lp_67_builder
            elif discipline == "biology":
                from .lp.grade_67.biology import biology_lp_67_builder
                return biology_lp_67_builder
            elif discipline == "computer_science":
                from .lp.grade_67.computer_science import computer_science_lp_67_builder
                return computer_science_lp_67_builder
            else:
                print(f"      [Science Router] ❌ Unknown discipline: {discipline}")
                return None

        else:
            print(f"      [Science Router] ❌ Unknown grade group: {grade_group}")
            return None

    except ImportError as e:
        print(f"      [Science Router] ⏳ Builder not yet implemented: {grade_group}/{discipline} — {e}")
        return None


# ============================================================================
# QA BUILDER ROUTER
# ============================================================================

def _get_qa_builder(grade_group: str, discipline: str):
    try:
        if grade_group == "grade_910":
            if discipline == "physics":
                from .qa.grade_910.physics import physics_qa_910_builder
                return physics_qa_910_builder
            elif discipline == "chemistry":
                from .qa.grade_910.chemistry import chemistry_qa_910_builder
                return chemistry_qa_910_builder
            elif discipline == "biology":
                from .qa.grade_910.biology import biology_qa_910_builder
                return biology_qa_910_builder
            elif discipline == "computer_science":
                from .qa.grade_910.computer_science import computer_science_qa_910_builder
                return computer_science_qa_910_builder
            else:
                print(f"      [Science Router] ❌ Unknown discipline: {discipline}")
                return None

        elif grade_group == "grade_67":
            if discipline == "physics":
                from .qa.grade_67.physics import physics_qa_67_builder
                return physics_qa_67_builder
            elif discipline == "chemistry":
                from .qa.grade_67.chemistry import chemistry_qa_67_builder
                return chemistry_qa_67_builder
            elif discipline == "biology":
                from .qa.grade_67.biology import biology_qa_67_builder
                return biology_qa_67_builder
            elif discipline == "computer_science":
                from .qa.grade_67.computer_science import computer_science_qa_67_builder
                return computer_science_qa_67_builder
            else:
                print(f"      [Science Router] ❌ Unknown discipline: {discipline}")
                return None

        else:
            print(f"      [Science Router] ❌ Unknown grade group: {grade_group}")
            return None

    except ImportError as e:
        print(f"      [Science Router] ⏳ QA builder not yet implemented: {grade_group}/{discipline} — {e}")
        return None


# ============================================================================
# PUBLIC API
# ============================================================================

def generate_lp(text: str, metadata: dict) -> Optional[str]:
    class_num  = int(metadata.get("class", 0))
    discipline = _normalise_discipline(metadata.get("discipline", ""))

    print(f"      [Science Router] LP request — Class {class_num} | {discipline}")

    if not discipline:
        return None

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_lp_builder(grade_group, discipline)
    if not builder:
        print(f"      [Science Router] ❌ No LP builder for {grade_group}/{discipline}")
        return None

    print(f"      [Science Router] → {grade_group}/{discipline} LP builder")
    return builder.generate(text, metadata)


def generate_qa(text: str, metadata: dict) -> Optional[str]:
    class_num  = int(metadata.get("class", 0))
    discipline = _normalise_discipline(metadata.get("discipline", ""))

    print(f"      [Science Router] QA request — Class {class_num} | {discipline}")

    if not discipline:
        return None

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_qa_builder(grade_group, discipline)
    if not builder:
        print(f"      [Science Router] ❌ No QA builder for {grade_group}/{discipline}")
        return None

    print(f"      [Science Router] → {grade_group}/{discipline} QA builder")
    return builder.generate(text, metadata)