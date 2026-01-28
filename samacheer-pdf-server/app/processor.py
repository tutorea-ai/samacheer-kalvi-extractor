import requests
import os
import json
import PyPDF2
import gdown
import pdfplumber
import shutil
from pathlib import Path
from typing import Dict, Tuple, Optional
from .services.ai_converter import ai_converter
from .config import settings

class PDFProcessor:
    """
    Core PDF processing engine with multi-subject and discipline support
    """
    
    def __init__(self):
        self.catalogs_cache = {}
        self.base_path = settings.BASE_DIR
        self.cache_dir = settings.CACHE_DIR
        self.temp_dir = settings.TEMP_DIR
        print("🚀 PDF Processor initialized with discipline support")
    
    def _load_catalog(self, subject: str, medium: str = "english") -> dict:
        """Dynamic catalog loading based on subject and medium"""
        cache_key = f"{subject}_{medium}"
        if cache_key in self.catalogs_cache:
            return self.catalogs_cache[cache_key]
        
        catalog_path = settings.get_catalog_path(subject, medium)
        
        if not catalog_path.exists():
            print(f"❌ Catalog not found: {catalog_path}")
            # Fallback for legacy English
            if subject == "english" and medium == "english":
                try:
                    response = requests.get(settings.CATALOG_URL, timeout=10)
                    if response.status_code == 200:
                        return response.json()
                except: pass
            return {}
        
        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog_data = json.load(f)
            self.catalogs_cache[cache_key] = catalog_data
            return catalog_data
        except Exception as e:
            print(f"❌ Error loading catalog: {e}")
            return {}
    
    def _load_unit_index(self, class_num: int, subject: str, medium: str = "english") -> dict:
        """Dynamic index loading"""
        index_path = settings.get_index_path(subject, class_num, medium)
        if not index_path.exists(): return {}
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return {}
    
    def _generate_book_key(self, class_num: int, term: int, subject: str, medium: str) -> str:
        subject = subject.lower().strip()
        medium = medium.lower().strip()
        if class_num >= 8: term = 0
        suffix = "" if subject in ["english", "tamil"] else f"-{medium}-medium"
        return f"class-{class_num}-term{term}-{subject}{suffix}.pdf"
    
    def _download_file(self, file_id: str, output_path: Path) -> bool:
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, str(output_path), quiet=False, fuzzy=True)
            return output_path.exists()
        except: return False
    
    def _slice_pdf(self, source_pdf: Path, output_pdf: Path, start_page: int, end_page: int) -> bool:
        try:
            with open(source_pdf, 'rb') as infile:
                reader = PyPDF2.PdfReader(infile)
                writer = PyPDF2.PdfWriter()
                if end_page > len(reader.pages): return False
                for i in range(start_page - 1, end_page):
                    writer.add_page(reader.pages[i])
                with open(output_pdf, 'wb') as outfile:
                    writer.write(outfile)
            return True
        except: return False
    
    def _extract_text(self, pdf_file: Path, start_page: int, end_page: int, output_txt: Path) -> bool:
        try:
            text_content = ""
            with pdfplumber.open(pdf_file) as pdf:
                if end_page > len(pdf.pages): end_page = len(pdf.pages)
                for page_num in range(start_page - 1, end_page):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    text_content += (text + "\n\n" + "="*50 + "\n\n") if text else ""
            with open(output_txt, 'w', encoding='utf-8') as f:
                f.write(text_content)
            return True
        except: return False

    def _get_lesson_details(self, index_data: dict, unit_num: int, lesson_choice: int, class_num: int, discipline: str = None):
        """
        Calculates start/end pages.
        Now handles both 'units' (English) and 'disciplines' (Social Science).
        """
        meta = index_data.get("meta", {"prelim_pages": 0, "total_pdf_pages": 999})
        offset = meta["prelim_pages"]

        # --- STEP 1: Determine which list of lessons to use ---
        target_units = []         # The list we select from (e.g. just History)
        all_units_for_slicing = [] # ALL units in the book (History + Geo + Civics) for boundary calculation

        if "disciplines" in index_data:
            # Social Science Structure (Split Lists)
            if not discipline:
                print("❌ Error: 'discipline' parameter is missing for this subject.")
                return None
            
            disc_key = discipline.lower()
            if disc_key not in index_data["disciplines"]:
                print(f"❌ Error: Discipline '{disc_key}' not found.")
                return None
            
            target_units = index_data["disciplines"][disc_key]
            
            # Flatten ALL disciplines to ensure we find the correct 'next page' even across subjects
            for d_list in index_data["disciplines"].values():
                all_units_for_slicing.extend(d_list)
                
        else:
            # English/Science Structure (Single List)
            target_units = index_data.get("units", [])
            all_units_for_slicing = target_units

        # --- STEP 2: Validate Selection ---
        if not target_units or unit_num > len(target_units):
            return None
        
        # Note: Index is unit_num - 1
        selected_unit_obj = target_units[unit_num - 1]

        # --- STEP 3: Handle Internal Lesson Structure (Prose vs Direct) ---
        # Case A: Social Science / Direct Structure ({ "page": 109, "title": "..." })
        if "page" in selected_unit_obj:
            start_pdf_page = selected_unit_obj["page"] + offset
            clean_title = selected_unit_obj['title'].replace(' ', '')
            filename = f"Class{class_num}-{discipline or 'Unit'}-{unit_num}-{clean_title}"
            # For direct units, we don't use 'lesson_choice' (it's always 1 unit = 1 file)
            selected_page_raw = selected_unit_obj["page"]

        # Case B: English Structure ({ "prose": { "page": 88 }, ... })
        else:
            lessons = []
            for cat in ["prose", "poem", "supplementary", "play"]:
                if cat in selected_unit_obj:
                    lessons.append({
                        "type": cat, 
                        "title": selected_unit_obj[cat]['title'], 
                        "page": selected_unit_obj[cat]['page']
                    })
            
            if lesson_choice > len(lessons): return None
            selected_lesson = lessons[lesson_choice - 1]
            start_pdf_page = selected_lesson["page"] + offset
            clean_title = selected_lesson['title'].replace(' ', '')
            filename = f"Class{class_num}-Unit{unit_num}-{selected_lesson['type'].capitalize()}-{clean_title}"
            selected_page_raw = selected_lesson["page"]

        # --- STEP 4: Calculate End Page (The Cut Boundary) ---
        # We look at ALL units to find the next starting number
        all_start_pages = []
        for u in all_units_for_slicing:
            # Check for direct page key
            if "page" in u:
                all_start_pages.append(u["page"])
            # Check for nested keys (English)
            else:
                for cat in ["prose", "poem", "supplementary", "play"]:
                    if cat in u:
                        all_start_pages.append(u[cat]['page'])
        
        all_start_pages.sort()
        
        # Find the next start page that is greater than our current start page
        next_pages = [p for p in all_start_pages if p > selected_page_raw]
        
        if next_pages:
            # Stop 1 page before the next lesson starts
            end_pdf_page = next_pages[0] + offset - 1
        else:
            # No next lesson? Go to end of PDF
            end_pdf_page = meta["total_pdf_pages"]

        return filename, start_pdf_page, end_pdf_page

    def process_request(self, request_data: dict) -> dict:
        try:
            # 1. Extract Parameters
            class_num = request_data["class_num"]
            subject = request_data["subject"]
            term = request_data.get("term", 0)
            medium = request_data.get("medium", "english")
            mode = request_data["mode"]
            output_format = request_data["output_format"]
            # 🆕 Extract Discipline
            discipline = request_data.get("discipline")
            
            print(f"📚 Processing: Class {class_num} | {subject} | {discipline or 'General'}")
            
            # 2. Load Catalog
            catalog = self._load_catalog(subject, medium)
            if not catalog: return {"error": True, "message": "Catalog not found"}
            
            # 3. Generate Key & Get Drive ID
            book_key = self._generate_book_key(class_num, term, subject, medium)
            if book_key not in catalog: return {"error": True, "message": f"Book not found: {book_key}"}
            
            drive_id = catalog[book_key]
            
            # 4. Download/Cache
            cached_file = self.cache_dir / book_key
            if not cached_file.exists():
                if not self._download_file(drive_id, cached_file):
                    return {"error": True, "message": "Download failed"}

            # === FULL BOOK MODE ===
            if mode == "full_book":
                if output_format == "pdf":
                    output_file = self.temp_dir / book_key
                    shutil.copy(cached_file, output_file)
                    return {"error": False, "filename": output_file.name, "file_path": str(output_file)}
                # TXT Handling
                elif output_format == "txt":
                    output_file = self.temp_dir / book_key.replace('.pdf', '.txt')
                    with open(cached_file, 'rb') as f: 
                        total = len(PyPDF2.PdfReader(f).pages)
                    self._extract_text(cached_file, 1, total, output_file)
                    return {"error": False, "filename": output_file.name, "file_path": str(output_file)}
                else:
                    return {"error": True, "message": "Full book only supports PDF/TXT formats"}

            # === LESSON MODE ===
            unit_num = request_data["unit"]
            lesson_choice = request_data.get("lesson_choice", 1) # Default to 1 if missing
            
            # 5. Load Index
            index_data = self._load_unit_index(class_num, subject, medium)
            if not index_data: return {"error": True, "message": "Index not found"}
            
            term_key = f"term{term}" if class_num in [6, 7] else "term0"
            if term_key not in index_data: return {"error": True, "message": f"Term {term} not found in index"}
            
            # 6. Get Details (Pass Discipline Here!)
            details = self._get_lesson_details(index_data[term_key], unit_num, lesson_choice, class_num, discipline)
            
            if not details: return {"error": True, "message": "Invalid lesson selection"}
            
            filename_base, start_page, end_page = details
            print(f"📄 Cutting Pages: {start_page} to {end_page}")

            # === OUTPUT HANDLERS ===
            if output_format == "pdf":
                output_file = self.temp_dir / f"{filename_base}.pdf"
                self._slice_pdf(cached_file, output_file, start_page, end_page)
                return {"error": False, "filename": output_file.name, "file_path": str(output_file)}
            
            elif output_format == "txt":
                output_file = self.temp_dir / f"{filename_base}.txt"
                self._extract_text(cached_file, start_page, end_page, output_file)
                return {"error": False, "filename": output_file.name, "file_path": str(output_file)}

            # === 💎 AI / MD / HTML LOGIC RESTORED HERE ===
            elif output_format in ["md", "html"]:
                print(f"🤖 AI Processing: Converting lesson...")
                
                # Step 1: Extract Text
                temp_txt = self.temp_dir / f"{filename_base}_temp.txt"
                if not self._extract_text(cached_file, start_page, end_page, temp_txt):
                    return {"error": True, "message": "Text extraction failed"}
                
                with open(temp_txt, 'r', encoding='utf-8') as f: 
                    raw_text = f.read()
                temp_txt.unlink(missing_ok=True)

                # Step 2: AI Convert to Markdown
                markdown_content = ai_converter.convert_to_markdown(
                    text=raw_text,
                    metadata={
                        'class': class_num, 
                        'subject': subject, 
                        'unit': unit_num, 
                        'lesson_title': filename_base,
                        'discipline': discipline  # 🆕 Passed discipline to AI
                    }
                )
                
                if not markdown_content: 
                    return {"error": True, "message": "AI conversion failed"}

                # Step 3: ALWAYS Save & Deploy Markdown (Mango #1)
                md_file = self.temp_dir / f"{filename_base}.md"
                with open(md_file, 'w', encoding='utf-8') as f: 
                    f.write(markdown_content)
                
                print(f"✅ Markdown saved: {md_file.name}")
                
                # Bridge MD
                from .services.bridge import bridge
                bridge_meta = {
                    "class_num": class_num, 
                    "term": term, 
                    "unit": unit_num, 
                    "lesson_choice": lesson_choice,
                    "subject": subject,
                    "medium": medium,
                    "discipline": discipline # 🆕 Added to Bridge
                }
                bridge.deploy_content(md_file, bridge_meta, "md")
                
                final_output = md_file

                # Step 4: If HTML Requested, Convert & Deploy HTML (Mango #2)
                if output_format == "html":
                    print(f"🎨 Converting Markdown to HTML (Server Mode)...")
                    from .services.html_converter import html_converter
                    
                    html_content = html_converter.convert_to_html(
                        markdown_content=markdown_content,
                        metadata={
                            'class': class_num, 
                            'lesson_title': filename_base
                        },
                        mode="server"
                    )
                    
                    html_file = self.temp_dir / f"{filename_base}.html"
                    with open(html_file, 'w', encoding='utf-8') as f: 
                        f.write(html_content)
                    
                    print(f"✅ HTML saved: {html_file.name}")
                    
                    # Bridge HTML
                    bridge.deploy_content(html_file, bridge_meta, "html")
                    final_output = html_file

                return {"error": False, "filename": final_output.name, "file_path": str(final_output)}

            return {"error": True, "message": "Invalid format"}

        except Exception as e:
            print(f"❌ Processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": True, "message": f"Processing error: {str(e)}"}

# Create singleton
processor = PDFProcessor()