"""
subjects/english.py
-------------------
English, new LP format only: lp-day-block days with a meta line
"Content Day N of M | ..." or "Grammar Day N of M | ...".
Old-format English LPs parse to 0 days; they get Flash Cards once regenerated.
"""

from .base import SubjectProfile


ENGLISH = SubjectProfile(
    key="english",
    display_name="English",

    card_types=[
        ("prose",         "Prose"),
        ("poem",          "Poem"),
        ("supplementary", "Supplementary"),
        ("play",          "Play"),
        ("grammar",       "Grammar"),
    ],

    # Matched against "<meta line> | <title> | <LP folder name>" (type_from_meta).
    # "grammar day" comes from the meta line; the rest from the folder suffix
    # (his_first_flight_prose → "_prose"), so words in story titles never decide the type.
    type_keywords=[
        ("grammar day",    "grammar"),
        ("_poem",          "poem"),
        ("_supplementary", "supplementary"),
        ("_play",          "play"),
        ("_drama",         "play"),
        ("_prose",         "prose"),
    ],

    type_guide={
        "prose":         "the main events of this part in order, who did what and why, and one key word with its meaning",
        "supplementary": "the main events in order, the main characters, and the lesson or message",
        "poem":          "what the poet says, the central idea, key images or lines, and any poetic device named in the material",
        "play":          "what happens in the scene, who says or does what, and what it shows about the characters",
        "grammar":       "the rule in plain words, when to use it, and 1-2 correct example sentences from the material",
    },

    audience="their English examinations",
    notation=(
        "Write names, titles and quoted lines exactly as they appear in the material.\n"
        'Never put "_" or "^" next to a letter or number; for a blank, write "____" with a space on each side.\n'
        "Use simple, clear English that a student of this class can read quickly."
    ),
    example_one='"Why was the young seagull afraid to fly?"',
    example_two='"How do modals show ability and permission?"',
    formula_rule='- formula: always "" — English cards have no formula.',
    tip_ideas="a line worth remembering, a common grammar mistake from the material, how to start a paragraph answer, a lesson word to use in answers — never promise marks",
    extra_rules=(
        "\n- For a prose, poem, supplementary or play card: the bullets give what happens or what is said,"
        "\n  in order, with the characters' names; one bullet may give a key word with its meaning."
        "\n- For a grammar card: the bullets give the rule in plain words, then 1-2 correct example"
        "\n  sentences taken from the material. Never invent new examples."
        "\n- Use only the story, poem or grammar explanation — not the teacher's warm-up questions,"
        "\n  activities, or examples about the students' own lives."
        "\n- Never add a detail, place, reason or meaning that the material does not state. If the"
        "\n  material gives an example without explaining what it shows, do not explain it yourself."
        "\n- Word meanings: use only the meaning the material gives. If the material does not give a"
        "\n  word's meaning, list the word without a meaning — never add a dictionary definition."
        "\n- Grammar examples go in single quotes, copied word for word from the material, and every"
        "\n  example must fit the rule stated in the same card."
        "\n- Each card's exam_tip must give different advice from the other cards' tips."
        "\n- ONE question means no second question word after a comma or \"and\" — never"
        "\n  \", and how\", \", and why\", \"and what\", \"and which\". If a day covers two things, ask about the idea"
        "\n  that joins them (bad: \"What dangers do hatchlings face, and why must humans protect them?\";"
        "\n  good: \"Why do sea turtle hatchlings need our protection?\")."
    ),
    recap_formula_note="",

    type_from_meta=True,
    title_strip=(
        r"^Class\s*\d+\b[^:]*:\s*",     # "Class 6 · Unit 1 · Prose · Sea Turtles: " / "Class6-Unit1-Prose-SeaTurtles: "
        r"\bSection\s+\d+\s*:\s*",      # "Section 1: The Young Seagull's Fear"
        r"^Grammar\s*:\s*",             # "Grammar: Modals" → "Modals" (the chip already says Grammar)
    ),
    drop_classes=(
        "lp-section-opening", "lp-section-student-task", "activity-block",
        "homework-block", "diff-block", "student-says", "ccq-block", "lp-section-label",
    ),
    max_text_per_day=8000,
    recap_from_cards=True,
    flatten_inline=True,
    drop_line_prefixes=("preview:",),
    tip_kind="exam",
)