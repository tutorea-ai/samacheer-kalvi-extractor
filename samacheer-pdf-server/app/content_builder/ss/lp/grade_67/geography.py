"""
geography.py
------------
LP Builder for Samacheer Kalvi Social Science — Geography
Class 6 & 7

v1.0 — Two-pass Chapter Analyser + New Day Plan Template (May 2026)

Architecture mirrors grade_910/geography.py with key differences:
  ✅ Two-pass analyser (Call 0a: Section Extractor, Call 0b: Day Allocator)
  ✅ Same 5-day structure (Geography = 5 days)
  ✅ Same Preamble structure (Chapter Overview + Objectives + Teaching Aids)
  ✅ Same separate Assessment call (Call 7)
  ✅ New Day Plan template per day (35 mins):
       [0-5 min]   Lead/Spark/Opening Question
       [5-20 min]  Key Learning Activity (Intro → Explanation+Activity → Summary)
       [20-30 min] Assessment (3 levels: Below Average / Average / Toppers)
       [30-35 min] Closing + Student Task (homework)
  ✅ Geography-specific features every day:
       - Map work every day
       - "I am..." CFU clues
       - Race/Radio Controller activities
       - T-Chart comparisons
       - Power Sentence closing
  ✅ Page numbers ALLOWED (unlike grade_910)
  ✅ Tamil in 3 places only (Key Terms, Main Explanation, Opening Question)
  ✅ Age-appropriate language for Class 6/7 (11-13 years)

API calls: 8 total
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
    STUDENT_TASK_STYLES,
    clean,
    PREAMBLE_START_INSTRUCTION,
)


# ============================================================================
# GEOGRAPHY DISCIPLINE NOTES — GRADE 6/7
# ============================================================================

GEOGRAPHY_DISCIPLINE_NOTES_67 = """
GEOGRAPHY-SPECIFIC TEACHING NOTES (Class 6 & 7):
- Map skills are central — every day must include map work
- Age-appropriate spatial thinking: where is it → why is it there → how does it affect us
- Simple physical features → human activities chain
- Board diagrams must show actual geographical shapes (V shape, slope, curved lines)
- Race activities: students race to find answers in textbook maps
- Radio Controller: teacher calls feature name → students find on map and shout
- Chanting: students chant lists of geographical names together
- "I am..." CFU clues: teacher gives clue → students identify the feature
- T-Chart comparisons for simple contrasts (mountains vs plains etc.)
- Power Sentence closing: students write ONE sentence connecting geography to real life
- Connect to students' daily life wherever possible
- Use simple analogies and comparisons for Class 6/7 level
- Page numbers may be referenced (Class 6/7 allowed)
"""


# ============================================================================
# GEOGRAPHY SPARK STYLES — 5 days, object/visual-based, age-appropriate
# ============================================================================

GEO_SPARK_STYLES_67 = {
    1: {
        "style": "Mystery Object",
        "instruction": """Hold up or describe a surprising object related to today's topic.
Allow 2-3 student guesses before revealing the connection.
Keep it simple and fun for Class 6/7.
End with a Big Question connecting the object to today's topic.
Example: Teacher holds a stone → 'How did this tiny rock become a mountain?'
Tell students WHY they are learning this and WHERE they use it in real life.""",
    },
    2: {
        "style": "Two Images Comparison",
        "instruction": """Describe two contrasting images related to today's topic.
Ask: 'Which is different and why?'
Keep comparison simple for Class 6/7.
End with a Big Question connecting the contrast to today's topic.
Example: Desert vs rainforest → 'Why does one place get rain and the other doesn't?'""",
    },
    3: {
        "style": "Physical Contrast",
        "instruction": """Hold up two contrasting physical materials that represent geographical features.
Students identify which is more useful for a given purpose.
Simple and hands-on for Class 6/7.
End with a Big Question.
Example: Handful of soil vs sand → 'Which one helps plants grow better and why?'""",
    },
    4: {
        "style": "Simple Demo",
        "instruction": """Use a simple classroom demonstration to show a geographical concept.
Objects from daily life — water bottle, sponge, bowl etc.
Students observe and predict.
End with a Big Question connecting demo to today's topic.
Example: Pour water on flat surface vs slope → 'Where does water flow faster?'""",
    },
    5: {
        "style": "Empty Map Challenge",
        "instruction": """Draw a giant empty outline map on the board.
Tell students the map has been wiped clean.
Challenge: 'Can you help me rebuild it from memory?'
Students draw outline in notebooks.
End with: 'Today we put the full puzzle together.'""",
    },
}


