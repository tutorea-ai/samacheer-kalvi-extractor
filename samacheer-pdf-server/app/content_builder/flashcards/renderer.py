"""
Flash Cards renderer — deck JSON (from builder.py) → one self-contained index.html.

    from app.content_builder.flashcards.renderer import render_deck
    html = render_deck(deck_dict)

CLI (for testing):
    python -m app.content_builder.flashcards.renderer deck.json out.html

Nothing subject-specific is hardcoded here:
  - type labels and filter chips come from deck["types"], and only types that
    actually have cards are shown
  - chip colours are assigned by position in deck["types"], so a new subject's
    types (fact, term, ...) get colours automatically
  - notation: "_" → subscript (v_d, R_eq, l_AJ), "^" → superscript (10^-6, m^{2})
"""

import html
import json
import re
import sys
from pathlib import Path

# ── Notation ──────────────────────────────────────────────────────────────────
# base_sub   : v_d, R_eq, I_G, l_AJ, ε_eq, R_{total}
# base^sup   : 10^-6, m^2, x^{n+1}
_SUB_RE = re.compile(r"(?<=[A-Za-z0-9Ͱ-Ͽ)\]])_(\{[^}]+\}|[A-Za-z0-9]+)")
_SUP_RE = re.compile(r"(?<=[A-Za-z0-9Ͱ-Ͽ)\]])\^(\{[^}]+\}|[-+−]?[A-Za-z0-9]+)")

# Formula strings can hold several formulas: "a | b", "a   and   b", "a,   b"
_FORMULA_SPLIT_RE = re.compile(r"\s+\|\s+|\s{2,}and\s{2,}|,\s{2,}")

SECONDS_PER_CARD = 40          # used for "about X min"


def _strip_braces(s: str) -> str:
    return s[1:-1] if s.startswith("{") and s.endswith("}") else s


def fmt(text) -> str:
    """Escape HTML, then turn _x / ^x notation into <sub>/<sup>."""
    if not text:
        return ""
    out = html.escape(str(text), quote=False)
    out = _SUB_RE.sub(lambda m: f"<sub>{_strip_braces(m.group(1))}</sub>", out)
    out = _SUP_RE.sub(lambda m: f"<sup>{_strip_braces(m.group(1))}</sup>", out)
    return out


def _formula_parts(formula) -> list:
    if not formula or not str(formula).strip():
        return []
    return [fmt(p.strip()) for p in _FORMULA_SPLIT_RE.split(str(formula)) if p.strip()]


# ── Deck → view model ─────────────────────────────────────────────────────────
def _view_model(deck: dict) -> dict:
    lesson = deck.get("lesson") or {}
    types = deck.get("types") or []
    used = {c.get("type") for c in deck.get("cards", [])}

    type_list = []
    for i, t in enumerate(types):
        if t.get("key") in used:
            type_list.append({"key": t["key"], "label": t.get("label") or t["key"].title(),
                              "tone": i % 6})
    # any card type missing from deck["types"] still gets a chip
    known_keys = {t["key"] for t in type_list}
    for k in sorted(k for k in used if k and k not in known_keys):
        type_list.append({"key": k, "label": k.replace("_", " ").title(),
                          "tone": len(type_list) % 6})
    labels = {t["key"]: t["label"] for t in type_list}

    cards = []
    for c in deck.get("cards", []):
        day = c.get("day")
        cards.append({
            "id": f"d{day}",
            "day": day,
            "dayLabel": f"Day {day}" if day is not None else "",
            "section": fmt(c.get("section", "")),
            "type": c.get("type", ""),
            "typeLabel": labels.get(c.get("type"), ""),
            "title": fmt(c.get("title", "")),
            "prompt": fmt(c.get("prompt", "")),
            "bullets": [fmt(b) for b in c.get("bullets", [])],
            "formula": _formula_parts(c.get("formula")),
            "tip": fmt(c.get("exam_tip", "")),
        })

    recap = deck.get("recap")
    if recap and recap.get("bullets"):
        cards.append({
            "id": "recap",
            "day": None,
            "dayLabel": "Whole chapter",
            "section": "",
            "type": "recap",
            "typeLabel": "Chapter Recap",
            "title": fmt(recap.get("title") or "Chapter Recap"),
            "prompt": fmt(recap.get("prompt", "")),
            "bullets": [fmt(b) for b in recap.get("bullets", [])],
            "formula": _formula_parts(recap.get("formula")),
            "tip": fmt(recap.get("exam_tip", "")),
        })

    subject = str(lesson.get("subject", "")).replace("_", " ").title()
    meta_bits = [subject]
    if lesson.get("class"):
        meta_bits.append(f"Class {lesson['class']}")
    if lesson.get("unit"):
        meta_bits.append(f"Unit {lesson['unit']}")

    src = deck.get("source_lp") or {}
    key_bits = [str(lesson.get("class", "")), str(lesson.get("subject", "")),
                str(lesson.get("unit", "")), str(src.get("hash", ""))]

    return {
        "title": fmt(lesson.get("title", "Flash Cards")),
        "titlePlain": str(lesson.get("title", "Flash Cards")),
        "meta": " · ".join(b for b in meta_bits if b),
        "types": type_list,
        "cards": cards,
        "storageKey": "sk-fc:" + ":".join(key_bits),
        "secondsPerCard": SECONDS_PER_CARD,
    }


