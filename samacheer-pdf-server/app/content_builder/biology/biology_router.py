"""
biology_router.py
-----------------
Router for all Biology LP and QA generation.
Handles Class 11 and 12 — Botany and Zoology.

Grade group:
    class 11, 12 → grade_1112
"""

from typing import Optional


def _get_grade_group(class_num: int) -> Optional[str]:
    if class_num in [11, 12]:
        return "grade_1112"
    else:
        print(f"      [Biology Router] ❌ Unknown class: {class_num}")
        return None


def _normalise_discipline(discipline: str) -> Optional[str]:
    d = discipline.lower().strip()
    mapping = {
        "botany":  "botany",
        "zoology": "zoology",
    }
    result = mapping.get(d)
    if not result:
        print(f"      [Biology Router] ❌ Unknown discipline: '{discipline}'")
    return result


def _get_lp_builder(grade_group: str, discipline: str):
    try:
        if grade_group == "grade_1112":
            if discipline == "botany":
                from .lp.grade_1112.botany import botany_lp_1112_builder
                return botany_lp_1112_builder
            elif discipline == "zoology":
                from .lp.grade_1112.zoology import zoology_lp_1112_builder
                return zoology_lp_1112_builder
            else:
                print(f"      [Biology Router] ❌ Unknown discipline: {discipline}")
                return None
        else:
            print(f"      [Biology Router] ❌ Unknown grade group: {grade_group}")
            return None
    except ImportError as e:
        print(f"      [Biology Router] ⏳ LP builder not yet implemented: {grade_group}/{discipline} — {e}")
        return None


def _get_qa_builder(grade_group: str, discipline: str):
    try:
        if grade_group == "grade_1112":
            if discipline == "botany":
                from .qa.grade_1112.botany import botany_qa_1112_builder
                return botany_qa_1112_builder
            elif discipline == "zoology":
                from .qa.grade_1112.zoology import zoology_qa_1112_builder
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


def generate_lp(text: str, metadata: dict) -> Optional[str]:
    class_num  = int(metadata.get("class", 0))
    discipline = _normalise_discipline(metadata.get("discipline", ""))

    print(f"      [Biology Router] LP request — Class {class_num} | {discipline}")

    if not discipline:
        return None

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_lp_builder(grade_group, discipline)
    if not builder:
        print(f"      [Biology Router] ❌ No LP builder for {grade_group}/{discipline}")
        return None

    print(f"      [Biology Router] → {grade_group}/{discipline} LP builder")
    return builder.generate(text, metadata)


def generate_qa(text: str, metadata: dict) -> Optional[str]:
    class_num  = int(metadata.get("class", 0))
    discipline = _normalise_discipline(metadata.get("discipline", ""))

    print(f"      [Biology Router] QA request — Class {class_num} | {discipline}")

    if not discipline:
        return None

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_qa_builder(grade_group, discipline)
    if not builder:
        print(f"      [Biology Router] ❌ No QA builder for {grade_group}/{discipline}")
        return None

    print(f"      [Biology Router] → {grade_group}/{discipline} QA builder")
    return builder.generate(text, metadata)