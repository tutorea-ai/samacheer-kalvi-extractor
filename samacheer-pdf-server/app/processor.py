"""
Core PDF Processing Engine
Handles the full pipeline:
  Download → Extract Text (EPUB or pdfplumber) → AI Generate (Content + QA + LP) → Deploy via Bridge

UPDATES (April 2026 — v6.0 EPUB):
  - EPUB extractor replaces pdf2htmlEX entirely
  - EPUB text feeds Content + QA + LP (all three via Claude)
  - pdfplumber kept as fallback when EPUB not available
  - epub_catalog.json added for EPUB Drive IDs
  - storage/epub/ folder added for EPUB zip cache
"""
from .extractors.google_docai import docai_extractor
import requests
import os
import json
import PyPDF2
import gdown
import shutil
from pathlib import Path
from typing import Dict, Optional
from .services.ai_converter import ai_converter
from .services.bridge import bridge
from .services.epub_extractor import EpubExtractor
from .services.ss_epub_extractor import SocialScienceEpubExtractor
from .config import settings


class PDFProcessor:
    """Core processing engine with EPUB + PDF fallback support."""

    def __init__(self):
        self.catalogs_cache = {}
        self.base_path  = settings.BASE_DIR
        self.cache_dir  = settings.CACHE_DIR
        self.temp_dir   = settings.TEMP_DIR
        self.epub_dir   = settings.BASE_DIR / "storage" / "epub"
        self.epub_dir.mkdir(parents=True, exist_ok=True)
        print("🚀 PDF Processor initialized")

    # ──────────────────────────────────────────────────────────────────────────
    # Catalog & Index Loading
    # ──────────────────────────────────────────────────────────────────────────

    def _load_catalog(self, subject: str, medium: str = "english") -> dict:
        """Dynamic catalog loading with in-memory cache."""
        cache_key = f"{subject}_{medium}"
        if cache_key in self.catalogs_cache:
            return self.catalogs_cache[cache_key]

        catalog_path = settings.get_catalog_path(subject, medium)

        if not catalog_path.exists():
            print(f"❌ Catalog not found: {catalog_path}")
            if subject == "english" and medium == "english":
                try:
                    response = requests.get(settings.CATALOG_URL, timeout=10)
                    if response.status_code == 200:
                        return response.json()
                except:
                    pass
            return {}

        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog_data = json.load(f)
            self.catalogs_cache[cache_key] = catalog_data
            return catalog_data
        except Exception as e:
            print(f"❌ Error loading catalog: {e}")
            return {}

    def _load_epub_catalog(self) -> dict:
        """Load the EPUB catalog (Drive IDs for EPUB zips)."""
        epub_catalog_path = settings.BASE_DIR / "data" / "catalogs" / "epub_catalog.json"
        if not epub_catalog_path.exists():
            return {}
        try:
            with open(epub_catalog_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading EPUB catalog: {e}")
            return {}

    def _load_unit_index(self, class_num: int, subject: str, medium: str = "english") -> dict:
        """Dynamic index loading."""
        index_path = settings.get_index_path(subject, class_num, medium)
        if not index_path.exists():
            return {}
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    # ──────────────────────────────────────────────────────────────────────────
    # PDF Utilities
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_book_key(self, class_num: int, term: int, subject: str, medium: str) -> str:
        subject = subject.lower().strip()
        medium  = medium.lower().strip()
        if class_num >= 8:
            term = 0
        suffix = "" if subject in ["english", "tamil"] else f"-{medium}-medium"
        return f"class-{class_num}-term{term}-{subject}{suffix}.pdf"

    def _generate_epub_key(self, class_num: int, term: int, subject: str) -> str:
        """Generate the key used in epub_catalog.json."""
        if class_num >= 8:
            term = 0
        return f"class-{class_num}-term{term}-{subject}"

    def _download_file(self, file_id: str, output_path: Path) -> bool:
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, str(output_path), quiet=False, fuzzy=True)
            return output_path.exists()
        except:
            return False

    def _slice_pdf(self, source_pdf: Path, output_pdf: Path, start_page: int, end_page: int) -> bool:
        try:
            with open(source_pdf, "rb") as infile:
                reader = PyPDF2.PdfReader(infile)
                writer = PyPDF2.PdfWriter()
                if end_page > len(reader.pages):
                    return False
                for i in range(start_page - 1, end_page):
                    writer.add_page(reader.pages[i])
                with open(output_pdf, "wb") as outfile:
                    writer.write(outfile)
            return True
        except:
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # EPUB Text Extraction
    # Primary source for Classes 8-12 English
    # ──────────────────────────────────────────────────────────────────────────

    def _get_epub_text(
        self,
        class_num: int,
        term: int,
        subject: str,
        unit_num: int,
        lesson_type: str = None,
        discipline: str = None,
    ) -> str | None:
        # Units where EPUB extraction is known to be unreliable
        # Format: (class_num, subject, discipline, unit_num)
        EPUB_EXCLUSIONS = [
            (10, "socialscience", "history", 2),  # bleeds into Unit 3
            (10, "socialscience", "history", 3),  # missing from nav
        ]

        if (class_num, subject.lower(), discipline, unit_num) in EPUB_EXCLUSIONS:
            print(f"   ⏭️  EPUB excluded for Class {class_num} {discipline} Unit {unit_num} — using pdfplumber")
            return None

        epub_key = self._generate_epub_key(class_num, term, subject)
        epub_zip_path = self.epub_dir / f"{epub_key}.zip"
        epub_folder   = self.epub_dir / epub_key

        # Download zip if not cached
        if not epub_zip_path.exists() and not epub_folder.exists():
            epub_catalog = self._load_epub_catalog()
            drive_id = epub_catalog.get(epub_key)
            if not drive_id or drive_id == "LOCAL":
                print(f"   ℹ️  No EPUB available for {epub_key}")
                return None
            print(f"   ⬇️  Downloading EPUB: {epub_key}.zip")
            if not self._download_file(drive_id, epub_zip_path):
                print(f"   ❌ EPUB download failed")
                return None

        # ── Social Science ─────────────────────────────────────────────
        if subject.lower() in ["socialscience", "social_science", "social science"]:
            if not epub_folder.exists():
                epub_folder = SocialScienceEpubExtractor.prepare(epub_zip_path)
                if not epub_folder:
                    return None
            extractor = SocialScienceEpubExtractor(epub_folder)
            text = extractor.extract(
                discipline=discipline or "history",
                unit=unit_num
            )

        # ── Science ────────────────────────────────────────────────────
        elif subject.lower() == "science":
            from .services.science_epub_extractor import ScienceEpubExtractor
            if not epub_folder.exists():
                epub_folder = ScienceEpubExtractor.prepare(epub_zip_path)
                if not epub_folder:
                    return None
            extractor = ScienceEpubExtractor(epub_folder)
            text = extractor.extract(unit=unit_num)

        # ── English (and other language subjects) ──────────────────────
        else:
            if not epub_folder.exists():
                epub_folder = EpubExtractor.prepare(epub_zip_path)
                if not epub_folder:
                    return None
            extractor = EpubExtractor(epub_folder)
            text = extractor.extract(
                unit=unit_num,
                lesson_type=lesson_type or "prose"
            )

        if text:
            print(f"   ✅ EPUB extraction done → {len(text)} chars")
        else:
            print(f"   ⚠️  EPUB extraction returned nothing — will fallback")

        return text

    # ──────────────────────────────────────────────────────────────────────────
    # Text Extraction — EPUB first, pdfplumber fallback
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_text(
        self,
        pdf_file: Path,
        start_page: int,
        end_page: int,
        output_txt: Path,
        class_num: int = None,
        term: int = None,
        subject: str = None,
        unit_num: int = None,
        lesson_type: str = None,
        discipline: str = None,
    ) -> bool:
        """
        Extract lesson text. EPUB is primary, pdfplumber is fallback.

        When EPUB params are provided, tries EPUB first.
        Always falls back to pdfplumber if EPUB fails or is unavailable.
        """
        # ── Primary: EPUB ─────────────────────────────────────────────────────
        if all([class_num, subject, unit_num]):
            print(f"   🔄 Trying EPUB extraction...")
            epub_text = self._get_epub_text(
                class_num, term or 0, subject, unit_num, lesson_type, discipline
            )
            if epub_text:
                with open(output_txt, "w", encoding="utf-8") as f:
                    f.write(epub_text)
                return True

        # ── Fallback: pdfplumber ──────────────────────────────────────────────
        print(f"   🔄 Falling back to pdfplumber...")
        success = self._extract_text_pdfplumber(pdf_file, start_page, end_page, output_txt)
        if success:
            return True

        # ── Last resort: Google Document AI ──────────────────────────────────
        if docai_extractor.is_available():
            print(f"   🔄 pdfplumber failed — trying Document AI...")
            success = docai_extractor.extract(pdf_file, start_page, end_page, output_txt)
            if success:
                return True

        print(f"   ❌ All text extraction methods failed")
        return False

    def _extract_text_pdfplumber(
        self,
        pdf_file: Path,
        start_page: int,
        end_page: int,
        output_txt: Path
    ) -> bool:
        """Text extraction using pdfplumber."""
        try:
            import pdfplumber
            import re
            print(f"   🔄 Extracting text via pdfplumber...")
            text_content = ""
            with pdfplumber.open(pdf_file) as pdf:
                if end_page > len(pdf.pages):
                    end_page = len(pdf.pages)
                for page_num in range(start_page - 1, end_page):
                    page = pdf.pages[page_num]
                    text = page.extract_text() or ""
                    if text:
                        text_content += text + "\n\n"
            # Clean noise
            text_content = re.sub(r'\[[A-Za-z0-9]{4,12}\]', '', text_content)
            text_content = re.sub(r'\d+th\s+\w+_Unit_\d+\.indd[^\n]*', '', text_content)
            text_content = re.sub(r'^\d{1,3}\s*$', '', text_content, flags=re.MULTILINE)
            text_content = re.sub(r'\n{3,}', '\n\n', text_content).strip()
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(text_content)
            print(f"   ✅ pdfplumber done → {len(text_content)} chars")
            return True
        except Exception as e:
            print(f"   ❌ pdfplumber failed: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Lesson Page Calculation
    # ──────────────────────────────────────────────────────────────────────────

    def _get_lesson_details(self, index_data: dict, unit_num: int, lesson_choice: int, class_num: int, discipline: str = None):
        """
        Calculates start/end PDF page numbers for a lesson.
        Handles both English (units list) and Social Science (disciplines dict).
        """
        meta = index_data.get("meta", {"prelim_pages": 0, "total_pdf_pages": 999})
        offset = meta["prelim_pages"]

        target_units = []
        all_units_for_slicing = []

        # Check for disciplines — either wrapped {"disciplines": {...}} or flat {discipline: [...]}
        flat_disciplines = all(
            k in ["physics", "chemistry", "biology", "computer_science",
                  "history", "geography", "civics", "economics"]
            for k in index_data.keys() if k != "meta"
        )

        if "disciplines" in index_data or flat_disciplines:
            if not discipline:
                print("❌ 'discipline' parameter is required for this subject.")
                return None
            disc_key = discipline.lower()

            # Handle both structures
            disc_data = index_data.get("disciplines", index_data)
            if disc_key not in disc_data:
                print(f"❌ Discipline '{disc_key}' not found.")
                return None
            target_units = disc_data[disc_key]
            for d_list in disc_data.values():
                if isinstance(d_list, list):
                    all_units_for_slicing.extend(d_list)
        else:
            target_units = index_data.get("units", [])
            all_units_for_slicing = target_units

        if not target_units:
            return None

        # Find by unit number — supports global numbering
        # (e.g. Chemistry starts at unit 7, not unit 1)
        selected_unit_obj = next(
            (u for u in target_units if u.get("unit") == unit_num),
            None
        )
        if not selected_unit_obj:
            print(f"❌ Unit {unit_num} not found in {discipline}")
            return None

        if "page" in selected_unit_obj:
            start_pdf_page = selected_unit_obj["page"] + offset
            clean_title = selected_unit_obj["title"].replace(" ", "")
            filename = f"Class{class_num}-{discipline or 'Unit'}-{unit_num}-{clean_title}"
            selected_page_raw = selected_unit_obj["page"]
        else:
            lessons = []
            for cat in ["prose", "poem", "supplementary", "play"]:
                if cat in selected_unit_obj:
                    lessons.append({
                        "type": cat,
                        "title": selected_unit_obj[cat]["title"],
                        "page": selected_unit_obj[cat]["page"]
                    })
            if lesson_choice > len(lessons):
                return None
            selected_lesson = lessons[lesson_choice - 1]
            start_pdf_page = selected_lesson["page"] + offset
            clean_title = selected_lesson["title"].replace(" ", "")
            filename = f"Class{class_num}-Unit{unit_num}-{selected_lesson['type'].capitalize()}-{clean_title}"
            selected_page_raw = selected_lesson["page"]

        all_start_pages = []
        for u in all_units_for_slicing:
            if "page" in u:
                all_start_pages.append(u["page"])
            else:
                for cat in ["prose", "poem", "supplementary", "play"]:
                    if cat in u:
                        all_start_pages.append(u[cat]["page"])

        all_start_pages.sort()
        next_pages = [p for p in all_start_pages if p > selected_page_raw]

        if next_pages:
            end_pdf_page = next_pages[0] + offset - 1
        else:
            end_pdf_page = meta["total_pdf_pages"]

        return filename, start_pdf_page, end_pdf_page

    # ──────────────────────────────────────────────────────────────────────────
    # Master Request Handler
    # ──────────────────────────────────────────────────────────────────────────

    def process_request(self, request_data: dict) -> dict:
        try:
            # 1. Extract parameters
            class_num     = request_data["class_num"]
            subject       = request_data["subject"]
            term          = request_data.get("term", 0)
            medium        = request_data.get("medium", "english")
            mode          = request_data["mode"]
            output_format = request_data["output_format"]
            discipline    = request_data.get("discipline")
            force         = request_data.get("force", False)

            print(f"\n📚 Processing: Class {class_num} | {subject} | {discipline or 'General'} | Format: {output_format} | Force: {force}")

            # 2. Load catalog
            catalog = self._load_catalog(subject, medium)
            if not catalog:
                return {"error": True, "message": "Catalog not found"}

            # 3. Get Drive ID
            book_key = self._generate_book_key(class_num, term, subject, medium)
            if book_key not in catalog:
                return {"error": True, "message": f"Book not found in catalog: {book_key}"}

            drive_id = catalog[book_key]

            # 4. Download PDF / use cache
            cached_file = self.cache_dir / book_key
            if not cached_file.exists():
                print(f"⬇️  Downloading PDF: {book_key}")
                if not self._download_file(drive_id, cached_file):
                    return {"error": True, "message": "Download failed"}

            # ── FULL BOOK MODE ────────────────────────────────────────────────
            if mode == "full_book":
                if output_format == "pdf":
                    output_file = self.temp_dir / book_key
                    shutil.copy(cached_file, output_file)
                    return {"error": False, "filename": output_file.name, "file_path": str(output_file)}

                elif output_format == "txt":
                    output_file = self.temp_dir / book_key.replace(".pdf", ".txt")
                    with open(cached_file, "rb") as f:
                        total = len(PyPDF2.PdfReader(f).pages)
                    self._extract_text(cached_file, 1, total, output_file)
                    return {"error": False, "filename": output_file.name, "file_path": str(output_file)}

                else:
                    return {"error": True, "message": "Full book mode only supports PDF or TXT format"}

            # ── LESSON MODE ───────────────────────────────────────────────────
            unit_num      = request_data["unit"]
            lesson_choice = request_data.get("lesson_choice", 1)

            # 5. Load index
            index_data = self._load_unit_index(class_num, subject, medium)
            if not index_data:
                return {"error": True, "message": "Index not found"}

            term_key = f"term{term}" if class_num in [6, 7] else "term0"
            if term_key not in index_data:
                return {"error": True, "message": f"Term key '{term_key}' not found in index"}

            # 6. Get lesson page range (still needed for PDF fallback)
            details = self._get_lesson_details(
                index_data[term_key], unit_num, lesson_choice, class_num, discipline
            )
            if not details:
                return {"error": True, "message": "Invalid lesson selection"}

            filename_base, start_page, end_page = details
            lesson_type = self._get_lesson_type(index_data[term_key], unit_num, lesson_choice, subject=subject)
            print(f"📄 Pages: {start_page} → {end_page} | Type: {lesson_type}")

            # ── PDF output ────────────────────────────────────────────────────
            if output_format == "pdf":
                output_file = self.temp_dir / f"{filename_base}.pdf"
                self._slice_pdf(cached_file, output_file, start_page, end_page)
                return {"error": False, "filename": output_file.name, "file_path": str(output_file)}

            # ── TXT output ────────────────────────────────────────────────────
            elif output_format == "txt":
                output_file = self.temp_dir / f"{filename_base}.txt"
                self._extract_text(
                    cached_file, start_page, end_page, output_file,
                    class_num=class_num, term=term, subject=subject,
                    unit_num=unit_num, lesson_type=lesson_type,
                    discipline=discipline
                )
                return {"error": False, "filename": output_file.name, "file_path": str(output_file)}

            # ── CONTENT ONLY output ───────────────────────────────────────────
            elif output_format == "content_only":

                bridge_meta = {
                    "class_num":     class_num,
                    "term":          term,
                    "unit":          unit_num,
                    "lesson_choice": lesson_choice,
                    "subject":       subject,
                    "medium":        medium,
                    "discipline":    discipline,
                }

                print(f"🤖 Starting Content-only generation...")

                # Extract text — EPUB first, pdfplumber fallback
                temp_txt = self.temp_dir / f"{filename_base}_raw.txt"
                if not self._extract_text(
                    cached_file, start_page, end_page, temp_txt,
                    class_num=class_num, term=term, subject=subject,
                    unit_num=unit_num, lesson_type=lesson_type,
                    discipline=discipline
                ):
                    return {"error": True, "message": "Text extraction failed"}

                with open(temp_txt, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                temp_txt.unlink(missing_ok=True)

                if not raw_text.strip():
                    return {"error": True, "message": "No text extracted"}

                ai_metadata = {
                    "class":        class_num,
                    "subject":      subject,
                    "unit":         unit_num,
                    "lesson_title": filename_base,
                    "lesson_type":  lesson_type,
                    "term":         term_key,
                    "discipline":   discipline,
                }

                # Generate content only via assembler
                from .services.section_detector import detect_sections, clean_noise
                from .content_builder.assembler import content_assembler
                from .services.ai_converter import _wrap_html

                clean_text = clean_noise(raw_text, subject=subject)
                if subject.lower() not in ["socialscience", "social_science"]:
                    sections = detect_sections(clean_text, lesson_type=lesson_type)
                else:
                    sections = {}
                ai_metadata["_sections"] = sections

                content_html = content_assembler.assemble(clean_text, sections, ai_metadata)
                if not content_html:
                    return {"error": True, "message": "Content generation failed"}

                if subject.lower() in ["socialscience", "social_science"] and discipline:
                    meta_line = f"Class {class_num} | Social Science — {discipline.title()} | Unit {unit_num}"
                elif subject.lower() == "science" and discipline:
                    meta_line = f"Class {class_num} | Science — {discipline.title()} | Unit {unit_num}"
                else:
                    type_display_map = {"prose": "Prose", "poem": "Poem", "supplementary": "Supplementary Reader"}
                    type_display = type_display_map.get(lesson_type, "Prose")
                    meta_line = f"Class {class_num} | English | Unit {unit_num} | {type_display}"

                wrapped = _wrap_html(
                    content_html,
                    title=f"{filename_base} | Class {class_num}",
                    content_type="content",
                    meta_line=meta_line
                )

                content_html_file = self.temp_dir / f"{filename_base}.html"
                with open(content_html_file, "w", encoding="utf-8") as f:
                    f.write(wrapped)

                content_md_file = self.temp_dir / f"{filename_base}.md"
                with open(content_md_file, "w", encoding="utf-8") as f:
                    f.write(f"# {filename_base}\n\n{raw_text}")

                bridge.deploy_content(content_html_file, bridge_meta, "html", "content")
                bridge.deploy_content(content_md_file,   bridge_meta, "md",   "content")
                print(f"✅ Content deployed")

                return {
                    "error":    False,
                    "filename": f"{filename_base}.html",
                    "file_path": str(content_html_file),
                    "deployed": ["content"],
                    "message":  "Content only generated and deployed"
                }

            # ── LP ONLY output ────────────────────────────────────────────────
            elif output_format == "lp_only":

                bridge_meta = {
                    "class_num":     class_num,
                    "term":          term,
                    "unit":          unit_num,
                    "lesson_choice": lesson_choice,
                    "subject":       subject,
                    "medium":        medium,
                    "discipline":    discipline,
                }

                print(f"🤖 Starting LP-only generation...")

                # Extract text — EPUB first, pdfplumber fallback
                temp_txt = self.temp_dir / f"{filename_base}_raw.txt"
                if not self._extract_text(
                    cached_file, start_page, end_page, temp_txt,
                    class_num=class_num, term=term, subject=subject,
                    unit_num=unit_num, lesson_type=lesson_type,
                    discipline=discipline
                ):
                    return {"error": True, "message": "Text extraction failed"}

                with open(temp_txt, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                temp_txt.unlink(missing_ok=True)

                if not raw_text.strip():
                    return {"error": True, "message": "No text extracted"}

                ai_metadata = {
                    "class":        class_num,
                    "subject":      subject,
                    "unit":         unit_num,
                    "lesson_title": filename_base,
                    "lesson_type":  lesson_type,
                    "term":         term_key,
                    "discipline":   discipline,
                }

                # Generate LP only
                from .services.section_detector import detect_sections, clean_noise
                from .services.ai_converter import _wrap_html

                clean_text = clean_noise(raw_text, subject=subject)
                sections   = detect_sections(clean_text, lesson_type=lesson_type)
                ai_metadata["_sections"] = sections

                if subject.lower() in ["socialscience", "social_science", "science"]:
                    from .content_builder.master_router import generate_lp
                    lp_html = generate_lp(clean_text, ai_metadata)
                else:
                    lp_html = ai_converter._generate_lp(clean_text, ai_metadata)
                if not lp_html:
                    return {"error": True, "message": "LP generation failed"}

                if subject.lower() in ["socialscience", "social_science"] and discipline:
                    meta_line = f"Class {class_num} | Social Science — {discipline.title()} | Unit {unit_num}"
                elif subject.lower() == "science" and discipline:
                    meta_line = f"Class {class_num} | Science — {discipline.title()} | Unit {unit_num}"
                else:
                    type_display_map = {"prose": "Prose", "poem": "Poem", "supplementary": "Supplementary Reader"}
                    type_display = type_display_map.get(lesson_type, "Prose")
                    meta_line = f"Class {class_num} | English | Unit {unit_num} | {type_display}"

                wrapped = _wrap_html(
                    lp_html,
                    title=f"Lesson Plan — {filename_base} | Class {class_num}",
                    content_type="lp",
                    meta_line=meta_line
                )

                lp_html_file = self.temp_dir / f"{filename_base}_lp.html"
                with open(lp_html_file, "w", encoding="utf-8") as f:
                    f.write(wrapped)

                bridge.deploy_content(lp_html_file, bridge_meta, "html", "lp")
                print(f"✅ LP deployed")

                return {
                    "error":    False,
                    "filename": f"{filename_base}_lp.html",
                    "file_path": str(lp_html_file),
                    "deployed": ["lp"],
                    "message":  "LP only generated and deployed"
                }

            # ── QA ONLY output ────────────────────────────────────────────────
            elif output_format == "qa_only":

                bridge_meta = {
                    "class_num":     class_num,
                    "term":          term,
                    "unit":          unit_num,
                    "lesson_choice": lesson_choice,
                    "subject":       subject,
                    "medium":        medium,
                    "discipline":    discipline,
                }

                print(f"🤖 Starting QA-only generation...")

                # Extract text
                temp_txt = self.temp_dir / f"{filename_base}_raw.txt"
                if not self._extract_text(
                    cached_file, start_page, end_page, temp_txt,
                    class_num=class_num, term=term, subject=subject,
                    unit_num=unit_num, lesson_type=lesson_type,
                    discipline=discipline
                ):
                    return {"error": True, "message": "Text extraction failed"}

                with open(temp_txt, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                temp_txt.unlink(missing_ok=True)

                if not raw_text.strip():
                    return {"error": True, "message": "No text extracted"}

                ai_metadata = {
                    "class":        class_num,
                    "subject":      subject,
                    "unit":         unit_num,
                    "lesson_title": filename_base,
                    "lesson_type":  lesson_type,
                    "term":         term_key,
                    "discipline":   discipline,
                }

                if subject.lower() in ["socialscience", "social_science"] and discipline:
                    meta_line = f"Class {class_num} | Social Science — {discipline.title()} | Unit {unit_num}"
                elif subject.lower() == "science" and discipline:
                    meta_line = f"Class {class_num} | Science — {discipline.title()} | Unit {unit_num}"
                else:
                    type_display_map = {"prose": "Prose", "poem": "Poem", "supplementary": "Supplementary Reader"}
                    meta_line = f"Class {class_num} | English | Unit {unit_num} | {type_display_map.get(lesson_type, 'Prose')}"

                from .services.ai_converter import _wrap_html

                if subject.lower() in ["socialscience", "social_science", "science"]:
                    from .content_builder.master_router import generate_qa
                    qa_html = generate_qa(raw_text, ai_metadata)
                else:
                    from .content_builder.qa_builder import qa_builder
                    qa_html = qa_builder.generate(raw_text, ai_metadata)

                if not qa_html:
                    return {"error": True, "message": "QA generation failed"}

                wrapped = _wrap_html(
                    qa_html,
                    title=f"Q&A — {filename_base} | Class {class_num}",
                    content_type="qa",
                    meta_line=meta_line
                )

                qa_html_file = self.temp_dir / f"{filename_base}_qa.html"
                with open(qa_html_file, "w", encoding="utf-8") as f:
                    f.write(wrapped)

                bridge.deploy_content(qa_html_file, bridge_meta, "html", "qa")
                print(f"✅ QA deployed")

                return {
                    "error":    False,
                    "filename": f"{filename_base}_qa.html",
                    "deployed": ["qa"],
                    "message":  "QA only generated and deployed"
                }

            # ── AI OUTPUT: html (Content + QA + LP) ──────────────────────────
            elif output_format == "html":

                bridge_meta = {
                    "class_num":      class_num,
                    "term":           term,
                    "unit":           unit_num,
                    "lesson_choice":  lesson_choice,
                    "subject":        subject,
                    "medium":         medium,
                    "discipline":     discipline,
                }

                if not force and bridge.is_already_deployed(bridge_meta):
                    return {
                        "error":    False,
                        "filename": f"{filename_base}.html",
                        "file_path": str(self.temp_dir / f"{filename_base}.html"),
                        "deployed": ["content", "qa", "lp"],
                        "skipped":  True,
                        "message":  "Already deployed — skipped"
                    }

                if force:
                    print(f"🔄 Force mode ON — regenerating even if already deployed")

                print(f"🤖 Starting AI generation pipeline...")

                # ── Extract text — EPUB first, pdfplumber fallback ────────────
                temp_txt = self.temp_dir / f"{filename_base}_raw.txt"
                if not self._extract_text(
                    cached_file, start_page, end_page, temp_txt,
                    class_num=class_num, term=term, subject=subject,
                    unit_num=unit_num, lesson_type=lesson_type,
                    discipline=discipline
                ):
                    return {"error": True, "message": "Text extraction failed"}

                with open(temp_txt, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                temp_txt.unlink(missing_ok=True)

                if not raw_text.strip():
                    return {"error": True, "message": "No text extracted"}

                ai_metadata = {
                    "class":        class_num,
                    "subject":      subject,
                    "unit":         unit_num,
                    "lesson_title": filename_base,
                    "lesson_type":  lesson_type,
                    "term":         term_key,
                    "discipline":   discipline,
                }

                # ── Claude generates Content + QA + LP ───────────────────────
                results  = ai_converter.generate_all(raw_text, ai_metadata)
                deployed = []

                # Deploy Content HTML
                if results.get("content"):
                    content_html_file = self.temp_dir / f"{filename_base}.html"
                    with open(content_html_file, "w", encoding="utf-8") as f:
                        f.write(results["content"])
                    content_md_file = self.temp_dir / f"{filename_base}.md"
                    with open(content_md_file, "w", encoding="utf-8") as f:
                        f.write(f"# {filename_base}\n\n{raw_text}")
                    bridge.deploy_content(content_html_file, bridge_meta, "html", "content")
                    bridge.deploy_content(content_md_file,   bridge_meta, "md",   "content")
                    deployed.append("content")
                    print(f"✅ Content deployed")
                else:
                    print(f"⚠️  Content generation failed — skipping")

                # Deploy QA HTML
                if results.get("qa"):
                    qa_html_file = self.temp_dir / f"{filename_base}_qa.html"
                    with open(qa_html_file, "w", encoding="utf-8") as f:
                        f.write(results["qa"])
                    bridge.deploy_content(qa_html_file, bridge_meta, "html", "qa")
                    deployed.append("qa")
                    print(f"✅ QA deployed")
                else:
                    print(f"⚠️  QA generation failed — skipping")

                # Deploy LP HTML
                if results.get("lp"):
                    lp_html_file = self.temp_dir / f"{filename_base}_lp.html"
                    with open(lp_html_file, "w", encoding="utf-8") as f:
                        f.write(results["lp"])
                    bridge.deploy_content(lp_html_file, bridge_meta, "html", "lp")
                    deployed.append("lp")
                    print(f"✅ LP deployed")
                else:
                    print(f"⚠️  LP generation failed — skipping")

                if not deployed:
                    return {"error": True, "message": "All generations failed"}

                return {
                    "error":     False,
                    "filename":  f"{filename_base}.html",
                    "file_path": str(self.temp_dir / f"{filename_base}.html"),
                    "deployed":  deployed,
                    "message":   f"Generated and deployed: {', '.join(deployed)}"
                }

            return {"error": True, "message": f"Unknown output format: {output_format}"}

        except Exception as e:
            print(f"❌ Processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": True, "message": f"Processing error: {str(e)}"}

    # ──────────────────────────────────────────────────────────────────────────
    # Helper: Get lesson type from index
    # ──────────────────────────────────────────────────────────────────────────

    def _get_lesson_type(self, term_index: dict, unit_num: int, lesson_choice: int, subject: str = "") -> str:
        """Returns lesson type. For discipline-based subjects, returns subject name."""
        try:
            # Discipline-based subjects (SS, Science) use disciplines key — not units
            flat_disciplines = all(
                k in ["physics", "chemistry", "biology", "computer_science",
                      "history", "geography", "civics", "economics"]
                for k in term_index.keys() if k != "meta"
            )
            if "disciplines" in term_index or flat_disciplines:
                return subject.lower() if subject else "socialscience"

            units = term_index.get("units", [])
            if unit_num > len(units):
                return "prose"
            unit_obj = units[unit_num - 1]
            lessons = []
            for cat in ["prose", "poem", "supplementary", "play"]:
                if cat in unit_obj:
                    lessons.append(cat)
            if lesson_choice <= len(lessons):
                return lessons[lesson_choice - 1]
        except:
            pass
        return "prose"


# Singleton instance
processor = PDFProcessor()