# ============================================================================
# GEOGRAPHY ACTIVITY MAP — per day, age-appropriate for Class 6/7
# ============================================================================

GEO_ACTIVITY_MAP_67 = {
    1: "Race activity (teacher calls feature name → students race to find in textbook and shout back) + Simple labeling (students label features in notebooks)",
    2: "Group Sorting (groups find Identity Card facts for different features) + Map Hunt (teacher calls feature name → students find and circle on textbook map)",
    3: "Simple T-Chart Comparison (students fill comparison table for two contrasting features) + Map labeling activity",
    4: "Feature ID Card (students find key facts for two contrasting features) + Radio Controller Map Hunt (teacher calls feature → students find on map)",
    5: "Synthesis Map Build (students sketch key features on outline map) + Radio Controller (teacher calls missions → students mark on map) + Memory Tricks review",
}


# ============================================================================
# GEOGRAPHY CLOSING STYLES — per day
# ============================================================================

GEO_CLOSING_STYLES_67 = {
    1: "One-Sentence Identity — students write one sentence connecting today's geographical feature to their daily life",
    2: "Feature Promise — students write one sentence about why a geographical feature is important to them",
    3: "Power Sentence — 'The [Feature] is important because [Reason]' — students pick one feature from today",
    4: "Connection Sentence — 'The [Feature] helps people because [Reason]' — students connect geography to human life",
    5: "One-Question Exit — 'If you lived near [feature], how would your life be different?' — students write one final sentence",
}


# ============================================================================
# GEOGRAPHY LP BUILDER CLASS — GRADE 6/7
# ============================================================================