def _json_for_script(obj) -> str:
    # safe inside <script type="application/json">
    return (json.dumps(obj, ensure_ascii=False)
            .replace("</", "<\\/").replace("<!--", "<\\!--"))


# ── Public API ────────────────────────────────────────────────────────────────
def render_deck(deck: dict) -> str:
    vm = _view_model(deck)
    return (_TEMPLATE
            .replace("%%TITLE_PLAIN%%", html.escape(vm["titlePlain"]))
            .replace("%%TITLE%%", vm["title"])
            .replace("%%META%%", html.escape(vm["meta"]))
            .replace("%%DATA%%", _json_for_script(vm)))


def render_file(json_path, out_path) -> Path:
    deck = json.loads(Path(json_path).read_text(encoding="utf-8"))
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_deck(deck), encoding="utf-8")
    return out


# ── Template ──────────────────────────────────────────────────────────────────
_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flash Cards · %%TITLE_PLAIN%%</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&family=Noto+Serif:wght@500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#FBF4E2; --surface:#FFFFFF; --surface-2:#FFFDF6; --back:#F2F9F8;
  --ink:#1F2A2E; --ink-2:#4F4A3B; --ink-3:#6B6450;
  --line:#E7DABA; --line-2:#E1D2A8; --line-back:#CFE5E2; --track:#EADDBB; --seg:#F1E6C8;
  --accent:#0B6B67; --accent-ink:#0A5552; --on-accent:#FFFFFF;
  --tip-bg:#FFF4D9; --tip-ink:#5A3D00; --tip-icon:#7A4F00;
  --formula-ink:#12302E;
  --shadow:0 1px 2px rgba(60,45,10,.06),0 8px 24px rgba(60,45,10,.07);
  --t0-bg:#E1F0EE; --t0-ink:#0A5552;
  --t1-bg:#FBE7C6; --t1-ink:#6E4300;
  --t2-bg:#E3E8F9; --t2-ink:#2B3C88;
  --t3-bg:#F6E1EA; --t3-ink:#7A2148;
  --t4-bg:#E3F2DE; --t4-ink:#2C6420;
  --t5-bg:#ECE4F7; --t5-ink:#4B2C7F;
  --recap-bg:#1F2A2E; --recap-ink:#FBF4E2;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#13191B; --surface:#1B2326; --surface-2:#1B2326; --back:#16211F;
    --ink:#ECE6D6; --ink-2:#C4BCA6; --ink-3:#9D9581;
    --line:#2C3639; --line-2:#36423F; --line-back:#24413D; --track:#2A3335; --seg:#222B2E;
    --accent:#3FB8AE; --accent-ink:#7FD6CD; --on-accent:#0E1A19;
    --tip-bg:#2C2414; --tip-ink:#F1D9A6; --tip-icon:#E8B85C;
    --formula-ink:#D6F0EC;
    --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.25);
    --t0-bg:#163A37; --t0-ink:#8FDCD3;
    --t1-bg:#3A2C12; --t1-ink:#F3CB86;
    --t2-bg:#1F2748; --t2-ink:#AFBDF3;
    --t3-bg:#3B1C2A; --t3-ink:#F0AECB;
    --t4-bg:#1D3519; --t4-ink:#A9DB9B;
    --t5-bg:#2C2142; --t5-ink:#CDB6F2;
    --recap-bg:#ECE6D6; --recap-ink:#13191B;
    color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#13191B; --surface:#1B2326; --surface-2:#1B2326; --back:#16211F;
  --ink:#ECE6D6; --ink-2:#C4BCA6; --ink-3:#9D9581;
  --line:#2C3639; --line-2:#36423F; --line-back:#24413D; --track:#2A3335; --seg:#222B2E;
  --accent:#3FB8AE; --accent-ink:#7FD6CD; --on-accent:#0E1A19;
  --tip-bg:#2C2414; --tip-ink:#F1D9A6; --tip-icon:#E8B85C;
  --formula-ink:#D6F0EC;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 24px rgba(0,0,0,.25);
  --t0-bg:#163A37; --t0-ink:#8FDCD3;
  --t1-bg:#3A2C12; --t1-ink:#F3CB86;
  --t2-bg:#1F2748; --t2-ink:#AFBDF3;
  --t3-bg:#3B1C2A; --t3-ink:#F0AECB;
  --t4-bg:#1D3519; --t4-ink:#A9DB9B;
  --t5-bg:#2C2142; --t5-ink:#CDB6F2;
  --recap-bg:#ECE6D6; --recap-ink:#13191B;
  color-scheme:dark;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink)}
