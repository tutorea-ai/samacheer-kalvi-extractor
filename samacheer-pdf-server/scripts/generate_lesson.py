import requests
import time
import json
import sys
from pathlib import Path

# === CONFIGURATION ===
API_URL = "http://localhost:8000/api/generate"
# Path to your curriculum file
CURRICULUM_PATH = Path(__file__).parent.parent / "data" / "curriculum.json"

def load_curriculum():
    if not CURRICULUM_PATH.exists():
        print(f"❌ Error: Could not find {CURRICULUM_PATH}")
        return {}
    with open(CURRICULUM_PATH, 'r') as f:
        return json.load(f)

def run_specific_lesson(target_class, target_unit, target_lesson):
    """
    Generates content ONLY for a specific Class, Unit, AND Lesson.
    """
    data = load_curriculum()
    
    # 1. Validate Class Exists
    class_str = str(target_class)
    if class_str not in data:
        print(f"❌ Error: Class {target_class} not found in curriculum.")
        return

    class_data = data[class_str]
    print(f"🎯 TARGET LOCKED: Class {target_class} | Unit {target_unit} | Lesson {target_lesson}")

    found_unit = False
    found_lesson = False

    # 2. Search for the Unit
    for term_key, term_data in class_data.items():
        # Handle Term Number
        term_num = 1
        if "term" in term_key:
            try:
                term_num = int(term_key.replace("term", ""))
            except:
                term_num = 1

        # Check if our target unit is in this term
        unit_key = f"unit{target_unit}"
        
        if unit_key in term_data:
            found_unit = True
            lessons = term_data[unit_key]
            
            # 3. Search for the specific Lesson
            if target_lesson > len(lessons):
                 print(f"❌ Error: Unit {target_unit} only has {len(lessons)} lessons. You asked for Lesson {target_lesson}.")
                 return

            # Get the specific lesson (Index is number - 1)
            lesson_index = target_lesson - 1
            lesson = lessons[lesson_index]
            lesson_title = lesson.get('title', 'Unknown Lesson')
            
            found_lesson = True
            print(f"   👉 Found Lesson: '{lesson_title}'")
            print(f"      Generating now...")

            payload = {
                "class_num": int(target_class),
                "subject": "english",
                "term": term_num,
                "mode": "lesson",
                "unit": int(target_unit),
                "lesson_choice": int(target_lesson),
                "output_format": "html"  # Will trigger Bingo (MD + HTML)
            }

            try:
                start_time = time.time()
                # 10 min timeout
                response = requests.post(API_URL, json=payload, timeout=600)
                
                if response.status_code == 200:
                    print(f"      ✅ Success! ({round(time.time() - start_time, 1)}s)")
                else:
                    print(f"      ❌ Failed: {response.text}")
            
            except Exception as e:
                print(f"      ⚠️ Connection Error: {e}")

            # Break after finding and running the specific lesson
            break
    
    if not found_unit:
        print(f"❌ Error: Unit {target_unit} not found in Class {target_class}.")
    elif not found_lesson:
        print(f"❌ Error: Could not find Lesson {target_lesson} (Unknown error).")
    else:
        print(f"\n✨ Mission Complete.")

if __name__ == "__main__":
    # ==========================================
    # 👇 CHANGE THESE 3 NUMBERS
    # ==========================================
    MY_CLASS = 9
    MY_UNIT = 4
    MY_LESSON = 3
    
    run_specific_lesson(MY_CLASS, MY_UNIT, MY_LESSON)