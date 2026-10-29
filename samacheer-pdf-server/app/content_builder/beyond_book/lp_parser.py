"""
Beyond the Book: LP reader.

Turns a deployed Lesson Plan index.html into a list of days. Knows
nothing about subjects: every class name, pattern and limit comes from
the SubjectProfile. This is BB's own reader, independent of Flash Cards.
"""
import re
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup

from .subjects import get_profile
from .subjects.base import SubjectProfile

TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
_SPACES = re.compile(r"[ \t\u00a0]+")


def _first(block, classes: Tuple[str, ...]):
    for c in classes:
        el = block.select_one("." + c)
        if el is not None:
            return el
    return None


def _clean_lines(text: str) -> List[str]:
    """Drop blank lines and any line containing Tamil; BB writes its own Tamil."""
    out = []
    for line in text.split("\n"):
        line = _SPACES.sub(" ", line).strip()
        if line and not TAMIL_RE.search(line):
            out.append(line)
    return out


def _match(text: str, pairs: Tuple[Tuple[str, str], ...]) -> Tuple[Optional[str], str]:
    """First (word, value) whose word appears in text."""
    low = (text or "").lower()
    for word, value in pairs:
        if word in low:
            return word, value
    return None, ""


def parse_lp(html: str, profile: SubjectProfile) -> Dict:
    soup = BeautifulSoup(html, "html.parser", on_duplicate_attribute="ignore")
    days: List[Dict] = []
    recap_days: List[Dict] = []

    for block in soup.select(profile.day_selector):
        m = re.search(r"(\d+)$", block.get("id", ""))
        num = int(m.group(1)) if m else len(days) + len(recap_days) + 1

        # Title and meta are read first, then removed from the text.
        title_el = _first(block, profile.title_classes)
        meta_el = _first(block, profile.meta_classes)

        title = title_el.get_text(" ", strip=True) if title_el else ""
        for pat in profile.title_strip:
            title = re.sub(pat, "", title).strip()
        title = title or f"Day {num}"

        meta = _SPACES.sub(" ", meta_el.get_text(" ", strip=True)) if meta_el else ""
        tm = re.search(profile.day_type_pattern, meta, re.I)
        day_type = tm.group(1).strip() if tm else ""

        for el in (title_el, meta_el):
            if el is not None:
                el.decompose()
        for c in profile.drop_classes + profile.extra_drop_classes:
            for el in block.select("." + c):
                el.decompose()

        text = "\n".join(_clean_lines(block.get_text("\n", strip=True)))
        truncated = len(text) > profile.max_text_per_day
        if truncated:
            text = text[: profile.max_text_per_day]

        probe = (day_type or title).lower()
        is_recap = any(k in probe for k in profile.recap_keywords)
        hint_key, hint = _match(day_type, profile.type_hints)

        day = {
            "day": num,
            "title": title,
            "meta": meta,
            "day_type": day_type,
            "hint_key": hint_key,
            "hint": hint,
            "is_recap": is_recap,
            "text": text,
            "truncated": truncated,
        }
        (recap_days if is_recap else days).append(day)

    return {
        "subject": profile.key,
        "day_count": len(days) + len(recap_days),
        "days": days,
        "recap_days": recap_days,
    }


def load_lp(path: str, subject: str) -> Dict:
    with open(path, encoding="utf-8") as f:
        return parse_lp(f.read(), get_profile(subject))