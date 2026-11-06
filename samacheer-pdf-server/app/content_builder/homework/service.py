"""
Homework: run one lesson end to end.

Homework lives in the LP folder with the 'lp' segment swapped for
'homework' (same rule as Flash Cards and Beyond the Book). Skips when
already deployed, otherwise generates, renders and writes
index.html + homework.json there.
Uses only bridge's public find_deployed(); bridge.py is not changed.
lesson_title() is Homework's own copy, so BB changes never affect it.
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Optional

HOMEWORK_FOLDER = "homework"
MIN_HTML_BYTES = 10240


def homework_dir(lp_path) -> Optional[Path]:
    """LP index.html path -> Homework folder (last 'lp' segment swapped)."""
    parts = list(Path(lp_path).parts)
    if "lp" not in parts:
        print(f"❌ Homework: cannot derive folder from {lp_path}")
        return None
    i = len(parts) - 1 - parts[::-1].index("lp")
    parts[i] = HOMEWORK_FOLDER
    folder = Path(*parts)
    return folder.parent if folder.suffix == ".html" else folder


def is_deployed(folder: Path) -> bool:
    html_f, json_f = folder / "index.html", folder / "homework.json"
    return html_f.exists() and html_f.stat().st_size > MIN_HTML_BYTES and json_f.exists()


def missing_answers(deck: Dict) -> bool:
    """True when the subject has answers on and any task still has no answer."""
    from .subjects import get_profile
    if not get_profile(deck.get("subject", "")).answers:
        return False
    return any(not (t.get("answer") or "").strip()
               for d in deck.get("days", []) for t in d.get("tasks", []))


def lesson_title(index_data: dict, term_key: str, subject: str, discipline: str,
                 unit_num, fallback: str, lesson_choice: int = 1) -> str:
    """Lesson title from the curriculum index (3 index shapes); falls back to the file name base."""
    same = lambda a, b: str(a) == str(b)
    try:
        term = index_data[term_key]

        # Physics, Biology, Pure Science, Maths: term -> chapters -> {discipline|subject: [{chapter, title}]}
        chapters = term.get("chapters", {})
        keys = [discipline, (subject or "").lower()]
        if (subject or "").lower() in ("maths", "math", "mathematics"):
            keys.append("maths")
        for k in keys:
            if k and k in chapters:
                sel = next((c for c in chapters[k] if same(c.get("chapter"), unit_num)), None)
                if sel and sel.get("title"):
                    return sel["title"]

        # Social Science: term -> disciplines -> {history: [{unit, title}]} (or without the wrapper)
        disc = term.get("disciplines", term)
        if discipline and isinstance(disc, dict) and isinstance(disc.get(discipline), list):
            sel = next((u for u in disc[discipline] if same(u.get("unit"), unit_num)), None)
            if sel and sel.get("title"):
                return sel["title"]

        # English: term -> units -> [{unit, prose: {title}, poem: {title}, ...}]
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
        print(f"   ⚠️  Homework: could not read lesson title: {e}")
    return fallback


def run_homework(lp_path, lesson: Dict, force: bool, temp_dir: Path, filename_base: str) -> Dict:
    folder = homework_dir(lp_path)
    if folder is None:
        return {"error": True, "message": "Could not derive the Homework folder from the LP path"}

    answers_only = False
    if not force and is_deployed(folder):
        deck = json.loads((folder / "homework.json").read_text(encoding="utf-8"))
        if not missing_answers(deck):
            print(f"⏭️  Homework: already deployed with every answer at {folder} — skipping")
            return {"error": False, "filename": f"{filename_base}_homework.html", "file_path": "",
                    "deployed": ["homework"], "skipped": True,
                    "message": "Homework already deployed — skipped (send force=true to rebuild)"}
        answers_only = True
        print(f"📝 Homework: deployed at {folder} — adding missing answers only, tasks unchanged")

    # Imported here so the Claude client is created only when Homework actually runs.
    from .builder import homework_builder
    from .renderer import render_deck

    if not answers_only:
        deck = homework_builder.generate(str(lp_path), lesson)
        if not deck or not deck.get("days"):
            return {"error": True, "message": "Homework generation failed — no day passed the checks"}
    homework_builder.generate_answers(str(lp_path), deck)

    json_tmp = Path(temp_dir) / f"{filename_base}_homework.json"
    html_tmp = Path(temp_dir) / f"{filename_base}_homework.html"
    with open(json_tmp, "w", encoding="utf-8") as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    with open(html_tmp, "w", encoding="utf-8") as f:
        f.write(render_deck(deck))

    try:
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(html_tmp, folder / "index.html")
        shutil.copy2(json_tmp, folder / "homework.json")
        print(f"🚀 Homework SUCCESS: {folder}")
    except Exception as e:
        return {"error": True, "message": f"Homework built but deploy failed: {e}"}

    total = sum(len(d["tasks"]) for d in deck["days"])
    answered = sum(1 for d in deck["days"] for t in d["tasks"] if (t.get("answer") or "").strip())
    msg = (f"Homework answers added — {answered}/{total} answers" if answers_only
           else f"Homework generated and deployed — {len(deck['days'])} days, {answered}/{total} answers")
    if deck.get("skipped_days"):
        msg += f" (skipped days {[d['day'] for d in deck['skipped_days']]})"
    print(f"✅ {msg}")
    return {"error": False, "filename": f"{filename_base}_homework.html",
            "file_path": str(html_tmp), "deployed": ["homework"], "message": msg}