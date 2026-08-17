"""
maths/lp/grade_67/maths.py
--------------------------
LP Builder for Samacheer Kalvi — Maths
Class 6 & 7

v1.0 — June 2026

Architecture:
  ✅ Two-pass Chapter Analyser (Call 0a: Topic Extractor, Call 0b: Day Allocator)
  ✅ Dynamic day count — derived from chapters_in_month in metadata
      1 chapter in month  → 20 teaching days (18 content + 2 final)
      2 chapters in month → 10 teaching days (8 content + 2 final)
  ✅ Formula Box at start of every day (if formulas present)
  ✅ Spark / Big Question / Real-life hook (not "Lead Question")
  ✅ 35-minute day structure matching teacher manual LP
  ✅ Differentiated assessment (3 levels) every day
  ✅ Tamil in 3 places only (Key Terms + Main Explanation + Spark)
  ✅ Final Day N-1: Textbook Exercise Practice
  ✅ Final Day N:   Quiz + Book-back + Evaluation
  ✅ Assessment Summary call
  ✅ lp-day-block CSS class on every day — tab bar auto-generates in _wrap_html()
  ✅ Page numbers ALLOWED (Class 6/7)

API calls: 3 + N days total
  Call 0a  → Topic Extractor    (JSON — strict extraction)
  Call 0b  → Day Allocator      (JSON — allocates topics to N days)
  Call 1   → Preamble
  Calls 2..(N) → Teaching Days  (dynamic)
  Call N+1 → Practice Day (Day N-1)
  Call N+2 → Evaluation Day (Day N)
  Call N+3 → Assessment Summary

Metadata expected:
  lesson_title      : str
  class             : str  ("6" or "7")
  chapter           : int
  unit              : int or str
  month             : str  ("June", "July" ...)
  discipline        : str  ("maths")
  chapters_in_month : int  (1 or 2 — from processor)
  month_chapters    : list (all chapter titles sharing this month)
"""

import json
import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    MATHS_LP_SYSTEM_PROMPT,
    MATHS_DISCIPLINE_NOTES_67,
    MATHS_CCQ_CFU_INSTRUCTION_67,
    MATHS_TAMIL_INSTRUCTION_67,
    MATHS_DAY_PLAN_STRUCTURE_67,
    MATHS_PREAMBLE_START_INSTRUCTION,
    MATHS_ACTIVITY_MAP,
    clean,
)


# ============================================================================
# DAY COUNT LOGIC
# ============================================================================

def _calculate_day_count(chapters_in_month: int) -> dict:
    """
    Derive teaching day counts from chapters_in_month.
    Always reserves 2 final days (practice + evaluation).

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
        "practice_day": total - 1,   # Day N-1
        "eval_day":     total,       # Day N
    }


# ============================================================================
# MATHS LP BUILDER — GRADE 6/7
# ============================================================================

class MathsLP67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Maths LP Builder (67) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Maths LP for Class 6 & 7.
        Total API calls = 3 (0a + 0b + Preamble) + content_days + 3 (Practice + Eval + Assessment)
        """
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

        total_calls = 3 + content_days + 3  # 0a + 0b + Preamble + days + Practice + Eval + Assessment

        print(f"      [Maths LP 67 v1] Generating: {lesson_title}")
        print(f"      [Maths LP 67 v1] Month: {month} | Chapters in month: {chapters_in_month}")
        print(f"      [Maths LP 67 v1] Days: {total_days} total ({content_days} content + 2 final)")
        print(f"      [Maths LP 67 v1] Total API calls: {total_calls}")

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
                            "focus": f"Continued practice and deeper coverage — {prev_data.get('focus', '')}",
                            "has_formula_box": prev_data.get("has_formula_box", False),
                            "estimated_mins": 15
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
                cleaned = clean(day_html)
                open_divs = cleaned.count('<div')
                close_divs = cleaned.count('</div>')
                missing = open_divs - close_divs
                if missing > 0:
                    print(f"         ⚠️ Day {day_num} — fixing {missing} unclosed divs")
                    cleaned = cleaned.rstrip() + '\n' + ('</div>' * missing)
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
            cleaned = clean(practice_html)
            open_divs = cleaned.count('<div')
            close_divs = cleaned.count('</div>')
            missing = open_divs - close_divs
            if missing > 0:
                print(f"         ⚠️ Practice Day — fixing {missing} unclosed divs")
                cleaned = cleaned.rstrip() + '\n' + ('</div>' * missing)
            parts.append(cleaned)
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
            cleaned = clean(eval_html)
            open_divs = cleaned.count('<div')
            close_divs = cleaned.count('</div>')
            missing = open_divs - close_divs
            if missing > 0:
                print(f"         ⚠️ Eval Day — fixing {missing} unclosed divs")
                cleaned = cleaned.rstrip() + '\n' + ('</div>' * missing)
            parts.append(cleaned)
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
            if 'assessment-block' in cleaned and not cleaned.rstrip().endswith('</div>'):
                cleaned = cleaned.rstrip() + '\n</div>'
            parts.append(cleaned)
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Maths LP 67 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — TOPIC EXTRACTOR
    # =========================================================================

    def _call_topic_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        """
        PASS 1: Extracts EXACTLY the topics, subtopics, formulas, and
        worked examples that exist in the chapter text.
        Pure extraction — NO planning, NO general knowledge.
        """
        try:
            safe_text = text.replace('\\', ' ').replace('"', "'").replace('\r', ' ').replace('\x00', ' ')

            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Maths chapter (Class 6/7).

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
6. Estimate teaching time (5-15 mins per topic)

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
      "estimated_teaching_time_mins": 10,
      "is_formula_heavy": false
    }}
  ],
  "total_estimated_teaching_mins": 70,
  "all_formulas": ["all formulas from chapter — verbatim"],
  "all_key_terms": ["all key mathematical terms"],
  "has_word_problems": true,
  "has_patterns": false
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
        """
        PASS 2: Allocates extracted topics to content_days teaching days.
        Each day = ~15 mins teaching slot.
        Formula-heavy topics get their own day.
        Max 2 subtopics per day.
        """
        try:
            topics_str = json.dumps(topics, indent=2)

            # Build the JSON schema dynamically for N days
            day_schema = ""
            for d in range(1, content_days + 1):
                day_schema += f"""  "day{d}": {{
    "topics": ["EXACT heading(s) from extractor"],
    "subtopics": ["subtopics covered today"],
    "formulas": ["formulas introduced today — verbatim"],
    "focus": "One sentence: what concept does this day teach?",
    "has_formula_box": true,
    "estimated_mins": 15
  }},
"""

            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Maths lesson plan (Class 6/7).

