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
        topic_count = len(chapter_plan.get('master_topic_list', []))
        day_themes = [
            chapter_plan.get('day_plan', {}).get(f'day{i}', {}).get('main_topic', '?')
            for i in range(1, 6)
        ]
        print(f"         ✅ Chapter plan ready — {topic_count} topics found")
        print(f"         ✅ Day themes: {day_themes}")

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
Your job is to read the chapter carefully and create a 5-day teaching plan.
This plan must work as a practical classroom guide for a teacher.

Chapter: {lesson_title}
Class: {lesson_title}

═══════════════════════════════════════════════════════
STEP 1 — READ AND LIST ALL TOPICS
═══════════════════════════════════════════════════════
Read the chapter from top to bottom.
Find EVERY main heading and EVERY subheading — in the exact order they appear.
Write them all down as master_topic_list.

RULES FOR LISTING:
✅ Include every heading and subheading you find in the text
✅ Keep original order — top to bottom as they appear in chapter
✅ Record parent-child relationship — which subheadings belong under which heading
✅ Do NOT skip any heading
✅ Do NOT invent any heading not present in the text
✅ Do NOT include exercise questions, activities, or summary sections as topics

═══════════════════════════════════════════════════════
STEP 2 — CALCULATE TIME BUDGET
═══════════════════════════════════════════════════════
Each class = 35 minutes structured as:
  - Opening/Hook     :  5 minutes (fixed)
  - Introduction     :  5 minutes (fixed)
  - Main Teaching    : 15 minutes (this is where subtopics are taught)
  - Student Activity :  5 minutes (fixed)
  - Closing          :  5 minutes (fixed)

So each day has exactly 15 minutes for teaching content.
Each subtopic needs minimum 5 minutes to explain properly.
Therefore: maximum 3 subtopics per day — never more.

TIME BUDGET CALCULATION (apply to every day):
  Count subtopics assigned to a day.
  Multiply by 5 minutes minimum.
  If total > 15 minutes → too many subtopics → move last one to next day.

This calculation must be done for EVERY day before finalising the plan.

═══════════════════════════════════════════════════════
STEP 3 — ALLOCATE TOPICS TO 5 DAYS
═══════════════════════════════════════════════════════
Using your master_topic_list and time budget calculation, allocate topics to days.

ALLOCATION LOGIC — apply in this order:

RULE 1 — NATURAL GROUPING:
Topics that are geographically or conceptually connected must stay together on the same day.
Never separate a main heading from its subheadings across different days.
Example logic: if a main heading has 3 subheadings, all 3 stay on the same day as the heading.
If the main heading + all subheadings exceed 15 minutes — keep the heading and first 2 subheadings on one day, remaining subheadings move to next day WITH a brief recap of the parent heading.

RULE 2 — CHRONOLOGICAL ORDER:
Topics must appear in the same order as in the chapter.
Never teach Day 3 topics on Day 2 or Day 2 topics on Day 4.

RULE 3 — DEPTH OVER BREADTH:
2 topics taught properly = better than 5 topics rushed.
If a topic is large and detailed — give it more time, even if that means fewer topics that day.

RULE 4 — DAY 5 RULE:
Day 5 = any remaining content from chapter (if chapter is large) + mandatory revision.
If all content fits in Days 1-4 — Day 5 is purely synthesis, mapping, and revision.
If content remains after Day 4 — Day 5 covers remaining content first, then revision.
Revision/synthesis must ALWAYS be present on Day 5 — never skip it.

RULE 5 — NO TOPIC LEFT BEHIND:
Every topic in master_topic_list must appear in exactly one day.
After allocating — cross-check: is every topic from master_topic_list assigned?
If any topic is missing — add it to the most appropriate day.

═══════════════════════════════════════════════════════
STEP 4 — FOR EACH DAY BUILD THE PLAN
═══════════════════════════════════════════════════════
For each day identify:

main_topic:
  The single overarching geographical theme for this day.
  This is what the teacher writes on the board as today's topic.

subtopics:
  List of subtopics to be taught today — maximum 3.
  These come directly from master_topic_list — never invented.

parent_subtopic_map:
  Which subtopics fall under which parent heading.
  Example: {{"Northern Mountains": ["Trans-Himalayas", "The Himalayas", "Purvanchal"]}}
  This ensures teacher introduces parent heading BEFORE explaining subtopics.
  If no parent-child relationship exists — use empty dict {{}}.

map_features:
  Specific geographical features from TODAY's subtopics that students locate on map.
  Maximum 3 features — only from today's content, not from other days.
  Only include features explicitly mentioned in the chapter text.

focus:
  One sentence — what students will understand by end of this day.
  Written from student perspective: "Students will be able to..."

