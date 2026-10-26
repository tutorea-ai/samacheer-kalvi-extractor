"""
Stage 2 of 2: blind-verify draft practice questions and publish only the ones that pass.

- Each topic's questions are solved WITHOUT the answer (one call per topic).
- Publish rule: no review_flags from stage 1 AND blind answer is one of our answers.
- Output: generated/{subject}/{slug}/practice.json      (synced to Node)
          generated/{subject}/{slug}/_practice_verify.json (report, never synced)

Usage:
    python -m app.exams.neet.builders.practice_verify --units phy_u06 che_u12 bio_u09
    python -m app.exams.neet.builders.practice_verify                 # all units with drafts
    python -m app.exams.neet.builders.practice_verify --units phy_u06 --force
"""
import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.exams.common.llm import RefusalError, call_json

ROOT = Path(__file__).resolve().parents[4]
EXAM_DIR = ROOT / "exams_data/neet"
SYLLABUS = EXAM_DIR / "syllabus/neet_2026.json"
GEN_DIR = EXAM_DIR / "generated"
CACHE_DIR = GEN_DIR / "_cache/practice_verify"
APPROVALS = GEN_DIR / "_manual_approvals.json"


def load_approvals() -> tuple:
    if not APPROVALS.exists():
        return {}, {}
    data = json.loads(APPROVALS.read_text(encoding="utf-8"))
    return ({a["q_id"]: a for a in data.get("approved", [])},
            {r["q_id"]: r for r in data.get("rejected", [])})

MODEL = os.getenv("NEET_PRACTICE_VERIFY_MODEL", "claude-opus-5-5")
WORKERS = int(os.getenv("NEET_PRACTICE_VERIFY_WORKERS", "4"))
PUBLISH_FIELDS = ["q_id", "source", "subject", "unit_id", "topic", "topic_index", "type", "difficulty",
                  "question", "statements", "match_lists", "options", "image", "answer", "status",
                  "solution"]

PROMPT = """Solve each of these NEET (UG) multiple-choice questions. Each has exactly one intended
correct option. Treat every question independently.

{questions}

Work each one out carefully and briefly, then choose the option.

Return ONLY a JSON object, no commentary:
{{"results": [{{"id": "Q1", "working": "brief working", "answer": 2, "confidence": "high | medium | low"}}]}}
"answer" is the option number 1-4. Include every question, in order.
"""


def format_question(label: str, q: dict) -> str:
    parts = [f"{label} [{q['type']}]", q["question"]]
    for k, v in (q.get("statements") or {}).items():
        parts.append(f"  {k}: {v}")
    ml = q.get("match_lists")
    if ml:
        parts.append("  List-I: " + "; ".join(f"{x['label']}. {x['text']}" for x in ml.get("list_I", [])))
        parts.append("  List-II: " + "; ".join(f"{x['label']}. {x['text']}" for x in ml.get("list_II", [])))
    for i, opt in enumerate(q["options"], 1):
        parts.append(f"  ({i}) {opt}")
    return "\n".join(parts)


def verify_topic(unit_id: str, topic_index: int, questions: list, force: bool) -> dict:
    """Return {q_id: result} for one topic's questions."""
    cache_file = CACHE_DIR / f"{unit_id}_t{topic_index:02d}.json"
    if cache_file.exists() and not force:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    labels = {f"Q{i}": q["q_id"] for i, q in enumerate(questions, 1)}
    prompt = PROMPT.format(questions="\n\n".join(format_question(l, q)
                                                 for l, q in zip(labels, questions)))
    try:
        result = call_json(prompt, model=MODEL, max_tokens=8000)
    except RefusalError:
        print(f"     ⚠ {unit_id} t{topic_index:02d}: verification declined by the model; sent to manual review")
        return {q["q_id"]: {"refused": True} for q in questions}   # not cached: retried next run
    except Exception as e:
        raise RuntimeError(f"{unit_id} topic t{topic_index:02d}: {e}") from e
    by_qid = {labels[r["id"]]: r for r in result.get("results", []) if r.get("id") in labels}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(by_qid, indent=2, ensure_ascii=False), encoding="utf-8")
    return by_qid


def verify_unit(subject: dict, unit: dict, force: bool) -> tuple:
    unit_dir = GEN_DIR / subject["subject_id"] / unit["slug"]
    draft = json.loads((unit_dir / "_practice_draft.json").read_text(encoding="utf-8"))

    by_topic = {}
    for q in draft["questions"]:
        by_topic.setdefault(q["topic_index"], []).append(q)
    blind = {}
    for t_idx, qs in sorted(by_topic.items()):
        blind.update(verify_topic(unit["unit_id"], t_idx, qs, force))

    approved, manual_rejected = load_approvals()
    published, report = [], []
    for q in draft["questions"]:
        r = blind.get(q["q_id"])
        if q["q_id"] in manual_rejected:
            reason = "manual_rejected"
        elif q["review_flags"]:
            reason = "stage1_flags"
        elif not r:
            reason = "no_blind_result"
        elif r.get("refused"):
            reason = None if q["q_id"] in approved else "verify_refused"
        elif r.get("answer") not in q["answer"]:
            reason = "blind_mismatch"
        else:
            reason = None
        if reason is None:
            published.append({k: q.get(k) for k in PUBLISH_FIELDS})
        report.append({"q_id": q["q_id"], "published": reason is None, "reason": reason,
                       "manual_approved": q["q_id"] in approved and reason is None and bool(r and r.get("refused")),
                       "our_answer": q["answer"], "blind_answer": r.get("answer") if r else None,
                       "confidence": r.get("confidence") if r else None,
                       "blind_working": r.get("working") if r else None})

    practice = {"exam": "neet", "subject": subject["subject_id"], "unit_id": unit["unit_id"],
                "slug": unit["slug"], "questions": published}
    (unit_dir / "practice.json").write_text(json.dumps(practice, indent=2, ensure_ascii=False),
                                            encoding="utf-8")
    (unit_dir / "_practice_verify.json").write_text(json.dumps({"unit_id": unit["unit_id"], "model": MODEL,
                                                                "results": report}, indent=2, ensure_ascii=False),
                                                    encoding="utf-8")
    return unit["unit_id"], published, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", nargs="*")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    syllabus = json.loads(SYLLABUS.read_text(encoding="utf-8"))
    jobs = [(s, u) for s in syllabus["subjects"] for u in s["units"]
            if (not args.units or u["unit_id"] in args.units)
            and (GEN_DIR / s["subject_id"] / u["slug"] / "_practice_draft.json").exists()]

    print(f"Model: {MODEL} | workers: {WORKERS} | units: {len(jobs)}")
    total_pub = total = 0
    rejected = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(verify_unit, s, u, args.force) for s, u in jobs]
        for f in as_completed(futures):
            unit_id, published, report = f.result()
            total += len(report)
            total_pub += len(published)
            low = sum(1 for r in report if r["published"] and r["confidence"] == "low")
            print(f"  {unit_id}: published {len(published)}/{len(report)}"
                  + (f" | low-confidence passes {low}" if low else ""))
            rejected += [(unit_id, r) for r in report if not r["published"]]

    print(f"\nPublished: {total_pub} / {total}")
    print(f"Rejected: {len(rejected)}")
    for unit_id, r in rejected:
        print(f"  {r['q_id']}: {r['reason']} | ours {r['our_answer']} | blind {r['blind_answer']}"
              f" ({r['confidence']})")


if __name__ == "__main__":
    main()