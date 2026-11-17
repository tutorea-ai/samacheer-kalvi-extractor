"""Concept Canvas: dev-only static preview.

Turns a storyboard deck (concept_canvas.json) into a plain HTML page in /tmp
for reading and checking content before Node's renderer exists. No
animation, never deployed. KaTeX comes from a CDN (dev machines only).

    PYTHONPATH=. python3 -m app.content_builder.concept_canvas.preview deck.json [out.html]
"""
import html
import json
import sys
from pathlib import Path

KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist"

CSS = """
body{font-family:system-ui,sans-serif;max-width:860px;margin:24px auto;padding:0 16px;
     background:#faf6f0;color:#2b2420}
h1{margin:0 0 4px} .sub{color:#7a6a5c;margin-bottom:20px}
.card{background:#fff;border:1px solid #e6dccf;border-radius:12px;padding:16px 18px;margin:14px 0}
.top{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.day{background:#8b5e34;color:#fff;border-radius:6px;padding:2px 8px;font-size:13px}
.tpl{background:#efe6da;border-radius:6px;padding:2px 8px;font-size:12px;font-family:monospace}
.cap{color:#5a4a3c;margin:8px 0 12px;font-style:italic}
.sides{display:flex;gap:16px;font-weight:600;margin-bottom:6px}
ol{margin:0;padding-left:22px} li{margin:8px 0}
li.hl{background:#fff3df;border-left:3px solid #d08a2c;padding:4px 8px;border-radius:4px}
.lbl{font-weight:600} .meta{font-size:12px;color:#8a7a6c;font-family:monospace}
.f{margin-top:4px;font-size:1.1em}
.skip{background:#fff;border:1px dashed #d8c8b4;border-radius:12px;padding:12px 18px;margin:14px 0}
.usage{font-family:monospace;font-size:12px;color:#7a6a5c}
"""


def _e(s) -> str:
    return html.escape(str(s))


def _step(s: dict) -> str:
    meta = [f"icon: {s['icon']}"] if s.get("icon") else []
    meta += [f"side: {s['side']}"] if s.get("side") else []
    meta += [f"time: {s['time']}"] if s.get("time") else []
    f = f'<div class="f" data-tex="{_e(s["formula"])}"></div>' if s.get("formula") else ""
    m = f' <span class="meta">[{_e(", ".join(meta))}]</span>' if meta else ""
    cls = ' class="hl"' if s.get("highlight") else ""
    return (f'<li{cls}><span class="lbl">{_e(s["label"])}</span> — {_e(s["text"])}{m}'
            f"<br><span class='meta'>{len(s['label'])}/25 · {len(s['text'])}/80</span>{f}</li>")


def _day(d: dict) -> str:
    extra = ""
    if d.get("left_title"):
        extra = f'<div class="sides"><span>◀ {_e(d["left_title"])}</span><span>{_e(d["right_title"])} ▶</span></div>'
    if d.get("center"):
        extra = f'<div class="sides">● {_e(d["center"])}</div>'
    steps = "".join(_step(s) for s in d["steps"])
    return (f'<div class="card"><div class="top"><span class="day">Day {d["day"]}</span>'
            f'<b>{_e(d["title"])}</b><span class="tpl">{_e(d["template"])}</span></div>'
            f'<div class="cap">{_e(d["caption"])}</div>{extra}<ol>{steps}</ol></div>')


def render(deck: dict) -> str:
    days = "".join(_day(d) for d in deck.get("days", []))
    skips = "".join(f'<div class="skip"><b>Day {s["day"]} skipped</b> — {_e("; ".join(s["reasons"]))}</div>'
                    for s in deck.get("skipped_days", []))
    u = deck.get("usage", {})
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CC preview — {_e(deck.get('lesson_title', ''))}</title>
<link rel="stylesheet" href="{KATEX}/katex.min.css"><style>{CSS}</style></head><body>
<h1>Concept Canvas — {_e(deck.get('lesson_title', ''))}</h1>
<div class="sub">{_e(deck.get('subject', ''))} · class {_e(deck.get('class', ''))} ·
{len(deck.get('days', []))} storyboards · {len(deck.get('skipped_days', []))} skipped ·
<span class="usage">{u.get('calls', 0)} calls · {u.get('input_tokens', 0)} in / {u.get('output_tokens', 0)} out tokens</span></div>
{days}{skips}
<script src="{KATEX}/katex.min.js"></script>
<script>document.querySelectorAll('[data-tex]').forEach(function(el){{
  try {{ katex.render(el.dataset.tex, el, {{throwOnError:true, displayMode:true}}); }}
  catch(e) {{ el.textContent = '⚠ KaTeX: ' + el.dataset.tex; el.style.color = '#b00'; }}
}});</script></body></html>"""


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp") / f"cc_preview_{src.stem}.html"
    out.write_text(render(json.loads(src.read_text(encoding="utf-8"))), encoding="utf-8")
    print(f"👀 Preview: {out}")


if __name__ == "__main__":
    main()