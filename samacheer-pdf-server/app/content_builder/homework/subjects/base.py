"""
Homework: subject profile definition.

Every subject-specific value lives in a SubjectProfile. The engine
(lp_parser.py, builder.py, renderer.py) reads only these fields and
never checks a subject name. Every optional field has a default, so a
subject file sets only what that subject needs.
"""
from dataclasses import dataclass, field
from typing import Dict, Tuple

# Classroom-only classes dropped for every subject. "homework-block" is
# the LP's own homework: Homework always writes fresh and never reuses it.
DEFAULT_DROP_CLASSES: Tuple[str, ...] = (
    "cfu-block", "cfu-wait-note", "ccq-block", "lp-time",
    "lp-tamil-scaffold", "tamil-scaffold", "homework-block",
)

# The daily task pair, (key, label, guide), in display order. The number
# of tasks per day is the length of this tuple.
UNDERSTAND_GUIDE = (
    "Check understanding of the day's main idea: explain, define, compare or answer "
    "in the student's own words. Never a pure copy-the-definition task."
)
DEFAULT_APPLY_GUIDE = (
    "Use the day's idea in a short practical task: solve, draw, label, classify or write."
)

# Length limits. A profile overrides any of these through `limits`;
# an unknown key is an error.
DEFAULT_LIMITS: Dict[str, int] = {
    "MAX_TASK_WORDS": 60,
    "MAX_HINT_WORDS": 30,
    "MAX_ANSWER_WORDS": 150,
}


@dataclass(frozen=True)
class SubjectProfile:
    # ── Identity ─────────────────────────────────────────────
    key: str
    display_name: str = ""
    aliases: Tuple[str, ...] = ()

    # ── Reading the LP ───────────────────────────────────────
    day_selector: str = 'div.lp-day-block[id^="lp-day-"]'
    title_classes: Tuple[str, ...] = ("lp-day-title",)
    meta_classes: Tuple[str, ...] = ("lp-day-meta",)
    drop_classes: Tuple[str, ...] = DEFAULT_DROP_CLASSES
    extra_drop_classes: Tuple[str, ...] = ()
    day_type_pattern: str = r"Day type:\s*([^|]+)"
    title_strip: Tuple[str, ...] = (r"^Day\s+\d+(\s+of\s+\d+)?\s*[—–:-]\s*",)
    max_text_per_day: int = 6000
    review_keywords: Tuple[str, ...] = ("revision", "assessment")
    max_review_chars: int = 24000          # "lesson so far" text given to a review day
    title_meta_before: bool = False        # title + meta sit just BEFORE the day block
    title_from_type: Tuple[str, ...] = ()  # titles matching these regexes -> use day_type
    meta_separator: str = " "              # joins the meta's text pieces (" | " for tables)

    # ── Homework ─────────────────────────────────────────────
    audience: str = ""
    local_context: str = "Tamil Nadu and India"
    apply_style: str = DEFAULT_APPLY_GUIDE
    hints: bool = True                     # one hidden hint per task
    answers: bool = True                   # one hidden, reviewer-checked answer per task
    letter_subscripts: bool = True         # show v_d as v + subscript d; off where "_" means
                                           # something else (genetics: R_Y_ = any allele)
    max_sentence_words: int = 0            # longest sentence allowed (young classes); 0 = off
    pipe_rules: bool = True                # "|" only in grid rows; off where | is notation
                                           # (Maths: |x|, |A|): tables fenced in [table]…[/table]
    tamil_hint: bool = False               # Tamil version of each hint (off for all subjects)
    extra_rules: str = ""                  # subject rules appended to the writer prompt, each "\n- …"
    answer_review_rules: str = ""          # extra rules for the answer reviewer only, each "\n- …"
    batch_size: int = 6
    limits: Dict[str, int] = field(default_factory=dict)

    @property
    def tasks(self) -> Tuple[Tuple[str, str, str], ...]:
        """The daily task pair: Understand, then Apply with this subject's guide."""
        return (
            ("understand", "Understand", UNDERSTAND_GUIDE),
            ("apply", "Apply", self.apply_style),
        )

    def limit(self, name: str) -> int:
        """Profile override if set, else the default. Unknown names raise."""
        for k in self.limits:
            if k not in DEFAULT_LIMITS:
                raise KeyError(f"[{self.key}] unknown limit '{k}'")
        if name not in DEFAULT_LIMITS:
            raise KeyError(f"unknown limit '{name}'")
        return self.limits.get(name, DEFAULT_LIMITS[name])