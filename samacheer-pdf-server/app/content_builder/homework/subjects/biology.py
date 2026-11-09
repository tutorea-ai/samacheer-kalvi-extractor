"""Homework profile: Biology (Botany / Zoology), Classes 11–12.

Reading values come from BB's Biology profile (measured on the Class 12
Botany Unit 2 Classical Genetics LP: 14 days, title + meta table BEFORE
each day block, Focus row instead of a "Day type:" label, some teaching
days titled "Revision and Assessment", Day 13 evaluation/glossary,
Day 14 whole-chapter revision). Unlike BB, Homework keeps the closing,
exam-prep, activity and vocabulary sections: they show the level and the
exact definitions the homework should match.
"""
from .base import SubjectProfile

BIOLOGY = SubjectProfile(
    key="biology",
    display_name="Biology",
    aliases=("botany", "zoology"),

    # Reading
    day_selector="div.lp-day-block",
    title_meta_before=True,
    meta_classes=("lp-day-meta-table",),
    meta_separator=" | ",
    day_type_pattern=r"Focus\s*\|\s*([^|]+)",
    title_strip=(r"^Day\s+\d+(\s+of\s+\d+)?\s*[—–:-]\s*", r"^Chapter\s+\d+\s+[^,]+,\s*"),
    title_from_type=(r"^Revision and Assessment$",),
    extra_drop_classes=("student-says",),
    max_text_per_day=14000,
    review_keywords=("whole-chapter revision", "evaluation questions"),

    # Homework
    audience="Class 11–12 Tamil Nadu State Board Biology students (about 16–17 years old)",
    apply_style=(
        "On inheritance or cross days: work out a cross from given parents — parents' "
        "genotypes, gametes, a Punnett square, F₁/F₂ genotypes and phenotypes with their "
        "ratios. On concept days: draw and label a simple diagram described in the lesson, "
        "or classify given examples, or complete a short flow or table. On review days: "
        "prefer one cross or problem that combines two ideas from the lesson so far; on an "
        "evaluation or glossary day, applying the chapter's terms to a new example is "
        "equally good."
    ),
    extra_rules=(
        "\n- Never use human skin colour, caste, intelligence or a disease as an example."
        "\n- In crosses, use only the organisms, traits and symbols the lesson uses (for "
        "example pea plant traits, Mirabilis, Antirrhinum, T/t, F₁, F₂): a cross depends on "
        "the exact dominance rules the lesson teaches."
        "\n- In classifying or recognising tasks, new familiar examples of the same idea "
        "(plants, crops or animals a student knows) are allowed, as long as the "
        "classification follows the lesson's own definitions."
        "\n- A cross may follow the pattern of a worked example in the LP, but must use a "
        "different trait or parent combination from that example; never repeat it."
        "\n- In answers, write every Punnett square as a grid (rows starting and ending "
        "with |), and always end a cross with the genotypic and phenotypic ratios."
    ),
    limits={"MAX_TASK_WORDS": 90, "MAX_HINT_WORDS": 45, "MAX_ANSWER_WORDS": 300},
    letter_subscripts=False,   # R_Y_ / R_yy is blank-allele notation, never a subscript
)