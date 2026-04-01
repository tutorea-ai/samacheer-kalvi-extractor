"""
Core PDF Processing Engine
Handles the full pipeline:
  Download → Slice → Extract Text (pdf2htmlEX + w3m) → AI Generate (Content + QA + LP) → Deploy via Bridge
"""

import requests
import os
import json
import PyPDF2
import gdown
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional
from .services.ai_converter import ai_converter
from .services.bridge import bridge
from .config import settings


# ── Docker image for pdf2htmlEX ───────────────────────────────────────────────
PDF2HTMLEX_IMAGE = "pdf2htmlex/pdf2htmlex:0.18.8.rc1-master-20200630-Ubuntu-focal-x86_64"


class PDFProcessor:
    """Core PDF processing engine with multi-subject and discipline support."""

    def __init__(self):
        self.catalogs_cache = {}
        self.base_path = settings.BASE_DIR
        self.cache_dir = settings.CACHE_DIR
        self.temp_dir = settings.TEMP_DIR
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
        medium = medium.lower().strip()
        if class_num >= 8:
            term = 0
        suffix = "" if subject in ["english", "tamil"] else f"-{medium}-medium"
        return f"class-{class_num}-term{term}-{subject}{suffix}.pdf"

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
    # NEW: Smart Text Extraction — pdf2htmlEX + w3m
    # Replaces old pdfplumber extraction
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_text(self, pdf_file: Path, start_page: int, end_page: int, output_txt: Path) -> bool:
        """
        Extracts clean text from PDF using pdf2htmlEX + w3m pipeline.

        Steps:
          1. pdf2htmlEX converts PDF pages → perfect HTML (correct column order)
          2. w3m converts HTML → clean readable text
          3. Save text to output_txt

        Falls back to pdfplumber if Docker/w3m fails.
        """
        try:
            print(f"   🔄 Extracting pages {start_page}→{end_page} via pdf2htmlEX + w3m...")

            # ── Step 1: pdf2htmlEX → HTML ─────────────────────────────────────
            html_output_name = f"{pdf_file.stem}_p{start_page}_{end_page}.html"
            html_output_path = self.temp_dir / html_output_name

            docker_result = subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{pdf_file.parent}:/pdf",        # mount PDF folder
                "-v", f"{self.temp_dir}:/output",        # mount output folder
                PDF2HTMLEX_IMAGE,
                "--first-page", str(start_page),
                "--last-page", str(end_page),
                "--zoom", "1.3",
                "--dest-dir", "/output",                 # save HTML to output folder
                f"/pdf/{pdf_file.name}",
                html_output_name                         # output filename
            ], capture_output=True, text=True, timeout=120)

            if docker_result.returncode != 0:
                print(f"   ⚠️  pdf2htmlEX failed — falling back to pdfplumber")
                print(f"   Docker error: {docker_result.stderr[:200]}")
                return self._extract_text_fallback(pdf_file, start_page, end_page, output_txt)

            # Fix permissions (Docker creates files as root)
            subprocess.run(["sudo", "chmod", "644", str(html_output_path)],
                         capture_output=True)

            if not html_output_path.exists():
                print(f"   ⚠️  HTML output not found — falling back to pdfplumber")
                return self._extract_text_fallback(pdf_file, start_page, end_page, output_txt)

            print(f"   ✅ pdf2htmlEX done → {html_output_name}")

            # ── Step 2: w3m → clean text ──────────────────────────────────────
            w3m_result = subprocess.run([
                "w3m", "-dump", str(html_output_path)
            ], capture_output=True, text=True, timeout=60)

            if w3m_result.returncode != 0 or not w3m_result.stdout.strip():
                print(f"   ⚠️  w3m failed — falling back to pdfplumber")
                html_output_path.unlink(missing_ok=True)
                return self._extract_text_fallback(pdf_file, start_page, end_page, output_txt)

            clean_text = w3m_result.stdout

            # ── Step 3: Save clean text ───────────────────────────────────────
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(clean_text)

            # Cleanup HTML temp file
            html_output_path.unlink(missing_ok=True)

            print(f"   ✅ w3m done → {len(clean_text)} chars extracted")
            return True

        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Extraction timed out — falling back to pdfplumber")
            return self._extract_text_fallback(pdf_file, start_page, end_page, output_txt)

        except Exception as e:
            print(f"   ⚠️  Extraction error: {e} — falling back to pdfplumber")
            return self._extract_text_fallback(pdf_file, start_page, end_page, output_txt)

    def _extract_text_fallback(self, pdf_file: Path, start_page: int, end_page: int, output_txt: Path) -> bool:
        """
        Fallback text extraction using pdfplumber.
        Used when pdf2htmlEX or w3m fails.
        """
        try:
            import pdfplumber
            print(f"   🔄 Fallback: extracting via pdfplumber...")
            text_content = ""
            with pdfplumber.open(pdf_file) as pdf:
                if end_page > len(pdf.pages):
                    end_page = len(pdf.pages)
                for page_num in range(start_page - 1, end_page):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    text_content += (text + "\n\n" + "=" * 50 + "\n\n") if text else ""
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(text_content)
            print(f"   ✅ pdfplumber fallback done → {len(text_content)} chars")
            return True
        except Exception as e:
            print(f"   ❌ pdfplumber fallback also failed: {e}")
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

        if "disciplines" in index_data:
            if not discipline:
                print("❌ 'discipline' parameter is required for this subject.")
                return None
            disc_key = discipline.lower()
            if disc_key not in index_data["disciplines"]:
                print(f"❌ Discipline '{disc_key}' not found.")
                return None
            target_units = index_data["disciplines"][disc_key]
            for d_list in index_data["disciplines"].values():
                all_units_for_slicing.extend(d_list)
        else:
            target_units = index_data.get("units", [])
            all_units_for_slicing = target_units

        if not target_units or unit_num > len(target_units):
            return None

        selected_unit_obj = target_units[unit_num - 1]

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

            print(f"\n📚 Processing: Class {class_num} | {subject} | {discipline or 'General'} | Format: {output_format}")

            # 2. Load catalog
            catalog = self._load_catalog(subject, medium)
            if not catalog:
                return {"error": True, "message": "Catalog not found"}

            # 3. Get Drive ID
            book_key = self._generate_book_key(class_num, term, subject, medium)
            if book_key not in catalog:
                return {"error": True, "message": f"Book not found in catalog: {book_key}"}

            drive_id = catalog[book_key]

            # 4. Download / use cache
            cached_file = self.cache_dir / book_key
            if not cached_file.exists():
                print(f"⬇️  Downloading: {book_key}")
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
            unit_num = request_data["unit"]
            lesson_choice = request_data.get("lesson_choice", 1)

            # 5. Load index
            index_data = self._load_unit_index(class_num, subject, medium)
            if not index_data:
                return {"error": True, "message": "Index not found"}

            term_key = f"term{term}" if class_num in [6, 7] else "term0"
            if term_key not in index_data:
                return {"error": True, "message": f"Term key '{term_key}' not found in index"}

            # 6. Get lesson page range
            details = self._get_lesson_details(
                index_data[term_key], unit_num, lesson_choice, class_num, discipline
            )
            if not details:
                return {"error": True, "message": "Invalid lesson selection"}

            filename_base, start_page, end_page = details
            print(f"📄 Pages: {start_page} → {end_page}")

            # ── PDF output ────────────────────────────────────────────────────
            if output_format == "pdf":
                output_file = self.temp_dir / f"{filename_base}.pdf"
                self._slice_pdf(cached_file, output_file, start_page, end_page)
                return {"error": False, "filename": output_file.name, "file_path": str(output_file)}

            # ── TXT output ────────────────────────────────────────────────────
            elif output_format == "txt":
                output_file = self.temp_dir / f"{filename_base}.txt"
                self._extract_text(cached_file, start_page, end_page, output_file)
                return {"error": False, "filename": output_file.name, "file_path": str(output_file)}

            # ── CONTENT ONLY output ───────────────────────────────────────────
            elif output_format == "content_only":

                bridge_meta = {
                    "class_num": class_num,
                    "term": term,
                    "unit": unit_num,
                    "lesson_choice": lesson_choice,
                    "subject": subject,
                    "medium": medium,
                    "discipline": discipline,
                }

                print(f"🤖 Starting Content-only generation...")

                temp_txt = self.temp_dir / f"{filename_base}_raw.txt"
                if not self._extract_text(cached_file, start_page, end_page, temp_txt):
                    return {"error": True, "message": "Text extraction failed"}

                with open(temp_txt, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                temp_txt.unlink(missing_ok=True)

                if not raw_text.strip():
                    return {"error": True, "message": "No text extracted from PDF pages"}

                ai_metadata = {
                    "class": class_num,
                    "subject": subject,
                    "unit": unit_num,
                    "lesson_title": filename_base,
                    "lesson_type": self._get_lesson_type(index_data[term_key], unit_num, lesson_choice),
                    "term": term_key,
                    "discipline": discipline,
                }

                from .services.ai_converter import _wrap_html
                content_html = ai_converter._generate_content(raw_text, ai_metadata)

                if not content_html:
                    return {"error": True, "message": "Content generation failed"}

                content_html_file = self.temp_dir / f"{filename_base}.html"
                with open(content_html_file, "w", encoding="utf-8") as f:
                    f.write(_wrap_html(content_html, title=filename_base, content_type="content"))

                content_md_file = self.temp_dir / f"{filename_base}.md"
                with open(content_md_file, "w", encoding="utf-8") as f:
                    f.write(f"# {filename_base}\n\n{raw_text}")

                bridge.deploy_content(content_html_file, bridge_meta, "html", "content")
                bridge.deploy_content(content_md_file, bridge_meta, "md", "content")
                print(f"✅ Content deployed")

                return {
                    "error": False,
                    "filename": f"{filename_base}.html",
                    "file_path": str(content_html_file),
                    "deployed": ["content"],
                    "message": "Content only generated and deployed"
                }

            # ── AI OUTPUT: html (Content + QA + LP) ──────────────────────────
            elif output_format == "html":

                bridge_meta = {
                    "class_num": class_num,
                    "term": term,
                    "unit": unit_num,
                    "lesson_choice": lesson_choice,
                    "subject": subject,
                    "medium": medium,
                    "discipline": discipline,
                }

                # ✅ SKIP CHECK
                if bridge.is_already_deployed(bridge_meta):
                    return {
                        "error": False,
                        "filename": f"{filename_base}.html",
                        "file_path": str(self.temp_dir / f"{filename_base}.html"),
                        "deployed": ["content", "qa", "lp"],
                        "skipped": True,
                        "message": "Already deployed — skipped"
                    }

                print(f"🤖 Starting AI generation pipeline...")

                # Extract text using new pipeline
                temp_txt = self.temp_dir / f"{filename_base}_raw.txt"
                if not self._extract_text(cached_file, start_page, end_page, temp_txt):
                    return {"error": True, "message": "Text extraction failed"}

                with open(temp_txt, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                temp_txt.unlink(missing_ok=True)

                if not raw_text.strip():
                    return {"error": True, "message": "No text extracted from PDF pages"}

                ai_metadata = {
                    "class": class_num,
                    "subject": subject,
                    "unit": unit_num,
                    "lesson_title": filename_base,
                    "lesson_type": self._get_lesson_type(index_data[term_key], unit_num, lesson_choice),
                    "term": term_key,
                    "discipline": discipline,
                }

                # Generate Content + QA + LP
                results = ai_converter.generate_all(raw_text, ai_metadata)
                deployed = []

                # Deploy Content HTML + MD
                if results["content"]:
                    content_html_file = self.temp_dir / f"{filename_base}.html"
                    with open(content_html_file, "w", encoding="utf-8") as f:
                        f.write(results["content"])

                    content_md_file = self.temp_dir / f"{filename_base}.md"
                    with open(content_md_file, "w", encoding="utf-8") as f:
                        f.write(f"# {filename_base}\n\n{raw_text}")

                    bridge.deploy_content(content_html_file, bridge_meta, "html", "content")
                    bridge.deploy_content(content_md_file, bridge_meta, "md", "content")
                    deployed.append("content")
                    print(f"✅ Content deployed")
                else:
                    print(f"⚠️  Content generation failed — skipping")

                # Deploy QA HTML
                if results["qa"]:
                    qa_html_file = self.temp_dir / f"{filename_base}_qa.html"
                    with open(qa_html_file, "w", encoding="utf-8") as f:
                        f.write(results["qa"])
                    bridge.deploy_content(qa_html_file, bridge_meta, "html", "qa")
                    deployed.append("qa")
                    print(f"✅ QA deployed")
                else:
                    print(f"⚠️  QA generation failed — skipping")

                # Deploy LP HTML
                if results["lp"]:
                    lp_html_file = self.temp_dir / f"{filename_base}_lp.html"
                    with open(lp_html_file, "w", encoding="utf-8") as f:
                        f.write(results["lp"])
                    bridge.deploy_content(lp_html_file, bridge_meta, "html", "lp")
                    deployed.append("lp")
                    print(f"✅ LP deployed")
                else:
                    print(f"⚠️  LP generation failed — skipping")

                if not deployed:
                    return {"error": True, "message": "All AI generations failed"}

                return {
                    "error": False,
                    "filename": f"{filename_base}.html",
                    "file_path": str(self.temp_dir / f"{filename_base}.html"),
                    "deployed": deployed,
                    "message": f"Generated and deployed: {', '.join(deployed)}"
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

    def _get_lesson_type(self, term_index: dict, unit_num: int, lesson_choice: int) -> str:
        """Returns the lesson type (prose/poem/supplementary/play) from index data."""
        try:
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