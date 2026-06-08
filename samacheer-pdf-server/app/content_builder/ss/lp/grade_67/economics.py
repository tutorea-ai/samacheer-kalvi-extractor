"""
economics.py
------------
LP Builder for Samacheer Kalvi Social Science — Economics
Class 6 & 7

v1.0 — Follows grade_67 pattern (May 2026)

Architecture mirrors grade_67/civics.py with Economics-specific differences:
  ✅ Two-pass analyser (Call 0a: Section Extractor, Call 0b: Day Allocator)
  ✅ Same 4-day structure
  ✅ Same Day Plan template (35 mins):
       [0-5 min]   Lead/Spark/Opening Question
       [5-20 min]  Key Learning Activity
       [20-30 min] Assessment (3 levels)
       [30-35 min] Closing + Student Task
  ✅ Economics-specific features:
       - Story-driven teaching (local context — tea shop, canteen, market)
       - Simple formula box at start of each day
       - Large group discussion before teacher explains
       - Sector identification activities
       - Real-life connections every day
  ✅ Page numbers ALLOWED (Class 6/7)
  ✅ Tamil in 3 places only
  ✅ Age-appropriate language for Class 6/7 (11-13 years)

API calls: 7 total
  Call 0a → Section Extractor  (JSON)
  Call 0b → Day Allocator      (JSON)
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
# ECONOMICS DISCIPLINE NOTES — GRADE 6/7
# ============================================================================

ECONOMICS_DISCIPLINE_NOTES_67 = """
ECONOMICS-SPECIFIC TEACHING NOTES (Class 6 & 7):
- Story-driven teaching — use local analogies (tea shop, school canteen, market)
- Every concept needs a simple real-life story BEFORE the formal definition
- Simple formula box at start of each day — students copy first
- Large group discussion BEFORE teacher explains — student ideas first
- Sector identification: teacher describes a real person → student identifies sector
- Real-life connections: connect every concept to students' daily life
- Age-appropriate language — simple, relatable, engaging for Class 6/7
- No complex calculations — concept understanding and simple formulas only
- Connect to students' immediate environment: school canteen, local market, neighbourhood
- Pocket money, bus ticket, school bag — use these as economic examples
"""


# ============================================================================
# ECONOMICS SPARK STYLES — 4 days, age-appropriate
# ============================================================================

ECON_SPARK_STYLES_67 = {
    1: {
        "style": "Classroom Game",
        "instruction": """Run a quick physical game that demonstrates today's core economic concept.
Students stand up and physically respond to teacher's prompts.
Game must be directly connected to today's topic.
Keep it simple and fun for Class 6/7.
End with a Big Question connecting to today's topic.
Example: Good vs Service game — teacher shouts item → students grab air (Good) or clap (Service).
Tell students WHY they are learning this and WHERE they use it in real life.""",
    },
    2: {
        "style": "Two Objects Comparison",
        "instruction": """Hold up or describe two real objects that look similar but differ economically.
Use the contrast to reveal a simple economic rule.
Keep comparison simple and relatable for Class 6/7.
End with Big Question connecting to today's topic.
Example: Homemade lunch vs canteen lunch → which adds to production?""",
    },
    3: {
        "style": "Story / Visual Metaphor",
        "instruction": """Tell a short story using contrasting characters from students' daily life.
Story must represent today's economic concepts simply.
Make it relatable — school, family, neighbourhood context.
End with Big Question connecting to today's topic.
Example: A student who saves vs a student who spends everything → what happens over time?""",
    },
    4: {
        "style": "Rapid Fire Recall Quiz",
        "instruction": """Start with a fun rapid-fire quiz reviewing key concepts from Days 1-3.
