"""
chemistry.py
------------
LP Builder for Samacheer Kalvi Science — Chemistry
Class 9 & 10

v1.0 — May 2026
Built to match teacher-approved manual LP reference (Chemistry: Atoms and Molecules)
Modeled on ss/lp/grade_910/history.py structure.

v1.1 — May 2026 (team feedback fixes)
  Fix 1: Spark block — added "Why are we learning this?" real-life use paragraph
  Fix 2: Numerical days — enforced Given→Formula→Substitution→Answer worked example structure
  Fix 3: Day 4 Board Race — replaced generic activity with structured 4-round dynamic tournament
  Fix 4: Final checks — added explicit departure shout verification (≥3 rounds mandatory)
  Fix 5: Assessment — formula checklist now includes unit + real-use case per formula;
          Avogadro's Law and VD checklist items added to completion checklist
  Fix 6: Tamil placement — restricted to Opening + Introduction + FIRST subheading of Topic 1 only

REFERENCE: Manual LP "Atoms and Molecules" — Grade 10 Chemistry
           Built by TNQ/Tutorea.ai teacher team — used as gold standard

STRUCTURE PER DAY (matches manual LP exactly):
  [0-5 min]   Spark / Hook / Opening
              → Real-object analogy OR dramatic entry OR formula puzzle
              → Big Question connecting to today's concept
              → 2-3 student guesses before teacher reveals focus
              → Day 2+: starts with previous day rapid-fire recap

  [5-10 min]  Introduction
              → Teacher explains today's concept in simple words
              → Real-life connection or analogy
              → Write topic + learning objective on board
              → Key terms table (English + Tamil meaning)
              → 1 CCQ from the introduction

  [10-20 min] Main Teaching — Topic 1
              → Teacher explains concept with board diagram/formula
              → Reads from textbook — explains sub-point by sub-point
              → Real-life example or analogy per sub-point
              → Day-specific student activity embedded here
              → CCQs woven in after each sub-point

  [20-30 min] Main Teaching — Topic 2
              → Same pattern as Topic 1
              → Day-specific strategy applied
              → Students calculate / classify / observe / explain

  [30-35 min] Closing
              → Final Departure Shout (call-and-response)
              → Student Task: 2 specific written homework tasks
              → Preview next day (name exact concepts)
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
    SCIENCE_LP_SYSTEM_PROMPT,
    clean,
    PREAMBLE_START_INSTRUCTION,
    TAMIL_INSTRUCTION,
    CCQ_INSTRUCTION,
    SCIENCE_SPARK_STYLES,
    SCIENCE_ACTIVITY_MAP,
)


# ============================================================================
# TEACHING STRATEGY PER DAY — matches manual LP reference
# Chemistry-flavored: analogy-driven, formula-on-board, call-and-response
# ============================================================================

DAY_STRATEGY = {
    1: {
        "spark_style":   SCIENCE_SPARK_STYLES[1]["style"],
        "spark_instruction": SCIENCE_SPARK_STYLES[1]["instruction"],
        "topic1_strategy": (
            "TEACHER ROLE: Explainer + Board Diagram Drawer + Call-and-Response Leader\n"
            "Step 1: Write today's concept name and learning objective on board.\n"
            "Step 2: Read the section aloud from textbook — sentence by sentence.\n"
            "Step 3: After each sub-point STOP and explain in simple words.\n"
            "        Add a real-life analogy for EACH sub-point.\n"
            "        Example style: 'Just like how [everyday object/situation]...'\n"
            "Step 4: Draw concept diagram or formula on board WHILE explaining.\n"
            "        Build it step by step — not all at once.\n"
            "Step 5: Ask 1-2 CCQ questions mid-explanation after each sub-point.\n"
            "        Students answer by raising hands or calling out."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Comparison Facilitator + Board Table Builder\n"
            "Step 1: Draw a comparison table on board (e.g. Old vs New, Type A vs Type B).\n"
            "Step 2: Read aloud and fill table column by column while explaining.\n"
            "Step 3: Ask 2 students to explain one row of the table back to class.\n"
            "Step 4: Students copy table into notebook.\n"
            "        Teacher circulates and checks for accuracy."
        ),
        "activity": SCIENCE_ACTIVITY_MAP[1],
        "closing_shout": (
            "Call-and-response: Teacher asks key concept question → "
            "Students shout answer together. Run 3 rounds."
        ),
    },
    2: {
        "spark_style":   SCIENCE_SPARK_STYLES[2]["style"],
        "spark_instruction": SCIENCE_SPARK_STYLES[2]["instruction"],
        "topic1_strategy": (
            "TEACHER ROLE: Formula Explainer + Classification Guide\n"
            "Step 1: Write today's formula or classification structure on board first.\n"
            "Step 2: Explain using textbook — sub-point by sub-point.\n"
            "Step 3: Students take active notes while teacher explains.\n"
            "Step 4: TEAM SORTING ACTIVITY — embedded here (see Activity block).\n"
            "Step 5: 2 CCQ questions after the sorting activity."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Worked Example Demonstrator\n"
            "Step 1: Write a worked example on board — show full step-by-step solution.\n"
            "Step 2: Explain each step — WHY this step, not just WHAT.\n"
            "Step 3: Ask students to solve a parallel example in their notebook — 3 minutes.\n"
            "Step 4: 1 student writes their solution on board.\n"
            "        Class checks — teacher corrects if needed."
        ),
        "activity": SCIENCE_ACTIVITY_MAP[2],
        "closing_shout": (
            "Call-and-response: 'One [unit/formula/term] equals...?' → "
            "Students shout correct answer. Run 3 rounds from today's content."
        ),
    },
    3: {
        "spark_style":   SCIENCE_SPARK_STYLES[3]["style"],
        "spark_instruction": SCIENCE_SPARK_STYLES[3]["instruction"],
        "topic1_strategy": (
            "TEACHER ROLE: Concept Hub Builder + Worksheet Facilitator\n"
            "Step 1: Draw the concept hub / conversion diagram on board.\n"
            "        (e.g. Mole Concept Hub: mass ↔ moles ↔ volume ↔ particles)\n"
            "Step 2: Explain each arrow / conversion path from textbook.\n"
            "Step 3: Students copy hub into notebooks and label each path.\n"
            "Step 4: Teacher gives 1 worked example per conversion path.\n"
            "Step 5: 2 CCQ questions after each path explanation."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Formula Derivation Guide\n"
            "Step 1: Write the formula to be derived on board.\n"
            "Step 2: Show derivation step by step — reference textbook.\n"
            "Step 3: Students mimic or chant the rule if there is a verbal pattern.\n"
            "        Example: 'More volume, more molecules!'\n"
            "Step 4: Give 1 numerical example from textbook — solve together.\n"
            "Step 5: 2 CCQ questions on the formula."
        ),
        "activity": SCIENCE_ACTIVITY_MAP[3],
        "closing_shout": (
            "Final Departure Shout: Teacher gives formula stem → "
            "Students complete it aloud together. Run 3 rounds."
        ),
    },
    4: {
        "spark_style":   SCIENCE_SPARK_STYLES[4]["style"],
        "spark_instruction": SCIENCE_SPARK_STYLES[4]["instruction"],
        "topic1_strategy": (
            "TEACHER ROLE: Math Arena Coach — Level 1 & 2\n"
            "Step 1: Write the problem type and formula on board.\n"
            "Step 2: Solve one full worked example — narrate every step aloud.\n"
            "        'Step 1: identify what is given. Step 2: identify what is asked.'\n"
            "Step 3: Students solve a parallel problem in pairs — 3 minutes.\n"
            "Step 4: One pair writes solution on board — class verifies.\n"
            "Step 5: 2 CCQ questions checking formula understanding."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Math Arena Coach — Level 3 (Advanced)\n"
            "Step 1: Write the harder problem type on board.\n"
            "Step 2: Demonstrate the cross-cancellation or bracket-expansion trick.\n"
            "Step 3: Students solve the Board Race problems (see Activity block).\n"
            "Step 4: Winning team explains their working to class.\n"
            "Step 5: Teacher reviews any common errors on board."
        ),
        "activity": (
            "BOARD RACE TOURNAMENT (embedded in Topic 2):\n"
            "Prepare 4 numerical problems from today's sections.\n"
            "Problems must use ONLY the exact formulas and values from the textbook.\n"
            "Round 1: Problem using the first formula taught today.\n"
            "Round 2: Problem using the second formula taught today.\n"
            "Round 3: A multi-step problem combining two formulas from today.\n"
            "Round 4 (optional): Percentage composition or unit conversion from today.\n"
            "Each round: one student per row runs to board, solves, returns.\n"
            "Teacher checks answer — correct gets 1 point. Write scores on board.\n"
            "Winning row earns 'Molar Masters' title — teacher announces with fanfare.\n"
            "⚠️ All problems must be dynamic — taken from today's actual chapter sections.\n"
            "⚠️ Board Race Tournament is used ONLY on Day 4 — not repeated."
        ),
        "closing_shout": (
            "Points to Remember Quick Recap: Teacher states formula stem → "
            "Students complete it. Run 4-5 rounds covering all 4 days."
        ),
    },
}


# ============================================================================
# CHEMISTRY LP BUILDER CLASS
# ============================================================================

class ChemistryLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Chemistry LP Builder (910) v1.1 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [Chemistry LP 910 v1.1] Generating: {lesson_title}")
        print(f"      [Chemistry LP 910 v1.1] 9 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

        parts = []

        # Call 0a
        print(f"      [Chemistry LP] Call 0a/9: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        # Call 0b
        print(f"      [Chemistry LP] Call 0b/9: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        # Call 1
        print(f"      [Chemistry LP] Call 1/9: Preamble...")
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
            print(f"      [Chemistry LP] Call {call_num}/9: Day {day_num}...")
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
        print(f"      [Chemistry LP] Call 6/9: Day 5...")
        day5_html = self._call_day5(text, class_num, unit, lesson_title, sections, day_plan)
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # Call 7: Assessment
        print(f"      [Chemistry LP] Call 7/9: Assessment...")
        assessment = self._call_assessment(text, class_num, unit, lesson_title, sections, day_plan)
        if assessment:
            parts.append(clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Chemistry LP 910 v1.1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Chemistry chapter.

YOUR ONLY JOB: Extract EVERY heading and subheading that appears in the chapter text.
Capture ALL levels:
  Level 1: Main headings (e.g. Modern Atomic Theory, Isotopes, Mole Concept)
  Level 2: Subheadings under each main heading
  Level 3: Sub-subheadings if present

ABSOLUTE RULES:
- Copy EVERY heading EXACTLY as written — do NOT paraphrase
- Do NOT skip any heading or subheading — extract ALL of them in order
- Do NOT add anything from general knowledge
- Estimate teaching time per section based on content length
- Capture key terms, formulas, and units per section
- A chapter with 30,000+ characters MUST have at least 8-12 sections
- Every paragraph topic is a section if no clear heading exists
- Mark whether a section contains numerical problems or derivations

Chapter: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "chapter_sections": [
    {{
      "heading": "EXACT Level 1 heading",
      "subheadings": [
        {{
          "title": "EXACT Level 2 subheading",
          "sub_subheadings": ["EXACT Level 3 if present"],
          "has_numerical": false,
          "has_derivation": false
        }}
      ],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "key_formulas": ["formula1"],
      "has_numerical": false,
      "has_diagram": false
    }}
  ],
  "total_estimated_teaching_mins": 70,
  "key_formulas": ["all formulas in chapter"],
  "key_terms": ["all key terms"],
  "numerical_sections": ["sections with problems"]
}}

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system="""You are a strict text extractor. Return ONLY valid JSON.
Extract ALL headings at ALL levels — minimum 8 sections expected for a full chapter.
Never skip any heading or subheading.
Never add general knowledge. No markdown. No code fences. Raw JSON starting with {{""",
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
            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Chemistry lesson plan.

Allocate ALL sections AND subheadings to exactly 4 days.

RULES:
- Each day: 20-25 minutes of content (35 min session minus 10 min opening/closing)
- Keep each main section in ONE day — do NOT split across days
- Keep subheadings WITH their main section
- EVERY section AND subheading must appear in exactly ONE day
- Day 4 must include the FINAL sections — numerical application day
- MAXIMUM 3 subheadings per day — if a section has more, split across 2 days
- Sections with numerical problems should be grouped on Day 4 where possible
- Sections must follow STRICT ORDER from the chapter text — never rearrange
- NEVER assign the same section to two different days
- Use EXACT heading text from extracted sections

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "day1": {{
    "sections": ["EXACT heading 1", "EXACT heading 2"],
    "subheadings": ["EXACT subheading 1", "EXACT subheading 2"],
    "focus": "One sentence — what Day 1 covers",
    "has_numerical": false,
    "estimated_mins": 22
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["EXACT subheading 3", "EXACT subheading 4"],
    "focus": "One sentence — what Day 2 covers",
    "has_numerical": false,
    "estimated_mins": 20
  }},
  "day3": {{
    "sections": ["EXACT heading 4", "EXACT heading 5"],
    "subheadings": ["EXACT subheading 5", "EXACT subheading 6"],
    "focus": "One sentence — what Day 3 covers",
    "has_numerical": false,
    "estimated_mins": 23
  }},
  "day4": {{
    "sections": ["EXACT heading 6", "EXACT heading 7"],
    "subheadings": ["EXACT subheading 7", "EXACT subheading 8"],
    "focus": "One sentence — what Day 4 covers — numerical application",
    "has_numerical": true,
    "estimated_mins": 22
  }}
}}

Extracted Sections:
---
{sections_str}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
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

            key_terms   = ", ".join([t for s in sections_list for t in s.get("key_terms", [])][:12])
            key_formulas = ", ".join(sections.get("key_formulas", [])[:8])

            prompt = f"""Generate ONLY the preamble section of this Chemistry Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Chemistry
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

ALL CHAPTER SECTIONS (extracted from text):
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY TERMS    : {key_terms}
KEY FORMULAS : {key_formulas}

Generate EXACTLY these sections in this order:

<h2>Part 1: Chapter Overview</h2>
Table: Class | Subject | Discipline | Unit/Chapter Title | Month |
       Total Teaching Hours | Session Duration | Main Sections Covered

<h2>Part 2: Learning Objectives</h2>
4-5 SWBAT objectives with action verbs (Explain, Define, Calculate, Classify, Apply)
Based ONLY on actual sections in this chapter — match teacher LP style exactly

<h2>Part 3: Value-Based Objectives</h2>
3-4 value objectives based on actual chapter content:
  e.g. Science as a software update (theories evolve), Global Standards,
  Precision in measurement, Collaborative scientific discovery

<h2>Part 4: Skill Objectives</h2>
4 skill objectives: Formula Application, Diagram Reading,
Classification, Unit Conversion — customised to this chapter

<h2>Part 5: Teaching Aids</h2>
All materials: board, chalk, everyday objects for analogies,
printed formula sheets, textbooks, notebooks, periodic table chart
Based on actual chapter content — no lab equipment needed.

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids

Chapter Text (reference):
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
            print(f"❌ Chemistry LP preamble error: {e}")
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
            has_numerical   = day_data.get("has_numerical", False)

            # Collect key terms and formulas for this day
            all_sections   = sections.get("chapter_sections", [])
            day_key_terms  = []
            day_formulas   = []
            for s in all_sections:
                if s["heading"] in day_sections:
                    day_key_terms.extend(s.get("key_terms", []))
                    day_formulas.extend(s.get("key_formulas", []))

            sections_str    = "\n".join([f"  ▸ {s}" for s in day_sections])
            subheadings_str = "\n".join([f"      • {s}" for s in day_subheadings])
            key_terms_str   = ", ".join(day_key_terms[:10])
            formulas_str    = "\n".join([f"  - {f}" for f in day_formulas[:6]])

            # Next day preview
            if day_num < 4:
                next_data     = day_plan.get(f"day{day_num + 1}", {})
                next_sections = next_data.get("sections", [])
                next_preview  = f"Day {day_num + 1}: {', '.join(next_sections)}"
            else:
                next_preview  = "Day 5: Book-back Exercises + Formula Review"

            numerical_note = ""
            if has_numerical:
                numerical_note = """
NUMERICAL DAY NOTE:
This day contains numerical problems. For each problem type:
  Step 1: Write formula on board
  Step 2: Solve one full worked example — narrate every step
  Step 3: Students solve a parallel problem — 3 minutes
  Step 4: One student writes solution on board — class verifies
Never skip the worked example. Never skip the student parallel problem.
"""

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi Chemistry Lesson Plan.

REFERENCE STYLE: Match the teacher-approved manual LP style exactly.
The manual LP style is:
  - Analogy-driven spark (everyday object or situation)
  - Concept explained with board diagram or formula
  - Call-and-response activities (e.g. 'Dalton Says!')
  - Students classify, calculate, or label — not just listen
  - Final Departure Shout to close the day
  - Script-level detail so any new teacher can follow

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Chemistry
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S SECTIONS — COVER ALL IN ORDER
═══════════════════════════════════════════════════════
Main sections:
{sections_str}

Subheadings (ALL must be taught):
{subheadings_str}

Day Focus   : {day_focus}
Key Terms   : {key_terms_str}
Key Formulas:
{formulas_str if formulas_str else "  (identify from chapter text)"}
{numerical_note}
═══════════════════════════════════════════════════════
CRITICAL RULES — READ BEFORE GENERATING
═══════════════════════════════════════════════════════

1. COVER ALL SECTIONS AND SUBHEADINGS:
   - Every section and subheading listed above MUST be taught
   - Teach them IN ORDER as listed
   - Do NOT skip any subheading
   - Do NOT add sections not in the list

2. EXPLANATION QUALITY (most important):
   - Teacher must NOT just read the textbook — they must EXPLAIN
   - After reading each sub-point aloud: give a detailed explanation
   - Add a real-life analogy for EACH sub-point
     Examples: "Just like how a pizza is cut into 12 equal slices..."
               "Think of it like a bag of mixed coins — some heavy, some light..."
               "Imagine a carton of eggs — a dozen is 12, a mole is 6.023 × 10²³..."
   - Use Indian context examples wherever possible
   - Explanation must be detailed enough that a new teacher can follow it exactly

3. CCQ QUESTIONS (woven into explanation — not separate blocks):
   - After EACH sub-point explanation: ask 1-2 CCQ questions
   - Write CCQ questions on board
   - Students answer by raising hands or calling out
   - For Chemistry: include at least 2 formula/unit CCQs per day
   - Use the exact CCQ HTML format below

4. BOARD WORK:
   - Every main concept must have something drawn/written on board
   - Options: formula, comparison table, concept hub, step-by-step derivation
   - Build it step by step as you explain — not all at once
   - Students copy into their notebooks

5. STUDENT ACTIVITY:
   - Activity EMBEDDED inside main teaching — not a separate block at the end
   - Use the day-specific activity: {strategy['activity'].split(chr(10))[0]}

6. FINAL DEPARTURE SHOUT — MANDATORY EVERY DAY:
   - End EVERY day with a call-and-response shout
   - Teacher gives formula stem or concept trigger
   - Students complete it together aloud
   - Run 3-4 rounds from today's key concepts
   - Format: Teacher: "[stem]...?" → Students: "[ANSWER IN CAPS]!"

{TAMIL_INSTRUCTION}

{CCQ_INSTRUCTION}

7. NO PAGE NUMBERS:
   - Do NOT mention any page numbers anywhere
   - Reference content by section/topic name only

8. NO RELIGIOUS REFERENCES:
   - NEVER use religious examples, gods, faith, or rituals in any analogy
   - Use everyday Indian life: food, sports, family, money, technology

9. NO SPECIFIC STUDENT NAMES:
   - Use "a student" or "Student A" — never real names

═══════════════════════════════════════════════════════
DAY {day_num} TEACHING STRATEGY
═══════════════════════════════════════════════════════
SPARK STYLE     : {strategy['spark_style']}
SPARK INSTRUCTION:
{strategy['spark_instruction']}

TOPIC 1 STRATEGY:
{strategy['topic1_strategy']}

TOPIC 2 STRATEGY:
{strategy['topic2_strategy']}

STUDENT ACTIVITY:
{strategy['activity']}

CLOSING SHOUT:
{strategy['closing_shout']}
═══════════════════════════════════════════════════════

GENERATE Day {day_num} using EXACTLY this HTML structure:

<h3 class="lp-day-title">Day {day_num} — [Exact section names taught today]</h3>

<div class="lp-day-meta">
  <table>
    <tr>
      <th>Learning Objective</th>
      <td>[Specific SWBAT objective for today — action verb + concept]</td>
      <th>Focus</th>
      <td>{day_focus}</td>
    </tr>
  </table>
</div>

<div class="lp-day-block">

  <!-- ═══ [0-5 min] SPARK / HOOK ═══ -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Opening [0–5 min]</span>
    <h4>Spark — {strategy['spark_style']}</h4>

    {"<!-- Day 2+: Start with rapid-fire recap -->" if day_num > 1 else ""}
    {"<p class='lp-teacher-says'><strong>Quick Recap (1 min):</strong> Teacher asks 2-3 rapid questions from yesterday. Students call out answers. No writing needed.</p>" if day_num > 1 else ""}

    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[{strategy['spark_style']} — 3-4 sentences. Everyday Indian object or scenario.
     Connects directly to today's concept: {', '.join(day_sections)}.
     Ends with a Big Question that makes students curious.]"</p>

    <p class="lp-tamil-scaffold"><em>தமிழில்:</em>
    "[Same opening question in Tamil — context-based, natural Tamil]"</p>

    <p><em>Allow 2-3 student guesses. Teacher acknowledges without revealing answer yet.</em></p>

    <p class="lp-teacher-says"><strong>Teacher then says (Real-life Connection):</strong><br/>
    "[Why are we learning this? Connect today's concept to ONE specific real-world application.
     Examples: pharmacists use atomic mass to calculate medicine doses;
     engineers use molecular mass to design industrial processes;
     NASA uses isotope ratios to detect water on other planets.
     Use the application most relevant to today's actual sections.
     Keep it to 2-3 sentences — make students feel the importance.]"</p>
  </div>

  <!-- ═══ [5-10 min] INTRODUCTION ═══ -->
  <div class="lp-section-intro">
    <span class="lp-section-label">Introduction [5–10 min]</span>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Topic: [today's concept names]<br/>
      Objective: [today's SWBAT in one line]<br/>
      {"Key Formula: [formula if applicable]" if formulas_str else "Key Idea: [core concept in one sentence]"}
    </div>

    <p class="lp-teacher-says"><strong>Teacher says (Introduction — English):</strong><br/>
    "[Teacher introduces today's concept in simple words — 3-4 sentences.
     One real-life analogy connecting to the concept.
     Example: 'Just like how [everyday Indian thing], this means [concept]...'
     Connect back to the Big Question from the spark.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — same introduction. Same length. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word. Pure Tamil Unicode only.]"</p>
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead><tr><th>Term</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
        <tbody>
          [5-6 key terms from today's sections with clear meanings and Tamil equivalents.
           For terms with no Tamil equivalent: write in Tamil script transliteration.]
        </tbody>
      </table>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Short question about the introduction concept — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Short factual answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>
  </div>

  <!-- ═══ [10-20 min] MAIN TEACHING — TOPIC 1 ═══ -->
  <div class="lp-section-main">
    <span class="lp-section-label">Main Teaching — Topic 1 [10–20 min]</span>
    <h4>[EXACT name of first section from today's list]</h4>

    <p class="teacher-role"><em>Teacher Role: {strategy['topic1_strategy'].split(chr(10))[0]}</em></p>

    [FOR EACH subheading under this section — in exact order from chapter:]

    <h5>[EXACT subheading name]</h5>

    <p class="lp-teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
    "[Teacher reads this sub-point from textbook.
     Then explains in simple clear language — 3-4 sentences.
     ANALOGY: 'Just like [specific everyday Indian/relatable example],
     this means that [explanation connecting analogy to concept]...'
     Include specific terms, formulas, units from the textbook.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[EXACT same explanation in Tamil — sentence by sentence mirror.
          Same length. Same detail. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word.
          Pure Tamil Unicode — no Hindi words, no English transliteration
          except for scientific terms with no Tamil equivalent.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw / Write on Board (step by step while explaining):</strong><br/>
      [Formula or diagram: build step by step as you explain]<br/>
      [e.g. Comparison table: Old Theory | New Theory — fill one row at a time]
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Short factual question about this sub-point — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[One word or one sentence]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Formula or unit question — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Formula or unit answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    [REPEAT the subheading block for each subheading under section 1]

    <!-- Embedded Activity for Topic 1 -->
    <div class="activity-block">
      <strong>⚙️ Activity ({strategy['activity'].split(chr(10))[0]}):</strong>
      <p>[Step by step activity instructions.
         Based ONLY on today's section content.
         Students are active — classifying, calculating, calling out, racing to board.]</p>
    </div>

  </div>

  <!-- ═══ [20-30 min] MAIN TEACHING — TOPIC 2 ═══ -->
  <div class="lp-section-main">
    <span class="lp-section-label">Main Teaching — Topic 2 [20–30 min]</span>
    <h4>[EXACT name of second section from today's list]</h4>

    <p class="teacher-role"><em>Teacher Role: {strategy['topic2_strategy'].split(chr(10))[0]}</em></p>

    [FOR EACH subheading under this section — in exact order:]

    <h5>[EXACT subheading name]</h5>

    <p class="lp-teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
    "[Teacher reads sub-point from textbook.
     Explains in simple language — 3-4 sentences.
     ANALOGY: [specific analogy for this sub-point].
     Specific facts, formulas, units from text.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[EXACT same explanation in Tamil — sentence by sentence mirror.
          Same length. Same detail. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word.
          Pure Tamil Unicode only.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      [Key formula / worked example / classification table to write on board]
    </div>

    {f"""
    [IF this subheading contains a numerical problem or formula application:]
    <div class="worked-example">
      <strong>Worked Example (Teacher models on board):</strong>
      <p><strong>Given:</strong> [list given quantities with units from textbook]</p>
      <p><strong>Formula:</strong> [write the exact formula]</p>
      <p><strong>Substitution:</strong> [plug in the numbers with units — show every step]</p>
      <p><strong>Answer:</strong> [result with correct unit]</p>
    </div>
    <p><em>Students then solve a parallel problem in pairs — 3 minutes.
    One pair writes solution on board. Class verifies step by step.</em></p>
    """ if has_numerical else ""}

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Question about this sub-point — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Short answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    [REPEAT for each subheading under section 2]

  </div>

  <!-- ═══ [25-30 min] STUDENT TASK — MANDATORY — NEVER SKIP ═══ -->
  <div class="lp-section-student-task">
    <span class="lp-section-label">Student Task [25–30 min]</span>
    <h4>Homework Task</h4>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "Write both tasks in your homework book. Submit tomorrow morning.
     Use your own words — do not copy from textbook."</p>
    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Task 1: [Specific written task — define/explain/list from today's concept]<br/>
      Task 2: [Concept task — draw a diagram OR write formula with explanation
               OR solve one practice problem from today's content]<br/>
      Submit: Tomorrow morning
    </div>
  </div>

  <!-- ═══ [30-35 min] CLOSING — MANDATORY — NEVER SKIP ═══ -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>

    <div class="board-work">
      <strong>Key Points on Board{"" if day_num < 4 else " (Full Chapter Summary)"}:</strong><br/>
      1. [Key concept 1 from today]<br/>
      2. [Key concept 2 from today]<br/>
      3. [Key formula or term from today]<br/>
      {"4. [Key point 4]<br/>5. [Key point 5]" if day_num == 4 else ""}
    </div>

    <div class="departure-shout">
      <strong>🔊 Final Departure Shout:</strong>
      <p><em>Teacher gives the stem — students complete it ALOUD together.</em></p>
      <p class="lp-teacher-says">Teacher: "[Key concept stem from today]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p class="lp-teacher-says">Teacher: "[Second stem from today]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p class="lp-teacher-says">Teacher: "[Third stem — formula or definition]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p><em>Run 3-4 rounds. Keep energy high. Students love this.</em></p>
    </div>

    <p class="lp-teacher-says"><strong>Closing Statement:</strong><br/>
    "[2 sentences — what was covered today. Connect to bigger picture of chemistry.
     {"Preview what comes next: " + next_preview if day_num < 4 else "Congratulate students on completing all 4 teaching days."}]"</p>

  </div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ ALL sections covered: {', '.join(day_sections)}
✅ ALL subheadings covered: {', '.join(day_subheadings)}
✅ EVERY subheading has full explanation — nothing summarised or skipped
✅ Every sub-point has: read aloud → explanation → analogy → CCQ
✅ Board work present for every main concept
✅ CCQ questions woven in after every sub-point — minimum 10 total
✅ Activity embedded inside main teaching — not a separate end block
✅ Final Departure Shout PRESENT with AT LEAST 3 call-and-response rounds — NEVER skip
✅ Student Task block PRESENT and COMPLETE — never skip
✅ Closing block PRESENT and COMPLETE — never skip
✅ Tamil mirror present after EVERY subheading explanation — Topic 1 AND Topic 2
✅ Tamil also in: Opening Question + Introduction + Key Terms table
✅ NO Tamil in: activity instructions, board work, closing, homework, student task
✅ No page numbers anywhere
✅ No religious references in any analogy
✅ No specific student names — use "a student" or "Student A"
✅ All English spelled correctly
✅ Raw HTML only — start with <h3 class="lp-day-title">Day {day_num}
✅ Do NOT generate Day {day_num + 1}

Chapter Text (use ONLY this — no general knowledge):
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
            print(f"❌ Chemistry LP Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — DAY 5: BOOK-BACK + FORMULA REVIEW
    # =========================================================================

    def _call_day5(self, text, class_num, unit, lesson_title,
                   sections: dict, day_plan: dict):
        try:
            key_formulas  = ", ".join(sections.get("key_formulas", []))
            key_terms     = ", ".join([t for s in sections.get("chapter_sections", [])
                                       for t in s.get("key_terms", [])][:15])

            all_section_names = [s["heading"] for s in sections.get("chapter_sections", [])]
            day_summaries = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summaries += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"
                subs = d_data.get("subheadings", [])
                if subs:
                    day_summaries += f"    Subs: {', '.join(subs[:3])}\n"

            prompt = f"""Generate ONLY Day 5 of the Chemistry Lesson Plan.
Day 5 = Book-back Marking → Formula Review → Closing.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Day      : 5 of 5 — Review and Book-back Day
Duration : 35 minutes

ALL CHAPTER SECTIONS:
{chr(10).join([f"  - {s}" for s in all_section_names])}

DAY-WISE SUMMARY:
{day_summaries}

KEY FORMULAS : {key_formulas}
KEY TERMS    : {key_terms}

<h3 class="lp-day-title">Day 5 — Book-back Exercises and Formula Review</h3>

<div class="lp-day-meta">
  <table>
    <tr>
      <th>Learning Objectives</th>
      <td>Evaluate understanding through book-back exercises.
      Consolidate all formulas and key terms from the chapter.</td>
    </tr>
  </table>
</div>

<div class="lp-day-block">

  <!-- [0-5 min] SPARK — RAPID-FIRE RECAP -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Opening [0–5 min]</span>
    <h4>Spark — Final Departure Shout (Recap Mode)</h4>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[Run 5-6 call-and-response rounds covering all 4 days of content.
     Teacher gives formula stem or concept trigger → Students shout answer.
     Example: 'One mole of any gas at STP occupies...?' → Students: 'TWENTY-TWO POINT FOUR LITERS!'
     Use actual formulas and terms from this chapter only.]"</p>
    <p><em>This activates all prior knowledge before book-back marking.</em></p>
  </div>

  <!-- [5-20 min] BOOK-BACK MARKING -->
  <div class="lp-section-main">
    <span class="lp-section-label">Book-back Marking [5–20 min]</span>
    <h4>Book-Back Exercise Marking and Discussion</h4>
    <p class="teacher-role"><em>Teacher facilitates step-by-step marking.
    Students swap notebooks or self-mark while teacher explains
    the logic behind each answer — especially for numerical problems.</em></p>
    <p><em>⚠️ Note to Teacher: All book-back questions with model answers
    are available in the QA section of this platform.
    Open the QA section for this chapter to get complete answers.</em></p>

    <h5>Section 1: Choose the Correct Answer / Fill in the Blanks</h5>
    <p>[For each answer: identify the key term/formula/concept being tested.
     Explain WHY the correct answer is right — reference the chapter section.
     Briefly discuss common wrong answers — especially for formula-based MCQs.]</p>

    <h5>Section 2: Match the Following / Short Answers</h5>
    <p>[For each answer: explain the connection to the chapter concept.
     For numerical short answers: show the formula and working on board.
     Students compare with their own answers and correct errors.]</p>

    <h5>Section 3: Numerical / Problem-Based Questions</h5>
    <p>[For 2-3 key numerical answers: give model solution on board step by step.
     Write: Given → Formula → Substitution → Answer with units.
     Students check their working — not just final answer.]</p>

    <div class="board-work">
      <strong>Key Answers on Board:</strong><br/>
      [Write main answers and formula steps for student verification]
    </div>
  </div>

  <!-- [20-30 min] FORMULA REVIEW -->
  <div class="lp-section-main">
    <span class="lp-section-label">Formula Review [20–30 min]</span>
    <h4>Master Formula Sheet Review</h4>
    <p class="teacher-role"><em>Teacher writes all chapter formulas on board.
    Students copy into formula log at back of notebook.
    Teacher explains one real use case per formula.</em></p>

    <div class="board-work">
      <strong>Chapter Formula Sheet — Write All on Board:</strong><br/>
      {key_formulas if key_formulas else "[All formulas from chapter — write each with units]"}<br/>
      <br/>
      <strong>Memory Tips:</strong><br/>
      [3-4 memory tricks — mnemonics or verbal patterns for key formulas]<br/>
      [Example: 'Moles = Mass divided by Molar Mass — M over M!']
    </div>

    <h5>Formula Verification Activity</h5>
    <p>[Students close notebooks. Teacher calls one student at a time to write
     one formula on board from memory. Class checks. 5-6 students participate.
     Teacher reinforces any formula written incorrectly.]</p>
  </div>

  <!-- CLOSING -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[Congratulate students on completing the chapter.
     Name 2-3 specific things learned across all 5 days.
     Connect the chapter to real-world chemistry applications.
     Motivate for next chapter.]"</p>

    <div class="board-work">
      <strong>All Students Must Submit:</strong><br/>
      ☐ Notebook — all 5 days of notes completed<br/>
      ☐ Book-back exercises — answered and marked<br/>
      ☐ Formula log page — all chapter formulas written neatly<br/>
      ☐ All homework tasks from Days 1-4<br/>
      ☐ Student task from Day 4 (if numerical — working must be shown)
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="lp-day-title">Day 5
- Book-back section must have real content from chapter
- Formula review based on actual chapter formulas
- No page numbers needed — reference section names only
- Do NOT generate any other day

Chapter Text:
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system=SCIENCE_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Chemistry LP Day 5 error: {e}")
            return None

    # =========================================================================
    # CALL 7 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, sections: dict, day_plan: dict):
        try:
            all_sections  = sections.get("chapter_sections", [])
            sections_str  = ", ".join([s["heading"] for s in all_sections])
            key_terms     = ", ".join([t for s in all_sections for t in s.get("key_terms", [])][:12])
            key_formulas  = ", ".join(sections.get("key_formulas", [])[:8])

            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Chemistry chapter.
Do NOT repeat day content. Do NOT generate day blocks.

Chapter      : {lesson_title}
Class        : {class_num}
Unit         : {unit}
All Sections : {sections_str}
Key Terms    : {key_terms}
Key Formulas : {key_formulas}

Day-wise:
{day_summary}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Written Assessment — Section A (Recall)</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Concepts Covered</th>
        <th>Recall Question</th>
        <th>Expected Answer</th>
      </tr>
    </thead>
    <tbody>
      [5 rows — Day 1 to Day 5.
       One factual recall question per day from actual chapter content.
       Expected answer: 1 sentence max.]
    </tbody>
  </table>

  <h3>Written Assessment — Section B (Application + Analysis)</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>CCQ / Application Question</th>
        <th>Expected Answer</th>
        <th>Tamil Prompt</th>
      </tr>
    </thead>
    <tbody>
      [5 rows — Day 1 to Day 5.
       One Why/How/Calculate question per day from actual chapter content.
       Tamil version in last column — context-based natural Tamil.]
    </tbody>
  </table>

  <h3>Differentiated Written Worksheet — 3 Levels</h3>
  <table class="diff-table" style="border: 2px solid #333;">
    <thead>
      <tr>
        <th>Foundation Level (Slow Learners)<br/>10 Marks</th>
        <th>Standard Level (Average Learners)<br/>10 Marks</th>
        <th>Advanced Level (Toppers)<br/>10 Marks</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Q1 (2M):</strong> Fill blanks — 4 sentences with word bank</p>
          <p><strong>Word Bank:</strong> [6 key terms from chapter]</p>
          <p><strong>Q2 (3M):</strong> Define 3 key terms from chapter</p>
          <p><strong>Q3 (5M):</strong> Complete a given formula and explain in 2 sentences</p>
        </td>
        <td>
          <p><strong>Q1 (3M):</strong> Answer 3 short questions — 2 sentences each</p>
          <p><strong>Q2 (3M):</strong> Draw and label a concept diagram from chapter</p>
          <p><strong>Q3 (4M):</strong> Solve 2 numerical problems using given formulas</p>
        </td>
        <td>
          <p><strong>Q1 (4M):</strong> Explain a key concept with formula, example, and unit</p>
          <p><strong>Q2 (3M):</strong> Solve 2 advanced numerical problems — show full working</p>
          <p><strong>Q3 (3M):</strong> Compare two related concepts from chapter in a table</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Formula Checklist — All Chapter Formulas</h3>
  <ul>
    [Each formula from the chapter as a checklist item in this format:
     ☐ [Formula name]: [Formula] — Unit: [unit if applicable] — Use: [1-sentence real-world use case]
     Example: ☐ Molar Volume: 1 mole of gas = 22.4 L at STP — Unit: Litres — Use: Used to calculate volume of gas produced in industrial reactions]
  </ul>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in notebook</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Key terms table filled for all 5 days</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Formula log page completed — all formulas with units</li>
    <li>☐ Can state Avogadro's Law in words and as equation (V ∝ n)</li>
    <li>☐ Can calculate Vapour Density from Molecular Mass (RMM = 2 × VD)</li>
    <li>☐ [One more chapter-specific checklist item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Section A table: exactly 5 rows
- Section B table: exactly 5 rows with Tamil column
- Differentiated worksheet: 3 columns with visible 2px border
- Formula checklist: every formula from chapter
- No page numbers
- Base all content on actual extracted sections

Chapter Text:
---
{text[:3000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system=SCIENCE_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Chemistry LP assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

chemistry_lp_910_builder = ChemistryLP910Builder()