"""
Homework: deck JSON -> one self-contained index.html.

Knows nothing about subjects: task labels come from each task, and every
field is optional so any profile renders. Same caramel family as Flash
Cards and Beyond the Book: one scrolling page of day cards, day chips to
jump to a day, a tap-to-reveal hint per task.
"""
import html
import re
from contextvars import ContextVar
from typing import Dict, List

from .subjects import get_profile

# Set once per page from the deck's subject profile.
_LETTER_SUBS: ContextVar[bool] = ContextVar("letter_subs", default=True)

BULB = ('<path d="M9 18h6M10 21h4"/>'
        '<path d="M12 3a6 6 0 0 0-3.6 10.8c.6.5 1 1.2 1.1 2h5c.1-.8.5-1.5 1.1-2A6 6 0 0 0 12 3z"/>')
CHEVRON = '<path d="M6 9l6 6 6-6"/>'
CHECK = '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.8 2.8L16 10"/>'
PENDING_NOTE = "Answer is being checked by our teachers. It will appear here soon."


def _e(s) -> str:
    return html.escape(str(s or ""), quote=True)


# v_d -> v<sub>d</sub>, l_AJ -> l<sub>AJ</sub>, R_(eq) -> R<sub>eq</sub>. Only after a
# letter or Greek symbol, and only 1–4 characters: anything else is left for the audit.
SUBSCRIPT_RE = re.compile(
    r"(?<=[A-Za-zα-ωΑ-Ω])_(?:\(([A-Za-z0-9]{1,6})\)|([A-Za-z0-9]{1,4})(?![A-Za-z0-9]))")


def _t(s) -> str:
    """Escape, then show subscripts the way the textbook does."""
    if not _LETTER_SUBS.get():
        return _e(s)
    return SUBSCRIPT_RE.sub(lambda m: f"<sub>{m.group(1) or m.group(2)}</sub>", _e(s))


def _svg(inner: str) -> str:
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{inner}</svg>'


def _grid(rows: List[List[str]]) -> str:
    """| | R | r | lines -> a table; the first row and first column are headings."""
    out = []
    for i, cells in enumerate(rows):
        tds = "".join(f'<{"th" if i == 0 or j == 0 else "td"}>{_t(c)}'
                      f'</{"th" if i == 0 or j == 0 else "td"}>' for j, c in enumerate(cells))
        out.append(f"<tr>{tds}</tr>")
    return f'<div class="grid"><table>{"".join(out)}</table></div>'


_SEP_RE = re.compile(r"^\|(?=.*-)[\s:|-]+\|$")   # Markdown "|---|---|": no content


def _is_row(line: str) -> bool:
    return len(line) > 1 and line.startswith("|") and line.endswith("|")


def _block(text: str, finals: bool = False) -> str:
    """Text -> paragraphs, with | a | b | lines as a table. Used by tasks and answers alike."""
    out, grid = [], []

    def flush():
        if grid:
            out.append(_grid(grid))
            grid.clear()

    for line in (text or "").split("\n"):
        line = line.strip()
        if _SEP_RE.match(line):
            continue
        if _is_row(line):
            grid.append([c.strip() for c in line[1:-1].split("|")])
            continue
        flush()
        if not line:
            continue
        final = finals and line.lower().startswith("final answer")
        out.append(f'<p class="{"final" if final else "step"}">{_t(line)}</p>')
    flush()
    return "".join(out)


def _answer(t: Dict, answers_on: bool) -> str:
    text = (t.get("answer") or "").strip()
    if not text:
        return f'<p class="answer-note">{_e(PENDING_NOTE)}</p>' if answers_on else ""
    return (f'<details class="answer"><summary>{_svg(CHECK)}<span>Show answer</span>'
            f'{_svg(CHEVRON)}</summary><div class="answer-body">{_block(text, finals=True)}'
            f'</div></details>')


def _task(i: int, t: Dict, answers_on: bool = False) -> str:
    hint = ""
    if t.get("hint"):
        ta = (f'<p class="ta" lang="ta">{_e(t["hint_ta"])}</p>' if t.get("hint_ta") else "")
        hint = (f'<details class="hint"><summary>{_svg(BULB)}<span>Show hint</span>'
                f'{_svg(CHEVRON)}</summary><div class="hint-body"><p>{_t(t["hint"])}</p>{ta}'
                f'</div></details>')
    answer = _answer(t, answers_on)
    reveal = f'<div class="reveal">{hint}{answer}</div>' if (hint or answer) else ""
    return (f'<section class="task {_e(t.get("kind"))}">'
            f'<p class="task-label"><span class="num">{i}</span>{_e(t.get("label"))}</p>'
            f'<div class="task-text">{_block(t.get("task"))}</div>{reveal}</section>')