YOU HAVE BEEN GIVEN the extracted topics from a chapter.
YOUR ONLY JOB: Allocate these topics to exactly {content_days} content teaching days.

ALLOCATION RULES:
- Each day has ~15 minutes of Key Learning Activity time
- Use estimated_teaching_time_mins from each topic to fill each day
- Do NOT split a topic across two days — keep each topic in ONE day
- Formula-heavy topics (is_formula_heavy: true) get their own day
- Maximum 2 subtopics per day — do not overload one day
- Every topic MUST appear in exactly ONE day — no topic can be skipped
- If topics run out before all {content_days} days are filled:
  DO NOT leave days empty — instead distribute topics across fewer days
  with deeper coverage (more worked examples, more practice problems per day)
- NEVER return empty topic lists for any day
- If chapter has fewer topics than days: reduce day count to match topics,
  remaining days become additional practice days automatically
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

            prompt = f"""Generate ONLY the opening preamble of a Samacheer Kalvi Maths Lesson Plan (Class 6/7).
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Maths
Month    : {month}
Chapters in this month: {chapters_in_month}
{month_chapters_str}
Total Teaching Days : {total_days} ({content_days} content days + 2 final days)
Session Duration    : 35 minutes per day

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
  4-5 objectives — use action verbs: Calculate, Identify, Solve, Apply, Explain
  Format: "Students will be able to [verb] [concept]"
  Based ONLY on actual topics listed above — not general Maths knowledge
  Age-appropriate for Class 6/7
</ul>

3. VALUE-BASED OBJECTIVES
<h2>Value-Based Objectives</h2>
<ul>
  2-3 values: accuracy, patience, real-life application, logical thinking
  Age-appropriate for Class 6/7
</ul>

4. SKILL-BASED OBJECTIVES
<h2>Skill-Based Objectives</h2>
<ul>
  3-4 skills: calculation, estimation, problem solving, pattern recognition
  Based on actual chapter content
</ul>

5. TEACHING AIDS
<h2>Teaching Aids</h2>
<ul>
  All materials: blackboard, chalk, textbook (with unit reference),
  number cards, chart paper, worked example sheets, worksheets,
  any chapter-specific aids (abacus, place value chart, geometric shapes etc.)
  Based on actual topics in this chapter
</ul>

{MATHS_PREAMBLE_START_INSTRUCTION}

Chapter Text (for reference):
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system=MATHS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 67 Preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2..N — CONTENT DAYS
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title, month,
                           day_num: int, content_days: int, total_days: int,
                           day_data: dict, topics: dict, day_plan: dict):
        try:
            activity = MATHS_ACTIVITY_MAP.get(day_num, "pair problem solving")

            day_topics    = day_data.get("topics", [])
            day_subtopics = day_data.get("subtopics", [])
            day_formulas  = day_data.get("formulas", [])
            day_focus     = day_data.get("focus", "")
            has_formula_box = day_data.get("has_formula_box", False)

            topics_str    = "\n".join([f"  - {t}" for t in day_topics])
            subtopics_str = "\n".join([f"    • {s}" for s in day_subtopics])
            formulas_str  = "\n".join([f"  • {f}" for f in day_formulas])

            # Day-specific notes
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
  Option B: Create a concept map / formula chart for today's topic (visual)
  Option C: Write 3 real-life situations where today's concept is used
Write all 3 options on board. Students choose based on their strength.
"""

            next_label = (
                f"Day {day_num + 1}" if day_num < content_days
                else f"Day {total_days - 1} — Practice Day"
            )

            formula_box_html = ""
            if has_formula_box and day_formulas:
                formula_box_html = f"""
  <!-- ═══ FORMULA BOX (write on board BEFORE teaching begins) ═══ -->
  <div class="formula-box" style="background:#1a1a2e;color:#fff;padding:12px;border-radius:6px;margin-bottom:12px;">
    <strong style="color:#fff;">📐 Formula Box — Write on Board First:</strong><br/>
    {"<br/>".join([f'<span style="display:block;color:#cccccc;">{f}</span>' for f in day_formulas])}
    <span style="display:block;color:#cccccc;font-style:italic;">Students copy all formulas into notebooks before lesson starts.</span>
  </div>"""

            prompt = f"""Generate ONLY Day {day_num} of the Maths lesson plan for Class 6/7.
Nothing else. Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years — use age-appropriate language)
Unit     : {unit}
Subject  : Maths
Month    : {month}
Day      : {day_num} of {total_days}
Duration : 35 minutes

{MATHS_DISCIPLINE_NOTES_67}

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
═══════════════════════════════════════════════════════

{MATHS_CCQ_CFU_INSTRUCTION_67}

{MATHS_TAMIL_INSTRUCTION_67}

{MATHS_DAY_PLAN_STRUCTURE_67}

OUTPUT THIS EXACT STRUCTURE:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — [Exact topic names being taught today]</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Maths | Class {class_num} | {day_focus}</p>

{formula_box_html}

  <!-- ═══ SECTION 1: SPARK / BIG QUESTION (0-5 min) ═══ -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Spark / Big Question</span>
    <strong>[0–5 min]</strong>

    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[5-question timed Mental Maths Starter — 30 seconds total.
       Each question tests the PREREQUISITE skill needed for today's topic: {', '.join(day_topics)}.
       Teacher reads aloud, students write only the answer (no working).
       Example format:
         Q1: [Simple one-step question — prior knowledge]
         Q2: [Slightly harder — prior knowledge]
         Q3: [Connects to today's concept]
         Q4: [Connects to today's concept]
         Q5: [Estimation — 'roughly, what is...?']
       After 30 seconds: reveal answers on board. Students self-mark.
       Big Question: [One sentence that creates curiosity about today's concept]"
    </div>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      "[3-4 Tamil sentences — same content as above. Same length.]<br/>
       பெரிய கேள்வி: [Big Question in Tamil]"
    </div>

    <p><em>⏱ Wait 20 seconds. Take 3–4 student responses. Stay energetic!</em></p>
    <p><em>[2-minute transition: "Now let's open our textbooks and explore this."]</em></p>

    <div class="lp-teacher-says">
      <strong>Teacher says — Why We Learn This:</strong><br/>
      "[Explain specifically WHY students learn today's topic.
       Give a concrete real-life example from Tamil Nadu daily life.
       Tell them exactly where they will use this knowledge.
       Must be specific to today's sections — not generic.]"
    </div>
  </div>

  <!-- ═══ SECTION 2: KEY LEARNING ACTIVITY (5-22 min) ═══ -->
  <div class="lp-section-main">
    <span class="lp-section-label">Key Learning Activity</span>
    <strong>[5–22 min]</strong>

    <!-- 2a. Concept Introduction -->
    <h4>Concept Introduction</h4>

    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[Connect to prior knowledge first.
       'We already know [previous concept]. Today we will learn [today's concept].'
       Real-life context: where do we see this in daily life?
       2-3 sentences — simple for Class 6/7.]"
    </div>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      "[2-3 Tamil sentences — exact same content. Age-appropriate.]"
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Today's Topic: {' | '.join(day_topics)}<br/>
      [One clear learning goal for today]
    </div>

    <div style="background:#e8f4f8;border:1px solid #b0d4e3;padding:10px;border-radius:6px;margin-top:8px;">
      <strong>📋 Board Layout Plan for Today:</strong>
      <table style="width:100%;margin-top:6px;">
        <thead>
          <tr>
            <th style="width:33%;background:#2E75B6;color:white;padding:6px;text-align:center;">LEFT SIDE</th>
            <th style="width:33%;background:#2E75B6;color:white;padding:6px;text-align:center;">CENTRE</th>
            <th style="width:33%;background:#2E75B6;color:white;padding:6px;text-align:center;">RIGHT SIDE</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding:6px;vertical-align:top;">[Formula / Rule for today — stays here all class]</td>
            <td style="padding:6px;vertical-align:top;">[Worked example — step by step]</td>
            <td style="padding:6px;vertical-align:top;">[Key terms table + student practice problem]</td>
          </tr>
        </tbody>
      </table>
      <em style="font-size:0.85rem;">Erase only right side between activities. Left and centre stay for reference.</em>
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [3-4 key mathematical terms from TODAY's topics — simple meanings for Class 6/7]
        </tbody>
      </table>
    </div>

    [CFU 1 — simple recall of prior knowledge connection]
    [CFU 2 — what is today's new concept called?]

    <!-- 2b. Worked Example — Teacher-led -->
    <h4>Worked Example — Step by Step</h4>

    [For EACH topic in today's list — in exact order:]

    <h4>[Topic heading — EXACTLY as in today's topic list]</h4>

    [For EACH subtopic:]
    <h5>[Subtopic — exactly as extracted]</h5>

    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[2-3 sentences explaining the concept.
       Simple language for Class 6/7.
       Based ONLY on chapter text — no outside knowledge.
       Use real-life analogy if possible.]"
    </div>

    <div style="background:#f3e5f5;border-left:4px solid #9C27B0;padding:8px 12px;margin-bottom:6px;border-radius:4px;">
      <strong>🎯 Estimation Checkpoint (before solving):</strong><br/>
      <em>Teacher says: "Before we solve — everyone estimate the answer. Write it down. No calculating — just your gut feeling."</em><br/>
      <em>Take 3-4 estimates from students. Write on board. Reveal actual answer after solving — compare.</em>
    </div>
    <div class="board-work">
      <strong>Worked Example (solve step-by-step on board):</strong><br/>
      Problem: [Problem from chapter text — exact numbers]<br/>
      Step 1: [First step — narrate aloud]<br/>
      Step 2: [Second step]<br/>
      Step 3: [Continue until answer]<br/>
      Answer: [Final answer]<br/>
      <br/>
      ⚠️ Common Mistakes to warn students:<br/>
      Mistake 1: [Most frequent error for this problem type]<br/>
      Mistake 2: [Second common error]<br/>
      Teacher says: "Many students make this mistake — let's make sure we don't!"
    </div>

    [CFU after each worked example — simple calculation check]
    [CFU — can students identify the next step?]

    [CCQ after CFUs — why this method / when to use it]
    [CCQ — real-life application question]

    <!-- Student Practice -->
    <div class="activity-block">
      <strong>Student Practice — {activity}:</strong>
      <p>[Similar problem(s) for students to attempt.
         From chapter exercises or similar to worked example.
         Step-by-step in pairs/groups. 5-7 minutes.]</p>
      <p><em>Teacher circulates and checks. Note who is struggling.</em></p>
      <p><em>1-2 students solve on board — class verifies.</em></p>
      <div style="background:#e8f5e9;border-left:4px solid #4CAF50;padding:8px 12px;margin-top:8px;border-radius:4px;">
        <strong>🏃 Fast Finisher Task:</strong><br/>
        "[One harder problem — same concept but one extra step or twist.
         From chapter challenge section or slightly beyond standard exercise.
         Students who finish early attempt this independently.]"<br/>
        <em>Do not announce this to whole class — quietly tell fast finishers only.</em>
      </div>
    </div>

    [Repeat for each topic/subtopic in today's list]

    <div style="background:#fce4ec;border-left:4px solid #E91E63;padding:10px 12px;margin-top:12px;border-radius:4px;">
      <strong>🔍 Misconception Probe — 2 Tricky Questions:</strong><br/>
      <p><em>These are DELIBERATELY tricky — designed to expose wrong thinking, not just check correct answers.</em></p>
      <p>Probe 1: "[Question that targets the most common conceptual error for today's topic — e.g. wrong operation, formula misapplication, sign error]"</p>
      <p><strong>What to watch for:</strong> [What wrong answer reveals about student thinking]</p>
      <p><strong>Correct response:</strong> [Right answer + one-sentence explanation of why]</p>
      <br/>
      <p>Probe 2: "[Second tricky question — slightly different misconception]"</p>
      <p><strong>What to watch for:</strong> [Wrong thinking pattern]</p>
      <p><strong>Correct response:</strong> [Right answer + explanation]</p>
      <p><em>⏱ Take 5-6 responses per probe. Do not confirm right/wrong immediately — let students debate first.</em></p>
    </div>

    <!-- 2c. Summary -->
    <h4>Concept Summary</h4>
    <div class="board-work">
      <strong>Summary on Board:</strong><br/>
      [Key rule/formula restated simply — 1-2 lines]<br/>
      [Real-life connection: "We use this when..."]
    </div>

    <div class="lp-teacher-says">
      "[Students, copy the summary and the key rule into your notebooks.]"
    </div>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
      "[Tamil mirror — same content, same length as the summary instruction above]"
    </div>
  </div>

  <!-- ═══ SECTION 3: SHOWCASE OF LEARNING (22-30 min) ═══ -->
  <div class="lp-section-student-task">
    <span class="lp-section-label">Showcase of Learning</span>
    <strong>[22–30 min]</strong>

    <div class="lp-teacher-says">
      <strong>Teacher says:</strong><br/>
      "Now let's check what we learned. Everyone write in your notebook."
    </div>

    <div class="board-work">
      <strong>Exit Slip — Write on Board:</strong><br/>
      Problem 1 (easier): [Specific problem from today's concept]<br/>
      Problem 2 (harder): [One extra step — same concept]<br/>
      [Must be solvable in 5-6 minutes]
    </div>
    <div style="background:#e3f2fd;border-left:4px solid #1565C0;padding:8px 12px;margin-top:6px;border-radius:4px;">
      <strong>🔑 Exit Slip Answer Key (teacher reference — do not show students yet):</strong><br/>
      Problem 1 Answer: [Exact answer with working shown]<br/>
      Problem 2 Answer: [Exact answer with working shown]<br/>
      <em>Mark during last 2 minutes while students pack up. Note names of students who got Problem 2 wrong — follow up tomorrow.</em>
    </div>

    <div class="diff-block">
      <strong>Differentiated Assessment:</strong>
      <table class="diff-table">
        <thead>
          <tr>
            <th>Below Average<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
            <th>Average Students<br/>(சராசரி மாணவர்கள்)</th>
            <th>Toppers / Advanced<br/>(திறமையான மாணவர்கள்)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p><strong>Task:</strong> Solve the easier problem only</p>
              <p>[Simple one-step problem from today's concept]</p>
              <p><em>Teacher assists this group directly.</em></p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Solve both problems</p>
              <p>[Same exit slip problems]</p>
            </td>
            <td>
              <p><strong>Task:</strong> Solve both + create one similar problem</p>
              <p>"Make your own problem using today's concept and solve it."</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ 6 minutes. Teacher circulates to each group.</em></p>
    </div>

    [2 CFU questions — quick oral check after exit slip]
  </div>

  <!-- ═══ SECTION 4: CLOSING + HOMEWORK (30-35 min) ═══ -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing & Homework</span>
    <strong>[30–35 min]</strong>

    <div class="lp-teacher-says">
      <strong>2-Minute Oral Recap:</strong><br/>
      "{'[Rapid-fire across ALL content days — 5 questions spanning full chapter so far. Tell students: Practice Day tomorrow.]' if is_last_content_day else '[3 rapid-fire questions about today only. Hands raised. Keep energetic.]'}"
    </div>
    <p><em>⏱ Wait 5 seconds per question.</em></p>

    <div class="board-work">
      <strong>Today's Key Rule / Formula (copy into notebook):</strong><br/>
      [Most important rule or formula from today — exact from chapter text]
    </div>

    <div class="lp-teacher-says">
      <strong>Real-Life Connection:</strong><br/>
      "[1-2 sentences — where does today's concept appear in daily life?
       Relatable for Class 6/7 — market, cricket, distance, measurement etc.]"
    </div>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
      "[Tamil mirror — same content, same length as the Real-Life Connection above]"
    </div>

    <div class="homework-block">
      <div class="lp-teacher-says">
        <strong>Homework:</strong><br/>
        {"Option A: Solve 5 textbook problems from today's exercise (written).<br/>Option B: Create a concept map / formula chart for today's topic.<br/>Option C: Write 3 real-life situations where today's concept is used.<br/><em>Write all 3 options on board — students choose their strength.</em>" if day_num == 2 else "[Specific textbook exercise problems from today's topic. Page and exercise number from chapter.]"}
      </div>

      <div class="board-work">
        <strong>Homework (write on board):</strong><br/>
        {"[All 3 options written clearly]" if day_num == 2 else "[Exact exercise number and problem range from textbook]"}
      </div>

      <div class="lp-teacher-says">
        <strong>Preview — {next_label}:</strong><br/>
        "[1-2 sentences — name the EXACT topic(s) from next day's plan. Build curiosity.]"
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
✅ Minimum 2 CFUs per concept (numbered sequentially)
✅ Minimum 2 CCQs per concept (numbered sequentially)
✅ Every CFU and CCQ has wait time
✅ Differentiated assessment has 3 levels
✅ Tamil mirrors in: Spark, Concept Intro, each subtopic explanation, Concept Summary, Real-Life Connection
✅ Every CFU has Tamil question; every CCQ has Tamil statement
✅ CCQs are closed (True/False or two-option) — NOT "Why/How" questions
✅ Closing + Homework included
✅ Page numbers may be referenced (Class 6/7 allowed)
✅ Age-appropriate language throughout
{"✅ Day 2 homework has 3 format options" if day_num == 2 else f"✅ Preview names exact topics from {next_label}"}
{"✅ Last content day closing = full chapter recap + Practice Day preview" if is_last_content_day else ""}
✅ Raw HTML only — start with <div class="lp-day-block">
✅ Do NOT generate Day {day_num + 1}

Chapter Text (use ONLY this — no general knowledge):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=16000,
                system=MATHS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 67 Day {day_num} error: {e}")
            if 'overloaded' in str(e).lower():
                import time
                print(f"         ⏳ API overloaded — waiting 30 seconds and retrying...")
                time.sleep(30)
                try:
                    response = self.client.messages.create(
                        model=self.model, max_tokens=16000,
                        system=MATHS_LP_SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
                except Exception as e2:
                    print(f"❌ Maths LP 67 Day {day_num} retry failed: {e2}")
            return None

    # =========================================================================
    # PRACTICE DAY (Day N-1)
    # =========================================================================

    def _call_practice_day(self, text, class_num, unit, lesson_title,
                            practice_day: int, total_days: int,
                            topics: dict, day_plan: dict):
        """
        Day N-1: Textbook Exercise Practice.
        Students work through all chapter exercises.
        Teacher facilitates, corrects, addresses doubts.
        """
        try:
            all_topics = [t["heading"] for t in topics.get("chapter_topics", [])]
            topics_str = ", ".join(all_topics)

            prompt = f"""Generate ONLY Day {practice_day} (Practice Day) of the Maths lesson plan for Class 6/7.
