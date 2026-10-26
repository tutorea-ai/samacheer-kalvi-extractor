"""
Generate original NEET practice questions (5 per syllabus topic), grounded in our verified unit notes.

Stage 1 of 2. Output is a DRAFT; practice_verify.py writes the published practice.json.

- Code plans every question: type, difficulty, correct-option position (balanced 1-4).
- Topics sent in chunks of 4 (20 questions per call); each chunk cached.
- Validates structure, answer position and LaTeX; flags near-copies of real PYQs and duplicates.
- Output: generated/{subject}/{slug}/_practice_draft.json  (underscore = never synced to Node)

Usage:
    python -m app.exams.neet.builders.practice --units phy_u06 che_u12 bio_u09   # test
    python -m app.exams.neet.builders.practice                                   # all 50
    python -m app.exams.neet.builders.practice --units phy_u06 --force           # regenerate
"""
import argparse
import difflib
import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.exams.common.latex_lint import check as latex_check
from app.exams.common.llm import RefusalError, call_json
from app.exams.common.tagger import question_text

ROOT = Path(__file__).resolve().parents[4]
EXAM_DIR = ROOT / "exams_data/neet"
SYLLABUS = EXAM_DIR / "syllabus/neet_2026.json"
PYQ_PAPERS = [EXAM_DIR / "pyq/re_neet_2026.json"]
GEN_DIR = EXAM_DIR / "generated"
CACHE_DIR = GEN_DIR / "_cache/practice"

MODEL = os.getenv("NEET_PRACTICE_MODEL", "claude-opus-5-5")
WORKERS = int(os.getenv("NEET_PRACTICE_WORKERS", "4"))
PER_TOPIC = 5
CHUNK = 4                       # topics per Claude call
SPECIAL_TYPES = ["assertion_reason", "statement_pair", "match_list", "multi_statement"]
DIFFICULTY = ["easy", "medium", "medium", "medium", "hard"]
NEAR_PYQ_RATIO = 0.8
FIXED_OPTIONS = {
    "assertion_reason": {"Both A and R are true and R is the correct explanation of A",
                         "Both A and R are true but R is not the correct explanation of A",
                         "A is true but R is false", "A is false but R is true"},
    "statement_pair": {"Both Statement I and Statement II are correct",
                       "Both Statement I and Statement II are incorrect",
                       "Statement I is correct but Statement II is incorrect",
                       "Statement I is incorrect but Statement II is correct"},
}

