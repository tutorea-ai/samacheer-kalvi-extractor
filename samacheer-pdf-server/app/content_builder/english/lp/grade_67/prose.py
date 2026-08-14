"""
english/lp/grade_67/prose.py
------------------------------
LP Builder for Samacheer Kalvi English — Prose
Classes 6 & 7

Lesson structure:
  6 days total — 3 content days + 3 grammar days
  Session duration: 35 minutes

API calls: 9 total
  Call 0a → Section Extractor     (JSON — prose sections + grammar topics)
  Call 0b → Day Allocator         (JSON — sections to 3 content days, topics to 3 grammar days)
  Call 1  → Preamble
  Calls 2–4  → Content Days 1–3
  Calls 5–7  → Grammar Days 1–3
  Call 8  → Assessment Summary

Grade_67 vs Grade_910 delta applied:
  - 35-minute sessions (not 45)
  - Time blocks: [0-4], [4-8], [8-20], [20-28], [28-32], [32-35]
  - Tamil in 3 places: Spark + Key Terms + CFU/CCQ touch
  - Vocabulary: 4-5 words, concrete/picturable
  - CCQ: simplified, scaffolded inference
  - Activities: concrete/kinesthetic
  - Differentiation ceiling: 3-4 sentence paragraph
  - Grammar practice: 3-4 questions, single-concept only
  - Grammar data: flat (topic only, no subtopics)

v1.0 — June 2026
"""

import json
import re
import anthropic
from typing import Optional

from .....config import settings
from ...base import (
    ENGLISH_LP_SYSTEM_PROMPT_67,
    ENGLISH_PREAMBLE_INSTRUCTION,
    ENGLISH_TAMIL_INSTRUCTION_67,
    ENGLISH_CCQ_CFU_INSTRUCTION_67,
    ENGLISH_CSS_RULES,
    clean,
)


# ============================================================================
# PROSE LP BUILDER — GRADE 67
# ============================================================================

class EnglishProseLPBuilder67:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English Prose LP Builder (67) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [English Prose LP 67] Generating: {lesson_title}")
        print(f"      [English Prose LP 67] 9 API calls: 0a+0b+Preamble+Days1-3+Grammar1-3+Assessment")

        parts = []

        # Call 0a
        print(f"      [English Prose LP 67] Call 0a/9: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('prose_sections', []))} prose sections, "
              f"{len(sections.get('grammar_topics', []))} grammar topics")

        # Call 0b
        print(f"      [English Prose LP 67] Call 0b/9: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        print(f"         ✅ Day plan ready")
        for d in range(1, 4):
            focus = day_plan.get(f"content_day{d}", {}).get("focus", "")
            print(f"            Content Day {d}: {focus}")
        for g in range(1, 4):
            topic = day_plan.get(f"grammar_day{g}", {}).get("topic", "")
            print(f"            Grammar Day {g}: {topic}")

        # Call 1
        print(f"      [English Prose LP 67] Call 1/9: Preamble...")
        preamble = self._call_preamble(text, class_num, unit, lesson_title, sections, day_plan)
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting")
            return None

        # Calls 2–4: Content Days 1–3
        for day_num in range(1, 4):
            call_num = day_num + 1
            print(f"      [English Prose LP 67] Call {call_num}/9: Content Day {day_num}...")
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

        # Calls 5–7: Grammar Days 1–3
        all_grammar_topics = [
            day_plan.get(f"grammar_day{g}", {}).get("topic", "")
            for g in range(1, 4)
        ]
        for g_num in range(1, 4):
            day_num  = 3 + g_num       # overall day number (4–6)
            call_num = 4 + g_num       # call number (5–7)
            print(f"      [English Prose LP 67] Call {call_num}/9: Grammar Day {g_num} (Day {day_num})...")
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

        # Call 8: Assessment
        print(f"      [English Prose LP 67] Call 8/9: Assessment...")
        assessment = self._call_assessment(text, class_num, unit, lesson_title, sections, day_plan)
        if assessment:
            cleaned = clean(assessment)
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
        print(f"      [English Prose LP 67] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi English Prose lesson
for Classes 6 and 7.

Extract every section of the prose AND every grammar topic present in this unit.
Do NOT add anything from general knowledge.

PROSE SECTIONS: Extract every named section of the prose in order.
  If no headings exist, divide the prose logically into 3 readable sections
  suitable for 3 teaching days of 35 minutes each.
  Keep sections short enough for young learners — Classes 6 & 7.

GRAMMAR TOPICS: Extract ONLY grammar topics explicitly present in this unit's
  exercise sections. You need exactly 3 grammar topics.
  Grade 67 grammar is simple — single-concept only:
  (e.g. Nouns, Pronouns, Adjectives, Verbs, Tenses, Prepositions, Articles)
  If fewer than 3 are present, repeat related topics.
  DO NOT include complex topics like Reported Speech or Passive Voice for grade_67.

VOCABULARY: Extract key vocabulary — simple, picturable words students will need.

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "prose_sections": [
    {{
      "title": "Section name or Para 1",
      "content_summary": "Brief description — simple words",
      "key_vocabulary": ["word1", "word2", "word3"],
      "estimated_teaching_mins": 8
    }}
  ],
  "grammar_topics": [
    {{
      "topic": "Simple grammar topic name (single concept only)",
      "exercise_type": "fill / identify / write"
    }}
  ],
  "total_vocabulary": ["word1", "word2"],
  "characters": ["character1", "character2"],
  "theme": "Central theme in simple words — one sentence",
  "moral": "Simple moral or lesson from the story"
}}

