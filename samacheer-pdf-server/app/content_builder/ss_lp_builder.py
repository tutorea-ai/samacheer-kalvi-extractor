"""
ss_lp_builder.py
----------------
Lesson Plan Generator for Samacheer Kalvi Social Science (Classes 6-12).
Handles History, Geography, Civics, Economics disciplines.

v7.0 — Teacher feedback fixes (May 2026)

Changes from v6.0:
  ✅ Spark style fixed per day (Day 1=analogy, Day 2=picture, Day 3=video,
       Day 4=quote/headline, Day 5=rapid recall quiz) — Claude fills content
  ✅ Student task style fixed per day — no consecutive repetition
       (Day 1=individual written, Day 2=group discussion+prompts,
        Day 3=think-pair-share, Day 4=peer assessment, Day 5=self-checklist)
  ✅ CCQ rule enforced: subject-matter ONLY — no ICQs (instruction-check questions)
  ✅ CCQ simplified: max 8 words, concrete factual questions only
  ✅ Tamil targeted rule enforced with explicit wrong/right examples
  ✅ Topic overflow: large topics explicitly carry into next day
  ✅ Day 4 closing → full chapter recap (not just Day 4 recap)
  ✅ Flowchart/model added wherever concept has a clear flow
  ✅ Day 5: map tips, memory tricks, print-ready map checklist added
  ✅ Day 5: sentence added linking Q&A to book-back answers
  ✅ Assessment: test series suggestion added
  ✅ focus_map: smarter topic boundaries, no hardcoded page ranges
  ✅ Discipline-specific _call_content_day routing (history/geo/civics/economics)

Structure:
  - 5 days per chapter (35 minutes per day)
  - Day 1-4: Content days
  - Day 5: Fixed template — Map work + Book-back exercises
  - 10 CCQs randomly placed per day (subject-matter only)
  - Targeted Tamil scaffolding (key terms + main explanation + opening question ONLY)
  - API calls: 7 total (Preamble + Day1 + Day2 + Day3 + Day4 + Day5 + Assessment)
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
# CCQ INSTRUCTION BLOCK
# ============================================================================

CCQ_INSTRUCTION = """
═══════════════════════════════════════════════════════
CCQ — CONCEPT CHECK QUESTIONS (CRITICAL RULES)
═══════════════════════════════════════════════════════

You MUST include exactly 10 CCQs spread randomly throughout this day's content.

WHAT IS A CCQ?
A CCQ (Concept Check Question) checks if students understood the SUBJECT MATTER
just taught. It is NOT about instructions or tasks.

⚠️ CRITICAL DIFFERENCE — READ THIS CAREFULLY:

❌ ICQ (Instruction Check Question) — WRONG, DO NOT USE:
   "Do you understand what you need to do?"
   "How many sentences should you write?"
   "Do you know which group you are in?"
   These check if students understood the TASK. We do NOT want these.

✅ CCQ (Concept Check Question) — CORRECT, USE ONLY THESE:
   "What triggered the assassination of Archduke Franz Ferdinand?"
   "Which two alliance systems faced each other in World War I?"
   "Name one consequence of the Treaty of Versailles."
   These check if students understood the CONTENT just taught.

RULES for CCQs:
- Every CCQ must be about the subject matter just explained — not the activity
- Keep each CCQ under 8 words
- Place them RANDOMLY — after explaining a concept, after a flowchart, after activity
- No two CCQs should repeat each other
- Tamil version mandatory for every CCQ

FORMAT — use this exact HTML block:
<div class="ccq-block">
  <strong>⚡ CCQ (Concept Check):</strong>
  <p class="teacher-says">"[Short factual question about content just taught — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Short factual answer — 1-2 sentences]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
