"""
physics.py
----------
LP Builder for Samacheer Kalvi Science — Physics
Class 8, 9 & 10

v1.0 — May 2026
v1.1 — May 2026 (validation team fixes)
  Fix 1: Formula extraction rule — never use hardcoded formulas
  Fix 2: Comparison table conditional — only when two comparable concepts exist
  Fix 3: Vector/scalar CCQs conditional — only if chapter mentions them
  Fix 4: Worksheet problems extracted from chapter text — not generic physics
  Fix 5: Numerical conditional — skip if no values in chapter text, never invent
Built to match teacher-approved manual LP reference
(Physics: Laws of Motion — Unit 1, Class 10)
Modeled on ss/lp/grade_910/history.py structure.

REFERENCE: Manual LP "Laws of Motion" — Grade 10 Physics
           Built by TNQ/Tutorea.ai teacher team — used as gold standard

KEY DIFFERENCES FROM CHEMISTRY AND BIOLOGY LP:
  - Spark: Prop + student physical body activity (coin flick, squat drop, clap test)
  - Activities: Human physical demos + calculation sprints every day
  - Numericals: Every day has worked examples + student calculation (not just Day 4)
  - Closing: Formula-focused Departure Shout (formula stem → answer)
  - Differentiated 3-level worksheets embedded in EVERY day
  - No synthesis sentence — replaced by rapid formula recap

STRUCTURE PER DAY (matches manual LP exactly):
  [0-5 min]   Spark / Prop + Physical Activity
              → Teacher brings prop OR leads a physical body activity
              → "Clap Test", "Door Challenge", "Squat Drop" style
              → Big Question connecting activity to today's physics concept
              → Real-life use stated clearly

  [5-10 min]  Introduction
              → Branch map or concept chain on board
              → Aristotle vs Galileo / historical context if applicable
              → Key terms + formula on board
              → CFU/CCQ from introduction

  [10-25 min] Main Teaching — Topics
              → Read aloud from textbook + explain
              → Formula derivation on board — step by step
              → Student physical activity embedded (Human Magnet, Tug-of-War etc.)
              → Worked numerical example (Given → Formula → Substitution → Answer)
              → CFU/CCQ after each sub-point

  [25-30 min] Differentiated Worksheet (3 levels — every day)
              → Level 1: Definition + simple matching + basic numerical
              → Level 2: Application + moderate numerical
              → Level 3: Derivation + advanced analysis

  [30-35 min] Closing
              → Rapid formula recap (call-and-response)
              → Homework: home experiment + numerical practice

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
)


# ============================================================================
# PHYSICS TEACHING STRATEGY PER DAY
# Prop + physical activity sparks, formula derivation, numericals every day,
# 3-level differentiated worksheets, formula departure shout
# ============================================================================

PHYSICS_DAY_STRATEGY = {
    1: {
        "spark_style": "Prop Demo + Physical Body Activity",
        "spark_instruction": (
            "Teacher brings a simple everyday prop AND leads a physical student activity.\n"
            "Examples from teacher LP:\n"
            "  - Glass + card + coin: flick card → coin drops into glass (Inertia)\n"
            "  - Students lean back when bus accelerates (simulate)\n"
            "  - Students lean forward when bus brakes (simulate)\n"
            "Structure:\n"
            "  Step 1: Show prop or describe demo dramatically.\n"
            "  Step 2: Ask prediction — 'What do you think will happen?'\n"
            "  Step 3: Do the demo / lead the physical activity.\n"
            "  Step 4: Reveal: 'This stubbornness/behaviour is called [concept].'\n"
            "  Step 5: Big Question + Real-life use (engineering, safety, sports).\n"
            "Allow 2-3 student predictions before revealing."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Branch Map Builder + Historical Context Explainer\n"
            "Step 1: Write a concept map or branch map on board:\n"
            "        CENTER: [Main concept] → Branch 1: [Sub-concept A] → Branch 2: [Sub-concept B]\n"
            "Step 2: Explain historical context if applicable\n"
            "        (e.g. Aristotle vs Galileo — old vs new understanding).\n"
            "Step 3: Read section aloud from textbook — explain sub-point by sub-point.\n"
            "Step 4: Add real-life Indian example for each sub-point.\n"
            "Step 5: 1-2 CFU/CCQ after each sub-point.\n"
            "Step 6: Write key definition + formula on board."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Deep Dive Explainer + Physical Demo Facilitator\n"
            "Step 1: Introduce the sub-concept with a physical student activity.\n"
            "        Examples: students lean left/right, push desk, press hand on table.\n"
            "Step 2: Explain each type/case from textbook — read aloud + explain.\n"
            "Step 3: Write worked example on board:\n"
            "        Given → Formula → Substitution → Answer with units.\n"
            "Step 4: Students solve a parallel numerical in notebook — 2 minutes.\n"
            "Step 5: 2 CFU/CCQ after each case."
        ),
        "activity": (
            "PHYSICAL BODY ACTIVITY — CONCEPT SIMULATION (Day 1):\n"
            "Teacher leads students in a physical simulation of today's concept.\n"
            "Examples from teacher LP:\n"
            "  - 'Lean back!' when bus accelerates → Inertia of Rest\n"
            "  - 'Lean forward!' when bus brakes → Inertia of Motion\n"
            "  - 'Lean sideways!' when bus turns → Inertia of Direction\n"
            "Design the simulation to match TODAY'S actual chapter content.\n"
            "Run 2-3 rounds — one for each sub-type or case.\n"
            "After simulation: students write the concept name + 1-sentence definition.\n"
            "⚠️ Physical Body Simulation is used ONLY on Day 1 — not repeated."
        ),
        "worksheet_levels": (
            "DIFFERENTIATED WORKSHEET — 3 LEVELS (Day 1):\n"
            "Level 1 (Foundation): Define key term + match concept to example + one basic numerical\n"
            "Level 2 (Standard): Explain a real-life application + moderate numerical + short analysis\n"
            "Level 3 (Advanced): Distinguish between two concepts + advanced numerical + evaluate statement\n"
            "All three levels based on TODAY'S chapter content only.\n"
            "Time: 5 minutes. Students identify their level from a symbol/color on paper."
        ),
        "closing_shout": (
            "Formula Departure Shout:\n"
            "Teacher gives formula stem → Students complete it aloud.\n"
            "Example: 'The stubbornness of a body is called...?' → Students: 'INERTIA!'\n"
            "         'The branch for bodies at rest is...?' → Students: 'STATICS!'\n"
            "Run 3 rounds from today's key definitions and formulas."
        ),
    },
    2: {
        "spark_style": "Prop Demo + Calculation Connection",
        "spark_instruction": (
            "Teacher brings a prop that connects to today's formula/concept.\n"
            "Examples from teacher LP:\n"
            "  - Light pencil vs heavy stack of books — blow on each (Momentum)\n"
            "  - Flick eraser gently vs with force — observe speed difference\n"
            "  - 'The combination of mass and speed creates impact'\n"
            "Structure:\n"
            "  Step 1: Show both objects — light vs heavy / slow vs fast.\n"
            "  Step 2: 'Which has more impact? Why?'\n"
            "  Step 3: Allow 2-3 student answers.\n"
            "  Step 4: 1-minute recap of yesterday's key formula.\n"
            "  Step 5: Reveal today's concept + formula connection.\n"
            "  Step 6: Real-life use (engineering, sports, vehicles)."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Formula Derivation Guide + Calculation Sprint Facilitator\n"
            "Step 1: Write today's formula on board — derive it step by step.\n"
            "        Show WHERE the formula comes from — not just the final form.\n"
            "Step 2: Read section aloud — explain sub-point by sub-point.\n"
            "Step 3: CALCULATION SPRINT — give one numerical on board:\n"
            "        Students solve in notebook — 2 minutes.\n"
            "        One student writes solution on board — class verifies.\n"
            "Step 4: 2 CFU/CCQ after the calculation."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Human Demo Facilitator + Comparison Table Builder\n"
            "Step 1: Lead a human physical activity connecting to today's concept.\n"
            "        Examples: Human Tug-of-War (resultant force),\n"
            "                  Door challenge (torque), Ruler seesaw (moments).\n"
            "Step 2: Build a comparison table on board if applicable.\n"
            "Step 3: Explain from textbook — read aloud + explain with analogy.\n"
            "Step 4: Worked numerical example (Given → Formula → Substitution → Answer).\n"
            "Step 5: 2 CFU/CCQ."
        ),
        "activity": (
            "HUMAN PHYSICAL DEMO — FORCE CONCEPTS (Day 2):\n"
            "Teacher leads a human physical demonstration of today's force concept.\n"
            "Examples from teacher LP:\n"
            "  - Two students push desk together → Like Parallel Forces\n"
            "  - Students push from opposite sides → Unlike Parallel / Resultant Force\n"
            "  - Door challenge: push near handle vs near hinge → Torque\n"
            "  - Balance ruler on finger with erasers → Principle of Moments\n"
            "Design the demo to match TODAY'S actual chapter content.\n"
            "After demo: students explain the concept they just demonstrated in 1 sentence.\n"
            "⚠️ Human Physical Demo is used ONLY on Day 2 — not repeated."
        ),
        "worksheet_levels": (
            "DIFFERENTIATED WORKSHEET — 3 LEVELS (Day 2):\n"
            "Level 1 (Foundation): Formula recall + give 2 real-life examples + basic calculation\n"
            "Level 2 (Standard): Application problem + moderate numerical + explain using concept\n"
            "Level 3 (Advanced): Derivation or proof + advanced numerical + evaluate statement\n"
            "All three levels based on TODAY'S chapter content only.\n"
            "Time: 5 minutes."
        ),
        "closing_shout": (
            "Formula Departure Shout:\n"
            "Teacher gives formula stem → Students complete it aloud.\n"
            "Example: 'Mass × Velocity is...?' → Students: 'MOMENTUM!'\n"
            "         'The turning effect of a force is...?' → Students: 'TORQUE!'\n"
            "Run 3 rounds from today's key formulas."
        ),
    },
    3: {
        "spark_style": "Scenario Dilemma + Physical Sensation Activity",
        "spark_instruction": (
            "Teacher presents a dramatic scenario dilemma connecting to today's concept.\n"
            "Examples from teacher LP:\n"
            "  - Egg drop dilemma: concrete vs foam cushion — why different outcomes?\n"
            "  - Clap test: sudden clap vs slow sliding hands — which stings more?\n"
            "  - Fielder pulling hands back when catching cricket ball\n"
            "Structure:\n"
            "  Step 1: Present the dilemma dramatically — 'If I drop a raw egg...'\n"
            "  Step 2: Lead a physical sensation activity students can feel.\n"
            "  Step 3: 'What changed? Why?' — allow guesses.\n"
            "  Step 4: Connect to today's formula/concept.\n"
            "  Step 5: 1-minute recap of yesterday's key formula.\n"
            "  Step 6: Real-life use (safety engineering, sports, vehicles)."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Law Derivation Guide + Formula Prover\n"
            "Step 1: State the law from textbook — read aloud.\n"
            "Step 2: Write the mathematical derivation on board — step by step.\n"
            "        Show how each formula step follows from the previous.\n"
            "Step 3: Explain units, dimensions, vector nature if applicable.\n"
            "Step 4: Worked numerical (Given → Formula → Substitution → Answer).\n"
            "Step 5: Students solve parallel numerical — 2 minutes.\n"
            "Step 6: 2 CFU/CCQ after derivation."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Real-World Application Connector\n"
            "Step 1: Introduce sub-concept with a physical mimic activity.\n"
            "        Example: Fielder pulling hands back (impulse),\n"
            "                 Balloon rocket demo (conservation of momentum),\n"
            "                 Rolling marble collision (momentum transfer).\n"
            "Step 2: Explain from textbook — read aloud + explain.\n"
            "Step 3: Write the key formula and its derivation on board.\n"
            "Step 4: Worked numerical example.\n"
            "Step 5: 2 CFU/CCQ."
        ),
        "activity": (
            "PHYSICAL MIMIC + OBSERVATION ACTIVITY (Day 3):\n"
            "Teacher leads a physical mimic of today's concept.\n"
            "Examples from teacher LP:\n"
            "  - Fielder's Mimic: catch ball and pull hands back → Impulse (time matters)\n"
            "  - Desk Push: press hand on desk → feel reaction force → Newton's 3rd Law\n"
            "  - Balloon Rocket: imagine letting go of untied balloon → Propulsion\n"
            "  - Rolling Marble Line: predict how many marbles pop out → Momentum conservation\n"
            "Design the activity to match TODAY'S actual chapter content.\n"
            "After activity: students write the law/principle in their own words.\n"
            "⚠️ Physical Mimic Activity is used ONLY on Day 3 — not repeated."
        ),
        "worksheet_levels": (
            "DIFFERENTIATED WORKSHEET — 3 LEVELS (Day 3):\n"
            "Level 1 (Foundation): State the law + basic calculation + identify action-reaction pair\n"
            "Level 2 (Standard): Explain real-life application + moderate numerical + short analysis\n"
            "Level 3 (Advanced): Mathematical proof/derivation + advanced numerical + evaluate scenario\n"
            "All three levels based on TODAY'S chapter content only.\n"
            "Time: 3 minutes."
        ),
        "closing_shout": (
            "Formula Departure Shout:\n"
            "Teacher gives law/formula stem → Students complete it aloud.\n"
            "Example: 'The formula connecting force, mass, acceleration is...?' → Students: 'F = ma!'\n"
            "         'A huge force in a tiny time is...?' → Students: 'IMPULSE!'\n"
            "Run 3 rounds from today's laws and formulas."
        ),
    },
    4: {
        "spark_style": "Imagination Scenario + Virtual Physical Activity",
        "spark_instruction": (
            "Teacher presents a vivid imagination scenario students can physically simulate.\n"
            "Examples from teacher LP:\n"
            "  - Roller coaster stomach drop: 'hands up if you've been on a giant wheel'\n"
            "  - Virtual Drop: students squat as fast as possible → feel weightlessness\n"
            "  - Moon Jump imagination: how high can you jump on the Moon?\n"
            "Structure:\n"
            "  Step 1: Ask about a real experience — 'hands up if...'\n"
            "  Step 2: Lead the virtual physical activity — 'Stand up, on 3, DROP!'\n"
            "  Step 3: 'That feeling is the beginning of [concept].'\n"
            "  Step 4: 1-minute rapid recap of Days 1-3 key formulas.\n"
            "  Step 5: Real-life use (space science, engineering, astronomy)."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Law Explainer + Comparison Table Builder\n"
            "Step 1: Write the universal law formula on board — explain each term.\n"
            "Step 2: Build a comparison table where applicable:\n"
            "        Format: Concept A | Concept B (e.g. Mass | Weight)\n"
            "Step 3: Read section aloud — explain sub-point by sub-point.\n"
            "Step 4: Use distance stretch / imagination activity for difficult concepts.\n"
            "Step 5: Worked numerical (Given → Formula → Substitution → Answer).\n"
            "Step 6: 2 CFU/CCQ."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: The 4-Case Rule Explainer\n"
            "Step 1: Write all cases/scenarios on board FIRST — students see structure.\n"
            "        Example: Lift going up (accelerating) / Lift going down (accelerating)\n"
            "                 / Uniform velocity / Free fall\n"
            "Step 2: Explain each case one by one — formula derivation for each.\n"
            "Step 3: Physical mimic for each case — students show the sensation.\n"
            "Step 4: Worked numerical for 1-2 cases.\n"
            "Step 5: 2 CFU/CCQ per case."
        ),
        "activity": (
            "IMAGINATION + VIRTUAL PHYSICAL ACTIVITY (Day 4):\n"
            "Teacher leads an imagination-based physical simulation.\n"
            "Examples from teacher LP:\n"
            "  - Virtual Drop squat → feel weightlessness sensation\n"
            "  - Moon Jump: 'jump as high as you can — on Moon you'd go 6x higher!'\n"
            "  - Distance Stretch: hold fists close then pull apart → gravitational force drops\n"
            "  - Root Pointer: point fingers down like plant roots → Geotropism\n"
            "Design the activity to match TODAY'S actual chapter content.\n"
            "After activity: students write 1 application of today's concept in real life.\n"
            "⚠️ Imagination Activity is used ONLY on Day 4 — not repeated."
        ),
        "worksheet_levels": (
            "DIFFERENTIATED WORKSHEET — 3 LEVELS (Day 4):\n"
            "Level 1 (Foundation): Basic definition + formula recall + simple calculation\n"
            "Level 2 (Standard): Differentiate two concepts + moderate numerical + explain phenomenon\n"
            "Level 3 (Advanced): Mathematical proof of special case + advanced numerical + analyse scenario\n"
            "All three levels based on TODAY'S chapter content only.\n"
            "Time: 3 minutes."
        ),
        "closing_shout": (
            "Formula Departure Shout — covering ALL 4 days:\n"
            "Teacher gives formula stem from any day → Students complete aloud.\n"
            "Example: 'The constant that never changes anywhere in space is...?' → Students: 'MASS!'\n"
            "         'Free fall happens when acceleration equals...?' → Students: 'g!'\n"
            "Run 4 rounds — one from each day's key concept."
        ),
    },
}


# ============================================================================
# PHYSICS LP BUILDER CLASS
# ============================================================================

class PhysicsLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Physics LP Builder (910) v1.1 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [Physics LP 910 v1.0] Generating: {lesson_title}")
        print(f"      [Physics LP 910 v1.0] 9 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

        parts = []

        # Call 0a
        print(f"      [Physics LP] Call 0a/9: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        # Call 0b
        print(f"      [Physics LP] Call 0b/9: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        # Call 1
        print(f"      [Physics LP] Call 1/9: Preamble...")
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
            print(f"      [Physics LP] Call {call_num}/9: Day {day_num}...")
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
        print(f"      [Physics LP] Call 6/9: Day 5...")
        day5_html = self._call_day5(text, class_num, unit, lesson_title, sections, day_plan)
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # Call 7: Assessment
        print(f"      [Physics LP] Call 7/9: Assessment...")
        assessment = self._call_assessment(text, class_num, unit, lesson_title, sections, day_plan)
        if assessment:
            parts.append(clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Physics LP 910 v1.0] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Physics chapter.

YOUR ONLY JOB: Extract EVERY heading and subheading in the chapter text.
Capture ALL levels:
  Level 1: Main headings (e.g. Force and Motion, Newton's Laws, Gravitation)
  Level 2: Subheadings under each main heading
  Level 3: Sub-subheadings if present

ABSOLUTE RULES:
- Copy EVERY heading EXACTLY as written — do NOT paraphrase
- Do NOT skip any heading or subheading — extract ALL of them in order
- Do NOT add anything from general knowledge
- Estimate teaching time per section based on content length
- Capture key terms, formulas, and laws per section
- A chapter with 30,000+ characters MUST have at least 8-15 sections
- Mark whether a section contains numerical problems, derivations, or laws

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
          "has_derivation": false,
          "has_law": false
        }}
      ],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "key_formulas": ["formula1"],
      "key_laws": ["law1"],
      "has_numerical": false,
      "has_derivation": false
    }}
  ],
  "total_estimated_teaching_mins": 70,
  "key_formulas": ["all formulas in chapter"],
  "key_laws": ["all laws in chapter"],
  "key_terms": ["all key terms"],
  "numerical_sections": ["sections with problems"],
  "derivation_sections": ["sections with derivations"]
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
            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Physics lesson plan.

Allocate ALL sections AND subheadings to exactly 4 days.

RULES:
- Each day: 20-25 minutes of content (35 min session minus 10 min opening/closing)
- Keep each main section in ONE day — do NOT split across days
- Keep subheadings WITH their main section
- EVERY section AND subheading must appear in exactly ONE day
- MAXIMUM 3 subheadings per day — if more, split across 2 days
- Sections with numerical problems should be distributed across all 4 days
- Sections with derivations should be given adequate time — max 1 major derivation per day
- Laws must be on the SAME day as their application
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
    "has_derivation": false,
    "estimated_mins": 22
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["EXACT subheading 3", "EXACT subheading 4"],
    "focus": "One sentence — what Day 2 covers",
    "has_numerical": true,
    "has_derivation": false,
    "estimated_mins": 20
  }},
  "day3": {{
    "sections": ["EXACT heading 4", "EXACT heading 5"],
    "subheadings": ["EXACT subheading 5", "EXACT subheading 6"],
    "focus": "One sentence — what Day 3 covers",
    "has_numerical": true,
    "has_derivation": true,
    "estimated_mins": 23
  }},
  "day4": {{
    "sections": ["EXACT heading 6", "EXACT heading 7"],
    "subheadings": ["EXACT subheading 7", "EXACT subheading 8"],
    "focus": "One sentence — what Day 4 covers",
    "has_numerical": true,
    "has_derivation": false,
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

            key_terms   = ", ".join([t for s in sections_list for t in s.get("key_terms", [])][:12])
            key_formulas = ", ".join(sections.get("key_formulas", [])[:8])
            key_laws    = ", ".join(sections.get("key_laws", [])[:6])

            prompt = f"""Generate ONLY the preamble section of this Physics Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Physics
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

