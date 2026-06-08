"""
history.py
----------
LP Builder for Samacheer Kalvi Social Science — History
Class 6 & 7

v1.0 — Two-pass Chapter Analyser + New Day Plan Template (May 2026)

Architecture mirrors grade_910/history.py v9.0 with key differences:
  ✅ Same two-pass analyser (Call 0a: Section Extractor, Call 0b: Day Allocator)
  ✅ Same 5-day structure (History = 5 days)
  ✅ Same Preamble structure (Chapter Overview + Objectives + Teaching Aids)
  ✅ Same separate Assessment call (Call 7)
  ✅ New Day Plan template per day (35 mins):
       [0-5 min]   Lead/Spark/Opening Question
       [5-20 min]  Key Learning Activity (Intro → Explanation+Activity → Summary)
       [20-30 min] Assessment (3 levels: toppers, average, below-average)
       [30-35 min] Closing + Student Task (homework)
  ✅ Page numbers ALLOWED (unlike grade_910)
  ✅ Tamil in 3 places only (Key Terms, Main Explanation, Opening Question)
  ✅ CFU/CCQ enforcement same as grade_910
  ✅ Skills focus: Critical Thinking, Communication, Collaboration, Empathy

API calls: 9 total
  Call 0a → Section Extractor  (JSON — strict extraction)
  Call 0b → Day Allocator      (JSON — day plan from extraction)
  Call 1  → Preamble
  Call 2  → Day 1
  Call 3  → Day 2
  Call 4  → Day 3
  Call 5  → Day 4
  Call 6  → Day 5
  Call 7  → Assessment
"""

import json
import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    SS_LP_SYSTEM_PROMPT,
    SPARK_STYLES,
    STUDENT_TASK_STYLES,
    ACTIVITY_MAP,
    clean,
    PREAMBLE_START_INSTRUCTION,
)


# ============================================================================
# HISTORY DISCIPLINE NOTES — GRADE 6/7
# ============================================================================

HISTORY_DISCIPLINE_NOTES_67 = """
HISTORY-SPECIFIC TEACHING NOTES (Class 6 & 7):
- Age-appropriate language — Class 6/7 students need simpler explanations
- Story-based teaching: use narrative style to make history engaging
- Timeline-based thinking: when → what caused it → what resulted
- Chronology matters — sequence of events must be clear
- Source analysis: use any primary source quote from chapter (age-appropriate)
- Board flowcharts: Cause → Event → Consequence chains (simple and visual)
- Map references as text descriptions
- Maintain main topic → subtopic hierarchy STRICTLY from section list
- Never introduce content not in today's section list
- Connect to students' daily life wherever possible
- Use relatable comparisons and analogies for Class 6/7 level
"""


# ============================================================================
# CCQ + CFU INSTRUCTION BLOCK
# ============================================================================

CCQ_CFU_INSTRUCTION_67 = """
═══════════════════════════════════════════════════════
CFU AND CCQ — STRICT MINIMUM REQUIREMENTS (Class 6/7)
═══════════════════════════════════════════════════════

MINIMUM REQUIREMENT:
- 2 CFU blocks per concept taught (age-appropriate, simple)
- 2 CCQ blocks per concept taught
- Total minimum: 10 CFUs + 8 CCQs across the full day

── CFU (Check For Understanding) ──────────────────────
Basic recall. Asked IMMEDIATELY after explaining something.
Simple, one-word or one-sentence answer.
Age-appropriate for Class 6/7. No Tamil required for CFU.

FORMAT — use EXACTLY this HTML:
<div class="cfu-block">
  <strong>🔎 CFU {number}:</strong>
  <p class="teacher-says">"[Very simple factual question — under 6 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One word or one sentence]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students before moving on.</em></p>
</div>

── CCQ (Concept Check Question) ───────────────────────
Deeper conceptual question. Tests WHY or HOW.
Tamil version mandatory.

FORMAT — use EXACTLY this HTML:
<div class="ccq-block">
  <strong>⚡ CCQ {number}:</strong>
  <p class="teacher-says">"[Deeper question — under 8 words — age appropriate]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion before taking answers.</em></p>
</div>

⚠️ CRITICAL — DO NOT USE ICQs:
❌ WRONG: "Do you understand?" / "How many sentences?" / "Which group are you in?"
✅ RIGHT: "What happened when...?" / "Why did...?"

NUMBER YOUR CFUs AND CCQs sequentially across the day.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# TAMIL INSTRUCTION
# ============================================================================

TAMIL_INSTRUCTION_67 = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING — TARGETED ONLY
═══════════════════════════════════════════════════════
Tamil appears in EXACTLY 3 places:
✅ 1. KEY TERMS TABLE — Tamil meaning column
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph after English
✅ 3. OPENING LEAD QUESTION — Tamil version after English

❌ NEVER in: activity instructions, board work, CFU blocks,
   time notes, closing, homework, assessment, differentiated support
Tamil mirror: same sentences, same length, same detail. Real Unicode only.
Age-appropriate Tamil for Class 6/7 students.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# DAY PLAN STRUCTURE INSTRUCTION
# ============================================================================

DAY_PLAN_STRUCTURE_67 = """
═══════════════════════════════════════════════════════
DAY PLAN STRUCTURE — 35 MINUTES (Class 6/7)
═══════════════════════════════════════════════════════

