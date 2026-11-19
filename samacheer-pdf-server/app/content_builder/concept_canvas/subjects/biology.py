"""Concept Canvas profile: Biology (Botany / Zoology), Classes 11–12.

Reading values copied from Homework's Biology profile (measured on the
Class 12 Botany Unit 2 Classical Genetics LP: 14 days, title + meta table
BEFORE each day block, Focus row instead of a "Day type:" label, some
teaching days titled "Revision and Assessment", Day 13 evaluation/glossary,
Day 14 whole-chapter revision).
"""
from .base import SubjectProfile

BIOLOGY = SubjectProfile(
    key="biology",
    display_name="Biology",
    aliases=("botany", "zoology"),

    # Reading (same as Homework)
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

    # Concept Canvas
    audience="Class 11–12 Tamil Nadu State Board Biology students (about 16–17 years old)",
    allowed_templates=(
        "step_build", "process_flow", "compare", "concept_map", "cycle", "punnett",
    ),
    icon_groups=("biology", "general"),
    formulas=False,
    extra_rules=(
        "\n- Never use human skin colour, caste, intelligence or a disease as an example."
        "\n- Use only the organisms, traits and symbols the lesson uses (for example pea "
        "plant traits, Mirabilis, Antirrhinum, T/t, F₁, F₂); never invent a trait."
        "\n- Write ratios with spaced colons (3 : 1, 9 : 3 : 3 : 1), never with = signs."
        "\n- Two contrasting ideas (dominant/recessive, complete/incomplete dominance): "
        "compare. A sequence of experiments or generations: process_flow."
        "\n- A day whose central idea is a cross (monohybrid, dihybrid, test cross, "
        "incomplete dominance, lethal genes, epistasis): punnett, using the lesson's own "
        "cross, letters and traits, written exactly as the lesson writes them (T/t, or "
        "numbered alleles such as R1/R2 for incomplete dominance); capital = dominant."
        "\n- In punnett, map every genotype in the grid to its trait as the lesson states it; "
        "a genotype whose offspring die is the trait \"Lethal\" (it is left out of the ratio). "
        "The ratio is the phenotype ratio the lesson gives (3 : 1, 9 : 3 : 3 : 1, 1 : 2 : 1, 2 : 1)."
        "\n- On a dihybrid day the central cross is the F₂: both parents double heterozygous "
        "(for example RrYy x RrYy, 9 : 3 : 3 : 1). Use a test cross only on a day whose central "
        "idea is the test cross."
        "\n- The parents step describes exactly the two plants in parent_1 and parent_2. Earlier "
        "generations (the P cross that made them) go only in the labels, or are left out."
    ),
    review_rules=(
        "\n- In a punnett day, the grid cells and the ratio are already verified by code: do not "
        "re-derive them. Check that the cross itself (organism, trait, parents, which allele is "
        "dominant, which genotype is lethal) is the one the lesson teaches."
        "\n- The parents-phase step must describe the same cross as parent_1 x parent_2; a step "
        "that names a different cross (for example the P generation over an F₁ x F₁ grid) is an error."
    ),
)