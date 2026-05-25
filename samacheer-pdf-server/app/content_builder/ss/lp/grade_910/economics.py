"""
economics.py
------------
LP Builder for Samacheer Kalvi Social Science — Economics
Class 9 & 10

v2.0 — Teacher feedback applied (May 2026)

Key differences from other discipline builders:
  - 3 days per chapter (same as Civics)
  - Day 3 always = new_content_and_revision (hardcoded — Economics is always content-heavy)
  - Story-driven teaching — tea shop, tiffin box, local context analogies
  - Formula-heavy — every formula on board with dedicated Formula Box at start of day
  - Local context — Ashok Nagar, Chennai, real-life business mapping
  - Game-based sparks (Good vs Service grab/clap game)
  - Large group discussion before teacher explains (student ideas first)
  - Sector identification activities (teacher describes person → student identifies sector)
  - Real-life homework (find examples on walk home / Three Tool Hunt)
  - Formula-based CFUs (if X happens, what is the Net/GDP/DI?)
  - Recap table in closing (Economic Term → Story meaning)

API calls: 7 total
  Call 0 → Chapter Analyser  (JSON)
  Call 1 → Preamble
  Call 2 → Day 1
  Call 3 → Day 2
  Call 4 → Day 3
  Call 5 → Day 4 (Revision + Notes + 50-mark worksheet)
  Call 6 → Assessment
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
)


# ============================================================================
# ECONOMICS DISCIPLINE NOTES
# ============================================================================

ECONOMICS_DISCIPLINE_NOTES = """
ECONOMICS-SPECIFIC TEACHING NOTES:
- Story-driven teaching — use local analogies (tea shop, tiffin box, school canteen)
- Every concept needs a simple real-life story BEFORE the formal definition
- Formula-heavy — write ALL formulas on board at the START of the day
- Local context is critical — reference Ashok Nagar, Chennai, local businesses
- Large group discussion BEFORE teacher explains — student ideas first
- Sector identification: teacher describes a real person → student identifies sector
- Formula-based CFUs: if X changes, what happens to GDP/NNP/PCI?
- Recap table in closing: Economic Term → Story meaning (two-column format)
- Real-life homework: students find examples in their neighbourhood/home
- Data from CSO, HDI, LPG reforms — reference accurately from chapter
- Connect every concept to students' daily life (canteen, bus, pocket money)
- Disposable income = pocket money after giving to mother → students relate
"""


# ============================================================================
# ECONOMICS SPARK STYLES — 3 days
# ============================================================================

ECON_SPARK_STYLES = {
    1: {
        "style": "Classroom Game",
        "instruction": """Run a quick physical game that demonstrates today's core economic concept.
Students stand up and physically respond to teacher's prompts.
Game must be directly connected to today's topic — not generic.
End with a thought-provoking question from 2 students.
Example: Good vs Service game — teacher shouts item → students grab air (Good) or clap (Service).
Tell students WHY they are learning this and WHERE they use it in real life.""",
    },
    2: {
        "style": "Two Objects Comparison",
        "instruction": """Hold up or describe two real objects that look similar but differ economically.
Use the contrast to reveal an economic rule (Home Ground rule, Time Period rule etc.)
The answer must be surprising — students expect one answer but the correct answer is different.
End with Big Question connecting the contrast to today's economic concept.
Example: Kashmir apple vs California apple → only Kashmir apple adds to India's GDP.""",
    },
    3: {
        "style": "Story / Visual Metaphor",
        "instruction": """Tell a short story or use a powerful visual metaphor to introduce today's concept.
Story must use contrasting characters or situations that represent the economic concepts.
Make it relatable — school, family, neighbourhood context.
End with Big Question connecting the story to today's economic concept.
Example: Tall student who can't read vs shorter student who is brilliant →
Growth (just a number) vs Development (quality of life).""",
    },
    4: {
        "style": "Rapid Fire Recall Quiz",
        "instruction": """Start with a rapid-fire keyword quiz reviewing Days 1, 2, and 3.
Teacher shouts a keyword/formula/concept → students shout the answer.
Example: 'GDP full form!' → 'Gross Domestic Product!'
         'If GDP=1000, Depreciation=100, NNP=?' → '900!'
         'Farmer → which sector?' → 'Primary!'
7-10 rapid fire questions. Energetic. Standing format if possible.
Then transition: 'Today we revise everything and make our notes.'""",
    },
}


# ============================================================================
# ECONOMICS STUDENT TASK STYLES — 3 days
# ============================================================================

ECON_STUDENT_TASK_STYLES = {
    1: {
        "style": "Draw + Label + Formula",
        "instruction": """Students draw a simple diagram or picture representing today's economic concept.
Label the key parts using today's economic terms.
Write the relevant formula(s) below the diagram.
Example: Draw a shop → label walls as GDP, family as GNP → write formulas.
One thing inside the shop that counts as Depreciation.""",
    },
    2: {
        "style": "Real-life Sector Hunt",
        "instruction": """Students identify real economic activity from their own neighbourhood/walk home.
Task has 3 parts: Name the person/shop → Identify the sector → Apply today's concept.
Example: On walk home, find one person from each sector.
Name them. Identify sector. Guess which GDP method applies.
Connects classroom economics to students' actual daily life.
NOTE: This task is DIFFERENT from the Real-life Homework — task is done IN CLASS,
homework is done OUTSIDE class tonight.""",
    },
    3: {
        "style": "Think-Pair-Share + Policy Match",
        "instruction": """Give students a specific economic scenario.
Step 1: Think independently (1 min) — which policy applies? Write answer.
Step 2: Pair with neighbour (2 min) — compare and justify.
Step 3: Share with class — 3-4 pairs share.
Then together match: scenario → correct policy tool (Agriculture/Industrial/LPG).
NOTE: This task is DIFFERENT from the Three Tool Hunt homework.""",
    },
    4: {
        "style": "50-Mark Differentiated Written Assessment",
        "instruction": """Full written assessment covering all 4 days.
Students choose their level — Slow/Average/Advanced.
Each level has 50 marks worth of questions appropriate to their ability.
Test conditions — no discussion. 10 minutes.
Teacher reads answers aloud after. Students self-mark.""",
    },
}


# ============================================================================
# ECONOMICS ACTIVITY MAP — 3 days
# ============================================================================

ECON_ACTIVITY_MAP = {
    1: "Tea Shop Story (teacher narrates Kannan Anna's tea shop → students connect each GDP concept to the story) + Formula writing on board (students copy all formulas) + Quick sector/formula CFU quiz strictly from TODAY's content only",
    2: "Sector Identification Race (teacher describes a real person/job → students shout Primary/Secondary/Tertiary) + Large group discussion on GDP limitations (student ideas first, teacher consolidates on board)",
    3: "Tiffin Box Object Lesson (teacher holds closed/open tiffin box → pre/post 1991 contrast) + Three Toolkits activity (students identify which policy applies to given real-life examples)",
    4: "Mind Map on Board (teacher draws full chapter mind map — students copy and complete gaps) + Notes Making (students write structured chapter summary in own words)",
}