[0-5 min]   LEAD / SPARK / OPENING QUESTION
            3-minute curiosity-building activity + 2-minute transition
            Use: real-life connections, simple games, debates,
                 group discussion, pictures/videos, student reflection,
                 role play by teacher
            End with a Big Question connecting to today's topic

[5-20 min]  KEY LEARNING ACTIVITY
            1. Topic Introduction (Textbook Context First)
               - Set context for the topic and chapter
               - Introduce topic from textbook with page reference
               - CFU questions after introduction
            2. Topic Explanation with Activity
               - Divide into subtopics, explain each using textbook
               - Integrate: debates, group discussions, group activities
               - CFU and CCQ after each subtopic
            3. Topic Closing — Summary
               - Overall conclusion creatively: flowchart on board,
                 mind map, timeline strip, etc.

[20-30 min] ASSESSMENT — 3 LEVELS
            Differentiated assessment:
            - Toppers (Advanced): Critical thinking, analysis
            - Average students: Core concept application
            - Below-average students: Basic recall with support
            Methods: writing, quizzes, rapid fire, worksheet

[30-35 min] CLOSING + STUDENT TASK
            2-minute recap
            Homework: poster / write answers / essay / flowchart / mindmap
            Focus: writing skills, conceptual knowledge, creativity

SKILLS TO DEVELOP (integrate naturally):
- Critical Thinking: Evidence-based reasoning
- Communication: Clear explanation in own words
- Collaboration: Group/pair activities
- Emotional Intelligence: Perspective-taking in historical contexts
- Creativity: Visual/artistic expression of concepts
- Resilience: Learning from historical mistakes
═══════════════════════════════════════════════════════
"""


# ============================================================================
# HISTORY LP BUILDER CLASS — GRADE 6/7
# ============================================================================

class HistoryLP67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ History LP Builder (67) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate History LP for Class 6 & 7.
        Makes 9 API calls:
            Call 0a: Section Extractor (strict JSON extraction)
            Call 0b: Day Allocator (day plan from extraction)
            Call 1:  Preamble
            Calls 2-5: Days 1-4
            Call 6:  Day 5
            Call 7:  Assessment
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [History LP 67 v1] Generating: {lesson_title}")
        print(f"      [History LP 67 v1] 9 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

        parts = []

        # ── Call 0a: Section Extractor ────────────────────────────────────────
        print(f"      [History LP] Call 0a/9: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting LP")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        # ── Call 0b: Day Allocator ────────────────────────────────────────────
        print(f"      [History LP] Call 0b/9: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting LP")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [History LP] Call 1/9: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, month, sections, day_plan
        )
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting LP")
            return None

        # ── Calls 2-5: Content Days 1-4 ──────────────────────────────────────
        for day_num in range(1, 5):
            call_num = day_num + 1
            print(f"      [History LP] Call {call_num}/9: Day {day_num}...")
            day_data = day_plan.get(f"day{day_num}", {})
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title,
                day_num, day_data, sections, day_plan
            )
            if day_html:
                parts.append(clean(day_html))
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        # ── Call 6: Day 5 ─────────────────────────────────────────────────────
        print(f"      [History LP] Call 6/9: Day 5 (Map + Book-back)...")
        day5_html = self._call_day5(text, class_num, unit, lesson_title, sections)
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # ── Call 7: Assessment ────────────────────────────────────────────────
        print(f"      [History LP] Call 7/9: Assessment...")
        assessment = self._call_assessment(
            text, class_num, unit, lesson_title, sections, day_plan
        )
        if assessment:
            parts.append(clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [History LP 67 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — STRICT SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        """
        PASS 1: Extracts EXACTLY what headings and subheadings exist in the chapter.
        Pure extraction — NO planning, NO general knowledge, NO day allocation.
        """
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi History chapter (Class 6/7).

YOUR ONLY JOB:
Extract EXACTLY the headings and subheadings that appear in the chapter text below.
Do NOT add anything from your general knowledge.
Do NOT reorganise or plan.
Do NOT add topics that are not explicitly in the text.
Extract ONLY what is written in the text — nothing more, nothing less.

For each section found:
1. Copy the heading EXACTLY as it appears in the text
2. List ALL subheadings under it EXACTLY as they appear
3. Estimate teaching time based on content length (5-15 mins per section)
4. Note key terms that appear in that section (age-appropriate for Class 6/7)

Chapter: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON only.

{{
  "chapter_sections": [
    {{
      "heading": "EXACT heading text from chapter",
      "subheadings": ["exact subheading 1", "exact subheading 2"],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "has_map_content": false,
      "has_dates": true,
      "important_dates": ["year — event"]
    }}
  ],
  "total_estimated_teaching_mins": 70,
  "map_locations": ["location1", "location2"],
  "key_personalities": ["Person 1", "Person 2"],
  "important_dates": ["date — event"]
}}

Chapter Text:
---
{text}
---

STRICT RULES:
- Copy headings EXACTLY — do not paraphrase or rename
- Do NOT add sections that don't exist in the text
- Do NOT reorganise the order
- Extract ONLY main content teaching sections
- If no clear headings exist, use paragraph topic sentences as headings

STRICT EXCLUSION — DO NOT extract these as sections (they are book-back, not teaching content):
- Exercises / Exercise sections
- Summary
- Glossary
- Internet Resources
- ICT CORNER
- Learning Objectives
- Student Activity
- Life Skill
- Answer Grid
- Map Work (book-back section)
- HOTS
- Choose the correct answer
- Fill in the blanks
- Match the following
- State True or False"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system="""You are a strict text extractor. Return ONLY valid JSON.
Extract ONLY what exists in the text. Never add general knowledge.
No markdown. No code fences. Raw JSON starting with {""",
                messages=[{"role": "user", "content": prompt}]
            )

            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            # Fix unterminated strings caused by special characters in chapter text
            raw = re.sub(r'[\x00-\x1f\x7f]', ' ', raw)  # remove control characters
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                # Second attempt — extract just the JSON object
                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group())
                    except json.JSONDecodeError:
                        pass
                return None

        except json.JSONDecodeError as e:
            print(f"❌ Section Extractor JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Section Extractor error: {e}")
            return None

    # =========================================================================
    # CALL 0b — SMART DAY ALLOCATOR
    # =========================================================================

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        """
        PASS 2: Takes the extracted sections and allocates them to 4 content days.
        Based STRICTLY on the section extractor output.
        Each day = 15 mins teaching time (Key Learning Activity slot).
        """
        try:
            sections_str = json.dumps(sections, indent=2)

            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi History lesson plan (Class 6/7).

YOU HAVE BEEN GIVEN the extracted sections from a chapter.
YOUR ONLY JOB: Allocate these sections to 4 days.

ALLOCATION RULES:
- Each day has 15 minutes of Key Learning Activity time
- Use estimated_teaching_time_mins from each section to fill each day
- Do NOT split a section across two days — keep each section in ONE day
- If a section is large (>12 mins), it gets its own day
- Day 4 must include the FINAL sections and chapter consolidation
- Every section MUST appear in exactly ONE day — no section can be skipped
- No section can appear in two days
- Keep allocation age-appropriate for Class 6/7

IMPORTANT:
- Use the EXACT heading text from the extracted sections
- Do NOT rename headings
- Do NOT add sections that were not extracted
- Do NOT use general knowledge about the chapter

Return ONLY valid JSON. No explanation. No markdown. Raw JSON only.

{{
  "day1": {{
    "sections": ["EXACT heading 1", "EXACT heading 2"],
    "subheadings": ["subheading 1", "subheading 2"],
    "focus": "One sentence describing what Day 1 covers",
    "estimated_mins": 15,
    "continuation_from_previous": false
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["subheading 3", "subheading 4"],
    "focus": "One sentence describing what Day 2 covers",
    "estimated_mins": 15,
    "continuation_from_previous": false
  }},
  "day3": {{
    "sections": ["EXACT heading 4", "EXACT heading 5"],
    "subheadings": ["subheading 5"],
    "focus": "One sentence describing what Day 3 covers",
    "estimated_mins": 15,
    "continuation_from_previous": false
  }},
  "day4": {{
    "sections": ["EXACT heading 6", "EXACT heading 7"],
    "subheadings": ["subheading 6", "subheading 7"],
    "focus": "One sentence describing what Day 4 covers + chapter consolidation",
    "estimated_mins": 15,
    "continuation_from_previous": false
  }}
}}

Extracted Chapter Sections:
---
{sections_str}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system="""You are a strict day allocator. Return ONLY valid JSON.
Use ONLY the sections provided. Never add general knowledge.
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

    def _call_preamble(self, text, class_num, unit, lesson_title,
                       month, sections: dict, day_plan: dict):
        try:
            sections_list = sections.get("chapter_sections", [])
            sections_str  = "\n".join([
                f"  - {s['heading']}: {', '.join(s.get('subheadings', []))}"
                for s in sections_list
            ])

            day_summary = ""
            for d in range(1, 5):
                day_data     = day_plan.get(f"day{d}", {})
                day_sections = day_data.get("sections", [])
                day_focus    = day_data.get("focus", "")
                day_summary += f"  Day {d}: {', '.join(day_sections)} — {day_focus}\n"

            key_terms     = ", ".join([
                t for s in sections_list for t in s.get("key_terms", [])
            ][:10])
            map_locations = ", ".join(sections.get("map_locations", []))
            personalities = ", ".join(sections.get("key_personalities", []))

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — History Lesson Plan for Class 6/7.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — History
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

CHAPTER SECTIONS (strictly extracted from text):
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY TERMS: {key_terms}
MAP LOCATIONS: {map_locations}
KEY PERSONALITIES: {personalities}

Generate these sections:

1. CHAPTER OVERVIEW TABLE
<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Sections Covered
</table>

2. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives — age-appropriate for Class 6/7
  Based ONLY on actual chapter sections listed above
</ul>

3. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives: chronology, storytelling, map skills, causal reasoning
  Age-appropriate for Class 6/7. Based on actual chapter content.
</ul>

4. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 objectives — based ONLY on actual sections listed above
  Use action verbs: Explain, Identify, List, Describe (Class 6/7 level)
  Format: "Students will be able to [action verb] [topic]"
</ul>

5. TEACHING AIDS
<h2>Part 5: Teaching Aids</h2>
<ul>
  All materials needed — textbook (with page references), board, chalk,
  outline maps, timeline strips, flashcards, chart paper
  Age-appropriate for Class 6/7
</ul>

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids </ul>
- Base ALL content on actual extracted sections only
- Age-appropriate language for Class 6/7

Chapter Text (for reference):
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ History LP 67 preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2-5 — CONTENT DAYS 1-4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            activity = ACTIVITY_MAP.get(day_num, "group discussion")

            # From day allocator — EXACT sections for this day
            day_sections    = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus       = day_data.get("focus", "")
            continuation    = day_data.get("continuation_from_previous", False)

            # Get key terms and page refs for this day's sections
            all_sections  = sections.get("chapter_sections", [])
            day_key_terms = []
            day_dates     = []
            for s in all_sections:
                if s["heading"] in day_sections:
                    day_key_terms.extend(s.get("key_terms", []))
                    day_dates.extend(s.get("important_dates", []))

            sections_str    = "\n".join([f"  - {s}" for s in day_sections])
            subheadings_str = "\n".join([f"    • {s}" for s in day_subheadings])
            key_terms_str   = ", ".join(day_key_terms[:8])

            # Day 4 closing note
            closing_note = ""
            if day_num == 4:
                closing_note = """
⚠️ DAY 4 CLOSING — FULL CHAPTER RECAP:
The closing on Day 4 MUST recap the ENTIRE chapter across all 4 days.
Rapid-fire questions must span ALL 4 days — not just Day 4.
Write ALL main section headings on board as summary.
"""

            # Continuation note
            continuation_note = ""
            if continuation:
                prev_day_data = day_plan.get(f"day{day_num-1}", {})
                prev_sections = prev_day_data.get("sections", [])
                continuation_note = f"""
⚠️ CONTINUATION FROM DAY {day_num-1}:
Start by completing: {', '.join(prev_sections[-1:])}
Teacher says: "Yesterday we started [topic]. Today we complete it first."
"""

            # Homework style
            homework_note = ""
            if day_num == 2:
                homework_note = """
⚠️ HOMEWORK FOR DAY 2 — Give students a CHOICE:
  Option A: Write the answers in their notebook
  Option B: Make a poster — draw and label key concepts visually
  Option C: Flowchart — show cause → event → result chain
Write all 3 options on board. Students choose based on their strength.
"""

            next_label = f"Day {day_num + 1}" if day_num < 4 else "Day 5 — Map Work and Book-back"

            prompt = f"""Generate ONLY Day {day_num} of the History lesson plan for Class 6/7.
Nothing else. Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years — use age-appropriate language)
Unit     : {unit}
Subject  : Social Science — History
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S EXACT SECTIONS — STRICTLY FOLLOW THIS LIST
═══════════════════════════════════════════════════════
Sections to cover today:
{sections_str}

Subheadings to cover:
{subheadings_str if subheadings_str else "  [Cover all subheadings under today's sections]"}

Day Focus: {day_focus}
Key Terms for today: {key_terms_str}

⛔ ABSOLUTE RULE:
Cover ONLY the sections listed above.
If a heading is NOT in this list — DO NOT mention it.
DO NOT use general knowledge to add extra content.
DO NOT introduce topics from other days.
The day heading must match EXACTLY what sections are taught today.
{continuation_note}
{closing_note}
{homework_note}
═══════════════════════════════════════════════════════

{CCQ_CFU_INSTRUCTION_67}

{TAMIL_INSTRUCTION_67}

{DAY_PLAN_STRUCTURE_67}

═══════════════════════════════════════════════════════
PAGE NUMBERS — ALLOWED FOR CLASS 6/7
═══════════════════════════════════════════════════════
You MAY reference textbook page numbers for Class 6/7.
Format: "Refer to page [X] in your textbook."
Use sparingly — only for key topic introductions.
═══════════════════════════════════════════════════════

DAY STRUCTURE — OUTPUT THIS EXACTLY:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — [Write EXACT section names being taught today]</h3>
<p class="lp-day-meta">Duration: 35 Minutes | History | Class {class_num} | {day_focus}</p>

  <!-- ═══ SECTION 1: LEAD / SPARK / OPENING QUESTION (0-5 min) ═══ -->
  <div class="lp-section-opening">
    <strong>[0-5 min] Lead / Spark / Opening Question</strong>

    <div class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-minute curiosity-building activity — use one of:
     real-life connection / simple game / debate / group discussion /
     picture description / student reflection / role play.
     Must connect to today's sections: {', '.join(day_sections)}.
     Age-appropriate for Class 6/7. End with Big Question.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same content. Same length.]"</p>
    </div>

    <p><em>⏱ Wait 20 seconds. Take 3-5 student responses.</em></p>
    <p><em>[2-minute transition: "Now let's open our textbooks and explore this topic."]</em></p>
  </div>

  <!-- ═══ SECTION 2: KEY LEARNING ACTIVITY (5-20 min) ═══ -->
  <div class="lp-section-main">
    <strong>[5-20 min] Key Learning Activity</strong>

    <!-- 2a. Topic Introduction -->
    <h4>Topic Introduction — Textbook Context</h4>
    <div class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[Set context for the topic and chapter first.
     Then: 'Let's look at [topic] in our textbook.'
     Reference page number if applicable.
     2-3 sentences — simple and clear for Class 6/7.]"</p>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Today's Topic: {' | '.join(day_sections)}<br/>
      [One clear learning objective for today]
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [4-5 key terms from TODAY's sections — simple meanings for Class 6/7]
        </tbody>
      </table>
    </div>

    [CFU 1 after introduction — very simple recall]
    [CFU 2 after introduction — who/what question]

    <!-- 2b. Topic Explanation with Activity -->
    <h4>Topic Explanation with Activity</h4>

    [For EACH section in today's list — in exact order:]

    <h4>[Section heading — EXACTLY as in today's section list]</h4>

    [For EACH subheading under this section:]
    <h5>[Subheading — exactly as extracted]</h5>

    <div class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — explain this section/subheading.
     Simple language for Class 6/7 — use story, analogy, or real-life connection.
     Based ONLY on chapter text — no outside knowledge.
     Include dates, events as they appear in text.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same. Age-appropriate Tamil.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board:</strong><br/>
      [Simple flowchart or timeline: Event 1 → Event 2 → Result]
      [OR simple mind map for Class 6/7 level]
    </div>

    <!-- 2 CFUs after each concept -->
    <div class="cfu-block">
      <strong>🔎 CFU {'{n}'}:</strong>
      <div class="lp-teacher-says">"[Simple what/who/when question — under 6 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>
    <div class="cfu-block">
      <strong>🔎 CFU {'{n+1}'}:</strong>
      <div class="lp-teacher-says">"[Which/where question — under 6 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>

    <!-- 2 CCQs after CFUs -->
    <div class="ccq-block">
      <strong>⚡ CCQ {'{n}'}:</strong>
      <div class="lp-teacher-says">"[Why did X happen? — simple, under 8 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
      <p><em>⏱ Wait 15 seconds. Allow pair discussion.</em></p>
    </div>
    <div class="ccq-block">
      <strong>⚡ CCQ {'{n+1}'}:</strong>
      <div class="lp-teacher-says">"[What was the result of Y? — under 8 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
      <p><em>⏱ Wait 15 seconds. Allow pair discussion.</em></p>
    </div>

    [Repeat explanation + CFUs + CCQs for each section/subheading in today's list]

    <!-- Activity -->
    <div class="activity-block">
      <strong>Activity — {activity}:</strong>
      <p>[Step by step. English only. Age-appropriate for Class 6/7.
         Based on today's sections only. Simple and engaging.]</p>
      <p><em>Teacher circulates and checks understanding.</em></p>
    </div>

    <!-- 2b. Topic Closing — Summary -->
    <h4>Topic Closing — Summary</h4>
    <div class="board-work">
      <strong>Summary on Board (choose one format):</strong><br/>
      [Flowchart OR Mind Map OR Timeline strip — based on today's content]<br/>
      [Keep simple for Class 6/7]
    </div>
    <div class="lp-teacher-says">"[2-3 sentences summarising what was learned today.
     Ask students to copy the summary into their notebooks.]"</p>
  </div>

  <!-- ═══ SECTION 3: ASSESSMENT (20-30 min) ═══ -->
  <div class="lp-section-student-task">
    <strong>[20-30 min] Assessment — 3 Levels</strong>

    <div class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "Now let's check what we learned today. Choose your task based on your level."</p>

    <div class="diff-block">
      <strong>Differentiated Assessment:</strong>
      <table class="diff-table">
        <thead>
          <tr>
            <th>Below Average Students<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
            <th>Average Students<br/>(சராசரி மாணவர்கள்)</th>
            <th>Toppers / Advanced<br/>(திறமையான மாணவர்கள்)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p><strong>Task:</strong> Fill in the blanks / Oral rapid-fire</p>
              <p>"[Simple sentence] _______ (word1 / word2)"</p>
              <p><strong>Word Bank:</strong> [4 terms from today's sections]</p>
              <p><em>Teacher sits with this group and helps.</em></p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>Question: "[Core concept question from today]"</p>
              <p>Starter: "[sentence starter]"</p>
            </td>
            <td>
              <p><strong>Task:</strong> Critical thinking / Analysis</p>
              <p>"[Why/How question requiring deeper thought from today's content]"</p>
              <p>Write 4-5 sentences with reason and evidence from textbook.</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ 8 minutes. Teacher circulates to each group.</em></p>
    </div>

    <div class="lp-teacher-says"><strong>Quick Review:</strong><br/>
    "[Take 2 minutes to hear 1-2 answers from each level. Give positive feedback.]"</p>
  </div>

  <!-- ═══ SECTION 4: CLOSING + STUDENT TASK (30-35 min) ═══ -->
  <div class="lp-section-closing">
    <strong>[30-35 min] {"Overall Chapter Recap & Closing" if day_num == 4 else "Closing & Student Task"}</strong>

    <div class="lp-teacher-says"><strong>2-Minute Recap:</strong><br/>
    "{'[Recap ALL sections from ALL 4 days. Write main headings on board. Rapid-fire: 5 questions spanning full chapter.]' if day_num == 4 else '[3 rapid-fire questions about today only. Hands raised. Keep energetic.]'}"</p>
    <p><em>⏱ Wait 5 seconds per question.</em></p>

    <div class="board-work">
      <strong>{"Full Chapter" if day_num == 4 else "Today's"} Key Points:</strong><br/>
      1. [Key point 1]<br/>
      2. [Key point 2]<br/>
      3. [Key point 3]
    </div>

    <div class="lp-teacher-says"><strong>Closing Statement:</strong><br/>
    "[2-3 sentences — what was learned today. Connect to real life.
     Motivate students for next day. Age-appropriate and encouraging.]"</p>

    {"" if day_num == 4 else f'''
    <div class="homework-block">
      <div class="lp-teacher-says"><strong>Student Task / Homework:</strong><br/>
      {"Option A: Write the answers in your notebook.<br/>Option B: Make a poster — draw and label key concepts from today.<br/>Option C: Make a flowchart — show cause → event → result chain." if day_num == 2 else "[Specific homework from today's sections. Clear and simple for Class 6/7.]"}</p>

      <div class="board-work">
        <strong>{"Write all 3 options on board — students choose their strength." if day_num == 2 else "Homework (write on board):"}</strong><br/>
        {"" if day_num == 2 else "[Exact homework task students copy from board]"}
      </div>

      <div class="lp-teacher-says"><strong>Preview — {next_label}:</strong><br/>
      "[1-2 sentences — name the EXACT sections from Day {day_num + 1 if day_num < 4 else 5} plan.
       Build curiosity for next class.]"</p>
    </div>'''}

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS — CRITICAL BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ Day heading matches EXACTLY: {' | '.join(day_sections)}
✅ Covered ONLY sections: {', '.join(day_sections)}
✅ NO sections from other days mentioned
✅ NO general knowledge added — only chapter text used
✅ Minimum 2 CFUs per concept (numbered sequentially)
✅ Minimum 2 CCQs per concept (numbered sequentially)
✅ Every CFU and CCQ has wait time
✅ Assessment has 3 levels (Below Average / Average / Toppers)
✅ Lead Question heading used — NOT "Spark"
✅ Tamil only in: Key Terms + Main explanations + Opening question
✅ Summary/flowchart in Topic Closing
✅ Closing + Student Task included
✅ Page numbers may be referenced (Class 6/7 allowed)
✅ Age-appropriate language throughout
{"✅ Day 2 homework has 3 format options" if day_num == 2 else ""}
{"✅ Day 4 closing = full chapter recap across all 4 days" if day_num == 4 else f"✅ Preview names exact sections from Day {day_num + 1}"}
✅ Raw HTML only — start with <div class="lp-day-block">
✅ Do NOT generate Day {day_num + 1}

Chapter Text (use ONLY this — no general knowledge):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ History LP 67 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — DAY 5: MAP + BOOK-BACK
    # =========================================================================

    def _call_day5(self, text, class_num, unit, lesson_title, sections: dict):
        try:
            map_locations = ", ".join(sections.get("map_locations", []))
            personalities = ", ".join(sections.get("key_personalities", []))
            dates         = sections.get("important_dates", [])
            dates_str     = "\n".join([f"  - {d}" for d in dates])

            prompt = f"""Generate ONLY Day 5 of the History lesson plan for Class 6/7.
Day 5: Rapid Recall Quiz → Book-back Marking → Map Work → Student Task → Closing.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years)
Unit     : {unit}
Subject  : Social Science — History
Day      : 5 of 5
Duration : 35 minutes

