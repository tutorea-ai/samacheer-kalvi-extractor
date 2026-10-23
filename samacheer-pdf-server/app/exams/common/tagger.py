"""
Tag each PYQ question with its syllabus unit and topic using Claude.

- Batches questions per subject and sends only that subject's units.
- Caches each batch (re-runs are free).
- Saves tags to a separate file, then applies them to the paper JSON.
- Prints unit-wise weightage at the end.

Usage:
    python -m app.exams.common.tagger
    python -m app.exams.common.tagger --force      # re-tag everything
"""
import argparse
import json
import os
import re
import time
from collections import Counter
from pathlib import Path

import anthropic

from app.config import settings

ROOT = Path(__file__).resolve().parents[3]
EXAM = "neet"
PAPER_ID = "re_neet_2026"
SYLLABUS = ROOT / f"exams_data/{EXAM}/syllabus/neet_2026.json"
PAPER = ROOT / f"exams_data/{EXAM}/pyq/{PAPER_ID}.json"
TAGS_OUT = ROOT / f"exams_data/{EXAM}/pyq/{PAPER_ID}_tags.json"
CACHE_DIR = ROOT / f"exams_data/{EXAM}/pyq/_cache/{PAPER_ID}_tags"

MODEL = os.getenv("NEET_TAG_MODEL", "claude-opus-5-5")
BATCH_SIZE = 15
RETRY_STATUS = {429, 500, 502, 503, 529}

PROMPT = """You are classifying NEET (UG) exam questions against the official NEET syllabus.

SUBJECT: {subject_name}

SYLLABUS UNITS (unit_id | unit name, then numbered topics):
{units_block}

QUESTIONS:
{questions_block}

For EACH question, choose the single best unit and the single best topic within that unit.
If a question genuinely does not belong to any unit above, set out_of_syllabus to true.

Return ONLY a JSON object, no commentary:
{{
  "tags": [
    {{"q_no": 13, "unit_id": "phy_u06", "topic_index": 4, "confidence": "high", "out_of_syllabus": false}}
  ]
}}

Rules:
- unit_id must be one of the unit_ids listed above.
- topic_index is the number shown before the topic (t0, t1, ...) -> use the integer only.
- confidence: "high" if clearly within the topic, "medium" if it spans topics, "low" if unsure.
- Include every question listed, in the same order.
"""


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    return json.loads(text[start:end + 1])


def call_claude(client, prompt: str, max_retries: int = 5) -> dict:
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )
            text = "".join(b.text for b in resp.content if b.type == "text")
            return parse_json(text)
        except anthropic.APIStatusError as e:
            if e.status_code in RETRY_STATUS and attempt < max_retries:
                print(f"    API {e.status_code}, retrying in 30s (attempt {attempt}/{max_retries})")
                time.sleep(30)
                continue
            raise
        except anthropic.APIConnectionError:
            if attempt < max_retries:
                print(f"    Connection error, retrying in 30s (attempt {attempt}/{max_retries})")
                time.sleep(30)
                continue
            raise
        except json.JSONDecodeError:
            if attempt < max_retries:
                print(f"    Bad JSON from model, retrying (attempt {attempt}/{max_retries})")
                continue
            raise


def units_block(subject: dict) -> str:
    lines = []
    for u in subject["units"]:
        lines.append(f"{u['unit_id']} | {u['unit_name']}")
        for i, t in enumerate(u["topics"]):
            lines.append(f"    t{i}: {t}")
    return "\n".join(lines)


def question_text(q: dict) -> str:
    parts = [f"Q{q['q_no']} [{q['type']}]", q.get("question", "")]
    st = q.get("statements")
    if st:
        parts += [f"  {k}: {v}" for k, v in st.items()]
    ml = q.get("match_lists")
    if ml:
        parts.append("  List-I: " + "; ".join(f"{x['label']}. {x['text']}" for x in ml.get("list_I", [])))
        parts.append("  List-II: " + "; ".join(f"{x['label']}. {x['text']}" for x in ml.get("list_II", [])))
    for i, opt in enumerate(q.get("options", []), 1):
        parts.append(f"  ({i}) {opt}")
    if q.get("diagram_description"):
        parts.append(f"  Figure: {q['diagram_description']}")
    return "\n".join(parts)


