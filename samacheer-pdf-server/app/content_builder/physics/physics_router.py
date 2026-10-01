"""
physics_router.py
-----------------
Router for Physics (Class 11-12) LP and QA generation.

Physics is a single-discipline subject (no botany/zoology split), so the
builder is chosen by grade group only.

Builder contract (owned by prompt team):
    LP: physics/lp/grade_1112/physics.py  → physics_lp_1112_builder
    QA: physics/qa/grade_1112/physics.py  → physics_qa_1112_builder
    Both expose: .generate(text: str, metadata: dict) -> str | None

Until the builder files are placed, the import fails gracefully and
generate_lp / generate_qa return None. Content generation is unaffected.

Adding a grade group: add one entry to BUILDERS and _get_grade_group().
"""

from importlib import import_module
from typing import Optional


# ============================================================================
# BUILDER REGISTRY — grade group → mode → (module path, singleton name)
# ============================================================================

BUILDERS = {
    "grade_1112": {
        "lp": (".lp.grade_1112.physics", "physics_lp_1112_builder"),
        "qa": (".qa.grade_1112.physics", "physics_qa_1112_builder"),
    },
}


# ============================================================================
# GRADE GROUP MAPPING
# ============================================================================

def _get_grade_group(class_num: int) -> Optional[str]:
    """Map class number to grade group string."""
    if class_num in [11, 12]:
        return "grade_1112"
    print(f"      [Physics Router] ❌ Unknown class: {class_num}")
    return None


# ============================================================================
# BUILDER LOOKUP
# ============================================================================

def _get_builder(grade_group: str, mode: str):
    """
    Return the builder singleton for grade group + mode ("lp" / "qa").
    Returns None if the builder file is not placed yet.
    """
    entry = BUILDERS.get(grade_group, {}).get(mode)
    if not entry:
        print(f"      [Physics Router] ❌ No {mode.upper()} builder registered for {grade_group}")
        return None

    module_path, singleton = entry
    try:
        module = import_module(module_path, package=__package__)
        return getattr(module, singleton)
    except ImportError as e:
        print(f"      [Physics Router] ⏳ {mode.upper()} builder not yet implemented: {grade_group} — {e}")
        return None
    except AttributeError:
        print(f"      [Physics Router] ❌ {module_path} found but '{singleton}' is missing — check builder contract")
        return None


def _generate(mode: str, text: str, metadata: dict) -> Optional[str]:
    class_num = int(metadata.get("class", 0))
    print(f"      [Physics Router] {mode.upper()} request — Class {class_num}")

    grade_group = _get_grade_group(class_num)
    if not grade_group:
        return None

    builder = _get_builder(grade_group, mode)
    if not builder:
        return None

    print(f"      [Physics Router] → {grade_group} {mode.upper()} builder")
    return builder.generate(text, metadata)


# ============================================================================
# PUBLIC API — same signature as every other subject router
# ============================================================================

def generate_lp(text: str, metadata: dict) -> Optional[str]:
    """Generate LP HTML for a Physics chapter."""
    return _generate("lp", text, metadata)


def generate_qa(text: str, metadata: dict) -> Optional[str]:
    """Generate QA HTML for a Physics chapter."""
    return _generate("qa", text, metadata)