PROMPT = """You are a senior NEET (UG) paper setter writing ORIGINAL practice questions.

SUBJECT: {subject}
UNIT {unit_no}: {unit_name}

VERIFIED STUDY NOTES FOR THESE TOPICS (the only source of facts you may test):
{notes}

REAL NEET QUESTIONS FROM THIS UNIT (style and difficulty reference ONLY; never copy, paraphrase,
or reuse their numbers, setups or option sets):
{pyqs}

WRITE EXACTLY THESE QUESTIONS, one per slot, in this order:
{slots}

Each slot fixes the topic, the question type, the difficulty and the position (1-4) of the correct
option. The correct option MUST be at that position.

Question types:
- single_correct: a stem and 4 options, exactly one correct.{numerical_rule}
The page shows the stem FIRST and the statements or lists AFTER it, so a stem must never say "above"
and must never repeat the statements. Use these stems and option texts EXACTLY (only reorder options
so the correct one is at the given position):
- assertion_reason: statements {{"A": "...", "R": "..."}}.
  Stem: "Given below are two statements: Assertion A and Reason R. Choose the correct answer."
  Options: "Both A and R are true and R is the correct explanation of A" /
           "Both A and R are true but R is not the correct explanation of A" /
           "A is true but R is false" / "A is false but R is true".
- statement_pair: statements {{"I": "...", "II": "..."}}.
  Stem: "Given below are two statements. Choose the most appropriate answer."
  Options: "Both Statement I and Statement II are correct" /
           "Both Statement I and Statement II are incorrect" /
           "Statement I is correct but Statement II is incorrect" /
           "Statement I is incorrect but Statement II is correct".
- match_list: match_lists with exactly 4 items each, List-I labels A-D and List-II labels I-IV.
  Stem: "Match List-I with List-II and choose the correct answer."
  Options: 4 different complete matchings written like "A-II, B-I, C-IV, D-III".
- multi_statement: statements {{"A": "...", "B": "...", "C": "...", "D": "..."}} (4 or 5 statements).
  Stem: "Which of the following statements are correct?" (a short topic phrase may be added, e.g.
  "Which of the following statements about the cyanide process are correct?").
  Options are combinations like "A, B and D only".

Return ONLY a JSON object, no commentary:
{{"questions": [
  {{"slot": "t00_1", "type": "single_correct", "question": "...", "statements": null, "match_lists": null,
    "options": ["...", "...", "...", "..."], "answer": 2,
    "solution": {{"key_concept": "...", "steps": ["...", "..."], "final_answer": "Option (2): ...",
                  "why_not_others": "...", "common_trap": "...", "time_saving_tip": null}} }}
]}}
match_lists shape: {{"list_I": [{{"label": "A", "text": "..."}}], "list_II": [{{"label": "I", "text": "..."}}]}}

Rules:
- Test only facts stated in the notes above. Each question must have exactly one defensible correct option.
- 4 distinct options, without "(1)" labels. No "all of the above", "none of the above", or options that
  refer to other options.
- Distractors must be plausible: common mistakes, sign errors, wrong units, confused terms.
- Numericals: choose values that give a clean answer and check the arithmetic twice. Each wrong option
  should come from a realistic mistake.
- No figures: every question must be fully answerable from its text.
- Write all mathematics and chemical formulas in LaTeX inside $...$. Plain text only, no markdown.
- Solution: 2-6 short steps; final_answer names the correct option number and its text.
- If a type truly cannot work for a topic, use single_correct for that slot and keep the same answer position.
- Do not mention any coaching institute, book, website or exam year.
"""

NUMERICAL_RULE = {
    "physics": " About half of the single_correct questions should be numericals.",
    "chemistry": " For physical-chemistry topics, about half of the single_correct questions should be numericals.",
    "biology": "",
}


def plan_unit(unit: dict) -> list:
    """Fix type, difficulty and correct-option position for every question of the unit."""
    rng = random.Random(unit["unit_id"])
    n = len(unit["topics"]) * PER_TOPIC
    positions = [(i % 4) + 1 for i in range(n)]
    rng.shuffle(positions)
    plan, k = [], 0
    for t_idx in range(len(unit["topics"])):
        specials = [SPECIAL_TYPES[(t_idx * 2) % 4], SPECIAL_TYPES[(t_idx * 2 + 1) % 4]]
        types = ["single_correct"] * 3 + specials
        for j in range(PER_TOPIC):
            plan.append({"slot": f"t{t_idx:02d}_{j + 1}", "topic_index": t_idx, "type": types[j],
                         "difficulty": DIFFICULTY[j], "answer_position": positions[k]})
            k += 1
    return plan


def notes_block(notes: dict, topic_indexes: list) -> str:
    by_idx = {t["topic_index"]: t for t in notes["topics"]}
    parts = []
    for i in topic_indexes:
        t = by_idx.get(i)
        if not t:
            continue
        formulas = "; ".join(f"{f['formula']} ({f['meaning']})" for f in t.get("formulas", []))
        parts.append(f"[t{i:02d}] {t['topic']}\n{t['explanation']}\n"
                     f"Key points: {' | '.join(t.get('key_points', []))}"
                     + (f"\nFormulas: {formulas}" if formulas else ""))
    parts.append("Common traps for the unit: " + " | ".join(notes.get("common_traps", [])))
    return "\n\n".join(parts)


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def content_key(q: dict) -> str:
    """Text used for similarity checks (statements when present, since their stems are boilerplate)."""
    body = " ".join(strings(q.get("statements"))) or q.get("question", "")
    body += " " + " ".join(strings(q.get("match_lists")))
    return re.sub(r"\s+", " ", body.lower()).strip()


