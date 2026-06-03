"""
physics.py
----------
LP Builder for Samacheer Kalvi Science — Physics
Class 6 & 7

v1.0 — May 2026
Modeled on ss/lp/grade_67/history.py structure.
Science-flavored for Physics: measurements, force, motion.

KEY DIFFERENCES FROM grade_910/physics.py:
  - 4-block day plan (Lead/Spark + Key Learning + Assessment + Closing)
  - Assessment embedded EVERY day (3 levels: below/average/toppers)
  - Hands-on observation experiments — household/classroom materials
  - Predict or Perish spark format
  - Page numbers ALLOWED
  - Age-appropriate language (11-13 years)
  - CFU numbered sequentially (cfu-block format)
  - Homework: choice of 3 formats (poster/essay/flowchart/experiment)
  - No formula derivations — focus on concept + observation

API calls: 9 total
  Call 0a → Section Extractor  (JSON)
  Call 0b → Day Allocator      (JSON)
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
    SCIENCE_LP_SYSTEM_PROMPT,
    clean,
    PREAMBLE_START_INSTRUCTION,
    TAMIL_INSTRUCTION_67,
    CCQ_CFU_INSTRUCTION_67,
    DAY_PLAN_STRUCTURE_67,
    SCIENCE_DISCIPLINE_NOTES_67,
    SCIENCE_SPARK_STYLES_67,
    SCIENCE_ACTIVITY_MAP_67,
)


DISCIPLINE_NOTES = SCIENCE_DISCIPLINE_NOTES_67["physics"]
SPARK_STYLES     = SCIENCE_SPARK_STYLES_67
ACTIVITY_MAP     = SCIENCE_ACTIVITY_MAP_67


class PhysicsLP67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Physics LP Builder (67) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [Physics LP 67 v1.0] Generating: {lesson_title}")
        print(f"      [Physics LP 67 v1.0] 9 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

        parts = []

        print(f"      [Physics LP 67] Call 0a/9: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        print(f"      [Physics LP 67] Call 0b/9: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        for d in range(1, 5):
            print(f"            Day {d}: {', '.join(day_plan.get(f'day{d}', {}).get('sections', []))}")

        print(f"      [Physics LP 67] Call 1/9: Preamble...")
        preamble = self._call_preamble(text, class_num, unit, lesson_title, month, sections, day_plan)
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting")
            return None

        for day_num in range(1, 5):
            print(f"      [Physics LP 67] Call {day_num+1}/9: Day {day_num}...")
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title,
                day_num, day_plan.get(f"day{day_num}", {}), sections, day_plan
            )
            if day_html:
                parts.append(clean(day_html))
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        print(f"      [Physics LP 67] Call 6/9: Day 5...")
        day5 = self._call_day5(text, class_num, unit, lesson_title, sections, day_plan)
        if day5:
            parts.append(clean(day5))
            print(f"         ✅ Day 5 ({len(day5)} chars)")

        print(f"      [Physics LP 67] Call 7/9: Assessment...")
        assessment = self._call_assessment(text, class_num, unit, lesson_title, sections, day_plan)
        if assessment:
            parts.append(clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")

        if not parts:
            return None
        combined = "\n\n".join(parts)
        print(f"      [Physics LP 67 v1.0] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Physics chapter (Class 6/7).

Extract EVERY heading and subheading EXACTLY as written in the chapter text.
Do NOT add general knowledge. Do NOT reorganise.

STRICT EXCLUSION — do NOT extract:
Exercises, Summary, Glossary, ICT Corner, Activity sections,
HOTS, Choose correct answer, Fill in blanks, Match following,
Internet Resources, Learning Objectives listed at start.

Chapter: {lesson_title}

Return ONLY valid JSON. No markdown. Raw JSON starting with {{

{{
  "chapter_sections": [
    {{
      "heading": "EXACT heading from text",
      "subheadings": ["exact subheading 1", "exact subheading 2"],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "has_experiment": false,
      "has_measurement": false
    }}
  ],
  "total_estimated_teaching_mins": 60,
  "key_terms": ["all key terms"],
  "key_experiments": ["experiments mentioned"],
  "key_units": ["units of measurement mentioned"]
}}

Chapter Text:
---
{text}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system="Strict text extractor. Return ONLY valid JSON. No markdown. Raw JSON starting with {",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = re.sub(r'```(?:json)?', '', response.content[0].text.strip()).strip()
            raw = re.sub(r'```', '', raw).strip()
            return json.loads(raw)
        except Exception as e:
            print(f"❌ Section Extractor error: {e}")
            return None

    # =========================================================================
    # CALL 0b — DAY ALLOCATOR
    # =========================================================================

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a DAY ALLOCATOR for a Class 6/7 Physics lesson plan.

Allocate ALL extracted sections to exactly 4 days.
Each day = 15 minutes of Key Learning Activity time.
Keep each section in ONE day. Every section must appear in exactly ONE day.
Use EXACT heading text. No general knowledge.

Return ONLY valid JSON. No markdown. Raw JSON starting with {{

{{
  "day1": {{
    "sections": ["EXACT heading"],
    "subheadings": ["exact subheading"],
    "focus": "One sentence — what Day 1 covers",
    "estimated_mins": 15,
    "has_experiment": false
  }},
  "day2": {{ ... }},
  "day3": {{ ... }},
  "day4": {{
    "sections": ["EXACT heading"],
    "subheadings": ["exact subheading"],
    "focus": "Day 4 — final sections + chapter consolidation",
    "estimated_mins": 15,
    "has_experiment": false
  }}
}}

Extracted Sections:
---
{json.dumps(sections, indent=2)}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=2000,
                system="Strict day allocator. Return ONLY valid JSON. No markdown. Raw JSON starting with {",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = re.sub(r'```(?:json)?', '', response.content[0].text.strip()).strip()
            raw = re.sub(r'```', '', raw).strip()
            return json.loads(raw)
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
                f"  ▸ {s['heading']}: {', '.join(s.get('subheadings', []))}"
                for s in sections_list
            ])
            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))} — {d_data.get('focus','')}\n"

            key_terms = ", ".join([t for s in sections_list for t in s.get("key_terms", [])][:10])
            key_units = ", ".join(sections.get("key_units", [])[:6])

            prompt = f"""Generate ONLY the preamble of this Physics Lesson Plan for Class 6/7.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Physics
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

