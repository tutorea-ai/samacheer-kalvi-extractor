"""
maths/lp/grade_910/maths.py
---------------------------
LP Builder for Samacheer Kalvi — Maths
Class 8, 9 & 10

v1.0 — June 2026

Shares architecture with grade_67 (maths_lp_67.py) but differs in:
  - 45-minute day structure (vs 35 min) — Real-Life Connect is its own block
  - Reduced activities — independent practice over games/group work
  - Reduced Tamil scope — 2 places only (Key Terms + Spark), vs 3 in grade_67
  - Geometric construction support in worked examples and board work
  - Higher max_tokens throughout — content is denser (proofs, constructions,
    multi-step word problems)
  - Same dynamic day-count logic as grade_67: derived from chapters_in_month

Inherits automatically from shared infrastructure (no extra work needed):
  ✅ balance_divs() safety net in ai_converter.py — protects tab bar/stepper
  ✅ CSS class discipline rule (baked into MATHS_LP_SYSTEM_PROMPT_910)
  ✅ clean() helper from maths/base/__init__.py

API calls: 3 + N days total
  Call 0a  → Topic Extractor    (JSON — strict extraction, incl. constructions)
  Call 0b  → Day Allocator      (JSON — allocates topics to N days)
  Call 1   → Preamble
  Calls 2..(N) → Teaching Days  (dynamic)
  Call N+1 → Practice Day (Day N-1)
  Call N+2 → Evaluation Day (Day N)
  Call N+3 → Assessment Summary

Metadata expected (same shape as grade_67):
  lesson_title / display_title : str
  class             : str  ("8", "9", or "10")
  chapter           : int
  unit              : int or str
  month             : str
  discipline        : str  ("maths")
  chapters_in_month : int  (1 or 2 — from processor)
  month_chapters    : list (chapter titles sharing this month)
"""

import json
import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    MATHS_LP_SYSTEM_PROMPT_910,
    MATHS_DISCIPLINE_NOTES_910,
    MATHS_CCQ_CFU_INSTRUCTION_910,
    MATHS_TAMIL_INSTRUCTION_910,
    MATHS_DAY_PLAN_STRUCTURE_910,
    MATHS_PREAMBLE_START_INSTRUCTION_910,
    MATHS_ACTIVITY_MAP,
    clean,
)


# ============================================================================
# DAY COUNT LOGIC — identical to grade_67, confirmed: month-driven only
# ============================================================================

def _calculate_day_count(chapters_in_month: int) -> dict:
    """
    chapters_in_month=1 → 20 total (18 content + 2 final)
    chapters_in_month=2 → 10 total (8 content + 2 final)
    """
    if chapters_in_month >= 2:
        total        = 10
        content_days = 8
    else:
        total        = 20
        content_days = 18
    return {
        "total":        total,
        "content_days": content_days,
        "practice_day": total - 1,
        "eval_day":     total,
    }


def _balance_divs(html: str) -> str:
    """Free, deterministic safety net — closes any unclosed divs in a block."""
    open_divs = html.count('<div')
    close_divs = html.count('</div>')
    missing = open_divs - close_divs
    if missing > 0:
        html = html.rstrip() + '\n' + ('</div>' * missing)
    return html


# ============================================================================
# MATHS LP BUILDER — GRADE 8-10
# ============================================================================

class MathsLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Maths LP Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title      = metadata.get("display_title") or metadata.get("lesson_title", "Unknown")
        class_num         = metadata.get("class", "")
        unit              = metadata.get("unit", "")
        month             = metadata.get("month", "")
        chapters_in_month = metadata.get("chapters_in_month", 1)
        month_chapters    = metadata.get("month_chapters", [lesson_title])

        day_counts    = _calculate_day_count(chapters_in_month)
        total_days    = day_counts["total"]
        content_days  = day_counts["content_days"]
        practice_day  = day_counts["practice_day"]
        eval_day      = day_counts["eval_day"]

        total_calls = 3 + content_days + 3

        print(f"      [Maths LP 910 v1] Generating: {lesson_title}")
        print(f"      [Maths LP 910 v1] Month: {month} | Chapters in month: {chapters_in_month}")
        print(f"      [Maths LP 910 v1] Days: {total_days} total ({content_days} content + 2 final)")
        print(f"      [Maths LP 910 v1] Total API calls: {total_calls}")

        parts = []

        # ── Call 0a: Topic Extractor ──────────────────────────────────────────
        print(f"      [Maths LP] Call 0a: Topic Extractor...")
        topics = self._call_topic_extractor(text, lesson_title)
        if not topics:
            print(f"         ❌ Topic Extractor failed — aborting LP")
            return None
        print(f"         ✅ Extracted {len(topics.get('chapter_topics', []))} topics")

        # ── Call 0b: Day Allocator ────────────────────────────────────────────
        print(f"      [Maths LP] Call 0b: Day Allocator...")
        day_plan = self._call_day_allocator(topics, lesson_title, content_days)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting LP")
            return None

        # ── Safety net: fill any empty days by copying previous day's topics ──
        for d in range(1, content_days + 1):
            day_data = day_plan.get(f"day{d}", {})
            if not day_data.get("topics"):
                for prev in range(d - 1, 0, -1):
                    prev_data = day_plan.get(f"day{prev}", {})
                    if prev_data.get("topics"):
                        day_plan[f"day{d}"] = {
                            "topics": prev_data.get("topics", []),
                            "subtopics": prev_data.get("subtopics", []),
                            "formulas": prev_data.get("formulas", []),
                            "has_construction": prev_data.get("has_construction", False),
                            "focus": f"Continued practice and deeper coverage — {prev_data.get('focus', '')}",
                            "has_formula_box": prev_data.get("has_formula_box", False),
                            "estimated_mins": 22
                        }
                        break

        print(f"         ✅ Day plan ready:")
        for d in range(1, content_days + 1):
            day_topics = day_plan.get(f"day{d}", {}).get("topics", [])
            print(f"            Day {d}: {', '.join(day_topics)}")

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [Maths LP] Call 1: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, month,
            chapters_in_month, month_chapters, topics, day_plan,
            total_days, content_days
        )
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting LP")
            return None

        # ── Content Days ──────────────────────────────────────────────────────
        for day_num in range(1, content_days + 1):
            call_num = day_num + 2
            print(f"      [Maths LP] Call {call_num}: Day {day_num}/{content_days} (Content)...")
            day_data = day_plan.get(f"day{day_num}", {})
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title, month,
                day_num, content_days, total_days, day_data, topics, day_plan
            )
            if day_html:
                cleaned = _balance_divs(clean(day_html))
                parts.append(cleaned)
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        # ── Practice Day (Day N-1) ────────────────────────────────────────────
        print(f"      [Maths LP] Practice Day (Day {practice_day})...")
        practice_html = self._call_practice_day(
            text, class_num, unit, lesson_title,
            practice_day, total_days, topics, day_plan
        )
        if practice_html:
            parts.append(_balance_divs(clean(practice_html)))
            print(f"         ✅ Practice Day ({len(practice_html)} chars)")
        else:
            print(f"         ❌ Practice Day failed — continuing")

        # ── Evaluation Day (Day N) ────────────────────────────────────────────
        print(f"      [Maths LP] Evaluation Day (Day {eval_day})...")
        eval_html = self._call_evaluation_day(
            text, class_num, unit, lesson_title,
            eval_day, total_days, topics
        )
        if eval_html:
            parts.append(_balance_divs(clean(eval_html)))
            print(f"         ✅ Evaluation Day ({len(eval_html)} chars)")
        else:
            print(f"         ❌ Evaluation Day failed — continuing")

        # ── Assessment Summary ────────────────────────────────────────────────
        print(f"      [Maths LP] Assessment Summary...")
        assessment = self._call_assessment(
            text, class_num, unit, lesson_title,
            total_days, content_days, topics, day_plan
        )
        if assessment:
            cleaned = clean(assessment)
            if 'assessment-block' in cleaned:
                open_divs = cleaned.count('<div')
                close_divs = cleaned.count('</div>')
                missing = open_divs - close_divs
                if missing > 0:
                    cleaned = cleaned.rstrip() + '\n' + ('</div>' * missing)
            parts.append(cleaned)
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Maths LP 910 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — TOPIC EXTRACTOR (includes construction detection)
    # =========================================================================

    def _call_topic_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            safe_text = text.replace('\\', ' ').replace('"', "'").replace('\r', ' ').replace('\x00', ' ')

            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Maths chapter (Class 8-10).

YOUR ONLY JOB:
Extract EXACTLY the topics, subtopics, formulas, and worked examples that appear in the chapter text.
Do NOT add anything from your general knowledge.
Do NOT reorganise or plan.
Do NOT add topics not explicitly in the text.

For each topic found:
1. Copy the heading EXACTLY as it appears in the text
2. List ALL subtopics under it EXACTLY as they appear
3. List ALL formulas or rules stated in that section (copy verbatim)
4. Count worked examples in that section
5. Note key mathematical terms introduced
6. Flag if this topic involves geometric construction (compass/ruler/protractor)
7. Estimate teaching time (8-20 mins per topic, since periods are 45 mins)

Chapter: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON only.

{{
  "chapter_topics": [
    {{
      "heading": "EXACT heading text from chapter",
      "subtopics": ["exact subtopic 1", "exact subtopic 2"],
      "formulas": ["formula or rule copied verbatim from text"],
      "worked_example_count": 2,
      "key_terms": ["term1", "term2"],
      "is_construction": false,
      "estimated_teaching_time_mins": 15,
      "is_formula_heavy": false
    }}
  ],
  "total_estimated_teaching_mins": 110,
  "all_formulas": ["all formulas from chapter — verbatim"],
  "all_key_terms": ["all key mathematical terms"],
  "has_word_problems": true,
  "has_constructions": false,
  "has_proofs": false
}}

Chapter Text:
---
{safe_text}
---

STRICT RULES:
- Copy headings EXACTLY — do not paraphrase or rename
- Copy formulas VERBATIM — do not rewrite or simplify
- Do NOT add topics not in the text
- Do NOT reorganise the order
- Extract ONLY main content teaching sections

