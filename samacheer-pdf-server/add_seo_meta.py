#!/usr/bin/env python3
"""
Add SEO meta tags to every HTML page of the curriculum site, and build
sitemap.xml + robots.txt.

Usage (run from anywhere):
  python add_seo_meta.py /path/to/project-root --base-url https://example.com --dry-run
  python add_seo_meta.py /path/to/project-root --base-url https://example.com --backup

Safe to re-run: it replaces its own block (between the SEO markers) each time.
"""
import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

START, END = "<!-- seo:start -->", "<!-- seo:end -->"
KINDS = {
    "content": "Lesson",
    "lp": "Lesson Plan",
    "qa": "Questions and Answers",
    "flashcards": "Flashcards",
}
SUFFIX_RE = re.compile(
    r"(maths(\d+)?(_t\d)?|botany|zoology|biology|physics|chemistry|history|"
    r"geography|civics|economics|computer_science|prose|poem|play|drama|"
    r"supplementary|grammar|thirukural|t\du\d)$"
)
TERM_RE = re.compile(r"^term(\d)$")

# Language subjects with their own SEO labels. A language not listed here keeps
# the English behaviour. Add a language = add one entry.
LANG_META = {
    "tamil": {
        "subject": "தமிழ்", "subject_en": "Tamil", "locale": "ta_IN",
        "class": "வகுப்பு", "term": "பருவம்",
        "kinds": {"content": "பாடம்", "lp": "பாடக்குறிப்பு", "qa": "வினா – விடை",
                  "flashcards": "நினைவு அட்டைகள்", "cheatsheet": "சுருக்கக் குறிப்பு"},
        "desc": {
            "content":    "{ch} — {where} பாடம்: பாடப்பகுதி, விளக்கங்கள், பயிற்சிகள். தமிழ்நாடு அரசு பாடநூல் (சமச்சீர் கல்வி).",
            "lp":         "{ch} — {where} பாடக்குறிப்பு: கற்றல் நோக்கங்கள், பாடவேளை வாரியான கற்பித்தல், செயல்பாடுகள், மதிப்பீடு. சமச்சீர் கல்வி.",
            "qa":         "{ch} — {where} வினா – விடை: பாடநூல் வினாக்களுக்கான விடைகள், விளக்கங்களுடன். சமச்சீர் கல்வி.",
            "flashcards": "{ch} — {where} நினைவு அட்டைகள்: விரைவான மீள்பார்வைக்கு. சமச்சீர் கல்வி.",
            "cheatsheet": "{ch} — {where} சுருக்கக் குறிப்பு: ஒரு பக்க மீள்பார்வை. சமச்சீர் கல்வி.",
        },
    },
}


def load_language_titles(root: Path) -> dict:
    """{(language, lesson_id): printed title} from curriculum/languages/*.json."""
    titles = {}
    for f in (root / "curriculum" / "languages").glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue

        def walk(node):
            if isinstance(node, dict):
                if "id" in node and "title" in node:
                    titles[(f.stem, node["id"])] = node["title"]
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(data)
    return titles


def prettify(slug: str) -> str:
    prev = None
    while prev != slug:  # strip stacked suffixes e.g. *_botany_botany
        prev, slug = slug, SUFFIX_RE.sub("", slug)
    return slug.replace("_", " ").replace("-", " ").strip().title()


def parse(path: Path, root: Path):
    """Return dict of info derived from the folder structure, or None."""
    parts = path.relative_to(root).parts
    idx = next((i for i, p in enumerate(parts) if p in KINDS), None)
    if idx is None or idx < 2:
        return None
    kind = parts[idx]
    before, after = parts[:idx], list(parts[idx + 1:])
    if len(after) < 2:
        return None
    filename = after.pop()
    if after and after[-1] == "cheatsheet":
        after.pop()
        kind_label = "Cheat Sheet"
    else:
        kind_label = KINDS[kind]
    if not after:
        return None
    chapter_slug = after[-1]
    term = after[0] if TERM_RE.match(after[0]) else None
    sub = [p for p in after[1:-1]]
    cls = before[-1]
    if not cls.isdigit():
        return None
    subject_raw = before[-2]
    is_lang = "languages" in before
    lang = subject_raw.lower() if is_lang else ""
    if is_lang:
        subject = LANG_META.get(lang, {}).get("subject_en") or subject_raw.title()
    else:
        subject = prettify(subject_raw.replace("-", "_"))
    # science/social-science have a sub-subject folder (physics, history ...)
    sub_subject = prettify(sub[-1]) if sub else ""
    if subject_raw == "pure-science":
        subject = "Pure Science"
    t = TERM_RE.match(term) if term else None
    term_label = f"Term {t.group(1)}" if t and t.group(1) != "0" else ""
    return dict(
        cls=cls, subject=subject, sub_subject=sub_subject, term=term_label,
        kind=kind, kind_label=kind_label, chapter=prettify(chapter_slug),
        filename=filename, is_lang=is_lang, lang=lang, slug=chapter_slug,
    )


