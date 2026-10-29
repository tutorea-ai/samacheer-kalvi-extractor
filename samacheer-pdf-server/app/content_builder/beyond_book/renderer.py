"""
Beyond the Book: deck JSON -> one self-contained index.html.

Knows nothing about subjects: chip labels come from the deck's
connections, and every field is optional so any profile renders.
Same caramel family as Flash Cards; story layout instead of flip cards.
"""
import html
from typing import Dict, List

# Inline SVG icons (stroke style), keyed by connection key. Unknown keys get a dot.
ICONS = {
    "home": '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>',
    "around": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/>'
              '<circle cx="12" cy="10" r="2.2"/>',
    "tech": '<rect x="6" y="6" width="12" height="12" rx="2"/>'
            '<path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    "nature": '<path d="M5 19c0-8 6-14 15-14 0 9-6 15-14 15"/><path d="M5 19l7-7"/>',
    "careers": '<rect x="3" y="7" width="18" height="13" rx="2"/>'
               '<path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M3 13h18"/>',
    "building": '<rect x="3" y="13" width="8" height="8" rx="1"/>'
                '<rect x="13" y="13" width="8" height="8" rx="1"/>'
                '<rect x="8" y="3" width="8" height="8" rx="1"/>',
}
DOT = '<circle cx="12" cy="12" r="4"/>'
EYE = ('<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/>'
       '<circle cx="12" cy="12" r="3"/>')
ARROW = '<path d="M7 17L17 7M8 7h9v9"/>'
SPARK = '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/>'


def _e(s) -> str:
    return html.escape(str(s or ""), quote=True)


def _svg(inner: str) -> str:
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{inner}</svg>'


def _hero(b: Dict) -> str:
    if not b:
        return ""
    ta = f'<p class="ta" lang="ta">{_e(b.get("tamil_line"))}</p>' if b.get("tamil_line") else ""
    return (f'<section class="hero">'
            f'<p class="hero-label">The big why</p>'
            f'<h2>{_e(b.get("question"))}</h2>'
            f'<p class="hero-story">{_e(b.get("story"))}</p>{ta}</section>')


def _card(c: Dict, labels: Dict[str, str]) -> str:
    key = c.get("connection", "")
    label = labels.get(key, key)
    icon = _svg(ICONS.get(key, DOT))
    panels = []
    if c.get("where_you_see_it"):
        panels.append(f'<section class="panel see"><h3>{_svg(EYE)}Where you see it</h3>'
                      f'<p>{_e(c["where_you_see_it"])}</p></section>')
    if c.get("beyond_school"):
        panels.append(f'<section class="panel beyond"><h3>{_svg(ARROW)}Beyond school</h3>'
                      f'<p>{_e(c["beyond_school"])}</p></section>')
    try_this = (f'<p class="try">{_svg(SPARK)}<span><b>Try this:</b> {_e(c["try_this"])}</span></p>'
                if c.get("try_this") else "")
    ta = f'<p class="ta" lang="ta">{_e(c["tamil_line"])}</p>' if c.get("tamil_line") else ""
    return (f'<article class="card" data-conn="{_e(key)}">'
            f'<div class="card-top"><span class="day">Day {_e(c.get("day"))}</span>'
            f'<span class="topic">{_e(c.get("title"))}</span>'
            f'<span class="conn">{icon}{_e(label)}</span></div>'
            f'<h2 class="hook">{_e(c.get("hook"))}</h2>'
            f'<p class="link">{_e(c.get("link"))}</p>'
            f'<div class="panels">{"".join(panels)}</div>{try_this}{ta}</article>')


def _chips(conns: List[Dict]) -> str:
    if len(conns) < 2:
        return ""
    btns = ['<button class="chip" data-key="all" aria-pressed="true">All</button>']
    for x in conns:
        btns.append(f'<button class="chip" data-key="{_e(x["key"])}" aria-pressed="false">'
                    f'{_svg(ICONS.get(x["key"], DOT))}{_e(x["label"])}</button>')
    return f'<nav class="chips" aria-label="Filter by connection">{"".join(btns)}</nav>'


def _note(left_out: List[Dict]) -> str:
    if not left_out:
        return ""
    days = ", ".join(str(d.get("day")) for d in left_out)
    return (f'<p class="note">Days {_e(days)} teach lab methods and building-block ideas '
            f'without an honest everyday example, so they have no card here.</p>')


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%PAGE_TITLE%%</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&family=Noto+Serif:wght@500;600&family=Noto+Sans+Tamil:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#FBF4E2; --surface:#FFFFFF; --ink:#1F2A2E; --ink-2:#4F4A3B; --ink-3:#6B6450;
  --line:#E7DABA; --accent:#0B6B67; --accent-soft:#E3F1EF;
  --warm:#B5482A; --warm-soft:#FCEBDD;
  --ta-bg:#FFF6E3; --ta-line:#EFD49E; --ta-ink:#4A3410;
  --hero-bg:#1F2A2E; --hero-ink:#FBF4E2; --hero-ink-2:#D9CFB4; --hero-accent:#F2C46D;
  --shadow:0 1px 2px rgba(60,45,10,.06),0 8px 24px rgba(60,45,10,.07);
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink)}
body{font:16px/1.6 'Noto Sans','Noto Sans Tamil',system-ui,sans-serif}
svg{width:18px;height:18px;flex:none;fill:none;stroke:currentColor;stroke-width:1.8;
    stroke-linecap:round;stroke-linejoin:round}
