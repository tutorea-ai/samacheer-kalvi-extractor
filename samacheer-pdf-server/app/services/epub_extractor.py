"""
epub_extractor.py
-----------------
Extracts clean lesson text from Samacheer Kalvi EPUB files (Classes 8-12).

How it works:
  1. Checks if EPUB folder already exists in storage/epub/ (cached)
  2. If not — downloads zip from Google Drive via gdown, unzips it
  3. Reads nav.xhtml → finds the correct anchor for (unit, lesson_type)
  4. Opens the correct index_split_00N.html
  5. Extracts HTML from lesson anchor to next lesson/unit boundary
  6. Strips HTML tags → returns clean plain text

Usage:
    extractor = EpubExtractor(epub_dir)
    text = extractor.extract(unit=2, lesson_type='prose')
    text = extractor.extract(unit=2, lesson_type='poem')
    text = extractor.extract(unit=2, lesson_type='supplementary')

Returns:
    str  — clean plain text ready to send to Claude
    None — if lesson not found (caller should fallback to pdfplumber)
"""

import os
import re
import zipfile
from pathlib import Path
from bs4 import BeautifulSoup


# Lesson type aliases — normalize whatever comes in
LESSON_TYPE_ALIASES = {
    'prose':         ['prose'],
    'poem':          ['poem'],
    'supplementary': ['supplementary', 'supplementary reader'],
}