Teacher shouts a keyword/concept → students shout the answer.
Keep it energetic and fun for Class 6/7.
5-6 quick questions. Standing format if possible.
Then transition: 'Today we put everything together and check what we learned.'""",
    },
}


# ============================================================================
# ECONOMICS ACTIVITY MAP — 4 days
# ============================================================================

ECON_ACTIVITY_MAP_67 = {
    1: "Local Market Story (teacher narrates a simple market story → students connect each concept to the story) + Simple formula writing on board (students copy)",
    2: "Sector Identification Game (teacher describes a real person/job → students shout Primary/Secondary/Tertiary) + Group Discussion (student ideas first, teacher consolidates)",
    3: "Real-life Hunt (students identify economic examples from their own neighbourhood/home) + Think-Pair-Share (connect today's concept to their daily life)",
    4: "Mind Map on Board (teacher draws full chapter mind map → students copy and complete gaps) + Quick Quiz (5 questions from all 4 days)",
}


# ============================================================================
# ECONOMICS CLOSING STYLES — 4 days
# ============================================================================

ECON_CLOSING_STYLES_67 = {
    1: "Recap Table — students complete a simple two-column table: Economic Term | What it means in my daily life",
    2: "Sector Sentence — 'I found a [sector] worker today — [name/job] — because [reason]'",
    3: "Real-life Connection — students write one sentence connecting today's concept to something they see at home or school",
    4: "3-2-1 Reflection — 3 things learned, 2 economic terms I remember, 1 way economics affects my daily life",
}


# ============================================================================
# ECONOMICS LP BUILDER CLASS — GRADE 6/7
# ============================================================================

class EconomicsLP67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Economics LP Builder (67) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [Economics LP 67 v1] Generating: {lesson_title}")
        print(f"      [Economics LP 67 v1] 7 API calls: 0a+0b+Preamble+Day1-4+Assessment")

        parts = []

        print(f"      [Economics LP] Call 0a/7: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting LP")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        print(f"      [Economics LP] Call 0b/7: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting LP")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        print(f"      [Economics LP] Call 1/7: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, month, sections, day_plan
        )
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting LP")
            return None

        for day_num in range(1, 5):
            call_num = day_num + 1
            print(f"      [Economics LP] Call {call_num}/7: Day {day_num}...")
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

        print(f"      [Economics LP] Call 6/7: Assessment...")
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
        print(f"      [Economics LP 67 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            # Sanitize text before injecting into JSON prompt
            safe_text = text.replace('\\', ' ').replace('"', "'").replace('\r', ' ').replace('\x00', ' ')

            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Economics chapter (Class 6/7).

YOUR ONLY JOB: Extract EXACTLY the headings and subheadings that appear in the chapter text.
Do NOT add anything from general knowledge. Extract ONLY what is in the text.

Chapter: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON only.

{{
  "chapter_sections": [
    {{
      "heading": "EXACT heading text from chapter",
      "subheadings": ["exact subheading 1", "exact subheading 2"],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "formulas": ["formula1"],
      "local_analogy": "simple story analogy for this section"
    }}
  ],
  "total_estimated_teaching_mins": 60,
  "all_formulas": ["formula1", "formula2"],
  "key_terms": ["term1", "term2"],
  "sector_examples": ["Farmer → Primary", "Factory worker → Secondary"]
}}

STRICT EXCLUSION — DO NOT extract:
Exercises, Summary, Glossary, Internet Resources, ICT CORNER,
Learning Objectives, Student Activity, Life Skill, Answer Grid,
HOTS, Choose the correct answer, Fill in the blanks, Match the following

Chapter Text:
---
{safe_text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system="You are a strict text extractor. Return ONLY valid JSON. No markdown. Raw JSON starting with {",
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
            print(f"❌ Economics 67 Section Extractor JSON error: {e}")
            print(f"❌ Raw response (first 500 chars): {raw[:500]}")
            return None
        except Exception as e:
            print(f"❌ Economics 67 Section Extractor error: {e}")
            return None

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        try:
            sections_str = json.dumps(sections, indent=2)
            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Economics lesson plan (Class 6/7).

Allocate extracted sections to 4 days.

RULES:
- Each day has 15 minutes of Key Learning Activity time
- Use estimated_teaching_time_mins to fill each day
- Do NOT split a section across two days
- Day 4 = final sections + chapter consolidation
- Every section must appear in exactly ONE day
- Use EXACT heading text from extracted sections

Return ONLY valid JSON. No markdown. Raw JSON starting with {{

{{
  "day1": {{
    "sections": ["EXACT heading"],
    "subheadings": ["subheading"],
    "formulas": ["formula if any"],
    "focus": "One sentence",
    "story_analogy": "local story for this day",
    "estimated_mins": 15,
    "continuation_from_previous": false
  }},
  "day2": {{ ... }},
  "day3": {{ ... }},
  "day4": {{ ... }}
}}

Extracted Sections:
---
{sections_str}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=2000,
                system="You are a strict day allocator. Return ONLY valid JSON. No markdown. Raw JSON starting with {",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"❌ Economics 67 Day Allocator JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Economics 67 Day Allocator error: {e}")
            return None

    def _call_preamble(self, text, class_num, unit,
                       lesson_title, month, sections: dict, day_plan: dict):
        try:
            sections_list = sections.get("chapter_sections", [])
            sections_str  = "\n".join([
                f"  - {s['heading']}: {', '.join(s.get('subheadings', []))}"
                for s in sections_list
            ])
            all_formulas = "\n".join([f"  - {f}" for f in sections.get("all_formulas", [])])
            key_terms    = ", ".join(sections.get("key_terms", []))

            day_summary = ""
            for d in range(1, 5):
                day_data     = day_plan.get(f"day{d}", {})
                day_sections = day_data.get("sections", [])
                day_focus    = day_data.get("focus", "")
                day_summary += f"  Day {d}: {', '.join(day_sections)} — {day_focus}\n"

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — Economics Lesson Plan for Class 6/7.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Economics
Month    : {month if month else 'As scheduled'}
Duration : 4 Days × 35 Minutes = 140 Minutes Total

CHAPTER SECTIONS:
{sections_str}

DAY-WISE PLAN:
{day_summary}

ALL FORMULAS:
{all_formulas if all_formulas else '  [Identify from chapter]'}

KEY TERMS: {key_terms}

Generate these sections:

<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Topics Covered | Key Formulas | Learning Objectives
</table>

<h2>Part 2: Value-Based Objectives</h2>
<ul>3-4 value objectives — age-appropriate for Class 6/7</ul>

<h2>Part 3: Skill Objectives</h2>
<ul>3-4 skill objectives — formula application, observation, communication</ul>

<h2>Part 4: Learning Objectives</h2>
<ul>4-5 objectives with action verbs — Define, Identify, Explain, Apply</ul>

<h2>Part 5: Formula Reference Sheet</h2>
<div class="board-work">
  <strong>📐 All Formulas in This Chapter:</strong><br/>
  {all_formulas if all_formulas else '[All formulas from chapter]'}
</div>

<h2>Part 6: Teaching Aids</h2>
<ul>All materials needed — textbook, board, chalk, objects for sparks,
formula chart, sector identification cards</ul>

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids </ul>
- Age-appropriate for Class 6/7

Chapter Text:
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Economics LP 67 preamble error: {e}")
            return None

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            spark         = ECON_SPARK_STYLES_67[day_num]
            task          = STUDENT_TASK_STYLES[day_num]
            activity      = ECON_ACTIVITY_MAP_67.get(day_num, "group discussion")
            closing_style = ECON_CLOSING_STYLES_67.get(day_num, "Recap")

            day_sections   = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus      = day_data.get("focus", "")
            formulas       = day_data.get("formulas", [])
            story_analogy  = day_data.get("story_analogy", "")
            continuation   = day_data.get("continuation_from_previous", False)

            sections_str    = "\n".join([f"  - {s}" for s in day_sections])
            subheadings_str = "\n".join([f"    • {s}" for s in day_subheadings])
            formulas_str    = "\n".join([f"  - {f}" for f in formulas])

            continuation_note = ""
            if continuation:
                prev_sections = day_plan.get(f"day{day_num-1}", {}).get("sections", [])
                continuation_note = f"""
