"""
ss_lp_builder.py
----------------
Lesson Plan Generator for Samacheer Kalvi Social Science (Classes 6-12).
Handles History, Geography, Civics, Economics disciplines.

v6.0 — Complete rewrite based on team feedback (May 2026)

Structure:
  - 5 days per chapter (35 minutes per day)
  - Day 1-4: Content days with Lead/Spark → Teaching → CCQs → Closing
  - Day 5: Fixed template — Map work + Book-back exercises
  - 10 CCQs randomly placed per day (concept check questions)
  - Targeted Tamil scaffolding:
      ✅ Key terms     → Tamil meaning
      ✅ Main explanation → Tamil mirror
      ✅ Opening question → Tamil
      ❌ Activity instructions → English only
      ❌ Time notes / page numbers → English only
  - API calls: 7 total (Preamble + Day 1 + Day 2 + Day 3 + Day 4 + Day 5 + Assessment)

Key changes from v5:
  - 3 days × 30 min  →  5 days × 35 min
  - Full Tamil mirror everywhere → Targeted Tamil only
  - Generic warm-up → Lead/Spark/Opening question format
  - Added 10 CCQs per day randomly in content
  - Day 5 is a fixed map + book-back template
  - Group activities, flowcharts, bucket activities added
  - Page numbers referenced in every activity
"""

import re
import anthropic
from typing import Optional
from ..config import settings


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SS_LP_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Social Science teacher
with deep knowledge of Tamil Nadu state board curriculum and activity-based
learning methods used in Indian government schools.

Create a detailed, practical, script-by-script lesson plan so that even a
brand-new inexperienced teacher can walk into class and deliver a confident,
effective 35-minute session just by following it.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Tamil script must be real Tamil Unicode — NOT transliteration"""


# ============================================================================
# CCQ INSTRUCTION BLOCK — injected into every day prompt
# ============================================================================

CCQ_INSTRUCTION = """
═══════════════════════════════════════════════════════
CCQ — CONCEPT CHECK QUESTIONS (CRITICAL)
═══════════════════════════════════════════════════════

You MUST include exactly 10 CCQs spread randomly throughout this day's content.
CCQs are short, sharp questions the teacher asks mid-lesson to check if students
are still concentrating and following.

FORMAT for each CCQ — use this exact HTML block:

<div class="ccq-block">
  <strong>⚡ CCQ (Concept Check):</strong>
  <p class="teacher-says">"[Short direct question about what was just taught — 1 sentence]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Short complete answer — 1-2 sentences]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
</div>

