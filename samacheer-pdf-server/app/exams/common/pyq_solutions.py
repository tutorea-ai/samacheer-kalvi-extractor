"""
Generate step-by-step solutions for PYQ questions using Claude.

- One question per call; official NTA answer is given to the model.
- Model independently verifies; disagreements are flagged, never silently applied.
- Diagram questions get their source page image.
- Each solution cached separately; saved to a solutions file and applied to the paper.

Usage:
    python -m app.exams.common.pyq_solutions --q 5 13 26 38 72 160   # test a few
    python -m app.exams.common.pyq_solutions                         # all
    python -m app.exams.common.pyq_solutions --q 38 --force          # redo one
"""
import argparse
import base64
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic

from app.config import settings
from app.exams.common.tagger import question_text, parse_json

ROOT = Path(__file__).resolve().parents[3]
EXAM = "neet"
PAPER_ID = "re_neet_2026"
SYLLABUS = ROOT / f"exams_data/{EXAM}/syllabus/neet_2026.json"
PAPER = ROOT / f"exams_data/{EXAM}/pyq/{PAPER_ID}.json"
PAGES_DIR = ROOT / f"exams_data/{EXAM}/pyq/_pages/{PAPER_ID}"
CACHE_DIR = ROOT / f"exams_data/{EXAM}/pyq/_cache/{PAPER_ID}_solutions"
SOLUTIONS_OUT = ROOT / f"exams_data/{EXAM}/pyq/{PAPER_ID}_solutions.json"

MODEL = os.getenv("NEET_SOLUTION_MODEL", "claude-opus-5-5")
WORKERS = int(os.getenv("NEET_SOLUTION_WORKERS", "4"))
RETRY_STATUS = {429, 500, 502, 503, 529}

PROMPT = """You are an experienced NEET faculty member writing the official solution for one exam question.
Your reader is a NEET aspirant revising for the exam.

SUBJECT: {subject}
UNIT: {unit}
TOPIC: {topic}

QUESTION:
{question}

{answer_line}

Write a clear, exam-focused solution. Work the problem out yourself and check it against the
official answer. If your own working leads to a different option, do NOT force it: write your
honest working, set "agrees_with_key" to false and explain in "key_check_note".
{image_line}

Return ONLY a JSON object, no commentary:
{{
  "key_concept": "the one core idea or formula this question tests (one sentence)",
  "steps": ["step 1", "step 2", "..."],
  "final_answer": "Option (n): the option text",
  "why_not_others": "one or two sentences on why the tempting wrong options fail, or null",
  "common_trap": "the mistake students usually make here (one sentence)",
  "time_saving_tip": "a faster exam approach if one exists, otherwise null",
  "agrees_with_key": true,
  "key_check_note": null
}}

Rules:
- Write all mathematics and chemical formulas in LaTeX inside $...$.
- 2 to 8 short steps. Show the key substitution for numericals.
- For statement / assertion-reason / match questions, judge each statement or pair in the steps.
- Do not mention any coaching institute, book or website.
"""


def call_claude(client, content: list, max_retries: int = 5) -> dict:
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": content}],
            )
            text = "".join(b.text for b in resp.content if b.type == "text")
            return parse_json(text)
        except anthropic.APIStatusError as e:
            if e.status_code in RETRY_STATUS and attempt < max_retries:
                time.sleep(30)
                continue
            raise
        except anthropic.APIConnectionError:
            if attempt < max_retries:
                time.sleep(30)
                continue
            raise
        except json.JSONDecodeError:
            if attempt < max_retries:
                continue
            raise


def answer_line(q: dict) -> str:
    opts = q["options"]
    if q["status"] == "dropped":
        return ("OFFICIAL STATUS: NTA DROPPED this question (all candidates awarded marks). "
                "Solve it as intended, then use key_check_note to explain briefly what makes it "
                "ambiguous or flawed. Set agrees_with_key to true and final_answer to your best option.")
    ans = q["answer"]
    listed = ", ".join(f"({a}) {opts[a - 1]}" for a in ans if 1 <= a <= len(opts))
    if len(ans) > 1:
        return (f"OFFICIAL ANSWER (NTA): BOTH options {listed} were accepted. "
                "Explain why each accepted option is valid.")
    return f"OFFICIAL ANSWER (NTA): {listed}"


