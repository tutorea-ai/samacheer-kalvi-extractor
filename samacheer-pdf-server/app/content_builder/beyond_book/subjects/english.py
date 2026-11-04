"""Beyond the Book profile: English, Classes 6–12.

Values come from the Class 6 Term 1 Unit 1 Sea Turtles (prose) LP:
6 days — 3 'Content Day' (the text) and 3 'Grammar Day' — title + meta
inside the block, titles prefixed with a lesson code up to a colon,
no revision day (the Big Why is built from the cards).
"""
from .base import SubjectProfile

ENGLISH = SubjectProfile(
    key="english",
    display_name="English",

    # Reading
    day_type_pattern=r"^\s*(Content|Grammar)\s+Day",
    title_strip=(r"^Day\s+\d+(\s+of\s+\d+)?\s*[—–:-]\s*",
                 r"^[^:]{0,80}(Prose|Poem|Supplementary|Play|Drama)[^:]{0,40}:\s*"),
    extra_drop_classes=("lp-section-student-task", "homework-block", "activity-block",
                        "lp-section-closing", "diff-block", "student-says", "vocab-block"),
    max_text_per_day=9000,

    # Cards
    audience="Class 6 Tamil Nadu State Board English students (about 11 years old)",
    type_hints=(
        ("content", "connect the text to the student's own life: where this animal, place, "
                    "idea or feeling shows up around them in Tamil Nadu today"),
        ("grammar", "show where the student already uses this grammar every day: talking at "
                    "the shop, messages to friends, reading signs and notices"),
    ),
    default_hint=("connect the text to the student's own life: where its subject, idea or "
                  "feeling shows up around them in Tamil Nadu today"),
    building_mode="card",
    try_this=False,
    pictures=True,
    picture_people=(
        "a school boy of about 11", "a school girl of about 11",
        "a boy and a girl, classmates of about 11", "a school girl of about 11",
        "a school boy of about 11", "three classmates of about 11, boys and girls",
    ),
    extra_rules=(
        "\n- For a story or poem, the connection is where its subject, idea or feeling shows"
        "\n  up in the student's own life, not a job that uses it."
        "\n- Write for an 11-year-old: short sentences and everyday words."
        "\n- Name a place, organisation, date or number only if the lesson text names it."
        "\n- Describe a poem or story in your own words; quote at most a few words from it."
    ),
)