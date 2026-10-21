"""
tamil_lp_try.py — run the Tamil LP builder on ONE lesson file, save the HTML,
print a one-screen audit. Nothing is deployed.

Run in the PYTHON SERVER root (samacheer-pdf-server), venv active:
    python3 tamil_lp_try.py poem
    python3 tamil_lp_try.py prose | supplementary | grammar | thirukural

Output: storage/temp/tamil_lp_try_<type>.html  (+ the full log on screen)
"""

import glob
import re
import sys
import time

from app.content_builder.tamil.lp.grade_67.tamil import tamil_lp_67_builder
from app.content_builder.tamil.base import (
    LABELS, count_day_blocks, count_assessment_blocks, check_book_lines,
    lp_source_text, latin_outside_glosses, count_glosses,
)

FILES = {
    "poem":          ("storage/temp/Class6-Unit1-Poem-இன்பத்தமிழ்.txt", 1, "இன்பத்தமிழ்"),
    "prose":         ("storage/temp/Class6-Unit1-Prose-வளர்தமிழ்.txt", 1, "வளர்தமிழ்"),
    "supplementary": ("storage/temp/Class6-Unit1-Supplementary-ஒளிபிறந்தது.txt", 1, "ஒளி பிறந்தது"),
    "grammar":       ("storage/temp/Class6-Unit1-Grammar-*.txt", 1, "தமிழ் எழுத்துகளின் வகையும் தொகையும்"),
    "thirukural":    ("storage/temp/Class6-Unit2-Thirukural-*.txt", 2, "திருக்குறள்"),
}


def main(ltype):
    pattern, unit, title = FILES[ltype]
    paths = glob.glob(pattern)
    if not paths:
        print(f"❌ No file matches {pattern}")
        return
    text = open(paths[0], encoding="utf-8").read()
    meta = {"class": 6, "subject": "tamil", "unit": unit, "term": "term1",
            "lesson_type": ltype, "display_title": title}

    t0 = time.time()
    html = tamil_lp_67_builder.generate(text, meta)
    mins = (time.time() - t0) / 60
    if not html:
        print(f"\n❌ generate() returned None after {mins:.1f} min — send me the log above")
        return

    out = f"storage/temp/tamil_lp_try_{ltype}.html"
    open(out, "w", encoding="utf-8").write(html)

    days = re.split(r'(?=<div class="lp-day-block">)', html)[1:]
    lp_text, _ = lp_source_text(text)
    print("\n" + "=" * 64)
    print(f"SAVED {out}  ({len(html)} chars, {mins:.1f} min)")
    print(f"periods={count_day_blocks(html)}  assessment={count_assessment_blocks(html)}  "
          f"failed={html.count('LP_DAY_FAILED')}  truncated={html.count('LP_DAY_TRUNCATED')}  "
          f"divs {html.count('<div')}/{html.count('</div>')}")
    for i, d in enumerate(days, 1):
        d = d.split('<div class="assessment-block">')[0]
        times = re.findall(r'class="lp-time">\s*([\d–-]+)', d)
        print(f"  P{i}: {len(d):>6} chars | cfu={d.count('cfu-block')} ccq={d.count('ccq-block')} "
              f"slip={'Y' if LABELS['exit_slip'] in d else 'N'} hw={'Y' if LABELS['homework'] in d else 'N'} "
              f"gloss={count_glosses(d)} latin={len(latin_outside_glosses(d))} "
              f"bookline_mismatch={len(check_book_lines(d, lp_text))} | {' '.join(times)}")
    cjk = len(re.findall(r"[぀-ヿ一-鿿가-힯]", html))
    print(f"CJK={cjk}  page-number-like={len(re.findall(r'பக்கம்\s*\d|pp?\.\s*\d', html))}")
    print("=" * 64)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "poem")
