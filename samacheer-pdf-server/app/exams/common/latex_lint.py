"""
Check every text field in NEET content for broken LaTeX:
- odd number of unescaped $ (unclosed math)
- unbalanced { } inside a math segment

Usage:
    python -m app.exams.common.latex_lint
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXAM_DIR = ROOT / "exams_data/neet"
FILES = sorted(EXAM_DIR.glob("generated/*/*/notes.json")) + [EXAM_DIR / "pyq/re_neet_2026.json"]
SKIP_KEYS = {"_meta", "review_flags", "corrections", "pyq", "image", "source_pages"}

DOLLAR_RE = re.compile(r"(?<!\\)\$")


def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k not in SKIP_KEYS:
                yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def check(text: str) -> list:
    problems = []
    parts = DOLLAR_RE.split(text)
    if len(parts) % 2 == 0:
        problems.append("unclosed $ (odd number of $)")
    for i in range(1, len(parts), 2):          # odd parts are inside $...$
        seg = re.sub(r"\\[{}]", "", parts[i])   # ignore escaped \{ \}
        depth = 0
        for ch in seg:
            depth += (ch == "{") - (ch == "}")
            if depth < 0:
                break
        if depth != 0:
            problems.append(f"unbalanced braces in ${parts[i][:60]}$")
    return problems


def main():
    total = 0
    for f in FILES:
        data = json.loads(f.read_text(encoding="utf-8"))
        for path, text in walk(data):
            for p in check(text):
                total += 1
                print(f"{f.relative_to(EXAM_DIR)} :: {path}\n    {p}")
    print(f"\nFiles checked: {len(FILES)} | problems: {total}")


if __name__ == "__main__":
    main()