class GeographyLP67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Geography LP Builder (67) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Geography LP for Class 6 & 7.
        Makes 8 API calls:
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

        print(f"      [Geography LP 67 v1] Generating: {lesson_title}")
        print(f"      [Geography LP 67 v1] 8 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

        parts = []

        # ── Call 0a: Section Extractor ────────────────────────────────────────
        print(f"      [Geography LP] Call 0a/8: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting LP")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        # ── Call 0b: Day Allocator ────────────────────────────────────────────
        print(f"      [Geography LP] Call 0b/8: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting LP")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [Geography LP] Call 1/8: Preamble...")
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
            print(f"      [Geography LP] Call {call_num}/8: Day {day_num}...")
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
        print(f"      [Geography LP] Call 6/8: Day 5 (Synthesis + Book-back)...")
        day5_html = self._call_day5(text, class_num, unit, lesson_title, sections, day_plan)
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # ── Call 7: Assessment ────────────────────────────────────────────────
        print(f"      [Geography LP] Call 7/8: Assessment...")
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
        print(f"      [Geography LP 67 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — STRICT SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Geography chapter (Class 6/7).

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
4. Note key geographical terms in that section
5. Note any map features mentioned

Chapter: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON only.

{{
  "chapter_sections": [
    {{
      "heading": "EXACT heading text from chapter",
      "subheadings": ["exact subheading 1", "exact subheading 2"],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "map_features": ["feature1", "feature2"],
      "has_comparison": false,
      "comparison_pair": []
    }}
  ],
  "total_estimated_teaching_mins": 60,
  "map_locations": ["location1", "location2"],
  "key_personalities": [],
  "comparison_pairs": [["Feature A", "Feature B"]]
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
- Map Work (book-back section)
- HOTS
- Choose the correct answer
- Fill in the blanks
- Match the following
- State True or False
- Pathway (introductory note)

STRICT RULES:
- Copy headings EXACTLY — do not paraphrase or rename
- Do NOT add sections that don't exist in the text
- Do NOT reorganise the order
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
        try:
            sections_str = json.dumps(sections, indent=2)

            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Geography lesson plan (Class 6/7).

YOU HAVE BEEN GIVEN the extracted sections from a chapter.
YOUR ONLY JOB: Allocate these sections to 4 days.

ALLOCATION RULES:
- Each day has 15 minutes of Key Learning Activity time
- Use estimated_teaching_time_mins from each section to fill each day
- Do NOT split a section across two days — keep each section in ONE day
- Day 4 must include the FINAL sections and chapter consolidation
- Every section MUST appear in exactly ONE day — no section can be skipped
- No section can appear in two days
- Day 5 is always Synthesis + Book-back — do NOT assign new content to Day 5
- Keep map features with their parent section

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
    "map_features": ["feature to locate today"],
    "focus": "One sentence describing what Day 1 covers",
    "estimated_mins": 15,
    "comparison_pair": null,
    "continuation_from_previous": false
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["subheading 3"],
    "map_features": ["feature to locate today"],
    "focus": "One sentence describing what Day 2 covers",
    "estimated_mins": 15,
    "comparison_pair": ["Feature A", "Feature B"],
    "continuation_from_previous": false
  }},
  "day3": {{
    "sections": ["EXACT heading 4", "EXACT heading 5"],
    "subheadings": ["subheading 4"],
    "map_features": ["feature to locate today"],
    "focus": "One sentence describing what Day 3 covers",
    "estimated_mins": 15,
    "comparison_pair": null,
    "continuation_from_previous": false
  }},
  "day4": {{
    "sections": ["EXACT heading 6"],
    "subheadings": ["subheading 5"],
    "map_features": ["feature to locate today"],
    "focus": "One sentence describing what Day 4 covers + consolidation",
    "estimated_mins": 15,
    "comparison_pair": null,
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

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — Geography Lesson Plan for Class 6/7.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Geography
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

CHAPTER SECTIONS (strictly extracted from text):
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY GEOGRAPHICAL TERMS: {key_terms}
MAP LOCATIONS: {map_locations}

Generate these sections:

1. CHAPTER OVERVIEW TABLE
<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Topics Covered | Key Map Features
</table>

2. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives — age-appropriate for Class 6/7
  Based ONLY on actual chapter sections
  (appreciation of nature, environmental care, curiosity about the world)
</ul>

3. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives: map reading, observation, comparison, communication
  Age-appropriate for Class 6/7. Based on actual chapter content.
</ul>

4. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 objectives — based ONLY on actual sections listed above
  Format: "Students will be able to [action verb] [topic]"
  Use: Identify, Locate, Describe, Explain, Compare (Class 6/7 level)
</ul>

5. TEACHING AIDS
<h2>Part 5: Teaching Aids</h2>
<ul>
  All materials needed — textbook (with page references), board, chalk,
  outline maps, wall map, flashcards, mystery objects for sparks,
  chart paper for T-Charts
  Age-appropriate for Class 6/7
</ul>

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids </ul>
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
            print(f"❌ Geography LP 67 preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2-5 — CONTENT DAYS 1-4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            spark         = GEO_SPARK_STYLES_67[day_num]
            task          = STUDENT_TASK_STYLES[day_num]
            activity      = GEO_ACTIVITY_MAP_67.get(day_num, "map activity")
            closing_style = GEO_CLOSING_STYLES_67.get(day_num, "Power Sentence")

            day_sections     = day_data.get("sections", [])
            day_subheadings  = day_data.get("subheadings", [])
            day_map_features = day_data.get("map_features", [])
            day_focus        = day_data.get("focus", "")
            comparison_pair  = day_data.get("comparison_pair", None)
            continuation     = day_data.get("continuation_from_previous", False)

            sections_str     = "\n".join([f"  - {s}" for s in day_sections])
            subheadings_str  = "\n".join([f"    • {s}" for s in day_subheadings])
            map_features_str = ", ".join(day_map_features) if day_map_features else "Identify from chapter"

            comparison_note = ""
            if comparison_pair and len(comparison_pair) == 2:
                comparison_note = f"""
⚠️ COMPARISON PAIR FOR TODAY:
Include a simple T-Chart comparison between: {comparison_pair[0]} vs {comparison_pair[1]}
Keep it simple for Class 6/7 — 3-4 rows maximum.
Students draw T-Chart in notebooks and fill facts.
"""

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
  Option A: Write the answers in notebook
  Option B: Draw and label a map/diagram from today
  Option C: Make a simple flowchart or T-Chart
Write all 3 options on board.
"""

            closing_note = ""
            if day_num == 4:
                closing_note = """
⚠️ DAY 4 CLOSING — FULL CHAPTER RECAP:
Recap ALL sections from ALL 4 days.
Write main headings on board. Rapid-fire: 5 questions spanning full chapter.
"""

            next_label = f"Day {day_num + 1}" if day_num < 4 else "Day 5 — Synthesis Map + Book-back"

            prompt = f"""Generate ONLY Day {day_num} of the Geography lesson plan for Class 6/7.
Nothing else. Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years — use age-appropriate language)
Unit     : {unit}
Subject  : Social Science — Geography
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S EXACT SECTIONS — STRICTLY FOLLOW THIS LIST
═══════════════════════════════════════════════════════
Sections to cover today:
{sections_str}

Subheadings to cover:
{subheadings_str if subheadings_str else "  [Cover all subheadings under today's sections]"}

Map Features for today: {map_features_str}
Day Focus: {day_focus}
{comparison_note}
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
GEOGRAPHY CFU/CCQ RULES — Class 6/7
═══════════════════════════════════════════════════════
Minimum 2 CFU + 2 CCQ per concept taught.
Total minimum: 8 CFUs + 6 CCQs across the full day.

CFU — use "I am..." clue format:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <div class="lp-teacher-says">"I am [clue about geographical feature]..."</p>
  <p class="student-says"><strong>Expected:</strong> "[Feature name]!"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

CCQ — deeper why/how question with Tamil:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <div class="lp-teacher-says">"[Why/How question — simple, under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion.</em></p>
</div>

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
   map work, closing, homework, assessment
Tamil mirror: same sentences, same length. Real Unicode only.
Age-appropriate Tamil for Class 6/7.

TAMIL QUALITY RULES:
- Grammatically correct Tamil — no spelling errors
- No word repetition in Tamil mirror
- No Hindi words in Tamil text — pure Tamil only
- If unsure of Tamil word, use English term
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
PAGE NUMBERS — ALLOWED FOR CLASS 6/7
═══════════════════════════════════════════════════════
You MAY reference textbook page numbers for Class 6/7.
Format: "Refer to page [X] in your textbook."
Use for key topic introductions and map references.
═══════════════════════════════════════════════════════

DAY STRUCTURE — OUTPUT THIS EXACTLY:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — [Write EXACT section names being taught today]</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Geography | Class {class_num} | {day_focus}</p>

  <!-- ═══ SECTION 1: LEAD / SPARK / OPENING QUESTION (0-5 min) ═══ -->
  <div class="lp-section-opening">
    <strong>[0-5 min] Lead / Spark / Opening Question — {spark['style']}</strong>

    <div class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-minute curiosity-building activity — {spark['style']} style.
     Simple, fun, and engaging for Class 6/7.
     Must connect to today's sections: {', '.join(day_sections)}.
     Allow 2-3 student guesses. End with Big Question.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same. Age-appropriate Tamil.]"</p>
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
    "[Set context for the topic. Then: 'Let's look at [topic] in our textbook.'
     Reference page number if applicable.
     2-3 simple sentences for Class 6/7.]"</p>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Today's Topic: {' | '.join(day_sections)}<br/>
      Map Features: {map_features_str}<br/>
      [One simple learning objective for today]
    </div>

    <div class="vocab-block">
      <strong>Key Geographical Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [4-5 key geographical terms from TODAY's sections — simple meanings for Class 6/7]
        </tbody>
      </table>
    </div>

    [CFU — "I am..." clue after vocab introduction]

    <!-- 2b. Topic Explanation with Activity -->
    <h4>Topic Explanation with Activity — {activity}</h4>

    [For EACH section in today's list — in exact order:]

    <h4>[Section heading — EXACTLY as in today's section list]</h4>

    [For EACH subheading:]
    <h5>[Subheading — exactly as extracted]</h5>

    <div class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — explain this section simply.
     Use story, analogy, or real-life connection for Class 6/7.
     Connect physical feature → effect on people's lives.
     Based ONLY on chapter text.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same. Simple, age-appropriate Tamil.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board — Simple Diagram:</strong><br/>
      [Simple diagram instruction — shape, arrows, labels.
       Keep it simple for Class 6/7.]
    </div>

    [CFU — "I am..." clue after each concept]
    [CCQ — simple why/how question after CFU]

    [Repeat for each section/subheading]

    {"<!-- T-Chart Comparison --><div class='activity-block'><strong>Simple T-Chart — " + (comparison_pair[0] if comparison_pair else "") + " vs " + (comparison_pair[1] if comparison_pair else "") + ":</strong><p>Students draw simple T-Chart in notebooks. Teacher calls facts → students fill correct column. Keep to 3-4 rows for Class 6/7.</p></div>" if comparison_pair else ""}

    <!-- Map Work -->
    <div class="activity-block">
      <strong>Map Work — {activity.split('+')[0].strip()}:</strong>
      <p>[Step by step map activity. English only.
         Teacher points on wall map first.
         Students label features in notebooks.
         Reference page number if applicable.]</p>
      <p><em>⏱ 3-4 minutes. Teacher circulates and checks map work.</em></p>
    </div>

    [CFU after map work — "I am..." clue about a map feature]

    <!-- 2c. Topic Closing — Summary -->
    <h4>Topic Closing — Summary</h4>
    <div class="board-work">
      <strong>Summary on Board:</strong><br/>
      [Simple flowchart OR mind map OR key points list — based on today's content]<br/>
      [Keep simple for Class 6/7]
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
              <p><strong>Task:</strong> Label the diagram/map with word bank</p>
              <p><strong>Word Bank:</strong> [4 geographical terms from today]</p>
              <p><em>Teacher sits with this group.</em></p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>"The [feature] is important because _______."</p>
            </td>
            <td>
              <p><strong>Task:</strong> Critical thinking</p>
              <p>"Explain [feature] and how it affects people's lives in 4-5 sentences."</p>
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
    "{'[Recap ALL sections from ALL 4 days. Write main headings on board. 5 rapid-fire questions spanning full chapter.]' if day_num == 4 else '[3 rapid-fire I am... clues about today only. Students shout the answer. Keep energetic.]'}"</p>
    <p><em>⏱ Wait 5 seconds per question.</em></p>

    <div class="board-work">
      <strong>{"Full Chapter" if day_num == 4 else "Today's"} Key Points:</strong><br/>
      1. [Key geographical fact 1]<br/>
      2. [Key geographical fact 2]<br/>
      3. [Key geographical fact 3]
    </div>

    <div class="lp-teacher-says"><strong>Power Sentence / Closing Reflection:</strong><br/>
    "[{closing_style} — students write ONE meaningful sentence connecting today's geography to real life.
     Give sentence frame on board. Age-appropriate for Class 6/7.]"</p>

    <div class="board-work">
      <strong>Sentence Frame (write on board):</strong><br/>
      "{closing_style.split('—')[0].strip()} frame"<br/>
      <em>Ask 3 students to read their sentences before bell rings.</em>
    </div>

    {"" if day_num == 4 else f'''
    <div class="homework-block">
      <div class="lp-teacher-says"><strong>Student Task / Homework:</strong><br/>
      {"Option A: Write answers in notebook.<br/>Option B: Draw and label a map/diagram from today.<br/>Option C: Make a simple T-Chart or flowchart." if day_num == 2 else "[Specific simple homework from today's sections. Clear for Class 6/7.]"}</p>

      <div class="board-work">
        <strong>{"Write all 3 options on board." if day_num == 2 else "Homework (write on board):"}</strong><br/>
        {"" if day_num == 2 else "[Exact homework task]"}
      </div>

      <div class="lp-teacher-says"><strong>Preview — {next_label}:</strong><br/>
      "[1-2 sentences — name the EXACT sections from Day {day_num + 1 if day_num < 4 else 5}.
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
✅ Map work included: {map_features_str}
✅ "I am..." CFU clues included
✅ Minimum 2 CFUs + 2 CCQs per concept
✅ Assessment has 3 levels
✅ Power Sentence closing included
✅ Tamil only in: Key Terms + Main explanations + Opening question
✅ Tamil quality: no errors, no repetition, no Hindi words
✅ Page numbers may be referenced
✅ Age-appropriate language throughout
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
            print(f"❌ Geography LP 67 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — DAY 5: SYNTHESIS MAP + BOOK-BACK
    # =========================================================================

    def _call_day5(self, text, class_num, unit, lesson_title,
                   sections: dict, day_plan: dict):
        try:
            map_locations    = ", ".join(sections.get("map_locations", []))
            comparison_pairs = sections.get("comparison_pairs", [])
            all_sections     = sections.get("chapter_sections", [])
            sections_str     = ", ".join([s["heading"] for s in all_sections])

            prompt = f"""Generate ONLY Day 5 of the Geography lesson plan for Class 6/7.
Day 5: Recap Game → Synthesis Map → Book-back Marking → Assessment → Closing.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years)
Unit     : {unit}
Subject  : Social Science — Geography
Day      : 5 of 5
Duration : 35 minutes

MAP LOCATIONS: {map_locations if map_locations else 'Identify from chapter text'}
ALL CHAPTER SECTIONS: {sections_str}

<div class="lp-day-block">
<h3 class="lp-day-title">Day 5 — Synthesis Map & Book-back</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Geography | Class {class_num} | Synthesis + Evaluation Day</p>

  <!-- LEAD / SPARK (0-5 min) -->
  <div class="lp-section-opening">
    <strong>[0-5 min] Lead / Spark — Chapter Recap Game</strong>
    <div class="lp-teacher-says">"Let's play a quick 'I am...' game! I'll give you a clue — you shout the answer.
    [4-5 simple 'I am...' clues about key features from the chapter. Fun and energetic for Class 6/7.]"</p>
    <p><em>⏱ Keep energetic. Take 4-5 responses.</em></p>
    <p><em>[2-minute transition to synthesis map work.]</em></p>
  </div>

  <!-- KEY LEARNING ACTIVITY (5-20 min) -->
  <div class="lp-section-main">
    <strong>[5-20 min] Key Learning Activity — Synthesis Map + Book-back</strong>

    <h4>Synthesis Map Build (5-12 min)</h4>
    <div class="lp-teacher-says">"Explorers, our map has been wiped clean!
    Let's rebuild it together from memory. Open your notebooks to a blank page."</p>

    <div class="board-work">
      <strong>Teacher builds map on board step by step:</strong><br/>
      [Step 1: Draw simple outline]<br/>
      [Step 2: Add key features from Days 1-4 — one by one]<br/>
      [Step 3: Label all features in CAPITAL LETTERS]<br/>
      <strong>Map Checklist — Mark All:</strong><br/>
      {map_locations if map_locations else '[All key geographical features from chapter]'}<br/>
      <strong>Simple Memory Tricks:</strong><br/>
      [2-3 fun, simple memory tricks for Class 6/7 students]
    </div>

    [CFU — "I am..." clue about a map feature]

    <h4>Radio Controller Map Hunt (12-15 min)</h4>
    <div class="lp-teacher-says"><strong>Teacher says (Radio Controller role):</strong><br/>
    "[Call out 3-4 simple missions based on actual chapter features.
     Students find and mark on their maps.
     Keep missions simple and fun for Class 6/7.]"</p>

    <div class="board-work">
      <strong>Map Missions (write on board):</strong><br/>
      Mission 1: Find and circle [feature from chapter]<br/>
      Mission 2: Draw and label [feature from chapter]<br/>
      Mission 3: Mark with a star [feature from chapter]<br/>
      Mission 4: Connect with an arrow [feature] to [feature]
    </div>

    <h4>Book-back Marking (15-20 min)</h4>
    <p><em>Teacher facilitates step-by-step marking.
    Platform Q&A section has all book-back questions with model answers.</em></p>

    <h5>Section 1: Choose the Correct Answer</h5>
    <p>[3-4 key MCQ answers — explain WHY correct in simple language for Class 6/7.]</p>

    <h5>Section 2: Fill in the Blanks / Match</h5>
    <p>[3-4 key answers — simple explanation.]</p>

    <h5>Section 3: Short Answers</h5>
    <p>[2-3 model answers — simple sentences for Class 6/7.]</p>

    <div class="board-work">
      <strong>Write Answers on Board:</strong><br/>
      [Key answers for student verification]
    </div>
  </div>

  <!-- ASSESSMENT (20-30 min) -->
  <div class="lp-section-student-task">
    <strong>[20-30 min] Assessment — 3 Levels (Chapter Review)</strong>

    <div class="lp-teacher-says">"Let's do a final chapter review. Choose your level."</p>

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
              <p><strong>Task:</strong> Label outline map with word bank</p>
              <p><strong>Word Bank:</strong> [6 key geographical terms from full chapter]</p>
              <p><em>Teacher sits with this group.</em></p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences</p>
              <p>[3 simple geography questions from full chapter]</p>
            </td>
            <td>
              <p><strong>Task:</strong> Write a short paragraph</p>
              <p>"Explain [key chapter theme] and how it affects people's lives in 5-6 sentences."</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ 8 minutes. Teacher circulates.</em></p>
    </div>
  </div>

  <!-- CLOSING (30-35 min) -->
  <div class="lp-section-closing">
    <strong>[30-35 min] One-Question Exit & Closing</strong>

    <div class="board-work">
      <strong>Exit Question (write on board):</strong><br/>
      "If you lived near [key geographical feature from chapter], how would your life be different?"<br/>
      Frame: "Living near [feature] would be [different/better/harder] because [one geographical fact]."
    </div>

    <p><em>Students write one final sentence at the bottom of their notes.</em></p>
    <p><em>⏱ Ask 3 students to share before bell rings.</em></p>

    <div class="lp-teacher-says">"[2-3 sentences — congratulate students on completing the chapter.
     Name 2-3 specific things learned. Use encouraging language for Class 6/7.]"</p>

    <div class="board-work">
      <strong>Submit before leaving:</strong><br/>
      ☐ Completed notebook — all 5 days of notes<br/>
      ☐ Synthesis outline map — all features labeled<br/>
      ☐ Book-back exercises — answered and marked<br/>
      ☐ All homework from Days 1-4
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <div class="lp-day-block">
- Map activities based on ACTUAL chapter content
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
            print(f"❌ Geography LP 67 Day 5 error: {e}")
            return None

    # =========================================================================
    # CALL 7 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, sections: dict, day_plan: dict):
        try:
            all_sections     = sections.get("chapter_sections", [])
            sections_str     = ", ".join([s["heading"] for s in all_sections])
            key_terms        = ", ".join([
                t for s in all_sections for t in s.get("key_terms", [])
            ][:10])
            map_locations    = ", ".join(sections.get("map_locations", []))
            comparison_pairs = sections.get("comparison_pairs", [])
            pairs_str        = ", ".join([
                f"{p[0]} vs {p[1]}" for p in comparison_pairs
            ]) if comparison_pairs else ""

            day_summary = ""
            for d in range(1, 5):
                day_data     = day_plan.get(f"day{d}", {})
                day_sections = day_data.get("sections", [])
                day_summary += f"  Day {d}: {', '.join(day_sections)}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Geography chapter (Class 6/7).
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years)
Unit     : {unit}
Subject  : Social Science — Geography
Total Days: 5

ALL CHAPTER SECTIONS: {sections_str}
KEY TERMS: {key_terms}
MAP LOCATIONS: {map_locations}
COMPARISON PAIRS: {pairs_str}

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
       Use simple "I am..." clue format for Geography.
       Age-appropriate for Class 6/7.
       Tamil version in last column.]
    </tbody>
  </table>

  <h3>CFU Bank — "I am..." Quick Reference</h3>
  <p><em>Simple "I am..." clue questions — 2 per major section — for teacher reference:</em></p>
  <ol>
    [10 "I am..." clue questions — 2 per each of the 5 sections.
     Simple language for Class 6/7.
     One-word or one-phrase answers.
     Based on actual chapter content.]
  </ol>

  <h3>CCQ Bank — Simple Why/How Questions</h3>
  <p><em>8 simple geography questions for revision:</em></p>
  <ol>
    [8 why/how questions — age-appropriate for Class 6/7.
     Feature → effect on people's lives chain.
     Based on actual chapter content.]
  </ol>

  <h3>Written Assessment Tasks</h3>
  <p>[2-3 simple written tasks covering different parts of the chapter.
     Age-appropriate for Class 6/7. Variety: label diagram, short answer, simple paragraph.]</p>
  <div class="board-work">
    <strong>Model Answers:</strong>
    <p>"[Task 1 model — simple sentences]"</p>
    <p>"[Task 2 model — slightly more detailed]"</p>
  </div>

  <h3>50-Mark Differentiated Worksheet</h3>
  <p><em>Chapter-end worksheet — choose level. All questions from actual chapter content.</em></p>

  <div class="board-work">
    <strong>🟢 Level 1 — Below Average Students (50 marks)</strong><br/>
    Q1-Q10: Fill in the blanks with word bank (1 mark each = 10 marks)<br/>
    Word Bank: [10 simple geographical terms from chapter]<br/>
    Q11-Q20: Choose the correct answer — MCQ (1 mark each = 10 marks)<br/>
    Q21-Q25: Match the following (2 marks each = 10 marks)<br/>
    Q26-Q30: Label the diagram / map (4 marks each = 20 marks)<br/>
    <br/>
    <strong>🟡 Level 2 — Average Students (50 marks)</strong><br/>
    Q1-Q10: Fill in the blanks (1 mark each = 10 marks)<br/>
    Q11-Q20: Choose correct answer (1 mark each = 10 marks)<br/>
    Q21-Q25: Answer in 2-3 sentences (4 marks each = 20 marks)<br/>
    Q26-Q28: Answer in detail — 5 marks each (5 marks each = 10 marks) [corrected: adjust to sum 50]<br/>
    <br/>
    <strong>🔴 Level 3 — Toppers / Advanced (50 marks)</strong><br/>
    Q1-Q5: Choose correct answer (1 mark each = 5 marks)<br/>
    Q6-Q15: Answer in 2-3 sentences (2 marks each = 20 marks)<br/>
    Q16-Q20: Answer in detail — 5 marks each (5 marks each = 25 marks)<br/>
    <br/>
    <em>All questions based on actual chapter content. Age-appropriate for Class 6/7.</em>
  </div>

  <h3>Map Checklist</h3>
  <p><em>All locations/features students must be able to identify:</em></p>
  <ul>
    [Numbered list of all map features from chapter — students mark and label these]
  </ul>

  {"<h3>Comparison Pairs</h3><p><em>Key comparison pairs from this chapter:</em></p>" if comparison_pairs else ""}
  {chr(10).join([f"<table class='exercise-table'><thead><tr><th>{p[0]}</th><th>{p[1]}</th></tr></thead><tbody><tr><td>[Difference 1A]</td><td>[Difference 1B]</td></tr><tr><td>[Difference 2A]</td><td>[Difference 2B]</td></tr><tr><td>[Difference 3A]</td><td>[Difference 3B]</td></tr></tbody></table>" for p in comparison_pairs]) if comparison_pairs else ""}

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
          <p><strong>Task:</strong> Label outline map with word bank</p>
          <p><strong>Word Bank:</strong> [5 simple key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences</p>
          <p>Starter: "The [feature] is found in [place] because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Paragraph + Map</p>
          <p>"Explain [key chapter theme] and its importance in 6-8 sentences."</p>
          <p>AND: Label all features on outline map.</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in notebook</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Synthesis outline map completed and labeled (Day 5)</li>
    <li>☐ Rapid recall quiz attempted (Day 5)</li>
    <li>☐ [Chapter-specific item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table: exactly 5 rows with Tamil column
- CFU bank: 10 "I am..." questions — simple for Class 6/7
- CCQ bank: 8 simple why/how questions
- Written tasks: 2-3 tasks
- 50-mark worksheet: 3 levels
- Map checklist: all features from chapter
- Age-appropriate language throughout
- No page numbers in assessment
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
            print(f"❌ Geography LP 67 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

geography_lp_67_builder = GeographyLP67Builder()