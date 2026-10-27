"""
Build a self-contained mock test JSON (schema agreed with the Node team).

- Hidden questions are excluded; audit fields are stripped.
- Image paths stay relative to pyq/, exactly as in the paper file.
- Validates everything before writing; writes nothing if a check fails.

Usage:
    python -m app.exams.common.mock_builder --paper re_neet_2026 --mock-id re-neet-2026 \
        --title "NEET (UG) 2026 · Full paper"
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXAM = "neet"
EXAM_DIR = ROOT / f"exams_data/{EXAM}"
SYLLABUS = EXAM_DIR / "syllabus/neet_2026.json"

QUESTION_FIELDS = ["q_id", "source", "exam_ref", "q_no", "subject", "unit_id", "topic", "type",
                   "question", "statements", "match_lists", "options", "diagram_description",
                   "image", "answer", "status", "solution"]
SOLUTION_FIELDS = ["key_concept", "steps", "final_answer", "why_not_others",
                   "common_trap", "time_saving_tip"]
FIGURE_FIELDS = ["kind", "path", "headers", "rows"]


def clean_figure(fig):
    return None if fig is None else {k: fig[k] for k in FIGURE_FIELDS if k in fig}


def clean_question(q: dict) -> dict:
    out = {k: q.get(k) for k in QUESTION_FIELDS}
    if out["solution"]:
        out["solution"] = {k: out["solution"].get(k) for k in SOLUTION_FIELDS}
    img = q.get("image")
    if img and (img.get("stem") or img.get("options")):
        out["image"] = {
            "stem": clean_figure(img.get("stem")),
            "options": [clean_figure(f) for f in img["options"]] if img.get("options") else None,
        }
    else:
        out["image"] = None
    return out


def validate(mock: dict, pyq_dir: Path) -> list:
    errors = []
    by_id = {q["q_id"]: q for q in mock["questions"]}
    listed = [qid for s in mock["sections"] for qid in s["question_ids"]]
    if sorted(listed) != sorted(by_id):
        errors.append("sections do not list exactly the questions in the file")
    for q in mock["questions"]:
        n = q["q_id"]
        if q["status"] == "hidden":
            errors.append(f"{n}: hidden question included")
        if len(q["options"] or []) != 4:
            errors.append(f"{n}: has {len(q['options'] or [])} options")
        if q["status"] == "normal" and not q["answer"]:
            errors.append(f"{n}: no answer")
        if any(a not in (1, 2, 3, 4) for a in q["answer"] or []):
            errors.append(f"{n}: answer out of range {q['answer']}")
        if not q["solution"]:
            errors.append(f"{n}: no solution")
        img = q["image"] or {}
        figs = [img.get("stem")] + (img.get("options") or [])
        for f in figs:
            if f and f.get("kind") == "svg" and not (pyq_dir / f["path"]).exists():
                errors.append(f"{n}: missing figure file {f['path']}")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", required=True)
    ap.add_argument("--mock-id", required=True)
    ap.add_argument("--title", required=True)
    args = ap.parse_args()

    syllabus = json.loads(SYLLABUS.read_text(encoding="utf-8"))
    paper = json.loads((EXAM_DIR / f"pyq/{args.paper}.json").read_text(encoding="utf-8"))
    pattern = syllabus["exam_pattern"]
    names = {s["subject_id"]: s["subject_name"] for s in syllabus["subjects"]}

    questions = [clean_question(q) for q in sorted(paper["questions"], key=lambda q: q["q_no"])
                 if q["status"] != "hidden"]
    sections = [{"subject": sid, "title": names[sid],
                 "question_ids": [q["q_id"] for q in questions if q["subject"] == sid]}
                for sid in pattern["subjects_order"]]
    order = [qid for s in sections for qid in s["question_ids"]]
    by_id = {q["q_id"]: q for q in questions}

    mock = {
        "exam": EXAM,
        "mock_id": args.mock_id,
        "title": args.title,
        "kind": "pyq_paper",
        "duration_minutes": pattern["duration_minutes"],
        "marking": {"correct": pattern["marks_correct"], "incorrect": pattern["marks_incorrect"],
                    "unanswered": 0},
        "sections": sections,
        "questions": [by_id[qid] for qid in order],
    }

    errors = validate(mock, EXAM_DIR / "pyq")
    if errors:
        print("NOT WRITTEN. Problems:")
        for e in errors:
            print(f"  {e}")
        raise SystemExit(1)

    out = EXAM_DIR / f"mock/{args.mock_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mock, indent=2, ensure_ascii=False), encoding="utf-8")

    n = len(mock["questions"])
    dropped = [q["q_no"] for q in mock["questions"] if q["status"] == "dropped"]
    multi = [q["q_no"] for q in mock["questions"] if len(q["answer"]) > 1]
    figs = sum(1 for q in mock["questions"] if q["image"])
    print(f"Saved: {out}")
    print(f"Questions: {n} | " + " | ".join(f"{s['title']} {len(s['question_ids'])}" for s in sections))
    print(f"Duration: {mock['duration_minutes']} min | Max marks: {n * pattern['marks_correct']}")
    print(f"Dropped: {dropped} | Multiple answers: {multi} | With figures: {figs}")


if __name__ == "__main__":
    main()