def tag_batch(client, subject: dict, batch: list, batch_no: int, force: bool) -> list:
    cache_file = CACHE_DIR / f"{subject['subject_id']}_{batch_no:02d}.json"
    if cache_file.exists() and not force:
        return json.loads(cache_file.read_text(encoding="utf-8"))["tags"]

    prompt = PROMPT.format(
        subject_name=subject["subject_name"],
        units_block=units_block(subject),
        questions_block="\n\n".join(question_text(q) for q in batch),
    )
    q_nos = [q["q_no"] for q in batch]
    print(f"  {subject['subject_id']} batch {batch_no}: Q{q_nos[0]}-Q{q_nos[-1]} calling Claude...")
    result = call_claude(client, prompt)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result["tags"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="ignore cache and re-tag")
    args = ap.parse_args()

    syllabus = json.loads(SYLLABUS.read_text(encoding="utf-8"))
    paper = json.loads(PAPER.read_text(encoding="utf-8"))
    subjects = {s["subject_id"]: s for s in syllabus["subjects"]}
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    print(f"Model: {MODEL}")
    all_tags = {}
    for subject_id, subject in subjects.items():
        qs = [q for q in paper["questions"] if q["subject"] == subject_id]
        for b in range(0, len(qs), BATCH_SIZE):
            batch = qs[b:b + BATCH_SIZE]
            for t in tag_batch(client, subject, batch, b // BATCH_SIZE + 1, args.force):
                all_tags[int(t["q_no"])] = t

    # Validate and apply tags
    unit_lookup = {u["unit_id"]: (s_id, u) for s_id, s in subjects.items() for u in s["units"]}
    problems = []
    for q in paper["questions"]:
        n = q["q_no"]
        flags = [f for f in q["review_flags"] if not f.startswith("tag_")]
        t = all_tags.get(n)

        if not t:
            problems.append(f"Q{n}: no tag returned")
            flags.append("tag_missing")
            q["unit_id"], q["topic"], q["out_of_syllabus"] = None, None, False
        else:
            q["out_of_syllabus"] = bool(t.get("out_of_syllabus"))
            unit = unit_lookup.get(t.get("unit_id"))
            if q["out_of_syllabus"]:
                q["unit_id"], q["topic"] = None, None
                flags.append("tag_out_of_syllabus")
            elif not unit or unit[0] != q["subject"]:
                problems.append(f"Q{n}: invalid unit_id {t.get('unit_id')}")
                flags.append("tag_invalid")
                q["unit_id"], q["topic"] = None, None
            else:
                idx = t.get("topic_index")
                topics = unit[1]["topics"]
                q["unit_id"] = unit[1]["unit_id"]
                q["topic"] = topics[idx] if isinstance(idx, int) and 0 <= idx < len(topics) else None
                if q["topic"] is None:
                    flags.append("tag_bad_topic_index")
                if t.get("confidence") == "low":
                    flags.append("tag_low_confidence")
        q["review_flags"] = flags

    TAGS_OUT.write_text(json.dumps(
        {"paper_id": PAPER_ID, "model": MODEL, "tags": {str(k): v for k, v in sorted(all_tags.items())}},
        indent=2, ensure_ascii=False), encoding="utf-8")
    PAPER.write_text(json.dumps(paper, indent=2, ensure_ascii=False), encoding="utf-8")

    # Weightage summary
    print(f"\nSaved tags: {TAGS_OUT}")
    print(f"Updated paper: {PAPER}")
    for subject_id, subject in subjects.items():
        counts = Counter(q["unit_id"] for q in paper["questions"]
                         if q["subject"] == subject_id and q["unit_id"])
        print(f"\n{subject['subject_name']} ({sum(counts.values())} tagged)")
        for u in subject["units"]:
            if counts[u["unit_id"]]:
                print(f"  {u['unit_no']:>2}. {u['unit_name']:<55} {counts[u['unit_id']]}")

    tag_flags = [(q["q_no"], [f for f in q["review_flags"] if f.startswith("tag_")])
                 for q in paper["questions"]]
    tag_flags = [(n, f) for n, f in tag_flags if f]
    print(f"\nTag issues: {len(tag_flags)}")
    for n, f in tag_flags:
        print(f"  Q{n}: {f}")
    for p in problems:
        print(f"  {p}")


if __name__ == "__main__":
    main()