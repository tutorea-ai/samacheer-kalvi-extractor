"""
english/english_router.py
--------------------------
Subject-level router for all English LP and QA builders.

Reads:
    metadata["class"]        → determines grade group (67 / 910 / 1112)
    metadata["lesson_type"]  → prose / poem / supplementary / play / drama

Returns:
    HTML string from the correct builder, or None on failure.

Current status:
    grade_910  → ✅ LP builders (prose, poem, supplementary) | ✅ QA builder
    grade_67   → ⏳ builders not yet implemented
    grade_1112 → ⏳ builders not yet implemented
"""

from typing import Optional


def _resolve_grade_group(class_num) -> Optional[str]:
    try:
        n = int(str(class_num).strip())
    except (ValueError, TypeError):
        print(f"   [English Router] ❌ Invalid class number: '{class_num}'")
        return None
    if n in (6, 7):
        return "grade_67"
    elif n in (8, 9, 10):
        return "grade_910"
    elif n in (11, 12):
        return "grade_1112"
    else:
        print(f"   [English Router] ❌ Class {n} not in any grade group")
        return None


def _resolve_lesson_type(raw_type: str) -> str:
    t = (raw_type or "prose").lower().strip()
    if t in ("play", "drama"):
        return "supplementary"
    if t in ("poem", "poetry"):
        return "poem"
    if t in ("supplementary", "sup", "reader", "supplementary reader"):
        return "supplementary"
    return "prose"


def generate_lp(text: str, metadata: dict) -> Optional[str]:
    class_num   = metadata.get("class", "")
    lesson_type = _resolve_lesson_type(metadata.get("lesson_type", "prose"))
    grade_group = _resolve_grade_group(class_num)
    if not grade_group:
        return None
    print(f"   [English Router] LP → grade: {grade_group} | type: {lesson_type}")

    if grade_group == "grade_910":
        if lesson_type == "prose":
            from .lp.grade_910.prose import english_prose_lp_910_builder
            return english_prose_lp_910_builder.generate(text, metadata)
        elif lesson_type == "poem":
            from .lp.grade_910.poem import english_poem_lp_910_builder
            return english_poem_lp_910_builder.generate(text, metadata)
        elif lesson_type == "supplementary":
            from .lp.grade_910.supplementary import english_supplementary_lp_910_builder
            return english_supplementary_lp_910_builder.generate(text, metadata)
        else:
            print(f"   [English Router] ❌ Unknown lesson_type: '{lesson_type}'")
            return None

    elif grade_group == "grade_67":
        try:
            if lesson_type == "prose":
                from .lp.grade_67.prose import english_prose_lp_67_builder
                return english_prose_lp_67_builder.generate(text, metadata)
            elif lesson_type == "poem":
                from .lp.grade_67.poem import english_poem_lp_67_builder
                return english_poem_lp_67_builder.generate(text, metadata)
            elif lesson_type == "supplementary":
                from .lp.grade_67.supplementary import english_supplementary_lp_67_builder
                return english_supplementary_lp_67_builder.generate(text, metadata)
        except ImportError:
            print(f"   [English Router] ⏳ English LP grade_67 not yet implemented")
            return None

    elif grade_group == "grade_1112":
        try:
            if lesson_type == "prose":
                from .lp.grade_1112.prose import english_prose_lp_1112_builder
                return english_prose_lp_1112_builder.generate(text, metadata)
            elif lesson_type == "poem":
                from .lp.grade_1112.poem import english_poem_lp_1112_builder
                return english_poem_lp_1112_builder.generate(text, metadata)
            elif lesson_type == "supplementary":
                from .lp.grade_1112.supplementary import english_supplementary_lp_1112_builder
                return english_supplementary_lp_1112_builder.generate(text, metadata)
        except ImportError:
            print(f"   [English Router] ⏳ English LP grade_1112 not yet implemented")
            return None

    return None


def generate_qa(text: str, metadata: dict) -> Optional[str]:
    class_num   = metadata.get("class", "")
    grade_group = _resolve_grade_group(class_num)
    if not grade_group:
        return None
    print(f"   [English Router] QA → grade: {grade_group}")

    if grade_group == "grade_910":
        from .qa.grade_910.english import english_qa_910_builder
        return english_qa_910_builder.generate(text, metadata)

    elif grade_group == "grade_67":
        try:
            from .qa.grade_67.english import english_qa_67_builder
            return english_qa_67_builder.generate(text, metadata)
        except ImportError:
            print(f"   [English Router] ⏳ English QA grade_67 not yet implemented")
            return None

    elif grade_group == "grade_1112":
        try:
            from .qa.grade_1112.english import english_qa_1112_builder
            return english_qa_1112_builder.generate(text, metadata)
        except ImportError:
            print(f"   [English Router] ⏳ English QA grade_1112 not yet implemented")
            return None

    return None