Lesson Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system="""You are a strict text extractor for Class 6-7 English.
Return ONLY valid JSON. No markdown. Raw JSON starting with {
Keep everything simple — suitable for young learners.""",
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
            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi English Prose lesson
for Classes 6 and 7.

Allocate prose sections to EXACTLY 3 content days.
Allocate grammar topics to EXACTLY 3 grammar days.

CONTENT DAY RULES:
- Each content day: 20 minutes of teaching time (35 min session minus 15 min opening/closing)
- Keep reading sections in order — Classes 6 & 7 need smaller chunks
- Each day must cover a manageable amount for young learners
- Day 3 must include the final section + simple prose recap

GRAMMAR DAY RULES:
- Each grammar day covers exactly ONE simple grammar topic
- Grammar days run AFTER all 3 content days (Days 4–6)
- Single-concept only — no complex grammar for grade_67
- Each grammar day: focused practice on one simple rule

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "content_day1": {{
    "sections": ["Section title 1"],
    "focus": "One sentence — what students read today (simple words)",
    "key_vocabulary": ["word1", "word2", "word3", "word4"],
    "estimated_mins": 20
  }},
  "content_day2": {{
    "sections": ["Section title 2"],
    "focus": "One sentence",
    "key_vocabulary": ["word5", "word6", "word7"],
    "estimated_mins": 20
  }},
  "content_day3": {{
    "sections": ["Section title 3"],
    "focus": "Final section + simple recap",
    "key_vocabulary": ["word8", "word9"],
    "estimated_mins": 20
  }},
  "grammar_day1": {{
    "topic": "Simple grammar topic (single concept)",
    "exercise_type": "fill / identify / write"
  }},
  "grammar_day2": {{
    "topic": "Simple grammar topic",
    "exercise_type": "fill / identify / write"
  }},
  "grammar_day3": {{
    "topic": "Simple grammar topic",
    "exercise_type": "fill / identify / write"
  }}
}}

