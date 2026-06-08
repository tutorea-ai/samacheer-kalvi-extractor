"""
civics.py
---------
LP Builder for Samacheer Kalvi Social Science — Civics
Class 6 & 7

v1.0 — Two-pass Chapter Analyser + New Day Plan Template (May 2026)

Architecture mirrors grade_910/civics.py with key differences:
  ✅ Two-pass analyser (Call 0a: Section Extractor, Call 0b: Day Allocator)
  ✅ Same 4-day structure (Civics = 4 days)
  ✅ Same Preamble structure (Chapter Overview + Objectives + Teaching Aids)
  ✅ Same separate Assessment call
  ✅ New Day Plan template per day (35 mins):
       [0-5 min]   Lead/Spark/Opening Question
       [5-20 min]  Key Learning Activity (Intro → Explanation+Activity → Summary)
       [20-30 min] Assessment (3 levels: Below Average / Average / Toppers)
       [30-35 min] Closing + Student Task (homework)
  ✅ Class 6/7 Civics topics: Diversity, Unity, Social values (NOT Constitution)
  ✅ NO article numbers — content is social/civic values based
  ✅ Age-appropriate activities: role play, group discussion, reflection
  ✅ NO map work
  ✅ Page numbers ALLOWED (unlike grade_910)
  ✅ Tamil in 3 places only
  ✅ Age-appropriate language for Class 6/7 (11-13 years)

API calls: 7 total
  Call 0a → Section Extractor  (JSON — strict extraction)
  Call 0b → Day Allocator      (JSON — day plan from extraction)
  Call 1  → Preamble
  Call 2  → Day 1
  Call 3  → Day 2
  Call 4  → Day 3
  Call 5  → Day 4
  Call 6  → Assessment
"""

import json
import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    SS_LP_SYSTEM_PROMPT,
    STUDENT_TASK_STYLES,
    clean,
    PREAMBLE_START_INSTRUCTION,
)


# ============================================================================
# CIVICS DISCIPLINE NOTES — GRADE 6/7
# ============================================================================

CIVICS_DISCIPLINE_NOTES_67 = """
CIVICS-SPECIFIC TEACHING NOTES (Class 6 & 7):
- Connect every concept to students' daily classroom and family life
- Diversity topics need real examples from students' own experience
- Unity in diversity — use examples from school, community, festivals
- Role play activities work very well for Class 6/7 Civics
- Group discussions: small groups sharing different perspectives
- Reflection activities: students write about their own experiences
- Story-based teaching: use real stories of people from different backgrounds
- Visual aids: pictures of different festivals, costumes, traditions
- No article numbers or constitutional provisions — purely social values
- Connect to students' immediate environment: classroom, school, neighbourhood
- Age-appropriate language — simple, relatable, empathetic
"""


# ============================================================================
# CIVICS SPARK STYLES — 4 days, age-appropriate for Class 6/7
# ============================================================================

CIVICS_SPARK_STYLES_67 = {
    1: {
        "style": "Classroom Observation",
        "instruction": """Ask students to look around the classroom and notice differences.
'Look at your classmates — what differences do you notice?'
Height, hair, language at home, food they eat, festivals they celebrate.
Build curiosity about WHY we are all different.
End with Big Question connecting to today's topic.
Tell students WHY they are learning this and WHERE they use it in real life.""",
    },
    2: {
        "style": "Story / Real-life Scenario",
        "instruction": """Tell a short engaging story about two children from different backgrounds
becoming friends despite their differences.
Keep it simple, relatable, and age-appropriate for Class 6/7.
After the story, ask: 'What made them friends despite being different?'
End with Big Question connecting to today's topic.""",
    },
    3: {
        "style": "Festival / Tradition Sharing",
        "instruction": """Ask 2-3 students to share one festival or tradition from their home.
Notice how different families celebrate differently.
'Why do we celebrate differently — but still celebrate together?'
Connect to today's topic about unity and diversity.
End with Big Question.""",
    },
    4: {
        "style": "Rapid Recall Quiz",
        "instruction": """Start with a fun rapid-fire quiz reviewing key concepts from Days 1-3.
Teacher asks → students shout the answer.
Keep it energetic and fun for Class 6/7.
5-6 quick questions. Standing format if possible.
Then transition: 'Today we put everything together and check what we learned.'""",
    },
}


