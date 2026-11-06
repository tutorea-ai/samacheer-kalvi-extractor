"""
Homework: LP reader.

Turns a deployed Lesson Plan index.html into an ordered list of days.
Knows nothing about subjects: every class name, pattern and limit comes
from the SubjectProfile. This is Homework's own reader, independent of
Flash Cards and Beyond the Book.

Every day is kept (Homework covers revision and assessment days too);
review days are only flagged with is_review so the builder can give them
the lesson so far instead of one day's text. The LP's own homework blocks
are always dropped: Homework writes its own.
"""
import re
from pathlib import Path
from typing import Dict, List, Tuple

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


def _before(block, classes: Tuple[str, ...], block_ids: set):
    """Nearest element before this day block (after the previous one) with one of the classes."""
    for sib in block.find_previous_siblings():
        if id(sib) in block_ids:
            return None
        if any(c in (sib.get("class") or []) for c in classes):
            return sib
    return None


def _clean_lines(text: str) -> List[str]:
    """Drop blank lines and any line containing Tamil; Homework is English only."""
    out = []
    for line in text.split("\n"):
        line = _SPACES.sub(" ", line).strip()
        if line and not TAMIL_RE.search(line):
            out.append(line)
    return out


_SUP = str.maketrans("0123456789+-−=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁼⁽⁾")
_SUB = str.maketrans("0123456789+-−=()", "₀₁₂₃₄₅₆₇₈₉₊₋₋₌₍₎")
_SCRIPT_OK = set("0123456789+-−=() ")
_ORDINALS = {"st", "nd", "rd", "th"}


def _scripts(soup) -> None:
    """Keep powers and indices when the LP becomes text:
    10<sup>−19</sup> -> 10⁻¹⁹, m<sup>2</sup> -> m², H<sub>2</sub>O -> H₂O, v<sub>d</sub> -> v_d."""
    for el in soup.find_all("sup"):
        t = el.get_text("", strip=True)
        if t and set(t) <= _SCRIPT_OK:
            el.replace_with(t.replace(" ", "").translate(_SUP))
        elif t.lower() in _ORDINALS:
            el.replace_with(t)
        else:
            el.replace_with(f"^{t}" if len(t) == 1 else f"^({t})")
    for el in soup.find_all("sub"):
        t = el.get_text("", strip=True)
        if t and set(t) <= _SCRIPT_OK:
            el.replace_with(t.replace(" ", "").translate(_SUB))
        else:
            el.replace_with(f"_{t}" if len(t) == 1 or t.isalnum() else f"_({t})")
    soup.smooth()   # join "× 10" + "⁻¹⁹" back into one piece of text


def parse_lp(html: str, profile: SubjectProfile) -> Dict:
    soup = BeautifulSoup(html, "html.parser", on_duplicate_attribute="ignore")
    _scripts(soup)
    days: List[Dict] = []

    blocks = soup.select(profile.day_selector)
    block_ids = {id(b) for b in blocks}
    for block in blocks:
        m = re.search(r"(\d+)$", block.get("id", ""))
        num = int(m.group(1)) if m else len(days) + 1

        # Title and meta are read first, then removed from the text.
        if profile.title_meta_before:
            title_el = _before(block, profile.title_classes, block_ids)
            meta_el = _before(block, profile.meta_classes, block_ids)
        else:
            title_el = _first(block, profile.title_classes)
            meta_el = _first(block, profile.meta_classes)

        title = title_el.get_text(" ", strip=True) if title_el else ""
        for pat in profile.title_strip:
            title = re.sub(pat, "", title).strip()
        title = title or f"Day {num}"

        meta = _SPACES.sub(" ", meta_el.get_text(profile.meta_separator, strip=True)) if meta_el else ""
        tm = re.search(profile.day_type_pattern, meta, re.I)
        day_type = tm.group(1).strip() if tm else ""
        if day_type and any(re.search(pat, title, re.I) for pat in profile.title_from_type):
            title = day_type

        for el in (title_el, meta_el):
            if el is not None:
                el.decompose()
        for c in profile.drop_classes + profile.extra_drop_classes:
            for el in block.select("." + c):
                el.decompose()

        probe = (day_type or title).lower()
        is_review = any(k in probe for k in profile.review_keywords)

        # Review days revisit the whole lesson, so they get the larger limit.
        cap = profile.max_review_chars if is_review else profile.max_text_per_day
        text = "\n".join(_clean_lines(block.get_text("\n", strip=True)))
        truncated = len(text) > cap
        if truncated:
            text = text[:cap]

        days.append({
            "day": num,
            "title": title,
            "meta": meta,
            "day_type": day_type,
            "is_review": is_review,
            "text": text,
            "truncated": truncated,
        })

    days.sort(key=lambda d: d["day"])
    return {
        "subject": profile.key,
        "day_count": len(days),
        "days": days,
    }


def load_lp(path: str, subject: str) -> Dict:
    p = Path(path)
    if p.is_dir():
        p = p / "index.html"
    return parse_lp(p.read_text(encoding="utf-8"), get_profile(subject))