ALL CHAPTER SECTIONS:
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY TERMS    : {key_terms}
KEY FORMULAS : {key_formulas}
KEY LAWS     : {key_laws}

Generate EXACTLY these sections in this order:

<h2>Part 1: Chapter Overview</h2>
Table: Class | Subject | Discipline | Unit/Chapter Title | Month |
       Total Teaching Hours | Session Duration | Main Sections Covered

<h2>Part 2: Learning Objectives</h2>
4-5 SWBAT objectives with action verbs (Define, State, Apply, Calculate, Derive, Analyse)
Based ONLY on actual sections in this chapter — match teacher LP style exactly
Physics-specific: include calculation, derivation, real-world application objectives

<h2>Part 3: Value-Based Objectives</h2>
3-4 value objectives based on actual chapter content:
  e.g. Appreciate Newton's contribution, Connect physics to everyday safety,
  Understand how science corrects old misconceptions, Respect mathematical precision

<h2>Part 4: Skill Objectives</h2>
4 skill objectives: Formula Derivation, Numerical Problem Solving,
Real-World Application, Experimental Observation
Customised to this chapter's actual content

<h2>Part 5: Teaching Aids</h2>
All materials: board, chalk, everyday props for demos
(coins, cards, rulers, erasers, balloons — whatever this chapter needs),
textbooks, notebooks, differentiated worksheet sheets (3 levels)
Based on actual chapter content — Physics-specific props mentioned

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
                system=SCIENCE_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Physics LP preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2-5 — CONTENT DAYS 1-4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            strategy = PHYSICS_DAY_STRATEGY[day_num]

            day_sections    = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus       = day_data.get("focus", "")
            has_numerical   = day_data.get("has_numerical", False)
            has_derivation  = day_data.get("has_derivation", False)

            # Collect key terms, formulas, laws for this day
            all_sections  = sections.get("chapter_sections", [])
            day_key_terms = []
            day_formulas  = []
            day_laws      = []
            for s in all_sections:
                if s["heading"] in day_sections:
                    day_key_terms.extend(s.get("key_terms", []))
                    day_formulas.extend(s.get("key_formulas", []))
                    day_laws.extend(s.get("key_laws", []))

            sections_str    = "\n".join([f"  ▸ {s}" for s in day_sections])
            subheadings_str = "\n".join([f"      • {s}" for s in day_subheadings])
            key_terms_str   = ", ".join(day_key_terms[:10])
            formulas_str    = "\n".join([f"  - {f}" for f in day_formulas[:6]])
            laws_str        = "\n".join([f"  - {l}" for l in day_laws[:4]])

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
NUMERICAL DAY NOTE — EVERY numerical sub-point must have:
  Step 1: Write formula on board
  Step 2: Solve one full worked example —
          Given: [quantities] | Formula: [formula] | Substitution: [numbers] | Answer: [result + unit]
  Step 3: Students solve a parallel problem — 2-3 minutes
  Step 4: One student writes solution on board — class verifies
