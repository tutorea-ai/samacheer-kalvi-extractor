"""
audit_lp.py — one-screen health report for a generated Physics LP.

Usage:
    python3 audit_lp.py <path/to/lp/index.html> [day numbers to save, default: 2 5]

Saves the chosen days to /tmp/lp_dayN.html for review. Changes nothing.
"""
import re
import sys

path = sys.argv[1]
save_days = [int(x) for x in sys.argv[2:]] or [2, 5]
h = open(path, encoding="utf-8").read()
strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

opens = list(re.finditer(r'<div[^>]*class="lp-day-block"[^>]*>', h))
a = re.search(r'<div[^>]*class="assessment-block"[^>]*>', h)
print(f"FILE {path}")
n_assess = len(re.findall(r"class=.assessment-block", h))
print(f"TOTAL {len(h)} chars | day blocks {len(opens)} | assessment blocks {n_assess}")
n_open, n_close = len(re.findall(r"<div\b", h)), len(re.findall(r"</div>", h))
print(f"div balance: open {n_open} / close {n_close}")
pre = h[:opens[0].start()] if opens else h
print("PREAMBLE parts:", len(re.findall(r"<h2[^>]*>\s*Part\s*\d+", pre)), "of 9")
for part in ("Part 7", "Part 8"):
    m = re.search(part + r".*?</table>", pre, re.S)
    print(f"  {part} rows: {len(re.findall('<tr', m.group(0))) - 1 if m else 'MISSING'}")


def time_issue(d):
    r = [(int(x), int(y)) for x, y in re.findall(r'class="lp-time">\s*(\d+)\s*[–—-]\s*(\d+)', d)]
    if not r:
        return "no times"
    bad = []
    if r[0][0] != 0:
        bad.append(f"start {r[0][0]}")
    if r[-1][1] != 35:
        bad.append(f"end {r[-1][1]}")
    bad += [f"{a1}-{b1}>{a2}-{b2}" for (a1, b1), (a2, b2) in zip(r, r[1:]) if a2 != b1]
    return ",".join(bad[:2]) if bad else "ok"


print("\nDay | chars | sec | ccq cfu tam fbox mist we | exit | time | flags")
ends = [o.start() for o in opens[1:]] + [a.start() if a else len(h)]
for i, (o, e) in enumerate(zip(opens, ends), 1):
    d = h[o.start():e]
    secs = "".join("Y" if f"lp-section-{c}" in d else "-"
                   for c in ("opening", "intro", "main", "student-task", "closing"))
    c = d.count
    worked = len(re.findall(r"Worked Example", d))
    flags = []
    if re.search(r"\$[^$\n]{1,60}\$|\\frac|<math", d): flags.append("LATEX")
    if re.search(r"[぀-ヿ一-鿿가-힯]", d): flags.append("CJK")
    if re.search(r"\bpage\s*\d|\bpp\.\s*\d", d, re.I): flags.append("PAGE#")
    if "homework" in d.lower(): flags.append("HOMEWORK")
    if "LP_DAY_FAILED" in d: flags.append("FAILED")
    if "LP_DAY_TRUNCATED" in d: flags.append("TRUNC")
    if worked > 2: flags.append(f"WORKED×{worked}")
    exit_ok = "Y" if re.search("exit ticket", d, re.I) else "NO"
    print(f"{i:>3} | {len(d):>6} | {secs} | {c('ccq-block'):>3} {c('cfu-block'):>3} "
          f"{c('lp-tamil-scaffold'):>3} {c('formula-box'):>4} {c('common-mistakes'):>4} {worked:>2} | "
          f"{exit_ok:>4} | {time_issue(d):<10} | {' '.join(flags)}")
    if i in save_days:
        open(f"/tmp/lp_day{i}.html", "w", encoding="utf-8").write(d)

for n in save_days:
    if n <= len(opens):
        d = h[opens[n - 1].start():ends[n - 1]]
        t = re.search(r'lp-day-title">(.*?)</h3>', d, re.S)
        nxt = re.search(r"Next lesson:\s*(.*?)</", d)
        print(f"\n--- Day {n}: {strip(t.group(1)) if t else '?'}")
        print("    next lesson:", strip(nxt.group(1)) if nxt else "-")
if a:
    ad = h[a.start():]
    print("\nASSESSMENT:", [s for s in ("Section A", "Section B", "Section C", "Section D",
                                        "Answer Key", "diff-table") if s in ad])
print("\nSaved:", " ".join(f"/tmp/lp_day{n}.html" for n in save_days))
