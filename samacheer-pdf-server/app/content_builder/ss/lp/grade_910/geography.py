"""
geography.py
------------
LP Builder for Samacheer Kalvi Social Science — Geography
Class 9 & 10

v1.0 — Based on teacher Geography LP sample (May 2026)

Key differences from History and Civics builders:
  - 5 days per chapter (same as History)
  - Day 5 = Synthesis/Mapping + Book-back (teacher chooses based on class)
  - Map work happens EVERY day — not just Day 5
  - Object-based sparks (seashell, ice cube, soil vs rocks)
  - Race activities — students race to find answers in textbook
  - Radio Controller format — teacher calls clues, students find on map
  - Chanting activities — students chant geographical names together
  - Mimicking — students physically mimic geological processes
  - Speed mapping — timed map hunt
  - T-Chart comparisons — Western vs Eastern Ghats etc.
  - CFU style: "I am..." clue format → students identify the feature
  - Closing: Power Sentence / One-Sentence Identity (real-life connection)
  - No page numbers anywhere (teacher LP had them but they were wrong)

API calls: 8 total
  Call 0 → Chapter Analyser  (JSON)
  Call 1 → Preamble
  Call 2 → Day 1
  Call 3 → Day 2
  Call 4 → Day 3
  Call 5 → Day 4
  Call 6 → Day 5 (Synthesis Mapping + Book-back — teacher chooses)
  Call 7 → Assessment
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
# GEOGRAPHY DISCIPLINE NOTES
# ============================================================================

GEOGRAPHY_DISCIPLINE_NOTES = """
GEOGRAPHY-SPECIFIC TEACHING NOTES:
- Map skills are central — every day must include map work
- Spatial thinking: where is it → why there → what effect on people
- Physical features → Human activities → Economic outcomes is the key chain
- Board diagrams must show actual geographical shapes (V shape, cross, slope)
- Race activities: students race to find answers in textbook maps
- Radio Controller format: teacher calls clue → students find on map and shout
- Chanting: students chant lists of geographical names together (mountain ranges etc.)
- Mimicking: students physically act out geological processes (folding, collision)
- Speed mapping: timed map hunt — use timer on board
- T-Chart comparisons for distinguishing between features (Western vs Eastern Ghats)
- CFU style: "I am..." clue → students identify the geographical feature
- Closing: students write ONE meaningful Power Sentence connecting geography to real life
- No page numbers anywhere
- Distinguish-between questions are very common in Geography
"""


# ============================================================================
# GEOGRAPHY SPARK STYLES — 5 days, all object/visual-based
# ============================================================================

GEO_SPARK_STYLES = {
    1: {
        "style": "Mystery Object",
        "instruction": """Hold up or describe a surprising object that seems out of place.
The object should create curiosity about today's geographical topic.
Allow 2-3 student guesses before revealing the connection.
End with a Big Question connecting the object to today's topic.
Example: Teacher holds seashell found at high altitude →
'How did an ocean creature end up on the world's highest peaks?'
Tell students WHY they are learning this and WHERE they use it in real life.""",
    },
    2: {
        "style": "Two Images / Two Objects Comparison",
        "instruction": """Show or describe two contrasting images or objects related to today's topic.
Ask: 'Which would you choose and why?'
Use the contrast to introduce today's geographical concept.
End with a Big Question connecting the contrast to today's topic.
Example: House with fence vs open field →
'If countries had fences, what would India's strongest natural fence be?'""",
    },
    3: {
        "style": "Two Handfuls / Physical Contrast",
        "instruction": """Hold up two contrasting physical materials that represent geographical features.
Students identify which is better/stronger/more useful for a given purpose.
Use the contrast to introduce today's topic.
End with a Big Question.
Example: Handful of soil vs handful of rocks →
'If you were a farmer, which hand would you bet your life on?'""",
    },
    4: {
        "style": "Science Demo / Physical Experiment",
        "instruction": """Use a simple physical demonstration to illustrate a geographical concept.
Objects from daily life — ice cube, sponge, bowl of water etc.
Students observe and predict what happens.
End with a Big Question connecting the demo to today's rivers/drainage topic.
Example: Ice cube vs dry sponge →
'Which one still produces water when it doesn't rain for months?'""",
    },
    5: {
        "style": "Empty Map Challenge",
        "instruction": """Draw a giant empty outline of India/region on the board.
Tell students the map has been 'wiped clean.'
Challenge: 'You are the architects — rebuild it from memory.'
Students draw outline in notebooks to prepare for today's synthesis activity.
End with: 'Today we put the full puzzle together.'""",
    },
}


# ============================================================================
# GEOGRAPHY ACTIVITY MAP — per day
# ============================================================================

GEO_ACTIVITY_MAP = {
    1: "Race activity (teacher calls feature name → students race to find border length/distance and shout back) + Mapping activity (students label features in notebooks with simple diagrams)",
    2: "Range Sorting (3 groups find Identity Card facts for 3 mountain ranges) + Interactive Map Hunt (teacher calls pass name → students find and circle on textbook map)",
    3: "Soil Journey Log (students draw slope and label 4 zones with keywords) + T-Chart Comparison Race (Western Ghats vs Eastern Ghats — students fill comparison table)",
    4: "River ID Card Duel (students find facts for Himalayan vs Peninsular rivers) + Radio Controller Map Hunt (teacher calls coordinates/codenames → students find on map)",
    5: "Relief Layer Build (students sketch physiographic divisions on outline map) + Radio Controller River Flow (teacher calls water missions → students draw rivers) + Treasure Hunt Markers (students mark strategic geographical spots)",
}


# ============================================================================
# GEOGRAPHY CLOSING STYLES — per day
# ============================================================================

