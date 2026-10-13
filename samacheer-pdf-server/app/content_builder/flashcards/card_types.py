"""
card_types.py
-------------
Per-subject Flash Card types: (key, filter-chip label), in display order.
The renderer shows only the types actually present in a deck.
Add a subject only after reviewing its LP day types.
"""

from .subjects import PROFILES, DEFAULT, get_profile

# Kept for older imports — the real lists live in subjects/<subject>.py
CARD_TYPES    = {key: p.card_types for key, p in PROFILES.items()}
DEFAULT_TYPES = DEFAULT.card_types


def types_for(subject: str) -> list[tuple[str, str]]:
    return get_profile(subject).card_types


def allowed_keys(subject: str) -> set[str]:
    return {key for key, _ in types_for(subject)}
