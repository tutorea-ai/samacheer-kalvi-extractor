"""
subjects/socialscience.py
-------------------------
Social Science (History, Geography, Civics, Economics), new LP format.
The LP has no "Day type:" label and no "Content Day" line, so card types come
from the lesson folder suffix (human_evolution_history → "_history") and from
"Map Work" in a day's title.
"""

from .base import SubjectProfile


SOCIALSCIENCE = SubjectProfile(
    key="socialscience",            # the API lowercases "SocialScience" → "socialscience"
    display_name="Social Science",

    # Filter chips, in display order. A deck only shows chips that have cards.
    card_types=[
        ("history",   "History"),
        ("geography", "Geography"),
        ("civics",    "Civics"),
        ("economics", "Economics"),
        ("map",       "Map Work"),
    ],

    # Matched against "<meta line> | <title> | <lesson folder>" (type_from_meta).
    # First match wins, so "map work" (from the title) comes before the discipline.
    type_keywords=[
        ("map work",   "map"),
        ("_history",   "history"),
        ("_geography", "geography"),
        ("_civics",    "civics"),
        ("_economics", "economics"),
    ],

    # What each card should focus on (sent to Claude only for types in the batch).
    type_guide={
        "history":   "who, what, when and where; the main developments in order; and why they mattered",
        "geography": "the key features, where they are found, causes and effects, and key terms with meanings",
        "civics":    "what the institution or right is, how it works, and why it matters to citizens",
        "economics": "the key idea in plain words, examples from the material, and key terms with meanings",
        "map":       "the places to locate on the map and what each place is known for, as given in the material",
    },

    # Prompt pieces.
    audience="their Social Science examinations",
    notation=(
        "Write names of people, places, dates and periods exactly as they appear in the material.\n"
        'Never put "_" or "^" next to a letter or number.\n'
        "Use simple, clear English that a student of this class can read quickly."
    ),
    example_one='"How did early humans get their food?"',
    example_two='"How did stone tools and rock paintings show early human skills?"',
    formula_rule='- formula: always "" — Social Science cards have no formula.',
    tip_ideas="a name or date to remember exactly, a place to practise on the map, how to start a short answer, "
              "two terms students often mix up — never promise marks",
    extra_rules=(
        "\n- Use only the textbook facts in the material — not the teacher's warm-up questions,"
        "\n  activities, or examples about the students' own lives."
        "\n- Never add a name, date, place, reason or meaning that the material does not state."
        "\n- For a map card: list only the places the material asks students to locate, each with"
        "\n  what the material says it is known for."
        "\n- Each card's exam_tip must give different advice from the other cards' tips."
        "\n- ONE question means no second question word after a comma or \"and\" — never"
        "\n  \", and how\", \", and why\", \"and what\", \"and which\". If a day covers two things, ask about the idea"
        "\n  that joins them (good: \"How did stone tools and rock paintings show early human skills?\")."
    ),
    recap_formula_note="",
    tip_kind="exam",

    # Reading options (what we learned in step 2).
    type_from_meta=True,              # no "Day type:" label → use meta + title + folder
    drop_classes=(                    # classroom-only parts
        "lp-section-student-task", "activity-block", "homework-block", "diff-block",
        "diff-table", "student-says", "ccq-block", "ccq-tamil",
    ),
    drop_line_prefixes=("[", "⏱", "preview:"),   # "[0-5 min] …", "⏱ Wait 20 seconds", next-day previews
    max_text_per_day=8000,            # days are 4.7–8.3K; the default 3,500 would cut them
    recap_from_cards=True,            # no revision day → Chapter Recap built from the cards
    flatten_inline=True,              # keep bold words inside their sentence
    aliases=("social_science", "social science", "social-science", "ss"),  # matches bridge.py's SOCIAL_SCIENCE_NAMES
)