GEO_CLOSING_STYLES = {
    1: "One-Sentence Identity — 'India is a subcontinent because...' (students write one sentence connecting today's content to India's identity)",
    2: "Himalayan Promise — students write one meaningful commitment connecting a Himalayan benefit to environmental protection",
    3: "Power Sentence — 'The [Feature] is vital to India because [Reason]' — students pick one feature from today and write its importance",
    4: "River Sentence — 'The [River] is vital to India because [Reason]' — students pick one river from today and explain its importance",
    5: "One-Question Exit — 'If you were a farmer, where would you build your house and why?' — students write one final sentence from their completed map",
}


# ============================================================================
# GEOGRAPHY LP BUILDER CLASS
# ============================================================================

class GeographyLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Geography LP Builder (910) v2.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Geography LP for Class 9 & 10.
        Makes 8 API calls:
            Call 0: Chapter Analyser (JSON)
            Call 1: Preamble
            Calls 2-5: Days 1-4
            Call 6: Day 5 (Synthesis + Book-back)
            Call 7: Assessment
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        total_calls = 8
        print(f"      [Geography LP 910 v1] Generating: {lesson_title}")
        print(f"      [Geography LP 910 v1] 8 API calls: Analyser + Preamble + Day1-4 + Day5 + Assessment")

        parts = []

        # ── Call 0: Chapter Analyser ──────────────────────────────────────────
        print(f"      [Geography LP] Call 0/{total_calls}: Chapter Analyser...")
        chapter_plan = self._call_chapter_analyser(text, lesson_title)
        if not chapter_plan:
            print(f"         ❌ Chapter Analyser failed — aborting LP")
            return None
        print(f"         ✅ Chapter plan ready — {len(chapter_plan.get('main_topics', []))} main topics identified")

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [Geography LP] Call 1/{total_calls}: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, month, chapter_plan
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
            print(f"      [Geography LP] Call {call_num}/{total_calls}: Day {day_num}...")
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

        # ── Call 6: Day 5 (Synthesis + Book-back) ────────────────────────────
        print(f"      [Geography LP] Call 6/{total_calls}: Day 5 (Synthesis + Book-back)...")
        day5_html = self._call_day5(
            text, class_num, unit, lesson_title, chapter_plan
        )
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # ── Call 7: Assessment ────────────────────────────────────────────────
        print(f"      [Geography LP] Call 7/{total_calls}: Assessment...")
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
        print(f"      [Geography LP 910 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 0 — Deep Chapter Analyser
    # -------------------------------------------------------------------------

    def _call_chapter_analyser(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are analysing a Samacheer Kalvi Social Science — Geography chapter.
Read the full chapter text carefully and return a structured JSON plan.

Chapter: {lesson_title}

YOUR JOB:
1. Identify ALL main topics in the chapter (in the order they appear)
2. For each main topic, list ALL subtopics under it
3. Plan which topics go on which day (Day 1 to Day 4 for new content)
4. Day 5 is always Synthesis + Book-back — do NOT assign new content to Day 5

DAY ALLOCATION RULES — STRICTLY FOLLOW:
- Day 1: Location, relief, physiographic divisions introduction
- Day 2: Himalayan Mountains — all ranges and passes
- Day 3: Northern Plains + Peninsular Plateau + Coastal Plains + Islands
  ⚠️ Islands MUST be in Day 3 — never skip, never move to Day 4 or 5
  ⚠️ Coastal Plains MUST be in Day 3 — never skip
- Day 4: Drainage system — Himalayan Rivers + Peninsular Rivers + characteristics
  ⚠️ South Indian/Peninsular River CHARACTERISTICS MUST be in Day 4
  ⚠️ Cover ALL characteristics — seasonal, shorter course, estuaries, hydel power
  ⚠️ Never skip characteristics — they are exam-critical content
- Day 5: Synthesis mapping + Book-back ONLY — NO new content

⚠️ CRITICAL:
- Himalayan Rivers and Peninsular Rivers MUST go in Day 4 — never Day 5
- Coastal Plains and Islands MUST go in Day 3 — never Day 4
- Day 5 must have ZERO new content — synthesis and book-back only
- Never mix Day 4 and Day 5 content

5. Identify key geographical features, map locations, and comparison pairs

CRITICAL RULES:
- Subtopics MUST be under their correct main topic
- Geography topics: mountains, plains, plateaus, coasts, rivers must be separate main topics
- Each day must have a distinct clear focus with map work
- Identify comparison pairs (e.g. Western Ghats vs Eastern Ghats, Himalayan vs Peninsular rivers)
- Identify features that can be chanted as lists (mountain ranges, river names etc.)

Return ONLY valid JSON. No explanation. No markdown. Just raw JSON.

JSON structure:
{{
  "main_topics": [
    {{
      "title": "Main topic title exactly as in chapter",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "map_features": ["feature 1 to locate on map", "feature 2"]
    }}
  ],
  "day_plan": {{
    "day1": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "map_features": ["feature to locate on map"],
      "focus": "One sentence describing Day 1 focus",
      "comparison_pair": null,
      "chant_list": ["item1", "item2"],
      "continuation": false
    }},
    "day2": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "map_features": ["feature to locate"],
      "focus": "One sentence describing Day 2 focus",
      "comparison_pair": ["Concept A", "Concept B"],
      "chant_list": [],
      "continuation": false
    }},
    "day3": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "map_features": ["feature to locate"],
      "focus": "One sentence describing Day 3 focus",
      "comparison_pair": null,
      "chant_list": [],
      "continuation": false
    }},
    "day4": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "map_features": ["feature to locate"],
      "focus": "One sentence describing Day 4 focus",
      "comparison_pair": ["Concept A", "Concept B"],
      "chant_list": [],
      "continuation": false
    }}
  }},
  "key_terms": ["term1", "term2"],
  "map_locations": ["location1", "location2"],
  "comparison_pairs": [["Western Ghats", "Eastern Ghats"], ["Himalayan Rivers", "Peninsular Rivers"]],
  "chant_lists": [["range1", "range2", "range3"]],
  "map_memory_tricks": ["memory trick for location 1", "memory trick for location 2"],
  "synthesis_markers": ["strategic feature 1 for Day 5 treasure hunt", "feature 2"]
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
            print(f"❌ Geography Analyser JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"❌ Geography Analyser error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 1 — Preamble
    # -------------------------------------------------------------------------

    def _call_preamble(self, text, class_num, unit,
                       lesson_title, month, chapter_plan: dict):
        try:
            main_topics_str = "\n".join([
                f"  - {t['title']}: {', '.join(t.get('subtopics', []))}"
                for t in chapter_plan.get("main_topics", [])
            ])
            key_terms     = ", ".join(chapter_plan.get("key_terms", []))
            map_locations = ", ".join(chapter_plan.get("map_locations", []))

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — Geography Lesson Plan. Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Geography
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

CHAPTER STRUCTURE (from analyser):
{main_topics_str}

KEY GEOGRAPHICAL TERMS: {key_terms}
MAP LOCATIONS TO COVER: {map_locations}

Generate these sections:

1. CHAPTER OVERVIEW TABLE (start directly here — no header block needed)
<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Topics Covered | Key Map Locations
</table>

3. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives specific to THIS Geography chapter
  (appreciation of natural diversity, protecting landforms/rivers,
   national pride in geography, environmental responsibility)
  Each with one-line explanation tied to actual chapter content
</ul>

4. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives: map reading, observation, critical thinking,
  communication, collaboration
  Each tied to actual chapter activities
</ul>

5. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 content objectives — what students will identify/explain/classify/locate
  Based on actual main topics from analyser
  Use action verbs: Identify, Explain, Describe, Classify, Locate, Differentiate
</ul>

6. TEACHING AIDS
<h2>Part 5: Teaching Aids</h2>
<ul>
  All materials needed across 5 days — textbook, physical map of India,
  outline maps, board, chalk, mystery objects for sparks,
  timer for speed mapping, flashcards
  Do NOT mention page numbers
</ul>

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids </ul>

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
            print(f"❌ Geography LP preamble error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Calls 2-5 — Content Days 1-4
    # -------------------------------------------------------------------------

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_topics: dict, chapter_plan: dict):
        try:
            spark          = GEO_SPARK_STYLES[day_num]
            task           = STUDENT_TASK_STYLES[day_num]
            activity       = GEO_ACTIVITY_MAP.get(day_num, "map activity")
            closing_style  = GEO_CLOSING_STYLES.get(day_num, "Power Sentence")

            main_topic      = day_topics.get("main_topic", "")
            subtopics       = day_topics.get("subtopics", [])
            map_features    = day_topics.get("map_features", [])
            day_focus       = day_topics.get("focus", "")
            comparison_pair = day_topics.get("comparison_pair", None)
            chant_list      = day_topics.get("chant_list", [])
            continuation    = day_topics.get("continuation", False)

            subtopics_str    = "\n".join([f"  - {s}" for s in subtopics])
            map_features_str = ", ".join(map_features) if map_features else "Identify from chapter"
            chant_str        = " → ".join(chant_list) if chant_list else ""

            comparison_note = ""
            if comparison_pair:
                comparison_note = f"""
⚠️ COMPARISON PAIR FOR TODAY:
Include a T-Chart comparison between: {comparison_pair[0]} vs {comparison_pair[1]}
Students draw T-Chart in notebooks and fill comparison facts.
"""

            chant_note = ""
            if chant_list:
                chant_note = f"""
⚠️ CHANTING ACTIVITY:
Students chant this list together: {chant_str}
Teacher points to board → class chants together → repeat 2-3 times.
"""

            continuation_note = ""
            if continuation:
                continuation_note = f"""
⚠️ CONTINUATION:
Start by completing carried-over topic from Day {day_num - 1}.
'Yesterday we started [topic]. Today we complete it first.'
"""

            day4_note = ""
            if day_num == 4:
                day4_note = """
⚠️ DAY 4 — RIVER CHARACTERISTICS (MANDATORY FLOW):
When teaching Himalayan Rivers and Peninsular Rivers,
follow this EXACT teaching flow:

STEP 1: Introduce Himalayan Rivers
- Name the major rivers (Ganga, Yamuna, Brahmaputra etc.)
- Teacher draws simple sketch of Himalayan river system on board

STEP 2: Explain Himalayan River CHARACTERISTICS (one by one):
- Perennial — fed by glaciers AND monsoon rain
- Long course, large basins
- Form V-shaped valleys in upper course (gorges)
- Form deltas at mouth
- Good for irrigation and navigation
- Carry large amount of silt

STEP 3: Introduce Peninsular Rivers
- Name the major rivers (Godavari, Krishna, Cauvery etc.)
- Teacher draws simple sketch of Peninsular river system on board

STEP 4: Explain Peninsular River CHARACTERISTICS (one by one):
- Seasonal — fed by monsoon rain only
- Shorter course, smaller basins
- Flow through hard rock — form waterfalls
- West-flowing rivers form estuaries
- East-flowing rivers form deltas
- Good for hydel power generation

STEP 5: T-Chart Comparison on board
Draw T-Chart comparing BOTH river systems with all characteristics.
Students copy and complete in notebooks.

This flow MUST be followed in order — do not jump to comparison before
explaining each river system's characteristics separately first.
"""

            next_label = f"Day {day_num + 1}" if day_num < 4 else "Day 5 — Synthesis and Map Building"

            prompt = f"""Generate ONLY Day {day_num} of the Geography lesson plan. Nothing else.
Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Geography
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S EXACT TOPIC PLAN — FOLLOW STRICTLY
═══════════════════════════════════════════════════════
Main Topic   : {main_topic}
Subtopics    :
{subtopics_str}
Map Features : {map_features_str}
{('''⚠️ DAY 2 — THREE MANDATORY MAPS:
All three maps MUST be included in Day 2 map work:
1. India Political Map — label states, union territories, capitals
2. India Physical Divisions Map — label all physiographic zones
3. India Rivers Map — label major rivers (Himalayan + Peninsular)

For each map:
- Teacher points on wall map first
- Students label on outline map in notebooks
- Use Radio Controller format — teacher calls feature → students find and label
- Speed mapping: set timer on board for each map (3-4 mins per map)
''' if day_num == 2 else '')}
Day Focus    : {day_focus}
{comparison_note}
{chant_note}
{continuation_note}
{day4_note}
CRITICAL: Cover ONLY the subtopics listed above.
Do NOT introduce subtopics from other days.
Do NOT repeat subtopics already covered in previous days.
{('''⚠️ DAY 1 — MATH CORNER (MANDATORY):
Add a dedicated Math Corner board-work block during the Introduction or Main Teaching section.
This is for longitude and time calculation.

FORMAT — use this exact board-work div:
<div class='board-work'>
  <strong>📐 Math Corner — Time and Longitude:</strong><br/>
  Earth rotates 360° in 24 hours.<br/>
  Therefore, 1° of longitude = 4 minutes.<br/>
  Longitudinal difference (97°25\'E - 68°7\'E) ≈ 30°<br/>
  30 × 4 minutes = 120 minutes (2 hours)<br/>
  <em>Students copy this calculation in notebooks and verify with a partner.</em>
</div>

[CFU after Math Corner — formula-based: \'If longitude difference is 15°, how many minutes difference in time?\']
''' if day_num == 1 else '')}
{('''⚠️ DAY 4 — HIMALAYAN vs PENINSULAR RIVERS (MANDATORY):
When explaining Himalayan Rivers and Peninsular Rivers:
1. Reference an image comparison — teacher draws/shows both river systems side by side
2. Explain CHARACTERISTICS of each while explaining — not just names

Himalayan Rivers characteristics to cover:
- Perennial (flow throughout year — fed by glaciers + rain)
- Long course, large basins
- Form deltas
- Have gorges in upper course
- Good for navigation and irrigation

Peninsular Rivers characteristics to cover:
- Seasonal (rain-fed only)
- Shorter course, smaller basins
- Flow through harder rocks
- Form estuaries (west-flowing) or deltas (east-flowing)
- Faster flow — good for hydel power

FORMAT — use T-Chart comparison on board:
<div class='board-work'>
  <strong>Draw on Board — Himalayan vs Peninsular Rivers:</strong><br/>
  [Draw simple sketch of both river systems side by side]<br/>
  <table style='border-collapse:collapse;'>
    <thead><tr>
      <th style='border:1px solid #333;padding:6px;'>Himalayan Rivers</th>
      <th style='border:1px solid #333;padding:6px;'>Peninsular Rivers</th>
    </tr></thead>
    <tbody>
      <tr><td style='border:1px solid #333;padding:6px;'>Perennial — glaciers + rain</td><td style='border:1px solid #333;padding:6px;'>Seasonal — rain only</td></tr>
      <tr><td style='border:1px solid #333;padding:6px;'>Long course, large basins</td><td style='border:1px solid #333;padding:6px;'>Short course, smaller basins</td></tr>
      <tr><td style='border:1px solid #333;padding:6px;'>Form deltas</td><td style='border:1px solid #333;padding:6px;'>Form estuaries (west) / deltas (east)</td></tr>
      <tr><td style='border:1px solid #333;padding:6px;'>Good for irrigation + navigation</td><td style='border:1px solid #333;padding:6px;'>Good for hydel power</td></tr>
    </tbody>
  </table>
</div>
''' if day_num == 4 else '')}
{('''⚠️ DAY 3 — MANDATORY CONTENT CHECK:
The following topics MUST be covered in Day 3 if chapter has them:
1. Coastal Plains — Western Coastal Plains + Eastern Coastal Plains
   - Location, width, features, significance
2. Islands — Andaman & Nicobar + Lakshadweep
   - Location, formation, significance
DO NOT skip these — they are frequently missed and exam-important.
Give full explanation with CFUs and CCQs for each.
''' if day_num == 3 else '')}
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
STUDENT TASK — DAY {day_num}: {task['style']}
═══════════════════════════════════════════════════════
{task['instruction']}
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
CLOSING STYLE — DAY {day_num}
═══════════════════════════════════════════════════════
{closing_style}
Students write ONE meaningful sentence connecting today's geography to real life.
Teacher asks 3 students to read their sentences before bell rings.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
GEOGRAPHY-SPECIFIC RULES
═══════════════════════════════════════════════════════
- Map work MUST be included every day
- Race activities: teacher calls feature → students race to find and shout back
- Radio Controller: teacher calls clue → students find on map and circle
- Board diagrams must show actual shapes (V shape, slope, cross, curved lines)
- Speed mapping: mention using a timer on the board
- "I am..." CFU clues: teacher gives clue → students identify the feature
- NO page numbers anywhere
- Chaining: Physical feature → Effect on climate → Effect on agriculture/people
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
WAIT TIME RULE
═══════════════════════════════════════════════════════
After every question:
<p><em>⏱ Wait [X] seconds. Call on [N] students.</em></p>
CFU → Wait 10 seconds, 2-3 students
CCQ → Wait 15 seconds, pair discussion first
Opening question → Wait 20 seconds, 2-3 guesses before revealing
═══════════════════════════════════════════════════════

DAY STRUCTURE:

<h3 class="day-header">
  Day {day_num} — {main_topic}
</h3>
<p class="day-meta">Duration: 35 Minutes | Geography | {day_focus}</p>

<div class="day-block">

  <!-- ═══ SECTION 1: LEAD QUESTION / OPENING (0-5 min) ═══ -->
  <div class="time-block">
    <strong>[0-5 min] Lead Question / Opening Question — {spark['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences using {spark['style']} style.
     Genuinely surprising and engaging — based on actual chapter content.
     Allow 2-3 student guesses before revealing connection.
     Include WHY students learn this + WHERE they use it in real life.
     End with Big Question.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same opening. Same length.]"</p>
    </div>

    <p><em>⏱ Wait 20 seconds. Allow 2-3 guesses before revealing. Take responses.</em></p>

  </div>

  <!-- ═══ SECTION 2: INTRODUCTION (5-10 min) ═══ -->
  <div class="time-block">
    <strong>[5-10 min] Introduction & Context Setting</strong>

    <p class="teacher-says"><strong>Teacher says (Introduction — English):</strong><br/>
    "[3-4 sentences — introduce {main_topic} clearly.
     Connect to what students saw in the spark.
     Tell students exactly what subtopics and map features they cover today.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — context-based mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same introduction in Tamil.
          Context-based — NOT word-for-word. Pure Tamil Unicode only.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Main Topic: {main_topic}<br/>
      Today's Subtopics: {', '.join(subtopics)}<br/>
      Map Features: {map_features_str}<br/>
      Objective: [One sentence learning objective]
    </div>

    <div class="vocab-block">
      <strong>Key Geographical Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [5 key geographical terms from TODAY's subtopics with Tamil meanings]
        </tbody>
      </table>
    </div>

    [CFU after vocab — "I am..." clue format]

  </div>

  <!-- ═══ SECTION 3: MAIN TEACHING (10-25 min) ═══ -->
  <div class="time-block">
    <strong>[10-25 min] Main Teaching & Activity — {activity}</strong>

    [For EACH subtopic in today's plan:]

    <h4>[Subtopic name — exactly as listed]</h4>

    <p class="teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
    "[Teacher reads this sub-point from textbook aloud.
     Then explains in simple clear language — 3-4 sentences.
     REAL-LIFE CONNECTION: 'Just like [Indian/relatable example]...'
     Connect physical feature → effect on climate/agriculture/people.
     Include specific facts and numbers from textbook.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — context-based mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same explanation in Tamil.
          Same length. Same real-life connection. Same detail.
          Context-based Tamil — NOT word-for-word translation.
          Pure Tamil Unicode only — no Hindi words, no transliteration.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board — Diagram:</strong><br/>
      [Specific board diagram instruction with actual shape description:
       V shape / slope / cross / curved lines / solid vs dashed lines etc.]
    </div>

    {"<div class='activity-block'><strong>Chanting Activity:</strong><p>Teacher points to board → class chants together: " + chant_str + "</p><p>Repeat 2-3 times. Keep it energetic.</p></div>" if chant_list else ""}

    [CFU — "I am..." clue: 'I am the [clue]...' → students: '[feature name]!']
    [CCQ — deeper: why/how question about this geographical feature]

    [Repeat for each subtopic]

    {"<!-- T-Chart Comparison --><div class='activity-block'><strong>T-Chart Comparison — " + (comparison_pair[0] if comparison_pair else "") + " vs " + (comparison_pair[1] if comparison_pair else "") + ":</strong><p>Students draw T-Chart in notebooks. Teacher calls facts → students fill correct column. Teacher draws solid line (continuous) vs dashed line (discontinuous) on board where relevant.</p></div>" if comparison_pair else ""}

    <!-- Activity 1 — ~8 mins -->
    <div class="activity-block">
      <strong>Activity 1 — [Race/Sorting/Drawing] (~8 mins):</strong>
      <p>[Specific step-by-step instructions for Activity 1.
         Based on today's first subtopic.
         Students race to find / shout back / label / draw.
         Include EXACT student action: what they say, write, or do.
         Example: 'Teacher shouts Bangladesh! → students race to find border length → shout 4097 km!'
         English only — no Tamil here.]</p>
      <p><em>⏱ Set timer on board. Teacher circulates and checks.</em></p>
    </div>

    [CFU after Activity 1 — "I am..." clue format]

    <!-- Activity 2 — ~7 mins -->
    <div class="activity-block">
      <strong>Activity 2 — [Map Hunt/Radio Controller/Chanting] (~7 mins):</strong>
      <p>[Specific step-by-step instructions for Activity 2.
         Based on today's second subtopic.
         Radio Controller format OR Interactive Map Hunt OR Chanting.
         Include EXACT student action.
         Example: 'Controller to Scouts: Find the Indus River. Find its largest branch. Over!'
         English only — no Tamil here.]</p>
      <p><em>⏱ Set timer. Students use fingers to trace on map.</em></p>
    </div>

    [CFU after Activity 2 — "I am..." clue format]

    <!-- Activity 3 — ~7 mins -->
    <div class="activity-block">
      <strong>Activity 3 — [T-Chart/Comparison/Mimicking] (~7 mins):</strong>
      <p>[Specific step-by-step instructions for Activity 3.
         Based on today's third subtopic or comparison pair.
         T-Chart comparison OR physical mimicking OR group sorting.
         Include EXACT student action.
         Example: 'Students mimic the folding action with their hands — creating a tent shape.'
         English only — no Tamil here.]</p>
      <p><em>⏱ Teacher circulates. Check all notebooks have the diagram.</em></p>
    </div>

    [CFU after Activity 3 — "I am..." clue format]

  </div>

  <!-- ═══ SECTION 4: STUDENT TASK — MANDATORY — NEVER SKIP ═══ -->
  <!-- If running long — reduce CFU count but NEVER remove this section -->
  <div class="time-block">
    <strong>[25-30 min] Student Task — {task['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — set up {task['style']} task.
     Specific geography prompt. Clear time limit. Clear output.]"</p>

    <div class="board-work">
      <strong>Write on Board — Task Prompt:</strong><br/>
      [Exact task prompt students can read from board]<br/>
      [Model sentence starter if written task]
    </div>

    <p class="student-says"><strong>Sample Answer:</strong><br/>
    "[Model answer based on actual chapter content — 2-3 sentences]"</p>

    [CCQ here — "I am..." clue or why/how question]

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
              <p><strong>Task:</strong> Label the diagram/map with word bank</p>
              <p><strong>Word Bank:</strong> [4 key geographical terms from today]</p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>Starter: "The [feature] is important because _______."</p>
            </td>
            <td>
              <p><strong>Task:</strong> Write independently</p>
              <p>"Explain [feature] and its impact on India's climate/agriculture/people in 5 sentences."</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ═══ SECTION 5: CLOSING (30-35 min) ═══ -->
  <div class="time-block">
    <strong>[30-35 min] Closing — {closing_style.split('—')[0].strip()}</strong>

    <p class="teacher-says"><strong>Rapid-Fire CFU (Teacher asks):</strong><br/>
    "[4-5 'I am...' clue questions about today's key features.
     Students shout the answer. Keep it fast and energetic.]"</p>

    <p><em>⏱ Wait 5 seconds per question. Raise hands or shout format.</em></p>

    <div class="board-work">
      <strong>Key Points from Today (write on board):</strong><br/>
      1. [Key geographical fact 1]<br/>
      2. [Key geographical fact 2]<br/>
      3. [Key geographical fact 3]
    </div>

    [Final CCQ]

    <div class="homework-block">
      <p class="teacher-says"><strong>Power Sentence / Closing Reflection:</strong><br/>
      "[Instruction using {closing_style} format.
       Students write ONE meaningful sentence connecting today's geography to real life.
       Specific frame given on board.]"</p>

      <div class="board-work">
        <strong>Write on Board — Sentence Frame:</strong><br/>
        "{closing_style.split('—')[0].strip()} frame here"<br/>
        <em>Ask 3 students to read their sentences before bell rings.</em>
      </div>

      <p class="teacher-says"><strong>Preview {next_label}:</strong><br/>
      "[1-2 sentences — what tomorrow covers.
       If any topic carries over, mention it explicitly.]"</p>
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS BEFORE FINISHING DAY {day_num}
═══════════════════════════════════════════════════════
✅ Covered ONLY these subtopics: {', '.join(subtopics)}
✅ Map work included with specific features: {map_features_str}
{"✅ Day 2: All THREE maps included — Political, Physical Divisions, Rivers" if day_num == 2 else ""}
✅ Board diagram has actual shape description
✅ "I am..." CFU clues included throughout
✅ Minimum 5 CFUs + 5 CCQs with wait times
✅ Lead Question used — NOT "Spark"
✅ NO page numbers anywhere
✅ Tamil only in: Key Terms + Main explanations + Opening question
✅ Race/Radio Controller/Speed mapping activity included
✅ 3 separate activities included (Activity 1 ~8 mins, Activity 2 ~7 mins, Activity 3 ~7 mins)
✅ Each activity has EXACT student action (what they say/write/do/shout)
✅ Student task block is PRESENT and COMPLETE — never skipped
✅ Closing Power Sentence included with exact frame on board
✅ 3 students read sentences before bell rings
✅ NEVER use religious references in examples
✅ NEVER mention specific student names — use 'a student' or 'Student A'
✅ All English words spelled correctly
✅ 3 students read sentences before bell
✅ Student task style: {task['style']}
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ Do NOT generate Day {day_num + 1}

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
            print(f"❌ Geography LP Day {day_num} error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 6 — Day 5: Synthesis Mapping + Book-back (Teacher's Choice)
    # -------------------------------------------------------------------------

    def _call_day5(self, text, class_num, unit,
                   lesson_title, chapter_plan: dict):
        try:
            map_locations     = ", ".join(chapter_plan.get("map_locations", []))
            synthesis_markers = chapter_plan.get("synthesis_markers", [])
            memory_tricks     = chapter_plan.get("map_memory_tricks", [])
            comparison_pairs  = chapter_plan.get("comparison_pairs", [])

            markers_str = "\n".join([f"  - {m}" for m in synthesis_markers])
            tricks_str  = "\n".join([f"  - {t}" for t in memory_tricks])

            prompt = f"""Generate ONLY Day 5 of the Geography lesson plan.
Day 5 has TWO sections — Synthesis Mapping AND Book-back Marking.
The teacher chooses which to prioritise based on class pace.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Geography
Day      : 5 of 5
Duration : 35 minutes

MAP LOCATIONS FROM ANALYSER: {map_locations}
SYNTHESIS MARKERS: {markers_str if markers_str else 'Key features from all 4 days'}
MAP MEMORY TRICKS: {tricks_str if tricks_str else 'Generate chapter-specific tricks'}

<h3 class="day-header">Day 5 — Synthesis, Mapping & Book-back</h3>
<p class="day-meta">Duration: 35 Minutes | Geography | Synthesis + Evaluation Day</p>

<div class="day-block">

  <!-- ═══ TEACHER'S CHOICE NOTE ═══ -->
  <div class="time-block" style="background:#fffbea; border-left: 4px solid #B8860B;">
    <strong>📌 Teacher's Choice — Day 5 has two sections:</strong>
    <ul>
      <li><strong>Option A (Recommended):</strong> Complete BOTH sections —
        Synthesis Mapping [0-20 min] + Book-back Marking [20-30 min] + Exit [30-35 min]</li>
      <li><strong>Option B:</strong> Focus on Synthesis Mapping only —
        if class needs more content consolidation time</li>
      <li><strong>Option C:</strong> Focus on Book-back Marking only —
        if synthesis was done informally during Days 1-4</li>
    </ul>
    <p><em>Choose what works best for your class today. Both sections are fully planned below.</em></p>
  </div>

  <!-- ═══ OPENING: EMPTY MAP CHALLENGE (0-5 min) ═══ -->
  <div class="time-block">
    <strong>[0-5 min] Lead Question / Opening — Empty Map Challenge</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "Explorers, our map has been wiped clean! Over the last 4 days, we discovered
    [key features from all days]. Today you are the architects — rebuild India from memory!"</p>

    <p><em>Students draw large simple outline of India/region in their notebooks.</em></p>
    <p><em>⏱ Give exactly 2 minutes for outline drawing.</em></p>
  </div>

  <!-- ═══ SECTION A: SYNTHESIS MAPPING (5-20 min) ═══ -->
  <div class="time-block">
    <strong>[5-20 min] SECTION A — Synthesis Mapping Activities</strong>

    <h4>Activity 1 — Relief Layer Build (8 mins)</h4>
    <p class="teacher-says"><strong>Teacher says (English — Construction Chief role):</strong><br/>
    "[Specific instructions for students to sketch physiographic divisions layer by layer
     on their outline map. Reference actual features from this chapter.
     Example: 'Draw 3 curved lines for mountains... V shape for plateau... solid line west, dashed east']"</p>

    <div class="board-work">
      <strong>Draw on Board — Layer by Layer:</strong><br/>
      [Step by step board diagram — teacher builds map on board as students follow]
    </div>

    [CFU — "Why did we draw [feature] with a dashed line?" format]

    <h4>Activity 2 — Radio Controller River/Feature Flow (7 mins)</h4>
    <p class="teacher-says"><strong>Teacher says (Radio Controller role):</strong><br/>
    "[Call out 3-4 'Water Missions' or 'Feature Missions' based on actual chapter content.
     Students draw/mark features on their maps based on directions.
     Use actual geographical names from this chapter.]"</p>

    <div class="board-work">
      <strong>Radio Controller Missions (write on board):</strong><br/>
      [3-4 specific missions based on actual chapter features]
    </div>

    [CFU after Radio Controller]

    <h4>Activity 3 — Treasure Hunt Markers (5 mins)</h4>
    <p class="teacher-says"><strong>Teacher says:</strong><br/>
    "Explorers, mark these strategic spots with a star!"</p>

    <div class="board-work">
      <strong>Strategic Markers to Find and Label:</strong><br/>
      {markers_str if markers_str else '[Key strategic geographical features from chapter]'}
    </div>

    <div class="board-work">
      <strong>Map Memory Tricks:</strong><br/>
      {tricks_str if tricks_str else '[Generate 3-5 catchy memory tricks for key locations from this chapter]'}<br/>
      <em>Students write these tricks next to their map labels.</em>
    </div>

  </div>

  <!-- ═══ SECTION B: BOOK-BACK MARKING (20-30 min) ═══ -->
  <div class="time-block">
    <strong>[20-30 min] SECTION B — Book-back Exercise Marking</strong>

    <p><em>Teacher facilitates step-by-step marking. Students swap notebooks or self-mark.
    Note: The platform Q&A section has all book-back questions with complete model answers.</em></p>

    <h4>Section 1: Choose the Correct Answer</h4>
    <p>[3-4 key MCQ answers from this chapter's book-back.
       Explain WHY each is correct — reference topic name not page number.]</p>

    <h4>Section 2: Fill in the Blanks / Match the Following</h4>
    <p>[3-4 key answers — explain the connection. Reference topic names.]</p>

    <h4>Section 3: Short Answer / Distinguish Between</h4>
    <p>[2-3 model answers — especially distinguish-between questions.
       Give comparison table structure where needed.]</p>

    <div class="board-work">
      <strong>Write Correct Answers on Board:</strong><br/>
      [Key answers for student verification]
    </div>

  </div>

  <!-- ═══ CLOSING: ONE-QUESTION EXIT (30-35 min) ═══ -->
  <div class="time-block">
    <strong>[30-35 min] One-Question Exit</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "Explorers, you have mapped the country! Before you leave — look at your map
    and answer one question:"</p>

    <div class="board-work">
      <strong>Exit Question (write on board):</strong><br/>
      "If you were a farmer / engineer / citizen — where would you [relevant choice] and why?"<br/>
      Frame: "I would [choice] in the [Place/Feature] because [one geographical fact from this week]."
    </div>

    <p><em>Students write one final sentence at the bottom of their notes.</em></p>
    <p><em>⏱ Ask 3 students to share their answers before the bell rings.</em></p>

    <p><em>All students must submit before leaving:</em></p>
    <ul>
      <li>Completed notebook — all 5 days of notes</li>
      <li>Outline map — all features labeled from today's synthesis</li>
      <li>Book-back exercises — answered and marked</li>
      <li>All homework from Days 1-4</li>
    </ul>

  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="day-header">Day 5
