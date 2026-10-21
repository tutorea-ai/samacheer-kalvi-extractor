"""
audit_tamil_content.py — one-screen audit of deployed Tamil Content pages.

Run in the PYTHON SERVER root:
    python3 audit_tamil_content.py            # all Class 6 Tamil content pages
    python3 audit_tamil_content.py term1      # only one term

Read-only. One line per page, then a list of anything that looks wrong.
"""

import glob
import os
import re
import sys

ROOT = os.path.expanduser(
    "~/test_m1_and_m2/content-qa-lp/samacheer-kalvi/backend/data/languages/tamil/6/content")


def audit(path):
    h = open(path, encoding="utf-8").read()
    body = h.split("<body>", 1)[-1]
    flags = []
    qids = re.findall(r'data-question-id="q(\d+)"', body)
    if qids != [str(i) for i in range(1, len(qids) + 1)]:
        flags.append("qids not q1..qN")
    if re.search(r"<textarea(?![^>]*data-question-id)", body):
        flags.append("textarea without qid")
    n_btn = body.count('class="show-answer-btn"')
    n_rev = body.count('class="answer-reveal" style="display:none;"')
    if n_btn != n_rev:
        flags.append(f"buttons {n_btn} vs hidden answers {n_rev}")
    if body.count("<div") != body.count("</div>"):
        flags.append(f"divs {body.count('<div')}/{body.count('</div>')}")
    if re.search(r'<div class="(do-you-know|content-note|intro-box)">\s*</div>', body):
        flags.append("empty box")
    if "###" in body:
        flags.append("### left")
    dbl = re.findall(r"<strong>(\d+)[.)]? </strong>\1[ .)]", body)
    if dbl:
        flags.append(f"doubled numbers {dbl[:3]}")
    if re.search(r"[぀-ヿ一-鿿가-힯]", body):
        flags.append("CJK")
    if re.search(r"\sid\s*=", body.split('<div class=\'sk-lesson-wrapper\'>')[-1]):
        flags.append("id attribute")
    if "டேஷ்" in body or re.search(r"கூட்டல்\s", body):
        flags.append("read-aloud word left")
    plain = re.sub(r"<[^>]+>", " ", body)
    # long line without end punctuation followed by a plain paragraph — possibly
    # prose split mid-sentence (a following bold speaker label is fine: dialogue)
    split = re.findall(r"<p>([^<]{45,}[^.?!:”\"’')\]<])</p>\s*<p>(?!<strong>)", body)
    stats = {
        "chars": len(body),
        "verse": body.count('<div class="content-note"><p>'),
        "boxes": body.count('class="do-you-know"'),
        "ex": body.count('class="exercise-section'),
        "mcq": body.count('class="mcq-item"'),
        "qids": len(qids),
        "answers": n_btn,
        "mem": body.count("(மனப்பாடப் பகுதி)"),
        "split?": len(split),
        "latin": len(re.findall(r"\b[A-Za-z]{3,}\b", re.sub(r"\([^)]*\)", " ", plain))),
    }
    return stats, flags


def main(term=None):
    pages = sorted(glob.glob(os.path.join(ROOT, term or "*", "*", "index.html")))
    if not pages:
        print(f"No pages under {ROOT}")
        return
    print(f"{'page':<34} {'chars':>6} {'verse':>5} {'box':>4} {'ex':>3} {'mcq':>4} "
          f"{'qid':>4} {'ans':>4} {'mem':>4} {'split?':>6} {'latin':>5}")
    problems = []
    for p in pages:
        name = "/".join(p.split(os.sep)[-3:-1])
        s, flags = audit(p)
        print(f"{name:<34} {s['chars']:>6} {s['verse']:>5} {s['boxes']:>4} {s['ex']:>3} {s['mcq']:>4} "
              f"{s['qids']:>4} {s['answers']:>4} {s['mem']:>4} {s['split?']:>6} {s['latin']:>5}")
        if flags:
            problems.append((name, flags))
    print()
    if problems:
        for name, flags in problems:
            print(f"⚠️  {name}: {'; '.join(flags)}")
    else:
        print(f"✅ No problems found in {len(pages)} page(s)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)