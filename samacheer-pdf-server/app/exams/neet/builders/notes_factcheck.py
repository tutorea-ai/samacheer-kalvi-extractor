"""
Independent fact-check of generated NEET unit notes.

- One Claude call per unit, given only the notes; job is to find errors.
- Reports issues (location, quote, problem, correction, severity). Changes nothing.
- Output: exams_data/neet/generated/{subject}/{slug}/factcheck.json

Usage:
    python -m app.exams.neet.builders.notes_factcheck              # all units
    python -m app.exams.neet.builders.notes_factcheck --units phy_u06 --force
"""
import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.exams.common.llm import call_json

ROOT = Path(__file__).resolve().parents[4]
EXAM_DIR = ROOT / "exams_data/neet"
SYLLABUS = EXAM_DIR / "syllabus/neet_2026.json"
GEN_DIR = EXAM_DIR / "generated"

MODEL = os.getenv("NEET_FACTCHECK_MODEL", "claude-opus-5-5")
WORKERS = int(os.getenv("NEET_FACTCHECK_WORKERS", "4"))

PROMPT = """You are a strict subject-expert reviewer checking study notes written for NEET (UG) aspirants.
The notes will be published to students, so every factual error matters. Check them against the
standard NCERT Class 11-12 treatment that NEET is based on.

SUBJECT: {subject}
UNIT: {unit_name}

NOTES (JSON):
{notes}

Find ONLY real problems:
- factual errors (wrong fact, number, value, unit, formula, sign, reaction, name, example)
- internal contradictions between parts of the notes
- statements that would mislead a student or are clearly outside the NEET syllabus

Do NOT report style, wording preferences, missing extra detail, or LaTeX formatting choices.
If the notes are correct, return an empty list. Do not invent problems.

Return ONLY a JSON object, no commentary:
{{
  "issues": [
    {{
      "location": "e.g. topics[2].key_points[1] or formula_sheet[5] or common_traps[0]",
      "quote": "the exact problematic text (short)",
      "problem": "what is wrong",
      "correction": "the correct statement",
      "severity": "error | minor"
    }}
  ]
}}
"error" = factually wrong. "minor" = imprecise or potentially confusing but not false.
"""


def check_unit(subject: dict, unit: dict, force: bool) -> tuple:
    unit_dir = GEN_DIR / subject["subject_id"] / unit["slug"]
    out_file = unit_dir / "factcheck.json"
    if out_file.exists() and not force:
        return unit["unit_id"], json.loads(out_file.read_text(encoding="utf-8")), True

    notes = json.loads((unit_dir / "notes.json").read_text(encoding="utf-8"))
    content = {k: v for k, v in notes.items() if k not in ("pyq", "review_flags", "_meta")}
    result = call_json(PROMPT.format(
        subject=subject["subject_name"],
        unit_name=unit["unit_name"],
        notes=json.dumps(content, ensure_ascii=False, indent=1),
    ), model=MODEL, max_tokens=12000)

    report = {"unit_id": unit["unit_id"], "model": MODEL, "issues": result.get("issues", [])}
    out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return unit["unit_id"], report, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", nargs="*")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    syllabus = json.loads(SYLLABUS.read_text(encoding="utf-8"))
    jobs = [(s, u) for s in syllabus["subjects"] for u in s["units"]
            if not args.units or u["unit_id"] in args.units]

    print(f"Model: {MODEL} | workers: {WORKERS} | units: {len(jobs)}")
    reports = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(check_unit, s, u, args.force) for s, u in jobs]
        for f in as_completed(futures):
            unit_id, report, cached = f.result()
            reports[unit_id] = report
            n_err = sum(1 for i in report["issues"] if i.get("severity") == "error")
            n_min = len(report["issues"]) - n_err
            print(f"  {unit_id}: {'cached' if cached else 'checked'} | errors {n_err} | minor {n_min}")

    total_err = sum(1 for r in reports.values() for i in r["issues"] if i.get("severity") == "error")
    total_min = sum(1 for r in reports.values() for i in r["issues"] if i.get("severity") != "error")
    print(f"\nTotal: errors {total_err} | minor {total_min}")
    print("\nERRORS (need review):")
    for unit_id in sorted(reports):
        for i in reports[unit_id]["issues"]:
            if i.get("severity") == "error":
                print(f"  [{unit_id}] {i.get('location')}")
                print(f"     quote:      {i.get('quote')}")
                print(f"     problem:    {i.get('problem')}")
                print(f"     correction: {i.get('correction')}")


if __name__ == "__main__":
    main()