RULES for CCQs:
- Place them RANDOMLY — not all bunched together
- After explaining a concept → drop a CCQ
- After drawing a flowchart → drop a CCQ
- After a group activity → drop a CCQ
- Before closing → drop a CCQ
- Each CCQ must be based on content just taught (not random)
- Keep each CCQ under 10 words
- No CCQ should repeat another
- Tamil version mandatory for every CCQ
═══════════════════════════════════════════════════════
"""

# ============================================================================
# TAMIL SCAFFOLDING INSTRUCTION — targeted, not everywhere
# ============================================================================

TAMIL_INSTRUCTION = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES — TARGETED ONLY
═══════════════════════════════════════════════════════

Tamil appears in EXACTLY these places — nowhere else:

✅ 1. KEY TERMS TABLE — Tamil meaning column (every day)
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph after English explanation
✅ 3. OPENING/LEAD QUESTION — Tamil version after English question

❌ Activity instructions → English only
❌ Group task descriptions → English only
❌ Time notes → English only
❌ Page numbers → English only
❌ Board work headings → English only
❌ Homework task description → English only

Tamil mirror rule (where Tamil IS used):
- Same sentences. Same detail. Same length as English.
- NOT a summary. Full mirror.
- Real Tamil Unicode script only — never transliteration.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# SS LP BUILDER CLASS
# ============================================================================

class SSLPBuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ SS LP Builder v6.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Social Science LP for a chapter.
        Makes 7 API calls:
            Preamble + Day 1 + Day 2 + Day 3 + Day 4 + Day 5 + Assessment

        Args:
            text:     Clean chapter text from EPUB extractor
            metadata: Dict with class, unit, lesson_title, discipline etc.

        Returns:
            Combined HTML string, or None on failure.
        """
        lesson_title       = metadata.get("lesson_title", "Unknown")
        class_num          = metadata.get("class", "")
        unit               = metadata.get("unit", "")
        discipline         = metadata.get("discipline", "history")
        discipline_display = discipline.title()
        month              = metadata.get("month", "")

        total_calls = 7
        print(f"      [SS LP v6] Generating: {discipline_display} | {lesson_title}")
        print(f"      [SS LP v6] 7 API calls: Preamble + Day1 + Day2 + Day3 + Day4 + Day5 + Assessment")

        parts = []

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [SS LP] Call 1/{total_calls}: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, discipline_display, month
        )
        if preamble:
            parts.append(self._clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting LP")
            return None

        # ── Calls 2–5: Content Days 1–4 ──────────────────────────────────────
        for day_num in range(1, 5):
            call_num = day_num + 1
            print(f"      [SS LP] Call {call_num}/{total_calls}: Day {day_num}...")
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title,
                discipline_display, day_num
            )
            if day_html:
                parts.append(self._clean(day_html))
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        # ── Call 6: Day 5 (Map + Book-back) ──────────────────────────────────
        print(f"      [SS LP] Call 6/{total_calls}: Day 5 (Map + Book-back)...")
        day5_html = self._call_day5(
            text, class_num, unit, lesson_title, discipline_display
        )
        if day5_html:
            parts.append(self._clean(day5_html))
            print(f"         ✅ Day 5 ({len(day5_html)} chars)")
        else:
            print(f"         ❌ Day 5 failed — continuing")

        # ── Call 7: Assessment ────────────────────────────────────────────────
        print(f"      [SS LP] Call 7/{total_calls}: Assessment...")
        assessment = self._call_assessment(
            text, class_num, unit, lesson_title, discipline_display
        )
        if assessment:
            parts.append(self._clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [SS LP v6] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — Preamble
    # -------------------------------------------------------------------------

    def _call_preamble(self, text, class_num, unit,
                       lesson_title, discipline_display, month):
        try:
            prompt = f"""Generate ONLY the opening preamble section of a Samacheer Kalvi
Social Science Lesson Plan. Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — {discipline_display}
Month    : {month if month else 'As scheduled'}
Duration : 5 Days × 35 Minutes = 175 Minutes Total

Generate these sections in order:

1. HEADER BLOCK
<div class="sk-content-header">
  <h1>Lesson Plan — {lesson_title}</h1>
  <p class="sk-meta">
    Class {class_num} | Social Science — {discipline_display} |
    Unit {unit} | 5 Days × 35 Minutes
  </p>
</div>

2. GENERAL INFORMATION TABLE
<h2>Part 1: General Information</h2>
<table>
  Rows: Class | Subject | Discipline | Unit/Chapter Title |
        Month | Total Teaching Hours | Session Duration |
        Teaching Hours per session
</table>

3. VALUE-BASED OBJECTIVES
<h2>Part 2: Value-Based Objectives</h2>
<ul>
  3-4 value objectives specific to this chapter
  (e.g. Social Justice, Peace Advocacy, Empathy, Global Cooperation)
  Each with a one-line explanation tied to chapter content
</ul>

4. SKILL OBJECTIVES
<h2>Part 3: Skill Objectives</h2>
<ul>
  3-4 skill objectives specific to this chapter
  (e.g. Map Skills, Source Analysis, Chronology, Causal Reasoning)
  Each with a one-line explanation tied to chapter content
</ul>

5. LEARNING OBJECTIVES
<h2>Part 4: Learning Objectives</h2>
<ul>
  4-5 content knowledge objectives — what students will be able to
  explain, analyze, evaluate after completing this chapter
</ul>

6. TEACHING AIDS
<h2>Part 5: Teaching Aids</h2>
<ul>
  All materials needed across all 5 days —
  textbook, maps, charts, flowcharts, colored chalk,
  outline maps, timeline strips, flashcards, board etc.
</ul>

OUTPUT RULES:
- Raw HTML only
- Start with <div class="sk-content-header">
- Stop after Teaching Aids </ul>
- Do NOT start any Day block
- Base all objectives on actual chapter content below

Chapter Text:
---
{text[:6000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ SS LP preamble error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Calls 2–5 — Content Days 1–4
    # -------------------------------------------------------------------------

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          discipline_display, day_num):
        try:
            # What each day focuses on
            focus_map = {
                1: "Introduction, background context, and first major topic of the chapter (Pages 1-4 approx)",
                2: "Causes, key events, and main concepts — first half of core content (Pages 4-8 approx)",
                3: "Results, consequences, and major turning points — second half of core content (Pages 8-10 approx)",
                4: "Final sections, analysis, source-based discussion, and chapter consolidation (Pages 10-12 approx)",
            }

            # Activity style per day
            activity_map = {
                1: "flowchart on board, real-life analogy opening, large group discussion",
                2: "group activity (3 groups answer different questions), active note-taking, student-led recap",
                3: "bucket activity (colored groups — Red/Yellow/Green), map pointing, pair discussion",
                4: "source analysis, timeline activity, student presentation of flowchart they prepared",
            }

            focus    = focus_map.get(day_num, "chapter content")
            activity = activity_map.get(day_num, "group discussion")
            next_day = f"Day {day_num + 1}" if day_num < 4 else "Day 5 (Map Work and Book-back Exercises)"

            prompt = f"""Generate ONLY Day {day_num} of the lesson plan. Nothing else.
Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — {discipline_display}
Day      : {day_num} of 5
Duration : 35 minutes
Focus    : {focus}
Activity style today: {activity}

{CCQ_INSTRUCTION}

{TAMIL_INSTRUCTION}

═══════════════════════════════════════════════════════
DAY STRUCTURE — FOLLOW EXACTLY
═══════════════════════════════════════════════════════

<h3 class="day-header">
  Day {day_num} — [Write the specific topic name from chapter for today]
</h3>
<p class="day-meta">Duration: 35 Minutes | {discipline_display} | Pages: [relevant page range]</p>

<div class="day-block">

  <!-- ═══ SECTION 1: LEAD / SPARK / OPENING (0–5 min) ═══ -->
  <div class="time-block">
    <strong>[0–5 min] Lead / Spark / Opening Question</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — creative real-life analogy or scenario that
     connects to today's topic. Make it relatable to Indian school students.
     End with the opening question that sparks curiosity.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same analogy, exact same opening
      question. Same length. Nothing shortened.]"</p>
    </div>

    <p><em>Allow 3-5 students to share their opinion in large group discussion.</em></p>

    <!-- CCQ can appear here -->
  </div>

  <!-- ═══ SECTION 2: INTRODUCTION (5–10 min) ═══ -->
  <div class="time-block">
    <strong>[5–10 min] Introduction & Context Setting</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — introduce the topic clearly. Reference the textbook
     page number. Write topic, objectives and page number on board.
     Connect to what students already know.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same introduction.
      Same page reference. Same board instruction.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Topic: [Today's topic]<br/>
      Objective: [One sentence learning objective]<br/>
      Page No: [Relevant pages]
    </div>

    <div class="vocab-block">
      <strong>Key Terms (write on board before teaching):</strong>
      <table>
        <thead>
          <tr>
            <th>Term</th>
            <th>English Meaning</th>
            <th>Tamil பொருள்</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>[term 1]</td><td>[meaning]</td><td>[Tamil]</td></tr>
          <tr><td>[term 2]</td><td>[meaning]</td><td>[Tamil]</td></tr>
          <tr><td>[term 3]</td><td>[meaning]</td><td>[Tamil]</td></tr>
          <tr><td>[term 4]</td><td>[meaning]</td><td>[Tamil]</td></tr>
          <tr><td>[term 5]</td><td>[meaning]</td><td>[Tamil]</td></tr>
        </tbody>
      </table>
    </div>

    <!-- CCQ appears here after vocab -->
  </div>

  <!-- ═══ SECTION 3: MAIN TEACHING (10–25 min) ═══ -->
  <div class="time-block">
    <strong>[10–25 min] Main Teaching & Activity</strong>

    <!-- Sub-topic 1 -->
    <h4>[First sub-topic name from chapter]</h4>
    <p class="page-ref"><em>Textbook Page: [page number]</em></p>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain this sub-topic clearly. Include what to
     read aloud, what to draw on board (flowchart/diagram),
     real-life example or scenario to explain the concept.
     Reference page number.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — exact same explanation, same page
      reference, same board instruction. Nothing shortened.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board — Flowchart/Diagram:</strong><br/>
      [Simple flowchart or diagram relevant to this sub-topic]<br/>
      Example: Concept A → Concept B → Concept C → Result
    </div>

    <!-- CCQ after sub-topic 1 -->

    <p class="teacher-says"><strong>Teacher asks:</strong><br/>
    "[Check-for-understanding question about sub-topic 1 — 1-2 sentences]"</p>
    <p class="student-says"><strong>Expected response:</strong>
    "[Complete answer in 1-2 sentences]"</p>

    <!-- Sub-topic 2 -->
    <h4>[Second sub-topic name from chapter]</h4>
    <p class="page-ref"><em>Textbook Page: [page number]</em></p>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain second sub-topic. Include specific
     activity for today: {activity}. Give clear group/pair instructions.
     Time box the activity.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — exact same explanation and
      same activity description.]"</p>
    </div>

    <!-- Activity block -->
    <div class="activity-block">
      <strong>Activity — {activity}:</strong>
      <p>[Step by step instructions for the activity.
         Who does what. How long. What the output is.]</p>
      <p><em>Teacher circulates and checks understanding during activity.</em></p>
    </div>

    <!-- CCQ after activity -->

    <!-- Sub-topic 3 if applicable -->
    <h4>[Third sub-topic if applicable]</h4>
    <p class="page-ref"><em>Textbook Page: [page number]</em></p>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — explain third sub-topic or connect
     all sub-topics together. Bring out the key insight.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact mirror.]"</p>
    </div>

    <!-- More CCQs randomly placed here -->

  </div>

  <!-- ═══ SECTION 4: STUDENT PRACTICE (25–30 min) ═══ -->
  <div class="time-block">
    <strong>[25–30 min] Student Practice</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — tell students to open notebook and write.
     Explain exactly what to write. Give time limit. Be specific.]"</p>

    <p><strong>Student Task:</strong> [Exactly what students write or do]</p>
    <p class="student-says"><strong>Sample Answer:</strong>
    "[Model answer for the task — 2-3 sentences]"</p>

    <!-- CCQ here -->

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
              <p>"[sentence with blank] _______ (word1 / word2)"</p>
              <p><strong>Word Bank:</strong> [3 key terms from today]</p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>"[Topic] happened because _______ and _______."</p>
            </td>
            <td>
              <p><strong>Task:</strong> Write independently</p>
              <p>"Explain [key concept] in your own words with 5 sentences."</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ═══ SECTION 5: CLOSING + HOMEWORK (30–35 min) ═══ -->
  <div class="time-block">
    <strong>[30–35 min] Closing & Student Task</strong>

    <p class="teacher-says"><strong>Rapid-Fire Recap (Teacher asks):</strong><br/>
    "[3 rapid-fire questions about today's key points.
     Students answer in one word or one sentence.
     Make it energetic — raise hands format.]"</p>

    <div class="board-work">
      <strong>Key Points from Today (write on board):</strong><br/>
      1. [Key point 1 — one sentence]<br/>
      2. [Key point 2 — one sentence]<br/>
      3. [Key point 3 — one sentence]
    </div>

    <!-- Final CCQs here before homework -->

    <div class="homework-block">
      <p class="teacher-says"><strong>Student Task / Homework (English):</strong><br/>
      "[3-4 sentences — explain exactly what to write. How many points.
       When to submit. Use homework book. Own words only.]"</p>

      <div class="board-work">
        <strong>Write on Board — Model Answer:</strong><br/>
        "[1-2 sentence model to guide students]"<br/>
        <em>Tell students: Write in your own words. Do not copy.</em>
      </div>

      <p class="teacher-says"><strong>Preview {next_day}:</strong><br/>
      "[1-2 sentences — tell students what tomorrow will cover.
       Build excitement or curiosity.]"</p>
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE RULES — CHECK BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ Exactly 10 CCQ blocks placed randomly in the day
✅ Each CCQ has Tamil version
✅ Tamil appears ONLY in: Key Terms table + Main explanations + Opening question
✅ Every sub-topic has a page number reference
✅ Activity block matches today's activity style: {activity}
✅ Board work at opening, during teaching, and at closing
✅ Homework has model answer written on board
✅ Rapid-fire recap at closing
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ Do NOT start Day {day_num + 1}
✅ Base ALL content on actual chapter text below

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ SS LP Day {day_num} error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 6 — Day 5: Map Work + Book-back (Fixed Template)
    # -------------------------------------------------------------------------

    def _call_day5(self, text, class_num, unit,
                   lesson_title, discipline_display):
        try:
            prompt = f"""Generate ONLY Day 5 of the lesson plan.
Day 5 is always a fixed structure: Book-back Exercise Marking + Map Work.
Do NOT generate any other day. Do NOT repeat any content from Days 1-4.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — {discipline_display}
Day      : 5 of 5
Duration : 35 minutes
Focus    : Book-back exercise marking + Map teaching session

<h3 class="day-header">Day 5 — Map Work & Book-back Exercises</h3>
<p class="day-meta">Duration: 35 Minutes | {discipline_display} | Evaluation Day</p>

<div class="day-block">

  <!-- ═══ SECTION 1: LEARNING OBJECTIVES ═══ -->
  <div class="time-block">
    <strong>Learning Objectives for Day 5</strong>
    <ul>
      <li>Evaluate understanding of the full chapter through book-back exercises.</li>
      <li>Identify and locate key places, events, and territorial changes on a map.</li>
      <li>[Add 1-2 more specific to this chapter — from actual content]</li>
    </ul>
  </div>

  <!-- ═══ SECTION 2: BOOK-BACK EXERCISE MARKING (0–20 min) ═══ -->
  <div class="time-block">
    <strong>[0–20 min] Book-back Exercise Marking & Discussion</strong>

    <p><em>Teacher facilitates step-by-step marking. Students swap notebooks
    or mark their own while teacher explains the correct answers.</em></p>

    <h4>Section 1: Choose the Correct Answer</h4>
    <p class="page-ref"><em>Refer textbook exercise pages</em></p>
    <p>[Identify 3-4 key MCQ answers from this chapter.
       For each, briefly explain WHY it is correct — not just the answer.
       Reference specific page numbers from the textbook.]</p>

    <h4>Section 2: Fill in the Blanks / Match the Following</h4>
    <p>[Identify 3-4 key fill-in or match answers.
       Explain the connection for each match.
       Reference specific terms from the chapter.]</p>

    <h4>Section 3: Short Answer Questions</h4>
    <p>[Identify 2-3 short answer questions from book-back.
       Give model answer structure — what lines to highlight
       in textbook. Reference specific page numbers.]</p>

    <div class="board-work">
      <strong>Write Correct Answers on Board as you discuss:</strong><br/>
      [List key answers for students to verify their work]
    </div>

  </div>

  <!-- ═══ SECTION 3: MAP TEACHING SESSION (20–35 min) ═══ -->
  <div class="time-block">
    <strong>[20–35 min] Map Teaching Session</strong>

    <p><em>Teacher uses wall map to point locations, then students mark
    their own outline maps. Students must bring outline map today.</em></p>

    <h4>Map Task 1 — [Primary Map Task for this chapter]</h4>
    <p class="page-ref"><em>Reference: Textbook map pages</em></p>
    <p>[Describe exactly what to locate and mark on the map.
       Be specific — country names, cities, borders, regions.
       Based on actual chapter content.]</p>

    <h4>Map Task 2 — [Secondary Map Task if applicable]</h4>
    <p>[Second set of locations or a different map focus.
       Example: India map for chapters with India-specific content.]</p>

    <div class="board-work">
      <strong>Map Checklist (write on board):</strong><br/>
      [List all locations students must mark — numbered list]
    </div>

  </div>

  <!-- ═══ SECTION 4: CLOSING ═══ -->
  <div class="time-block">
    <strong>Closing</strong>

    <p><em>All students must submit:</em></p>
    <ul>
      <li>Completed notebook with all 5 days of notes</li>
      <li>Book-back exercises answered and marked</li>
      <li>Outline map(s) with all required locations marked and labeled</li>
      <li>All homework tasks from Days 1–4</li>
    </ul>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[2-3 sentences — congratulate students on completing the chapter.
     Name 2-3 key things they have learned. Motivate them for the next chapter.]"</p>

  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="day-header">Day 5
- Map tasks must be based on ACTUAL chapter content below
- Book-back discussion must reference ACTUAL chapter topics
- No Tamil required in Day 5 (evaluation day — English only)
- Do NOT generate any other day

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
            print(f"❌ SS LP Day 5 error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 7 — Assessment Summary
    # -------------------------------------------------------------------------

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, discipline_display):
        try:
            prompt = f"""Generate ONLY the Assessment Summary section.
