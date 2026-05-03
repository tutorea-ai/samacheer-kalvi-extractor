"""
ss_lp_builder.py
----------------
Lesson Plan Generator for Samacheer Kalvi Social Science (Classes 6-12).
Handles History, Geography, Civics, Economics disciplines.

Structure:
  - 3 days per chapter (30 minutes per day)
  - Same bilingual format as English LP (English + Tamil mirror)
  - No grammar days — all 3 days are content days
  - Claude decides how to split chapter across 3 days dynamically
  - Preamble + 3 content days + Assessment = 5 API calls total

Key difference from English LP:
  - 3 days instead of 10
  - No grammar section
  - Subject-specific activities (timeline, map description, source analysis etc.)
  - Same bilingual scripting requirement
"""

import re
import anthropic
from typing import Optional, Dict
from ..config import settings


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SS_LP_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Social Science teacher
with deep knowledge of Tamil Nadu state board curriculum and activity-based
learning methods used in Indian government schools.

Create a detailed, practical, script-by-script lesson plan so that even a
brand new inexperienced teacher can walk into class and deliver a confident,
effective 30-minute session just by following it.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text"""


# ============================================================================
# SS LP BUILDER CLASS
# ============================================================================

class SSLPBuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ SS LP Builder initialized — model: {self.model}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Social Science LP for a chapter.
        Makes 5 API calls: Preamble + Day 1 + Day 2 + Day 3 + Assessment

        Args:
            text:     Clean chapter text from EPUB extractor
            metadata: Dict with class, unit, lesson_title, discipline etc.

        Returns:
            Combined HTML string, or None on failure.
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        discipline   = metadata.get("discipline", "history")
        discipline_display = discipline.title()

        total_calls = 5  # preamble + 3 days + assessment
        print(f"      [SS LP] Generating: {discipline_display} | {lesson_title}")
        print(f"      [SS LP] 5 API calls: Preamble + 3 Days + Assessment")

        parts = []

        # ── Call 1: Preamble ──────────────────────────────────────────
        print(f"      [SS LP] Call 1/{total_calls}: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, discipline_display
        )
        if preamble:
            parts.append(self._clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting LP")
            return None

        # ── Calls 2-4: Content Days ───────────────────────────────────
        for day_num in range(1, 4):
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

        # ── Call 5: Assessment ────────────────────────────────────────
        print(f"      [SS LP] Call 5/{total_calls}: Assessment...")
        assessment = self._call_assessment(
            text, class_num, unit, lesson_title,
            discipline_display
        )
        if assessment:
            parts.append(self._clean(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [SS LP] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # ------------------------------------------------------------------
    # Preamble
    # ------------------------------------------------------------------

    def _call_preamble(self, text, class_num, unit,
                       lesson_title, discipline_display):
        try:
            prompt = f"""Generate ONLY the opening section of a Samacheer Kalvi
Social Science lesson plan. Do NOT generate any days. Stop after Teaching Aids.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | {discipline_display}
Duration: 3 days × 30 minutes = 90 minutes total

Generate these sections:

<div class="sk-content-header">
  <h1>Lesson Plan — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — {discipline_display} |
     Unit {unit} | 3 Days × 30 Minutes</p>
</div>

<h2>Part 1: General Information</h2>
<table>
  [rows for: Class, Subject, Discipline, Unit/Chapter Title,
   Total Days, Session Duration (30 min each)]
</table>

