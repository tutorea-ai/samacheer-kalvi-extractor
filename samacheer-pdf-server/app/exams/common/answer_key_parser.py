"""
Parse an NTA NEET final answer key PDF into JSON.
Handles all booklet codes, dropped questions and multi-answer questions.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROW_RE = re.compile(r"^\s*(\d{1,3}\s+(?:Drop|\d(?:\s*,\s*\d)*)\s*)+$", re.IGNORECASE)
PAIR_RE = re.compile(r"(\d{1,3})\s+(Drop|\d(?:\s*,\s*\d)*)", re.IGNORECASE)
CODE_RE = re.compile(r"Test Booklet Code:\s*(\d+)")
DATE_RE = re.compile(r"Exam Date:\s*([\d.]+)")


def pdf_to_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def parse_answer_key(text: str, total_questions: int = 180) -> dict:
    # Split into one block per booklet code
    parts = CODE_RE.split(text)
    codes = {}
    exam_date = None

    # parts = [before, code1, block1, code2, block2, ...]
    for i in range(1, len(parts), 2):
        code = parts[i]
        block = parts[i + 1]

        if exam_date is None:
            m = DATE_RE.search(block)
            if m:
                exam_date = m.group(1)

        answers, dropped, multi = {}, [], []
        for line in block.splitlines():
            if not ROW_RE.match(line):
                continue
            for q_no, ans in PAIR_RE.findall(line):
                q = int(q_no)
                if ans.lower() == "drop":
                    answers[q] = []
                    dropped.append(q)
                else:
                    opts = [int(x) for x in re.split(r"\s*,\s*", ans.strip())]
                    answers[q] = opts
                    if len(opts) > 1:
                        multi.append(q)

        # Validation
        missing = [q for q in range(1, total_questions + 1) if q not in answers]
        if missing:
            raise ValueError(f"Code {code}: missing answers for questions {missing}")

        codes[code] = {
            "answers": {str(q): answers[q] for q in sorted(answers)},
            "dropped": sorted(dropped),
            "multiple_correct": sorted(multi),
        }

    if not codes:
        raise ValueError("No booklet codes found in answer key")

    return {"exam_date": exam_date, "codes": codes}


def main():
    root = Path(__file__).resolve().parents[3]
    src = root / "exams_data/neet/source/pyq/re_neet_2026/final_answer_key.pdf"
    out = root / "exams_data/neet/pyq/re_neet_2026_answer_key.json"

    data = parse_answer_key(pdf_to_text(src))
    data = {
        "exam": "neet",
        "paper_id": "re_neet_2026",
        "paper_name": "NEET (UG) 2026",
        "source": "NTA Final Answer Key (16-07-2026)",
        **data,
    }

    out.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"Saved: {out}")
    print(f"Exam date: {data['exam_date']}")
    for code, info in data["codes"].items():
        print(f"Code {code}: {len(info['answers'])} answers | "
              f"dropped={info['dropped']} | multiple_correct={info['multiple_correct']}")


if __name__ == "__main__":
    sys.exit(main())