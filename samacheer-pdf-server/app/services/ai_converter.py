"""
AI Content Converter — Final Version
Thin orchestrator. Delegates to content_builder modules.

Content → content_builder/assembler.py (restored — EPUB text replaces pdf2htmlEX)
QA      → content_builder/qa_builder.py
LP      → handled here directly (working perfectly, do not move)
"""

import re
import anthropic
from typing import Optional, Dict
from ..config import settings
from .section_detector import detect_sections, clean_noise
from ..content_builder.qa_builder import qa_builder
from ..content_builder.assembler import content_assembler


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
    .show-answer-btn {{
      background: #8B4513;
      color: white;
      border: none;
      padding: 6px 16px;
      border-radius: 6px;
      cursor: pointer;
      margin: 8px 0;
      font-size: 0.9rem;
    }}
    .show-answer-btn.active {{ background: #5c4033; }}
    .answer-reveal {{
      display: none;
      padding: 10px;
      background: #f5ebe0;
      border-left: 3px solid #8B4513;
      border-radius: 4px;
      margin-bottom: 12px;
    }}
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
        sections = {}
        if subject.lower() not in ["socialscience", "social_science"]:
            sections = detect_sections(text, lesson_type=lesson_type)
            print(f"   📋 Sections: { {k:v for k,v in sections.items() if v and k != 'lesson_type'} }")
        metadata["_sections"] = sections

        # ── CONTENT — via assembler (EPUB clean text → Claude → interactive HTML)
        print(f"\n   📄 Generating Content HTML...")
        try:
            content_html = content_assembler.assemble(text, sections, metadata)
            if content_html:
                results["content"] = _wrap_html(
                    content_html,
                    title=f"{lesson_title} | Class {class_num}",
                    content_type="content"
                )
                print(f"   ✅ Content HTML ready ({len(content_html)} chars)")
            else:
                print(f"   ❌ Content generation failed")
        except Exception as e:
            print(f"   ❌ Content error: {e}")

        # ── QA ────────────────────────────────────────────────────────────────
        print(f"\n   ❓ Generating QA HTML...")
        try:
            if subject.lower() in ["socialscience", "social_science"]:
                from ..content_builder.master_router import generate_qa
                qa_html = generate_qa(text, metadata)
            else:
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

        # ── LP ────────────────────────────────────────────────────────────────
        print(f"\n   📌 Generating LP HTML...")
        try:
            if subject.lower() in ["socialscience", "social_science"]:
                lp_html = self._generate_ss_lp(text, metadata)
            else:
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
            print(f"      [LP] Detecting grammar topics for {grammar_days} days...")
            grammar_topics = self._detect_grammar_topics(text, grammar_days)
            print(f"         ✅ Topics: {grammar_topics}")

            for g_day in range(1, grammar_days + 1):
                day_num  = content_days + g_day
                call_num = day_num + 1
                topic = grammar_topics[g_day - 1] if g_day <= len(grammar_topics) else f"Day {day_num}: Language Activities"
                print(f"      [LP] Call {call_num}/{total_calls}: Day {day_num} (Grammar {g_day} — {topic})...")
                day_html = self._lp_call_grammar_day(
                    text, class_num, unit, lesson_title,
                    type_display, day_num, g_day, grammar_days, total_days,
                    topic=topic,
                    all_topics=grammar_topics
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
            from .lp_prompt_builder import build_content_day_prompt
            prompt = build_content_day_prompt(
                text=text, class_num=class_num, unit=unit,
                lesson_title=lesson_title, type_display=type_display,
                day_num=day_num, content_days=content_days,
                total_days=total_days
            )
            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system=LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ LP content day {day_num} error: {e}")
            return None

    def _detect_grammar_topics(self, text: str, grammar_days: int) -> list:
        prompt = f"""Read this lesson text carefully.

Identify ALL language learning topics present:
- Grammar rules (Articles, Tenses, Conjunctions etc.)
- Vocabulary sections
- Listening exercises
- Speaking activities
- Reading comprehension
- Writing tasks

Then distribute them across exactly {grammar_days} days.
Return ONLY a JSON list like:
["Day 5: Articles — a, an, the rules",
 "Day 6: Prepositional Phrases",
 "Day 7: Vocabulary and Slang Expressions",
 "Day 8: Listening and Speaking activities",
 "Day 9: Reading Comprehension",
 "Day 10: Writing — Speech Writing"]

Return JSON only. No explanation.

Lesson text:
---
{text[-20000:]}
---"""
        try:
            response = self.client.messages.create(
                model=self.model, max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            import json, re
            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            return json.loads(raw)
        except Exception as e:
            print(f"⚠️  Topic detection failed ({e}) — using fallback topics")
            return [f"Day {i+1}: Grammar and Language Activities"
                    for i in range(grammar_days)]

    def _lp_call_grammar_day(self, text, class_num, unit, lesson_title,
                              type_display, day_num, grammar_day_num,
                              grammar_days, total_days, topic: str = "",
                              all_topics: list = None):
        try:
            from .lp_prompt_builder import build_grammar_day_prompt
            prompt = build_grammar_day_prompt(
                text=text, class_num=class_num, unit=unit,
                lesson_title=lesson_title, type_display=type_display,
                day_num=day_num, grammar_day_num=grammar_day_num,
                grammar_days=grammar_days, total_days=total_days,
                topic=topic, all_topics=all_topics or []
            )
            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system=LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ LP grammar day {grammar_day_num} error: {e}")
            return None

    def _lp_call_assessment(self, text, class_num, unit, lesson_title,
                             type_display, total_days):
        try:
            prompt = f"""Generate ONLY the Assessment Summary. Do NOT repeat any days.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}
Total days: {total_days}

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
      [One row per day — Day 1 through Day {total_days}]
      [Each row: day number, English question, complete sentence answer,
       Tamil version of question for struggling students]
    </tbody>
  </table>

  <h3>Written Assessment Task</h3>
  <p>[One meaningful written task covering the full lesson]</p>
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
          <p><strong>Word Bank:</strong> [3-4 words from lesson]</p>
          <p><em>ஆசிரியர் கூடவே உட்கார்ந்து உதவலாம்</em></p>
        </td>
        <td>
          <p><strong>Task:</strong> Answer in 2-3 sentences</p>
          <p><strong>Example:</strong> "[character] was _______ because _______."</p>
        </td>
        <td>
          <p><strong>Task:</strong> Write a full paragraph independently</p>
          <p><strong>Prompt:</strong> "Describe [topic] in your own words with 5 sentences."</p>
        </td>
      </tr>
    </tbody>
  </table>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table MUST have exactly {total_days} rows with Tamil column
- Differentiation MUST have actual example tasks
- Model example MUST be on board
- Base on lesson text below

Lesson Text:
---
{text}
---"""
            response = self.client.messages.create(
                model=self.model, max_tokens=6000,
                system=LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ LP assessment error: {e}")
            return None

    def _generate_ss_lp(self, text: str, metadata: dict) -> Optional[str]:
        """Generate Social Science LP via master_router."""
        from ..content_builder.master_router import generate_lp
        metadata.setdefault("subject", "SocialScience")
        return generate_lp(text, metadata)


# Singleton instance
ai_converter = AIContentConverter()