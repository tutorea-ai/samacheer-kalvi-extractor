"""Homework profile: Physics, Classes 11–12.

Reading values come from BB's Physics profile (measured on the Class 12
Current Electricity LP: 19 days, "Day type:" label on every day,
Day 19 = "Revision · No new content"). Unlike BB, Homework keeps the
Student Task and Closing sections: their numericals and exam questions
show the level the Apply task should match.
"""
from .base import SubjectProfile

PHYSICS = SubjectProfile(
    key="physics",
    display_name="Physics",

    # Reading
    max_text_per_day=12000,
    review_keywords=("revision",),

    # Homework
    audience="Class 11–12 Tamil Nadu State Board Physics students (about 16–17 years old)",
    apply_style=(
        "On formula, numerical or application days: one short numerical solvable in a few "
        "lines with the day's formulas, realistic values in SI units, every needed value "
        "given. On derivation days: reproduce one key step of the derivation or explain why "
        "a step is valid. On process or lab days: explain the measurement procedure, or "
        "calculate a result from given readings. On review days: one numerical that combines "
        "two ideas from the lesson so far."
    ),
    extra_rules=(
        "\n- A numerical may follow the pattern of a worked example or student task in the "
        "LP, but must use different values; never repeat an in-class problem as homework."
        "\n- Values must be physically realistic and consistent: currents, resistances, "
        "voltages and times a student would meet in a lab or a home circuit."
        "\n- Use the LP's symbols and units exactly (for example v_d, μ, ρ, Ω m)."
    ),
    # Numericals give every value with units, often in parts (a) and (b).
    limits={"MAX_TASK_WORDS": 100},
)