MAP LOCATIONS: {map_locations if map_locations else 'Identify from chapter text'}
KEY PERSONALITIES: {personalities}
IMPORTANT DATES:
{dates_str if dates_str else '  Identify from chapter text'}

<div class="lp-day-block">
<h3 class="lp-day-title">Day 5 — Map Work & Book-back Exercises</h3>
<p class="lp-day-meta">Duration: 35 Minutes | History | Class {class_num} | Evaluation Day</p>

  <!-- LEAD / SPARK (0-5 min) -->
  <div class="lp-section-opening">
    <strong>[0-5 min] Lead / Spark — Chapter Recap Game</strong>
    <div class="lp-teacher-says">"Let's play a quick recap game! I'll say a clue — you guess the answer.
    [3-4 fun clue-based questions about the chapter. Age-appropriate for Class 6/7.]"</p>
    <p><em>⏱ Keep energetic. Take 4-5 responses.</em></p>
    <p><em>[2-minute transition to book-back work.]</em></p>
  </div>

  <!-- KEY LEARNING ACTIVITY (5-20 min) -->
  <div class="lp-section-main">
    <strong>[5-20 min] Key Learning Activity — Book-back Marking + Map Work</strong>

    <h4>Rapid Recall Quiz — 10 Questions (5-10 min)</h4>
    <div class="lp-teacher-says">"Write answers in your notebook. No discussion yet. 10 quick questions."</p>
    <div class="board-work">
      <strong>10 Quiz Questions (write on board):</strong><br/>
      1. [Factual — Day 1 content — simple for Class 6/7]<br/>
      2. [Factual — Day 1 content]<br/>
      3. [Factual — Day 2 content]<br/>
      4. [Factual — Day 2 content]<br/>
      5. [Factual — Day 3 content]<br/>
      6. [Factual — Day 3 content]<br/>
      7. [Factual — Day 4 content]<br/>
      8. [Factual — Day 4 content]<br/>
      9. [Key date from chapter]<br/>
      10. [Key personality from chapter]<br/>
      <strong>Answers:</strong> 1.[A] 2.[A] 3.[A] 4.[A] 5.[A] 6.[A] 7.[A] 8.[A] 9.[A] 10.[A]
    </div>
    <p><em>Students self-mark. Teacher notes who struggled.</em></p>

    <h4>Book-back Exercise Marking (10-15 min)</h4>
    <p><em>Teacher facilitates step-by-step marking.
    Platform Q&A section has all book-back questions with model answers.</em></p>

    <h5>Section 1: Choose the Correct Answer</h5>
    <p>[3-4 key MCQ answers — explain WHY correct in simple language for Class 6/7.]</p>

    <h5>Section 2: Fill in the Blanks / Match the Following</h5>
    <p>[3-4 key answers — explain connection simply.]</p>

    <h5>Section 3: Short Answer Questions</h5>
    <p>[2-3 model answer structures — simple sentences for Class 6/7.]</p>

    <div class="board-work">
      <strong>Write Answers on Board:</strong><br/>
      [Key answers for student verification]
    </div>

    <h4>Map Work (15-20 min)</h4>
    <p><em>Teacher points on wall map first. Students mark outline maps.</em></p>

    <h5>Map Task 1 — [Primary map task from chapter]</h5>
    <p>[What to locate — simple description for Class 6/7. No page numbers for maps.]</p>

    <div class="board-work">
      <strong>Map Checklist — Mark All:</strong><br/>
      {map_locations if map_locations else '[All map locations from chapter]'}<br/>
      <strong>Memory Tricks:</strong><br/>
      [2-3 simple, fun memory tricks for Class 6/7 students]<br/>
      <em>Label all in CAPITAL LETTERS.</em>
    </div>

    <h5>Map Task 2 — [Secondary map task]</h5>
    <p>[Second set based on actual chapter content.]</p>
  </div>

  <!-- ASSESSMENT (20-30 min) -->
  <div class="lp-section-student-task">
    <strong>[20-30 min] Assessment — 3 Levels (Chapter Review)</strong>

    <div class="lp-teacher-says">"Now let's do a final chapter review. Choose your level."</p>

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
              <p><strong>Task:</strong> Fill in blanks + label map</p>
              <p><strong>Word Bank:</strong> [6 key terms from full chapter]</p>
              <p><em>Teacher sits with this group.</em></p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences each</p>
              <p>[3 core concept questions from full chapter]</p>
            </td>
            <td>
              <p><strong>Task:</strong> Write a short paragraph</p>
              <p>"Explain [key chapter theme] with causes, events, and results in 6-8 sentences."</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ 8 minutes. Teacher circulates.</em></p>
    </div>
  </div>

  <!-- CLOSING (30-35 min) -->
  <div class="lp-section-closing">
    <strong>[30-35 min] Closing</strong>

    <div class="lp-teacher-says">"[2-3 sentences — congratulate students on completing the chapter.
     Name 2-3 specific things learned. Use encouraging language for Class 6/7.
     Motivate for next chapter.]"</p>

    <div class="board-work">
      <strong>Submit before leaving:</strong><br/>
      ☐ Completed notebook — all 5 days of notes<br/>
      ☐ Book-back exercises — answered and marked<br/>
      ☐ Outline map — all locations labeled<br/>
      ☐ All homework from Days 1-4
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <div class="lp-day-block">
- Map tasks based on ACTUAL chapter content
- No Tamil in Day 5
- Page numbers may be referenced
- Age-appropriate language for Class 6/7
- Do NOT generate any other day