body{font-family:'Noto Sans',system-ui,-apple-system,'Segoe UI',sans-serif;line-height:1.5;-webkit-text-size-adjust:100%}
button{font:inherit;color:inherit}
sub,sup{font-size:.72em;line-height:0}
.serif{font-family:'Noto Serif',Georgia,serif}
.wrap{position:relative;max-width:1100px;margin:0 auto;padding:28px 24px 64px}
.embed .wrap{padding-top:16px}
.embed .page-head{display:none}

/* header */
.page-head{display:flex;flex-direction:column;gap:6px;margin-bottom:18px}
.eyebrow{font-size:13px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)}
h1{margin:0;font-family:'Noto Serif',Georgia,serif;font-size:clamp(28px,4.5vw,38px);line-height:1.15;font-weight:600}
.intro{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:16px 28px;margin-bottom:18px}
.intro h2{margin:0 0 4px;font-size:21px;font-weight:700}
.intro p{margin:0;max-width:600px;font-size:15px;color:var(--ink-2)}
.progress{min-width:240px;flex:0 1 300px;display:flex;flex-direction:column;gap:7px}
.progress-row{display:flex;justify-content:space-between;gap:12px;font-size:14px;font-weight:600}
.progress-row .soft{color:var(--ink-3);font-weight:500}
.bar{height:8px;border-radius:999px;background:var(--track);overflow:hidden}
.bar > i{display:block;height:100%;width:0;background:var(--accent);border-radius:999px;transition:width .35s}

/* toolbar */
.toolbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}
.seg{display:inline-flex;background:var(--seg);border-radius:12px;padding:4px}
.seg button{height:38px;padding:0 16px;border:0;border-radius:9px;background:transparent;font-size:14px;font-weight:600;color:var(--ink-2);cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--surface);color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.12)}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px}
.chip-btn{height:36px;padding:0 14px;border-radius:999px;border:1px solid var(--line-2);background:var(--surface-2);font-size:13.5px;font-weight:600;color:var(--ink-2);cursor:pointer}
.chip-btn[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--bg)}
.tools{display:flex;gap:8px}
.icon-btn{height:40px;min-width:40px;padding:0 12px;border-radius:11px;border:1px solid var(--line-2);background:var(--surface);font-size:14px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px}
.icon-btn svg{flex:none}
:is(button,a):focus-visible{outline:3px solid var(--accent);outline-offset:2px}

/* notice */
.notice{display:none;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:12px;padding:10px 14px;margin-bottom:16px;font-size:14px}
.notice.show{display:flex}
.link-btn{border:0;background:none;padding:4px 2px;font-size:14px;font-weight:600;color:var(--accent-ink);cursor:pointer;text-decoration:underline;text-underline-offset:3px}

/* chips */
.chip{display:inline-flex;align-items:center;height:26px;padding:0 10px;border-radius:999px;font-size:12px;font-weight:600;letter-spacing:.02em;white-space:nowrap}
.tone-0{background:var(--t0-bg);color:var(--t0-ink)}
.tone-1{background:var(--t1-bg);color:var(--t1-ink)}
.tone-2{background:var(--t2-bg);color:var(--t2-ink)}
.tone-3{background:var(--t3-bg);color:var(--t3-ink)}
.tone-4{background:var(--t4-bg);color:var(--t4-ink)}
.tone-5{background:var(--t5-bg);color:var(--t5-ink)}
.tone-recap{background:var(--recap-bg);color:var(--recap-ink)}