</div>
═══════════════════════════════════════════════════════
"""


# ============================================================================
# TAMIL SCAFFOLDING INSTRUCTION
# ============================================================================

TAMIL_INSTRUCTION = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES — TARGETED ONLY
═══════════════════════════════════════════════════════

Tamil appears in EXACTLY 3 places — nowhere else:

✅ 1. KEY TERMS TABLE — Tamil meaning column only
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph after English paragraph
✅ 3. OPENING/LEAD QUESTION — Tamil version after English question

❌ NEVER add Tamil to:
   - Activity instructions
   - Group task descriptions
   - Time notes
   - Page numbers
   - Board work headings
   - Homework task description
   - Student task instructions
   - Closing / recap sections

⚠️ WRONG vs RIGHT EXAMPLE:

❌ WRONG (Tamil added to activity instructions):
   <div class="activity-block">
     <strong>Activity:</strong>
     <p>Divide into 3 groups. Each group answers one question.</p>
     <p>குழுவாக பிரியுங்கள். ஒவ்வொரு குழுவும் ஒரு கேள்விக்கு பதில் சொல்லுங்கள்.</p>
   </div>

✅ RIGHT (Tamil only in key terms and main explanation):
   <div class="activity-block">
     <strong>Activity:</strong>
     <p>Divide into 3 groups. Each group answers one question.</p>
     [NO Tamil here]
   </div>

   <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
   "The Triple Alliance was formed between Germany, Austria-Hungary, and Italy..."</p>
   <div class="tamil-scaffold">
     <strong>ஆசிரியருக்கு (Tamil):</strong>
     <p>"ட்ரிபிள் அலையன்ஸ் என்பது ஜெர்மனி, ஆஸ்திரியா-ஹங்கேரி மற்றும் இத்தாலி இடையே..."</p>
   </div>

Tamil mirror rule (where Tamil IS used):
- Same sentences. Same detail. Same length as English.
- NOT a summary. Full mirror.
- Real Tamil Unicode script only — never transliteration.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# SPARK STYLES — fixed per day, Claude fills the content
# ============================================================================

SPARK_STYLES = {
    1: {
        "style": "Real-life Analogy",
        "instruction": """Use a real-life analogy or relatable scenario from everyday Indian life
to connect to today's topic. Make it feel close to the student's world.
End with one opening question that sparks curiosity.
Example structure: 'Imagine you are... / Think about when... → Opening question'""",
    },
    2: {
        "style": "Picture / Image + Reflection",
        "instruction": """Describe a specific image or visual related to today's topic
(as if showing it on the board or projector).
Tell the teacher exactly what image to draw or display and what to ask about it.
End with one reflection question students think about before answering.
Example structure: 'Show this image: [describe clearly] → What do you see? What does this tell us about...?'""",
    },
    3: {
        "style": "Video Clip Description + Discussion",
        "instruction": """Describe a short video clip (60-90 seconds) the teacher can find on YouTube
that directly connects to today's topic. Give the search keywords.
After the clip: ask students 2 quick reaction questions.
Example structure: 'Play this clip: [YouTube search: "..."] → What did you notice? How does this connect to...?'""",
    },
    4: {
        "style": "Historical Quote / Newspaper Headline + Reaction",
        "instruction": """Open with a powerful real historical quote OR a dramatic newspaper headline
from the era of today's topic. Write it on the board.
Ask students: What does this tell us? Who said this and why?
Example structure: Board: "[Quote or Headline]" → Teacher asks: What does this mean? What do you think happened next?'""",
    },
    5: {
        "style": "Rapid Recall Quiz",
        "instruction": """Start with a 5-question rapid-fire quiz reviewing the key facts from Days 1-4.
Read questions aloud — students answer on a slip of paper or call out.
This activates prior knowledge and sets up the evaluation day.
Example structure: '5 quick questions → students write answers → teacher reveals → quick discussion of any gaps'""",
    },
}


# ============================================================================
# STUDENT TASK STYLES — fixed per day, no consecutive repetition
# ============================================================================

STUDENT_TASK_STYLES = {
    1: {
        "style": "Individual Written Answer",
        "instruction": """Students open their notebooks and write independently.
Give a clear specific prompt — not open-ended.
Give a time limit. Give a model sentence starter on the board.
Example: 'Write 4 sentences in your notebook: [specific prompt]. Start with: "[starter sentence]..."'""",
    },
    2: {
        "style": "Group Discussion with Prompts",
        "instruction": """Divide class into groups of 4-5. Give each group a specific discussion prompt.
Each group discusses for 3 minutes, then one student shares with the class.
Give written prompts on board — not open-ended.
Example: 'Group 1: Discuss why... | Group 2: Explain how... | Group 3: Give reasons for...'
After sharing, teacher adds key points to board.""",
    },
    3: {
        "style": "Think-Pair-Share",
        "instruction": """Give students a specific question or prompt.
Step 1: Think independently (1 min) — write one answer in notebook.
Step 2: Pair with neighbour (2 min) — share and improve each other's answer.
Step 3: Share with class — 3-4 pairs share their combined answer.
Teacher consolidates on board.""",
    },
    4: {
        "style": "Peer Assessment — Swap Notebooks",
        "instruction": """Students write their answer to a given prompt (3 mins).
Then swap notebook with neighbour.
Teacher reads out model answer. Students mark their neighbour's work.
Discuss: what was good, what was missing.
This builds critical reading and self-correction habits.""",
    },
    5: {
        "style": "Self-Assessment Checklist + Test Prep",
        "instruction": """Students use a checklist to self-assess their chapter notes.
Then attempt 2 unseen short-answer questions independently (test conditions).
Teacher collects for checking.
This prepares students for actual exams.""",
    },
}