⚠️ CONTINUATION FROM DAY {day_num-1}:
Start by completing: {', '.join(prev_sections[-1:])}
"""

            closing_note = ""
            if day_num == 4:
                closing_note = """
⚠️ DAY 4 CLOSING — FULL CHAPTER RECAP:
Recap ALL sections from ALL 4 days.
Mind map on board covering full chapter.
3-2-1 Reflection: 3 things learned, 2 economic terms, 1 real-life connection.
"""

            next_label = f"Day {day_num + 1}" if day_num < 4 else "end of chapter"

            prompt = f"""Generate ONLY Day {day_num} of the Economics lesson plan for Class 6/7.
Nothing else. Do NOT include Preamble. Do NOT generate Day {day_num + 1}.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years — use age-appropriate language)
Unit     : {unit}
Subject  : Social Science — Economics
Day      : {day_num} of 4
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S EXACT SECTIONS
═══════════════════════════════════════════════════════
Sections:
{sections_str}

Subheadings:
{subheadings_str if subheadings_str else "  [Cover all subheadings]"}

Formulas for today:
{formulas_str if formulas_str else "  [Identify from chapter — keep simple for Class 6/7]"}

Story Analogy: {story_analogy if story_analogy else "Use local market / school canteen / neighbourhood context"}
Day Focus: {day_focus}
{continuation_note}
{closing_note}

