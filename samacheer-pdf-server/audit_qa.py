"""
audit_qa.py — one-screen health report for a generated Physics QA bank.

Usage:
    python3 audit_qa.py <path/to/qa/index.html>

Saves 2 sample questions per part to /tmp/qa_samples.html. Changes nothing.
"""
import re
import sys

path = sys.argv[1]
h = open(path, encoding="utf-8").read()
strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

items = h.count('<div class="qa-item">')
nums = [int(x) for x in re.findall(r"<strong>Q(\d+)\.</strong>", h)]
print(f"FILE {path}")
print(f"TOTAL {len(h)} chars | qa-items {items} | numbering Q1..Q100 continuous: {nums == list(range(1, 101))}")
n_open, n_close = len(re.findall(r"<div\b", h)), len(re.findall(r"</div>", h))
print(f"div balance: open {n_open} / close {n_close}")
n_rev, n_btn = h.count('class="answer-reveal"'), h.count("toggleSectionAnswers")
print(f"answers hidden (answer-reveal): {n_rev} | Show Answers buttons: {n_btn}")

samples = []
expected = {"section-mcq": (1, 40), "section-2mark": (41, 65),
            "section-3mark": (66, 85), "section-5mark": (86, 100)}
print("\nSection        | range ok | items | book-back | numerical* | svg | flags")
for sid, (lo, hi) in expected.items():
    m = re.search(rf'id="{sid}"(.*?)(?=<div class="qa-section"|\Z)', h, re.S)
    if not m:
        print(f"{sid:<14} | MISSING")
        continue
    sec = m.group(1)
    got = [int(x) for x in re.findall(r"<strong>Q(\d+)\.</strong>", sec)]
    blocks = re.split(r'<div class="qa-item">', sec)[1:]
    numerical = sum(1 for b in blocks if re.search(r"Given|Substitut|calculate|find the", b, re.I))
    flags = []
    if re.search(r"\$[^$\n]{1,60}\$|\\frac|<math", sec): flags.append("LATEX")
    if re.search(r"[぀-ヿ一-鿿가-힯]", sec): flags.append("CJK")
    if "<script" in sec.lower(): flags.append("SCRIPT!")
    if sid == "section-mcq":
        letters = re.findall(r"<strong>Answer:</strong>\s*([abcd])\)", sec)
        dist = "/".join(l + str(letters.count(l)) for l in "abcd")
        flags.append("answers " + dist)
    print(f"{sid:<14} | {str(got == list(range(lo, hi + 1))):<8} | {len(got):>5} | "
          f"{sec.count('Book-back'):>9} | {numerical:>10} | {sec.count('<svg'):>3} | {' '.join(flags)}")
    samples += blocks[:2]

print("\n* numerical = questions whose text/answer mentions Given / Substitute / calculate / find the")
for n, b in zip((1, 41, 66, 86), samples[::2]):
    print(f"\n--- sample from Q{n} block:", strip(b)[:300])
open("/tmp/qa_samples.html", "w", encoding="utf-8").write("\n".join(samples))
print("\nSaved: /tmp/qa_samples.html")