/* ── Test myself: one card ───────────────────────────────────────────── */
.stage{max-width:680px;margin:0 auto}
.count-row{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:10px;font-size:14px;font-weight:600;color:var(--ink-2)}
.count-row .soft{font-weight:500;color:var(--ink-3)}
.card{perspective:1600px;touch-action:pan-y;user-select:none;-webkit-user-select:none}
.card-inner{display:grid;transition:transform .5s cubic-bezier(.2,.7,.2,1);transform-style:preserve-3d}
.card.flipped .card-inner{transform:rotateY(180deg)}
.face{grid-area:1/1;border-radius:18px;backface-visibility:hidden;-webkit-backface-visibility:hidden;display:flex;flex-direction:column;min-height:420px;padding:24px}
.front{background:var(--surface);border:1px solid var(--line);box-shadow:var(--shadow);cursor:pointer;text-align:left;width:100%}
.back{background:var(--back);border:1px solid var(--line-back);box-shadow:var(--shadow);transform:rotateY(180deg)}
.face-top{display:flex;align-items:center;justify-content:space-between;gap:10px}
.day{font-size:13px;font-weight:600;color:var(--ink-3);white-space:nowrap}
.card-title{margin:22px 0 0;font-family:'Noto Serif',Georgia,serif;font-size:clamp(23px,3.4vw,28px);line-height:1.22;font-weight:600}
.section{margin-top:6px;font-size:13px;color:var(--ink-3)}
.label{margin-top:28px;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-ink)}
.prompt{margin-top:8px;font-size:18px;line-height:1.5;color:var(--ink)}
.hint{margin-top:auto;padding-top:16px;border-top:1px solid var(--line);display:flex;align-items:center;justify-content:center;gap:8px;font-size:14px;font-weight:600;color:var(--accent-ink)}
.got-badge{display:inline-flex;align-items:center;gap:5px;font-size:13px;font-weight:700;color:var(--accent-ink)}
.back-title{font-size:16px;font-weight:700}
.bullets{margin:14px 0 0;padding-left:20px;display:flex;flex-direction:column;gap:8px}
.bullets li{font-size:15.5px;line-height:1.5}
.bullets li::marker{color:var(--accent)}
.formula{margin-top:16px;display:flex;flex-wrap:wrap;justify-content:center;gap:8px}
.formula span{background:var(--surface);border:1px solid var(--line-back);border-radius:10px;padding:8px 14px;font-family:'Noto Serif',Georgia,serif;font-size:18px;color:var(--formula-ink);white-space:nowrap}
.tip{margin-top:14px;background:var(--tip-bg);border-radius:12px;padding:11px 13px;display:flex;gap:10px;align-items:flex-start;font-size:14.5px;line-height:1.45;color:var(--tip-ink)}
.tip svg{flex:none;margin-top:2px;color:var(--tip-icon)}
.answer-actions{margin-top:auto;padding-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:10px}
.btn{height:46px;padding:0 16px;white-space:nowrap;border-radius:12px;font-size:15px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1px solid var(--line-2);background:var(--surface);color:var(--ink)}
.btn-primary{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.btn-primary[aria-pressed="true"]{box-shadow:inset 0 0 0 2px var(--on-accent)}
.nav{margin-top:14px;display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:center}
.nav .btn{background:transparent}
.nav .btn:disabled{opacity:.4;cursor:default}
.nav .flip-btn{min-width:150px;background:var(--surface)}
.keys{margin-top:12px;text-align:center;font-size:12.5px;color:var(--ink-3)}
kbd{font-family:inherit;font-size:11.5px;border:1px solid var(--line-2);border-bottom-width:2px;border-radius:5px;padding:0 5px;background:var(--surface)}

/* finished */
.done{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:40px 28px;text-align:center;box-shadow:var(--shadow)}
.done h3{margin:10px 0 6px;font-family:'Noto Serif',Georgia,serif;font-size:26px;font-weight:600}
.done p{margin:0 auto;max-width:440px;color:var(--ink-2);font-size:15.5px}
.done-actions{margin-top:22px;display:flex;flex-wrap:wrap;justify-content:center;gap:10px}
.done-mark{width:56px;height:56px;border-radius:50%;margin:0 auto;background:var(--t0-bg);color:var(--accent-ink);display:flex;align-items:center;justify-content:center}

/* ── Quick read: all answers open ────────────────────────────────────── */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}
.read-card{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px;display:flex;flex-direction:column;box-shadow:var(--shadow)}
.read-card .card-title{margin-top:14px;font-size:21px}
.read-card .prompt{margin-top:6px;font-size:14.5px;color:var(--ink-2);font-style:italic}
.read-card .bullets li{font-size:14.5px}
.read-card .formula span{font-size:16px}
.read-card .tip{font-size:13.5px}
.read-foot{margin-top:auto;padding-top:14px;display:flex;justify-content:flex-end}
.read-foot .btn{height:38px;font-size:13.5px}
.read-card.is-got{border-color:var(--line-back)}
.empty{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:40px 24px;text-align:center;color:var(--ink-2)}

#print-list{display:none}

@media (max-width:640px){
  .wrap{padding:16px 16px 40px}
  .intro{margin-bottom:14px}
    .progress{flex-basis:100%}
  .intro h2{font-size:17px;margin:0}
  .intro p{display:none}
  .toolbar{gap:8px}
  .seg{flex:1}
  .seg button{flex:1;padding:0 8px}
  .filters{flex-wrap:nowrap;overflow-x:auto;margin:0 -16px 16px;padding:0 16px 2px;scrollbar-width:none}
  .filters::-webkit-scrollbar{display:none}
  .chip-btn{flex:none}
  .tools .txt{display:none}
  .tools .icon-btn{height:46px;width:46px;padding:0}
  .btn{font-size:14.5px;padding:0 12px}
  .nav{grid-template-columns:52px 1fr 52px}
  .nav .btn .navtxt{display:none}
  .nav .btn{padding:0}
  .nav .flip-btn{min-width:0}
  .face{padding:20px;min-height:400px}
  .keys{display:none}
  .grid{grid-template-columns:1fr}
}
@media (prefers-reduced-motion: reduce){.card-inner,.bar > i{transition:none}}

