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

def run_specific_unit(target_class, target_unit):
    """
    Generates content ONLY for a specific Class and Unit.
    """
    data = load_curriculum()
    
    # 1. Validate Class Exists
    class_str = str(target_class)
    if class_str not in data:
        print(f"❌ Error: Class {target_class} not found in curriculum.")
        return

    class_data = data[class_str]
    print(f"🎯 TARGET LOCKED: Class {target_class} | Unit {target_unit}")

    found_unit = False

    # 2. Search for the Unit
    for term_key, term_data in class_data.items():
        # Handle Term Number (default 1)
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
            
            print(f"   👉 Found {len(lessons)} lessons in {term_key}/{unit_key}")

            # 3. Generate Every Lesson in this Unit
            for i, lesson in enumerate(lessons):
                lesson_choice = i + 1
                lesson_title = lesson.get('title', 'Unknown Lesson')
                
                print(f"      [{i+1}/{len(lessons)}] Generating: '{lesson_title}'...")

                payload = {
                    "class_num": int(target_class),
                    "subject": "english",
                    "term": term_num,
                    "mode": "lesson",
                    "unit": int(target_unit),
                    "lesson_choice": lesson_choice,
                    "output_format": "html"  # Will trigger Bingo (MD + HTML)
                }

                try:
                    start_time = time.time()
                    # 10 min timeout for safety
                    response = requests.post(API_URL, json=payload, timeout=600)
                    
                    if response.status_code == 200:
                        print(f"      ✅ Success! ({round(time.time() - start_time, 1)}s)")
                    else:
                        print(f"      ❌ Failed: {response.text}")
                
                except Exception as e:
                    print(f"      ⚠️ Connection Error: {e}")

                # Safety Sleep (3 seconds is enough for single unit work)
                if i < len(lessons) - 1:
                    print("      ⏳ Cooling down (3s)...")
                    time.sleep(3)
    
    if not found_unit:
        print(f"❌ Error: Unit {target_unit} not found in Class {target_class}.")
    else:
        print(f"\n✨ Mission Complete: Class {target_class} Unit {target_unit} is updated.")

if __name__ == "__main__":
    # ==========================================
    # 👇 CHANGE THESE NUMBERS TO WHAT YOU WANT
    # ==========================================
    MY_CLASS = 10
    MY_UNIT = 7
    
    run_specific_unit(MY_CLASS, MY_UNIT)