Never skip the worked example. Never skip the student parallel problem.
Use ONLY values that appear in the chapter text — never invent numbers.
"""

            derivation_note = ""
            if has_derivation:
                derivation_note = """
DERIVATION NOTE — For every law derivation:
  Step 1: State the law in words first — read from textbook
  Step 2: Write the starting point on board (what we know)
  Step 3: Show each algebraic/mathematical step — narrate every step aloud
  Step 4: Arrive at the final formula — box it on the board
  Step 5: Explain the meaning of each term in the final formula
Never skip steps. Never jump to the final formula without showing working.
"""

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi Physics Lesson Plan.

REFERENCE STYLE: Match the teacher-approved manual LP style exactly.
The manual LP style is:
  - Prop + physical body activity spark (coin flick, squat drop, clap test)
  - Branch map or concept chain on board for introduction
  - Human physical demos embedded in teaching (Tug-of-War, Door Challenge, Desk Push)
  - Formula derivation step by step on board
  - Worked numerical every day (Given → Formula → Substitution → Answer)
  - Differentiated 3-level worksheet every day (5 minutes)
  - Formula Departure Shout to close the day
  - Script-level detail so any new teacher can follow

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Physics
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S SECTIONS — COVER ALL IN ORDER
═══════════════════════════════════════════════════════
Main sections:
{sections_str}

Subheadings (ALL must be taught):
{subheadings_str}

Day Focus    : {day_focus}
Key Terms    : {key_terms_str}
Key Formulas :
{formulas_str if formulas_str else "  (identify from chapter text)"}
Key Laws     :
{laws_str if laws_str else "  (identify from chapter text)"}
{numerical_note}{derivation_note}
═══════════════════════════════════════════════════════
CRITICAL RULES — READ BEFORE GENERATING
═══════════════════════════════════════════════════════

1. COVER ALL SECTIONS AND SUBHEADINGS:
   - Every section and subheading listed above MUST be taught
   - Teach them IN ORDER as listed
   - Do NOT skip any subheading
   - Do NOT add sections not in the list

2. EXPLANATION QUALITY:
   - Teacher must NOT just read the textbook — they must EXPLAIN
   - After each sub-point: give detailed explanation
   - Add a real-life analogy for EACH sub-point
     Examples: "Just like how a bus passenger leans back when the bus accelerates..."
               "Think of it like a cricket fielder pulling hands back to catch..."
               "Imagine a balloon released without tying..."
   - Historical context where applicable (Aristotle vs Galileo etc.)

2b. FORMULA EXTRACTION RULE — STRICTLY ENFORCE:
   - NEVER use hardcoded formulas like p=mv, F=ma, W=mg unless they appear
     VERBATIM in the chapter text provided below
   - Extract ALL formulas ONLY from the chapter text
   - If a formula is not in the chapter text — do NOT include it
   - This applies to every board work block, every worked example, every CCQ

3. CCQ QUESTIONS (woven in — not separate blocks):
   - After EACH sub-point: 1-2 CCQ questions
   - Mix CFU (factual) and CCQ (application) types
   - Write questions on board — students answer by raising hands
   - Physics CCQs must include at least 2 formula/unit questions per day
   - Include vector/scalar CCQs ONLY IF the chapter text explicitly mentions
     vector or scalar quantities — never force these if not in the chapter

4. FORMULA ON BOARD — MANDATORY:
   - Every formula must be written on board as it is introduced
   - Derivations shown step by step — never jump to final formula
   - Units written alongside every formula
   - Students copy formula + derivation into notebook

5. WORKED NUMERICAL — EVERY DAY:
   - At least ONE worked numerical per day
   - Format: Given → Formula → Substitution → Answer with unit
   - After worked example: students solve parallel problem (2-3 minutes)
   - Use ONLY values from the chapter text — never invent numbers

6. DIFFERENTIATED WORKSHEET — EVERY DAY (mandatory):
   - 3 levels: Level 1 (Foundation) / Level 2 (Standard) / Level 3 (Advanced)
   - 5 minutes near end of session
   - Each level based on TODAY'S content only
   - Students identify level from symbol/color on worksheet

7. DEPARTURE SHOUT — MANDATORY EVERY DAY:
   - Formula stem → Students shout completion
   - Run 3 rounds
   - Teacher gives homework after shout

8. HOMEWORK — EVERY DAY:
   - 2 tasks: one home observation/experiment + one numerical practice
   - Based on TODAY'S content — not next day's

{TAMIL_INSTRUCTION}

{CCQ_INSTRUCTION}

9. NO PAGE NUMBERS:
   - Do NOT mention any page numbers anywhere

10. NO RELIGIOUS REFERENCES in any analogy

11. NO SPECIFIC STUDENT NAMES — use "a student" or "Student A"

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

WORKSHEET LEVELS:
{strategy['worksheet_levels']}

CLOSING SHOUT:
{strategy['closing_shout']}
═══════════════════════════════════════════════════════

GENERATE Day {day_num} using EXACTLY this HTML structure:

<h3 class="lp-day-title">Day {day_num} — [Exact section names taught today]</h3>

<div class="lp-day-meta">
  <table>
    <tr>
      <th>Learning Objective</th>
      <td>[Specific SWBAT — action verb + physics concept + calculation if applicable]</td>
      <th>Focus</th>
      <td>{day_focus}</td>
    </tr>
  </table>
</div>

<div class="lp-day-block">

  <!-- ═══ [0-5 min] SPARK / PROP + PHYSICAL ACTIVITY ═══ -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Opening [0–5 min]</span>
    <h4>Spark — {strategy['spark_style']}</h4>

    {"<!-- Day 2+: 1-minute formula recap first -->" if day_num > 1 else ""}
    {"<p class='lp-teacher-says'><strong>Quick Recap (1 min):</strong> Teacher asks 2-3 rapid formula questions from yesterday. Students shout answers. Example: 'p = ?' → 'mv!' No writing needed.</p>" if day_num > 1 else ""}

    <p class="lp-teacher-says"><strong>Teacher says (Prop + Physical Activity):</strong><br/>
    "[{strategy['spark_style']} — describe the prop clearly OR give the physical activity instruction.
     'Class, I have [prop]. What do you think will happen when I [action]?'
     OR 'Stand up! On my count, [physical activity]! Ready?'
     After the activity/demo: 'That [sensation/observation] is called [concept].'
     Connects to today's sections: {', '.join(day_sections)}.]"</p>

    <p class="lp-tamil-scaffold"><em>தமிழில்:</em>
    "[Same opening question in Tamil — context-based, natural Tamil]"</p>

    <p class="lp-teacher-says"><strong>Teacher then says (Real-life Connection):</strong><br/>
    "[Why are we learning this? Connect today's physics concept to ONE specific
     real-world application — safety engineering, sports, space science, vehicles.
     Keep it to 2-3 sentences. Make students feel the importance.]"</p>

    <p><em>Allow 2-3 student predictions/answers. Teacher acknowledges without revealing yet.</em></p>

    <div class="lp-teacher-says">
      <strong>Teacher says — Why We Learn This:</strong><br/>
      "[Explain specifically WHY students learn today's topic.
       Give a concrete real-life example from Tamil Nadu daily life.
       Tell them exactly where they will use this knowledge.
       Must be specific to today's sections — not generic.]"
    </div>
  </div>

  <!-- ═══ [5-10 min] INTRODUCTION ═══ -->
  <div class="lp-section-intro">
    <span class="lp-section-label">Introduction [5–10 min]</span>

    <div class="board-work">
      <strong>Write on Board — Branch Map / Concept Chain:</strong><br/>
      [Write a rapid branch map or chain connecting today's concepts:]<br/>
      [e.g. MECHANICS → STATICS (bodies at rest) | DYNAMICS (bodies in motion)]<br/>
      Topic: [today's section names]<br/>
      Objective: [today's SWBAT in one line]<br/>
      Key Formula: [main formula if applicable]
    </div>

    <p class="lp-teacher-says"><strong>Teacher says (Introduction — English):</strong><br/>
    "[Teacher introduces today's concept in simple words — 3-4 sentences.
     Historical context if applicable (e.g. 'Aristotle believed X, but Galileo proved Y').
     One real-life analogy connecting to the concept.
     Connect back to the prop/activity from the spark.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — same introduction. Same length. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word. Pure Tamil Unicode only.]"</p>
    </div>

    <div class="vocab-block">
      <strong>Key Terms + Formulas — Write on Board:</strong>
      <table>
        <thead><tr><th>Term / Formula</th><th>Meaning / Value</th><th>Tamil பொருள்</th></tr></thead>
        <tbody>
          [5-6 key physics terms AND formulas from today's sections.
           Include SI units for each formula.
           Tamil equivalent or transliteration for each term.]
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

    [FOR EACH subheading under this section — in exact order:]

    <h5>[EXACT subheading name]</h5>

    <p class="lp-teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
    "[Teacher reads sub-point from textbook.
     Explains in simple language — 3-4 sentences.
     ANALOGY: 'Just like [everyday Indian/physical experience]...'
     Include specific formula, law, or definition from textbook.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[Same explanation in Tamil — context-based, same length, same analogy.]"</p>
    </div>

    <div class="board-work">
      <strong>Write / Derive on Board:</strong><br/>
      [Formula or derivation step — build step by step]<br/>
      [Write units alongside every formula]<br/>
      [Box the final formula when derivation is complete]
    </div>

    [IF this subheading has a numerical problem:]
    <div class="worked-example">
      <strong>Worked Example (Teacher models):</strong>
      <p><strong>Given:</strong> [quantities with units from textbook]</p>
      <p><strong>Formula:</strong> [exact formula]</p>
      <p><strong>Substitution:</strong> [numbers with units — every step shown]</p>
      <p><strong>Answer:</strong> [result with correct unit]</p>
    </div>
    <p><em>Students solve parallel problem in notebook — 2 minutes.
    One student writes solution on board. Class verifies step by step.</em></p>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Factual or formula question — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Answer with unit if applicable]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Application or Why question — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    [REPEAT subheading block for each subheading under section 1]

    <!-- Embedded Activity -->
    <div class="activity-block">
      <strong>⚙️ Activity ({strategy['activity'].split(chr(10))[0]}):</strong>
      <p>[Step by step physical activity or demo instructions.
         Based ONLY on today's chapter content.
         Students are physically active — pushing, leaning, catching, dropping.]</p>
    </div>

  </div>

  <!-- ═══ [20-25 min] MAIN TEACHING — TOPIC 2 ═══ -->
  <div class="lp-section-main">
    <span class="lp-section-label">Main Teaching — Topic 2 [20–25 min]</span>
    <h4>[EXACT name of second section from today's list]</h4>

    <p class="teacher-role"><em>Teacher Role: {strategy['topic2_strategy'].split(chr(10))[0]}</em></p>

    [FOR EACH subheading — in exact order:]

    <h5>[EXACT subheading name]</h5>

    <p class="lp-teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
    "[Read sub-point from textbook. Explain — 3-4 sentences.
     ANALOGY: [physical or everyday analogy].
     Formula/law from textbook.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[EXACT same explanation in Tamil — sentence by sentence mirror.
          Same length. Same detail. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word.
          Pure Tamil Unicode only.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      [IF today's content contains two comparable concepts (e.g. Mass vs Weight,
       Speed vs Velocity, Scalar vs Vector) — draw a comparison table:
       | Feature | Concept A | Concept B |
       Fill one row at a time as you explain.
       IF no two comparable concepts exist today — write formula derivation
       or case-by-case breakdown instead.
       NEVER force a comparison table where one does not naturally exist.]
    </div>

    [IF numerical: include worked-example block — same format as Topic 1]

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Question about this sub-point — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Short answer with unit]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    [REPEAT for each subheading]

  </div>

  <!-- ═══ [25-30 min] DIFFERENTIATED WORKSHEET — EVERY DAY — NEVER SKIP ═══ -->
  <div class="lp-section-student-task">
    <span class="lp-section-label">Differentiated Worksheet [25–30 min]</span>
    <h4>3-Level Assessment Worksheet</h4>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "Check the symbol on your worksheet. Find your level and solve your block.
     You have 5 minutes. Work independently."</p>

    <table class="diff-table" style="border: 2px solid #333; width: 100%;">
      <thead>
        <tr>
          <th>Level 1 — Foundation<br/><em>(Explainer Group)</em></th>
          <th>Level 2 — Standard<br/><em>(Logic Group)</em></th>
          <th>Level 3 — Advanced<br/><em>(Analyst Group)</em></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            [Q1: Define a key term — use EXACT term from today's chapter text]<br/>
            [Q2: Match concept to example — 3 pairs from today's actual content only]<br/>
            [Q3: Basic numerical — use ONLY values and formulas from today's chapter text.
                 If no numerical in today's chapter — replace with: complete a definition
                 or identify a term from a description]
          </td>
          <td>
            [Q1: Explain a real-life application of today's concept from chapter text only]<br/>
            [Q2: Moderate numerical — use ONLY values from today's chapter text.
                 If no numerical in today's chapter — replace with a conceptual question]<br/>
            [Q3: Short analysis — explain why/how using today's concept from chapter text only]
          </td>
          <td>
            [Q1: Distinguish between two related concepts from today's chapter text only]<br/>
            [Q2: Advanced numerical — use ONLY values from today's chapter text.
                 If no numerical in today's chapter — replace with a conceptual question]<br/>
            [Q3: Evaluate a statement or derive a formula from today's chapter text only]
          </td>
        </tr>
      </tbody>
    </table>

    <p><em>After 5 minutes: teacher gives answers rapidly. Students check own work.</em></p>
  </div>

  <!-- ═══ [30-35 min] CLOSING — MANDATORY — NEVER SKIP ═══ -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>

    <div class="board-work">
      <strong>Key Formulas on Board{"" if day_num < 4 else " (All 4 Days)"}:</strong><br/>
      1. [Key formula 1 from today — with unit]<br/>
      2. [Key formula 2 from today — with unit]<br/>
      3. [Key law or definition from today]<br/>
      {"4. [Formula 4]<br/>5. [Formula 5]" if day_num == 4 else ""}
    </div>

    <!-- FORMULA DEPARTURE SHOUT -->
    <div class="departure-shout">
      <strong>🔊 Formula Departure Shout:</strong>
      <p><em>Teacher gives formula stem → Students shout completion ALOUD together.</em></p>
      <p class="lp-teacher-says">Teacher: "[Formula or concept stem from today]...?"</p>
      <p class="student-says">Students: "[ANSWER / FORMULA IN CAPS]!"</p>
      <p class="lp-teacher-says">Teacher: "[Second formula stem]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p class="lp-teacher-says">Teacher: "[Third stem — law or definition]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p><em>Run 3 rounds minimum. Keep energy high.</em></p>
    </div>

    <!-- HOMEWORK -->
    <div class="lp-section-student-task" style="margin-top: 10px;">
      <strong>Homework (2 min):</strong>
      <div class="board-work">
        <strong>Write on Board:</strong><br/>
        Home Observation: [One real-life observation task connecting to today's concept]<br/>
        Numerical Practice: [One numerical problem from today's content — students solve at home]<br/>
        {"Read Ahead: [Name the first concept from next day]" if day_num < 4 else "Review: Go over all 4 days of notes for tomorrow's summary session."}
      </div>
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ ALL sections covered: {', '.join(day_sections)}
✅ ALL subheadings covered: {', '.join(day_subheadings)}
✅ Every sub-point: read aloud → explanation → analogy → formula on board → CCQ
✅ Worked numerical PRESENT if chapter text contains numerical values for today's sections
   If no numerical values in chapter text for today — skip worked example and use
   conceptual CCQ instead — NEVER invent numbers
✅ Formula Departure Shout PRESENT with at least 3 rounds — NEVER skip
✅ Differentiated 3-level worksheet PRESENT and COMPLETE — never skip
✅ Homework block PRESENT — home observation + numerical
✅ Tamil mirror present after EVERY subheading explanation — Topic 1 AND Topic 2
✅ Tamil also in: Opening Question + Introduction + Key Terms table
✅ NO Tamil in: activity instructions, board work, closing, homework, student task
✅ No page numbers anywhere
✅ No religious references
✅ No specific student names — "a student" or "Student A" only
✅ All English spelled correctly — especially physics terms
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
            print(f"❌ Physics LP Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — DAY 5: BOOK-BACK + FORMULA REVIEW
    # =========================================================================

    def _call_day5(self, text, class_num, unit, lesson_title,
                   sections: dict, day_plan: dict):
        try:
            key_formulas = ", ".join(sections.get("key_formulas", []))
            key_laws     = ", ".join(sections.get("key_laws", []))
            key_terms    = ", ".join([t for s in sections.get("chapter_sections", [])
                                      for t in s.get("key_terms", [])][:15])

            all_section_names = [s["heading"] for s in sections.get("chapter_sections", [])]
            day_summaries = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summaries += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"
                subs = d_data.get("subheadings", [])
                if subs:
                    day_summaries += f"    Subs: {', '.join(subs[:3])}\n"

            prompt = f"""Generate ONLY Day 5 of the Physics Lesson Plan.
