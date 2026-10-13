"""
subjects/physics.py
-------------------
Physics (Classes 11–12). Values moved unchanged from card_types.py,
lp_parser.py (TYPE_KEYWORDS) and builder.py (TYPE_GUIDE, prompts).
"""

from .base import SubjectProfile


PHYSICS = SubjectProfile(
    key="physics",
    display_name="Physics",

    card_types=[
        ("concept",     "Concepts"),
        ("formula",     "Formulas"),
        ("derivation",  "Derivations"),
        ("device",      "Devices & Experiments"),
        ("application", "Applications"),
    ],

    # LP "Day type" text → card type (keyword match, order matters)
    type_keywords=[
        ("revision",    "recap"),
        ("derivation",  "derivation"),      # also "Derivation + Numerical"
        ("process",     "device"),          # "Process / Working": instruments & experiments
        ("working",     "device"),
        ("formula",     "formula"),
        ("numerical",   "formula"),
        ("application", "application"),
        ("comparison",  "concept"),
        ("concept",     "concept"),
    ],

    type_guide={
        "concept":     "definitions, properties, key statements, important distinctions",
        "formula":     "the law or relation, what each symbol means with SI units, the common numerical trick",
        "derivation":  "the starting idea, the key steps in order, and the final result",
        "device":      "principle, key parts / construction, how it works, what it is used for",
        "application": "where and how it is used, with the reason",
    },

    audience="SSLC / HSC board examinations",
    notation=(
        "Notation: use Unicode where it exists (×, ², ³, ⁻¹, ₀, ₁, ₂, √, π, ε, μ, Ω, Δ, →, q₁, ε₀, 10⁻¹⁹).\n"
        'Write fractions and division with "/" exactly as the textbook does (R = ρl/A, I = V/R) — never "÷".\n'
        "For a subscript with no Unicode form write an underscore: v_d, R_eq, ε_eq, I_g, r_min.\n"
        "For a superscript with no Unicode form write a caret: x^n."
    ),
    example_one='"How does drift velocity depend on the electric field?"',
    example_two='"What are the key facts about electric current and drift velocity?"',
    formula_rule='- formula: the single most important formula for that day, or "" if none.',
    tip_ideas="what to state first, a unit to convert, a diagram to draw, a common mistake",
    extra_rules=(
        "\n- For a derivation card: the bullets are the derivation steps in order, and"
        "\n  the last bullet is the final result. No side facts or extra formulas."
    ),
    recap_formula_note=" Include the key formula where one exists.",
)