<h2>Part 2: Learning Objectives</h2>
<ul>
  • Knowledge objectives (3-4 points specific to this chapter)
  • Skill objectives (reading maps/sources, analysis, discussion)
  • Value-based objectives (from this chapter's themes)
</ul>

<h2>Part 3: Teaching Aids</h2>
<ul>
  [All materials needed across all 3 days — textbook, maps,
   charts, timeline materials, blackboard, flashcards etc.]
</ul>

OUTPUT RULES:
- Raw HTML only
- Start with <div class="sk-content-header">
- Stop after Teaching Aids </ul>
- Do NOT start any Day block

Chapter Text:
---
{text}
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

    # ------------------------------------------------------------------
    # Content Day
    # ------------------------------------------------------------------

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          discipline_display, day_num):
        try:
            focus_map = {
                1: "introduction, background context, and first major section of the chapter",
                2: "middle sections, key events/concepts, and analysis activities",
                3: "final sections, summary, exercises, and consolidation",
            }
            focus = focus_map.get(day_num, "chapter content")
            next_day = f"Day {day_num + 1}" if day_num < 3 else "the Assessment"

            prompt = f"""Generate ONLY Day {day_num} of the lesson plan. Nothing else.
Do NOT include Preamble. Do NOT generate Day {day_num + 1} or any other day.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | {discipline_display}
Day {day_num} of 3 | Duration: 30 minutes
Focus for today: {focus}

═══════════════════════════════════════════════════════
CONTEXT — READ CAREFULLY
═══════════════════════════════════════════════════════

This lesson plan is for Tamil Nadu government school teachers.
Students are from underprivileged rural backgrounds.
Many teachers are Tamil-medium trained and not fully confident in English.

THE LP MUST DO THREE THINGS:
1. Give teacher a word-for-word English script to deliver to class
2. Give teacher the exact same script in Tamil — full understanding
3. Bridge students from Tamil to English through bilingual support

═══════════════════════════════════════════════════════
LANGUAGE RULE — MOST IMPORTANT
═══════════════════════════════════════════════════════

EVERY instruction must have TWO equal layers:

LAYER 1 — ENGLISH: Minimum 3-4 complete sentences.
Word for word. What to say, what to write on board, how much time.

LAYER 2 — TAMIL: Exact mirror of Layer 1.
Same sentences. Same detail. Same length. NOT a summary.

═══════════════════════════════════════════════════════

<h3 class="day-header">Day {day_num} — [Topic Focus for today from chapter]</h3>
<!-- TOPIC LOCK: Day {day_num} covers {focus} -->
<div class="day-block">

  <div class="time-block">
    <strong>[0–5 min] Warm Up / Review</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — greet students, connect to previous day or
     introduce the chapter context, state today's focus,
     give specific opening instruction]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — same greeting, same connection,
      same today's focus, same instruction. Nothing missing.]"</p>
    </div>

    <div class="board-work">
      <strong>Board Work:</strong><br/>
      [Write 3-4 key terms from today's content with Tamil meanings]<br/>
      Term 1: [English] — [Tamil meaning]<br/>
      Term 2: [English] — [Tamil meaning]<br/>
      Term 3: [English] — [Tamil meaning]
    </div>

    <p class="teacher-says"><strong>Teacher asks (English):</strong><br/>
    "[2-3 sentences — opening question to activate prior knowledge.
     Give thinking time. Call on a student.]"</p>

    <div class="tamil-scaffold">
      <em>Tamil version (exact mirror):</em><br/>
      "[2-3 Tamil sentences — same question, same thinking time]"
    </div>

    <p class="student-says"><strong>Expected response:</strong>
    "[Complete sentence answer]"</p>
  </div>

  <div class="time-block">
    <strong>[5–20 min] Main Activity — Teaching + Discussion</strong>

    <div class="vocab-block">
      <strong>Key Terms (write on board before starting):</strong>
      <table>
        <thead>
          <tr><th>Term</th><th>English Meaning</th><th>Tamil பொருள்</th></tr>
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

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain the main content for today.
     Tell students what to read, what to look for,
     key events/concepts to understand, time given.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[4-5 Tamil sentences — same explanation, same content,
      same instructions. Nothing shortened.]"</p>
      <p><em>கஷ்டப்படும் மாணவர்களுக்கு:</em><br/>
      "[2-3 Tamil sentences — simpler explanation for struggling students]"</p>
    </div>

    <p class="teacher-says"><strong>Teacher asks Q1 (English):</strong><br/>
    "[Question about today's content — 2 sentences]"</p>
    <div class="tamil-scaffold">
      <em>Tamil version:</em> "[Exact Tamil mirror of Q1]"
    </div>
    <p class="student-says"><strong>Expected:</strong> "[Complete answer]"</p>

    <p class="teacher-says"><strong>Teacher asks Q2 (English):</strong><br/>
    "[Second question — 2 sentences]"</p>
    <div class="tamil-scaffold">
      <em>Tamil version:</em> "[Exact Tamil mirror of Q2]"
    </div>
    <p class="student-says"><strong>Expected:</strong> "[Complete answer]"</p>

    <p class="teacher-says"><strong>Teacher asks Q3 (English):</strong><br/>
    "[Third question — 2 sentences]"</p>
    <div class="tamil-scaffold">
      <em>Tamil version:</em> "[Exact Tamil mirror of Q3]"
    </div>
    <p class="student-says"><strong>Expected:</strong> "[Complete answer]"</p>
  </div>

  <div class="time-block">
    <strong>[20–25 min] Student Practice</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — tell students to open notebook and write.
     Explain exactly what to write. Give time limit.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — same notebook instruction,
      same task, same time limit.]"</p>
      <p><em>கஷ்டப்படும் மாணவர்களுக்கு:</em><br/>
      "[2-3 Tamil sentences — what to say to struggling students]"</p>
    </div>

    <p><strong>Student Task:</strong> [Exactly what students write/do]</p>
    <p class="student-says"><strong>Expected output:</strong>
    "[Sample answer or notes]"</p>
  </div>

  <div class="time-block">
    <strong>[25–30 min] Closure + Homework</strong>

    <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 sentences — summarize today's key learning.
     Name specific things students learned.
     Preview {next_day}. Praise the class.]"</p>

    <div class="tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
      <p>"[3-4 Tamil sentences — same summary, same preview,
      same praise.]"</p>
    </div>

    <div class="board-work">
      <strong>Key Points from Today:</strong><br/>
      1. [Key point 1]<br/>
      2. [Key point 2]<br/>
      3. [Key point 3]
    </div>

    <div class="homework-block">
      <p class="teacher-says"><strong>Homework (English):</strong><br/>
      "[3-4 sentences — explain homework. What to write,
       how many points, when to submit.]"</p>

      <div class="tamil-scaffold">
        <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
        <p>"[3-4 Tamil sentences — same homework instructions.]"</p>
      </div>

      <div class="board-work">
        <strong>Model Answer (write on board):</strong><br/>
        "[1-2 sentences model answer for homework]"
      </div>

      <div class="tamil-scaffold">
        <em>மாணவர்களிடம் சொல்லுங்கள்:</em><br/>
        "இந்த மாதிரி எழுதுங்கள். Copy பண்ணாதீர்கள் —
        உங்கள் வார்த்தைகளில் எழுதுங்கள்."
      </div>
    </div>
  </div>

  <div class="time-block">
    <strong>Differentiated Activities</strong>
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
            <p><strong>Example:</strong> "[sentence] _______ (option1/option2)"</p>
            <p><strong>Word Bank:</strong> [3-4 key terms from today]</p>
            <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
          </td>
          <td>
            <p><strong>Task:</strong> Answer in 2-3 sentences</p>
            <p><strong>Example:</strong> "[starter sentence] _______ because _______."</p>
          </td>
          <td>
            <p><strong>Task:</strong> Write a paragraph independently</p>
            <p><strong>Prompt:</strong> "Explain [key concept] in your own words
               with at least 5 sentences."</p>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

</div>

ABSOLUTE RULES:
✅ Raw HTML only — start with <h3 class="day-header">Day {day_num}
✅ EVERY English instruction: minimum 3-4 complete sentences
✅ EVERY Tamil instruction: exact mirror — same length, same detail
✅ Key Terms table: 5 terms with Tamil meanings every day
✅ Board Work: always includes Tamil meanings
✅ Homework: always has model answer on board
✅ Differentiation: real example tasks with actual sentences
✅ Tamil must be real Tamil script — not transliteration
✅ Base ALL content on actual chapter text below
✅ Do NOT start Day {day_num + 1}

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

    # ------------------------------------------------------------------
    # Assessment
    # ------------------------------------------------------------------

    def _call_assessment(self, text, class_num, unit,
                         lesson_title, discipline_display):
        try:
            prompt = f"""Generate ONLY the Assessment Summary. Do NOT repeat any days.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | {discipline_display}