- Teacher's Choice note MUST appear at top of Day 5
- Synthesis mapping activities based on ACTUAL chapter content from analyser
- Radio Controller missions based on ACTUAL features from chapter
- Treasure Hunt markers based on ACTUAL strategic features from chapter
- Map memory tricks must be chapter-specific and catchy
- Book-back discussion based on ACTUAL chapter topics — no page numbers
- No Tamil in Day 5 — English only
- Do NOT generate any other day

Chapter Text:
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=6000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ Geography LP Day 5 error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 7 — Assessment Summary
    # -------------------------------------------------------------------------

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, chapter_plan: dict):
        try:
            main_topics_str  = ", ".join([t['title'] for t in chapter_plan.get("main_topics", [])])
            key_terms        = ", ".join(chapter_plan.get("key_terms", []))
            map_locations    = ", ".join(chapter_plan.get("map_locations", []))
            comparison_pairs = chapter_plan.get("comparison_pairs", [])
            pairs_str        = ", ".join([f"{p[0]} vs {p[1]}" for p in comparison_pairs]) if comparison_pairs else ""

            prompt = f"""Generate ONLY the Assessment Summary section for this Geography chapter.
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Geography
Total Days: 5

CHAPTER MAIN TOPICS: {main_topics_str}
KEY TERMS: {key_terms}
MAP LOCATIONS: {map_locations}
COMPARISON PAIRS: {pairs_str}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Oral Assessment</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Main Topic Covered</th>
        <th>Oral Question (English)</th>
        <th>Expected Answer</th>
        <th>Tamil Prompt</th>
      </tr>
    </thead>
    <tbody>
      [5 rows — Day 1 through Day 5.
       Use "I am..." clue format where possible for Geography.
       Questions about actual geographical features from chapter.
       Tamil version in last column.]
    </tbody>
  </table>

  <h3>CFU Bank — "I am..." Quick Reference</h3>
  <p><em>10 "I am..." clue questions for revision — teacher gives clue, students identify feature:</em></p>
  <ol>
    [10 "I am..." clue questions with one-word or one-phrase answers.
     Based on actual geographical features from chapter.
     Example: "I am the narrow sea passage between India and Sri Lanka." → "Palk Strait!"]
  </ol>

  <h3>CCQ Bank — Why/How Questions</h3>
  <p><em>10 deeper geography questions for revision:</em></p>
  <ol>
    [10 why/how/what-happens-if questions.
     Focus on: feature → effect on climate/agriculture/people chain.
     Based on actual chapter content.]
  </ol>

  <h3>Distinguish Between Questions</h3>
  <p><em>Key comparison pairs from this chapter:</em></p>
  [For each comparison pair identified by analyser, generate a filled comparison table]
  <table class="exercise-table">
    <thead>
      <tr><th>[Concept A]</th><th>[Concept B]</th></tr>
    </thead>
    <tbody>
      <tr><td>[Difference 1A]</td><td>[Difference 1B]</td></tr>
      <tr><td>[Difference 2A]</td><td>[Difference 2B]</td></tr>
      <tr><td>[Difference 3A]</td><td>[Difference 3B]</td></tr>
    </tbody>
  </table>

  <h3>Map Checklist</h3>
  <p><em>All locations students must be able to identify on an outline map:</em></p>
  <ul>
    [Numbered list of all map locations from analyser — students mark and label these]
  </ul>

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
          <p><strong>Task:</strong> Label outline map with word bank</p>
          <p><strong>Word Bank:</strong> [5 key geographical features]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences</p>
          <p>Starter: "The [feature] affects India because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Structured essay</p>
          <p>"Explain India's physiographic divisions and their impact on climate, agriculture, and people in 8-10 sentences."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in classwork notebook</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Synthesis outline map completed with all features labeled (Day 5)</li>
    <li>☐ All map locations memorised: {map_locations}</li>
    <li>☐ [Chapter-specific checklist item]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table MUST have exactly 5 rows with Tamil column
- CFU bank: 10 "I am..." clue questions
- CCQ bank: 10 why/how questions
- Distinguish between tables: one per comparison pair from analyser
- Map checklist: all locations from analyser
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
            print(f"❌ Geography LP assessment error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_cfu_ccq_instruction(self) -> str:
        return """