STRICT EXCLUSION — DO NOT extract these as topics:
- Exercise sections (Exercise 1.1, Exercise 1.2 etc.)
- Answers / Answer key
- Summary
- Glossary
- Try These / Think About It sections
- ICT Corner
- Student Activity boxes (extract formula inside if any, but not as a topic)
- Book-back questions"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                system="""You are a strict text extractor. Return ONLY valid JSON.
Extract ONLY what exists in the text. Never add general knowledge.
No markdown. No code fences. Raw JSON starting with {""",
                messages=[{"role": "user", "content": prompt}]
            )

            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group())
                    except json.JSONDecodeError:
                        pass
                return None

        except Exception as e:
            print(f"❌ Topic Extractor error: {e}")
            return None

    # =========================================================================
    # CALL 0b — DAY ALLOCATOR
    # =========================================================================

    def _call_day_allocator(self, topics: dict, lesson_title: str,
                             content_days: int) -> Optional[dict]:
        try:
            topics_str = json.dumps(topics, indent=2)

            day_schema = ""
            for d in range(1, content_days + 1):
                day_schema += f"""  "day{d}": {{
    "topics": ["EXACT heading(s) from extractor"],
    "subtopics": ["subtopics covered today"],
    "formulas": ["formulas introduced today — verbatim"],
    "has_construction": false,
    "focus": "One sentence: what concept does this day teach?",
    "has_formula_box": true,
    "estimated_mins": 22
  }},
"""

            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Maths lesson plan (Class 8-10).

YOU HAVE BEEN GIVEN the extracted topics from a chapter.
YOUR ONLY JOB: Allocate these topics to exactly {content_days} content teaching days.

ALLOCATION RULES:
- Each day has ~22 minutes of Key Learning Activity time (45-min period)
- Use estimated_teaching_time_mins from each topic to fill each day
- Do NOT split a topic across two days — keep each topic in ONE day
- Formula-heavy topics (is_formula_heavy: true) get their own day
- Construction topics (is_construction: true) get their own day — constructions
  need full focus, never combine with other heavy topics
- Maximum 2 subtopics per day — do not overload one day
- Every topic MUST appear in exactly ONE day — no topic skipped
- If topics run out before all {content_days} days are filled: distribute
  topics across fewer days with deeper coverage (more practice, more rigor)
  rather than leaving any day empty
- NEVER return an empty topics list for any day
- Keep allocation logical — simpler concepts before complex ones
- Final 2 days are RESERVED for Practice and Evaluation — do NOT allocate content there

IMPORTANT:
- Use EXACT heading text from the extracted topics
- Do NOT rename headings
- Do NOT add topics not in the extractor output
- Do NOT use general knowledge about the chapter

Return ONLY valid JSON. No explanation. No markdown. Raw JSON only.

{{
{day_schema}}}

Extracted Chapter Topics:
---
{topics_str}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=5000,
                system="""You are a strict day allocator. Return ONLY valid JSON.
Use ONLY the topics provided. Never add general knowledge.
No markdown. No code fences. Raw JSON starting with {""",
                messages=[{"role": "user", "content": prompt}]
            )

            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            return json.loads(raw)

        except json.JSONDecodeError as e:
            print(f"❌ Day Allocator JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Day Allocator error: {e}")
            return None

    # =========================================================================
    # CALL 1 — PREAMBLE
    # =========================================================================

    def _call_preamble(self, text, class_num, unit, lesson_title, month,
                        chapters_in_month, month_chapters,
                        topics: dict, day_plan: dict,
                        total_days: int, content_days: int):
        try:
            topic_list = topics.get("chapter_topics", [])
            topics_str = "\n".join([
                f"  - {t['heading']}: {', '.join(t.get('subtopics', []))}"
                for t in topic_list
            ])

            day_summary = ""
            for d in range(1, content_days + 1):
                day_data   = day_plan.get(f"day{d}", {})
                day_topics = day_data.get("topics", [])
                day_focus  = day_data.get("focus", "")
                day_summary += f"  Day {d}: {', '.join(day_topics)} — {day_focus}\n"
            day_summary += f"  Day {total_days - 1}: Textbook Exercise Practice\n"
            day_summary += f"  Day {total_days}: Quiz + Book-back + Evaluation\n"

            all_formulas  = ", ".join(topics.get("all_formulas", [])[:8])
            all_key_terms = ", ".join(topics.get("all_key_terms", [])[:10])
            month_chapters_str = "\n".join([f"  {i+1}. {c}" for i, c in enumerate(month_chapters)])

            prompt = f"""Generate ONLY the opening preamble of a Samacheer Kalvi Maths Lesson Plan (Class 8-10).
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Maths
Month    : {month}
Chapters in this month: {chapters_in_month}
{month_chapters_str}
Total Teaching Days : {total_days} ({content_days} content days + 2 final days)
Session Duration    : 45 minutes per day

CHAPTER TOPICS (strictly extracted from text):
{topics_str}

DAY-WISE PLAN:
{day_summary}

ALL FORMULAS IN CHAPTER: {all_formulas}
KEY MATHEMATICAL TERMS: {all_key_terms}

Generate these sections as raw HTML:

1. CHAPTER OVERVIEW TABLE
<h2>Chapter Overview</h2>
<table>
  Rows: Class | Subject | Unit/Chapter Title | Month |
        Chapters This Month | Total Teaching Days |
        Session Duration | Main Topics Covered
</table>

2. LEARNING OBJECTIVES
<h2>Learning Objectives</h2>
<ul>
  4-6 objectives — use action verbs: Calculate, Identify, Solve, Apply, Prove, Construct
  Format: "Students will be able to [verb] [concept]"
  Based ONLY on actual topics listed above
  Age-appropriate for Class 8-10 — exam-focused
</ul>

3. VALUE-BASED OBJECTIVES
<h2>Value-Based Objectives</h2>
<ul>
  2-3 values: precision, patience in multi-step work, logical reasoning, systematic approach
</ul>

4. SKILL-BASED OBJECTIVES
<h2>Skill-Based Objectives</h2>
<ul>
  3-4 skills: calculation, proof construction, problem solving, geometric accuracy (if relevant)
  Based on actual chapter content
</ul>

5. TEACHING AIDS
<h2>Teaching Aids</h2>
<ul>
  All materials: blackboard, chalk, textbook (with unit reference),
  compass/ruler/protractor (if constructions present), graph paper,
  worksheets, any chapter-specific aids
  Based on actual topics in this chapter
</ul>

{MATHS_PREAMBLE_START_INSTRUCTION_910}

Chapter Text (for reference):
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3500,
                system=MATHS_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 910 Preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2..N — CONTENT DAYS
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title, month,
                           day_num: int, content_days: int, total_days: int,
                           day_data: dict, topics: dict, day_plan: dict):
        try:
            day_topics      = day_data.get("topics", [])
            day_subtopics   = day_data.get("subtopics", [])
            day_formulas    = day_data.get("formulas", [])
            day_focus       = day_data.get("focus", "")
            has_formula_box = day_data.get("has_formula_box", False)
            has_construction = day_data.get("has_construction", False)

            topics_str    = "\n".join([f"  - {t}" for t in day_topics])
            subtopics_str = "\n".join([f"    • {s}" for s in day_subtopics])
            formulas_str  = "\n".join([f"  • {f}" for f in day_formulas])

            is_last_content_day = (day_num == content_days)
            last_content_note = ""
            if is_last_content_day:
                last_content_note = f"""
⚠️ DAY {day_num} — LAST CONTENT DAY:
The closing MUST recap ALL main topics covered across Days 1–{content_days}.
Brief oral rapid-fire spanning all content days.
Tell students: "Tomorrow is Practice Day — bring your textbook exercises."
"""

            homework_note = ""
            if day_num == 2:
                homework_note = """
⚠️ HOMEWORK FOR DAY 2 — Give students a CHOICE:
  Option A: Solve 5 textbook problems from today's exercise (written)
  Option B: Write a concise summary of today's rule/property with one example
Write both options on board. Students choose based on their strength.
"""

            construction_note = ""
            if has_construction:
                construction_note = """
⚠️ THIS DAY INVOLVES GEOMETRIC CONSTRUCTION:
- Worked example must give EXACT step-by-step construction instructions
  (e.g. "Step 1: Draw line segment AB = 6 cm using ruler.
  Step 2: With A as center, open compass to more than half of AB...")
- Students replicate the construction in their notebooks using compass/ruler/protractor
- Independent practice = students perform ONE similar construction themselves
- Board work section should describe the construction sequence clearly
"""

            next_label = (
                f"Day {day_num + 1}" if day_num < content_days
                else f"Day {total_days - 1} — Practice Day"
            )

            formula_box_html = ""
            if has_formula_box and day_formulas:
                formula_box_html = f"""
  <div class="formula-box" style="background:#1a1a2e;color:#fff;padding:12px;border-radius:6px;margin-bottom:12px;">
    <strong style="color:#fff;">📐 Formula Box — Write on Board First:</strong><br/>
    {"<br/>".join([f'<span style="display:block;color:#cccccc;">{f}</span>' for f in day_formulas])}
    <span style="display:block;color:#cccccc;font-style:italic;">Students copy all formulas into notebooks before lesson starts.</span>
  </div>"""

            prompt = f"""Generate ONLY Day {day_num} of the Maths lesson plan for Class 8-10.
Nothing else. Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 13-16 years — exam-focused, independent learners)
Unit     : {unit}
Subject  : Maths
Month    : {month}
Day      : {day_num} of {total_days}
Duration : 45 minutes

{MATHS_DISCIPLINE_NOTES_910}

═══════════════════════════════════════════════════════
TODAY'S EXACT TOPICS — STRICTLY FOLLOW THIS LIST
═══════════════════════════════════════════════════════
Topics to cover today:
{topics_str}

Subtopics to cover:
{subtopics_str if subtopics_str else "  [Cover all subtopics under today's topics]"}

Formulas for today:
{formulas_str if formulas_str else "  [No new formulas today — consolidation day]"}

Day Focus: {day_focus}

⛔ ABSOLUTE RULE:
Cover ONLY the topics listed above.
If a topic is NOT in this list — DO NOT mention it.
DO NOT use general Maths knowledge to add extra content.
DO NOT introduce topics from other days.
All worked examples must use numbers/problems from the chapter text only.
{last_content_note}
{homework_note}
{construction_note}
═══════════════════════════════════════════════════════

{MATHS_CCQ_CFU_INSTRUCTION_910}

{MATHS_TAMIL_INSTRUCTION_910}

{MATHS_DAY_PLAN_STRUCTURE_910}

OUTPUT THIS EXACT STRUCTURE:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — [Exact topic names being taught today]</h3>
<p class="lp-day-meta">Duration: 45 Minutes | Maths | Class {class_num} | {day_focus}</p>

{formula_box_html}

  <!-- ═══ SECTION 1: SPARK / BIG QUESTION (0-5 min) ═══ -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Spark / Big Question</span>
    <strong>[0–5 min]</strong>

    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[3-5 minute hook — number puzzle, contradiction, or provocative question.
       Must connect to today's topics: {', '.join(day_topics)}.
       End with Big Question.]"
    </div>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      "[Tamil mirror of the Big Question only — same meaning, natural Tamil.]"
    </div>

    <p><em>⏱ Wait 15 seconds. Take 2-3 student responses.</em></p>
  </div>

  <!-- ═══ SECTION 2: REAL-LIFE CONNECT (5-10 min) ═══ -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Real-Life Connect</span>
    <strong>[5–10 min]</strong>

    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[1-2 concrete real-world scenarios where today's concept applies.
       Brief — sets purpose for the lesson, not a discussion. 2-3 sentences.]"
    </div>

    <p><em>[Transition: "Now let's see how this works mathematically."]</em></p>
  </div>

  <!-- ═══ SECTION 3: KEY LEARNING ACTIVITIES (10-32 min) ═══ -->
  <div class="lp-section-main">
    <span class="lp-section-label">Key Learning Activities</span>
    <strong>[10–32 min]</strong>

    <!-- Concept Introduction -->
    <h4>Concept Introduction</h4>

    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[Connect explicitly to prior knowledge — name the earlier grade/chapter concept.
       2-3 sentences — precise, exam-focused tone for Class 8-10.]"
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Today's Topic: {' | '.join(day_topics)}<br/>
      [One clear learning goal for today]
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [3-5 key mathematical terms from TODAY's topics]
        </tbody>
      </table>
    </div>

    [CFU 1 — recall of prior knowledge connection]
    [CFU 2 — what is today's new concept called?]

    <!-- Worked Example -->
    <h4>Worked Example — Step by Step</h4>

    [For EACH topic in today's list — in exact order:]

    <h4>[Topic heading — EXACTLY as in today's topic list]</h4>

    [For EACH subtopic:]
    <h5>[Subtopic — exactly as extracted]</h5>

    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[2-3 sentences explaining the concept precisely.
       Based ONLY on chapter text — no outside knowledge.
       For constructions: describe what is being constructed and why.]"
    </div>

    <div class="board-work">
      <strong>Worked Example (solve step-by-step on board):</strong><br/>
      Problem: [Problem from chapter text — exact numbers]<br/>
      Step 1: [First step — narrate aloud. For constructions: exact compass/ruler instruction]<br/>
      Step 2: [Second step]<br/>
      Step 3: [Continue until answer/construction complete]<br/>
      Answer: [Final answer or completed construction description]<br/>
      <br/>
      ⚠️ Common Mistakes to warn students:<br/>
      Mistake 1: [Most frequent error for this problem/construction type]<br/>
      Mistake 2: [Second common error]<br/>
      Teacher says: "Many students make this mistake — let's make sure we don't!"
    </div>

    [CFU after each worked example — calculation or construction-step check]
    [CFU — can students identify the next step?]

    [CCQ after CFUs — why this method / when to use it — True/False or two-option]
    [CCQ — real-life or cross-topic connection question]

    <!-- Brief Independent Practice -->
    <div class="activity-block">
      <strong>Independent Practice:</strong>
      <p>[1-2 similar problems for students to attempt INDEPENDENTLY — not group work.
         From chapter exercises or similar to worked example. 5-7 minutes.]</p>
      <p><em>Teacher circulates and checks individually.</em></p>
      <p><em>1-2 students solve on board — class verifies.</em></p>
    </div>

    [Repeat for each topic/subtopic in today's list]

    <!-- Concept Summary -->
    <h4>Concept Summary</h4>
    <div class="board-work">
      <strong>Summary on Board:</strong><br/>
      [Key rule/formula/property restated precisely — 1-2 lines]<br/>
      [Connection to upcoming topics if relevant]
    </div>
  </div>

  <!-- ═══ SECTION 4: SHOWCASE OF LEARNING (32-42 min) ═══ -->
  <div class="lp-section-student-task">
    <span class="lp-section-label">Showcase of Learning</span>
    <strong>[32–42 min]</strong>

    <div class="lp-teacher-says">
      <strong>Teacher says:</strong><br/>
      "Now let's check what we learned. Everyone write independently in your notebook."
    </div>

    <div class="board-work">
      <strong>Exit Slip — Write on Board:</strong><br/>
      Problem 1 (standard): [Specific problem from today's concept]<br/>
      Problem 2 (slightly harder): [One extra step — same concept]<br/>
      [Must be solvable in 8 minutes]
    </div>
    <div class="board-work">
      <strong>Exit Slip Answer Key (teacher reference):</strong><br/>
      Problem 1 Answer: [Exact answer with working shown]<br/>
      Problem 2 Answer: [Exact answer with working shown]<br/>
      <em>Mark during last 2 minutes while students pack up.</em>
    </div>

    [2 CFU questions — quick oral check after exit slip]
  </div>

  <!-- ═══ SECTION 5: CLOSING (42-45 min) ═══ -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing</span>
    <strong>[42–45 min]</strong>

    <div class="lp-teacher-says">
      <strong>Recap:</strong><br/>
      "{'[Rapid-fire across ALL content days — questions spanning full chapter so far. Tell students: Practice Day tomorrow.]' if is_last_content_day else '[2-3 rapid-fire questions about today only.]'}"
    </div>

    <div class="board-work">
      <strong>Today's Key Rule / Formula (copy into notebook):</strong><br/>
      [Most important rule or formula from today — exact from chapter text]
    </div>

    <div class="homework-block">
      <div class="lp-teacher-says">
        <strong>Homework:</strong><br/>
        {"Option A: Solve 5 textbook problems from today's exercise.<br/>Option B: Write a concise summary of today's rule/property with one example.<br/><em>Write both options on board — students choose.</em>" if day_num == 2 else "[Specific textbook exercise problems from today's topic.]"}
      </div>

      <div class="lp-teacher-says">
        <strong>Preview — {next_label}:</strong><br/>
        "[1-2 sentences — name the EXACT topic(s) from next day's plan.]"
      </div>
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS — CRITICAL BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ Day heading matches EXACTLY: {' | '.join(day_topics)}
✅ Covered ONLY topics: {', '.join(day_topics)}
✅ NO topics from other days mentioned
✅ NO general Maths knowledge added — only chapter text used
✅ Worked examples use numbers from chapter text only
✅ Formula Box present if formulas exist for today
✅ Real-Life Connect is its OWN block — not merged into Spark
✅ Independent practice — NOT group games or posters
✅ Minimum 2 CFUs per concept (numbered sequentially)
✅ Minimum 2 CCQs per concept — CLOSED form only (True/False or two-option)
✅ Tamil ONLY in: Key Terms table + Spark Big Question — nowhere else
✅ Common Mistakes is INSIDE board-work — never a separate styled div
✅ NO invented inline styles anywhere — use only board-work, teacher-says,
   cfu-block, ccq-block classes with NO custom style attributes
✅ Closing + Homework included
{"✅ Construction steps are EXACT (compass/ruler/protractor instructions)" if has_construction else ""}
{"✅ Day 2 homework has 2 format options" if day_num == 2 else f"✅ Preview names exact topics from {next_label}"}
{"✅ Last content day closing = full chapter recap + Practice Day preview" if is_last_content_day else ""}
✅ Raw HTML only — start with <div class="lp-day-block">
✅ Do NOT generate Day {day_num + 1}

Chapter Text (use ONLY this — no general knowledge):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=18000,
                system=MATHS_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 910 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # PRACTICE DAY (Day N-1)
    # =========================================================================

    def _call_practice_day(self, text, class_num, unit, lesson_title,
                            practice_day: int, total_days: int,
                            topics: dict, day_plan: dict):
        try:
            all_topics = [t["heading"] for t in topics.get("chapter_topics", [])]
            topics_str = ", ".join(all_topics)
            has_constructions = topics.get("has_constructions", False)

            construction_line = ""
            if has_constructions:
                construction_line = "Students bring compass, ruler, protractor for construction practice.\n"

            prompt = f"""Generate ONLY Day {practice_day} (Practice Day) of the Maths lesson plan for Class 8-10.
This is the second-to-last day. Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Maths
Day      : {practice_day} of {total_days} — PRACTICE DAY
Duration : 45 minutes

ALL CHAPTER TOPICS: {topics_str}
{construction_line}

<div class="lp-day-block">
<h3 class="lp-day-title">Day {practice_day} — Textbook Exercise Practice</h3>
<p class="lp-day-meta">Duration: 45 Minutes | Maths | Class {class_num} | Practice & Consolidation Day</p>

  <div class="lp-section-opening">
    <span class="lp-section-label">Warmup</span>
    <strong>[0–5 min] Quick Chapter Recap</strong>
    <div class="lp-teacher-says">
      "[Rapid-fire recap — questions covering all topics from Days 1–{practice_day - 1}.
       One question per major topic. Oral.]"
    </div>
    <p><em>[Transition: 'Now let's open our textbooks. Today we practise all exercises independently.']</em></p>
  </div>

  <div class="lp-section-main">
    <span class="lp-section-label">Textbook Exercise Practice</span>
    <strong>[5–35 min] Independent Exercise Practice</strong>

    <div class="lp-teacher-says">
      "Open your textbooks. I'll demonstrate the first problem of each exercise — then you solve the rest independently."
    </div>

    <h4>Exercise Walkthrough — Teacher-led (8 mins)</h4>
    <div class="board-work">
      <strong>Demonstrate First Problem of Each Exercise:</strong><br/>
      [For each exercise in the chapter — write exercise number on board]<br/>
      [Solve first problem step-by-step]<br/>
      [Highlight common mistakes for each exercise type]
    </div>

    <h4>Independent Student Practice (22 mins)</h4>
    <div class="lp-teacher-says">
      "Now solve the remaining problems independently. Raise your hand if stuck."
    </div>
    <p><em>Teacher circulates continuously. Note which students need help with which topics.</em></p>
    <p><em>Students who finish early: attempt the challenge problems in the textbook.</em></p>
  </div>

  <div class="lp-section-student-task">
    <span class="lp-section-label">Answer Verification</span>
    <strong>[35–42 min]</strong>

    <div class="lp-teacher-says">
      "Let's verify answers together. I'll call students to write their answers on the board."
    </div>

    <div class="board-work">
      <strong>Board Verification — Call 3-4 students:</strong><br/>
      [Student writes answer to a representative problem from each exercise]<br/>
      [Class checks — correct or explain error]
    </div>
  </div>

  <div class="lp-section-closing">
    <span class="lp-section-label">Closing</span>
    <strong>[42–45 min]</strong>

    <div class="lp-teacher-says">
      "[2-3 sentences summarising today's practice. Motivate for tomorrow's evaluation.]"
    </div>

    <div class="board-work">
      <strong>Tomorrow — Evaluation Day (Day {total_days}):</strong><br/>
      ☐ Bring completed textbook exercises<br/>
      ☐ Revise all formulas and key terms<br/>
      ☐ Be ready for a written quiz<br/>
      ☐ Book-back exercises will be marked
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <div class="lp-day-block">
- No Tamil required on Practice Day
- Independent practice — no group games
- Do NOT generate any other day

Chapter Text:
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=6000,
                system=MATHS_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 910 Practice Day error: {e}")
            return None

    # =========================================================================
    # EVALUATION DAY (Day N)
    # =========================================================================

    def _call_evaluation_day(self, text, class_num, unit, lesson_title,
                              eval_day: int, total_days: int, topics: dict):
        try:
            all_topics    = [t["heading"] for t in topics.get("chapter_topics", [])]
            all_formulas  = topics.get("all_formulas", [])
            topics_str    = ", ".join(all_topics)
            formulas_str  = "\n".join([f"  • {f}" for f in all_formulas])

            prompt = f"""Generate ONLY Day {eval_day} (Evaluation Day — final day) of the Maths lesson plan for Class 8-10.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Maths
Day      : {eval_day} of {total_days} — EVALUATION DAY (FINAL)
Duration : 45 minutes

ALL CHAPTER TOPICS: {topics_str}
ALL FORMULAS:
{formulas_str if formulas_str else "  [As identified in chapter text]"}

<div class="lp-day-block">
<h3 class="lp-day-title">Day {eval_day} — Quiz + Book-back Marking + Chapter Completion</h3>
<p class="lp-day-meta">Duration: 45 Minutes | Maths | Class {class_num} | Evaluation Day</p>

  <div class="lp-section-opening">
    <span class="lp-section-label">Warmup</span>
    <strong>[0–5 min] Formula Rapid-Fire</strong>
    <div class="lp-teacher-says">
      "[Teacher calls out a formula/property name — students call back the formula.
       Cover all formulas from the chapter.]"
    </div>
    <p><em>[Transition: 'Now close your books. Quiz time — 25 questions.']</em></p>
  </div>

  <div class="lp-section-main">
    <span class="lp-section-label">Chapter Quiz + Book-back</span>
    <strong>[5–25 min] Written Quiz + Book-back Marking</strong>

    <h4>25-Question Written Quiz (5-18 min)</h4>
    <div class="lp-teacher-says">
      "Close all books. Attempt all 25 questions independently. Show your working."
    </div>

    <div class="board-work">
      <strong>Quiz — 25 Questions (write on board or dictate):</strong><br/>
      [Mix from each major topic — direct calculations, one-step word problems,
       and if relevant, one construction-step question]<br/>
      All based on actual chapter content<br/>
      <br/>
      <strong>Answers (reveal after collecting):</strong><br/>
      [Model answers for all 25 questions]
    </div>

    <h4>Book-back Exercise Marking (18-25 min)</h4>
    <div class="lp-teacher-says">
      "Open textbooks. Let's go through the book-back exercises together."
    </div>

    <div class="board-work">
      <strong>Mark on Board — Key Answers:</strong><br/>
      [Step-by-step model answers for 3-4 key textbook problems]
    </div>
  </div>

  <div class="lp-section-student-task">
    <span class="lp-section-label">Final Assessment</span>
    <strong>[25–40 min] Differentiated Final Assessment</strong>

    <div class="diff-block">
      <strong>Final Chapter Assessment:</strong>
      <table class="diff-table">
        <thead>
          <tr>
            <th>Below Average</th>
            <th>Average Students</th>
            <th>Advanced</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p><strong>Task:</strong> Fill in the blanks + match formula to use</p>
              <p><strong>Formula Bank:</strong> [3-4 key formulas from chapter]</p>
            </td>
            <td>
              <p><strong>Task:</strong> Solve 3 textbook problems independently</p>
            </td>
            <td>
              <p><strong>Task:</strong> Solve 2 challenge problems with full reasoning shown</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ 12 minutes.</em></p>
    </div>
  </div>

  <div class="lp-section-closing">
    <span class="lp-section-label">Chapter Closing</span>
    <strong>[40–45 min] Chapter Completion</strong>

    <div class="lp-teacher-says">
      "[2-3 sentences congratulating students. Name 2-3 specific skills gained.
       Connect to upcoming chapter if relevant.]"
    </div>

    <div class="board-work">
      <strong>Chapter Submission Checklist:</strong><br/>
      ☐ All {total_days} days of notes completed<br/>
      ☐ All homework submitted<br/>
      ☐ All textbook exercises completed and marked<br/>
      ☐ Quiz attempted<br/>
      ☐ All formulas copied into formula reference page
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <div class="lp-day-block">
- Quiz questions based on actual chapter content only
- No Tamil required on Evaluation Day
- Do NOT generate any other day

Chapter Text:
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=6000,
                system=MATHS_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 910 Evaluation Day error: {e}")
            return None

    # =========================================================================
    # ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit, lesson_title,
                          total_days: int, content_days: int,
                          topics: dict, day_plan: dict):
        try:
            all_topics   = [t["heading"] for t in topics.get("chapter_topics", [])]
            all_formulas = topics.get("all_formulas", [])
            topics_str   = ", ".join(all_topics)
            formulas_str = ", ".join(all_formulas[:8])

            day_summary = ""
            for d in range(1, content_days + 1):
                day_data   = day_plan.get(f"day{d}", {})
                day_topics = day_data.get("topics", [])
                day_summary += f"  Day {d}: {', '.join(day_topics)}\n"
            day_summary += f"  Day {total_days - 1}: Textbook Exercise Practice\n"
            day_summary += f"  Day {total_days}: Quiz + Book-back + Evaluation\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Maths chapter (Class 8-10).
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Maths
Total Days: {total_days}

ALL TOPICS: {topics_str}
ALL FORMULAS: {formulas_str}

DAY-WISE COVERAGE:
{day_summary}

Generate the following as raw HTML — start with <h2>Assessment Summary</h2>:

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>CFU Bank — Quick Reference</h3>
  <p><em>Recall/calculation questions — 2 per major topic — for teacher reference:</em></p>
  <ol>
    [10 CFU questions — 2 per each of the 5 main topics.
     Based on actual chapter content only.]
  </ol>

  <h3>CCQ Bank — Deeper Understanding</h3>
  <p><em>8 conceptual questions for revision — CLOSED form (True/False or two-option):</em></p>
  <ol>
    [8 CCQ questions — True/False or two-option format.
     Based on actual chapter content.]
  </ol>

  <h3>Formula Reference Sheet</h3>
  <p><em>All formulas from the chapter — for teacher and student reference:</em></p>
  <table>
    <thead>
      <tr><th>Formula / Rule</th><th>Used For</th><th>Example</th></tr>
    </thead>
    <tbody>
      [One row per formula — verbatim from chapter text.]
    </tbody>
  </table>

  <h3>50-Mark Differentiated Worksheet</h3>
  <p><em>Chapter-end worksheet — 3 levels. All questions from actual chapter content.</em></p>

  <div class="board-work">
    <strong>🟢 Level 1 — Below Average (50 marks)</strong><br/>
    Section A: Fill in the blanks (1 mark × 10 = 10 marks)<br/>
    Section B: Match formula to use (1 mark × 10 = 10 marks)<br/>
    Section C: Simple calculations (2 marks × 10 = 20 marks)<br/>
    Section D: One-sentence answers (2 marks × 5 = 10 marks)<br/>
    <br/>
    <strong>🟡 Level 2 — Average Students (50 marks)</strong><br/>
    Section A: Fill in the blanks (1 mark × 10 = 10 marks)<br/>
    Section B: MCQ (1 mark × 10 = 10 marks)<br/>
    Section C: Two-step calculations (3 marks × 5 = 15 marks)<br/>
    Section D: Word problems (5 marks × 3 = 15 marks)<br/>
    <br/>
    <strong>🔴 Level 3 — Advanced (50 marks)</strong><br/>
    Section A: MCQ (1 mark × 5 = 5 marks)<br/>
    Section B: Multi-step calculations with working (2 marks × 10 = 20 marks)<br/>
    Section C: Word problems / proofs (5 marks × 5 = 25 marks)<br/>
    <br/>
    <em>All questions based on actual chapter content.</em>
  </div>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All {total_days} days of notes completed in notebook</li>
    <li>☐ All homework tasks submitted (Days 1–{content_days})</li>
    <li>☐ All textbook exercises completed and marked (Day {total_days - 1})</li>
    <li>☐ Chapter quiz attempted (Day {total_days})</li>
    <li>☐ All formulas copied into formula reference section</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- CFU bank: 10 questions — simple for Class 8-10
- CCQ bank: 8 questions — CLOSED form only (True/False or two-option)
- Formula Reference Sheet: verbatim from chapter text only
- 50-mark worksheet: 3 levels clearly marked, marks sum to 50 each
- Base everything on actual extracted topics and formulas
- Your output MUST end with the assessment-block div properly closed —
  final two lines must be </ul> then </div>

Chapter Text:
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=14000,
                system=MATHS_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 910 Assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

maths_lp_910_builder = MathsLP910Builder()