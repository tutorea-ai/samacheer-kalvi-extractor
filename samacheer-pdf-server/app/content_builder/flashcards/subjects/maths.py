"""
subjects/maths.py
-----------------
Maths (new LP format). Like Social Science, the LP has no "Day type:" label, so
card types come from the day title (+ meta line and folder name for the fallback).
Prompts start from Physics: Unicode notation, "/" for division, a real formula field.
"""

from .base import SubjectProfile


MATHS = SubjectProfile(
    key="maths",
    display_name="Maths",
    aliases=("math", "mathematics"),            # same names processor.py treats as maths

    card_types=[
        ("concept",  "Concepts & Methods"),
        ("graph",    "Graphs"),
        ("problems", "Word Problems"),
        ("practice", "Practice"),
    ],

    # Matched against "<meta line> | <title> | <lesson folder>". First match wins.
    # The last line catches every other Maths day ("| Maths |" is in every meta line).
    type_keywords=[
        ("chapter completion", "recap"),        # Day 10 "Quiz + Book-back Marking + Chapter Completion"
        ("revision",           "recap"),
        ("exercise practice",  "practice"),
        ("problems involving", "problems"),
        ("word problem",       "problems"),
        ("graph",              "graph"),
        ("maths",              "concept"),
    ],

    type_guide={
        "concept":  "the definition or rule, the key formula with what each symbol means, and the method steps in order",
        "graph":    "how to draw or read the graph, what its shape or points show, and the key result",
        "problems": "how the words become an equation, the solving steps in order, and the answer from the material's example",
        "practice": "the problem types practised, the method for each, and the mistakes the material warns about",
    },

    audience="their Maths examinations",
    notation=(
        "Notation: use Unicode where it exists (×, ², ³, √, π, ≤, ≥, ≠, ±, a₁, b₂, x²).\n"
        'Write fractions with "/" ((x + 1)/(x − 2)); use "÷" only to divide one expression by another, as the textbook does.\n'
        "For a subscript with no Unicode form write an underscore: a_n, S_n.\n"
        "For a superscript with no Unicode form write a caret: x^n, a^(m+n)."
    ),
    example_one='"How do you find the GCD of two polynomials by long division?"',
    example_two='"What are the key methods for square roots of polynomials and graphs of variation?"',
    formula_rule='- formula: the day\'s key formula; if the day has two or three key formulas, give them all joined with " | ", or "" if none.',
    tip_ideas="a step students often skip, a sign or bracket mistake to avoid, how to set out the working, "
              "a quick way to check the answer — never promise marks",
    extra_rules=(
        "\n- For a method or worked-example card: the bullets are the steps in order, and the last"
        "\n  bullet is the result (with the example's answer if the material gives one)."
        "\n- Copy formulas and example numbers exactly from the material; never invent a new example or answer."
        "\n- Use only the explanation, formula box and board work — not the teacher's warm-up stories,"
        "\n  real-life hooks or activities."
        "\n- Each card's exam_tip must give different advice from the other cards' tips."
        "\n- ONE question means no second question word after a comma or \"and\" — never"
        "\n  \", and how\", \", and why\", \"and what\", \"and which\". If a day covers two things, ask about the idea"
        "\n  that joins them, or name both topics with \"and\" in ONE question (good: \"What are the key"
        "\n  methods for square roots of polynomials and graphs of variation?\"). Never use section numbers"
        "\n  or \"|\" in the question."
    ),
    recap_formula_note=" Include the key formula where one exists.",
    tip_kind="exam",

    # Reading options (from the step 3 measurement)
    type_from_meta=True,
    drop_classes=(
        "lp-section-opening", "ccq-block", "lp-section-student-task", "activity-block",
        "homework-block", "diff-block", "diff-table", "student-says", "teacher-says",
        "lp-section-label",
    ),
    drop_line_prefixes=("[", "⏱", "preview:"),
    max_text_per_day=13500,           # days are 5.5–13K after drops; keeps every day's last example

    # Formula-heavy bullets: symbols (=, −, >) count as words, and a day covers 2–3 sections
    limits={
        "MAX_BULLET_WORDS": 24, "HARD_BULLET_WORDS": 32,
        "MAX_PROMPT_WORDS": 24,
        "MAX_BACK_CHARS": 720, "MAX_RECAP_BACK_CHARS": 900,
    },
    flatten_inline=True,
)