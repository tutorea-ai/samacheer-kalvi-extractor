"""
Content Bridge
Deploys generated files (HTML + MD) to the correct locations
in the Node.js Content Server.

Destination structure (Node.js server):

ENGLISH (Language subject):
  HTML → backend/data/languages/english/{class}/content/{term}/{lessonId}/index.html
  HTML → backend/data/languages/english/{class}/qa/{term}/{lessonId}/index.html
  HTML → backend/data/languages/english/{class}/lp/{term}/{lessonId}/index.html
  MD   → backend/data/languages/english/md-files/{class}/{lessonId}.md

SOCIAL SCIENCE (Subject):
  HTML → backend/data/subjects/english-medium/social_science/{class}/content/{term}/{discipline}/{lessonId}/index.html
  HTML → backend/data/subjects/english-medium/social_science/{class}/qa/{term}/{discipline}/{lessonId}/index.html
  HTML → backend/data/subjects/english-medium/social_science/{class}/lp/{term}/{discipline}/{lessonId}/index.html

FIX APPLIED (April 2026):
  - Social Science path fully implemented
  - SS curriculum loaded separately from English curriculum
  - _resolve_lesson_id() handles both English and Social Science
  - _is_already_deployed() handles both path structures
"""

import json
import shutil
from pathlib import Path
from ..config import settings

# Language subjects — use languages/ folder
LANGUAGE_SUBJECTS = ["english", "tamil"]

