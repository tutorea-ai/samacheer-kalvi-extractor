"""
subjects/biology.py
-------------------
Biology 11–12 (Botany / Zoology), new LP format.
Biology 12 LPs put the day title and a meta table (Focus, Day, Key Ratios…) just
BEFORE each day block; lp_parser reads them there. There is no "Day type:" label,
so card types come from the title + meta table + lesson folder.
"""

from .base import SubjectProfile


BIOLOGY = SubjectProfile(
    key="biology",
    display_name="Biology",

    card_types=[
        ("concept", "Concepts"),
        ("cross",   "Crosses & Ratios"),
        ("terms",   "Key Terms"),
    ],

    # Matched against "<meta table> | <title> | <lesson folder>". First match wins.
    # No bare "cross": it would match "across".
    type_keywords=[
        ("whole-chapter revision",  "recap"),     # Day 14's Focus. NOT the title "Revision and Assessment":
        ("no new content",          "recap"),     # Days 5, 6, 9 use that title but teach new topics
        ("glossary",                "terms"),
        ("key ratios",              "cross"),
        ("monohybrid",              "cross"),
        ("dihybrid",                "cross"),
        ("test cross",              "cross"),
        ("gene interaction",        "cross"),
        ("lethal",                  "cross"),
        ("polygenic",               "cross"),
        ("epistasis",               "cross"),
        ("_botany",                 "concept"),
        ("_zoology",                "concept"),
        ("botany",                  "concept"),
        ("zoology",                 "concept"),
    ],

    type_guide={
        "concept": "the key idea or law in plain words, the experiment or evidence behind it, and the key terms",
        "cross":   "the parents and their genotypes, the cross in order (P → F1 → F2), and the phenotypic and genotypic ratios",
        "terms":   "key terms, each with its one-line meaning from the material",
    },

    audience="the HSC board examinations",
    notation=(
        "Copy genotypes and allele symbols exactly, keeping capital and small letters (TT, Tt, tt, RrYy).\n"
        "Write ratios with spaced colons (3 : 1, 9 : 3 : 3 : 1, 1 : 2 : 1) and crosses with × (Tt × Tt).\n"
        "Write scientific names, terms and numbers exactly as they appear in the material.\n"
        'Never put "_" or "^" next to a letter or number.'
    ),
    example_one='"Why did Mendel choose the garden pea for his experiments?"',
    example_two='"What are the key facts about lethal genes and pleiotropy?"',
    formula_rule='- formula: the day\'s key cross or ratio (for example "Tt × Tt → 3 : 1 | genotypic 1 : 2 : 1"), '
                 'joined with " | ", or "" if the day has none.',
    tip_ideas="advice from the material's exam-prep notes when there are any; otherwise a ratio to learn exactly, "
              "a diagram to draw, or two terms students mix up — never promise marks",
    extra_rules=(
        "\n- For a cross card: give the parents' genotypes, then F1, then F2 in order, and end with the"
        "\n  ratios exactly as the material states them."
        "\n- For a key-terms card: each bullet is one term with its meaning, taken from the material."
        "\n- Never add a fact, ratio, example or scientific name that the material does not state."
        "\n- Use only the explanation, board work and exam-prep notes — not the teacher's warm-up"
        "\n  stories, analogies about the students' families, or activities."
        "\n- Each card's exam_tip must give different advice from the other cards' tips."
        "\n- ONE question means no second question word after a comma or \"and\" — never"
        "\n  \", and how\", \", and why\", \"and what\", \"and which\". If a day covers two things, name both"
        "\n  topics with \"and\" in ONE question (good: \"What are the key facts about lethal genes and pleiotropy?\")."
    ),
    recap_formula_note=" Include the key ratios where they exist.",

    # Reading options (from the step 4 measurement)
    type_from_meta=True,
    drop_classes=(
        "lp-section-opening", "lp-section-activity", "lp-activity-block", "ccq-block",
        "ccq-tamil", "student-says", "homework-block", "lead-tamil",
    ),
    drop_line_prefixes=("[", "⏱", "preview:"),
    board_classes=("board-work", "lp-board-work"),
    max_text_per_day=10000,
    flatten_inline=True,

    # Recap: Day 14 (last "Revision and Assessment") from its text — it has little board work
    recap_day="last",
    title_from_focus=(r"revision and assessment",),
    recap_from_text=True,

    # A little above Physics (longer terms, ratios); adjust after the first run
    limits={
        "MAX_BULLET_WORDS": 22, "HARD_BULLET_WORDS": 30,
        "MAX_PROMPT_WORDS": 24,
        "MAX_BACK_CHARS": 680, "MAX_RECAP_BACK_CHARS": 860,
    },
)