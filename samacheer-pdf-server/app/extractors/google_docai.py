"""
app/extractors/google_docai.py

Google Document AI extractor using Layout Parser.
Replaces pdf2htmlEX + w3m pipeline.

Key improvements over OCR processor:
- Uses document_layout.blocks instead of pages
- Block types: paragraph, heading-1, heading-2, footer, table, list-item
- Footers auto-detected and filtered
- Section headings labeled correctly
- Do You Know box detected and normalized
- Tables extracted with structure
"""

import os
import io
import re
from pathlib import Path
from typing import Optional
import PyPDF2

from ..config import settings


# ── Noise patterns — blocks to always skip ───────────────────────────────────
NOISE_PATTERNS = [
    r'^\d{1,3}$',                                    # standalone page numbers
    r'^\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2}$',    # timestamps
    r'^\d+th\s+\w+_Unit_\d+\.indd',                  # PDF file info
    r'^[A-Za-z0-9]{4,8}$',                           # QR code artifacts
    r'^[A-Z]{2,6}$',                                  # short caps artifacts
]
NOISE_COMPILED = [re.compile(p, re.IGNORECASE) for p in NOISE_PATTERNS]


# ── Do You Know heading variations ───────────────────────────────────────────
# Layout Parser reads the styled heading as split text
DO_YOU_KNOW_PATTERNS = [
    r'^do\s+you\??\s*know',
    r'^do\s*you\s*\?\s*know',
    r'^do\s+you\s+know',
]
DO_YOU_KNOW_COMPILED = [re.compile(p, re.IGNORECASE) for p in DO_YOU_KNOW_PATTERNS]


def _is_noise(text: str, block_type: str = "") -> bool:
    """Returns True if block should be filtered out."""
    text = text.strip()
    if not text:
        return True
    # Layout Parser detects footers — always skip
    if block_type in ("footer", "page-footer", "page-header"):
        return True
    if len(text) < 2:
        return True
    for pattern in NOISE_COMPILED:
        if pattern.match(text):
            return True
    return False


def _is_do_you_know(text: str) -> bool:
    """Detects if a block is the Do You Know heading."""
    text = text.strip()
    for pattern in DO_YOU_KNOW_COMPILED:
        if pattern.match(text):
            return True
    return False


def _normalize_text(text: str) -> str:
    """Clean and normalize block text."""
    # Fix broken hyphenation across lines
    text = re.sub(r'-\n(\w)', r'\1', text)
    # Normalize whitespace
    text = re.sub(r' {2,}', ' ', text)
    text = text.strip()
    return text


class GoogleDocAIExtractor:
    """
    Extracts clean structured text from PDF using Google Document AI Layout Parser.
    """

    def __init__(self):
        self._client      = None
        self._processor_name = None
        self._initialized = False

    def _initialize(self):
        """Lazy initialization."""
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
        output_txt: Path
    ) -> bool:
        """
        Extract clean text from PDF pages using Layout Parser.

        Args:
            pdf_file:   Path to full PDF
            start_page: First page (1-indexed)
            end_page:   Last page (1-indexed, inclusive)
            output_txt: Path to write extracted text

        Returns:
            True if successful, False if failed
        """
        self._initialize()
        if not self._initialized:
            return False

        try:
            print(f"   🔄 Document AI: extracting pages {start_page}→{end_page}...")

            # Slice PDF pages to bytes
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

            # Extract clean text from layout blocks
            clean_text = self._extract_from_layout(document)

            if not clean_text.strip():
                print(f"   ❌ No text extracted from Layout Parser")
                return False

            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(clean_text)

            print(f"   ✅ Document AI: {len(clean_text)} chars extracted")
            return True

        except Exception as e:
            print(f"   ❌ Document AI extraction failed: {e}")
            return False

    def _slice_pdf_to_bytes(
        self, pdf_file: Path, start_page: int, end_page: int
    ) -> Optional[bytes]:
        """Extract specific pages from PDF and return as bytes."""
        try:
            writer = PyPDF2.PdfWriter()
            with open(pdf_file, "rb") as f:
                reader    = PyPDF2.PdfReader(f)
                end_page  = min(end_page, len(reader.pages))
                for i in range(start_page - 1, end_page):
                    writer.add_page(reader.pages[i])
            output = io.BytesIO()
            writer.write(output)
            return output.getvalue()
        except Exception as e:
            print(f"   ❌ PDF slicing failed: {e}")
            return None

    def _extract_from_layout(self, document) -> str:
        """
        Extracts clean text from Layout Parser response.

        Uses document.document_layout.blocks which gives:
        - type=paragraph   → story content, definitions, info
        - type=heading-1   → section headings, exercise headings
        - type=heading-2   → sub-headings
        - type=footer      → PDF footers (auto-filtered)
        - type=table       → tables with structure
        - type=list-item   → list items
        """
        layout = document.document_layout
        if not layout or not layout.blocks:
            print(f"   ⚠️  No layout blocks found")
            return ""

        text_parts  = []
        in_dyk      = False   # tracking Do You Know content
        dyk_content = []

        for block in layout.blocks:
            text_block = block.text_block
            if not text_block:
                continue

            block_type = text_block.type_ or "paragraph"
            block_text = _normalize_text(text_block.text or "")

            # ── Skip noise and footers ────────────────────────────────────────
            if _is_noise(block_text, block_type):
                continue

            # ── Detect Do You Know heading ────────────────────────────────────
            if _is_do_you_know(block_text):
                in_dyk = True
                text_parts.append("Do You Know?")
                continue

            # ── Handle table blocks ───────────────────────────────────────────
            if block_type == "table":
                table_text = self._extract_table_text(text_block)
                if table_text:
                    text_parts.append(table_text)
                continue

            # ── Handle heading blocks ─────────────────────────────────────────
            if block_type in ("heading-1", "heading-2", "heading-3"):
                # Add heading text
                text_parts.append(block_text)

                # If heading has sub-blocks (like exercise A with questions)
                if text_block.blocks:
                    sub_texts = self._extract_sub_blocks(text_block.blocks)
                    text_parts.extend(sub_texts)
                continue

            # ── Regular paragraph ─────────────────────────────────────────────
            if block_text:
                text_parts.append(block_text)

        # Join all parts
        full_text = "\n\n".join(text_parts)
        full_text = re.sub(r'\n{3,}', '\n\n', full_text)
        return full_text.strip()

    def _extract_table_text(self, text_block) -> str:
        """Extract table content as structured text."""
        if not text_block.blocks:
            return _normalize_text(text_block.text or "")

        rows = []
        for row_block in text_block.blocks:
            row_text = _normalize_text(row_block.text_block.text or "")
            if row_text:
                rows.append(row_text)

        return "\n".join(rows) if rows else ""

    def _extract_sub_blocks(self, sub_blocks) -> list:
        """Extract text from sub-blocks inside a heading block."""
        texts = []
        for sub in sub_blocks:
            if not sub.text_block:
                continue
            sub_type = sub.text_block.type_ or ""
            sub_text = _normalize_text(sub.text_block.text or "")

            # Skip footers even in sub-blocks
            if _is_noise(sub_text, sub_type):
                continue

            if sub_text:
                texts.append(sub_text)

        return texts


# Singleton instance
docai_extractor = GoogleDocAIExtractor()