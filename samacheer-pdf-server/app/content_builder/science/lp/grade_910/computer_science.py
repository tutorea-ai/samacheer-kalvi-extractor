"""
cs.py
-----
LP Builder for Samacheer Kalvi Science — Computer Science
Class 8, 9 & 10

v1.0 — May 2026
Built from first principles — no teacher manual LP available.
Modeled on ss/lp/grade_910/history.py structure.
Content reference: Class 10 Unit 23 — Visual Communication (File, Folder, Scratch)

KEY DIFFERENCES FROM OTHER SCIENCE DISCIPLINES:
  - No formulas, no numericals, no diagrams to draw
  - Purely procedural (step-by-step) + conceptual (definition, function, type)
  - Spark: real device or daily tech scenario (phone, laptop, animation, cinema)
  - Board work: UI layout sketch, step-by-step flow, block diagram, classification tree
  - Student activity: mime the clicks, term sorting, true/false rapid fire, concept map
  - Closing: Term Departure Shout (term → function/definition)
  - No synthesis sentence — replaced by "What I learned today" exit slip

STRUCTURE PER DAY (CS-specific):
  [0-5 min]   Spark / Tech Scenario Hook
              → Real device or everyday tech experience
              → Big Question connecting tech to today's CS concept
              → Real-life use stated clearly
              → Day 2+: quick recap of yesterday's key terms

  [5-10 min]  Introduction
              → Concept chain or classification tree on board
              → Key terms table (English + Tamil meaning)
              → 1 CCQ from introduction

  [10-20 min] Main Teaching — Topic 1
              → Read aloud from textbook + explain
              → Step-by-step flow on board (for procedural content)
              → Classification/block diagram (for conceptual content)
              → Analogy connecting CS concept to real-world equivalent
              → CCQs woven in after each sub-point
              → Student activity embedded

  [20-30 min] Main Teaching — Topic 2
              → Same pattern
              → Hands-on mime activity or term sorting

  [30-35 min] Closing
              → "What I learned today" exit slip (1-2 sentences)
              → Term Departure Shout
              → Homework: observe tech at home + define key terms

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
    TAMIL_INSTRUCTION,
    CCQ_INSTRUCTION,
)


# ============================================================================
# CS TEACHING STRATEGY PER DAY
# Tech scenario sparks, step-by-step flow on board, mime activities,
# term sorting, exit slip closing, Term Departure Shout
# ============================================================================

CS_DAY_STRATEGY = {
    1: {
        "spark_style": "Real Device + Everyday Tech Scenario",
        "spark_instruction": (
            "Teacher holds up or refers to a real everyday device or tech scenario.\n"
            "Examples for CS:\n"
            "  - Hold up a phone: 'Where do your photos live on this phone?'\n"
            "  - 'Think of the last time you saved a document — where did it go?'\n"
            "  - 'When you watch a cartoon or animation — how was it made?'\n"
            "Structure:\n"
            "  Step 1: Describe the device or scenario dramatically.\n"
            "  Step 2: Ask: 'Have you ever wondered how this works?'\n"
            "  Step 3: Connect to today's CS concept.\n"
            "  Step 4: Big Question — ends with curiosity about today's topic.\n"
            "  Step 5: Real-life use — where will students use this skill?\n"
            "Allow 2-3 student answers before revealing today's focus."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Concept Definer + Real-World Analogy Provider\n"
            "Step 1: Write the key term on board — large and clear.\n"
            "Step 2: Read the definition from textbook — aloud.\n"
            "Step 3: Explain in simple words — 3-4 sentences.\n"
            "Step 4: Give a real-world analogy:\n"
            "        'Just like [everyday equivalent], in a computer [concept] means...'\n"
            "Step 5: Write the analogy as a comparison on board:\n"
            "        Real World → Computer World\n"
            "        [Analogy item] → [CS term]\n"
            "Step 6: 1-2 CCQ questions after explanation."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Step-by-Step Flow Guide\n"
            "Step 1: Write the procedure as a numbered flow on board:\n"
            "        Step 1 → Step 2 → Step 3 → ...\n"
            "Step 2: Explain each step — read from textbook + explain.\n"
            "Step 3: Students mime the procedure at their desks (no computer needed).\n"
            "        Example: 'Pretend to right-click. Now move to NEW. Now click Folder.'\n"
            "Step 4: 2 CCQ questions after the procedure."
        ),
        "activity": (
            "REAL-WORLD ANALOGY MAPPING (Day 1):\n"
            "Teacher writes two columns on board: 'Real World' | 'Computer World'\n"
            "Teacher gives 4-5 real-world items one by one.\n"
            "Students call out the CS equivalent for each.\n"
            "Example: 'A single book in a library shelf' → Students: 'FILE!'\n"
            "         'The whole shelf of books' → Students: 'FOLDER!'\n"
            "         'The library building' → Students: 'COMPUTER/HARD DRIVE!'\n"
            "Run with actual terms from TODAY'S chapter content only.\n"
            "After activity: students write 3 CS terms with real-world analogies in notebook.\n"
            "⚠️ Analogy Mapping is used ONLY on Day 1 — not repeated."
        ),
        "closing_shout": (
            "Term Departure Shout:\n"
            "Teacher gives term → Students shout definition/function.\n"
            "Example: 'A storage space containing multiple files is called...?'\n"
            "         → Students: 'FOLDER!'\n"
            "Run 3 rounds from today's key terms."
        ),
        "exit_slip": (
            "EXIT SLIP (CS closing — replaces synthesis sentence):\n"
            "Teacher writes on board: 'Today I learned that [term 1] is _____ and\n"
            "[term 2] is _____.'\n"
            "Students complete in notebook — 1 minute.\n"
            "2-3 students read aloud. Teacher gives 1-line feedback."
        ),
    },
    2: {
        "spark_style": "Software Demo Description + Curiosity Hook",
        "spark_instruction": (
            "Teacher describes a software or app scenario students have seen or used.\n"
            "Examples for CS:\n"
            "  - 'Have you seen a cartoon made entirely on a computer? Like [popular cartoon]?'\n"
            "  - 'When you play a game on a phone — someone programmed every single move.'\n"
            "  - 'What if I told you that YOU can make an animation today — without being\n"
            "     a programmer?'\n"
            "Structure:\n"
            "  Step 1: Describe the software/scenario with energy.\n"
            "  Step 2: 1-minute recap: ask 2-3 rapid questions from yesterday's terms.\n"
            "  Step 3: Big Question connecting to today's software/tool.\n"
            "  Step 4: Real-life use — career, creativity, problem-solving.\n"
            "Allow 2-3 student guesses before revealing today's focus."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Software Environment Layout Explainer\n"
            "Step 1: Draw a simple block diagram of the software interface on board.\n"
            "        Label each panel/area clearly as you draw.\n"
            "Step 2: Explain each component — read from textbook + explain.\n"
            "Step 3: Use spatial memory anchor for each component:\n"
            "        'Top left is [name] — it shows [function].'\n"
            "        'Bottom left is [name] — it does [function].'\n"
            "Step 4: Students copy the block diagram with labels into notebook.\n"
            "Step 5: 2 CCQ questions on component names and functions."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Component Deep-Dive Explainer\n"
            "Step 1: Point to each sub-component one by one on the board diagram.\n"
            "Step 2: Explain its function — read from textbook + explain.\n"
            "Step 3: Real-world analogy for each component.\n"
            "        Example: 'Script area is like a kitchen — where you actually cook\n"
            "        (build) your program.'\n"
            "Step 4: Students label their diagram as each component is explained.\n"
            "Step 5: 2 CCQ questions."
        ),
        "activity": (
            "COMPONENT IDENTIFICATION QUIZ (Day 2):\n"
            "Teacher points to different areas of the board diagram one by one.\n"
            "Students must name the component and its function.\n"
            "Run 5-6 rounds — each round: teacher points → students call out name + function.\n"
            "Example: Teacher points to Stage area → Students: 'STAGE — the background!'\n"
            "         Teacher points to Sprite → Students: 'SPRITE — the character!'\n"
            "Use ONLY components from TODAY'S actual chapter content.\n"
            "After quiz: students write all component names + functions in notebook.\n"
            "⚠️ Component Identification Quiz is used ONLY on Day 2 — not repeated."
        ),
        "closing_shout": (
            "Term Departure Shout — Component + Function:\n"
            "Teacher names component → Students shout function.\n"
            "Example: 'Stage is...?' → Students: 'THE BACKGROUND!'\n"
            "         'Sprite is...?' → Students: 'THE CHARACTER!'\n"
            "Run 3 rounds from today's components."
        ),
        "exit_slip": (
            "EXIT SLIP:\n"
            "Teacher writes on board: 'The [software name] editor has [X] main parts:\n"
            "_____, _____, and _____.'\n"
            "Students complete in notebook — 1 minute.\n"
            "2 students read aloud. Teacher confirms."
        ),
    },
    3: {
        "spark_style": "Step-by-Step Challenge + Prediction Hook",
        "spark_instruction": (
            "Teacher presents a step-by-step challenge that connects to today's procedure.\n"
            "Examples for CS:\n"
            "  - 'If I told you to make a character move 100 steps — what would you do first?'\n"
            "  - 'How many steps does it take to make a character say Hello?'\n"
            "  - 'Can you predict what happens if we change the number 10 to 100 in the\n"
            "     move block?'\n"
            "Structure:\n"
            "  Step 1: Present the challenge or prediction question.\n"
            "  Step 2: 1-minute recap of yesterday's components.\n"
            "  Step 3: Students write their prediction in notebook — 30 seconds.\n"
            "  Step 4: 2-3 students share predictions.\n"
            "  Step 5: Real-life use — game development, animation, storytelling.\n"
            "Reveal answer at the end of today's teaching."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Step-by-Step Flow Demonstrator\n"
            "Step 1: Write the procedure as a numbered flow on board:\n"
            "        Step 1 → Step 2 → Step 3 → ... → Output\n"
            "Step 2: Explain each step — read from textbook + explain.\n"
            "Step 3: Students mime the procedure at their desks:\n"
            "        'Pretend to click File → New. Now drag the block. Now snap it.'\n"
            "Step 4: After each step — CCQ: 'What did we just do? Why?'\n"
            "Step 5: Students write the numbered steps in their notebook."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Variation Explainer\n"
            "Step 1: Show what happens when a value or option changes.\n"
            "        'If we change 10 to 100 in the move block — what changes?'\n"
            "Step 2: Explain the effect — read from textbook + explain.\n"
            "Step 3: Students predict the output — write in notebook.\n"
            "Step 4: Teacher reveals the correct output.\n"
            "Step 5: 2 CCQ questions on the procedure steps."
        ),
        "activity": (
            "MIME THE PROCEDURE (Day 3):\n"
            "Teacher reads each step of today's procedure aloud.\n"
            "Students physically mime the action at their desks — no computer needed.\n"
            "Example: 'Click File' → Students mime clicking\n"
            "         'Drag the block to the script area' → Students mime dragging\n"
            "         'Snap it to the bottom' → Students mime snapping\n"
            "Run through the FULL procedure from today's chapter — all steps.\n"
            "After mime: students write the procedure steps from memory in notebook.\n"
            "Compare with textbook — correct any wrong steps.\n"
            "⚠️ Mime the Procedure is used ONLY on Day 3 — not repeated."
        ),
        "closing_shout": (
            "Term Departure Shout — Step + Action:\n"
            "Teacher gives step description → Students shout the action/result.\n"
            "Example: 'To start a new project you click...?' → Students: 'FILE → NEW!'\n"
            "         'The character in Scratch is called...?' → Students: 'SPRITE!'\n"
            "Run 3 rounds from today's procedure steps."
        ),
        "exit_slip": (
            "EXIT SLIP:\n"
            "Teacher writes on board: 'To make a character move, the steps are:\n"
            "1. _____ 2. _____ 3. _____'\n"
            "Students complete from memory — 1 minute.\n"
            "2 students read aloud. Class checks."
        ),
    },
    4: {
        "spark_style": "Complete Program Challenge + Real Output Hook",
        "spark_instruction": (
            "Teacher presents the goal of building a complete mini-program.\n"
            "Examples for CS:\n"
            "  - 'Today we put EVERYTHING together — by the end, you will know how to\n"
            "     make a character speak AND play a sound.'\n"
            "  - 'Yesterday we made things move. Today we add VOICE to our animation.'\n"
            "  - '5-step challenge: can you predict all 5 steps to make Hello appear\n"
            "     with a sound?'\n"
            "Structure:\n"
            "  Step 1: Present the complete program goal.\n"
            "  Step 2: 1-minute rapid recap of Days 1-3 key terms — call-and-response.\n"
            "  Step 3: Challenge: 'Who can write all the steps before I teach them?'\n"
            "  Step 4: Students attempt — 1 minute.\n"
            "  Step 5: Real-life use — animation, game creation, storytelling with code."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Full Program Walkthrough Guide\n"
            "Step 1: Write the complete program steps on board — all at once first.\n"
            "        Students see the full picture before details.\n"
            "Step 2: Go through each step one by one — read + explain.\n"
            "Step 3: Explain WHY each step is needed — not just WHAT it does.\n"
            "Step 4: Students copy complete program steps into notebook.\n"
            "Step 5: 2 CCQ questions on the complete program."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Output Predictor + Consolidator\n"
            "Step 1: Ask: 'What is the output of this program?'\n"
            "        Students predict — write in notebook.\n"
            "Step 2: Walk through the program again — focusing on output.\n"
            "Step 3: Explain what each block contributes to the final output.\n"
            "Step 4: Connect to real-world output — animation, game, visual story.\n"
            "Step 5: 2 CCQ questions on output and block functions."
        ),
        "activity": (
            "TRUE/FALSE RAPID FIRE (Day 4):\n"
            "Teacher reads 6-8 statements about today's program steps.\n"
            "Students write T or F in notebook for each — fast.\n"
            "Example: 'Scratch was developed by MIT.' → T\n"
            "         'The Stage is where you build scripts.' → F (that's Script Area)\n"
            "         'Sprite is the background of Scratch window.' → F (that's Stage)\n"
            "Use ONLY statements from TODAY'S actual chapter content.\n"
            "After 2 minutes: teacher reads correct answers. Students mark own work.\n"
            "Discuss any wrong answers — explain why.\n"
            "⚠️ True/False Rapid Fire is used ONLY on Day 4 — not repeated."
        ),
        "closing_shout": (
            "Term Departure Shout — All 4 Days:\n"
            "Teacher gives definition or function → Students shout the term.\n"
            "Example: 'A visual programming language from MIT is...?' → Students: 'SCRATCH!'\n"
            "         'The characters in Scratch window are called...?' → Students: 'SPRITES!'\n"
            "         'A storage space with multiple files is called...?' → Students: 'FOLDER!'\n"
            "Run 4 rounds — one from each day's key term."
        ),
        "exit_slip": (
            "EXIT SLIP — Full Chapter:\n"
            "Teacher writes on board:\n"
            "'Today I completed learning about [chapter topic].\n"
            " The most important thing I learned is _____.\n"
            " One question I still have is _____.'\n"
            "Students complete — 1 minute. 3 students share.\n"
            "Teacher addresses the questions briefly."
        ),
    },
}


# ============================================================================
# CS LP BUILDER CLASS
# ============================================================================

class ComputerScienceLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ CS LP Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [CS LP 910 v1.0] Generating: {lesson_title}")
        print(f"      [CS LP 910 v1.0] 9 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

        parts = []

        # Call 0a
        print(f"      [CS LP] Call 0a/9: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        # Call 0b
        print(f"      [CS LP] Call 0b/9: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        # Call 1
        print(f"      [CS LP] Call 1/9: Preamble...")
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
            print(f"      [CS LP] Call {call_num}/9: Day {day_num}...")
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
        print(f"      [CS LP] Call 6/9: Day 5...")
        day5_html = self._call_day5(text, class_num, unit, lesson_title, sections, day_plan)
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # Call 7: Assessment
        print(f"      [CS LP] Call 7/9: Assessment...")
        assessment = self._call_assessment(text, class_num, unit, lesson_title, sections, day_plan)
        if assessment:
            parts.append(clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [CS LP 910 v1.0] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Computer Science chapter.

YOUR ONLY JOB: Extract EVERY heading and subheading that appears in the chapter text.
Capture ALL levels:
  Level 1: Main headings (e.g. File, Folder, Visual Communication, Scratch)
  Level 2: Subheadings under each main heading
  Level 3: Sub-subheadings if present

ABSOLUTE RULES:
- Copy EVERY heading EXACTLY as written — do NOT paraphrase
- Do NOT skip any heading or subheading — extract ALL of them in order
- Do NOT add anything from general knowledge
- Estimate teaching time per section based on content length
- Capture key terms, software names, and procedures per section
- Mark whether a section contains step-by-step procedures

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
          "has_procedure": false,
          "has_definition": true
        }}
      ],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "key_software": ["software1"],
      "has_procedure": false,
      "has_definition": true
    }}
  ],
  "total_estimated_teaching_mins": 70,
  "key_terms": ["all key terms"],
  "key_software": ["all software mentioned"],
  "procedure_sections": ["sections with step-by-step procedures"],
  "definition_sections": ["sections with definitions"]
}}

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system="""You are a strict text extractor. Return ONLY valid JSON.
Extract ALL headings at ALL levels.
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
            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Computer Science lesson plan.

