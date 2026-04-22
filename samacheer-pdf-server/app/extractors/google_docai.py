"""
app/extractors/google_docai.py

Hybrid PDF extractor — Google Document AI + pdfplumber.

Strategy:
  - Extract full document with Document AI (correct column order, clean)
  - Extract full document with pdfplumber (complete content, needs cleaning)
  - Compare total char counts
  - If pdfplumber has >30% more → use pdfplumber (after noise cleaning)
  - Otherwise → use Document AI (better column order, cleaner)

For Tamil: Document AI only (pdfplumber garbles Tamil script)
"""

import os
import io
import re
from pathlib import Path
from typing import Optional
import PyPDF2

from ..config import settings


# ── Noise patterns for pdfplumber text cleaning ───────────────────────────────
NOISE_PATTERNS = [
    (r'\[[A-Za-z0-9]{4,12}\]', ''),                          # hash codes
    (r'\d+th\s+\w+_Unit_\d+\.indd[^\n]*', ''),               # PDF file info
    (r'^\d{1,3}\s*$', ''),                                    # standalone page numbers
    (r'^\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2}\s*$', ''),   # timestamps
]


def _clean_pdfplumber_text(text: str) -> str:
    """Remove noise from pdfplumber extracted text."""
    for pattern, replacement in NOISE_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _extract_sub_blocks_recursive(sub_blocks) -> list:
    """Recursively extract text from nested sub-blocks."""
    texts = []
    for sub in sub_blocks:
        if not sub.text_block:
            continue
        sub_type = sub.text_block.type_ or ""
        if sub_type in ("footer", "page-footer"):
            continue
        sub_text = (sub.text_block.text or "").strip()
        if sub_text and len(sub_text) > 2:
            texts.append(sub_text)
        if sub.text_block.blocks:
            texts.extend(_extract_sub_blocks_recursive(sub.text_block.blocks))
    return texts


