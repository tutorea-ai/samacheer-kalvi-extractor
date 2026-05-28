"""
science_epub_extractor.py
-------------------------
Science EPUB extractor for SK-CAP.
Uses EpubPreprocessor — same pattern as SocialScienceEpubExtractor.

Handles Physics, Chemistry, Biology, Computer Science disciplines.
Unit numbers are GLOBAL per class (not per discipline):
  Class 10: Physics=1-6, Chemistry=7-11, Biology=12-22, CS=23

Usage:
    extractor = ScienceEpubExtractor(epub_dir)
    text = extractor.extract(unit=1)   # Physics Unit 1
    text = extractor.extract(unit=7)   # Chemistry Unit 7
    text = extractor.extract(unit=12)  # Biology Unit 12

Returns:
    str  — clean plain text ready to send to Claude
    None — if chapter not found
"""

from pathlib import Path
from .epub_preprocessor import EpubPreprocessor


class ScienceEpubExtractor:

    def __init__(self, epub_dir: Path):
        epub_dir = Path(epub_dir)

        # Handle double-nested EPUBs
        if not (epub_dir / 'nav.xhtml').exists():
            nested = epub_dir / epub_dir.name
            if nested.exists() and (nested / 'nav.xhtml').exists():
                epub_dir = nested
            else:
                for subdir in epub_dir.iterdir():
                    if subdir.is_dir() and (subdir / 'nav.xhtml').exists():
                        epub_dir = subdir
                        break

        self.epub_dir     = epub_dir
        self.preprocessor = EpubPreprocessor(self.epub_dir)

    def extract(self, unit: int) -> str | None:
        """
        Extract clean text for the given unit number.

        Args:
            unit: global unit number (1-based, continuous across disciplines)

        Returns:
            Clean plain text string, or None if not found.
        """
        # Ensure preprocessed
        if not self.preprocessor.combined_tagged_path.exists():
            print(f"[ScienceEpubExtractor] Preprocessing {self.epub_dir.name}...")
            success = self.preprocessor.prepare()
            if not success:
                print(f"[ScienceEpubExtractor] ❌ Preprocessing failed")
                return None

        text = self.preprocessor.extract("unit", unit)

        if text is None:
            print(f"[ScienceEpubExtractor] ❌ Unit {unit} not found — fallback to pdfplumber")

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

        preprocessor = EpubPreprocessor(epub_dir)
        preprocessor.prepare()

        return epub_dir