# ============================================================================
# ECONOMICS CLOSING STYLES — 3 days
# ============================================================================

ECON_CLOSING_STYLES = {
    1: "Recap Table — students complete a two-column table: Economic Term | What it means in the Tea Shop. Then draw shop diagram with formula labels.",
    2: "Real-life Reflection — on walk home today, find one person working in each sector. Name, sector, and which GDP method applies. NOTE: Different from in-class sector hunt task.",
    3: "Policy Match Closing — students write one real example for each policy tool (Agriculture/Industrial/LPG) from their own life.",
    4: "Chapter Complete — submit notebook, self-marked worksheet, Three Tool Hunt. Teacher gives final motivating message for next chapter.",
}


# ============================================================================
# ECONOMICS LP BUILDER CLASS
# ============================================================================

class EconomicsLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Economics LP Builder (910) v2.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Economics LP for Class 9 & 10.
        Makes 7 API calls:
            Call 0: Chapter Analyser (JSON)
            Call 1: Preamble
            Call 2: Day 1
            Call 3: Day 2
            Call 4: Day 3
            Call 5: Day 4 (Revision + Notes + 50-mark worksheet)
            Call 6: Assessment
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        total_calls = 7
        print(f"      [Economics LP 910 v2] Generating: {lesson_title}")
        print(f"      [Economics LP 910 v2] 7 API calls: Analyser + Preamble + Day1 + Day2 + Day3 + Day4 + Assessment")

        parts = []

        # ── Call 0: Chapter Analyser ──────────────────────────────────────────
        print(f"      [Economics LP] Call 0/{total_calls}: Chapter Analyser...")
        chapter_plan = self._call_chapter_analyser(text, lesson_title)
        if not chapter_plan:
            print(f"         ❌ Chapter Analyser failed — aborting LP")
            return None
        print(f"         ✅ Chapter plan ready — {len(chapter_plan.get('main_topics', []))} main topics | Day 3: new_content_and_revision")

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [Economics LP] Call 1/{total_calls}: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, month, chapter_plan
        )
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting LP")
            return None

        # ── Calls 2-5: Days 1-4 ──────────────────────────────────────────────
        for day_num in range(1, 5):
            call_num = day_num + 1
            print(f"      [Economics LP] Call {call_num}/{total_calls}: Day {day_num}...")
            day_topics = chapter_plan.get("day_plan", {}).get(f"day{day_num}", {})
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title,
                day_num, day_topics, chapter_plan
            )
            if day_html:
                parts.append(clean(day_html))
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        # ── Call 6: Assessment ────────────────────────────────────────────────
        print(f"      [Economics LP] Call 6/{total_calls}: Assessment...")
        assessment = self._call_assessment(
            text, class_num, unit, lesson_title, chapter_plan
        )
        if assessment:
            parts.append(clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Economics LP 910 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 0 — Deep Chapter Analyser
    # -------------------------------------------------------------------------

    def _call_chapter_analyser(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are analysing a Samacheer Kalvi Social Science — Economics chapter.
Read the full chapter text carefully and return a structured JSON plan.

Chapter: {lesson_title}

YOUR JOB:
1. Identify ALL main topics in the chapter (in order they appear)
2. For each main topic, list ALL subtopics and key formulas under it
3. Plan which topics go on which day (Day 1, 2, 3, 4)
   - Day 1: GDP definition + introduction + formulas
   - Day 2: Methods of GDP calculation + Composition
   - Day 3: Economic Growth vs Development + Economic Policies
   - Day 4: Full revision + notes making + 50-mark assessment
4. Identify all economic formulas, key terms, local context opportunities
5. Identify story analogies that can explain each concept simply

CRITICAL RULES:
- Subtopics MUST be under their correct main topic
- Every formula must be captured accurately
- Local analogies (tea shop, tiffin box, canteen) must be identified
- Each day must have a distinct focus with formula work
- Day 3 always includes new content AND revision

MANDATORY TOPIC COVERAGE — these MUST appear if in chapter text:
Day 1 MUST cover:
  - Definition of GDP (with C+I+G+(X-M) formula)
  - National Income (Section 1.1) — GNP, GDP, NNP, NDP, PCI
  - All formulas for each measure with explanation
  - Do NOT summarise National Income briefly — explain ALL 5 measures in detail

Day 2 MUST cover:
  - Composition of GDP / Methods of GDP calculation
  - Sectors of economy — Primary, Secondary, Tertiary
  - Sector content must be DETAILED — not just names
  - DIFFERENCE BETWEEN sections:
    * Primary vs Secondary vs Tertiary sectors
    * GDP vs GNP vs NNP
    * Economic Growth vs Economic Development
  Include explicit comparison tables for each difference

Day 3 MUST cover:
  - Economic Growth vs Development
  - Economic Policies (Agriculture, Industrial, LPG)
  - Remaining content + revision

Day 4 MUST be:
  - Full revision + notes + 50-mark worksheet

Return ONLY valid JSON. No explanation. No markdown. Just raw JSON.

JSON structure:
{{
  "main_topics": [
    {{
      "title": "Main topic title exactly as in chapter",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "formulas": ["Formula 1 = X + Y", "Formula 2 = A - B"],
      "local_analogy": "Tea shop / tiffin box / canteen story that explains this"
    }}
  ],
  "day_plan": {{
    "day1": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "formulas": ["GDP = C + I + G + (X-M)", "GNP = GDP + NFIA"],
      "focus": "One sentence describing Day 1 focus",
      "story_analogy": "Tea shop / local story to use for Day 1",
      "sector_examples": [],
      "continuation": false
    }},
    "day2": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "formulas": [],
      "focus": "One sentence describing Day 2 focus",
      "story_analogy": "Local story for Day 2",
      "sector_examples": ["Person A → Primary", "Person B → Secondary"],
      "continuation": false
    }},
    "day3": {{
      "main_topic": "Economic Growth vs Development and Economic Policies",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "formulas": [],
      "focus": "One sentence describing Day 3 content focus",
      "story_analogy": "Local story for Day 3",
      "sector_examples": [],
      "continuation": false
    }},
    "day4": {{
      "main_topic": "Revision + Notes + Assessment",
      "subtopics": ["Full chapter revision", "Notes making", "50-mark worksheet"],
      "formulas": [],
      "focus": "Full chapter revision, structured notes, and differentiated assessment",
      "story_analogy": "",
      "sector_examples": [],
      "continuation": false
    }}
  }},
  "all_formulas": ["GDP = C + I + G + (X-M)", "GNP = GDP + NFIA"],
  "key_terms": ["GDP", "GNP", "NNP", "PCI"],
  "local_analogies": ["Kannan Anna's tea shop", "School canteen vadas"],
  "real_life_connections": ["Pocket money = Disposable Income", "Bus ticket = Service"],
  "sector_examples": [
    "Farmer → Primary",
    "Factory worker → Secondary",
    "Bank manager → Tertiary"
  ]
}}

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system="""You are a precise chapter analyser. Return ONLY valid JSON.
No explanation. No markdown. No code fences. Just raw JSON starting with {{""",
                messages=[{"role": "user", "content": prompt}]
            )

            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()

            plan = json.loads(raw)
            return plan

        except json.JSONDecodeError as e:
            print(f"❌ Economics Analyser JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"❌ Economics Analyser error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 1 — Preamble
    # -------------------------------------------------------------------------

    def _call_preamble(self, text, class_num, unit,
                       lesson_title, month, chapter_plan: dict):
        try:
            main_topics_str = "\n".join([
                f"  - {t['title']}: {', '.join(t.get('subtopics', []))}"
                f" | Formulas: {', '.join(t.get('formulas', []))}"
                for t in chapter_plan.get("main_topics", [])
            ])
            all_formulas     = "\n".join([f"  - {f}" for f in chapter_plan.get("all_formulas", [])])
            key_terms        = ", ".join(chapter_plan.get("key_terms", []))
            local_analogies  = ", ".join(chapter_plan.get("local_analogies", []))

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — Economics Lesson Plan. Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Economics
Month    : {month if month else 'As scheduled'}
Duration : 3 Days × 35 Minutes = 105 Minutes Total

CHAPTER STRUCTURE (from analyser):
{main_topics_str}

ALL FORMULAS IN THIS CHAPTER:
{all_formulas if all_formulas else '  [Identify from chapter text]'}

KEY ECONOMIC TERMS: {key_terms}
LOCAL ANALOGIES USED: {local_analogies}

Generate these sections:

1. CHAPTER OVERVIEW TABLE (start directly here — no header block needed)
<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Topics Covered | Key Formulas |
        Learning Objectives
</table>
Add a "Learning Objectives" row at the bottom of the table.
List 3-4 key objectives directly inside the table row — not as a separate section.

3. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives specific to THIS Economics chapter
  (social equity, environmental stewardship, labor dignity, civic responsibility)
  Each with one-line explanation tied to actual chapter content
</ul>

4. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives: formula application, economic mapping,
  causal reasoning, source analysis, comparative evaluation
  Each tied to actual chapter content
</ul>

5. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 content objectives — what students will define/analyze/calculate/distinguish
  Based on actual main topics from analyser
  Use action verbs: Define, Analyze, Calculate, Distinguish, Evaluate, Apply
</ul>

6. ALL FORMULAS REFERENCE
<h2>Part 5: Formula Reference Sheet</h2>
<div class="board-work">
  <strong>📐 All Formulas in This Chapter (reference for teacher):</strong><br/>
  [List ALL formulas from analyser — one per line with clear labels]
</div>

7. TEACHING AIDS
<h2>Part 6: Teaching Aids</h2>
<ul>
  All materials needed across 3 days —
  textbook, board, chalk, objects for sparks (apples, tiffin box etc.),
  formula chart, sector identification cards
  Do NOT mention page numbers
</ul>

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids </ul>
- Base all objectives on actual chapter content

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
            print(f"❌ Economics LP preamble error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Calls 2-4 — Content Days 1-3
    # -------------------------------------------------------------------------

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_topics: dict, chapter_plan: dict):
        try:
            spark          = ECON_SPARK_STYLES[day_num]
            task           = ECON_STUDENT_TASK_STYLES[day_num]
            activity       = ECON_ACTIVITY_MAP.get(day_num, "group discussion")
            closing_style  = ECON_CLOSING_STYLES.get(day_num, "Recap")

            main_topic      = day_topics.get("main_topic", "")
            subtopics       = day_topics.get("subtopics", [])
            formulas        = day_topics.get("formulas", [])
            day_focus       = day_topics.get("focus", "")
            story_analogy   = day_topics.get("story_analogy", "")
            sector_examples = day_topics.get("sector_examples", [])
            continuation    = day_topics.get("continuation", False)
            all_formulas    = chapter_plan.get("all_formulas", [])
            real_life       = chapter_plan.get("real_life_connections", [])

            subtopics_str    = "\n".join([f"  - {s}" for s in subtopics])
            formulas_str     = "\n".join([f"  - {f}" for f in formulas])
            sectors_str      = "\n".join([f"  - {s}" for s in sector_examples])
            real_life_str    = ", ".join(real_life[:3]) if real_life else ""

            continuation_note = ""
            if continuation:
                continuation_note = f"""
⚠️ CONTINUATION:
Start by completing carried-over topic from Day {day_num - 1}.
'Yesterday we started [topic]. Today we complete it first.'
"""

            day1_note = ""
            if day_num == 1:
                day1_note = """
⚠️ DAY 1 — MANDATORY CONTENT:
1. GDP Definition — explain fully with C+I+G+(X-M) formula
2. National Income — this is a MAJOR topic with its OWN <h4> heading
   Under National Income, explain ALL 5 measures as SEPARATE <h5> subheadings:
   <h5>1. GDP (Gross Domestic Product)</h5>
   - Definition: market value of all final goods/services within country
   - Formula: GDP = C + I + G + (X-M) — explain EACH letter
   - Numerical example on board
   - Tea shop analogy: everything made inside the shop walls

   <h5>2. GNP (Gross National Product)</h5>
   - Definition: GDP + income earned by nationals abroad
   - Formula: GNP = GDP + NFIA
   - Explain NFIA = Net Factor Income from Abroad
   - Numerical example on board
   - Tea shop analogy: family members working outside the shop

   <h5>3. NNP (Net National Product)</h5>
   - Definition: GNP minus depreciation
   - Formula: NNP = GNP - Depreciation
   - Explain Depreciation = wear and tear of capital
   - Numerical example: if GNP=1000, Depreciation=100, NNP=900
   - Tea shop analogy: broken glasses and rusty stove

   <h5>4. NDP (Net Domestic Product)</h5>
   - Definition: GDP minus depreciation
   - Formula: NDP = GDP - Depreciation
   - Numerical example on board

   <h5>5. Per Capita Income (PCI)</h5>
   - Definition: National Income divided by population
   - Formula: PCI = National Income / Population
   - Numerical example: if NI=2000, Population=10, PCI=200
   - Tea shop analogy: sharing the plate equally

   EACH measure MUST have:
   - Its own <h5> subheading
   - Full explanation (3-4 sentences minimum)
   - Formula written on board
   - Numerical example
   - Tea shop analogy
   - 1 CFU + 1 CCQ

   Do NOT summarise — each measure is a separate teaching point
"""

            day2_note = ""
            if day_num == 2:
                day2_note = """
⚠️ DAY 2 — MANDATORY CONTENT:
1. Sectors of Economy — explain ALL THREE as SEPARATE <h4> headings:

   <h4>Primary Sector</h4>
   - Definition: activities that directly extract from nature
   - Examples from chapter: Agriculture, Cattle farming, Fishing,
     Mining (Coal, Iron ore), Forestry
   - Local example: vegetable sellers bringing produce from farms
   - Contribution to GDP: explain percentage/rank
   - 2 CFUs + 1 CCQ after explanation

   <h4>Secondary Sector</h4>
   - Definition: transforms raw materials into finished goods
   - Examples from chapter: Iron and Steel, Textiles, Jute,
     Automobiles, Engineering goods
   - Local example: car factories in Chennai, garment units
   - Contribution to GDP: explain percentage/rank
   - 2 CFUs + 1 CCQ after explanation

   <h4>Tertiary Sector</h4>
   - Definition: provides services to support other sectors
   - Examples from chapter: Teaching, Healthcare, Banking,
     Transport, IT/Software
   - Local example: bank manager in Ashok Nagar, IT companies
   - Status: currently LARGEST contributor to India's GDP
   - 2 CFUs + 1 CCQ after explanation

   Each sector MUST have:
   - Its own <h4> heading
   - Full explanation minimum 4 sentences
   - Real local examples (Chennai/Ashok Nagar context)
   - Contribution to GDP mentioned
   - 2 CFUs + 1 CCQ

2. DIFFERENCE BETWEEN (MANDATORY — include explicit comparison table):
   The table MUST use this exact style for visibility:
   - Border: 2px solid black on all cells
   - Header row: bold text
   - Each row clearly separated
   - Minimum 4 rows of differences
   - Table must be wide enough to read clearly

   Also add these TWO difference tables in Day 2:

   Table 1: Primary vs Secondary vs Tertiary Sectors (3 columns)
   <div class="board-work">
     <strong>Difference Between Primary, Secondary and Tertiary Sectors:</strong>
     <table style="border-collapse:collapse;width:100%;">
       <thead>
         <tr>
           <th style="border:2px solid black;padding:8px;font-weight:bold;">Basis</th>
           <th style="border:2px solid black;padding:8px;font-weight:bold;">Primary Sector</th>
           <th style="border:2px solid black;padding:8px;font-weight:bold;">Secondary Sector</th>
           <th style="border:2px solid black;padding:8px;font-weight:bold;">Tertiary Sector</th>
         </tr>
       </thead>
       <tbody>
         <tr>
           <td style="border:2px solid black;padding:8px;">Definition</td>
           <td style="border:2px solid black;padding:8px;">Extraction from natural resources</td>
           <td style="border:2px solid black;padding:8px;">Manufacturing and processing</td>
           <td style="border:2px solid black;padding:8px;">Providing services</td>
         </tr>
         <tr>
           <td style="border:2px solid black;padding:8px;">Examples</td>
           <td style="border:2px solid black;padding:8px;">Farming, Fishing, Mining</td>
           <td style="border:2px solid black;padding:8px;">Factory, Construction, Processing</td>
           <td style="border:2px solid black;padding:8px;">Banking, Transport, Education</td>
         </tr>
         <tr>
           <td style="border:2px solid black;padding:8px;">Workers</td>
           <td style="border:2px solid black;padding:8px;">Farmers, Fishermen, Miners</td>
           <td style="border:2px solid black;padding:8px;">Factory workers, Builders</td>
           <td style="border:2px solid black;padding:8px;">Teachers, Doctors, Bankers</td>
         </tr>
         <tr>
           <td style="border:2px solid black;padding:8px;">Contribution to GDP</td>
           <td style="border:2px solid black;padding:8px;">~15-20% of India's GDP</td>
           <td style="border:2px solid black;padding:8px;">~25-30% of India's GDP</td>
           <td style="border:2px solid black;padding:8px;">~50-55% of India's GDP</td>
         </tr>
       </tbody>
     </table>
   </div>

   Table 2: GDP vs GNP vs NNP (3 columns)
   <div class="board-work">
     <strong>Difference Between GDP, GNP and NNP:</strong>
     <table style="border-collapse:collapse;width:100%;">
       <thead>
         <tr>
           <th style="border:2px solid black;padding:8px;font-weight:bold;">Basis</th>
           <th style="border:2px solid black;padding:8px;font-weight:bold;">GDP</th>
           <th style="border:2px solid black;padding:8px;font-weight:bold;">GNP</th>
           <th style="border:2px solid black;padding:8px;font-weight:bold;">NNP</th>
         </tr>
       </thead>
       <tbody>
         <tr>
           <td style="border:2px solid black;padding:8px;">Definition</td>
           <td style="border:2px solid black;padding:8px;">Market value of all goods/services within country</td>
           <td style="border:2px solid black;padding:8px;">GDP + income earned by nationals abroad</td>
           <td style="border:2px solid black;padding:8px;">GNP minus depreciation</td>
         </tr>
         <tr>
           <td style="border:2px solid black;padding:8px;">Formula</td>
           <td style="border:2px solid black;padding:8px;">C + I + G + (X-M)</td>
           <td style="border:2px solid black;padding:8px;">GDP + NFIA</td>
           <td style="border:2px solid black;padding:8px;">GNP - Depreciation</td>
         </tr>
         <tr>
           <td style="border:2px solid black;padding:8px;">What it measures</td>
           <td style="border:2px solid black;padding:8px;">Output within geographical boundary</td>
           <td style="border:2px solid black;padding:8px;">Output by nationals anywhere in world</td>
           <td style="border:2px solid black;padding:8px;">Net output after wear and tear</td>
         </tr>
         <tr>
           <td style="border:2px solid black;padding:8px;">Key difference</td>
           <td style="border:2px solid black;padding:8px;">Includes foreigners working in India</td>
           <td style="border:2px solid black;padding:8px;">Excludes foreigners, includes Indians abroad</td>
           <td style="border:2px solid black;padding:8px;">Most accurate — accounts for capital loss</td>
         </tr>
       </tbody>
     </table>
   </div>

3. Student task must be DIFFERENT from real-life homework
"""

            day3_note = ""
            if day_num == 3:
                day3_note = """
═══════════════════════════════════════════════════════
DAY 3: NEW CONTENT + REVISION
═══════════════════════════════════════════════════════
Structure:
[0-5 min]   Spark — Story/Visual Metaphor
[5-20 min]  Complete remaining new content
[20-30 min] Three Toolkits activity
[30-35 min] Policy Match Closing + homework

MANDATORY DIFFERENCE BETWEEN TABLE FOR DAY 3:
Economic Growth vs Economic Development — MUST include this table:

<div class="board-work">
  <strong>Difference Between Economic Growth and Economic Development:</strong>
  <table style="border-collapse:collapse;width:100%;">
    <thead>
      <tr>
        <th style="border:2px solid #333;padding:8px;">Basis</th>
        <th style="border:2px solid #333;padding:8px;">Economic Growth</th>
        <th style="border:2px solid #333;padding:8px;">Economic Development</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="border:2px solid #333;padding:8px;">Meaning</td>
        <td style="border:2px solid #333;padding:8px;">Quantitative increase in GDP/output</td>
        <td style="border:2px solid #333;padding:8px;">Qualitative improvement in living standards</td>
      </tr>
      <tr>
        <td style="border:2px solid #333;padding:8px;">Concept</td>
        <td style="border:2px solid #333;padding:8px;">Narrow concept — just numbers</td>
        <td style="border:2px solid #333;padding:8px;">Broader concept — quality of life</td>
      </tr>
      <tr>
        <td style="border:2px solid #333;padding:8px;">Measures</td>
        <td style="border:2px solid #333;padding:8px;">GDP, GNP, NNP</td>
        <td style="border:2px solid #333;padding:8px;">HDI, literacy, health, happiness</td>
      </tr>
      <tr>
        <td style="border:2px solid #333;padding:8px;">Example</td>
        <td style="border:2px solid #333;padding:8px;">Factory output increases</td>
        <td style="border:2px solid #333;padding:8px;">Children go to school, people are healthy</td>
      </tr>
      <tr>
        <td style="border:2px solid #333;padding:8px;">Thinker</td>
        <td style="border:2px solid #333;padding:8px;">Traditional economists</td>
        <td style="border:2px solid #333;padding:8px;">Amartya Sen — capabilities approach</td>
      </tr>
    </tbody>
  </table>
</div>

This table MUST appear after explaining Economic Growth and Development.
Students copy this table in their notebooks.
═══════════════════════════════════════════════════════
"""

            day4_note = ""
            if day_num == 4:
                day4_note = """
═══════════════════════════════════════════════════════
DAY 4: REVISION + NOTES + ASSESSMENT
═══════════════════════════════════════════════════════
Structure:
[0-8 min]   Rapid Fire Quiz — 10 REAL questions from ALL days
[8-15 min]  Mind Map — full chapter on board, students copy
[15-23 min] Notes Making — refer to Q&A section for answers
[23-35 min] 50-Mark Differentiated Worksheet (3 levels)
No new content today.

RAPID FIRE QUIZ — MUST be REAL questions with REAL answers:
Generate 10 actual questions — NOT placeholders like [Question here].
Each question must be answerable in one word or one sentence.
Example format:
  Q1: What does GDP stand for? → Gross Domestic Product
  Q2: Formula for NNP? → NNP = GNP - Depreciation
  Q3: Who said growth is just one aspect of development? → Amartya Sen
  Q4: Farmer works in which sector? → Primary
  Q5: What does 'L' in LPG stand for? → Liberalisation

NOTES MAKING — refer to Q&A section:
Teacher says: "For detailed answers to all book-back questions,
refer to the Q&A section of this platform — all answers are there."

50-MARK WORKSHEET — MUST have REAL questions at all 3 levels:
Generate actual questions — NOT placeholders.

🟢 Level 1 — Foundation (Slow Learners) — 50 Marks:
  Section A: Fill in the blanks (10 × 1 = 10 marks)
  - Write 10 ACTUAL fill-in-blank sentences from chapter content
  - Word bank provided below questions
  Section B: Match the following (10 × 1 = 10 marks)
  - Write 10 ACTUAL match pairs from chapter
  Section C: Answer in one sentence (6 × 5 = 30 marks)
  - Write 6 ACTUAL one-sentence answer questions

🟡 Level 2 — Standard (Average Learners) — 50 Marks:
  Section A: Fill in blanks (5 × 1 = 5 marks)
  - Write 5 ACTUAL fill-in-blank sentences
  Section B: Calculate using formula (5 × 3 = 15 marks)
  - Write 5 ACTUAL calculation problems
  - Example: "If GDP = 5000 and Depreciation = 500, find NNP"
  Section C: Answer in 2-3 sentences (5 × 4 = 20 marks)
  - Write 5 ACTUAL short answer questions
  Section D: Answer in detail (1 × 10 = 10 marks)
  - Write 1 ACTUAL detail question

🔴 Level 3 — Advanced (Toppers) — 50 Marks:
  Section A: Calculate and explain (5 × 4 = 20 marks)
  - Write 5 ACTUAL calculation + explanation questions
  Section B: Answer in detail (3 × 10 = 30 marks)
  - Write 3 ACTUAL essay questions from chapter
  - Example: "Evaluate India's GDP growth and explain why GDP
    alone cannot measure development. Use examples."

ALL QUESTIONS MUST BE REAL — not template placeholders.
Base all questions on actual chapter content.
═══════════════════════════════════════════════════════
"""

            next_label = f"Day {day_num + 1}" if day_num < 3 else "end of chapter"

            prompt = f"""Generate ONLY Day {day_num} of the Economics lesson plan. Nothing else.
Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Economics
Day      : {day_num} of 3
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S EXACT TOPIC PLAN — FOLLOW STRICTLY
═══════════════════════════════════════════════════════
Main Topic    : {main_topic}
Subtopics     :
{subtopics_str}
Formulas      :
{formulas_str if formulas_str else '  [No new formulas today — review previous]'}
Story Analogy : {story_analogy if story_analogy else 'Use local tea shop / canteen / neighbourhood context'}
Sector Examples:
{sectors_str if sectors_str else '  [Generate from chapter content]'}
Real-life connections: {real_life_str}
{continuation_note}
{day1_note}{day2_note}{day3_note}{day4_note}
═══════════════════════════════════════════════════════

{self._get_cfu_ccq_instruction()}

{self._get_tamil_instruction()}

═══════════════════════════════════════════════════════
LEAD QUESTION / OPENING QUESTION — DAY {day_num}
═══════════════════════════════════════════════════════
Style: {spark['style']}
{spark['instruction']}
Heading: [0-5 min] Lead Question / Opening Question
Include Big Question at end.
Include: WHY students are learning this + WHERE they use it in real life.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
FORMULA BOX RULE — CRITICAL FOR ECONOMICS
═══════════════════════════════════════════════════════
At the START of Introduction (5-10 min section):
Include a dedicated Formula Box with ALL formulas for today.
Teacher writes ALL formulas on board BEFORE teaching — students copy first.

FORMAT:
<div class="board-work">
  <strong>📐 Formulas for Today (write all on board before starting):</strong><br/>
  [Formula 1 with label]<br/>
  [Formula 2 with label]<br/>
  [Formula 3 with label]
</div>

Then explain each formula one by one using the story analogy.
Every time a formula is introduced in teaching, reference back to the Formula Box.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
STUDENT TASK — DAY {day_num}: {task['style']}
═══════════════════════════════════════════════════════
{task['instruction']}
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
ECONOMICS-SPECIFIC RULES
═══════════════════════════════════════════════════════
- Story BEFORE definition — always use local analogy first, then formal term
- Large group discussion BEFORE teacher explains — ask students first
- Sector identification: teacher describes real person → students shout sector
- Formula CFUs: if X changes, what happens to Y?
- Real-life connections: connect every concept to students' daily life
- Recap table in closing: Economic Term | Tea Shop meaning
- NO page numbers anywhere
- Local context: Ashok Nagar, Chennai, school canteen, neighbourhood
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
WAIT TIME RULE
═══════════════════════════════════════════════════════
After every question:
<p><em>⏱ Wait [X] seconds. Call on [N] students.</em></p>
CFU → Wait 10 seconds, 2-3 students
CCQ → Wait 15 seconds, pair discussion first
Opening question → Wait 20 seconds, 2 students explain choice
Large group discussion → Wait 30 seconds, 3 large group responses
═══════════════════════════════════════════════════════

DAY STRUCTURE:

<h3 class="day-header">
  Day {day_num} — {main_topic}
</h3>
<p class="day-meta">Duration: 35 Minutes | Economics | {day_focus}</p>

<div class="day-block">

  <!-- ═══ SECTION 1: LEAD QUESTION / OPENING (0-5 min) ═══ -->
  <div class="time-block">
    <strong>[0-5 min] Lead Question / Opening Question — {spark['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences using {spark['style']} style.
     Genuinely engaging — based on actual Economics content.
     Use local/familiar context students relate to.
     Include WHY students learn this + WHERE they use it in real life.
     End with Big Question or student discussion prompt.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same opening. Same length.]"</p>
    </div>

    <p><em>⏱ Wait 20 seconds. Allow 2 students to briefly explain their choice.</em></p>

  </div>

  <!-- ═══ SECTION 2: INTRODUCTION + FORMULA BOX (5-10 min) ═══ -->
  <div class="time-block">
    <strong>[5-10 min] Introduction — {story_analogy if story_analogy else 'Local Story'}</strong>

    <p class="teacher-says"><strong>Teacher says (Introduction — English):</strong><br/>
    "[3-4 sentences — introduce today's topic using the story analogy.
     Start with the story FIRST — then connect to formal economic concept.
     Reference local context: school canteen / neighbourhood / family.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — context-based mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same introduction in Tamil.
          Context-based — NOT word-for-word. Pure Tamil Unicode only.
          No Hindi words — pure Tamil only.]"</p>
    </div>

    <div class="board-work">
      <strong>📐 Formulas for Today (write ALL on board before starting):</strong><br/>
      {formulas_str if formulas_str else '[All relevant formulas for today from chapter]'}
    </div>

    <p><em>Students copy all formulas into notebooks first. Then teacher explains.</em></p>

    <div class="vocab-block">
      <strong>Key Economic Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Real-life Example</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [5 key economic terms from TODAY's subtopics.
           Real-life example column: pocket money = DI, bus ticket = service etc.
           Tamil meaning in last column.]
        </tbody>
      </table>
    </div>

    [CFU — formula-based: simple calculation or "what does X stand for?"]

  </div>

  <!-- ═══ SECTION 3: MAIN TEACHING (10-25 min) ═══ -->
  <div class="time-block">
    <strong>[10-25 min] Main Teaching — {activity}</strong>

    [For EACH subtopic in today's plan:]

    <h4>[Subtopic name — exactly as listed]</h4>

    <p class="teacher-says"><strong>Teacher says (English) — Story First:</strong><br/>
    "[3-4 sentences — tell the local story/analogy FIRST.
     Then introduce the formal economic term.
     Connect to the formula already on the board.
     Use local context: tea shop / canteen / neighbourhood.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — context-based mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same story and explanation in Tamil.
          Translate the MEANING — not word-for-word.
          Pure Tamil Unicode only — no Hindi words, no transliteration.
          Same length, same story, same economic term in Tamil.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board — Formula + Example:</strong><br/>
      [Relevant formula from Formula Box]<br/>
      [Simple numerical example: if X = 1000, Y = 200, then Z = ?]
    </div>

    [CFU — formula CFU: "If [X] changes, what happens to [Y]?"]
    [CCQ — deeper: why/how question about this economic concept]

    [Repeat for each subtopic]

    <!-- Activity -->
    <div class="activity-block">
      <strong>Activity — {activity}:</strong>
      <p>[Step by step instructions. English only — no Tamil here.
         For sector identification: teacher describes real person → students shout sector.
         For story activity: narrate story step by step, pause for student responses.
         For large group discussion: ask students FIRST, teacher consolidates after.]</p>
      <p><em>⏱ [Time box]. Take 3 large group responses before explaining.</em></p>
    </div>

    [CFU after activity]

  </div>

  <!-- ═══ SECTION 4: STUDENT TASK — MANDATORY — NEVER SKIP ═══ -->
  <!-- If running long — reduce CFU count but NEVER remove this section -->
  <div class="time-block">
    <strong>[25-30 min] Student Task — {task['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — set up {task['style']} task.
     Specific economic prompt. Clear time limit. Real-life connection.]"</p>

    <div class="board-work">
      <strong>Write on Board — Task:</strong><br/>
      [Exact task prompt students can read from board]
    </div>

    <p class="student-says"><strong>Sample Answer:</strong><br/>
    "[Model answer — 2-3 sentences using actual economic terms and local context]"</p>

    [CCQ here — formula or concept check]

    <div class="diff-block">
      <strong>Differentiated Support:</strong>
      <table class="diff-table">
        <thead>
          <tr>
            <th>Slow Learners<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
            <th>Average Learners<br/>(சராசரி மாணவர்கள்)</th>
            <th>Advanced Learners<br/>(திறமையான மாணவர்கள்)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <p><strong>Task:</strong> Fill in formula blanks</p>
              <p>"GDP = ___ + I + G + (X - M)"</p>
              <p><strong>Word Bank:</strong> [4 key terms from today]</p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Calculate using formula</p>
              <p>"If GDP = 1000 and Depreciation = 100, what is NNP?"</p>
            </td>
            <td>
              <p><strong>Task:</strong> Explain and evaluate</p>
              <p>"Explain [economic concept] and give one real example from Chennai."</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ═══ SECTION 5: CLOSING (30-35 min) ═══ -->
  <div class="time-block">
    <strong>[30-35 min] Closing — {closing_style.split('—')[0].strip()}</strong>

    {"<p class='teacher-says'><strong>Quick Quiz (5 questions covering all 3 days):</strong><br/>[5 rapid-fire questions: who said X, what happened in 1991, which policy gives Y, what does Z stand for, which index measures W]</p><p><em>⏱ Wait 5 seconds per question. Students write answers on paper. Teacher reveals.</em></p>" if day_num == 3 else "<p class='teacher-says'><strong>Rapid-Fire Recap:</strong><br/>[3 rapid-fire questions about today's key formulas and concepts]</p><p><em>⏱ Wait 5 seconds per question. Raise hands format.</em></p>"}

    {"<div class='recap-table'><strong>Recap Table (write on board — bold text, no background colours):</strong><br/><table style='border-collapse:collapse;'><thead><tr><th style='border:1px solid #333;padding:8px;font-weight:bold;background:none;'>Economic Term</th><th style='border:1px solid #333;padding:8px;font-weight:bold;background:none;'>What it means in the " + (story_analogy.split('/')[0] if story_analogy else 'Tea Shop') + "</th></tr></thead><tbody><tr><td style='border:1px solid #333;padding:8px;font-weight:bold;'>[Term 1]</td><td style='border:1px solid #333;padding:8px;'>[Story meaning 1]</td></tr><tr><td style='border:1px solid #333;padding:8px;font-weight:bold;'>[Term 2]</td><td style='border:1px solid #333;padding:8px;'>[Story meaning 2]</td></tr><tr><td style='border:1px solid #333;padding:8px;font-weight:bold;'>[Term 3]</td><td style='border:1px solid #333;padding:8px;'>[Story meaning 3]</td></tr><tr><td style='border:1px solid #333;padding:8px;font-weight:bold;'>[Term 4]</td><td style='border:1px solid #333;padding:8px;'>[Story meaning 4]</td></tr><tr><td style='border:1px solid #333;padding:8px;font-weight:bold;'>[Term 5]</td><td style='border:1px solid #333;padding:8px;'>[Story meaning 5]</td></tr></tbody></table></div>" if day_num == 1 else ""}

    <div class="board-work">
      <strong>Key Points from {"Full Chapter" if day_num == 3 else "Today"} (write on board):</strong><br/>
      1. [Key economic point 1 — one sentence with formula if relevant]<br/>
      2. [Key economic point 2 — one sentence]<br/>
      3. [Key economic point 3 — one sentence]
    </div>

    [Final CCQ]

    <div class="homework-block">
      <p class="teacher-says"><strong>{"Three Tool Hunt (Tonight's Task)" if day_num == 3 else "Real-life Homework"}:</strong><br/>
      "{closing_style}"</p>

      <div class="board-work">
        <strong>Write on Board — Tonight's Task:</strong><br/>
        {"Find 3 items at home: 1. From a farm (Agriculture Policy) 2. Made in a factory (Industrial Policy) 3. Foreign app/brand (LPG). Bonus: Which tool helped your family most today?" if day_num == 3 else "[Specific real-life task based on today's economic concept]"}<br/>
        <em>Share your findings at the start of next class.</em>
      </div>

      {"" if day_num == 3 else f'<p class="teacher-says"><strong>Preview Day {day_num + 1}:</strong><br/>"[1-2 sentences — what tomorrow covers. Build curiosity.]"</p>'}
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS BEFORE FINISHING DAY {day_num}
═══════════════════════════════════════════════════════
✅ Covered ONLY these subtopics: {', '.join(subtopics)}
✅ Formula Box at top of Introduction with ALL today's formulas
✅ Every formula has a numerical example on board
✅ Story/analogy used BEFORE formal definition for every concept
✅ Large group discussion — student ideas BEFORE teacher explains
✅ Sector identification activity included (teacher describes → students shout)
✅ Minimum 5 CFUs + 5 CCQs with wait times
✅ CFUs are formula-based or concept-based (not instruction-based)
✅ Lead Question used — NOT "Spark"
✅ NO page numbers anywhere
✅ Tamil only in: Key Terms + Main explanations + Opening question
✅ Real-life connections throughout (pocket money, bus ticket, canteen)
✅ Recap table in closing (Day 1 only)
✅ Real-life homework assigned
✅ Student Task block is PRESENT and COMPLETE — never skipped
✅ Closing block is PRESENT and COMPLETE — never skipped
✅ NEVER use religious references in examples
✅ NEVER mention specific student names — use 'a student' only
✅ All English words spelled correctly
{"✅ Day 3: Quick Quiz covering all 3 days + Three Tool Hunt homework" if day_num == 3 else f"✅ Preview of Day {day_num + 1} included"}
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ Do NOT generate Day {day_num + 1 if day_num < 3 else ' beyond 3'}

═══════════════════════════════════════════════════════
DAY-SPECIFIC RULES
═══════════════════════════════════════════════════════
{"DAY 1 RULES:" if day_num == 1 else ""}
{"✅ Every subtopic MUST have an <h4> main heading before explanation" if day_num == 1 else ""}
{"✅ Minimum 3 CFU + 3 CCQ per concept — NOT just 1" if day_num == 1 else ""}
{"✅ Activity quiz MUST use ONLY today's content — NO next day topics" if day_num == 1 else ""}
{"✅ Every CFU and activity question must be from TODAY's sections only" if day_num == 1 else ""}
{"✅ If a topic appears in Day 2 plan — do NOT mention it in Day 1 activity" if day_num == 1 else ""}
{"✅ Day 1 activity quiz covers ONLY: GDP definition, GNP, NNP, NDP, PCI formulas" if day_num == 1 else ""}
{"✅ Day 2 activity covers ONLY: sectors, GDP methods, limitations" if day_num == 2 else ""}
{"✅ Day 3 activity covers ONLY: growth vs development, 3 policies" if day_num == 3 else ""}
{"✅ Recap table: bold text only, NO background colours — plain white cells" if day_num == 1 else ""}

{"DAY 2 RULES:" if day_num == 2 else ""}
{"✅ Minimum 3 CFU + 3 CCQ per concept — NOT just 1" if day_num == 2 else ""}
{"✅ Student Task (in-class) MUST be DIFFERENT from Real-life Homework (tonight)" if day_num == 2 else ""}
{"✅ Student task = done in class NOW | Homework = done at home TONIGHT — never the same" if day_num == 2 else ""}

{"DAY 3 RULES:" if day_num == 3 else ""}
{"✅ Minimum 3 CFU + 3 CCQ per concept — NOT just 1" if day_num == 3 else ""}
{"✅ Closing rapid-fire covers Day 3 content only — NOT full chapter revision" if day_num == 3 else ""}
{"✅ Full chapter revision is handled in Day 4 — do NOT do it here" if day_num == 3 else ""}

{"DAY 4 RULES:" if day_num == 4 else ""}
{"✅ Day 4 is REVISION + NOTES + ASSESSMENT — no new content" if day_num == 4 else ""}
{"✅ Start with rapid-fire quiz covering ALL 4 days" if day_num == 4 else ""}
{"✅ Mind map on board — full chapter structure" if day_num == 4 else ""}
{"✅ Notes making — students write structured summary in own words" if day_num == 4 else ""}
{"✅ 50-mark differentiated worksheet — 3 levels (Slow/Average/Advanced)" if day_num == 4 else ""}
{"✅ Written assessment — NOT oral" if day_num == 4 else ""}
═══════════════════════════════════════════════════════

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=14000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Economics LP Day {day_num} error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 5 — Assessment Summary
    # -------------------------------------------------------------------------

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, chapter_plan: dict):
        try:
            main_topics_str = ", ".join([t['title'] for t in chapter_plan.get("main_topics", [])])
            all_formulas    = "\n".join([f"  - {f}" for f in chapter_plan.get("all_formulas", [])])
            key_terms       = ", ".join(chapter_plan.get("key_terms", []))
            sector_examples = "\n".join([f"  - {s}" for s in chapter_plan.get("sector_examples", [])])

            prompt = f"""Generate ONLY the Assessment Summary for this Economics chapter.
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Economics
Total Days: 4

CHAPTER MAIN TOPICS: {main_topics_str}
ALL FORMULAS:
{all_formulas if all_formulas else '  [Identify from chapter]'}
KEY TERMS: {key_terms}
SECTOR EXAMPLES:
{sector_examples if sector_examples else '  [Identify from chapter]'}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Formula Reference Sheet</h3>
  <div class="board-work">
    <strong>📐 All Formulas — Students Must Memorise:</strong><br/>
    {all_formulas if all_formulas else '[All formulas from chapter]'}
  </div>

  <h3>Day-wise Oral Assessment</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Main Topic</th>
        <th>Oral Question (English)</th>
        <th>Expected Answer</th>
        <th>Tamil Prompt</th>
      </tr>
    </thead>
    <tbody>
      [4 rows — Day 1, 2, 3, 4.
       Mix of: formula questions, story-based questions, sector identification.
       Tamil version in last column.
       Based on actual topics from analyser.]
    </tbody>
  </table>

  <h3>CFU Bank — Formula Quick Reference</h3>
  <p><em>10 formula-based and concept-based questions for revision:</em></p>
  <ol>
    [10 questions — mix of:
     - Formula fill: "GDP = ___ + I + G + (X-M)"
     - Calculation: "If GDP = 1000, Depreciation = 100, NNP = ?"
     - Sector ID: "A person mining coal works in which sector?"
     - Concept: "What does 'C' in the GDP formula stand for?"
     Based on actual chapter content.]
  </ol>

  <h3>CCQ Bank — Deeper Understanding</h3>
  <p><em>10 why/how/what-if questions for revision:</em></p>
  <ol>
    [10 deeper questions — if X happens, what is the effect on Y?
     Connect economic concepts to real-life situations.
     Based on actual chapter content.]
  </ol>

  <h3>Sector Identification Quick Quiz</h3>
  <p><em>Teacher describes a person → students identify the sector:</em></p>
  <table>
    <thead>
      <tr><th>Person / Activity</th><th>Sector</th><th>Reason</th></tr>
    </thead>
    <tbody>
      [8 rows — varied examples from Primary, Secondary, Tertiary sectors.
       Based on actual examples from chapter.
       Include local Chennai/Ashok Nagar context where possible.]
    </tbody>
  </table>

  <h3>Three Tool Hunt — Final Assessment</h3>
  <p>[Final assessment task connecting all 3 days:
     Students find 3 real examples from their home/neighbourhood.
     One per major economic concept from the chapter.
     Based on actual chapter content.]</p>

  <h3>Differentiated Assessment</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Slow Learners<br/>(கஷ்டப்படும் மாணவர்கள்)</th>
        <th>Average Learners<br/>(சராசரி மாணவர்கள்)</th>
        <th>Advanced Learners<br/>(திறமையான மாணவர்கள்)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Task:</strong> Fill in formula blanks with word bank</p>
          <p><strong>Word Bank:</strong> [5 key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Calculate using formulas + answer 2 questions</p>
          <p>Example: "If GDP = 5000 and Depreciation = 500, calculate NNP."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Essay — evaluate</p>
          <p>"Evaluate India's GDP growth and explain why GDP alone is not enough to measure development."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 3 days of notes completed in classwork notebook</li>
    <li>☐ All formulas copied and memorised</li>
    <li>☐ All homework tasks submitted (Days 1-3)</li>
    <li>☐ Three Tool Hunt completed (Day 3)</li>
    <li>☐ 50-mark worksheet completed and self-marked (Day 4)</li>
    <li>☐ Chapter notes written in own words (Day 4)</li>
    <li>☐ Sector identification — can identify Primary/Secondary/Tertiary correctly</li>
    <li>☐ [Chapter-specific checklist item from actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Formula Reference Sheet MUST appear at top
- Day table MUST have exactly 3 rows with Tamil column
- CFU bank: 10 questions — mix of formula, calculation, sector ID
- CCQ bank: 10 deeper why/how questions
- Sector table: 8 rows with local context
- No page numbers anywhere
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
            print(f"❌ Economics LP assessment error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_cfu_ccq_instruction(self) -> str:
        return """
═══════════════════════════════════════════════════════
CFU AND CCQ — ECONOMICS SPECIFIC
═══════════════════════════════════════════════════════

Each day must include BOTH types — minimum 5 CFU + 5 CCQ:

── CFU (Check For Understanding) ──────────────────────
Basic recall. Economics CFUs are formula-based or concept-based.
NOT instruction-based (no ICQs).

FORMAT:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <p class="teacher-says">"[Formula question or sector ID — under 6 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Formula answer, letter, sector name]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

── CCQ (Concept Check Question) ───────────────────────
Deeper understanding. Tests WHY or WHAT HAPPENS IF.
Economics CCQs: if X changes, what happens to Y?

FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="teacher-says">"[If X happens, what happens to Y? — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer with economic reasoning]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion first.</em></p>
</div>

ECONOMICS CFU EXAMPLES (formula/concept-based):
✅ "What does 'C' in GDP formula stand for?" → "Consumption!"
✅ "A fisherman at the coast — which sector?" → "Primary!"
✅ "If GDP = 1000, Depreciation = 100, what is NNP?" → "900!"

ECONOMICS CCQ EXAMPLES:
✅ "If population increases but National Income stays same, what happens to PCI?"
✅ "Why isn't a mother's housework counted in GDP?"
✅ "If a car is made in Chennai by a Japanese company, is it India's GDP?"

NEVER use ICQs:
❌ "Do you understand?" ❌ "How many sentences to write?"
═══════════════════════════════════════════════════════
"""

    def _get_tamil_instruction(self) -> str:
        return """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING — TARGETED ONLY
═══════════════════════════════════════════════════════
Tamil appears in EXACTLY 3 places:
✅ 1. KEY TERMS TABLE — Tamil meaning column
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph
✅ 3. OPENING LEAD QUESTION — Tamil version

❌ NEVER in: activity instructions, formula boxes, board work,
   sector identification, recap table, homework task
Tamil mirror: same sentences, same length, same detail. Real Unicode only.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# Singleton instance
# ============================================================================

economics_lp_910_builder = EconomicsLP910Builder()