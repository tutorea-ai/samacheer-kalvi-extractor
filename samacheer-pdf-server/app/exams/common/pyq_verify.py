"""
Blind verification: solve each PYQ WITHOUT the answer, compare with the NTA key.

- Does not modify solutions; only flags mismatches for human review.
- Diagram questions get their source page image.
- Each result cached; summary saved to a verify file.

Usage:
    python -m app.exams.common.pyq_verify
    python -m app.exams.common.pyq_verify --q 12 47 --force
"""
import argparse
import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic

from app.config import settings
from app.exams.common.tagger import question_text, parse_json

ROOT = Path(__file__).resolve().parents[3]
EXAM = "neet"
PAPER_ID = "re_neet_2026"
PAPER = ROOT / f"exams_data/{EXAM}/pyq/{PAPER_ID}.json"
PAGES_DIR = ROOT / f"exams_data/{EXAM}/pyq/_pages/{PAPER_ID}"
CACHE_DIR = ROOT / f"exams_data/{EXAM}/pyq/_cache/{PAPER_ID}_verify"
VERIFY_OUT = ROOT / f"exams_data/{EXAM}/pyq/{PAPER_ID}_verify.json"

MODEL = os.getenv("NEET_VERIFY_MODEL", "claude-opus-5-5")
WORKERS = int(os.getenv("NEET_VERIFY_WORKERS", "4"))
RETRY_STATUS = {429, 500, 502, 503, 529}

PROMPT = """Solve this NEET (UG) multiple-choice question. Exactly one option is intended to be correct.
{image_line}
QUESTION:
{question}

Work it out carefully and briefly, then choose the option.

Return ONLY a JSON object, no commentary:
{{
  "working": "brief working (a few lines)",
  "answer": 2,
  "confidence": "high | medium | low"
}}
"answer" is the option number 1-4.
"""


def call_claude(client, content: list, max_retries: int = 5) -> dict:
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=3000,
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


def build_content(q: dict) -> list:
    needs_image = q.get("has_diagram") or q.get("options_are_diagrams")
    content = []
    if needs_image:
        for p in q.get("source_pages", []):
            img = PAGES_DIR / f"page-{p:02d}.png"
            if img.exists():
                content.append({"type": "image", "source": {
                    "type": "base64", "media_type": "image/png",
                    "data": base64.standard_b64encode(img.read_bytes()).decode()}})
    image_line = (f"The attached page image contains this question (Q{q['q_no']}) with its figure. "
                  "Use the figure; ignore other questions and the background watermark.\n"
                  if needs_image else "")
    content.append({"type": "text", "text": PROMPT.format(image_line=image_line, question=question_text(q))})
    return content


def verify(client, q: dict, force: bool) -> tuple:
    cache_file = CACHE_DIR / f"q{q['q_no']:03d}.json"
    if cache_file.exists() and not force:
        return q["q_no"], json.loads(cache_file.read_text(encoding="utf-8")), True
    result = call_claude(client, build_content(q))
    result["_model"] = MODEL
    cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return q["q_no"], result, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", type=int, nargs="*")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    paper = json.loads(PAPER.read_text(encoding="utf-8"))
    targets = [q for q in paper["questions"]
               if q["status"] == "normal" and (not args.q or q["q_no"] in args.q)]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    print(f"Model: {MODEL} | workers: {WORKERS} | questions: {len(targets)}")
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(verify, client, q, args.force) for q in targets]
        for f in as_completed(futures):
            f.result()
            done += 1
            if done % 20 == 0 or done == len(targets):
                print(f"  {done}/{len(targets)} done")

    # Compare every cached result with the official key
    results = {int(f.stem[1:]): json.loads(f.read_text(encoding="utf-8"))
               for f in sorted(CACHE_DIR.glob("q*.json"))}
    mismatches, low_conf_matches, checked = [], [], 0

    for q in paper["questions"]:
        flags = [x for x in q["review_flags"] if x != "blind_mismatch"]
        r = results.get(q["q_no"])
        if r and q["status"] == "normal":
            checked += 1
            blind = r.get("answer")
            if blind not in q["answer"]:
                flags.append("blind_mismatch")
                mismatches.append((q["q_no"], q["subject"], blind, q["answer"], r.get("confidence")))
            elif r.get("confidence") == "low":
                low_conf_matches.append(q["q_no"])
        q["review_flags"] = flags

    VERIFY_OUT.write_text(json.dumps(
        {"paper_id": PAPER_ID, "model": MODEL,
         "results": {str(k): v for k, v in sorted(results.items())}},
        indent=2, ensure_ascii=False), encoding="utf-8")
    PAPER.write_text(json.dumps(paper, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved: {VERIFY_OUT}")
    print(f"Checked: {checked} | Matches NTA key: {checked - len(mismatches)} | Mismatches: {len(mismatches)}")
    for n, subj, blind, key, conf in mismatches:
        print(f"  Q{n} [{subj}]: blind={blind}  NTA={key}  confidence={conf}")
    print(f"Matched but low confidence: {low_conf_matches}")


if __name__ == "__main__":
    main()