Allocate ALL sections AND subheadings to exactly 4 days.

RULES:
- Each day: 20-25 minutes of content (35 min session minus 10 min opening/closing)
- Keep each main section in ONE day — do NOT split across days
- Keep subheadings WITH their main section
- EVERY section AND subheading must appear in exactly ONE day
- MAXIMUM 3 subheadings per day
- Procedure sections (step-by-step) need more time — max 1 major procedure per day
- Definition sections can be grouped together
- Sections must follow STRICT ORDER from the chapter text
- NEVER assign the same section to two different days
- If chapter is short, give each concept more depth — do NOT rush
- Use EXACT heading text from extracted sections

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "day1": {{
    "sections": ["EXACT heading 1", "EXACT heading 2"],
    "subheadings": ["EXACT subheading 1", "EXACT subheading 2"],
    "focus": "One sentence — what Day 1 covers",
    "has_procedure": false,
    "estimated_mins": 22
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["EXACT subheading 3", "EXACT subheading 4"],
    "focus": "One sentence — what Day 2 covers",
    "has_procedure": false,
    "estimated_mins": 20
  }},
  "day3": {{
    "sections": ["EXACT heading 4"],
    "subheadings": ["EXACT subheading 5", "EXACT subheading 6"],
    "focus": "One sentence — what Day 3 covers — step-by-step procedure",
    "has_procedure": true,
    "estimated_mins": 23
  }},
  "day4": {{
    "sections": ["EXACT heading 5"],
    "subheadings": ["EXACT subheading 7", "EXACT subheading 8"],
    "focus": "One sentence — what Day 4 covers — complete program + consolidation",
    "has_procedure": true,
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

            key_terms    = ", ".join([t for s in sections_list for t in s.get("key_terms", [])][:12])
            key_software = ", ".join(sections.get("key_software", [])[:8])

            prompt = f"""Generate ONLY the preamble section of this Computer Science Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Computer Science
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

ALL CHAPTER SECTIONS:
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY TERMS    : {key_terms}
KEY SOFTWARE : {key_software}

Generate EXACTLY these sections in this order:

<h2>Part 1: Chapter Overview</h2>
Table: Class | Subject | Discipline | Unit/Chapter Title | Month |
       Total Teaching Hours | Session Duration | Main Sections Covered

<h2>Part 2: Learning Objectives</h2>
4-5 SWBAT objectives with action verbs (Define, Differentiate, Identify, Create, Explain, Use)
Based ONLY on actual sections in this chapter
CS-specific: include practical skill objectives (create file, use software, follow procedure)

<h2>Part 3: Value-Based Objectives</h2>
3-4 value objectives based on actual chapter content:
  e.g. Appreciate how technology organizes information, Connect animation to creativity,
  Understand how programming makes ideas come alive, Value systematic step-by-step thinking

<h2>Part 4: Skill Objectives</h2>
4 skill objectives: Procedural Thinking, Software Navigation,
Definition and Classification, Creative Application
Customised to this chapter's actual content

<h2>Part 5: Teaching Aids</h2>
All materials: board, chalk, printed step-by-step procedure cards,
textbooks, notebooks, computer lab access if available
CS-specific: mention software name if applicable
Note: lesson plan is designed to work WITHOUT computer access (mime activities)

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
            print(f"❌ CS LP preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2-5 — CONTENT DAYS 1-4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            strategy = CS_DAY_STRATEGY[day_num]

            day_sections    = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus       = day_data.get("focus", "")
            has_procedure   = day_data.get("has_procedure", False)

            # Collect key terms and software for this day
            all_sections    = sections.get("chapter_sections", [])
            day_key_terms   = []
            day_software    = []
            for s in all_sections:
                if s["heading"] in day_sections:
                    day_key_terms.extend(s.get("key_terms", []))
                    day_software.extend(s.get("key_software", []))

            sections_str    = "\n".join([f"  ▸ {s}" for s in day_sections])
            subheadings_str = "\n".join([f"      • {s}" for s in day_subheadings])
            key_terms_str   = ", ".join(day_key_terms[:10])
            software_str    = ", ".join(day_software[:5])

            # Next day preview
            if day_num < 4:
                next_data     = day_plan.get(f"day{day_num + 1}", {})
                next_sections = next_data.get("sections", [])
                next_preview  = f"Day {day_num + 1}: {', '.join(next_sections)}"
            else:
                next_preview  = "Day 5: Book-back Exercises + Chapter Review"

            procedure_note = ""
            if has_procedure:
                procedure_note = """
PROCEDURE DAY NOTE:
This day contains step-by-step procedures. For each procedure:
  Step 1: Write ALL steps as a numbered flow on board FIRST
  Step 2: Explain each step — read from textbook + explain
  Step 3: Students mime the procedure at their desks
  Step 4: Students write the steps from memory in notebook
  Step 5: Compare with textbook — correct any wrong steps
Never skip steps. Never combine two steps into one.
Keep the exact order from the textbook.
"""

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi Computer Science Lesson Plan.

REFERENCE STYLE: This is a CS lesson — no formulas, no numericals, no diagrams to draw.
The style is:
  - Real device or tech scenario spark (phone, cartoon, animation)
  - Concept explained with real-world analogy (library/bookshelf for files/folders)
  - Step-by-step procedures written as numbered flows on board
  - Students mime the procedure at their desks (no computer needed)
  - Term sorting and true/false activities
  - Exit slip closing (What I learned today)
  - Term Departure Shout
  - Script-level detail so any new teacher can follow

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Computer Science
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
Key Software : {software_str}
{procedure_note}
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
   - After reading each definition/concept: give a real-world analogy
     Examples: "Just like a book in a library shelf is one file..."
               "Scratch is like LEGO blocks for programming — snap pieces together"
               "The Stage is like a cinema screen — characters perform on it"
   - Use Indian everyday context examples wherever possible

3. CCQ QUESTIONS (woven into explanation):
   - After EACH sub-point: 1-2 CCQ questions
   - CS CCQs test definition, function, classification, procedure step
   - Write questions on board — students answer by raising hands
   - Tamil version mandatory for every CCQ

4. BOARD WORK — MANDATORY:
   - Every definition: write term + meaning on board
   - Every comparison: write Real World → Computer World table
   - Every procedure: write numbered steps as flow on board
   - Every software component: draw simple block diagram with labels
   - Students copy ALL board work into notebook

5. STUDENT ACTIVITY:
   - Activity EMBEDDED inside main teaching — not a separate block at end
   - CS activities: mime procedure, term sorting, analogy mapping, true/false
   - No computer required — all activities work in classroom

6. EXIT SLIP — CS CLOSING (replaces synthesis sentence):
   - Before Departure Shout: students write 1-2 sentences
   - Teacher writes sentence starter on board
   - Students complete in 1 minute
   - 2-3 students read aloud

7. TERM DEPARTURE SHOUT — MANDATORY EVERY DAY:
   - Teacher gives term/definition stem → Students shout answer
   - Run 3 rounds from today's key terms
   - Format: Teacher: "[term or definition]...?" → Students: "[ANSWER IN CAPS]!"

{TAMIL_INSTRUCTION}

{CCQ_INSTRUCTION}

8. NO PAGE NUMBERS anywhere
9. NO RELIGIOUS REFERENCES in any analogy
10. NO SPECIFIC STUDENT NAMES — use "a student" or "Student A"

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

EXIT SLIP:
{strategy['exit_slip']}

CLOSING SHOUT:
{strategy['closing_shout']}
═══════════════════════════════════════════════════════

GENERATE Day {day_num} using EXACTLY this HTML structure:

<h3 class="lp-day-title">Day {day_num} — [Exact section names taught today]</h3>

<div class="lp-day-meta">
  <table>
    <tr>
      <th>Learning Objective</th>
      <td>[Specific SWBAT — action verb + CS concept]</td>
      <th>Focus</th>
      <td>{day_focus}</td>
    </tr>
  </table>
</div>

<div class="lp-day-block">

  <!-- ═══ [0-5 min] SPARK / TECH SCENARIO ═══ -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Opening [0–5 min]</span>
    <h4>Spark — {strategy['spark_style']}</h4>

    {"<!-- Day 2+: Quick term recap first -->" if day_num > 1 else ""}
    {"<p class='lp-teacher-says'><strong>Quick Recap (1 min):</strong> Teacher asks 2-3 rapid questions from yesterday's key terms. Students call out answers.</p>" if day_num > 1 else ""}

    <p class="lp-teacher-says"><strong>Teacher says (Tech Scenario Hook):</strong><br/>
    "[{strategy['spark_style']} — describe the real device or tech scenario.
     'Have you ever wondered how [everyday tech experience] works?'
     OR 'What would happen if [CS scenario]?'
     Connects to today's sections: {', '.join(day_sections)}.
     Ends with a Big Question about today's concept.]"</p>

    <p class="lp-tamil-scaffold"><em>தமிழில்:</em>
    "[Same opening question in Tamil — context-based, natural Tamil]"</p>

    <p class="lp-teacher-says"><strong>Teacher then says (Real-life Connection):</strong><br/>
    "[Why are we learning this? Connect today's CS concept to ONE real-world use —
     creativity, career, problem-solving, digital literacy.
     Keep it to 2-3 sentences.]"</p>

    <p><em>Allow 2-3 student answers. Teacher acknowledges without revealing yet.</em></p>
  </div>

  <!-- ═══ [5-10 min] INTRODUCTION ═══ -->
  <div class="lp-section-intro">
    <span class="lp-section-label">Introduction [5–10 min]</span>

    <div class="board-work">
      <strong>Write on Board — Concept Chain / Classification:</strong><br/>
      [Write a simple chain or classification connecting today's concepts:]<br/>
      [e.g. Computer → stores data → in Files → organized in Folders]<br/>
      Topic: [today's section names]<br/>
      Objective: [today's SWBAT in one line]
    </div>

    <p class="lp-teacher-says"><strong>Teacher says (Introduction — English):</strong><br/>
    "[Teacher introduces today's CS concept in simple words — 3-4 sentences.
     One real-world analogy connecting to the concept.
     Example: 'Just like a library organizes books on shelves,
     a computer organizes data in [today's concept]...'
     Connect back to the tech scenario from the spark.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — same introduction. Same length. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word. Pure Tamil Unicode only.]"</p>
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead><tr><th>CS Term</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
        <tbody>
          [5-6 key CS terms from today's sections with clear meanings and Tamil.
           For terms with no Tamil equivalent: write in Tamil script transliteration.]
        </tbody>
      </table>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Short question about today's intro concept — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Short definition or term]"</p>
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
    "[Teacher reads definition/concept from textbook.
     Explains in simple clear language — 3-4 sentences.
     REAL-WORLD ANALOGY: 'Just like [everyday Indian equivalent],
     in a computer [CS concept] means...'
     Specific terms from textbook.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[EXACT same explanation in Tamil — sentence by sentence mirror.
          Same length. Same detail. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word.
          Pure Tamil Unicode only.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      [Term + Definition OR Real World → Computer World comparison table
       OR numbered procedure steps — whichever fits this sub-point]
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Definition or function question — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Term or short definition]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Classification or comparison question — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Short answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    [REPEAT subheading block for each subheading under section 1]

    <!-- Embedded Activity -->
    <div class="activity-block">
      <strong>⚙️ Activity ({strategy['activity'].split(chr(10))[0]}):</strong>
      <p>[Step by step activity instructions.
         Based ONLY on today's chapter content.
         No computer required — works in classroom.]</p>
    </div>

  </div>

  <!-- ═══ [20-30 min] MAIN TEACHING — TOPIC 2 ═══ -->
  <div class="lp-section-main">
    <span class="lp-section-label">Main Teaching — Topic 2 [20–30 min]</span>
    <h4>[EXACT name of second section from today's list]</h4>

    <p class="teacher-role"><em>Teacher Role: {strategy['topic2_strategy'].split(chr(10))[0]}</em></p>

    [FOR EACH subheading — in exact order:]

    <h5>[EXACT subheading name]</h5>

    <p class="lp-teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
    "[Read definition/procedure from textbook.
     Explain — 3-4 sentences.
     ANALOGY: [real-world analogy for this sub-point].
     Specific CS terms from text.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[Same explanation in Tamil — context-based, same length.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      [Term + definition OR numbered procedure steps OR block diagram label]
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Question about this sub-point — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Short answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    [REPEAT for each subheading under section 2]

  </div>

  <!-- ═══ [25-30 min] STUDENT TASK — MANDATORY ═══ -->
  <div class="lp-section-student-task">
    <span class="lp-section-label">Student Task [25–30 min]</span>
    <h4>Homework Task</h4>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "Write both tasks in your homework book. Submit tomorrow morning."</p>
    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Task 1: [Define 2 key terms from today in your own words — with real-life example]<br/>
      Task 2: [Write the steps of today's procedure from memory
               OR observe one tech device at home and describe its files/folders/software]<br/>
      Submit: Tomorrow morning
    </div>
  </div>

  <!-- ═══ [30-35 min] CLOSING — MANDATORY ═══ -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>

    <div class="board-work">
      <strong>Key Terms on Board{"" if day_num < 4 else " (Full Chapter Summary)"}:</strong><br/>
      1. [Key CS term 1 from today — with one-line definition]<br/>
      2. [Key CS term 2 from today — with one-line definition]<br/>
      3. [Key procedure or software component from today]<br/>
      {"4. [Key term 4]<br/>5. [Key term 5]" if day_num == 4 else ""}
    </div>

    <!-- EXIT SLIP — CS-specific closing -->
    <div class="exit-slip-block">
      <strong>✍️ Exit Slip (What I Learned Today):</strong>
      <p><em>Teacher writes sentence starter on board. Students complete — 1 minute.</em></p>
      <div class="board-work">
        <strong>Write on Board (sentence starter):</strong><br/>
        "[Sentence starter connecting today's two key concepts —\n"
        " e.g. 'Today I learned that [term 1] is _____ and [term 2] is _____.]"
      </div>
      <p><em>2-3 students read aloud. Teacher gives 1-line feedback each.</em></p>
    </div>

    <!-- TERM DEPARTURE SHOUT -->
    <div class="departure-shout">
      <strong>🔊 Term Departure Shout:</strong>
      <p><em>Teacher gives term or definition stem → Students shout answer ALOUD.</em></p>
      <p class="lp-teacher-says">Teacher: "[Key term or definition stem from today]...?"</p>
      <p class="student-says">Students: "[TERM OR ANSWER IN CAPS]!"</p>
      <p class="lp-teacher-says">Teacher: "[Second term stem]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p class="lp-teacher-says">Teacher: "[Third term — software or procedure]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p><em>Run 3 rounds. Keep energy high.</em></p>
    </div>

    <p class="lp-teacher-says"><strong>Closing Statement:</strong><br/>
    "[2 sentences — what was covered today. Connect to digital literacy and creativity.
     {"Preview: " + next_preview if day_num < 4 else "Congratulate students on completing all 4 teaching days."}]"</p>

  </div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ ALL sections covered: {', '.join(day_sections)}
✅ ALL subheadings covered: {', '.join(day_subheadings)}
✅ Every sub-point: read aloud → explanation → real-world analogy → CCQ
✅ Board work present — term+definition OR procedure steps OR block diagram
✅ CCQ questions woven in after every sub-point — minimum 10 total
✅ Activity embedded inside main teaching — not a separate end block
✅ Exit Slip PRESENT — starter on board, students complete in 1 minute
✅ Term Departure Shout PRESENT with 3 rounds — NEVER skip
✅ Student Task PRESENT — define terms + procedure/observation task
✅ Closing PRESENT and COMPLETE
✅ Tamil mirror present after EVERY subheading explanation — Topic 1 AND Topic 2
✅ Tamil also in: Opening Question + Introduction
✅ NO Tamil in: activity instructions, board work headings, closing, homework
✅ No page numbers anywhere
✅ No religious references
✅ No specific student names — "a student" or "Student A" only
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
            print(f"❌ CS LP Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — DAY 5: BOOK-BACK + TERM REVIEW
    # =========================================================================

    def _call_day5(self, text, class_num, unit, lesson_title,
                   sections: dict, day_plan: dict):
        try:
            key_terms    = ", ".join([t for s in sections.get("chapter_sections", [])
                                      for t in s.get("key_terms", [])][:15])
            key_software = ", ".join(sections.get("key_software", []))
            proc_secs    = ", ".join(sections.get("procedure_sections", []))

            all_section_names = [s["heading"] for s in sections.get("chapter_sections", [])]
            day_summaries = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summaries += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"

            prompt = f"""Generate ONLY Day 5 of the Computer Science Lesson Plan.
Day 5 = Book-back Marking → Term and Procedure Review → Closing.
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

KEY TERMS         : {key_terms}
KEY SOFTWARE      : {key_software}
PROCEDURE SECTIONS: {proc_secs}

Generate Day 5 with this structure:

<h3 class="lp-day-title">Day 5 — Book-back Exercises and Chapter Review</h3>

<div class="lp-day-meta">
  <table>
    <tr>
      <th>Learning Objectives</th>
      <td>Evaluate understanding through book-back exercises.
      Consolidate all key terms, software components, and procedures from the chapter.</td>
    </tr>
  </table>
</div>

<div class="lp-day-block">

  <!-- [0-5 min] SPARK — RAPID TERM RECALL -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Opening [0–5 min]</span>
    <h4>Spark — Term Rapid Fire (All 4 Days)</h4>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[Run 5-6 term call-and-response rounds covering ALL 4 days.
     Teacher gives definition or function → Students shout the term.
     Example: 'A visual programming language from MIT is...?' → Students: 'SCRATCH!'
     Use actual terms from this chapter only.]"</p>
  </div>

  <!-- [5-20 min] BOOK-BACK MARKING -->
  <div class="lp-section-main">
    <span class="lp-section-label">Book-back Marking [5–20 min]</span>
    <h4>Book-Back Exercise Marking and Discussion</h4>
    <p class="teacher-role"><em>Teacher facilitates step-by-step marking.
    Students self-mark while teacher explains each answer.
    For procedure questions: go through steps on board.</em></p>
    <p><em>⚠️ All book-back answers available in the QA section of this platform.</em></p>

    <h5>Section 1: Fill in the Blanks / MCQ</h5>
    <p>[For each answer: explain the key CS term being tested.
     Why is this the correct answer? Reference the chapter section.
     Common wrong answers: explain what they confused.]</p>

    <h5>Section 2: Short Answer Questions</h5>
    <p>[For each answer: give model answer structure.
     For procedure questions: write numbered steps on board.
     Students compare and correct their own answers.]</p>

    <div class="board-work">
      <strong>Key Answers on Board:</strong><br/>
      [Write main answers for student verification]
    </div>
  </div>

  <!-- [20-30 min] TERM AND PROCEDURE REVIEW -->
  <div class="lp-section-main">
    <span class="lp-section-label">Term and Procedure Review [20–30 min]</span>
    <h4>Master Term and Procedure Sheet</h4>
    <p class="teacher-role"><em>Teacher writes all chapter key terms on board.
    Students copy into term log at back of notebook.
    Teacher goes through all procedures step by step one last time.</em></p>

    <div class="board-work">
      <strong>Chapter Master Term Sheet:</strong><br/>
      {key_terms if key_terms else "[All key terms from chapter — with one-line definitions]"}<br/>
      <br/>
      <strong>Chapter Procedures (Step-by-Step):</strong><br/>
      {proc_secs if proc_secs else "[All step-by-step procedures from chapter]"}<br/>
      <br/>
      <strong>Software Used:</strong><br/>
      {key_software if key_software else "[All software mentioned in chapter]"}
    </div>

    <h5>Term Memory Check</h5>
    <p>[Students close notebooks. Teacher calls students one by one.
     Each student defines one term from memory. Class checks.
     5-6 students participate. Teacher reinforces wrong definitions.]</p>
  </div>

  <!-- CLOSING -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[Congratulate students on completing the chapter.
     Name 2-3 specific things learned across all 5 days.
     Connect the chapter to digital literacy and everyday technology.
     Motivate for next chapter.]"</p>

    <div class="board-work">
      <strong>All Students Must Submit:</strong><br/>
      ☐ Notebook — all 5 days of notes completed<br/>
      ☐ Key terms defined — all chapter terms with meanings<br/>
      ☐ All procedures written step-by-step in notebook<br/>
      ☐ Book-back exercises answered and marked<br/>
      ☐ All homework tasks from Days 1-4
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="lp-day-title">Day 5
- Book-back section must have real content from chapter
- Term review based on actual chapter terms
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
            print(f"❌ CS LP Day 5 error: {e}")
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
            key_software  = ", ".join(sections.get("key_software", [])[:6])
            proc_secs     = ", ".join(sections.get("procedure_sections", [])[:4])

            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Computer Science chapter.
Do NOT repeat day content. Do NOT generate day blocks.

Chapter       : {lesson_title}
Class         : {class_num}
Unit          : {unit}
All Sections  : {sections_str}
Key Terms     : {key_terms}
Key Software  : {key_software}
Procedures    : {proc_secs}

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
       CS-specific: definition, software component name, procedure step.]
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
       One Why/How/Differentiate question per day from actual chapter content.
       CS-specific: include procedure-based and comparison questions.
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
          <p><strong>Word Bank:</strong> [6 key CS terms from chapter]</p>
          <p><strong>Q2 (3M):</strong> Match CS term to its definition — 3 pairs</p>
          <p><strong>Q3 (5M):</strong> Write the steps to create a file/folder
          (or relevant procedure) — from memory</p>
        </td>
        <td>
          <p><strong>Q1 (3M):</strong> Differentiate between two CS terms from chapter</p>
          <p><strong>Q2 (3M):</strong> Explain a software component and its function</p>
          <p><strong>Q3 (4M):</strong> Write the complete procedure for [chapter task]
          and explain each step</p>
        </td>
        <td>
          <p><strong>Q1 (4M):</strong> Compare two software tools / components from chapter</p>
          <p><strong>Q2 (3M):</strong> Explain how [CS concept] is used in real life
          — give 2 examples</p>
          <p><strong>Q3 (3M):</strong> If you were teaching a friend to use [software],
          what would you tell them? Write a 5-step guide.</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Key Terms Checklist</h3>
  <ul>
    [Each key term from the chapter as a checklist item:
     ☐ [Term]: [one-line definition from chapter text]]
  </ul>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in notebook</li>
    <li>☐ All key terms defined — in own words</li>
    <li>☐ All procedures written step-by-step</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ [One chapter-specific item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Section A table: exactly 5 rows
- Section B table: exactly 5 rows with Tamil column
- Differentiated worksheet: 3 columns with visible 2px border
- Key Terms checklist: every term from chapter with definition
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
            print(f"❌ CS LP assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

cs_lp_910_builder = ComputerScienceLP910Builder()