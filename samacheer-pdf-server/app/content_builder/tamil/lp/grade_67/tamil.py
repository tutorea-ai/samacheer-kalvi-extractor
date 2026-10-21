"""
tamil.py (LP)
-------------
LP Builder for Samacheer Kalvi Tamil — Class 6 (grade_67)

v0.2 — Oct 2026  (first real run review: next-period line built in Python;
                  நூல்வெளி only in the last period; no mythology in meanings;
                  poetic features from the book's own definition)

TEMPLATE: Manual LP "Class 6 Tamil · Term 1 · Unit 1 தமிழ்த்தேன்" (26 periods),
used as a content-agnostic teaching template for every Class 6 lesson
(see tamil/base/day_structures.py), plus the TL decisions of 20 Oct 2026
(see tamil/base/__init__.py).

ONE SHARED BUILDER for all five lesson types; it branches on
metadata["lesson_type"]. A type-specific file (e.g. thirukural.py) dropped
next to this one overrides that type without touching this file.

CALL STRUCTURE (N = periods, decided per lesson by type):
  Python   → normalise the read-aloud text, cut the unit-end sections
  Call 0   → Lesson Extractor (JSON: sections / stanzas / kurals, word wall,
             key content, நூல்வெளி facts, objectives, materials)
  Python   → period plan (fixed 4 for poem / supplementary / thirukural;
             from sections for prose / grammar) and the WHOLE preamble
             (every table built from extractor data — no model HTML)
  Calls    → Period 1 .. N (one call each; last period carries homework)
  Call     → Assessment (top-level <div class="assessment-block">)

COST: one fixed system prompt + one cached lesson-text block are shared by
every period and the assessment call (prompt caching), so each period pays
only for its own short brief.

WEB CONTRACT: as Physics — each period exactly <div class="lp-day-block">,
title inside; one top-level assessment-block after the last period;
enforced in Python and re-checked on the assembled output.

BACKEND CONTRACT:
  - generate(text, metadata) -> str | None ; never raises
  - streaming for every call; builder retries mid-stream drops (10/30/60 s)
  - no per-run state on self (the singleton serves parallel requests)
  - failed period → visible placeholder with <!-- LP_DAY_FAILED -->
  - return None if: extractor unusable, assessment fails, more than
    MAX_FAILED_DAYS periods fail, or the final contract check fails
"""

import difflib
import html as html_lib
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import anthropic
import httpx                    # installed with the anthropic SDK

from .....config import settings
from ...base import (
    LABELS,
    PREAMBLE_TITLES,
    ASSESSMENT_TITLES,
    LESSON_TYPE_NAMES,
    PERIOD_MINUTES,
    TAMIL_LP_SYSTEM_PROMPT,
    BOOK_LINES_INSTRUCTION,
    CFU_INSTRUCTION,
    CCQ_GRAMMAR_INSTRUCTION,
    EXIT_SLIP_INSTRUCTION,
    HOMEWORK_INSTRUCTION,
    lp_source_text,
    normalize_lesson_type,
    normalize_tamil,
    get_display_title,
    get_meta_line,
    static_language_tables_html,
    clean,
    normalize_day_html,
    normalize_assessment_html,
    normalize_preamble_html,
    check_day_structure,
    check_book_lines,
    is_critical,
    count_day_blocks,
    count_assessment_blocks,
    failed_day_block,
    mark_truncated,
    parse_json_response,
    _matching_close_index,
)
from ...base.day_structures import (
    TAMIL_PERIOD_TIMING,
    TAMIL_STRUCTURE_META,
    KEY_CONTENT_TABLES,
    WORD_WALL_COLUMNS,
    assessment_items,
    get_pattern,
    get_period_strategy,
    split_evenly,
)

L = LABELS


# ============================================================================
# TUNABLES
# ============================================================================

MAX_TOKENS_EXTRACTOR  = 16000
MAX_TOKENS_PERIOD     = 12000   # Tamil is token-heavy; set from the first real run's out=
MAX_TOKENS_ASSESSMENT = 12000

MAX_FAILED_DAYS = 1             # backend rule: >1 failed period → return None

REQUEST_TIMEOUT_S = 900.0
SDK_MAX_RETRIES   = 3                    # failures BEFORE a stream starts
STREAM_RETRY_BACKOFF_S = (10, 30, 60)    # drops DURING a stream

MAX_WORD_WALL_ROWS = 16
MAX_KEY_ROWS       = 24
SNAP_MIN_RATIO     = 0.80       # extractor line -> nearest source line


# ============================================================================
# TAMIL LP BUILDER
# ============================================================================

