"""
history.py
----------
LP Builder for Samacheer Kalvi Social Science — History
Class 9 & 10

v9.0 — Two-pass Chapter Analyser + all teacher feedback fixes (May 2026)

Changes from v8.0:
  ✅ Two-pass Chapter Analyser:
       Call 0a: Strict Section Extractor — extracts EXACTLY what's in chapter
                Every heading/subheading in order, estimated teaching time
                Pure extraction — NO general knowledge, NO planning
       Call 0b: Smart Day Allocator — allocates sections to days
                Based ONLY on Call 0a output — NO general knowledge
                Each day gets exact section list
  ✅ Each day prompt: "Cover ONLY these sections — if not in list, DO NOT mention"
  ✅ CFU/CCQ: minimum 3 per concept (much stronger enforcement)
  ✅ Differentiated support: explicit timing added per level
  ✅ Homework Day 2: poster/flowchart option added
  ✅ Day headings: must match EXACTLY what's taught that day
  ✅ Topic mismatch impossible — each day only sees its own section list

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
)


# ============================================================================
# HISTORY DISCIPLINE NOTES
# ============================================================================

HISTORY_DISCIPLINE_NOTES = """
HISTORY-SPECIFIC TEACHING NOTES:
- Timeline-based thinking: when → what caused it → what resulted
- Chronology matters — sequence of events must be clear
- Source analysis: use any primary source quote from chapter
- Board flowcharts: Cause → Event → Consequence chains
- Map references as text descriptions — no page numbers
- Maintain main topic → subtopic hierarchy STRICTLY from section list
- Never introduce content not in today's section list
"""


# ============================================================================
# CCQ + CFU INSTRUCTION BLOCK — STRONGER ENFORCEMENT
# ============================================================================

CCQ_CFU_INSTRUCTION = """
═══════════════════════════════════════════════════════
CFU AND CCQ — STRICT MINIMUM REQUIREMENTS
═══════════════════════════════════════════════════════

MINIMUM REQUIREMENT:
- 3 CFU blocks per concept taught (not 1 — MINIMUM 3)
- 3 CCQ blocks per concept taught (not 1 — MINIMUM 3)
- Total minimum: 15 CFUs + 10 CCQs across the full day

WHY 3 PER CONCEPT:
Teachers may forget one question — having 3 ensures at least 1-2 are used.
More questions = more checking = stronger learning.

── CFU (Check For Understanding) ──────────────────────
Basic recall. Asked IMMEDIATELY after explaining something.
Simple, one-word or one-sentence answer.
No Tamil required for CFU.

FORMAT — use EXACTLY this HTML:
<div class="cfu-block">
  <strong>🔎 CFU {number}:</strong>
  <p class="teacher-says">"[Very simple factual question — under 6 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One word or one sentence]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students before moving on.</em></p>
</div>

PLACE 3 CFUs after EACH concept explanation:
  CFU 1 — What/Who/When question
  CFU 2 — Which/Where question
  CFU 3 — Name/State question

── CCQ (Concept Check Question) ───────────────────────
Deeper conceptual question. Tests WHY or HOW.
Tamil version mandatory.

FORMAT — use EXACTLY this HTML:
<div class="ccq-block">
  <strong>⚡ CCQ {number}:</strong>
  <p class="teacher-says">"[Deeper question about concept — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion before taking answers.</em></p>
</div>

PLACE 2-3 CCQs after EACH concept — after the CFUs:
  CCQ 1 — Why did X happen?
  CCQ 2 — What was the effect of Y?
  CCQ 3 — How did Z lead to W?

⚠️ CRITICAL — DO NOT USE ICQs:
❌ WRONG: "Do you understand?" / "How many sentences?" / "Which group are you in?"
✅ RIGHT: "What triggered the assassination?" / "Why did the alliance system spread the war?"

NUMBER YOUR CFUs AND CCQs:
Use CFU 1, CFU 2, CFU 3... and CCQ 1, CCQ 2, CCQ 3...
This helps teachers track and students follow.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# TAMIL INSTRUCTION
# ============================================================================

