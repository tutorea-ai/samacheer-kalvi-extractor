"""
tamil_text_check.py — one-screen check of extracted Tamil lesson text.

Run in the PYTHON SERVER root (samacheer-pdf-server), venv active:
    python3 tamil_text_check.py lesson1.txt lesson2.txt ...

Prints, per file: size, ### lines, memorisation lines, boxes, read-aloud
symbol conversions (and the ambiguous lines left alone), where the book
exercises and the unit-end block start, and the last lines of the text.
Read-only: changes nothing.
"""

import importlib.util
import os
import re
import sys

BASE = os.path.join("app", "content_builder", "tamil", "base", "__init__.py")


def load_base():
    spec = importlib.util.spec_from_file_location("tamil_base", BASE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def short(s, n=70):
    s = s.replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n] + "…"


def main(paths):
    tb = load_base()
    for path in paths:
        raw = open(path, encoding="utf-8").read()
        norm, rep = tb.normalize_source_text(raw)
        parts = tb.split_lesson_parts(norm)
        heads = tb.list_hash_headings(norm)

        print("=" * 72)
        print(f"FILE {os.path.basename(path)}")
        print(f"  chars raw={len(raw)}  normalized={len(norm)}  lines={norm.count(chr(10)) + 1}")
        print(f"  teaching={len(parts['teaching'])}  exercises={len(parts['exercises'])}  "
              f"unit_end={len(parts['unit_end'])}")
        if parts["exercises"]:
            print(f"  exercises start: {short(parts['exercises'], 60)}")
        if parts["unit_end"]:
            print(f"  unit-end start : {short(parts['unit_end'], 60)}")

        print(f"  ### lines ({len(heads)}):")
        for h in heads[:25]:
            print(f"     · {short(h, 66)}")
        if len(heads) > 25:
            print(f"     … {len(heads) - 25} more")

        print(f"  memorise lines ({len(rep['memorise_lines'])}):")
        for l in rep["memorise_lines"][:12]:
            print(f"     * {short(l, 66)}")

        print(f"  boxes={rep['boxes']}  dash={rep['dash']}  '1,'→'1.'={rep['line_numbers']}  "
              f"symbols: numbers={rep['symbols_number']} chains={rep['symbols_chain']} "
              f"ambiguous={len(rep['symbol_ambiguous'])}")
        for l in rep["symbol_ambiguous"][:10]:
            print(f"     ? {short(l, 66)}")

        converted = [l for l in norm.split("\n") if re.search(r"[+×−÷=]", l)]
        for l in converted[:10]:
            print(f"     = {short(l, 66)}")

        left = {w: len(re.findall(w, norm)) for w in list(tb.SYMBOL_WORDS) + ["டேஷ்", "மனப்பாடப்"]}
        left = {w: n for w, n in left.items() if n}
        if left:
            print(f"  still in text: {left}")

        unit_hits = re.findall(r"(?i)unit\s*[-–]\s*[2-9]", raw)
        if unit_hits:
            print(f"  ⚠️ 'Unit – N' found {len(unit_hits)}x (clean_noise truncation trap)")

        tail = [l for l in norm.split("\n") if l.strip()][-3:]
        print("  last lines:")
        for l in tail:
            print(f"     … {short(l, 66)}")
    print("=" * 72)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1:])