# ============================================================================
# CIVICS ACTIVITY MAP — 4 days, age-appropriate
# ============================================================================

CIVICS_ACTIVITY_MAP_67 = {
    1: "Diversity Circle (students share one unique thing about themselves) + Quick Sorting (teacher gives examples → students identify type of diversity)",
    2: "Role Play (students act out a scenario showing respect for differences) + Think-Pair-Share (how do differences make us stronger?)",
    3: "Festival Map (groups share different festivals and how they celebrate together) + Group Discussion (examples of unity in our school/community)",
    4: "Reflection Web (students connect today's learning to their own life) + Class Constitution (students write 3 rules for respecting diversity in class)",
}


# ============================================================================
# CIVICS CLOSING STYLES — 4 days
# ============================================================================

CIVICS_CLOSING_STYLES_67 = {
    1: "One-Sentence Reflection — 'Diversity is important because...' — students complete the sentence",
    2: "Respect Pledge — students write one way they will show respect for differences this week",
    3: "Unity Sentence — 'Even though we are different, we are united because...' — students complete",
    4: "3-2-1 Reflection — 3 things learned, 2 examples of diversity, 1 way to celebrate differences",
}


# ============================================================================
# CIVICS LP BUILDER CLASS — GRADE 6/7
# ============================================================================

class CivicsLP67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Civics LP Builder (67) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Civics LP for Class 6 & 7.
        Makes 7 API calls:
            Call 0a: Section Extractor (strict JSON extraction)
            Call 0b: Day Allocator (day plan from extraction)
            Call 1:  Preamble
            Calls 2-5: Days 1-4
            Call 6:  Assessment
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [Civics LP 67 v1] Generating: {lesson_title}")
        print(f"      [Civics LP 67 v1] 7 API calls: 0a+0b+Preamble+Day1-4+Assessment")

        parts = []

        # ── Call 0a: Section Extractor ────────────────────────────────────────
        print(f"      [Civics LP] Call 0a/7: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting LP")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        # ── Call 0b: Day Allocator ────────────────────────────────────────────
        print(f"      [Civics LP] Call 0b/7: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting LP")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [Civics LP] Call 1/7: Preamble...")
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
            print(f"      [Civics LP] Call {call_num}/7: Day {day_num}...")
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

        # ── Call 6: Assessment ────────────────────────────────────────────────
        print(f"      [Civics LP] Call 6/7: Assessment...")
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
        print(f"      [Civics LP 67 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — STRICT SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Civics chapter (Class 6/7).

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
      "has_activity": false,
      "activity_description": ""
    }}
  ],
  "total_estimated_teaching_mins": 60,
  "key_values": ["value1", "value2"],
  "real_life_examples": ["example1", "example2"]
}}

Chapter Text:
---
{text}
---

STRICT EXCLUSION — DO NOT extract these as sections:
- Exercises / Exercise sections
- Summary
- Glossary
- Internet Resources
- ICT CORNER
- Learning Objectives
- Student Activity
- Life Skill
- Answer Grid
- HOTS
- Choose the correct answer
- Fill in the blanks
- Match the following
- State True or False
- Pathway (introductory note)

STRICT RULES:
- Copy headings EXACTLY — do not paraphrase or rename
- Do NOT add sections that don't exist in the text
- Extract ONLY main content teaching sections
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
        try:
            sections_str = json.dumps(sections, indent=2)

            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Civics lesson plan (Class 6/7).

YOU HAVE BEEN GIVEN the extracted sections from a chapter.
YOUR ONLY JOB: Allocate these sections to 4 days.

