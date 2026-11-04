"""Beyond the Book profile: Social Science (History, Geography, Civics, Economics), Classes 6–10.

Values come from the Class 6 Term 1 History Unit 2 Human Evolution LP:
5 days, title + meta inside the block, meta's last '|' segment states the
day's focus, Day 5 Map Work & Book-back = Evaluation Day. Timing lines
('[0-5 min]', '⏱') are harmless; the writer ignores classroom instructions.
"""
from .base import SubjectProfile

SOCIALSCIENCE = SubjectProfile(
    key="socialscience",
    display_name="Social Science",
    aliases=("social_science", "social science", "ss"),

    # Reading: the focus is the meta line's last segment (same as Maths).
    day_type_pattern=r"\|\s*([^|]+?)\s*$",
    extra_drop_classes=("lp-section-student-task", "lp-section-closing", "diff-block",
                        "diff-table", "activity-block", "student-says", "homework-block",
                        "vocab-block"),
    max_text_per_day=9000,
    recap_keywords=("evaluation day",),

    # Cards
    audience="Class 6 Tamil Nadu State Board Social Science students (about 11 years old)",
    building_mode="card",
    try_this=False,
    pictures=True,
    picture_people=(
        "a school boy of about 11", "a school girl of about 11",
        "a boy and a girl, classmates of about 11", "a school girl of about 11",
        "a school boy of about 11", "three classmates of about 11, boys and girls",
    ),
    extra_rules=(
        "\n- For history, the connection is where this past still lives in the student's life"
        "\n  today (the wheel in every bicycle, settled farming in villages), not a modern"
        "\n  job that uses the idea."
        "\n- Write for an 11-year-old: short sentences and everyday words."
        "\n- Name a place, site, date or find only if the lesson text names it."
        "\n- In pictures, early humans are always fully clothed in simple animal-skin"
        "\n  clothing and shown with dignity; hunting is shown as tracking or gathering,"
        "\n  never killing, weapons in use, or blood. Prefer today's children with the"
        "\n  modern form of the idea."
    ),
)