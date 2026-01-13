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
    Core PDF processing engine
    """
    
    def __init__(self):
        self.catalog = self._load_catalog()
        print(f"📚 Loaded catalog with {len(self.catalog)} books")
        self.base_path = settings.BASE_DIR
        self.cache_dir = settings.CACHE_DIR
        self.temp_dir = settings.TEMP_DIR
    
    def _load_catalog(self) -> dict:
        try:
            response = requests.get(settings.CATALOG_URL, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"❌ Catalog load error: {e}")
            return {}
    
    def _load_unit_index(self, class_num: int, subject: str) -> dict:
        category = "languages" if subject.lower() in ["english", "tamil"] else "subjects"
        index_path = settings.DATA_DIR / "indexes" / category / subject.lower() / f"class-{class_num}.json"
        
        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _generate_book_key(self, class_num: int, term: int, subject: str, medium: str) -> str:
        subject = subject.lower().strip()
        medium = medium.lower().strip()
        if class_num >= 8: term = 0
        suffix = "" if subject in ["english", "tamil"] else f"-{medium}-medium"
        return f"class-{class_num}-term{term}-{subject}{suffix}.pdf"
    
    def _download_file(self, file_id: str, output_path: Path, show_progress: bool = True) -> bool:
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, str(output_path), quiet=not show_progress, fuzzy=True)
            return output_path.exists()
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
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
        except Exception:
            return False
    
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
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return False

    def _get_lesson_details(self, index_data: dict, unit_num: int, lesson_choice: int, class_num: int):
        meta = index_data.get("meta", {"prelim_pages": 0, "total_pdf_pages": 999})
        offset = meta["prelim_pages"]
        units = index_data.get("units", [])
        if not units or unit_num > len(units): return None
        
        selected_unit = units[unit_num - 1]
        lessons = []
        for cat in ["prose", "poem", "supplementary", "play"]:
            if cat in selected_unit:
                lessons.append({"type": cat, "title": selected_unit[cat]['title'], "page": selected_unit[cat]['page']})
        
        if lesson_choice > len(lessons): return None
        selected_lesson = lessons[lesson_choice - 1]
        
        start_pdf_page = selected_lesson["page"] + offset
        
        # Calculate end page
        all_pages = []
        for u in units:
            for cat in ["prose", "poem", "supplementary", "play"]:
                if cat in u: all_pages.append(u[cat]['page'])
        all_pages.sort()
        next_pages = [p for p in all_pages if p > selected_lesson["page"]]
        end_pdf_page = (next_pages[0] + offset - 1) if next_pages else meta["total_pdf_pages"]
        
        clean_title = selected_lesson['title'].replace(' ', '').replace('(', '').replace(')', '')
        filename = f"Class{class_num}-Unit{unit_num}-{selected_lesson['type'].capitalize()}-{clean_title}"
        
        return filename, start_pdf_page, end_pdf_page

    def process_request(self, request_data: dict) -> dict:
        try:
            # 1. Setup Parameters
            class_num = request_data["class_num"]
            subject = request_data["subject"]
            term = request_data.get("term", 0)
            medium = request_data.get("medium", "english")
            mode = request_data["mode"]
            output_format = request_data["output_format"]
            
            book_key = self._generate_book_key(class_num, term, subject, medium)
            if book_key not in self.catalog:
                return {"error": True, "message": f"Book not found: {book_key}"}
            
            drive_id = self.catalog[book_key]
            
            # 2. Check/Download Cache
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
                elif output_format == "txt":
                    output_file = self.temp_dir / book_key.replace('.pdf', '.txt')
                    with open(cached_file, 'rb') as f: total = len(PyPDF2.PdfReader(f).pages)
                    self._extract_text(cached_file, 1, total, output_file)
                    return {"error": False, "filename": output_file.name, "file_path": str(output_file)}
                else:
                    return {"error": True, "message": "Full book only supports PDF/TXT"}

            # === LESSON MODE ===
            unit_num = request_data["unit"]
            lesson_choice = request_data["lesson_choice"]
            
            # Load Index & Find Pages
            index_data = self._load_unit_index(class_num, subject)
            term_key = f"term{term}" if class_num in [6, 7] else "term0"
            if term_key not in index_data: return {"error": True, "message": f"Index missing for {term_key}"}
            
            details = self._get_lesson_details(index_data[term_key], unit_num, lesson_choice, class_num)
            if not details: return {"error": True, "message": "Invalid lesson selection"}
            
            filename_base, start_page, end_page = details

            # Handle PDF/TXT requests (Simple)
            if output_format == "pdf":
                output_file = self.temp_dir / f"{filename_base}.pdf"
                self._slice_pdf(cached_file, output_file, start_page, end_page)
                return {"error": False, "filename": output_file.name, "file_path": str(output_file)}
            
            elif output_format == "txt":
                output_file = self.temp_dir / f"{filename_base}.txt"
                self._extract_text(cached_file, start_page, end_page, output_file)
                return {"error": False, "filename": output_file.name, "file_path": str(output_file)}

            # === 💎 THE BINGO LOGIC: DUAL DEPLOYMENT (MD + HTML) ===
            elif output_format in ["md", "html"]:
                print(f"🤖 AI Processing: Converting lesson...")
                
                # Step 1: Extract Text
                temp_txt = self.temp_dir / f"{filename_base}_temp.txt"
                if not self._extract_text(cached_file, start_page, end_page, temp_txt):
                    return {"error": True, "message": "Text extraction failed"}
                
                with open(temp_txt, 'r', encoding='utf-8') as f: raw_text = f.read()
                temp_txt.unlink(missing_ok=True)

                # Step 2: AI Convert to Markdown
                markdown_content = ai_converter.convert_to_markdown(
                    text=raw_text,
                    metadata={'class': class_num, 'subject': subject, 'unit': unit_num, 'lesson_title': filename_base}
                )
                if not markdown_content: return {"error": True, "message": "AI failed"}

                # Step 3: ALWAYS Save & Deploy Markdown (Mango #1)
                md_file = self.temp_dir / f"{filename_base}.md"
                with open(md_file, 'w', encoding='utf-8') as f: f.write(markdown_content)
                
                # Bridge MD
                from .services.bridge import bridge
                bridge_meta = {"class_num": class_num, "term": term, "unit": unit_num, "lesson_choice": lesson_choice}
                bridge.deploy_content(md_file, bridge_meta, "md")
                
                final_output = md_file

                # Step 4: If HTML Requested, Convert & Deploy HTML (Mango #2)
                if output_format == "html":
                    print(f"🎨 Converting Markdown to HTML (Server Mode)...")
                    from .services.html_converter import html_converter
                    
                    html_content = html_converter.convert_to_html(
                        markdown_content=markdown_content,
                        metadata={'class': class_num, 'lesson_title': filename_base},
                        mode="server"
                    )
                    
                    html_file = self.temp_dir / f"{filename_base}.html"
                    with open(html_file, 'w', encoding='utf-8') as f: f.write(html_content)
                    
                    # Bridge HTML
                    bridge.deploy_content(html_file, bridge_meta, "html")
                    final_output = html_file

                return {"error": False, "filename": final_output.name, "file_path": str(final_output)}

        except Exception as e:
            return {"error": True, "message": f"Processing error: {str(e)}"}

# Create singleton
processor = PDFProcessor()