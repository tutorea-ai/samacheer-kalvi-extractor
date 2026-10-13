"""
card_types.py
-------------
Per-subject Flash Card types: (key, filter-chip label), in display order.
The lists live in subjects/<subject>.py (profile.card_types); this is the
lookup the builder uses. The renderer shows only types present in a deck.
"""

from .subjects import get_profile


def types_for(subject: str) -> list[tuple[str, str]]:
    return get_profile(subject).card_types