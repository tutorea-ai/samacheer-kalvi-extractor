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


PROFILES = {p.key: p for p in (PHYSICS,)}

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
    return PROFILES.get((subject or "").lower().strip(), DEFAULT)


__all__ = ["SubjectProfile", "PROFILES", "DEFAULT", "get_profile"]