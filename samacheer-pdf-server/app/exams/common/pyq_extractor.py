"""
Extract NEET PYQ questions from rendered page images using Claude vision.

- One Claude call per page; each page result is cached (re-runs are free).
- Handles questions that continue across pages (leading fragments).
- Merges answers from the NTA answer key JSON (dropped / multi-answer aware).
- Flags issues for human review: incomplete options, duplicate questions,
  duplicate options, diagram-dependent questions.

Usage:
    python app/exams/common/pyq_extractor.py --pages 2          # test one page
    python app/exams/common/pyq_extractor.py                    # all pages
    python app/exams/common/pyq_extractor.py --pages 5 --force  # redo a page
"""
import argparse
import base64
import json
import os
import re
import time
from pathlib import Path

import anthropic

from app.config import settings

ROOT = Path(__file__).resolve().parents[3]
PAPER_ID = "re_neet_2026"
BOOKLET_CODE = "50"
PAGES_DIR = ROOT / f"exams_data/neet/pyq/_pages/{PAPER_ID}"
CACHE_DIR = ROOT / f"exams_data/neet/pyq/_cache/{PAPER_ID}"
ANSWER_KEY = ROOT / f"exams_data/neet/pyq/{PAPER_ID}_answer_key.json"
OUTPUT = ROOT / f"exams_data/neet/pyq/{PAPER_ID}.json"

MODEL = os.getenv("NEET_EXTRACT_MODEL", "claude-opus-5-5")
DEFAULT_PAGES = list(range(2, 23))   # page 1 = instructions
TOTAL_QUESTIONS = 180

# NEET 2026 section split (Code 50)
SUBJECT_RANGES = [
    (1, 45, "physics"),
    (46, 90, "chemistry"),
    (91, 180, "biology"),
]

PROMPT = """You are extracting questions from one page of a NEET (UG) exam question paper.
The page has TWO columns. Read the LEFT column top to bottom, then the RIGHT column top to bottom.
Ignore the header line, page footer and the large background watermark logo.

Return ONLY a JSON object, no commentary, in exactly this shape:

{
  "leading_fragment": null or {
      "text": "any text at the very TOP of the LEFT column that continues a question from the previous page (no question number)",
      "options": ["option text", ...]
  },
  "questions": [
    {
      "q_no": 13,
      "type": "single_correct | assertion_reason | statement_pair | match_list | multi_statement",
      "question": "full question stem",
      "statements": null or {"A": "...", "R": "..."} or {"I": "...", "II": "..."} or {"a": "...", "b": "...", ...},
      "match_lists": null or {
          "list_I":  [{"label": "A", "text": "..."}, ...],
          "list_II": [{"label": "I", "text": "..."}, ...]
      },
      "options": ["text of option (1)", "text of option (2)", "text of option (3)", "text of option (4)"],
      "has_diagram": false,
      "diagram_description": null,
      "options_are_diagrams": false
    }
  ]
}

Rules:
- Write ALL mathematics in LaTeX inside $...$ (e.g. $\\mu_0 n^2 \\pi r^2 l$, $\\frac{v_2}{v_1}$, $10^{-31}$).
- Write chemical formulas in LaTeX too (e.g. $K_2Cr_2O_7$, $[Co(NH_3)_6]^{3+}$, $SO_4^{2-}$).
- Keep the exact wording of the question. Do not solve, rephrase or correct anything.
- options: exactly the 4 options in order, WITHOUT the "(1)" "(2)" labels.
- If a question's options continue onto the NEXT page, return only the options visible here.
- has_diagram: true if the question relies on a figure, circuit, graph, structure or table image.
  Then describe that figure precisely in diagram_description (values, labels, connections).
- options_are_diagrams: true if the options themselves are graphs/structures; then put a precise
  text description of each option's figure in the options list.
- Use the matching type: "Assertion A / Reason R" -> assertion_reason; "Statement I / Statement II"
  -> statement_pair; "Match List-I with List-II" -> match_list; lettered statements (a)(b)(c)
  with "choose the correct" -> multi_statement; everything else -> single_correct.
- Include EVERY question that starts on this page, even if its options are cut off.
"""

RETRY_STATUS = {429, 500, 502, 503, 529}


def parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise json.JSONDecodeError("No JSON object found", text, 0)
    return json.loads(text[start:end + 1])


def call_claude(client, img_path: Path, max_retries: int = 5) -> dict:
    data = base64.standard_b64encode(img_path.read_bytes()).decode()
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=16000,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}},
                        {"type": "text", "text": PROMPT},
                    ],
                }],
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


