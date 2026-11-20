"""Concept Canvas: subject profile registry.

Adding a subject = one import + one name in PROFILES. The engine never
checks a subject name; it only calls get_profile().
"""
from typing import Dict

from .base import SubjectProfile
from .biology import BIOLOGY
from .maths import MATHS
from .physics import PHYSICS

PROFILES: Dict[str, SubjectProfile] = {
    p.key: p for p in (
        PHYSICS,
        BIOLOGY,
        MATHS,
    )
}

# Plain generic settings for a subject with no profile yet. Never another
# subject's values.
DEFAULT = SubjectProfile(key="default")


def get_profile(subject: str) -> SubjectProfile:
    """Find a profile by the request's subject: aliases first, then keys."""
    s = (subject or "").strip().lower()
    for p in PROFILES.values():
        if s in p.aliases:
            return p
    return PROFILES.get(s, DEFAULT)