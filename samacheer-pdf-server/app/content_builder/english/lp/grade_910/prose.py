"""
english/lp/grade_910/prose.py
------------------------------
LP Builder for Samacheer Kalvi English — Prose
Classes 8, 9 & 10

Lesson structure:
  10 days total — 4 content days + 6 grammar days
  Session duration: 45 minutes

API calls: 13 total
  Call 0a → Section Extractor     (JSON — prose sections + grammar topics)
  Call 0b → Day Allocator         (JSON — sections to content days, topics to grammar days)
  Call 1  → Preamble
  Calls 2–5  → Content Days 1–4
  Calls 6–11 → Grammar Days 1–6
  Call 12 → Assessment Summary

v1.0 — June 2026
Built on lp_prompt_builder.py reference (grade_910 English prompt logic)
"""

import json
import re
import anthropic
from typing import Optional

from .....config import settings
from ...base import (
    ENGLISH_LP_SYSTEM_PROMPT_910,
    ENGLISH_PREAMBLE_INSTRUCTION,
    ENGLISH_TAMIL_INSTRUCTION_910,
    ENGLISH_CCQ_CFU_INSTRUCTION_910,
    ENGLISH_DAY_STRUCTURE_910,
    ENGLISH_ACTIVITY_MAP_910,
    ENGLISH_GRAMMAR_SPARK_STYLES,
    ENGLISH_CSS_RULES,
    clean,
)


# ============================================================================
# PROSE LP BUILDER — GRADE 910
# ============================================================================

class EnglishProseLPBuilder910:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English Prose LP Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public entry point — called by english_router.py
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [English Prose LP 910] Generating: {lesson_title}")
        print(f"      [English Prose LP 910] 13 API calls: 0a+0b+Preamble+Days1-4+Grammar1-6+Assessment")

        parts = []

        # ── Call 0a: Section Extractor ─────────────────────────────────────
        print(f"      [English Prose LP 910] Call 0a/13: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('prose_sections', []))} prose sections, "
              f"{len(sections.get('grammar_topics', []))} grammar topics")

        # ── Call 0b: Day Allocator ─────────────────────────────────────────
        print(f"      [English Prose LP 910] Call 0b/13: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        print(f"         ✅ Day plan ready")
        for d in range(1, 5):
            focus = day_plan.get(f"content_day{d}", {}).get("focus", "")
            print(f"            Content Day {d}: {focus}")
        for g in range(1, 7):
            topic = day_plan.get(f"grammar_day{g}", {}).get("topic", "")
            print(f"            Grammar Day {g}: {topic}")

        # ── Call 1: Preamble ───────────────────────────────────────────────
        print(f"      [English Prose LP 910] Call 1/13: Preamble...")
        preamble = self._call_preamble(text, class_num, unit, lesson_title, sections, day_plan)
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting")
            return None

        # ── Calls 2–5: Content Days 1–4 ───────────────────────────────────
        for day_num in range(1, 5):
            call_num = day_num + 1
            print(f"      [English Prose LP 910] Call {call_num}/13: Content Day {day_num}...")
            day_data = day_plan.get(f"content_day{day_num}", {})
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title,
                day_num, day_data, sections, day_plan
            )
            if day_html:
                parts.append(clean(day_html))
                print(f"         ✅ Content Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Content Day {day_num} failed — continuing")

        # ── Calls 6–11: Grammar Days 1–6 ──────────────────────────────────
        all_grammar_topics = [
            day_plan.get(f"grammar_day{g}", {}).get("topic", "")
            for g in range(1, 7)
        ]
        for g_num in range(1, 7):
            day_num  = 4 + g_num          # overall day number (5–10)
            call_num = 5 + g_num          # call number (6–11)
            print(f"      [English Prose LP 910] Call {call_num}/13: Grammar Day {g_num} (Day {day_num})...")
            g_data = day_plan.get(f"grammar_day{g_num}", {})
            g_html = self._call_grammar_day(
                text, class_num, unit, lesson_title,
                day_num, g_num, g_data, all_grammar_topics
            )
            if g_html:
                parts.append(clean(g_html))
                print(f"         ✅ Grammar Day {g_num} ({len(g_html)} chars)")
            else:
                print(f"         ❌ Grammar Day {g_num} failed — continuing")

        # ── Call 12: Assessment ────────────────────────────────────────────
        print(f"      [English Prose LP 910] Call 12/13: Assessment...")
        assessment = self._call_assessment(text, class_num, unit, lesson_title, sections, day_plan)
        if assessment:
            cleaned = clean(assessment)
            # Safety net — close assessment-block if unclosed
            if 'assessment-block' in cleaned:
                open_divs  = cleaned.count('<div')
                close_divs = cleaned.count('</div>')
                missing    = open_divs - close_divs
                if missing > 0:
                    cleaned = cleaned.rstrip() + '\n' + ('</div>' * missing)
            parts.append(cleaned)
            print(f"         ✅ Assessment ({len(assessment)} chars)")
        else:
            print(f"         ❌ Assessment failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [English Prose LP 910] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi English Prose lesson.

YOUR ONLY JOB: Extract every section of the prose AND every grammar topic present
in this lesson unit. Do NOT add anything from general knowledge.

PROSE SECTIONS: Extract every named section of the prose in order.
  Example: Introduction, Paragraphs 1–3, Character Description, Climax, Resolution
  If no headings exist, divide the prose logically into 4 readable sections
  suitable for 4 teaching days.

GRAMMAR TOPICS: Extract ONLY grammar topics explicitly present in this unit's
  exercise sections (e.g. Tenses, Reported Speech, Passive Voice, Articles).
  Do NOT invent grammar topics. If fewer than 6 are present, list only those found.
  You need exactly 6 grammar topics — if fewer exist in the text, repeat closely
  related topics (e.g. Simple Past + Past Continuous both count separately).

VOCABULARY: Extract key vocabulary words from the prose — difficult or important
  words students will need help with.

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "prose_sections": [
    {{
      "title": "Section name or Para 1-2",
      "content_summary": "Brief description of what happens in this section",
      "key_vocabulary": ["word1", "word2", "word3"],
      "estimated_teaching_mins": 10
    }}
  ],
  "grammar_topics": [
    {{
      "topic": "Exact grammar topic name from textbook",
      "subtopics": ["subtopic1", "subtopic2"],
      "exercise_type": "fill / transform / identify / write"
    }}
  ],
  "total_vocabulary": ["word1", "word2"],
  "literary_devices": ["device1", "device2"],
  "characters": ["character1", "character2"],
  "theme": "Central theme of the prose in one sentence"
}}