def page_number(filename: str):
    m = re.fullmatch(r"p(\d+)\.html", filename)
    return int(m.group(1)) if m else None


def build_meta(info, url, site_name, author):
    lm = LANG_META.get(info.get("lang", ""))
    if lm:
        return build_lang_meta(info, url, site_name, author, lm)
    ch, cls = info["chapter"], info["cls"]
    area = info["sub_subject"] or info["subject"]
    pn = page_number(info["filename"])
    title_bits = [ch, info["kind_label"], f"Class {cls} {area}"]
    if info["sub_subject"] and info["sub_subject"] != info["subject"]:
        title_bits[2] = f"Class {cls} {info['subject']} {info['sub_subject']}"
    title = " | ".join(title_bits) + f" | {site_name}"
    if pn:
        title = f"{ch} (Page {pn}) | Class {cls} {area} | {site_name}"

    where = f"Class {cls} {info['subject']}"
    if info["sub_subject"] and info["sub_subject"] != info["subject"]:
        where += f" ({info['sub_subject']})"
    if info["term"]:
        where += f", {info['term']}"
    desc = {
        "content": f"{ch}: complete {where} lesson notes with explanations, "
                   f"key points, examples and exercises. Tamil Nadu State Board (Samacheer Kalvi) English medium.",
        "lp": f"{ch}: ready-to-use lesson plan for {where} with objectives, "
              f"teaching steps, activities and assessment. Tamil Nadu State Board (Samacheer Kalvi).",
        "qa": f"{ch}: book-back questions with answers and explanations for {where}. "
              f"Practice and revise for Tamil Nadu State Board (Samacheer Kalvi) exams.",
        "flashcards": f"{ch}: revision flashcards for {where}. Quick recall practice "
                      f"for Tamil Nadu State Board (Samacheer Kalvi).",
    }[info["kind"]]
    if info["kind_label"] == "Cheat Sheet":
        desc = f"{ch}: one-page cheat sheet and quick revision summary for {where}."
    desc = desc[:300]

    kw = [ch, f"Class {cls}", info["subject"], info["sub_subject"], info["term"],
          info["kind_label"], "Samacheer Kalvi", "Tamil Nadu State Board",
          f"{cls}th standard", "notes", "book back answers"]
    keywords = ", ".join(dict.fromkeys(k for k in kw if k))

    robots = "noindex, follow" if pn else "index, follow, max-snippet:-1, max-image-preview:large"
    return title, _meta_block(title, desc, keywords, robots, url, site_name, author), robots.startswith("index")


def build_lang_meta(info, url, site_name, author, lm):
    """Meta for a language subject with its own labels (e.g. Tamil)."""
    ch, cls = info["chapter"], info["cls"]
    kind_key = "cheatsheet" if info["kind_label"] == "Cheat Sheet" else info["kind"]
    kind = lm["kinds"].get(kind_key, info["kind_label"])
    where = f'{lm["class"]} {cls} {lm["subject"]}'
    if info["term"]:
        where += f', {lm["term"]} {info["term"].split()[-1]}'
    pn = page_number(info["filename"])
    title = f"{ch} ({pn}) | {where} | {site_name}" if pn else f"{ch} | {kind} | {where} | {site_name}"
    desc = lm["desc"].get(kind_key, lm["desc"]["content"]).format(ch=ch, where=where)[:300]
    kw = [ch, prettify(info["slug"]), kind, where,
          f'Class {cls} {lm["subject_en"]}', f'{cls}th standard {lm["subject_en"]}',
          "சமச்சீர் கல்வி", "Samacheer Kalvi", "Tamil Nadu State Board"]
    keywords = ", ".join(dict.fromkeys(k for k in kw if k))
    robots = "noindex, follow" if pn else "index, follow, max-snippet:-1, max-image-preview:large"
    block = _meta_block(title, desc, keywords, robots, url, site_name, author, locale=lm.get("locale"))
    return title, block, robots.startswith("index")


