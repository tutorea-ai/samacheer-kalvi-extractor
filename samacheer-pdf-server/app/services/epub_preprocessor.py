"""
epub_preprocessor.py
--------------------
One-time EPUB preprocessing for SK-CAP.

What it does:
  1. Reads nav.xhtml — source of truth for all lesson anchors
  2. Combines all index_split_*.html files into one big HTML
  3. Finds each lesson heading in the combined HTML
  4. Stamps a clean data-sk-unit tag on each heading
  5. Saves combined_tagged.html — used forever after

Tag format:
  English:        data-sk-unit="prose-2"
                  data-sk-unit="poem-2"
                  data-sk-unit="supplementary-2"
  Social Science: data-sk-unit="history-1"
                  data-sk-unit="geography-3"
                  data-sk-unit="civics-2"
                  data-sk-unit="economics-4"
  Science/Maths:  data-sk-unit="unit-1"
                  data-sk-unit="unit-2"

Usage:
  preprocessor = EpubPreprocessor(epub_dir)
  preprocessor.prepare()   ← run once, creates combined_tagged.html
  
  # Then extract:
  text = preprocessor.extract("prose", 2)        # English
  text = preprocessor.extract("history", 1)       # Social Science
  text = preprocessor.extract("unit", 5)          # Science

Returns:
  str  — clean plain text
  None — if lesson not found
"""

import re
import copy
import zipfile
from pathlib import Path
from bs4 import BeautifulSoup, Tag

# ── Lesson type aliases ────────────────────────────────────────────────────────
ENGLISH_LESSON_TYPES = {
    'prose':         'prose',
    'poem':          'poem',
    'supplementary': 'supplementary',
    'supplementary reader': 'supplementary',
}

# ── Discipline names for Social Science ───────────────────────────────────────
SS_DISCIPLINES = ['history', 'geography', 'civics', 'economics']

# ── Geography keywords for discipline detection ───────────────────────────────
GEOGRAPHY_KEYWORDS = [
    'india', 'location', 'climate', 'agriculture', 'resources',
    'population', 'physical geography', 'human geography',
    'drainage', 'vegetation', 'tamil nadu', 'landforms',
    'atmosphere', 'hydrosphere', 'lithosphere', 'biosphere',
    'universe', 'solar system', 'globe', 'continent', 'map'
]

# ── Inline HTML tags — walk up to block parent ────────────────────────────────
INLINE_TAGS = {'b', 'span', 'em', 'i', 'a', 'strong', 'small'}
BLOCK_TAGS  = {'h1', 'h2', 'h3', 'h4', 'p', 'div', 'section', 'ul', 'ol', 'table'}


