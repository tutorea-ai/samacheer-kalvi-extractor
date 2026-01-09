import requests
import os
import json
import PyPDF2
import gdown
import pdfplumber
from pathlib import Path
from typing import Dict, Tuple, Optional

from .config import settings

class PDFProcessor:
    """
    Core PDF processing engine
    Refactored from book_downloader.py to work without user interaction
    """
    
    def __init__(self):
        self.catalog = self._load_catalog()
        self.base_path = settings.BASE_DIR
        self.cache_dir = settings.CACHE_DIR
        self.temp_dir = settings.TEMP_DIR
    
    def _load_catalog(self) -> dict:
        """Load book catalog from GitHub"""
        try:
            response = requests.get(settings.CATALOG_URL, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"❌ Catalog load error: {e}")
            return {}
    
    def _load_unit_index(self, class_num: int, subject: str) -> dict:
        """
        Load unit index JSON
        Path: data/indexes/languages/english/class-6.json
        """
        # Determine category
        category = "languages" if subject.lower() in ["english", "tamil"] else "subjects"
        
        # Build path
        index_path = (
            settings.DATA_DIR / 
            "indexes" / 
            category / 
            subject.lower() / 
            f"class-{class_num}.json"
        )
        
        if index_path.exists():
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ Invalid JSON in {index_path}")
                return {}
        return {}
    
    def _generate_book_key(
        self, 
        class_num: int, 
        term: int, 
        subject: str, 
        medium: str
    ) -> str:
        """
        Generate catalog key
        Example: class-12-term0-english.pdf
        """
        subject = subject.lower().strip()
        medium = medium.lower().strip()
        
        # Auto-adjust term for classes 8-12
        if class_num >= 8:
            term = 0
        
        # Add medium suffix for non-language subjects
        suffix = "" if subject in ["english", "tamil"] else f"-{medium}-medium"
        
        return f"class-{class_num}-term{term}-{subject}{suffix}.pdf"
    
    def _download_file(
        self, 
        file_id: str, 
        output_path: Path,
        show_progress: bool = True
    ) -> bool:
        """Download file from Google Drive"""
        try:
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, str(output_path), quiet=not show_progress, fuzzy=True)
            return output_path.exists()
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def _slice_pdf(
        self,
        source_pdf: Path,
        output_pdf: Path,
        start_page: int,
        end_page: int
    ) -> bool:
        """Extract specific pages from PDF"""
        try:
            with open(source_pdf, 'rb') as infile:
                reader = PyPDF2.PdfReader(infile)
                writer = PyPDF2.PdfWriter()
                
                if end_page > len(reader.pages):
                    print(f"⚠️ Book has only {len(reader.pages)} pages")
                    return False
                
                for i in range(start_page - 1, end_page):
                    writer.add_page(reader.pages[i])
                
                with open(output_pdf, 'wb') as outfile:
                    writer.write(outfile)
            
            return True
        except Exception as e:
            print(f"❌ Slicing error: {e}")
            return False
    
    def _extract_text(
        self,
        pdf_file: Path,
        start_page: int,
        end_page: int,
        output_txt: Path
    ) -> bool:
        """Extract text from PDF to TXT file"""
        try:
            text_content = ""
            with pdfplumber.open(pdf_file) as pdf:
                # Adjust range if needed
                if end_page > len(pdf.pages):
                    end_page = len(pdf.pages)
                
                for page_num in range(start_page - 1, end_page):
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_content += page_text + "\n\n" + "="*50 + "\n\n"
                    else:
                        text_content += f"[Page {page_num + 1} - No text found]\n\n"
            
            with open(output_txt, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return True
        except Exception as e:
            print(f"❌ Text extraction error: {e}")
            return False
    
    def _get_lesson_details(
        self,
        index_data: dict,
        unit_num: int,
        lesson_choice: int,
        class_num: int
    ) -> Optional[Tuple[str, int, int]]:
        """
        Get lesson page range from index
        Returns: (filename, start_page, end_page) or None
        """
        meta = index_data.get("meta", {"prelim_pages": 0, "total_pdf_pages": 999})
        offset = meta["prelim_pages"]
        max_pages = meta["total_pdf_pages"]
        
        units = index_data.get("units", [])
        if not units or unit_num > len(units):
            return None
        
        selected_unit = units[unit_num - 1]
        
        # Build lessons list
        lessons = []
        for category in ["prose", "poem", "supplementary", "play"]:
            if category in selected_unit:
                item = selected_unit[category]
                lessons.append({
                    "type": category,
                    "title": item['title'],
                    "page": item['page']
                })
        
        if lesson_choice > len(lessons):
            return None
        
        selected_lesson = lessons[lesson_choice - 1]
        
        # Calculate PDF range
        start_pdf_page = selected_lesson["page"] + offset
        
        # Find next lesson page
        all_pages = []
        for u in units:
            for cat in ["prose", "poem", "supplementary", "play"]:
                if cat in u:
                    all_pages.append(u[cat]['page'])
        
        all_pages.sort()
        next_pages = [p for p in all_pages if p > selected_lesson["page"]]
        
        if next_pages:
            end_pdf_page = (next_pages[0] + offset) - 1
        else:
            end_pdf_page = max_pages
        
        # Generate filename
        clean_title = selected_lesson['title'].replace(' ', '').replace('(', '').replace(')', '')
        filename = f"Class{class_num}-Unit{unit_num}-{selected_lesson['type'].capitalize()}-{clean_title}"
        
        return filename, start_pdf_page, end_pdf_page
    
    def process_request(self, request_data: dict) -> dict:
        """
        Main processing function
        
        Args:
            request_data: Dictionary with keys:
                - class_num, subject, term, medium
                - mode, unit, lesson_choice
                - output_format
        
        Returns:
            Dictionary with file info or error
        """
        try:
            # Extract parameters
            class_num = request_data["class_num"]
            subject = request_data["subject"]
            term = request_data.get("term", 0)
            medium = request_data.get("medium", "english")
            mode = request_data["mode"]
            output_format = request_data["output_format"]
            
            # Generate book key
            book_key = self._generate_book_key(class_num, term, subject, medium)
            
            # Check catalog
            if book_key not in self.catalog:
                return {
                    "error": True,
                    "message": f"Book not found in catalog: {book_key}"
                }
            
            drive_id = self.catalog[book_key]
            
            # === FULL BOOK MODE ===
            if mode == "full_book":
                # Check cache first
                cached_file = self.cache_dir / book_key
                
                if not cached_file.exists():
                    # Download to cache
                    success = self._download_file(drive_id, cached_file)
                    if not success:
                        return {"error": True, "message": "Download failed"}
                
                if output_format == "pdf":
                    # Copy to temp
                    output_file = self.temp_dir / book_key
                    import shutil
                    shutil.copy(cached_file, output_file)
                    
                else:  # txt
                    # Extract text
                    output_file = self.temp_dir / book_key.replace('.pdf', '.txt')
                    
                    with open(cached_file, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        total_pages = len(reader.pages)
                    
                    success = self._extract_text(cached_file, 1, total_pages, output_file)
                    if not success:
                        return {"error": True, "message": "Text extraction failed"}
                
                return {
                    "error": False,
                    "filename": output_file.name,
                    "file_path": str(output_file)
                }
            
            # === LESSON MODE ===
            else:
                unit_num = request_data["unit"]
                lesson_choice = request_data["lesson_choice"]
                
                # Load index
                index_data = self._load_unit_index(class_num, subject)
                
                # Get correct term key
                term_key = f"term{term}" if class_num in [6, 7] else "term0"
                
                if term_key not in index_data:
                    return {
                        "error": True,
                        "message": f"Index data not found for {term_key}"
                    }
                
                target_data = index_data[term_key]
                
                # Get lesson details
                result = self._get_lesson_details(
                    target_data, unit_num, lesson_choice, class_num
                )
                
                if not result:
                    return {"error": True, "message": "Invalid unit/lesson selection"}
                
                filename_base, start_page, end_page = result
                
                # Check cache for source
                cached_source = self.cache_dir / book_key
                
                if not cached_source.exists():
                    success = self._download_file(drive_id, cached_source, show_progress=False)
                    if not success:
                        return {"error": True, "message": "Source download failed"}
                
                # Process based on format
                if output_format == "pdf":
                    output_file = self.temp_dir / f"{filename_base}.pdf"
                    success = self._slice_pdf(cached_source, output_file, start_page, end_page)
                else:
                    output_file = self.temp_dir / f"{filename_base}.txt"
                    success = self._extract_text(cached_source, start_page, end_page, output_file)
                
                if not success:
                    return {"error": True, "message": "Processing failed"}
                
                return {
                    "error": False,
                    "filename": output_file.name,
                    "file_path": str(output_file)
                }
        
        except Exception as e:
            return {
                "error": True,
                "message": f"Processing error: {str(e)}"
            }
    # In PDFProcessor.__init__()
def __init__(self):
    self.catalog = self._load_catalog()
    print(f"📚 Loaded catalog with {len(self.catalog)} books")  # ADD THIS
    print(f"📂 Sample keys: {list(self.catalog.keys())[:3]}")  # ADD THIS
    self.base_path = settings.BASE_DIR
    self.cache_dir = settings.CACHE_DIR
    self.temp_dir = settings.TEMP_DIR


# Create singleton instance
processor = PDFProcessor()