"""
text_normalisers.py
-------------------
Subject-specific normalisation of extracted lesson text.
Runs ONCE, right after extraction, so Content / QA / LP and the txt output
all get the same text. Subjects without an entry pass through unchanged.

Returns (text, extra_metadata). extra_metadata is merged into ai_metadata.
"""
from typing import Callable, Dict, Tuple

TAMIL_TEXT_VERSION = 1   # bump when a Tamil normalisation rule changes


def _tamil(text: str) -> Tuple[str, dict]:
    from .tamil_text import normalize_source_text
    t, rep = normalize_source_text(text)
    print(f"   🔤 Tamil text v{TAMIL_TEXT_VERSION}: blanks {rep['dash']} | "
          f"symbols {rep['symbols_number'] + rep['symbols_chain']} | "
          f"ambiguous {len(rep['symbol_ambiguous'])} | boxes {rep['boxes']} | "
          f"memorise {len(rep['memorise_blocks'])}")
    meta = {
        "memorise_blocks":    rep["memorise_blocks"],
        "tamil_text_version": TAMIL_TEXT_VERSION,
        "symbol_ambiguous":   rep["symbol_ambiguous"],
    }
    return t, meta


NORMALISERS: Dict[str, Callable[[str], Tuple[str, dict]]] = {
    "tamil": _tamil,
}


def normalise_lesson_text(subject: str, text: str) -> Tuple[str, dict]:
    fn = NORMALISERS.get((subject or "").lower().strip())
    if not fn or not text:
        return text, {}
    return fn(text)