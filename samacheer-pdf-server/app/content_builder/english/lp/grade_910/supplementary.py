"""
english/lp/grade_910/supplementary.py
--------------------------------------
LP Builder for Samacheer Kalvi English — Supplementary Reader
Classes 8, 9 & 10

Lesson structure:
  3 days total — 3 content days (no grammar days)
  Session duration: 45 minutes

API calls: 6 total
  Call 0a → Section Extractor   (JSON — story sections + characters)
  Call 0b → Day Allocator       (JSON — sections to 3 days)
  Call 1  → Preamble
  Calls 2–4 → Content Days 1–3
  Call 5  → Assessment Summary

v1.0 — June 2026
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
    ENGLISH_CSS_RULES,
    clean,
)

# Supplementary-specific activity styles per day
SUPPLEMENTARY_ACTIVITY_MAP_910 = {
    1: "Prediction Activity — what happens next? Students discuss in pairs",
    2: "Character Map — students draw and fill in a character relationship chart",
    3: "Story Retell + Personal Response — students retell in own words then give opinion",
}


# ============================================================================
# SUPPLEMENTARY LP BUILDER — GRADE 910
# ============================================================================

class EnglishSupplementaryLPBuilder910:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English Supplementary LP Builder (910) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [English Supplementary LP 910] Generating: {lesson_title}")
        print(f"      [English Supplementary LP 910] 6 API calls: 0a+0b+Preamble+Days1-3+Assessment")

        parts = []

        # Call 0a
        print(f"      [English Supplementary LP 910] Call 0a/6: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('story_sections', []))} sections")

        # Call 0b
        print(f"      [English Supplementary LP 910] Call 0b/6: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None

        # Call 1
        print(f"      [English Supplementary LP 910] Call 1/6: Preamble...")
        preamble = self._call_preamble(text, class_num, unit, lesson_title, sections, day_plan)
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting")
            return None

        # Calls 2–4: Days 1–3
        for day_num in range(1, 4):
            call_num = day_num + 1
            print(f"      [English Supplementary LP 910] Call {call_num}/6: Day {day_num}...")
            day_data = day_plan.get(f"day{day_num}", {})
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title,
                day_num, day_data, sections, day_plan
            )
            if day_html:
                parts.append(clean(day_html))
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        # Call 5: Assessment
        print(f"      [English Supplementary LP 910] Call 5/6: Assessment...")
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
        print(f"      [English Supplementary LP 910] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi English Supplementary Reader.

Extract every section/part of the story, all characters, key events, vocabulary,
and the central theme — from the text only. Do NOT add general knowledge.

If no headings exist, divide the story logically into 3 readable sections
suitable for 3 teaching days.

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "story_sections": [
    {{
      "title": "Section name or Part 1",
      "content_summary": "Brief description of what happens",
      "key_events": ["event1", "event2"],
      "key_vocabulary": ["word1", "word2"],
      "estimated_teaching_mins": 25
    }}
  ],
  "characters": [
    {{
      "name": "Character name",
      "role": "protagonist / antagonist / supporting",
      "description": "Brief description from text"
    }}
  ],
  "theme": "Central theme of the story in one sentence",
  "setting": "Where and when the story takes place",
  "total_vocabulary": ["word1", "word2"],
  "moral_or_message": "What the reader is meant to take away"
}}

Story Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=8000,
                system="You are a strict text extractor. Return ONLY valid JSON. No markdown. Raw JSON starting with {",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"❌ Supplementary Section Extractor JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Supplementary Section Extractor error: {e}")
            return None

    # =========================================================================
    # CALL 0b — DAY ALLOCATOR
    # =========================================================================

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        try:
            sections_str = json.dumps(sections, indent=2)
            prompt = f"""Allocate the story sections to EXACTLY 3 days.