⛔ ABSOLUTE RULE: Cover ONLY sections listed above.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
CFU/CCQ RULES — ECONOMICS Class 6/7
═══════════════════════════════════════════════════════
Minimum 2 CFU + 2 CCQ per concept taught.

CFU — formula-based or concept-based:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <p class="teacher-says">"[Simple formula or concept question — under 6 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One word or short phrase]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

CCQ — deeper why/how with Tamil:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="teacher-says">"[Why/How question — simple, under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion.</em></p>
</div>

NEVER use ICQs: "Do you understand?" / "How many sentences?"
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING — TARGETED ONLY
═══════════════════════════════════════════════════════
Tamil in EXACTLY 3 places:
✅ 1. KEY TERMS TABLE — Tamil meaning column
✅ 2. MAIN EXPLANATION — Tamil mirror after English
✅ 3. OPENING LEAD QUESTION — Tamil version

❌ NEVER in: activity, formula box, board work, closing, homework
Real Tamil Unicode only. Age-appropriate. No Hindi words.
═══════════════════════════════════════════════════════

DAY STRUCTURE:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — [EXACT section names today]</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Economics | Class {class_num} | {day_focus}</p>

  <!-- SECTION 1: LEAD / SPARK (0-5 min) -->
  <div class="lp-section-opening">
    <div class="lp-section-label">🎯 Lead / Spark / Opening Question</div>
    <span class="lp-time">[0–5 min]</span>

    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[{spark['style']} style — simple, fun, engaging for Class 6/7.
       Connect to today's sections: {', '.join(day_sections)}.
       Use local context (canteen, market, pocket money).
       End with Big Question. Tell WHY they learn this.]"
    </div>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
      "[Same opening in Tamil — age-appropriate]"
    </div>

    <p><em>⏱ Wait 20 seconds. Take 3-5 student responses.</em></p>
  </div><!-- end lp-section-opening -->

  <!-- SECTION 2: KEY LEARNING ACTIVITY (5-20 min) -->
  <div class="lp-section-main">
    <div class="lp-section-label">🏫 Key Learning Activity</div>
    <span class="lp-time">[5–20 min]</span>

    <h4>Topic Introduction</h4>
    <div class="lp-teacher-says">
      <strong>Teacher says (English):</strong><br/>
      "[Introduce topic with local story FIRST — then formal term.
       'Let's look at [topic] in our textbook.' Page reference if applicable.]"
    </div>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
      "[Same introduction in Tamil]"
    </div>

    <div class="board-work">
      <strong>📐 Formulas for Today (write on board first):</strong><br/>
      {formulas_str if formulas_str else '[Simple formulas from today — students copy first]'}
    </div>

    <div class="vocab-block">
      <strong>Key Economic Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Real-life Example</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [4-5 key terms from TODAY's sections — simple for Class 6/7
           Real-life example: pocket money, bus ticket, canteen food]
        </tbody>
      </table>
    </div>

    [CFU after introduction]

    <h4>Topic Explanation with Activity — {activity}</h4>

    [For EACH section in today's list:]
    <h4>[Section heading — EXACTLY as listed]</h4>
    [For EACH subheading:]
    <h5>[Subheading — exactly as extracted]</h5>

    <div class="lp-teacher-says">
      <strong>Teacher says (English — Story First):</strong><br/>
      "[Tell local story FIRST — then connect to formal economic term.
       3-4 simple sentences. Age-appropriate for Class 6/7.
       Use: school canteen, local market, pocket money examples.
       Based ONLY on chapter text.]"
    </div>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
      "[Same explanation in Tamil — context-based, age-appropriate]"
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      [Formula + simple numerical example if applicable]<br/>
      [Key points from this section]
    </div>

    [CFU — formula or concept based]
    [CCQ — simple why/how question]

    [Repeat for each section/subheading]

    <div class="activity-block">
      <strong>Activity — {activity.split('+')[0].strip()}:</strong>
      <p>[Step by step. English only. Simple and fun for Class 6/7.
         Large group discussion BEFORE teacher explains — student ideas first.
         Sector identification: teacher describes person → students shout sector.]</p>
      <p><em>⏱ 5-6 minutes. Teacher circulates.</em></p>
    </div>

    [CFU after activity]

    <h4>Topic Summary</h4>
    <div class="board-work">
      <strong>Summary on Board:</strong><br/>
      [Simple key points or recap table: Economic Term | Real-life meaning]
    </div>

  </div><!-- end lp-section-main -->

  <!-- SECTION 3: ASSESSMENT (20-30 min) -->
  <div class="lp-section-student-task">
    <div class="lp-section-label">✏️ Assessment — 3 Levels</div>
    <span class="lp-time">[20–30 min]</span>

    <div class="lp-teacher-says">
      <strong>Teacher says:</strong><br/>
      "Now let's check what we learned today. Choose your task based on your level."
    </div>

    <div class="diff-block">
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
              <p><strong>Task:</strong> Fill in formula blanks with word bank</p>
              <p><strong>Word Bank:</strong> [4 key terms from today]</p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>"The [concept] is important because _______."</p>
            </td>
            <td>
              <p><strong>Task:</strong> Explain and give real example</p>
              <p>"Explain [concept] and give one example from your neighbourhood."</p>
            </td>
          </tr>
        </tbody>
      </table>
      <p><em>⏱ 8 minutes. Teacher circulates.</em></p>
    </div>

  </div><!-- end lp-section-student-task -->

  <!-- SECTION 4: CLOSING + STUDENT TASK (30-35 min) -->
  <div class="lp-section-closing">
    <div class="lp-section-label">🔔 {"Full Chapter Recap & Closing" if day_num == 4 else "Closing & Student Task"}</div>
    <span class="lp-time">[30–35 min]</span>

    <div class="lp-teacher-says">
      <strong>{"Chapter Recap" if day_num == 4 else "2-Minute Recap"}:</strong><br/>
      "{'[Recap ALL sections from ALL 4 days. Mind map on board. 3-2-1 Reflection.]' if day_num == 4 else '[3 rapid-fire questions about today. Students shout answers.]'}"
    </div>

    <div class="board-work">
      <strong>{"Full Chapter" if day_num == 4 else "Today's"} Key Points:</strong><br/>
      1. [Key economic point 1]<br/>
      2. [Key economic point 2]<br/>
      3. [Key economic point 3]
    </div>

    <div class="lp-teacher-says">
      <strong>Closing Reflection:</strong><br/>
      "[{closing_style}]"
    </div>

    <div class="board-work">
      <strong>Sentence Frame:</strong><br/>
      "{closing_style.split('—')[0].strip()} frame"
    </div>

    {"" if day_num == 4 else f'''
    <div class="board-work">
      <strong>Homework (write on board):</strong><br/>
      [Specific real-life task from today's economic concept]<br/>
      Preview: {next_label} — [1 sentence about what comes next]
    </div>'''}

  </div><!-- end lp-section-closing -->

