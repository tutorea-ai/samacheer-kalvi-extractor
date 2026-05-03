"""
ss_epub_extractor.py
--------------------
Extracts clean chapter text from Samacheer Kalvi Social Science EPUB files.
Handles History, Geography, Civics, Economics disciplines.

Key differences from English epub_extractor.py:
  - No lesson_type (prose/poem/supplementary) — each unit is one complete chapter
  - Discipline detection from nav.xhtml using text content + unit number reset logic
  - TOC anchors are sequential (id_Toc168552968) not semantic
  - Geography has no explicit heading — detected by unit number reset after History

Usage:
    extractor = SocialScienceEpubExtractor(epub_dir)
    text = extractor.extract(discipline='history', unit=1)
    text = extractor.extract(discipline='geography', unit=2)
    text = extractor.extract(discipline='civics', unit=1)
    text = extractor.extract(discipline='economics', unit=3)

Returns:
    str  — clean plain text ready to send to Claude
    None — if chapter not found
"""

import os
import re
import zipfile
from pathlib import Path
from bs4 import BeautifulSoup


# Known discipline headings in nav.xhtml
DISCIPLINE_HEADINGS = ['history', 'civics', 'economics']

# Geography keywords — used to detect Geography units
# (Geography has no explicit heading in nav.xhtml)
GEOGRAPHY_KEYWORDS = ['india', 'location', 'climate', 'agriculture', 'resources',
                      'population', 'physical geography', 'human geography',
                      'drainage', 'vegetation', 'tamil nadu']