Day 5 = Book-back Marking → Formula + Law Review → Closing.
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
KEY LAWS     : {key_laws}
KEY TERMS    : {key_terms}

Generate Day 5 with this structure:

<h3 class="lp-day-title">Day 5 — Book-back Exercises and Formula Review</h3>

<div class="lp-day-meta">
  <table>
    <tr>
      <th>Learning Objectives</th>
      <td>Evaluate understanding through book-back exercises.
      Consolidate all formulas, laws, and derivations from the chapter.</td>
    </tr>
  </table>
</div>

<div class="lp-day-block">

  <!-- [0-5 min] SPARK — FORMULA RAPID FIRE -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Opening [0–5 min]</span>
    <h4>Spark — Formula Rapid Fire (All 4 Days)</h4>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[Run 5-6 formula call-and-response rounds covering ALL 4 days.
     Teacher gives formula stem → Students shout completion.
     Use actual formulas and laws from this chapter only.
     Example: 'Force equals mass times...?' → Students: 'ACCELERATION! F = ma!']"</p>
    <p><em>This activates all prior knowledge before book-back marking.</em></p>
  </div>

  <!-- [5-20 min] BOOK-BACK MARKING -->
  <div class="lp-section-main">
    <span class="lp-section-label">Book-back Marking [5–20 min]</span>
    <h4>Book-Back Exercise Marking and Discussion</h4>
    <p class="teacher-role"><em>Teacher facilitates step-by-step marking.
    Students self-mark while teacher shows solutions on board.
    For numericals: show full working — Given → Formula → Substitution → Answer.</em></p>
    <p><em>⚠️ Note to Teacher: All book-back answers are in the QA section of this platform.</em></p>

    <h5>Section 1: MCQ / Fill in the Blanks</h5>
    <p>[For each answer: identify the key formula/law being tested.
     Explain WHY the correct answer is right.
     Common mistakes: highlight what wrong answers assumed.]</p>

    <h5>Section 2: Short Answer / Match</h5>
    <p>[For each answer: reference the law or derivation from chapter.
     For formula-based answers: write the formula on board.
     Students check and correct their own answers.]</p>

    <h5>Section 3: Numerical Problems</h5>
    <p>[For 3-4 key numericals: solve completely on board.
     Given → Formula → Substitution → Answer with unit.
     Students check their working — not just final answer.
     Highlight common errors in unit conversion or formula selection.]</p>

    <div class="board-work">
      <strong>Key Answers on Board:</strong><br/>
      [Main answers and numerical solutions for verification]
    </div>
  </div>

  <!-- [20-30 min] FORMULA + LAW REVIEW -->
  <div class="lp-section-main">
    <span class="lp-section-label">Formula and Law Review [20–30 min]</span>
    <h4>Master Formula and Law Sheet</h4>
    <p class="teacher-role"><em>Teacher writes ALL chapter formulas and laws on board.
    Students copy into formula log at back of notebook.
    Teacher solves one revision numerical from each day's content.</em></p>

    <div class="board-work">
      <strong>Chapter Master Formula Sheet — Write All on Board:</strong><br/>
      {key_formulas if key_formulas else "[All formulas from chapter — with units]"}<br/>
      <br/>
      <strong>Chapter Laws:</strong><br/>
      {key_laws if key_laws else "[All laws from chapter — stated in words]"}<br/>
      <br/>
      <strong>Memory Tips:</strong><br/>
      [3-4 memory tricks — mnemonics or verbal patterns for key formulas/laws]
    </div>

    <h5>Formula Memory Check</h5>
    <p>[Students close notebooks. Teacher calls students to write one formula from memory.
     5-6 students participate. Class checks. Teacher reinforces any errors.]</p>
  </div>

  <!-- CLOSING -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[Congratulate students on completing the chapter.
     Name 2-3 specific concepts learned across all 5 days.
     Connect the chapter to real-world physics applications.
     Motivate for next chapter.]"</p>

    <div class="board-work">
      <strong>All Students Must Submit:</strong><br/>
      ☐ Notebook — all 5 days of notes completed<br/>
      ☐ Book-back exercises — answered and marked<br/>
      ☐ Formula log — all chapter formulas with units written neatly<br/>
      ☐ All differentiated worksheets completed (Days 1-4)<br/>
      ☐ All homework tasks from Days 1-4
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="lp-day-title">Day 5
- Book-back section must have real content from chapter
- Formula review based on actual chapter formulas and laws
- No page numbers — reference section names only
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
            print(f"❌ Physics LP Day 5 error: {e}")
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
            key_laws      = ", ".join(sections.get("key_laws", [])[:6])

            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Physics chapter.