Extracted Sections:
---
{sections_str}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
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
            moral          = sections.get("moral", "")
            vocab          = sections.get("total_vocabulary", [])[:10]

            sections_str = "\n".join(
                [f"  ▸ {s['title']} — {s.get('content_summary', '')}" for s in prose_sections]
            )
            grammar_str = "\n".join(
                [f"  ▸ Grammar Day {i+1}: {g['topic']}" for i, g in enumerate(grammar_topics)]
            )
            day_summary = ""
            for d in range(1, 4):
                d_data = day_plan.get(f"content_day{d}", {})
                day_summary += f"  Content Day {d}: {d_data.get('focus', '')}\n"
            for g in range(1, 4):
                g_data = day_plan.get(f"grammar_day{g}", {})
                day_summary += f"  Grammar Day {g} (Day {3+g}): {g_data.get('topic', '')}\n"

            prompt = f"""Generate ONLY the preamble section of this English Prose Lesson Plan
for Class {class_num} (Grade 6-7).

Do NOT generate any Day blocks. Stop after Teaching Aids.

Lesson   : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Prose
Duration : 6 Days × 35 Minutes = 210 Minutes Total
           (3 Content Days + 3 Grammar Days)

PROSE SECTIONS:
{sections_str}

GRAMMAR TOPICS:
{grammar_str}

DAY-WISE SUMMARY:
{day_summary}

Characters : {', '.join(characters)}
Theme      : {theme}
Moral      : {moral}
Key Vocabulary: {', '.join(vocab)}

Generate EXACTLY these sections:

<h2>Part 1: Lesson Overview</h2>
Table: Class | Subject | Unit/Lesson Title | Lesson Type | Total Days |
       Session Duration | Content Days | Grammar Days

<h2>Part 2: Learning Objectives</h2>
Generate a simple <ul> list — 4 bullet points only.
Each bullet: one sentence starting with action verb (Read, Say, Find, Write).
NO tables. NO Tamil. Plain English bullet points only.
Example: <li>Read the lesson aloud with correct pronunciation.</li>

<h2>Part 3: Language Objectives</h2>
Generate a simple <ul> list — 3 bullet points only.
Each bullet: one sentence in English only.
NO tables. NO Tamil column. Plain English only.

<h2>Part 4: Teaching Aids</h2>
Board, chalk, textbook, notebooks, vocabulary cards, picture cards if relevant.

OUTPUT RULES:
- Raw HTML only
{ENGLISH_PREAMBLE_INSTRUCTION}
- Stop after Teaching Aids — do NOT generate any Day content
- Keep language simple — suitable for Class 6-7

ABSOLUTE RULES:
✅ Stop COMPLETELY after Teaching Aids closing tag
✅ Do NOT generate any <div class="lp-day-block"> in the preamble
✅ Do NOT generate any Day content in the preamble
❌ NEVER continue beyond Teaching Aids

Lesson Text:
---
{text[:2000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system=ENGLISH_LP_SYSTEM_PROMPT_67,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Prose LP 67 preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2–4 — CONTENT DAYS 1–3
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict) -> Optional[str]:
        try:
            day_sections = day_data.get("sections", [])
            day_focus    = day_data.get("focus", "")
            day_vocab    = day_data.get("key_vocabulary", [])
            theme        = sections.get("theme", "")
            moral        = sections.get("moral", "")
            characters   = sections.get("characters", [])

            # Next day preview
            if day_num < 3:
                next_data    = day_plan.get(f"content_day{day_num + 1}", {})
                next_preview = f"Content Day {day_num + 1}: {next_data.get('focus', '')}"
            else:
                g1_data      = day_plan.get("grammar_day1", {})
                next_preview = f"Grammar Day 1: {g1_data.get('topic', 'Grammar')}"

            sections_str = "\n".join([f"  ▸ {s}" for s in day_sections])
            vocab_str    = ", ".join(day_vocab) if day_vocab else "(identify from text)"
            chars_str    = ", ".join(characters) if characters else "(from text)"

            # Concrete kinesthetic activity per day
            activities = {
                1: "Picture-word matching — students draw or point to vocabulary words",
                2: "Read aloud in pairs — one reads, one listens and retells",
                3: "Story map in notebook — draw Title + Characters + Events + Moral",
            }
            activity = activities.get(day_num, "Individual written response")

            prompt = f"""You are writing Content Day {day_num} of a Samacheer Kalvi English Prose
Lesson Plan for Class {class_num} (Grade 6-7).

Lesson   : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Prose
Day      : {day_num} of 6 (Content Day {day_num} of 3)
Duration : 35 minutes

IMPORTANT — THIS IS GRADE 6-7:
- Students are young learners (11-12 years old)
- Keep all explanations very simple — short sentences
- Every new word needs a simple meaning + Tamil meaning
- Activities must be concrete and hands-on — not analytical
- Writing tasks: maximum 3-4 sentences
- Teacher script must be very clear and easy to follow

PROSE THEME: {theme}
MORAL: {moral}
CHARACTERS: {chars_str}

TODAY'S SECTIONS:
{sections_str}

Day Focus: {day_focus}
Key Vocabulary (4-5 words): {vocab_str}
Today's Activity: {activity}

{ENGLISH_TAMIL_INSTRUCTION_67}
{ENGLISH_CCQ_CFU_INSTRUCTION_67}
{ENGLISH_CSS_RULES}

