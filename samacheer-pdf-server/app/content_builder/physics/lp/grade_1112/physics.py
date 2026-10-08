"""
physics.py
----------
LP Builder for Samacheer Kalvi Physics — Class 11 & 12

v1.0 — Oct 2026

TEMPLATE: Manual LP "Class 12 Physics — Unit 1: Electrostatics" (21 days),
used as a content-agnostic teaching template for every Physics chapter
(see physics/base/day_structures.py). Topics are discovered per chapter.

CALL STRUCTURE (N = total days, decided per chapter, 3..22):
  Call 0a  → Section Extractor   (JSON — numbered subsections + physics data:
                                   formulae, derivations, solved examples,
                                   key terms with Tamil, misconceptions)
  Call 0b  → Day Allocator       (JSON — total_days + section ids per day +
                                   day type; validated and repaired in Python,
                                   deterministic fallback if it fails)
  Call 1   → Preamble            (model writes Parts 1-4, 6, 9; Python injects
                                   Part 5 Day-wise Plan, Part 7 Tamil Sheet,
                                   Part 8 Formula Wall from extractor data)
  Calls    → Day 1 .. Day N-1    (content days, one call each)
  Call     → Day N               (whole-chapter revision, no new content)
  Call     → Assessment          (top-level <div class="assessment-block">)

WEB CONTRACT (ai_converter._wrap_html + lesson-viewer.js):
  - each day = exactly <div class="lp-day-block"> ... </div>, title inside
  - one top-level <div class="assessment-block"> after the last day
  - enforced in Python by normalize_day_html / normalize_assessment_html,
    and checked again on the assembled output before returning

BACKEND CONTRACT (Physics handoff, Oct 2026):
  - generate(text, metadata) -> str | None ; never raises
  - streaming for every call (16k-token days exceed non-streaming limits)
  - SDK owns network retries (max_retries=3); the builder retries ONCE only
    for content problems (bad JSON, truncation, missing structure)
  - no per-run state on self (the singleton serves parallel requests)
  - failed day → visible placeholder with <!-- LP_DAY_FAILED -->
  - return None if: extractor/allocator unusable, preamble fails,
    assessment fails, or more than MAX_FAILED_DAYS days fail
"""

import html as html_lib
import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import anthropic
import httpx                    # installed with the anthropic SDK

from .....config import settings
from ...base import (
    PHYS_LP_SYSTEM_PROMPT,
    PREAMBLE_START_INSTRUCTION,
    TAMIL_INSTRUCTION,
    CCQ_CFU_INSTRUCTION,
    NUMERICAL_ROUTINE_INSTRUCTION,
    DERIVATION_INSTRUCTION,
    COMMON_MISTAKES_INSTRUCTION,
    clean,
    normalize_day_html,
    normalize_assessment_html,
    normalize_preamble_html,
    check_day_structure,
    is_critical,
    count_day_blocks,
    count_assessment_blocks,
    failed_day_block,
    mark_truncated,
    parse_json_response,
    get_display_title,
)
from ...base.day_structures import (
    PHYSICS_DAY_TYPES,
    PHYSICS_REVISION_DAY_STRATEGY,
    PHYSICS_ASSESSMENT_STRUCTURE,
    PHYSICS_STRUCTURE_META,
    PHYSICS_DEFAULT_TIMING,
    DAY_TYPE_ALIASES,
    get_day_strategy,
    normalize_day_type,
    expected_day_range,
)

try:  # LP text is normally already cleaned by the backend; this is a safety net
    from .....services.section_detector import clean_noise
except Exception:  # pragma: no cover
    clean_noise = None


# ============================================================================
# TUNABLES
# ============================================================================

MAX_TOKENS_EXTRACTOR  = 24000
MAX_TOKENS_ALLOCATOR  = 12000
MAX_TOKENS_PREAMBLE   = 8000
MAX_TOKENS_DAY        = 16000   # NEVER lower — days get cut off below this
MAX_TOKENS_ASSESSMENT = 12000

MAX_FAILED_DAYS = 1             # backend rule: >1 failed day → return None
                                # (TL to confirm; may become a ratio)

REQUEST_TIMEOUT_S = 900.0       # per streamed request
SDK_MAX_RETRIES   = 3           # connection errors / 429 / 5xx BEFORE the stream starts
STREAM_RETRY_BACKOFF_S = (10, 30, 60)   # our retries for drops DURING a stream

DAY_TEXT_MIN_CHARS = 800        # smaller slice than this → send full chapter
DAY_TEXT_MAX_CHARS = 90000

MAX_TAMIL_SHEET_ROWS = 40
MAX_FORMULA_ROWS     = 45


# ============================================================================
# PHYSICS LP BUILDER
# ============================================================================

