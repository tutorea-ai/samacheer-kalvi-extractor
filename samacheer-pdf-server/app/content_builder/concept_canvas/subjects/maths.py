"""Concept Canvas profile: Maths, Classes 6–10.

Reading values copied from Homework's Maths profile (measured on the
Class 10 Unit 3 Algebra LP: 10 days, title + meta inside the block, the meta
line's last '|' segment states the day's focus, Day 9 exercise practice and
Day 10 quiz / chapter completion).
"""
from .base import SubjectProfile

MATHS = SubjectProfile(
    key="maths",
    display_name="Maths",
    aliases=("math", "mathematics"),

    # Reading (same as Homework)
    day_type_pattern=r"\|\s*([^|]+?)\s*$",
    extra_drop_classes=("student-says", "activity-block", "diff-block", "diff-table"),
    max_text_per_day=24000,
    review_keywords=("consolidation", "evaluation day", "chapter completion"),

    # Concept Canvas
    audience="Class 10 Tamil Nadu State Board Maths students (about 15 years old)",
    allowed_templates=("step_build", "process_flow", "compare", "concept_map"),
    icon_groups=("general",),
    formulas=True,
    formula_text_words=3,       # working lines carry labels: \text{new divisor}, \text{next term}
    formula_relation=False,     # showing a matrix or an expression alone is a valid step
    extra_rules=(
        "\n- Show the day's method on ONE worked example from the lesson, step by step: each "
        "step's formula is the next line of working, and the highlight is the final result."
        "\n- Use the lesson's own example, notation and method exactly; never invent a "
        "method or a shortcut the lesson does not teach."
        "\n- Every expression, equation or matrix goes in formula; text says in words what "
        "the step does (for example 'Add the two equations to remove y')."
        "\n- Two contrasting cases (for example unique / no / infinite solutions, or "
        "real / equal / no real roots): compare."
        "\n- Icons are rarely useful in maths; leave them out unless one truly shows the step."
        "\n- Pick the SMALLEST worked example in the lesson (for example 2 x 2 matrices, a short "
        "division) so every step of the working fits; never jump to a result whose working "
        "was not shown."
    ),
)