Do NOT repeat any day content. This is a summary evaluation block.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — {discipline_display}
Total Days: 5

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Oral Assessment Questions</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Topic Covered</th>
        <th>Oral Question (English)</th>
        <th>Expected Answer</th>
        <th>Tamil Prompt (தமிழ் உதவி)</th>
      </tr>
    </thead>
    <tbody>
      [5 rows — one per day. Day 1 through Day 5.
       Each row: Day number | Topic | English question |
       Complete sentence answer | Tamil version of question]
    </tbody>
  </table>

  <h3>CCQ Bank — Quick Reference</h3>
  <p><em>10 concept check questions from across all 5 days
  for teacher's reference during revision:</em></p>
  <ol>
    [List 10 CCQ questions with one-line answers — based on chapter content]
  </ol>

  <h3>Written Assessment Task</h3>
  <p>[One meaningful written task covering the full chapter —
     suitable for a class test or revision exercise]</p>

  <div class="board-work">
    <strong>Model Answer (write on board before students start):</strong>
    <p>"[Sentence 1 of model answer]"</p>
    <p>"[Sentence 2 of model answer]"</p>
    <p>"[Sentence 3 of model answer]"</p>
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
          <p><strong>Task:</strong> Fill in the blanks with word bank</p>
          <p><strong>Example:</strong> "[sentence] _______ (word1 / word2)"</p>
          <p><strong>Word Bank:</strong> [5 key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences each</p>
          <p><strong>Example starter:</strong> "[event] happened because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Write a structured essay</p>
          <p><strong>Prompt:</strong> "Explain [key chapter theme] with
             causes, events, and consequences in 8-10 sentences."</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 5 days of notes completed in classwork notebook</li>
    <li>☐ All homework tasks submitted (Days 1–4)</li>
    <li>☐ Book-back exercises answered and marked (Day 5)</li>
    <li>☐ Outline map completed with all required locations (Day 5)</li>
    <li>☐ [Add 1-2 chapter-specific checklist items]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table MUST have exactly 5 rows with Tamil column
- CCQ bank MUST have exactly 10 questions
- Differentiation MUST have actual example tasks with real sentences
- Model answer MUST be realistic and based on chapter content
- Base everything on chapter text below

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
            print(f"❌ SS LP assessment error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Helper — clean raw AI output
    # -------------------------------------------------------------------------

    def _clean(self, raw: str) -> str:
        if not raw:
            return raw
        text = raw.strip()
        # Remove markdown code fences
        text = re.sub(r'```(?:html)?', '', text).strip()
        text = re.sub(r'```', '', text).strip()
        # Remove any inline style blocks
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        # Strip any leading non-HTML preamble text
        first_tag = re.search(r'<(?:div|h[1-6]|section|p|table)', text)
        if first_tag and first_tag.start() > 0:
            preamble = text[:first_tag.start()].strip()
            if preamble and not preamble.startswith('<'):
                text = text[first_tag.start():]
        return text.strip()


# ============================================================================
# Singleton instance
# ============================================================================

ss_lp_builder = SSLPBuilder()