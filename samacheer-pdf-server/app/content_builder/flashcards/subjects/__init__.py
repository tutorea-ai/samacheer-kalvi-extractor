"""
subjects — one profile per subject.

    from app.content_builder.flashcards.subjects import get_profile
    profile = get_profile("physics")

To add a subject: create subjects/<subject>.py with a SubjectProfile and add
it to PROFILES below. Nothing else in the engine needs to change.
"""

from dataclasses import replace

from .base import SubjectProfile
from .physics import PHYSICS
from .english import ENGLISH
from .socialscience import SOCIALSCIENCE
from .maths import MATHS
from .biology import BIOLOGY


PROFILES = {p.key: p for p in (PHYSICS, ENGLISH, SOCIALSCIENCE, MATHS, BIOLOGY)}

# Alias → key lookup, e.g. "social_science" / "ss" → "socialscience".
_ALIAS_TO_KEY = {alias: p.key for p in PROFILES.values() for alias in p.aliases}

# Any subject without a profile gets exactly today's behaviour:
# Physics prompts and Day-type keywords, generic chips, and the full focus guide.
DEFAULT = replace(
    PHYSICS,
    key="default",
    display_name="",
    card_types=[
        ("concept", "Concepts"),
        ("fact",    "Key Facts"),
        ("term",    "Key Terms"),
    ],
    type_guide={
        **PHYSICS.type_guide,
        "fact": "key facts most likely to be asked",
        "term": "key terms with one-line meanings",
    },
)


def get_profile(subject) -> SubjectProfile:
    key = (subject or "").lower().strip()
    key = _ALIAS_TO_KEY.get(key, key)
    return PROFILES.get(key, DEFAULT)


__all__ = ["SubjectProfile", "PROFILES", "DEFAULT", "get_profile"]