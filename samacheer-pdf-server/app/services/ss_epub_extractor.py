"""
ss_epub_extractor.py
--------------------
Social Science EPUB extractor for SK-CAP.
Now uses EpubPreprocessor — clean, simple, reliable.

Handles History, Geography, Civics, Economics disciplines.

Usage:
    extractor = SocialScienceEpubExtractor(epub_dir)
    text = extractor.extract(discipline='history', unit=1)
    text = extractor.extract(discipline='geography', unit=2)
    text = extractor.extract(discipline='civics', unit=1)
    text = extractor.extract(discipline='economics', unit=3)

Returns:
    str  — clean plain text ready to send to Claude
    None — if chapter not found
"""

import zipfile
from pathlib import Path
from .epub_preprocessor import EpubPreprocessor


class SocialScienceEpubExtractor:

    def __init__(self, epub_dir: Path):
        epub_dir = Path(epub_dir)

        # Handle double-nested EPUBs — some ZIPs unzip into a subfolder
        if not (epub_dir / 'nav.xhtml').exists():
            # Look for nav.xhtml one level deeper
            nested = epub_dir / epub_dir.name
            if nested.exists() and (nested / 'nav.xhtml').exists():
                epub_dir = nested
            else:
                # Try any subdirectory that has nav.xhtml
                for subdir in epub_dir.iterdir():
                    if subdir.is_dir() and (subdir / 'nav.xhtml').exists():
                        epub_dir = subdir
                        break

        self.epub_dir     = epub_dir
        self.preprocessor = EpubPreprocessor(self.epub_dir)

    def extract(self, discipline: str, unit: int) -> str | None:
        """
        Extract clean text for the given discipline and unit.

        Args:
            discipline: 'history', 'geography', 'civics', 'economics'
            unit:       unit number (1-based)

        Returns:
            Clean plain text string, or None if not found.
        """
        discipline = discipline.lower().strip()

        # Ensure preprocessed
        if not self.preprocessor.combined_tagged_path.exists():
            print(f"[SSEpubExtractor] Preprocessing {self.epub_dir.name}...")
            success = self.preprocessor.prepare()
            if not success:
                print(f"[SSEpubExtractor] ❌ Preprocessing failed")
                return None

        text = self.preprocessor.extract(discipline, unit)

        if text is None:
            print(f"[SSEpubExtractor] ❌ {discipline} Unit {unit} not found — fallback to pdfplumber")

        return text

    @staticmethod
    def prepare(epub_zip_path: Path) -> Path | None:
        """
        Unzip EPUB and run preprocessing.
        Returns path to unzipped folder, or None on failure.
        """
        epub_dir = EpubPreprocessor.prepare_zip(Path(epub_zip_path))
        if not epub_dir:
            return None

        # Run preprocessing (skips if already done)
        preprocessor = EpubPreprocessor(epub_dir)
        preprocessor.prepare()

        return epub_dir


# ── Quick test ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    epub_zip = sys.argv[1] if len(sys.argv) > 1 else 'class-10-term0-socialscience.zip'
    epub_dir = SocialScienceEpubExtractor.prepare(Path(epub_zip))

    if not epub_dir:
        print("❌ Could not prepare EPUB")
        sys.exit(1)

    extractor = SocialScienceEpubExtractor(epub_dir)

    test_cases = [
        ('history',   1), ('history',   2), ('history',   3), ('history',  10),
        ('geography', 1), ('geography', 4), ('geography', 5), ('geography', 7),
        ('civics',    1), ('civics',    5),
        ('economics', 1), ('economics', 5),
    ]

    for discipline, unit in test_cases:
        text = extractor.extract(discipline=discipline, unit=unit)
        if text:
            print(f"✅ {discipline:12} Unit {unit:2}: {len(text):6} chars — {text[:60]}...")
        else:
            print(f"❌ {discipline:12} Unit {unit:2}: not found — fallback to pdfplumber")