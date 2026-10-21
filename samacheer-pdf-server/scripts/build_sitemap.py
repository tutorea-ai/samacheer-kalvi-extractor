#!/usr/bin/env python3
"""
scripts/build_sitemap.py
------------------------
Build the public sitemap of content.tutorea.online from the Node curriculum JSONs.

Rules (agreed with Node team + TL):
  URL      = {HOST}/lesson/{subject}/{class}/{type}/{name}
             subject = curriculum file name (tamil, social-science, pure-science, ...)
             type    = the lesson's "type" field
             name    = the lesson id minus a trailing "_{type}", if it has one
  Listed   = only lessons whose Content index.html is on disk
  lastmod  = newest of the lesson's content / qa / lp files
  Output   = frontend/sitemap.xml (served live, no restart); home page always kept
  --split  = sitemap.xml becomes an index → sitemap-home.xml + sitemap-{subject}.xml
  --check  = fetch every URL from a local Node server; report pages with the generic title

Run after every generation batch:
  python3 scripts/build_sitemap.py --node-root ~/test_m1_and_m2/content-qa-lp/samacheer-kalvi
"""
import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

HOST = "https://content.tutorea.online"
GENERIC_TITLE = "Samacheer Learning Resources"
XMLNS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def lesson_name(lesson_id: str, ltype: str) -> str:
    suffix = f"_{ltype}"
    return lesson_id[: -len(suffix)] if ltype and lesson_id.endswith(suffix) else lesson_id


def iter_lessons(node):
    """Yield every dict with an 'id' and a 'type', at any depth."""
    if isinstance(node, dict):
        if isinstance(node.get("id"), str) and isinstance(node.get("type"), str):
            yield node
            return
        for v in node.values():
            yield from iter_lessons(v)
    elif isinstance(node, list):
        for v in node:
            yield from iter_lessons(v)


def find_content(base: Path, cls: str, term: str, lesson_id: str):
    term_dir = base / cls / "content" / term
    if not term_dir.is_dir():
        return None
    # "**" covers subjects with a discipline folder (science, social-science, biology)
    return next(iter(term_dir.glob(f"**/{lesson_id}/index.html")), None)


def lastmod(base: Path, content_file: Path) -> str:
    rel = content_file.relative_to(base).parts          # (cls, "content", term, ..., id, index.html)
    files = [base / rel[0] / kind / Path(*rel[2:]) for kind in ("content", "qa", "lp")]
    newest = max(f.stat().st_mtime for f in files if f.exists())
    return datetime.fromtimestamp(newest, timezone.utc).strftime("%Y-%m-%d")


def collect(node_root: Path) -> dict:
    """{subject: {url: lastmod}} for every lesson whose Content page is on disk."""
    data_dir = node_root / "backend" / "data"
    curr_dir = data_dir / "curriculum"
    out = {}
    for cfile in sorted(curr_dir.rglob("*.json")):
        subject = cfile.stem
        base = data_dir / cfile.parent.relative_to(curr_dir) / subject
        try:
            data = json.loads(cfile.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  {cfile}: {e}")
            continue
        urls = out.setdefault(subject, {})
        for cls in (k for k in data if k.isdigit()):
            for term, term_val in data[cls].items():
                for lesson in iter_lessons(term_val):
                    found = find_content(base, cls, term, lesson["id"])
                    if not found:
                        continue
                    url = f"{HOST}/lesson/{subject}/{cls}/{lesson['type']}/{lesson_name(lesson['id'], lesson['type'])}"
                    lm = lastmod(base, found)
                    urls[url] = max(lm, urls.get(url, ""))   # same URL in two terms → keep newest
    return out


def urlset(entries) -> str:
    rows = "\n".join(f"  <url><loc>{escape(u)}</loc><lastmod>{lm}</lastmod></url>" for u, lm in entries)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="{XMLNS}">\n{rows}\n</urlset>\n'


def sitemap_index(entries) -> str:
    rows = "\n".join(f"  <sitemap><loc>{escape(u)}</loc><lastmod>{lm}</lastmod></sitemap>" for u, lm in entries)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="{XMLNS}">\n{rows}\n</sitemapindex>\n'


def write_atomic(path: Path, text: str):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)                                    # served live — never half-written


def check(urls, local: str) -> int:
    bad = 0
    for u in urls:
        path = u[len(HOST):] or "/"
        try:
            html = urllib.request.urlopen(local.rstrip("/") + path, timeout=20).read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"ERROR   {path} ({e})"); bad += 1; continue
        m = re.search(r"<title>([^<]*)</title>", html, re.I)
        if not m or GENERIC_TITLE in m.group(1):
            print(f"GENERIC {path}"); bad += 1
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node-root", type=Path, required=True, help="Node repo root (contains backend/ and frontend/)")
    ap.add_argument("--split", action="store_true", help="sitemap index + one file per subject")
    ap.add_argument("--dry-run", action="store_true", help="print counts, write nothing")
    ap.add_argument("--check", metavar="LOCAL_URL", help="e.g. http://localhost:3001 — report generic pages")
    args = ap.parse_args()

    node_root = args.node_root.expanduser().resolve()
    front = node_root / "frontend"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    by_subject = collect(node_root)

    total = 0
    for subject, urls in by_subject.items():
        total += len(urls)
        example = next(iter(urls), "—")
        print(f"{subject:16} {len(urls):5} lessons | e.g. {example}")
    print(f"{'TOTAL':16} {total:5} lessons (+ home page)")

    home = [(f"{HOST}/", today)]
    if not args.dry_run:
        if args.split:
            index = []
            write_atomic(front / "sitemap-home.xml", urlset(home))
            index.append((f"{HOST}/sitemap-home.xml", today))
            for subject, urls in by_subject.items():
                if not urls:
                    continue
                entries = sorted(urls.items())
                write_atomic(front / f"sitemap-{subject}.xml", urlset(entries))
                index.append((f"{HOST}/sitemap-{subject}.xml", max(lm for _, lm in entries)))
            write_atomic(front / "sitemap.xml", sitemap_index(index))
            print(f"✅ wrote sitemap index + {len(index)} files in {front}")
        else:
            entries = home + sorted(u for s in by_subject.values() for u in s.items())
            write_atomic(front / "sitemap.xml", urlset(entries))
            print(f"✅ wrote {front / 'sitemap.xml'} ({len(entries)} URLs)")

    if args.check:
        all_urls = [u for s in by_subject.values() for u in s]
        bad = check(all_urls, args.check)
        print(f"check: {len(all_urls) - bad}/{len(all_urls)} OK")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()