Lesson Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system="""You are a strict text extractor. Return ONLY valid JSON.
Extract ALL prose sections and grammar topics found in the text.
Never add general knowledge. No markdown. No code fences. Raw JSON starting with {""",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"❌ Section Extractor JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Section Extractor error: {e}")
            return None

    # =========================================================================
    # CALL 0b — DAY ALLOCATOR
    # =========================================================================

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        try:
            sections_str = json.dumps(sections, indent=2)
            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi English Prose lesson plan.

Allocate prose sections to EXACTLY 4 content days.
Allocate grammar topics to EXACTLY 6 grammar days.

CONTENT DAY RULES:
- Each content day: 30 minutes of teaching time (45 min session minus 15 min opening/closing)
- Keep reading sections in chronological order
- Each day must cover a meaningful chunk students can absorb and respond to
- Day 4 must include the final section + full prose recap

GRAMMAR DAY RULES:
- Each grammar day covers exactly ONE grammar topic
- Grammar days run AFTER all 4 content days (Days 5–10)
- Topics must follow the order they appear in the textbook exercises
- Each grammar day: focused practice on one rule

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "content_day1": {{
    "sections": ["Section title 1", "Section title 2"],
    "focus": "One sentence — what students read and learn today",
    "key_vocabulary": ["word1", "word2", "word3"],
    "estimated_mins": 30
  }},
  "content_day2": {{
    "sections": ["Section title 3"],
    "focus": "One sentence",
    "key_vocabulary": ["word4", "word5"],
    "estimated_mins": 30
  }},
  "content_day3": {{
    "sections": ["Section title 4", "Section title 5"],
    "focus": "One sentence",
    "key_vocabulary": ["word6", "word7"],
    "estimated_mins": 30
  }},
  "content_day4": {{
    "sections": ["Section title 6", "Final section"],
    "focus": "Final section + full prose recap",
    "key_vocabulary": ["word8", "word9"],
    "estimated_mins": 30
  }},
  "grammar_day1": {{
    "topic": "Exact grammar topic name",
    "subtopics": ["subtopic1"],
    "exercise_type": "fill / transform / identify / write"
  }},
  "grammar_day2": {{ "topic": "...", "subtopics": [], "exercise_type": "..." }},
  "grammar_day3": {{ "topic": "...", "subtopics": [], "exercise_type": "..." }},
  "grammar_day4": {{ "topic": "...", "subtopics": [], "exercise_type": "..." }},
  "grammar_day5": {{ "topic": "...", "subtopics": [], "exercise_type": "..." }},
  "grammar_day6": {{ "topic": "...", "subtopics": [], "exercise_type": "..." }}
}}