This is the second-to-last day. Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Maths
Day      : {practice_day} of {total_days} — PRACTICE DAY
Duration : 35 minutes

ALL CHAPTER TOPICS: {topics_str}

<div class="lp-day-block">
<h3 class="lp-day-title">Day {practice_day} — Textbook Exercise Practice</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Maths | Class {class_num} | Practice & Consolidation Day</p>

  <!-- SPARK (0-5 min) -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Spark / Warmup</span>
    <strong>[0–5 min] Quick Chapter Recap</strong>
    <div class="lp-teacher-says">
      "[Rapid-fire recap — 5 quick questions covering all topics from Days 1–{practice_day - 1}.
       One question per major topic. Oral — hands raised.
       Age-appropriate for Class 6/7.]"
    </div>
    <p><em>⏱ 5 seconds per question. Keep energetic.</em></p>
    <p><em>[Transition: 'Now let's open our textbooks. Today we practise all exercises.']</em></p>
  </div>

  <!-- KEY LEARNING ACTIVITY (5-22 min) -->
  <div class="lp-section-main">
    <span class="lp-section-label">Textbook Exercise Practice</span>
    <strong>[5–22 min] Guided Exercise Practice</strong>

    <div class="lp-teacher-says">
      "Open your textbooks. We will work through the exercises together.
       I'll do the first problem of each exercise on the board — then you try the rest."
    </div>

    <h4>Exercise Walkthrough — Teacher-led (5 mins)</h4>
    <div class="board-work">
      <strong>Demonstrate First Problem of Each Exercise:</strong><br/>
      [For each exercise in the chapter — write exercise number on board]<br/>
      [Solve first problem step-by-step — narrate every step]<br/>
      [Highlight common mistakes for each exercise type]
    </div>

    <h4>Student Practice — Independent / Pairs (12 mins)</h4>
    <div class="lp-teacher-says">
      "Now you try the remaining problems. Work in pairs if you need help.
       Raise your hand if you are stuck — I'll come to you."
    </div>
    <p><em>Teacher circulates continuously. Note which students need help with which topics.</em></p>
    <p><em>Students who finish early: attempt the challenge problems in the textbook.</em></p>

    <div class="diff-block">
      <strong>Support during practice:</strong>
      <table class="diff-table">
        <thead>
          <tr>
            <th>Below Average<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
            <th>Average Students<br/>(சராசரி மாணவர்கள்)</th>
            <th>Toppers / Advanced<br/>(திறமையான மாணவர்கள்)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p>Attempt first 3 problems of each exercise with teacher support.</p>
              <p><em>Teacher sits with this group for 5 minutes.</em></p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p>Complete all standard problems independently.</p>
              <p>Check answers with partner before moving on.</p>
            </td>
            <td>
              <p>Complete all problems including challenge questions.</p>
              <p>Write explanations for each step (not just answers).</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- SHOWCASE OF LEARNING (22-30 min) -->
  <div class="lp-section-student-task">
    <span class="lp-section-label">Showcase of Learning</span>
    <strong>[22–30 min] Answer Verification</strong>

    <div class="lp-teacher-says">
      "Let's verify answers together. I'll call students to write their answers on the board."
    </div>

    <div class="board-work">
      <strong>Board Verification — Call 3-4 students:</strong><br/>
      [Student 1 writes answer to Exercise A problem]<br/>
      [Student 2 writes answer to Exercise B problem]<br/>
      [Class checks — correct or explain error]
    </div>

    <p><em>For each error on board: ask class "What went wrong? How do we fix it?"</em></p>
    <p><em>This turns mistakes into learning moments.</em></p>
  </div>

  <!-- CLOSING (30-35 min) -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing</span>
    <strong>[30–35 min] Closing</strong>

    <div class="lp-teacher-says">
      "[2-3 sentences summarising today's practice.
       Acknowledge effort. Name specific exercises completed.
       Motivate for tomorrow's evaluation day.
       Age-appropriate and encouraging for Class 6/7.]"
    </div>

    <div class="board-work">
      <strong>Tomorrow — Evaluation Day (Day {total_days}):</strong><br/>
      ☐ Bring completed textbook exercises<br/>
      ☐ Revise all formulas and key terms<br/>
      ☐ Be ready for a 20-question quiz<br/>
      ☐ Book-back exercises will be marked
    </div>

    <div class="lp-teacher-says">
      <strong>Homework — Complete any unfinished exercises:</strong><br/>
      "[Specific exercise numbers not completed in class today]"
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <div class="lp-day-block">
- No Tamil required on Practice Day
- Page numbers may be referenced
- Age-appropriate language for Class 6/7
- Do NOT generate any other day