.wrap{max-width:860px;margin:0 auto;padding:28px 16px 48px}
.top{margin-bottom:22px}
.eyebrow{margin:0;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--warm)}
.top h1{margin:4px 0 2px;font:600 30px/1.25 'Noto Serif',Georgia,serif}
.tagline{margin:0;color:var(--ink-3)}

.hero{background:var(--hero-bg);color:var(--hero-ink);border-radius:18px;padding:26px 24px;
      box-shadow:var(--shadow);margin-bottom:22px}
.hero-label{margin:0 0 6px;font-size:12px;font-weight:700;letter-spacing:.1em;
            text-transform:uppercase;color:var(--hero-accent)}
.hero h2{margin:0 0 12px;font:600 24px/1.35 'Noto Serif',Georgia,serif}
.hero-story{margin:0;color:var(--hero-ink-2);font-size:16.5px}
.hero .ta{margin-top:16px;background:rgba(242,196,109,.12);border-color:rgba(242,196,109,.35);color:var(--hero-ink)}

.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--surface);
      color:var(--ink-2);font:500 14px 'Noto Sans',sans-serif;padding:7px 13px;border-radius:999px;cursor:pointer}
.chip svg{width:16px;height:16px}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.chip:focus-visible{outline:2px solid var(--warm);outline-offset:2px}

.cards{display:grid;gap:18px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:22px 22px 20px;
      box-shadow:var(--shadow);border-top:4px solid var(--warm)}
.card[hidden]{display:none}
.card-top{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;margin-bottom:10px}
.day{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
     background:var(--warm-soft);color:var(--warm);padding:3px 9px;border-radius:6px}
.topic{font-size:14px;color:var(--ink-3);flex:1 1 200px}
.conn{display:inline-flex;align-items:center;gap:5px;font-size:13px;font-weight:600;color:var(--accent);
      background:var(--accent-soft);padding:3px 10px;border-radius:999px}
.conn svg{width:15px;height:15px}
.hook{margin:0 0 10px;font:600 21px/1.4 'Noto Serif',Georgia,serif}
.link{margin:0 0 16px;color:var(--ink-2)}
.panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.panels:empty{display:none}
.panel{border:1px solid var(--line);border-radius:12px;padding:12px 14px;background:#FFFDF6}
.panel h3{display:flex;align-items:center;gap:6px;margin:0 0 6px;font-size:13px;font-weight:700;
          letter-spacing:.04em;text-transform:uppercase;color:var(--ink-3)}
.panel.see h3{color:var(--accent)}
.panel.beyond h3{color:var(--warm)}
.panel p{margin:0;font-size:15px}
.try{display:flex;gap:8px;margin:14px 0 0;padding:10px 12px;border-radius:10px;
     background:var(--accent-soft);font-size:15px}
.try svg{color:var(--accent);margin-top:3px}
.ta{margin:14px 0 0;padding:10px 14px;border-radius:10px;background:var(--ta-bg);
    border:1px solid var(--ta-line);color:var(--ta-ink);
    font:500 16px/1.75 'Noto Sans Tamil','Noto Sans',sans-serif}
.note{margin:26px 0 0;font-size:14px;color:var(--ink-3);text-align:center}

@media (max-width:560px){
  .wrap{padding:20px 16px 36px}
  .top h1{font-size:25px}
  .hero{padding:22px 18px}
  .hero h2{font-size:21px}
  .card{padding:18px 16px}
  .hook{font-size:19px}
}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <p class="eyebrow">Beyond the Book</p>
    <h1>%%TITLE%%</h1>
    <p class="tagline">Where your lesson meets your life</p>
  </header>
  %%HERO%%
  %%CHIPS%%
  <main class="cards">%%CARDS%%</main>
  %%NOTE%%
</div>
<script>
(function(){
  var chips = document.querySelectorAll('.chip');
  var cards = document.querySelectorAll('.card');
  chips.forEach(function(b){
    b.addEventListener('click', function(){
      var k = b.getAttribute('data-key');
      chips.forEach(function(x){ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      cards.forEach(function(c){ c.hidden = !(k === 'all' || c.getAttribute('data-conn') === k); });
    });
  });
})();
</script>
</body>
</html>
"""


def render_deck(deck: Dict) -> str:
    lesson = deck.get("lesson") or {}
    title = lesson.get("title") or "Beyond the Book"
    conns = deck.get("connections") or []
    labels = {x["key"]: x["label"] for x in conns}
    cards = "".join(_card(c, labels) for c in deck.get("cards") or [])
    return (TEMPLATE
            .replace("%%PAGE_TITLE%%", _e(f"{title} · Beyond the Book"))
            .replace("%%TITLE%%", _e(title))
            .replace("%%HERO%%", _hero(deck.get("big_why")))
            .replace("%%CHIPS%%", _chips(conns))
            .replace("%%CARDS%%", cards)
            .replace("%%NOTE%%", _note(deck.get("left_out_days") or [])))