</div><!-- end lp-day-block -->

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS
═══════════════════════════════════════════════════════
✅ Covered ONLY sections: {', '.join(day_sections)}
✅ Formula box present at start of Introduction
✅ Story/analogy BEFORE formal definition
✅ Large group discussion — student ideas first
✅ Minimum 2 CFUs + 2 CCQs per concept
✅ Assessment has 3 levels
✅ Tamil in exactly 3 places only
✅ Age-appropriate language throughout
✅ Local context (canteen, market, pocket money)
✅ Page numbers may be referenced
✅ Raw HTML only — start with <div class="lp-day-block">
✅ Do NOT generate Day {day_num + 1}

Chapter Text:
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
            print(f"❌ Economics LP 67 Day {day_num} error: {e}")
            return None

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, sections: dict, day_plan: dict):
        try:
            all_sections = sections.get("chapter_sections", [])
            sections_str = ", ".join([s["heading"] for s in all_sections])
            all_formulas = "\n".join([f"  - {f}" for f in sections.get("all_formulas", [])])
            key_terms    = ", ".join(sections.get("key_terms", []))

            day_summary = ""
            for d in range(1, 5):
                day_data     = day_plan.get(f"day{d}", {})
                day_sections = day_data.get("sections", [])
                day_summary += f"  Day {d}: {', '.join(day_sections)}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Economics chapter (Class 6/7).
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num} (Age group: 11-13 years)
Unit     : {unit}
Subject  : Social Science — Economics
Total Days: 4