def _day(d: Dict, answers_on: bool = False) -> str:
    review = '<span class="tag">Revision</span>' if d.get("is_review") else ""
    tasks = "".join(_task(i, t, answers_on) for i, t in enumerate(d.get("tasks") or [], 1))
    return (f'<article class="card{" review" if d.get("is_review") else ""}" '
            f'id="hw-day-{_e(d.get("day"))}">'
            f'<div class="card-top"><span class="day">Day {_e(d.get("day"))}</span>{review}'
            f'<h2 class="topic">{_t(d.get("title"))}</h2></div>{tasks}</article>')


def _chips(days: List[Dict]) -> str:
    if len(days) < 2:
        return ""
    links = "".join(f'<a class="chip" '
                    f'href="#hw-day-{_e(d.get("day"))}" data-target="hw-day-{_e(d.get("day"))}" '
                    f'title="{_e(d.get("title"))}">{_e(d.get("day"))}</a>'
                    for d in days)
    return (f'<nav class="chips" aria-label="Jump to a day">'
            f'<span class="chips-label">Day</span>{links}</nav>')


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
  --hint-bg:#FFFAEC; --hint-line:#EFD49E;
  --shadow:0 1px 2px rgba(60,45,10,.06),0 8px 24px rgba(60,45,10,.07);
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--ink)}
body{font:16px/1.6 'Noto Sans','Noto Sans Tamil',system-ui,sans-serif}
svg{width:18px;height:18px;flex:none;fill:none;stroke:currentColor;stroke-width:1.8;
    stroke-linecap:round;stroke-linejoin:round}
.wrap{max-width:860px;margin:0 auto;padding:28px 16px 48px}
.top{margin-bottom:20px}
.eyebrow{margin:0;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--warm)}
.top h1{margin:4px 0 2px;font:600 30px/1.25 'Noto Serif',Georgia,serif}
.tagline{margin:0;color:var(--ink-3)}

.chips{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin:0 0 20px}
.chips-label{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
             color:var(--ink-3);margin-right:4px}
.chip{display:inline-flex;align-items:center;justify-content:center;min-width:38px;height:38px;
      padding:0 10px;border:1px solid var(--line);background:var(--surface);color:var(--ink-2);
      font:600 14px 'Noto Sans',sans-serif;border-radius:999px;text-decoration:none}
.chip:hover{border-color:var(--warm);color:var(--warm)}
.chip:focus-visible{outline:2px solid var(--warm);outline-offset:2px}

.cards{display:grid;gap:18px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:22px 22px 20px;
      box-shadow:var(--shadow);border-top:4px solid var(--warm);scroll-margin-top:12px}
.card.review{border-top-color:var(--accent)}
.card-top{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;margin-bottom:14px}
.day{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
     background:var(--warm-soft);color:var(--warm);padding:3px 9px;border-radius:6px}