def build_content(q: dict, unit_name: str) -> list:
    needs_image = q.get("has_diagram") or q.get("options_are_diagrams")
    prompt = PROMPT.format(
        subject=q["subject"].title(),
        unit=unit_name or "unknown",
        topic=q.get("topic") or "unknown",
        question=question_text(q),
        answer_line=answer_line(q),
        image_line=(f"The attached page image contains this question (Q{q['q_no']}) with its figure. "
                    "Use the figure; ignore other questions and the background watermark.")
                   if needs_image else "",
    )
    content = []
    if needs_image:
        for p in q.get("source_pages", []):
            img = PAGES_DIR / f"page-{p:02d}.png"
            if img.exists():
                content.append({"type": "image", "source": {
                    "type": "base64", "media_type": "image/png",
                    "data": base64.standard_b64encode(img.read_bytes()).decode()}})
    content.append({"type": "text", "text": prompt})
    return content


def solve(client, q: dict, unit_name: str, force: bool) -> tuple:
    cache_file = CACHE_DIR / f"q{q['q_no']:03d}.json"
    if cache_file.exists() and not force:
        return q["q_no"], json.loads(cache_file.read_text(encoding="utf-8")), True
    result = call_claude(client, build_content(q, unit_name))
    result["_model"] = MODEL
    cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return q["q_no"], result, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", type=int, nargs="*", help="question numbers (default: all)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    syllabus = json.loads(SYLLABUS.read_text(encoding="utf-8"))
    paper = json.loads(PAPER.read_text(encoding="utf-8"))
    unit_names = {u["unit_id"]: u["unit_name"] for s in syllabus["subjects"] for u in s["units"]}

    targets = [q for q in paper["questions"]
               if q["status"] != "hidden" and (not args.q or q["q_no"] in args.q)]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    print(f"Model: {MODEL} | workers: {WORKERS} | questions: {len(targets)}")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(solve, client, q, unit_names.get(q["unit_id"]), args.force)
                   for q in targets]
        for f in as_completed(futures):
            n, _, cached = f.result()
            print(f"  Q{n}: {'cached' if cached else 'solved'}")

    # Collect every cached solution and apply to the paper
    solutions = {}
    for f in sorted(CACHE_DIR.glob("q*.json")):
        n = int(f.stem[1:])
        solutions[n] = json.loads(f.read_text(encoding="utf-8"))

    disagreements = []
    for q in paper["questions"]:
        flags = [x for x in q["review_flags"] if x != "solution_disagrees_with_key"]
        sol = solutions.get(q["q_no"])
        q["solution"] = {k: v for k, v in sol.items() if not k.startswith("_")} if sol else None
        if sol and sol.get("agrees_with_key") is False:
            flags.append("solution_disagrees_with_key")
            disagreements.append((q["q_no"], sol.get("key_check_note")))
        q["review_flags"] = flags

    SOLUTIONS_OUT.write_text(json.dumps(
        {"paper_id": PAPER_ID, "solutions": {str(k): v for k, v in sorted(solutions.items())}},
        indent=2, ensure_ascii=False), encoding="utf-8")
    PAPER.write_text(json.dumps(paper, indent=2, ensure_ascii=False), encoding="utf-8")

    solved = sum(1 for q in paper["questions"] if q["solution"])
    print(f"\nSaved: {SOLUTIONS_OUT}")
    print(f"Questions with solutions: {solved} / {len(paper['questions'])}")
    print(f"Disagreements with official key: {len(disagreements)}")
    for n, note in disagreements:
        print(f"  Q{n}: {note}")


if __name__ == "__main__":
    main()