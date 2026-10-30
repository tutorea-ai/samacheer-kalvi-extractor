"""
Beyond the Book: subject profile definition.

Every subject-specific value lives in a SubjectProfile. The engine
(lp_parser.py, builder.py, renderer.py) reads only these fields and
never checks a subject name. Every optional field has a default, so a
subject file sets only what that subject needs.
"""
from dataclasses import dataclass, field
from typing import Dict, Tuple

# Connection chips shown in the tab, (key, label), in display order.
DEFAULT_CONNECTIONS: Tuple[Tuple[str, str], ...] = (
    ("home", "At Home"),
    ("around", "Around You"),
    ("tech", "Technology"),
    ("nature", "Nature"),
    ("careers", "Careers"),
    ("building", "Behind the Scenes"),
)

# Classroom-only classes dropped for every subject.
DEFAULT_DROP_CLASSES: Tuple[str, ...] = (
    "cfu-block", "cfu-wait-note", "ccq-block", "lp-time",
    "lp-tamil-scaffold", "tamil-scaffold",
)

# Card length limits. A profile overrides any of these through `limits`;
# an unknown key is an error.
DEFAULT_LIMITS: Dict[str, int] = {
    "MAX_HOOK_WORDS": 20,
    "MAX_FIELD_WORDS": 45,
    "MAX_TRY_WORDS": 30,
    "MAX_TAMIL_CHARS": 160,
    "MAX_BIGWHY_WORDS": 90,
    "MAX_PICTURE_WORDS": 60,
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
    board_classes: Tuple[str, ...] = ("board-work",)
    drop_classes: Tuple[str, ...] = DEFAULT_DROP_CLASSES
    extra_drop_classes: Tuple[str, ...] = ()
    day_type_pattern: str = r"Day type:\s*([^|]+)"
    title_strip: Tuple[str, ...] = (r"^Day\s+\d+(\s+of\s+\d+)?\s*[—–:-]\s*",)
    max_text_per_day: int = 6000
    recap_keywords: Tuple[str, ...] = ("revision",)

    # ── Cards ────────────────────────────────────────────────
    connections: Tuple[Tuple[str, str], ...] = DEFAULT_CONNECTIONS
    building_key: str = "building"   # the connection that may leave where_you_see_it empty
    building_mode: str = "card"      # "card": keep building cards | "skip": leave them out
    type_hints: Tuple[Tuple[str, str], ...] = ()
    audience: str = ""
    local_context: str = "Tamil Nadu and India"
    tamil_line: bool = True
    tamil_style: str = (
        "one short sentence in simple, everyday written Tamil that any student understands: "
        "correct written forms (இல்லாமல், not இல்லாம; செய்ய, not பண்ண), no literary or "
        "old-style words, and English only for technical terms"
    )
    try_this: bool = True              # the optional home-observation field
    pictures: bool = False             # one AI picture per card (OpenAI images)
    picture_model: str = "gpt-image-2.5-sunburst"
    picture_style: str = (
        "clean modern flat illustration, soft warm colours, friendly realistic proportions, "
        "everyday Tamil Nadu setting and people, no text, no labels, no letters or numbers "
        "anywhere in the image"
    )
    picture_size: str = "1536x1024"
    picture_quality: str = "medium"
    extra_rules: str = ""
    batch_size: int = 6
    limits: Dict[str, int] = field(default_factory=dict)

    def limit(self, name: str) -> int:
        """Profile override if set, else the default. Unknown names raise."""
        for k in self.limits:
            if k not in DEFAULT_LIMITS:
                raise KeyError(f"[{self.key}] unknown limit '{k}'")
        if name not in DEFAULT_LIMITS:
            raise KeyError(f"unknown limit '{name}'")
        return self.limits.get(name, DEFAULT_LIMITS[name])