TAMIL_INSTRUCTION = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING — TARGETED ONLY
═══════════════════════════════════════════════════════
Tamil appears in EXACTLY 3 places:
✅ 1. KEY TERMS TABLE — Tamil meaning column
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph after English
✅ 3. OPENING LEAD QUESTION — Tamil version after English

❌ NEVER in: activity instructions, board work, CFU blocks,
   time notes, closing, homework, differentiated support
Tamil mirror: same sentences, same length, same detail. Real Unicode only.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# HISTORY LP BUILDER CLASS
# ============================================================================

class HistoryLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ History LP Builder (910) v9.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate History LP for Class 9 & 10.
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

        total_calls = 9
        print(f"      [History LP 910 v9] Generating: {lesson_title}")
        print(f"      [History LP 910 v9] 9 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

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
        print(f"      [History LP 910 v9] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — STRICT SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        """
        PASS 1: Extracts EXACTLY what headings and subheadings exist in the chapter.
        Pure extraction — NO planning, NO general knowledge, NO day allocation.
        Returns every section in the order it appears in the text.
        """
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi History chapter.

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
4. Note key terms that appear in that section

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
      "important_dates": ["1914 — event", "1919 — event"]
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
- Extract ALL sections — do not skip any
- If no clear headings exist, use paragraph topic sentences as headings"""

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
            return json.loads(raw)

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
        PASS 2: Takes the extracted sections and allocates them to days.
        Based STRICTLY on the section extractor output.
        NO general knowledge. NO assumptions about chapter content.
        Each day gets 20-25 mins of content (35 min session - 10 min fixed).
        """
        try:
            sections_str = json.dumps(sections, indent=2)

            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi History lesson plan.

YOU HAVE BEEN GIVEN the extracted sections from a chapter.
YOUR ONLY JOB: Allocate these sections to 4 days.

ALLOCATION RULES:
- Each day has 20-25 minutes of content time (35 min session minus 10 min fixed)
- Use estimated_teaching_time_mins from each section to fill each day
- Do NOT split a section across two days — keep each section in ONE day
- If a section is large (>15 mins), it gets its own day or part of a day
- Day 4 must include the FINAL sections and chapter consolidation
- Every section MUST appear in exactly ONE day — no section can be skipped
- No section can appear in two days

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
    "estimated_mins": 20,
    "continuation_from_previous": false
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["subheading 3", "subheading 4"],
    "focus": "One sentence describing what Day 2 covers",
    "estimated_mins": 22,
    "continuation_from_previous": false
  }},
  "day3": {{
    "sections": ["EXACT heading 4", "EXACT heading 5"],
    "subheadings": ["subheading 5"],
    "focus": "One sentence describing what Day 3 covers",
    "estimated_mins": 20,
    "continuation_from_previous": false
  }},
  "day4": {{
    "sections": ["EXACT heading 6", "EXACT heading 7"],
    "subheadings": ["subheading 6", "subheading 7"],
    "focus": "One sentence describing what Day 4 covers + chapter consolidation",
    "estimated_mins": 23,
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
            # Build section summary from extractor
            sections_list = sections.get("chapter_sections", [])
            sections_str  = "\n".join([
                f"  - {s['heading']}: {', '.join(s.get('subheadings', []))}"
                for s in sections_list
            ])

            # Build day plan summary
            day_summary = ""
            for d in range(1, 5):
                day_data    = day_plan.get(f"day{d}", {})
                day_sections = day_data.get("sections", [])
                day_focus    = day_data.get("focus", "")
                day_summary += f"  Day {d}: {', '.join(day_sections)} — {day_focus}\n"

            key_terms      = ", ".join([
                t for s in sections_list for t in s.get("key_terms", [])
            ][:10])
            map_locations  = ", ".join(sections.get("map_locations", []))
            personalities  = ", ".join(sections.get("key_personalities", []))

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — History Lesson Plan. Do NOT generate any Day blocks. Stop after Teaching Aids.

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

1. HEADER BLOCK
<div class="sk-content-header">
  <h1>Lesson Plan — {lesson_title}</h1>
  <p class="sk-meta">
    Class {class_num} | Social Science — History |
    Unit {unit} | 5 Days × 35 Minutes
  </p>
</div>

2. CHAPTER OVERVIEW TABLE
<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Sections Covered
</table>

3. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives — based ONLY on actual chapter sections listed above
</ul>

4. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives: chronology, source analysis, map skills, causal reasoning
  Based on actual chapter content
</ul>

5. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 objectives — based ONLY on actual sections listed above
  Use action verbs: Explain, Analyze, Identify, Evaluate
</ul>

6. TEACHING AIDS
<h2>Part 5: Teaching Aids</h2>
<ul>
  All materials needed — board, chalk, outline maps, timeline strips,
  flowchart templates, flashcards
  Do NOT mention page numbers
</ul>

OUTPUT RULES:
- Raw HTML only
- Start with <div class="sk-content-header">
- Stop after Teaching Aids </ul>
- Do NOT start any Day block
- Base ALL content on actual extracted sections only

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
            print(f"❌ History LP preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2-5 — CONTENT DAYS 1-4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            spark    = SPARK_STYLES[day_num]
            task     = STUDENT_TASK_STYLES[day_num]
            activity = ACTIVITY_MAP.get(day_num, "group discussion")

            # From day allocator — EXACT sections for this day
            day_sections    = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus       = day_data.get("focus", "")
            continuation    = day_data.get("continuation_from_previous", False)

            # Get key terms for this day's sections
            all_sections  = sections.get("chapter_sections", [])
            day_key_terms = []
            for s in all_sections:
                if s["heading"] in day_sections:
                    day_key_terms.extend(s.get("key_terms", []))
                    day_key_terms.extend(s.get("important_dates", []))

            sections_str    = "\n".join([f"  - {s}" for s in day_sections])
            subheadings_str = "\n".join([f"    • {s}" for s in day_subheadings])
            key_terms_str   = ", ".join(day_key_terms[:8])

            # Day 4 closing instruction
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

            # Homework style — Day 2 gets poster/flowchart option
            homework_note = ""
            if day_num == 2:
                homework_note = """
⚠️ HOMEWORK STYLE FOR DAY 2:
Offer students a CHOICE of homework format:
  Option A: Written answer (detail answer format)
  Option B: Poster — draw and label key concepts visually
  Option C: Flowchart — show cause → event → consequence chain
Write all 3 options on board. Students choose based on their strength.
"""

            next_label = f"Day {day_num + 1}" if day_num < 4 else "Day 5 — Map Work and Book-back"

            prompt = f"""Generate ONLY Day {day_num} of the History lesson plan. Nothing else.
Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num}
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
{subheadings_str if subheadings_str else '  [Cover all subheadings under today\'s sections]'}

Day Focus: {day_focus}
Key Terms/Dates for today: {key_terms_str}

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

{CCQ_CFU_INSTRUCTION}

{TAMIL_INSTRUCTION}

═══════════════════════════════════════════════════════
LEAD QUESTION / OPENING QUESTION — DAY {day_num}
═══════════════════════════════════════════════════════
Style: {spark['style']}
{spark['instruction']}
Heading: [0-5 min] Lead Question / Opening Question
Must connect DIRECTLY to today's sections: {', '.join(day_sections)}
Include Big Question at end.
Include: WHY students learn this + WHERE they use it in real life.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
STUDENT TASK — DAY {day_num}: {task['style']}
═══════════════════════════════════════════════════════
{task['instruction']}

DIFFERENTIATED SUPPORT TIMING (add to diff table):
- Slow Learners: 5 minutes (fill blanks with word bank)
- Average Learners: 4 minutes (2-3 sentence answer)
- Advanced Learners: 5 minutes (independent writing)
Teacher circulates to each group during their time.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
FLOWCHART / MODEL RULE
═══════════════════════════════════════════════════════
For every concept with a clear flow:
Include text-based flowchart in <div class="board-work">
Label: "Draw on Board — Model:"
Format: Factor 1 → Event → Consequence → Result
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
NO PAGE NUMBERS
═══════════════════════════════════════════════════════
Do NOT include any page numbers anywhere.
Reference content by section/topic name only.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
WAIT TIME AFTER EVERY QUESTION
═══════════════════════════════════════════════════════
After EVERY question:
<p><em>⏱ Wait [X] seconds. Call on [N] students.</em></p>
CFU → Wait 10 seconds, 2-3 students
CCQ → Wait 15 seconds, pair discussion first
Opening → Wait 20 seconds, 3-5 responses
═══════════════════════════════════════════════════════

DAY STRUCTURE:

<h3 class="day-header">
  Day {day_num} — [Write EXACT section names being taught today — match sections list above]
</h3>
<p class="day-meta">Duration: 35 Minutes | History | {day_focus}</p>

<div class="day-block">

  <!-- ═══ SECTION 1: LEAD QUESTION (0-5 min) ═══ -->
  <div class="time-block">
    <strong>[0-5 min] Lead Question / Opening Question</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — {spark['style']} style.
     Must connect to today's sections: {', '.join(day_sections)}.
     Engaging and real-life. End with Big Question.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same. Same length.]"</p>
    </div>

    <p><em>⏱ Wait 20 seconds. Take 3-5 student responses.</em></p>
  </div>

  <!-- ═══ SECTION 2: INTRODUCTION (5-10 min) ═══ -->
  <div class="time-block">
    <strong>[5-10 min] Introduction & Context Setting</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — introduce today's sections clearly.
     Connect to previous day if applicable.
     Tell students exactly what they cover today.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Today's Sections: {' | '.join(day_sections)}<br/>
      Objective: [One sentence learning objective matching today's sections]
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [5 key terms from TODAY's sections only — with Tamil meanings]
        </tbody>
      </table>
    </div>

    <!-- 3 CFUs after vocab -->
    [CFU 1 — basic question about a key term]
    [CFU 2 — who/what question about today's section]
    [CFU 3 — when/where question about today's section]

  </div>

  <!-- ═══ SECTION 3: MAIN TEACHING (10-25 min) ═══ -->
  <div class="time-block">
    <strong>[10-25 min] Main Teaching & Activity</strong>

    [For EACH section in today's list — in exact order:]

    <h4>[Section heading — EXACTLY as in today's section list]</h4>

    [For EACH subheading under this section:]
    <h5>[Subheading — exactly as extracted]</h5>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain this section/subheading.
     Based ONLY on chapter text — no outside knowledge.
     Include dates, events, causes as they appear in text.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — exact same.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board — Model:</strong><br/>
      [Text-based flowchart: Cause → Event → Consequence → Result]
    </div>

    <!-- 3 CFUs after each concept -->
    <div class="cfu-block">
      <strong>🔎 CFU 1:</strong>
      <p class="teacher-says">"[What/Who/When question — under 6 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>
    <div class="cfu-block">
      <strong>🔎 CFU 2:</strong>
      <p class="teacher-says">"[Which/Where question — under 6 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>
    <div class="cfu-block">
      <strong>🔎 CFU 3:</strong>
      <p class="teacher-says">"[Name/State question — under 6 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>

    <!-- 2-3 CCQs after CFUs -->
    <div class="ccq-block">
      <strong>⚡ CCQ 1:</strong>
      <p class="teacher-says">"[Why did X happen? — under 8 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
      <p><em>⏱ Wait 15 seconds. Pair discussion first.</em></p>
    </div>
    <div class="ccq-block">
      <strong>⚡ CCQ 2:</strong>
      <p class="teacher-says">"[What was the effect of Y? — under 8 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
      <p><em>⏱ Wait 15 seconds. Pair discussion first.</em></p>
    </div>
    <div class="ccq-block">
      <strong>⚡ CCQ 3:</strong>
      <p class="teacher-says">"[How did Z lead to W? — under 8 words]"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
      <p><em>⏱ Wait 15 seconds. Pair discussion first.</em></p>
    </div>

    [Repeat for each section/subheading in today's list]

    <!-- Activity -->
    <div class="activity-block">
      <strong>Activity — {activity}:</strong>
      <p>[Step by step. English only. Based on today's sections only.]</p>
      <p><em>Teacher circulates and checks understanding.</em></p>
    </div>

    <!-- 3 more CFUs after activity -->
    [CFU 4, CFU 5, CFU 6 — about activity content]

  </div>

  <!-- ═══ SECTION 4: STUDENT TASK (25-30 min) ═══ -->
  <div class="time-block">
    <strong>[25-30 min] Student Task — {task['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[Set up task. Specific prompt from today's sections. Clear time limit.]"</p>

    <div class="board-work">
      <strong>Task Prompt (write on board):</strong><br/>
      [Exact prompt students read from board]<br/>
      [Model starter sentence]
    </div>

    <p class="student-says"><strong>Sample Answer:</strong><br/>
    "[2-3 sentences based on actual chapter content from today's sections]"</p>

    [CCQ 4 here]

    <div class="diff-block">
      <strong>Differentiated Support:</strong>
      <table class="diff-table">
        <thead>
          <tr>
            <th>Slow Learners (5 mins)<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
            <th>Average Learners (4 mins)<br/>(சராசரி மாணவர்கள்)</th>
            <th>Advanced Learners (5 mins)<br/>(திறமையான மாணவர்கள்)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p><strong>Task:</strong> Fill in the blanks</p>
              <p>"[sentence] _______ (word1 / word2)"</p>
              <p><strong>Word Bank:</strong> [4 terms from today's sections]</p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>Starter: "[sentence starter from today's content]"</p>
            </td>
            <td>
              <p><strong>Task:</strong> Write independently</p>
              <p>"Explain [key concept from today] in 5 sentences."</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ Teacher circulates to each group during their allocated time.</em></p>
    </div>
  </div>

  <!-- ═══ SECTION 5: CLOSING (30-35 min) ═══ -->
  <div class="time-block">
    <strong>[30-35 min] {"Overall Chapter Recap & Closing" if day_num == 4 else "Closing & Preview"}</strong>

    {"<p><em>⚠️ Day 4 Closing = FULL CHAPTER RECAP across all 4 days.</em></p>" if day_num == 4 else ""}

    <p class="teacher-says"><strong>Rapid-Fire Recap:</strong><br/>
    "{"[5 questions covering ALL sections from ALL 4 days. Full chapter sweep.]" if day_num == 4 else "[3 questions about today's sections only. One word or sentence. Hands raised.]"}"</p>
    <p><em>⏱ Wait 5 seconds per question. Keep energetic.</em></p>

    <div class="board-work">
      <strong>Key Points {"from Full Chapter" if day_num == 4 else "from Today"} (write on board):</strong><br/>
      1. [Key point 1]<br/>
      2. [Key point 2]<br/>
      3. [Key point 3]{"<br/>4. [Key point 4]<br/>5. [Key point 5]" if day_num == 4 else ""}
    </div>

    [Final CCQ 5]

    <div class="homework-block">
      {"<p class='teacher-says'><strong>Homework (choose one format):</strong><br/>Option A: Written answer — explain [key concept from today's sections] in 5 sentences.<br/>Option B: Poster — draw and label the key concepts from today visually.<br/>Option C: Flowchart — show cause → event → consequence chain for today's topic.</p><div class='board-work'><strong>Write all 3 options on board. Students choose their strength.</strong></div>" if day_num == 2 else "<p class='teacher-says'><strong>Homework:</strong><br/>'[Specific prompt from today's sections. Own words. When to submit.]'</p>"}

      <div class="board-work">
        <strong>Homework Model Answer:</strong><br/>
        "[1-2 sentence model]"<br/>
        <em>Write in your own words. Do not copy.</em>
      </div>

      <p class="teacher-says"><strong>Preview {next_label}:</strong><br/>
      "[1-2 sentences — exact sections from Day {day_num + 1 if day_num < 4 else 5} plan.
       Name the actual sections — don't be vague.]"</p>
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS — CRITICAL BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ Day heading matches EXACTLY: {' | '.join(day_sections)}
✅ Covered ONLY sections: {', '.join(day_sections)}
✅ NO sections from other days mentioned
✅ NO general knowledge added — only chapter text used
✅ Minimum 3 CFUs per concept (numbered CFU 1, CFU 2, CFU 3)
✅ Minimum 2 CCQs per concept (numbered CCQ 1, CCQ 2)
✅ Every CFU and CCQ has wait time
✅ Differentiated table has timing (5 mins / 4 mins / 5 mins)
✅ Lead Question heading used — NOT "Spark"
✅ NO page numbers anywhere
✅ Tamil only in: Key Terms + Main explanations + Opening question
✅ Flowchart model in board-work for every concept
✅ Sample answer in student task
{"✅ Day 2 homework has 3 format options (written/poster/flowchart)" if day_num == 2 else ""}
{"✅ Day 4 closing = full chapter recap across all 4 days" if day_num == 4 else f"✅ Preview names exact sections from Day {day_num + 1}"}
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
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
            print(f"❌ History LP Day {day_num} error: {e}")
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
            task          = STUDENT_TASK_STYLES[5]

            prompt = f"""Generate ONLY Day 5 of the History lesson plan.
Day 5: Rapid Recall Quiz → Book-back Marking → Map Work → Test Prep → Closing.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — History
Day      : 5 of 5
Duration : 35 minutes

MAP LOCATIONS: {map_locations if map_locations else 'Identify from chapter text'}
KEY PERSONALITIES: {personalities}
IMPORTANT DATES:
{dates_str if dates_str else '  Identify from chapter text'}

<h3 class="day-header">Day 5 — Map Work & Book-back Exercises</h3>
<p class="day-meta">Duration: 35 Minutes | History | Evaluation Day</p>

<div class="day-block">

  <!-- RAPID RECALL QUIZ (0-5 min) -->
  <div class="time-block">
    <strong>[0-5 min] Rapid Recall Quiz</strong>
    <p class="teacher-says">"5 rapid-fire questions from Days 1-4. Write on slip of paper."</p>
    <div class="board-work">
      <strong>5 Quiz Questions:</strong><br/>
      1. [Factual — Day 1 section content]<br/>
      2. [Factual — Day 2 section content]<br/>
      3. [Factual — Day 3 section content]<br/>
      4. [Factual — Day 4 section content]<br/>
      5. [Key date or personality from chapter]<br/>
      <strong>Answers:</strong> 1.[A] 2.[A] 3.[A] 4.[A] 5.[A]
    </div>
    <p><em>Students self-mark. Teacher notes who struggled.</em></p>
  </div>

  <!-- BOOK-BACK MARKING (5-20 min) -->
  <div class="time-block">
    <strong>[5-20 min] Book-back Exercise Marking</strong>

    <p><em>Teacher facilitates step-by-step marking.
    Note: Platform Q&A section has all book-back questions with model answers.</em></p>

    <h4>Section 1: Choose the Correct Answer</h4>
    <p>[3-4 key MCQ answers — explain WHY correct. Reference section name not page.]</p>

    <h4>Section 2: Fill in the Blanks / Match the Following</h4>
    <p>[3-4 key answers — explain connection. Reference section names.]</p>

    <h4>Section 3: Short Answer Questions</h4>
    <p>[2-3 model answer structures. Reference section names.]</p>

    <div class="board-work">
      <strong>Write Answers on Board:</strong><br/>
      [Key answers for student verification]
    </div>
  </div>

  <!-- MAP TEACHING (20-30 min) -->
  <div class="time-block">
    <strong>[20-30 min] Map Teaching Session</strong>
    <p><em>Teacher points on wall map first. Students mark outline maps.</em></p>

    <h4>Map Task 1 — [Primary map task from chapter content]</h4>
    <p>[Exactly what to locate — countries, cities, regions from chapter text.]</p>

    <div class="board-work">
      <strong>Map Tips & Memory Tricks:</strong><br/>
      [3-5 catchy chapter-specific memory tricks for key locations]<br/>
      <br/>
      <strong>Map Checklist — Mark All:</strong><br/>
      {map_locations if map_locations else '[All map locations from chapter]'}<br/>
      <em>Label all in CAPITAL LETTERS.</em>
    </div>

    <h4>Map Task 2 — [Secondary map task]</h4>
    <p>[Second set based on actual chapter content.]</p>
  </div>

  <!-- TEST PREP (30-35 min) -->
  <div class="time-block">
    <strong>[30-35 min] {task['style']} + Test Prep</strong>

    <p class="teacher-says">"Attempt 2 questions independently — test conditions."</p>
    <div class="board-work">
      <strong>Practice Questions:</strong><br/>
      Q1. [2-mark question — different from book-back]<br/>
      Q2. [5-mark question — different from book-back]<br/>
      <br/>
      <strong>Test Series:</strong><br/>
      <em>Use online question bank for this chapter. Timer for exam readiness.</em>
    </div>

    <p><em>Submit before leaving:</em></p>
    <ul>
      <li>Completed notebook — all 5 days</li>
      <li>Book-back exercises — answered and marked</li>
      <li>Outline map — all locations labeled</li>
      <li>All homework from Days 1-4</li>
      <li>Today's practice questions</li>
    </ul>
  </div>

  <!-- CLOSING -->
  <div class="time-block">
    <strong>Closing</strong>
    <p class="teacher-says">"[2-3 sentences — congratulate students.
     Name 2-3 specific things learned. Motivate for next chapter.]"</p>
  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="day-header">Day 5
- Map tasks based on ACTUAL chapter content
- No Tamil in Day 5
- No page numbers
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
            print(f"❌ History LP Day 5 error: {e}")
            return None

    # =========================================================================
    # CALL 7 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, sections: dict, day_plan: dict):
        try:
            # Build full section list
            all_sections = sections.get("chapter_sections", [])
            sections_str = ", ".join([s["heading"] for s in all_sections])
            key_terms    = ", ".join([
                t for s in all_sections for t in s.get("key_terms", [])
            ][:10])

            # Day summaries
            day_summary = ""
            for d in range(1, 5):
                day_data     = day_plan.get(f"day{d}", {})
                day_sections = day_data.get("sections", [])
                day_summary += f"  Day {d}: {', '.join(day_sections)}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this History chapter.
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num}
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
       Questions about SUBJECT MATTER only — based on actual sections.
       Tamil version in last column.]
    </tbody>
  </table>

  <h3>CFU Bank — Quick Reference (3 per section)</h3>
  <p><em>Basic recall questions — 3 per major section for teacher reference:</em></p>
  <ol>
    [15 CFU questions — 3 per each of the 5 major sections.
     Under 6 words each. What/Who/When/Which/Name format.
     Based on actual extracted sections.]
  </ol>

  <h3>CCQ Bank — Deeper Understanding</h3>
  <p><em>10 conceptual questions for revision:</em></p>
  <ol>
    [10 CCQ questions — Why/How/What happened if format.
     Under 8 words each. Tamil version mentioned.
     Based on actual chapter content.]
  </ol>

  <h3>Written Assessment Task</h3>
  <p>[One meaningful written task covering the full chapter.]</p>
  <div class="board-work">
    <strong>Model Answer (write on board):</strong>
    <p>"[Sentence 1 — from actual chapter content]"</p>
    <p>"[Sentence 2]"</p>
    <p>"[Sentence 3]"</p>
  </div>

  <h3>Differentiated Assessment</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Slow Learners (5 mins)<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
        <th>Average Learners (4 mins)<br/>(சராசரி மாணவர்கள்)</th>
        <th>Advanced Learners (5 mins)<br/>(திறமையான மாணவர்கள்)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Task:</strong> Fill in blanks with word bank</p>
          <p><strong>Word Bank:</strong> [5 key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences</p>
          <p>Starter: "[event] happened because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Structured essay</p>
          <p>"Explain [key chapter theme] with causes, events, consequences in 8-10 sentences."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Outline map completed (Day 5)</li>
    <li>☐ Practice questions attempted (Day 5)</li>
    <li>☐ [Chapter-specific item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table: exactly 5 rows with Tamil column
- CFU bank: 15 questions (3 per section)
- CCQ bank: 10 questions
- Diff table has timing per level
- No page numbers
- Base everything on actual extracted sections

Chapter Text:
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ History LP assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

history_lp_910_builder = HistoryLP910Builder()