CHAPTER SECTIONS:
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY TERMS : {key_terms}
KEY UNITS : {key_units}

Generate EXACTLY in this order:

<h2>Part 1: Chapter Overview</h2>
Table: Class | Subject | Discipline | Unit/Chapter Title | Month |
       Total Teaching Hours | Session Duration | Main Sections Covered

<h2>Part 2: Learning Objectives</h2>
4-5 SWBAT — age-appropriate for Class 6/7
Action verbs: Identify, Measure, Explain, Observe, Describe
Based ONLY on actual chapter sections

<h2>Part 3: Value-Based Objectives</h2>
3-4 values — connect Physics to everyday life for Class 6/7
e.g. Appreciate precision in measurement, Connect force to sports,
     Curiosity about motion in daily life

<h2>Part 4: Skill Objectives</h2>
4 skills: Observation, Measurement, Prediction, Communication
Age-appropriate for Class 6/7

<h2>Part 5: Teaching Aids</h2>
Textbook (with pages), board, chalk, rulers, scales,
simple household objects for demos, notebooks
Physics-specific: measurement tools, simple force demos

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Age-appropriate language for Class 6/7
- Stop after Teaching Aids

Chapter Text:
---
{text[:3000]}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system=SCIENCE_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Physics LP 67 preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2-5 — CONTENT DAYS 1-4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            spark    = SPARK_STYLES[day_num]
            activity = ACTIVITY_MAP[day_num]

            day_sections    = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus       = day_data.get("focus", "")
            has_experiment  = day_data.get("has_experiment", False)

            all_sections  = sections.get("chapter_sections", [])
            day_key_terms = []
            for s in all_sections:
                if s["heading"] in day_sections:
                    day_key_terms.extend(s.get("key_terms", []))

            sections_str    = "\n".join([f"  ▸ {s}" for s in day_sections])
            subheadings_str = "\n".join([f"      • {s}" for s in day_subheadings])
            key_terms_str   = ", ".join(day_key_terms[:8])

            next_preview = (
                f"Day {day_num+1}: {', '.join(day_plan.get(f'day{day_num+1}', {}).get('sections', []))}"
                if day_num < 4 else "Day 5: Recap Quiz + Book-back Exercises"
            )

            experiment_note = ""
            if has_experiment:
                experiment_note = """
EXPERIMENT NOTE:
This day includes a simple hands-on activity.
Use ONLY safe household/classroom materials.
Steps: Observe → Record what you see → Explain in own words.
Students write: 'I observed... / This happened because...'
"""

            prompt = f"""Generate ONLY Day {day_num} of a Class 6/7 Physics Lesson Plan.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num} (Age: 11-13 years — use simple, clear language)
Unit     : {unit}
Subject  : Science — Physics
Day      : {day_num} of 5
Duration : 35 minutes

{DISCIPLINE_NOTES}

TODAY'S SECTIONS — COVER ALL IN ORDER:
{sections_str}

Subheadings:
{subheadings_str}

Day Focus   : {day_focus}
Key Terms   : {key_terms_str}
{experiment_note}

{CCQ_CFU_INSTRUCTION_67}

{TAMIL_INSTRUCTION_67}

{DAY_PLAN_STRUCTURE_67}

SPARK STYLE: {spark['style']}
SPARK INSTRUCTION:
{spark['instruction']}

ACTIVITY: {activity}

ABSOLUTE RULES:
- Cover ONLY today's sections — nothing from other days
- Age-appropriate language throughout — Class 6/7 (11-13 years)
- Real-life Indian examples: playground, kitchen, sports, travel
- Page numbers MAY be referenced
- No complex mathematics — focus on concept and observation
- Tamil mirror after EVERY subheading explanation
- Assessment block MANDATORY every day — 3 levels
- Homework gives students CHOICE of 3 formats

GENERATE Day {day_num} using EXACTLY this structure:

<h3 class="day-header">Day {day_num} — [Exact section names]</h3>
<p class="day-meta">Duration: 35 Minutes | Physics | Class {class_num} | {day_focus}</p>

<div class="day-block">

  <!-- [0-5 min] LEAD / SPARK -->
  <div class="time-block lp-section-opening">
    <span class="lp-section-label">Lead / Spark [0–5 min]</span>
    <h4>Science Spark — {spark['style']}</h4>

    {"<p><em>Quick 1-min recap: 2-3 rapid questions from yesterday. Students call out answers.</em></p>" if day_num > 1 else ""}

    <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-minute Science Spark — use {spark['style']} style.
     Curiosity question + Predict or Perish (30 seconds).
     Real-life superpower application of today's physics concept.
     1-word student reflection.
     Connects to today's sections: {', '.join(day_sections)}.]"</p>

    <p class="lp-tamil-scaffold"><em>தமிழில்:</em>
    "[Same opening question in Tamil — age-appropriate, natural Tamil]"</p>

    <p class="lp-teacher-says"><strong>Real-life Connection:</strong><br/>
    "[Why are we learning this? 2-3 sentences. Connect to everyday Indian life —
     playground, sports, kitchen, travel. Age-appropriate for Class 6/7.]"</p>

    <p><em>⏱ Take 3-5 student responses. 2-minute transition to textbook.</em></p>
  </div>

  <!-- [5-20 min] KEY LEARNING ACTIVITY -->
  <div class="time-block lp-section-main">
    <span class="lp-section-label">Key Learning Activity [5–20 min]</span>

    <!-- Topic Introduction -->
    <h4>Topic Introduction — Textbook Context</h4>
    <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[Set context for the topic. Then: 'Let's look at [topic] in our textbook.'
     Page reference if applicable. 2-3 simple sentences for Class 6/7.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[Same explanation in Tamil — same length, same example.
          Age-appropriate Tamil for Class 6/7.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Today's Topic: {' | '.join(day_sections)}<br/>
      Learning Goal: [One clear goal for today]
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead><tr><th>Term</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
        <tbody>
          [4-5 key physics terms from today — simple meanings for Class 6/7.
           Tamil equivalent or transliteration.]
        </tbody>
      </table>
    </div>

    <div class="cfu-block">
      <strong>🔎 CFU 1:</strong>
      <p class="lp-teacher-says">"[Simple what/who question — under 6 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>

    <!-- Topic Explanation with Activity -->
    <h4>Topic Explanation with Activity</h4>

    [FOR EACH section in today's list — in exact order:]

    <h4>[EXACT section heading]</h4>

    [FOR EACH subheading:]
    <h5>[EXACT subheading]</h5>

    <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[Read from textbook. Explain in simple words — 3-4 sentences.
     Real-life Indian example: playground, sports, kitchen, travel.
     Age-appropriate for Class 6/7.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[Same explanation in Tamil — same length, same example.
          Age-appropriate Tamil for Class 6/7.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw / Write on Board:</strong><br/>
      [Simple diagram with arrows OR observation chart OR concept map]<br/>
      [Keep simple for Class 6/7]
    </div>

    <div class="cfu-block">
      <strong>🔎 CFU [N]:</strong>
      <p class="lp-teacher-says">"[Simple factual question — under 6 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>

    <div class="cfu-block">
      <strong>🔎 CFU [N+1]:</strong>
      <p class="lp-teacher-says">"[Which/where/what question — under 6 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or sentence]"</p>
      <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ [N]:</strong>
      <p class="lp-teacher-says">"[Why/How question — simple, under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
      <p><em>⏱ Wait 15 seconds. Allow pair discussion.</em></p>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ [N+1]:</strong>
      <p class="lp-teacher-says">"[What would happen if...? — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
      <p><em>⏱ Wait 15 seconds. Allow pair discussion.</em></p>
    </div>

    [REPEAT for each section/subheading in today's list]

    <!-- Activity -->
    <div class="activity-block">
      <strong>⚙️ Activity — {activity.split(chr(10))[0]}:</strong>
      <p>[Step by step. Based on today's physics content.
         Uses classroom/household materials. Safe for Class 6/7.
         Students observe, record, explain in own words.]</p>
    </div>

    <!-- Topic Closing Summary -->
    <h4>Topic Closing — Summary</h4>
    <div class="board-work">
      <strong>Summary on Board (choose one):</strong><br/>
      [Simple flowchart OR mind map OR observation chart from today]<br/>
      [Keep very simple for Class 6/7]
    </div>
    <p class="lp-teacher-says">"[2-3 sentences summarising today.
     'Copy this summary into your notebooks.']"</p>
  </div>

  <!-- [20-30 min] ASSESSMENT — 3 LEVELS -->
  <div class="time-block lp-section-student-task">
    <span class="lp-section-label">Assessment [20–30 min]</span>
    <h4>Differentiated Assessment — 3 Levels</h4>

    <p class="lp-teacher-says">"Now let's check what we learned.
    Choose your task based on your level."</p>

    <table class="diff-table" style="border: 2px solid #333; width:100%;">
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
            <p><strong>Task:</strong> Fill in the blanks</p>
            <p>[2-3 simple sentences with blanks from today's content]</p>
            <p><strong>Word Bank:</strong> [4 key terms from today]</p>
            <p><em>Teacher sits with this group and helps.</em></p>
            <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
          </td>
          <td>
            <p><strong>Task:</strong> Answer in 2-3 sentences</p>
            <p>"[Core concept question from today's content]"</p>
            <p>Starter: "[sentence starter from today's topic]"</p>
          </td>
          <td>
            <p><strong>Task:</strong> Think and explain</p>
            <p>"[Why/How question requiring deeper thought — from today's physics]"</p>
            <p>Write 4-5 sentences with reason and observation.</p>
          </td>
        </tr>
      </tbody>
    </table>
    <p><em>⏱ 8 minutes. Teacher circulates to each group.</em></p>

    <p class="lp-teacher-says"><strong>Quick Review:</strong><br/>
    "[1-2 answers from each level. Positive feedback. 2 minutes.]"</p>
  </div>

  <!-- [30-35 min] CLOSING + STUDENT TASK -->
  <div class="time-block lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>

    <p class="lp-teacher-says"><strong>2-Minute Recap:</strong><br/>
    "{'[Recap ALL sections from ALL 4 days — rapid fire across full chapter]' if day_num == 4 else '[3 rapid-fire questions about today — hands raised, energetic]'}"</p>

    <div class="board-work">
      <strong>Today's Key Points:</strong><br/>
      1. [Key physics concept from today]<br/>
      2. [Key term or observation from today]<br/>
      3. [Real-life connection from today]
    </div>

    <p class="lp-teacher-says"><strong>Closing Statement:</strong><br/>
    "[2-3 encouraging sentences. What was learned. Connect to real life.
     Age-appropriate and motivating for Class 6/7.]"</p>

    {"" if day_num == 4 else f"""
    <div class="homework-block">
      <p class="lp-teacher-says"><strong>Student Task / Homework:</strong></p>
      <div class="board-work">
        <strong>Choose ONE task (write all 3 on board):</strong><br/>
        Option A: Write the answers to [specific questions from today] in your notebook<br/>
        Option B: Make a poster — draw and label today's key concept with examples<br/>
        Option C: Make a flowchart or mind map showing today's physics concept<br/>
        Submit: Tomorrow morning
      </div>
      <p class="lp-teacher-says"><strong>Preview — {next_preview}:</strong><br/>
      "[1-2 sentences — name exact sections. Build curiosity for next class.]"</p>
    </div>"""}

  </div>

</div>

FINAL CHECKS:
✅ Covered ONLY: {', '.join(day_sections)}
✅ Age-appropriate language — Class 6/7 (11-13 years)
✅ Tamil mirror after EVERY subheading explanation
✅ Tamil in: Opening + Introduction + Every subheading
✅ Assessment block PRESENT — 3 levels with Tamil label for below-average
✅ CFUs numbered sequentially — minimum 2 per concept
✅ CCQs numbered sequentially — minimum 2 per concept
✅ Homework has 3 format choices (except Day 4)
✅ Page numbers may be referenced
✅ No complex maths — concept and observation focus
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ Do NOT generate Day {day_num+1}

Chapter Text (use ONLY this):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=16000,
                system=SCIENCE_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Physics LP 67 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — DAY 5
    # =========================================================================

    def _call_day5(self, text, class_num, unit, lesson_title,
                   sections: dict, day_plan: dict):
        try:
            key_terms  = ", ".join([t for s in sections.get("chapter_sections", [])
                                    for t in s.get("key_terms", [])][:12])
            key_units  = ", ".join(sections.get("key_units", []))
            all_secs   = [s["heading"] for s in sections.get("chapter_sections", [])]
            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"

            prompt = f"""Generate ONLY Day 5 of the Physics Lesson Plan for Class 6/7.
