"""
history.py
----------
LP Builder for Samacheer Kalvi Social Science — History
Class 8, 9 & 10

v11.1 — Built to match teacher-approved manual LP reference (May 2026)
       Issue 5 fix: Day 4 closing softened to match manual LP style
v11.2 — Tamil scaffolding restored from base TAMIL_INSTRUCTION
v11.3 — Tamil mirror block explicitly added to Topic 1 and Topic 2 explanation templates
v11.4 — Tamil mirror added to Introduction block (matching civics.py pattern)

REFERENCE: Manual LP "Outbreak of World War I and Its Aftermath"
           Built by TNQ/Tutorea.ai teacher team — used as gold standard

STRUCTURE PER DAY (matches manual LP exactly):
  [0-5 min]   Lead / Spark / Opening Question
              → Day 2+ starts with previous day recap
              → Relatable real-life analogy or scenario
              → Big question connecting to today's topic
              → 3-5 students share in large group

  [5-10 min]  Introduction
              → Teacher reads intro from textbook aloud
              → Explains in simple words + real-life example/analogy
              → Write topic + learning objective + page nos on board
              → 1 CFU question from the intro

  [10-20 min] Main Teaching — Topic 1
              → Teacher reads each sub-point from textbook aloud
              → Explains in detail with real-life example per sub-point
              → Draws flowchart/mind map on board WHILE explaining
              → 1-2 CFU questions mid-explanation (woven in, not blocks)
              → Day-specific student activity embedded here

  [20-30 min] Main Teaching — Topic 2
              → Same pattern as Topic 1
              → Day-specific strategy:
                 Day 1: flowchart on board + read aloud + CFU
                 Day 2: group activity (3 groups, 3 questions) + flowchart making
                 Day 3: bucket activity (Red/Yellow/Green groups) + board + map
                 Day 4: narrator role + board listing names/dates + student notes

  [30-35 min] Closing
              → Teacher recap from board (3 rapid-fire questions)
              → Student Task: 2 specific written homework tasks
              → Preview next day (name exact sections)
              → Day 5: submission checklist instead

API calls: 9 total
  Call 0a → Section Extractor  (JSON — all heading levels)
  Call 0b → Day Allocator      (JSON — explicit subheading assignment)
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
    clean,
    PREAMBLE_START_INSTRUCTION,
    TAMIL_INSTRUCTION,
)


# ============================================================================
# TEACHING STRATEGY PER DAY — matches manual LP reference
# ============================================================================

DAY_STRATEGY = {
    1: {
        "spark_style": "Real-life Analogy",
        "spark_instruction": (
            "Use a relatable real-life analogy from Indian student life "
            "(school, family, sports, friendships) to connect to today's topic. "
            "End with a Big Question that links the analogy to the chapter. "
            "Example from manual: 'Imagine you signed a contract that says if your friend "
            "gets into a fight, you must join in — suddenly the whole school is fighting.' "
            "→ Big Question connecting to today's sections."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Reader + Explainer + Board Flowchart Drawer\n"
            "Step 1: Write topic name, learning objective, and page numbers on board.\n"
            "Step 2: Read the section aloud from textbook — sentence by sentence.\n"
            "Step 3: After each sub-point, STOP and explain in simple words.\n"
            "        Add a real-life example or analogy for EACH sub-point.\n"
            "        Example style: 'Just like how [Indian example], this means...'\n"
            "Step 4: Draw a simple flowchart on board WHILE explaining.\n"
            "        Format: Cause → Event → Result → Consequence\n"
            "Step 5: Ask 1-2 CFU questions mid-explanation after each sub-point.\n"
            "        Students answer by raising hands — not writing yet."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Flowchart Facilitator\n"
            "Step 1: Paste or draw a prepared flowchart on board.\n"
            "Step 2: Read aloud and explain with textbook reference.\n"
            "Step 3: Ask 2 students to explain the flowchart back in their own words.\n"
            "Step 4: Students take active notes in notebook.\n"
            "        Teacher circulates and checks notes."
        ),
        "activity": (
            "STUDENT ACTIVITY (embedded in Topic 2):\n"
            "Ask 2 students to come to the board and explain the flowchart back to the class.\n"
            "Rest of class listens and adds any missed points.\n"
            "Teacher corrects and adds final key points."
        ),
    },
    2: {
        "spark_style": "Previous Day Recap + Real-life Connection",
        "spark_instruction": (
            "START with a 1-minute recap: Ask students what they learned yesterday. "
            "Call on 2-3 students to name one topic each. "
            "THEN give a relatable question connecting to today's new topics. "
            "Example from manual: 'What are reasons for a fight between friends in class? "
            "Likewise there are causes for World War I — let's discuss.' "
            "4-5 students share opinions in large group."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Flowchart Explainer + Group Facilitator\n"
            "Step 1: Draw/display flowchart on board for today's topic.\n"
            "Step 2: Explain the flowchart using textbook — sub-point by sub-point.\n"
            "Step 3: Students take active notes while teacher explains.\n"
            "Step 4: GROUP ACTIVITY — divide class into 3 groups (5 mins):\n"
            "        Write 3 questions on board — one per group.\n"
            "        Each group answers their question using notes + textbook.\n"
            "        One student per group shares answer with class.\n"
            "        Teacher adds key points to board after sharing.\n"
            "Step 5: 2 CFU questions after group sharing."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Flowchart Explainer + Creative Task Giver\n"
            "Step 1: Draw/explain flowchart for Topic 2 from textbook.\n"
            "Step 2: Ask 3-4 CFU questions mid-explanation:\n"
            "        Write them on board — students answer by raising hands.\n"
            "Step 3: STUDENT CREATIVE TASK (embedded):\n"
            "        'Go through the textbook section. Then prepare your own\n"
            "         flowchart of [topic] — as creative as you can.'\n"
            "        Students draw in notebook — 3 minutes.\n"
            "        Teacher circulates and gives feedback."
        ),
        "activity": (
            "GROUP ACTIVITY (3 groups, embedded in Topic 1):\n"
            "3 groups answer 3 different questions from today's content.\n"
            "Questions written on board — taken directly from the sections.\n"
            "Each group discusses using notes + textbook — 3 minutes.\n"
            "One student per group shares with class.\n"
            "Teacher consolidates key points on board."
        ),
    },
    3: {
        "spark_style": "Student Recap Leader + Moral Dilemma",
        "spark_instruction": (
            "START by asking a student leader to briefly recap yesterday's key topic "
            "(one student stands up and recaps in 3-4 sentences). "
            "THEN give a moral dilemma or ethical question connecting to today's content. "
            "Example from manual: 'If a group project fails because of one person's choice, "
            "is it fair to make that one person pay for everyone's losses?' "
            "Students think and share in pairs — then one large group response if time permits."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Board Recorder + Map Facilitator\n"
            "BUCKET ACTIVITY — divide class into 3 colored groups:\n"
            "  Group 1 (Red Bucket): Find [Social Impact points] from textbook section\n"
            "  Group 2 (Yellow Bucket): Find [Political Shifts] from textbook section\n"
            "  Group 3 (Green Bucket): Find [Economic/Other Impact] from textbook section\n"
            "Each group reads their textbook section and finds specific evidence.\n"
            "As groups present, teacher writes points in 3 colored areas on board.\n"
            "Teacher points to relevant locations on wall map simultaneously.\n"
            "2 CFU questions after group presentations."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Map Facilitator + Direct Explainer\n"
            "Step 1: Teacher explains Topic 2 using textbook — sub-point by sub-point.\n"
            "Step 2: Point to wall map for geographic references.\n"
            "        Circle or label key locations on board sketch.\n"
            "Step 3: Explain each sub-point with specific facts and numbers from text.\n"
            "Step 4: 2-3 CFU questions mid-explanation.\n"
            "        Students answer by raising hands."
        ),
        "activity": (
            "BUCKET ACTIVITY (embedded in Topic 1):\n"
            "3 colored groups each find specific evidence from their textbook section.\n"
            "Red Bucket: Social/Human impact\n"
            "Yellow Bucket: Political changes\n"
            "Green Bucket: Economic/India impact\n"
            "Groups present — teacher records on board in 3 colored areas.\n"
            "Teacher uses wall map to show geographic context."
        ),
    },
    4: {
        "spark_style": "Map Recall + Emotional Hook",
        "spark_instruction": (
            "START with a quick map/fact recall: 'Yesterday we saw changes. "
            "Who remembers one specific change? — call on 3 students.' "
            "THEN give an emotional hook or powerful scenario connecting to today's topic. "
            "Example from manual: 'Imagine you are hungry, cold, and at war. "
            "One leader says Keep fighting. Another says Bread, Peace, and Land. "
            "Which one do you follow?' "
            "Students get 30 seconds to consolidate answer — then 3 share with class."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Narrator and Guide\n"
            "Step 1: Write topic name and ALL sub-topics on board first.\n"
            "        Students see the full structure before teaching starts.\n"
            "Step 2: For each sub-topic — read aloud from textbook.\n"
            "Step 3: Narrate and explain with key names and dates written on board.\n"
            "        Bold every KEY NAME and DATE as you write it.\n"
            "        Add a brief real-life connection for complex concepts.\n"
            "Step 4: Students take active notes — teacher pauses for notes after each sub-topic.\n"
            "Step 5: 1 CFU question after each sub-topic (3 sub-topics = 3 CFU questions).\n"
            "        Students answer by raising hands."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Structure Guide + Discussion Facilitator\n"
            "Step 1: Write all sub-topics on board first.\n"
            "Step 2: For each sub-topic — read aloud and explain with textbook.\n"
            "Step 3: Note key facts, dates, names on board as you go.\n"
            "Step 4: 1 CFU question per sub-topic.\n"
            "Step 5: At end — ask 2 students to summarise the full topic in 2 sentences each."
        ),
        "activity": (
            "STUDENT NOTES + NARRATION (embedded throughout):\n"
            "Teacher pauses after each sub-topic for students to write notes.\n"
            "At end of each main topic: 1 student narrates back the sub-topic.\n"
            "Teacher corrects and reinforces on board."
        ),
    },
}


# ============================================================================
# HISTORY LP BUILDER CLASS
# ============================================================================

class HistoryLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ History LP Builder (910) v11.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [History LP 910 v11] Generating: {lesson_title}")
        print(f"      [History LP 910 v11] 9 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

        parts = []

        # Call 0a
        print(f"      [History LP] Call 0a/9: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        # Call 0b
        print(f"      [History LP] Call 0b/9: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        # Call 1
        print(f"      [History LP] Call 1/9: Preamble...")
        preamble = self._call_preamble(text, class_num, unit, lesson_title, month, sections, day_plan)
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting")
            return None

        # Calls 2-5: Days 1-4
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

        # Call 6: Day 5
        print(f"      [History LP] Call 6/9: Day 5...")
        day5_html = self._call_day5(text, class_num, unit, lesson_title, sections, day_plan)
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # Call 7: Assessment
        print(f"      [History LP] Call 7/9: Assessment...")
        assessment = self._call_assessment(text, class_num, unit, lesson_title, sections, day_plan)
        if assessment:
            parts.append(clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [History LP 910 v11] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi History chapter.

YOUR ONLY JOB: Extract EVERY heading and subheading that appears in the chapter text.
Capture ALL levels:
  Level 1: Main headings
  Level 2: Subheadings under each main heading
  Level 3: Sub-subheadings if present

ABSOLUTE RULES:
- Copy EVERY heading EXACTLY as written — do NOT paraphrase
- Do NOT skip any heading or subheading — extract ALL of them in order
- Do NOT add anything from general knowledge
- Estimate teaching time per section based on content length
- Capture key terms, dates, personalities per section
- A chapter with 40,000+ characters MUST have at least 10-15 sections
- Every paragraph topic is a section if no clear heading exists
- Sub-subheadings like "In the Middle East", "In the Far East", "In the Balkans"
  must be extracted as separate subheadings — never merge them into one

Chapter: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "chapter_sections": [
    {{
      "heading": "EXACT Level 1 heading",
      "subheadings": [
        {{
          "title": "EXACT Level 2 subheading",
          "sub_subheadings": ["EXACT Level 3 if present"]
        }}
      ],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "has_map_content": false,
      "important_dates": ["1914 — event"]
    }}
  ],
  "total_estimated_teaching_mins": 70,
  "map_locations": ["location1"],
  "key_personalities": ["Person 1"],
  "important_dates": ["date — event"]
}}

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system="""You are a strict text extractor. Return ONLY valid JSON.
Extract ALL headings at ALL levels — minimum 10 sections expected for a full chapter.
Never skip any heading or subheading.
Never add general knowledge. No markdown. No code fences. Raw JSON starting with {""",
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
    # CALL 0b — DAY ALLOCATOR
    # =========================================================================

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        try:
            sections_str = json.dumps(sections, indent=2)
            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi History lesson plan.

Allocate ALL sections AND subheadings to exactly 4 days.

RULES:
- Each day: 20-25 minutes of content (35 min session minus 10 min opening/closing)
- Keep each main section in ONE day — do NOT split across days
- Keep subheadings WITH their main section
- EVERY section AND subheading must appear in exactly ONE day
- Day 4 must include the FINAL sections and chapter consolidation
- MAXIMUM 3 subheadings per day — if a section has more, split across 2 days
- Day 3 must never have more than 3 subheadings — it is always the heaviest day
- If total subheadings exceed 12, redistribute evenly — max 3 per day
- Sections must follow STRICT CHRONOLOGICAL ORDER from the chapter text
- Never move a later section to an earlier day — always follow text order
- Day 1 covers ONLY the first sections — never jump ahead
- NEVER assign the same section to two different days
- NEVER leave Day 4 with more than 2 main sections
- Every section must appear in EXACTLY one day — no duplicates, no omissions
- If a section is large (>15 mins), give it its own day
- Use EXACT heading text from extracted sections

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "day1": {{
    "sections": ["EXACT heading 1", "EXACT heading 2"],
    "subheadings": ["EXACT subheading 1", "EXACT subheading 2"],
    "focus": "One sentence — what Day 1 covers",
    "estimated_mins": 22
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["EXACT subheading 3", "EXACT subheading 4"],
    "focus": "One sentence — what Day 2 covers",
    "estimated_mins": 20
  }},
  "day3": {{
    "sections": ["EXACT heading 4", "EXACT heading 5"],
    "subheadings": ["EXACT subheading 5", "EXACT subheading 6"],
    "focus": "One sentence — what Day 3 covers",
    "estimated_mins": 23
  }},
  "day4": {{
    "sections": ["EXACT heading 6", "EXACT heading 7"],
    "subheadings": ["EXACT subheading 7", "EXACT subheading 8"],
    "focus": "One sentence — what Day 4 covers + consolidation",
    "estimated_mins": 22
  }}
}}

Extracted Sections:
---
{sections_str}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=2500,
                system="You are a strict day allocator. Return ONLY valid JSON. No markdown. Raw JSON starting with {",
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

            sections_str = ""
            for s in sections_list:
                sections_str += f"  ▸ {s['heading']}\n"
                for sub in s.get("subheadings", []):
                    title = sub.get("title", sub) if isinstance(sub, dict) else sub
                    sections_str += f"      • {title}\n"

            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))} — {d_data.get('focus','')}\n"

            key_terms     = ", ".join([t for s in sections_list for t in s.get("key_terms", [])][:12])
            map_locations = ", ".join(sections.get("map_locations", []))
            personalities = ", ".join(sections.get("key_personalities", []))

            prompt = f"""Generate ONLY the preamble section of this History Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — History
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

ALL CHAPTER SECTIONS (extracted from text):
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY TERMS: {key_terms}
MAP LOCATIONS: {map_locations}
KEY PERSONALITIES: {personalities}

Generate EXACTLY these sections in this order:

<h2>Part 1: Chapter Overview</h2>
Table: Class | Subject | Discipline | Unit/Chapter Title | Month |
       Total Teaching Hours | Session Duration | Main Sections Covered

<h2>Part 2: Value-Based Objectives</h2>
4 value objectives based on actual chapter content (like the manual LP):
  Social Justice, Peace, Global Cooperation, Empathy — adapted to this chapter

<h2>Part 3: Skill Objectives</h2>
4 skill objectives: Map Skills, Source Analysis, Chronology, Causal Reasoning
Customised to this specific chapter's content

<h2>Part 4: Learning Objectives</h2>
4-5 objectives with action verbs (Explain, Analyze, Evaluate, Identify)
Based ONLY on actual sections in this chapter

<h2>Part 5: Teaching Aids</h2>
All materials: board, chalk, outline maps, flowchart templates,
wall map, timeline strips, textbooks, notebooks
No page numbers. Based on chapter content.

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids

Chapter Text (reference):
---
{text[:3000]}
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
            strategy = DAY_STRATEGY[day_num]

            day_sections    = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus       = day_data.get("focus", "")

            # Get page nos + key terms for this day
            all_sections  = sections.get("chapter_sections", [])
            day_key_terms = []
            day_dates     = []
            for s in all_sections:
                if s["heading"] in day_sections:
                    day_key_terms.extend(s.get("key_terms", []))
                    day_dates.extend(s.get("important_dates", []))

            sections_str    = "\n".join([f"  ▸ {s}" for s in day_sections])
            subheadings_str = "\n".join([f"      • {s}" for s in day_subheadings])
            key_terms_str   = ", ".join(day_key_terms[:10])
            dates_str       = "\n".join([f"  - {d}" for d in day_dates[:8]])

            # Next day preview
            if day_num < 4:
                next_data     = day_plan.get(f"day{day_num+1}", {})
                next_sections = next_data.get("sections", [])
                next_preview  = f"Day {day_num+1}: {', '.join(next_sections)}"
            else:
                next_preview  = "Day 5: Map Work and Book-back Exercises"

            # Day 4 closing note
            closing_note = ""
            if day_num == 4:
                closing_note = """
DAY 4 CLOSING NOTE:
Recap from board covering today's sections.
Student task: one substantial writing task (essay or structured answer on today's content).
Remind students to bring classwork notebook and outline map tomorrow for Day 5.
"""

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi History Lesson Plan.

REFERENCE: This LP must match the style of a teacher-approved manual LP.
The manual LP style is: read aloud → explain with examples → flowchart on board →
CFU questions woven in → student activity → closing with homework.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — History
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S SECTIONS — COVER ALL IN ORDER
═══════════════════════════════════════════════════════
Main sections:
{sections_str}

Subheadings (ALL must be taught):
{subheadings_str}

Day Focus: {day_focus}
Key Terms: {key_terms_str}
Key Dates:
{dates_str if dates_str else "  (identify from chapter text)"}
{closing_note}
═══════════════════════════════════════════════════════
CRITICAL RULES — READ BEFORE GENERATING
═══════════════════════════════════════════════════════

1. COVER ALL SECTIONS AND SUBHEADINGS:
   - Every section and subheading listed above MUST be taught
   - Teach them IN ORDER as listed
   - Do NOT skip any subheading
   - Do NOT add sections not in the list

2. EXPLANATION QUALITY (most important feedback):
   - Teacher must NOT just read the textbook — they must EXPLAIN
   - After reading each sub-point aloud: give a detailed explanation
   - Add a real-life example or analogy for EACH sub-point
     Examples: "Just like how India and Pakistan have border tensions..."
               "Think of it like a company merger where..."
               "Similar to how a class monitor has authority but no power to punish..."
   - Use Indian context examples wherever possible
   - Explanation must be detailed enough that a new teacher understands

3. CFU QUESTIONS (woven into explanation — not separate blocks):
   - After EACH sub-point explanation: ask 1-2 CFU questions
   - Write CFU questions on board
   - Students answer by raising hands
   - Format: <p class="cfu-inline"><strong>Teacher asks:</strong> "[question]?"
     <em>(Students raise hands — call on 2-3 before continuing)</em></p>

4. FLOWCHART ON BOARD:
   - Every main topic must have a flowchart drawn on board WHILE explaining
   - Format: Term/Cause → Event → Result → Consequence
   - Draw it step by step as you explain — not all at once
   - Students copy into their notebooks

5. STUDENT ACTIVITY:
   - Activity must be EMBEDDED inside the main teaching — not a separate block
   - Day-specific strategy: {strategy['topic1_strategy'][:100]}...

{TAMIL_INSTRUCTION}

═══════════════════════════════════════════════════════
CFU AND CCQ — STRICT RULES
═══════════════════════════════════════════════════════
CFU = Basic recall — immediately after each sub-point explanation.
CCQ = Deeper Why/How — after CFUs, Tamil version mandatory.

CFU FORMAT:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <p class="teacher-says">"[Simple factual question — under 6 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

CCQ FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="teacher-says">"[Why/How question — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Pair discussion first.</em></p>
</div>

MINIMUM PER DAY: 5 CFU blocks + 5 CCQ blocks
Place after EVERY sub-point explanation — not at end.
❌ NEVER use ICQs ("Do you understand?" / "How many sentences?")
═══════════════════════════════════════════════════════

7. PAGE NUMBERS:
   - Do NOT mention any page numbers anywhere in the lesson plan
   - Reference content by section/topic name only

8. SPELLING:
   - Check all English words are spelled correctly before finishing

═══════════════════════════════════════════════════════
DAY {day_num} TEACHING STRATEGY
═══════════════════════════════════════════════════════
SPARK STYLE: {strategy['spark_style']}
SPARK INSTRUCTION: {strategy['spark_instruction']}

TOPIC 1 STRATEGY:
{strategy['topic1_strategy']}

TOPIC 2 STRATEGY:
{strategy['topic2_strategy']}

STUDENT ACTIVITY:
{strategy['activity']}
═══════════════════════════════════════════════════════

GENERATE Day {day_num} using EXACTLY this HTML structure:

<h3 class="day-header">Day {day_num} — [Exact section names taught today]</h3>

<div class="day-meta-table">
  <table>
    <tr>
      <th>Learning Objective</th>
      <td>[Specific objective for today's sections — action verb + what students will do]</td>
      <th>Focus</th>
      <td>{day_focus}</td>
    </tr>
  </table>
</div>

<div class="day-block">

  <!-- ═══ [0-5 min] LEAD / SPARK / OPENING QUESTION ═══ -->
  <div class="time-block">
    <h4>[0-5 min] Lead / Spark / Opening Question</h4>

    {"<!-- Day 2+: Start with previous day recap -->" if day_num > 1 else ""}
    {"<p class='recap-note'><strong>Quick Recap (1 min):</strong> Ask 2-3 students: What did we learn yesterday? Name one topic each.</p>" if day_num > 1 else ""}

    <p class="teacher-says"><strong>Teacher says:</strong><br/>
    "[{strategy['spark_style']} — 3-4 sentences. Relatable Indian context analogy.
     Connects directly to today's sections: {', '.join(day_sections)}.
     Ends with a Big Question.]"</p>

    <p class="lead-tamil"><em>தமிழில்:</em> "[Same opening question in Tamil — context-based translation]"</p>

    <p class="student-response"><em>3-5 students share their opinions in large group.
    Teacher acknowledges each response without correcting — builds curiosity.</em></p>
  </div>

  <!-- ═══ [5-10 min] INTRODUCTION ═══ -->
  <div class="time-block">
    <h4>[5-10 min] Introduction</h4>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Topic: [today's section names]<br/>
      Objective: [today's learning objective]
    </div>

    <p class="teacher-says"><strong>Teacher says (Introduction — English):</strong><br/>
    "[Teacher reads the introduction paragraph from textbook aloud.
     Then explains in simple words — 3-4 sentences.
     Add one real-life example: 'Just like [Indian example]...'
     Connect to the Big Question from the spark.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same introduction. Same length. Same example.
          Context-based Tamil — NOT word-for-word. Pure Tamil Unicode only.]"</p>
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead><tr><th>Term</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
        <tbody>
          [5-6 key terms from today's sections with clear meanings and Tamil]
        </tbody>
      </table>
    </div>

    <p class="cfu-inline"><strong>Teacher asks:</strong>
    "According to the textbook, what is the main topic we are studying today?
    Can anyone explain in your own words?"
    <em>(Call on 2 students before continuing)</em></p>
  </div>

  <!-- ═══ [10-20 min] MAIN TEACHING — TOPIC 1 ═══ -->
  <div class="time-block">
    <h4>[10-20 min] [EXACT name of first section from today's list]</h4>

    <p class="teacher-role"><em>Teacher Role: {strategy['topic1_strategy'].split(chr(10))[0]}</em></p>

    [FOR EACH subheading under this section — in exact order:]

    <h5>[EXACT subheading name]</h5>

    <p class="teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
    "[Teacher reads this sub-point from textbook.
     Then explains in simple clear language — 3-4 sentences.
     REAL-LIFE EXAMPLE: 'Just like [specific Indian/relatable example],
     this means that [explanation connecting example to content]...'
     Include specific facts, dates, names from the textbook.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[EXACT same explanation in Tamil — sentence by sentence mirror.
          Same length. Same detail. Same real-life example in Tamil.
          Context-based Tamil — NOT word-for-word translation.
          Pure Tamil Unicode — no Hindi words, no transliteration.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board (step by step while explaining):</strong><br/>
      [Simple flowchart: Key Term → Cause/Event → Result]<br/>
      [Draw each arrow as you explain each step — not all at once]
    </div>

    <div class="cfu-block">
      <strong>🔎 CFU:</strong>
      <p class="teacher-says">"[Short factual question — under 6 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or one sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>

    <div class="cfu-block">
      <strong>🔎 CFU:</strong>
      <p class="teacher-says">"[Which/Where question — under 6 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or one sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ:</strong>
      <p class="teacher-says">"[Why or How question about this sub-point — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
      <p><em>⏱ Wait 15 seconds. Pair discussion first.</em></p>
    </div>

    [REPEAT for each subheading under section 1]

    <!-- Embedded activity for Topic 1 -->
    <div class="activity-block">
      <strong>Activity ({strategy['activity'].split(chr(10))[0]}):</strong>
      <p>[Step by step activity instructions from the day strategy.
         Based on today's section content only.
         Students are active — reading, discussing, drawing, presenting.]</p>
    </div>

  </div>

  <!-- ═══ [20-30 min] MAIN TEACHING — TOPIC 2 ═══ -->
  <div class="time-block">
    <h4>[20-30 min] [EXACT name of second section from today's list]</h4>

    <p class="teacher-role"><em>Teacher Role: {strategy['topic2_strategy'].split(chr(10))[0]}</em></p>

    [FOR EACH subheading under this section — in exact order:]

    <h5>[EXACT subheading name]</h5>

    <p class="teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
    "[Teacher reads sub-point from textbook.
     Explains in simple language — 3-4 sentences.
     REAL-LIFE EXAMPLE for this sub-point.
     Specific facts, names, dates from text.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[EXACT same explanation in Tamil — sentence by sentence mirror.
          Same length. Same detail. Same real-life example in Tamil.
          Context-based Tamil — NOT word-for-word translation.
          Pure Tamil Unicode — no Hindi words, no transliteration.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      [Key names/dates to write on board as you explain]<br/>
      [Flowchart if applicable]
    </div>

    <p class="cfu-inline"><strong>Teacher asks:</strong> "[Question about this sub-point]?"
    <em>(Write on board. Call on 2 students.)</em></p>

    [REPEAT for each subheading under section 2]

  </div>

  <!-- ═══ [25-30 min] STUDENT TASK — MANDATORY — NEVER SKIP ═══ -->
  <!-- If running long — reduce CFU/CCQ count but NEVER remove this block -->
  <div class="time-block">
    <h4>[25-30 min] Student Task (Homework)</h4>
    <p class="teacher-says"><strong>Teacher says:</strong><br/>
    "Write both tasks in your homework book. Submit tomorrow morning.
     Use your own words — do not copy from textbook."</p>
    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Task 1: [Specific written task from today's sections — paragraph or short answer]<br/>
      Task 2: [Creative task — flowchart OR poster OR headline based on today's content]<br/>
      Submit: Tomorrow morning
    </div>
  </div>

  <!-- ═══ [30-35 min] CLOSING ═══ -->
  <div class="time-block">
    <h4>[30-35 min] Closing{"" if day_num < 4 else " — Full Chapter Recap"}</h4>

    <p class="teacher-says"><strong>Recap from Board:</strong><br/>
    "[3 quick questions covering today's sections. Students call out answers.]"</p>

    <div class="board-work">
      <strong>Key Points on Board{"" if day_num < 4 else " (Full Chapter Summary)"}:</strong><br/>
      1. [Key point 1 from today]<br/>
      2. [Key point 2 from today]<br/>
      3. [Key point 3 from today]<br/>
      {"4. [Key point 4]<br/>5. [Key point 5]" if day_num == 4 else ""}
    </div>

    <p class="teacher-says"><strong>Closing Statement:</strong><br/>
    "[2 sentences — what was covered. Connect to bigger picture.
     Preview what comes next.]"</p>

    <div class="homework-block">
      <strong>Student Task (Homework):</strong>
      <p class="teacher-says">"Write this in your homework book and submit tomorrow morning.
      Use your own words — do not copy from the textbook."</p>
      <div class="board-work">
        <strong>Write on Board:</strong><br/>
        Task 1: [Specific written task — paragraph or short answer about today's content]<br/>
        Task 2: [Creative task — flowchart OR poster OR headline OR essay
                 based on today's sections]<br/>
        Submit: Tomorrow morning
      </div>
      {"<p><em>Preview: Tomorrow we cover — " + next_preview + "</em></p>" if day_num < 4 else ""}
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ ALL sections covered: {', '.join(day_sections)}
✅ ALL subheadings covered: {', '.join(day_subheadings)}
✅ EVERY subheading has full explanation — nothing summarised or skipped
✅ If a subheading has sub-points in the text — ALL sub-points are taught
✅ Do NOT stop generating until ALL subheadings in today's list are fully covered
✅ If running long — reduce CFU/CCQ count slightly but NEVER skip a subheading
✅ Every sub-point has: read aloud → explanation → real-life example → CFU
✅ Flowchart drawn on board for every main concept
✅ CFU questions written as cfu-inline — woven into explanation
✅ Student activity embedded inside main teaching (not a separate block at end)
✅ Closing is PRESENT and COMPLETE with 2 homework tasks on board
✅ {"Day 4: full chapter recap across all 4 days" if day_num == 4 else f"Preview names exact sections: {next_preview}"}
✅ Tamil ONLY in: Key Terms table + Opening Question
✅ Page numbers mentioned in learning objective table and board work
✅ No general knowledge — only chapter text used
✅ NEVER use religious references in any real-life example — no religion, no god, no faith
✅ NEVER mention specific student names — use "a student" or "Student A" only
✅ All English words spelled correctly
✅ Student Task block is PRESENT and COMPLETE — never skip this section
✅ Closing block is PRESENT and COMPLETE — never skip this section
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ Do NOT generate Day {day_num+1}

Chapter Text (use ONLY this — no general knowledge):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=16000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ History LP Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — DAY 5: MAP + BOOK-BACK + WORKSHEET
    # =========================================================================

    def _call_day5(self, text, class_num, unit, lesson_title,
                   sections: dict, day_plan: dict):
        try:
            map_locations = ", ".join(sections.get("map_locations", []))
            personalities = ", ".join(sections.get("key_personalities", []))
            dates_str     = "\n".join([f"  - {d}" for d in sections.get("important_dates", [])])

            all_section_names = [s["heading"] for s in sections.get("chapter_sections", [])]
            day_summaries = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summaries += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"
                subs = d_data.get("subheadings", [])
                if subs:
                    day_summaries += f"    Subs: {', '.join(subs[:3])}\n"

            prompt = f"""Generate ONLY Day 5 of the History Lesson Plan.
Day 5 = Book-back Marking → Map Work → Closing.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Day      : 5 of 5 — Map and Notes Day
Duration : 35 minutes

ALL CHAPTER SECTIONS:
{chr(10).join([f"  - {s}" for s in all_section_names])}

DAY-WISE SUMMARY:
{day_summaries}

MAP LOCATIONS: {map_locations}
KEY PERSONALITIES: {personalities}
IMPORTANT DATES:
{dates_str if dates_str else "  (from chapter text)"}

<h3 class="day-header">Day 5 — Map Work and Book-back Exercises</h3>

<div class="day-meta-table">
  <table>
    <tr>
      <th>Learning Objectives</th>
      <td>Evaluate understanding through book-back exercises.
      Identify and locate key places on map.</td>
    </tr>
  </table>
</div>

<div class="day-block">

  <!-- [0-20 min] BOOK-BACK MARKING -->
  <div class="time-block">
    <h4>[0-20 min] Book-Back Exercise Marking and Discussion</h4>
    <p class="teacher-role"><em>Teacher facilitates step-by-step marking.
    Students swap notebooks or self-mark while teacher explains logic behind each answer.</em></p>
    <p><em>⚠️ Note to Teacher: All book-back questions with model answers are available
    in the QA section of this platform. Open the QA section for this chapter
    to get complete answers for every book-back exercise.</em></p>

    <h5>Section 1: Choose the Correct Answer</h5>
    <p>[For each MCQ answer: identify the key figure/date/event being tested.
     Explain WHY the correct answer is right — reference section name from chapter.
     Briefly discuss common wrong answers.]</p>

    <h5>Section 2: Fill in the Blanks / Match the Following</h5>
    <p>[For each answer: explain the connection to the chapter.
     Review key pairings (e.g. treaty → outcome, person → role).
     Students highlight the relevant line in their textbook.]</p>

    <h5>Section 3: Short Answer Questions</h5>
    <p>[For 3-4 key short answers: give model answer structure.
     Students compare with their own answer.
     Teacher points to the section in textbook where answer is found.]</p>

    <div class="board-work">
      <strong>Key Answers on Board:</strong><br/>
      [Write main answers for student verification]
    </div>
  </div>

  <!-- [20-35 min] MAP TEACHING -->
  <div class="time-block">
    <h4>[20-35 min] Map Teaching Session</h4>
    <p class="teacher-role"><em>Teacher Action: Point on wall map first.
    Students then mark their own outline maps.</em></p>

    <h5>Map Task 1 — [Primary map task based on chapter content]</h5>
    <p>[Exactly what to locate and label. Countries, cities, regions from chapter.
     Teacher points to wall map → students mark outline maps.]</p>

    <div class="board-work">
      <strong>Map Checklist — Mark All These:</strong><br/>
      {map_locations if map_locations else "[All map locations from chapter]"}<br/>
      <br/>
      <strong>Memory Tips:</strong><br/>
      [3-4 catchy memory tricks specific to this chapter's locations]<br/>
      <em>Label all locations in CAPITAL LETTERS.</em>
    </div>

    <h5>Map Task 2 — [Secondary map task from chapter]</h5>
    <p>[Second set of locations or a different type of map task
     (e.g. India map, battle sites, territorial changes).]</p>
  </div>

  <!-- CLOSING -->
  <div class="time-block">
    <h4>Closing</h4>
    <p class="teacher-says"><strong>Teacher says:</strong><br/>
    "[Congratulate students on completing the chapter.
     Name 2-3 specific things they learned across all 5 days.
     Motivate for next chapter.]"</p>

    <div class="board-work">
      <strong>All Students Must Submit:</strong><br/>
      ☐ Notebook — all 5 days of notes completed<br/>
      ☐ Book-back exercises — answered and marked<br/>
      ☐ Outline map — all locations labeled neatly<br/>
      ☐ All homework from Days 1-4
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="day-header">Day 5
- Book-back section must have real content from chapter
- Map tasks based on actual chapter locations
- No Tamil in Day 5
- No page numbers needed — reference section names only
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
            all_sections = sections.get("chapter_sections", [])
            sections_str = ", ".join([s["heading"] for s in all_sections])
            key_terms    = ", ".join([t for s in all_sections for t in s.get("key_terms", [])][:12])

            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this History chapter.
Do NOT repeat day content. Do NOT generate day blocks.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
All Sections: {sections_str}
Key Terms: {key_terms}

Day-wise:
{day_summary}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Oral Assessment Questions</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Sections Covered</th>
        <th>Assessment Question</th>
        <th>Expected Answer</th>
        <th>Tamil Prompt</th>
      </tr>
    </thead>
    <tbody>
      [5 rows — Day 1 to Day 5.
       One content-based question per day from actual sections.
       Tamil version in last column — context-based natural Tamil.]
    </tbody>
  </table>

  <h3>CFU Question Bank (3 per main section)</h3>
  <p><em>Quick recall questions — 3 per major section for teacher reference:</em></p>
  <ol>
    [15 CFU questions — 3 per each of the 5 major sections.
     Under 6 words. What/Who/When/Which/Name.
     Based on actual extracted sections only.]
  </ol>

  <h3>Written Assessment Tasks — 3 Levels</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Foundation Level<br/>(Slow Learners)</th>
        <th>Standard Level<br/>(Average Learners)</th>
        <th>Advanced Level<br/>(Toppers)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Task 1:</strong> Fill blanks with word bank</p>
          <p><strong>Word Bank:</strong> [6 key terms from chapter]</p>
          <p><strong>Task 2:</strong> Answer 2 one-sentence questions</p>
        </td>
        <td>
          <p><strong>Task 1:</strong> Answer 3 questions in 2-3 sentences each</p>
          <p><strong>Task 2:</strong> Draw a simple timeline of key events</p>
        </td>
        <td>
          <p><strong>Task 1:</strong> Essay — explain key chapter theme in 8-10 sentences
          with causes, events, consequences</p>
          <p><strong>Task 2:</strong> Source analysis — quote from chapter + 3 questions</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in notebook</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Key terms table filled for all 5 days</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Outline map completed — all locations labeled (Day 5)</li>
    <li>☐ [Chapter-specific item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table: exactly 5 rows with Tamil column
- CFU bank: 15 questions (3 per section)
- No page numbers
- Base all content on actual extracted sections

Chapter Text:
---
{text[:3000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
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