# ============================================================================
# TOPIC FOCUS MAP — smarter per-day topic guidance (no hardcoded pages)
# ============================================================================

FOCUS_MAP = {
    1: "Opening context, background, and the FIRST major topic or cause of the chapter. "
       "Cover only what can be taught well in 25 minutes of content time. "
       "If the first topic is large, teach it fully — do NOT rush into the second topic.",

    2: "Second and third major topics or causes. "
       "Start with a 2-minute recap of Day 1. "
       "If Day 1's topic was large and carried over, complete it first before moving to new topics. "
       "Cover only what can be taught well — do NOT rush.",

    3: "Results, consequences, turning points, or the second half of core content. "
       "Start with a 2-minute recap of Day 2. "
       "If a previous topic was large and not completed, finish it first. "
       "Use anchor charts, graphic organizers, or flowcharts for complex cause-effect concepts.",

    4: "Final sections — analysis, source-based discussion, and chapter consolidation. "
       "Start with a 2-minute recap of Day 3. "
       "If any major topic (e.g. Russian Revolution, League of Nations) was not fully covered "
       "in a previous day, open with completing it before moving to consolidation. "
       "Closing must be an OVERALL CHAPTER RECAP — not just Day 4 recap.",
}


# ============================================================================
# ACTIVITY STYLES — per day
# ============================================================================

ACTIVITY_MAP = {
    1: "Flowchart on board showing cause→event→result chain. Large group discussion after.",
    2: "Group activity: 3 groups answer 3 different questions. Each group shares with class. Active note-taking.",
    3: "Bucket activity: Red/Yellow/Green groups each get a different focus. Map pointing if relevant. Pair discussion.",
    4: "Source analysis OR timeline activity. Students present their own flowchart prepared during the lesson.",
}


# ============================================================================
# SS LP BUILDER CLASS
# ============================================================================

class SSLPBuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ SS LP Builder v7.0 initialized — model: {self.model}")

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
        print(f"      [SS LP v7] Generating: {discipline_display} | {lesson_title}")
        print(f"      [SS LP v7] 7 API calls: Preamble + Day1 + Day2 + Day3 + Day4 + Day5 + Assessment")

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
                discipline, discipline_display, day_num
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
        print(f"      [SS LP v7] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
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
    # Calls 2–5 — Content Days 1–4 (discipline-aware routing)
    # -------------------------------------------------------------------------

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          discipline, discipline_display, day_num):
        """Routes to discipline-specific day builder."""
        if discipline == "history":
            return self._call_day_history(
                text, class_num, unit, lesson_title, discipline_display, day_num)
        elif discipline == "geography":
            return self._call_day_geography(
                text, class_num, unit, lesson_title, discipline_display, day_num)
        elif discipline == "civics":
            return self._call_day_civics(
                text, class_num, unit, lesson_title, discipline_display, day_num)
        elif discipline == "economics":
            return self._call_day_economics(
                text, class_num, unit, lesson_title, discipline_display, day_num)
        else:
            return self._call_day_history(
                text, class_num, unit, lesson_title, discipline_display, day_num)

    # -------------------------------------------------------------------------
    # Day builder — shared prompt builder used by all disciplines
    # -------------------------------------------------------------------------

    def _build_day_prompt(self, text, class_num, unit, lesson_title,
                          discipline_display, day_num,
                          discipline_notes: str = "") -> str:
        """
        Builds the full prompt for a content day.
        discipline_notes: any discipline-specific instructions injected into prompt.
        """
        spark      = SPARK_STYLES[day_num]
        task       = STUDENT_TASK_STYLES[day_num]
        focus      = FOCUS_MAP[day_num]
        activity   = ACTIVITY_MAP.get(day_num, "group discussion")
        next_label = f"Day {day_num + 1}" if day_num < 4 else "Day 5 — Map Work and Book-back Exercises"

        return f"""Generate ONLY Day {day_num} of the lesson plan. Nothing else.
Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — {discipline_display}
Day      : {day_num} of 5
Duration : 35 minutes
Focus    : {focus}
Activity style today: {activity}
{discipline_notes}

{CCQ_INSTRUCTION}

{TAMIL_INSTRUCTION}

═══════════════════════════════════════════════════════
SPARK STYLE FOR TODAY — DAY {day_num}: {spark['style']}
═══════════════════════════════════════════════════════
{spark['instruction']}
Use this exact spark style. Do NOT use a different style for this day.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
STUDENT TASK STYLE FOR TODAY — DAY {day_num}: {task['style']}
═══════════════════════════════════════════════════════
{task['instruction']}
Use this exact student task style. Do NOT use individual written answers
or any other style — use ONLY the style specified above.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
FLOWCHART / MODEL RULE
═══════════════════════════════════════════════════════
Wherever a concept has a clear flow (cause → event → result, or step by step),
include a simple text-based flowchart model inside a <div class="board-work"> block.
Label it clearly as "Draw on Board — Model Flowchart:" so the teacher can copy it.
Example format:
  Cause 1 → Event A
  Cause 2 ↗
         → Event A → Consequence → Result
This helps students visualise the concept. Always provide a model, not just text.
═══════════════════════════════════════════════════════

═══════════════════════════════════════════════════════
TOPIC OVERFLOW RULE
═══════════════════════════════════════════════════════
If a topic is large and cannot be covered well in the available time:
- Teach what you can cover PROPERLY in the time available
- At the closing, explicitly tell students: "We will continue [topic name] tomorrow"
- Day {day_num + 1 if day_num < 4 else 5} should open by completing the carried-over topic
  before moving to new content
Do NOT squeeze large topics into 5 minutes. Quality over quantity.
═══════════════════════════════════════════════════════

DAY STRUCTURE — FOLLOW EXACTLY:

<h3 class="day-header">
  Day {day_num} — [Write the specific topic name from chapter for today]
</h3>
<p class="day-meta">Duration: 35 Minutes | {discipline_display} | Pages: [relevant page range from textbook]</p>

<div class="day-block">

  <!-- ═══ SECTION 1: SPARK / LEAD (0–5 min) ═══ -->
  <div class="time-block">
    <strong>[0–5 min] {spark['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences using the SPARK STYLE specified above.
     Make it genuinely engaging — not generic.
     Based on actual chapter content.
     End with the opening question.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same spark, exact same question.
      Same length. Nothing shortened.]"</p>
    </div>

    <p><em>Allow 3-5 students to share their response. Large group discussion format.</em></p>

  </div>

  <!-- ═══ SECTION 2: INTRODUCTION (5–10 min) ═══ -->
  <div class="time-block">
    <strong>[5–10 min] Introduction & Context Setting</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — introduce today's topic clearly.
     Reference the textbook page number.
     Connect to what students already know from previous days.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact same introduction.
      Same page reference.]"</p>
    </div>

    <div class="board-work">
      <strong>Write on Board:</strong><br/>
      Topic: [Today's specific topic]<br/>
      Objective: [One sentence learning objective]<br/>
      Page No: [Relevant pages]
    </div>

    <div class="vocab-block">
      <strong>Key Terms — Write on Board Before Teaching:</strong>
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

    <!-- CCQ after vocab — subject-matter question about terms just introduced -->

  </div>

  <!-- ═══ SECTION 3: MAIN TEACHING (10–25 min) ═══ -->
  <div class="time-block">
    <strong>[10–25 min] Main Teaching & Activity</strong>

    <!-- Sub-topic 1 -->
    <h4>[First sub-topic name — from actual chapter content]</h4>
    <p class="page-ref"><em>Textbook Page: [page number]</em></p>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain this sub-topic clearly.
     What to read aloud, what to draw on board.
     Use a concrete example or scenario.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — exact same explanation.
      Same page reference. Nothing shortened.]"</p>
    </div>

    <div class="board-work">
      <strong>Draw on Board — Model Flowchart/Diagram:</strong><br/>
      [Simple text-based flowchart model relevant to this sub-topic]<br/>
      Example: Factor 1 → Event → Consequence → Result<br/>
      [Make it a real model the teacher can draw in 1-2 minutes]
    </div>

    <!-- CCQ here — factual question about sub-topic 1 just taught -->

    <!-- Sub-topic 2 -->
    <h4>[Second sub-topic name — from actual chapter content]</h4>
    <p class="page-ref"><em>Textbook Page: [page number]</em></p>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain second sub-topic.
     Include specific activity for today: {activity}.
     Give clear group/pair instructions with time box.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — exact same explanation.]"</p>
    </div>

    <div class="activity-block">
      <strong>Activity — {activity}:</strong>
      <p>[Step by step instructions for the activity.
         Who does what. How long. What the output is.
         NO Tamil here — English only.]</p>
      <p><em>Teacher circulates and checks understanding during activity.</em></p>
    </div>

    <!-- CCQ after activity — factual question about concept in the activity -->

    <!-- Sub-topic 3 if applicable — or carry-over note if time is short -->
    <h4>[Third sub-topic OR carry-over note]</h4>
    <p class="page-ref"><em>Textbook Page: [page number]</em></p>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — explain third sub-topic OR explicitly state:
     'We will continue [topic] tomorrow. Today we covered [X].
     Tomorrow we will start with [Y].' — if time is short.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — exact mirror.]"</p>
    </div>

    <!-- More CCQs randomly placed here -->

  </div>

  <!-- ═══ SECTION 4: STUDENT TASK (25–30 min) ═══ -->
  <div class="time-block">
    <strong>[25–30 min] Student Task — {task['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — set up the student task using the TASK STYLE specified above.
     Be very specific about what students do, how long, and what the output is.]"</p>

    <div class="board-work">
      <strong>Write on Board — Task Prompt:</strong><br/>
      [Write the exact task prompt on the board so all students can see it]<br/>
      [Include a model starter sentence if individual written task]
    </div>

    <p class="student-says"><strong>Sample Answer / Model Response:</strong><br/>
    "[Model answer for the task — 2-3 sentences.
     Real content from the chapter. Not generic.]"</p>

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
              <p><strong>Word Bank:</strong> [3-4 key terms from today's content]</p>
              <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
            </td>
            <td>
              <p><strong>Task:</strong> Answer in 2-3 sentences</p>
              <p>Prompt: "[Specific sentence starter from today's content]"</p>
            </td>
            <td>
              <p><strong>Task:</strong> Write independently</p>
              <p>Prompt: "Explain [key concept from today] with 5 sentences using your own words."</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- ═══ SECTION 5: CLOSING (30–35 min) ═══ -->
  <div class="time-block">
    <strong>[30–35 min] Closing{"& Overall Chapter Recap" if day_num == 4 else " & Preview"}</strong>

    {"<p><em>Day 4 Closing is an OVERALL CHAPTER RECAP — not just Day 4 recap.</em></p>" if day_num == 4 else ""}

    <p class="teacher-says"><strong>Rapid-Fire Recap (Teacher asks):</strong><br/>
    {"[3 rapid-fire questions covering ALL key points from ALL 4 days. Make it a full chapter review — energetic, hands-raised format.]" if day_num == 4 else "[3 rapid-fire questions about today's key points. Students answer in one word or one sentence. Energetic — raise hands format.]"}</p>

    <div class="board-work">
      <strong>Key Points {"from the Full Chapter" if day_num == 4 else "from Today"} (write on board):</strong><br/>
      1. [Key point 1 — one sentence]<br/>
      2. [Key point 2 — one sentence]<br/>
      3. [Key point 3 — one sentence]{"<br/>4. [Key point 4 — one sentence]<br/>5. [Key point 5 — one sentence]" if day_num == 4 else ""}
    </div>

    <!-- Final CCQs before homework -->

    <div class="homework-block">
      <p class="teacher-says"><strong>Homework:</strong><br/>
      "[3-4 sentences — explain exactly what to write in homework notebook.
       Specific prompt. How many points. Own words only. When to submit.]"</p>

      <div class="board-work">
        <strong>Write on Board — Homework Model Answer:</strong><br/>
        "[1-2 sentence model to guide students]"<br/>
        <em>Tell students: Write in your own words. Do not copy.</em>
      </div>

      <p class="teacher-says"><strong>Preview {next_label}:</strong><br/>
      "[1-2 sentences — tell students what tomorrow will cover.
       Build excitement or curiosity. If any topic is carrying over, mention it here.]"</p>
    </div>

  </div>

</div>

═══════════════════════════════════════════════════════
ABSOLUTE CHECKS BEFORE FINISHING DAY {day_num}
═══════════════════════════════════════════════════════
✅ Exactly 10 CCQ blocks — all about SUBJECT MATTER (content), NOT instructions
✅ Each CCQ has Tamil version and is under 8 words
✅ Spark style used: {spark['style']} — NO other spark style
✅ Student task style used: {task['style']} — NO other task style
✅ Tamil appears ONLY in: Key Terms + Main explanations + Opening question
✅ Activity instructions have NO Tamil
✅ At least one flowchart model in board-work
✅ Sample answer / model response in student task section
✅ Every sub-topic has a page number reference
✅ Large topics explicitly carry over to next day if needed
{"✅ Closing is FULL CHAPTER RECAP across all 5 days" if day_num == 4 else "✅ Closing previews next day clearly"}
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ Do NOT start Day {day_num + 1}
✅ Base ALL content on actual chapter text below

Chapter Text:
---
{text}
---"""

    # -------------------------------------------------------------------------
    # Discipline-specific day callers
    # -------------------------------------------------------------------------

    def _call_day_history(self, text, class_num, unit, lesson_title,
                          discipline_display, day_num):
        try:
            discipline_notes = """
HISTORY-SPECIFIC NOTES:
- Use timeline-based thinking: when did it happen → what caused it → what resulted
- Chronology matters — always reference dates and sequence of events
- Source analysis is a key skill — if any primary source quote is in the chapter, use it
- Map work is important — reference map pages when discussing territorial changes
- Board flowcharts should show: Cause → Event → Consequence chains
"""
            prompt = self._build_day_prompt(
                text, class_num, unit, lesson_title,
                discipline_display, day_num, discipline_notes
            )
            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ SS LP History Day {day_num} error: {e}")
            return None

    def _call_day_geography(self, text, class_num, unit, lesson_title,
                            discipline_display, day_num):
        try:
            discipline_notes = """
GEOGRAPHY-SPECIFIC NOTES:
- Map skills are central — every day must reference the textbook map page
- Use spatial thinking: where is it → why there → what effect on people
- Physical features → Human activities → Economic outcomes is the key chain
- Board flowcharts should show: Location → Climate → Resources → Human Settlement chains
- Anchor charts (graphic organizers) work very well for Geography comparisons
- Distinguish-between questions are common in Geography — prepare students for these
"""
            prompt = self._build_day_prompt(
                text, class_num, unit, lesson_title,
                discipline_display, day_num, discipline_notes
            )
            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ SS LP Geography Day {day_num} error: {e}")
            return None

    def _call_day_civics(self, text, class_num, unit, lesson_title,
                         discipline_display, day_num):
        try:
            discipline_notes = """
CIVICS-SPECIFIC NOTES:
- Connect every concept to real-life governance and students' daily lives
- Constitutional concepts should be explained with simple real examples first
- Rights → Duties → Institutions is a common Civics chain
- Board flowcharts should show: Problem → Law/Policy → Institution → Outcome
- Case studies or real examples from Indian democracy make abstract concepts concrete
- Short answer and detail questions in Civics often ask students to explain OR distinguish
"""
            prompt = self._build_day_prompt(
                text, class_num, unit, lesson_title,
                discipline_display, day_num, discipline_notes
            )
            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ SS LP Civics Day {day_num} error: {e}")
            return None

    def _call_day_economics(self, text, class_num, unit, lesson_title,
                            discipline_display, day_num):
        try:
            discipline_notes = """
ECONOMICS-SPECIFIC NOTES:
- Connect economic concepts to students' everyday experience (prices, markets, jobs)
- Use simple analogies before introducing formal definitions
- Key chains: Production → Distribution → Consumption → Impact on People
- Board flowcharts should show: Economic concept → How it works → Real-world effect
- Data and statistics from the chapter should be referenced and explained (not just read)
- Short answer questions in Economics often ask for definitions OR reasons — prepare both
"""
            prompt = self._build_day_prompt(
                text, class_num, unit, lesson_title,
                discipline_display, day_num, discipline_notes
            )
            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system=SS_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ SS LP Economics Day {day_num} error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 6 — Day 5: Map Work + Book-back (Fixed Template)
    # -------------------------------------------------------------------------

    def _call_day5(self, text, class_num, unit,
                   lesson_title, discipline_display):
        try:
            spark = SPARK_STYLES[5]
            task  = STUDENT_TASK_STYLES[5]

            prompt = f"""Generate ONLY Day 5 of the lesson plan.
Day 5 is always: Rapid Recall Quiz opening → Book-back Exercise Marking → Map Work → Closing.
Do NOT generate any other day. Do NOT repeat content from Days 1-4.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — {discipline_display}
Day      : 5 of 5
Duration : 35 minutes

<h3 class="day-header">Day 5 — Map Work & Book-back Exercises</h3>
<p class="day-meta">Duration: 35 Minutes | {discipline_display} | Evaluation Day</p>

<div class="day-block">

  <!-- ═══ OPENING: RAPID RECALL QUIZ (0–5 min) ═══ -->
  <div class="time-block">
    <strong>[0–5 min] Rapid Recall Quiz — {spark['style']}</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[Give 5 rapid-fire questions reviewing the most important facts
     from Days 1-4. Read aloud one by one. Students write answers on a slip of paper.
     After all 5 — teacher reveals correct answers. Quick class discussion on any gaps.]"</p>

    <div class="board-work">
      <strong>Write 5 Quiz Questions on Board:</strong><br/>
      1. [Factual question from chapter — Day 1 content]<br/>
      2. [Factual question from chapter — Day 2 content]<br/>
      3. [Factual question from chapter — Day 3 content]<br/>
      4. [Factual question from chapter — Day 4 content]<br/>
      5. [Key term or date or name from chapter]<br/>
      <br/>
      <strong>Answers:</strong><br/>
      1. [Answer 1]  2. [Answer 2]  3. [Answer 3]  4. [Answer 4]  5. [Answer 5]
    </div>

    <p><em>Students self-mark. Teacher notes who struggled and gives support during book-back session.</em></p>
  </div>

  <!-- ═══ SECTION 2: BOOK-BACK EXERCISE MARKING (5–20 min) ═══ -->
  <div class="time-block">
    <strong>[5–20 min] Book-back Exercise Marking & Discussion</strong>

    <p><em>Teacher facilitates step-by-step marking. Students swap notebooks
    or mark their own while teacher explains the correct answers.
    Note: The platform's Q&A section has all book-back questions with complete model answers
    for student reference and revision.</em></p>

    <h4>Section 1: Choose the Correct Answer</h4>
    <p class="page-ref"><em>Refer textbook exercise pages</em></p>
    <p>[Identify 3-4 key MCQ answers from this chapter's book-back.
       For each, briefly explain WHY it is correct — not just the answer.
       Reference specific page numbers from the textbook.]</p>

    <h4>Section 2: Fill in the Blanks / Match the Following</h4>
    <p>[Identify 3-4 key fill-in or match answers.
       Explain the connection for each match.
       Reference specific terms from the chapter.]</p>

    <h4>Section 3: Short Answer Questions</h4>
    <p>[Identify 2-3 short answer questions from book-back.
       Give model answer structure — what lines to highlight in textbook.
       Reference specific page numbers.]</p>

    <div class="board-work">
      <strong>Write Correct Answers on Board as you discuss:</strong><br/>
      [List key answers clearly — students verify their work]
    </div>

  </div>

  <!-- ═══ SECTION 3: MAP TEACHING SESSION (20–30 min) ═══ -->
  <div class="time-block">
    <strong>[20–30 min] Map Teaching Session</strong>

    <p><em>Teacher uses wall map to point locations, then students mark
    their own outline maps. Students must bring outline map today.</em></p>

    <h4>Map Task 1 — [Primary Map Task for this chapter]</h4>
    <p class="page-ref"><em>Reference: Textbook map pages</em></p>
    <p>[Describe exactly what to locate and mark on the map.
       Be specific — country names, cities, borders, regions.
       Based on actual chapter content.]</p>

    <div class="board-work">
      <strong>Map Tips & Memory Tricks:</strong><br/>
      [Give 3-5 specific memory tricks for locating/remembering the key places.
       Example: "Germany is in the CENTER of Europe — remember it as the 'heart' that started the war."
       Example: "The Balkans — remember B for Burning fuse of Europe."
       Make them catchy and specific to this chapter's geography.]
    </div>

    <h4>Map Task 2 — [Secondary Map Task if applicable]</h4>
    <p>[Second set of locations or a different map focus.
       Based on actual chapter content.]</p>

    <div class="board-work">
      <strong>Map Checklist — Students Must Mark All of These (write on board):</strong><br/>
      [Numbered list of all specific locations students must mark and label]<br/>
      <br/>
      <strong>Print-Ready Map Reference:</strong><br/>
      <em>Textbook outline map: Page [X] | Also available: NCERT outline maps for this region</em><br/>
      <em>Students must label each location clearly in CAPITAL LETTERS.</em>
    </div>

  </div>

  <!-- ═══ SECTION 4: STUDENT TASK + TEST SERIES (30–35 min) ═══ -->
  <div class="time-block">
    <strong>[30–35 min] {task['style']} + Chapter Test Prep</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[2-3 sentences — tell students to attempt 2 unseen questions independently
     in test conditions. Collect for checking. These are practice for the real exam.]"</p>

    <div class="board-work">
      <strong>Chapter Practice Questions (write on board):</strong><br/>
      Q1. [1-mark or 2-mark question from chapter — slightly different from book-back]<br/>
      Q2. [2-mark or 5-mark question from chapter — slightly different from book-back]<br/>
      <br/>
      <strong>Test Series Suggestion:</strong><br/>
      <em>For further practice, attempt the online question bank for this chapter.
      Practice objective questions with timer for exam readiness.</em>
    </div>

    <p><em>All students must submit before leaving:</em></p>
    <ul>
      <li>Completed notebook — all 5 days of notes</li>
      <li>Book-back exercises — answered and marked</li>
      <li>Outline map — all required locations marked and labeled</li>
      <li>All homework tasks from Days 1–4</li>
      <li>Chapter practice questions (Q1 and Q2 from today)</li>
    </ul>

  </div>

  <!-- ═══ CLOSING ═══ -->
  <div class="time-block">
    <strong>Closing</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[2-3 sentences — congratulate students on completing the full chapter.
     Name 2-3 specific things they have learned and can now do.
     Motivate them for the next chapter.]"</p>

  </div>

</div>

RULES:
- Raw HTML only — start with <h3 class="day-header">Day 5
- Map tasks must be based on ACTUAL chapter content below
- Map tips must be specific and memorable — not generic
- Book-back discussion must reference ACTUAL chapter topics
- No Tamil required in Day 5 — English only (evaluation day)
- Test series suggestion must appear in student task section
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
            print(f"❌ SS LP Day 5 error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 7 — Assessment Summary
    # -------------------------------------------------------------------------

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, discipline_display):
        try:
            prompt = f"""Generate ONLY the Assessment Summary section.
