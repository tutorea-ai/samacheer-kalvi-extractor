"""
biology.py
----------
LP Builder for Samacheer Kalvi Science — Biology
Class 8, 9 & 10

v1.0 — May 2026
Built to match teacher-approved manual LP reference
(Biology: Plant Anatomy and Plant Physiology)
Modeled on ss/lp/grade_910/history.py structure.

REFERENCE: Manual LP "Plant Anatomy and Plant Physiology" — Grade 10 Biology
           Built by TNQ/Tutorea.ai teacher team — used as gold standard

KEY DIFFERENCES FROM CHEMISTRY LP:
  - Spark: Prop-driven + dramatic reveal (celery, pencils, leaf, battery)
  - Board work: Cross-section sketches, comparison tables, diagram builders
  - Student activity: Microscopic Detective, diagram labeling, structural classification
  - Closing: Synthesis sentence + Final Departure Shout
  - No formula calculation days — structure, function, comparison, classification

STRUCTURE PER DAY (matches manual LP exactly):
  [0-5 min]   Spark / Prop Hook
              → Teacher brings a real prop or describes a dramatic visual
              → Big Question connecting prop to today's biology concept
              → Real-life use — where will students use this?
              → 2-3 student guesses before teacher reveals focus
              → Day 2+: starts with previous day rapid recap

  [5-10 min]  Introduction
              → Teacher explains today's concept in simple words
              → Concept map or structural chain written on board
              → Key terms table (English + Tamil meaning)
              → 1 CCQ from the introduction

  [10-20 min] Main Teaching — Topic 1
              → Live Drawing Session on board (cross-sections, diagrams)
              → Structural analogy per sub-point
              → Comparison table (Dicot vs Monocot etc.) built live
              → CCQs woven in after each sub-point

  [20-30 min] Main Teaching — Topic 2
              → Same pattern — diagram + analogy + CCQ
              → Day-specific student activity embedded

  [30-35 min] Closing
              → Students write synthesis sentence (Biology-style)
              → Final Departure Shout (2-3 rounds)
              → Student Task: diagram + comparison table homework
              → Day 5: submission checklist

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
# BIOLOGY TEACHING STRATEGY PER DAY
# Prop-driven sparks, diagram building, microscopic detective, synthesis closing
# ============================================================================

BIOLOGY_DAY_STRATEGY = {
    1: {
        "spark_style": "Prop Reveal + Dramatic Question",
        "spark_instruction": (
            "Teacher brings a real everyday prop OR describes a dramatic visual "
            "that directly connects to today's biology concept.\n"
            "Examples from teacher LP:\n"
            "  - Celery stalk in red food coloring — snapped open dramatically\n"
            "  - Fresh mango/hibiscus leaf — flip it, compare both sides\n"
            "  - Dead battery vs charged phone — photosynthesis vs respiration\n"
            "Structure:\n"
            "  Step 1: Hold up or describe the prop dramatically.\n"
            "  Step 2: 'Class, look closely at this. How does [observation] happen\n"
            "           without [expected mechanism]?'\n"
            "  Step 3: Big Question — connects prop to today's concept.\n"
            "  Step 4: Real-life use — agriculture, medicine, environment.\n"
            "Allow 2-3 student guesses. Acknowledge each without revealing answer."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Concept Map Builder + Live Diagram Drawer\n"
            "Step 1: Write a rapid organizational chain on board:\n"
            "        [Term 1] → [Term 2] → [Term 3] → [Term 4]\n"
            "        Build it horizontally as you explain each level.\n"
            "Step 2: Read the section aloud from textbook — sentence by sentence.\n"
            "Step 3: After each sub-point STOP and explain using a structural analogy.\n"
            "        Example style: 'Think of it like a high-tech building where...'\n"
            "                       'Just like a security guard at a checkpoint...'\n"
            "Step 4: Draw the diagram or cross-section on board WHILE explaining.\n"
            "        Label each part as you draw — not after.\n"
            "Step 5: Ask 1-2 CCQ questions mid-explanation after each sub-point."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Live Drawing Session Facilitator\n"
            "Step 1: Draw two contrasting diagrams side by side on board.\n"
            "        Example: Radial vs Conjoint bundles / Dicot vs Monocot\n"
            "Step 2: Label each part as you explain — build the comparison visually.\n"
            "Step 3: Ask 2 students to come and label one part each on the board.\n"
            "Step 4: Students copy both diagrams into their notebooks with labels.\n"
            "        Teacher circulates and checks labeling accuracy."
        ),
        "activity": (
            "STRUCTURAL HIERARCHY CHAIN ACTIVITY (Day 1):\n"
            "Teacher writes the chain on board:\n"
            "Atoms → Molecules → Organelles → Cells → Tissues → Organs\n"
            "Students copy into notebook.\n"
            "Teacher asks: 'What level sits between organelles and tissues?'\n"
            "Students write answer on scrap paper. Teacher reveals: 'Cells!'\n"
            "Then students stand up and form a human chain —\n"
            "each student calls out one level in order.\n"
            "Class repeats the full chain three times aloud together.\n"
            "After the chain: students write the 3 tissue systems from Sachs'\n"
            "classification with one function each — in their notebooks.\n"
            "⚠️ Structural Hierarchy Chain is used ONLY on Day 1 — not repeated."
        ),
        "closing_shout": (
            "Final Departure Shout — Biology style:\n"
            "Teacher gives structural term stem → Students shout classification.\n"
            "Example: 'Bicycle wheel layout in roots is...?' → Students: 'RADIAL!'\n"
            "Run 2-3 rounds from today's key structural terms."
        ),
        "synthesis_sentence": (
            "Students write ONE comprehensive synthesis sentence in their notebooks\n"
            "connecting all of today's structural concepts together.\n"
            "Teacher writes the sentence starter on board:\n"
            "'[Today's Topic 1 term] organizes plants into [classification], while\n"
            " [Today's Topic 2 term] shows [structural contrast]...'\n"
            "Students complete it in their own words — 2-3 minutes."
        ),
    },
    2: {
        "spark_style": "Contrasting Props + Structural Puzzle",
        "spark_instruction": (
            "Teacher displays TWO contrasting objects that mirror today's structural contrast.\n"
            "Examples from teacher LP:\n"
            "  - Bundle of neatly tied colored pencils (ring arrangement)\n"
            "    vs box of loose scattered toothpicks (scattered bundles)\n"
            "  - Orderly vs chaotic — connects to Dicot vs Monocot structure\n"
            "Structure:\n"
            "  Step 1: Display both objects side by side.\n"
            "  Step 2: 'If we slice open a plant, its internal layout is either like\n"
            "           [Object A] or [Object B]. This tells us exactly what class of\n"
            "           plant we are looking at.'\n"
            "  Step 3: Big Question + Real-life use (agriculture, grafting, disease).\n"
            "  Step 4: 1-minute recap of yesterday's key terms before proceeding.\n"
            "Allow 2-3 student guesses."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Security Guard Analogy + Pathway Sketch\n"
            "Step 1: Sketch the pathway / journey on board as a flow diagram.\n"
            "        Example: Root Hair → Cortex → Endodermis → Pericycle → Xylem\n"
            "Step 2: Use a journey analogy — water drop traveling through checkpoints.\n"
            "        'At this checkpoint, the security wall [structure] does [function].'\n"
            "Step 3: Explain each structure's role — read aloud from textbook.\n"
            "Step 4: Label each checkpoint on the board diagram as you explain.\n"
            "Step 5: 2 CCQ questions after each checkpoint."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Symbolic Blueprint Comparator\n"
            "Step 1: Draw two cross-sections side by side — Dicot vs Monocot.\n"
            "Step 2: Point out visual differences one by one — build the table live.\n"
            "        Write a comparison table on board: Feature | Dicot | Monocot\n"
            "Step 3: Fill one row at a time as you explain each difference.\n"
            "Step 4: Students copy table — must have at least 4 rows completed.\n"
            "Step 5: 'Microscopic Detective' check — teacher describes a mystery slide,\n"
            "        students identify Dicot or Monocot based on the table."
        ),
        "activity": (
            "MICROSCOPIC DETECTIVE — STRUCTURAL CLASSIFICATION (Day 2):\n"
            "Teacher describes 4 mystery plant slides one by one — no diagrams shown.\n"
            "Students write their classification in notebook for each slide.\n"
            "Use ONLY clues from the actual chapter text — never invent features.\n"
            "Example slide clues (adapt to today's actual chapter content):\n"
            "  Slide 1: 'Cross-section shows star-shaped xylem with 4 arms, no central pith.'\n"
            "           → Answer: Dicot Root (Tetrarch, pith absent)\n"
            "  Slide 2: 'Vascular bundles scattered randomly, each shaped like a skull,\n"
            "            protoxylem lacuna visible at base.' → Answer: Monocot Stem\n"
            "  Slide 3: 'Open collateral bundles arranged in a ring, cambium strip present.'\n"
            "           → Answer: Dicot Stem\n"
            "  Slide 4: 'Polyarch xylem with many alternating patches, large central pith.'\n"
            "           → Answer: Monocot Root\n"
            "Generate slide clues from TODAY'S actual chapter sections — not these examples.\n"
            "After 3 minutes: teacher reveals correct answers one by one.\n"
            "Students mark their own work. Discuss any wrong classifications.\n"
            "⚠️ Microscopic Detective is used ONLY on Day 2 — not repeated."
        ),
        "closing_shout": (
            "Final Departure Shout — Dicot vs Monocot:\n"
            "Teacher gives structural clue → Students shout Dicot or Monocot.\n"
            "Example: 'Open bundles in a ring...' → Students: 'DICOT STEM!'\n"
            "         'Scattered skull-shaped bundles...' → Students: 'MONOCOT STEM!'\n"
            "Run 3 rounds from today's comparison table."
        ),
        "synthesis_sentence": (
            "Students write ONE comprehensive synthesis sentence connecting\n"
            "today's root and stem structural contrasts.\n"
            "Teacher writes the sentence starter on board:\n"
            "'Roots use [layout] where water passes through [filter], whereas\n"
            " stems use [layout] where dicots [pattern] while monocots [pattern]...'\n"
            "Students complete in their own words — 2 minutes."
        ),
    },
    3: {
        "spark_style": "Living Object Comparison + Observation Hook",
        "spark_instruction": (
            "Teacher holds up a real leaf OR describes a vivid visual observation\n"
            "that immediately connects to today's leaf/cell biology concept.\n"
            "Examples from teacher LP:\n"
            "  - Hold a fresh mango/hibiscus leaf — flip it, compare both sides\n"
            "  - 'Why is the top dark glossy green and the bottom pale and rough?'\n"
            "  - 'Nature designed this leaf with two completely different faces — why?'\n"
            "Structure:\n"
            "  Step 1: Hold up the object or describe the observation dramatically.\n"
            "  Step 2: Ask students to observe and describe what they notice.\n"
            "  Step 3: Big Question connecting observation to today's biology.\n"
            "  Step 4: Real-life use — solar energy, photosynthesis, food production.\n"
            "  Step 5: 1-minute recap of yesterday's key structural terms."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Structural Contrast Session Facilitator\n"
            "Step 1: Draw a comparative cross-section of both types on board.\n"
            "        Label each anatomical landmark clearly as you draw.\n"
            "Step 2: Explain each zone/layer — read aloud from textbook.\n"
            "Step 3: Use color-coding or visual markers to distinguish layers.\n"
            "        Example: 'Palisade = tightly packed columns → maximum light trap'\n"
            "Step 4: Build a comparison table live: Feature | Type A | Type B\n"
            "Step 5: 2 CCQ questions after each structural zone."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Step-by-Step Diagram Builder\n"
            "Step 1: Draw a large, clean outline on the board — oval or rectangle.\n"
            "Step 2: Add internal sub-compartments ONE AT A TIME as you explain.\n"
            "        Name and label each part before adding the next.\n"
            "Step 3: Use spatial memory anchors:\n"
            "        'The outer part is [name] — think of it as [analogy].'\n"
            "        'The inner part is [name] — its job is [function].'\n"
            "Step 4: Students copy diagram with labels into notebook.\n"
            "Step 5: 2 CCQ questions on structure-function relationships."
        ),
        "activity": (
            "DIAGRAM LABELING RACE (Day 3):\n"
            "Teacher draws a blank, unlabeled CHLOROPLAST on board —\n"
            "large oval outline only, no internal structures shown.\n"
            "Students must label as many parts as they can in 3 minutes — in their notebooks.\n"
            "Labels to find (from chapter text only — no invented structures):\n"
            "  outer membrane, inner membrane, stroma, thylakoid,\n"
            "  granum, stroma lamella, chloroplast DNA, 70S ribosome\n"
            "Use ONLY labels that appear in the actual chapter text.\n"
            "After 3 minutes: teacher calls students one by one to label one part on board.\n"
            "Class checks each label. Teacher corrects any wrong labels.\n"
            "Highest scorer gets recognition.\n"
            "⚠️ Diagram Labeling Race is used ONLY on Day 3 — not repeated."
        ),
        "closing_shout": (
            "Final Departure Shout — Structure and Function:\n"
            "Teacher gives organelle/structure name → Students shout function.\n"
            "Example: 'Grana inside chloroplast does...?' → Students: 'LIGHT REACTION!'\n"
            "         'Stroma inside chloroplast does...?' → Students: 'DARK REACTION!'\n"
            "Run 3 rounds from today's diagram labels."
        ),
        "synthesis_sentence": (
            "Students write ONE comprehensive synthesis sentence connecting\n"
            "today's leaf anatomy and organelle ultrastructure.\n"
            "Teacher writes the sentence starter on board:\n"
            "'While [Type A leaf] organizes its [structure] into [zones],\n"
            " [Type B leaf] uses [structure] to [function], and both cook\n"
            " food inside the [organelle] using [part A] and [part B]...'\n"
            "Students complete in their own words — 2 minutes."
        ),
    },
    4: {
        "spark_style": "Dead Object vs Alive Object + Energy Hook",
        "spark_instruction": (
            "Teacher brings two contrasting objects — one dead/empty, one alive/charged.\n"
            "Examples from teacher LP:\n"
            "  - Dead battery vs fully charged phone\n"
            "  - 'Living cells do the exact same thing as charging a phone!'\n"
            "  - 'Plants run a solar-charging station. Mitochondria run the power plant.'\n"
            "Structure:\n"
            "  Step 1: Hold up both objects — dead vs alive/charged.\n"
            "  Step 2: 'This [dead object] has no energy. This [charged object] is full.\n"
            "           Living cells do the same thing — how?'\n"
            "  Step 3: Big Question + Real-life use (food, oxygen, metabolism).\n"
            "  Step 4: 1-minute rapid recap of Days 1-3 key terms — call-and-response.\n"
            "Allow 2-3 student guesses before revealing today's focus."
        ),
        "topic1_strategy": (
            "TEACHER ROLE: Dual-Phase Assembly Line Explainer\n"
            "Step 1: Write the two phases on board as a split diagram:\n"
            "        Phase 1: [Location] → [Inputs] → [Outputs]\n"
            "        Phase 2: [Location] → [Inputs] → [Outputs]\n"
            "Step 2: Explain each phase from textbook — read aloud + explain.\n"
            "Step 3: Draw the organelle diagram and mark where each phase occurs.\n"
            "Step 4: Write the balanced chemical equation on board — explain each term.\n"
            "Step 5: 2 CCQ questions on phase locations and inputs/outputs."
        ),
        "topic2_strategy": (
            "TEACHER ROLE: Three-Step Disassembly Line Tracer\n"
            "Step 1: Write the 3 stages as a numbered sequence on board:\n"
            "        Stage 1 → Stage 2 → Stage 3\n"
            "        Under each: Location | Inputs | Outputs | ATP produced\n"
            "Step 2: Explain each stage — read from textbook + explain with analogy.\n"
            "Step 3: For RQ calculation: write formula on board, solve one example.\n"
            "        Given → Formula → Substitution → Answer (same as worked example)\n"
            "Step 4: Students solve one RQ parallel problem — 3 minutes.\n"
            "Step 5: 2 CCQ questions on stage locations and outputs."
        ),
        "activity": (
            "BIOENERGETICS RAPID WORKSHEET (Day 4):\n"
            "Teacher writes 4 quick-check questions on board from today's content.\n"
            "Students solve them in notebooks — 4 minutes, test conditions.\n"
            "Questions must cover: equation, location, stage identification, RQ if applicable.\n"
            "After 4 minutes: teacher reads answers one by one.\n"
            "Students self-mark. Students who got all 4 correct explain one answer to class.\n"
            "⚠️ Bioenergetics Rapid Worksheet is used ONLY on Day 4 — not repeated."
        ),
        "closing_shout": (
            "Final Departure Shout — Process and Location:\n"
            "Teacher gives process name → Students shout location.\n"
            "Example: 'Light Reaction occurs in...?' → Students: 'THYLAKOID / GRANA!'\n"
            "         'Krebs Cycle occurs in...?' → Students: 'MITOCHONDRIAL MATRIX!'\n"
            "         'Glycolysis occurs in...?' → Students: 'CYTOPLASM!'\n"
            "Run 3-4 rounds covering all 4 days of content."
        ),
        "synthesis_sentence": (
            "Students write ONE comprehensive synthesis sentence connecting\n"
            "photosynthesis and respiration as a circular energy loop.\n"
            "Teacher writes the sentence starter on board:\n"
            "'While Photosynthesis takes place inside the [organelle] to [function]\n"
            " using [reaction] in the [location], Aerobic Respiration splits that\n"
            " [molecule] via [stage] and strips its energy within [location] to\n"
            " manufacture [product]...'\n"
            "Students complete in their own words — 2 minutes."
        ),
    },
}


# ============================================================================
# BIOLOGY LP BUILDER CLASS
# ============================================================================

class BiologyLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Biology LP Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        print(f"      [Biology LP 910 v1.0] Generating: {lesson_title}")
        print(f"      [Biology LP 910 v1.0] 9 API calls: 0a+0b+Preamble+Day1-4+Day5+Assessment")

        parts = []

        # Call 0a
        print(f"      [Biology LP] Call 0a/9: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('chapter_sections', []))} sections")

        # Call 0b
        print(f"      [Biology LP] Call 0b/9: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        print(f"         ✅ Day plan ready:")
        for d in range(1, 5):
            day_sections = day_plan.get(f"day{d}", {}).get("sections", [])
            print(f"            Day {d}: {', '.join(day_sections)}")

        # Call 1
        print(f"      [Biology LP] Call 1/9: Preamble...")
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
            print(f"      [Biology LP] Call {call_num}/9: Day {day_num}...")
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
        print(f"      [Biology LP] Call 6/9: Day 5...")
        day5_html = self._call_day5(text, class_num, unit, lesson_title, sections, day_plan)
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # Call 7: Assessment
        print(f"      [Biology LP] Call 7/9: Assessment...")
        assessment = self._call_assessment(text, class_num, unit, lesson_title, sections, day_plan)
        if assessment:
            parts.append(clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Biology LP 910 v1.0] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""Extract ALL headings and subheadings from this Biology chapter.

Chapter: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "chapter_sections": [
    {{
      "heading": "EXACT heading as written in text",
      "subheadings": ["subheading 1", "subheading 2"],
      "estimated_teaching_time_mins": 10
    }}
  ],
  "total_estimated_teaching_mins": 70
}}

RULES:
- Copy EVERY heading EXACTLY as written
- Do NOT skip any heading
- A 30000+ char chapter must have at least 8-15 sections
- Keep JSON minimal — no extra fields
- Return ONLY the JSON object — nothing else

Chapter Text:
---
{text}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system="""You are a strict text extractor. Return ONLY valid JSON.
Extract ALL headings — minimum 8 sections for a full chapter.
Keep JSON minimal and compact. No markdown. No code fences. Raw JSON starting with {""",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()

            # Safety — truncate at last valid closing bracket
            last_bracket = raw.rfind('}')
            if last_bracket != -1:
                raw = raw[:last_bracket + 1]

            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"❌ Section Extractor JSON error: {e}")
            # Return minimal fallback so LP doesn't abort
            return {
                "chapter_sections": [
                    {"heading": lesson_title, "subheadings": [], "estimated_teaching_time_mins": 70}
                ],
                "total_estimated_teaching_mins": 70
            }
        except Exception as e:
            print(f"❌ Section Extractor error: {e}")
            return None

    # =========================================================================
    # CALL 0b — DAY ALLOCATOR
    # =========================================================================

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        try:
            sections_str = json.dumps(sections, indent=2)
            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Biology lesson plan.

Allocate ALL sections AND subheadings to exactly 4 days.

RULES:
- Each day: 20-25 minutes of content (35 min session minus 10 min opening/closing)
- Keep each main section in ONE day — do NOT split across days
- Keep subheadings WITH their main section
- EVERY section AND subheading must appear in exactly ONE day
- MAXIMUM 3 subheadings per day — if a section has more, split across 2 days
- Sections with diagrams should be grouped together where possible
- Comparison sections (Dicot vs Monocot etc.) must stay on the SAME day
- Process sections (Photosynthesis, Respiration steps) must stay on the SAME day
- Sections must follow STRICT ORDER from the chapter text — never rearrange
- NEVER assign the same section to two different days
- Use EXACT heading text from extracted sections

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "day1": {{
    "sections": ["EXACT heading 1", "EXACT heading 2"],
    "subheadings": ["EXACT subheading 1", "EXACT subheading 2"],
    "focus": "One sentence — what Day 1 covers",
    "has_diagram": true,
    "has_comparison": false,
    "has_process": false,
    "estimated_mins": 22
  }},
  "day2": {{
    "sections": ["EXACT heading 3"],
    "subheadings": ["EXACT subheading 3", "EXACT subheading 4"],
    "focus": "One sentence — what Day 2 covers",
    "has_diagram": true,
    "has_comparison": true,
    "has_process": false,
    "estimated_mins": 20
  }},
  "day3": {{
    "sections": ["EXACT heading 4", "EXACT heading 5"],
    "subheadings": ["EXACT subheading 5", "EXACT subheading 6"],
    "focus": "One sentence — what Day 3 covers",
    "has_diagram": true,
    "has_comparison": false,
    "has_process": false,
    "estimated_mins": 23
  }},
  "day4": {{
    "sections": ["EXACT heading 6", "EXACT heading 7"],
    "subheadings": ["EXACT subheading 7", "EXACT subheading 8"],
    "focus": "One sentence — what Day 4 covers — physiology and processes",
    "has_diagram": true,
    "has_comparison": false,
    "has_process": true,
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

            key_terms      = ", ".join([t for s in sections_list for t in s.get("key_terms", [])][:12])
            key_structures = ", ".join(sections.get("key_structures", [])[:10])

            prompt = f"""Generate ONLY the preamble section of this Biology Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Biology
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

ALL CHAPTER SECTIONS (extracted from text):
{sections_str}

DAY-WISE PLAN:
{day_summary}

KEY TERMS      : {key_terms}
KEY STRUCTURES : {key_structures}

Generate EXACTLY these sections in this order:

<h2>Part 1: Chapter Overview</h2>
Table: Class | Subject | Discipline | Unit/Chapter Title | Month |
       Total Teaching Hours | Session Duration | Main Sections Covered

<h2>Part 2: Learning Objectives</h2>
4-5 SWBAT objectives with action verbs (Identify, Classify, Sketch, Explain, Differentiate)
Based ONLY on actual sections in this chapter — match teacher LP style exactly
Biology-specific: include microscopic detective, diagram labeling, process mapping

<h2>Part 3: Value-Based Objectives</h2>
3-4 value objectives based on actual chapter content:
  e.g. Admire division of labor in plant cells, Connect plant physiology to human survival,
  Respect nature's engineering, Appreciate zero-waste circular design of biology

<h2>Part 4: Skill Objectives</h2>
4 skill objectives: Diagram Labeling, Comparative Table Building,
Microscopic Detective (structural identification), Process Flow Mapping
Customised to this chapter's actual content

<h2>Part 5: Teaching Aids</h2>
All materials: board, chalk, real props (leaves, celery, objects),
colored chalk for diagram work, comparison charts, textbooks, notebooks
Based on actual chapter content — Biology-specific props mentioned

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
            print(f"❌ Biology LP preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2-5 — CONTENT DAYS 1-4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict):
        try:
            strategy = BIOLOGY_DAY_STRATEGY[day_num]

            day_sections    = day_data.get("sections", [])
            day_subheadings = day_data.get("subheadings", [])
            day_focus       = day_data.get("focus", "")
            has_diagram     = day_data.get("has_diagram", True)
            has_comparison  = day_data.get("has_comparison", False)
            has_process     = day_data.get("has_process", False)

            # Collect key terms and structures for this day
            all_sections      = sections.get("chapter_sections", [])
            day_key_terms     = []
            day_key_structures = []
            for s in all_sections:
                if s["heading"] in day_sections:
                    day_key_terms.extend(s.get("key_terms", []))
                    day_key_structures.extend(s.get("key_structures", []))

            sections_str       = "\n".join([f"  ▸ {s}" for s in day_sections])
            subheadings_str    = "\n".join([f"      • {s}" for s in day_subheadings])
            key_terms_str      = ", ".join(day_key_terms[:10])
            key_structures_str = ", ".join(day_key_structures[:8])

            # Next day preview
            if day_num < 4:
                next_data     = day_plan.get(f"day{day_num + 1}", {})
                next_sections = next_data.get("sections", [])
                next_preview  = f"Day {day_num + 1}: {', '.join(next_sections)}"
            else:
                next_preview  = "Day 5: Book-back Exercises + Diagram Review"

            # Day-type specific notes
            diagram_note = ""
            if has_diagram:
                diagram_note = """
DIAGRAM DAY NOTE:
This day requires board diagrams. For every main structure:
  Step 1: Draw the outline first — large and clear
  Step 2: Add internal parts one at a time while explaining
  Step 3: Label each part AS you draw it — not after
  Step 4: Students copy diagram with labels into notebook
  Step 5: Teacher checks 3-4 notebooks for labeling accuracy
Never describe a diagram in words only — always draw it on board.
"""

            comparison_note = ""
            if has_comparison:
                comparison_note = """
COMPARISON DAY NOTE:
This day requires a live comparison table on board.
  Format: | Feature | Type A | Type B |
  Build one row at a time as you explain each difference.
  Minimum 4 rows in the table.
  Students copy the complete table into notebook.
  After table: run Microscopic Detective activity.
"""

            process_note = ""
            if has_process:
                process_note = """
PROCESS DAY NOTE:
This day contains step-by-step biological processes.
For each process:
  Step 1: Write the process name and location on board
  Step 2: Draw inputs → process → outputs as a flow diagram
  Step 3: Write balanced equation if applicable (from textbook only)
  Step 4: Explain each step from textbook — read aloud + explain
  Step 5: Students copy the flow diagram into notebook
Never skip the flow diagram. Never invent equations.

IF THIS DAY CONTAINS RESPIRATORY QUOTIENT (RQ):
Include this exact worked example block in Topic 2 board work:

<div class="worked-example">
  <strong>Worked Example — Respiratory Quotient (RQ):</strong>
  <p><strong>Given:</strong> Volume of CO₂ liberated = [value from textbook], Volume of O₂ consumed = [value from textbook]</p>
  <p><strong>Formula:</strong> RQ = Volume of CO₂ liberated ÷ Volume of O₂ consumed</p>
  <p><strong>Substitution:</strong> RQ = [value] ÷ [value] = [result]</p>
  <p><strong>Answer:</strong> RQ = [result] (no units — it is a ratio)</p>
</div>
<p><em>Students then solve a parallel RQ problem using different values from the textbook — 3 minutes.</em></p>

Use ONLY values that appear in the chapter text — never invent numbers.
"""

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi Biology Lesson Plan.

REFERENCE STYLE: Match the teacher-approved manual LP style exactly.
The manual LP style is:
  - Prop-driven dramatic spark (celery stalk, leaves, pencils, battery)
  - Live diagram drawing on board — build step by step with labels
  - Structural analogies (security guard, high-tech building, assembly line)
  - Comparison tables built live (Dicot vs Monocot)
  - Students label diagrams, classify structures, write synthesis sentences
  - Final Departure Shout to close the day
  - Script-level detail so any new teacher can follow

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Science — Biology
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S SECTIONS — COVER ALL IN ORDER
═══════════════════════════════════════════════════════
Main sections:
{sections_str}

Subheadings (ALL must be taught):
{subheadings_str}

Day Focus       : {day_focus}
Key Terms       : {key_terms_str}
Key Structures  : {key_structures_str}
{diagram_note}{comparison_note}{process_note}
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
   - Add a structural analogy for EACH sub-point
     Examples: "Think of it like a high-tech building where each floor has a job..."
               "Just like a security guard at a checkpoint, this layer filters..."
               "Imagine a solar panel factory — this part captures, that part converts..."
   - Use Indian agricultural / everyday context examples wherever possible
   - Explanation must be detailed enough that a new teacher can follow it exactly

3. CCQ QUESTIONS (woven into explanation — not separate blocks):
   - After EACH sub-point explanation: ask 1-2 CCQ questions
   - Write CCQ questions on board
   - Students answer by raising hands or calling out
   - Biology CCQs must test structure-function relationships
   - Use the exact CCQ HTML format from CCQ_INSTRUCTION

4. BOARD WORK — DIAGRAMS MANDATORY:
   - Every main biological structure must be drawn on board
   - Draw outline → add parts → label — build step by step
   - Comparison tables built live — one row at a time
   - Process flows drawn as input → process → output diagrams
   - Students copy ALL diagrams and tables into notebooks

5. STUDENT ACTIVITY:
   - Activity EMBEDDED inside main teaching — not a separate block at the end
   - Use the day-specific activity: {strategy['activity'].split(chr(10))[0]}

6. SYNTHESIS SENTENCE — MANDATORY EVERY DAY:
   - Before the Final Departure Shout: students write ONE synthesis sentence
   - Teacher writes the sentence starter on board
   - Students complete it in their own words — 2 minutes
   - This is a Biology-specific closing — not used in Chemistry

7. FINAL DEPARTURE SHOUT — MANDATORY EVERY DAY:
   - End EVERY day with call-and-response
   - Teacher gives structure/process name → Students shout function/classification
   - Run 2-3 rounds from today's key terms
   - Format: Teacher: "[term/structure]...?" → Students: "[ANSWER IN CAPS]!"

{TAMIL_INSTRUCTION}

{CCQ_INSTRUCTION}

8. NO PAGE NUMBERS:
   - Do NOT mention any page numbers anywhere
   - Reference content by section/topic name only

9. NO RELIGIOUS REFERENCES:
   - NEVER use religious examples in any analogy
   - Use nature, agriculture, engineering, everyday objects

10. NO SPECIFIC STUDENT NAMES:
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

SYNTHESIS SENTENCE STARTER:
{strategy['synthesis_sentence']}

CLOSING SHOUT:
{strategy['closing_shout']}
═══════════════════════════════════════════════════════

GENERATE Day {day_num} using EXACTLY this HTML structure:

<h3 class="lp-day-title">Day {day_num} — [Exact section names taught today]</h3>

<div class="lp-day-meta">
  <table>
    <tr>
      <th>Learning Objective</th>
      <td>[Specific SWBAT objective for today — action verb + biological concept]</td>
      <th>Focus</th>
      <td>{day_focus}</td>
    </tr>
  </table>
</div>

<div class="lp-day-block">

  <!-- ═══ [0-5 min] SPARK / PROP HOOK ═══ -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Opening [0–5 min]</span>
    <h4>Spark — {strategy['spark_style']}</h4>

    {"<!-- Day 2+: Start with previous day recap -->" if day_num > 1 else ""}
    {"<p class='lp-teacher-says'><strong>Quick Recap (1 min):</strong> Teacher asks 2-3 rapid questions from yesterday. Students call out answers. Example: 'What are Sachs' three tissue systems?' No writing needed.</p>" if day_num > 1 else ""}

    <p class="lp-teacher-says"><strong>Teacher says (Prop + Dramatic Reveal):</strong><br/>
    "[{strategy['spark_style']} — describe the prop or visual clearly.
     Teacher holds up / displays the prop dramatically.
     'Class, look at this. [Dramatic observation connecting to today's biology concept.]
     How does [observation] happen without [expected mechanism]?'
     Connects directly to today's sections: {', '.join(day_sections)}.
     Ends with a Big Question.]"</p>

    <p class="lp-tamil-scaffold"><em>தமிழில்:</em>
    "[Same opening question in Tamil — context-based, natural Tamil]"</p>

    <p class="lp-teacher-says"><strong>Teacher then says (Real-life Connection):</strong><br/>
    "[Why are we learning this? Connect today's biology concept to ONE specific
     real-world application — agriculture, medicine, environment, food production.
     Keep it to 2-3 sentences. Make students feel the importance.]"</p>

    <p><em>Allow 2-3 student guesses. Teacher acknowledges without revealing answer yet.</em></p>

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
      <strong>Write on Board — Concept Chain:</strong><br/>
      [Write a rapid organizational chain horizontally:]<br/>
      [Term 1] → [Term 2] → [Term 3] → [Term 4]<br/>
      Topic: [today's section names]<br/>
      Objective: [today's SWBAT in one line]
    </div>

    <p class="lp-teacher-says"><strong>Teacher says (Introduction — English):</strong><br/>
    "[Teacher introduces today's biological concept in simple words — 3-4 sentences.
     One structural analogy connecting to the concept.
     Example: 'Just like a high-tech building where each floor has a specific job,
     a plant is organized into [today's systems/structures]...'
     Connect back to the prop from the spark.]"</p>

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
          [5-6 key biological terms from today's sections with clear meanings and Tamil.
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
     STRUCTURAL ANALOGY: 'Think of it like [specific structural comparison]...'
     Include specific biological terms and structures from the textbook.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[EXACT same explanation in Tamil — sentence by sentence mirror.
          Same length. Same detail. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word.
          Pure Tamil Unicode — no Hindi words.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board (step by step while explaining):</strong><br/>
      [Draw the structure/cross-section/diagram for this sub-point]<br/>
      [Label each part AS you draw — not after]<br/>
      {"[Build comparison table: | Feature | " + " | ".join(day_subheadings[:2]) + " |]" if has_comparison else "[Draw flow diagram or structural outline]"}
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Short structure-function question — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[One structure or function]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Classification or identification question — under 8 words]?"</p>
      <p class="student-says"><strong>Expected:</strong> "[Classification answer]"</p>
      <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    </div>

    [REPEAT the subheading block for each subheading under section 1]

    <!-- Embedded Activity for Topic 1 -->
    <div class="activity-block">
      <strong>⚙️ Activity ({strategy['activity'].split(chr(10))[0]}):</strong>
      <p>[Step by step activity instructions.
         Based ONLY on today's section content.
         Students are active — labeling, classifying, identifying, writing.]</p>
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
     STRUCTURAL ANALOGY: [specific analogy for this sub-point].
     Specific biological terms and structures from text.]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[EXACT same explanation in Tamil — sentence by sentence mirror.
          Same length. Same detail. Same analogy in Tamil.
          Context-based Tamil — NOT word-for-word.
          Pure Tamil Unicode only.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      [Draw or extend the diagram for this sub-point]<br/>
      [Add labels as you explain — build the complete picture]
    </div>

    <div class="ccq-block">
      <strong>⚡ CCQ (Concept Check):</strong>
      <p class="lp-teacher-says">"[Structure or function question — under 8 words]?"</p>
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
      Task 1: [Diagram task — sketch and label [today's main structure] from memory]<br/>
      Task 2: [Comparison task — write a table comparing [Type A] vs [Type B]
               from today's content OR write a synthesis sentence connecting today's concepts]<br/>
      Submit: Tomorrow morning
    </div>
  </div>

  <!-- ═══ [30-35 min] CLOSING — MANDATORY — NEVER SKIP ═══ -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>

    <div class="board-work">
      <strong>Key Points on Board{"" if day_num < 4 else " (Full Chapter Summary)"}:</strong><br/>
      1. [Key structure or term 1 from today]<br/>
      2. [Key structure or term 2 from today]<br/>
      3. [Key function or process from today]<br/>
      {"4. [Key point 4]<br/>5. [Key point 5]" if day_num == 4 else ""}
    </div>

    <!-- SYNTHESIS SENTENCE — Biology-specific closing -->
    <div class="synthesis-block">
      <strong>✍️ Synthesis Sentence (Biology Closing):</strong>
      <p><em>Teacher writes the sentence starter on board.
      Students complete it in their own words — 2 minutes.</em></p>
      <div class="board-work">
        <strong>Write on Board (sentence starter):</strong><br/>
        "[Sentence starter from today's key concepts — connecting Topic 1 and Topic 2]..."
      </div>
      <p><em>2-3 students read their sentence aloud. Teacher gives 1-line feedback each.</em></p>
    </div>

    <!-- FINAL DEPARTURE SHOUT -->
    <div class="departure-shout">
      <strong>🔊 Final Departure Shout:</strong>
      <p><em>Teacher gives structure/process name → Students shout function/classification ALOUD.</em></p>
      <p class="lp-teacher-says">Teacher: "[Key structure or term from today]...?"</p>
      <p class="student-says">Students: "[FUNCTION OR CLASSIFICATION IN CAPS]!"</p>
      <p class="lp-teacher-says">Teacher: "[Second key term from today]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p class="lp-teacher-says">Teacher: "[Third term — structure or process]...?"</p>
      <p class="student-says">Students: "[ANSWER IN CAPS]!"</p>
      <p><em>Run 3 rounds. Keep energy high.</em></p>
    </div>

    <p class="lp-teacher-says"><strong>Closing Statement:</strong><br/>
    "[2 sentences — what was covered today. Connect to bigger picture of biology.
     {"Preview what comes next: " + next_preview if day_num < 4 else "Congratulate students on completing all 4 teaching days."}]"</p>

  </div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ ALL sections covered: {', '.join(day_sections)}
✅ ALL subheadings covered: {', '.join(day_subheadings)}
✅ EVERY subheading has full explanation — nothing summarised or skipped
✅ Every sub-point has: read aloud → explanation → structural analogy → CCQ
✅ Board diagram drawn for every main structure — with labels
✅ CCQ questions woven in after every sub-point — minimum 10 total
✅ Activity embedded inside main teaching — not a separate end block
✅ Synthesis Sentence block PRESENT — starter on board, students complete
✅ Final Departure Shout PRESENT with at least 3 rounds — NEVER skip
✅ Student Task block PRESENT — diagram task + comparison/synthesis task
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
            print(f"❌ Biology LP Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 6 — DAY 5: BOOK-BACK + DIAGRAM REVIEW
    # =========================================================================

    def _call_day5(self, text, class_num, unit, lesson_title,
                   sections: dict, day_plan: dict):
        try:
            key_structures = ", ".join(sections.get("key_structures", []))
            key_terms      = ", ".join([t for s in sections.get("chapter_sections", [])
                                        for t in s.get("key_terms", [])][:15])
            diagram_sections = ", ".join(sections.get("diagram_sections", []))

            all_section_names = [s["heading"] for s in sections.get("chapter_sections", [])]
            day_summaries = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summaries += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"
                subs = d_data.get("subheadings", [])
                if subs:
                    day_summaries += f"    Subs: {', '.join(subs[:3])}\n"

            prompt = f"""Generate ONLY Day 5 of the Biology Lesson Plan.
Day 5 = Book-back Marking → Diagram Review → Closing.
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

KEY STRUCTURES   : {key_structures}
KEY TERMS        : {key_terms}
DIAGRAM SECTIONS : {diagram_sections}

<h3 class="lp-day-title">Day 5 — Book-back Exercises and Diagram Review</h3>

<div class="lp-day-meta">
  <table>
    <tr>
      <th>Learning Objectives</th>
      <td>Evaluate understanding through book-back exercises.
      Consolidate all diagrams and key structures from the chapter.</td>
    </tr>
  </table>
</div>

<div class="lp-day-block">

  <!-- [0-5 min] SPARK — RAPID RECALL -->
  <div class="lp-section-opening">
    <span class="lp-section-label">Opening [0–5 min]</span>
    <h4>Spark — Final Departure Shout (Recap Mode)</h4>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[Run 5-6 call-and-response rounds covering ALL 4 days of content.
     Teacher gives structure/process name → Students shout function/classification.
     Example: 'Xylem and Phloem alternating in roots is...?' → Students: 'RADIAL!'
     Use actual structures and terms from this chapter only.]"</p>
    <p><em>This activates all prior knowledge before book-back marking.</em></p>
  </div>

  <!-- [5-20 min] BOOK-BACK MARKING -->
  <div class="lp-section-main">
    <span class="lp-section-label">Book-back Marking [5–20 min]</span>
    <h4>Book-Back Exercise Marking and Discussion</h4>
    <p class="teacher-role"><em>Teacher facilitates step-by-step marking.
    Students swap notebooks or self-mark while teacher explains
    the logic behind each answer — especially for diagram-based questions.</em></p>
    <p><em>⚠️ Note to Teacher: All book-back questions with model answers
    are available in the QA section of this platform.
    Open the QA section for this chapter to get complete answers.</em></p>

    <h5>Section 1: Choose the Correct Answer / Fill in the Blanks</h5>
    <p>[For each answer: identify the key structure/term being tested.
     Explain WHY the correct answer is right — reference the chapter section.
     For diagram-based MCQs: point to the board diagram from Days 1-4.]</p>

    <h5>Section 2: Match the Following / Short Answers</h5>
    <p>[For each answer: explain the structure-function connection.
     For comparison questions: reference the comparison table built during Days 1-4.
     Students compare with their own answers and correct errors.]</p>

    <h5>Section 3: Diagram / Descriptive Questions</h5>
    <p>[For 2-3 key diagram answers: redraw the diagram on board quickly.
     Label the key parts. Students check their own diagram labels.
     For descriptive answers: give model answer structure — 2-3 sentences.]</p>

    <div class="board-work">
      <strong>Key Answers on Board:</strong><br/>
      [Write main answers for student verification — especially diagram labels]
    </div>
  </div>

  <!-- [20-30 min] DIAGRAM REVIEW -->
  <div class="lp-section-main">
    <span class="lp-section-label">Diagram Review [20–30 min]</span>
    <h4>Master Diagram Review Session</h4>
    <p class="teacher-role"><em>Teacher redraws all chapter diagrams quickly on board.
    Students check their notebook diagrams against board versions.
    Teacher points out the most commonly missed labels.</em></p>

    <div class="board-work">
      <strong>Chapter Diagrams to Review — Redraw All on Board:</strong><br/>
      {diagram_sections if diagram_sections else "[All diagrams from chapter — redraw each with labels]"}<br/>
      <br/>
      <strong>Most Commonly Missed Labels:</strong><br/>
      [3-4 labels students typically miss — based on chapter content]
    </div>

    <h5>Diagram Memory Check Activity</h5>
    <p>[Students close notebooks. Teacher calls one student at a time to label
     one part on a blank board diagram from memory. 5-6 students participate.
     Class checks each label. Teacher reinforces any wrong labels.]</p>
  </div>

  <!-- CLOSING -->
  <div class="lp-section-closing">
    <span class="lp-section-label">Closing [30–35 min]</span>
    <p class="lp-teacher-says"><strong>Teacher says:</strong><br/>
    "[Congratulate students on completing the chapter.
     Name 2-3 specific things learned across all 5 days.
     Connect the chapter to real-world biology — agriculture, medicine, environment.
     Motivate for next chapter.]"</p>

    <div class="board-work">
      <strong>All Students Must Submit:</strong><br/>
      ☐ Notebook — all 5 days of notes completed<br/>
      ☐ All diagrams drawn and labeled — checked against board<br/>
      ☐ Book-back exercises — answered and marked<br/>
      ☐ All comparison tables completed (Dicot vs Monocot etc.)<br/>
      ☐ All homework tasks from Days 1-4<br/>
      ☐ Synthesis sentences written for all 4 days
    </div>
  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="lp-day-title">Day 5
- Book-back section must have real content from chapter
- Diagram review based on actual chapter diagrams
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
            print(f"❌ Biology LP Day 5 error: {e}")
            return None

    # =========================================================================
    # CALL 7 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, sections: dict, day_plan: dict):
        try:
            all_sections   = sections.get("chapter_sections", [])
            sections_str   = ", ".join([s["heading"] for s in all_sections])
            key_terms      = ", ".join([t for s in all_sections for t in s.get("key_terms", [])][:12])
            key_structures = ", ".join(sections.get("key_structures", [])[:10])
            diagram_secs   = ", ".join(sections.get("diagram_sections", [])[:6])

            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"day{d}", {})
                day_summary += f"  Day {d}: {', '.join(d_data.get('sections', []))}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this Biology chapter.
Do NOT repeat day content. Do NOT generate day blocks.

Chapter        : {lesson_title}
Class          : {class_num}
Unit           : {unit}
All Sections   : {sections_str}
Key Terms      : {key_terms}
Key Structures : {key_structures}
Diagram Sections: {diagram_secs}

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
       Expected answer: 1 sentence max. Biology-specific: structure or function.]
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
       One Why/How/Classify/Identify question per day from actual chapter content.
       Biology-specific: include Microscopic Detective questions (classify from clue).
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
          <p><strong>Word Bank:</strong> [6 key biological terms from chapter]</p>
          <p><strong>Q2 (3M):</strong> Label a given blank diagram — 3 parts</p>
          <p><strong>Q3 (5M):</strong> Match structure to function — 5 pairs</p>
        </td>
        <td>
          <p><strong>Q1 (3M):</strong> Answer 3 short questions — 2 sentences each</p>
          <p><strong>Q2 (4M):</strong> Draw and label the main diagram from chapter</p>
          <p><strong>Q3 (3M):</strong> Complete a comparison table — 3 features</p>
        </td>
        <td>
          <p><strong>Q1 (4M):</strong> Microscopic Detective — identify plant type from
          4 structural clues and explain your reasoning</p>
          <p><strong>Q2 (3M):</strong> Explain a key biological process with diagram</p>
          <p><strong>Q3 (3M):</strong> Compare two structures/processes in a full table</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Diagram Checklist — All Chapter Diagrams</h3>
  <ul>
    [For each diagram in the chapter — extract EXACT labels from the chapter text below.
     Do NOT invent any label. Only use terms that appear verbatim in the chapter text.
     Format:
     ☐ [Exact diagram name from chapter] — Labels: [exact terms from text, comma separated]
     Example: ☐ Chloroplast — Labels: outer membrane, inner membrane, stroma, thylakoid, granum, stroma lamella
     List every diagram that appears in this chapter. Minimum 3 diagrams expected.]
  </ul>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in notebook</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ All diagrams drawn and labeled — checked against board</li>
    <li>☐ All comparison tables completed (at least 4 rows each)</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Synthesis sentences written for all 4 days</li>
    <li>☐ [One chapter-specific checklist item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Section A table: exactly 5 rows
- Section B table: exactly 5 rows with Tamil column
- Differentiated worksheet: 3 columns with visible 2px border
- Diagram checklist: every diagram from chapter with key labels
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
            print(f"❌ Biology LP assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

biology_lp_910_builder = BiologyLP910Builder()