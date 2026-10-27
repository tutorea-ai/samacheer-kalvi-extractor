"""
Redraw PYQ figures cleanly (no source watermark) using Claude + RDKit.

Claude returns each figure as structured data:
  svg      -> Claude-written SVG (circuits, graphs, physics diagrams)
  molecule -> SMILES, drawn by RDKit
  scheme   -> simple left-to-right reaction, assembled here from RDKit structures + arrows
  table    -> rows/headers kept as data (rendered as HTML by the frontend)

Rendering is local and always re-done (cheap); Claude results are cached.
A review HTML page shows the original page next to the redrawn figures.

Usage:
    python -m app.exams.common.pyq_figures --q 3 8 42 46 48 52    # test a few
    python -m app.exams.common.pyq_figures                        # all figure questions
    python -m app.exams.common.pyq_figures --q 8 --force          # re-ask Claude for one
"""
import argparse
import base64
import html
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import anthropic
import cairosvg
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

from app.config import settings
from app.exams.common.tagger import question_text, parse_json

ROOT = Path(__file__).resolve().parents[3]
EXAM = "neet"
PAPER_ID = "re_neet_2026"
PYQ_DIR = ROOT / f"exams_data/{EXAM}/pyq"
PAPER = PYQ_DIR / f"{PAPER_ID}.json"
PAGES_DIR = PYQ_DIR / f"_pages/{PAPER_ID}"
CACHE_DIR = PYQ_DIR / f"_cache/{PAPER_ID}_figures"
IMG_DIR = PYQ_DIR / f"images/{PAPER_ID}"
REVIEW_HTML = PYQ_DIR / f"_review/{PAPER_ID}_figures.html"

MODEL = os.getenv("NEET_FIGURE_MODEL", "claude-opus-5-5")
WORKERS = int(os.getenv("NEET_FIGURE_WORKERS", "4"))
RETRY_STATUS = {429, 500, 502, 503, 529}

PROMPT = """You are redrawing the figure(s) of ONE question from a NEET exam paper, so it can be shown
cleanly on a website. The attached page image contains question Q{q_no}. Look ONLY at Q{q_no}.
Ignore the background watermark logo, page header and other questions.

QUESTION (already extracted as text):
{question}

Existing figure description:
{description}

Reproduce the figure(s) EXACTLY: same topology, connections, values, labels, axes, curve shapes and
orientation. Do not add anything that is not in the original. Never reveal or hint at the answer.

Return ONLY a JSON object, no commentary:
{{
  "stem_figure": null or FIGURE,
  "option_figures": null or [FIGURE, FIGURE, FIGURE, FIGURE]
}}
- stem_figure: the figure that belongs to the question itself (null if none).
- option_figures: only if the four OPTIONS are figures (graphs/structures); exactly 4, in order.

FIGURE is one of:
1. {{"kind": "svg", "svg": "<svg ...>...</svg>"}}
   For circuits, graphs, mechanics diagrams, optics, Newman projections, complex reaction schemes.
2. {{"kind": "molecule", "smiles": "..."}}
   For a single chemical structure (charged species allowed, e.g. "C[CH+]c1ccccc1").
3. {{"kind": "scheme", "items": [ITEM, ...]}}
   ONLY for a simple left-to-right reaction. ITEM is one of:
     {{"smiles": "..."}}  |  {{"text": "P + Q"}}  |  {{"arrow": "reagent above", "below": "reagent below or null"}}
4. {{"kind": "table", "headers": ["...", "..."], "rows": [["...", "..."], ...]}}
   For tabular data inside the question.

SVG rules:
- Self-contained. Include xmlns="http://www.w3.org/2000/svg" and a viewBox; width between 300 and 640.
- White background rect first. Black strokes (stroke-width 2). No external images, fonts or CSS.
- Text: font-family="Arial, sans-serif", font-size 15-18. Use Unicode for symbols (μ, Ω, θ, π, λ, ε, ρ, σ, →).
  For subscripts/superscripts use <tspan baseline-shift="sub|super" font-size="11">.
- Circuit symbols: standard battery, resistor zigzag, capacitor plates, inductor coils, diode triangle+bar.
- Graphs: draw axes with arrowheads, axis labels, tick labels exactly as shown, dotted guide lines where shown.
- Do NOT include the question number or option labels (1)(2)(3)(4) inside figures.
"""


# ------------------------------------------------------------------ Claude

def call_claude(client, content: list, max_retries: int = 5) -> dict:
    for attempt in range(1, max_retries + 1):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=16000,
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