class EpubPreprocessor:

    def __init__(self, epub_dir: Path):
        """
        epub_dir: Path to unzipped EPUB folder
        """
        self.epub_dir = Path(epub_dir)
        self.combined_tagged_path = self.epub_dir / 'combined_tagged.html'

    # ──────────────────────────────────────────────────────────────────────────
    # Static helper: unzip EPUB
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def prepare_zip(epub_zip_path: Path) -> Path | None:
        """Unzip EPUB if not already done. Returns path to unzipped folder."""
        epub_zip_path = Path(epub_zip_path)
        epub_dir = epub_zip_path.parent / epub_zip_path.stem

        if epub_dir.exists() and (epub_dir / 'nav.xhtml').exists():
            print(f"[Preprocessor] Using cached EPUB: {epub_dir.name}")
            return epub_dir

        if epub_zip_path.exists():
            print(f"[Preprocessor] Unzipping {epub_zip_path.name}...")
            try:
                epub_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(epub_zip_path, 'r') as z:
                    z.extractall(epub_dir)
                print(f"[Preprocessor] ✅ Unzipped to {epub_dir.name}")
                return epub_dir
            except Exception as e:
                print(f"[Preprocessor] ❌ Unzip failed: {e}")
                return None

        print(f"[Preprocessor] ❌ Zip not found: {epub_zip_path}")
        return None

    # ──────────────────────────────────────────────────────────────────────────
    # Public: prepare combined_tagged.html
    # ──────────────────────────────────────────────────────────────────────────

    def prepare(self, force: bool = False) -> bool:
        """
        Run preprocessing — combine + tag.
        Skips if combined_tagged.html already exists (unless force=True).

        Returns True on success, False on failure.
        """
        if self.combined_tagged_path.exists() and not force:
            print(f"[Preprocessor] combined_tagged.html already exists — skipping")
            return True

        print(f"[Preprocessor] Starting preprocessing for {self.epub_dir.name}...")

        # Step 1: Parse nav.xhtml → get lesson tag map
        tag_map = self._build_tag_map()
        if not tag_map:
            print(f"[Preprocessor] ❌ Failed to build tag map")
            return False

        print(f"[Preprocessor] Tag map built — {len(tag_map)} lessons found:")
        for tag, (split_file, anchor) in tag_map.items():
            print(f"   {tag} → {anchor} ({split_file})")

        # Step 2: Combine all split HTML files into one
        combined_soup = self._combine_split_files()
        if not combined_soup:
            print(f"[Preprocessor] ❌ Failed to combine split files")
            return False

        print(f"[Preprocessor] Combined HTML built")

        # Step 3: Stamp clean tags on headings
        tagged_count = self._stamp_tags(combined_soup, tag_map)
        print(f"[Preprocessor] ✅ Stamped {tagged_count} tags")

        # Step 4: Save combined_tagged.html
        with open(self.combined_tagged_path, 'w', encoding='utf-8') as f:
            f.write(str(combined_soup))

        print(f"[Preprocessor] ✅ Saved: {self.combined_tagged_path}")
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # Public: extract lesson text
    # ──────────────────────────────────────────────────────────────────────────

    def extract(self, lesson_type: str, unit: int) -> str | None:
        """
        Extract clean text for a lesson.

        Args:
            lesson_type: 'prose'/'poem'/'supplementary' for English
                         'history'/'geography'/'civics'/'economics' for SS
                         'unit' for Science/Maths
            unit:        unit number (1-based)

        Returns:
            Clean plain text, or None if not found.
        """
        if not self.combined_tagged_path.exists():
            print(f"[Preprocessor] combined_tagged.html not found — run prepare() first")
            return None

        tag_value = f"{lesson_type}-{unit}"

        with open(self.combined_tagged_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        # Find start element
        start_el = soup.find(attrs={"data-sk-unit": tag_value})
        if not start_el:
            print(f"[Preprocessor] Tag '{tag_value}' not found in combined_tagged.html")
            return None

        # Find stop element — next lesson tag
        stop_el = self._find_next_tag(soup, lesson_type, unit)

        # Collect content between start and stop
        content_parts = [str(start_el)]
        for sibling in start_el.next_siblings:
            if not hasattr(sibling, 'get'):
                content_parts.append(str(sibling))
                continue
            if stop_el and sibling == stop_el:
                break
            content_parts.append(str(sibling))

        # Strip HTML → clean text
        full_html = ''.join(content_parts)
        text = BeautifulSoup(full_html, 'html.parser').get_text(
            separator=' ', strip=True
        )
        text = re.sub(r'\s+', ' ', text).strip()

        if text:
            print(f"[Preprocessor] ✅ Extracted {len(text)} chars for {tag_value}")
        return text if text else None

    # ──────────────────────────────────────────────────────────────────────────
    # Step 1: Build tag map from nav.xhtml
    # ──────────────────────────────────────────────────────────────────────────

    def _build_tag_map(self) -> dict | None:
        """
        Parse nav.xhtml and build:
        {
            "prose-1":         ("index_split_000.html", "id_His_First_Flight"),
            "poem-1":          ("index_split_000.html", "id_Life"),
            "history-1":       ("index_split_000.html", "id_Toc168552968"),
            "geography-1":     ("index_split_002.html", "id_Toc168553050"),
            ...
        }
        """
        nav_path = self.epub_dir / 'nav.xhtml'
        if not nav_path.exists():
            return None

        with open(nav_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        nav = soup.find('nav')
        if not nav:
            return None

        top_ol = nav.find('ol', recursive=False)
        if not top_ol:
            return None

        # Detect subject type from nav structure
        subject_type = self._detect_subject_type(top_ol)
        print(f"[Preprocessor] Detected subject type: {subject_type}")

        if subject_type == 'english':
            return self._build_english_tag_map(top_ol)
        elif subject_type == 'socialscience':
            return self._build_ss_tag_map(top_ol)
        else:
            return self._build_linear_tag_map(top_ol)

    def _detect_subject_type(self, top_ol) -> str:
        """
        Detect whether this is English, Social Science, or Linear (Science/Maths).
        """
        all_text = top_ol.get_text().lower()

        # Social Science has discipline headings
        if 'history' in all_text and 'geography' in all_text:
            return 'socialscience'

        # English has prose/poem/supplementary
        if 'prose' in all_text or 'poem' in all_text:
            return 'english'

        # Default — linear (Science, Maths)
        return 'linear'

    def _build_english_tag_map(self, top_ol) -> dict:
        """Build tag map for English (Type A) nav structure."""
        tag_map = {}

        for unit_li in top_ol.find_all('li', recursive=False):
            unit_link = unit_li.find('a')
            if not unit_link:
                continue

            unit_text = unit_link.get_text(strip=True)
            unit_match = re.search(r'[Uu]nit\s*[-–]?\s*(\d+)', unit_text)
            if not unit_match:
                continue

            unit_num = int(unit_match.group(1))
            sub_ol = unit_li.find('ol')
            if not sub_ol:
                continue

            for item_li in sub_ol.find_all('li', recursive=False):
                item_link = item_li.find('a')
                if not item_link:
                    continue

                item_text = item_link.get_text(strip=True).lower()
                lesson_type = None

                for alias, normalized in ENGLISH_LESSON_TYPES.items():
                    if alias in item_text:
                        lesson_type = normalized
                        break

                if not lesson_type:
                    continue

                # Get first lesson anchor inside
                inner_ol = item_li.find('ol')
                if inner_ol:
                    first_link = inner_ol.find('a')
                    if first_link:
                        href = first_link.get('href', '')
                        sf, anchor = self._parse_href(href)
                        if sf and anchor:
                            tag = f"{lesson_type}-{unit_num}"
                            tag_map[tag] = (sf, anchor)

        return tag_map

    def _build_ss_tag_map(self, top_ol) -> dict:
        """Build tag map for Social Science (Type B) nav structure."""
        tag_map = {}
        current_discipline = 'history'
        prev_unit_num = 0
        pending_unit_num = None
        pending_unit_href = None
        history_done = False

        for li in top_ol.find_all('li', recursive=False):
            link = li.find('a')
            if not link:
                continue

            text = link.get_text(strip=True)
            href = link.get('href', '')
            text_upper = text.strip().upper()

            # Explicit discipline headings
            if text_upper == 'HISTORY':
                current_discipline = 'history'
                pending_unit_num = None
                prev_unit_num = 0
                continue

            if text_upper == 'CIVICS':
                current_discipline = 'civics'
                history_done = True
                pending_unit_num = None
                prev_unit_num = 0
                # Civics Unit 1 may be nested inside
                nested_ol = li.find('ol')
                if nested_ol:
                    for nli in nested_ol.find_all('li', recursive=False):
                        nl = nli.find('a')
                        if not nl: continue
                        nt = nl.get_text(strip=True)
                        nh = nl.get('href', '')
                        um = re.search(r'Unit\s*[-–]\s*(\d+)', nt)
                        if um:
                            sf, an = self._parse_href(nh)
                            if an:
                                tag = f"civics-{um.group(1)}"
                                tag_map[tag] = (sf, an)
                            break
                continue

            if text_upper == 'ECONOMICS':
                current_discipline = 'economics'
                pending_unit_num = None
                prev_unit_num = 0
                continue

            # Unit number only (e.g. "Unit – 2")
            unit_num_only = re.match(r'^Unit\s*[-–]\s*(\d+)\s*$', text.strip())
            if unit_num_only:
                pending_unit_num = int(unit_num_only.group(1))
                pending_unit_href = href
                continue

            # Unit with title on same line
            unit_with_title = re.match(r'^Unit\s*[-–]\s*(\d+)\s+(.+)', text.strip())
            if unit_with_title:
                unit_num = int(unit_with_title.group(1))
                sf, an = self._parse_href(href)
                if an:
                    if current_discipline == 'history' and not history_done:
                        if unit_num < prev_unit_num and self._is_geo(text):
                            current_discipline = 'geography'
                            prev_unit_num = 0
                    tag = f"{current_discipline}-{unit_num}"
                    tag_map[tag] = (sf, an)
                    prev_unit_num = unit_num
                pending_unit_num = None
                pending_unit_href = None
                continue

            # Title entry following unit number entry
            if pending_unit_num is not None:
                # Use pending_unit_href anchor (unit number entry) as boundary
                if pending_unit_href:
                    sf, an = self._parse_href(pending_unit_href)
                else:
                    sf, an = self._parse_href(href)

                if an:
                    if current_discipline == 'history' and not history_done:
                        if pending_unit_num < prev_unit_num and self._is_geo(text):
                            current_discipline = 'geography'
                            prev_unit_num = 0

                    tag = f"{current_discipline}-{pending_unit_num}"
                    tag_map[tag] = (sf, an)
                    prev_unit_num = pending_unit_num

                    # Check nested ol for hidden sub-units (e.g. Unit 3 in Unit 2)
                    nested_ol = li.find('ol')
                    if nested_ol:
                        existing = {t for t in tag_map if t.startswith(current_discipline)}
                        for nli in nested_ol.find_all('li', recursive=False):
                            nl = nli.find('a')
                            if not nl: continue
                            nt = nl.get_text(strip=True)
                            nh = nl.get('href', '')
                            if re.match(r'^\d+\.\d+', nt): continue
                            if nt in ['Learning Objectives', 'To acquaint ourselves with']: continue
                            if re.match(r'^\d', nt): continue
                            nsf, nan = self._parse_href(nh)
                            if nan:
                                inferred = pending_unit_num + 1
                                while f"{current_discipline}-{inferred}" in existing:
                                    inferred += 1
                                tag = f"{current_discipline}-{inferred}"
                                tag_map[tag] = (nsf, nan)
                                existing.add(tag)

                pending_unit_num = None
                pending_unit_href = None
                continue

            pending_unit_num = None
            pending_unit_href = None

        return tag_map

    def _build_linear_tag_map(self, top_ol) -> dict:
        """Build tag map for linear subjects like Science/Maths (Type C)."""
        tag_map = {}

        for li in top_ol.find_all('li', recursive=False):
            link = li.find('a')
            if not link:
                continue

            text = link.get_text(strip=True)
            href = link.get('href', '')

            unit_match = re.search(r'[Uu]nit\s*[-–]?\s*(\d+)', text)
            if unit_match:
                unit_num = int(unit_match.group(1))
                sf, an = self._parse_href(href)
                if sf and an:
                    tag = f"unit-{unit_num}"
                    tag_map[tag] = (sf, an)

        return tag_map

    # ──────────────────────────────────────────────────────────────────────────
    # Step 2: Combine all split HTML files
    # ──────────────────────────────────────────────────────────────────────────

    def _combine_split_files(self):
        """
        Combine all index_split_*.html files into one BeautifulSoup object.
        Files are combined in order: 000, 001, 002...
        Returns a BeautifulSoup with all content in one <body>.
        """
        # Get all split files in order
        split_files = sorted(
            self.epub_dir.glob('index_split_*.html'),
            key=lambda f: f.name
        )

        if not split_files:
            print(f"[Preprocessor] No split files found")
            return None

        print(f"[Preprocessor] Combining {len(split_files)} split files...")

        # Create a new combined soup
        combined = BeautifulSoup(
            '<html><head></head><body></body></html>',
            'html.parser'
        )
        combined_body = combined.find('body')

        for split_file in split_files:
            with open(split_file, 'r', encoding='utf-8') as f:
                file_soup = BeautifulSoup(f.read(), 'html.parser')

            body = file_soup.find('body')
            if body:
                for child in list(body.children):
                    combined_body.append(copy.copy(child))

        print(f"[Preprocessor] ✅ Combined successfully")
        return combined

    # ──────────────────────────────────────────────────────────────────────────
    # Step 3: Stamp clean tags on headings
    # ──────────────────────────────────────────────────────────────────────────

    def _stamp_tags(self, soup, tag_map: dict) -> int:
        """
        For each entry in tag_map, find the element in soup and stamp
        data-sk-unit tag on it.

        Returns count of successfully stamped tags.
        """
        count = 0

        for tag_value, (split_file, anchor) in tag_map.items():
            # Find element with this anchor
            el = soup.find(id=anchor)
            if not el:
                print(f"   ⚠️  Anchor '{anchor}' not found for tag '{tag_value}'")
                continue

            # If inline element, walk up to block parent
            if el.name in INLINE_TAGS:
                parent = el.parent
                while parent and parent.name not in BLOCK_TAGS:
                    parent = parent.parent
                if parent and parent.name in BLOCK_TAGS:
                    el = parent

            # Stamp the tag
            el['data-sk-unit'] = tag_value
            count += 1
            print(f"   ✅ Stamped '{tag_value}' on <{el.name}>")

        return count

    # ──────────────────────────────────────────────────────────────────────────
    # Extraction helper: find next tag
    # ──────────────────────────────────────────────────────────────────────────

    def _find_next_tag(self, soup, lesson_type: str, unit: int):
        """
        Find the stop element — next lesson data-sk-unit tag.
        Skips gaps (e.g. Geography Unit 5 missing from nav).
        """
        english_order = ['prose', 'poem', 'supplementary']
        ss_order      = ['history', 'geography', 'civics', 'economics']

        # Try next units of same type — skip gaps
        for next_unit in range(unit + 1, unit + 10):
            el = soup.find(attrs={"data-sk-unit": f"{lesson_type}-{next_unit}"})
            if el:
                return el

        # For English — try next lesson type in same unit
        if lesson_type in english_order:
            idx = english_order.index(lesson_type)
            for next_type in english_order[idx + 1:]:
                el = soup.find(attrs={"data-sk-unit": f"{next_type}-{unit}"})
                if el:
                    return el
            for next_unit in range(unit + 1, unit + 10):
                el = soup.find(attrs={"data-sk-unit": f"prose-{next_unit}"})
                if el:
                    return el

        # For Social Science — try next discipline
        if lesson_type in ss_order:
            idx = ss_order.index(lesson_type)
            for next_disc in ss_order[idx + 1:]:
                el = soup.find(attrs={"data-sk-unit": f"{next_disc}-1"})
                if el:
                    return el

        return None  # Last lesson in book

    # ──────────────────────────────────────────────────────────────────────────
    # Utility helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _parse_href(self, href: str) -> tuple:
        if '#' in href:
            parts = href.split('#', 1)
            return (parts[0], parts[1] if parts[1] else None)
        return (href, None)

    def _is_geo(self, title: str) -> bool:
        return any(kw in title.lower() for kw in GEOGRAPHY_KEYWORDS)


# ──────────────────────────────────────────────────────────────────────────────
# Quick test
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python epub_preprocessor.py <epub_zip_path>")
        print("Example: python epub_preprocessor.py class-10-term0-english.zip")
        sys.exit(1)

    epub_zip = Path(sys.argv[1])
    epub_dir = EpubPreprocessor.prepare_zip(epub_zip)

    if not epub_dir:
        print("❌ Could not prepare EPUB")
        sys.exit(1)

    preprocessor = EpubPreprocessor(epub_dir)

    # Run preprocessing
    success = preprocessor.prepare(force=True)
    if not success:
        print("❌ Preprocessing failed")
        sys.exit(1)

    print("\n=== Extraction Test ===")

    # Detect subject from epub name
    epub_name = epub_zip.stem.lower()

    if 'social' in epub_name:
        tests = [
            ('history', 1), ('history', 2), ('history', 3),
            ('geography', 1), ('civics', 1), ('economics', 1),
        ]
    else:
        tests = [
            ('prose', 1), ('poem', 1), ('supplementary', 1),
            ('prose', 2), ('poem', 2), ('supplementary', 2),
        ]

    for lesson_type, unit in tests:
        text = preprocessor.extract(lesson_type, unit)
        if text:
            print(f"✅ {lesson_type}-{unit}: {len(text):6} chars — {text[:60]}...")
        else:
            print(f"❌ {lesson_type}-{unit}: FAILED")