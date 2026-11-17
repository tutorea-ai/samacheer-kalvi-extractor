"""Concept Canvas: run one lesson end to end.

Concept Canvas lives in the LP folder with the last 'lp' segment swapped for
'canvas' (agreed with the Node team), as concept_canvas.json. Same call shape
as Homework's run_homework(): processor.py finds the LP and the title.

  not deployed / force    -> full run
  deployed, failed days   -> re-run only those days, merge (repair)
  deployed, nothing to do -> skip at no cost
  test=True               -> /tmp + preview, never deployed

Every day is re-validated before writing; any failure means nothing is
deployed. The write is atomic so Node never reads a half-written file.
lesson_title() is Concept Canvas's own copy (from Homework).
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

CANVAS_FOLDER = "canvas"
CANVAS_FILE = "concept_canvas.json"

# USD per million tokens (input, output). Unknown model -> tokens only.
PRICES = {"claude-sonnet-4-6": (3.0, 15.0)}

# Skips that are decisions, not failures: never re-run automatically.
_NOT_REPAIRABLE = ("review day", "writer:")


def canvas_dir(lp_path) -> Optional[Path]:
    """LP index.html path or folder -> Concept Canvas folder (last 'lp' segment swapped)."""
    parts = list(Path(lp_path).parts)
    if "lp" not in parts:
        print(f"❌ Concept Canvas: cannot derive folder from {lp_path}")
        return None
    i = len(parts) - 1 - parts[::-1].index("lp")
    parts[i] = CANVAS_FOLDER
    folder = Path(*parts)
    return folder.parent if folder.suffix == ".html" else folder


def lesson_title(index_data: dict, term_key: str, subject: str, discipline: str,
                 unit_num, fallback: str, lesson_choice: int = 1) -> str:
    """Lesson title from the curriculum index (3 index shapes); falls back to the file name base."""
    same = lambda a, b: str(a) == str(b)
    try:
        term = index_data[term_key]

        chapters = term.get("chapters", {})
        keys = [discipline, (subject or "").lower()]
        if (subject or "").lower() in ("maths", "math", "mathematics"):
            keys.append("maths")
        for k in keys:
            if k and k in chapters:
                sel = next((c for c in chapters[k] if same(c.get("chapter"), unit_num)), None)
                if sel and sel.get("title"):
                    return sel["title"]

        disc = term.get("disciplines", term)
        if discipline and isinstance(disc, dict) and isinstance(disc.get(discipline), list):
            sel = next((u for u in disc[discipline] if same(u.get("unit"), unit_num)), None)
            if sel and sel.get("title"):
                return sel["title"]

        units = term.get("units")
        if units:
            seq = units if isinstance(units, list) else list(units.values())
            u = next((x for x in seq if isinstance(x, dict) and same(x.get("unit"), unit_num)), None)
            if u:
                parts = [u[k] for k in ("prose", "poem", "supplementary", "play", "drama")
                         if isinstance(u.get(k), dict)]
                if 1 <= int(lesson_choice) <= len(parts) and parts[int(lesson_choice) - 1].get("title"):
                    return parts[int(lesson_choice) - 1]["title"]
    except Exception as e:
        print(f"   ⚠️  Concept Canvas: could not read lesson title: {e}")
    return fallback


def repairable_days(deck: Dict) -> List[int]:
    return [s["day"] for s in deck.get("skipped_days", [])
            if not any(r.startswith(_NOT_REPAIRABLE) for r in s.get("reasons", []))]


def audit(deck: Dict) -> Dict[int, list]:
    """Re-validate every day on a copy. Returns {day: problems} for failures only."""
    from .schema import validate_day
    from .subjects import get_profile
    p = get_profile(deck.get("subject", ""))
    bad = {}
    for d in deck.get("days", []):
        probs, _ = validate_day(json.loads(json.dumps(d)), p)
        if probs:
            bad[d["day"]] = probs
    return bad


def cost_line(usage: Dict, model: str) -> str:
    i, o = usage.get("input_tokens", 0), usage.get("output_tokens", 0)
    line = f"{usage.get('calls', 0)} calls, {i} in / {o} out tokens"
    if model in PRICES:
        pin, pout = PRICES[model]
        line += f" ≈ ${i / 1e6 * pin + o / 1e6 * pout:.2f}"
    return line


def _write_atomic(path: Path, deck: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name("." + path.name + ".tmp")
    tmp.write_text(json.dumps(deck, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def _merge(old: Dict, new: Dict) -> Dict:
    """Put re-generated days into the deployed deck; keep everything else."""
    days = {d["day"]: d for d in old["days"]}
    days.update({d["day"]: d for d in new["days"]})
    redone = {d["day"] for d in new["days"]} | {s["day"] for s in new["skipped_days"]}
    old["days"] = [days[n] for n in sorted(days)]
    old["skipped_days"] = sorted(
        [s for s in old["skipped_days"] if s["day"] not in redone] + new["skipped_days"],
        key=lambda s: s["day"])
    old["generated_at"] = new["generated_at"]
    for k in ("calls", "input_tokens", "output_tokens"):
        old.setdefault("usage", {})[k] = old["usage"].get(k, 0) + new["usage"].get(k, 0)
    return old


def run_concept_canvas(lp_path, lesson: Dict, force: bool, temp_dir: Path,
                       filename_base: str, test: bool = False) -> Dict:
    """lesson = {"class": 12, "subject": "physics", "title": "..."} (slug comes from the folder)."""
    folder = canvas_dir(lp_path)
    if folder is None:
        return {"error": True, "message": "Could not derive the Concept Canvas folder from the LP path"}
    target = folder / CANVAS_FILE
    lesson = dict(lesson, slug=folder.name)

    old, only = None, None
    if not force and not test and target.exists():
        old = json.loads(target.read_text(encoding="utf-8"))
        only = repairable_days(old)
        if not only:
            print(f"⏭️  Concept Canvas: already deployed at {folder} — skipping")
            return {"error": False, "filename": CANVAS_FILE, "file_path": str(target),
                    "deployed": ["canvas"], "skipped": True,
                    "message": "Concept Canvas already deployed — skipped (send force=true to rebuild)"}
        print(f"🔧 Concept Canvas: deployed at {folder} — repairing days {only} only")

    # Imported here so the Claude client is created only when Concept Canvas actually runs.
    from .builder import concept_canvas_builder

    new = concept_canvas_builder.generate(str(lp_path), lesson, only_days=only)
    cost = cost_line(new["usage"], new.get("model", ""))
    deck = _merge(old, new) if old else new
    if not deck.get("days"):
        return {"error": True, "message": f"Concept Canvas generation failed — no day passed ({cost})"}

    bad = audit(deck)
    if bad:
        print(f"❌ Concept Canvas audit failed, nothing deployed: {bad}")
        return {"error": True, "message": f"Concept Canvas audit failed on days {sorted(bad)} — not deployed"}

    if test:
        out = Path("/tmp") / f"cc_{filename_base}.json"
        _write_atomic(out, deck)
        from .preview import render
        prev = out.with_suffix(".html")
        prev.write_text(render(deck), encoding="utf-8")
        msg = f"Concept Canvas TEST — {len(deck['days'])} days → {out} (preview {prev}); not deployed · {cost}"
        print(f"🧪 {msg}")
        return {"error": False, "filename": out.name, "file_path": str(out), "deployed": [], "message": msg}

    try:
        _write_atomic(target, deck)
    except Exception as e:
        return {"error": True, "message": f"Concept Canvas built but deploy failed: {e}"}

    msg = (f"Concept Canvas {'repaired' if old else 'generated and deployed'} — "
           f"{len(deck['days'])} days")
    left = [s["day"] for s in deck.get("skipped_days", [])]
    if left:
        msg += f" (skipped days {left})"
    msg += f" · {cost}"
    print(f"🚀 Concept Canvas SUCCESS: {folder}\n✅ {msg}")
    return {"error": False, "filename": CANVAS_FILE, "file_path": str(target),
            "deployed": ["canvas"], "message": msg}