def validate(q: dict, slot: dict) -> list:
    flags = []
    opts = q.get("options") or []
    if len(opts) != 4:
        flags.append(f"options_count_{len(opts)}")
    if len({re.sub(r"\s+", "", o) for o in opts}) < len(opts):
        flags.append("duplicate_options")
    if q.get("answer") != slot["answer_position"]:
        flags.append("wrong_answer_position")
    qtype = q.get("type")
    if qtype not in (slot["type"], "single_correct"):
        flags.append("wrong_type")
    if qtype in ("assertion_reason", "statement_pair", "multi_statement") and not q.get("statements"):
        flags.append("missing_statements")
    if qtype == "match_list":
        ml = q.get("match_lists") or {}
        if len(ml.get("list_I", [])) != 4 or len(ml.get("list_II", [])) != 4:
            flags.append("bad_match_lists")
    if qtype in FIXED_OPTIONS and set(opts) != FIXED_OPTIONS[qtype]:
        flags.append("nonstandard_options")
    stem = (q.get("question") or "").lower()
    if re.search(r"\bgiven above\b|\babove (statements|lists|options)\b|\bstatements above\b", stem):
        flags.append("stem_says_above")
    if any(len(s) > 20 and s.lower()[:40] in stem for s in strings(q.get("statements"))):
        flags.append("stem_repeats_statements")
    sol = q.get("solution") or {}
    if not sol.get("steps") or not sol.get("final_answer"):
        flags.append("incomplete_solution")
    if any(latex_check(s) for s in strings([q.get("question"), opts, q.get("statements"),
                                            q.get("match_lists"), sol])):
        flags.append("latex_error")
    return flags


def load_pyqs() -> tuple:
    by_unit, keys = {}, []
    for paper_file in PYQ_PAPERS:
        for q in json.loads(paper_file.read_text(encoding="utf-8"))["questions"]:
            if q["status"] == "normal" and q.get("unit_id"):
                by_unit.setdefault(q["unit_id"], []).append(q)
                keys.append((q["q_id"], content_key(q)))
    return by_unit, keys


def generate_chunk(subject, unit, notes, pyqs, slots, chunk_no, force) -> list:
    cache_file = CACHE_DIR / f"{unit['unit_id']}_c{chunk_no:02d}.json"
    if cache_file.exists() and not force:
        return json.loads(cache_file.read_text(encoding="utf-8"))["questions"]
    topic_idx = sorted({s["topic_index"] for s in slots})
    prompt = PROMPT.format(
        subject=subject["subject_name"],
        unit_no=unit["unit_no"],
        unit_name=unit["unit_name"],
        notes=notes_block(notes, topic_idx),
        pyqs="\n\n".join(question_text(q) for q in pyqs[:6]) or "(none)",
        slots="\n".join(f"- slot {s['slot']} | topic t{s['topic_index']:02d}: "
                        f"{unit['topics'][s['topic_index']]} | type: {s['type']} | "
                        f"difficulty: {s['difficulty']} | correct option at position {s['answer_position']}"
                        for s in slots),
        numerical_rule=NUMERICAL_RULE[subject["subject_id"]],
    )
    try:
        result = call_json(prompt, model=MODEL, max_tokens=32000)
    except RefusalError:
        print(f"     ⚠ {unit['unit_id']} chunk {chunk_no}: generation declined by the model; slots left missing")
        return []                                                   # not cached: retried next run
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result["questions"]