class SocialScienceEpubExtractor:

    def __init__(self, epub_dir: Path):
        """
        epub_dir: Path to the unzipped EPUB folder
                  e.g. storage/epub/class-10-term0-socialscience/
        """
        self.epub_dir = Path(epub_dir)
        self._nav_map = None  # lazy loaded

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, discipline: str, unit: int) -> str | None:
        """
        Extract clean text for the given discipline and unit.

        Args:
            discipline: 'history', 'geography', 'civics', 'economics'
            unit:       unit number (1-based)

        Returns:
            Clean plain text string, or None if not found.
        """
        discipline = discipline.lower().strip()

        nav_map = self._get_nav_map()
        if not nav_map:
            return None

        disc_units = nav_map.get(discipline)
        if not disc_units:
            print(f"[SSEpubExtractor] Discipline '{discipline}' not found in nav.xhtml")
            return None

        # Find the requested unit
        unit_entry = next((u for u in disc_units if u['unit'] == unit), None)
        if not unit_entry:
            print(f"[SSEpubExtractor] Unit {unit} not found in {discipline}")
            return None

        # Find stop anchor — next unit entry across all disciplines
        stop_entry = self._get_stop_entry(discipline, unit, nav_map)

        # Extract content
        text = self._extract_content(unit_entry, stop_entry)
        return text

    # ------------------------------------------------------------------
    # Static helper: unzip EPUB
    # ------------------------------------------------------------------

    @staticmethod
    def prepare(epub_zip_path: Path) -> Path | None:
        """
        Unzip EPUB if not already done. Returns path to unzipped folder.
        """
        epub_zip_path = Path(epub_zip_path)
        epub_dir = epub_zip_path.parent / epub_zip_path.stem

        if epub_dir.exists() and (epub_dir / 'nav.xhtml').exists():
            print(f"[SSEpubExtractor] Using cached EPUB: {epub_dir.name}")
            return epub_dir

        if epub_zip_path.exists():
            print(f"[SSEpubExtractor] Unzipping {epub_zip_path.name}...")
            try:
                epub_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(epub_zip_path, 'r') as z:
                    z.extractall(epub_dir)
                print(f"[SSEpubExtractor] ✅ Unzipped to {epub_dir.name}")
                return epub_dir
            except Exception as e:
                print(f"[SSEpubExtractor] ❌ Unzip failed: {e}")
                return None

        print(f"[SSEpubExtractor] ❌ Zip not found: {epub_zip_path}")
        return None

    # ------------------------------------------------------------------
    # Nav map building
    # ------------------------------------------------------------------

    def _get_nav_map(self) -> dict | None:
        """
        Parse nav.xhtml and build a discipline → units map:
        {
            'history':   [{'unit': 1, 'file': 'index_split_000.html', 'anchor': 'id_Toc...'}, ...],
            'geography': [...],
            'civics':    [...],
            'economics': [...],
        }

        Geography detection:
            - No explicit GEOGRAPHY heading in nav.xhtml
            - Detected when unit numbers reset from high (9,10) back to low (1,2)
              after History section ends
            - Unit titles contain India/location/climate etc.
        """
        if self._nav_map is not None:
            return self._nav_map

        nav_path = self.epub_dir / 'nav.xhtml'
        if not nav_path.exists():
            print(f"[SSEpubExtractor] nav.xhtml not found at {nav_path}")
            return None

        with open(nav_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        nav = soup.find('nav')
        if not nav:
            return None

        top_ol = nav.find('ol', recursive=False)
        if not top_ol:
            return None

        nav_map = {
            'history': [],
            'geography': [],
            'civics': [],
            'economics': [],
        }

        current_discipline = 'history'  # default start
        prev_unit_num = 0
        history_done = False

        for li in top_ol.find_all('li', recursive=False):
            link = li.find('a')
            if not link:
                continue

            text = link.get_text(strip=True)
            href = link.get('href', '')

            # ── Explicit discipline heading detection ──────────────────
            text_clean = text.strip().upper()
            if text_clean == 'HISTORY':
                current_discipline = 'history'
                continue
            if text_clean == 'CIVICS':
                current_discipline = 'civics'
                history_done = True
                prev_unit_num = 0
                # Check if Civics Unit 1 is nested inside this li
                nested_ol = li.find('ol')
                if nested_ol:
                    for nested_li in nested_ol.find_all('li', recursive=False):
                        nested_link = nested_li.find('a')
                        if not nested_link:
                            continue
                        nested_text = nested_link.get_text(strip=True)
                        nested_unit = re.search(r'Unit\s*[-–]\s*(\d+)', nested_text)
                        if nested_unit:
                            nested_href = nested_link.get('href', '')
                            nf, na = self._parse_href(nested_href)
                            if na:
                                nav_map['civics'].append({
                                    'unit':   int(nested_unit.group(1)),
                                    'title':  nested_text,
                                    'file':   nf,
                                    'anchor': na,
                                })
                            break  # Only get Unit 1 — rest are sub-sections
                continue
            if text_clean == 'ECONOMICS':
                current_discipline = 'economics'
                prev_unit_num = 0
                continue

            # ── Unit detection ─────────────────────────────────────────
            unit_match = re.search(r'Unit\s*[-–]\s*(\d+)', text)
            if not unit_match:
                continue

            unit_num = int(unit_match.group(1))
            split_file, anchor = self._parse_href(href)

            if not anchor:
                continue

            # ── Geography detection ────────────────────────────────────
            # Geography has no heading — detected when:
            # 1. We're still in history_done=False territory
            # 2. Unit number resets (goes from 10 back to 1)
            # 3. Unit title contains geography keywords
            if current_discipline == 'history' and not history_done:
                if unit_num < prev_unit_num and self._is_geography_unit(text):
                    current_discipline = 'geography'
                    prev_unit_num = 0

            entry = {
                'unit':   unit_num,
                'title':  text,
                'file':   split_file,
                'anchor': anchor,
            }

            nav_map[current_discipline].append(entry)
            prev_unit_num = unit_num

        self._nav_map = nav_map
        return nav_map

    def _is_geography_unit(self, title: str) -> bool:
        """Check if a unit title belongs to Geography."""
        title_lower = title.lower()
        return any(kw in title_lower for kw in GEOGRAPHY_KEYWORDS)

    # ------------------------------------------------------------------
    # Content extraction
    # ------------------------------------------------------------------

    def _extract_content(self, unit_entry: dict, stop_entry: dict | None) -> str | None:
        """
        Extract content from unit_entry anchor to stop_entry anchor.
        Handles cross-file content automatically.
        """
        start_file   = unit_entry['file']
        start_anchor = unit_entry['anchor']

        html_path = self.epub_dir / start_file
        if not html_path.exists():
            print(f"[SSEpubExtractor] File not found: {html_path}")
            return None

        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        start_el = soup.find(id=start_anchor)
        if not start_el:
            print(f"[SSEpubExtractor] Anchor '{start_anchor}' not found in {start_file}")
            return None

        # Determine stop anchor
        stop_anchor = stop_entry['anchor'] if stop_entry else None
        stop_file   = stop_entry['file']   if stop_entry else None

        # Collect content
        content_parts = [str(start_el)]

        for sibling in start_el.next_siblings:
            if not hasattr(sibling, 'get'):
                content_parts.append(str(sibling))
                continue
            # Stop if we hit the stop anchor in the same file
            if stop_file == start_file and sibling.get('id') == stop_anchor:
                break
            content_parts.append(str(sibling))

        # Cross-file continuation
        if stop_file and stop_file != start_file:
            cross = self._get_cross_file_content(stop_file, stop_anchor)
            if cross:
                content_parts.append(cross)

        # Strip HTML → clean text
        full_html = ''.join(content_parts)
        text = BeautifulSoup(full_html, 'html.parser').get_text(
            separator=' ', strip=True
        )
        text = re.sub(r'\s+', ' ', text).strip()

        if text:
            print(f"[SSEpubExtractor] ✅ Extracted {len(text)} chars")
        return text if text else None

    def _get_cross_file_content(self, stop_file: str, stop_anchor: str) -> str | None:
        """
        When content spans two split files, get content from start
        of stop_file up to the stop_anchor.
        """
        html_path = self.epub_dir / stop_file
        if not html_path.exists():
            return None

        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        parts = []
        body = soup.body or soup
        for el in body.children:
            if not hasattr(el, 'get'):
                parts.append(str(el))
                continue
            if el.get('id') == stop_anchor:
                break
            parts.append(str(el))

        return ''.join(parts) if parts else None

    # ------------------------------------------------------------------
    # Stop entry helper
    # ------------------------------------------------------------------

    def _get_stop_entry(
        self,
        discipline: str,
        unit: int,
        nav_map: dict
    ) -> dict | None:
        """
        Find the next unit entry after (discipline, unit) across all disciplines.
        This is the stop boundary for content extraction.

        Order of disciplines in the book:
        history → geography → civics → economics
        """
        discipline_order = ['history', 'geography', 'civics', 'economics']

        disc_units = nav_map.get(discipline, [])

        # Find current unit index
        current_idx = next(
            (i for i, u in enumerate(disc_units) if u['unit'] == unit),
            None
        )
        if current_idx is None:
            return None

        # Next unit in same discipline
        if current_idx + 1 < len(disc_units):
            return disc_units[current_idx + 1]

        # Last unit in discipline — jump to first unit of next discipline
        current_disc_idx = discipline_order.index(discipline)
        for next_disc in discipline_order[current_disc_idx + 1:]:
            next_units = nav_map.get(next_disc, [])
            if next_units:
                return next_units[0]

        return None  # Last chapter in book

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _parse_href(self, href: str) -> tuple:
        """Parse 'index_split_001.html#id_Toc168553000' → (file, anchor)"""
        if '#' in href:
            parts = href.split('#', 1)
            return (parts[0], parts[1] if parts[1] else None)
        return (href, None)


# ------------------------------------------------------------------
# Quick test
# ------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    epub_zip = sys.argv[1] if len(sys.argv) > 1 else 'class-10-term0-socialscience.zip'
    epub_dir = SocialScienceEpubExtractor.prepare(Path(epub_zip))

    if not epub_dir:
        print("❌ Could not prepare EPUB")
        sys.exit(1)

    extractor = SocialScienceEpubExtractor(epub_dir)

    test_cases = [
        ('history',   1),
        ('history',   2),
        ('history',  10),
        ('geography', 1),
        ('geography', 2),
        ('civics',    1),
        ('civics',    2),
        ('economics', 1),
        ('economics', 5),
    ]

    for discipline, unit in test_cases:
        text = extractor.extract(discipline=discipline, unit=unit)
        if text:
            print(f"✅ {discipline:12} Unit {unit:2}: {len(text):6} chars — {text[:60]}...")
        else:
            print(f"❌ {discipline:12} Unit {unit:2}: FAILED")