Do NOT repeat day content. Do NOT generate day blocks.

Chapter      : {lesson_title}
Class        : {class_num}
Unit         : {unit}
All Sections : {sections_str}
Key Terms    : {key_terms}
Key Formulas : {key_formulas}
Key Laws     : {key_laws}

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
       Physics-specific: include formula recall and law statement questions.]
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
       One Why/How/Calculate question per day.
       Physics-specific: include numerical application and derivation questions.
       Tamil version in last column — context-based natural Tamil.]
    </tbody>
  </table>

  <h3>Differentiated Written Worksheet — 3 Levels</h3>
  <table class="diff-table" style="border: 2px solid #333;">
    <thead>
      <tr>
        <th>Level 1 — Foundation<br/>10 Marks</th>
        <th>Level 2 — Standard<br/>10 Marks</th>
        <th>Level 3 — Advanced<br/>10 Marks</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Q1 (2M):</strong> Define 2 key terms from the chapter</p>
          <p><strong>Q2 (3M):</strong> State Newton's [relevant] Law and give one example</p>
          <p><strong>Q3 (5M):</strong> Solve a basic one-step numerical using a chapter formula</p>
        </td>
        <td>
          <p><strong>Q1 (3M):</strong> Explain a real-life application using today's law/formula</p>
          <p><strong>Q2 (3M):</strong> Solve a 2-step numerical problem from chapter content</p>
          <p><strong>Q3 (4M):</strong> Compare two related concepts from the chapter in a table</p>
        </td>
        <td>
          <p><strong>Q1 (4M):</strong> Derive a key formula from the chapter — show all steps</p>
          <p><strong>Q2 (3M):</strong> Solve an advanced multi-step numerical</p>
          <p><strong>Q3 (3M):</strong> Evaluate a given statement using chapter concepts</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Formula and Law Checklist</h3>
  <ul>
    [Each formula and law from the chapter as a checklist item:
     ☐ [Formula/Law name]: [Formula] — Unit: [unit] — Use: [1-sentence real-world use]]
  </ul>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in notebook</li>
    <li>☐ All differentiated worksheets completed (Days 1-4)</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Formula log completed — all formulas and laws with units</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ All numericals attempted — working shown clearly</li>
    <li>☐ [One chapter-specific item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Section A table: exactly 5 rows
- Section B table: exactly 5 rows with Tamil column
- Differentiated worksheet: 3 columns with visible 2px border
- Formula checklist: every formula and law from chapter with units and real-use
- No page numbers
- Base all content on actual extracted sections

Chapter Text:
---
{text[:3000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=6000,
                system=SCIENCE_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Physics LP assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

physics_lp_910_builder = PhysicsLP910Builder()