def ask_figures(client, q: dict, force: bool, note: str = None) -> dict:
    cache_file = CACHE_DIR / f"q{q['q_no']:03d}.json"
    if cache_file.exists() and not force:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    content = []
    for p in q.get("source_pages", []):
        img = PAGES_DIR / f"page-{p:02d}.png"
        if img.exists():
            content.append({"type": "image", "source": {
                "type": "base64", "media_type": "image/png",
                "data": base64.standard_b64encode(img.read_bytes()).decode()}})
    content.append({"type": "text", "text": PROMPT.format(
        q_no=q["q_no"],
        question=question_text(q),
        description=q.get("diagram_description") or "(none)",
    ) + (f"\n\nREVIEWER FEEDBACK ON A PREVIOUS ATTEMPT (you must fix these):\n{note}" if note else "")})
    result = call_claude(client, content)
    result["_model"] = MODEL
    cache_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


# ------------------------------------------------------------------ Rendering

def mol_svg(smiles: str, width: int = 280, height: int = 210) -> str:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.bondLineWidth = 2
    opts.fixedBondLength = 30
    opts.clearBackground = True
    opts.padding = 0.08
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def nest_svg(svg: str, x: float, y: float) -> str:
    """Place a full SVG document inside another SVG at (x, y)."""
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
    return re.sub(r"<svg\b", f'<svg x="{x}" y="{y}"', svg, count=1)


def scheme_svg(items: list) -> str:
    mol_w, mol_h, arrow_w, pad = 260, 200, 170, 12
    parts, x = [], pad
    for it in items:
        if it.get("smiles"):
            parts.append(nest_svg(mol_svg(it["smiles"], mol_w, mol_h), x, pad))
            x += mol_w
        elif it.get("arrow") is not None:
            y = pad + mol_h / 2
            parts.append(f'<line x1="{x + 10}" y1="{y}" x2="{x + arrow_w - 14}" y2="{y}" '
                         f'stroke="black" stroke-width="2" marker-end="url(#ah)"/>')
            if it.get("arrow"):
                parts.append(f'<text x="{x + arrow_w / 2}" y="{y - 12}" text-anchor="middle" '
                             f'font-family="Arial, sans-serif" font-size="14">{html.escape(it["arrow"])}</text>')
            if it.get("below"):
                parts.append(f'<text x="{x + arrow_w / 2}" y="{y + 24}" text-anchor="middle" '
                             f'font-family="Arial, sans-serif" font-size="14">{html.escape(it["below"])}</text>')
            x += arrow_w
        elif it.get("text"):
            w = max(60, int(len(it["text"]) * 11 + 20))
            parts.append(f'<text x="{x + w / 2}" y="{pad + mol_h / 2 + 6}" text-anchor="middle" '
                         f'font-family="Arial, sans-serif" font-size="18">{html.escape(it["text"])}</text>')
            x += w
    total_w, total_h = x + pad, mol_h + 2 * pad
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" '
            f'viewBox="0 0 {total_w} {total_h}">'
            '<defs><marker id="ah" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
            '<path d="M0,0 L10,4 L0,8 z" fill="black"/></marker></defs>'
            f'<rect width="100%" height="100%" fill="white"/>{"".join(parts)}</svg>')


SHIFT_RE = re.compile(r'<tspan([^>]*?)\sbaseline-shift=["\'](super|sub)["\']([^>]*)>(.*?)</tspan>', re.S)


def fix_shifts(svg: str) -> str:
    """Replace baseline-shift (unsupported in Firefox) with dy offsets."""
    def rep(m):
        before, kind, after, text = m.groups()
        d = -7 if kind == "super" else 5
        return f'<tspan{before} dy="{d}"{after}>{text}</tspan><tspan dy="{-d}">​</tspan>'
    return SHIFT_RE.sub(rep, svg)


def render_figure(fig: dict, out_base: str):
    """Return what goes into the paper JSON for this figure: a relative path or table data."""
    kind = fig.get("kind")
    if kind == "table":
        return {"kind": "table", "headers": fig.get("headers", []), "rows": fig.get("rows", [])}
    if kind == "svg":
        svg = fig["svg"]
    elif kind == "molecule":
        svg = mol_svg(fig["smiles"])
    elif kind == "scheme":
        svg = scheme_svg(fig["items"])
    else:
        raise ValueError(f"Unknown figure kind: {kind}")

    svg = fix_shifts(svg)
    cairosvg.svg2png(bytestring=svg.encode("utf-8"))   # validation: raises if SVG is broken
    out = IMG_DIR / f"{out_base}.svg"
    out.write_text(svg, encoding="utf-8")
    return {"kind": "svg", "path": f"images/{PAPER_ID}/{out_base}.svg", "source_kind": kind}


# ------------------------------------------------------------------ Review page

def figure_html(entry) -> str:
    if entry is None:
        return '<div class="missing">render failed</div>'
    if entry["kind"] == "table":
        head = "".join(f"<th>{html.escape(str(h))}</th>" for h in entry["headers"])
        body = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>"
                       for r in entry["rows"])
        return f"<table><tr>{head}</tr>{body}</table>"
    return f'<img src="../{entry["path"]}">'


