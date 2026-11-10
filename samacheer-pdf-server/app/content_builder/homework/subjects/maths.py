"""Homework profile: Maths, Classes 6–10.

Reading values come from BB's Maths profile (measured on the Class 10
Unit 3 Algebra LP: 10 days, title + meta inside the block, the meta line's
last '|' segment states the day's focus, Day 9 exercise practice and
Day 10 quiz / chapter completion). Unlike BB, Homework keeps the board work
(worked examples), student tasks, closing and vocabulary: the worked
examples show the exact method and level the homework should match.
"""
from .base import SubjectProfile

MATHS = SubjectProfile(
    key="maths",
    display_name="Maths",
    aliases=("math", "mathematics"),

    # Reading
    day_type_pattern=r"\|\s*([^|]+?)\s*$",
    extra_drop_classes=("student-says", "activity-block", "diff-block", "diff-table"),
    max_text_per_day=24000,
    review_keywords=("consolidation", "evaluation day", "chapter completion"),

    # Homework
    audience="Class 10 Tamil Nadu State Board Maths students (about 15 years old)",
    apply_style=(
        "One problem solvable in a few steps with the method taught that day, with numbers "
        "chosen so the answer comes out clean (integers or simple fractions). A short "
        "everyday word problem with small made-up numbers is fine. On review days: prefer "
        "one problem that combines two ideas from the lesson so far."
    ),
    extra_rules=(
        "\n- A problem may follow the pattern of a worked example in the LP, but must use "
        "different numbers or expressions; never repeat a worked example or class exercise."
        "\n- Choose numbers so every intermediate step and the final answer stay simple: "
        "integers or simple fractions, no messy decimals."
        "\n- Small made-up numbers in an everyday problem are fine (2 pens and 3 notebooks "
        "cost 110 rupees), but never present them as real prices or statistics."
        "\n- Use the lesson's own notation and the method the lesson teaches for that day."
    ),
    limits={"MAX_TASK_WORDS": 80, "MAX_HINT_WORDS": 40, "MAX_ANSWER_WORDS": 250},
    pipe_rules=False,   # | is notation (|x|, |A|, P(A|B)); tables only inside [table] fences
)