"""
Generate exam-focused concept notes for every NEET syllabus unit.

- One Claude call per unit; notes cover every syllabus topic, in order.
- The unit's real PYQs are shown to calibrate depth (not copied).
- PYQ links are attached by code from our tags, not by the model.
- Output: exams_data/neet/generated/{subject}/{slug}/notes.json
- Review page: exams_data/neet/generated/_review/notes.html

Usage:
    python -m app.exams.neet.builders.notes --units phy_u06 che_u12 bio_u05   # test
    python -m app.exams.neet.builders.notes                                   # all 50
    python -m app.exams.neet.builders.notes --units phy_u06 --force           # regenerate
"""
import argparse
import html
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

from app.exams.common.llm import call_json
from app.exams.common.tagger import question_text

ROOT = Path(__file__).resolve().parents[4]
EXAM_DIR = ROOT / "exams_data/neet"
SYLLABUS = EXAM_DIR / "syllabus/neet_2026.json"
PYQ_PAPERS = [EXAM_DIR / "pyq/re_neet_2026.json"]
GEN_DIR = EXAM_DIR / "generated"
REVIEW_HTML = GEN_DIR / "_review/notes.html"

MODEL = os.getenv("NEET_NOTES_MODEL", "claude-opus-5-5")
WORKERS = int(os.getenv("NEET_NOTES_WORKERS", "4"))

PROMPT = """You are a senior NEET (UG) faculty member writing the official study notes for ONE syllabus unit.
Readers are NEET aspirants. The notes must be accurate, exam-focused and aligned with the NCERT
Class 11-12 treatment that NEET is based on.

SUBJECT: {subject}
UNIT {unit_no}: {unit_name}

SYLLABUS TOPICS (cover EVERY topic, in this exact order, nothing outside this list):
{topics}

RECENT REAL NEET QUESTIONS FROM THIS UNIT (to calibrate depth and angle only; do NOT copy or solve them):
{pyqs}

Return ONLY a JSON object, no commentary:
{{
  "overview": "2-3 sentences: what this unit is about and why it matters in NEET",
  "topics": [
    {{
      "topic_index": 0,
      "explanation": "clear exam-focused explanation, 60-160 words",
      "key_points": ["short point", "..."],
      "formulas": [{{"formula": "$...$", "meaning": "what it gives / when to use it"}}],
      "neet_tip": "one line on how NEET tests this topic"
    }}
  ],
  "{summary_key}": [{summary_shape}],
  "common_traps": ["a mistake students make, and the correct idea", "..."],
  "quick_revision": ["8-12 crisp last-minute revision bullets"]
}}

Rules:
- "topics" must contain exactly {n_topics} entries, topic_index 0 to {last_index}, in order.
- Write all mathematics and chemical formulas in LaTeX inside $...$ (e.g. $K_2Cr_2O_7$, $\\frac{{1}}{{2}}mv^2$).
- Plain text only: no markdown, no headings, no bullet characters inside strings.
- "formulas" may be an empty list for descriptive topics.
- {subject_rule}
- 4-8 common_traps.
- Do not mention any coaching institute, book or website.
"""

SUBJECT_RULES = {
    "physics": ("formula_sheet", '{"formula": "$...$", "meaning": "..."}',
                "formula_sheet: every important formula of the unit (10-25 entries), with symbols explained in meaning."),
    "chemistry": ("formula_sheet", '{"formula": "$...$", "meaning": "..."}',
                  "formula_sheet: key formulas, named reactions, reagents and trends of the unit (10-25 entries)."),
    "biology": ("key_facts", '"a high-yield fact"',
                "key_facts: 15-30 high-yield facts (numbers, names, examples, sequences) NEET often asks."),
}


def load_pyqs() -> dict:
    """unit_id -> list of PYQ questions (normal status only)."""
    by_unit = {}
    for paper_file in PYQ_PAPERS:
        paper = json.loads(paper_file.read_text(encoding="utf-8"))
        for q in paper["questions"]:
            if q["status"] == "normal" and q.get("unit_id"):
                by_unit.setdefault(q["unit_id"], []).append(
                    {"paper_id": paper["paper_id"], "exam_ref": q["exam_ref"], "q_id": q["q_id"], "q": q})
    return by_unit


