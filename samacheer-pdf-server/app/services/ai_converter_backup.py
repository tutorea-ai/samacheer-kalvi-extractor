"""
AI Content Converter — Final Version
Thin orchestrator. Delegates to content_builder modules.

Content → content_builder/assembler.py
QA      → content_builder/qa_builder.py
LP      → handled here directly (working perfectly, do not move)
"""

import re
import anthropic
from typing import Optional, Dict
from ..config import settings
from .section_detector import detect_sections, clean_noise
from ..content_builder.assembler import content_assembler
from ..content_builder.qa_builder import qa_builder


# ============================================================================
# LP SYSTEM PROMPT
# ============================================================================

LP_SYSTEM_PROMPT = """You are an experienced English teacher with deep knowledge of the Tamil Nadu Samacheer Kalvi syllabus and activity-based learning methods used in Indian classrooms.
Create a detailed, practical, script-by-script lesson plan so that even a brand new inexperienced teacher can walk into class and deliver a confident, effective session just by following it.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks (```html or ```)
- NEVER use backticks anywhere in your output
- Start directly with HTML tags — no preamble text"""


# ============================================================================
# LP DURATION RULES
# ============================================================================

LP_DURATION_RULES = {
    "prose":         {"total": 10, "content": 4, "grammar": 6, "has_grammar": True},
    "poem":          {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "supplementary": {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "play":          {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "drama":         {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
}

def _get_lp_duration(lesson_type: str) -> dict:
    return LP_DURATION_RULES.get(lesson_type.lower(), LP_DURATION_RULES["supplementary"])


# ============================================================================
# HTML WRAPPER
# ============================================================================

def _wrap_html(body_content: str, title: str, content_type: str = "content") -> str:
    accent_colors = {"content": "#2E75B6", "qa": "#27AE60", "lp": "#8E44AD"}
    accent = accent_colors.get(content_type, "#2E75B6")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="/frontend/css/content-styles.css" />
  <style>
    .sk-content-header {{ border-left: 5px solid {accent}; padding-left: 12px; margin-bottom: 24px; }}
    .sk-content-header h1 {{ color: {accent}; font-size: 1.6rem; margin: 0 0 4px 0; }}
    .sk-content-header .sk-meta {{ font-size: 0.85rem; color: #777; }}
    table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
    th {{ background: {accent}; color: white; padding: 10px 14px; text-align: left; }}
    td {{ padding: 9px 14px; border-bottom: 1px solid #eee; }}
    tr:nth-child(even) td {{ background: #f9f9f9; }}
    blockquote {{ border-left: 4px solid {accent}; margin: 16px 0; padding: 10px 16px; background: #f5f5f5; color: #444; font-style: italic; }}
    .day-block {{ background: #fafafa; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; margin-bottom: 24px; }}
    .day-header {{ color: {accent}; border-bottom: 2px solid {accent}; padding-bottom: 8px; }}
    .time-block {{ margin-bottom: 16px; padding: 12px; background: white; border-left: 3px solid {accent}; }}
    .teacher-says {{ background: #f0f7ff; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }}
    .student-says {{ background: #f0fff4; padding: 8px 12px; border-radius: 4px; margin: 4px 0; }}
    .board-work {{ background: #1a1a2e; color: #fff; padding: 8px 12px; border-radius: 4px; margin: 4px 0; font-family: monospace; }}
    .transition {{ color: #666; font-style: italic; margin: 4px 0; }}
    .assessment-block {{ background: #fafafa; border: 1px solid #e8e8e8; border-radius: 8px; padding: 16px; }}
  </style>
</head>
<body>
  <div class="sk-lesson-wrapper">
    {body_content}
  </div>
</body>
</html>"""


# ============================================================================
# CLEAN AI OUTPUT
# ============================================================================

def _clean_ai_output(raw: str) -> str:
    if not raw:
        return raw
    text = raw.strip()
    text = re.sub(r'^```(?:html)?\s*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    text = re.sub(r'```(?:html)?\s*\n', '', text)
    text = re.sub(r'\n```', '', text)
    first_tag = re.search(r'<(?:div|h[1-6]|section|p|table|hr)', text)
    if first_tag and first_tag.start() > 0:
        preamble = text[:first_tag.start()].strip()
        if preamble and not preamble.startswith('<'):
            text = text[first_tag.start():]
    return text.strip()


# ============================================================================
# MAIN CONVERTER CLASS
# ============================================================================

class AIContentConverter:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Claude AI Converter initialized — model: {self.model}")

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC: generate_all
    # ──────────────────────────────────────────────────────────────────────────

    def generate_all(self, text: str, metadata: Dict) -> Dict[str, Optional[str]]:
        results      = {"content": None, "qa": None, "lp": None}
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        subject      = metadata.get("subject", "english")
        lesson_type  = metadata.get("lesson_type", "prose")

        print(f"🤖 Generating: Content + QA + LP for '{lesson_title}'")

        # ── Clean + detect sections ONCE — used by all three generators ───────
        print(f"   🧹 Cleaning extracted text...")
        text = clean_noise(text)
        print(f"   📋 Detecting sections...")
        sections = detect_sections(text, lesson_type=lesson_type)
        print(f"   📋 Sections: { {k:v for k,v in sections.items() if v and k != 'lesson_type'} }")
        metadata["_sections"] = sections

        # ── CONTENT — via assembler ───────────────────────────────────────────
        print(f"\n   📄 Generating Content HTML...")
        try:
            content_html = content_assembler.assemble(text, sections, metadata)
            if content_html:
                results["content"] = _wrap_html(
                    content_html,
                    title=f"{lesson_title} | Class {class_num} {subject.title()}",
                    content_type="content"
                )
                print(f"   ✅ Content HTML ready ({len(content_html)} chars)")
            else:
                print(f"   ❌ Content generation failed")
        except Exception as e:
            print(f"   ❌ Content error: {e}")

        # ── QA — via qa_builder ───────────────────────────────────────────────
        print(f"\n   ❓ Generating QA HTML...")
        try:
            qa_html = qa_builder.generate(text, metadata)
            if qa_html:
                results["qa"] = _wrap_html(
                    qa_html,
                    title=f"Q&A — {lesson_title} | Class {class_num}",
                    content_type="qa"
                )
                print(f"   ✅ QA HTML ready ({len(qa_html)} chars)")
            else:
                print(f"   ❌ QA generation failed")
        except Exception as e:
            print(f"   ❌ QA error: {e}")

        # ── LP — handled directly here, working perfectly, do not change ──────
        print(f"\n   📌 Generating LP HTML...")
        try:
            lp_html = self._generate_lp(text, metadata)
            if lp_html:
                results["lp"] = _wrap_html(
                    lp_html,
                    title=f"Lesson Plan — {lesson_title} | Class {class_num}",
                    content_type="lp"
                )
                print(f"   ✅ LP HTML ready ({len(lp_html)} chars)")
            else:
                print(f"   ❌ LP generation failed")
        except Exception as e:
            print(f"   ❌ LP error: {e}")

        return results

    # ══════════════════════════════════════════════════════════════════════════
    # LP GENERATION
    # Day-by-day. One call per day. Full text context every call.
    # This is the core of the platform. Do not modify without careful testing.
    # ══════════════════════════════════════════════════════════════════════════

    def _generate_lp(self, text: str, metadata: Dict) -> Optional[str]:
        """
        Generates LP day by day.
        One API call per day — no text splitting, no continuation guessing.
        Every call receives the full lesson text as context.

        Prose:              12 calls (preamble + 10 days + assessment)
        Poem/Supplementary:  5 calls (preamble + 3 days  + assessment)
        Play/Drama:          5 calls (preamble + 3 days  + assessment)
        """
        lesson_type  = metadata.get("lesson_type", "prose").lower()
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        lesson_title = metadata.get("lesson_title", "Unknown")

        duration     = _get_lp_duration(lesson_type)
        total_days   = duration["total"]
        content_days = duration["content"]
        grammar_days = duration["grammar"]
        has_grammar  = duration["has_grammar"]

        type_display_map = {
            "prose":         "Prose",
            "poem":          "Poem",
            "supplementary": "Supplementary Reader",
            "play":          "Drama or Play",
            "drama":         "Drama or Play",
        }
        type_display  = type_display_map.get(lesson_type, "Prose")
        duration_line = (
            f"{total_days} days ({content_days} Content + {grammar_days} Grammar)"
            if has_grammar else
            f"{total_days} days (Content Only)"
        )
        total_calls = total_days + 2  # preamble + days + assessment

        print(f"      [LP] Day-by-day: {total_calls} API calls total")
        print(f"      [LP] Type: {type_display} | Days: {total_days}")
        parts = []

        # ── Call 1: Preamble ──────────────────────────────────────────────────
        print(f"      [LP] Call 1/{total_calls}: Preamble...")
        preamble = self._lp_call_preamble(
            text, class_num, unit, lesson_title,
            type_display, duration_line, total_days, has_grammar
        )
        if preamble:
            parts.append(_clean_ai_output(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting LP")
            return None

        # ── Content days ──────────────────────────────────────────────────────
        for day_num in range(1, content_days + 1):
            call_num = day_num + 1
            print(f"      [LP] Call {call_num}/{total_calls}: Day {day_num} (Content)...")
            day_html = self._lp_call_content_day(
                text, class_num, unit, lesson_title,
                type_display, day_num, content_days, total_days
            )
            if day_html:
                parts.append(_clean_ai_output(day_html))
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        # ── Grammar days (prose only) ─────────────────────────────────────────
        if has_grammar:
            for g_day in range(1, grammar_days + 1):
                day_num  = content_days + g_day
                call_num = day_num + 1
                print(f"      [LP] Call {call_num}/{total_calls}: Day {day_num} (Grammar {g_day})...")
                day_html = self._lp_call_grammar_day(
                    text, class_num, unit, lesson_title,
                    type_display, day_num, g_day, grammar_days, total_days
                )
                if day_html:
                    parts.append(_clean_ai_output(day_html))
                    print(f"         ✅ Grammar Day {g_day} ({len(day_html)} chars)")
                else:
                    print(f"         ❌ Grammar Day {g_day} failed — continuing")

        # ── Assessment Summary ────────────────────────────────────────────────
        print(f"      [LP] Call {total_calls}/{total_calls}: Assessment Summary...")
        assessment = self._lp_call_assessment(
            text, class_num, unit, lesson_title,
            type_display, total_days
        )
        if assessment:
            parts.append(_clean_ai_output(assessment))
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [LP] ✅ Complete — {len(parts)} parts, {len(combined)} chars total")
        return combined

    # ──────────────────────────────────────────────────────────────────────────
    # LP: Preamble
    # ──────────────────────────────────────────────────────────────────────────

    def _lp_call_preamble(self, text, class_num, unit, lesson_title,
                           type_display, duration_line, total_days, has_grammar):
        try:
            grammar_obj = "• Grammar objectives (specific topics from this lesson's grammar section)" if has_grammar else ""
            prompt = f"""Generate ONLY the opening section of a Samacheer Kalvi lesson plan.
Do NOT generate any days. Stop after Teaching Aids.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}
Duration: {duration_line}

Generate these 4 sections:

<div class="sk-content-header">
  <h1>Lesson Plan — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | English | Unit {unit} | {type_display} | {duration_line}</p>
</div>

<h2>Part 1: General Information</h2>
<table>
  [rows for: Class, Subject, Unit/Lesson Title, Text Type, Total Days, Session Duration]
</table>

<h2>Part 2: Learning Objectives</h2>
<ul>
  • Knowledge objectives (2-3 points specific to this lesson)
  • Skill objectives — Reading, Writing, Listening, Speaking
  {grammar_obj}
  • Value-based objectives (from this lesson's themes)
</ul>

<h2>Part 3: Teaching Aids</h2>
<ul>
  [All materials needed across all {total_days} days]
  [Textbook, blackboard, charts, flashcards, worksheets etc.]
</ul>

OUTPUT RULES:
- Raw HTML only
- Start with <div class="sk-content-header">
- Stop after Teaching Aids closing </ul>
- Do NOT start any Day block

Lesson Text:
---
{text}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system=LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ LP preamble error: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # LP: Content Day
    # ──────────────────────────────────────────────────────────────────────────

    def _lp_call_content_day(self, text, class_num, unit, lesson_title,
                              type_display, day_num, content_days, total_days):
        try:
            if content_days == 1:
                focus = "the entire lesson"
            elif day_num == 1:
                focus = "introduction and first section of the lesson"
            elif day_num == content_days:
                focus = "final section of the lesson"
            else:
                focus = f"middle section (~{int((day_num/content_days)*100)}% through)"

            next_preview = f"Day {day_num+1}" if day_num < total_days else "the assessment"

            prompt = f"""Generate ONLY Day {day_num} of the lesson plan. Nothing else.
Do NOT include Preamble, General Info, Objectives, or Teaching Aids.
Do NOT generate Day {day_num+1} or any other day.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}
Content Day {day_num} of {content_days} | Total: {total_days} days
Focus for today: {focus}

Generate Day {day_num} in this EXACT format:

<h3 class="day-header">Day {day_num} — [Topic Focus for this day]</h3>
<div class="day-block">

  <div class="time-block">
    <strong>[0–5 min] Warm Up / Review</strong>
    <p class="teacher-says"><strong>Teacher says:</strong> "[exact words to say]"</p>
    <div class="board-work"><strong>Board Work:</strong> [exactly what to write on board]</div>
    <p class="teacher-says"><strong>Teacher asks:</strong> "[question to class]"</p>
    <p class="student-says"><strong>Expected response:</strong> "[complete sentence answer]"</p>
    <div class="transition"><em>Transition:</em> "[exact words to move to next segment]"</div>
  </div>

  <div class="time-block">
    <strong>[5–15 min] Main Activity</strong>
    <p class="teacher-says"><strong>Teacher says:</strong> "[exact instructions]"</p>
    <div class="board-work"><strong>Board Work:</strong> [exactly what to write]</div>
    <p>Student Activity: [exactly what students do]</p>
    <p class="student-says"><strong>Expected response:</strong> "[sample complete answer]"</p>
    <p class="teacher-says"><strong>If students struggle:</strong> "[supportive hint]"</p>
    <div class="transition"><em>Transition:</em> "[exact words]"</div>
  </div>

  <div class="time-block">
    <strong>[15–25 min] Student Practice</strong>
    <p class="teacher-says"><strong>Teacher says:</strong> "[exact instructions]"</p>
    <p>Activity Type: [Think-Pair-Share / Group / Individual / Role play]</p>
    <p>Step 1: [exact instruction]</p>
    <p>Step 2: [exact instruction]</p>
    <p>Step 3: [exact instruction]</p>
    <p class="student-says"><strong>Expected output:</strong> "[what students produce]"</p>
    <div class="transition"><em>Transition:</em> "[exact words]"</div>
  </div>

  <div class="time-block">
    <strong>[25–30 min] Closure</strong>
    <p class="teacher-says"><strong>Teacher says:</strong> "[summarize key points in exact words]"</p>
    <div class="board-work"><strong>Board Work:</strong> [3-5 key words or summary sentence]</div>
    <p><strong>Exit Question:</strong> "[one question every student answers before leaving]"</p>
    <p class="student-says"><strong>Expected answer:</strong> "[complete sentence]"</p>
    <p class="teacher-says"><strong>Teacher says:</strong> "[closing words + preview of {next_preview}]"</p>
    <p><strong>Homework:</strong> [specific simple task based on today's lesson]</p>
    <p><strong>Model Answer:</strong> "[one complete model answer for homework]"</p>
  </div>

</div>

OUTPUT RULES:
- Raw HTML only
- Start directly with <h3 class="day-header">Day {day_num}
- Be detailed and scripted — teacher reads this word for word
- Base ALL content on the actual lesson text below
- Do NOT start Day {day_num+1}

Lesson Text:
---
{text}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system=LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ LP content day {day_num} error: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # LP: Grammar Day
    # ──────────────────────────────────────────────────────────────────────────

    def _lp_call_grammar_day(self, text, class_num, unit, lesson_title,
                              type_display, day_num, grammar_day_num,
                              grammar_days, total_days):
        try:
            next_preview = f"Day {day_num+1}" if day_num < total_days else "the assessment"
            prompt = f"""Generate ONLY Day {day_num} of the lesson plan.
This is Grammar Day {grammar_day_num} of {grammar_days} grammar days.
Do NOT generate any other day.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}
Day {day_num} of {total_days} total days.

IMPORTANT: Use the ACTUAL grammar topic from the lesson text below.
Do NOT invent grammar topics. Use only what is in the grammar section.

<h3 class="day-header">Day {day_num} — Grammar: [Exact Topic from Textbook]</h3>
<div class="day-block">

  <div class="time-block">
    <strong>[0–5 min] Review + Grammar Introduction</strong>
    <p class="teacher-says"><strong>Teacher says:</strong> "[connect grammar topic to a sentence from the lesson]"</p>
    <div class="board-work"><strong>Board Work:</strong> [example sentence from the lesson]</div>
    <p class="teacher-says"><strong>Teacher says:</strong> "[simple clear explanation of the grammar rule]"</p>
    <p class="teacher-says"><strong>Teacher asks:</strong> "[question to check if students recognise the pattern]"</p>
    <p class="student-says"><strong>Expected response:</strong> "[complete sentence]"</p>
  </div>

  <div class="time-block">
    <strong>[5–15 min] Grammar Explanation + Examples</strong>
    <p class="teacher-says"><strong>Teacher says:</strong> "[step-by-step explanation with examples from lesson]"</p>
    <div class="board-work"><strong>Board Work:</strong> [grammar rule + 3 example sentences from lesson]</div>
    <p><strong>Q1:</strong> [question] — <strong>Expected:</strong> [complete sentence]</p>
    <p><strong>Q2:</strong> [question] — <strong>Expected:</strong> [complete sentence]</p>
    <p><strong>Q3:</strong> [question] — <strong>Expected:</strong> [complete sentence]</p>
  </div>

  <div class="time-block">
    <strong>[15–25 min] Student Practice</strong>
    <p class="teacher-says"><strong>Teacher says:</strong> "Now let us practice. Open your notebook and write these."</p>
    <p><strong>Q1:</strong> [question] — Answer: [complete sentence]</p>
    <p><strong>Q2:</strong> [question] — Answer: [complete sentence]</p>
    <p><strong>Q3:</strong> [question] — Answer: [complete sentence]</p>
    <p><strong>Q4:</strong> [question] — Answer: [complete sentence]</p>
    <p><strong>Q5:</strong> [question] — Answer: [complete sentence]</p>
  </div>

  <div class="time-block">
    <strong>[25–30 min] Closure</strong>
    <p class="teacher-says"><strong>Teacher says:</strong> "[summarize the grammar rule in 2 simple sentences]"</p>
    <div class="board-work"><strong>Board Work:</strong> [rule + one clear example]</div>
    <p><strong>Exit Question:</strong> "[one grammar question every student answers]"</p>
    <p class="student-says"><strong>Expected answer:</strong> "[complete sentence]"</p>
    <p class="teacher-says"><strong>Teacher says:</strong> "[closing + preview of {next_preview}]"</p>
    <p><strong>Homework:</strong> [3-5 grammar practice questions]</p>
    <p><strong>Model Answer:</strong> "[one complete model answer]"</p>
  </div>

</div>

OUTPUT RULES:
- Raw HTML only
- Start directly with <h3 class="day-header">Day {day_num}
- Do NOT start Day {day_num+1}

Lesson Text:
---
{text}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system=LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ LP grammar day {grammar_day_num} error: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # LP: Assessment Summary
    # ──────────────────────────────────────────────────────────────────────────

    def _lp_call_assessment(self, text, class_num, unit, lesson_title,
                             type_display, total_days):
        try:
            prompt = f"""Generate ONLY the Assessment Summary section. Do NOT repeat any days.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}
Total days in this lesson plan: {total_days}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Oral Assessment Questions</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Oral Assessment Question</th>
        <th>Expected Answer</th>
      </tr>
    </thead>
    <tbody>
      [One row for EVERY day — Day 1 through Day {total_days}]
      [Each question tests the key learning from that specific day]
      [Each answer is a complete sentence based on the lesson]
    </tbody>
  </table>

  <h3>Written Assessment Task</h3>
  <p>[One meaningful written task that covers the full lesson — character sketch, summary, paragraph, letter etc.]</p>
  <div class="answer-box">
    <textarea placeholder="Student writes answer here..."></textarea>
  </div>

  <h3>Differentiated Support Plan</h3>
  <table>
    <thead>
      <tr>
        <th>Learner Type</th>
        <th>Strategy</th>
        <th>Activity</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Slow Learners</td>
        <td>[specific support strategy]</td>
        <td>[simpler activity with teacher support]</td>
      </tr>
      <tr>
        <td>Average Learners</td>
        <td>[standard approach]</td>
        <td>[standard classroom activity]</td>
      </tr>
      <tr>
        <td>Advanced Learners</td>
        <td>[extension strategy]</td>
        <td>[enrichment or creative activity]</td>
      </tr>
    </tbody>
  </table>

</div>

OUTPUT RULES:
- Raw HTML only
- Start directly with <h2>Assessment Summary</h2>
- Day-wise table MUST have exactly {total_days} rows — one per day
- Base ALL questions on actual content from the lesson text below
- This is the FINAL section — nothing comes after </div>

Lesson Text:
---
{text}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system=LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ LP assessment error: {e}")
            return None


# Singleton instance
ai_converter = AIContentConverter()