class EpubExtractor:

    def __init__(self, epub_dir: Path):
        """
        epub_dir: Path to the unzipped EPUB folder
                  e.g. storage/epub/class-10-term0-english/
        """
        self.epub_dir = Path(epub_dir)
        self._nav_map = None   # lazy loaded

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, unit: int, lesson_type: str) -> str | None:
        """
        Extract clean text for the given unit and lesson type.

        Args:
            unit:        unit number (1-based, e.g. 1, 2, 3...)
            lesson_type: 'prose', 'poem', or 'supplementary'

        Returns:
            Clean plain text string, or None if not found.
        """
        lesson_type = lesson_type.lower().strip()

        if not self.epub_dir.exists():
            print(f"[EpubExtractor] EPUB folder not found: {self.epub_dir}")
            return None

        nav_map = self._get_nav_map()
        if not nav_map:
            return None

        unit_data = nav_map.get(unit)
        if not unit_data:
            print(f"[EpubExtractor] Unit {unit} not found in nav.xhtml")
            return None

        lesson_anchor = self._resolve_lesson_type(unit_data, lesson_type)
        if not lesson_anchor:
            print(f"[EpubExtractor] Lesson type '{lesson_type}' not found in Unit {unit}")
            return None

        split_file, anchor_id = lesson_anchor
        text = self._extract_content(unit, lesson_type, split_file, anchor_id, nav_map)
        return text

    # ------------------------------------------------------------------
    # Static helper: ensure EPUB is downloaded and unzipped
    # ------------------------------------------------------------------

    @staticmethod
    def prepare(epub_zip_path: Path) -> Path | None:
        """
        Given a zip file path, unzip it into a sibling folder if not already done.
        Returns the path to the unzipped folder, or None on failure.

        epub_zip_path: e.g. storage/epub/class-10-term0-english.zip
        Returns:       e.g. storage/epub/class-10-term0-english/
        """
        epub_zip_path = Path(epub_zip_path)
        epub_dir = epub_zip_path.parent / epub_zip_path.stem

        # Already unzipped — use cache
        if epub_dir.exists() and (epub_dir / 'nav.xhtml').exists():
            print(f"[EpubExtractor] Using cached EPUB: {epub_dir.name}")
            return epub_dir

        # Zip exists — unzip it
        if epub_zip_path.exists():
            print(f"[EpubExtractor] Unzipping {epub_zip_path.name}...")
            try:
                epub_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(epub_zip_path, 'r') as z:
                    z.extractall(epub_dir)
                print(f"[EpubExtractor] ✅ Unzipped to {epub_dir.name}")
                return epub_dir
            except Exception as e:
                print(f"[EpubExtractor] ❌ Unzip failed: {e}")
                return None

        print(f"[EpubExtractor] ❌ Zip not found: {epub_zip_path}")
        return None

    # ------------------------------------------------------------------
    # Nav map building
    # ------------------------------------------------------------------

    def _get_nav_map(self) -> dict | None:
        """
        Parse nav.xhtml and build a map:
        {
            unit_number (int): {
                'prose':         (split_file, anchor_id),
                'poem':          (split_file, anchor_id),
                'supplementary': (split_file, anchor_id),
            }
        }
        """
        if self._nav_map is not None:
            return self._nav_map

        nav_path = self.epub_dir / 'nav.xhtml'
        if not nav_path.exists():
            print(f"[EpubExtractor] nav.xhtml not found at {nav_path}")
            return None

        with open(nav_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        nav = soup.find('nav')
        if not nav:
            print("[EpubExtractor] <nav> element not found in nav.xhtml")
            return None

        top_ol = nav.find('ol', recursive=False)
        if not top_ol:
            return None

        nav_map = {}

        for li in top_ol.find_all('li', recursive=False):
            link = li.find('a')
            if not link:
                continue

            label = link.get_text(strip=True)

            # Skip the Contents entry
            if label.lower() == 'contents':
                continue

            unit_num = self._parse_unit_number(label)
            if unit_num is None:
                continue

            unit_data = {}
            sub_ol = li.find('ol')
            if not sub_ol:
                nav_map[unit_num] = unit_data
                continue

            for item in sub_ol.find_all('li', recursive=False):
                item_link = item.find('a')
                if not item_link:
                    continue

                item_label = item_link.get_text(strip=True).lower()
                normalized = self._normalize_lesson_type(item_label)

                if normalized:
                    # Store section heading anchor (e.g. id_Poem_1) as _heading
                    section_href = item_link.get('href', '')
                    sec_file, sec_anchor = self._parse_href(section_href)
                    if sec_file and sec_anchor:
                        unit_data[f'{normalized}_heading'] = (sec_file, sec_anchor)
                    # Store first lesson anchor (e.g. id_The_Grumble_Family)
                    inner_ol = item.find('ol')
                    if inner_ol:
                        first_lesson_link = inner_ol.find('a')
                        if first_lesson_link:
                            href = first_lesson_link.get('href', '')
                            split_file, anchor_id = self._parse_href(href)
                            if split_file and anchor_id:
                                unit_data[normalized] = (split_file, anchor_id)

            nav_map[unit_num] = unit_data

        self._nav_map = nav_map
        return nav_map

    # ------------------------------------------------------------------
    # Content extraction
    # ------------------------------------------------------------------

    def _extract_content(
        self,
        unit: int,
        lesson_type: str,
        split_file: str,
        anchor_id: str,
        nav_map: dict
    ) -> str | None:
        """
        Open the split HTML file, find the anchor, extract content
        until the next lesson/unit boundary, return clean text.
        """
        html_path = self.epub_dir / split_file
        if not html_path.exists():
            print(f"[EpubExtractor] File not found: {html_path}")
            return None

        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        start_el = soup.find(id=anchor_id)
        if not start_el:
            print(f"[EpubExtractor] Anchor id='{anchor_id}' not found in {split_file}")
            return None

        stop_ids = self._get_stop_ids(unit, lesson_type, nav_map)

        # Collect all siblings after start until a stop id
        content_parts = [str(start_el)]
        for sibling in start_el.next_siblings:
            if not hasattr(sibling, 'get'):
                content_parts.append(str(sibling))
                continue
            if sibling.get('id') in stop_ids:
                break
            content_parts.append(str(sibling))

        # Handle cross-file continuation
        cross_content = self._get_cross_file_content(unit, lesson_type, split_file, nav_map)
        if cross_content:
            content_parts.append(cross_content)

        full_html = ''.join(content_parts)
        text = BeautifulSoup(full_html, 'html.parser').get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text).strip()

        return text if text else None

    def _get_cross_file_content(
        self,
        unit: int,
        lesson_type: str,
        current_file: str,
        nav_map: dict
    ) -> str | None:
        """
        Handle lessons that genuinely span two split files.
        e.g. Unit 6 Prose starts in index_split_002.html
             but Glossary/exercises continue in index_split_003.html

        Only triggers when:
        1. The FIRST stop anchor is in a different file than current_file
           (meaning there is NO stop boundary in the current file at all)
        2. The lesson itself started in current_file

        Does NOT trigger when the lesson has a stop anchor in the current file
        but a later stop anchor is in a different file — that means the lesson
        ends cleanly in the current file.
        """
        stops = self._get_stop_anchors(unit, lesson_type, nav_map)
        if not stops:
            return None

        # Check the FIRST stop anchor only
        first_stop_file, first_stop_anchor = stops[0]

        # If the first stop is in the same file — lesson ends here, no cross-file needed
        if first_stop_file == current_file:
            return None

        # First stop is in a different file — lesson genuinely continues there
        html_path = self.epub_dir / first_stop_file
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
            if el.get('id') == first_stop_anchor:
                break
            parts.append(str(el))

        return ''.join(parts) if parts else None

    # ------------------------------------------------------------------
    # Stop ID helpers
    # ------------------------------------------------------------------

    def _get_stop_ids(self, unit: int, lesson_type: str, nav_map: dict) -> set:
        stop_ids = set()
        for _, anchor_id in self._get_stop_anchors(unit, lesson_type, nav_map):
            if anchor_id:
                stop_ids.add(anchor_id)
        return stop_ids

    def _get_stop_anchors(self, unit: int, lesson_type: str, nav_map: dict) -> list:
        """
        Returns list of (split_file, anchor_id) that mark the END
        of the current lesson — start of next section.
        """
        stops = []
        unit_data = nav_map.get(unit, {})
        lesson_order = ['prose', 'poem', 'supplementary']

        # Next lesson type in same unit
        # Add BOTH the section heading anchor (e.g. id_Poem_1)
        # AND the first lesson anchor as stop points.
        # Section heading comes first so the <h2>Poem</h2> is excluded.
        if lesson_type in lesson_order:
            idx = lesson_order.index(lesson_type)
            for next_type in lesson_order[idx + 1:]:
                if next_type in unit_data:
                    # Section heading anchor (earlier boundary)
                    heading_key = f"{next_type}_heading"
                    if heading_key in unit_data:
                        stops.append(unit_data[heading_key])
                    # First lesson anchor (later boundary — belt and braces)
                    stops.append(unit_data[next_type])
                    break

        # Start of next unit
        next_unit_anchor = self._get_unit_anchor(unit + 1)
        if next_unit_anchor:
            stops.append(next_unit_anchor)

        return stops

    def _get_unit_anchor(self, unit_num: int) -> tuple | None:
        """Get the (split_file, anchor_id) for a unit heading from nav.xhtml."""
        nav_path = self.epub_dir / 'nav.xhtml'
        if not nav_path.exists():
            return None

        with open(nav_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        nav = soup.find('nav')
        if not nav:
            return None

        top_ol = nav.find('ol', recursive=False)
        for li in top_ol.find_all('li', recursive=False):
            link = li.find('a')
            if not link:
                continue
            label = link.get_text(strip=True)
            num = self._parse_unit_number(label)
            if num == unit_num:
                href = link.get('href', '')
                return self._parse_href(href)

        return None

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _parse_unit_number(self, label: str) -> int | None:
        """
        Extract unit number from labels like:
        'Unit1', 'Unit – 2', 'Unit - 4', 'Unit 7'
        """
        match = re.search(r'[Uu]nit\s*[-–]?\s*(\d+)', label.strip())
        if match:
            return int(match.group(1))
        return None

    def _normalize_lesson_type(self, label: str) -> str | None:
        """Normalize to 'prose', 'poem', or 'supplementary'."""
        label = label.lower().strip()
        for normalized, aliases in LESSON_TYPE_ALIASES.items():
            if any(alias in label for alias in aliases):
                return normalized
        return None

    def _resolve_lesson_type(self, unit_data: dict, lesson_type: str) -> tuple | None:
        normalized = self._normalize_lesson_type(lesson_type)
        if not normalized:
            return None
        return unit_data.get(normalized)

    def _parse_href(self, href: str) -> tuple:
        """
        Parse 'index_split_001.html#id_Zigzag'
        Returns (split_file, anchor_id) or (href, None)
        """
        if '#' in href:
            parts = href.split('#', 1)
            return (parts[0], parts[1] if parts[1] else None)
        return (href, None)


# ------------------------------------------------------------------
# Quick test
# ------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    epub_zip = sys.argv[1] if len(sys.argv) > 1 else 'class-10-term0-english.zip'
    epub_dir = EpubExtractor.prepare(Path(epub_zip))

    if not epub_dir:
        print("❌ Could not prepare EPUB")
        sys.exit(1)

    extractor = EpubExtractor(epub_dir)

    test_cases = [
        (1, 'prose'),
        (2, 'prose'),
        (2, 'poem'),
        (2, 'supplementary'),
        (3, 'prose'),
        (6, 'prose'),
        (7, 'supplementary'),
    ]

    for unit, lesson_type in test_cases:
        text = extractor.extract(unit=unit, lesson_type=lesson_type)
        if text:
            print(f"✅ Unit {unit} {lesson_type}: {len(text)} chars — {text[:80]}...")
        else:
            print(f"❌ Unit {unit} {lesson_type}: FAILED")