RULES:
- Day 1: Introduction to story, setting, characters + first section
- Day 2: Middle section + rising action / conflict
- Day 3: Final section + resolution + personal response

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "day1": {{
    "sections": ["Section 1 title"],
    "focus": "Introduction, characters, setting, and first events",
    "key_vocabulary": ["word1", "word2"]
  }},
  "day2": {{
    "sections": ["Section 2 title"],
    "focus": "Rising action and key conflict",
    "key_vocabulary": ["word3", "word4"]
  }},
  "day3": {{
    "sections": ["Section 3 title"],
    "focus": "Resolution, theme, and personal response",
    "key_vocabulary": ["word5", "word6"]
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
            print(f"❌ Supplementary Day Allocator JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Supplementary Day Allocator error: {e}")
            return None

    # =========================================================================
    # CALL 1 — PREAMBLE
    # =========================================================================

    def _call_preamble(self, text, class_num, unit, lesson_title,
                       sections: dict, day_plan: dict) -> Optional[str]:
        try:
            characters   = [c["name"] for c in sections.get("characters", [])]
            theme        = sections.get("theme", "")
            setting      = sections.get("setting", "")
            moral        = sections.get("moral_or_message", "")
            vocab        = ", ".join(sections.get("total_vocabulary", [])[:10])
            section_ct   = len(sections.get("story_sections", []))

            prompt = f"""Generate ONLY the preamble for this English Supplementary Reader Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Story    : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Supplementary Reader
Duration : 3 Days × 45 Minutes = 135 Minutes Total
Sections : {section_ct}
Characters: {', '.join(characters)}
Setting  : {setting}
Theme    : {theme}
Moral    : {moral}
Key Vocabulary: {vocab}

Day 1: {day_plan.get('day1', {}).get('focus', '')}
Day 2: {day_plan.get('day2', {}).get('focus', '')}
Day 3: {day_plan.get('day3', {}).get('focus', '')}

Generate EXACTLY these sections:

<h2>Part 1: Lesson Overview</h2>
Table: Class | Subject | Unit | Story Title | Total Days |
       Session Duration | Theme | Setting

<h2>Part 2: Learning Objectives</h2>
4 objectives — read with understanding, identify characters, explain events, discuss theme
Based on this story only.

<h2>Part 3: Language Objectives</h2>
3 objectives — vocabulary in context, narrative comprehension, written response

<h2>Part 4: Teaching Aids</h2>
Board, chalk, textbook, notebooks, vocabulary cards

OUTPUT RULES:
- Raw HTML only
{ENGLISH_PREAMBLE_INSTRUCTION}
- Stop after Teaching Aids

Story Text:
---
{text[:2000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3000,
                system=ENGLISH_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Supplementary LP 910 preamble error: {e}")
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
            activity     = SUPPLEMENTARY_ACTIVITY_MAP_910.get(day_num, "Individual written response")
            theme        = sections.get("theme", "")
            characters   = [c["name"] for c in sections.get("characters", [])]
            moral        = sections.get("moral_or_message", "")

            next_preview = (
                f"Day {day_num + 1}: {day_plan.get(f'day{day_num + 1}', {}).get('focus', '')}"
                if day_num < 3 else "Assessment and Review"
            )

            sections_str = "\n".join([f"  ▸ {s}" for s in day_sections])
            chars_str    = ", ".join(characters)
            vocab_str    = ", ".join(day_vocab) if day_vocab else "(from story sections)"

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi English Supplementary Reader Lesson Plan.

Story    : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Day      : {day_num} of 3
Duration : 45 minutes

Theme: {theme}
Characters: {chars_str}
Moral/Message: {moral}

TODAY'S SECTIONS — COVER ALL IN ORDER:
{sections_str}

Day Focus: {day_focus}
Today's Activity: {activity}
Key Vocabulary Today: {vocab_str}

{ENGLISH_TAMIL_INSTRUCTION_910}
{ENGLISH_CCQ_CFU_INSTRUCTION_910}
{ENGLISH_CSS_RULES}

GENERATE Day {day_num} using this structure:

<div id="lp-day-{day_num}" class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — {lesson_title}: {day_focus}</h3>
<p class="lp-day-meta">Supplementary Day {day_num} of 3 | 45 minutes | {lesson_title}</p>

<!-- [0-5 min] SPARK -->
<div class="lp-section-opening">
  <p class="lp-section-label">⚡ Spark / Opening [0–5 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — {'Recap previous section briefly.' if day_num > 1 else 'Introduce the story, setting, and main character.'}
   Ask a prediction or opinion question connected to today's section.
   Build curiosity before reading.]"</p>
  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
    <p>"[3-4 Tamil sentences — exact same content and length.]"</p>
  </div>
  <p class="student-says"><em>2-3 students respond. Teacher acknowledges.</em></p>
</div>

<!-- [5-10 min] VOCABULARY -->
<div class="lp-section-intro">
  <p class="lp-section-label">📚 Vocabulary [5–10 min]</p>
  <div class="vocab-block">
    <strong>Key Vocabulary — Write on Board:</strong>
    <table>
      <thead><tr><th>Word</th><th>English Meaning</th><th>Tamil பொருள்</th></tr></thead>
      <tbody>
        [5-6 key words from today's section with meaning and Tamil]
      </tbody>
    </table>
  </div>
</div>

<!-- [10-25 min] READING + EXPLANATION -->
<div class="lp-section-main">
  <p class="lp-section-label">📖 Reading + Explanation [10–25 min]</p>

  [FOR EACH section in today's list — cover in order:]

  <h4>[Section/Part name]</h4>
  <p class="lp-teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
  "[4-5 sentences — read the passage aloud. Explain key events.
   Name characters and their actions. Connect to theme.
   Give one relatable real-life connection.]"</p>

  <div class="cfu-block">
    <strong>🔎 CFU:</strong>
    <p class="lp-teacher-says">"[What happened in this section — under 8 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[One sentence from story]"</p>
    <p><em>⏱ Wait 10 seconds. Call on 2 students.</em></p>
  </div>

  <div class="ccq-block">
    <strong>⚡ CCQ:</strong>
    <p class="lp-teacher-says">"[Why did [character] do/say [action] — under 10 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[Inference about character motivation]"</p>
    <p><em>⏱ Wait 20 seconds. Think-pair-share.</em></p>
  </div>

  [REPEAT for each section]
</div>

<!-- [25-35 min] STUDENT ACTIVITY -->
<div class="lp-section-student-task">
  <p class="lp-section-label">✍️ Student Activity [25–35 min]</p>
  <div class="activity-block">
    <strong>Activity: {activity}</strong>
    <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[4-5 sentences — explain activity step by step with time limit.]"</p>
    <p><strong>Step 1:</strong> [instruction]</p>
    <p><strong>Step 2:</strong> [instruction]</p>
    <p><strong>Step 3:</strong> [sharing]</p>
    <p class="student-says"><strong>Expected output:</strong> "[Example]"</p>
  </div>
</div>

<!-- [35-40 min] CLOSURE -->
<div class="lp-section-closing">
  <p class="lp-section-label">🔔 Closure [35–40 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — recap today's story section.
   {'Connect to moral/message: ' + moral if day_num == 3 else 'Preview what happens next.'}
   Praise the class.]"</p>
  <div class="board-work">
    <strong>Key Points:</strong><br/>
    1. [Key event from today]<br/>
    2. [Character action/decision]<br/>
    3. [Connection to theme]
  </div>
  <p><em>Preview: {next_preview}</em></p>
</div>

<!-- [40-45 min] HOMEWORK -->
<div class="homework-block">
  <p class="lp-section-label">📝 Homework [40–45 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — explain homework. What to write. How many sentences. Submit when.]"</p>
  <div class="board-work">
    <strong>Homework:</strong><br/>
    Task: [Written task from today's section]<br/>
    Length: 3-5 sentences<br/>
    Submit: Tomorrow
  </div>
  <div class="diff-block">
    <strong>Differentiated Tasks:</strong>
    <table>
      <thead><tr><th>Slow Learners</th><th>Average Learners</th><th>Advanced Learners</th></tr></thead>
      <tbody>
        <tr>
          <td>Fill blanks with word bank<br/>Answer 1 question about today's section</td>
          <td>Answer 2 comprehension questions<br/>in 2-3 sentences each</td>
          <td>Write a paragraph about a character's decision<br/>5+ sentences, own words</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div>

FINAL CHECKS:
✅ All sections covered: {', '.join(day_sections)}
✅ Vocabulary table has 5-6 words with Tamil meanings
✅ Minimum 3 CFU + 3 CCQ blocks
✅ Activity is specific and step-by-step
✅ Tamil ONLY in Spark + Key Terms table
✅ NO inline styles
✅ Raw HTML only — start with <div id="lp-day-{day_num}"
✅ Do NOT generate Day {day_num + 1}
✅ All content from story text only — no invented events

Story Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=16000,
                system=ENGLISH_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Supplementary LP 910 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 5 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit, lesson_title,
                         sections: dict, day_plan: dict) -> Optional[str]:
        try:
            characters = ", ".join([c["name"] for c in sections.get("characters", [])])
            theme      = sections.get("theme", "")
            moral      = sections.get("moral_or_message", "")
            vocab      = ", ".join(sections.get("total_vocabulary", [])[:10])

            prompt = f"""Generate ONLY the Assessment Summary for this English Supplementary Reader lesson plan.

Story  : {lesson_title}
Class  : {class_num}
Theme  : {theme}
Moral  : {moral}
Characters: {characters}
Key Vocabulary: {vocab}

Day 1: {day_plan.get('day1', {}).get('focus', '')}
Day 2: {day_plan.get('day2', {}).get('focus', '')}
Day 3: {day_plan.get('day3', {}).get('focus', '')}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Check Questions</h3>
  <table>
    <thead>
      <tr><th>Day</th><th>Section</th><th>Check Question</th><th>Expected Answer</th></tr>
    </thead>
    <tbody>
      [3 rows — one per day. Comprehension + inference questions.]
    </tbody>
  </table>

  <h3>Vocabulary List — 10 Words</h3>
  <table>
    <thead><tr><th>Word</th><th>Meaning</th><th>Used in story context</th></tr></thead>
    <tbody>[10 vocabulary words from story text only]</tbody>
  </table>

  <h3>Written Assessment — 3 Levels</h3>
  <table class="diff-table">
    <thead>
      <tr><th>Foundation Level</th><th>Standard Level</th><th>Advanced Level</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Fill blanks with word bank<br/>Answer 2 basic questions</td>
        <td>Retell the story in 5 sentences<br/>Describe one character in 3 sentences</td>
        <td>Essay — discuss the moral/theme using events from the story<br/>
            8-10 sentences, own words, no copying</td>
      </tr>
    </tbody>
  </table>

  <h3>Completion Checklist</h3>
  <ul>
    <li>☐ All 3 days of notes completed</li>
    <li>☐ All homework submitted</li>
    <li>☐ Vocabulary table filled</li>
    <li>☐ Written assessment submitted</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- All content from story text only

Story Text:
---
{text[:2000]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=4000,
                system=ENGLISH_LP_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Supplementary LP 910 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_supplementary_lp_910_builder = EnglishSupplementaryLPBuilder910()