class GoogleDocAIExtractor:
    """
    Hybrid PDF extractor combining Document AI and pdfplumber.
    Uses Document AI as primary (correct column order).
    Falls back to pdfplumber if it gets significantly more content.
    """

    def __init__(self):
        self._client         = None
        self._processor_name = None
        self._initialized    = False

    def _initialize(self):
        """Lazy initialization of Document AI client."""
        if self._initialized:
            return
        try:
            from google.cloud import documentai

            credentials = settings.GOOGLE_APPLICATION_CREDENTIALS
            if credentials and not os.path.isabs(credentials):
                credentials = str(settings.BASE_DIR / credentials)

            if credentials and Path(credentials).exists():
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials
            else:
                print(f"⚠️  Document AI credentials not found: {credentials}")
                return

            self._client = documentai.DocumentProcessorServiceClient()
            self._processor_name = (
                f"projects/{settings.DOCAI_PROJECT_ID}"
                f"/locations/{settings.DOCAI_LOCATION}"
                f"/processors/{settings.DOCAI_PROCESSOR_ID}"
            )
            self._initialized = True
            print(f"✅ Google Document AI (Layout Parser) initialized")
            print(f"   Processor: {self._processor_name}")

        except Exception as e:
            print(f"⚠️  Document AI initialization failed: {e}")

    def is_available(self) -> bool:
        self._initialize()
        return self._initialized and self._client is not None

    def extract(
        self,
        pdf_file: Path,
        start_page: int,
        end_page: int,
        output_txt: Path,
        subject: str = "english"
    ) -> bool:
        """
        Extract text from PDF pages using hybrid approach.

        For Tamil: Document AI only
        For others: Compare Document AI vs pdfplumber — use better one
        """
        self._initialize()
        if not self._initialized:
            return False

        try:
            print(f"   🔄 Document AI: extracting pages {start_page}→{end_page}...")

            # Slice PDF to bytes
            pdf_bytes = self._slice_pdf_to_bytes(pdf_file, start_page, end_page)
            if not pdf_bytes:
                print(f"   ❌ Failed to slice PDF pages")
                return False

            print(f"   📄 PDF slice: {len(pdf_bytes)} bytes")

            # Send to Document AI
            from google.cloud import documentai
            raw_document = documentai.RawDocument(
                content=pdf_bytes,
                mime_type="application/pdf"
            )
            request = documentai.ProcessRequest(
                name=self._processor_name,
                raw_document=raw_document
            )
            result   = self._client.process_document(request=request)
            document = result.document

            # For Tamil — use Document AI only
            if subject.lower() == "tamil":
                clean_text = self._extract_full_docai(document)
                print(f"   ✅ Tamil: Document AI only — {len(clean_text)} chars")
            else:
                # Hybrid — compare Document AI vs pdfplumber
                clean_text = self._hybrid_extract(
                    document, pdf_file, start_page, end_page
                )

            if not clean_text.strip():
                print(f"   ❌ No text extracted")
                return False

            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(clean_text)

            print(f"   ✅ Extraction complete: {len(clean_text)} chars")
            return True

        except Exception as e:
            print(f"   ❌ Document AI extraction failed: {e}")
            return False

    def _hybrid_extract(
        self,
        document,
        pdf_file: Path,
        start_page: int,
        end_page: int
    ) -> str:
        """
        Hybrid extraction.
        Get full text from both Document AI and pdfplumber.
        Use whichever gives more content (30% threshold).
        No per-page splitting — avoids duplicate content.
        """
        try:
            import pdfplumber
        except ImportError:
            print(f"   ⚠️  pdfplumber not available — using Document AI only")
            return self._extract_full_docai(document)

        # Full Document AI extraction (all blocks in order)
        docai_full = self._extract_full_docai(document)

        # Full pdfplumber extraction with noise cleaning
        plumber_parts = []
        with pdfplumber.open(pdf_file) as pdf:
            for page_idx in range(start_page - 1, min(end_page, len(pdf.pages))):
                page_text = pdf.pages[page_idx].extract_text() or ""
                if page_text.strip():
                    plumber_parts.append(_clean_pdfplumber_text(page_text))
        plumber_full = "\n\n".join(plumber_parts)

        docai_len   = len(docai_full.strip())
        plumber_len = len(plumber_full.strip())

        print(f"   📊 DocAI: {docai_len} chars | pdfplumber: {plumber_len} chars")

        # Use pdfplumber if it has more content
        # pdfplumber consistently gets complete content for English textbooks
        # Document AI sometimes misses structured content (tables, conversations)
        if plumber_len > docai_len:
            print(f"   📊 Using pdfplumber (more complete content)")
            return plumber_full
        else:
            print(f"   📊 Using Document AI (equal or better content)")
            return docai_full

    def _extract_full_docai(self, document) -> str:
        """
        Extract full text from Document AI response.
        Reads all blocks in document order — no per-page splitting.
        Recursively extracts nested sub-blocks.
        """
        text_parts = []
        seen = set()  # deduplicate blocks

        for block in document.document_layout.blocks:
            tb = block.text_block
            if not tb or not tb.text:
                continue
            block_type = tb.type_ or ""
            if block_type in ("footer", "page-footer", "page-header"):
                continue
            block_text = tb.text.strip()
            if block_text and len(block_text) > 2:
                # Deduplicate
                key = block_text[:50]
                if key not in seen:
                    seen.add(key)
                    text_parts.append(block_text)
            # Extract sub-blocks
            if tb.blocks:
                for sub_text in _extract_sub_blocks_recursive(tb.blocks):
                    key = sub_text[:50]
                    if key not in seen:
                        seen.add(key)
                        text_parts.append(sub_text)

        full_text = "\n\n".join(text_parts)
        return re.sub(r'\n{3,}', '\n\n', full_text).strip()

    def _slice_pdf_to_bytes(
        self, pdf_file: Path, start_page: int, end_page: int
    ) -> Optional[bytes]:
        """Extract specific pages from PDF and return as bytes."""
        try:
            writer = PyPDF2.PdfWriter()
            with open(pdf_file, "rb") as f:
                reader   = PyPDF2.PdfReader(f)
                end_page = min(end_page, len(reader.pages))
                for i in range(start_page - 1, end_page):
                    writer.add_page(reader.pages[i])
            output = io.BytesIO()
            writer.write(output)
            return output.getvalue()
        except Exception as e:
            print(f"   ❌ PDF slicing failed: {e}")
            return None


# Singleton instance
docai_extractor = GoogleDocAIExtractor()