.card.review .day{background:var(--accent-soft);color:var(--accent)}
.tag{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;
     color:#fff;background:var(--accent);padding:3px 9px;border-radius:6px}
.topic{flex:1 1 100%;margin:2px 0 0;font:600 20px/1.4 'Noto Serif',Georgia,serif}

.task{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#FFFDF6}
.task + .task{margin-top:12px}
.task-label{display:flex;align-items:center;gap:8px;margin:0 0 6px;font-size:13px;font-weight:700;
            letter-spacing:.04em;text-transform:uppercase;color:var(--warm)}
.task.apply .task-label{color:var(--accent)}
.num{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;
     border-radius:50%;background:var(--warm);color:#fff;font-size:12px;letter-spacing:0}
.task.apply .num{background:var(--accent)}
.task-text{font-size:16px;color:var(--ink)}
.task-text p{margin:0}
.task-text p + p{margin-top:6px}

.hint{margin-top:12px}
.hint summary{display:inline-flex;align-items:center;gap:6px;cursor:pointer;list-style:none;
              font:600 14px 'Noto Sans',sans-serif;color:var(--ink-2);padding:6px 12px;
              border:1px solid var(--hint-line);border-radius:999px;background:var(--hint-bg)}
.hint summary::-webkit-details-marker{display:none}
.hint summary svg{width:16px;height:16px}
.hint summary svg:last-child{transition:transform .15s}
.hint[open] summary svg:last-child{transform:rotate(180deg)}
.hint[open] summary span::after{content:""}
.hint summary:focus-visible{outline:2px solid var(--warm);outline-offset:2px}
.hint-body{margin-top:10px;padding:10px 14px;border-radius:10px;background:var(--hint-bg);
           border:1px solid var(--hint-line)}
.hint-body p{margin:0;font-size:15px;color:var(--ink-2)}
.ta{margin:10px 0 0 !important;padding:8px 12px;border-radius:8px;background:var(--ta-bg);
    border:1px solid var(--ta-line);color:var(--ta-ink) !important;
    font:500 15px/1.75 'Noto Sans Tamil','Noto Sans',sans-serif !important}

.reveal{display:flex;flex-wrap:wrap;align-items:flex-start;gap:8px;margin-top:12px}
.reveal .hint{margin-top:0}
.reveal details[open]{flex-basis:100%}
.answer summary{display:inline-flex;align-items:center;gap:6px;cursor:pointer;list-style:none;
                font:600 14px 'Noto Sans',sans-serif;color:var(--ink-3);padding:6px 12px;
                border:1px dashed var(--line);border-radius:999px;background:transparent}
.answer summary::-webkit-details-marker{display:none}
.answer summary svg{width:16px;height:16px}
.answer summary svg:last-child{transition:transform .15s}
.answer[open] summary{color:var(--accent);border-style:solid;border-color:var(--accent)}
.answer[open] summary svg:last-child{transform:rotate(180deg)}
.answer summary:focus-visible{outline:2px solid var(--warm);outline-offset:2px}
.answer-body{margin-top:10px;padding:10px 14px;border-radius:10px;background:var(--accent-soft);
             border:1px solid #BFDCD8}
.answer-body p{margin:0;font-size:15px;color:var(--ink)}
.answer-body p + p{margin-top:4px}
.answer-body .final{margin-top:8px;font-weight:700;color:var(--accent)}
.grid{overflow-x:auto;margin:8px 0}
.grid table{border-collapse:collapse;background:var(--surface)}
.grid th,.grid td{border:1px solid #BFDCD8;padding:5px 12px;text-align:center;font-size:15px}
.grid th{background:var(--accent-soft);color:var(--accent);font-weight:700}
.grid tr:first-child th:first-child{background:transparent;border-top-color:transparent;
                                    border-left-color:transparent}
.answer-note{margin:0;align-self:center;font-size:13px;font-style:italic;color:var(--ink-3)}

@media (max-width:560px){
  .wrap{padding:20px 16px 36px}
  .top h1{font-size:25px}
  .card{padding:18px 16px}
  .topic{font-size:18px}
  .task{padding:12px 14px}
  .chip{min-width:34px;height:34px;font-size:13px}
}
@media print{
  html,body{background:#fff}
  .chips{display:none}
  .card{box-shadow:none;break-inside:avoid}
}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <p class="eyebrow">Homework</p>
    <h1>%%TITLE%%</h1>
    <p class="tagline">Two tasks for each day. Try first; open the hint only if you're stuck.</p>
  </header>
  %%CHIPS%%
  <main class="cards">%%DAYS%%</main>
</div>
<script>
(function(){
  // scrollIntoView also scrolls the outer page when this sits in a full-height iframe.
  document.querySelectorAll('.chip').forEach(function(a){
    a.addEventListener('click', function(e){
      var t = document.getElementById(a.getAttribute('data-target'));
      if (!t) return;
      e.preventDefault();
      t.scrollIntoView({behavior: 'smooth', block: 'start'});
    });
  });
})();
</script>
</body>
</html>
"""


def render_deck(deck: Dict) -> str:
    lesson = deck.get("lesson") or {}
    title = lesson.get("title") or "Homework"
    days = deck.get("days") or []
    token = _LETTER_SUBS.set(get_profile(deck.get("subject", "")).letter_subscripts)
    try:
        return (TEMPLATE
                .replace("%%PAGE_TITLE%%", _e(f"{title} · Homework"))
                .replace("%%TITLE%%", _e(title))
                .replace("%%CHIPS%%", _chips(days))
                .replace("%%DAYS%%", "".join(_day(d, bool(deck.get("answers"))) for d in days)))
    finally:
        _LETTER_SUBS.reset(token)