ALLOCATION RULES:
- Each day has 15 minutes of Key Learning Activity time
- Use estimated_teaching_time_mins from each section to fill each day
- Do NOT split a section across two days — keep each section in ONE day
- Day 4 must include the FINAL sections and chapter consolidation/reflection
- Every section MUST appear in exactly ONE day — no section can be skipped
- No section can appear in two days
- Keep age-appropriate pacing for Class 6/7

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
    "key_values": ["value from today's content"],
    "continuation_from_previous": false
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["subheading 3"],
    "focus": "One sentence describing what Day 2 covers",
    "estimated_mins": 15,
    "key_values": ["value from today's content"],
    "continuation_from_previous": false
  }},
  "day3": {{
    "sections": ["EXACT heading 4", "EXACT heading 5"],
    "subheadings": ["subheading 4"],
    "focus": "One sentence describing what Day 3 covers",
    "estimated_mins": 15,
    "key_values": ["value from today's content"],
    "continuation_from_previous": false
  }},
  "day4": {{
    "sections": ["EXACT heading 6"],
    "subheadings": ["subheading 5"],
    "focus": "One sentence describing what Day 4 covers + reflection",
    "estimated_mins": 15,
    "key_values": ["value from today's content"],
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

            key_terms  = ", ".join([
                t for s in sections_list for t in s.get("key_terms", [])
            ][:10])
            key_values = ", ".join(sections.get("key_values", []))

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — Civics Lesson Plan for Class 6/7.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Civics
Month    : {month if month else 'As scheduled'}
Duration : 4 Days × 35 Minutes = 140 Minutes Total

CHAPTER SECTIONS (strictly extracted from text):
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY TERMS: {key_terms}
KEY VALUES: {key_values}

NOTE: This is Class 6/7 Civics — topics are about social values, diversity,
unity, and civic responsibility. NOT about Constitution or article numbers.

Generate these sections:

1. CHAPTER OVERVIEW TABLE
<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Topics Covered | Key Values Taught
</table>

2. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives — age-appropriate for Class 6/7
  Based ONLY on actual chapter sections
  (respect for diversity, empathy, unity, social responsibility)
</ul>

3. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives: observation, reflection, communication, collaboration
  Age-appropriate for Class 6/7. Based on actual chapter content.
</ul>

4. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 objectives — based ONLY on actual sections listed above
  Format: "Students will be able to [action verb] [topic]"
  Use: Understand, Explain, Identify, Appreciate, Describe (Class 6/7 level)
</ul>

5. TEACHING AIDS
<h2>Part 5: Teaching Aids</h2>
<ul>
  All materials needed — textbook (with page references), board, chalk,
  pictures of different festivals/traditions, chart paper,
  role play props, flashcards
  Age-appropriate for Class 6/7
</ul>

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids </ul>
- Age-appropriate language for Class 6/7
- NO article numbers — this is values-based Civics

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
            print(f"❌ Civics LP 67 preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2-5 — CONTENT DAYS 1-4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            spark         = CIVICS_SPARK_STYLES_67[day_num]
            task          = STUDENT_TASK_STYLES[day_num]
            activity      = CIVICS_ACTIVITY_MAP_67.get(day_num, "group discussion")
            closing_style = CIVICS_CLOSING_STYLES_67.get(day_num, "Reflection sentence")

            day_sections   = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus      = day_data.get("focus", "")
            key_values     = day_data.get("key_values", [])
            continuation   = day_data.get("continuation_from_previous", False)

            sections_str    = "\n".join([f"  - {s}" for s in day_sections])
            subheadings_str = "\n".join([f"    • {s}" for s in day_subheadings])
            key_values_str  = ", ".join(key_values) if key_values else "respect, empathy, unity"

            continuation_note = ""
            if continuation:
                prev_day_data = day_plan.get(f"day{day_num-1}", {})
                prev_sections = prev_day_data.get("sections", [])
                continuation_note = f"""
⚠️ CONTINUATION FROM DAY {day_num-1}:
Start by completing: {', '.join(prev_sections[-1:])}
Teacher says: "Yesterday we started [topic]. Today we complete it first."
"""

            homework_note = ""
            if day_num == 2:
                homework_note = """
⚠️ HOMEWORK FOR DAY 2 — Give students a CHOICE:
  Option A: Write a short paragraph about a time you appreciated someone different from you
  Option B: Draw a picture showing diversity in your community
  Option C: Make a list of 5 things that make your class diverse
Write all 3 options on board.
"""

            closing_note = ""
            if day_num == 4:
                closing_note = """
⚠️ DAY 4 CLOSING — FULL CHAPTER RECAP + REFLECTION:
Recap ALL sections from ALL 4 days.
3-2-1 Reflection: 3 things learned, 2 examples of diversity, 1 way to celebrate differences.
Class Constitution: students write 3 rules for respecting diversity in class.
"""

            next_label = f"Day {day_num + 1}" if day_num < 4 else "end of chapter"

            prompt = f"""Generate ONLY Day {day_num} of the Civics lesson plan for Class 6/7.
Nothing else. Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years — use age-appropriate language)
Unit     : {unit}
Subject  : Social Science — Civics
Day      : {day_num} of 4
Duration : 35 minutes

NOTE: This is Class 6/7 Civics about social values and diversity.
NO article numbers. NO constitutional provisions.
Focus on real-life examples, stories, and student experiences.

═══════════════════════════════════════════════════════
TODAY'S EXACT SECTIONS — STRICTLY FOLLOW THIS LIST
═══════════════════════════════════════════════════════
Sections to cover today:
{sections_str}

Subheadings to cover:
{subheadings_str if subheadings_str else "  [Cover all subheadings under today's sections]"}

Day Focus: {day_focus}
Key Values for today: {key_values_str}
{continuation_note}
{closing_note}
{homework_note}

⛔ ABSOLUTE RULE:
Cover ONLY the sections listed above.
If a heading is NOT in this list — DO NOT mention it.
DO NOT use general knowledge to add extra content.
DO NOT introduce topics from other days.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
CFU/CCQ RULES — CIVICS Class 6/7
═══════════════════════════════════════════════════════
Minimum 2 CFU + 2 CCQ per concept taught.
Total minimum: 8 CFUs + 6 CCQs across the full day.

CFU — simple recall or scenario-based:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <div class="lp-teacher-says">"[Simple question or scenario — under 6 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

CCQ — deeper reflection question with Tamil:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <div class="lp-teacher-says">"[Why/How question — simple, under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion.</em></p>
</div>

CIVICS CFU EXAMPLES (scenario-based, age-appropriate):
✅ "Your classmate speaks a different language — how do you respond?"
✅ "Name one way people are different in India."
✅ "What does unity in diversity mean?"

NEVER use ICQs: "Do you understand?" / "How many sentences?"
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING — TARGETED ONLY
═══════════════════════════════════════════════════════
Tamil appears in EXACTLY 3 places:
✅ 1. KEY TERMS TABLE — Tamil meaning column
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph after English
✅ 3. OPENING LEAD QUESTION — Tamil version after English

❌ NEVER in: activity instructions, board work, CFU blocks,
   closing, homework, assessment
Tamil mirror: same sentences, same length. Real Unicode only.
Age-appropriate Tamil for Class 6/7.
TAMIL QUALITY: No spelling errors, no word repetition, no Hindi words.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
PAGE NUMBERS — ALLOWED FOR CLASS 6/7
═══════════════════════════════════════════════════════
You MAY reference textbook page numbers for Class 6/7.
Format: "Refer to page [X] in your textbook."
═══════════════════════════════════════════════════════

DAY STRUCTURE — OUTPUT THIS EXACTLY:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — [Write EXACT section names being taught today]</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Civics | Class {class_num} | {day_focus}</p>

  <!-- ═══ SECTION 1: LEAD / SPARK / OPENING QUESTION (0-5 min) ═══ -->
  <div class="lp-section-opening">
    <strong>[0-5 min] Lead / Spark / Opening Question — {spark['style']}</strong>

    <div class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-minute curiosity-building activity — {spark['style']} style.
     Simple, relatable, engaging for Class 6/7.
     Must connect to today's sections: {', '.join(day_sections)}.
     End with Big Question about today's topic.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same. Age-appropriate Tamil.]"</p>
    </div>

    <p><em>⏱ Wait 20 seconds. Take 3-5 student responses.</em></p>
    <p><em>[2-minute transition: "Now let's explore this topic together."]</em></p>
  </div>

  <!-- ═══ SECTION 2: KEY LEARNING ACTIVITY (5-20 min) ═══ -->
  <div class="lp-section-main">
    <strong>[5-20 min] Key Learning Activity</strong>

    <!-- 2a. Topic Introduction -->
    <h4>Topic Introduction — Textbook Context</h4>
    <div class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[Set context for the topic. Then: 'Let's look at [topic] in our textbook.'
     Reference page number if applicable.
     2-3 simple sentences for Class 6/7.
     Connect to students' daily life immediately.]"</p>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Today's Topic: {' | '.join(day_sections)}<br/>
      Key Values: {key_values_str}<br/>
      [One simple learning objective for today]
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

    [CFU after introduction — very simple recall]

    <!-- 2b. Topic Explanation with Activity -->
    <h4>Topic Explanation with Activity — {activity}</h4>

    [For EACH section in today's list — in exact order:]

    <h4>[Section heading — EXACTLY as in today's section list]</h4>

    [For EACH subheading:]
    <h5>[Subheading — exactly as extracted]</h5>

    <div class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — explain this section simply.
     Use story, real example, or student's daily life connection.
     Simple language for Class 6/7.
     Based ONLY on chapter text — no outside knowledge.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same. Simple, age-appropriate Tamil.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      [Key points from this section — simple bullet points]
    </div>

    [CFU — simple scenario or recall question]
    [CCQ — simple why/how reflection question]

    [Repeat for each section/subheading]

    <!-- Activity -->
    <div class="activity-block">
      <strong>Activity — {activity.split('+')[0].strip()}:</strong>
      <p>[Step by step activity instructions. English only.
         Simple, fun, and engaging for Class 6/7.
         Based on today's sections only.]</p>
      <p><em>⏱ 5-6 minutes. Teacher circulates and encourages sharing.</em></p>
    </div>

    [CFU after activity]

    <!-- 2c. Topic Closing — Summary -->
    <h4>Topic Closing — Summary</h4>
    <div class="board-work">
      <strong>Summary on Board:</strong><br/>
      [Simple key points list OR mind map — based on today's content]<br/>
      [Keep very simple for Class 6/7]
    </div>
    <div class="lp-teacher-says">"[2 sentences summarising what was learned today.
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
            <th>Below Average<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
            <th>Average Students<br/>(சராசரி மாணவர்கள்)</th>
            <th>Toppers / Advanced<br/>(திறமையான மாணவர்கள்)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p><strong>Task:</strong> Fill in the blanks / Oral answer</p>
              <p>"[Simple sentence] _______ (word1 / word2)"</p>
              <p><strong>Word Bank:</strong> [4 key terms from today]</p>
              <p><em>Teacher sits with this group.</em></p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>Question: "[Core concept question from today]"</p>
              <p>Starter: "[sentence starter]"</p>
            </td>
            <td>
              <p><strong>Task:</strong> Reflection / Creative</p>
              <p>"[Why/How question requiring deeper thought.
                 Give a real-life example from your own experience.]"</p>
              <p>Write 4-5 sentences.</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ 8 minutes. Teacher circulates to each group.</em></p>
    </div>

    <div class="lp-teacher-says"><strong>Quick Review:</strong><br/>
    "[Take 2 minutes — hear 1 answer from each level. Give positive feedback.]"</p>
  </div>

  <!-- ═══ SECTION 4: CLOSING + STUDENT TASK (30-35 min) ═══ -->
  <div class="lp-section-closing">
    <strong>[30-35 min] {"Full Chapter Recap & Closing" if day_num == 4 else "Closing & Student Task"}</strong>

    <div class="lp-teacher-says"><strong>2-Minute Recap:</strong><br/>
    "{'[Recap ALL sections from ALL 4 days. 3-2-1 Reflection: 3 things learned, 2 examples of diversity, 1 way to celebrate differences. Class Constitution: students write 3 rules for respecting diversity.]' if day_num == 4 else '[3 rapid-fire questions about today only. Students call out answers. Keep energetic.]'}"</p>
    <p><em>⏱ Wait 5 seconds per question.</em></p>

    <div class="board-work">
      <strong>{"Full Chapter" if day_num == 4 else "Today's"} Key Points:</strong><br/>
      1. [Key point 1]<br/>
      2. [Key point 2]<br/>
      3. [Key point 3]
    </div>

    <div class="lp-teacher-says"><strong>Closing Reflection:</strong><br/>
    "[{closing_style} — students write ONE meaningful sentence.
     Give sentence frame on board. Age-appropriate for Class 6/7.]"</p>

    <div class="board-work">
      <strong>Sentence Frame (write on board):</strong><br/>
      "{closing_style.split('—')[0].strip()} frame"<br/>
      <em>Ask 3 students to read their sentences before bell rings.</em>
    </div>

    {"" if day_num == 4 else f'''
    <div class="homework-block">
      <div class="lp-teacher-says"><strong>Student Task / Homework:</strong><br/>
      {"Option A: Write a short paragraph about a time you appreciated someone different from you.<br/>Option B: Draw a picture showing diversity in your community.<br/>Option C: Make a list of 5 things that make your class diverse." if day_num == 2 else "[Specific simple homework from today's sections. Clear for Class 6/7.]"}</p>

      <div class="board-work">
        <strong>{"Write all 3 options on board." if day_num == 2 else "Homework (write on board):"}</strong><br/>
        {"" if day_num == 2 else "[Exact homework task]"}
      </div>

      <div class="lp-teacher-says"><strong>Preview — {next_label}:</strong><br/>
      "[1-2 sentences — name the EXACT sections from Day {day_num + 1 if day_num < 4 else 4}.
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
✅ NO article numbers — this is values-based Civics for Class 6/7
✅ Minimum 2 CFUs + 2 CCQs per concept
✅ Assessment has 3 levels
✅ Closing reflection included
✅ Tamil only in: Key Terms + Main explanations + Opening question
✅ Tamil quality: no errors, no repetition, no Hindi words
✅ Page numbers may be referenced
✅ Age-appropriate language throughout
✅ Real-life examples and student connections included
{"✅ Day 4: 3-2-1 Reflection + Class Constitution included" if day_num == 4 else f"✅ Preview names exact sections from Day {day_num + 1}"}
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
            print(f"❌ Civics LP 67 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, sections: dict, day_plan: dict):
        try:
            all_sections = sections.get("chapter_sections", [])
            sections_str = ", ".join([s["heading"] for s in all_sections])
            key_terms    = ", ".join([
                t for s in all_sections for t in s.get("key_terms", [])
            ][:10])
            key_values   = ", ".join(sections.get("key_values", []))

            day_summary = ""
            for d in range(1, 5):
                day_data     = day_plan.get(f"day{d}", {})
                day_sections = day_data.get("sections", [])
                day_summary += f"  Day {d}: {', '.join(day_sections)}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Civics chapter (Class 6/7).
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years)
Unit     : {unit}
Subject  : Social Science — Civics
Total Days: 4

NOTE: Class 6/7 Civics — social values and diversity topics.
NO article numbers. Age-appropriate questions only.

ALL CHAPTER SECTIONS: {sections_str}
KEY TERMS: {key_terms}
KEY VALUES: {key_values}

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
      [4 rows — Day 1 through Day 4.
       Simple, age-appropriate questions for Class 6/7.
       Scenario-based where possible.
       Tamil version in last column.]
    </tbody>
  </table>

  <h3>CFU Bank — Quick Reference</h3>
  <p><em>Simple recall questions — 2 per major section — for teacher reference:</em></p>
  <ol>
    [8 CFU questions — 2 per each of the 4 days.
     Under 6 words each. Simple for Class 6/7.
     Scenario-based where possible.
     Based on actual chapter content.]
  </ol>

  <h3>CCQ Bank — Reflection Questions</h3>
  <p><em>8 deeper reflection questions for revision:</em></p>
  <ol>
    [8 why/how/what questions — age-appropriate for Class 6/7.
     Focus on real-life connections and values.
     Based on actual chapter content.]
  </ol>

  <h3>Written Assessment Tasks</h3>
  <p>[2-3 simple written tasks covering different parts of the chapter.
     Age-appropriate for Class 6/7. Variety: short answer, reflection, creative.]</p>
  <div class="board-work">
    <strong>Model Answers:</strong>
    <p>"[Task 1 model — simple sentences]"</p>
    <p>"[Task 2 model]"</p>
  </div>

  <h3>50-Mark Differentiated Worksheet</h3>
  <p><em>Chapter-end worksheet — choose level. All questions from actual chapter content.</em></p>

  <div class="board-work">
    <strong>🟢 Level 1 — Below Average Students (50 marks)</strong><br/>
    Q1-Q10: Fill in the blanks with word bank (1 mark each = 10 marks)<br/>
    Word Bank: [10 simple key terms from chapter]<br/>
    Q11-Q20: Choose the correct answer — MCQ (1 mark each = 10 marks)<br/>
    Q21-Q25: Match the following (2 marks each = 10 marks)<br/>
    Q26-Q30: Answer in ONE simple sentence (4 marks each = 20 marks)<br/>
    <br/>
    <strong>🟡 Level 2 — Average Students (50 marks)</strong><br/>
    Q1-Q10: Fill in the blanks (1 mark each = 10 marks)<br/>
    Q11-Q20: Choose correct answer (1 mark each = 10 marks)<br/>
    Q21-Q25: Answer in 2-3 sentences (4 marks each = 20 marks)<br/>
    Q26-Q28: Answer in detail (5 marks each = 10 marks) [adjust to sum 50]<br/>
    <br/>
    <strong>🔴 Level 3 — Toppers / Advanced (50 marks)</strong><br/>
    Q1-Q5: Choose correct answer (1 mark each = 5 marks)<br/>
    Q6-Q15: Answer in 2-3 sentences (2 marks each = 20 marks)<br/>
    Q16-Q20: Answer in detail (5 marks each = 25 marks)<br/>
    <br/>
    <em>All questions based on actual chapter content. Age-appropriate for Class 6/7.</em>
  </div>

  <h3>3-2-1 Final Reflection</h3>
  <div class="board-work">
    <strong>Write on Board:</strong><br/>
    3 things you learned from this chapter<br/>
    2 examples of diversity you see in your daily life<br/>
    1 way you will celebrate differences around you
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
          <p>Starter: "[Topic] is important because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Reflection paragraph</p>
          <p>"Explain [key chapter value] with examples from your own life in 6-8 sentences."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 4 days of notes completed in notebook</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Written Assessment completed (Day 4)</li>
    <li>☐ 3-2-1 Reflection written (Day 4)</li>
    <li>☐ [Chapter-specific item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table: exactly 4 rows with Tamil column
- CFU bank: 8 questions — simple for Class 6/7
- CCQ bank: 8 reflection questions
- Written tasks: 2-3 tasks
- 50-mark worksheet: 3 levels
- NO article numbers anywhere
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
            print(f"❌ Civics LP 67 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

civics_lp_67_builder = CivicsLP67Builder()