"""
civics.py
---------
LP Builder for Samacheer Kalvi Social Science — Civics
Class 9 & 10

v1.0 — Based on teacher Civics LP sample (May 2026)

Key differences from History builder:
  - 3 days per chapter (not 5)
  - Day 3 type decided by Chapter Analyser (revision or new_content_and_revision)
  - Visual aid heavy — portraits, charts, flashcards
  - Choral response activities
  - Scenario-based CFUs (students shout answers)
  - Article numbers tested directly
  - No map work (Civics has no map exercises)
  - Mime activities for duties/rights
  - Constitution-style concept mapping on Day 3

API calls: 6 total
  Call 0 → Chapter Analyser  (JSON — chapter structure + day plan + day3 type)
  Call 1 → Preamble
  Call 2 → Day 1
  Call 3 → Day 2
  Call 4 → Day 3 (revision or new_content_and_revision — decided by analyser)
  Call 5 → Assessment
"""

import json
import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    SS_LP_SYSTEM_PROMPT,
    clean,
)


# ============================================================================
# CIVICS DISCIPLINE NOTES
# ============================================================================

CIVICS_DISCIPLINE_NOTES = """
CIVICS-SPECIFIC TEACHING NOTES:
- Connect every concept to real-life governance and students' daily lives
- Constitutional provisions need simple real examples before formal definitions
- Article numbers must be accurate — always reference the correct article
- Rights → Duties → Institutions is the key Civics chain
- Board flowcharts: Problem → Law/Policy → Institution → Outcome
- Visual aids are critical — portraits, charts, flashcards must be mentioned
- Scenario-based CFUs work best for Civics — give a situation, student identifies the law
- Choral response activities: teacher points to chart, students read aloud together
- Mime activities: students act out duties/rights physically
- Short answer questions in Civics ask to explain OR distinguish — prepare both
"""


# ============================================================================
# CIVICS SPARK STYLES — 3 days only
# ============================================================================

CIVICS_SPARK_STYLES = {
    1: {
        "style": "Real-life Analogy",
        "instruction": """Use a real-life scenario that connects to today's Civics topic.
Make it relatable — something students experience daily (school rules, traffic rules, elections).
End with a Big Question that connects the analogy to the constitutional concept.
Example structure: 'Imagine [scenario] → what happens without rules? → Big Question about today's topic'
Tell students WHY they are learning this and WHERE they will use it in real life.""",
    },
    2: {
        "style": "Object / Visual Trigger",
        "instruction": """Hold up or point to a specific object or visual aid related to today's topic.
Could be: the textbook, a newspaper headline, a portrait, a chart, a flag.
Ask students what they notice and what it means.
End with a Big Question connecting the object to today's constitutional concept.
Example structure: 'Hold up [object] → What do you notice? → Big Question'""",
    },
    3: {
        "style": "Rapid Fire Recall Quiz",
        "instruction": """Start with a rapid-fire keyword quiz reviewing Days 1 and 2.
Teacher shouts a keyword/phrase → students shout the answer.
Example: 'Father of Constitution!' → 'Ambedkar!' / 'Heart and Soul!' → 'Article 32!'
5-7 rapid fire pairs. Energetic. Standing format if possible.
Then transition: 'Today we put it all together.'""",
    },
}


# ============================================================================
# CIVICS STUDENT TASK STYLES — 3 days only
# ============================================================================

CIVICS_STUDENT_TASK_STYLES = {
    1: {
        "style": "Timeline Race / Quick Sorting",
        "instruction": """Give students flashcards or write items on board.
Students rush to arrange them in correct order (timeline) OR
Teacher calls out a scenario → students shout the correct category/article/term.
Example Timeline: 'Tape these dates in order: 1946 → 1949 → 1950'
Example Sorting: 'A person born in India in 1950 — which citizenship method?' → students: 'By Birth!'
Keep it energetic — standing, rushing, shouting format.""",
    },
    2: {
        "style": "Mime + One-Minute Paper",
        "instruction": """Mime activity first — students physically act out a duty or right.
Example: 'Show me Fundamental Duty — protect environment' → students mime picking up litter.
Then One-Minute Paper: students write down the most important thing they learned today.
Specific prompt on board — not open-ended.
Example: 'Write the most important Fundamental Duty every student should follow and WHY.'""",
    },
    3: {
        "style": "Big Unit Quiz",
        "instruction": """5 high-impact questions covering the full chapter.
Mix of types: list, name, identify, explain, distinguish.
Students write answers independently in test conditions (5 mins).
Teacher reads correct answers aloud — students self-mark.
End with: students write 3-2-1 reflection (3 things learned, 2 leaders, 1 key article).""",
    },
}


