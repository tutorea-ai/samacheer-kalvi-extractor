"""
Bulk Generation Script
Automates Content + QA + LP generation for entire classes.

Usage:
    python scripts/bulk_generate.py

Configuration:
    - Set target_class to run a specific class only
    - Set start_unit to resume from a specific unit
    - Add class keys to SKIP_CLASSES if already completed
    - output_format is always "html" → triggers full Content + QA + LP pipeline
"""

import requests
import time
import json
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = "http://localhost:8000/api/generate"

# ✅ FIXED: Updated path to new curriculum location
CURRICULUM_PATH = Path(__file__).parent.parent / "data" / "curriculum" / "languages" / "english.json"

# Classes to skip (already fully generated)
# Add class numbers here as strings when done: e.g. "8", "9"
SKIP_CLASSES = {
    # "8",   # ← Uncomment when Class 8 is complete
}

# Sleep between lessons (seconds) — respect Claude API rate limits
SLEEP_BETWEEN_LESSONS = 15


# ============================================================================
# HELPERS
# ============================================================================

def load_curriculum() -> dict:
    if not CURRICULUM_PATH.exists():
        print(f"❌ Error: Curriculum not found at {CURRICULUM_PATH}")
        return {}
    with open(CURRICULUM_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_term_num(term_key: str) -> int:
    """Extracts integer term number from key like 'term1' → 1"""
    try:
        return int(term_key.replace("term", ""))
    except:
        return 0


# ============================================================================
# MAIN BULK RUNNER
# ============================================================================

def run_bulk_update(target_class: int = None, start_unit: int = 1):
    """
    Runs bulk generation for all lessons in the curriculum.

    Each lesson sends ONE request that generates:
      ✅ Content HTML  (deployed to content/{term}/{lessonId}/index.html)
      ✅ QA HTML       (deployed to qa/{term}/{lessonId}/index.html)
      ✅ LP HTML       (deployed to lp/{term}/{lessonId}/index.html)
      ✅ Content MD    (deployed to md-files/{class}/{lessonId}.md)

    Args:
        target_class: If set, only runs for this class. If None, runs all.
        start_unit: Start from this unit number (useful for resuming).
    """
    curriculum = load_curriculum()
    if not curriculum:
        return

    print(f"\n🚀 Starting Bulk Generation")
    print(f"   Target  : {'All classes' if not target_class else f'Class {target_class}'}")
    print(f"   From    : Unit {start_unit}")
    print(f"   Skipping: {SKIP_CLASSES or 'None'}")
    print(f"   Output  : Content + QA + LP (HTML + MD)")
    print("=" * 60)

    total_success = 0
    total_failed = 0

    for class_key, class_data in curriculum.items():

        # Skip non-class keys (like "subject", "version" etc.)
        if not str(class_key).isdigit():
            continue

        # Skip completed classes
        if str(class_key) in SKIP_CLASSES:
            print(f"\n⏩ Skipping Class {class_key} (marked as complete)")
            continue

        # Skip if targeting a specific class
        if target_class and str(class_key) != str(target_class):
            continue

        print(f"\n📚 CLASS {class_key} {'─' * 40}")

        for term_key, term_data in class_data.items():

            # Skip metadata keys
            if not term_key.startswith("term"):
                continue

            term_num = get_term_num(term_key)
            print(f"\n   📅 {term_key.upper()}")

            for unit_key, lessons in term_data.items():

                if not isinstance(lessons, list):
                    continue

                try:
                    unit_num = int(unit_key.replace("unit", ""))
                except:
                    continue

                # Resume from start_unit
                if unit_num < start_unit:
                    continue

                print(f"\n   📖 Unit {unit_num}  ({len(lessons)} lessons)")

                for i, lesson in enumerate(lessons):
                    lesson_choice = i + 1
                    lesson_title = lesson.get("title", "Unknown")
                    lesson_id = lesson.get("id", "unknown")

                    print(f"\n      [{lesson_choice}/{len(lessons)}] {lesson_title}")
                    print(f"            ID: {lesson_id}")

                    # Build payload
                    payload = {
                        "class_num": int(class_key),
                        "subject": "english",
                        "term": term_num,
                        "mode": "lesson",
                        "unit": unit_num,
                        "lesson_choice": lesson_choice,
                        "output_format": "html",   # Always html → triggers full pipeline
                    }

                    # Send request
                    try:
                        start_time = time.time()
                        response = requests.post(API_URL, json=payload, timeout=700)
                        elapsed = round(time.time() - start_time, 1)

                        if response.status_code == 200:
                            data = response.json()
                            deployed = data.get("deployed", [])
                            skipped = data.get("skipped", False)
                            if skipped:
                                print(f"      ⏩ Already deployed — skipped")
                            else:
                                print(f"      ✅ Done ({elapsed}s) — Deployed: {', '.join(deployed)}")
                            total_success += 1
                        else:
                            print(f"      ❌ Failed ({response.status_code}): {response.text[:100]}")
                            total_failed += 1

                    except requests.exceptions.Timeout:
                        print(f"      ⏱️  Timeout after 700s — skipping")
                        total_failed += 1
                    except Exception as e:
                        print(f"      ⚠️  Error: {e}")
                        total_failed += 1

                    # Cool down between lessons
                    print(f"      ⏳ Cooling down ({SLEEP_BETWEEN_LESSONS}s)...")
                    time.sleep(SLEEP_BETWEEN_LESSONS)

    print("\n" + "=" * 60)
    print(f"🏁 Bulk generation complete!")
    print(f"   ✅ Success : {total_success}")
    print(f"   ❌ Failed  : {total_failed}")
    print("=" * 60)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":

    # ── OPTIONS ──────────────────────────────────────────────────────────────
    # Uncomment the one you want to run:

    # OPTION 1: Run ALL classes (long — use for full generation)
    # run_bulk_update()

    # OPTION 2: Run a specific class only
    run_bulk_update(target_class=10, start_unit=2)

    # OPTION 3: Run a specific class starting from a specific unit
    # run_bulk_update(target_class=10, start_unit=3)

    # OPTION 4: Run Class 6 Term 1 only (set start_unit and add skip logic manually)
    # run_bulk_update(target_class=6)