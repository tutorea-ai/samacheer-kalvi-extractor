"""Public Past Papers — phase 1: file the DGE PDFs and build catalog.json.

Reads downloaded papers named  {Subject}_Q_paper_{SSLC|HSC2}_{YYYY}.pdf,
copies each one to

    <data-root>/public-past-papers/{exam}/{year}/{session}/{subject}/original.pdf

and rebuilds <data-root>/public-past-papers/catalog.json from everything on disk
(so adding 2025 later keeps 2026).

Fail closed: if any file name, exam or subject is unknown, or a PDF is broken,
nothing is copied and nothing is written.

Usage (from samacheer-pdf-server, with PYTHONPATH=.):

    python3 -m app.content_builder.public_past_papers.catalog \
        --src ~/Downloads/10th_Question_Paper \
        --src ~/Downloads/12th_Question_Paper \
        --data-root <node repo>/backend/data \
        --dry-run            # remove to actually copy and write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pypdf import PdfReader

MODULE = "public_past_papers"
VERSION = 1
FOLDER = "public-past-papers"
CATALOG = "catalog.json"
PDF_NAME = "original.pdf"
IST = timezone(timedelta(hours=5, minutes=30))

SOURCE = {
    "en": "Directorate of Government Examinations, Tamil Nadu",
    "ta": "அரசுத் தேர்வுகள் இயக்ககம், தமிழ்நாடு",
    "url": "https://dge.tn.gov.in",
}

# File-name exam tag -> exam info. Order here is the order in the catalog.
EXAMS = {
    "sslc": {"tags": ("SSLC",), "class": 10,
             "title": {"en": "SSLC (Class 10)", "ta": "பத்தாம் வகுப்பு"}},
    "hsc": {"tags": ("HSC2",), "class": 12,
            "title": {"en": "HSC (Class 12)", "ta": "பன்னிரண்டாம் வகுப்பு"}},
}

# File-name subject (lower-case) -> (slug, titles). Order here is the display order.
# A new subject = one line here; nothing else changes.
SUBJECTS = {
    "sslc": {
        "tamil": ("tamil", {"en": "Tamil", "ta": "தமிழ்"}),
        "english": ("english", {"en": "English", "ta": "ஆங்கிலம்"}),
        "maths": ("maths", {"en": "Maths", "ta": "கணிதம்"}),
        "science": ("science", {"en": "Science", "ta": "அறிவியல்"}),
        "socialscience": ("social-science", {"en": "Social Science", "ta": "சமூக அறிவியல்"}),
    },
    "hsc": {
        # Languages
        "tamil": ("tamil", {"en": "Tamil", "ta": "தமிழ்"}),
        "advancedtamil": ("advanced-tamil", {"en": "Advanced Tamil", "ta": "சிறப்புத் தமிழ்"}),
        "english": ("english", {"en": "English", "ta": "ஆங்கிலம்"}),
        "communicativeenglish": ("communicative-english", {"en": "Communicative English", "ta": "தொடர்பு ஆங்கிலம்"}),
        # Science
        "maths": ("maths", {"en": "Maths", "ta": "கணிதம்"}),
        "physics": ("physics", {"en": "Physics", "ta": "இயற்பியல்"}),
        "chemistry": ("chemistry", {"en": "Chemistry", "ta": "வேதியியல்"}),
        "biology": ("biology", {"en": "Biology", "ta": "உயிரியல்"}),
        "botany": ("botany", {"en": "Botany", "ta": "தாவரவியல்"}),
        "zoology": ("zoology", {"en": "Zoology", "ta": "விலங்கியல்"}),
        "biochemistry": ("biochemistry", {"en": "Biochemistry", "ta": "உயிர் வேதியியல்"}),
        "microbiology": ("microbiology", {"en": "Microbiology", "ta": "நுண்ணுயிரியல்"}),
        "computerscience": ("computer-science", {"en": "Computer Science", "ta": "கணினி அறிவியல்"}),
        # Commerce
        "accountancy": ("accountancy", {"en": "Accountancy", "ta": "கணக்குப்பதிவியல்"}),
        "commerce": ("commerce", {"en": "Commerce", "ta": "வணிகவியல்"}),
        "economics": ("economics", {"en": "Economics", "ta": "பொருளியல்"}),
        "businessmathsandstatistics": ("business-maths-and-statistics",
                                       {"en": "Business Maths and Statistics", "ta": "வணிகக் கணிதம் மற்றும் புள்ளியியல்"}),
        "statistics": ("statistics", {"en": "Statistics", "ta": "புள்ளியியல்"}),
        "computerapplications": ("computer-applications", {"en": "Computer Applications", "ta": "கணினிப் பயன்பாடுகள்"}),
        # Arts
        "history": ("history", {"en": "History", "ta": "வரலாறு"}),
        "geography": ("geography", {"en": "Geography", "ta": "புவியியல்"}),
        "politicalscience": ("political-science", {"en": "Political Science", "ta": "அரசியல் அறிவியல்"}),
        "ethicsandindianculture": ("ethics-and-indian-culture",
                                   {"en": "Ethics and Indian Culture", "ta": "அறவியலும் இந்தியப் பண்பாடும்"}),
        # Vocational
        "homescience": ("home-science", {"en": "Home Science", "ta": "மனையியல்"}),
        "nutritionanddietetics": ("nutrition-and-dietetics",
                                  {"en": "Nutrition and Dietetics", "ta": "ஊட்டச்சத்து மற்றும் உணவுமுறையியல்"}),
        "generalnursing": ("general-nursing", {"en": "General Nursing", "ta": "பொது செவிலியம்"}),
    },
}

# Optional subject groups per exam, in display order: (id, titles, member slugs in order).
# An exam with groups must place every one of its subjects in exactly one group
# (checked at import, before anything runs). An exam without groups stays flat.
GROUPS = {
    "hsc": [
        ("languages", {"en": "Languages", "ta": "மொழிகள்"},
         ["tamil", "advanced-tamil", "english", "communicative-english"]),
        ("science", {"en": "Science", "ta": "அறிவியல்"},
         ["maths", "physics", "chemistry", "biology", "botany", "zoology",
          "biochemistry", "microbiology", "computer-science"]),
        ("commerce", {"en": "Commerce", "ta": "வணிகவியல்"},
         ["accountancy", "commerce", "economics", "business-maths-and-statistics",
          "statistics", "computer-applications"]),
        ("arts", {"en": "Arts", "ta": "கலை"},
         ["history", "geography", "political-science", "ethics-and-indian-culture"]),
        ("vocational", {"en": "Vocational", "ta": "தொழிற்கல்வி"},
         ["home-science", "nutrition-and-dietetics", "general-nursing"]),
    ],
}


def _check_groups() -> None:
    for exam, groups in GROUPS.items():
        slugs = [slug for slug, _ in SUBJECTS[exam].values()]
        placed = [s for _, _, members in groups for s in members]
        unknown = sorted(set(placed) - set(slugs))
        twice = sorted({s for s in placed if placed.count(s) > 1})
        missing = [s for s in slugs if s not in placed]
        if unknown or twice or missing:
            raise RuntimeError(f"GROUPS['{exam}'] is wrong: unknown {unknown}, "
                               f"in two groups {twice}, in no group {missing}")


_check_groups()

SESSIONS = ("march",)  # supplementary later: add "supplementary" here
FILE_MODE = 0o644  # readable by a Node process running as another user
FILE_RE = re.compile(r"^(?P<subject>[A-Za-z]+)_Q_paper_(?P<tag>[A-Za-z0-9]+)_(?P<year>\d{4})\.pdf$")


class CatalogError(Exception):
    pass


def _exam_for_tag(tag: str) -> str:
    for exam, info in EXAMS.items():
        if tag.upper() in info["tags"]:
            return exam
    raise CatalogError(f"unknown exam tag '{tag}' (known: "
                       f"{', '.join(t for i in EXAMS.values() for t in i['tags'])})")


def _pdf_pages(path: Path) -> int:
    with open(path, "rb") as fh:
        if fh.read(5) != b"%PDF-":
            raise CatalogError(f"{path.name}: not a PDF")
    try:
        pages = len(PdfReader(str(path)).pages)
    except Exception as exc:  # noqa: BLE001 — any parse failure means a broken file
        raise CatalogError(f"{path.name}: unreadable PDF ({exc})") from exc
    if pages < 1:
        raise CatalogError(f"{path.name}: PDF has no pages")
    return pages


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def plan_sources(src_dirs: list[Path], session: str) -> list[dict]:
    """Map every PDF in the source folders to its target. Raises on any problem."""
    if session not in SESSIONS:
        raise CatalogError(f"unknown session '{session}' (known: {', '.join(SESSIONS)})")
    plan, problems, seen = [], [], {}
    for src in src_dirs:
        if not src.is_dir():
            raise CatalogError(f"source folder not found: {src}")
        for path in sorted(src.iterdir()):
            if path.is_dir() or path.name.startswith("."):
                continue
            m = FILE_RE.match(path.name)
            if not m:
                problems.append(f"{path.name}: name does not match "
                                f"<Subject>_Q_paper_<SSLC|HSC2>_<YYYY>.pdf")
                continue
            try:
                exam = _exam_for_tag(m["tag"])
                key = m["subject"].lower()
                if key not in SUBJECTS[exam]:
                    raise CatalogError(f"unknown {exam} subject '{m['subject']}' "
                                       f"(add it to SUBJECTS['{exam}'])")
                slug = SUBJECTS[exam][key][0]
                year = int(m["year"])
                pages = _pdf_pages(path)
            except CatalogError as exc:
                problems.append(f"{path.name}: {exc}" if path.name not in str(exc) else str(exc))
                continue
            rel = f"{exam}/{year}/{session}/{slug}/{PDF_NAME}"
            if rel in seen:
                problems.append(f"{path.name}: same target as {seen[rel]} ({rel})")
                continue
            seen[rel] = path.name
            plan.append({"src": path, "rel": rel, "pages": pages})
    if problems:
        raise CatalogError("fix these first, nothing was copied:\n  - " + "\n  - ".join(problems))
    if not plan:
        raise CatalogError("no PDFs found in the source folders")
    return plan


def build_catalog(root: Path) -> dict:
    """Build the catalog from every original.pdf on disk under root/public-past-papers."""
    base = root / FOLDER
    exams = []
    for exam, info in EXAMS.items():
        titles = {slug: t for slug, t in SUBJECTS[exam].values()}
        groups = GROUPS.get(exam, [])
        group_of = {s: gid for gid, _, members in groups for s in members}
        if groups:  # display order: group order, then member order within the group
            order = {s: i for i, s in enumerate(s for _, _, members in groups for s in members)}
        else:
            order = {slug: i for i, (slug, _) in enumerate(SUBJECTS[exam].values())}
        papers = []
        for pdf in sorted((base / exam).glob(f"*/*/*/{PDF_NAME}")):
            year_s, session, slug = pdf.parts[-4], pdf.parts[-3], pdf.parts[-2]
            if not year_s.isdigit() or session not in SESSIONS or slug not in titles:
                raise CatalogError(f"unexpected folder on disk: {pdf.relative_to(base)}")
            paper = {
                "year": int(year_s),
                "session": session,
                "subject": slug,
                "subject_title": titles[slug],
                "pdf": pdf.relative_to(base).as_posix(),
                "pages": _pdf_pages(pdf),
                "size_kb": round(pdf.stat().st_size / 1024),
            }
            if groups:
                paper["group"] = group_of[slug]
            papers.append(paper)
        papers.sort(key=lambda p: (-p["year"], SESSIONS.index(p["session"]), order[p["subject"]]))
        entry = {"exam": exam, "class": info["class"], "title": info["title"]}
        if groups:
            entry["groups"] = [{"id": gid, "title": t} for gid, t, _ in groups]
        entry["papers"] = papers
        exams.append(entry)
    return {
        "module": MODULE,
        "version": VERSION,
        "generated_at": datetime.now(IST).isoformat(timespec="seconds"),
        "source": SOURCE,
        "exams": exams,
    }


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, FILE_MODE)  # mkstemp creates 0600; set before the rename so the file is never 0600
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def run(src_dirs: list[Path], data_root: Path, session: str = "march", dry_run: bool = True) -> dict:
    if not data_root.is_dir():
        raise CatalogError(f"data root not found: {data_root}")
    plan = plan_sources(src_dirs, session)
    base = data_root / FOLDER
    copied = unchanged = 0
    for item in plan:
        target = base / item["rel"]
        same = target.exists() and _sha256(target) == _sha256(item["src"])
        action = "same" if same else ("update" if target.exists() else "new")
        print(f"  {action:6} {item['src'].name:42} -> {FOLDER}/{item['rel']}  ({item['pages']} pages)")
        if same:
            unchanged += 1
            if not dry_run:
                os.chmod(target, FILE_MODE)  # repairs PDFs written as 0600 by earlier runs
        elif not dry_run:
            _write_atomic(target, item["src"].read_bytes())
            copied += 1
    if dry_run:
        print(f"\nDRY RUN: {len(plan)} papers planned, nothing copied or written.")
        return {}
    catalog = build_catalog(data_root)
    _write_atomic(base / CATALOG,
                  (json.dumps(catalog, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    total = sum(len(e["papers"]) for e in catalog["exams"])
    per_exam = ", ".join("%s: %d" % (e["exam"], len(e["papers"])) for e in catalog["exams"])
    print(f"\n✅ {copied} copied, {unchanged} unchanged; catalog.json lists {total} papers ({per_exam})")
    print(f"🚀 Public Past Papers SUCCESS: {base}")
    return catalog


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", action="append", required=True, type=Path,
                    help="folder of downloaded PDFs (repeat for more folders)")
    ap.add_argument("--data-root", required=True, type=Path,
                    help="Node backend/data folder (public-past-papers/ is created inside it)")
    ap.add_argument("--session", default="march", choices=SESSIONS)
    ap.add_argument("--dry-run", action="store_true", help="show the plan, copy and write nothing")
    args = ap.parse_args(argv)
    try:
        run([p.expanduser() for p in args.src], args.data_root.expanduser(), args.session, args.dry_run)
    except CatalogError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())