═══════════════════════════════════════════════════════
LANGUAGE RULE
═══════════════════════════════════════════════════════
EVERY teacher instruction must have TWO layers:
LAYER 1 — ENGLISH: 3-4 simple sentences. Short words. Easy to follow.
LAYER 2 — TAMIL: Exact mirror. Same length. Same detail.
Tamil appears in 3 places: Spark + Key Terms table + one CFU/CCQ touch.

═══════════════════════════════════════════════════════
GENERATE Day {day_num} using EXACTLY this structure:
═══════════════════════════════════════════════════════

✅ Start with <div class="lp-day-block"> as the FIRST tag
✅ Never nest lp-day-block inside any table or th element

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — {lesson_title}: {day_focus}</h3>
<p class="lp-day-meta">Content Day {day_num} of 3 | 35 minutes | Class {class_num}</p>

<!-- [0-4 min] SPARK / OPENING -->
<div class="lp-section-opening">
  <p class="lp-section-label">⚡ Spark / Opening [0–4 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — {'Recap yesterday in one sentence.' if day_num > 1 else 'Introduce the lesson with a simple question.'}
   Ask one easy question connected to today's reading.
   Something from students' daily life.]"</p>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
    <p>"[3 Tamil sentences — exact same content. Simple Tamil. Same length.]"</p>
  </div>

  <p class="student-says"><em>2-3 students answer. Teacher says "Good!" and moves on.</em></p>
</div>

<!-- [4-8 min] VOCABULARY -->
<div class="lp-section-intro">
  <p class="lp-section-label">📚 New Words [4–8 min]</p>

  <div class="vocab-block">
    <strong>New Words — Write on Board:</strong>
    <table>
      <thead><tr><th>Word</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
      <tbody>
        [4-5 simple, picturable words from today's section]
        [Simple one-word or one-phrase meaning]
        [Tamil meaning]
      </tbody>
    </table>
  </div>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 sentences — say each word aloud. Students repeat.
   Show meaning with a simple action or picture if possible.
   Ask students to use the word in one sentence.]"</p>
</div>

<!-- [8-20 min] READING + EXPLANATION -->
<div class="lp-section-main">
  <p class="lp-section-label">📖 Reading + Explanation [8–20 min]</p>

  [FOR EACH section in today's list:]

  <h4>[Section name]</h4>

  <p class="lp-teacher-says"><strong>Teacher reads aloud (English):</strong><br/>
  "[3-4 simple sentences — teacher reads the passage slowly and clearly.
   Then explains in very simple words — what happens, who does what.
   Give one simple real-life connection students can relate to.]"</p>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
    <p>"[3-4 Tamil sentences — exact same explanation in Tamil.
    Simple Tamil words. Same length as English.]"</p>
  </div>

  <div class="cfu-block">
    <strong>🔎 CFU:</strong>
    <p class="lp-teacher-says">"[Simple question — under 6 words. What/Who/Where]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[One word or short phrase]"</p>
    <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    <p><em>⏱ Wait 10 seconds. Call on 2 students.</em></p>
  </div>

  <div class="ccq-block">
    <strong>⚡ CCQ:</strong>
    <p class="lp-teacher-says">"[Simple Why question — under 8 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[1-2 sentence simple answer]"</p>
    <p><em>⏱ Wait 15 seconds. Students may answer in Tamil if needed.</em></p>
  </div>

  [REPEAT for each section]

</div>

<!-- [20-28 min] STUDENT ACTIVITY -->
<div class="lp-section-student-task">
  <p class="lp-section-label">✍️ Activity [20–28 min]</p>

  <div class="activity-block">
    <strong>Activity: {activity}</strong>

    <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 simple sentences — explain activity step by step.
     What to do. How long. What to show teacher when done.]"</p>

    <p><strong>Step 1:</strong> [Simple clear instruction]</p>
    <p><strong>Step 2:</strong> [Simple clear instruction]</p>
    <p><strong>Step 3:</strong> [Share with class / show teacher]</p>

    <p class="student-says"><strong>Expected output:</strong>
    "[Simple example — 1-2 sentences or a drawing]"</p>
  </div>
</div>

