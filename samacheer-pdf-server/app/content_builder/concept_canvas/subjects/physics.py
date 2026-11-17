"""Concept Canvas profile: Physics, Classes 11–12.

Reading values copied from Homework's Physics profile (measured on the
Class 12 Current Electricity LP: 19 days, "Day type:" label on every day,
Day 19 = "Revision · No new content"). Only "revision" marks a review day.
"""
from .base import SubjectProfile

PHYSICS = SubjectProfile(
    key="physics",
    display_name="Physics",

    # Reading (same as Homework)
    max_text_per_day=12000,
    review_keywords=("revision",),

    # Concept Canvas
    audience="Class 11–12 Tamil Nadu State Board Physics students (about 16–17 years old)",
    allowed_templates=(
        "step_build", "process_flow", "cycle", "compare", "concept_map",
    ),
    icon_groups=("physics", "general"),
    formulas=True,
    extra_rules=(
        "\n- Visualise the day's ONE central idea; leave side remarks and worked "
        "numericals out of the steps."
        "\n- Formula or derivation days: step_build, ending on the formula as the "
        "highlight step. Process or measurement days: process_flow. Two contrasting "
        "cases (series/parallel, ohmic/non-ohmic): compare."
        "\n- Use the LP's symbols, units and formulas exactly (for example v_d, μ, ρ, "
        "Ω m); never introduce a formula the LP does not teach."
        "\n- A step describes what a component DOES (pushes charge, opposes flow), "
        "never how wires are connected; circuit wiring is not drawn in v1."
        "\n- If the day teaches two topics, visualise the main one (the one with the "
        "day's key formula or most lesson time); the template follows that topic."
    ),
    review_rules=(
        "\n- Check every formula symbol by symbol against the LP text, including "
        "subscripts, powers and units."
    ),
)