Do NOT repeat any day content. This is a summary evaluation block only.

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
       Complete sentence answer | Tamil version of question.
       Questions must be about SUBJECT MATTER — not about tasks or instructions.]
    </tbody>
  </table>

  <h3>CCQ Bank — Quick Reference for Revision</h3>
  <p><em>10 concept check questions from across all 5 days.
  All questions are about subject matter — not about instructions or tasks.
  For teacher's reference during revision sessions:</em></p>
  <ol>
    [List 10 CCQ questions with one-line factual answers.
     Each CCQ must be under 8 words.
     Based on actual chapter content — not generic.]
  </ol>

  <h3>Written Assessment Task</h3>
  <p>[One meaningful written task covering the full chapter —
     suitable for a class test or revision exercise.
     Give a specific prompt — not open-ended.]</p>

  <div class="board-work">
    <strong>Model Answer (write on board before students start):</strong>
    <p>"[Sentence 1 of model answer — based on actual chapter content]"</p>
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
          <p><strong>Example:</strong> "[sentence from chapter] _______ (word1 / word2)"</p>
          <p><strong>Word Bank:</strong> [5 key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer 3 questions in 2-3 sentences each</p>
          <p><strong>Example starter:</strong> "[event from chapter] happened because _______."</p>
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
    <li>☐ Chapter practice questions attempted (Day 5)</li>
    <li>☐ [Add 1-2 chapter-specific checklist items based on actual content]</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table MUST have exactly 5 rows with Tamil column
- CCQ bank MUST have exactly 10 questions — all about subject matter, under 8 words each
- Differentiation MUST have actual example tasks with real sentences from chapter
- Model answer MUST be realistic and based on actual chapter content
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