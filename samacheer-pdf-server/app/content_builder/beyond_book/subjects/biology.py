"""Beyond the Book profile: Biology (Botany / Zoology), Classes 11–12.

Values come from the Class 12 Botany Unit 2 Classical Genetics LP:
14 days, title + meta table BEFORE each day block, Focus row instead of a
"Day type:" label, some teaching days titled "Revision and Assessment",
Day 13 evaluation/glossary and Day 14 whole-chapter revision.
"""
from .base import SubjectProfile

BIOLOGY = SubjectProfile(
    key="biology",
    display_name="Biology",
    aliases=("botany", "zoology"),

    # Reading
    title_meta_before=True,
    meta_classes=("lp-day-meta-table",),
    meta_separator=" | ",
    day_type_pattern=r"Focus\s*\|\s*([^|]+)",
    title_strip=(r"^Day\s+\d+(\s+of\s+\d+)?\s*[—–:-]\s*", r"^Chapter\s+\d+\s+[^,]+,\s*"),
    title_from_type=(r"^Revision and Assessment$",),
    extra_drop_classes=("lp-section-closing", "lp-section-exam-prep", "lp-section-activity",
                        "homework-block", "lp-vocab-block", "student-says"),
    max_text_per_day=9500,
    recap_keywords=("whole-chapter revision", "evaluation questions"),

    # Cards (same decisions as Physics)
    audience="Class 11–12 Tamil Nadu State Board Biology students",
    building_mode="card",
    try_this=False,
    pictures=True,
    picture_people=(
        "a school boy of about 17", "a school girl of about 17",
        "a boy and a girl, classmates of about 17", "a school girl of about 17",
        "a school boy of about 17", "three classmates of about 17, boys and girls",
    ),
    extra_rules=(
        "\n- Never use skin colour, caste, intelligence or a disease as a mark against"
        "\n  people. For inheritance examples prefer plants, crops, flowers, height or"
        "\n  blood groups."
    ),
)