Day 5 = Rapid Recall Quiz + Book-back Marking + Practical Review + Closing.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Day      : 5 of 5
Duration : 35 minutes

ALL SECTIONS: {', '.join(all_secs)}
DAY SUMMARY:
{day_summary}
KEY TERMS : {key_terms}
KEY UNITS : {key_units}

<h3 class="day-header">Day 5 — Recap Quiz and Book-back Exercises</h3>
<p class="day-meta">Duration: 35 Minutes | Physics | Class {class_num} | Evaluation Day</p>

<div class="day-block">

  <div class="time-block lp-section-opening">
    <span class="lp-section-label">Lead / Spark [0–5 min]</span>
    <h4>Chapter Recap Game</h4>
    <p class="lp-teacher-says">"Let's play a quick recall game!
    [3-4 fun clue-based questions covering all 4 days.
     Age-appropriate for Class 6/7. Keep energetic.]"</p>
    <p><em>4-5 student responses. 2-minute transition.</em></p>
  </div>

  <div class="time-block lp-section-main">
    <span class="lp-section-label">Key Learning Activity [5–20 min]</span>

    <h4>Rapid Recall Quiz — 10 Questions</h4>
    <p class="lp-teacher-says">"Write answers in notebook. No discussion yet."</p>
    <div class="board-work">
      <strong>10 Quiz Questions (write on board):</strong><br/>
      1-2: [Day 1 content — simple factual]<br/>
      3-4: [Day 2 content — simple factual]<br/>
      5-6: [Day 3 content — simple factual]<br/>
      7-8: [Day 4 content — simple factual]<br/>
      9: [Key unit of measurement from chapter]<br/>
      10: [Key physics term from chapter]<br/>
      <strong>Answers:</strong> [Write all answers — students self-mark]
    </div>

    <h4>Book-back Exercise Marking</h4>
    <p><em>Teacher facilitates marking. QA section has all model answers.</em></p>

    <h5>Section 1: Choose Correct Answer / Fill Blanks</h5>
    <p>[Explain 3-4 key answers. WHY correct — simple language for Class 6/7.]</p>

    <h5>Section 2: Short Answer Questions</h5>
    <p>[Model answer structure — simple sentences for Class 6/7.]</p>

    <div class="board-work">
      <strong>Key Answers on Board:</strong><br/>
      [Main answers for student verification]
    </div>

    <h4>Practical Concept Review</h4>
    <p>[Quick hands-on reminder activity OR observation recap from chapter.
       Based on actual chapter experiments/demos. Safe for Class 6/7.]</p>
  </div>

  <div class="time-block lp-section-student-task">
    <span class="lp-section-label">Assessment [20–30 min]</span>
    <h4>Final Chapter Assessment — 3 Levels</h4>
    <table class="diff-table" style="border: 2px solid #333; width:100%;">
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
            <p><strong>Task:</strong> Fill blanks with word bank</p>
            <p><strong>Word Bank:</strong> [6 key terms from full chapter]</p>
            <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
          </td>
          <td>
            <p><strong>Task:</strong> Answer 3 questions — 2-3 sentences each</p>
            <p>[3 core questions from full chapter]</p>
          </td>
          <td>
            <p><strong>Task:</strong> Explain + Design</p>
            <p>"Explain [key physics concept] and draw a diagram showing it."</p>
            <p>6-8 sentences with diagram.</p>
          </td>
        </tr>
      </tbody>
    </table>
    <p><em>⏱ 8 minutes. Teacher circulates.</em></p>
  </div>

  <div class="time-block lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>
    <p class="lp-teacher-says">"[Congratulate students. Name 2-3 specific things learned.
     Connect physics to everyday life. Encouraging for Class 6/7.]"</p>
    <div class="board-work">
      <strong>Submit before leaving:</strong><br/>
      ☐ Notebook — all 5 days of notes completed<br/>
      ☐ Book-back exercises answered and marked<br/>
      ☐ All homework from Days 1-4
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="day-header">Day 5
- Age-appropriate for Class 6/7
- No Tamil in Day 5
- Page numbers may be referenced
- Do NOT generate any other day

