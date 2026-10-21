"""
language_rules.py
-----------------
Language-specific words used by the generic pipeline code, loaded from
data/language_rules/{language}.json. The code holds the LOGIC; the JSON
holds the WORDS. A new language (or a corrected marker) is a data change.

Today only the "epub" section is used (lesson-list EPUBs, e.g. Tamil):
    unit_label, number_words, unit_intro_heading,
    back_matter_markers, section_labels
"""
import json
import re
from functools import lru_cache
from typing import Dict, Optional

from ..config import settings

RULES_DIR = settings.DATA_DIR / "language_rules"


def phrase_re(phrase: str) -> str:
    """Regex for a phrase; any spacing between its words (incl. none)."""
    return r"\s*".join(map(re.escape, phrase.split()))


@lru_cache(maxsize=None)
def load_all() -> Dict[str, dict]:
    rules = {}
    for f in sorted(RULES_DIR.glob("*.json")):
        try:
            rules[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  Language rules {f.name} not loaded: {e}")
    return rules


class LessonListRules:
    """Compiled EPUB patterns for one language's lesson-list books."""

    def __init__(self, language: str, epub: dict):
        self.language = language
        unit = phrase_re(epub["unit_label"])
        self.unit_re = re.compile(rf"{unit}\s*(\d+)")

        markers = [r"\s*###\s*".join(phrase_re(p) for p in seq) for seq in epub["back_matter_markers"]]
        self.back_matter_re = re.compile(r"###\s*(?:" + "|".join(markers) + ")")

        self.section_types = {}
        label_alts = []
        for s in epub["section_labels"]:
            for v in [s["label"], *s.get("variants", [])]:
                label_alts.append(phrase_re(v))
                self.section_types[v] = s.get("type")
        self.trailing_label_re = re.compile(r"\s*(?:###\s*)?(?:" + "|".join(label_alts) + r")\s*$")

        numbers = "|".join(map(re.escape, epub["number_words"]))
        intro = phrase_re(epub["unit_intro_heading"])
        self.trailing_unit_re = re.compile(
            rf"\s*###\s*{unit}\s*(?:{numbers})(?=[\s,]|$)[^#]*"
            rf"(?:###\s*{intro}[^#]*)?$"
        )


@lru_cache(maxsize=None)
def lesson_list_rules(language: str) -> Optional[LessonListRules]:
    epub = load_all().get(language, {}).get("epub")
    return LessonListRules(language, epub) if epub else None


def match_lesson_list(top_ol) -> Optional[LessonListRules]:
    """
    The rules of the language whose unit label heads the nav's top-level
    entries (each with a nested <ol> of lessons), or None.
    """
    for language in load_all():
        rules = lesson_list_rules(language)
        if not rules:
            continue
        for li in top_ol.find_all("li", recursive=False):
            link = li.find("a")
            if link and rules.unit_re.search(link.get_text(strip=True)) and li.find("ol"):
                return rules
    return None