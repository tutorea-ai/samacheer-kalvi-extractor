"""
Unit-Specific Generation Script
Generates Content + QA + LP for a specific Class and Unit only.

Usage:
    python scripts/generate_unit.py

Configuration:
    - Set MY_CLASS and MY_UNIT at the bottom of this file
    - Curriculum path points to: data/curriculum/languages/english.json
"""

import requests
import time
import json
import sys
from pathlib import Path

# === CONFIGURATION ===
API_URL = "http://localhost:8000/api/generate"

# ✅ FIXED: Correct curriculum path matching project structure
CURRICULUM_PATH = Path(__file__).parent.parent / "data" / "curriculum" / "languages" / "english.json"

# Sleep between lessons (seconds) — respect Claude API rate limits
# Each lesson now makes multiple API calls (content split + 2×50 QA + LP split)
# 10-15 seconds is safe to avoid throttling
SLEEP_BETWEEN_LESSONS = 60


def load_curriculum():
    if not CURRICULUM_PATH.exists():
        print(f"❌ Error: Could not find {CURRICULUM_PATH}")
        print(f"   Expected at: {CURRICULUM_PATH.resolve()}")
        return {}
    with open(CURRICULUM_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_term_num(term_key: str) -> int:
    """Extracts integer term number from key like 'term1' → 1, 'term0' → 0"""
    try:
        return int(term_key.replace("term", ""))
    except:
        return 0


def run_specific_unit(target_class, target_unit):
    """
    Generates content ONLY for a specific Class and Unit.

    Each lesson generates:
      ✅ Content HTML + MD
      ✅ QA HTML (2×50 = 100 questions)
      ✅ LP HTML (day-wise lesson plan)
    """
    data = load_curriculum()
    if not data:
        return

    # 1. Validate Class Exists
    class_str = str(target_class)
    if class_str not in data:
        print(f"❌ Error: Class {target_class} not found in curriculum.")
        print(f"   Available classes: {[k for k in data.keys() if k.isdigit()]}")
        return

    class_data = data[class_str]
    print(f"\n🎯 TARGET LOCKED: Class {target_class} | Unit {target_unit}")
    print(f"   Curriculum: {CURRICULUM_PATH}")
    print("=" * 60)

    found_unit = False

    # 2. Search for the Unit across terms
    for term_key, term_data in class_data.items():

        # Skip non-term keys (metadata etc.)
        if not term_key.startswith("term"):
            continue

        # ✅ FIXED: Proper term number extraction
        term_num = get_term_num(term_key)

        # Check if our target unit is in this term
        unit_key = f"unit{target_unit}"

        if unit_key in term_data:
            found_unit = True
            lessons = term_data[unit_key]

            print(f"\n   📅 Found in: {term_key}")
            print(f"   📖 Unit {target_unit}: {len(lessons)} lesson(s)")
            print("-" * 60)

            total_success = 0
            total_failed = 0

            # 3. Generate Every Lesson in this Unit
            for i, lesson in enumerate(lessons):
                lesson_choice = i + 1
                lesson_title = lesson.get('title', 'Unknown Lesson')
                lesson_id = lesson.get('id', 'unknown')
                lesson_type = lesson.get('type', 'prose')

                print(f"\n      [{i+1}/{len(lessons)}] {lesson_title}")
                print(f"            ID: {lesson_id} | Type: {lesson_type}")

                payload = {
                    "class_num": int(target_class),
                    "subject": "english",
                    "term": term_num,
                    "mode": "lesson",
                    "unit": int(target_unit),
                    "lesson_choice": lesson_choice,
                    "output_format": "html",
                    "force": True  # ✅ Always regenerate — bypass skip check
                }

                try:
                    start_time = time.time()
                    response = requests.post(API_URL, json=payload, timeout=3600)
                    elapsed = round(time.time() - start_time, 1)

                    if response.status_code == 200:
                        result = response.json()
                        deployed = result.get("deployed", [])
                        skipped = result.get("skipped", False)

                        if skipped:
                            print(f"      ⏩ Already deployed — skipped")
                        else:
                            print(f"      ✅ Done ({elapsed}s) — Deployed: {', '.join(deployed)}")
                        total_success += 1
                    else:
                        print(f"      ❌ Failed ({response.status_code}): {response.text[:150]}")
                        total_failed += 1

                except requests.exceptions.Timeout:
                    print(f"      ⏱️  Timeout after 3600s — skipping")
                    total_failed += 1
                except Exception as e:
                    print(f"      ⚠️  Error: {e}")
                    total_failed += 1

                # ✅ FIXED: 10s cooldown to respect API rate limits (each lesson = multiple API calls)
                if i < len(lessons) - 1:
                    print(f"      ⏳ Cooling down ({SLEEP_BETWEEN_LESSONS}s)...")
                    time.sleep(SLEEP_BETWEEN_LESSONS)

            # Summary
            print("\n" + "=" * 60)
            print(f"✨ Mission Complete: Class {target_class} Unit {target_unit}")
            print(f"   ✅ Success: {total_success}")
            print(f"   ❌ Failed:  {total_failed}")
            print("=" * 60)

    if not found_unit:
        print(f"\n❌ Error: Unit {target_unit} not found in Class {target_class}.")
        # Help debug: show available units
        for term_key, term_data in class_data.items():
            if term_key.startswith("term"):
                units = [k for k in term_data.keys() if k.startswith("unit")]
                if units:
                    print(f"   Available in {term_key}: {units}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":

    # ==========================================
    # 👇 CHANGE THESE NUMBERS TO WHAT YOU WANT
    # ==========================================
    MY_CLASS = 10
    MY_UNIT = 2     # Start with Unit 1 to test prose + poem + supplementary

    run_specific_unit(MY_CLASS, MY_UNIT)