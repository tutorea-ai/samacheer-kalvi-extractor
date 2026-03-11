"""
Content Bridge
Deploys generated files (HTML + MD) to the correct locations
in the Node.js Content Server.

Destination structure (Node.js server):
─────────────────────────────────────────────────────────────
HTML Content → backend/data/languages/{subject}/{class}/content/{term}/{lessonId}/index.html
HTML QA      → backend/data/languages/{subject}/{class}/qa/{term}/{lessonId}/index.html
HTML LP      → backend/data/languages/{subject}/{class}/lp/{term}/{lessonId}/index.html

MD Content   → backend/data/languages/{subject}/md-files/{class}/{lessonId}.md
MD QA        → backend/data/languages/{subject}/md-files/{class}/{lessonId}_qa.md
MD LP        → backend/data/languages/{subject}/md-files/{class}/{lessonId}_lp.md

NOTE: Social Science (subjects/english-medium/social-science/...) path logic
      is stubbed below — implement when English is complete.
─────────────────────────────────────────────────────────────
"""

import json
import shutil
from pathlib import Path
from ..config import settings

# Language subjects — use languages/ folder
LANGUAGE_SUBJECTS = ["english", "tamil"]


class ContentBridge:

    def __init__(self):
        # ── Load Node server target root ──────────────────────────────────────
        target_root = settings.CONTENT_SERVER_PATH
        if not target_root:
            print("⚠️  Bridge Warning: CONTENT_SERVER_PATH is not set in .env")
            self.target_base = None
        else:
            self.target_base = Path(target_root).resolve()
            print(f"🌉 Bridge initialized → {self.target_base}")

        # ── Load curriculum (Node server version — sanitized IDs) ─────────────
        # IMPORTANT: We use the Node server's curriculum.json to resolve
        # lesson IDs because it has sanitized IDs (no hyphens/apostrophes).
        # This must match exactly what api.js uses.
        self.curriculum = self._load_curriculum()

    def _load_curriculum(self) -> dict:
        """Load curriculum from the PDF extractor's data directory."""
        curriculum_path = settings.get_curriculum_path("english")
        try:
            with open(curriculum_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"✅ Bridge curriculum loaded: {curriculum_path}")
            return data
        except FileNotFoundError:
            print(f"❌ Bridge Error: curriculum not found at {curriculum_path}")
            return {}
        except Exception as e:
            print(f"❌ Bridge Error loading curriculum: {e}")
            return {}

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC: Deploy a single file to the Node server
    # ──────────────────────────────────────────────────────────────────────────

    def deploy_content(self, source_file: Path, metadata: dict, fmt: str, file_type: str = "content") -> str | bool:
        """
        Copies a generated file to the correct Node.js server location.

        Args:
            source_file: Path to the generated file (in temp/)
            metadata: {
                'class_num': int,
                'term': int,
                'unit': int,
                'lesson_choice': int,
                'subject': str,
                'medium': str,
                'discipline': str (optional, for social science)
            }
            fmt: "html" or "md"
            file_type: "content" | "qa" | "lp"

        Returns:
            Destination path string if successful, False otherwise.
        """
        if not self.target_base:
            print("❌ Bridge Error: CONTENT_SERVER_PATH not configured.")
            return False

        if not self.curriculum:
            print("❌ Bridge Error: Curriculum not loaded.")
            return False

        # ── Resolve lesson ID ─────────────────────────────────────────────────
        lesson_id = self._resolve_lesson_id(metadata)
        if not lesson_id:
            return False

        # ── Build destination path ────────────────────────────────────────────
        dest_path = self._build_dest_path(metadata, lesson_id, fmt, file_type)
        if not dest_path:
            return False

        # ── Copy file ─────────────────────────────────────────────────────────
        return self._copy_file(source_file, dest_path, lesson_id, file_type)

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Resolve lesson ID from curriculum
    # ──────────────────────────────────────────────────────────────────────────

    def _resolve_lesson_id(self, metadata: dict) -> str | None:
        """
        Maps (class, term, unit, lesson_choice) → lesson_id string.
        e.g. class=8, term=0, unit=1, lesson_choice=1 → 'the_nose_jewel_prose'
        """
        class_str = str(metadata["class_num"])
        unit_key = f"unit{metadata['unit']}"
        lesson_idx = metadata["lesson_choice"] - 1

        # Build term key
        class_num = int(class_str)
        if class_num >= 8:
            term_key = "term0"
        else:
            term_key = f"term{metadata.get('term', 1)}"

        try:
            if class_str not in self.curriculum:
                print(f"❌ Bridge: Class '{class_str}' not in curriculum")
                return None

            term_data = self.curriculum[class_str].get(term_key)
            if not term_data:
                print(f"❌ Bridge: '{term_key}' not found for class {class_str}")
                return None

            unit_lessons = term_data.get(unit_key)
            if not unit_lessons:
                print(f"❌ Bridge: '{unit_key}' not found in {term_key}")
                return None

            lesson_data = unit_lessons[lesson_idx]
            lesson_id = lesson_data["id"]
            print(f"🌉 Bridge: Resolved → '{lesson_id}'")
            return lesson_id

        except (KeyError, IndexError) as e:
            print(f"❌ Bridge: Lesson ID resolution failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Build destination path
    # ──────────────────────────────────────────────────────────────────────────

    def _build_dest_path(self, metadata: dict, lesson_id: str, fmt: str, file_type: str) -> Path | None:
        """
        Constructs the full destination path for the file.

        HTML paths:
          content → backend/data/languages/english/{class}/content/{term}/{lessonId}/index.html
          qa      → backend/data/languages/english/{class}/qa/{term}/{lessonId}/index.html
          lp      → backend/data/languages/english/{class}/lp/{term}/{lessonId}/index.html

        MD paths:
          content → backend/data/languages/english/md-files/{class}/{lessonId}.md
          qa      → backend/data/languages/english/md-files/{class}/{lessonId}_qa.md
          lp      → backend/data/languages/english/md-files/{class}/{lessonId}_lp.md
        """
        class_str = str(metadata["class_num"])
        subject = metadata.get("subject", "english").lower()
        class_num = int(class_str)

        # Build term folder string
        if class_num >= 8:
            term_folder = "term0"
        else:
            term_folder = f"term{metadata.get('term', 1)}"

        # ── HTML paths ────────────────────────────────────────────────────────
        if fmt == "html":
            if subject in LANGUAGE_SUBJECTS:
                base = self.target_base / "backend" / "data" / "languages" / subject / class_str

                if file_type == "content":
                    folder = base / "content" / term_folder / lesson_id
                elif file_type == "qa":
                    folder = base / "qa" / term_folder / lesson_id
                elif file_type == "lp":
                    folder = base / "lp" / term_folder / lesson_id
                else:
                    print(f"❌ Bridge: Unknown file_type '{file_type}'")
                    return None

                return folder / "index.html"

            else:
                # TODO: Implement social science / other subject paths here
                # Pattern: backend/data/subjects/english-medium/{subject}/{class}/{type}/{term}/{lessonId}/index.html
                print(f"⚠️  Bridge: Subject '{subject}' path not yet implemented. English only for now.")
                return None

        # ── MD paths ──────────────────────────────────────────────────────────
        elif fmt == "md":
            if subject in LANGUAGE_SUBJECTS:
                md_base = self.target_base / "backend" / "data" / "languages" / subject / "md-files" / class_str

                if file_type == "content":
                    return md_base / f"{lesson_id}.md"
                elif file_type == "qa":
                    return md_base / f"{lesson_id}_qa.md"
                elif file_type == "lp":
                    return md_base / f"{lesson_id}_lp.md"
                else:
                    print(f"❌ Bridge: Unknown file_type '{file_type}'")
                    return None

            else:
                # TODO: MD paths for other subjects
                print(f"⚠️  Bridge: MD path for subject '{subject}' not yet implemented.")
                return None

        else:
            print(f"❌ Bridge: Unknown format '{fmt}'")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Copy file to destination
    # ──────────────────────────────────────────────────────────────────────────

    def _copy_file(self, source_file: Path, dest_path: Path, lesson_id: str, file_type: str) -> str | bool:
        """Creates destination folder and copies file."""
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, dest_path)
            print(f"🚀 Bridge SUCCESS [{file_type.upper()}]: {dest_path}")
            return str(dest_path)
        except Exception as e:
            print(f"❌ Bridge FAILED [{file_type.upper()}] → {dest_path}: {e}")
            return False


# Singleton instance
bridge = ContentBridge()