def build_review(questions: list):
    rows = []
    for q in questions:
        img = q.get("image") or {}
        pages = "".join(f'<img src="../_pages/{PAPER_ID}/page-{p:02d}.png">' for p in q.get("source_pages", []))
        ours = ""
        if img.get("stem") is not None or "stem" in img:
            ours += "<h4>Question figure</h4>" + figure_html(img.get("stem")) if img.get("stem") else ""
        if img.get("options"):
            ours += "<h4>Option figures</h4>" + "".join(
                f'<div class="opt"><b>({i})</b> {figure_html(e)}</div>' for i, e in enumerate(img["options"], 1))
        flags = ", ".join(f for f in q["review_flags"] if f.startswith("figure_"))
        rows.append(f"""
<section id="q{q['q_no']}" class="{q['subject']}">
  <h2>Q{q['q_no']} <small>{q['subject']} · {html.escape(q.get('topic') or '')}</small>
      {f'<span class="flag">{flags}</span>' if flags else ''}</h2>
  <p class="qt">{html.escape(q['question'])}</p>
  <div class="cols"><div class="orig"><h4>Original page</h4>{pages}</div>
  <div class="ours">{ours or '<div class="missing">no figures returned</div>'}</div></div>
</section>""")
    REVIEW_HTML.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_HTML.write_text(f"""<!doctype html><html><head><meta charset="utf-8">
<title>NEET 2026 figure review</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
  onload="renderMathInElement(document.body,{{delimiters:[{{left:'$',right:'$',display:false}}]}})"></script>
<style>
body{{font-family:Arial,sans-serif;margin:24px;background:#f4f4f4}}
section{{background:#fff;padding:16px;margin-bottom:24px;border-radius:8px}}
.cols{{display:flex;gap:16px}} .orig{{flex:1}} .ours{{flex:1}}
.orig img{{width:100%;border:1px solid #ccc}} .ours img{{max-width:100%;border:1px solid #ddd;background:#fff}}
.opt{{margin:8px 0}} .flag{{color:#b00;font-size:14px;margin-left:8px}}
.missing{{color:#b00}} .qt{{color:#333}} small{{color:#777;font-weight:normal}}
table{{border-collapse:collapse}} td,th{{border:1px solid #999;padding:4px 10px}}
.chemistry .katex .mathnormal{{font-style:normal}}
</style></head><body><h1>NEET 2026 · figure review</h1>{"".join(rows)}</body></html>""",
                           encoding="utf-8")


# ------------------------------------------------------------------ Main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", type=int, nargs="*")
    ap.add_argument("--force", action="store_true", help="re-ask Claude (ignore cache)")
    ap.add_argument("--note", help="reviewer feedback for a re-ask (use with --force and one --q)")
    args = ap.parse_args()

    paper = json.loads(PAPER.read_text(encoding="utf-8"))
    targets = [q for q in paper["questions"]
               if q["status"] != "hidden"
               and (q.get("has_diagram") or q.get("options_are_diagrams"))
               and (not args.q or q["q_no"] in args.q)]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    print(f"Model: {MODEL} | workers: {WORKERS} | figure questions: {len(targets)}")
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(ask_figures, client, q, args.force, args.note): q for q in targets}
        for f in as_completed(futures):
            f.result()
            print(f"  Q{futures[f]['q_no']}: figures ready")

    # Render every question that has a cached Claude result
    rendered, failures = [], []
    for q in paper["questions"]:
        cache_file = CACHE_DIR / f"q{q['q_no']:03d}.json"
        if not cache_file.exists():
            continue
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        flags = [x for x in q["review_flags"] if not x.startswith("figure_")]
        entry = {"stem": None, "options": None, "review": "pending"}
        try:
            if data.get("stem_figure"):
                entry["stem"] = render_figure(data["stem_figure"], f"q{q['q_no']:03d}_stem")
            if data.get("option_figures"):
                entry["options"] = [render_figure(fig, f"q{q['q_no']:03d}_opt{i}")
                                    for i, fig in enumerate(data["option_figures"], 1)]
                if len(entry["options"]) != 4:
                    flags.append("figure_options_count")
        except Exception as e:
            flags.append("figure_render_failed")
            failures.append((q["q_no"], str(e)[:160]))
        if not entry["stem"] and not entry["options"]:
            flags.append("figure_empty")
        q["image"] = entry
        q["review_flags"] = flags
        rendered.append(q)

    PAPER.write_text(json.dumps(paper, indent=2, ensure_ascii=False), encoding="utf-8")
    build_review(rendered)

    print(f"\nRendered: {len(rendered)} question(s)")
    print(f"Failures: {len(failures)}")
    for n, err in failures:
        print(f"  Q{n}: {err}")
    print(f"Review page: {REVIEW_HTML}")


if __name__ == "__main__":
    main()