def extract_page(client, page_no: int, force: bool = False) -> dict:
    cache_file = CACHE_DIR / f"page-{page_no:02d}.json"
    if cache_file.exists() and not force:
        return json.loads(cache_file.read_text(encoding="utf-8"))

    img = PAGES_DIR / f"page-{page_no:02d}.png"
    if not img.exists():
        raise FileNotFoundError(img)

    print(f"  Page {page_no:02d}: calling Claude...")
    result = call_claude(client, img)
    result["_page"] = page_no
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def merge_pages(page_results: list) -> dict:
    """Combine page results; attach leading fragments to the previous page's last question."""
    questions = {}
    last_q_no = None

    for page in sorted(page_results, key=lambda p: p["_page"]):
        frag = page.get("leading_fragment")
        if frag and last_q_no is not None:
            prev = questions[last_q_no]
            if frag.get("text"):
                prev["question"] = (prev["question"] + " " + frag["text"]).strip()
            if frag.get("options"):
                prev["options"] = (prev.get("options") or []) + frag["options"]
            prev.setdefault("_pages", []).append(page["_page"])

        for q in page.get("questions", []):
            n = int(q["q_no"])
            q["_pages"] = [page["_page"]]
            if n in questions:
                # Same question seen twice: keep the more complete option list
                existing = questions[n]
                if len(q.get("options") or []) > len(existing.get("options") or []):
                    existing["options"] = q["options"]
                existing["_pages"].append(page["_page"])
            else:
                questions[n] = q
            last_q_no = n

    return questions


def subject_for(q_no: int) -> str:
    for lo, hi, subj in SUBJECT_RANGES:
        if lo <= q_no <= hi:
            return subj
    return "unknown"


def normalize(text) -> str:
    """Exact comparison key: ignore whitespace only (keep case, symbols, signs)."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = json.dumps(text, sort_keys=True, ensure_ascii=False)
    return re.sub(r"\s+", "", text)


def build_final(questions: dict, answer_key: dict) -> dict:
    code = answer_key["codes"][BOOKLET_CODE]
    dropped = set(code["dropped"])
    seen_stems = {}
    final = []

    for n in sorted(questions):
        q = questions[n]
        flags = []

        options = q.get("options") or []
        if len(options) != 4:
            flags.append(f"options_count_{len(options)}")
        if len(set(normalize(o) for o in options)) < len(options):
            flags.append("duplicate_options")
        if q.get("has_diagram") or q.get("options_are_diagrams"):
            flags.append("needs_image")

        stem_key = "|".join([
            normalize(q.get("question")),
            normalize(q.get("statements")),
            normalize(q.get("match_lists")),
            *(normalize(o) for o in options),
        ])
        if stem_key in seen_stems:
            flags.append(f"duplicate_of_q{seen_stems[stem_key]}")
        else:
            seen_stems[stem_key] = n

        final.append({
            "q_id": f"{PAPER_ID}_c{BOOKLET_CODE}_q{n:03d}",
            "source": "pyq",
            "exam_ref": f"NEET (UG) 2026 · Code {BOOKLET_CODE} · Q{n}",
            "q_no": n,
            "subject": subject_for(n),
            "unit_id": None,       # filled by tagger
            "topic": None,         # filled by tagger
            "type": q.get("type", "single_correct"),
            "question": q.get("question", ""),
            "statements": q.get("statements"),
            "match_lists": q.get("match_lists"),
            "options": options,
            "has_diagram": bool(q.get("has_diagram")),
            "diagram_description": q.get("diagram_description"),
            "options_are_diagrams": bool(q.get("options_are_diagrams")),
            "image": None,         # filled after diagram cropping
            "answer": code["answers"][str(n)],
            "status": "dropped" if n in dropped else "normal",
            "solution": None,      # filled by solutions builder
            "review_flags": flags,
            "source_pages": q.get("_pages", []),
        })

    return {
        "exam": "neet",
        "paper_id": PAPER_ID,
        "paper_name": "NEET (UG) 2026",
        "booklet_code": BOOKLET_CODE,
        "exam_date": answer_key.get("exam_date"),
        "answer_source": answer_key.get("source"),
        "total_questions": TOTAL_QUESTIONS,
        "questions": final,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, nargs="*", help="page numbers to process (default: all)")
    ap.add_argument("--force", action="store_true", help="ignore cache and re-call Claude")
    args = ap.parse_args()

    pages = args.pages or DEFAULT_PAGES
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    print(f"Model: {MODEL}")
    for p in pages:
        res = extract_page(client, p, force=args.force)
        q_nos = [q["q_no"] for q in res.get("questions", [])]
        frag = "yes" if res.get("leading_fragment") else "no"
        print(f"  Page {p:02d}: questions {q_nos} | leading_fragment={frag}")

    # Build the final file from everything cached so far
    cached = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(CACHE_DIR.glob("page-*.json"))]
    questions = merge_pages(cached)
    answer_key = json.loads(ANSWER_KEY.read_text(encoding="utf-8"))
    data = build_final(questions, answer_key)
    OUTPUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    found = {q["q_no"] for q in data["questions"]}
    missing = [n for n in range(1, TOTAL_QUESTIONS + 1) if n not in found]
    flagged = [q for q in data["questions"] if q["review_flags"]]

    print(f"\nSaved: {OUTPUT}")
    print(f"Questions extracted: {len(found)} / {TOTAL_QUESTIONS}")
    print(f"Missing: {len(missing)} question(s)" + (f" -> {missing[:20]}..." if len(missing) > 20 else f" -> {missing}"))
    print(f"Flagged for review: {len(flagged)}")
    for q in flagged:
        print(f"  Q{q['q_no']}: {q['review_flags']}")


if __name__ == "__main__":
    main()