═══════════════════════════════════════════════════════
CFU AND CCQ — GEOGRAPHY SPECIFIC
═══════════════════════════════════════════════════════

Each day must include BOTH types — minimum 5 CFU + 5 CCQ:

── CFU (Check For Understanding) ──────────────────────
Basic recall. Geography CFUs use "I am..." clue format.
Teacher gives a clue → students identify the geographical feature.

FORMAT:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <p class="teacher-says">"I am [clue description of geographical feature]..."</p>
  <p class="student-says"><strong>Expected:</strong> "[Feature name]!"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

── CCQ (Concept Check Question) ───────────────────────
Deeper understanding. Tests WHY or HOW.
Geography CCQs: feature → effect on climate/agriculture/people.

FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="teacher-says">"[Why/How/What happens if question — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer explaining impact]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion first.</em></p>
</div>

GEOGRAPHY CFU EXAMPLES ("I am..." format):
✅ "I am the narrow sea passage between India and Sri Lanka..." → "Palk Strait!"
✅ "I am the highest peak located entirely within India..." → "Kanchenjunga!"
✅ "I am the most continuous Himalayan range with permanent snow..." → "Himadri!"

NEVER use ICQs:
❌ "Do you understand?" ❌ "How many points?"
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

❌ NEVER in: activity instructions, board work, race activities,
   time notes, closing power sentence, map work
Tamil mirror: same sentences, same length, same detail. Real Unicode only.
⚠️ CRITICAL — Tamil translation must be PURE TAMIL only:
- NO Hindi words anywhere in Tamil text
- NO transliteration of Hindi into Tamil script
- If a concept has no Tamil equivalent, use the English term — never Hindi
- Examples of common mistakes to AVOID:
  ❌ நதி (correct Tamil) vs गंगा in Tamil script (Hindi — wrong)
  ❌ Using Hindi geographical terms transliterated into Tamil
- Every word in the Tamil mirror must be either pure Tamil or English loanword
- Never use Hindi loanwords in Tamil output
═══════════════════════════════════════════════════════
"""


# ============================================================================
# Singleton instance
# ============================================================================

geography_lp_910_builder = GeographyLP910Builder()