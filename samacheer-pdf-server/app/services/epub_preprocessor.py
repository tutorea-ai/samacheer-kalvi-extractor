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

# ── Roman numeral map for unit numbers ────────────────────────────────────────
ROMAN = {
    'I':1,'II':2,'III':3,'IV':4,'V':5,
    'VI':6,'VII':7,'VIII':8,'IX':9,'X':10
}

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

        if epub_dir.exists():
            if (epub_dir / 'nav.xhtml').exists():
                print(f"[Preprocessor] Using cached EPUB: {epub_dir.name}")
                return epub_dir
            # Handle double-nested zip — some EPUBs unzip into a subfolder
            nested = epub_dir / epub_dir.name
            if nested.exists() and (nested / 'nav.xhtml').exists():
                print(f"[Preprocessor] Using cached EPUB (nested): {nested.name}")
                return nested

        if epub_zip_path.exists():
            print(f"[Preprocessor] Unzipping {epub_zip_path.name}...")
            try:
                epub_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(epub_zip_path, 'r') as z:
                    z.extractall(epub_dir)
                print(f"[Preprocessor] ✅ Unzipped to {epub_dir.name}")
                # Check for double-nesting — some EPUBs unzip into a subfolder
                nested = epub_dir / epub_dir.stem
                if nested.exists() and (
                    (nested / 'nav.xhtml').exists() or
                    (nested / 'toc.ncx').exists()
                ):
                    print(f"[Preprocessor] ✅ Detected nested folder — using: {nested.name}")
                    return nested
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

        # Strip HTML → clean text with heading markers preserved
        full_html = ''.join(content_parts)
        content_soup = BeautifulSoup(full_html, 'html.parser')

        # Mark headings BEFORE get_text() strips them
        # h1-h4 tags → clear heading markers
        for tag in content_soup.find_all(['h1', 'h2', 'h3', 'h4']):
            tag.insert_before('\n\n### ')
            tag.insert_after('\n')

        # Bold tags that are standalone (short text = subheading)
        for tag in content_soup.find_all(['b', 'strong']):
            tag_text = tag.get_text(strip=True)
            # Only mark as heading if short (under 10 words) and not inside a sentence
            if tag_text and len(tag_text.split()) <= 10:
                parent = tag.parent
                # Check if bold tag is the primary content of its parent
                parent_text = parent.get_text(strip=True) if parent else ""
                if parent_text and len(parent_text.split()) <= 12:
                    tag.insert_before('\n\n### ')
                    tag.insert_after('\n')

        text = content_soup.get_text(separator=' ', strip=True)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n +', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text).strip()

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
        # Try nav.xhtml first (EPUB 3), fall back to toc.ncx (EPUB 2)
        nav_path = self.epub_dir / 'nav.xhtml'
        ncx_path = self.epub_dir / 'toc.ncx'

        if nav_path.exists():
            with open(nav_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            nav = soup.find('nav')
            if not nav:
                return None
            top_ol = nav.find('ol', recursive=False)
            if not top_ol:
                return None
            subject_type = self._detect_subject_type(top_ol)
            print(f"[Preprocessor] Detected subject type: {subject_type}")
            if subject_type == 'english':
                return self._build_english_tag_map(top_ol)
            elif subject_type == 'socialscience':
                return self._build_ss_tag_map(top_ol)
            else:
                return self._build_linear_tag_map(top_ol)

        elif ncx_path.exists():
            print(f"[Preprocessor] nav.xhtml not found — using toc.ncx (EPUB 2)")
            return self._build_ncx_tag_map(ncx_path)

        else:
            print(f"[Preprocessor] ❌ No navigation file found (nav.xhtml or toc.ncx)")
            return None

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
            unit_num = self._parse_unit_num(unit_text)
            if not unit_num:
                continue
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
        """
        Build tag map for Social Science (Type B) nav structure.
        Handles:
          - Standard:          'Unit – 2 Title'
          - Split entries:     'Unit – 2' then 'Title' as separate <li>
          - Roman numerals:    'Unit I The universe...'
          - Discipline prefix: 'Civics Unit 1 Understanding diversity'
          - Nested units:      Unit 2 inside Unit 1's <ol>
          - Duplicate headings:'geography' + 'Geography' (same discipline, skip second)
          - Missing disciplines: Economics absent in Class 6 — silently skipped
        """
        tag_map = {}
        current_discipline = 'history'
        prev_unit_num = 0
        pending_unit_num = None
        pending_unit_href = None
        seen_disciplines = set()   # prevents double-processing duplicate headings

        def _register_unit(discipline, unit_num, href, li_el=None):
            """
            Register one unit into tag_map.
            After registering, scans nested <ol> inside li_el for
            additional units (e.g. Unit 2 nested inside Unit 1's ol).
            """
            sf, an = self._parse_href(href)
            if not an:
                return
            tag = f"{discipline}-{unit_num}"
            if tag not in tag_map:
                tag_map[tag] = (sf, an)
                print(f"   [SS] Registered {tag} → {an}")

            # Scan nested ol for hidden additional units
            if li_el:
                nested_ol = li_el.find('ol')
                if nested_ol:
                    for nli in nested_ol.find_all('li', recursive=False):
                        nl = nli.find('a')
                        if not nl:
                            continue
                        nt = nl.get_text(strip=True)
                        nh = nl.get('href', '')

                        # Skip sub-sections like 2.1, 3.2 etc.
                        if re.match(r'^\d+\.\d+', nt):
                            continue
                        # Skip known non-unit entries
                        if nt in ['Learning Objectives', 'Summary', 'Glossary',
                                  'Exercises', 'Internet Resources', 'ICT CORNER',
                                  'References', '(Untitled)']:
                            continue

                        nested_unit = self._parse_unit_num(nt)
                        if nested_unit and nested_unit != unit_num:
                            nsf, nan = self._parse_href(nh)
                            if nan:
                                nested_tag = f"{discipline}-{nested_unit}"
                                if nested_tag not in tag_map:
                                    tag_map[nested_tag] = (nsf, nan)
                                    print(f"   [SS] Registered nested {nested_tag} → {nan}")

        for li in top_ol.find_all('li', recursive=False):
            link = li.find('a')
            if not link:
                continue

            text = link.get_text(strip=True)
            href = link.get('href', '')
            text_upper = text.strip().upper()
            text_lower = text.strip().lower()

            # ── Explicit discipline headings ──────────────────────────────────────
            # Matches: 'HISTORY', 'CIVICS', 'ECONOMICS'
            # Also:    'geography', 'Geography', 'GEOGRAPHY' (any case)
            if text_lower in SS_DISCIPLINES:
                if text_lower in seen_disciplines:
                    # Duplicate heading — but still scan nested ol for units we may have missed
                    nested_ol = li.find('ol')
                    if nested_ol:
                        for nli in nested_ol.find_all('li', recursive=False):
                            nl = nli.find('a')
                            if not nl:
                                continue
                            nt = nl.get_text(strip=True)
                            nh = nl.get('href', '')
                            if nt in ['Learning Objectives', 'Summary', 'Glossary',
                                      'Exercises', 'Internet Resources', 'ICT CORNER',
                                      'References', '(Untitled)']:
                                continue
                            nested_unit = self._parse_unit_num(nt)
                            if nested_unit:
                                _register_unit(text_lower, nested_unit, nh, nli)
                    continue
                seen_disciplines.add(text_lower)
                current_discipline = text_lower
                prev_unit_num = 0
                pending_unit_num = None
                pending_unit_href = None

                # Geography heading sometimes has Unit I nested directly inside it
                nested_ol = li.find('ol')
                if nested_ol:
                    for nli in nested_ol.find_all('li', recursive=False):
                        nl = nli.find('a')
                        if not nl:
                            continue
                        nt = nl.get_text(strip=True)
                        nh = nl.get('href', '')
                        nested_unit = self._parse_unit_num(nt)
                        if nested_unit:
                            _register_unit(current_discipline, nested_unit, nh, nli)
                            prev_unit_num = nested_unit
                continue

            # ── Unit number only — e.g. 'Unit – 2' ───────────────────────────────
            text_stripped = text.strip()
            unit_num_only = re.match(r'^Unit\s*[-–]\s*(\d+)\s*$', text_stripped)
            if unit_num_only:
                pending_unit_num = int(unit_num_only.group(1))
                pending_unit_href = href
                continue

            # ── Unit with title — e.g. 'Unit 2 Land and Oceans' ──────────────────
            # Also handles: 'Civics Unit 1 Understanding diversity' (discipline prefix)
            # Also handles: 'Unit I The universe...' (Roman numeral)
            unit_num = self._parse_unit_num(text_stripped)
            if unit_num:
                # Discipline-switch detection for History→Geography
                # (unit numbers reset when discipline changes)
                if current_discipline == 'history' and 'history' in seen_disciplines:
                    if unit_num <= prev_unit_num and self._is_geo(text):
                        current_discipline = 'geography'
                        seen_disciplines.add('geography')
                        prev_unit_num = 0

                _register_unit(current_discipline, unit_num, href, li)
                prev_unit_num = unit_num
                pending_unit_num = None
                pending_unit_href = None
                continue

            # ── Title entry following a unit-number-only entry ────────────────────
            # e.g. 'Unit – 2' on one line, then 'The World Between Two World Wars' next
            if pending_unit_num is not None:
                use_href = pending_unit_href if pending_unit_href else href

                # Discipline-switch detection
                if current_discipline == 'history' and 'history' in seen_disciplines:
                    if pending_unit_num <= prev_unit_num and self._is_geo(text):
                        current_discipline = 'geography'
                        seen_disciplines.add('geography')
                        prev_unit_num = 0

                _register_unit(current_discipline, pending_unit_num, use_href, li)
                prev_unit_num = pending_unit_num
                pending_unit_num = None
                pending_unit_href = None
                continue

            # ── Nothing matched — reset pending ───────────────────────────────────
            pending_unit_num = None
            pending_unit_href = None

        return tag_map

    def _build_linear_tag_map(self, top_ol) -> dict:
        """
        Build tag map for linear subjects like Science/Maths (Type C).

        Handles 3 nav patterns found in Science EPUBs:
          Pattern 1 — Inline:  <li><a href="...#anchor">UNIT-1 LAWS OF MOTION</a></li>
          Pattern 2 — Split A: <li><a href="...#toc_id_130">UNIT-5 ACOUSTICS</a></li>
                               <li><a href="...#toc_id_131">(Untitled)</a>  ← real anchor
          Pattern 3 — Split B: <li><a href="index_split_009.html">UNIT-6</a></li>
                               <li><a href="...#toc_id_159">NUCLEAR PHYSICS</a>  ← real anchor
        """
        tag_map = {}

        SKIP_TITLES = {
            'learning objectives', 'summary', 'glossary', 'exercises',
            'textbook evaluation', 'references', 'practicals',
            'points to remember', 'solved problems',
        }

        all_li = top_ol.find_all('li', recursive=False)
        i = 0

        while i < len(all_li):
            li   = all_li[i]
            link = li.find('a')
            if not link:
                i += 1
                continue

            text = link.get_text(strip=True)
            href = link.get('href', '')

            unit_num = self._parse_unit_num(text)

            if unit_num:
                tag = f"unit-{unit_num}"

                if '#' in href:
                    # Pattern 1 — unit heading has a real anchor — use it directly
                    sf, an = self._parse_href(href)
                    # If anchor is toc_id_ style, check if next <li> has a better id_ anchor
                    if an and an.startswith('toc_id_') and i + 1 < len(all_li):
                        next_li = all_li[i + 1]
                        next_link = next_li.find('a')
                        if next_link:
                            next_href = next_link.get('href', '')
                            next_sf, next_an = self._parse_href(next_href)
                            next_is_unit = self._parse_unit_num(next_link.get_text(strip=True)) is not None
                            if not next_is_unit and next_an and next_an.startswith('id_'):
                                # Use the better id_ anchor and consume next <li>
                                sf, an = next_sf, next_an
                                i += 1
                    if sf and an and tag not in tag_map:
                        tag_map[tag] = (sf, an)
                        print(f"   [Linear] Registered {tag} → {an} (inline)")

                else:
                    # Pattern 2 / 3 — no anchor on unit <li>
                    # Real content anchor is on the NEXT sibling <li>
                    # BUT only if the next <li> is NOT itself a unit heading
                    if i + 1 < len(all_li):
                        next_li   = all_li[i + 1]
                        next_link = next_li.find('a')
                        if next_link:
                            next_href = next_link.get('href', '')
                            next_text = next_link.get_text(strip=True)
                            next_is_unit = self._parse_unit_num(next_text) is not None

                            if next_is_unit:
                                # Next <li> is another unit heading — use _find_first_element_in_file
                                # to locate the first real element in the split file
                                split_file = href.split('#')[0] if href else None
                                if split_file:
                                    sf = split_file
                                    an = split_file  # sentinel — _stamp_tags will use _find_first_element_in_file
                                    if tag not in tag_map:
                                        tag_map[tag] = (sf, an)
                                        print(f"   [Linear] Registered {tag} → {sf} (file-sentinel)")
                                # do NOT consume next <li>

                            elif next_text.lower() not in SKIP_TITLES and '#' in next_href:
                                # Next <li> is content — but only use its anchor if it's
                                # in the SAME split file as the unit heading
                                # If different file → use file sentinel instead
                                unit_file = href.split('#')[0] if href else None
                                next_file = next_href.split('#')[0] if next_href else None

                                if unit_file and next_file and unit_file != next_file:
                                    # Different file — next sibling belongs to next unit
                                    # Use file sentinel for this unit
                                    if unit_file and tag not in tag_map:
                                        tag_map[tag] = (unit_file, unit_file)
                                        print(f"   [Linear] Registered {tag} → {unit_file} (file-sentinel, diff-file)")
                                    # do NOT consume next <li>
                                else:
                                    # Same file — safe to use next sibling's anchor
                                    sf, an = self._parse_href(next_href)
                                    if sf and an and tag not in tag_map:
                                        tag_map[tag] = (sf, an)
                                        print(f"   [Linear] Registered {tag} → {an} (split→next)")
                                    i += 1  # consume the next <li>

                            else:
                                # Next sibling is in SKIP_TITLES or has no anchor
                                # Fall back to file sentinel for current unit
                                unit_file = href.split('#')[0] if href else None
                                if unit_file and tag not in tag_map:
                                    tag_map[tag] = (unit_file, unit_file)
                                    print(f"   [Linear] Registered {tag} → {unit_file} (file-sentinel, skip-fallback)")

                    else:
                        # No next sibling at all — last unit in book
                        # Use file sentinel directly
                        unit_file = href.split('#')[0] if href else None
                        if unit_file and tag not in tag_map:
                            tag_map[tag] = (unit_file, unit_file)
                            print(f"   [Linear] Registered {tag} → {unit_file} (file-sentinel, last-unit)")

            i += 1

        # ── Gap filler: assign title-only entries to missing unit numbers ─────────
        # Some EPUBs have title-only <li> entries with no "Unit N" prefix
        # We collect all anchored <li> that weren't consumed as unit headings,
        # then fill gaps in unit sequence order
        if tag_map:
            max_unit = max(int(t.split('-')[1]) for t in tag_map)
            missing_units = [u for u in range(1, max_unit + 3) if f"unit-{u}" not in tag_map]

            # Collect unused anchored li entries (not unit headings, not skip titles)
            # Prefer entries with readable id_ anchors over toc_id_ style
            unused_entries = []
            for li in all_li:
                link = li.find('a')
                if not link:
                    continue
                text = link.get_text(strip=True)
                href = link.get('href', '')
                if self._parse_unit_num(text):
                    continue  # already processed as unit heading
                if text.lower() in SKIP_TITLES:
                    continue
                if '#' not in href:
                    continue
                sf, an = self._parse_href(href)
                already_used = any(an == v[1] for v in tag_map.values())
                if not already_used and an:
                    # Prefer readable id_ anchors — skip toc_id_ and ALL-CAPS duplicates
                    if an.startswith('toc_id_'):
                        continue
                    if text.isupper():
                        continue
                    # Skip if anchor is semantically duplicate of an already-registered unit
                    # e.g. 'Universe and Space' when unit-2 anchor is toc_id_20 on same file
                    # Detection: check if any registered unit is on the same split file
                    # AND this entry's position in nav is right after that unit
                    registered_anchors = {v[1] for v in tag_map.values()}
                    # Skip entries whose title words heavily overlap with already-registered unit titles
                    text_words = set(text.lower().split())
                    already_covered = False
                    for reg_tag, (reg_sf, reg_an) in tag_map.items():
                        if reg_sf == sf:
                            # Same file — check if this looks like a subtitle/duplicate
                            reg_words = set(reg_an.lower().replace('_', ' ').split())
                            overlap = text_words & reg_words - {'and', 'the', 'of', 'in', 'a'}
                            if overlap and len(overlap) >= 2:
                                already_covered = True
                                break
                    if already_covered:
                        continue
                    unused_entries.append((text, sf, an))

            # Assign unused entries to missing units in order
            for unit_num, (title, sf, an) in zip(missing_units, unused_entries):
                tag = f"unit-{unit_num}"
                if tag not in tag_map:
                    tag_map[tag] = (sf, an)
                    print(f"   [Linear] Registered {tag} → {an} (title-fallback: {title!r})")

        return tag_map

    def _build_ncx_tag_map(self, ncx_path: Path) -> dict:
        """
        Build tag map from toc.ncx (EPUB 2 format).
        Used when nav.xhtml is not present.

        NCX structure:
          <navMap>
            <navPoint>
              <navLabel><text>UNIT 1 MEASUREMENT</text></navLabel>
              <content src="index_split_000.html#id_UNIT_1_MEASUREMENT"/>
            </navPoint>
          </navMap>

        Handles:
          - Units with anchor:      index_split_000.html#id_UNIT_1
          - Units without anchor:   index_split_002.html  (file sentinel)
        """
        from bs4 import XMLParsedAsHTMLWarning
        import warnings
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

        tag_map = {}

        with open(ncx_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

        # html.parser lowercases all tags
        nav_map = soup.find('navmap')
        if not nav_map:
            nav_map = soup.find('navMap')  # fallback for xml parser
        if not nav_map:
            print(f"[Preprocessor] ❌ No navMap found in toc.ncx")
            return {}

        # Find top-level navpoints (html.parser lowercases)
        top_nav_points = nav_map.find_all('navpoint', recursive=False)

        SKIP_LABELS = {
            'table of contents', 'learning objectives', 'summary',
            'glossary', 'exercises', 'textbook evaluation', 'references',
            'practicals', 'points to remember', 'solved problems',
            '(untitled)', 'introduction', 'do you know', 'more to know'
        }

        SS_DISCIPLINES = {'history', 'geography', 'civics', 'economics'}

        def process_navpoint(nav_point, discipline=None):
            label   = nav_point.find('navlabel', recursive=False)
            content = nav_point.find('content', recursive=False)
            if not label:
                return
            text = label.find('text')
            if not text:
                return
            text_str = text.get_text(strip=True)

            # Check if this is a discipline heading
            if text_str.lower() in SS_DISCIPLINES:
                # Process all children with this discipline
                child_navpoints = nav_point.find_all('navpoint', recursive=False)
                for child in child_navpoints:
                    process_navpoint(child, discipline=text_str.lower())
                return

            # Skip non-unit entries
            if text_str.lower() in SKIP_LABELS:
                return

            # Parse unit number
            unit_num = self._parse_unit_num(text_str)
            if not unit_num:
                return

            if not content:
                return
            src = content.get('src', '')
            sf, an = self._parse_href(src)
            if not sf:
                return

            # Build tag — use discipline prefix if available
            if discipline:
                tag = f"{discipline}-{unit_num}"
            else:
                tag = f"unit-{unit_num}"

            if tag not in tag_map:
                if not an or an == sf:
                    tag_map[tag] = (sf, sf)
                    print(f"   [NCX] Registered {tag} → {sf} (file-sentinel)")
                else:
                    tag_map[tag] = (sf, an)
                    print(f"   [NCX] Registered {tag} → {an} (anchor)")

        for nav_point in top_nav_points:
            process_navpoint(nav_point)

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
            # Fallback — single index.html (some EPUBs don't split)
            index_file = self.epub_dir / 'index.html'
            if index_file.exists():
                print(f"[Preprocessor] No split files — using single index.html")
                split_files = [index_file]
            else:
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
            # Try finding by id first
            el = soup.find(id=anchor)

            # Fallback: anchor is a filename sentinel — locate first element in that split file
            if not el and anchor and anchor.endswith('.html'):
                el = self._find_first_element_in_file(soup, anchor)

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
        # No anchor — use filename as fallback sentinel so _stamp_tags can locate
        # the first element in that split file
        if href:
            return (href, href)
        return (href, None)

    def _find_first_element_in_file(self, soup, split_file: str):
        """
        Find the first element in the combined soup that originates from the
        given split file. Used when a nav href has no #anchor fragment.
        """
        split_path = self.epub_dir / split_file
        if not split_path.exists():
            return None
        with open(split_path, 'r', encoding='utf-8') as f:
            file_soup = BeautifulSoup(f.read(), 'html.parser')
        body = file_soup.find('body')
        if not body:
            return None
        # Prefer first element that carries an id — match it in combined soup
        first_el = body.find(id=True)
        if first_el:
            return soup.find(id=first_el.get('id'))
        # Fall back to matching by text of first heading/paragraph
        first_block = body.find(['h1', 'h2', 'h3', 'h4', 'p'])
        if first_block:
            text = first_block.get_text(strip=True)[:30]
            for el in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p']):
                if el.get_text(strip=True)[:30] == text:
                    return el
        return None

    def _is_geo(self, title: str) -> bool:
        return any(kw in title.lower() for kw in GEOGRAPHY_KEYWORDS)

    def _parse_unit_num(self, text: str) -> int | None:
        """
        Parse unit number from text — handles both Arabic and Roman numerals.
        Examples:
            'Unit 1 History'         → 1
            'Unit – 2'               → 2
            'Unit I The universe'    → 1
            'Civics Unit 1 ...'      → 1
            'UNIT 2 Achieving ...'   → 2
        """
        # Arabic numerals first
        m = re.search(r'(?i)unit\s*[-–\s]*(\d+)', text)
        if m:
            return int(m.group(1))
        # Roman numerals — must be followed by space or end of string to avoid false matches
        m = re.search(r'(?i)unit\s*[-–\s]*([IVX]+)(?:\s|$)', text)
        if m and m.group(1).upper() in ROMAN:
            return ROMAN[m.group(1).upper()]
        return None


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