Chapter Text:
---
{text[:4000]}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system=SCIENCE_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Physics LP 67 Day 5 error: {e}")
            return None

    # =========================================================================
    # CALL 7 — ASSESSMENT
    # =========================================================================

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, sections: dict, day_plan: dict):
        try:
            all_sections = sections.get("chapter_sections", [])
            sections_str = ", ".join([s["heading"] for s in all_sections])
            key_terms    = ", ".join([t for s in all_sections for t in s.get("key_terms", [])][:10])
            day_summary  = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Physics chapter (Class 6/7).

Chapter  : {lesson_title}
Class    : {class_num}
All Sections: {sections_str}
Key Terms: {key_terms}
Day-wise:
{day_summary}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Oral Assessment</h3>
  <table>
    <thead>
      <tr><th>Day</th><th>Sections</th><th>Question (English)</th>
      <th>Expected Answer</th><th>Tamil Prompt</th></tr>
    </thead>
    <tbody>
      [5 rows — Day 1-5. Simple age-appropriate physics questions.
       Tamil version in last column.]
    </tbody>
  </table>

  <h3>CFU Bank — Quick Reference</h3>
  <ol>[10 CFU questions — 2 per major section. Under 6 words. Simple for Class 6/7.]</ol>

  <h3>CCQ Bank</h3>
  <ol>[8 CCQ questions — Why/How. Age-appropriate. Under 8 words. Tamil noted.]</ol>

  <h3>Differentiated Worksheet — 3 Levels</h3>
  <table class="diff-table" style="border: 2px solid #333;">
    <thead>
      <tr>
        <th>Below Average (கஷ்டப்படும்)</th>
        <th>Average Students (சராசரி)</th>
        <th>Toppers (திறமையான)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p>Fill blanks with word bank</p>
          <p><strong>Word Bank:</strong> [8 key terms]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p>Answer 3 questions — 2-3 sentences each</p>
          <p>[Core concept questions from chapter]</p>
        </td>
        <td>
          <p>Explain + Draw + Apply</p>
          <p>"Explain [concept] + draw diagram + give 2 real-life examples"</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Key Terms Checklist</h3>
  <ul>
    [Each key term: ☐ [Term]: [simple one-line definition for Class 6/7]]
  </ul>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed</li>
    <li>☐ All homework submitted (Days 1-4)</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Rapid recall quiz attempted (Day 5)</li>
    <li>☐ Key terms defined in own words</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Age-appropriate for Class 6/7
- Tamil in oral assessment table only
- Base all content on actual extracted sections

Chapter Text:
---
{text[:3000]}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system=SCIENCE_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Physics LP 67 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

physics_lp_67_builder = PhysicsLP67Builder()