class TamilLP67Builder:

    discipline = "tamil"

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            max_retries=SDK_MAX_RETRIES,
            timeout=REQUEST_TIMEOUT_S,
        )
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Tamil LP Builder (67) v0.2 initialized — model: {self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """Never raises. Returns LP body HTML, or None on failure."""
        try:
            return self._generate(text, metadata or {})
        except Exception as e:
            print(f"❌ [Tamil LP] Unexpected error — returning None: {type(e).__name__}: {e}")
            return None

    # ------------------------------------------------------------------
    # Orchestration (all per-run state lives in the local `run` dict)
    # ------------------------------------------------------------------

    def _generate(self, text: str, metadata: dict) -> Optional[str]:
        t0 = time.time()
        if not text or not text.strip():
            print("❌ [Tamil LP] Empty lesson text — aborting")
            return None

        lp_text, info = lp_source_text(text)
        ltype = normalize_lesson_type(metadata.get("lesson_type"))
        run: Dict[str, Any] = {
            "text": lp_text,
            "info": info,
            "lesson_type": ltype,
            "title": get_display_title(metadata),
            "meta_line": get_meta_line(metadata),
            "class_num": metadata.get("class", 6),
            "unit": metadata.get("unit", ""),
            "source_lines": [l.strip() for l in lp_text.split("\n") if l.strip()],
            "memorise": info["report"]["memorise_blocks"],
        }
        rep = info["report"]
        print(f"      [Tamil LP] Generating: {run['meta_line']} — {run['title']} "
              f"({info['chars_in']} chars in, {info['chars_lp']} for LP, "
              f"{info['chars_unit_end_dropped']} unit-end dropped)")
        print(f"         · text: symbols {rep['symbols_number'] + rep['symbols_chain']} restored, "
              f"{len(rep['symbol_ambiguous'])} ambiguous left, "
              f"{len(run['memorise'])} memorisation unit(s), exercises={'yes' if info['has_exercises'] else 'NO'}")

        # ── Call 0 — Lesson Extractor ────────────────────────────────
        print("      [Tamil LP] Call 0: Lesson Extractor...")
        data = self._call_extractor(run)
        if not data:
            print("         ❌ Lesson Extractor failed — aborting")
            return None
        run["data"] = data

        # ── Period plan (Python) ─────────────────────────────────────
        run["periods"] = self._plan_periods(run)
        total = len(run["periods"])
        run["total"] = total
        print(f"         ✅ {total} periods ({ltype})")
        for p in run["periods"]:
            print(f"            {L['period']} {p['num']}: {p['title']}")

        parts: List[str] = [self._build_preamble(run)]

        # ── Periods ──────────────────────────────────────────────────
        failed = 0
        for p in run["periods"]:
            print(f"      [Tamil LP] {L['period']} {p['num']}/{total}: {p['title']}...")
            html = self._generate_period(run, p)
            if html is None:
                failed += 1
                print(f"         ❌ Period {p['num']} failed ({failed} so far)")
                if failed > MAX_FAILED_DAYS:
                    print(f"         ❌ More than {MAX_FAILED_DAYS} failed period(s) — aborting")
                    return None
                html = failed_day_block(p["num"], total, p["title"])
            parts.append(html)

        # ── Assessment ───────────────────────────────────────────────
        print("      [Tamil LP] Assessment...")
        assessment = self._call_assessment(run)
        if not assessment:
            print("         ❌ Assessment failed — aborting")
            return None
        parts.append(assessment)

        combined = "\n\n".join(parts)
        n_days, n_assess = count_day_blocks(combined), count_assessment_blocks(combined)
        if n_days != total or n_assess != 1:
            print(f"         ❌ Contract check failed: {n_days} period blocks (expected {total}), "
                  f"{n_assess} assessment blocks (expected 1)")
            return None

        mins = (time.time() - t0) / 60
        print(f"      [Tamil LP] ✅ Complete — {total} periods, {failed} failed, "
              f"{len(combined)} chars, {mins:.1f} min")
        return combined

    # ==================================================================
    # API CALLS — streaming, cached system + lesson text, mid-stream retries
    # ==================================================================

    def _lesson_block(self, run: dict) -> dict:
        """Identical for every call of this lesson → prompt-cached."""
        return {
            "type": "text",
            "text": f"LESSON TEXT (the only source of content):\n---\n{run['text']}\n---",
            "cache_control": {"type": "ephemeral"},
        }

    def _call(self, system: str, run: dict, prompt: str, max_tokens: int,
              label: str) -> Tuple[Optional[str], Optional[str]]:
        attempts = len(STREAM_RETRY_BACKOFF_S) + 1
        for attempt in range(1, attempts + 1):
            text, stop, retryable = self._call_once(system, run, prompt, max_tokens, label)
            if text is not None or not retryable:
                return text, stop
            if attempt < attempts:
                wait = STREAM_RETRY_BACKOFF_S[attempt - 1]
                print(f"         ↻ {label}: transient failure — retry {attempt}/{attempts - 1} in {wait}s")
                time.sleep(wait)
        print(f"❌ [Tamil LP] {label}: still failing after {attempts - 1} retries")
        return None, None

    @staticmethod
    def _is_transient(e: Exception) -> bool:
        if isinstance(e, (anthropic.APIConnectionError, httpx.TransportError)):
            return True
        if isinstance(e, anthropic.APIStatusError):
            code = getattr(e, "status_code", 0) or 0
            return code == 429 or code >= 500 or "overloaded" in str(e).lower()
        return False

    def _call_once(self, system: str, run: dict, prompt: str, max_tokens: int,
                   label: str) -> Tuple[Optional[str], Optional[str], bool]:
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=[{"type": "text", "text": system,
                         "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": [
                    self._lesson_block(run),
                    {"type": "text", "text": prompt},
                ]}],
            ) as stream:
                msg = stream.get_final_message()
            text = "".join(getattr(b, "text", "") for b in msg.content
                           if getattr(b, "type", "") == "text")
            usage = getattr(msg, "usage", None)
            if usage is not None:
                print(f"         · {label}: in={getattr(usage, 'input_tokens', '?')} "
                      f"cache_write={getattr(usage, 'cache_creation_input_tokens', 0) or 0} "
                      f"cached={getattr(usage, 'cache_read_input_tokens', 0) or 0} "
                      f"out={getattr(usage, 'output_tokens', '?')} stop={msg.stop_reason}")
            return text, msg.stop_reason, False
        except Exception as e:
            transient = self._is_transient(e)
            print(f"❌ [Tamil LP] {label} {'transient ' if transient else ''}error: "
                  f"{type(e).__name__}: {e}")
            return None, None, transient

    def _call_json(self, system: str, run: dict, prompt: str, max_tokens: int,
                   label: str) -> Optional[dict]:
        """JSON call with ONE content-level retry (bad JSON or truncation)."""
        feedback = ""
        for attempt in (1, 2):
            raw, stop = self._call(system, run, prompt + feedback, max_tokens, f"{label} #{attempt}")
            if raw is None:
                return None
            if stop == "max_tokens":
                print(f"         ⚠️ {label}: output cut off at max_tokens")
                feedback = ("\n\nIMPORTANT: Your previous answer was cut off. Keep every "
                            "string SHORT and every list to its most important items so "
                            "the full JSON fits. Never shorten a copied book line.")
                continue
            try:
                return parse_json_response(raw)
            except ValueError as e:          # json.JSONDecodeError is a ValueError
                print(f"         ⚠️ {label}: invalid JSON ({e}) — retrying once")
                feedback = ("\n\nIMPORTANT: Your previous answer was not valid JSON. "
                            "Return ONLY one valid JSON object — no prose, no code "
                            "fences, double quotes only, no trailing commas.")
        return None

    # ==================================================================
    # CALL 0 — LESSON EXTRACTOR
    # ==================================================================

    _EXTRACTOR_SYSTEM = (
        "You are a strict text extractor for Samacheer Kalvi Class 6 Tamil lessons. "
        "Return ONLY valid JSON. Copy book lines and headings character for character "
        "from the lesson text. Never invent lines, names, facts or numbers. No markdown, "
        "no code fences. Raw JSON starting with {"
    )

    def _type_extraction_rules(self, ltype: str) -> str:
        if ltype == "poem":
            return """THIS IS A POEM (கவிதைப்பேழை):
- "stanzas": EVERY line of the poem itself, in order, grouped as printed
  (couplets / stanzas). Copy each line EXACTLY. Do not include headings,
  சொல்லும் பொருளும், பாடலின் பொருள் or நூல்வெளி lines.
- "poetic_feature": the sound pattern this lesson's exercises ask about
  (e.g. இயைபு / எதுகை / மோனை), exactly as the book names it, or "".
- "sections": [] (not used for poems).
- "key_content": rows [book word or image in the poem | its meaning in spoken
  Tamil | short English gloss] — the poem's main images / comparisons."""
        if ltype == "thirukural":
            return """THIS IS A THIRUKKURAL LESSON (வாழ்வியல்):
- "kurals": EVERY kural in the lesson, in order: its serial number as printed
  (or 1, 2, 3 … if none), its chapter (அதிகாரம்) name as printed, its TWO
  lines copied EXACTLY, its meaning in one short spoken-Tamil line based on
  the book's own meaning line, and a short English gloss.
- "sections": [] (not used).
- "key_content": [] (Python builds the kural table)."""
        if ltype == "supplementary":
            return """THIS IS A SUPPLEMENTARY READER (விரிவானம்):
- "sections": EXACTLY 3 consecutive parts that together cover the whole
  lesson text before the exercises (beginning / middle / end, roughly equal).
  "heading": your short Tamil title for the part (3-6 words);
  "start": the first 6-8 words of the part EXACTLY as in the text;
  "size": "medium".
- "key_content": rows [event or idea | spoken-Tamil explanation | short
  English gloss] — the lesson's key events and ideas, in order."""
        if ltype == "grammar":
            return """THIS IS A GRAMMAR LESSON (கற்கண்டு):
- "sections": every grammar sub-topic in textbook order (e.g. each new term
  or rule). "heading": the sub-topic heading EXACTLY as in the text
  (or the term itself if it has no heading); "start": first 6-8 words of the
  sub-topic EXACTLY as in the text; "size": "small" (a few lines),
  "medium" or "large" (several rules / many examples).
- "key_content": rows [grammar term | its meaning in simple book Tamil | one
  example from the book, copied exactly]."""
        return """THIS IS A PROSE LESSON (உரைநடை உலகம்):
- "sections": every teaching section in textbook order. Real sub-headings
  sometimes arrive WITHOUT ### and some ### lines are only boxes or table
  titles — decide from the text. A box ([பெட்டிச் செய்தி]) or a small table
  belongs to the section it sits in; it is not a section of its own.
  "heading": EXACTLY as in the text; "start": first 6-8 words EXACTLY;
  "size": "small" (a few lines), "medium", or "large".
- "key_content": rows [section heading | its main idea in one short Tamil
  line | one example printed in the book, copied exactly]."""

    def _call_extractor(self, run: dict) -> Optional[dict]:
        ltype = run["lesson_type"]
        cols = KEY_CONTENT_TABLES[ltype]["columns"]
        prompt = f"""Extract the data a lesson planner needs from the LESSON TEXT above.

Lesson : {run['title']}
Type   : {LESSON_TYPE_NAMES[ltype]} ({ltype})
Class  : {run['class_num']}

The lesson text is already cleaned: [பெட்டிச் செய்தி] … [/பெட்டிச் செய்தி] is a
boxed note, [செயல்பாடு] … [/செயல்பாடு] an activity box, ________ a blank,
+ and = are printed symbols. The book exercises (கற்பவை கற்றபின், மதிப்பீடு …)
come at the end: they are NOT teaching sections.

{self._type_extraction_rules(ltype)}

FOR EVERY LESSON:
- "word_wall": 8-14 words children need: the book's சொல்லும் பொருளும் words
  first (copied exactly), then other key words of the lesson. Each:
  book_word (exact) | spoken_meaning (simple spoken Tamil) | english (1-3 words).
- "key_content" columns are: {' | '.join(cols)}
- "nool_veli": facts from நூல்வெளி / author notes, ONLY as printed (short lines).
- "objectives": 3-5 "I can" lines in spoken Tamil, first person, e.g.
  "பாட்டை ராகத்தோட பாடுவேன்." — no English.
- "difficulty_points": 2-3 short Tamil lines: what children of 10-11 may find
  hard in THIS lesson.
- "materials": 4-8 short Tamil items: pictures, objects, cards, chart paper
  that THIS lesson's periods will need. No internet, no page numbers.

RULES:
- Copy every book line and heading exactly. Never correct spellings.
- Meanings ("spoken_meaning", key_content) come from the book's own
  சொல்லும் பொருளும் / பாடலின் பொருள் / explanations — no outside background,
  no gods, devas or myths unless the book itself says so.
- Keep every string you write yourself short (under 15 words).
- No CJK characters. No Tamil written in English letters.

Return ONLY this JSON:
{{
  "sections": [{{"heading": "...", "start": "...", "size": "medium"}}],
  "stanzas": [{{"lines": ["...", "..."]}}],
  "poetic_feature": "",
  "kurals": [{{"number": "1", "chapter": "...", "lines": ["...", "..."], "meaning_spoken": "...", "english": "..."}}],
  "word_wall": [{{"book_word": "...", "spoken_meaning": "...", "english": "..."}}],
  "key_content": [["...", "...", "..."]],
  "nool_veli": ["..."],
  "objectives": ["..."],
  "difficulty_points": ["..."],
  "materials": ["..."]
}}"""
        data = self._call_json(self._EXTRACTOR_SYSTEM, run, prompt,
                               MAX_TOKENS_EXTRACTOR, "Lesson Extractor")
        if not isinstance(data, dict):
            return None
        return self._validate_extraction(run, data)

    # ---------- validation / repair of extractor output ----------

    @staticmethod
    def _str(x) -> str:
        """Plain text from an extractor field: tags dropped, whitespace trimmed."""
        s = re.sub(r"<[^>]+>", "", str(x if x is not None else ""))
        return html_lib.unescape(re.sub(r"\s+", " ", s)).strip()

    def _snap(self, run: dict, line: str) -> Tuple[str, bool]:
        """
        Replace an extractor line with the matching line from the lesson text
        (so book lines are always the extracted text's own version).
        Returns (line, found).
        """
        line = self._str(line)
        if not line:
            return line, False
        src = run["source_lines"]
        n = normalize_tamil(line)
        for s in src:
            if normalize_tamil(s) == n:
                return s, True
        best = difflib.get_close_matches(line, src, n=1, cutoff=SNAP_MIN_RATIO)
        if best:
            return best[0], True
        return line, normalize_tamil(line) in normalize_tamil(run["text"])

    def _validate_extraction(self, run: dict, data: dict) -> Optional[dict]:
        ltype = run["lesson_type"]
        out: Dict[str, Any] = {}
        unfound: List[str] = []

        def str_list(key, limit):
            v = data.get(key)
            return [self._str(x) for x in v if self._str(x)][:limit] if isinstance(v, list) else []

        # sections
        secs = []
        for s in data.get("sections") or []:
            if not isinstance(s, dict) or not self._str(s.get("heading")):
                continue
            size = self._str(s.get("size")).lower()
            secs.append({
                "heading": self._str(s.get("heading")),
                "start": self._str(s.get("start")),
                "size": size if size in ("small", "medium", "large") else "medium",
            })
        out["sections"] = secs

        # stanzas (poem) — every line snapped to the source
        stanzas = []
        for st in data.get("stanzas") or []:
            lines = st.get("lines") if isinstance(st, dict) else st
            if not isinstance(lines, list):
                continue
            fixed = []
            for l in lines:
                s, ok = self._snap(run, l)
                if s:
                    fixed.append(s)
                    if not ok:
                        unfound.append(s)
            if fixed:
                stanzas.append(fixed)
        out["stanzas"] = stanzas
        out["poetic_feature"] = self._str(data.get("poetic_feature"))

        # kurals
        kurals = []
        for i, k in enumerate(data.get("kurals") or [], start=1):
            if not isinstance(k, dict) or not isinstance(k.get("lines"), list):
                continue
            lines = []
            for l in k["lines"]:
                s, ok = self._snap(run, l)
                if s:
                    lines.append(s)
                    if not ok:
                        unfound.append(s)
            if not lines:
                continue
            kurals.append({
                "number": self._str(k.get("number")) or str(i),
                "chapter": self._str(k.get("chapter")),
                "lines": lines,
                "meaning_spoken": self._str(k.get("meaning_spoken")),
                "english": self._str(k.get("english")),
            })
        out["kurals"] = kurals

        # memorisation: from the deterministic markers, not the model
        mem_lines = {normalize_tamil(l) for b in run["memorise"] for l in b}
        for k in kurals:
            k["memorise"] = any(normalize_tamil(l) in mem_lines for l in k["lines"])
        out["stanza_memorise"] = [any(normalize_tamil(l) in mem_lines for l in st) for st in stanzas]

        # word wall
        ww = []
        for w in data.get("word_wall") or []:
            if isinstance(w, dict) and self._str(w.get("book_word")):
                ww.append([self._str(w.get("book_word")), self._str(w.get("spoken_meaning")),
                           self._str(w.get("english"))])
        out["word_wall"] = ww[:MAX_WORD_WALL_ROWS]

        rows = []
        for r in data.get("key_content") or []:
            if isinstance(r, list) and any(self._str(c) for c in r):
                rows.append([self._str(c) for c in (r + ["", "", ""])[:3]])
        out["key_content"] = rows[:MAX_KEY_ROWS]

        out["nool_veli"] = str_list("nool_veli", 10)
        out["objectives"] = str_list("objectives", 6)
        out["difficulty_points"] = str_list("difficulty_points", 4)
        out["materials"] = str_list("materials", 10)
        out["unfound_lines"] = unfound

        # usability per type
        if ltype == "poem" and not stanzas:
            print("         ⚠️ No poem lines extracted — periods will work from the lesson text only")
        if ltype == "thirukural" and not kurals:
            print("         ❌ No kurals extracted")
            return None
        if ltype in ("prose", "grammar", "supplementary") and not secs:
            print("         ❌ No teaching sections extracted")
            return None
        if unfound:
            print(f"         ⚠️ {len(unfound)} extracted book line(s) not found in the text "
                  f"(kept, flagged for review): {unfound[:2]}")
        print(f"         ✅ sections={len(secs)} stanzas={len(stanzas)} kurals={len(kurals)} "
              f"word_wall={len(ww)} memorise={sum(out['stanza_memorise']) + sum(k['memorise'] for k in kurals)}")
        return out

    # ==================================================================
    # PERIOD PLAN (Python, deterministic)
    # ==================================================================

    @staticmethod
    def _group_sections(sections: List[dict], max_groups: int) -> List[List[dict]]:
        """Small sections merge forward; then merge the lightest adjacent pair until it fits."""
        weight = {"small": 1, "medium": 2, "large": 3}
        groups, pending = [], []
        for s in sections:
            pending.append(s)
            if s["size"] != "small":
                groups.append(pending)
                pending = []
        if pending:
            if groups:
                groups[-1].extend(pending)
            else:
                groups.append(pending)
        while len(groups) > max(1, max_groups):
            w = [sum(weight[s["size"]] for s in g) for g in groups]
            i = min(range(len(groups) - 1), key=lambda k: w[k] + w[k + 1])
            groups[i:i + 2] = [groups[i] + groups[i + 1]]
        return groups

    @staticmethod
    def _join_headings(group: List[dict]) -> str:
        return " · ".join(s["heading"] for s in group)

    def _plan_periods(self, run: dict) -> List[dict]:
        ltype, data = run["lesson_type"], run["data"]
        pat = get_pattern(ltype)
        plan: List[dict] = []

        if ltype == "poem":
            halves = split_evenly(list(range(len(data["stanzas"]))), 2) if data["stanzas"] else [[], []]
            while len(halves) < 2:
                halves.append([])
            feature = data["poetic_feature"]
            titles = [pat["periods"][0]["title_hint"],
                      "பாடலின் முதல் பகுதி",
                      "பாடலின் இரண்டாம் பகுதி" + (f", {feature}" if feature else ""),
                      pat["periods"][3]["title_hint"]]
            for i in range(4):
                idx = halves[i - 1] if i in (1, 2) else (list(range(len(data["stanzas"]))) if i == 0 else [])
                plan.append({"title": titles[i], "stanzas": idx, "sections": [], "kurals": []})

        elif ltype == "thirukural":
            groups = split_evenly(list(range(len(data["kurals"]))), pat["kural_periods"])
            while len(groups) < pat["kural_periods"]:
                groups.append([])
            for gi, g in enumerate(groups):
                nums = [data["kurals"][i]["number"] for i in g]
                rng = f"{nums[0]}–{nums[-1]}" if len(nums) > 1 else (nums[0] if nums else "")
                title = (f"குறள் அறிமுகம், குறள் {rng}" if gi == 0 else f"குறள் {rng}").strip()
                plan.append({"title": title, "kurals": g, "sections": [], "stanzas": []})
            plan.append({"title": pat["periods"][3]["title_hint"], "kurals": [],
                         "sections": [], "stanzas": []})

        elif ltype == "supplementary":
            parts = split_evenly(data["sections"], 3)
            while len(parts) < 3:
                parts.append([])
            for g in parts:
                plan.append({"title": self._join_headings(g) or "பாடப் பகுதி",
                             "sections": g, "stanzas": [], "kurals": []})
            plan.append({"title": "பாத்திரமேற்று வாசித்தல், கற்பவை கற்றபின்",
                         "sections": [], "stanzas": [], "kurals": []})

        elif ltype == "grammar":
            groups = self._group_sections(data["sections"], pat["max_periods"])
            for g in groups:
                plan.append({"title": self._join_headings(g), "sections": g,
                             "stanzas": [], "kurals": []})

        else:  # prose
            groups = self._group_sections(data["sections"], pat["max_periods"] - 1)
            for g in groups:
                plan.append({"title": self._join_headings(g), "sections": g,
                             "stanzas": [], "kurals": []})
            plan.append({"title": pat["final_period"]["title_hint"], "sections": [],
                         "stanzas": [], "kurals": []})

        total = len(plan)
        if not (pat["min_periods"] <= total <= pat["max_periods"]):
            print(f"         ⚠️ {total} periods is outside {pat['min_periods']}-{pat['max_periods']} "
                  f"for {ltype} (kept — lesson is short/long)")
        occurrence = 0
        for i, p in enumerate(plan):
            p["num"] = i + 1
            p["is_last"] = i == total - 1
            p["strategy"] = get_period_strategy(ltype, i, total, occurrence)
            if p["sections"]:
                occurrence += 1
        return plan

    # ==================================================================
    # PREAMBLE — built entirely in Python from extractor data
    # ==================================================================

    @staticmethod
    def _esc(s: Any) -> str:
        return html_lib.escape(str(s if s is not None else ""), quote=False)

    def _table(self, head: List[str], rows: List[List[str]]) -> str:
        th = "".join(f"<th>{self._esc(h)}</th>" for h in head)
        body = "\n".join("<tr>" + "".join(f"<td>{self._esc(c)}</td>" for c in r) + "</tr>"
                         for r in rows)
        return (f'<div class="vocab-block">\n<table>\n<thead><tr>{th}</tr></thead>\n'
                f"<tbody>\n{body}\n</tbody>\n</table>\n</div>")

    def _ul(self, items: List[str]) -> str:
        return "<ul>\n" + "\n".join(f"<li>{self._esc(i)}</li>" for i in items) + "\n</ul>"

    def _key_rows(self, run: dict) -> List[List[str]]:
        data = run["data"]
        if run["lesson_type"] == "thirukural":
            return [[f"{k['number']} · {k['chapter']}" + (" *" if k["memorise"] else ""),
                     k["meaning_spoken"], k["english"]] for k in data["kurals"]]
        return data["key_content"]

    def _build_preamble(self, run: dict) -> str:
        data, ltype, T = run["data"], run["lesson_type"], PREAMBLE_TITLES
        total = run["total"]
        part = lambda n, key: f'<h2>{L["part"]} {n}: {T[key]}</h2>'

        overview = self._table(["விவரம்", "குறிப்பு"], [
            ["வகுப்பு", run["class_num"]],
            ["இயல்", run["unit"]],
            ["பாட வகை", LESSON_TYPE_NAMES[ltype]],
            ["பாடத் தலைப்பு", run["title"]],
            [L["period"] + "கள்", f"{total} × {PERIOD_MINUTES} {L['minutes']}"],
        ])

        objectives = self._ul(data["objectives"]) if data["objectives"] else "<p>—</p>"
        word_wall = (self._table(WORD_WALL_COLUMNS, data["word_wall"])
                     if data["word_wall"] else "<p>—</p>")

        kc = KEY_CONTENT_TABLES[ltype]
        key_rows = self._key_rows(run)
        key_html = ""
        if key_rows:
            key_html = f"<h3>{self._esc(kc['title'])}</h3>\n" + self._table(kc["columns"], key_rows)
            if ltype == "thirukural" and any(k["memorise"] for k in data["kurals"]):
                key_html += "\n<p><em>* மனப்பாடப் பகுதி</em></p>"
        if run["memorise"]:
            key_html += ("\n<h3>மனப்பாடப் பகுதி</h3>\n<div class=\"board-work\">"
                         + "<br/><br/>".join("<br/>".join(self._esc(l) for l in b)
                                             for b in run["memorise"])
                         + "</div>")
        if data["nool_veli"]:
            key_html += "\n<h3>நூல்வெளி</h3>\n" + self._ul(data["nool_veli"])

        plan = self._table([L["period"], "தலைப்பு", "கவனம்"],
                           [[p["num"], p["title"], self._plan_focus(run, p)]
                            for p in run["periods"]])

        meta = TAMIL_STRUCTURE_META
        approach = (
            "<ul>\n"
            "<li>ஒவ்வொரு பாடவேளையிலும்: தமிழ் முதலில், படம் அல்லது செயல் அடுத்து, ஆங்கிலம் கடைசியில்.</li>\n"
            "<li>ஆசிரியர் பேச்சு பேச்சுத் தமிழில்; பாடநூல் வரிகள் எழுத்துத் தமிழில், உள்ளபடியே.</li>\n"
            "<li>ஆசிரியர் முதலில் படிக்கிறார் / பாடுகிறார், வகுப்பு திருப்பிச் சொல்கிறது, பிறகு இணையாகப் படிக்கிறார்கள்.</li>\n"
            "<li>குழந்தைகள் எந்த மொழியிலும் பதில் சொல்லலாம்; ஆசிரியர் அதைத் தமிழில், முக்கியச் சொல்லுடன் திருப்பிச் சொல்கிறார்.</li>\n"
            "</ul>\n"
        )
        if data["difficulty_points"]:
            approach += "<h3>இந்தப் பாடத்தில் கவனிக்க வேண்டியவை</h3>\n" + self._ul(data["difficulty_points"]) + "\n"
        approach += static_language_tables_html()

        materials = self._ul(data["materials"]) if data["materials"] else "<p>—</p>"

        html = "\n".join([
            part(1, "overview"), overview,
            part(2, "objectives"), objectives,
            part(3, "word_wall"), word_wall,
            key_html,
            part(4, "plan"), plan,
            part(5, "approach"), approach,
            part(6, "materials"), materials,
        ])
        return normalize_preamble_html(html)

    def _plan_focus(self, run: dict, p: dict) -> str:
        """One line per period for the plan table — from real content, not free text."""
        data = run["data"]
        if p["kurals"]:
            return "குறள் " + ", ".join(data["kurals"][i]["number"] for i in p["kurals"])
        if p["stanzas"] and len(p["stanzas"]) < len(data["stanzas"]):
            first = data["stanzas"][p["stanzas"][0]][0]
            return f"“{first[:40]}…” முதல்"
        if p["sections"]:
            return self._join_headings(p["sections"])
        if p["is_last"]:
            return "கற்பவை கற்றபின், மதிப்பீடு, " + L["homework"]
        return "முழுப் பாடல் — கேட்டல், பாடுதல்" if run["lesson_type"] == "poem" else p["title"]

    # ==================================================================
    # PERIODS
    # ==================================================================

    _PERIOD_SYSTEM = "\n".join([
        TAMIL_LP_SYSTEM_PROMPT, BOOK_LINES_INSTRUCTION, CFU_INSTRUCTION,
        CCQ_GRAMMAR_INSTRUCTION, EXIT_SLIP_INSTRUCTION, HOMEWORK_INSTRUCTION,
    ])

    def _period_content_block(self, run: dict, p: dict) -> str:
        data, lines = run["data"], []
        if p["stanzas"]:
            lines.append("TODAY'S POEM LINES (copy exactly into the பாடநூல் வரிகள் box):")
            for i in p["stanzas"]:
                mark = "   ← மனப்பாடப் பகுதி" if data["stanza_memorise"][i] else ""
                lines.append("  " + " / ".join(data["stanzas"][i]) + mark)
        if p["kurals"]:
            lines.append("TODAY'S KURALS (copy exactly into the பாடநூல் வரிகள் box):")
            for i in p["kurals"]:
                k = data["kurals"][i]
                lines.append(f"  குறள் {k['number']} ({k['chapter']}){'   ← மனப்பாடப் பகுதி' if k['memorise'] else ''}")
                lines.append("    " + " / ".join(k["lines"]))
                if k["meaning_spoken"]:
                    lines.append(f"    meaning (spoken): {k['meaning_spoken']}")
        if p["sections"]:
            lines.append("TODAY'S SECTIONS (teach ALL, in order; nothing from other periods):")
            for s in p["sections"]:
                lines.append(f"  ■ {s['heading']}" + (f"  — begins: “{s['start']}”" if s["start"] else ""))
        if not lines:
            if p["is_last"]:
                lines.append("TODAY: the whole lesson again, through the book's own exercises "
                             "(see BOOK EXERCISES below).")
            else:
                lines.append(f"TODAY: {p['strategy']['focus']}")
        if run["data"]["nool_veli"] and p["is_last"] and run["lesson_type"] in ("poem", "thirukural"):
            lines.append("நூல்வெளி FACTS (only these): " + " | ".join(run["data"]["nool_veli"]))
        return "\n".join(lines)

    def _build_period_prompt(self, run: dict, p: dict) -> str:
        n, total, st = p["num"], run["total"], p["strategy"]
        ltype = run["lesson_type"]
        prev = run["periods"][n - 2] if n > 1 else None
        nxt = run["periods"][n] if n < total else None
        next_line = self._next_line(run, p)
        recall = ("This is the FIRST period — no recall; go straight to the hook."
                  if prev is None else
                  f"Open with a one-minute recall of the last period (“{prev['title']}”), then the hook.")
        timing = "\n".join(f"  {t:<6} {L[key]:<24} {cls:<26} {purpose}"
                           for cls, key, t, purpose in TAMIL_PERIOD_TIMING)
        ccq_rule = ("CCQ: REQUIRED — one ccq-block right after EACH new grammar term in "
                    f"{L['teach']}." if ltype == "grammar"
                    else "CCQ: NOT used in this lesson — no ccq-block anywhere.")
        hw_rule = (f"{L['homework']}: REQUIRED in this period — one item chosen from BOOK "
                   "EXERCISES below, copied exactly." if p["is_last"]
                   else f"{L['homework']}: NOT in this period.")
        exercises = run["info"]["parts"]["exercises"]
        nool_rule = ""
        if ltype in ("poem", "thirukural") and not p["is_last"]:
            nool_rule = ("\nநூல்வெளி: NOT in this period — the poet / book facts are taught "
                         "only in the last period. At most name the poet in one line.")
        ex_block = ""
        if p["is_last"] and exercises:
            ex_block = f"\nBOOK EXERCISES (exactly as in the lesson text):\n---\n{exercises}\n---\n"
        last_note = f"\nLAST PERIOD: {st['last_period_note']}" if st["last_period_note"] else ""
        mem_note = ""
        if run["memorise"] and ltype == "poem":
            mem_note = ("\nMEMORISATION (மனப்பாடப் பகுதி) of this lesson: "
                        + " || ".join(" / ".join(b) for b in run["memorise"]))

        ccq_tpl = ""
        if ltype == "grammar":
            ccq_tpl = f"\n  [one ccq-block right after each new grammar term — see the CCQ rules]"
        hw_tpl = (f'\n  <div class="board-work"><strong>{L["homework"]}:</strong><br/>[one book item, copied exactly]</div>'
                  if p["is_last"] else "")

        return f"""Write {L['period']} {n} of {total} of a Class 6 Tamil lesson plan.

Lesson  : {run['title']}
Meta    : {run['meta_line']}
Period  : {n} of {total} · {PERIOD_MINUTES} minutes

═══════════════════════════════════════════════════════
TODAY'S CONTENT (from THIS lesson's text)
═══════════════════════════════════════════════════════
Title : {p['title']}
{self._period_content_block(run, p)}{mem_note}

═══════════════════════════════════════════════════════
TODAY'S TEACHING PLAN (from the teacher-approved manual LP)
═══════════════════════════════════════════════════════
Focus      : {st['focus']}
Recall     : {recall}
{L['hook']:<10} : {st['hook_style']} — {st['hook_instruction']}
{L['teach']:<10} : {st['teach_instruction']}
{L['do']:<10} : {st['do_style']} — {st['do_instruction']}
{L['close']:<10} : {st['close_instruction']}{last_note}
{ccq_rule}
{hw_rule}{nool_rule}

TIMING (minutes; contiguous 0 → {PERIOD_MINUTES}; boundaries may move a little):
{timing}

DETAIL LEVEL: about 6-10 lines per block. Write the EXACT teacher words for the
hook and for every question, each with its expected answer. Do not script every
sentence.
{ex_block}
═══════════════════════════════════════════════════════
GENERATE {L['period']} {n} using EXACTLY this HTML structure
═══════════════════════════════════════════════════════

<div class="lp-day-block">
<h3 class="lp-day-title">{L['period']} {n} / {total} — {self._esc(p['title'])}</h3>
<p class="lp-day-meta">{self._esc(run['meta_line'])}</p>

<div class="lp-section-opening">
  <p class="lp-section-label">{L['hook']}</p>
  <span class="lp-time">0–4 {L['minutes']}</span>
  <div class="lp-teacher-says"><strong>{L['teacher']}:</strong> [recall line if not the first period, then the hook question in spoken Tamil] ([English gloss])</div>
  <p>[2-3 answers to expect; how the teacher says them back in Tamil]</p>
</div>

<div class="lp-section-main">
  <p class="lp-section-label">{L['teach']}</p>
  <span class="lp-time">4–13 {L['minutes']}</span>
  <div class="lp-teacher-says"><strong>{L['teacher']}:</strong> [explanation of today's chunk in spoken Tamil; ONE English gloss after the main explanation of the new idea]</div>
  [பாடநூல் வரிகள் board-work with today's book lines, if any]{ccq_tpl}
</div>

<div class="lp-section-student-task">
  <p class="lp-section-label">{L['do']}</p>
  <span class="lp-time">13–23 {L['minutes']}</span>
  <div class="lp-teacher-says"><strong>{L['teacher']}:</strong> [task instructions in spoken Tamil] ([English gloss])</div>
  <p>[what children do, step by step, and what the teacher looks for]</p>
</div>

<div class="lp-section-closing">
  <p class="lp-section-label">{L['close']}</p>
  <span class="lp-time">23–30 {L['minutes']}</span>
  [cfu-block — two oral questions with expected answers in book Tamil]
  <div class="board-work"><strong>{L['exit_slip']}:</strong><br/>[one-line task] ([expected answer])</div>{hw_tpl}
  <p><em>{self._esc(next_line)}</em></p>
</div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ Output starts with <div class="lp-day-block"> and ends with its </div>
✅ Four lp-section blocks in order, each closed before the next
✅ All labels exactly as in the template, in Tamil, with no English beside them
✅ Teacher talk in neutral spoken Tamil; book lines copied exactly; no Tamil in English letters
✅ English glosses ONLY after the hook, the main explanation and task instructions
✅ One CFU (two questions + expected answers in book Tamil); {L['exit_slip']} present
✅ {"One CCQ after each new grammar term" if ltype == "grammar" else "No ccq-block"}
✅ {"Homework present, copied from the book exercises" if p["is_last"] else "No homework"}
✅ Time labels 0 → {PERIOD_MINUTES}, contiguous, Arabic digits
✅ Only facts from the lesson text; no religious examples added; no page numbers
✅ Do NOT write {L['period']} {n + 1}"""

    LESSON_END_LINE = "இந்தப் பாடம் நிறைவு."
    _NEXT_P_RE = re.compile(r"<p>\s*(?:<em>)?[^<]*?" + re.escape(LABELS["next_period"])
                            + r".*?</p>", re.DOTALL)

    def _next_line(self, run: dict, p: dict) -> str:
        """Built from the real plan — the model once named a lesson that does not follow."""
        n = p["num"]
        if n < run["total"]:
            return f"{L['next_period']}: {run['periods'][n]['title']}"
        return self.LESSON_END_LINE

    def _set_next_line(self, run: dict, p: dict, html: str) -> str:
        """Remove whatever next-period line the model wrote; put ours at the end of the closing block."""
        html = self._NEXT_P_RE.sub("", html)
        html = html.replace(f"<p><em>{self.LESSON_END_LINE}</em></p>", "")
        line = f"<p><em>{self._esc(self._next_line(run, p))}</em></p>"
        m = re.search(r'<div class="lp-section-closing">', html)
        if not m:
            return html
        close = _matching_close_index(html, m.end())
        if not close:
            return html
        return html[: close[0]] + line + "\n" + html[close[0]:]

    def _generate_period(self, run: dict, p: dict) -> Optional[str]:
        ltype = run["lesson_type"]
        prompt = self._build_period_prompt(run, p)
        best: Optional[str] = None
        best_truncated = False
        feedback = ""
        for attempt in (1, 2):
            raw, stop = self._call(self._PERIOD_SYSTEM, run, prompt + feedback,
                                   MAX_TOKENS_PERIOD, f"Period {p['num']} #{attempt}")
            if not raw or not raw.strip():
                continue
            html = self._set_next_line(run, p, normalize_day_html(clean(raw), ltype))
            truncated = stop == "max_tokens"
            problems = check_day_structure(html, ltype, is_last_period=p["is_last"])

            if best is None or (not truncated and not is_critical(problems)):
                best, best_truncated = html, truncated

            if not truncated and not is_critical(problems):
                if problems:
                    print(f"         ⚠️ Period {p['num']} minor issues: {'; '.join(problems)}")
                self._log_book_lines(run, p, html)
                print(f"         ✅ Period {p['num']} ({len(html)} chars)")
                return html

            if attempt == 1:
                if truncated:
                    print(f"         ⚠️ Period {p['num']} cut off — retrying with a tighter brief")
                    feedback = ("\n\nIMPORTANT: Your previous answer was CUT OFF before "
                                f"{L['close']}. Write more concisely (about 6 lines per "
                                f"block) and make sure {L['close']} with the CFU and "
                                f"{L['exit_slip']} is complete.")
                else:
                    print(f"         ⚠️ Period {p['num']} problems: {'; '.join(problems)} — retrying")
                    feedback = ("\n\nIMPORTANT: Your previous answer had these problems: "
                                + "; ".join(x for x in problems if not x.startswith("minor:"))
                                + ". Follow the HTML structure exactly.")

        if best is None:
            return None
        if best_truncated:
            print(f"         ⚠️ Period {p['num']} still cut off — kept with LP_DAY_TRUNCATED marker")
            best = mark_truncated(best)
        else:
            print(f"         ⚠️ Period {p['num']} kept with structure problems after retry")
        self._log_book_lines(run, p, best)
        return best

    def _log_book_lines(self, run: dict, p: dict, html: str) -> None:
        bad = check_book_lines(html, run["text"])
        if bad:
            print(f"         ⚠️ Period {p['num']}: {len(bad)} book line(s) not as in the text "
                  f"(for the reviewer — not changed): {bad[:2]}")

    # ==================================================================
    # ASSESSMENT — separate top-level block
    # ==================================================================

    def _call_assessment(self, run: dict) -> Optional[str]:
        ltype, A = run["lesson_type"], ASSESSMENT_TITLES
        exercises = run["info"]["parts"]["exercises"] or "(no exercises found in the lesson text)"
        items = "\n".join(f"  - {x}" for x in assessment_items(ltype))
        extra = ""
        if ltype in ("poem", "thirukural"):
            extra += f"\n  <h3>{A['recitation']}</h3>\n  [what to listen for when children recite the memorisation part]"
        if ltype == "grammar":
            extra += f"\n  <h3>{A['rule_example']}</h3>\n  [one worked example of the main rule, from the book, in a board-work div]"
        mem = (" || ".join(" / ".join(b) for b in run["memorise"])) or "(none marked)"

        prompt = f"""Write ONLY the assessment pointers for this Class 6 Tamil lesson plan.
They appear in their own tab after the last period.

Lesson : {run['title']}
Meta   : {run['meta_line']}
Memorisation part: {mem}

COVER:
{items}

BOOK EXERCISES (exactly as in the lesson text — answer THESE, do not invent new ones):
---
{exercises}
---

RULES:
- Answers in BOOK Tamil (written Tamil). Copy MCQ options exactly as printed.
- Base every answer on the lesson text. If the lesson text does not settle an
  answer, write "{A['check_note']}" for that item.
- No English glosses here except one or two key terms where they truly help.
- Do NOT write homework here (it is in the last period).
- Maximum 3 table columns.

GENERATE using EXACTLY this HTML structure:

<div class="assessment-block">
  <h2>{L['assessment']} — {self._esc(run['title'])}</h2>
  <p><em>{A['check_note']}</em></p>
  <h3>{A['answers']}</h3>
  [numbered answers for the MCQs, fill-ins, matching and join/split items, in book order]
  <h3>{A['short']}</h3>
  [model answers in book Tamil, 1-3 sentences each]
  <h3>{A['thinking']}</h3>
  [what kinds of answers to accept, 2-3 lines]{extra}
  <h3>{A['diff']}</h3>
  <div class="vocab-block">
  <table>
    <thead><tr><th>{A['diff_support']}</th><th>{A['diff_stretch']}</th></tr></thead>
    <tbody><tr><td>[one support idea for this lesson]</td><td>[one stretch task for this lesson]</td></tr></tbody>
  </table>
  </div>
</div>

Raw HTML only. Start with <div class="assessment-block">. Do NOT use lp-day-block."""
        for attempt in (1, 2):
            raw, stop = self._call(self._PERIOD_SYSTEM, run, prompt, MAX_TOKENS_ASSESSMENT,
                                   f"Assessment #{attempt}")
            if not raw:
                continue
            if stop == "max_tokens" and attempt == 1:
                print("         ⚠️ Assessment cut off — retrying")
                prompt += ("\n\nIMPORTANT: Your previous answer was cut off. Keep answers "
                           "short so the whole block fits.")
                continue
            html = normalize_assessment_html(clean(raw))
            print(f"         ✅ Assessment ({len(html)} chars)")
            return html
        return None


# ============================================================================
# Singleton — imported by the Tamil router
# ============================================================================

tamil_lp_67_builder = TamilLP67Builder()