# Social Science subject names (various casings from API)
SOCIAL_SCIENCE_NAMES = ["socialscience", "social_science", "social science", "ss"]


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

        # ── Load English curriculum ───────────────────────────────────────────
        self.curriculum = self._load_curriculum("english")

        # ── Load Social Science curriculum ────────────────────────────────────
        self.ss_curriculum = self._load_ss_curriculum()

    def _load_curriculum(self, subject: str) -> dict:
        """Load English curriculum from the PDF extractor's data directory."""
        curriculum_path = settings.get_curriculum_path(subject)
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

    def _load_ss_curriculum(self) -> dict:
        """Load Social Science curriculum JSON."""
        try:
            ss_curriculum_path = settings.get_curriculum_path("socialscience")
            with open(ss_curriculum_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"✅ Bridge SS curriculum loaded: {ss_curriculum_path}")
            return data
        except FileNotFoundError:
            # Try alternate path
            try:
                alt_path = settings.BASE_DIR / "data" / "curriculum" / "subjects" / "english-medium" / "social-science.json"
                with open(alt_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"✅ Bridge SS curriculum loaded (alt): {alt_path}")
                return data
            except Exception:
                print(f"⚠️  Bridge: SS curriculum not found — SS deployment will fail")
                return {}
        except Exception as e:
            print(f"❌ Bridge Error loading SS curriculum: {e}")
            return {}

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC: Deploy a single file to the Node server
    # ──────────────────────────────────────────────────────────────────────────

    def deploy_content(self, source_file: Path, metadata: dict,
                       fmt: str, file_type: str = "content") -> str | bool:
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
                'discipline': str (required for social science)
            }
            fmt: "html" or "md"
            file_type: "content" | "qa" | "lp"

        Returns:
            Destination path string if successful, False otherwise.
        """
        if not self.target_base:
            print("❌ Bridge Error: CONTENT_SERVER_PATH not configured.")
            return False

        subject = metadata.get("subject", "english").lower().strip()

        # ── Route to correct resolver ─────────────────────────────────────────
        if subject in SOCIAL_SCIENCE_NAMES:
            lesson_id = self._resolve_ss_lesson_id(metadata)
        else:
            if not self.curriculum:
                print("❌ Bridge Error: Curriculum not loaded.")
                return False
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
    # PUBLIC: Check if lesson is already fully deployed
    # ──────────────────────────────────────────────────────────────────────────

    def is_already_deployed(self, metadata: dict) -> bool:
        """
        Checks if Content + QA + LP are already deployed for a lesson.
        Returns True only if all 3 HTML files exist AND are > 10KB.
        """
        if not self.target_base:
            return False

        subject = metadata.get("subject", "english").lower().strip()

        if subject in SOCIAL_SCIENCE_NAMES:
            return self._is_ss_deployed(metadata)
        else:
            return self._is_english_deployed(metadata)

    def _is_english_deployed(self, metadata: dict) -> bool:
        """Check deployment status for English lessons."""
        lesson_id = self._resolve_lesson_id(metadata)
        if not lesson_id:
            return False

        class_str  = str(metadata["class_num"])
        class_num  = int(class_str)
        term_folder = "term0" if class_num >= 8 else f"term{metadata.get('term', 1)}"

        base = self.target_base / "backend" / "data" / "languages" / "english" / class_str

        content_path = base / "content" / term_folder / lesson_id / "index.html"
        qa_path      = base / "qa"      / term_folder / lesson_id / "index.html"
        lp_path      = base / "lp"      / term_folder / lesson_id / "index.html"

        print(f"   🔍 Checking content : {content_path} → {'✅' if content_path.exists() else '❌'}")
        print(f"   🔍 Checking qa      : {qa_path} → {'✅' if qa_path.exists() else '❌'}")
        print(f"   🔍 Checking lp      : {lp_path} → {'✅' if lp_path.exists() else '❌'}")

        def _is_valid(path: Path) -> bool:
            index_file = path if path.name == "index.html" else path / "index.html"
            return index_file.exists() and index_file.stat().st_size > 10240

        missing = [
            t for t, p in [("content", content_path), ("qa", qa_path), ("lp", lp_path)]
            if not _is_valid(p)
        ]

        if missing:
            print(f"🔄  Bridge: '{lesson_id}' missing/invalid → {missing}")
            return False
        else:
            print(f"⏭️  Bridge: '{lesson_id}' already fully deployed — skipping")
            return True

    def _is_ss_deployed(self, metadata: dict) -> bool:
        """Check deployment status for Social Science lessons."""
        lesson_id  = self._resolve_ss_lesson_id(metadata)
        if not lesson_id:
            return False

        class_str   = str(metadata["class_num"])
        class_num   = int(class_str)
        discipline  = metadata.get("discipline", "history").lower()
        term_folder = "term0" if class_num >= 8 else f"term{metadata.get('term', 1)}"

        base = (self.target_base / "backend" / "data" / "subjects" /
                "english-medium" / "social-science" / class_str)

        content_path = base / "content" / term_folder / discipline / lesson_id / "index.html"
        qa_path      = base / "qa"      / term_folder / discipline / lesson_id / "index.html"
        lp_path      = base / "lp"      / term_folder / discipline / lesson_id / "index.html"

        print(f"   🔍 Checking content : {content_path} → {'✅' if content_path.exists() else '❌'}")
        print(f"   🔍 Checking qa      : {qa_path} → {'✅' if qa_path.exists() else '❌'}")
        print(f"   🔍 Checking lp      : {lp_path} → {'✅' if lp_path.exists() else '❌'}")

        def _is_valid(path: Path) -> bool:
            index_file = path if path.name == "index.html" else path / "index.html"
            return index_file.exists() and index_file.stat().st_size > 10240

        missing = [
            t for t, p in [("content", content_path), ("qa", qa_path), ("lp", lp_path)]
            if not _is_valid(p)
        ]

        if missing:
            print(f"🔄  Bridge: '{lesson_id}' missing/invalid → {missing}")
            return False
        else:
            print(f"⏭️  Bridge: '{lesson_id}' already fully deployed — skipping")
            return True

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Resolve lesson ID — English
    # ──────────────────────────────────────────────────────────────────────────

    def _resolve_lesson_id(self, metadata: dict) -> str | None:
        """
        Maps (class, term, unit, lesson_choice) → lesson_id for English.
        e.g. class=10, unit=2, lesson_choice=1 → 'the_night_the_ghost_got_in_prose'
        """
        class_str   = str(metadata["class_num"])
        unit_key    = f"unit{metadata['unit']}"
        lesson_idx  = metadata["lesson_choice"] - 1
        class_num   = int(class_str)
        term_key    = "term0" if class_num >= 8 else f"term{metadata.get('term', 1)}"

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
            lesson_id   = lesson_data["id"]
            print(f"🌉 Bridge: Resolved → '{lesson_id}'")
            return lesson_id

        except (KeyError, IndexError) as e:
            print(f"❌ Bridge: Lesson ID resolution failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Resolve lesson ID — Social Science
    # ──────────────────────────────────────────────────────────────────────────

    def _resolve_ss_lesson_id(self, metadata: dict) -> str | None:
        """
        Maps (class, term, discipline, unit) → lesson_id for Social Science.
        e.g. class=10, discipline=history, unit=1
             → 'outbreak_of_world_war_i_and_its_aftermath_history'
        """
        class_str  = str(metadata["class_num"])
        discipline = metadata.get("discipline", "history").lower().strip()
        unit_num   = metadata.get("unit", 1)
        class_num  = int(class_str)
        term_key   = "term0" if class_num >= 8 else f"term{metadata.get('term', 1)}"

        try:
            if class_str not in self.ss_curriculum:
                print(f"❌ Bridge SS: Class '{class_str}' not in SS curriculum")
                return None

            term_data = self.ss_curriculum[class_str].get(term_key)
            if not term_data:
                print(f"❌ Bridge SS: '{term_key}' not found for class {class_str}")
                return None

            disc_lessons = term_data.get(discipline)
            if not disc_lessons:
                print(f"❌ Bridge SS: Discipline '{discipline}' not found in {term_key}")
                return None

            # Find lesson by unit number
            lesson_data = next(
                (l for l in disc_lessons if l.get("unit") == unit_num),
                None
            )
            if not lesson_data:
                print(f"❌ Bridge SS: Unit {unit_num} not found in {discipline}")
                return None

            lesson_id = lesson_data["id"]
            print(f"🌉 Bridge: Resolved → '{lesson_id}'")
            return lesson_id

        except Exception as e:
            print(f"❌ Bridge SS: Lesson ID resolution failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Build destination path
    # ──────────────────────────────────────────────────────────────────────────

    def _build_dest_path(self, metadata: dict, lesson_id: str,
                         fmt: str, file_type: str) -> Path | None:
        """
        Constructs the full destination path for the file.
        Routes to English or Social Science path based on subject.
        """
        subject   = metadata.get("subject", "english").lower().strip()
        class_str = str(metadata["class_num"])
        class_num = int(class_str)
        term_folder = "term0" if class_num >= 8 else f"term{metadata.get('term', 1)}"

        # ── Social Science paths ──────────────────────────────────────────────
        if subject in SOCIAL_SCIENCE_NAMES:
            discipline = metadata.get("discipline", "history").lower()
            base = (self.target_base / "backend" / "data" / "subjects" /
                    "english-medium" / "social-science" / class_str)

            if fmt == "html":
                if file_type == "content":
                    folder = base / "content" / term_folder / discipline / lesson_id
                elif file_type == "qa":
                    folder = base / "qa" / term_folder / discipline / lesson_id
                elif file_type == "lp":
                    folder = base / "lp" / term_folder / discipline / lesson_id
                else:
                    print(f"❌ Bridge: Unknown file_type '{file_type}'")
                    return None
                return folder / "index.html"

            elif fmt == "md":
                if file_type == "content":
                    md_base = (self.target_base / "backend" / "data" / "subjects" /
                               "english-medium" / "social-science" /
                               "md-files" / class_str / discipline)
                    return md_base / f"{lesson_id}.md"
                else:
                    print(f"ℹ️  Bridge: MD skipped for file_type '{file_type}'")
                    return None

            else:
                print(f"❌ Bridge: Unknown format '{fmt}'")
                return None

        # ── English (Language subject) paths ──────────────────────────────────
        elif subject in LANGUAGE_SUBJECTS:
            base = self.target_base / "backend" / "data" / "languages" / subject / class_str

            if fmt == "html":
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

            elif fmt == "md":
                if file_type == "content":
                    md_base = (self.target_base / "backend" / "data" /
                               "languages" / subject / "md-files" / class_str)
                    return md_base / f"{lesson_id}.md"
                else:
                    print(f"ℹ️  Bridge: MD skipped for file_type '{file_type}'")
                    return None

            else:
                print(f"❌ Bridge: Unknown format '{fmt}'")
                return None

        else:
            print(f"⚠️  Bridge: Subject '{subject}' path not yet implemented.")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Copy file to destination
    # ──────────────────────────────────────────────────────────────────────────

    def _copy_file(self, source_file: Path, dest_path: Path,
                   lesson_id: str, file_type: str) -> str | bool:
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