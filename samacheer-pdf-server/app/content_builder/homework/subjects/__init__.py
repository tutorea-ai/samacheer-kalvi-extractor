"""
Homework: subject profile registry.

get_profile() lowercases the request's subject, checks every profile's
aliases, then the profile keys, and falls back to DEFAULT: plain generic
settings, never another subject's.

Adding a subject: write subjects/<subject>.py, then add one import and
one name in PROFILES below.
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

DEFAULT = SubjectProfile(key="default")


def get_profile(subject: str) -> SubjectProfile:
    s = (subject or "").strip().lower()
    for p in PROFILES.values():
        if s in p.aliases:
            return p
    return PROFILES.get(s, DEFAULT)