Extracted Sections:
---
{sections_str}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system="You are a strict day allocator. Return ONLY valid JSON. No markdown. Raw JSON starting with {",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"❌ Day Allocator JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Day Allocator error: {e}")
            return None

    # =========================================================================
    # CALL 1 — PREAMBLE
    # =========================================================================

    def _call_preamble(self, text, class_num, unit, lesson_title,
                       sections: dict, day_plan: dict) -> Optional[str]:
        try:
            prose_sections = sections.get("prose_sections", [])
            grammar_topics = sections.get("grammar_topics", [])
            characters     = sections.get("characters", [])
            theme          = sections.get("theme", "")
            vocab          = sections.get("total_vocabulary", [])[:12]

            sections_str = "\n".join(
                [f"  ▸ {s['title']} — {s.get('content_summary', '')}" for s in prose_sections]
            )
            grammar_str = "\n".join(
                [f"  ▸ Grammar Day {i+1}: {g['topic']}" for i, g in enumerate(grammar_topics)]
            )
            day_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"content_day{d}", {})
                day_summary += f"  Content Day {d}: {d_data.get('focus', '')}\n"
            for g in range(1, 7):
                g_data = day_plan.get(f"grammar_day{g}", {})
                day_summary += f"  Grammar Day {g} (Day {4+g}): {g_data.get('topic', '')}\n"

            prompt = f"""Generate ONLY the preamble section of this English Prose Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Lesson   : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Prose
Duration : 10 Days × 45 Minutes = 450 Minutes Total
           (4 Content Days + 6 Grammar Days)

PROSE SECTIONS:
{sections_str}

GRAMMAR TOPICS:
{grammar_str}

DAY-WISE SUMMARY:
{day_summary}

Characters: {', '.join(characters)}
Theme: {theme}
Key Vocabulary: {', '.join(vocab)}

Generate EXACTLY these sections in this order:

<h2>Part 1: Lesson Overview</h2>
Table: Class | Subject | Unit/Lesson Title | Lesson Type | Total Days |
       Session Duration | Content Days | Grammar Days

<h2>Part 2: Learning Objectives</h2>
4-5 objectives with action verbs (Read, Identify, Explain, Analyse, Write)
Based ONLY on this prose's actual content — character, theme, events

<h2>Part 3: Language Objectives</h2>
4 objectives for language skills: vocabulary in context, grammar rule application,
reading comprehension, written response
Match the grammar topics found in this unit

<h2>Part 4: Teaching Aids</h2>
Board, chalk, textbook, notebooks, vocabulary cards, grammar exercise sheets
No page numbers. Based on lesson content.

OUTPUT RULES:
- Raw HTML only
{ENGLISH_PREAMBLE_INSTRUCTION}
- Stop after Teaching Aids — do NOT generate any Day content

ABSOLUTE RULES:
✅ Stop COMPLETELY after Teaching Aids closing tag
✅ Do NOT generate any <div class="lp-day-block"> in the preamble
✅ Do NOT generate any Day content in the preamble
❌ NEVER continue beyond Teaching Aids

Lesson Text (reference):
---
{text[:3000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3500,
                system=ENGLISH_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Prose LP 910 preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2–5 — CONTENT DAYS 1–4
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict) -> Optional[str]:
        try:
            day_sections = day_data.get("sections", [])
            day_focus    = day_data.get("focus", "")
            day_vocab    = day_data.get("key_vocabulary", [])
            activity     = ENGLISH_ACTIVITY_MAP_910.get(day_num, "Individual written response")
            theme        = sections.get("theme", "")
            characters   = sections.get("characters", [])

            # Next day preview
            if day_num < 4:
                next_data    = day_plan.get(f"content_day{day_num + 1}", {})
                next_preview = f"Content Day {day_num + 1}: {next_data.get('focus', '')}"
            else:
                g1_data      = day_plan.get("grammar_day1", {})
                next_preview = f"Grammar Day 1: {g1_data.get('topic', 'Grammar')}"

            sections_str = "\n".join([f"  ▸ {s}" for s in day_sections])
            vocab_str    = ", ".join(day_vocab) if day_vocab else "(identify from text)"
            chars_str    = ", ".join(characters) if characters else "(from text)"

            prompt = f"""You are writing Content Day {day_num} of a Samacheer Kalvi English Prose Lesson Plan.

