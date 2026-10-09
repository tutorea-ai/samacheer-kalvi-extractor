"""
lp_parser.py
------------
Splits a deployed Lesson Plan (LP) HTML into clean per-day records for
Flash Cards. Pure parsing — no AI calls.

For each LP day it returns:
  - day number, title, textbook section, normalised card type
  - learning objectives (student-facing — best source for bullets)
  - board-work blocks (formulas, worked examples)
  - cleaned text: Tamil scaffolding, CFU blocks, timings and
    "Next lesson" lines removed (Flash Cards are English only)
  - is_recap: True for the whole-chapter revision day

Works on any LP passed through _wrap_html(), which stamps every day block
as <div id="lp-day-N" class="lp-day-block">. Title / meta extraction uses
lp-day-title / lp-day-meta when present, falling back to the first heading.
"""

import re
import hashlib
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup


# Teacher-only or Tamil blocks — removed before anything reaches the AI
DROP_CLASSES = ["lp-tamil-scaffold", "tamil-scaffold", "cfu-block",
                "cfu-wait-note", "lp-time"]

TAMIL_RE      = re.compile(r"[\u0B80-\u0BFF]")
DAY_TITLE_RE  = re.compile(r"^\s*Day\s+\d+\s*(?:of\s+\d+)?\s*[—–:\-]\s*(.+)$", re.IGNORECASE)
META_FIELD_RE = re.compile(r"(Textbook|Day type|Technique)\s*:\s*([^|]+)", re.IGNORECASE)

# LP "Day type" text → card type (keyword match, order matters)
TYPE_KEYWORDS = [
    ("revision",    "recap"),
    ("derivation",  "derivation"),      # also "Derivation + Numerical"
    ("process",     "device"),          # "Process / Working": instruments & experiments
    ("working",     "device"),
    ("formula",     "formula"),
    ("numerical",   "formula"),
    ("application", "application"),
    ("comparison",  "concept"),
    ("concept",     "concept"),
]


def normalise_type(day_type: str | None) -> str | None:
    """Map the LP's free-text day type to a card type; None if unknown."""
    if not day_type:
        return None
    low = day_type.lower()
    for keyword, card_type in TYPE_KEYWORDS:
        if keyword in low:
            return card_type
    return None


def fingerprint(html: str) -> str:
    """Short content hash — lets the backfill detect a regenerated LP."""
    return hashlib.sha256(html.encode("utf-8")).hexdigest()[:16]


def _objectives(block) -> list[str]:
    for p in block.find_all("p"):
        if p.get_text(strip=True).lower().startswith("learning objectives"):
            ul = p.find_next_sibling("ul")
            if ul:
                return [li.get_text(" ", strip=True) for li in ul.find_all("li")]
            break
    return []


def _clean_lines(text: str) -> list[str]:
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if TAMIL_RE.search(line):
            continue
        if line.lower().startswith("next lesson"):
            continue
        lines.append(line)
    return lines


def parse_lp(html: str) -> dict:
    soup   = BeautifulSoup(html, "html.parser")
    blocks = soup.select('div.lp-day-block[id^="lp-day-"]')
    days   = []

    for block in blocks:
        num = int(block["id"].rsplit("-", 1)[-1])

        # Title
        title_el  = block.select_one(".lp-day-title") or block.find(["h2", "h3", "h4"])
        raw_title = title_el.get_text(" ", strip=True) if title_el else f"Day {num}"
        m         = DAY_TITLE_RE.match(raw_title)
        title     = m.group(1).strip() if m else raw_title

        # Meta line: Textbook / Day type / Technique
        meta    = {}
        meta_el = block.select_one(".lp-day-meta")
        if meta_el:
            for key, val in META_FIELD_RE.findall(meta_el.get_text(" ", strip=True)):
                meta[key.lower()] = val.strip()

        section   = meta.get("textbook", "")
        day_type  = meta.get("day type")
        card_type = normalise_type(day_type)
        if card_type is None and "revision" in title.lower():
            card_type = "recap"

        # Cleaned copy: drop teacher-only / Tamil blocks, title and meta
        clean = BeautifulSoup(str(block), "html.parser")
        for sel in [f".{c}" for c in DROP_CLASSES] + [".lp-day-title", ".lp-day-meta"]:
            for el in clean.select(sel):
                el.decompose()

        board_work = [_clean_lines(bw.get_text("\n", strip=True)) for bw in clean.select(".board-work")]
        lines      = _clean_lines(clean.get_text("\n", strip=True))

        days.append({
            "day":        num,
            "title":      title,
            "section":    section,
            "day_type":   day_type,
            "card_type":  card_type,
            "is_recap":   card_type == "recap",
            "objectives": _objectives(block),
            "board_work": ["\n".join(b) for b in board_work if b],
            "text":       "\n".join(lines),
        })

    return {"day_count": len(days), "days": days}


def load_lp(path: str | Path) -> dict:
    """Read a deployed LP file and parse it, with source info for staleness checks."""
    path = Path(path)
    html = path.read_text(encoding="utf-8")
    parsed = parse_lp(html)
    parsed["source_lp"] = {
        "path":         str(path),
        "hash":         fingerprint(html),
        "generated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
    }
    return parsed