# ============================================================================
# CIVICS ACTIVITY MAP — 3 days
# ============================================================================

CIVICS_ACTIVITY_MAP = {
    1: "Choral response (teacher points to chart → students read aloud) + Quick sorting activity (teacher gives scenario → students identify correct citizenship method/right/article)",
    2: "Mime activity (students act out a duty) + Emergency Buzz (teacher describes scenario → students shout correct article number)",
    3: "Constitution Tree concept map (groups label parts of the constitution on board) + Big Unit Quiz",
}


# ============================================================================
# CIVICS LP BUILDER CLASS
# ============================================================================

class CivicsLP910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Civics LP Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Civics LP for Class 9 & 10.
        Makes 6 API calls:
            Call 0: Chapter Analyser (JSON)
            Call 1: Preamble
            Call 2: Day 1
            Call 3: Day 2
            Call 4: Day 3 (revision or new_content_and_revision)
            Call 5: Assessment
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        total_calls = 6
        print(f"      [Civics LP 910 v1] Generating: {lesson_title}")
        print(f"      [Civics LP 910 v1] 6 API calls: Analyser + Preamble + Day1 + Day2 + Day3 + Assessment")

        parts = []

        # ── Call 0: Chapter Analyser ──────────────────────────────────────────
        print(f"      [Civics LP] Call 0/{total_calls}: Chapter Analyser...")
        chapter_plan = self._call_chapter_analyser(text, lesson_title)
        if not chapter_plan:
            print(f"         ❌ Chapter Analyser failed — aborting LP")
            return None
        print(f"         ✅ Chapter plan ready — {len(chapter_plan.get('main_topics', []))} main topics | Day 3 type: {chapter_plan.get('day3_type', 'revision')}")

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [Civics LP] Call 1/{total_calls}: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, month, chapter_plan
        )
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting LP")
            return None

        # ── Calls 2-4: Days 1-3 ──────────────────────────────────────────────
        for day_num in range(1, 4):
            call_num = day_num + 1
            print(f"      [Civics LP] Call {call_num}/{total_calls}: Day {day_num}...")
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

        # ── Call 5: Assessment ────────────────────────────────────────────────
        print(f"      [Civics LP] Call 5/{total_calls}: Assessment...")
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
        print(f"      [Civics LP 910 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 0 — Deep Chapter Analyser
    # -------------------------------------------------------------------------

    def _call_chapter_analyser(self, text: str, lesson_title: str) -> Optional[dict]:
        """
        Reads the full Civics chapter and returns a structured JSON plan.
        Also decides Day 3 type based on content size.
        """
        try:
            prompt = f"""You are analysing a Samacheer Kalvi Social Science — Civics chapter.
Read the full chapter text carefully and return a structured JSON plan.

Chapter: {lesson_title}

YOUR JOB:
1. Identify ALL main topics in the chapter (in order they appear)
2. For each main topic, list ALL subtopics and key article numbers under it
3. Plan which topics go on which day (Day 1 and Day 2 only for new content)
4. Decide Day 3 type:
   - "revision" → if Days 1 and 2 cover all content fully
   - "new_content_and_revision" → if there is remaining content for Day 3
5. Identify key constitutional terms, article numbers, and important dates

CRITICAL RULES:
- Subtopics MUST be under their correct main topic
- Article numbers must be accurate and placed under correct topic
- Rights, Duties, and Powers must be treated as separate main topics
- Day 1 and Day 2 must each have a distinct clear focus
- Day 3 type must be honest — if content is large, use "new_content_and_revision"

Return ONLY valid JSON. No explanation. No markdown. Just raw JSON.

JSON structure:
{{
  "main_topics": [
    {{
      "title": "Main topic title exactly as in chapter",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "key_articles": ["Article 32", "Article 368"]
    }}
  ],
  "day_plan": {{
    "day1": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "key_articles": ["Article X", "Article Y"],
      "focus": "One sentence describing Day 1 focus",
      "visual_aids": ["Portrait of X", "Chart showing Y"],
      "continuation": false
    }},
    "day2": {{
      "main_topic": "Exact main topic title",
      "subtopics": ["subtopic 1", "subtopic 2"],
      "key_articles": ["Article X", "Article Y"],
      "focus": "One sentence describing Day 2 focus",
      "visual_aids": ["Chart showing X"],
      "continuation": false
    }},
    "day3": {{
      "main_topic": "Revision and Assessment OR remaining topic title",
      "subtopics": ["subtopic if new content" ],
      "key_articles": [],
      "focus": "One sentence describing Day 3 focus",
      "visual_aids": ["Constitution Tree diagram"],
      "continuation": false
    }}
  }},
  "day3_type": "revision",
  "key_terms": ["term1", "term2"],
  "key_articles": ["Article 32 — Constitutional Remedies", "Article 368 — Amendments"],
  "important_dates": ["date — event"],
  "visual_aids_needed": ["Portrait of Ambedkar", "Preamble Chart"]
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
            print(f"❌ Civics Analyser JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"❌ Civics Analyser error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 1 — Preamble
    # -------------------------------------------------------------------------

    def _call_preamble(self, text, class_num, unit,
                       lesson_title, month, chapter_plan: dict):
        try:
            main_topics_str = "\n".join([
                f"  - {t['title']}: {', '.join(t.get('subtopics', []))}"
                f" | Articles: {', '.join(t.get('key_articles', []))}"
                for t in chapter_plan.get("main_topics", [])
            ])
            key_terms    = ", ".join(chapter_plan.get("key_terms", []))
            key_articles = ", ".join(chapter_plan.get("key_articles", []))
            visual_aids  = ", ".join(chapter_plan.get("visual_aids_needed", []))

            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science — Civics Lesson Plan. Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Civics
Month    : {month if month else 'As scheduled'}
Duration : 3 Days × 35 Minutes = 105 Minutes Total

CHAPTER STRUCTURE (from analyser):
{main_topics_str}

KEY CONSTITUTIONAL TERMS: {key_terms}
KEY ARTICLES: {key_articles}
VISUAL AIDS NEEDED: {visual_aids}

Generate these sections:

1. HEADER BLOCK
<div class="sk-content-header">
  <h1>Lesson Plan — {lesson_title}</h1>
  <p class="sk-meta">
    Class {class_num} | Social Science — Civics |
    Unit {unit} | 3 Days × 35 Minutes
  </p>
</div>

2. CHAPTER OVERVIEW TABLE
<h2>Part 1: Chapter Overview</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Main Topics Covered | Key Articles Covered
</table>

3. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives specific to THIS Civics chapter
  (Self identity as citizen, respecting all religions, power of We the People etc.)
  Each with one-line explanation tied to actual chapter content
</ul>

4. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives: timeline building, word analysis, decision making,
  article identification, scenario analysis
  Each tied to actual chapter content
</ul>

5. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 content objectives — what students will explain/identify/list after this chapter
  Based on actual main topics and subtopics from analyser
  Use action verbs: Understand, Identify, Name, List, Explain, Distinguish
</ul>

6. TEACHING AIDS
<h2>Part 5: Teaching Aids</h2>
<ul>
  All materials needed across 3 days
  Include: textbook, portraits, preamble chart, flashcards, timeline strips,
  citizenship cards, board, chalk
  Based on visual aids identified by analyser: {visual_aids}
  Do NOT mention page numbers
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
            print(f"❌ Civics LP preamble error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Calls 2-4 — Content Days 1-3
    # -------------------------------------------------------------------------

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_topics: dict, chapter_plan: dict):
        try:
            spark      = CIVICS_SPARK_STYLES[day_num]
            task       = CIVICS_STUDENT_TASK_STYLES[day_num]
            activity   = CIVICS_ACTIVITY_MAP.get(day_num, "group discussion")
            day3_type  = chapter_plan.get("day3_type", "revision")

            main_topic   = day_topics.get("main_topic", "")
            subtopics    = day_topics.get("subtopics", [])
            key_articles = day_topics.get("key_articles", [])
            day_focus    = day_topics.get("focus", "")
            visual_aids  = day_topics.get("visual_aids", [])
            continuation = day_topics.get("continuation", False)

            subtopics_str    = "\n".join([f"  - {s}" for s in subtopics])
            key_articles_str = "\n".join([f"  - {a}" for a in key_articles])
            visual_aids_str  = ", ".join(visual_aids) if visual_aids else "Textbook, Board"

            # Day 3 special instructions
            day3_instruction = ""
            if day_num == 3:
                if day3_type == "revision":
                    day3_instruction = """
═══════════════════════════════════════════════════════
DAY 3 TYPE: FULL REVISION + ASSESSMENT
═══════════════════════════════════════════════════════
All chapter content was covered in Days 1 and 2.
Day 3 is entirely for revision and assessment.

Structure:
[0-5 min]   Rapid Fire Recall Quiz (spark)
[5-17 min]  Constitution Tree concept map — groups label parts on board
[17-30 min] Big Unit Quiz — 5 high-impact questions, students write independently
[30-35 min] 3-2-1 Closing reflection + Final Assessment Questions

Do NOT introduce any new content today.
═══════════════════════════════════════════════════════
"""
                else:
                    day3_instruction = """
═══════════════════════════════════════════════════════
DAY 3 TYPE: NEW CONTENT + REVISION
═══════════════════════════════════════════════════════
Day 3 has remaining new content to cover PLUS revision.

Structure:
[0-5 min]   Rapid Fire Recall Quiz (spark)
[5-20 min]  Complete remaining new content from today's topic plan
[20-30 min] Constitution Tree or concept map — connecting all topics
[30-35 min] Big Quiz (3 questions) + 3-2-1 Closing reflection

Cover new content FIRST, then revision.
═══════════════════════════════════════════════════════
"""

            continuation_note = ""
            if continuation:
                continuation_note = f"""
⚠️ CONTINUATION NOTE:
This day starts by completing the topic carried over from Day {day_num - 1}.
Begin with: "Yesterday we started [topic]. Today we complete it before moving on."
"""

            next_label = f"Day {day_num + 1}" if day_num < 3 else "end of chapter"

            prompt = f"""Generate ONLY Day {day_num} of the Civics lesson plan. Nothing else.
Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Civics
Day      : {day_num} of 3
Duration : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S EXACT TOPIC PLAN — FOLLOW STRICTLY
═══════════════════════════════════════════════════════
Main Topic   : {main_topic}
Subtopics    :
{subtopics_str if subtopics_str else "  [Revision — no new subtopics]"}
Key Articles :
{key_articles_str if key_articles_str else "  [Review all articles from Days 1-2]"}
Day Focus    : {day_focus}
Visual Aids  : {visual_aids_str}
{continuation_note}
{day3_instruction}
═══════════════════════════════════════════════════════

{self._get_cfu_ccq_instruction()}

{self._get_tamil_instruction()}

═══════════════════════════════════════════════════════
LEAD QUESTION / OPENING QUESTION — DAY {day_num}
═══════════════════════════════════════════════════════
Style: {spark['style']}
{spark['instruction']}
Heading must be: [0-5 min] Lead Question / Opening Question
Include Big Question at the end of the spark.
Include: "Why are students learning this? Where will they use it in real life?"
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
STUDENT TASK — DAY {day_num}: {task['style']}
═══════════════════════════════════════════════════════
{task['instruction']}
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
CIVICS-SPECIFIC RULES
═══════════════════════════════════════════════════════
- Article numbers MUST be accurate — double check before writing
- Every constitutional term needs a simple real-life example first
- Visual aids must be explicitly mentioned: when to hold up, when to point
- Choral response: teacher points → students read aloud together
- Scenario CFU: teacher gives situation → students identify correct article/method
- Mime activities: students physically act out duties or rights
- NO page numbers anywhere
- Board flowcharts: Problem → Law → Institution → Outcome chain
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
WAIT TIME RULE
═══════════════════════════════════════════════════════
After EVERY question add:
<p><em>⏱ Wait [X] seconds. Call on [N] students.</em></p>
CFU → Wait 10 seconds, 2-3 students
CCQ → Wait 15 seconds, pair discussion first
Opening question → Wait 20 seconds, 3-5 responses
═══════════════════════════════════════════════════════

DAY STRUCTURE:

<h3 class="day-header">
  Day {day_num} — {main_topic}
</h3>
<p class="day-meta">Duration: 35 Minutes | Civics | {day_focus}</p>

<div class="day-block">

  <!-- ═══ SECTION 1: LEAD QUESTION / OPENING (0-5 min) ═══ -->
  <div class="time-block">
    <strong>[0-5 min] Lead Question / Opening Question — {spark['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences using {spark['style']} style.
     Genuinely engaging — based on actual Civics content.
     Include WHY students are learning this and WHERE they use it.
     End with Big Question.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same opening. Same length.]"</p>
    </div>

    <p><em>⏱ Wait 20 seconds. Take 3-5 student responses.</em></p>

  </div>

  <!-- ═══ SECTION 2: INTRODUCTION (5-10 min) ═══ -->
  <div class="time-block">
    <strong>[5-10 min] Introduction & Context Setting</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — introduce {main_topic} clearly.
     Reference visual aids: {visual_aids_str}.
     Tell students exactly what subtopics they cover today.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same introduction.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Main Topic: {main_topic}<br/>
      Today's Subtopics: {', '.join(subtopics) if subtopics else 'Revision'}<br/>
      Key Articles: {', '.join(key_articles) if key_articles else 'All covered articles'}<br/>
      Objective: [One sentence learning objective]
    </div>

    <div class="vocab-block">
      <strong>Key Constitutional Terms — Write on Board:</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
        </thead>
        <tbody>
          [5 key constitutional terms from TODAY's subtopics with Tamil meanings]
        </tbody>
      </table>
    </div>

    [CFU after vocab — basic question about a key term]

  </div>

  <!-- ═══ SECTION 3: MAIN TEACHING (10-25 min) ═══ -->
  <div class="time-block">
    <strong>[10-25 min] Main Teaching & Activity</strong>

    [For EACH subtopic in today's plan:]

    <h4>[Subtopic name — exactly as listed]</h4>

    <div class="board-work">
      <strong>Visual Aid — {visual_aids_str}:</strong><br/>
      [Explicit instruction: when to hold up portrait / point to chart / show flashcard]
    </div>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain this subtopic with simple real-life example first.
     Then formal constitutional definition.
     Reference correct article numbers from: {key_articles_str if key_articles_str else 'chapter content'}.
     Keep {main_topic} hierarchy clear.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — exact same explanation.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board — Model:</strong><br/>
      [Text-based flowchart: Problem → Law/Article → Institution → Outcome]
    </div>

    [CFU — scenario-based: teacher gives situation → students identify correct article/method]
    [CCQ — deeper: why/how question about this subtopic]

    [Repeat for each subtopic]

    <!-- Activity -->
    <div class="activity-block">
      <strong>Activity — {activity}:</strong>
      <p>[Step by step instructions. English only — no Tamil here.]</p>
      <p><em>⏱ [Time box for activity]. Teacher circulates.</em></p>
    </div>

    [CFU after activity]

  </div>

  <!-- ═══ SECTION 4: STUDENT TASK (25-30 min) ═══ -->
  <div class="time-block">
    <strong>[25-30 min] Student Task — {task['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — set up {task['style']} task.
     Specific prompt. Clear time limit. Clear output.]"</p>

    <div class="board-work">
      <strong>Write on Board — Task:</strong><br/>
      [Exact task prompt students can read from board]
    </div>

    <p class="student-says"><strong>Sample Answer / Expected Response:</strong><br/>
    "[Model answer based on actual chapter content — 2-3 sentences]"</p>

    [CCQ here]

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
              <p><strong>Task:</strong> Fill in blanks with word bank</p>
              <p>"[sentence] _______ (word1 / word2)"</p>
              <p><strong>Word Bank:</strong> [4 key terms from today]</p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>Starter: "[Constitutional concept] means _______."</p>
            </td>
            <td>
              <p><strong>Task:</strong> Write independently</p>
              <p>"Explain [key concept] with correct article number and real example."</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ═══ SECTION 5: CLOSING (30-35 min) ═══ -->
  <div class="time-block">
    <strong>[30-35 min] {"Overall Chapter Recap & Closing" if day_num == 3 else "Closing & Preview"}</strong>

    {"<p><em>Day 3 Closing — Full Chapter Recap across all 3 days.</em></p>" if day_num == 3 else ""}

    <p class="teacher-says"><strong>{"Final Assessment Questions" if day_num == 3 else "Rapid-Fire Recap"} (Teacher asks):</strong><br/>
    "{"[5 final assessment questions covering full chapter. Students write independently. Teacher reads answers aloud.]" if day_num == 3 else "[3 rapid-fire questions about today's subtopics. One word or one sentence. Raise hands format.]"}"</p>

    <p><em>⏱ {"5 minutes for quiz. Self-mark after." if day_num == 3 else "Wait 5 seconds per question. Keep energetic."}</em></p>

    {"<div class='board-work'><strong>3-2-1 Reflection (write on board):</strong><br/>3 things learned from this chapter<br/>2 leaders / articles you remember<br/>1 way you will use this as a citizen</div>" if day_num == 3 else ""}

    <div class="board-work">
      <strong>Key Points from {"Full Chapter" if day_num == 3 else "Today"} (write on board):</strong><br/>
      1. [Key point 1 — one sentence]<br/>
      2. [Key point 2 — one sentence]<br/>
      3. [Key point 3 — one sentence]
    </div>

    [Final CCQ]

    {"" if day_num == 3 else f'''<div class="homework-block">
      <p class="teacher-says"><strong>Homework:</strong><br/>
      "[3-4 sentences — specific written prompt. Own words. When to submit.]"</p>
      <div class="board-work">
        <strong>Homework Model Answer:</strong><br/>
        "[1-2 sentence model]"<br/>
        <em>Write in your own words. Do not copy.</em>
      </div>
      <p class="teacher-says"><strong>Preview {next_label}:</strong><br/>
      "[1-2 sentences — what tomorrow covers.]"</p>
    </div>'''}

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS BEFORE FINISHING DAY {day_num}
═══════════════════════════════════════════════════════
✅ Covered ONLY these subtopics: {', '.join(subtopics) if subtopics else 'Revision topics'}
✅ All article numbers are ACCURATE
✅ Visual aids explicitly mentioned with instructions
✅ Choral response activity included
✅ Scenario-based CFUs included (situation → student identifies article/method)
✅ Minimum 5 CFUs and 5 CCQs with wait times
✅ Lead Question used — NOT "Spark"
✅ NO page numbers anywhere
✅ Tamil only in: Key Terms + Main explanations + Opening question
✅ Flowchart model: Problem → Law → Institution → Outcome
✅ Sample answer in student task
{"✅ Day 3: Revision/quiz structure followed" if day_num == 3 else f"✅ Preview of Day {day_num + 1} included"}
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ Do NOT generate Day {day_num + 1 if day_num < 3 else 'beyond 3'}

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
            print(f"❌ Civics LP Day {day_num} error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 5 — Assessment Summary
    # -------------------------------------------------------------------------

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, chapter_plan: dict):
        try:
            main_topics_str = ", ".join([
                t['title'] for t in chapter_plan.get("main_topics", [])
            ])
            key_terms    = ", ".join(chapter_plan.get("key_terms", []))
            key_articles = ", ".join(chapter_plan.get("key_articles", []))

            prompt = f"""Generate ONLY the Assessment Summary section for this Civics chapter.
Do NOT repeat any day content.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — Civics
Total Days: 3

CHAPTER MAIN TOPICS: {main_topics_str}
KEY TERMS: {key_terms}
KEY ARTICLES: {key_articles}

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
      [3 rows — Day 1, Day 2, Day 3.
       Questions about SUBJECT MATTER — scenario-based where possible.
       Based on actual topics and articles from analyser.
       Tamil version of question in last column.]
    </tbody>
  </table>

  <h3>CFU Bank — Quick Reference</h3>
  <p><em>10 basic recall questions for revision:</em></p>
  <ol>
    [10 CFU questions — under 6 words each.
     Mix of: who/what/which/when questions.
     Include article numbers where relevant.
     Based on actual chapter content.]
  </ol>

  <h3>CCQ Bank — Quick Reference</h3>
  <p><em>10 deeper scenario-based questions for revision:</em></p>
  <ol>
    [10 CCQ questions — scenario-based where possible.
     Example: 'If a person is illegally arrested, which article protects them?'
     Based on actual chapter content.]
  </ol>

  <h3>Big Unit Quiz — 5 Questions</h3>
  <p><em>High-impact questions covering the full chapter:</em></p>
  <ol>
    [5 questions — mix of: list, name, identify, explain, distinguish.
     Cover different main topics from the chapter.
     Based on actual chapter content.]
  </ol>
  <div class="board-work">
    <strong>Model Answers (write on board after quiz):</strong>
    <p>1. [Answer 1]</p>
    <p>2. [Answer 2]</p>
    <p>3. [Answer 3]</p>
    <p>4. [Answer 4]</p>
    <p>5. [Answer 5]</p>
  </div>

  <h3>3-2-1 Final Reflection</h3>
  <div class="board-work">
    <strong>Write on Board:</strong><br/>
    3 things you learned from this chapter<br/>
    2 leaders / articles you will always remember<br/>
    1 way you will use this knowledge as a citizen of India
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
          <p><strong>Word Bank:</strong> [5 key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences</p>
          <p>Starter: "[Constitutional concept] is important because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Structured essay</p>
          <p>"Explain [key chapter theme] with correct articles, examples, and significance in 8-10 sentences."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 3 days of notes completed in classwork notebook</li>
    <li>☐ All homework tasks submitted (Days 1-2)</li>
    <li>☐ Big Unit Quiz attempted (Day 3)</li>
    <li>☐ 3-2-1 Reflection written (Day 3)</li>
    <li>☐ Key article numbers memorised: {key_articles}</li>
    <li>☐ [Chapter-specific checklist item]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table MUST have exactly 3 rows with Tamil column
- CFU bank: 10 questions, under 6 words each
- CCQ bank: 10 scenario-based questions
- Big Unit Quiz: exactly 5 questions with model answers
- No page numbers anywhere
- Article numbers must be accurate
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
            print(f"❌ Civics LP assessment error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_cfu_ccq_instruction(self) -> str:
        return """
═══════════════════════════════════════════════════════
CFU AND CCQ — CIVICS SPECIFIC
═══════════════════════════════════════════════════════

Each day must include BOTH types — minimum 5 CFU + 5 CCQ:

── CFU (Check For Understanding) ──────────────────────
Basic recall. Asked immediately after explaining something.
For Civics — often scenario-based: teacher gives situation → student identifies article/method.

FORMAT:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <p class="teacher-says">"[Simple factual question or scenario — under 6 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One word, article number, or one sentence]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

── CCQ (Concept Check Question) ───────────────────────
Deeper understanding. Tests WHY or HOW.
For Civics — often: 'Why is Article X important?' or 'What happens if Right Y is violated?'

FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="teacher-says">"[Deeper question — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer with article reference]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion first.</em></p>
</div>

CIVICS CFU EXAMPLES (scenario-based):
✅ "If illegally arrested — which article protects you?"
✅ "Person born in India in 1950 — citizenship method?"
✅ "State government fails — which article applies?"

NEVER use ICQs:
❌ "Do you understand?" ❌ "How many sentences?"
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

❌ NEVER in: activity instructions, board work, time notes, closing
Tamil mirror: same sentences, same length, same detail. Real Unicode only.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# Singleton instance
# ============================================================================

civics_lp_910_builder = CivicsLP910Builder()