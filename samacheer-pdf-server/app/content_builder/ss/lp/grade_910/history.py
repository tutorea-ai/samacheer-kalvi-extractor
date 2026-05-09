"""
history.py
----------
LP Builder for Samacheer Kalvi Social Science — History
Class 9 & 10

v8.0 — Deep Chapter Analyser + full teacher feedback fixes (May 2026)

Changes from v7.0:
  ✅ Call 0: Deep Chapter Analyser — reads chapter structure first
       Returns exact main topics, subtopics, parent-child relationships
       Day-wise topic plan based on actual chapter content
  ✅ Each day prompt receives exact topics + subtopics from Call 0
       No guessing, no repetition, no misplacement
  ✅ Spark renamed → Lead Question / Opening Question
  ✅ Student response wait time added after every question
  ✅ Page numbers removed entirely (were wrong — better to omit)
  ✅ Video clip + offline alternative added for Day 3
  ✅ CFU (Check For Understanding — basic recall) added alongside CCQ
  ✅ Continuation explicitly defined when topic carries over
  ✅ Subtopic under wrong main topic problem fixed via Call 0
  ✅ Missing topics problem fixed via Call 0
  ✅ Total: 8 API calls

API calls:
  Call 0 → Chapter Analyser  (JSON — chapter structure + day plan)
  Call 1 → Preamble
  Call 2 → Day 1
  Call 3 → Day 2
  Call 4 → Day 3
  Call 5 → Day 4
  Call 6 → Day 5
  Call 7 → Assessment
"""

import json
import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    SS_LP_SYSTEM_PROMPT,
    SPARK_STYLES,
    STUDENT_TASK_STYLES,
    ACTIVITY_MAP,
    clean,
)


# ============================================================================
# HISTORY DISCIPLINE NOTES
# ============================================================================

HISTORY_DISCIPLINE_NOTES = """
HISTORY-SPECIFIC TEACHING NOTES:
- Use timeline-based thinking: when → what caused it → what resulted
- Chronology matters — always reference sequence of events clearly
- Source analysis is a key skill — use any primary source quote in the chapter
- Board flowcharts must show: Cause → Event → Consequence chains
- Map references as text descriptions — do NOT give page numbers
- Always maintain main topic → subtopic hierarchy from the chapter plan
"""


# ============================================================================
# CCQ + CFU INSTRUCTION BLOCK
# ============================================================================

CCQ_CFU_INSTRUCTION = """
═══════════════════════════════════════════════════════
CCQ AND CFU — CONCEPT AND UNDERSTANDING CHECKS
═══════════════════════════════════════════════════════

Each day must include BOTH types — placed randomly throughout:

── CFU (Check For Understanding) ──────────────────────
Basic recall question. Asked immediately after explaining something.
Simple, one-word or one-sentence answer.
No Tamil required for CFU.

FORMAT:
<div class="cfu-block">
  <strong>🔎 CFU (Check For Understanding):</strong>
  <p class="teacher-says">"[Very simple factual question — under 6 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One word or one sentence]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students before moving on.</em></p>
</div>

── CCQ (Concept Check Question) ───────────────────────
Deeper conceptual question. Tests if student understood the WHY or HOW.
Tamil version mandatory.

FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ (Concept Check):</strong>
  <p class="teacher-says">"[Deeper question about concept just taught — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion before taking answers.</em></p>
</div>

⚠️ CRITICAL DIFFERENCE — CFU vs CCQ:
❌ WRONG ICQ (never use): "Do you understand?" / "How many sentences?"
✅ CFU example: "What year did WW1 start?"
✅ CCQ example: "Why did the alliance system make the war spread so fast?"

RULES:
- Minimum 5 CFUs and 5 CCQs per day (10 total checks)
- Place AFTER explaining each concept — never before
- ALWAYS include wait time instruction after each CFU and CCQ
- CFU comes first → CCQ follows for deeper check on same concept
- No two questions repeat
═══════════════════════════════════════════════════════
"""


# ============================================================================
# TAMIL INSTRUCTION
# ============================================================================

TAMIL_INSTRUCTION = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES — TARGETED ONLY
═══════════════════════════════════════════════════════