def build_unit(subject: dict, unit: dict, pyqs: list, force: bool) -> tuple:
    out_file = GEN_DIR / subject["subject_id"] / unit["slug"] / "notes.json"
    if out_file.exists() and not force:
        return unit["unit_id"], json.loads(out_file.read_text(encoding="utf-8")), True

    summary_key, summary_shape, subject_rule = SUBJECT_RULES[subject["subject_id"]]
    topics = unit["topics"]
    prompt = PROMPT.format(
        subject=subject["subject_name"],
        unit_no=unit["unit_no"],
        unit_name=unit["unit_name"],
        topics="\n".join(f"{i}. {t}" for i, t in enumerate(topics)),
        pyqs="\n\n".join(question_text(p["q"]) for p in pyqs) or "(none in our current papers)",
        summary_key=summary_key,
        summary_shape=summary_shape,
        n_topics=len(topics),
        last_index=len(topics) - 1,
        subject_rule=subject_rule,
    )
    max_tokens = min(64000, 6000 + 1800 * len(topics))
    result = call_json(prompt, model=MODEL, max_tokens=max_tokens)

    # Validate topic coverage and attach the syllabus topic names
    got = {t.get("topic_index"): t for t in result.get("topics", [])}
    missing = [i for i in range(len(topics)) if i not in got]
    notes = {
        "exam": "neet",
        "subject": subject["subject_id"],
        "unit_id": unit["unit_id"],
        "unit_no": unit["unit_no"],
        "unit_name": unit["unit_name"],
        "slug": unit["slug"],
        "overview": result.get("overview", ""),
        "topics": [dict(got[i], topic=topics[i]) for i in range(len(topics)) if i in got],
        summary_key: result.get(summary_key, []),
        "common_traps": result.get("common_traps", []),
        "quick_revision": result.get("quick_revision", []),
        "pyq": {
            "count": len(pyqs),
            "questions": [{"paper_id": p["paper_id"], "q_id": p["q_id"], "exam_ref": p["exam_ref"]} for p in pyqs],
        },
        "review_flags": [f"missing_topics_{missing}"] if missing else [],
        "_meta": {"model": MODEL, "syllabus_year": 2026, "generated": date.today().isoformat()},
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")
    return unit["unit_id"], notes, False


def esc(s) -> str:
    return html.escape(str(s or ""))


def build_review(all_notes: list):
    sections = []
    for n in all_notes:
        topics = "".join(
            f"<div class='topic'><h4>{esc(t['topic'])}</h4><p>{esc(t.get('explanation'))}</p>"
            + ("<ul>" + "".join(f"<li>{esc(k)}</li>" for k in t.get("key_points", [])) + "</ul>")
            + "".join(f"<p class='f'>{esc(f.get('formula'))} <span>{esc(f.get('meaning'))}</span></p>"
                      for f in t.get("formulas", []))
            + f"<p class='tip'>NEET tip: {esc(t.get('neet_tip'))}</p></div>"
            for t in n["topics"])
        if "formula_sheet" in n:
            summary = "<h3>Formula sheet</h3>" + "".join(
                f"<p class='f'>{esc(f.get('formula'))} <span>{esc(f.get('meaning'))}</span></p>"
                for f in n["formula_sheet"])
        else:
            summary = "<h3>Key facts</h3><ul>" + "".join(f"<li>{esc(k)}</li>" for k in n.get("key_facts", [])) + "</ul>"
        traps = "<h3>Common traps</h3><ul>" + "".join(f"<li>{esc(t)}</li>" for t in n["common_traps"]) + "</ul>"
        rev = "<h3>Quick revision</h3><ul>" + "".join(f"<li>{esc(t)}</li>" for t in n["quick_revision"]) + "</ul>"
        pyq = ", ".join(esc(q["exam_ref"]) for q in n["pyq"]["questions"]) or "none"
        flags = f"<span class='flag'>{esc(', '.join(n['review_flags']))}</span>" if n["review_flags"] else ""
        sections.append(
            f"<section class='{n['subject']}' id='{n['unit_id']}'><h2>{n['subject'].title()} · Unit {n['unit_no']}: "
            f"{esc(n['unit_name'])} {flags}</h2><p class='ov'>{esc(n['overview'])}</p>"
            f"<p class='pyq'>PYQs ({n['pyq']['count']}): {pyq}</p>{topics}{summary}{traps}{rev}</section>")

    REVIEW_HTML.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_HTML.write_text(f"""<!doctype html><html><head><meta charset="utf-8"><title>NEET notes review</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{{delimiters:[{{left:'$',right:'$',display:false}}]}})"></script>
<style>
body{{font-family:Arial,sans-serif;margin:24px;background:#f4f4f4;line-height:1.5}}
section{{background:#fff;padding:20px;margin-bottom:28px;border-radius:8px;max-width:900px}}
.topic{{border-left:3px solid #4a7;padding-left:12px;margin:14px 0}} .tip{{color:#2a6}}
.f span{{color:#555}} .ov{{font-style:italic}} .pyq{{color:#36c}} .flag{{color:#b00;font-size:14px}}
.chemistry .katex .mathnormal{{font-style:normal}}
</style></head><body><h1>NEET unit notes · review</h1>{"".join(sections)}</body></html>""", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", nargs="*", help="unit_ids (default: all)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    syllabus = json.loads(SYLLABUS.read_text(encoding="utf-8"))
    pyqs = load_pyqs()
    jobs = [(s, u) for s in syllabus["subjects"] for u in s["units"]
            if not args.units or u["unit_id"] in args.units]

    print(f"Model: {MODEL} | workers: {WORKERS} | units: {len(jobs)}")
    results = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(build_unit, s, u, pyqs.get(u["unit_id"], []), args.force) for s, u in jobs]
        for f in as_completed(futures):
            unit_id, notes, cached = f.result()
            results[unit_id] = notes
            flags = f"  ⚠ {notes['review_flags']}" if notes["review_flags"] else ""
            print(f"  {unit_id}: {'cached' if cached else 'generated'} | topics {len(notes['topics'])}"
                  f" | PYQs {notes['pyq']['count']}{flags}")

    # Review page covers every notes file that exists, in syllabus order
    all_notes = []
    for s in syllabus["subjects"]:
        for u in s["units"]:
            f = GEN_DIR / s["subject_id"] / u["slug"] / "notes.json"
            if f.exists():
                all_notes.append(json.loads(f.read_text(encoding="utf-8")))
    build_review(all_notes)
    print(f"\nNotes files: {len(all_notes)} / 50")
    print(f"Review page: {REVIEW_HTML}")


if __name__ == "__main__":
    main()