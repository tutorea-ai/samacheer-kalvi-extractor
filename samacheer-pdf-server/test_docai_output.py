"""
Test script to see raw Document AI output for a Samacheer Kalvi PDF.
Run this BEFORE writing google_docai.py so we understand the structure.

Usage:
    python3 test_docai_output.py <path_to_pdf> <start_page> <end_page>

Example:
    python3 test_docai_output.py storage/cache/class-10-term0-english.pdf 25 28
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

credentials  = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
project_id   = os.getenv("DOCAI_PROJECT_ID")
location     = os.getenv("DOCAI_LOCATION")
processor_id = os.getenv("DOCAI_PROCESSOR_ID")

# Make credentials absolute
base_dir = Path(__file__).parent
credentials_abs = str(base_dir / credentials)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_abs

from google.cloud import documentai
import PyPDF2

def extract_pages_to_bytes(pdf_path: str, start_page: int, end_page: int) -> bytes:
    """Extract specific pages from PDF and return as bytes."""
    writer = PyPDF2.PdfWriter()
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for i in range(start_page - 1, min(end_page, len(reader.pages))):
            writer.add_page(reader.pages[i])

    import io
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_docai(pdf_path: str, start_page: int, end_page: int):
    print(f"🔄 Sending pages {start_page}-{end_page} to Document AI...")

    # Extract pages
    pdf_bytes = extract_pages_to_bytes(pdf_path, start_page, end_page)
    print(f"   PDF size: {len(pdf_bytes)} bytes")

    # Call Document AI
    client = documentai.DocumentProcessorServiceClient()
    processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"

    raw_document = documentai.RawDocument(
        content=pdf_bytes,
        mime_type="application/pdf"
    )

    request = documentai.ProcessRequest(
        name=processor_name,
        raw_document=raw_document
    )

    result = client.process_document(request=request)
    document = result.document

    print(f"✅ Document AI response received!")
    print(f"   Total pages: {len(document.pages)}")
    print(f"   Full text length: {len(document.text)} chars")
    print()

    # Show full extracted text
    print("=" * 60)
    print("FULL EXTRACTED TEXT:")
    print("=" * 60)
    print(document.text[:3000])
    print()

    # Show page structure
    print("=" * 60)
    print("PAGE STRUCTURE:")
    print("=" * 60)
    for page_num, page in enumerate(document.pages, 1):
        print(f"\n--- Page {page_num} ---")
        print(f"  Blocks: {len(page.blocks)}")
        print(f"  Paragraphs: {len(page.paragraphs)}")
        print(f"  Lines: {len(page.lines)}")
        print(f"  Tokens: {len(page.tokens)}")

        if page.tables:
            print(f"  Tables: {len(page.tables)}")
            for t_idx, table in enumerate(page.tables):
                print(f"    Table {t_idx+1}: {len(table.header_rows)} header rows, {len(table.body_rows)} body rows")

        # Show first 3 blocks with their text
        print(f"  First blocks:")
        for b_idx, block in enumerate(page.blocks[:5]):
            block_text = get_text(document.text, block.layout)
            print(f"    Block {b_idx+1}: {repr(block_text[:80])}")

    # Save full response for inspection
    output_file = "docai_test_output.txt"
    with open(output_file, "w") as f:
        f.write("FULL TEXT:\n")
        f.write(document.text)
        f.write("\n\n")
        f.write("BLOCKS PER PAGE:\n")
        for page_num, page in enumerate(document.pages, 1):
            f.write(f"\n=== Page {page_num} ===\n")
            for b_idx, block in enumerate(page.blocks):
                block_text = get_text(document.text, block.layout)
                f.write(f"Block {b_idx+1}: {block_text}\n")
                f.write("-" * 40 + "\n")

    print(f"\n✅ Full output saved to: {output_file}")


def get_text(full_text: str, layout) -> str:
    """Extract text from a layout element using text anchors."""
    text = ""
    for segment in layout.text_anchor.text_segments:
        start = int(segment.start_index) if segment.start_index else 0
        end   = int(segment.end_index)
        text += full_text[start:end]
    return text.strip()


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 test_docai_output.py <pdf_path> <start_page> <end_page>")
        print("Example: python3 test_docai_output.py storage/cache/class-10-term0-english.pdf 25 28")
        sys.exit(1)

    pdf_path   = sys.argv[1]
    start_page = int(sys.argv[2])
    end_page   = int(sys.argv[3])

    test_docai(pdf_path, start_page, end_page)