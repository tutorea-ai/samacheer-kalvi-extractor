"""Concept Canvas: subject profile definition.

Every subject-specific value lives in a SubjectProfile. The engine
(lp_parser.py, builder.py, service.py) reads only these fields and never
checks a subject name. Every optional field has a default, so a subject
file sets only what that subject needs.

Text limits and the icon list are NOT here: they are part of the Node
contract and live in schema.py, the same for every subject.
"""
from dataclasses import dataclass
from typing import Tuple

# Classroom-only classes dropped for every subject. "homework-block" is
# the LP's own homework: not part of the day's concept.
DEFAULT_DROP_CLASSES: Tuple[str, ...] = (
    "cfu-block", "cfu-wait-note", "ccq-block", "lp-time",
    "lp-tamil-scaffold", "tamil-scaffold", "homework-block",
)

ALL_TEMPLATES: Tuple[str, ...] = (
    "step_build", "process_flow", "cycle", "compare", "timeline", "concept_map",
)


@dataclass(frozen=True)
class SubjectProfile:
    # ── Identity ─────────────────────────────────────────────
    key: str
    display_name: str = ""
    aliases: Tuple[str, ...] = ()

    # ── Reading the LP (same fields as Homework's profile) ───
    day_selector: str = 'div.lp-day-block[id^="lp-day-"]'
    title_classes: Tuple[str, ...] = ("lp-day-title",)
    meta_classes: Tuple[str, ...] = ("lp-day-meta",)
    drop_classes: Tuple[str, ...] = DEFAULT_DROP_CLASSES
    extra_drop_classes: Tuple[str, ...] = ()
    day_type_pattern: str = r"Day type:\s*([^|]+)"
    title_strip: Tuple[str, ...] = (r"^Day\s+\d+(\s+of\s+\d+)?\s*[—–:-]\s*",)
    max_text_per_day: int = 6000
    review_keywords: Tuple[str, ...] = ("revision", "assessment")
    max_review_chars: int = 24000
    title_meta_before: bool = False        # title + meta sit just BEFORE the day block
    title_from_type: Tuple[str, ...] = ()  # titles matching these regexes -> use day_type
    meta_separator: str = " "              # joins the meta's text pieces (" | " for tables)

    # ── Concept Canvas ───────────────────────────────────────
    audience: str = ""                     # "…for {audience}" in every prompt
    allowed_templates: Tuple[str, ...] = ALL_TEMPLATES
    icon_groups: Tuple[str, ...] = ("general",)   # icon sets from schema.ICONS
    formulas: bool = True                  # allow the LaTeX "formula" field
    skip_review_days: bool = True          # no Claude call for revision/assessment days
    extra_rules: str = ""                  # subject rules for the writer + reviewer, each "\n- …"
    review_rules: str = ""                 # extra rules for the reviewer only, each "\n- …"
    batch_size: int = 6                    # LP days per writer call

    def __post_init__(self):
        bad = [t for t in self.allowed_templates if t not in ALL_TEMPLATES]
        if bad:
            raise ValueError(f"[{self.key}] unknown templates: {bad}")
        if not self.allowed_templates:
            raise ValueError(f"[{self.key}] allowed_templates is empty")