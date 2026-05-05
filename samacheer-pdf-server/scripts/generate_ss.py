"""
Social Science Generation Script
Generates Content + QA + LP for Social Science lessons.

Can run in two modes:
  1. Single discipline + unit  → set MY_MODE = "unit"
  2. Full discipline           → set MY_MODE = "discipline"
  3. Full class (all discs)   → set MY_MODE = "class"

Configuration:
  - Set MY_CLASS, MY_DISCIPLINE, MY_UNIT, MY_MODE at the bottom
  - Curriculum path: data/curriculum/subjects/english-medium/social-science.json

Discipline names: "history", "geography", "civics", "economics"
"""

import requests
import time
import json
import sys
from pathlib import Path

# === CONFIGURATION ===
API_URL = "http://localhost:8000/api/generate"

CURRICULUM_PATH = (
    Path(__file__).parent.parent
    / "data" / "curriculum" / "subjects"
    / "english-medium" / "social-science.json"
)

# Sleep between lessons — SS LP = 5 API calls, give enough cooldown
SLEEP_BETWEEN_LESSONS = 60

# Discipline order — always generate in this order
DISCIPLINE_ORDER = ["history", "geography", "civics", "economics"]


# ============================================================================
# Curriculum Loader
# ============================================================================

def load_curriculum():
    if not CURRICULUM_PATH.exists():
        print(f"❌ Error: Could not find {CURRICULUM_PATH}")
        print(f"   Expected at: {CURRICULUM_PATH.resolve()}")
        return {}
    with open(CURRICULUM_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_term_num(term_key: str) -> int:
    try:
        return int(term_key.replace("term", ""))
    except:
        return 0


# ============================================================================
# Core Generator
# ============================================================================

def generate_lesson(class_num: int, term_num: int, discipline: str,
                    unit_num: int, lesson: dict) -> bool:
    """
    Generate Content + QA + LP for a single SS lesson.
    Returns True on success, False on failure.
    """
    lesson_title = lesson.get("title", "Unknown")
    lesson_id    = lesson.get("id", "unknown")

    print(f"\n      📖 {discipline.title()} Unit {unit_num}: {lesson_title}")
    print(f"            ID: {lesson_id}")

    payload = {
        "class_num":     class_num,
        "subject":       "SocialScience",
        "discipline":    discipline,
        "term":          term_num,
        "unit":          unit_num,
        "lesson_choice": 1,
        "mode":          "lesson",
        "output_format": "html",
        "force":         True,
        "medium":        "english",
    }

    try:
        start_time = time.time()
        response   = requests.post(API_URL, json=payload, timeout=3600)
        elapsed    = round(time.time() - start_time, 1)

        if response.status_code == 200:
            result   = response.json()
            deployed = result.get("deployed", [])
            skipped  = result.get("skipped", False)

            if skipped:
                print(f"      ⏩ Already deployed — skipped")
            else:
                print(f"      ✅ Done ({elapsed}s) — Deployed: {', '.join(deployed)}")
            return True
        else:
            print(f"      ❌ Failed ({response.status_code}): {response.text[:200]}")
            return False

    except requests.exceptions.Timeout:
        print(f"      ⏱️  Timeout after 3600s — skipping")
        return False
    except Exception as e:
        print(f"      ⚠️  Error: {e}")
        return False


# ============================================================================
# Mode 1: Single Unit
# ============================================================================

def run_single_unit(target_class: int, target_discipline: str, target_unit: int):
    """Generate one specific unit."""
    data = load_curriculum()
    if not data:
        return

    class_str = str(target_class)
    if class_str not in data:
        print(f"❌ Class {target_class} not found in curriculum.")
        return

    discipline = target_discipline.lower().strip()
    print(f"\n🎯 TARGET: Class {target_class} | {discipline.title()} | Unit {target_unit}")
    print("=" * 60)

    class_data = data[class_str]
    found = False

    for term_key, term_data in class_data.items():
        if not term_key.startswith("term"):
            continue

        disc_lessons = term_data.get(discipline, [])
        lesson = next((l for l in disc_lessons if l.get("unit") == target_unit), None)

        if lesson:
            found = True
            term_num = get_term_num(term_key)
            success = generate_lesson(
                target_class, term_num, discipline, target_unit, lesson
            )
            print("\n" + "=" * 60)
            print(f"{'✅ Success' if success else '❌ Failed'}: Class {target_class} | {discipline.title()} Unit {target_unit}")
            print("=" * 60)
            return

    if not found:
        print(f"❌ {discipline.title()} Unit {target_unit} not found in Class {target_class}.")


# ============================================================================
# Mode 2: Full Discipline
# ============================================================================

def run_full_discipline(target_class: int, target_discipline: str):
    """Generate all units for one discipline."""
    data = load_curriculum()
    if not data:
        return

    class_str  = str(target_class)
    if class_str not in data:
        print(f"❌ Class {target_class} not found in curriculum.")
        return

    discipline = target_discipline.lower().strip()
    class_data = data[class_str]

    print(f"\n🎯 TARGET: Class {target_class} | {discipline.title()} — ALL UNITS")
    print("=" * 60)

    total_success = 0
    total_failed  = 0
    lesson_count  = 0

    for term_key, term_data in class_data.items():
        if not term_key.startswith("term"):
            continue

        disc_lessons = term_data.get(discipline, [])
        if not disc_lessons:
            continue

        term_num = get_term_num(term_key)
        print(f"\n   📅 Term: {term_key} | {len(disc_lessons)} units")
        print("-" * 60)

        for i, lesson in enumerate(disc_lessons):
            unit_num = lesson.get("unit", i + 1)
            success  = generate_lesson(
                target_class, term_num, discipline, unit_num, lesson
            )

            if success:
                total_success += 1
            else:
                total_failed += 1
            lesson_count += 1

            # Cooldown between lessons
            if i < len(disc_lessons) - 1:
                print(f"      ⏳ Cooling down ({SLEEP_BETWEEN_LESSONS}s)...")
                time.sleep(SLEEP_BETWEEN_LESSONS)

    print("\n" + "=" * 60)
    print(f"✨ Complete: Class {target_class} | {discipline.title()}")
    print(f"   Total:   {lesson_count}")
    print(f"   ✅ Success: {total_success}")
    print(f"   ❌ Failed:  {total_failed}")
    print("=" * 60)


# ============================================================================
# Mode 3: Full Class (All Disciplines)
# ============================================================================

def run_full_class(target_class: int):
    """Generate all disciplines and all units for a class."""
    data = load_curriculum()
    if not data:
        return

    class_str = str(target_class)
    if class_str not in data:
        print(f"❌ Class {target_class} not found in curriculum.")
        return

    class_data = data[class_str]

    print(f"\n🎯 TARGET: Class {target_class} — ALL DISCIPLINES — ALL UNITS")
    print("=" * 60)

    grand_success = 0
    grand_failed  = 0
    grand_total   = 0

    for term_key, term_data in class_data.items():
        if not term_key.startswith("term"):
            continue

        term_num = get_term_num(term_key)
        print(f"\n📅 Term: {term_key}")

        # Generate in discipline order
        for discipline in DISCIPLINE_ORDER:
            disc_lessons = term_data.get(discipline, [])
            if not disc_lessons:
                continue

            print(f"\n   🔷 {discipline.title()} — {len(disc_lessons)} units")
            print("   " + "-" * 55)

            disc_success = 0
            disc_failed  = 0

            for i, lesson in enumerate(disc_lessons):
                unit_num = lesson.get("unit", i + 1)
                success  = generate_lesson(
                    target_class, term_num, discipline, unit_num, lesson
                )

                if success:
                    disc_success += 1
                    grand_success += 1
                else:
                    disc_failed += 1
                    grand_failed += 1
                grand_total += 1

                # Cooldown between lessons
                if i < len(disc_lessons) - 1:
                    print(f"      ⏳ Cooling down ({SLEEP_BETWEEN_LESSONS}s)...")
                    time.sleep(SLEEP_BETWEEN_LESSONS)

            print(f"\n   {discipline.title()} Done — ✅ {disc_success} | ❌ {disc_failed}")

        # Cooldown between disciplines
        print(f"\n   ⏳ Discipline complete. Cooling down (30s) before next...")
        time.sleep(30)

    print("\n" + "=" * 60)
    print(f"✨ FULL CLASS COMPLETE: Class {target_class}")
    print(f"   Total:      {grand_total}")
    print(f"   ✅ Success:  {grand_success}")
    print(f"   ❌ Failed:   {grand_failed}")
    print("=" * 60)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":

    # =====================================================
    # 👇 CONFIGURE THESE BEFORE RUNNING
    # =====================================================

    MY_CLASS      = 10
    MY_DISCIPLINE = "history"    # "history" | "geography" | "civics" | "economics"
    MY_UNIT       = 1            # Unit number (used only in "unit" mode)

    # Mode options:
    #   "unit"       → Generate one specific unit only
    #   "discipline" → Generate all units in one discipline
    #   "class"      → Generate all disciplines + all units for the class
    MY_MODE = "discipline"

    # =====================================================

    if MY_MODE == "unit":
        run_single_unit(MY_CLASS, MY_DISCIPLINE, MY_UNIT)

    elif MY_MODE == "discipline":
        run_full_discipline(MY_CLASS, MY_DISCIPLINE)

    elif MY_MODE == "class":
        run_full_class(MY_CLASS)

    else:
        print(f"❌ Unknown mode: {MY_MODE}")
        print("   Valid modes: 'unit', 'discipline', 'class'")
        sys.exit(1)