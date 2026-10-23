"""
Apply manual corrections to a PYQ paper JSON.
Run this LAST, after the extractor and tagger.

Usage:
    python -m app.exams.common.apply_corrections
    python -m app.exams.common.apply_corrections --paper re_neet_2026
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXAM = "neet"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", default="re_neet_2026")
    args = ap.parse_args()

    paper_file = ROOT / f"exams_data/{EXAM}/pyq/{args.paper}.json"
    corr_file = ROOT / f"exams_data/{EXAM}/pyq/{args.paper}_corrections.json"

    paper = json.loads(paper_file.read_text(encoding="utf-8"))
    corrections = json.loads(corr_file.read_text(encoding="utf-8"))["corrections"]
    by_no = {q["q_no"]: q for q in paper["questions"]}

    for c in corrections:
        q = by_no.get(c["q_no"])
        if q is None:
            raise ValueError(f"Correction for unknown question Q{c['q_no']}")

        field = c["field"]
        if "index" in c:
            old = q[field][c["index"]]
            q[field][c["index"]] = c["value"]
        else:
            old = q.get(field)
            q[field] = c["value"]

        q.setdefault("corrections", [])
        q["corrections"] = [x for x in q["corrections"]
                            if not (x["field"] == field and x.get("index") == c.get("index"))]
        q["corrections"].append({
            "field": field,
            "index": c.get("index"),
            "old": old,
            "new": c["value"],
            "note": c["note"],
        })
        where = f"{field}[{c['index']}]" if "index" in c else field
        print(f"Q{c['q_no']}: {where} -> {c['value']!r}")

    paper_file.write_text(json.dumps(paper, indent=2, ensure_ascii=False), encoding="utf-8")

    statuses = {}
    for q in paper["questions"]:
        statuses[q["status"]] = statuses.get(q["status"], 0) + 1
    print(f"\nSaved: {paper_file}")
    print(f"Question status: {statuses}")


if __name__ == "__main__":
    main()