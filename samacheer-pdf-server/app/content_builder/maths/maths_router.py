"""
maths_router.py
---------------
Router for all Maths LP and QA generation.

Reads:
    metadata["class"] → maps to grade group (67, 910)
    mode              → "lp" or "qa"

Grade group mapping:
    class 6, 7  → grade_67
    class 8-10  → grade_910

No disciplines — Maths is Type C linear.
"""

from typing import Optional


def _get_grade_group(class_num: int) -> Optional[str]:
    if class_num in [6, 7]:
        return "grade_67"
    elif class_num in [8, 9, 10]:
        return "grade_910"
    else:
        print(f"      [Maths Router] ❌ Unknown class: {class_num}")
        return None


def _get_lp_builder(grade_group: str):
    try:
        if grade_group == "grade_910":
            from .lp.grade_910.maths import maths_lp_910_builder
            return maths_lp_910_builder
        elif grade_group == "grade_67":
            from .lp.grade_67.maths import maths_lp_67_builder
            return maths_lp_67_builder
        else:
            print(f"      [Maths Router] ❌ Unknown grade group: {grade_group}")
            return None
    except ImportError as e:
        print(f"      [Maths Router] ⏳ LP builder not yet implemented: {grade_group} — {e}")
        return None


def _get_qa_builder(grade_group: str):
    try:
        if grade_group == "grade_910":
            from .qa.grade_910.maths import maths_qa_910_builder
            return maths_qa_910_builder
        elif grade_group == "grade_67":
            from .qa.grade_67.maths import maths_qa_67_builder
            return maths_qa_67_builder
        else:
            print(f"      [Maths Router] ❌ Unknown grade group: {grade_group}")
            return None
    except ImportError as e:
        print(f"      [Maths Router] ⏳ QA builder not yet implemented: {grade_group} — {e}")
        return None


def generate_lp(text: str, metadata: dict) -> Optional[str]:
    class_num = int(metadata.get("class", 0))
    print(f"      [Maths Router] LP request — Class {class_num}")

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_lp_builder(grade_group)
    if not builder:
        print(f"      [Maths Router] ❌ No LP builder for {grade_group}")
        return None

    print(f"      [Maths Router] → {grade_group} LP builder")
    return builder.generate(text, metadata)


def generate_qa(text: str, metadata: dict) -> Optional[str]:
    class_num = int(metadata.get("class", 0))
    print(f"      [Maths Router] QA request — Class {class_num}")

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_qa_builder(grade_group)
    if not builder:
        print(f"      [Maths Router] ❌ No QA builder for {grade_group}")
        return None

    print(f"      [Maths Router] → {grade_group} QA builder")
    return builder.generate(text, metadata)