Chapter Text:
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system=MATHS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 67 Practice Day error: {e}")
            return None

    # =========================================================================
    # EVALUATION DAY (Day N)
    # =========================================================================

    def _call_evaluation_day(self, text, class_num, unit, lesson_title,
                              eval_day: int, total_days: int, topics: dict):
        """
        Day N: Quiz + Book-back marking + Chapter completion.
        """
        try:
            all_topics    = [t["heading"] for t in topics.get("chapter_topics", [])]
            all_formulas  = topics.get("all_formulas", [])
            topics_str    = ", ".join(all_topics)
            formulas_str  = "\n".join([f"  • {f}" for f in all_formulas])

            prompt = f"""Generate ONLY Day {eval_day} (Evaluation Day — final day) of the Maths lesson plan for Class 6/7.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Maths
Day      : {eval_day} of {total_days} — EVALUATION DAY (FINAL)
Duration : 35 minutes

ALL CHAPTER TOPICS: {topics_str}
ALL FORMULAS:
{formulas_str if formulas_str else "  [As identified in chapter text]"}

<div class="lp-day-block">
<h3 class="lp-day-title">Day {eval_day} — Quiz + Book-back Marking + Chapter Completion</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Maths | Class {class_num} | Evaluation Day</p>

  <!-- SPARK (0-5 min) -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Spark / Warmup</span>
    <strong>[0–5 min] Formula Rapid-Fire</strong>
    <div class="lp-teacher-says">
      "[Teacher calls out a formula name — students call back the formula.
       Cover all formulas from the chapter. Fast and energetic.
       Builds confidence before the quiz.
       Age-appropriate for Class 6/7.]"
    </div>
    <p><em>⏱ 5 seconds per formula. All students participate.</em></p>
    <p><em>[Transition: 'Now put your books away. Quiz time — 20 questions.']</em></p>
  </div>

  <!-- KEY LEARNING ACTIVITY (5-22 min) -->
  <div class="lp-section-main">
    <span class="lp-section-label">Chapter Quiz + Book-back</span>
    <strong>[5–22 min] Written Quiz + Book-back Marking</strong>

    <h4>20-Question Written Quiz (5-15 min)</h4>
    <div class="lp-teacher-says">
      "Close all books and notebooks. Attempt all 20 questions.
       Show your working for calculation problems.
       No discussion during quiz."
    </div>

    <div class="board-work">
      <strong>Quiz — 20 Questions (write on board or dictate):</strong><br/>
      [5 questions from each major topic area of the chapter]<br/>
      Mix: 10 direct calculation + 5 fill-in-blank + 5 one-step word problems<br/>
      All based on actual chapter content and exercises<br/>
      <br/>
      <strong>Answers (reveal after collecting):</strong><br/>
      [Model answers for all 20 questions]
    </div>

    <p><em>Collect quiz papers. Students self-mark OR teacher marks later.</em></p>

    <h4>Book-back Exercise Marking (15-22 min)</h4>
    <div class="lp-teacher-says">
      "Open textbooks. Let's go through the book-back exercises together."
    </div>

    <div class="board-work">
      <strong>Mark on Board — Key Answers:</strong><br/>
      [Step-by-step model answers for 3-4 key textbook problems]<br/>
      [Focus on problems students found difficult during Practice Day]
    </div>

    <p><em>Students correct their notebooks as teacher explains each answer.</em></p>
    <p><em>Teacher asks: "Who got this right? Who got a different answer? Let's see why."</em></p>
  </div>

  <!-- SHOWCASE OF LEARNING (22-30 min) -->
  <div class="lp-section-student-task">
    <span class="lp-section-label">Showcase of Learning</span>
    <strong>[22–30 min] Differentiated Final Assessment</strong>

    <div class="diff-block">
      <strong>Final Chapter Assessment:</strong>
      <table class="diff-table">
        <thead>
          <tr>
            <th>Below Average<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
            <th>Average Students<br/>(சராசரி மாணவர்கள்)</th>
            <th>Toppers / Advanced<br/>(திறமையான மாணவர்கள்)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p><strong>Task:</strong> Fill in the blanks + match formula to name</p>
              <p><strong>Formula Bank:</strong> [3-4 key formulas from chapter]</p>
              <p><em>Teacher assists directly.</em></p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Solve 3 textbook problems independently</p>
              <p>[Standard difficulty — from chapter exercises]</p>
            </td>
            <td>
              <p><strong>Task:</strong> Solve 2 challenge problems</p>
              <p>[From chapter challenge section or similar complexity]</p>
              <p>Write explanation for each step — not just answer.</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ 8 minutes. Teacher circulates.</em></p>
    </div>
  </div>

  <!-- CLOSING (30-35 min) -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Chapter Closing</span>
    <strong>[30–35 min] Chapter Completion & Reflection</strong>

    <div class="lp-teacher-says">
      "[2-3 sentences — congratulate students on completing the chapter.
       Name 2-3 specific skills they have gained.
       Connect the chapter concepts to real-life one final time.
       Encouraging and motivating language for Class 6/7.]"
    </div>

    <div class="board-work">
      <strong>Chapter Submission Checklist:</strong><br/>
      ☐ All {total_days} days of notes completed in notebook<br/>
      ☐ All homework from Days 1–{eval_day - 2} submitted<br/>
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
- Page numbers may be referenced
- Age-appropriate language for Class 6/7
- Do NOT generate any other day

Chapter Text:
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system=MATHS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 67 Evaluation Day error: {e}")
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

            prompt = f"""Generate ONLY the Assessment Summary for this Maths chapter (Class 6/7).
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
  <p><em>Simple calculation/recall questions — 2 per major topic — for teacher reference:</em></p>
  <ol>
    [10 CFU questions — 2 per each of the 5 main topics.
     One-step calculation or direct recall.
     Simple language for Class 6/7.
     Based on actual chapter content only.]
  </ol>

  <h3>CCQ Bank — Deeper Understanding</h3>
  <p><em>8 conceptual questions for revision — why/when/what if:</em></p>
  <ol>
    [8 CCQ questions — Why/When/What if/How format.
     Age-appropriate for Class 6/7. Under 8 words each.
     Tamil version noted. Based on actual chapter content.]
  </ol>

  <h3>Formula Reference Sheet</h3>
  <p><em>All formulas from the chapter — for teacher and student reference:</em></p>
  <table>
    <thead>
      <tr><th>Formula / Rule</th><th>Used For</th><th>Example</th></tr>
    </thead>
    <tbody>
      [One row per formula — verbatim from chapter text.
       Explanation of when to use it. Simple numeric example.]
    </tbody>
  </table>

  <h3>50-Mark Differentiated Worksheet</h3>
  <p><em>Chapter-end worksheet — 3 levels. All questions from actual chapter content.</em></p>

  <div class="board-work">
    <strong>🟢 Level 1 — Below Average (50 marks)</strong><br/>
    Section A: Fill in the blanks (1 mark × 10 = 10 marks)<br/>
    Word/Formula Bank: [10 key terms or formula values from chapter]<br/>
    Section B: Match the formula to its use (1 mark × 10 = 10 marks)<br/>
    Section C: Simple one-step calculations (2 marks × 10 = 20 marks)<br/>
    Section D: Answer in one sentence (2 marks × 5 = 10 marks)<br/>
    <br/>
    <strong>🟡 Level 2 — Average Students (50 marks)</strong><br/>
    Section A: Fill in the blanks (1 mark × 10 = 10 marks)<br/>
    Section B: MCQ — choose correct answer (1 mark × 10 = 10 marks)<br/>
    Section C: Two-step calculations (3 marks × 5 = 15 marks)<br/>
    Section D: Word problems (5 marks × 3 = 15 marks)<br/>
    <br/>
    <strong>🔴 Level 3 — Toppers / Advanced (50 marks)</strong><br/>
    Section A: MCQ (1 mark × 5 = 5 marks)<br/>
    Section B: Short calculations with working shown (2 marks × 10 = 20 marks)<br/>
    Section C: Word problems (5 marks × 5 = 25 marks)<br/>
    <br/>
    <em>All questions based on actual chapter content. Age-appropriate for Class 6/7.</em>
  </div>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All {total_days} days of notes completed in notebook</li>
    <li>☐ All homework tasks submitted (Days 1–{content_days})</li>
    <li>☐ All textbook exercises completed and marked (Day {total_days - 1})</li>
    <li>☐ Chapter quiz attempted (Day {total_days})</li>
    <li>☐ All formulas copied into formula reference section</li>
    <li>☐ [Chapter-specific checklist item — based on actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- CFU bank: 10 questions (2 per major topic) — simple for Class 6/7
- CCQ bank: 8 questions — age-appropriate, with Tamil note
- Formula Reference Sheet: verbatim from chapter text only
- 50-mark worksheet: 3 levels clearly marked, marks sum to 50 each
- Completion checklist: day references correct
- Base everything on actual extracted topics and formulas
- No page numbers in Assessment Summary
- CRITICAL: The assessment-block div MUST be explicitly closed
- Your output MUST end with exactly: </div> closing the assessment-block
- Final two lines of output must always be:
  </ul>
  </div>

Chapter Text:
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=MATHS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Maths LP 67 Assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

maths_lp_67_builder = MathsLP67Builder()