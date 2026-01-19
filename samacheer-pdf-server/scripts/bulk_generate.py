import requests
import time
import json
import os
from pathlib import Path

# === CONFIGURATION ===
API_URL = "http://localhost:8000/api/generate"
# Adjust path to find curriculum.json relative to this script
CURRICULUM_PATH = Path(__file__).parent.parent / "data" / "curriculum.json"

def load_curriculum():
    if not CURRICULUM_PATH.exists():
        print(f"❌ Error: Could not find {CURRICULUM_PATH}")
        return {}
    with open(CURRICULUM_PATH, 'r') as f:
        return json.load(f)

def run_bulk_update(target_class=None, start_unit=1):
    """
    Runs the bulk generation.
    target_class: If set (e.g., 8), only runs for that class. If None, runs ALL.
    """
    data = load_curriculum()
    print(f"🚀 Starting Bulk Update Automation...")
    if target_class:
        print(f"🎯 Target: Class {target_class} only")

    # Iterate through Classes (6, 7, 8, etc.)
    for class_key, class_data in data.items():
        
        # === 🛑 SKIP LOGIC ADDED HERE ===
        if str(class_key) == "8":
            print(f"⏩ Skipping Class {class_key} (Already completed)")
            continue
        # ================================

        # Skip if we want a specific class and this isn't it
        if target_class and str(class_key) != str(target_class):
            continue

        print(f"\n📚 PROCESSING CLASS {class_key} ----------------------------")

        # Iterate through Terms (term1, term2...)
        for term_key, term_data in class_data.items():
            # Extract term number (default to 1 if missing)
            term_num = 1
            if "term" in term_key:
                try:
                    term_num = int(term_key.replace("term", ""))
                except:
                    term_num = 1

            # Iterate through Units
            for unit_key, lessons in term_data.items():
                try:
                    unit_num = int(unit_key.replace("unit", ""))
                except:
                    continue

                # Skip units if we want to start later (optional)
                if unit_num < start_unit:
                    continue

                print(f"   👉 Unit {unit_num} ({len(lessons)} lessons)")

                # Iterate through Lessons
                for i, lesson in enumerate(lessons):
                    lesson_choice = i + 1
                    lesson_title = lesson.get('title', 'Unknown Lesson')
                    
                    print(f"      [{i+1}/{len(lessons)}] Generating: '{lesson_title}'...")

                    # PREPARE THE PAYLOAD
                    payload = {
                        "class_num": int(class_key),
                        "subject": "english",
                        "term": term_num,
                        "mode": "lesson",
                        "unit": unit_num,
                        "lesson_choice": lesson_choice,
                        "output_format": "html"  # Change to 'md' if you want Markdown
                    }

                    # SEND REQUEST
                    try:
                        start_time = time.time()
                        # Timeout set to 700s (approx 11 mins) to handle large PDF downloads
                        response = requests.post(API_URL, json=payload, timeout=700)
                        
                        if response.status_code == 200:
                            print(f"      ✅ Success! ({round(time.time() - start_time, 1)}s)")
                        else:
                            print(f"      ❌ Failed: {response.text}")
                    
                    except Exception as e:
                        print(f"      ⚠️ Connection Error: {e}")

                    # === SAFETY SLEEP ===
                    # Wait 15 seconds to keep AI happy
                    print("      ⏳ Cooling down (15s)...")
                    time.sleep(15)

if __name__ == "__main__":
    # === INSTRUCTIONS ===
    # Uncomment the line below corresponding to what you want to do
    
    # OPTION 1: Run EVERYTHING (Classes 6-12) - Takes a long time!
    # run_bulk_update()
    
    # OPTION 2: Run Just Class 8 (Recommended Test)
    run_bulk_update(target_class=12)
    
    # OPTION 3: Run Class 6
    # run_bulk_update(target_class=6)