class PhysicsLP1112Builder:

    discipline = "physics"

    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            max_retries=SDK_MAX_RETRIES,
            timeout=REQUEST_TIMEOUT_S,
        )
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Physics LP Builder (1112) v1.0 initialized — model: {self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """Never raises. Returns LP body HTML, or None on failure."""
        try:
            return self._generate(text, metadata or {})
        except Exception as e:  # last line of defence — backend contract
            print(f"❌ [Physics LP] Unexpected error — returning None: {type(e).__name__}: {e}")
            return None

    # ------------------------------------------------------------------
    # Orchestration (all per-run state lives in the local `run` dict)
    # ------------------------------------------------------------------

    def _generate(self, text: str, metadata: dict) -> Optional[str]:
        t0 = time.time()
        if not text or not text.strip():
            print("❌ [Physics LP] Empty chapter text — aborting")
            return None

        if clean_noise is not None:
            text = clean_noise(text, subject="physics")   # never the english default

        run: Dict[str, Any] = {
            "text": text,
            "title": get_display_title(metadata),
            "class_num": metadata.get("class", ""),
            "unit": metadata.get("unit", ""),
        }
        print(f"      [Physics LP] Generating: Class {run['class_num']} Unit {run['unit']} "
              f"— {run['title']} ({len(text)} chars)")

        # ── Call 0a — Section Extractor ───────────────────────────────
        print("      [Physics LP] Call 0a: Section Extractor...")
        extracted = self._call_section_extractor(run)
        if not extracted:
            print("         ❌ Section Extractor failed — aborting")
            return None
        run["sections"] = extracted["sections"]
        run["section_index"] = {s["id"]: i for i, s in enumerate(run["sections"])}
        print(f"         ✅ {len(run['sections'])} teaching sections")

        # ── Call 0b — Day Allocator (+ Python validation / fallback) ──
        print("      [Physics LP] Call 0b: Day Allocator...")
        content_days = self._call_day_allocator(run)
        if not content_days:
            print("         ❌ Day Allocator failed and fallback impossible — aborting")
            return None
        total_days = len(content_days) + 1
        run["total_days"] = total_days
        run["days"] = self._build_day_records(run, content_days)

        lo, hi = expected_day_range(len(text))
        print(f"         ✅ {total_days} days ({len(content_days)} content + 1 revision)"
              f"{'' if lo <= total_days <= hi else f'  ⚠️ outside expected {lo}-{hi}'}")
        for d in run["days"]:
            print(f"            Day {d['num']} [{d['strategy']['day_type']}]: {d['reference']}")

        parts: List[str] = []

        # ── Call 1 — Preamble ────────────────────────────────────────
        print("      [Physics LP] Call 1: Preamble...")
        preamble = self._call_preamble(run)
        if not preamble:
            print("         ❌ Preamble failed — aborting")
            return None
        parts.append(preamble)
        print(f"         ✅ Preamble ({len(preamble)} chars)")

        # ── Content days ─────────────────────────────────────────────
        failed = 0
        for d in run["days"]:
            print(f"      [Physics LP] Day {d['num']}/{total_days}: {d['title']}...")
            day_html = self._generate_day(run, d)
            if day_html is None:
                failed += 1
                print(f"         ❌ Day {d['num']} failed ({failed} so far)")
                if failed > MAX_FAILED_DAYS:
                    print(f"         ❌ More than {MAX_FAILED_DAYS} failed day(s) — aborting")
                    return None
                day_html = failed_day_block(d["num"], total_days, d["title"])
            parts.append(day_html)

        # ── Revision day (Day N) ─────────────────────────────────────
        print(f"      [Physics LP] Day {total_days}/{total_days}: Whole-chapter revision...")
        rev_html = self._generate_revision_day(run)
        if rev_html is None:
            failed += 1
            print(f"         ❌ Revision day failed ({failed} so far)")
            if failed > MAX_FAILED_DAYS:
                print(f"         ❌ More than {MAX_FAILED_DAYS} failed day(s) — aborting")
                return None
            rev_html = failed_day_block(total_days, total_days,
                                        PHYSICS_REVISION_DAY_STRATEGY["title"])
        parts.append(rev_html)

        # ── Assessment (top level, after the last day) ───────────────
        print("      [Physics LP] Assessment...")
        assessment = self._call_assessment(run)
        if not assessment:
            print("         ❌ Assessment failed — aborting")
            return None
        parts.append(assessment)

        combined = "\n\n".join(parts)

        # ── Final web-contract check ─────────────────────────────────
        n_days, n_assess = count_day_blocks(combined), count_assessment_blocks(combined)
        if n_days != total_days or n_assess != 1:
            print(f"         ❌ Contract check failed: {n_days} day blocks "
                  f"(expected {total_days}), {n_assess} assessment blocks (expected 1)")
            return None

        mins = (time.time() - t0) / 60
        print(f"      [Physics LP] ✅ Complete — {total_days} days, {failed} failed, "
              f"{len(combined)} chars, {mins:.1f} min")
        return combined

    # ==================================================================
    # API CALL HELPER — streaming, returns (text, stop_reason)
    # ==================================================================

    def _call(self, system: str, prompt: str, max_tokens: int,
              label: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Streamed call with retries for MID-STREAM failures.

        The SDK's max_retries only covers failures before the stream starts.
        A connection dropped during streaming (httpx.RemoteProtocolError
        "incomplete chunked read"), a read timeout, or an overloaded / 5xx
        error event mid-stream is NOT retried by the SDK — so we retry here,
        with backoff. Permanent errors (400/401/403/404/413/422) fail at once.
        """
        attempts = len(STREAM_RETRY_BACKOFF_S) + 1
        for attempt in range(1, attempts + 1):
            text, stop, retryable = self._call_once(system, prompt, max_tokens, label)
            if text is not None or not retryable:
                return text, stop
            if attempt < attempts:
                wait = STREAM_RETRY_BACKOFF_S[attempt - 1]
                print(f"         ↻ {label}: transient failure — retry {attempt}/{attempts - 1} in {wait}s")
                time.sleep(wait)
        print(f"❌ [Physics LP] {label}: still failing after {attempts - 1} retries")
        return None, None

    @staticmethod
    def _is_transient(e: Exception) -> bool:
        if isinstance(e, (anthropic.APIConnectionError, httpx.TransportError)):
            return True                       # dropped connection, read timeout, DNS blip
        if isinstance(e, anthropic.APIStatusError):
            code = getattr(e, "status_code", 0) or 0
            return code == 429 or code >= 500 or "overloaded" in str(e).lower()
        return False

    def _call_once(self, system: str, prompt: str, max_tokens: int,
                   label: str) -> Tuple[Optional[str], Optional[str], bool]:
        """Returns (text, stop_reason, retryable)."""
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=[{
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},  # same system text every day
                }],
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                msg = stream.get_final_message()
            text = "".join(
                getattr(b, "text", "") for b in msg.content
                if getattr(b, "type", "") == "text"
            )
            usage = getattr(msg, "usage", None)
            if usage is not None:
                print(f"         · {label}: in={getattr(usage, 'input_tokens', '?')} "
                      f"out={getattr(usage, 'output_tokens', '?')} stop={msg.stop_reason}")
            return text, msg.stop_reason, False
        except Exception as e:
            transient = self._is_transient(e)
            print(f"❌ [Physics LP] {label} {'transient ' if transient else ''}error: "
                  f"{type(e).__name__}: {e}")
            return None, None, transient

    def _call_json(self, system: str, prompt: str, max_tokens: int,
                   label: str) -> Optional[dict]:
        """JSON call with ONE content-level retry (bad JSON or truncation)."""
        feedback = ""
        for attempt in (1, 2):
            raw, stop = self._call(system, prompt + feedback, max_tokens, f"{label} #{attempt}")
            if raw is None:
                return None          # network failure already retried in _call()
            if stop == "max_tokens":
                print(f"         ⚠️ {label}: output cut off at max_tokens")
                feedback = ("\n\nIMPORTANT: Your previous answer was cut off. Keep every "
                            "string field SHORT (under 15 words) and every list to its "
                            "most important items so the full JSON fits.")
                continue
            try:
                return parse_json_response(raw)
            except json.JSONDecodeError as e:
                print(f"         ⚠️ {label}: invalid JSON ({e}) — retrying once")
                feedback = ("\n\nIMPORTANT: Your previous answer was not valid JSON. "
                            "Return ONLY one valid JSON object — no prose, no code "
                            "fences, double quotes only, no trailing commas.")
        return None

    # ==================================================================
    # CALL 0a — SECTION EXTRACTOR
    # ==================================================================

    def _call_section_extractor(self, run: dict) -> Optional[dict]:
        non_teaching = ", ".join(PHYSICS_STRUCTURE_META["non_teaching_parts"])
        day_types = "\n".join(
            f'  "{k}": {v["allocator_hint"]}' for k, v in PHYSICS_DAY_TYPES.items()
        )
        prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Physics chapter.

Chapter : {run['title']}
Class   : {run['class_num']}
Unit    : {run['unit']}

YOUR JOB: list every TEACHABLE numbered subsection of this chapter, in
textbook order, with the physics data a lesson planner needs.

WHAT COUNTS AS ONE SECTION:
- The smallest NUMBERED heading that has its own teaching content:
  use x.y.z when the textbook has it, otherwise x.y.
- A numbered parent heading whose text is only a 1-2 line lead-in to its
  children is NOT a separate section — fold its lead-in into the first child.
- Unnumbered sub-headings inside a numbered section go in "subheadings".
- Copy numbers and headings EXACTLY as written. Do not paraphrase.

EXCLUDE (these are not teaching content): {non_teaching}.
List what you excluded in "excluded_parts".

FOR EACH SECTION:
- content_type: one of
{day_types}
- est_minutes: realistic classroom teaching minutes for THIS section alone
  (a short definition ≈ 5-8; a law with a solved example ≈ 15-20; a long
  derivation ≈ 20-30)
- formulae: every formula/law stated in this section. "expression_html" uses
  plain HTML only: <sup>, <sub> and Unicode symbols (× − ε₀ π λ θ Δ √ ∝).
  Copy from the text. If the text's formula is garbled by extraction, write the
  standard textbook form and set "reconstructed": true.
- derivations: names of expressions the text DERIVES step by step here
- solved_examples: one short line each, keeping the textbook's numbers exactly
- key_terms: important terms with a simple-English meaning and a short Tamil
  term or phrase (standard Tamil Nadu textbook Tamil; keep English if unsure)
- misconceptions: typical student confusions with THIS section's content
  (from the text's own emphasis or well-known errors for this exact idea)
- diagrams: figures/diagrams the text refers to (short description)
- historical_facts: only names / dates / facts that appear in the text

RULES:
- Use ONLY this chapter's text. Never invent numbers, dates, names or data.
- Keep every string short (under 20 words). Keep lists to what matters.

Return ONLY valid JSON, starting with {{ — no prose, no code fences:

{{
  "chapter_title": "...",
  "sections": [
    {{
      "id": "S1",
      "number": "1.2.1",
      "heading": "Superposition principle",
      "subheadings": ["..."],
      "content_type": "formula_numerical",
      "est_minutes": 18,
      "has_derivation": false,
      "formulae": [
        {{"name": "Coulomb's law", "expression_html": "F = k q<sub>1</sub>q<sub>2</sub>/r<sup>2</sup>", "si_unit": "N", "reconstructed": false}}
      ],
      "derivations": [],
      "solved_examples": ["..."],
      "key_terms": [{{"english": "...", "simple_english": "...", "tamil": "..."}}],
      "misconceptions": ["..."],
      "diagrams": ["..."],
      "historical_facts": []
    }}
  ],
  "excluded_parts": ["Summary", "Evaluation"]
}}

Chapter Text:
---
{run['text']}
---"""
        system = ("You are a strict text extractor for physics textbooks. Return ONLY "
                  "valid JSON. Never invent structure, numbers, dates or names. No "
                  "markdown. No code fences. Raw JSON starting with {")

        data = self._call_json(system, prompt, MAX_TOKENS_EXTRACTOR, "Section Extractor")
        if not data or not isinstance(data.get("sections"), list) or not data["sections"]:
            return None

        sections = []
        seen_ids = set()
        for i, s in enumerate(data["sections"], start=1):
            if not isinstance(s, dict) or not str(s.get("heading", "")).strip():
                continue
            sid = str(s.get("id") or f"S{i}").strip()
            if sid in seen_ids:
                sid = f"S{i}x"
            seen_ids.add(sid)
            s["id"] = sid
            s["number"] = str(s.get("number", "")).strip()
            s["heading"] = str(s["heading"]).strip()
            s["content_type"] = normalize_day_type(s.get("content_type", ""))
            try:
                s["est_minutes"] = max(3, min(40, int(s.get("est_minutes", 12))))
            except (TypeError, ValueError):
                s["est_minutes"] = 12
            for key in ("subheadings", "formulae", "derivations", "solved_examples",
                        "key_terms", "misconceptions", "diagrams", "historical_facts"):
                if not isinstance(s.get(key), list):
                    s[key] = []
            s["has_derivation"] = bool(s.get("has_derivation")) or bool(s["derivations"])
            sections.append(s)

        if not sections:
            return None
        if data.get("excluded_parts"):
            print(f"         · excluded: {', '.join(map(str, data['excluded_parts']))[:200]}")
        return {"sections": sections}

    # ==================================================================
    # CALL 0b — DAY ALLOCATOR  (+ validation, repair, fallback)
    # ==================================================================

    def _call_day_allocator(self, run: dict) -> Optional[List[dict]]:
        sections = run["sections"]
        meta = PHYSICS_STRUCTURE_META
        compact = [{
            "id": s["id"], "number": s["number"], "heading": s["heading"],
            "content_type": s["content_type"], "est_minutes": s["est_minutes"],
            "has_derivation": s["has_derivation"],
            "solved_examples": len(s["solved_examples"]),
        } for s in sections]
        total_minutes = sum(s["est_minutes"] for s in sections)
        day_types = "\n".join(
            f'  "{k}": {v["allocator_hint"]}' for k, v in PHYSICS_DAY_TYPES.items()
        )

        prompt = f"""You are the DAY ALLOCATOR for a Samacheer Kalvi Physics lesson plan.

Chapter: {run['title']} (Class {run['class_num']}, Unit {run['unit']})
Chapter length: {len(run['text'])} characters. Estimated teaching minutes: {total_minutes}.
Each day is 35 minutes, with about {meta['content_minutes_per_day']} minutes for new teaching.

PACING RULE (from the teacher-approved manual LP):
{meta['pacing_rule']}

RULES:
- Decide total_days yourself. It INCLUDES one final revision day.
  total_days must be between {meta['min_days']} and {meta['max_days']}.
- Days 1..total_days-1 are content days. Every section id below must appear in
  EXACTLY ONE content day — no omissions, no duplicates.
- Keep strict textbook order: a later section never comes before an earlier one.
- The LAST day is revision: "section_ids": [] and "day_type": "revision".
- day_type for each content day — exactly one of:
{day_types}
  Choose by what the day mainly teaches. A day with a textbook derivation is
  "derivation" unless the derivation is trivial.
- title: short day title built ONLY from THIS day's own section headings
  (never mention a topic that belongs to another day).
- focus: one sentence — the day's main outcome.
- learning_objectives: 3-4 items, each starting with an action verb
  (State, Explain, Derive, Calculate, Distinguish, Apply, Predict).

Return ONLY valid JSON, starting with {{ — no prose, no code fences:

{{
  "total_days": 6,
  "days": {{
    "1": {{"title": "...", "section_ids": ["S1", "S2"], "day_type": "concept",
           "focus": "...", "learning_objectives": ["...", "...", "..."]}},
    "2": {{ ... }},
    "6": {{"title": "Whole-Chapter Revision + Exam Practice", "section_ids": [],
           "day_type": "revision", "focus": "Revision and exam practice",
           "learning_objectives": []}}
  }}
}}

Sections (in textbook order):
{json.dumps(compact, ensure_ascii=False, indent=1)}
"""
        system = ("You are a strict day allocator. Return ONLY valid JSON. No markdown, "
                  "no code fences. Raw JSON starting with {")

        plan = self._call_json(system, prompt, MAX_TOKENS_ALLOCATOR, "Day Allocator")
        days = self._validate_plan(plan, run) if plan else None
        if not days:
            print("         ⚠️ Using deterministic fallback allocation")
            days = self._fallback_allocation(run)
        return days

    def _validate_plan(self, plan: dict, run: dict) -> Optional[List[dict]]:
        """
        Turn allocator JSON into an ordered list of CONTENT days and repair:
        unknown ids, duplicates, omissions, ordering, empty days, day count,
        day types. Returns None if the plan is unusable.
        """
        sections, idx = run["sections"], run["section_index"]
        raw_days = plan.get("days") if isinstance(plan, dict) else None
        if not isinstance(raw_days, dict) or not raw_days:
            return None

        def _num(k):
            try:
                return int(str(k).strip().lower().replace("day", ""))
            except ValueError:
                return 10**6

        days: List[dict] = []
        seen = set()
        for key in sorted(raw_days.keys(), key=_num):
            d = raw_days[key] if isinstance(raw_days[key], dict) else {}
            ids = [str(x).strip() for x in (d.get("section_ids") or [])]
            ids = [i for i in ids if i in idx and i not in seen]
            seen.update(ids)
            if not ids:          # revision day or empty day — dropped here
                continue
            days.append({
                "section_ids": sorted(ids, key=lambda i: idx[i]),
                "title": str(d.get("title", "")).strip(),
                "day_type": str(d.get("day_type", "")).strip(),
                "focus": str(d.get("focus", "")).strip(),
                "learning_objectives": [str(x).strip() for x in (d.get("learning_objectives") or [])
                                        if str(x).strip()][:4],
            })
        if not days:
            return None

        # Omissions → put each missing section into the day of its predecessor
        missing = [s["id"] for s in sections if s["id"] not in seen]
        if missing:
            print(f"         ⚠️ Allocator omitted {len(missing)} section(s) — placing them")
            for sid in missing:
                pos = idx[sid]
                target = days[0]
                for d in days:
                    if any(idx[i] < pos for i in d["section_ids"]):
                        target = d
                target["section_ids"] = sorted(target["section_ids"] + [sid], key=lambda i: idx[i])

        # Textbook order across days
        days.sort(key=lambda d: idx[d["section_ids"][0]])

        # Day-count bounds (content days = total - 1)
        max_content = PHYSICS_STRUCTURE_META["max_days"] - 1
        if len(days) > max_content:
            print(f"         ⚠️ {len(days)} content days > {max_content} — merging lightest neighbours")
            while len(days) > max_content:
                mins = [self._day_minutes(run, d) for d in days]
                j = min(range(len(days) - 1), key=lambda k: mins[k] + mins[k + 1])
                a, b = days[j], days[j + 1]
                a["section_ids"] += b["section_ids"]
                a["title"] = f"{a['title']} + {b['title']}".strip(" +")
                a["learning_objectives"] = (a["learning_objectives"] + b["learning_objectives"])[:4]
                del days[j + 1]

        # Fill gaps in each day's metadata
        for d in days:
            if not d["title"]:
                d["title"] = " + ".join(sections[idx[i]]["heading"] for i in d["section_ids"])
            raw_type = d["day_type"].strip().lower().replace(" ", "_").replace("-", "_")
            if raw_type in PHYSICS_DAY_TYPES or raw_type in DAY_TYPE_ALIASES:
                d["day_type"] = normalize_day_type(raw_type)
            else:                                   # missing / "revision" / unknown
                d["day_type"] = self._infer_day_type(run, d)
            if not d["focus"]:
                d["focus"] = d["title"]
        return days

    def _day_minutes(self, run: dict, day: dict) -> int:
        idx, sections = run["section_index"], run["sections"]
        return sum(sections[idx[i]]["est_minutes"] for i in day["section_ids"])

    def _infer_day_type(self, run: dict, day: dict) -> str:
        idx, sections = run["section_index"], run["sections"]
        secs = [sections[idx[i]] for i in day["section_ids"]]
        if any(s["has_derivation"] for s in secs):
            return "derivation"
        if any(s["solved_examples"] for s in secs):
            return "formula_numerical"
        counts: Dict[str, int] = {}
        for s in secs:
            counts[s["content_type"]] = counts.get(s["content_type"], 0) + s["est_minutes"]
        return max(counts, key=counts.get) if counts else "concept"

    def _fallback_allocation(self, run: dict) -> Optional[List[dict]]:
        """Pack sections in order into days of ~content_minutes_per_day."""
        sections = run["sections"]
        if not sections:
            return None
        budget = PHYSICS_STRUCTURE_META["content_minutes_per_day"]
        max_content = PHYSICS_STRUCTURE_META["max_days"] - 1

        def pack(limit: int) -> List[List[dict]]:
            groups, cur, cur_min = [], [], 0
            for s in sections:
                heavy = s["est_minutes"] >= limit * 0.8
                if cur and (heavy or cur_min + s["est_minutes"] > limit):
                    groups.append(cur)
                    cur, cur_min = [], 0
                cur.append(s)
                cur_min += s["est_minutes"]
            if cur:
                groups.append(cur)
            return groups

        groups = pack(budget)
        while len(groups) > max_content:
            budget += 5
            groups = pack(budget)

        days = []
        for g in groups:
            d = {
                "section_ids": [s["id"] for s in g],
                "title": " + ".join(s["heading"] for s in g),
                "day_type": "",
                "focus": "",
                "learning_objectives": [],
            }
            d["day_type"] = self._infer_day_type(run, d)
            d["focus"] = d["title"]
            days.append(d)
        return days

    def _build_day_records(self, run: dict, content_days: List[dict]) -> List[dict]:
        """Attach section data, textbook reference and teaching strategy per day."""
        idx, sections = run["section_index"], run["sections"]
        occurrences: Dict[str, int] = {}
        records = []
        for n, d in enumerate(content_days, start=1):
            secs = [sections[idx[i]] for i in d["section_ids"]]
            dtype = normalize_day_type(d["day_type"])
            strategy = get_day_strategy(dtype, occurrences.get(dtype, 0))
            occurrences[dtype] = occurrences.get(dtype, 0) + 1
            records.append({
                "num": n,
                "title": d["title"],
                "focus": d["focus"],
                "learning_objectives": d["learning_objectives"],
                "sections": secs,
                "reference": "; ".join(
                    f"{s['number']} {s['heading']}".strip() for s in secs
                ),
                "strategy": strategy,
            })
        return records

    # ==================================================================
    # CALL 1 — PREAMBLE (model text + Python-built tables)
    # ==================================================================

    def _call_preamble(self, run: dict) -> Optional[str]:
        total = run["total_days"]
        day_lines = "\n".join(
            f"  Day {d['num']}: {d['title']} — {d['focus']} ({d['reference']})"
            for d in run["days"]
        ) + f"\n  Day {total}: {PHYSICS_REVISION_DAY_STRATEGY['title']}"
        diagrams = sorted({dg for s in run["sections"] for dg in s["diagrams"] if dg})[:25]
        avoid = "\n".join(f"  - {a}" for a in PHYSICS_STRUCTURE_META["avoid"])
        instead = "\n".join(f"  - {a}" for a in PHYSICS_STRUCTURE_META["instead"])

        prompt = f"""Generate ONLY the preamble of this Physics Lesson Plan.
Do NOT generate any Day blocks.

Chapter    : {run['title']}
Class      : {run['class_num']}
Unit       : {run['unit']}
Subject    : Physics
Duration   : {total} Days × 35 Minutes = {total * 35} Minutes
             ({total - 1} teaching days + 1 revision day, followed by a graded assessment)

DAY-WISE PLAN (already decided from the chapter text):
{day_lines}

DIAGRAMS MENTIONED IN THE CHAPTER (for Teaching Aids — do not invent others):
{chr(10).join('  - ' + d for d in diagrams) or '  (none extracted)'}

TEACHER SHOULD NOT:
{avoid}
INSTEAD:
{instead}

{PREAMBLE_START_INSTRUCTION}

WRITE THESE PARTS — and put the three placeholders EXACTLY where shown.
Python fills the placeholders with tables built from the chapter data.

<h2>Part 1: Chapter Overview</h2>
  <div class="vocab-block"> table with 2 columns (Item | Details):
  Class, Subject, Unit and Chapter Title ("Unit {run['unit']}: {run['title']}"),
  Total Days, Session Duration, Main Topics Covered (short).

<h2>Part 2: Learning Objectives</h2>
  4-6 chapter-level objectives, action verbs, traceable to the day-wise plan.

<h2>Part 3: Value-Based Objectives</h2>
  3-4, each grounded in a REAL idea from this chapter (safety, scientific
  thinking, everyday technology, careful measurement) — never generic.

<h2>Part 4: Skill Objectives</h2>
  3-4, each naming a real skill practised in this chapter (drawing diagrams,
  vector direction, five-step numericals, deriving expressions, unit conversion).

<!--PART5-->

<h2>Part 6: Teaching Approach for This Chapter</h2>
  - 2-3 sentences: physics stays at full level; the language and route change.
  - The teaching cycle: Familiar experience → simple English → Tamil →
    scientific English → board diagram / formula → guided practice.
  - Name this chapter's likely difficulty points (look-alike terms, vectors,
    multi-symbol formulas) in 2-3 bullets.
  - "The teacher should NOT" list and "Instead" list (use the lists above).
  - One sentence explaining CCQ (checks one idea as it is taught) vs CFU
    (checks the whole block before moving on).

<!--PART7-->

<!--PART8-->

<h2>Part 9: Teaching Aids</h2>
  Board, chalk, chart paper for the diagrams above, simple everyday objects
  relevant to this chapter, textbook, notebooks. No page numbers.

OUTPUT RULES:
- Raw HTML only. First tag must be <h2>Part 1: Chapter Overview</h2>
- Keep the three placeholder comments exactly as written
- Stop after Part 9

Chapter text (opening part, for tone and context only):
---
{run['text'][:4000]}
---"""
        raw, stop = self._call(PHYS_LP_SYSTEM_PROMPT, prompt, MAX_TOKENS_PREAMBLE, "Preamble")
        if not raw:
            return None
        html = clean(raw)
        html = self._inject_preamble_tables(run, html)
        return normalize_preamble_html(html)

    def _inject_preamble_tables(self, run: dict, html: str) -> str:
        tables = {
            "<!--PART5-->": self._html_day_plan(run),
            "<!--PART7-->": self._html_tamil_sheet(run),
            "<!--PART8-->": self._html_formula_wall(run),
        }
        missing = []
        for marker, table in tables.items():
            # BeautifulSoup keeps comments; tolerate spaces inside the marker
            num = re.search(r"\d+", marker).group(0)
            pat = re.compile(r"<!--\s*PART\s*" + num + r"\s*-->", re.IGNORECASE)
            if pat.search(html):
                html = pat.sub(lambda _m, t=table: t, html, count=1)
            else:
                missing.append(table)
        if missing:
            block = "\n".join(missing)
            m = re.search(r"<h2[^>]*>\s*Part\s*9", html, re.IGNORECASE)
            html = html[:m.start()] + block + "\n" + html[m.start():] if m else html + "\n" + block
        return html

    # ---------- Python-built preamble tables (deterministic) ----------

    @staticmethod
    def _esc(s: Any) -> str:
        return html_lib.escape(str(s or ""), quote=False)

    @staticmethod
    def _safe_inline_html(s: Any) -> str:
        """Allow only <sup>, <sub>, <strong>, <em>, <b>, <i>, <br/> from extractor data."""
        text = html_lib.escape(html_lib.unescape(str(s or "")), quote=False)
        text = re.sub(r"&lt;(/?)(sup|sub|strong|em|b|i)&gt;", r"<\1\2>", text, flags=re.IGNORECASE)
        text = re.sub(r"&lt;br\s*/?&gt;", "<br/>", text, flags=re.IGNORECASE)
        return text

    def _html_day_plan(self, run: dict) -> str:
        rows = "".join(
            f"<tr><td>{d['num']}</td><td>{self._esc(d['title'])}</td>"
            f"<td>{self._esc(d['focus'])}</td></tr>"
            for d in run["days"]
        )
        rows += (f"<tr><td>{run['total_days']}</td>"
                 f"<td>{self._esc(PHYSICS_REVISION_DAY_STRATEGY['title'])}</td>"
                 f"<td>Formula recall, exam practice and graded assessment</td></tr>")
        return ("<h2>Part 5: Day-wise Plan</h2>\n<div class=\"vocab-block\">\n<table>"
                "<thead><tr><th>Day</th><th>Topic</th><th>Main outcome</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>\n</div>")

    def _html_tamil_sheet(self, run: dict) -> str:
        seen, rows = set(), []
        for s in run["sections"]:
            for t in s["key_terms"]:
                if not isinstance(t, dict):
                    continue
                eng = str(t.get("english", "")).strip()
                if not eng or eng.lower() in seen:
                    continue
                seen.add(eng.lower())
                rows.append(f"<tr><td>{self._esc(eng)}</td>"
                            f"<td>{self._esc(t.get('simple_english', ''))}</td>"
                            f"<td>{self._esc(t.get('tamil', ''))}</td></tr>")
                if len(rows) >= MAX_TAMIL_SHEET_ROWS:
                    break
            if len(rows) >= MAX_TAMIL_SHEET_ROWS:
                break
        if not rows:
            return ""
        return ("<h2>Part 7: Teacher's Tamil Scaffolding Sheet</h2>\n"
                "<p><em>Keep this beside the textbook.</em></p>\n<div class=\"vocab-block\">\n<table>"
                "<thead><tr><th>English</th><th>Simple English</th><th>Tamil support</th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table>\n</div>")

    def _all_formulae(self, run: dict) -> List[dict]:
        seen, out = set(), []
        for s in run["sections"]:
            for f in s["formulae"]:
                if not isinstance(f, dict):
                    continue
                expr = str(f.get("expression_html", "")).strip()
                key = re.sub(r"\s+", "", expr).lower()
                if not expr or key in seen:
                    continue
                seen.add(key)
                out.append({
                    "name": str(f.get("name", "")).strip() or s["heading"],
                    "expression_html": expr,
                    "si_unit": str(f.get("si_unit", "")).strip(),
                    "reconstructed": bool(f.get("reconstructed")),
                    "section": s["number"],
                })
        return out[:MAX_FORMULA_ROWS]

    def _html_formula_wall(self, run: dict) -> str:
        formulae = self._all_formulae(run)
        if not formulae:
            return ""
        rows = "".join(
            f"<tr><td>{self._esc(f['name'])}</td>"
            f"<td>{self._safe_inline_html(f['expression_html'])}"
            f"{' ⚠️ verify' if f['reconstructed'] else ''}</td>"
            f"<td>{self._safe_inline_html(f['si_unit'])}</td></tr>"
            for f in formulae
        )
        note = ("<p><em>⚠️ verify = formula reconstructed from a garbled extraction; "
                "check it against the textbook.</em></p>\n"
                if any(f["reconstructed"] for f in formulae) else "")
        return ("<h2>Part 8: Formula Wall</h2>\n"
                "<p><em>Put this on the classroom wall. Tell students: first know what "
                "every symbol means, and which situation each formula answers.</em></p>\n"
                f"{note}<div class=\"vocab-block\">\n<table>"
                "<thead><tr><th>Quantity / Law</th><th>Formula</th><th>SI unit</th></tr></thead>"
                f"<tbody>{rows}</tbody></table>\n</div>")

    # ==================================================================
    # CONTENT DAYS
    # ==================================================================

    def _generate_day(self, run: dict, day: dict) -> Optional[str]:
        prompt = self._build_day_prompt(run, day)
        return self._day_with_retry(prompt, day["num"], is_revision=False)

    def _generate_revision_day(self, run: dict) -> Optional[str]:
        prompt = self._build_revision_prompt(run)
        return self._day_with_retry(prompt, run["total_days"], is_revision=True)

    def _day_system_prompt(self) -> str:
        return "\n".join([
            PHYS_LP_SYSTEM_PROMPT, TAMIL_INSTRUCTION, CCQ_CFU_INSTRUCTION,
            NUMERICAL_ROUTINE_INSTRUCTION, DERIVATION_INSTRUCTION,
            COMMON_MISTAKES_INSTRUCTION,
        ])

    def _day_with_retry(self, prompt: str, day_num: int,
                        is_revision: bool) -> Optional[str]:
        """
        One retry for content problems (truncation / missing structure).
        Keeps the best attempt so a weak-but-usable day is never thrown away.
        """
        system = self._day_system_prompt()
        best: Optional[str] = None
        best_truncated = False
        feedback = ""
        for attempt in (1, 2):
            raw, stop = self._call(system, prompt + feedback, MAX_TOKENS_DAY,
                                   f"Day {day_num} #{attempt}")
            if not raw or not raw.strip():
                continue
            html = normalize_day_html(clean(raw))
            truncated = stop == "max_tokens"
            problems = check_day_structure(html, is_revision_day=is_revision)

            if best is None or (not truncated and not is_critical(problems)):
                best, best_truncated = html, truncated

            if not truncated and not is_critical(problems):
                if problems:
                    print(f"         ⚠️ Day {day_num} minor issues: {'; '.join(problems)}")
                print(f"         ✅ Day {day_num} ({len(html)} chars)")
                return html

            if attempt == 1:
                if truncated:
                    print(f"         ⚠️ Day {day_num} cut off — retrying with a tighter brief")
                    feedback = ("\n\nIMPORTANT: Your previous answer was CUT OFF before the "
                                "closing section. Write more concisely: shorter teacher "
                                "scripts, at most 2 CCQs per block, and make sure the "
                                "closing section with the Exit Ticket is complete.")
                else:
                    print(f"         ⚠️ Day {day_num} structure problems: {'; '.join(problems)} — retrying")
                    feedback = ("\n\nIMPORTANT: Your previous answer was missing: "
                                + "; ".join(problems)
                                + ". Follow the HTML structure exactly, including all five "
                                  "lp-section-* blocks and the Exit Ticket.")

        if best is None:
            return None
        if best_truncated:
            print(f"         ⚠️ Day {day_num} still cut off — keeping it with LP_DAY_TRUNCATED marker")
            best = mark_truncated(best)
        else:
            print(f"         ⚠️ Day {day_num} kept with structure problems after retry")
        return best

    # ---------- per-day data helpers ----------

    def _day_data_block(self, day: dict) -> str:
        lines = []
        for s in day["sections"]:
            lines.append(f"■ {s['number']} {s['heading']}  (≈{s['est_minutes']} min, "
                         f"{s['content_type']})")
            if s["subheadings"]:
                lines.append("  Sub-headings (teach ALL, in order): " +
                             "; ".join(map(str, s["subheadings"])))
            for f in s["formulae"]:
                if isinstance(f, dict):
                    lines.append(f"  Formula: {f.get('name', '')}: {f.get('expression_html', '')}"
                                 f" [{f.get('si_unit', '')}]"
                                 f"{'  (RECONSTRUCTED — add the ⚠️ verify line)' if f.get('reconstructed') else ''}")
            for x in s["derivations"]:
                lines.append(f"  Derivation in text: {x}")
            for x in s["solved_examples"]:
                lines.append(f"  Textbook solved example (use these numbers exactly): {x}")
            for t in s["key_terms"]:
                if isinstance(t, dict):
                    lines.append(f"  Key term: {t.get('english', '')} — {t.get('simple_english', '')}"
                                 f" — {t.get('tamil', '')}")
            for x in s["misconceptions"]:
                lines.append(f"  Common misconception: {x}")
            for x in s["diagrams"]:
                lines.append(f"  Diagram: {x}")
            for x in s["historical_facts"]:
                lines.append(f"  Historical fact in text: {x}")
        return "\n".join(lines)

    def _day_text_slice(self, run: dict, day: dict) -> Tuple[str, bool]:
        """
        Text for today's sections only (keeps the model on-topic and cuts cost).
        Falls back to the full chapter if headings cannot be located reliably.
        Returns (text, is_full_chapter).
        """
        text = run["text"]
        positions = run.get("_section_positions")
        if positions is None:
            positions = self._locate_sections(text, run["sections"])
            run["_section_positions"] = positions

        ids = [s["id"] for s in day["sections"]]
        if all(positions.get(i) is None for i in positions):
            if not run.get("_text_dumped"):
                run["_text_dumped"] = True
                try:   # debug aid: the exact text the builder received
                    dump = f"/tmp/physics_lp_text_unit{run.get('unit', 'x')}.txt"
                    with open(dump, "w", encoding="utf-8") as fh:
                        fh.write(text)
                    print(f"         · text slicing failed — chapter text saved to {dump}")
                except OSError:
                    pass
            return text, True

        idx = run["section_index"]
        first_idx, last_idx = idx[ids[0]], idx[ids[-1]]

        # Start: today's first heading; if it wasn't located, widen back to the
        # nearest earlier heading that was (a little extra text, nothing missing)
        start = positions.get(ids[0])
        if start is None:
            start = 0
            for s in reversed(run["sections"][:first_idx]):
                if positions.get(s["id"]) is not None:
                    start = positions[s["id"]]
                    break

        # End: the next located heading after today's last section
        end = len(text)
        for s in run["sections"][last_idx + 1:]:
            p = positions.get(s["id"])
            if p is not None and p > start:
                end = p
                break
        chunk = text[start:end]
        if len(chunk) < DAY_TEXT_MIN_CHARS:
            return text, True
        return chunk[:DAY_TEXT_MAX_CHARS], False

    @staticmethod
    def _norm_heading(s: str) -> str:
        """Lower-case, straighten quotes, drop leading numbering and punctuation."""
        s = (s or "").lower()
        s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
        # Section-number prefixes: "1.2.1 ", "1.2) " and the EPUB's spoken form
        # "1 point 9 point 3 " (screen-reader text for 1.9.3)
        s = re.sub(r"^\s*\d+(?:\s*(?:\.|point)\s*\d+)*\s*[.:)\-–]?\s*", "", s)
        s = re.sub(r"^[\s\d.:)\-–]+", "", s)
        s = s.replace("'", "")                        # coulomb's → coulombs
        s = re.sub(r"[^a-z0-9]+", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    @staticmethod
    def _normalize_with_map(text: str) -> Tuple[str, List[int]]:
        """
        Same normalization as _norm_heading (lower-case ASCII letters/digits,
        apostrophes dropped, everything else → single space), applied to the
        whole chapter, plus a map from each normalized char to its offset in
        the original text.
        """
        out: List[str] = []
        idx: List[int] = []
        prev_space = True
        for i, ch in enumerate(text):
            c = ch.lower()
            if c in "'’‘":
                continue
            if c.isascii() and c.isalnum():
                out.append(c)
                idx.append(i)
                prev_space = False
            elif not prev_space:
                out.append(" ")
                idx.append(i)
                prev_space = True
        return "".join(out), idx

    @classmethod
    def _locate_sections(cls, text: str, sections: List[dict]) -> Dict[str, Optional[int]]:
        """
        Find where each section heading starts in the chapter text.

        The preprocessor's text layout varies (headings may or may not sit on
        their own lines; section numbers may appear as "3.8.1", as the EPUB's
        spoken form "3 point 8 point 1", or not at all), so:
          1. candidates = EVERY occurrence of the normalized heading text,
             anywhere in the chapter
          2. each candidate gets a "heading-likeness" score:
               +3  this section's own number right before it (3.8.1 / 3 point 8 point 1)
               +2  some other section-style number right before it
               +1  a line break right before it,  +1 a line break right after it
             plain mentions inside body text score 0
          3. pick ONE candidate per section so positions strictly increase,
             maximizing (sections matched, total heading-likeness, well-
             separated gaps) — dynamic programming over the candidates
          4. give up (→ full chapter) if under half the sections are found, or
             if most matches are only plain mentions (not trustworthy)
        """
        norm, nmap = cls._normalize_with_map(text)
        n_text = len(text)
        number_tail = re.compile(r"\d+(?: (?:point )?\d+){1,3} ?$")

        def number_forms(num: str) -> List[str]:
            parts = re.findall(r"\d+", num or "")
            if len(parts) < 2:
                return []
            return [" ".join(parts), " point ".join(parts)]

        def line_break_before(orig: int) -> bool:
            j = orig - 1
            while j >= 0 and text[j] in " \t\r":
                j -= 1
            return j < 0 or text[j] == "\n"

        def line_break_after(orig_end: int) -> bool:
            j = orig_end
            while j < n_text and text[j] in " \t\r.:":
                j += 1
            return j >= n_text or text[j] == "\n"

        cands: List[Dict[int, int]] = []          # per section: {orig_pos: quality}
        for sec in sections:
            h = cls._norm_heading(sec["heading"])
            found: Dict[int, int] = {}
            if h:
                forms = number_forms(sec.get("number", ""))
                pat = re.compile(r"(?<![a-z0-9])" + re.escape(h) + r"(?![a-z0-9])")
                for m in pat.finditer(norm):
                    st, en = m.start(), m.end()
                    before = norm[max(0, st - 30):st].rstrip()
                    q = 0
                    if forms and any(before.endswith(f) for f in forms):
                        q += 3
                    elif number_tail.search(before + " "):
                        q += 2
                    orig_st, orig_en = nmap[st], nmap[en - 1] + 1
                    if line_break_before(orig_st):
                        q += 1
                    if line_break_after(orig_en):
                        q += 1
                    found[orig_st] = q
            # keep the most heading-like occurrences (bounded for speed)
            keep = sorted(found.items(), key=lambda kv: (-kv[1], kv[0]))[:25]
            cands.append(dict(keep))

        # DP: best chain ending at (section i, position p)
        #     score = (matched count, heading-likeness sum, well-separated gaps)
        GAP = 300
        best: List[Dict[int, Tuple[Tuple[int, int, int], Optional[Tuple[int, int]]]]] = []
        for i, cl in enumerate(cands):
            row: Dict[int, Tuple[Tuple[int, int, int], Optional[Tuple[int, int]]]] = {}
            for p, q in cl.items():
                score, back = (1, q, 0), None
                for j in range(i):
                    for prev, (sc, _) in best[j].items():
                        if prev < p:
                            cand = (sc[0] + 1, sc[1] + q, sc[2] + (1 if p - prev >= GAP else 0))
                            # ties → the LATER predecessor (body heading just
                            # before, not an early contents-list entry)
                            if cand > score or (cand == score and back is not None and prev > back[1]):
                                score, back = cand, (j, prev)
                row[p] = (score, back)
            best.append(row)

        end, end_score = None, (0, 0, 0)
        for i, row in enumerate(best):
            for p, (sc, _) in row.items():
                if sc > end_score:
                    end_score, end = sc, (i, p)

        positions: Dict[str, Optional[int]] = {s["id"]: None for s in sections}
        heading_like = 0
        node = end
        while node is not None:
            i, p = node
            positions[sections[i]["id"]] = p
            if cands[i].get(p, 0) > 0:
                heading_like += 1
            node = best[i][p][1]

        found = sum(1 for v in positions.values() if v is not None)
        if found < max(2, len(sections) // 2):
            print(f"         · text slicing: only {found}/{len(sections)} headings located "
                  f"— days will use the full chapter")
            return {k: None for k in positions}
        if heading_like < found / 2:
            print(f"         · text slicing: {found}/{len(sections)} matched but only "
                  f"{heading_like} look like headings — not trusted, days will use the full chapter")
            return {k: None for k in positions}
        print(f"         · text slicing: located {found}/{len(sections)} section headings "
              f"({heading_like} heading-like)")
        return positions

    # ---------- day prompt ----------

    def _build_day_prompt(self, run: dict, day: dict) -> str:
        n, total = day["num"], run["total_days"]
        st = day["strategy"]
        prev_day = run["days"][n - 2] if n > 1 else None
        # Built from the next day's own section headings (not the allocator's
        # free-text title, which once named another day's topic)
        next_title = (" + ".join(s["heading"] for s in run["days"][n]["sections"])
                      if n < len(run["days"]) else PHYSICS_REVISION_DAY_STRATEGY["title"])
        objectives = "\n".join(f"  - {o}" for o in day["learning_objectives"]) \
            or "  (write 3-4 objectives with action verbs from today's sections)"
        timing = "\n".join(f"  {t:<10} {cls:<26} {purpose}"
                           for cls, t, purpose in PHYSICS_DEFAULT_TIMING)
        has_numerical = any(s["solved_examples"] for s in day["sections"]) \
            or st["day_type"] == "formula_numerical"
        has_derivation = any(s["has_derivation"] for s in day["sections"])
        text_slice, is_full = self._day_text_slice(run, day)

        recall_line = (
            f'Day {n} is the FIRST day — no recall; go straight to the hook.'
            if prev_day is None else
            f'Start with a one-minute recall of Day {n - 1} ("{prev_day["title"]}") '
            f'— revisit yesterday\'s key formula or idea, then the hook.'
        )

        return f"""You are writing Day {n} of {total} of a Samacheer Kalvi Physics Lesson Plan.

Chapter : Unit {run['unit']}: {run['title']}  (Class {run['class_num']})
Day     : {n} of {total}  (Day {total} is whole-chapter revision)
Duration: 35 minutes

═══════════════════════════════════════════════════════
TODAY'S CONTENT (discovered from THIS chapter's text)
═══════════════════════════════════════════════════════
Day title : {day['title']}
Textbook  : {day['reference']}
Focus     : {day['focus']}
Learning objectives:
{objectives}

{self._day_data_block(day)}

Teach EVERY section and sub-heading listed above, in order. Do NOT teach
sections that belong to other days. Do NOT add outside topics.

═══════════════════════════════════════════════════════
TODAY'S TEACHING TECHNIQUE (fixed by day type — {st['day_type_label']})
═══════════════════════════════════════════════════════
Opening style   : {st['opening_style']}
Opening         : {recall_line}
                  {st['opening_instruction']}
Main teaching   : {st['main_focus']}
Activity style  : {st['activity_style']}
Activity        : {st['activity_instruction']}
Exit ticket     : {st['exit_ticket_style']}
{"Numerical day  : model the five-step routine in a worked example (use the textbook's solved example if listed above)." if has_numerical else ""}
{"Derivation day : follow the DERIVATION rules — numbered steps in board-work, reasons in teacher script, result in formula-box." if has_derivation else ""}

DEFAULT TIMING (resize blocks if a topic needs more board time):
{timing}

TIME LABELS — STRICT:
- Every lp-time label is a range "A–B min". Labels appear in order and are
  CONTIGUOUS: the opening starts at 0, each label starts exactly where the
  previous one ended, and the closing ends at 35. No gaps, no overlaps.
  ✅ 0–5, 5–12, 12–18, 18–24, 24–31, 31–35      ❌ ...13–20 then 23–30 (gap)
- If the main section gets more minutes, the student task and closing start
  later — move their labels; never squeeze them out.

REALISTIC PACING — A NEW TEACHER MUST BE ABLE TO DELIVER THIS IN 35 MINUTES:
- A teacher speaks about 120 words a minute. Each block's teacher script and
  board work must fit inside that block's minutes.
- Fully work AT MOST TWO examples in the whole day: one modelled by the
  teacher (main section) and one solved by students (student task).
  Any other textbook solved examples: do NOT solve them in class — list them in
  the closing as "Also practise from the textbook: Example x.y" for students.
- At most ONE long derivation is written out in full in class. If today has a
  second long derivation, derive its key steps on the board, and keep the
  student task to one short activity with no extra numerical.
- Prefer depth on the core idea over covering side remarks. Every listed
  section and sub-heading is still TAUGHT — but side points get one or two
  sentences, not a full block.

═══════════════════════════════════════════════════════
GENERATE Day {n} using EXACTLY this HTML structure
═══════════════════════════════════════════════════════

<div class="lp-day-block">
<h3 class="lp-day-title">Day {n} of {total} — {self._esc(day['title'])}</h3>
<p class="lp-day-meta">Textbook: {self._esc(day['reference'])} | Day type: {st['day_type_label']} | Technique: {st['activity_style']}</p>
<p><strong>Learning objectives</strong></p>
<ul>[3-4 objectives]</ul>

<div class="lp-section-opening">
  <p class="lp-section-label">Opening — {st['opening_style']}</p>
  <span class="lp-time">0–[A] min</span>
  <div class="lp-teacher-says">[recall line if Day 2+, then the hook question — exact words the teacher says]</div>
  <div class="lp-tamil-scaffold"><strong>தமிழில்:</strong> [the hook question in code-mixed Tamil]</div>
  [cfu-block — whole-class check on the hook]
</div>

<div class="lp-section-intro">
  <p class="lp-section-label">Introduction — [first idea of today]</p>
  <span class="lp-time">[A]–[B] min</span>
  <div class="lp-teacher-says">[familiar experience → simple English explanation]</div>
  [formula-box with the key statement or law]
  <div class="lp-tamil-scaffold"><strong>தமிழில்:</strong> [one code-mixed Tamil line]</div>
  [1-3 ccq-block]
  [cfu-block]
</div>

<div class="lp-section-main">
  <p class="lp-section-label">Main Teaching — Board Work</p>
  [ONE OR MORE teaching blocks, one per remaining idea / sub-heading, each:]
  <h4><span class="lp-time">[B]–[C] min</span> [sub-topic name]</h4>   (next block starts at [C], and so on)
  <div class="lp-teacher-says">[explanation in simple English, then scientific English]</div>
  [board-work: diagram description / derivation steps / worked example (five steps)]
  [formula-box for each key formula]
  <div class="lp-tamil-scaffold"><strong>தமிழில்:</strong> [one code-mixed Tamil line]</div>
  [1-3 ccq-block]
  [common-mistakes box where the misconception fits]
  [cfu-block]
</div>

<div class="lp-section-student-task">
  <p class="lp-section-label">Student Task — {st['activity_style']}</p>
  <span class="lp-time">[D]–[E] min</span>   ([D] = where the last main block ended)
  <div class="lp-teacher-says">[exact instructions to students, grounded in today's content]</div>
  [board-work with the task items / numerical; give the expected answers for the teacher]
  [cfu-block]
</div>

<div class="lp-section-closing">
  <p class="lp-section-label">Closing</p>
  <span class="lp-time">[E]–35 min</span>
  <div class="lp-teacher-says"><strong>Exam-oriented question:</strong> [one exam-style question on today's content]<br/><strong>Model answer:</strong> [short model answer in exam English]</div>
  [cfu-block]
  <div class="board-work"><strong>Exit Ticket:</strong><br/>[{st['exit_ticket_style']} — on today's content; include the answers in brackets for the teacher]</div>
  [if other textbook solved examples exist for today: <p><strong>Also practise from the textbook:</strong> Example x.y, ...</p>]
  <p><em>Next lesson: {self._esc(next_title)}</em></p>
</div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ Output starts with <div class="lp-day-block"> and ends with its </div>
✅ Title is INSIDE the day block; no id or data-* attributes anywhere
✅ All five lp-section-* blocks present, in order, each closed before the next
✅ Every section and sub-heading listed in TODAY'S CONTENT is taught
✅ CCQs right after each new idea; exactly one CFU at the end of every block
✅ One code-mixed Tamil line per teaching block + the Tamil hook — none in CCQ/CFU/activity/exit ticket
✅ At least one common-mistakes box
✅ Formulas in plain HTML (<sup>/<sub>/Unicode) — no LaTeX
✅ Textbook numbers used exactly; practice-problem answers calculated correctly with units
✅ Time labels run 0 → 35 with no gaps or overlaps (each starts where the previous ended)
✅ Pacing is realistic: at most 2 fully worked examples, at most 1 full long derivation
✅ Exit Ticket present; NO homework
✅ No page numbers, no student names, no religious references
✅ Do NOT generate Day {n + 1}

{"FULL CHAPTER TEXT (teach ONLY today's sections listed above):" if is_full else "TEXTBOOK TEXT FOR TODAY'S SECTIONS (use ONLY this — no general knowledge):"}
---
{text_slice}
---"""

    # ---------- revision day prompt ----------

    def _build_revision_prompt(self, run: dict) -> str:
        total = run["total_days"]
        day_list = "\n".join(f"  Day {d['num']}: {d['title']} ({d['reference']})" for d in run["days"])
        formula_names = "\n".join(
            f"  - {f['name']}: {f['expression_html']}" for f in self._all_formulae(run)
        ) or "  (none extracted — use the formulae taught in the days above)"
        blocks = "\n".join(
            f"  {cls} | {t} | {name}: {instr}"
            for cls, t, name, instr in PHYSICS_REVISION_DAY_STRATEGY["blocks"]
        )
        rules = "\n".join(f"  - {r}" for r in PHYSICS_REVISION_DAY_STRATEGY["rules"])

        section_html = ""
        for cls, t, name, _ in PHYSICS_REVISION_DAY_STRATEGY["blocks"]:
            section_html += f"""
<div class="{cls}">
  <p class="lp-section-label">{name}</p>
  <span class="lp-time">{t}</span>
  <div class="lp-teacher-says">[exact teacher instructions for this block]</div>
  [board-work with the items, plus the answers for the teacher]
  [cfu-block]
</div>
"""
        return f"""You are writing Day {total} of {total} — the FINAL day — of a Samacheer Kalvi
Physics Lesson Plan. This day is WHOLE-CHAPTER REVISION. NO new content.

Chapter : Unit {run['unit']}: {run['title']}  (Class {run['class_num']})

DAYS ALREADY TAUGHT:
{day_list}

CHAPTER FORMULAE:
{formula_names}

REVISION BLOCKS (from the teacher-approved manual LP):
{blocks}

RULES:
{rules}
- The closing block's "I can..." checklist must contain the words "Exit Ticket".
- The graded assessment is a SEPARATE tab — do NOT write it here.

GENERATE using EXACTLY this HTML structure:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {total} of {total} — {PHYSICS_REVISION_DAY_STRATEGY['title']}</h3>
<p class="lp-day-meta">Textbook: Summary and Evaluation | Day type: Revision | No new content</p>
<p><strong>Learning objectives</strong></p>
<ul>[3 revision objectives]</ul>
{section_html}
</div>

In the closing block, write the checklist inside:
<div class="board-work"><strong>Exit Ticket — "I can..." checklist:</strong><br/>☐ I can ...<br/>...<br/>The topic I most need to practise is ______.</div>

Raw HTML only. Start with <div class="lp-day-block">. Do NOT use the class assessment-block.

Chapter text (reference for accuracy):
---
{run['text'][:DAY_TEXT_MAX_CHARS]}
---"""

    # ==================================================================
    # ASSESSMENT — separate top-level block (gets the 📋 Assessment tab)
    # ==================================================================

    def _call_assessment(self, run: dict) -> Optional[str]:
        a = PHYSICS_ASSESSMENT_STRUCTURE
        sections_spec = "\n".join(
            f"  {label}: {n} questions × {m} mark{'s' if m > 1 else ''} — {g}"
            for label, m, n, g in a["sections"]
        )
        total_marks = sum(m * n for _, m, n, _ in a["sections"])
        day_list = "\n".join(f"  Day {d['num']}: {d['title']} ({d['reference']})" for d in run["days"])
        derivations = sorted({x for s in run["sections"] for x in s["derivations"] if x})
        formulae = "\n".join(f"  - {f['name']}: {f['expression_html']}" for f in self._all_formulae(run))

        section_html = "\n".join(
            f'  <h3>{label} — {m} mark{"s" if m > 1 else ""} each</h3>\n'
            f'  <ol>[{n} questions]</ol>'
            for label, m, n, _ in a["sections"]
        )
        levels = a["differentiated_levels"]

        prompt = f"""Generate ONLY the graded Assessment for this Physics chapter.
It appears in its own "📋 Assessment" tab after the last day.

Chapter : Unit {run['unit']}: {run['title']}  (Class {run['class_num']})
Total   : {total_marks} marks

DAYS TAUGHT (questions must cover the whole chapter, not just the end):
{day_list}

DERIVATIONS IN THE CHAPTER: {', '.join(derivations) or '(none extracted)'}
FORMULAE:
{formulae or '  (use the chapter text)'}

QUESTION PAPER:
{sections_spec}
- Include at least one numerical in Section C (solved with the five-step routine in the answer key).
- Section D: one derivation from the list above (if any) + one detailed explanation.
- Every question must come from THIS chapter's content.

GENERATE using EXACTLY this HTML structure:

<div class="assessment-block">
  <h2>Assessment — Unit {run['unit']}: {self._esc(run['title'])}</h2>
  <p><strong>Total: {total_marks} marks</strong> | Covers all {run['total_days'] - 1} teaching days</p>
{section_html}

  <h3>Answer Key (for the teacher)</h3>
  [numbered answers matching the questions; numericals as five steps:
   Given / Find / Formula / Substitute / Answer with unit; derivations as
   numbered key steps]

  <h3>Marking Guide for Numericals</h3>
  <div class="board-work">{a['numerical_marking']}</div>

  <h3>Differentiated Practice</h3>
  <div class="diff-block">
    <table class="diff-table">
      <thead><tr><th>{levels[0]}</th><th>{levels[1]}</th><th>{levels[2]}</th></tr></thead>
      <tbody><tr>
        <td>[2 supported tasks — fill blanks with word bank, one-step calculation]</td>
        <td>[2 standard tasks — short answer + two-step numerical]</td>
        <td>[2 stretch tasks — multi-step numerical / derivation / reasoning]</td>
      </tr></tbody>
    </table>
  </div>
</div>

RULES:
- Raw HTML only. Start with <div class="assessment-block">
- Formulas in plain HTML (<sup>/<sub>/Unicode) — no LaTeX
- No Tamil, no page numbers, no student names
- Do NOT use the class lp-day-block

Chapter text (use ONLY this — no general knowledge):
---
{run['text'][:DAY_TEXT_MAX_CHARS]}
---"""
        system = PHYS_LP_SYSTEM_PROMPT + NUMERICAL_ROUTINE_INSTRUCTION
        for attempt in (1, 2):
            raw, stop = self._call(system, prompt, MAX_TOKENS_ASSESSMENT, f"Assessment #{attempt}")
            if not raw:
                continue
            if stop == "max_tokens" and attempt == 1:
                print("         ⚠️ Assessment cut off — retrying")
                prompt += ("\n\nIMPORTANT: Your previous answer was cut off. Keep answers "
                           "concise so the whole assessment, answer key and table fit.")
                continue
            html = normalize_assessment_html(clean(raw))
            print(f"         ✅ Assessment ({len(html)} chars)")
            return html
        return None


# ============================================================================
# Singleton — imported by physics_router
# ============================================================================

physics_lp_1112_builder = PhysicsLP1112Builder()