comparison_pair:
  Two concepts from TODAY's content that the chapter explicitly compares.
  Only if comparison exists in today's content — otherwise null.

chant_list:
  List of geographical names from today's content that students can chant together.
  Example: list of mountain ranges, river names, states etc.
  Only include if today's content has a list of 3+ names — otherwise empty list.

time_budget:
  Estimated minutes per subtopic for the 15-minute teaching window.
  Must be realistic integers. Must sum to 15 or less.
  Example: {{"subtopic 1": 7, "subtopic 2": 8}}

═══════════════════════════════════════════════════════
STEP 5 — SELF CHECK BEFORE RETURNING JSON
═══════════════════════════════════════════════════════
Before returning JSON, verify:
✅ Every topic in master_topic_list appears in exactly one day
✅ No day has more than 3 subtopics
✅ time_budget for each day sums to 15 or less
✅ Topics are in chronological order across days
✅ No topic invented that is not in the chapter text
✅ No topic from the chapter is missing from the day plan
✅ Day 5 has revision/synthesis marked

Return ONLY valid JSON. No explanation. No markdown. No code fences.
Start directly with {{ — nothing before it.

JSON structure:
{{
  "master_topic_list": [
    "Every heading and subheading from chapter — in order"
  ],
  "day_plan": {{
    "day1": {{
      "main_topic": "Overarching theme for Day 1",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "parent_subtopic_map": {{}},
      "map_features": ["feature 1", "feature 2"],
      "focus": "Students will be able to...",
      "comparison_pair": null,
      "chant_list": [],
      "time_budget": {{"subtopic 1": 7, "subtopic 2": 8}},
      "continuation": false
    }},
    "day2": {{
      "main_topic": "Overarching theme for Day 2",
      "subtopics": ["subtopic 1", "subtopic 2", "subtopic 3"],
      "parent_subtopic_map": {{
        "Parent heading": ["child subtopic 1", "child subtopic 2"]
      }},
      "map_features": ["feature 1", "feature 2", "feature 3"],
      "focus": "Students will be able to...",
      "comparison_pair": null,
      "chant_list": ["name 1", "name 2", "name 3"],
      "time_budget": {{"subtopic 1": 5, "subtopic 2": 5, "subtopic 3": 5}},
      "continuation": false
    }},
    "day3": {{
      "main_topic": "Overarching theme for Day 3",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "parent_subtopic_map": {{}},
      "map_features": ["feature 1", "feature 2"],
      "focus": "Students will be able to...",
      "comparison_pair": ["Concept A", "Concept B"],
      "chant_list": [],
      "time_budget": {{"subtopic 1": 8, "subtopic 2": 7}},
      "continuation": false
    }},
    "day4": {{
      "main_topic": "Overarching theme for Day 4",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "parent_subtopic_map": {{}},
      "map_features": ["feature 1"],
      "focus": "Students will be able to...",
      "comparison_pair": null,
      "chant_list": [],
      "time_budget": {{"subtopic 1": 8, "subtopic 2": 7}},
      "continuation": false
    }},
    "day5": {{
      "main_topic": "Remaining content + Synthesis and Revision",
      "subtopics": ["remaining subtopic if any", "Revision", "Map Synthesis"],
      "parent_subtopic_map": {{}},
      "map_features": ["key features from all days for synthesis map"],
      "focus": "Students will be able to...",
      "comparison_pair": null,
      "chant_list": [],
      "time_budget": {{"remaining content": 8, "Revision": 4, "Map Synthesis": 3}},
      "continuation": false,
      "has_remaining_content": true,
      "synthesis": true
    }}
  }},
  "key_terms": ["term from chapter text only"],
  "map_locations": ["location explicitly mentioned in chapter"],
  "comparison_pairs": [["Concept A", "Concept B"]],
  "chant_lists": [["name 1", "name 2", "name 3"]],
  "map_memory_tricks": ["catchy memory aid based on actual chapter content"],
  "synthesis_markers": ["strategic feature for Day 5 map activity"]
}}

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system="""You are a precise Geography chapter analyser for Samacheer Kalvi.
You work for any Geography chapter across Class 8, 9 and 10.
Your job: read the chapter, list all topics, calculate time budget, allocate to 5 days.

ABSOLUTE RULES:
- Return ONLY valid JSON — no explanation, no markdown, no code fences
- Start directly with {{ — nothing before it
- Only use topics found in the chapter text — never invent
- Never skip a topic present in the chapter text
- time_budget per day must sum to 15 or less
- Maximum 3 subtopics per day — never more
- Every topic must appear in exactly one day""",
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

            prompt = f"""Generate ONLY Day {day_num} of the Geography lesson plan.
Do NOT generate any other day. Do NOT generate preamble.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Geography
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S TOPIC PLAN — FROM CHAPTER ANALYSER
═══════════════════════════════════════════════════════
Main Topic     : {main_topic}
Subtopics      :
{subtopics_str}
Map Feature    : ONE map feature from today's content only — {map_features_str}
Day Focus      : {day_focus}
Time Budget    : {day_topics.get('time_budget', {})}
{comparison_note}
{chant_note}
{continuation_note}

CRITICAL CONTENT RULES:
✅ Cover ONLY the subtopics listed above — nothing more
✅ Every fact, figure, number must come VERBATIM from chapter text
✅ Never invent statistics, measurements, or data not in the chapter text
✅ Introduce parent heading before explaining any subtopic under it
✅ Follow time_budget — if a subtopic is allocated 5 min, don't spend 10 min on it
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
TIME STRUCTURE — 35 MINUTES — STRICTLY FOLLOW
═══════════════════════════════════════════════════════
TEACHER TALK    : maximum 25% = 8-9 minutes total across entire class
STUDENT ACTION  : minimum 75% = 26-27 minutes total across entire class

This means:
- Teacher never speaks more than 2-3 sentences at a stretch
- After every teacher explanation → immediate student response
- Student response = writing, discussing, labelling, racing, answering, debating
- If teacher has spoken for 2 minutes → MUST stop and give students an activity

MINUTE BY MINUTE RULE:
[0-5 min]    Opening — Teacher: 3 sentences max → Students: guess/respond immediately
[5-10 min]   Introduction — Teacher: 4 sentences max → Students: write key terms
[10-25 min]  Main Teaching — For EACH subtopic:
               Teacher reads 2-3 sentences from chapter → Students respond
               Teacher explains in own words 2-3 sentences → Students activity
               Never more than 3 minutes of teacher talk before student action
[25-30 min]  Student Task — Students work independently — teacher circulates only
[30-35 min]  Closing — Teacher: 3 sentences → Students: write power sentence
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
MAP RULE — ONE MAP ONLY PER DAY
═══════════════════════════════════════════════════════
Each day has EXACTLY ONE map activity.
Map feature today: {map_features_str}
- Teacher points to feature on wall map first — 1 minute
- Students locate same feature in textbook map — 1 minute
- Students label feature in notebook outline map — 2 minutes
- One CFU after map work — "I am..." clue format
Total map time: maximum 5 minutes
Do NOT add additional maps — one is enough for quality over quantity
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
BOARD WORK RULE — STRUCTURED NOT SPORADIC
═══════════════════════════════════════════════════════
Board must be organised and purposeful — not random notes.
Claude decides the best board layout for today's content.
But every day MUST have ALL of these on the board:

MANDATORY BOARD ELEMENTS:
1. Today's main topic + subtopics (written at start — never erased)
2. Key geographical terms with meanings (built during introduction)
3. A diagram or sketch relevant to today's content
   - Must show actual geographical shape — V shape, slope, arc, cross etc.
   - Never a vague box or arrow — must mean something geographically
4. One comparison or T-chart if today has a comparison pair
5. The student task prompt (written clearly before student task begins)
6. Power sentence frame for closing

Board layout format in HTML:
<div class="board-work">
  <strong>📋 Board Layout — Day {day_num}:</strong><br/>
  <table style="width:100%; border-collapse:collapse;">
    <tr>
      <td style="width:35%; vertical-align:top; border:1px solid #ccc; padding:8px;">
        <strong>Left — Topic & Terms</strong><br/>
        [Main topic + subtopics + key terms]
      </td>
      <td style="width:35%; vertical-align:top; border:1px solid #ccc; padding:8px;">
        <strong>Centre — Diagram</strong><br/>
        [Specific diagram with shape description]
      </td>
      <td style="width:30%; vertical-align:top; border:1px solid #ccc; padding:8px;">
        <strong>Right — Task & Closing</strong><br/>
        [Student task prompt + power sentence frame]
      </td>
    </tr>
  </table>
</div>
═══════════════════════════════════════════════════════

{self._get_cfu_ccq_instruction()}
{self._get_tamil_instruction()}

═══════════════════════════════════════════════════════
TOPIC HIERARCHY RULE — ALWAYS FOLLOW
═══════════════════════════════════════════════════════
ALWAYS introduce parent heading before explaining subtopics under it.

FORMAT:
<h4>[Parent Heading]</h4>
<div class="lp-teacher-says">
  "[1-2 sentences introducing this parent topic — what it is, why students are learning it today]"
</div>
<h5>1. [Subtopic name]</h5>
<div class="lp-teacher-says">
  "[Transition sentence: Now let us look at the first part — [subtopic name]...]"
</div>
[explanation + student activity]

<h5>2. [Next subtopic name]</h5>
<div class="lp-teacher-says">
  "[Transition sentence before explaining]"
</div>
[explanation + student activity]

NEVER jump into a subtopic without the parent heading and transition sentence.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
ACTIVITY RULE — DAY {day_num}
═══════════════════════════════════════════════════════
Activity for today: {activity}

Activities must have EXACT student actions:
- What exactly students say
- What exactly students write
- What exactly students do or shout
- How long each step takes

Activity time = minimum 8 minutes of student action
Teacher role during activity = circulate and observe only — not explain
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
CCQ RULE — MIXED DIFFICULTY
═══════════════════════════════════════════════════════
Each day: minimum 3 CFU + minimum 3 CCQ

CFU — "I am..." clue format — recall level:
"I am the narrow sea passage between India and Sri Lanka..." → "Palk Strait!"

CCQ — MIXED: half application, half analysis level — never pure recall:

APPLICATION level CCQ examples:
"If the Western Ghats did not exist, what would happen to rainfall in the Deccan?"
"A farmer wants to settle near a river — which type of plain would you recommend and why?"

ANALYSIS level CCQ examples:
"Why do west-flowing rivers form estuaries while east-flowing rivers form deltas?"
"The Himalayas are young fold mountains — what does this tell us about their height and rivers?"

NEVER write a CCQ that students can answer by just reading one line from the textbook.
Every CCQ must require students to THINK and CONNECT two ideas.
Every CCQ must be a complete grammatical question ending with "?"

FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ ({{"Application" if day_num % 2 == 1 else "Analysis"}}):</strong>
  <p class="teacher-says">"[Complete question — requires thinking, not just recall]"</p>
  <p class="student-says"><strong>Expected:</strong> "[2-3 sentence answer connecting two ideas]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 20 seconds. Pair discussion first. Then call 2 students.</em></p>
</div>
═══════════════════════════════════════════════════════

NOW GENERATE DAY {day_num} USING THIS EXACT HTML STRUCTURE:

<div class="lp-day-block">

<h3 class="lp-day-title">Day {day_num} — {{main_topic}}</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Geography | {{day_focus}}</p>

<!-- ══ SECTION 1: OPENING (0-5 min) ══ -->
<div class="lp-section-opening">
  <div class="lp-section-label">🎯 Opening / Lead Question</div>
  <span class="lp-time">[0–5 min] — Teacher: max 3 sentences | Students: respond immediately</span>

  <div class="lp-teacher-says">
    <strong>Teacher says (English):</strong><br/>
    "[{spark['style']} style opening — 3 sentences maximum.

     QUALITY STANDARD — your spark must meet this bar:
     - Use a physical object, image, or demo that seems OUT OF PLACE
     - The surprise must be directly connected to today's chapter content
     - Students must be genuinely curious before teacher reveals the connection
     - End with one Big Question that only today's lesson can answer
     - Include WHY students are learning this + one real-life use they recognise

     Example of the quality expected:
     'Teacher holds up a seashell found at 5,000m altitude in the mountains.
     How did an ocean creature end up on the world's highest peaks?
     Today we discover how a giant ocean was squeezed out of existence
     to create India's greatest mountain wall.'

     Generate a spark of this quality — but based on TODAY's actual chapter content.
     Never generic. Never textbook-sounding. Always surprising.]"
  </div>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
    "[Exact same opening in Tamil — context-based translation — same length]"
  </div>

  <p><em>⏱ Wait 20 seconds. Take 2-3 student guesses before revealing.
  Students respond — teacher listens — max 2 minute teacher talk total here.</em></p>

</div><!-- end lp-section-opening -->

<!-- ══ SECTION 2: INTRODUCTION (5-10 min) ══ -->
<div class="lp-section-intro">
  <div class="lp-section-label">📖 Introduction & Context Setting</div>
  <span class="lp-time">[5–10 min] — Teacher: max 4 sentences | Students: write key terms (3 min)</span>

  <div class="lp-teacher-says">
    <strong>Teacher says (English):</strong><br/>
    "[4 sentences maximum — introduce today's main topic.
     Connect to what students saw in the opening.
     Tell students exactly what they will cover today and why it matters.]"
  </div>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
    "[Same introduction in Tamil — context-based — same length]"
  </div>

  [BOARD WORK — write main topic and subtopics on board NOW]

  <div class="board-work">
    <strong>📋 Write on Board (left side):</strong><br/>
    Day {day_num}: {{main_topic}}<br/>
    Subtopics: {{subtopics listed clearly}}
  </div>

  <div class="vocab-block">
    <strong>Key Geographical Terms — Students write in notebooks (3 minutes):</strong>
    <table>
      <thead>
        <tr><th>Term</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
      </thead>
      <tbody>
        [4-5 key terms from TODAY's subtopics only — from chapter text only]
      </tbody>
    </table>
  </div>

  <p><em>⏱ Students write terms — teacher circulates — 3 minutes silent writing.
  Teacher does NOT explain yet — students discover meanings first.</em></p>

  [ONE CFU here — "I am..." clue about a key term just written]

</div><!-- end lp-section-intro -->

<!-- ══ SECTION 3: MAIN TEACHING (10-25 min) ══ -->
<div class="lp-section-main">
  <div class="lp-section-label">🏫 Main Teaching & Activities</div>
  <span class="lp-time">[10–25 min] — Teacher: max 8 min total | Students: min 7 min activity</span>

  [For EACH subtopic — follow this pattern STRICTLY:]

  <h4>[Parent heading — introduce FIRST before any subtopics]</h4>
  <div class="lp-teacher-says">
    "[1-2 sentences — what this parent topic is and why we study it today]"
  </div>

  <h5>1. [First subtopic name — exactly as in chapter]</h5>

  <div class="lp-teacher-says">
    <strong>Teacher transition + explanation (English):</strong><br/>
    "[Transition: Now let us look at [subtopic]...]
     [2-3 sentences explaining this subtopic — facts ONLY from chapter text.
      Include ONE real-life connection students can relate to.
      Speak max 2 minutes — then stop.]"
  </div>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
    "[Same explanation in Tamil — context-based — same length]"
  </div>

  [BOARD DIAGRAM — specific shape description]
  <div class="board-work">
    <strong>Draw on Board (centre):</strong><br/>
    "[Specific diagram with actual geographical shape —
     V shape / arc / slope / cross / layered lines etc.
     Describe exactly what to draw — never vague]"
  </div>

  [STUDENT ACTIVITY — immediately after teacher explanation]
  <div class="activity-block">
    <strong>⚡ Student Response ({{"~5 min" if day_num <= 2 else "~4 min"}}):</strong>
    <p>[Exact student action — what they say, write, or do.
       Example: Students open notebooks → draw the diagram from board →
       label 3 features → share with partner → partner checks.
       Teacher circulates — does NOT explain further.]</p>
    <p><em>⏱ Set timer. Students work. Teacher circulates only.</em></p>
  </div>

  [CFU after student response — "I am..." clue]

  <h5>2. [Second subtopic name]</h5>

  <div class="lp-teacher-says">
    <strong>Teacher transition + explanation (English):</strong><br/>
    "[Transition sentence. 2-3 sentences max. Facts from chapter text only.]"
  </div>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
    "[Same in Tamil]"
  </div>

  [STUDENT ACTIVITY]
  <div class="activity-block">
    <strong>⚡ {activity} (~8 min):</strong>
    <p>[Specific step-by-step activity instructions.
       EXACT student actions: what they say, write, shout, draw.
       This is the main activity for today — {activity}.
       Minimum 8 minutes of student action.
       Teacher role: circulate and observe only.]</p>
    <p><em>⏱ Set timer on board. Students work independently or in pairs.</em></p>
  </div>

  [CCQ after main activity — application or analysis level — never recall]

  {"<!-- MAP ACTIVITY (ONE MAP ONLY) -->" }
  <div class="activity-block">
    <strong>🗺️ Map Activity — {map_features_str} (~5 min):</strong>
    <p>Step 1: Teacher points to {map_features_str} on wall map — 1 minute.<br/>
    Step 2: Students find same feature in textbook map — 1 minute.<br/>
    Step 3: Students label {map_features_str} in notebook outline map — 2 minutes.<br/>
    Step 4: CFU — "I am..." clue about this map feature.</p>
    <p><em>⏱ One map only today. Quality labelling — not rushed.</em></p>
  </div>

  {"<!-- T-CHART COMPARISON --><div class='activity-block'><strong>T-Chart: " + (comparison_pair[0] if comparison_pair else "") + " vs " + (comparison_pair[1] if comparison_pair else "") + ":</strong><p>Students draw T-Chart in notebooks. Teacher calls facts → students fill correct column. 5 minutes.</p></div>" if comparison_pair else ""}

  [BOARD WORK — add diagram to centre of board NOW]
  <div class="board-work">
    <strong>📋 Full Board Layout — Day {day_num}:</strong><br/>
    <table style="width:100%; border-collapse:collapse;">
      <tr>
        <td style="width:35%; vertical-align:top; border:1px solid #ccc; padding:8px;">
          <strong>Left — Topic & Terms</strong><br/>
          [Main topic + subtopics + key terms built during intro]
        </td>
        <td style="width:35%; vertical-align:top; border:1px solid #ccc; padding:8px;">
          <strong>Centre — Diagram</strong><br/>
          [Specific geographical diagram — actual shape — built during main teaching]
        </td>
        <td style="width:30%; vertical-align:top; border:1px solid #ccc; padding:8px;">
          <strong>Right — Task & Closing</strong><br/>
          [Student task prompt written here BEFORE student task begins]<br/>
          [Power sentence frame written here BEFORE closing]
        </td>
      </tr>
    </table>
  </div>

</div><!-- end lp-section-main -->

<!-- ══ SECTION 4: STUDENT TASK (25-30 min) ══ -->
<div class="lp-section-student-task">
  <div class="lp-section-label">✏️ Student Task — MANDATORY — NEVER SKIP</div>
  <span class="lp-time">[25–30 min] — Students: 5 min independent work | Teacher: circulates only</span>

  <div class="lp-teacher-says">
    <strong>Teacher says (English):</strong><br/>
    "[2-3 sentences setting up {task['style']} task.
     Point to board — task prompt is already written there.
     Give clear time limit. No further explanation.]"
  </div>

  <div class="board-work">
    <strong>📋 Task Prompt (already on board — right side):</strong><br/>
    [Exact task prompt — geography specific — based on today's content]<br/>
    Starter: "[Model sentence frame students can use]"
  </div>

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
            <p><strong>Task:</strong> Label diagram/map with word bank</p>
            <p><strong>Word Bank:</strong> [4 key terms from today]</p>
            <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
          </td>
          <td>
            <p><strong>Task:</strong> Answer in 2-3 sentences</p>
            <p>Starter: "The [feature] is important because..."</p>
          </td>
          <td>
            <p><strong>Task:</strong> Write independently</p>
            <p>"Explain [feature] and its impact on India's
            climate/agriculture/people in 5 sentences."</p>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <p><em>⏱ 5 minutes silent independent work.
  Teacher circulates — checks notebooks — does NOT explain.
  After 5 minutes: 2 students share answers aloud.</em></p>

  [ONE CCQ here — analysis level]

</div><!-- end lp-section-student-task -->

<!-- ══ SECTION 5: CLOSING (30-35 min) ══ -->
<div class="lp-section-closing">
  <div class="lp-section-label">🔔 Closing & Homework</div>
  <span class="lp-time">[30–35 min] — Teacher: 2 sentences | Students: write power sentence (3 min)</span>

  <div class="lp-teacher-says">
    <strong>Rapid-Fire CFU (Teacher asks — students shout answers):</strong><br/>
    "[3 rapid "I am..." clue questions about today's key features.
     Fast and energetic. Students shout answers together.]"
  </div>

  <p><em>⏱ 5 seconds per question. Whole class responds together.</em></p>

  <div class="board-work">
    <strong>📋 Power Sentence Frame (already on board — right side):</strong><br/>
    "{closing_style}"<br/>
    <em>Students write ONE sentence. 3 minutes silent writing.</em>
  </div>

  <p class="teacher-says"><strong>Teacher says:</strong><br/>
  "[1 sentence asking 3 students to read their power sentence.
   1 sentence previewing tomorrow: what Day {day_num + 1 if day_num < 5 else 5} will cover.]"</p>

  <div class="board-work">
    <strong>📋 Homework (write on board):</strong><br/>
    1. [Specific geography homework — based on today's content — not generic]<br/>
    2. [One map task — label or sketch one feature from today at home]
  </div>

</div><!-- end lp-section-closing -->

</div><!-- end lp-day-block -->

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS BEFORE FINISHING DAY {day_num}
═══════════════════════════════════════════════════════
✅ Teacher talk ≤ 25% — count teacher sentences — max 15 sentences total
✅ Student action ≥ 75% — activities, writing, responding, labelling
✅ ONE map only — {map_features_str}
✅ Parent heading introduced before subtopics
✅ Transition sentence before each subtopic
✅ Board has 3 columns — left/centre/right — all filled
✅ Diagram has actual geographical shape description
✅ CCQs are application or analysis level — not recall
✅ Every CCQ is a complete grammatical question ending with "?"
✅ Student task is present and complete — never skipped
✅ Closing power sentence frame on board
✅ All facts from chapter text only — no invented numbers
✅ No religious references
✅ No specific student names — use "a student" or "Student A"
✅ Tamil in exactly 3 places: opening + introduction + first subtopic explanation
✅ Raw HTML only — start with <div class="lp-day-block">
✅ Do NOT generate Day {day_num + 1 if day_num < 5 else 6}

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

<div class="lp-day-block">
<h3 class="lp-day-title">Day 5 — Synthesis, Mapping & Book-back</h3>
<p class="lp-day-meta">Duration: 35 Minutes | Geography | Synthesis + Evaluation Day</p>

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
- Raw HTML only — start with <div class="lp-day-block">
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
            main_topics_str  = ", ".join(chapter_plan.get("master_topic_list", []))
            key_terms        = ", ".join(chapter_plan.get("key_terms", []))
            map_locations    = ", ".join(chapter_plan.get("map_locations", []))
            comparison_pairs = chapter_plan.get("comparison_pairs", [])
            pairs_str        = ", ".join([f"{p[0]} vs {p[1]}" for p in comparison_pairs]) if comparison_pairs else ""

            prompt = f"""Generate ONLY the Assessment Summary section for this Geography chapter.
Do NOT repeat any day content. Do NOT generate any day blocks.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Geography
Total Days: 5

CHAPTER MAIN TOPICS: {main_topics_str}
KEY TERMS: {key_terms}
MAP LOCATIONS: {map_locations}
COMPARISON PAIRS: {pairs_str}

CONTENT ACCURACY RULE:
All questions and answers must be based ONLY on chapter text.
Never invent facts, figures, or statistics not present in the chapter.

═══════════════════════════════════════════════════════
GENERATE THESE SECTIONS IN ORDER:
═══════════════════════════════════════════════════════

<!-- ══ SECTION 1: CFU BANK ══ -->
<h2>Assessment Summary</h2>
<div class="assessment-block">

<h3>1. Written Assessment — Section A (Recall)</h3>
<p><em>10 questions — students write answers in their notebooks.
Based on actual chapter content only.</em></p>
<table style="width:100%; border-collapse:collapse;">
  <thead>
    <tr>
      <th style="border:2px solid #333; padding:8px; width:5%;">Q.No</th>
      <th style="border:2px solid #333; padding:8px; width:55%;">Question</th>
      <th style="border:2px solid #333; padding:8px; width:40%;">Answer</th>
    </tr>
  </thead>
  <tbody>
    [10 rows — Q1 to Q10.
     Questions: "I am..." clue format — recall level.
     Answer column: filled with correct answer from chapter text.
     Each row:
     <tr>
       <td style="border:2px solid #333; padding:8px;">Q1</td>
       <td style="border:2px solid #333; padding:8px;">"I am [clue]... What am I?"</td>
       <td style="border:2px solid #333; padding:8px;">[Answer from chapter]</td>
     </tr>]
  </tbody>
</table>

<!-- ══ SECTION 2: CCQ BANK — MIXED DIFFICULTY ══ -->
<h3>2. Written Assessment — Section B (Higher Order Thinking)</h3>
<p><em>10 questions — mixed application and analysis level.
Students write answers in notebooks. Teacher marks after collection.</em></p>
<table style="width:100%; border-collapse:collapse;">
  <thead>
    <tr>
      <th style="border:2px solid #333; padding:8px; width:5%;">Q.No</th>
      <th style="border:2px solid #333; padding:8px; width:10%;">Type</th>
      <th style="border:2px solid #333; padding:8px; width:50%;">Question</th>
      <th style="border:2px solid #333; padding:8px; width:35%;">Expected Answer</th>
    </tr>
  </thead>
  <tbody>
    [10 rows — Q1 to Q10.
     5 Application + 5 Analysis — labelled in Type column.
     Questions require connecting two ideas — never pure recall.
     Expected Answer: 2-3 sentence model answer from chapter text.
     Each row:
     <tr>
       <td style="border:2px solid #333; padding:8px;">Q1</td>
       <td style="border:2px solid #333; padding:8px;">Application</td>
       <td style="border:2px solid #333; padding:8px;">[Complete question ending with ?]</td>
       <td style="border:2px solid #333; padding:8px;">[2-3 sentence model answer]</td>
     </tr>]
  </tbody>
</table>

<!-- ══ SECTION 3: DISTINGUISH BETWEEN TABLES ══ -->
<h3>3. Distinguish Between — Comparison Tables</h3>
<p><em>Key comparison pairs from this chapter:</em></p>
[For EACH comparison pair in: {pairs_str}
 Generate one filled comparison table with 4-5 rows of differences.
 All differences from chapter text only.
 Table format:]
<table style="border-collapse:collapse; width:100%; margin-bottom:20px;">
  <thead>
    <tr>
      <th style="border:2px solid #333; padding:8px; background:#f0f0f0;">[Concept A]</th>
      <th style="border:2px solid #333; padding:8px; background:#f0f0f0;">[Concept B]</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border:2px solid #333; padding:8px;">[Difference 1A]</td>
      <td style="border:2px solid #333; padding:8px;">[Difference 1B]</td>
    </tr>
    [4-5 rows total]
  </tbody>
</table>

<!-- ══ SECTION 4: MAP CHECKLIST ══ -->
<h3>4. Map Checklist</h3>
<p><em>All locations students must identify on an outline map.
Based on map locations covered across all 5 days.</em></p>
<ul>
  [Numbered list — all map locations from chapter text only.
   Students use this to self-check their synthesis map from Day 5.]
</ul>

<!-- ══ SECTION 5: DIFFERENTIATED WRITTEN WORKSHEET ══ -->
<h3>5. Chapter Assessment Worksheet</h3>
<p><em>Use after Day 5. Students attempt their own level.
Teacher collects and marks after completion.</em></p>

<div class="diff-block">
  <table class="diff-table" style="width:100%; border-collapse:collapse;">
    <thead>
      <tr>
        <th style="border:2px solid #333; padding:10px; background:#ffe0e0; width:33%;">
          🔴 Level 1 — Slow Learners<br/>
          <small>(கஷ்டப்படும் மாணவர்கள்)</small>
        </th>
        <th style="border:2px solid #333; padding:10px; background:#fff3cd; width:33%;">
          🟡 Level 2 — Average Learners<br/>
          <small>(சராசரி மாணவர்கள்)</small>
        </th>
        <th style="border:2px solid #333; padding:10px; background:#d4edda; width:33%;">
          🟢 Level 3 — Advanced Learners<br/>
          <small>(திறமையான மாணவர்கள்)</small>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="border:2px solid #333; padding:10px; vertical-align:top;">
          <strong>Part A — Label the Map (4 marks)</strong><br/>
          <p>Label these features on the outline map:</p>
          <ol>
            [4 key map features from chapter — easy, well-known ones]
          </ol>
          <strong>Part B — Fill in the Blanks (3 marks)</strong><br/>
          <ol>
            [3 fill-in-the-blank sentences — key facts from chapter]
          </ol>
          <strong>Part C — One sentence answer (3 marks)</strong><br/>
          <ol>
            [3 simple questions — one sentence answer each
             based on chapter content]
          </ol>
          <p><em>Total: 10 marks</em></p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td style="border:2px solid #333; padding:10px; vertical-align:top;">
          <strong>Part A — Label the Map (4 marks)</strong><br/>
          <p>Label these features on the outline map:</p>
          <ol>
            [4 map features — mix of easy and moderate]
          </ol>
          <strong>Part B — Short Answer (6 marks)</strong><br/>
          <ol>
            [3 short answer questions — 2-3 sentences each
             Mix of explain and distinguish questions
             Based on chapter content]
          </ol>
          <p><em>Total: 10 marks</em></p>
        </td>
        <td style="border:2px solid #333; padding:10px; vertical-align:top;">
          <strong>Part A — Label the Map (3 marks)</strong><br/>
          <p>Label these features on the outline map:</p>
          <ol>
            [3 map features — challenging, less obvious ones]
          </ol>
          <strong>Part B — Paragraph Answer (4 marks)</strong><br/>
          <ol>
            [2 paragraph questions — 5-7 sentences each
             Application or analysis level
             Example: "Explain how the physiography of India
             influences its drainage pattern"]
          </ol>
          <strong>Part C — Map + Reasoning (3 marks)</strong><br/>
          <p>[One map-based reasoning question — student marks
          a location AND explains why that location has that
          geographical significance]</p>
          <p><em>Total: 10 marks</em></p>
        </td>
      </tr>
    </tbody>
  </table>
</div>

<!-- ══ SECTION 6: CHAPTER COMPLETION CHECKLIST ══ -->
<h3>6. Chapter Completion Checklist</h3>
<ul>
  <li>☐ All 5 days of notes completed in classwork notebook</li>
  <li>☐ All homework tasks submitted (Days 1-4)</li>
  <li>☐ Book-back exercises answered and marked (Day 5)</li>
  <li>☐ Synthesis outline map completed with all features labeled</li>
  <li>☐ Assessment worksheet attempted and submitted</li>
  <li>☐ All map locations memorised: {map_locations}</li>
  [1-2 chapter-specific checklist items based on this chapter's content]
</ul>

</div>

RULES:
- Raw HTML only — start with <h2>Assessment Summary</h2>
- No oral assessment table — written worksheet only
- CFU bank: exactly 10 "I am..." clue questions
- CCQ bank: exactly 10 questions — 5 application + 5 analysis — labelled
- Distinguish between: one table per comparison pair — 2px border visible
- Worksheet: 3 levels — all worth 10 marks — questions from chapter text only
- Map checklist: all locations from chapter text
- No page numbers anywhere
- No invented facts — chapter text only

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

CRITICAL: Every CCQ must be a COMPLETE grammatical question ending with "?".
Never write a partial sentence or fragment as a CCQ.
✅ Correct: "Why do Peninsular rivers dry up in summer?"
❌ Wrong: "Why Peninsular rivers..."
❌ Wrong: "The rivers of Peninsular India..."

FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="teacher-says">"[Complete grammatical question ending with ? — under 10 words]"</p>
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