def build_unit(subject, unit, pyqs, pyq_keys, force) -> tuple:
    unit_dir = GEN_DIR / subject["subject_id"] / unit["slug"]
    notes = json.loads((unit_dir / "notes.json").read_text(encoding="utf-8"))
    plan = plan_unit(unit)
    chunks = [[s for s in plan if s["topic_index"] // CHUNK == c]
              for c in range((len(unit["topics"]) + CHUNK - 1) // CHUNK)]

    raw = {}
    for c, slots in enumerate(chunks, 1):
        for q in generate_chunk(subject, unit, notes, pyqs, slots, c, force):
            raw[q.get("slot")] = q

    questions, seen = [], {}
    for slot in plan:
        q = raw.get(slot["slot"])
        if not q:
            continue
        flags = validate(q, slot)
        key = content_key(q)
        if key in seen:
            flags.append(f"duplicate_of_{seen[key]}")
        seen.setdefault(key, slot["slot"])
        for pyq_id, pyq_key in pyq_keys:
            if difflib.SequenceMatcher(None, key, pyq_key).ratio() >= NEAR_PYQ_RATIO:
                flags.append(f"near_pyq_{pyq_id}")
        sol = q.get("solution") or {}
        questions.append({
            "q_id": f"neet_{unit['unit_id']}_{slot['slot']}",
            "source": "generated",
            "subject": subject["subject_id"],
            "unit_id": unit["unit_id"],
            "topic": unit["topics"][slot["topic_index"]],
            "topic_index": slot["topic_index"],
            "type": q.get("type"),
            "difficulty": slot["difficulty"],
            "question": q.get("question", ""),
            "statements": q.get("statements"),
            "match_lists": q.get("match_lists"),
            "options": q.get("options") or [],
            "image": None,
            "answer": [q.get("answer")],
            "status": "normal",
            "solution": {k: sol.get(k) for k in ("key_concept", "steps", "final_answer",
                                                 "why_not_others", "common_trap", "time_saving_tip")},
            "review_flags": flags,
        })

    draft = {"exam": "neet", "subject": subject["subject_id"], "unit_id": unit["unit_id"],
             "slug": unit["slug"], "questions": questions,
             "_meta": {"model": MODEL, "expected": len(plan),
                       "missing_slots": [s["slot"] for s in plan if s["slot"] not in raw]}}
    (unit_dir / "_practice_draft.json").write_text(json.dumps(draft, indent=2, ensure_ascii=False),
                                                   encoding="utf-8")
    return unit["unit_id"], draft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", nargs="*")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    syllabus = json.loads(SYLLABUS.read_text(encoding="utf-8"))
    pyqs, pyq_keys = load_pyqs()
    jobs = [(s, u) for s in syllabus["subjects"] for u in s["units"]
            if not args.units or u["unit_id"] in args.units]

    print(f"Model: {MODEL} | workers: {WORKERS} | units: {len(jobs)}")
    totals = {"questions": 0, "flagged": 0, "missing": 0}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(build_unit, s, u, pyqs.get(u["unit_id"], []), pyq_keys, args.force)
                   for s, u in jobs]
        for f in as_completed(futures):
            unit_id, draft = f.result()
            qs = draft["questions"]
            flagged = [q for q in qs if q["review_flags"]]
            missing = draft["_meta"]["missing_slots"]
            totals["questions"] += len(qs)
            totals["flagged"] += len(flagged)
            totals["missing"] += len(missing)
            pos = [q["answer"][0] for q in qs]
            spread = " ".join(f"({i}){pos.count(i)}" for i in range(1, 5))
            print(f"  {unit_id}: {len(qs)}/{draft['_meta']['expected']} | flagged {len(flagged)}"
                  f" | answers {spread}" + (f" | ⚠ missing {missing}" if missing else ""))
            for q in flagged:
                print(f"     {q['q_id']}: {q['review_flags']}")

    print(f"\nTotal questions: {totals['questions']} | flagged: {totals['flagged']}"
          f" | missing: {totals['missing']}")


if __name__ == "__main__":
    main()