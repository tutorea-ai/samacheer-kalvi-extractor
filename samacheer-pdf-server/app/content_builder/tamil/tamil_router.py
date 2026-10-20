"""
tamil/tamil_router.py
---------------------
Subject-level router for Tamil (language subject) LP, QA and Content builders.

Reads:
    metadata["class"]        → grade group (grade_67 / grade_910 / grade_1112)
    metadata["lesson_type"]  → poem / prose / supplementary / grammar / thirukural
                               (comes from the index JSON, never hardcoded here)

Builder lookup (first match wins), e.g. LP, Class 6, poem:
    1. type-specific: .lp.grade_67.poem   → tamil_poem_lp_67_builder
    2. shared:        .lp.grade_67.tamil  → tamil_lp_67_builder  (branches on lesson_type itself)

Every builder exposes .generate(text, metadata) → HTML string (body only).
A builder file that doesn't exist yet → logged as "not yet implemented", returns None.
"""

import importlib
from typing import Optional

TAG = "[Tamil Router]"


def _resolve_grade_group(class_num) -> Optional[str]:
    try:
        n = int(str(class_num).strip())
    except (ValueError, TypeError):
        print(f"   {TAG} ❌ Invalid class number: '{class_num}'")
        return None
    if n in (6, 7):
        return "grade_67"
    if n in (8, 9, 10):
        return "grade_910"
    if n in (11, 12):
        return "grade_1112"
    print(f"   {TAG} ❌ Class {n} not in any grade group")
    return None


def _import_builder(kind: str, grade_group: str, module_name: str, attr: str):
    full = f"{__package__}.{kind}.{grade_group}.{module_name}"
    try:
        module = importlib.import_module(full)
    except ModuleNotFoundError as e:
        # Only "this builder file / folder doesn't exist yet" counts as not implemented.
        # A missing dependency INSIDE an existing builder must surface as a real error.
        if e.name and full.startswith(e.name):
            return None
        raise
    return getattr(module, attr, None)


def _find_builder(kind: str, metadata: dict):
    grade_group = _resolve_grade_group(metadata.get("class", ""))
    if not grade_group:
        return None
    suffix      = grade_group.replace("grade_", "")
    lesson_type = (metadata.get("lesson_type") or "").lower().strip()

    candidates = []
    if lesson_type:
        candidates.append((lesson_type, f"tamil_{lesson_type}_{kind}_{suffix}_builder"))
    candidates.append(("tamil", f"tamil_{kind}_{suffix}_builder"))

    for module_name, attr in candidates:
        builder = _import_builder(kind, grade_group, module_name, attr)
        if builder:
            print(f"   {TAG} {kind.upper()} → {grade_group} | type: {lesson_type} | {module_name}.{attr}")
            return builder

    print(f"   {TAG} ⏳ No {kind.upper()} builder yet for {grade_group} / {lesson_type or 'any type'}")
    return None


def generate_lp(text: str, metadata: dict) -> Optional[str]:
    builder = _find_builder("lp", metadata)
    return builder.generate(text, metadata) if builder else None


def generate_qa(text: str, metadata: dict) -> Optional[str]:
    builder = _find_builder("qa", metadata)
    return builder.generate(text, metadata) if builder else None


def generate_content(text: str, metadata: dict) -> Optional[str]:
    builder = _find_builder("content", metadata)
    return builder.generate(text, metadata) if builder else None