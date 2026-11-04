"""Beyond the Book profile: Maths, Classes 6–10.

Values come from the Class 10 Unit 3 Algebra LP: 10 days, title + meta
inside the block, meta's last '|' segment states the day's focus, days of
10–23k chars mostly worked examples (board work), Day 9 exercise practice
and Day 10 quiz / chapter completion.
"""
from .base import SubjectProfile

MATHS = SubjectProfile(
    key="maths",
    display_name="Maths",
    aliases=("math", "mathematics"),

    # Reading: the focus is the meta line's last segment.
    day_type_pattern=r"\|\s*([^|]+?)\s*$",
    extra_drop_classes=("board-work", "lp-section-student-task", "lp-section-closing",
                        "student-says", "activity-block", "homework-block", "vocab-block",
                        "diff-block", "diff-table"),
    max_text_per_day=9000,
    recap_keywords=("consolidation", "evaluation day", "chapter completion"),

    # Cards
    audience="Class 10 Tamil Nadu State Board Maths students (about 15 years old)",
    building_mode="card",
    try_this=False,
    pictures=True,
    picture_people=(
        "a school boy of about 15", "a school girl of about 15",
        "a boy and a girl, classmates of about 15", "a school girl of about 15",
        "a school boy of about 15", "three classmates of about 15, boys and girls",
    ),
    extra_rules=(
        "\n- Real uses of algebra are everyday reasoning students do themselves: sharing a"
        "\n  bill, comparing phone plans, mixing quantities, the area of a plot, a marks"
        "\n  table. Never claim professionals solve this exact kind of equation unless that"
        "\n  is common knowledge."
        "\n- Small made-up numbers in an everyday example are fine (2 pens and 3 notebooks"
        "\n  cost 110 rupees), but never present them as real prices or statistics."
        "\n- Pictures show the everyday situation itself, never a notebook, textbook,"
        "\n  worksheet or board with working on it."
    ),
)