@media print{
  .filters{display:none !important}
  :root:root:root{color-scheme:light;--bg:#fff;--surface:#fff;--surface-2:#fff;--back:#fff;--ink:#000;--line-2:#bbb;--ink-2:#222;--ink-3:#444;--line:#bbb;--line-back:#bbb;--tip-bg:#f3f3f3;--tip-ink:#000;--formula-ink:#000;--accent:#000;--accent-ink:#000;--shadow:none}
  body{background:#fff}
  .wrap{max-width:none;padding:0}
  .intro,.toolbar,.notice,#app{display:none !important}
  #print-list{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  #print-list .read-card{break-inside:avoid;page-break-inside:avoid;padding:12px;border-radius:8px}
  #print-list .read-foot{display:none}
  #print-list .card-title{font-size:15px;margin-top:6px}
  #print-list .bullets li,#print-list .tip{font-size:11.5px}
  #print-list .formula span{font-size:13px;padding:3px 8px}
  .chip{border:1px solid #888;background:#fff !important;color:#000 !important}
  @page{margin:12mm}
}
</style>
</head>
<body>
<div class="wrap">
  <header class="page-head">
    <div class="eyebrow">%%META%%</div>
    <h1>%%TITLE%%</h1>
  </header>

  <section class="intro">
    <div>
      <h2>Revise the chapter, one day at a time</h2>
      <p>One card for each day of your lesson plan, plus a chapter recap. Try to remember the answer, then flip the card to check. No marks, no timer.</p>
    </div>
    <div class="progress">
      <div class="progress-row"><span>Your progress</span><span id="got-count"></span></div>
      <div class="bar" role="progressbar" aria-label="Cards you've got" aria-valuemin="0" id="got-bar"><i></i></div>
    </div>
  </section>

  <div class="toolbar">
    <div class="seg" role="group" aria-label="How to revise">
      <button type="button" data-mode="test">Test myself</button>
      <button type="button" data-mode="read">Quick read</button>
    </div>
    <div class="tools">
      <button type="button" class="icon-btn" id="theme-btn" aria-label="Switch to night mode">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
        <span class="txt" id="theme-txt">Night</span>
      </button>
      <button type="button" class="icon-btn" id="print-btn" aria-label="Print all cards">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
        <span class="txt">Print</span>
      </button>
    </div>
  </div>
  <div class="filters" role="group" aria-label="Show cards" id="filters"></div>

  <div class="notice" id="notice" role="status">
    <span id="notice-text"></span>
    <button type="button" class="link-btn" id="notice-reset">Start from the beginning</button>
  </div>

  <main id="app" aria-live="polite"></main>
  <div id="print-list" aria-hidden="true"></div>
</div>

<script type="application/json" id="deck-data">%%DATA%%</script>
<script>
(function(){
  "use strict";
  var D = JSON.parse(document.getElementById("deck-data").textContent);
  var TONE = {}; D.types.forEach(function(t){ TONE[t.key] = "tone-" + t.tone; });
  TONE.recap = "tone-recap";

  if (/[?&]embed=1\b/.test(location.search)) document.body.classList.add("embed");

  // ── storage (optional: page works without it) ───────────────────────
  function load(){ try { return JSON.parse(localStorage.getItem(D.storageKey) || "null"); } catch(e){ return null; } }
  function save(){ try { localStorage.setItem(D.storageKey, JSON.stringify({got:S.got, mode:S.mode, filter:S.filter, pos:currentId(), reviseOnly:S.reviseOnly})); } catch(e){} }
  function loadTheme(){ try { return localStorage.getItem("sk-fc:theme"); } catch(e){ return null; } }
  function saveTheme(v){ try { localStorage.setItem("sk-fc:theme", v); } catch(e){} }

  var saved = load() || {};
  var S = {
    got: saved.got && typeof saved.got === "object" ? saved.got : {},
    mode: saved.mode === "read" ? "read" : "test",
    filter: saved.filter || "all",
    reviseOnly: !!saved.reviseOnly,
    idx: 0, flipped: false, finished: false, queue: []
  };
  if (S.filter !== "all" && !D.types.some(function(t){ return t.key === S.filter; })) S.filter = "all";

  // ── helpers ──────────────────────────────────────────────────────────
  var ICON = {
    flip:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/></svg>',
    check:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>',
    bulb:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/></svg>',
    left:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 18l-6-6 6-6"/></svg>',
    right:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 18l6-6-6-6"/></svg>'
  };
  function chip(c){ return '<span class="chip ' + (TONE[c.type] || "tone-0") + '">' + c.typeLabel + '</span>'; }
  function inFilter(c){ return S.filter === "all" || c.type === S.filter; }
  function filtered(){ return D.cards.filter(inFilter); }
  function buildQueue(){
    var list = filtered();
    S.queue = S.reviseOnly ? list.filter(function(c){ return !S.got[c.id]; }) : list;
  }
  function currentId(){ var c = S.queue[S.idx]; return c ? c.id : null; }
  function minutes(n){ return Math.max(1, Math.round(n * D.secondsPerCard / 60)); }
  function stripTags(h){ var d = document.createElement("div"); d.innerHTML = h; return d.textContent; }

  function answerHTML(c){
    var h = '<ul class="bullets">' + c.bullets.map(function(b){ return "<li>" + b + "</li>"; }).join("") + "</ul>";
    if (c.formula.length) h += '<div class="formula">' + c.formula.map(function(f){ return '<span>' + f + '</span>'; }).join("") + "</div>";
    if (c.tip) h += '<div class="tip">' + ICON.bulb + '<span><strong>Exam tip: </strong>' + c.tip + "</span></div>";
    return h;
  }

  // ── progress + filters ──────────────────────────────────────────────
  function renderProgress(){
    var list = filtered(), got = list.filter(function(c){ return S.got[c.id]; }).length;
    document.getElementById("got-count").innerHTML = got + ' of ' + list.length + ' <span class="soft">got</span>';
    var bar = document.getElementById("got-bar");
    bar.setAttribute("aria-valuemax", list.length); bar.setAttribute("aria-valuenow", got);
    bar.firstElementChild.style.width = (list.length ? got / list.length * 100 : 0) + "%";
  }
  function renderFilters(){
    var hasRecap = D.cards.some(function(c){ return c.type === "recap"; });
    var opts = [{key:"all", label:"All"}].concat(D.types);
    var el = document.getElementById("filters");
    el.innerHTML = opts.map(function(o){
      return '<button type="button" class="chip-btn" data-filter="' + o.key + '" aria-pressed="' + (S.filter === o.key) + '">' + o.label + '</button>';
    }).join("");
    if (D.types.length < 2 && !hasRecap) el.style.display = "none";
  }
  function renderSeg(){
    document.querySelectorAll(".seg button").forEach(function(b){ b.setAttribute("aria-pressed", String(b.dataset.mode === S.mode)); });
  }

  // ── Test myself ─────────────────────────────────────────────────────
  function renderTest(){
    var app = document.getElementById("app");
    if (!S.queue.length){
      app.innerHTML = '<div class="stage"><div class="empty">' +
        (S.reviseOnly ? "Nothing left to revise here — you've got every card in this set." : "No cards in this set.") +
        '</div></div>';
      return;
    }
    if (S.finished){ renderDone(); return; }
    var c = S.queue[S.idx];
    var left = S.queue.slice(S.idx).filter(function(x){ return !S.got[x.id]; }).length;
    var leftTxt = left ? (left + (left === 1 ? " card" : " cards") + ' to go <span class="soft">· about ' + minutes(left) + ' min</span>') : 'All got <span class="soft">· just flip through</span>';
    var isGot = !!S.got[c.id];
    var plainTitle = stripTags(c.title);
    app.innerHTML =
      '<div class="stage">' +
        '<div class="count-row"><span>Card ' + (S.idx + 1) + ' of ' + S.queue.length + (S.reviseOnly ? ' <span class="soft">· revising</span>' : '') + '</span><span>' + leftTxt + '</span></div>' +
        '<div class="card' + (S.flipped ? ' flipped' : '') + '" id="card">' +
          '<div class="card-inner">' +
            '<button type="button" class="face front" id="front" aria-label="' + plainTitle + '. Show the answer"' + (S.flipped ? ' tabindex="-1" aria-hidden="true"' : '') + '>' +
              '<span class="face-top">' + chip(c) + '<span class="day">' + c.dayLabel + '</span></span>' +
              '<span class="card-title">' + c.title + '</span>' +
              (c.section ? '<span class="section">' + c.section + '</span>' : '') +
              '<span class="label">Try to remember</span>' +
              '<span class="prompt">' + c.prompt + '</span>' +
              '<span class="hint">' + (isGot ? '<span class="got-badge">' + ICON.check + 'Got it</span>' : ICON.flip + 'Tap the card to see the answer') + '</span>' +
            '</button>' +
            '<div class="face back"' + (S.flipped ? '' : ' aria-hidden="true"') + '>' +
              '<div class="face-top"><span class="back-title">' + c.title + '</span><span class="day">' + c.dayLabel + '</span></div>' +
              answerHTML(c) +
              '<div class="answer-actions">' +
                '<button type="button" class="btn" data-act="unsure"' + (S.flipped ? '' : ' tabindex="-1"') + '>Not sure yet</button>' +
                '<button type="button" class="btn btn-primary" data-act="got" aria-pressed="' + isGot + '"' + (S.flipped ? '' : ' tabindex="-1"') + '>' + ICON.check + "I've got this</button>" +
              '</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
        '<div class="nav">' +
          '<button type="button" class="btn" data-act="prev" aria-label="Previous card"' + (S.idx === 0 ? ' disabled' : '') + '>' + ICON.left + '<span class="navtxt">Prev</span></button>' +
          '<button type="button" class="btn flip-btn" data-act="flip">' + (S.flipped ? 'Show question' : 'Show answer') + '</button>' +
          '<button type="button" class="btn" data-act="next" aria-label="Next card">' + '<span class="navtxt">' + (S.idx === S.queue.length - 1 ? 'Finish' : 'Next') + '</span>' + ICON.right + '</button>' +
        '</div>' +
        '<div class="keys"><kbd>Space</kbd> flip · <kbd>←</kbd> <kbd>→</kbd> move · <kbd>G</kbd> got it</div>' +
      '</div>';
    attachSwipe(document.getElementById("card"));
  }

  function renderDone(){
    var list = S.queue, gotN = list.filter(function(c){ return S.got[c.id]; }).length, rest = list.length - gotN;
    var msg = rest === 0
      ? "You've got every card in this set. Come back tomorrow for a quick look — that's how it stays in memory."
      : "You've got " + gotN + " of " + list.length + ". " + rest + (rest === 1 ? " card needs" : " cards need") + " one more look — that's completely normal.";
    document.getElementById("app").innerHTML =
      '<div class="stage"><div class="done">' +
        '<div class="done-mark">' + ICON.check + '</div>' +
        '<h3>' + (rest === 0 ? "Well done!" : "Nice work — you went through them all") + '</h3>' +
        '<p>' + msg + '</p>' +
        '<div class="done-actions">' +
          (rest ? '<button type="button" class="btn btn-primary" data-act="revise">Revise the ' + rest + " I wasn't sure about</button>" : '') +
          '<button type="button" class="btn" data-act="restart">Go through all again</button>' +
          '<button type="button" class="btn" data-act="toread">Quick read</button>' +
        '</div>' +
      '</div></div>';
  }

  // ── Quick read ──────────────────────────────────────────────────────
  function readCard(c, withFoot){
    var isGot = !!S.got[c.id];
    return '<article class="read-card' + (isGot ? ' is-got' : '') + '">' +
      '<div class="face-top">' + chip(c) + '<span class="day">' + c.dayLabel + '</span></div>' +
      '<div class="card-title">' + c.title + '</div>' +
      '<div class="prompt">' + c.prompt + '</div>' +
      answerHTML(c) +
      (withFoot ? '<div class="read-foot"><button type="button" class="btn' + (isGot ? ' btn-primary' : '') + '" data-act="toggle" data-id="' + c.id + '" aria-pressed="' + isGot + '">' + ICON.check + (isGot ? 'Got it' : "I've got this") + '</button></div>' : '') +
    '</article>';
  }
  function renderRead(){
    var list = filtered();
    document.getElementById("app").innerHTML = list.length
      ? '<div class="grid">' + list.map(function(c){ return readCard(c, true); }).join("") + '</div>'
      : '<div class="empty">No cards in this set.</div>';
  }
  function renderPrint(){
    document.getElementById("print-list").innerHTML = filtered().map(function(c){ return readCard(c, false); }).join("");
  }

  function render(){
    renderSeg(); renderProgress();
    document.querySelectorAll("#filters .chip-btn").forEach(function(b){ b.setAttribute("aria-pressed", String(b.dataset.filter === S.filter)); });
    if (S.mode === "test") renderTest(); else renderRead();
    renderPrint();
    save();
  }

  // ── actions ─────────────────────────────────────────────────────────
  function flip(){ if (S.mode !== "test" || S.finished) return; S.flipped = !S.flipped; render(); focusCard(); }
  function focusCard(){
    var t = S.flipped ? document.querySelector('[data-act="got"]') : document.getElementById("front");
    if (t) t.focus({preventScroll:true});
  }
  function go(step){
    if (S.mode !== "test" || S.finished) return;
    var n = S.idx + step;
    if (n < 0) return;
    if (n >= S.queue.length){ S.finished = true; S.flipped = false; render(); return; }
    S.idx = n; S.flipped = false; render();
  }
  function markGot(){
    var c = S.queue[S.idx]; if (!c) return;
    S.got[c.id] = true; renderProgress(); save();
    setTimeout(function(){ go(1); }, 180);
  }
  function markUnsure(){
    var c = S.queue[S.idx]; if (!c) return;
    delete S.got[c.id]; go(1);
  }
  function restart(reviseOnly){
    S.reviseOnly = reviseOnly; S.idx = 0; S.flipped = false; S.finished = false; S.mode = "test";
    buildQueue(); render(); window.scrollTo({top:0});
  }

  document.addEventListener("click", function(e){
    var t = e.target.closest("button"); if (!t) return;
    if (t.id === "front"){ if (!swipe.moved) flip(); return; }
    if (t.dataset.mode){ S.mode = t.dataset.mode; S.finished = false; S.flipped = false; render(); return; }
    if (t.dataset.filter){ S.filter = t.dataset.filter; S.reviseOnly = false; S.idx = 0; S.finished = false; S.flipped = false; buildQueue(); render(); return; }
    switch (t.dataset.act){
      case "flip": flip(); break;
      case "prev": go(-1); break;
      case "next": go(1); break;
      case "got": markGot(); break;
      case "unsure": markUnsure(); break;
      case "revise": restart(true); break;
      case "restart": restart(false); break;
      case "toread": S.mode = "read"; S.finished = false; render(); break;
      case "toggle":
        if (S.got[t.dataset.id]) delete S.got[t.dataset.id]; else S.got[t.dataset.id] = true;
        render(); break;
    }
  });

  document.addEventListener("keydown", function(e){
    if (S.mode !== "test" || e.altKey || e.ctrlKey || e.metaKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (e.key === "ArrowRight"){ e.preventDefault(); go(1); }
    else if (e.key === "ArrowLeft"){ e.preventDefault(); go(-1); }
    else if (e.key === " " || e.key === "Spacebar"){ if (tag === "button" && !e.target.closest(".card")) return; e.preventDefault(); flip(); }
    else if ((e.key === "g" || e.key === "G") && S.flipped){ markGot(); }
  });

  // swipe: left = next, right = prev; a tap still flips
  var swipe = {x:0, y:0, moved:false};
  function attachSwipe(el){
    if (!el) return;
    el.addEventListener("touchstart", function(e){ var p = e.touches[0]; swipe.x = p.clientX; swipe.y = p.clientY; swipe.moved = false; }, {passive:true});
    el.addEventListener("touchmove", function(e){ var p = e.touches[0]; if (Math.abs(p.clientX - swipe.x) > 12) swipe.moved = true; }, {passive:true});
    el.addEventListener("touchend", function(e){
      var p = e.changedTouches[0], dx = p.clientX - swipe.x, dy = p.clientY - swipe.y;
      if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.4){ go(dx < 0 ? 1 : -1); }
      setTimeout(function(){ swipe.moved = false; }, 60);
    });
  }

  // ── night mode ──────────────────────────────────────────────────────
  var mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  function isDark(){ var t = document.documentElement.getAttribute("data-theme"); return t ? t === "dark" : !!(mq && mq.matches); }
  function paintThemeBtn(){
    var dark = isDark();
    document.getElementById("theme-txt").textContent = dark ? "Day" : "Night";
    document.getElementById("theme-btn").setAttribute("aria-label", dark ? "Switch to day mode" : "Switch to night mode");
  }
  var th = loadTheme(); if (th === "dark" || th === "light") document.documentElement.setAttribute("data-theme", th);
  document.getElementById("theme-btn").addEventListener("click", function(){
    var next = isDark() ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next); saveTheme(next); paintThemeBtn();
  });
  if (mq && mq.addEventListener) mq.addEventListener("change", paintThemeBtn);
  paintThemeBtn();

  document.getElementById("print-btn").addEventListener("click", function(){ renderPrint(); window.print(); });

  // ── continue where you left off ─────────────────────────────────────
  buildQueue();
  if (saved.pos){
    var i = S.queue.findIndex(function(c){ return c.id === saved.pos; });
    if (i > 0){
      S.idx = i;
      document.getElementById("notice-text").textContent = "Welcome back — you're on card " + (i + 1) + " of " + S.queue.length + ".";
      document.getElementById("notice").classList.add("show");
    }
  }
  document.getElementById("notice-reset").addEventListener("click", function(){
    document.getElementById("notice").classList.remove("show");
    S.idx = 0; S.flipped = false; S.finished = false; render();
  });

  renderFilters();
  render();
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python -m app.content_builder.flashcards.renderer deck.json out.html")
        sys.exit(1)
    p = render_file(sys.argv[1], sys.argv[2])
    print(f"✅ Rendered → {p}")