Chapter Text:
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ History LP 67 Day 5 error: {e}")
            return None

    # =========================================================================
    # CALL 7 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, sections: dict, day_plan: dict):
        try:
            all_sections = sections.get("chapter_sections", [])
            sections_str = ", ".join([s["heading"] for s in all_sections])
            key_terms    = ", ".join([
                t for s in all_sections for t in s.get("key_terms", [])
            ][:10])

            day_summary = ""
            for d in range(1, 5):
                day_data     = day_plan.get(f"day{d}", {})
                day_sections = day_data.get("sections", [])
                day_summary += f"  Day {d}: {', '.join(day_sections)}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this History chapter (Class 6/7).
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years)
Unit     : {unit}
Subject  : Social Science — History
Total Days: 5

ALL CHAPTER SECTIONS (in order): {sections_str}
KEY TERMS: {key_terms}

DAY-WISE SECTIONS:
{day_summary}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Oral Assessment</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Sections Covered</th>
        <th>Oral Question (English)</th>
        <th>Expected Answer</th>
        <th>Tamil Prompt</th>
      </tr>
    </thead>
    <tbody>
      [5 rows — Day 1 through Day 5.
       Simple, age-appropriate questions for Class 6/7.
       Based on actual sections. Tamil version in last column.]
    </tbody>
  </table>

  <h3>CFU Bank — Quick Reference</h3>
  <p><em>Simple recall questions — 2 per major section — for teacher reference:</em></p>
  <ol>
    [10 CFU questions — 2 per each of the 5 major sections.
     Under 6 words each. What/Who/When/Which format.
     Simple language for Class 6/7.
     Based on actual extracted sections.]
  </ol>

  <h3>CCQ Bank — Deeper Understanding</h3>
  <p><em>8 conceptual questions for revision:</em></p>
  <ol>
    [8 CCQ questions — Why/How/What happened format.
     Age-appropriate for Class 6/7. Under 8 words each.
     Tamil version mentioned. Based on actual chapter content.]
  </ol>

  <h3>Written Assessment Tasks</h3>
  <p>[2-3 meaningful written tasks covering different parts of the chapter.
     Age-appropriate for Class 6/7. Variety: short answer, paragraph, creative.]</p>
  <div class="board-work">
    <strong>Model Answers (write on board):</strong>
    <p>"[Task 1 model — simple sentences from actual chapter content]"</p>
    <p>"[Task 2 model — slightly more detailed]"</p>
  </div>

  <h3>50-Mark Differentiated Worksheet</h3>
  <p><em>Chapter-end worksheet — choose level. All questions from actual chapter content.</em></p>

  <div class="board-work">
    <strong>🟢 Level 1 — Below Average Students (50 marks)</strong><br/>
    Q1-Q10: Fill in the blanks with word bank (1 mark each = 10 marks)<br/>
    Word Bank: [10 key terms from chapter — simple]<br/>
    Q11-Q20: Choose the correct answer — MCQ (1 mark each = 10 marks)<br/>
    Q21-Q25: Match the following (2 marks each = 10 marks)<br/>
    Q26-Q30: Answer in ONE simple sentence (4 marks each = 20 marks)<br/>
    <br/>
    <strong>🟡 Level 2 — Average Students (50 marks)</strong><br/>
    Q1-Q10: Fill in the blanks (1 mark each = 10 marks)<br/>
    Q11-Q20: Choose correct answer (1 mark each = 10 marks)<br/>
    Q21-Q25: Answer in 2-3 sentences (4 marks each = 20 marks)<br/>
    Q26-Q28: Answer in detail — 5 marks each (5 marks each = 10 marks) [wait, that's wrong, fix to sum to 50]<br/>
    <br/>
    <strong>🔴 Level 3 — Toppers / Advanced (50 marks)</strong><br/>
    Q1-Q5: Choose correct answer (1 mark each = 5 marks)<br/>
    Q6-Q15: Answer in 2-3 sentences (2 marks each = 20 marks)<br/>
    Q16-Q20: Answer in detail — 5 marks each (5 marks each = 25 marks)<br/>
    <br/>
    <em>All questions based on actual chapter content. Age-appropriate for Class 6/7.</em>
  </div>

  <h3>Differentiated Assessment</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Below Average (8 mins)<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
        <th>Average Students (8 mins)<br/>(சராசரி மாணவர்கள்)</th>
        <th>Toppers / Advanced (8 mins)<br/>(திறமையான மாணவர்கள்)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Task:</strong> Fill in blanks with word bank</p>
          <p><strong>Word Bank:</strong> [5 simple key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences</p>
          <p>Starter: "[event] happened because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Paragraph / Creative writing</p>
          <p>"Explain [key chapter theme] with causes, events, and consequences in 8-10 sentences."</p>
          <p>OR: "Draw a timeline of [chapter events] and write 1 sentence per event."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in notebook</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Outline map completed and labeled (Day 5)</li>
    <li>☐ Rapid recall quiz attempted (Day 5)</li>
    <li>☐ [Chapter-specific item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table: exactly 5 rows with Tamil column
- CFU bank: 10 questions (2 per section) — simple for Class 6/7
- CCQ bank: 8 questions — age-appropriate
- Written tasks: 2-3 tasks (more than grade 910)
- 50-mark worksheet: 3 levels clearly marked
- Diff table has timing per level
- No page numbers
- Age-appropriate language throughout
- Base everything on actual extracted sections

Chapter Text:
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=6000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ History LP 67 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

history_lp_67_builder = HistoryLP67Builder()