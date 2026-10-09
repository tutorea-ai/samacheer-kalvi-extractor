"""
card_types.py
-------------
Per-subject Flash Card types: (key, filter-chip label), in display order.
The renderer shows only the types actually present in a deck.
Add a subject only after reviewing its LP day types.
"""

CARD_TYPES = {
    "physics": [
        ("concept",     "Concepts"),
        ("formula",     "Formulas"),
        ("derivation",  "Derivations"),
        ("device",      "Devices & Experiments"),
        ("application", "Applications"),
    ],
}

# Used for any subject not listed yet
DEFAULT_TYPES = [
    ("concept", "Concepts"),
    ("fact",    "Key Facts"),
    ("term",    "Key Terms"),
]


def types_for(subject: str) -> list[tuple[str, str]]:
    return CARD_TYPES.get((subject or "").lower().strip(), DEFAULT_TYPES)


def allowed_keys(subject: str) -> set[str]:
    return {key for key, _ in types_for(subject)}