Total days: 3

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Oral Assessment Questions</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Oral Question (English)</th>
        <th>Expected Answer</th>
        <th>Tamil Prompt (தமிழ் உதவி)</th>
      </tr>
    </thead>
    <tbody>
      [One row per day — Day 1, Day 2, Day 3]
      [English question, complete sentence answer,
       Tamil version of question for struggling students]
    </tbody>
  </table>

  <h3>Written Assessment Task</h3>
  <p>[One meaningful written task covering the full chapter]</p>
  <div class="board-work">
    <strong>Model Example (write on board before students start):</strong>
    <p>"[Sentence 1 of model answer]"</p>
    <p>"[Sentence 2 of model answer]"</p>
    <p>"[Sentence 3 of model answer]"</p>
  </div>
  <div class="tamil-scaffold">
    <em>மாணவர்களிடம் சொல்லுங்கள்:</em>
    "இந்த மாதிரி வாக்கியங்களை பார்த்து உங்கள் சொந்த
    வாக்கியங்கள் எழுதுங்கள். Copy பண்ணாதீர்கள்."
  </div>

  <h3>Differentiated Support</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Slow Learners (கஷ்டப்படும் மாணவர்கள்)</th>
        <th>Average Learners (சராசரி மாணவர்கள்)</th>
        <th>Advanced Learners (திறமையான மாணவர்கள்)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Task:</strong> Fill in the blanks</p>
          <p><strong>Example:</strong> "[sentence] _______ (word1/word2)"</p>
          <p><strong>Word Bank:</strong> [3-4 key terms from chapter]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer in 2-3 sentences</p>
          <p><strong>Example:</strong> "[character/event] happened because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Write a full paragraph independently</p>
          <p><strong>Prompt:</strong> "Explain [key topic] in your own words
             with 5 sentences."</p>
        </td>
      </tr>
    </tbody>
  </table>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table MUST have exactly 3 rows with Tamil column
- Differentiation MUST have actual example tasks
- Model example MUST be on board
- Base on chapter text below

Chapter Text:
---
{text}
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

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _clean(self, raw: str) -> str:
        if not raw:
            return raw
        text = raw.strip()
        text = re.sub(r'```(?:html)?', '', text).strip()
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        first_tag = re.search(r'<(?:div|h[1-6]|section|p|table)', text)
        if first_tag and first_tag.start() > 0:
            preamble = text[:first_tag.start()].strip()
            if preamble and not preamble.startswith('<'):
                text = text[first_tag.start():]
        return text.strip()


# Singleton instance
ss_lp_builder = SSLPBuilder()