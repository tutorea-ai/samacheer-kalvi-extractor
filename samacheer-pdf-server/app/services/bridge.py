import json
import shutil
import os
from pathlib import Path
from ..config import settings

class ContentBridge:
    def __init__(self):
        # 1. Load the Map
        self.curriculum_path = settings.DATA_DIR / "curriculum.json"
        
        try:
            with open(self.curriculum_path, 'r') as f:
                self.curriculum = json.load(f)
        except FileNotFoundError:
            print(f"❌ Bridge Error: curriculum.json not found.")
            self.curriculum = {}

        # 2. Load Target Path
        target_root = settings.CONTENT_SERVER_PATH
        if not target_root:
            print("⚠️ Bridge Warning: CONTENT_SERVER_PATH is empty.")
            self.target_base = None
        else:
            self.target_base = Path(target_root).resolve()

    def deploy_content(self, source_file: Path, metadata: dict, fmt: str):
        """
        Moves the generated file to the correct Content Server location.
        """
        if not self.target_base or not self.curriculum:
            print("❌ Bridge Error: Configuration missing.")
            return False

        class_str = str(metadata['class_num'])
        unit_key = f"unit{metadata['unit']}"
        
        # Term Logic
        term_key = "term1"
        if int(class_str) < 8 and 'term' in metadata:
             term_key = f"term{metadata['term']}"

        # 3. Find the Lesson ID
        try:
            lesson_idx = metadata['lesson_choice'] - 1 
            
            if class_str not in self.curriculum:
                print(f"❌ Bridge Error: Class {class_str} not in curriculum.json")
                return False

            lesson_data = self.curriculum[class_str][term_key][unit_key][lesson_idx]
            lesson_id = lesson_data['id']
            print(f"🌉 Bridge: Mapped 'Unit {metadata['unit']} Lesson {metadata['lesson_choice']}' -> '{lesson_id}'")
        except (KeyError, IndexError) as e:
            print(f"❌ Bridge Error: Mapping failed: {e}")
            return False

        # === 🎯 FINAL DESTINATION LOGIC ===
        dest_folder = None

        if fmt == "md":
            # [MD Rule] All classes go deep into: backend/english/{class}/english/
            # This ensures we hit 'the_nose-jewel_prose.md'
            dest_folder = self.target_base / "backend" / "english" / class_str / "english"

        elif fmt == "html":
            if int(class_str) <= 7:
                # [HTML Rule 1] Class 6-7: backend/english/{class}/english-html/
                dest_folder = self.target_base / "backend" / "english" / class_str / "english-html"
            else:
                # [HTML Rule 2] Class 8-12: Root/{class}/english/
                dest_folder = self.target_base / class_str / "english"

        # 5. Deployment
        if dest_folder:
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            # This constructs "the_nose-jewel_prose.md"
            # It will NOT match "the_nose-jewel_prose_qa.md"
            target_filename = f"{lesson_id}.{fmt}"
            dest_path = dest_folder / target_filename

            try:
                shutil.copy2(source_file, dest_path)
                print(f"🚀 BRIDGE SUCCESS: Overwrote {dest_path}")
                return str(dest_path)
            except Exception as e:
                print(f"❌ Deployment Failed: {e}")
                return False
        
        return False

bridge = ContentBridge()