Lesson   : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Prose
Day      : {day_num} of 10 (Content Day {day_num} of 4)
Duration : 45 minutes

PROSE THEME: {theme}
CHARACTERS: {chars_str}

TODAY'S SECTIONS — COVER ALL IN ORDER:
{sections_str}

Day Focus: {day_focus}
Key Vocabulary: {vocab_str}
Today's Activity Style: {activity}

{ENGLISH_TAMIL_INSTRUCTION_910}

{ENGLISH_CCQ_CFU_INSTRUCTION_910}

{ENGLISH_CSS_RULES}

═══════════════════════════════════════════════════════
LANGUAGE RULE — MOST IMPORTANT
═══════════════════════════════════════════════════════
EVERY teacher instruction must have TWO layers:

LAYER 1 — ENGLISH: Minimum 3-4 complete sentences.
Exactly what the teacher says. What to do, how to do it,
how much time, what comes next.

LAYER 2 — TAMIL: Exact mirror of Layer 1.
Same sentences. Same detail. Same length. NOT a summary.
Tamil appears ONLY in Spark/Opening + Key Terms table.

═══════════════════════════════════════════════════════
GENERATE Day {day_num} using EXACTLY this structure:
═══════════════════════════════════════════════════════

✅ Start with <div class="lp-day-block"> as the FIRST tag
✅ Never nest lp-day-block inside any table or th element

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — [Today's prose section names]</h3>
<p class="lp-day-meta">Content Day {day_num} of 4 | 45 minutes | Prose: {lesson_title}</p>

<!-- [0-5 min] SPARK / OPENING QUESTION -->
<div class="lp-section-opening">
  <p class="lp-section-label">⚡ Spark / Opening [0–5 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — relatable question or scenario connecting to today's reading.
   {'Recap yesterday' if day_num > 1 else 'Introduce the lesson'}.
   End with one Big Question about today's section.]"</p>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
    <p>"[3-4 Tamil sentences — exact same question and instruction. Same length.]"</p>
  </div>

  <p class="student-says"><em>3-4 students respond. Teacher acknowledges without correcting.</em></p>

  <div class="lp-teacher-says">
    <strong>Teacher says — Why We Learn This:</strong><br/>
    "[Explain specifically WHY students learn today's topic.
     Give a concrete real-life example from Tamil Nadu daily life.
     Tell them exactly where they will use this knowledge.
     Must be specific to today's sections — not generic.]"
  </div>
</div>

<!-- [5-10 min] VOCABULARY -->
<div class="lp-section-intro">
  <p class="lp-section-label">📚 Vocabulary [5–10 min]</p>

  <div class="vocab-block">
    <strong>Key Vocabulary — Write on Board:</strong>
    <table>
      <thead><tr><th>Word</th><th>English Meaning</th><th>Tamil பொருள்</th></tr></thead>
      <tbody>
        [5-6 key words from today's section — with meaning and Tamil]
      </tbody>
    </table>
  </div>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — introduce each word. Say the word aloud.
   Give meaning. Give an example sentence from the prose.
   Ask students to repeat the word.]"</p>
</div>

<!-- [10-25 min] MAIN TEACHING — READING + EXPLANATION -->
<div class="lp-section-main">
  <p class="lp-section-label">📖 Main Teaching — Reading + Explanation [10–25 min]</p>

  [FOR EACH section in today's list — cover in order:]

  <h4>[Exact section/paragraph name]</h4>

  <p class="lp-teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
  "[4-5 sentences — teacher reads the passage aloud.
   Then explains in simple words — what happens, what it means.
   Name characters. Describe actions. Connect to theme.
   Give one real-life connection or analogy.]"</p>

  <div class="cfu-block">
    <strong>🔎 CFU:</strong>
    <p class="lp-teacher-says">"[Simple recall question about what was just read — under 8 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[One sentence answer from text]"</p>
    <p><em>⏱ Wait 10 seconds. Call on 2 students.</em></p>
  </div>

  <div class="ccq-block">
    <strong>⚡ CCQ:</strong>
    <p class="lp-teacher-says">"[Why/What does this mean question — under 10 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[2-3 sentence analytical answer]"</p>
    <p><em>⏱ Wait 20 seconds. Think-pair-share.</em></p>
  </div>

  [REPEAT for each section in today's list]

</div>

<!-- [25-35 min] STUDENT PRACTICE / ACTIVITY -->
<div class="lp-section-student-task">
  <p class="lp-section-label">✍️ Student Practice [25–35 min]</p>

  <div class="activity-block">
    <strong>Activity: {activity}</strong>

    <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain activity step by step.
     What to do. How many sentences/questions.
     How much time. Alone or in pairs. What to do when done.]"</p>

    <p><strong>Step 1:</strong> [Exact instruction with time]</p>
    <p><strong>Step 2:</strong> [Exact instruction with time]</p>
    <p><strong>Step 3:</strong> [Sharing / checking instruction]</p>

    <p class="student-says"><strong>Expected output:</strong>
    "[Example answer based on today's section]"</p>
  </div>
</div>

<!-- [35-40 min] CLOSURE + EXIT QUESTION -->
<div class="lp-section-closing">
  <p class="lp-section-label">🔔 Closure [35–40 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — summarize today's reading.
   Name specific things students learned.
   Connect to the bigger theme. Praise the class.]"</p>

  <div class="board-work">
    <strong>Key Points on Board:</strong><br/>
    1. [Key point from today's reading]<br/>
    2. [Key point from today's reading]<br/>
    3. [Key vocabulary word + meaning]
  </div>

  <p class="lp-teacher-says"><strong>Exit Question (English):</strong><br/>
  "[2-3 sentences — one question about today's section.
   Students write answer in notebook. Give 2 minutes.]"</p>
  <p class="student-says"><strong>Expected answer:</strong> "[Complete sentence from text]"</p>

  <p><em>Preview: Tomorrow — {next_preview}</em></p>
</div>

<!-- [40-45 min] HOMEWORK + DIFFERENTIATION -->
<div class="homework-block">
  <p class="lp-section-label">📝 Homework + Differentiation [40–45 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — explain homework.
   What to write. How many sentences. Which vocabulary words to use.
   When to submit. Do not copy — use own words.]"</p>

  <div class="board-work">
    <strong>Homework (Write on Board):</strong><br/>
    Task: [Specific written task from today's section]<br/>
    Length: [3-5 sentences]<br/>
    Submit: Tomorrow
  </div>

  <div class="diff-block">
    <strong>Differentiated Tasks:</strong>
    <table>
      <thead>
        <tr>
          <th>Slow Learners</th>
          <th>Average Learners</th>
          <th>Advanced Learners</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Fill in the blanks with word bank<br/>
              Word Bank: [4-5 words from today]</td>
          <td>Answer 2 comprehension questions<br/>
              in 2-3 sentences each</td>
          <td>Write a paragraph response<br/>
              5+ sentences, own words</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS
═══════════════════════════════════════════════════════
✅ ALL sections covered: {', '.join(day_sections)}
✅ Vocabulary table has 5-6 words with Tamil meanings
✅ Minimum 3 CFU blocks + 3 CCQ blocks
✅ Activity is specific and step-by-step
✅ Homework task is clear — what to write, how many sentences
✅ Differentiation has real example tasks
✅ Tamil ONLY in Spark + Key Terms table
✅ NO inline styles on any div or p tag
✅ Raw HTML only — start with <div class="lp-day-block">
❌ NEVER add <style> blocks anywhere in your output
❌ NEVER add inline color styles on any element — no style="color:..." anywhere
❌ NEVER add inline style attributes of any kind inside board-work divs
✅ Do NOT generate Day {day_num + 1}
✅ All content from lesson text only — no invented facts

Lesson Text (use ONLY this):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=18000,
                system=ENGLISH_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Prose LP 910 Content Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALLS 6–11 — GRAMMAR DAYS 1–6
    # =========================================================================

    def _call_grammar_day(self, text, class_num, unit, lesson_title,
                          day_num: int, grammar_day_num: int,
                          g_data: dict, all_grammar_topics: list) -> Optional[str]:
        try:
            topic        = g_data.get("topic", "Grammar")
            subtopics    = g_data.get("subtopics", [])
            ex_type      = g_data.get("exercise_type", "write")
            spark_style  = ENGLISH_GRAMMAR_SPARK_STYLES.get(grammar_day_num, "Connect to lesson")
            topics_list  = "\n".join(f"  - {t}" for t in all_grammar_topics if t)

            next_preview = (
                f"Grammar Day {grammar_day_num + 1}: {all_grammar_topics[grammar_day_num]}"
                if grammar_day_num < 6 and grammar_day_num < len(all_grammar_topics)
                else "Assessment and Review"
            )

            prompt = f"""You are writing Grammar Day {grammar_day_num} (overall Day {day_num}) of a
Samacheer Kalvi English Prose Lesson Plan.

Lesson   : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Grammar
Day      : {day_num} of 10 (Grammar Day {grammar_day_num} of 6)
Duration : 45 minutes

MANDATORY GRAMMAR TOPIC FOR TODAY — NO EXCEPTIONS:
Topic: {topic}
Subtopics: {', '.join(subtopics) if subtopics else 'As in textbook'}
Exercise Type: {ex_type}

ALL GRAMMAR TOPICS IN THIS UNIT (for reference):
{topics_list}

Do NOT teach any grammar topic not in the above list.
Do NOT substitute with vocabulary, comprehension, or creative writing tasks.

SPARK STYLE FOR THIS DAY: {spark_style}

{ENGLISH_CSS_RULES}

═══════════════════════════════════════════════════════
LANGUAGE RULE
═══════════════════════════════════════════════════════
EVERY teacher instruction must have TWO layers:
  LAYER 1 — ENGLISH: 3-4 complete sentences. Word for word script.
  LAYER 2 — TAMIL: Exact mirror. Same sentences. Same length.
Tamil appears ONLY in Spark/Opening and Key Terms table.

═══════════════════════════════════════════════════════
GENERATE Grammar Day {grammar_day_num} using EXACTLY this structure:
═══════════════════════════════════════════════════════

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — Grammar: {topic}</h3>
<p class="lp-day-meta">Grammar Day {grammar_day_num} of 6 | 45 minutes | {lesson_title}</p>

<!-- [0-5 min] GRAMMAR INTRODUCTION / SPARK -->
<div class="lp-section-opening">
  <p class="lp-section-label">⚡ Grammar Spark [0–5 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — {spark_style}.
   Connect the grammar topic to a specific sentence from the lesson.
   Write the example sentence on board. Ask students what they notice.]"</p>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
    <p>"[3-4 Tamil sentences — exact same introduction. Same sentence on board.
    Same question to students. Same length as English.]"</p>
    <p><em>Grammar rule in Tamil (ஆசிரியர் தெரிந்துகொள்ள):</em><br/>
    "[Full grammar rule explained in Tamil — 3-4 sentences for teacher's own understanding.]"</p>
  </div>

  <div class="board-work">
    <strong>Write on Board:</strong><br/>
    Example sentence: "[sentence from lesson using this grammar]"<br/>
    Tamil meaning: "[Tamil translation of the sentence]"<br/>
    Grammar focus: "[highlight the grammar point]"
  </div>
</div>

<!-- [5-15 min] GRAMMAR EXPLANATION + EXAMPLES -->
<div class="lp-section-intro">
  <p class="lp-section-label">📐 Grammar Explanation [5–15 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[4-5 sentences — explain the grammar rule step by step.
   Give 3 examples from the lesson text.
   Write each example on board.
   Ask students to identify the pattern. Check understanding.]"</p>

  <div class="board-work">
    <strong>Board Work — Rule + 3 Examples from lesson:</strong><br/>
    Rule: [{topic} rule in English]<br/>
    தமிழில்: [same rule in Tamil]<br/>
    1. [example sentence from lesson] → [Tamil meaning]<br/>
    2. [example sentence from lesson] → [Tamil meaning]<br/>
    3. [example sentence from lesson] → [Tamil meaning]
  </div>

  <div class="cfu-block">
    <strong>🔎 CFU:</strong>
    <p class="lp-teacher-says">"[Question identifying the grammar pattern — under 8 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[Student identifies the pattern]"</p>
    <p><em>⏱ Wait 10 seconds. Call on 2 students.</em></p>
  </div>

  <div class="ccq-block">
    <strong>⚡ CCQ:</strong>
    <p class="lp-teacher-says">"[Why do we use {topic} here — under 10 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[Explanation of the grammar rule]"</p>
    <p><em>⏱ Wait 20 seconds. Think-pair-share.</em></p>
  </div>
</div>

<!-- [15-30 min] STUDENT PRACTICE -->
<div class="lp-section-student-task">
  <p class="lp-section-label">✍️ Student Practice [15–30 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[4-5 sentences — tell students to open notebooks.
   Explain exactly what to write. State how many questions ({ex_type} exercises).
   Give time limit. Say you will walk around to check.]"</p>

  <div class="activity-block">
    <strong>Practice Questions (from textbook exercises on {topic}):</strong>
    <p><strong>Q1:</strong> [question using {topic}] — <strong>Answer:</strong> [complete sentence]</p>
    <p><strong>Q2:</strong> [question using {topic}] — <strong>Answer:</strong> [complete sentence]</p>
    <p><strong>Q3:</strong> [question using {topic}] — <strong>Answer:</strong> [complete sentence]</p>
    <p><strong>Q4:</strong> [question using {topic}] — <strong>Answer:</strong> [complete sentence]</p>
    <p><strong>Q5:</strong> [question using {topic}] — <strong>Answer:</strong> [complete sentence]</p>
  </div>
</div>

<!-- [30-40 min] CLOSURE + EXIT QUESTION -->
<div class="lp-section-closing">
  <p class="lp-section-label">🔔 Closure [30–40 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — summarize {topic} rule in simple words.
   Give one final clear example. Ask exit question.
   Tell students to write answer before leaving.]"</p>

  <div class="board-work">
    <strong>Board — Final Summary:</strong><br/>
    Rule: [{topic} in one clear sentence]<br/>
    தமிழில்: [Tamil rule]<br/>
    Example: [one final clear example sentence]
  </div>

  <p class="lp-teacher-says"><strong>Exit Question (English):</strong><br/>
  "[Grammar question every student answers in notebook.]"</p>
  <p class="student-says"><strong>Expected answer:</strong> "[Complete sentence using {topic}]"</p>

  <p><em>Preview: Tomorrow — {next_preview}</em></p>
</div>

<!-- [40-45 min] HOMEWORK + DIFFERENTIATION -->
<div class="homework-block">
  <p class="lp-section-label">📝 Homework + Differentiation [40–45 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — explain homework. How many grammar questions.
   Use the rule from today. Point to board. Bring tomorrow.]"</p>

  <div class="board-work">
    <strong>Homework (Write on Board):</strong><br/>
    Task: Write 5 sentences using {topic}<br/>
    Model: "[example sentence]"<br/>
    Submit: Tomorrow
  </div>

  <div class="diff-block">
    <strong>Differentiated Tasks:</strong>
    <table>
      <thead>
        <tr>
          <th>Slow Learners</th>
          <th>Average Learners</th>
          <th>Advanced Learners</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Fill in blanks using grammar rule<br/>
              "[sentence] _______ (option1/option2)"</td>
          <td>Write 3 sentences using {topic}<br/>
              using the pattern from board</td>
          <td>Write a paragraph using {topic}<br/>
              5+ times correctly. No help.</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS
═══════════════════════════════════════════════════════
✅ Topic lock: {topic} — do NOT teach any other grammar topic
✅ All 5 practice questions given with model answers
✅ Grammar rule explained in English AND Tamil (for teacher)
✅ Board work has English rule + Tamil rule + 3 examples
✅ Homework is specific with model example
✅ Differentiation has real example sentences for each level
✅ NO inline styles on any div or p tag
✅ Raw HTML only — start with <div class="lp-day-block">
❌ NEVER add <style> blocks anywhere in your output
❌ NEVER add inline color styles on any element — no style="color:..." anywhere
❌ NEVER add inline style attributes of any kind inside board-work divs
✅ Do NOT generate Day {day_num + 1}
✅ Every example sentence must be grammatically 100% correct
✅ Check subject-verb agreement in EVERY sentence before finishing
✅ NEVER use a grammatically incorrect sentence as an example
✅ CFU questions on grammar days = identification only (one word answer)
✅ NEVER ask transformation questions as CFU — those are practice questions
✅ All grammar examples taken from lesson text only — never invented

Lesson Text (use ONLY this for grammar examples):
---
{text[:5000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=16000,
                system=ENGLISH_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Prose LP 910 Grammar Day {grammar_day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 12 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit, lesson_title,
                         sections: dict, day_plan: dict) -> Optional[str]:
        try:
            characters = ", ".join(sections.get("characters", []))
            theme      = sections.get("theme", "")
            vocab      = ", ".join(sections.get("total_vocabulary", [])[:12])

            grammar_topics_str = "\n".join(
                [f"  Day {4+g}: {day_plan.get(f'grammar_day{g}', {}).get('topic', '')}"
                 for g in range(1, 7)]
            )

            content_summary = ""
            for d in range(1, 5):
                d_data = day_plan.get(f"content_day{d}", {})
                content_summary += f"  Content Day {d}: {d_data.get('focus', '')}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this English Prose lesson plan.
Do NOT repeat day content. Do NOT generate day blocks.

Lesson   : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Characters: {characters}
Theme: {theme}
Key Vocabulary: {vocab}

Content Days:
{content_summary}

Grammar Topics:
{grammar_topics_str}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Comprehension Check Questions</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Focus</th>
        <th>Check Question</th>
        <th>Expected Answer</th>
      </tr>
    </thead>
    <tbody>
      [10 rows — one per day (4 content + 6 grammar).
       Content days: comprehension question from the prose section.
       Grammar days: grammar rule application question.
       All answers based on lesson text only.]
    </tbody>
  </table>

  <h3>Vocabulary Assessment — 15 Words</h3>
  <table>
    <thead>
      <tr><th>Word</th><th>Meaning</th><th>Use in a sentence (from lesson)</th></tr>
    </thead>
    <tbody>
      [15 vocabulary words from the lesson with meanings and example sentences]
    </tbody>
  </table>

  <h3>Written Assessment Tasks — 3 Levels</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Foundation Level<br/>(Slow Learners)</th>
        <th>Standard Level<br/>(Average Learners)</th>
        <th>Advanced Level<br/>(Toppers)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p><strong>Task 1:</strong> Fill blanks with word bank (8 words from lesson)</p>
          <p><strong>Task 2:</strong> Answer 2 one-sentence comprehension questions</p>
        </td>
        <td>
          <p><strong>Task 1:</strong> Answer 3 questions in 3-4 sentences each</p>
          <p><strong>Task 2:</strong> Write 3 sentences using grammar topics from this unit</p>
        </td>
        <td>
          <p><strong>Task 1:</strong> Short essay — describe the theme or a key character
          in 8-10 sentences. Own words only.</p>
          <p><strong>Task 2:</strong> Creative task — write an alternate ending OR
          a diary entry from a character's perspective</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Chapter Completion Checklist</h3>
  <ul>
    <li>☐ All 10 days of notes completed in notebook</li>
    <li>☐ All homework submitted (Days 1–10)</li>
    <li>☐ Vocabulary table filled for all content days</li>
    <li>☐ Grammar exercises completed and checked (Grammar Days 1–6)</li>
    <li>☐ Exit questions answered for all days</li>
    <li>☐ Written assessment task submitted</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Day table: exactly 10 rows
- Vocabulary table: 15 words from lesson text only
- No page numbers
- All content based on actual lesson text

Lesson Text:
---
{text[:3000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=6000,
                system=ENGLISH_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Prose LP 910 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_prose_lp_910_builder = EnglishProseLPBuilder910()