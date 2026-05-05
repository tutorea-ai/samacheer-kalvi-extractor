"""
epub_extractor.py
-----------------
English EPUB extractor for SK-CAP.
Now uses EpubPreprocessor — clean, simple, reliable.

Usage:
    extractor = EpubExtractor(epub_dir)
    text = extractor.extract(unit=2, lesson_type='prose')
    text = extractor.extract(unit=2, lesson_type='poem')
    text = extractor.extract(unit=2, lesson_type='supplementary')

Returns:
    str  — clean plain text ready to send to Claude
    None — if lesson not found
"""

import zipfile
from pathlib import Path
from .epub_preprocessor import EpubPreprocessor


class EpubExtractor:

    def __init__(self, epub_dir: Path):
        self.epub_dir    = Path(epub_dir)
        self.preprocessor = EpubPreprocessor(self.epub_dir)

    def extract(self, unit: int, lesson_type: str) -> str | None:
        """
        Extract clean text for the given unit and lesson type.

        Args:
            unit:        unit number (1-based)
            lesson_type: 'prose', 'poem', or 'supplementary'

        Returns:
            Clean plain text string, or None if not found.
        """
        lesson_type = lesson_type.lower().strip()

        # Normalize lesson type
        if 'supplementary' in lesson_type:
            lesson_type = 'supplementary'

        # Ensure preprocessed
        if not self.preprocessor.combined_tagged_path.exists():
            print(f"[EpubExtractor] Preprocessing {self.epub_dir.name}...")
            success = self.preprocessor.prepare()
            if not success:
                print(f"[EpubExtractor] ❌ Preprocessing failed")
                return None

        return self.preprocessor.extract(lesson_type, unit)

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

    epub_zip = sys.argv[1] if len(sys.argv) > 1 else 'class-10-term0-english.zip'
    epub_dir = EpubExtractor.prepare(Path(epub_zip))

    if not epub_dir:
        print("❌ Could not prepare EPUB")
        sys.exit(1)

    extractor = EpubExtractor(epub_dir)

    test_cases = [
        (1, 'prose'), (1, 'poem'), (1, 'supplementary'),
        (2, 'prose'), (2, 'poem'), (2, 'supplementary'),
        (6, 'prose'), (7, 'supplementary'),
    ]

    for unit, lesson_type in test_cases:
        text = extractor.extract(unit=unit, lesson_type=lesson_type)
        if text:
            print(f"✅ Unit {unit} {lesson_type}: {len(text):6} chars — {text[:60]}...")
        else:
            print(f"❌ Unit {unit} {lesson_type}: FAILED")