<!-- [28-32 min] CLOSURE -->
<div class="lp-section-closing">
  <p class="lp-section-label">🔔 Closure [28–32 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — what did we read today.
   Ask one easy question. Praise the class warmly.]"</p>

  <div class="board-work">
    <strong>Write on Board:</strong><br/>
    1. [One key word from today]<br/>
    2. [One simple sentence from today's reading]<br/>
    3. [Moral or message in simple words — Day 3 only]
  </div>

  <p><em>Preview: Tomorrow — {next_preview}</em></p>
</div>

<!-- [32-35 min] HOMEWORK -->
<div class="homework-block">
  <p class="lp-section-label">📝 Homework [32–35 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 sentences — explain homework clearly.
   Write 3-4 sentences only. Use your own words.
   Bring tomorrow.]"</p>

  <div class="board-work">
    <strong>Homework (Write on Board):</strong><br/>
    Task: [Simple written task — 3-4 sentences max]<br/>
    Example: "[One model sentence from today's lesson]"<br/>
    Submit: Tomorrow
  </div>

  <div class="diff-block">
    <strong>Different Tasks for Different Learners:</strong>
    <table>
      <thead>
        <tr>
          <th>Slow Learners</th>
          <th>Average Learners</th>
          <th>Fast Learners</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Copy 2 sentences from board<br/>
              Draw one picture from the story</td>
          <td>Answer 2 simple questions<br/>
              in 1-2 sentences each</td>
          <td>Write 3-4 sentences about<br/>
              [character/event] in own words</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS
═══════════════════════════════════════════════════════
✅ All sections covered: {', '.join(day_sections)}
✅ Vocabulary table has 4-5 simple picturable words with Tamil
✅ Minimum 3 CFU + 3 CCQ blocks — simple questions only
✅ Activity is concrete and hands-on — not analytical
✅ Homework max 3-4 sentences — never an essay
✅ Tamil in 3 places: Spark + Key Terms + CFU touch
✅ NO inline styles on any div or p tag
✅ Raw HTML only — start with <div class="lp-day-block">
❌ NEVER add <style> blocks anywhere in your output
❌ NEVER add inline color styles on any element — no style="color:..." anywhere
❌ NEVER add inline style attributes of any kind inside board-work divs
✅ Do NOT generate Day {day_num + 1}
✅ All content simple enough for Class 6-7 students

Lesson Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=16000,
                system=ENGLISH_LP_SYSTEM_PROMPT_67,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Prose LP 67 Content Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALLS 5–7 — GRAMMAR DAYS 1–3
    # =========================================================================

    def _call_grammar_day(self, text, class_num, unit, lesson_title,
                          day_num: int, grammar_day_num: int,
                          g_data: dict, all_grammar_topics: list) -> Optional[str]:
        try:
            topic    = g_data.get("topic", "Grammar")
            ex_type  = g_data.get("exercise_type", "fill")
            topics_list = "\n".join(f"  - {t}" for t in all_grammar_topics if t)

            next_preview = (
                f"Grammar Day {grammar_day_num + 1}: {all_grammar_topics[grammar_day_num]}"
                if grammar_day_num < 3 and grammar_day_num < len(all_grammar_topics)
                else "Assessment and Review"
            )

            # Simple spark styles for grade_67
            spark_styles = {
                1: "Find this word in today's lesson — what kind of word is it?",
                2: "Write one sentence on the board — students identify the grammar point",
                3: "Two sentences on board — what is different between them?",
            }
            spark = spark_styles.get(grammar_day_num, "Connect grammar to lesson sentence")

            prompt = f"""You are writing Grammar Day {grammar_day_num} (overall Day {day_num})
of a Samacheer Kalvi English Prose Lesson Plan for Class {class_num} (Grade 6-7).

Lesson   : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Day      : {day_num} of 6 (Grammar Day {grammar_day_num} of 3)
Duration : 35 minutes

MANDATORY GRAMMAR TOPIC: {topic}
Exercise Type: {ex_type}

IMPORTANT — GRADE 6-7 GRAMMAR RULES:
- Single concept only — teach ONE rule clearly
- Use very simple examples from the lesson text
- Maximum 3-4 practice questions — not 5
- Questions must be easy — fill blanks or identify only
- Never teach complex grammar (passive voice, reported speech etc.)
- Tamil explanation of rule is mandatory — teacher must fully understand

ALL GRAMMAR TOPICS IN THIS UNIT:
{topics_list}

SPARK FOR TODAY: {spark}

{ENGLISH_CSS_RULES}

GENERATE Grammar Day {grammar_day_num} using EXACTLY this structure:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — Grammar: {topic}</h3>
<p class="lp-day-meta">Grammar Day {grammar_day_num} of 3 | 35 minutes | Class {class_num}</p>

<!-- [0-4 min] GRAMMAR SPARK -->
<div class="lp-section-opening">
  <p class="lp-section-label">⚡ Grammar Spark [0–4 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — {spark}.
   Write one example sentence from the lesson on board.
   Ask students what they notice about it.]"</p>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
    <p>"[3 Tamil sentences — same spark, same sentence, same question.]"</p>
    <p><em>இலக்கண விதி தமிழில் (Grammar rule in Tamil):</em><br/>
    "[Full simple grammar rule in Tamil — 2-3 sentences for teacher's understanding.]"</p>
  </div>

  <div class="board-work">
    <strong>Write on Board:</strong><br/>
    Example: "[sentence from lesson using {topic}]"<br/>
    Tamil: "[Tamil meaning of that sentence]"<br/>
    Focus: "[highlight the {topic} in the sentence]"
  </div>
</div>

<!-- [4-12 min] GRAMMAR EXPLANATION -->
<div class="lp-section-intro">
  <p class="lp-section-label">📐 Grammar Rule [4–12 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 simple sentences — explain {topic} rule step by step.
   Give 2 examples from the lesson text.
   Write each on board. Students repeat after teacher.]"</p>

  <div class="board-work">
    <strong>Board — Rule + 2 Examples:</strong><br/>
    Rule: [{topic} — one simple sentence rule]<br/>
    தமிழில்: [same rule in Tamil]<br/>
    1. [example from lesson] — [Tamil meaning]<br/>
    2. [example from lesson] — [Tamil meaning]
  </div>

  <div class="cfu-block">
    <strong>🔎 CFU:</strong>
    <p class="lp-teacher-says">"[Find one [topic] in this sentence — under 6 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[Student points to or names it]"</p>
    <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    <p><em>⏱ Wait 10 seconds. Call on 2 students.</em></p>
  </div>
</div>

<!-- [12-26 min] STUDENT PRACTICE -->
<div class="lp-section-student-task">
  <p class="lp-section-label">✍️ Practice [12–26 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — open notebook.
   Do these 3-4 questions. I will help if you need.
   Write neatly.]"</p>

  <div class="activity-block">
    <strong>Practice Questions ({ex_type} — {topic}):</strong>
    <p><strong>Q1:</strong> [Simple question] — <strong>Answer:</strong> [answer]</p>
    <p><strong>Q2:</strong> [Simple question] — <strong>Answer:</strong> [answer]</p>
    <p><strong>Q3:</strong> [Simple question] — <strong>Answer:</strong> [answer]</p>
    <p><strong>Q4:</strong> [Simple question] — <strong>Answer:</strong> [answer]</p>
  </div>

  <p class="lp-teacher-says"><strong>Teacher walks around and checks notebooks.</strong><br/>
  "[2 sentences — encourage students. Help slowly learners by pointing to board rule.]"</p>
</div>

<!-- [26-32 min] CLOSURE -->
<div class="lp-section-closing">
  <p class="lp-section-label">🔔 Closure [26–32 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — today we learned {topic}.
   Give one final simple example. Ask exit question.]"</p>

  <div class="board-work">
    <strong>Board — Remember This:</strong><br/>
    Rule: [{topic} in one simple sentence]<br/>
    Example: "[one clear example]"
  </div>

  <p><em>Preview: Tomorrow — {next_preview}</em></p>
</div>

<!-- [32-35 min] HOMEWORK -->
<div class="homework-block">
  <p class="lp-section-label">📝 Homework [32–35 min]</p>

  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 sentences — do 3 questions at home.
   Use today's rule. Bring tomorrow.]"</p>

  <div class="board-work">
    <strong>Homework:</strong><br/>
    Task: Write 3 sentences using {topic}<br/>
    Example: "[one model sentence]"<br/>
    Submit: Tomorrow
  </div>

  <div class="diff-block">
    <strong>Different Tasks:</strong>
    <table>
      <thead>
        <tr><th>Slow Learners</th><th>Average Learners</th><th>Fast Learners</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>Fill 2 blanks using word given<br/>
              "[sentence] _____ (option1/option2)"</td>
          <td>Write 2 sentences using {topic}<br/>
              using board examples as guide</td>
          <td>Write 3-4 sentences using {topic}<br/>
              about themselves or their family</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div>

FINAL CHECKS:
✅ Topic: {topic} — single concept only
✅ 3-4 practice questions — not more
✅ Questions simple — fill or identify only
✅ Grammar rule explained in Tamil for teacher
✅ Board has English rule + Tamil rule + 2 examples
✅ Homework max 3 sentences
✅ NO inline styles
✅ Raw HTML only — start with <div class="lp-day-block">
❌ NEVER add <style> blocks anywhere in your output
❌ NEVER add inline color styles on any element — no style="color:..." anywhere
❌ NEVER add inline style attributes of any kind inside board-work divs
✅ Do NOT generate Day {day_num + 1}

Lesson Text (for grammar examples):
---
{text[:4000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=14000,
                system=ENGLISH_LP_SYSTEM_PROMPT_67,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Prose LP 67 Grammar Day {grammar_day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 8 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit, lesson_title,
                         sections: dict, day_plan: dict) -> Optional[str]:
        try:
            characters = ", ".join(sections.get("characters", []))
            theme      = sections.get("theme", "")
            moral      = sections.get("moral", "")
            vocab      = ", ".join(sections.get("total_vocabulary", [])[:10])

            grammar_str = "\n".join(
                [f"  Day {3+g}: {day_plan.get(f'grammar_day{g}', {}).get('topic', '')}"
                 for g in range(1, 4)]
            )
            content_str = ""
            for d in range(1, 4):
                d_data = day_plan.get(f"content_day{d}", {})
                content_str += f"  Content Day {d}: {d_data.get('focus', '')}\n"

            prompt = f"""Generate ONLY the Assessment Summary for this English Prose lesson plan
for Class {class_num} (Grade 6-7).

Lesson     : {lesson_title}
Class      : {class_num}
Characters : {characters}
Theme      : {theme}
Moral      : {moral}
Vocabulary : {vocab}

Content Days:
{content_str}

Grammar Days:
{grammar_str}

Keep ALL assessment tasks SIMPLE — suitable for Class 6-7 students.
Maximum writing: 3-4 sentences. No essays.

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Check Questions</h3>
  <table>
    <thead>
      <tr>
        <th>Day</th>
        <th>Focus</th>
        <th>Simple Check Question</th>
        <th>Expected Answer</th>
      </tr>
    </thead>
    <tbody>
      [6 rows — one per day (3 content + 3 grammar).
       Content days: simple comprehension question.
       Grammar days: simple grammar identification question.
       All questions easy enough for Class 6-7.]
    </tbody>
  </table>

  <h3>Vocabulary Check — 10 Words</h3>
  <table>
    <thead>
      <tr><th>Word</th><th>Meaning</th><th>Tamil பொருள்</th></tr>
    </thead>
    <tbody>[10 simple vocabulary words from lesson — with meaning and Tamil]</tbody>
  </table>

  <h3>Written Assessment — 3 Levels</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Slow Learners</th>
        <th>Average Learners</th>
        <th>Fast Learners</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>
          <p>Fill blanks with word bank (5 words)</p>
          <p>Draw one scene from the story</p>
        </td>
        <td>
          <p>Answer 3 simple questions in 1-2 sentences each</p>
          <p>Write 2 sentences using any grammar topic from this unit</p>
        </td>
        <td>
          <p>Write 3-4 sentences about the story in own words</p>
          <p>Write 2 sentences about what you learned (moral/theme)</p>
        </td>
      </tr>
    </tbody>
  </table>

  <h3>Completion Checklist</h3>
  <ul>
    <li>☐ All 6 days of notes completed in notebook</li>
    <li>☐ All homework submitted (Days 1–6)</li>
    <li>☐ New words table filled for all content days</li>
    <li>☐ Grammar practice questions completed (Grammar Days 1–3)</li>
    <li>☐ Written assessment submitted</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- All content simple — Class 6-7 level
- No page numbers
- All content from lesson text only

Lesson Text:
---
{text[:2000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=5000,
                system=ENGLISH_LP_SYSTEM_PROMPT_67,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Prose LP 67 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_prose_lp_67_builder = EnglishProseLPBuilder67()