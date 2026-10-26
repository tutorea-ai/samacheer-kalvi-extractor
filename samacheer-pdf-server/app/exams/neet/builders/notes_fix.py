"""
Apply accepted fact-check corrections to NEET unit notes.

- Reads factcheck.json for each unit + _factcheck_decisions.json (accept / reject / custom).
- Claude returns exact field edits; code validates that each path exists and holds text.
- Keeps a one-time backup (notes.orig.json) and writes a diff log (fixes.json).

Usage:
    python -m app.exams.neet.builders.notes_fix                 # all units with open issues
    python -m app.exams.neet.builders.notes_fix --units phy_u02
"""
import argparse
import json
import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.exams.common.llm import call_json

ROOT = Path(__file__).resolve().parents[4]
EXAM_DIR = ROOT / "exams_data/neet"
SYLLABUS = EXAM_DIR / "syllabus/neet_2026.json"
GEN_DIR = EXAM_DIR / "generated"
DECISIONS = GEN_DIR / "_factcheck_decisions.json"

MODEL = os.getenv("NEET_FIX_MODEL", "claude-opus-5-5")
WORKERS = int(os.getenv("NEET_FIX_WORKERS", "4"))
EDITABLE = ("overview", "topics", "formula_sheet", "key_facts", "common_traps", "quick_revision")

PROMPT = """You are correcting NEET study notes. Apply ONLY the corrections listed below, nothing else.

NOTES (JSON):
{notes}

CORRECTIONS TO APPLY (each was reviewed and approved by a subject expert):
{corrections}

Rules:
- For each correction, find EVERY place in the notes where the same mistake appears (the given
  location is a hint and may be off) and fix it there too.
- Change as little text as possible. Keep the surrounding wording, style and LaTeX ($...$).
- Do not add new facts beyond what the correction requires. Do not "improve" anything else.
- Each edit replaces one whole string field. Paths look like: topics[3].explanation,
  topics[2].key_points[4], topics[1].formulas[0].formula, formula_sheet[5].meaning,
  key_facts[7], common_traps[2], quick_revision[9], overview.

Return ONLY a JSON object, no commentary:
{{
  "edits": [
    {{"path": "topics[3].explanation", "new_value": "the full corrected string", "fixes": "which correction (short)"}}
  ]
}}
"""

PATH_RE = re.compile(r"[A-Za-z_]+|\[\d+\]")


def resolve(obj, path: str):
    """Return (parent, key) for a path like topics[3].key_points[2]."""
    parts = PATH_RE.findall(path)
    if not parts or parts[0] not in EDITABLE:
        raise KeyError(f"path not editable: {path}")
    parent, key = None, None
    cur = obj
    for p in parts:
        parent = cur
        key = int(p[1:-1]) if p.startswith("[") else p
        cur = cur[key]
    if not isinstance(cur, str):
        raise TypeError(f"path does not point to text: {path}")
    return parent, key


def decide(unit_id: str, issue: dict, decisions: dict):
    """Return the correction text to apply, or None if rejected."""
    for o in decisions.get("overrides", []):
        if o["unit_id"] == unit_id and o["quote_contains"].lower() in (
                issue.get("quote", "") + " " + issue.get("problem", "")).lower():
            if o["action"] == "reject":
                return None
            if o["action"] == "custom":
                return o["correction"]
    return issue.get("correction") if decisions.get("default", "accept") == "accept" else None


def fix_unit(subject: dict, unit: dict, decisions: dict) -> tuple:
    unit_dir = GEN_DIR / subject["subject_id"] / unit["slug"]
    fc_file = unit_dir / "factcheck.json"
    if not fc_file.exists():
        return unit["unit_id"], "no factcheck", 0, []
    factcheck = json.loads(fc_file.read_text(encoding="utf-8"))
    if factcheck.get("status") == "fixed":
        return unit["unit_id"], "already fixed", 0, []

    corrections = []
    for i in factcheck["issues"]:
        c = decide(unit["unit_id"], i, decisions)
        if c:
            corrections.append({"location_hint": i.get("location"), "wrong_text": i.get("quote"),
                                "problem": i.get("problem"), "correction": c})
    if not corrections:
        factcheck["status"] = "fixed"
        fc_file.write_text(json.dumps(factcheck, indent=2, ensure_ascii=False), encoding="utf-8")
        return unit["unit_id"], "nothing to apply", 0, []

    notes_file = unit_dir / "notes.json"
    notes = json.loads(notes_file.read_text(encoding="utf-8"))
    content = {k: notes[k] for k in EDITABLE if k in notes}
    result = call_json(PROMPT.format(
        notes=json.dumps(content, ensure_ascii=False, indent=1),
        corrections=json.dumps(corrections, ensure_ascii=False, indent=1),
    ), model=MODEL, max_tokens=16000)

    backup = unit_dir / "notes.orig.json"
    if not backup.exists():
        shutil.copy(notes_file, backup)

    log, rejected = [], []
    for e in result.get("edits", []):
        try:
            parent, key = resolve(notes, e["path"])
        except (KeyError, IndexError, TypeError) as err:
            rejected.append(f"{e.get('path')}: {err}")
            continue
        old = parent[key]
        if old == e["new_value"]:
            continue
        parent[key] = e["new_value"]
        log.append({"path": e["path"], "old": old, "new": e["new_value"], "fixes": e.get("fixes")})

    notes_file.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
    prev = json.loads((unit_dir / "fixes.json").read_text(encoding="utf-8")) if (unit_dir / "fixes.json").exists() else []
    (unit_dir / "fixes.json").write_text(json.dumps(prev + log, indent=2, ensure_ascii=False), encoding="utf-8")
    factcheck["status"] = "fixed"
    fc_file.write_text(json.dumps(factcheck, indent=2, ensure_ascii=False), encoding="utf-8")
    return unit["unit_id"], "fixed", len(log), rejected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", nargs="*")
    args = ap.parse_args()

    syllabus = json.loads(SYLLABUS.read_text(encoding="utf-8"))
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    jobs = [(s, u) for s in syllabus["subjects"] for u in s["units"]
            if not args.units or u["unit_id"] in args.units]

    print(f"Model: {MODEL} | workers: {WORKERS} | units: {len(jobs)}")
    total = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(fix_unit, s, u, decisions) for s, u in jobs]
        for f in as_completed(futures):
            unit_id, status, n, rejected = f.result()
            total += n
            line = f"  {unit_id}: {status}" + (f" | {n} field(s) changed" if n else "")
            print(line)
            for r in rejected:
                print(f"     ⚠ rejected edit {r}")
    print(f"\nTotal fields changed: {total}")


if __name__ == "__main__":
    main()