Tamil appears in EXACTLY 3 places — nowhere else:

✅ 1. KEY TERMS TABLE — Tamil meaning column only
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph after English paragraph
✅ 3. OPENING LEAD QUESTION — Tamil version after English question

❌ NEVER add Tamil to:
   - Activity instructions
   - Group task descriptions
   - Time notes
   - Board work headings
   - Homework task description
   - Student task instructions
   - CFU blocks
   - Closing / recap sections

Tamil mirror rule (where Tamil IS used):
- Same sentences. Same detail. Same length as English.
- NOT a summary. Full mirror.
- Real Tamil Unicode script only — never transliteration.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# HISTORY LP BUILDER CLASS
# ============================================================================

class HistoryLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ History LP Builder (910) v8.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate History LP for Class 9 & 10.
        Makes 8 API calls:
            Call 0: Chapter Analyser (JSON)
            Call 1: Preamble
            Calls 2-5: Day 1-4 (each receives exact topics from Call 0)
            Call 6: Day 5
            Call 7: Assessment
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        total_calls = 8
        print(f"      [History LP 910 v8] Generating: {lesson_title}")
        print(f"      [History LP 910 v8] 8 API calls: Analyser + Preamble + Day1-4 + Day5 + Assessment")

        parts = []

        # ── Call 0: Chapter Analyser ──────────────────────────────────────────
        print(f"      [History LP] Call 0/{total_calls}: Chapter Analyser...")
        chapter_plan = self._call_chapter_analyser(text, lesson_title)
        if not chapter_plan:
            print(f"         ❌ Chapter Analyser failed — aborting LP")
            return None
        print(f"         ✅ Chapter plan ready — {len(chapter_plan.get('main_topics', []))} main topics identified")

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [History LP] Call 1/{total_calls}: Preamble...")
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
            print(f"      [History LP] Call {call_num}/{total_calls}: Day {day_num}...")
            day_topics = chapter_plan.get("day_plan", {}).get(f"day{day_num}", [])
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title,
                day_num, day_topics, chapter_plan
            )
            if day_html:
                parts.append(clean(day_html))
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        # ── Call 6: Day 5 ────────────────────────────────────────────────────
        print(f"      [History LP] Call 6/{total_calls}: Day 5 (Map + Book-back)...")
        day5_html = self._call_day5(
            text, class_num, unit, lesson_title, chapter_plan
        )
        if day5_html:
            parts.append(clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # ── Call 7: Assessment ────────────────────────────────────────────────
        print(f"      [History LP] Call 7/{total_calls}: Assessment...")
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
        print(f"      [History LP 910 v8] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 0 — Deep Chapter Analyser
    # -------------------------------------------------------------------------

    def _call_chapter_analyser(self, text: str, lesson_title: str) -> Optional[dict]:
        """
        Reads the full chapter and returns a structured JSON plan.
        This plan drives all subsequent day prompts — ensuring correct
        topic placement, subtopic hierarchy, and no repetition.
        """
        try:
            prompt = f"""You are analysing a Samacheer Kalvi Social Science — History chapter.
Read the full chapter text carefully and return a structured JSON plan.

Chapter: {lesson_title}

YOUR JOB:
1. Identify ALL main topics in the chapter (in the order they appear)
2. For each main topic, list ALL subtopics under it
3. Plan which topics go on which day (Day 1 to Day 4)
   - Each day covers 25 minutes of content (5 min spark + 5 min intro = 10 min fixed)
   - If a main topic is large, it can span 2 days — mark it as continuation
   - Day 4 must include final consolidation
4. Identify key terms, important dates, and map locations

CRITICAL RULES:
- Subtopics MUST be listed under their correct main topic
- Do NOT place a subtopic under the wrong main topic
- Do NOT skip any topic that appears in the chapter
- Causes, Course, and Results must be treated as separate main topics
- Each day must have a clear, distinct focus — no repetition across days

Return ONLY a valid JSON object. No explanation. No markdown. Just raw JSON.

JSON structure:
{{
  "main_topics": [
    {{
      "title": "Main topic title exactly as in chapter",
      "subtopics": ["subtopic 1", "subtopic 2", "subtopic 3"]
    }}
  ],
  "day_plan": {{
    "day1": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "focus": "One sentence describing what Day 1 covers",
      "continuation": false
    }},
    "day2": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 3", "subtopic 4"],
      "focus": "One sentence describing what Day 2 covers",
      "continuation": false
    }},
    "day3": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "focus": "One sentence describing what Day 3 covers",
      "continuation": false
    }},
    "day4": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "focus": "One sentence describing what Day 4 covers and chapter consolidation",
      "continuation": false
    }}
  }},
  "key_terms": ["term1", "term2", "term3"],
  "important_dates": ["date1 — event", "date2 — event"],
  "map_locations": ["location1", "location2"]
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
            # Strip any accidental markdown fences
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()

            plan = json.loads(raw)
            return plan

        except json.JSONDecodeError as e:
            print(f"❌ Chapter Analyser JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"❌ Chapter Analyser error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 1 — Preamble
    # -------------------------------------------------------------------------

    def _call_preamble(self, text, class_num, unit,
                       lesson_title, month, chapter_plan: dict):
        try:
            main_topics_str = "\n".join([
                f"  - {t['title']}: {', '.join(t['subtopics'])}"
                for t in chapter_plan.get("main_topics", [])
            ])
            key_terms = ", ".join(chapter_plan.get("key_terms", []))

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — History Lesson Plan. Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — History
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

CHAPTER STRUCTURE (from analyser — use this exactly):
{main_topics_str}

KEY TERMS: {key_terms}

Generate these sections in order:

1. HEADER BLOCK
<div class="sk-content-header">
  <h1>Lesson Plan — {lesson_title}</h1>
  <p class="sk-meta">
    Class {class_num} | Social Science — History |
    Unit {unit} | 5 Days × 35 Minutes
  </p>
</div>

2. CHAPTER OVERVIEW TABLE
<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Topics Covered (list from analyser)
</table>

3. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives specific to THIS chapter
  Each with one-line explanation tied to actual chapter content
</ul>

4. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives: chronology, source analysis, map skills, causal reasoning
  Each tied to actual chapter content
</ul>

5. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 content objectives — what students will explain/analyse after this chapter
  Based on actual main topics and subtopics from chapter structure above
</ul>

6. TEACHING AIDS
<h2>Part 5: Teaching Aids</h2>
<ul>
  All materials needed across 5 days — board, chalk, outline maps,
  timeline strips, flowchart templates, flashcards etc.
  Do NOT mention specific page numbers.
</ul>

OUTPUT RULES:
- Raw HTML only
- Start with <div class="sk-content-header">
- Stop after Teaching Aids </ul>
- Do NOT start any Day block
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
            print(f"❌ History LP preamble error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Calls 2-5 — Content Days 1-4
    # -------------------------------------------------------------------------

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_topics: dict, chapter_plan: dict):
        try:
            spark      = SPARK_STYLES[day_num]
            task       = STUDENT_TASK_STYLES[day_num]
            activity   = ACTIVITY_MAP.get(day_num, "group discussion")
            next_label = f"Day {day_num + 1}" if day_num < 4 else "Day 5 — Map Work and Book-back"

            # Extract day plan details from analyser output
            main_topic   = day_topics.get("main_topic", "")
            subtopics    = day_topics.get("subtopics", [])
            day_focus    = day_topics.get("focus", "")
            continuation = day_topics.get("continuation", False)

            subtopics_str = "\n".join([f"  - {s}" for s in subtopics])

            # Build continuation note if needed
            continuation_note = ""
            if continuation:
                continuation_note = f"""
⚠️ CONTINUATION NOTE:
This day starts by completing the topic carried over from Day {day_num - 1}.
Begin with: "Yesterday we started [topic]. Today we complete it before moving on."
Only after completing the carried-over topic, move to today's new subtopics.
"""

            # Day 4 special closing instruction
            closing_instruction = ""
            if day_num == 4:
                closing_instruction = """
⚠️ DAY 4 CLOSING — FULL CHAPTER RECAP:
The closing on Day 4 must recap the ENTIRE chapter across all 4 days.
Not just Day 4 content. Cover all main topics briefly.
Rapid-fire questions must span all 4 days.
"""

            prompt = f"""Generate ONLY Day {day_num} of the History lesson plan. Nothing else.
Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — History
Day      : {day_num} of 5
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S EXACT TOPIC PLAN — FOLLOW STRICTLY
═══════════════════════════════════════════════════════
Main Topic : {main_topic}
Subtopics  :
{subtopics_str}
Day Focus  : {day_focus}

CRITICAL: Cover ONLY the subtopics listed above.
Do NOT introduce subtopics from other days.
Do NOT repeat subtopics already covered in previous days.
Subtopics must appear UNDER their correct main topic — not mixed up.
{continuation_note}
{closing_instruction}
═══════════════════════════════════════════════════════

{CCQ_CFU_INSTRUCTION}

{TAMIL_INSTRUCTION}

═══════════════════════════════════════════════════════
LEAD QUESTION / OPENING QUESTION STYLE — DAY {day_num}
═══════════════════════════════════════════════════════
Style: {spark['style']}
{spark['instruction']}

IMPORTANT RENAME: This section is called "Lead Question" or "Opening Question"
NOT "Spark" or "Analogy". Use the heading: [0-5 min] Lead Question / Opening Question
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
STUDENT TASK STYLE — DAY {day_num}: {task['style']}
═══════════════════════════════════════════════════════
{task['instruction']}
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
FLOWCHART / MODEL RULE
═══════════════════════════════════════════════════════
For every concept that has a clear flow (cause→event→result):
Include a simple text-based flowchart inside <div class="board-work">
Label it: "Draw on Board — Model:"
Example: Cause 1 → Event → Consequence → Result
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
PAGE NUMBER RULE
═══════════════════════════════════════════════════════
Do NOT include any page numbers anywhere in this lesson plan.
Do NOT write "Page X" or "Pages X-Y" or "refer page" anywhere.
Instead reference content by topic name only.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
STUDENT RESPONSE WAIT TIME RULE
═══════════════════════════════════════════════════════
After EVERY question asked by the teacher — add this line:
<p><em>⏱ Wait [X] seconds before taking answers. Call on [N] students.</em></p>
CFU → Wait 10 seconds, call 2-3 students
CCQ → Wait 15 seconds, allow pair discussion first
Opening question → Wait 20 seconds, take 3-5 responses
═══════════════════════════════════════════════════════

DAY STRUCTURE — FOLLOW EXACTLY:

<h3 class="day-header">
  Day {day_num} — {main_topic}
</h3>
<p class="day-meta">Duration: 35 Minutes | History | {day_focus}</p>

<div class="day-block">

  <!-- ═══ SECTION 1: LEAD QUESTION / OPENING QUESTION (0-5 min) ═══ -->
  <div class="time-block">
    <strong>[0-5 min] Lead Question / Opening Question</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences using {spark['style']} style.
     Genuinely engaging — based on actual chapter content.
     End with the opening question.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same opening question. Same length.]"</p>
    </div>

    <p><em>⏱ Wait 20 seconds. Take 3-5 student responses. Large group discussion.</em></p>

  </div>

  <!-- ═══ SECTION 2: INTRODUCTION (5-10 min) ═══ -->
  <div class="time-block">
    <strong>[5-10 min] Introduction & Context Setting</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — introduce {main_topic} clearly.
     Connect to what students already know.
     Tell students what subtopics they will cover today.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same introduction.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Main Topic: {main_topic}<br/>
      Today's Subtopics: {', '.join(subtopics)}<br/>
      Objective: [One sentence learning objective for today]
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board Before Teaching:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [5 key terms from TODAY'S subtopics only — with Tamil meanings]
        </tbody>
      </table>
    </div>

    <!-- CFU after vocab -->
    [CFU block here — basic question about a key term just introduced]

  </div>

  <!-- ═══ SECTION 3: MAIN TEACHING (10-25 min) ═══ -->
  <div class="time-block">
    <strong>[10-25 min] Main Teaching & Activity</strong>

    [For EACH subtopic listed in today's plan:]

    <h4>[Subtopic name — exactly as listed in today's plan]</h4>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences explaining this subtopic clearly.
     This subtopic is UNDER {main_topic} — keep that hierarchy clear.
     Include concrete example or scenario.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — exact same explanation.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board — Model:</strong><br/>
      [Text-based flowchart for this subtopic]
    </div>

    <!-- CFU immediately after explanation -->
    [CFU block — basic recall about this subtopic]

    <!-- CCQ after CFU — deeper conceptual check -->
    [CCQ block — why/how question about this subtopic]

    [Repeat for each subtopic in today's plan]

    <!-- Activity block in the middle of teaching -->
    <div class="activity-block">
      <strong>Activity — {activity}:</strong>
      <p>[Step by step instructions. English only — no Tamil here.]</p>
      <p><em>Teacher circulates and checks understanding during activity.</em></p>
    </div>

    <!-- CFU after activity -->
    [CFU block about activity content]

  </div>

  <!-- ═══ SECTION 4: STUDENT TASK (25-30 min) ═══ -->
  <div class="time-block">
    <strong>[25-30 min] Student Task — {task['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — set up task using {task['style']}.
     Specific prompt. Clear time limit. Clear output.]"</p>

    <div class="board-work">
      <strong>Write on Board — Task Prompt:</strong><br/>
      [Exact task prompt — students can read from board]<br/>
      [Model starter sentence if written task]
    </div>

    <p class="student-says"><strong>Sample Answer:</strong><br/>
    "[Model answer — 2-3 sentences based on actual chapter content.]"</p>

    <!-- CCQ here -->
    [CCQ block]

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
              <p><strong>Task:</strong> Fill in the blanks</p>
              <p>"[sentence] _______ (word1 / word2)"</p>
              <p><strong>Word Bank:</strong> [4 key terms from today]</p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>Starter: "[Sentence starter from today's content]"</p>
            </td>
            <td>
              <p><strong>Task:</strong> Write independently</p>
              <p>"Explain [key concept from today] in 5 sentences."</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ═══ SECTION 5: CLOSING (30-35 min) ═══ -->
  <div class="time-block">
    <strong>[30-35 min] {"Overall Chapter Recap & Closing" if day_num == 4 else "Closing & Preview"}</strong>

    <p class="teacher-says"><strong>{"Full Chapter Rapid-Fire Recap" if day_num == 4 else "Rapid-Fire Recap"} (Teacher asks):</strong><br/>
    "{"[3 rapid-fire questions covering ALL key points from ALL 4 days. Full chapter review.]" if day_num == 4 else "[3 rapid-fire questions about today's subtopics only. One word or one sentence answers.]"}"</p>

    <p><em>⏱ Wait 5 seconds per question. Raise hands format. Keep it energetic.</em></p>

    <div class="board-work">
      <strong>Key Points from {"Full Chapter" if day_num == 4 else "Today"} (write on board):</strong><br/>
      1. [Key point 1 — one sentence]<br/>
      2. [Key point 2 — one sentence]<br/>
      3. [Key point 3 — one sentence]
    </div>

    <!-- Final CCQ before homework -->
    [CCQ block — final check on today's main concept]

    <div class="homework-block">
      <p class="teacher-says"><strong>Homework:</strong><br/>
      "[3-4 sentences — specific prompt. How many points. Own words. When to submit.]"</p>

      <div class="board-work">
        <strong>Homework Model Answer (write on board):</strong><br/>
        "[1-2 sentence model]"<br/>
        <em>Write in your own words. Do not copy.</em>
      </div>

      <p class="teacher-says"><strong>Preview {next_label}:</strong><br/>
      "[1-2 sentences — what tomorrow covers. If carrying over a topic, say so explicitly:
       'Tomorrow we continue with [topic name] and then move to [next topic].']"</p>
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS BEFORE FINISHING DAY {day_num}
═══════════════════════════════════════════════════════
✅ Covered ONLY these subtopics: {', '.join(subtopics)}
✅ All subtopics are under main topic: {main_topic}
✅ No subtopics from other days included
✅ Minimum 5 CFUs and 5 CCQs placed throughout
✅ Every CFU and CCQ has wait time instruction
✅ Lead Question used — NOT "Spark" or "Analogy"
✅ NO page numbers anywhere
✅ Tamil only in: Key Terms + Main explanations + Opening question
✅ At least one flowchart model in board-work per subtopic
✅ Student task style: {task['style']}
✅ Activity style: {activity}
✅ Sample answer included in student task section
{"✅ Closing is FULL CHAPTER RECAP across all 4 days" if day_num == 4 else "✅ Preview mentions next day topics clearly"}
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ Do NOT generate Day {day_num + 1}

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=10000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ History LP Day {day_num} error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 6 — Day 5: Map Work + Book-back
    # -------------------------------------------------------------------------

    def _call_day5(self, text, class_num, unit,
                   lesson_title, chapter_plan: dict):
        try:
            map_locations = ", ".join(chapter_plan.get("map_locations", []))
            important_dates = chapter_plan.get("important_dates", [])
            dates_str = "\n".join([f"  - {d}" for d in important_dates])
            task = STUDENT_TASK_STYLES[5]

            prompt = f"""Generate ONLY Day 5 of the History lesson plan.
Day 5 is always: Rapid Recall Quiz → Book-back Marking → Map Work → Test Prep → Closing.
Do NOT generate any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — History
Day      : 5 of 5
Duration : 35 minutes

MAP LOCATIONS FROM CHAPTER ANALYSER:
{map_locations if map_locations else "Identify from chapter text"}

IMPORTANT DATES FROM CHAPTER ANALYSER:
{dates_str if dates_str else "Identify from chapter text"}

<h3 class="day-header">Day 5 — Map Work & Book-back Exercises</h3>
<p class="day-meta">Duration: 35 Minutes | History | Evaluation Day</p>

<div class="day-block">

  <!-- ═══ RAPID RECALL QUIZ (0-5 min) ═══ -->
  <div class="time-block">
    <strong>[0-5 min] Rapid Recall Quiz</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "5 rapid-fire questions from Days 1-4. Write answers on a slip of paper."</p>

    <div class="board-work">
      <strong>5 Quiz Questions (write on board):</strong><br/>
      1. [Factual question — Day 1 content]<br/>
      2. [Factual question — Day 2 content]<br/>
      3. [Factual question — Day 3 content]<br/>
      4. [Factual question — Day 4 content]<br/>
      5. [Key date or key term from chapter]<br/>
      <br/>
      <strong>Answers:</strong> 1.[A] 2.[A] 3.[A] 4.[A] 5.[A]
    </div>

    <p><em>Students self-mark. Teacher notes who struggled.</em></p>
  </div>

  <!-- ═══ BOOK-BACK MARKING (5-20 min) ═══ -->
  <div class="time-block">
    <strong>[5-20 min] Book-back Exercise Marking</strong>

    <p><em>Teacher facilitates step-by-step marking.
    Note: The platform Q&A section has all book-back questions with complete model answers.</em></p>

    <h4>Section 1: Choose the Correct Answer</h4>
    <p>[3-4 key MCQ answers — explain WHY each is correct. Reference topic name not page.]</p>

    <h4>Section 2: Fill in the Blanks / Match the Following</h4>
    <p>[3-4 key answers — explain the connection. Reference topic names.]</p>

    <h4>Section 3: Short Answer Questions</h4>
    <p>[2-3 short answers — give model answer structure. Reference topic names.]</p>

    <div class="board-work">
      <strong>Write Correct Answers on Board:</strong><br/>
      [List key answers for student verification]
    </div>
  </div>

  <!-- ═══ MAP TEACHING (20-30 min) ═══ -->
  <div class="time-block">
    <strong>[20-30 min] Map Teaching Session</strong>

    <p><em>Teacher points on wall map first, then students mark outline maps.</em></p>

    <h4>Map Task 1 — [Primary map task based on chapter content]</h4>
    <p>[Exactly what to locate and mark — specific countries, cities, regions from chapter.]</p>

    <div class="board-work">
      <strong>Map Tips & Memory Tricks:</strong><br/>
      [3-5 specific memory tricks for key locations in this chapter.
       Make them catchy and chapter-specific.]<br/>
      <br/>
      <strong>Map Checklist — Mark All of These:</strong><br/>
      [Numbered list of all locations to mark and label]<br/>
      <br/>
      <em>Label all locations in CAPITAL LETTERS on outline map.</em>
    </div>

    <h4>Map Task 2 — [Secondary map task if applicable]</h4>
    <p>[Second set of locations based on chapter content.]</p>

  </div>

  <!-- ═══ STUDENT TASK + TEST PREP (30-35 min) ═══ -->
  <div class="time-block">
    <strong>[30-35 min] {task['style']} + Test Prep</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "Attempt these 2 questions independently in test conditions."</p>

    <div class="board-work">
      <strong>Practice Questions:</strong><br/>
      Q1. [1-mark or 2-mark question — different from book-back]<br/>
      Q2. [5-mark question — different from book-back]<br/>
      <br/>
      <strong>Test Series:</strong><br/>
      <em>For more practice, attempt the online question bank for this chapter.
      Use the timer for exam readiness.</em>
    </div>

    <p><em>Collect all submissions before closing.</em></p>
    <ul>
      <li>Completed notebook — all 5 days of notes</li>
      <li>Book-back exercises — answered and marked</li>
      <li>Outline map — all locations marked and labeled</li>
      <li>All homework from Days 1-4</li>
      <li>Today's practice questions</li>
    </ul>
  </div>

  <!-- ═══ CLOSING ═══ -->
  <div class="time-block">
    <strong>Closing</strong>
    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[2-3 sentences — congratulate students. Name 2-3 specific things they learned.
     Motivate for next chapter.]"</p>
  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="day-header">Day 5
- Map tasks based on ACTUAL chapter content and locations from analyser
- No Tamil in Day 5 — English only
- No page numbers anywhere
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
            print(f"❌ History LP Day 5 error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 7 — Assessment Summary
    # -------------------------------------------------------------------------

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, chapter_plan: dict):
        try:
            main_topics_str = ", ".join([
                t['title'] for t in chapter_plan.get("main_topics", [])
            ])
            key_terms = ", ".join(chapter_plan.get("key_terms", []))

            prompt = f"""Generate ONLY the Assessment Summary section.
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — History

CHAPTER MAIN TOPICS: {main_topics_str}
KEY TERMS: {key_terms}

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
       Questions about SUBJECT MATTER only — not tasks.
       Based on actual main topics from chapter analyser.]
    </tbody>
  </table>

  <h3>CFU Bank — Quick Reference</h3>
  <p><em>10 basic recall questions for revision — one per key concept:</em></p>
  <ol>
    [10 CFU questions with one-line answers — under 6 words each]
  </ol>

  <h3>CCQ Bank — Quick Reference</h3>
  <p><em>10 deeper conceptual questions for revision:</em></p>
  <ol>
    [10 CCQ questions with 1-2 sentence answers — under 8 words each]
  </ol>

  <h3>Written Assessment Task</h3>
  <p>[One meaningful written task covering the full chapter.]</p>
  <div class="board-work">
    <strong>Model Answer (write on board):</strong>
    <p>"[Sentence 1]"</p>
    <p>"[Sentence 2]"</p>
    <p>"[Sentence 3]"</p>
  </div>

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
          <p><strong>Task:</strong> Fill in blanks with word bank</p>
          <p><strong>Word Bank:</strong> {key_terms[:5] if key_terms else '[5 key terms]'}</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences</p>
          <p>Starter: "[Event] happened because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Structured essay</p>
          <p>"Explain [key chapter theme] with causes, events, consequences in 8-10 sentences."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed</li>
    <li>☐ All homework tasks submitted (Days 1-4)</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Outline map completed with all locations (Day 5)</li>
    <li>☐ Practice questions attempted (Day 5)</li>
    <li>☐ [Chapter-specific checklist item 1]</li>
    <li>☐ [Chapter-specific checklist item 2]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table MUST have exactly 5 rows with Tamil column
- CFU bank: 10 questions, under 6 words each
- CCQ bank: 10 questions, under 8 words each
- No page numbers anywhere
- Base everything on actual chapter content

Chapter Text:
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ History LP assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

history_lp_910_builder = HistoryLP910Builder()