ALL SECTIONS: {sections_str}
ALL FORMULAS:
{all_formulas if all_formulas else '  [From chapter]'}
KEY TERMS: {key_terms}

DAY-WISE:
{day_summary}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Formula Reference Sheet</h3>
  <div class="board-work">
    <strong>📐 All Formulas — Students Must Know:</strong><br/>
    {all_formulas if all_formulas else '[All formulas from chapter]'}
  </div>

  <h3>Day-wise Oral Assessment</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th><th>Main Topic</th>
        <th>Oral Question (English)</th>
        <th>Expected Answer</th>
        <th>Tamil Prompt</th>
      </tr>
    </thead>
    <tbody>
      [4 rows — Day 1 to Day 4.
       Simple age-appropriate questions for Class 6/7.
       Mix of formula, concept, sector identification.
       Tamil version in last column.]
    </tbody>
  </table>

  <h3>CFU Bank</h3>
  <p><em>Simple recall questions — 2 per section:</em></p>
  <ol>
    [8 CFU questions — formula-based or concept-based.
     Simple language for Class 6/7.
     Based on actual chapter content.]
  </ol>

  <h3>CCQ Bank</h3>
  <p><em>8 deeper why/how questions for revision:</em></p>
  <ol>
    [8 CCQ questions — if X happens, what happens to Y?
     Age-appropriate. Based on actual chapter content.]
  </ol>

  <h3>50-Mark Differentiated Worksheet</h3>
  <div class="board-work">
    <strong>🟢 Level 1 — Below Average (50 marks)</strong><br/>
    Q1-Q10: Fill in the blanks with word bank (1 mark = 10)<br/>
    Q11-Q20: Choose correct answer — MCQ (1 mark = 10)<br/>
    Q21-Q25: Match the following (2 marks = 10)<br/>
    Q26-Q30: Answer in ONE sentence (4 marks = 20)<br/>
    <br/>
    <strong>🟡 Level 2 — Average (50 marks)</strong><br/>
    Q1-Q10: Fill in blanks (1 mark = 10)<br/>
    Q11-Q15: Simple calculation using formula (4 marks = 20)<br/>
    Q16-Q20: Answer in 2-3 sentences (4 marks = 20)<br/>
    <br/>
    <strong>🔴 Level 3 — Advanced (50 marks)</strong><br/>
    Q1-Q5: Choose correct answer (1 mark = 5)<br/>
    Q6-Q15: Answer in 2-3 sentences (2 marks = 20)<br/>
    Q16-Q20: Answer in detail (5 marks = 25)<br/>
    <em>All questions from actual chapter content. Age-appropriate.</em>
  </div>

  <h3>3-2-1 Final Reflection</h3>
  <div class="board-work">
    3 economic terms I learned<br/>
    2 real-life examples of economics I see every day<br/>
    1 way economics affects my daily life
  </div>

  <h3>Differentiated Assessment</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Below Average<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
        <th>Average Students<br/>(சராசரி மாணவர்கள்)</th>
        <th>Toppers<br/>(திறமையான மாணவர்கள்)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Task:</strong> Fill formula blanks with word bank</p>
          <p><strong>Word Bank:</strong> [5 key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions + simple calculation</p>
          <p>"If [X] = 100 and [Y] = 20, find [Z]."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Explain with real example</p>
          <p>"Explain [key concept] with an example from your neighbourhood."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 4 days of notes completed</li>
    <li>☐ All formulas copied and understood</li>
    <li>☐ All homework submitted (Days 1-4)</li>
    <li>☐ 50-mark worksheet completed (Day 4)</li>
    <li>☐ 3-2-1 Reflection written</li>
    <li>☐ [Chapter-specific item]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Formula sheet at top
- Day table: exactly 4 rows with Tamil column
- Age-appropriate language throughout
- Base everything on actual chapter content

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
            print(f"❌ Economics LP 67 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

economics_lp_67_builder = EconomicsLP67Builder()