def _meta_block(title, desc, keywords, robots, url, site_name, author, locale=None):
    e = html.escape
    lines = [
        START,
        f'<meta name="description" content="{e(desc, quote=True)}">',
        f'<meta name="keywords" content="{e(keywords, quote=True)}">',
        f'<meta name="author" content="{e(author, quote=True)}">',
        f'<meta name="robots" content="{robots}">',
    ]
    if url:
        lines.append(f'<link rel="canonical" href="{e(url, quote=True)}">')
    lines += [
        f'<meta property="og:type" content="article">',
        *([f'<meta property="og:locale" content="{locale}">'] if locale else []),
        f'<meta property="og:site_name" content="{e(site_name, quote=True)}">',
        f'<meta property="og:title" content="{e(title, quote=True)}">',
        f'<meta property="og:description" content="{e(desc, quote=True)}">',
    ]
    if url:
        lines.append(f'<meta property="og:url" content="{e(url, quote=True)}">')
    lines += [
        '<meta name="twitter:card" content="summary">',
        f'<meta name="twitter:title" content="{e(title, quote=True)}">',
        f'<meta name="twitter:description" content="{e(desc, quote=True)}">',
        END,
    ]
    return "\n  ".join(lines)


REMOVE_RES = [
    re.compile(r"\s*" + re.escape(START) + r".*?" + re.escape(END), re.S),
    re.compile(r'\s*<meta\s+name=["\'](description|keywords|author|robots)["\'][^>]*>', re.I),
    re.compile(r'\s*<link\s+rel=["\']canonical["\'][^>]*>', re.I),
]


def process(path: Path, info, url, args):
    text = path.read_text(encoding="utf-8")
    if not re.search(r"<head[^>]*>", text, re.I):
        return None, False
    title, block, indexable = build_meta(info, url, args.site_name, args.author)
    new = text
    for r in REMOVE_RES:
        new = r.sub("", new)
    # <title>
    if re.search(r"<title>.*?</title>", new, re.I | re.S):
        new = re.sub(r"<title>.*?</title>", lambda m: f"<title>{html.escape(title)}</title>",
                     new, count=1, flags=re.I | re.S)
        extra = ""
    else:
        extra = f"\n  <title>{html.escape(title)}</title>"
    if not re.search(r'<meta\s+name=["\']viewport["\']', new, re.I):
        extra += '\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">'
    insert = extra + "\n  " + block
    m = re.search(r"<meta\s+charset[^>]*>", new, re.I)
    if m:
        new = new[:m.end()] + insert + new[m.end():]
    else:
        m = re.search(r"<head[^>]*>", new, re.I)
        new = new[:m.end()] + '\n  <meta charset="UTF-8">' + insert + new[m.end():]
    if new != text and not args.dry_run:
        if args.backup:
            path.with_suffix(path.suffix + ".seo.bak").write_text(text, encoding="utf-8")
        path.write_text(new, encoding="utf-8")
    return indexable, new != text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path, help="project root (contains subjects/ and languages/)")
    ap.add_argument("--base-url", default="", help="e.g. https://www.yoursite.com (no trailing slash)")
    ap.add_argument("--site-name", default="Samacheer Study Hub")
    ap.add_argument("--author", default="Your Name")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backup", action="store_true")
    ap.add_argument("--web-root", type=Path, default=None,
                    help="folder that maps to the site's URL root (default: project root)")
    args = ap.parse_args()

    root = args.root.resolve()
    web_root = (args.web_root or root).resolve()
    base = args.base_url.rstrip("/")
    changed = skipped = 0
    sitemap = []
    lang_titles = load_language_titles(root)
    for path in sorted(root.rglob("*.html")):
        info = parse(path, root)
        if not info:
            skipped += 1
            continue
        if info["is_lang"]:
            info["chapter"] = lang_titles.get((info["lang"], info["slug"]), info["chapter"])
        rel = path.relative_to(web_root).as_posix()
        url = ""
        if base:
            url = f"{base}/{rel[:-10] if rel.endswith('index.html') else rel}"
        indexable, did = process(path, info, url, args)
        if indexable is None:
            skipped += 1
            continue
        changed += did
        if indexable and url:
            lm = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")
            sitemap.append((url, lm))

    print(f"updated: {changed}, skipped (not a lesson page): {skipped}, sitemap urls: {len(sitemap)}")
    if base and not args.dry_run:
        rows = "\n".join(
            f"  <url><loc>{html.escape(u)}</loc><lastmod>{lm}</lastmod></url>" for u, lm in sitemap)
        (web_root / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "\n</urlset>\n",
            encoding="utf-8")
        (web_root / "robots.txt").write_text(
            f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
        print("wrote sitemap.xml and robots.txt")
    if len(sitemap) > 50000:
        print("WARNING: sitemap exceeds 50,000 URLs; split it.", file=sys.stderr)


if __name__ == "__main__":
    main()
