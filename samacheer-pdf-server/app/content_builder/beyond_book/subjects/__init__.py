"""Beyond the Book: subject profile registry.

Adding a subject = one import + one name in PROFILES.
"""
from typing import Dict

from .base import SubjectProfile
from .physics import PHYSICS

PROFILES: Dict[str, SubjectProfile] = {p.key: p for p in (PHYSICS,)}

# Unlisted subjects get generic defaults, never another subject's settings.
DEFAULT = SubjectProfile(key="default")


def get_profile(subject: str) -> SubjectProfile:
    s = (subject or "").strip().lower()
    for p in PROFILES.values():
        if s in p.aliases:
            return p
    return PROFILES.get(s, DEFAULT)