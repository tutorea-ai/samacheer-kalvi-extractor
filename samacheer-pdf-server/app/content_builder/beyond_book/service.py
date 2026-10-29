"""
Beyond the Book: run one lesson end to end.

BB lives in the LP folder with the 'lp' segment swapped for 'beyond'
(same rule as Flash Cards). Skips when already deployed, otherwise
generates, renders and writes index.html + beyond.json there.
Uses only bridge's public find_deployed(); bridge.py is not changed.
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Optional

BEYOND_FOLDER = "beyond"
MIN_HTML_BYTES = 10240


def beyond_dir(lp_path) -> Optional[Path]:
    """LP index.html path -> BB folder (last 'lp' segment swapped)."""
    parts = list(Path(lp_path).parts)
    if "lp" not in parts:
        print(f"❌ Beyond: cannot derive folder from {lp_path}")
        return None
    i = len(parts) - 1 - parts[::-1].index("lp")
    parts[i] = BEYOND_FOLDER
    return Path(*parts).parent


def is_deployed(folder: Path) -> bool:
    html_f, json_f = folder / "index.html", folder / "beyond.json"
    return html_f.exists() and html_f.stat().st_size > MIN_HTML_BYTES and json_f.exists()


def lesson_title(index_data: dict, term_key: str, subject: str,
                 discipline: str, unit_num, fallback: str) -> str:
    """Chapter title from the curriculum index; falls back to the file name base."""
    try:
        chapters = index_data[term_key].get("chapters", {})
        keys = [discipline, (subject or "").lower()]
        if (subject or "").lower() in ("maths", "math", "mathematics"):
            keys.append("maths")
        for k in keys:
            if k and k in chapters:
                sel = next((c for c in chapters[k] if c.get("chapter") == unit_num), None)
                if sel and sel.get("title"):
                    return sel["title"]
    except Exception as e:
        print(f"   ⚠️  Beyond: could not read chapter title: {e}")
    return fallback


def run_beyond(lp_path, lesson: Dict, force: bool, temp_dir: Path, filename_base: str) -> Dict:
    folder = beyond_dir(lp_path)
    if folder is None:
        return {"error": True, "message": "Could not derive the Beyond the Book folder from the LP path"}

    if not force and is_deployed(folder):
        print(f"⏭️  Beyond: already deployed at {folder} — skipping")
        return {"error": False, "filename": f"{filename_base}_beyond.html", "file_path": "",
                "deployed": ["beyond"], "skipped": True,
                "message": "Beyond the Book already deployed — skipped (send force=true to rebuild)"}

    # Imported here so the Claude client is created only when BB actually runs.
    from .builder import beyond_builder
    from .renderer import render_deck

    deck = beyond_builder.generate(str(lp_path), lesson)
    if not deck or not deck.get("cards"):
        return {"error": True, "message": "Beyond the Book generation failed — no cards passed the checks"}

    json_tmp = Path(temp_dir) / f"{filename_base}_beyond.json"
    html_tmp = Path(temp_dir) / f"{filename_base}_beyond.html"
    with open(json_tmp, "w", encoding="utf-8") as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    with open(html_tmp, "w", encoding="utf-8") as f:
        f.write(render_deck(deck))

    try:
        folder.mkdir(parents=True, exist_ok=True)
        shutil.copy2(html_tmp, folder / "index.html")
        shutil.copy2(json_tmp, folder / "beyond.json")
        print(f"🚀 Beyond SUCCESS: {folder}")
    except Exception as e:
        return {"error": True, "message": f"Beyond the Book built but deploy failed: {e}"}

    msg = f"Beyond the Book generated and deployed — {len(deck['cards'])} cards"
    msg += " + big why" if deck.get("big_why") else ""
    if deck.get("left_out_days"):
        msg += f" (left out days {[d['day'] for d in deck['left_out_days']]})"
    if deck.get("skipped_days"):
        msg += f" (skipped days {[d['day'] for d in deck['skipped_days']]})"
    print(f"✅ {msg}")
    return {"error": False, "filename": f"{filename_base}_beyond.html",
            "file_path": str(html_tmp), "deployed": ["beyond"], "message": msg}