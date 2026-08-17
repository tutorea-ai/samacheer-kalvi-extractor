"""
english/lp/grade_67/supplementary.py
--------------------------------------
LP Builder for Samacheer Kalvi English — Supplementary Reader
Classes 6 & 7

Lesson structure:
  3 days total — 3 content days (no grammar days)
  Session duration: 35 minutes

API calls: 6 total
  Call 0a → Section Extractor  (JSON — story sections + characters)
  Call 0b → Day Allocator      (JSON — sections to 3 days)
  Call 1  → Preamble
  Calls 2–4 → Content Days 1–3
  Call 5  → Assessment Summary

Grade_67 supplementary focus:
  - Simple story retelling
  - Character identification (good/bad/helpful)
  - Simple moral extraction
  - Activities: act out, draw, retell to partner
  - Writing max 3-4 sentences

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

# Grade_67 supplementary activity per day — concrete and fun
SUPPLEMENTARY_ACTIVITY_MAP_67 = {
    1: "Act it out — students role-play the characters from today's section",
    2: "Retell to partner — one student retells what happened, partner listens",
    3: "Story map — draw Title + Characters + What happened + Moral in notebook",
}


# ============================================================================
# SUPPLEMENTARY LP BUILDER — GRADE 67
# ============================================================================

class EnglishSupplementaryLPBuilder67:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English Supplementary LP Builder (67) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [English Supplementary LP 67] Generating: {lesson_title}")
        print(f"      [English Supplementary LP 67] 6 API calls: 0a+0b+Preamble+Days1-3+Assessment")

        parts = []

        # Call 0a
        print(f"      [English Supplementary LP 67] Call 0a/6: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('story_sections', []))} sections")

        # Call 0b
        print(f"      [English Supplementary LP 67] Call 0b/6: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None

        # Call 1
        print(f"      [English Supplementary LP 67] Call 1/6: Preamble...")
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
            print(f"      [English Supplementary LP 67] Call {call_num}/6: Day {day_num}...")
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
        print(f"      [English Supplementary LP 67] Call 5/6: Assessment...")
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
        print(f"      [English Supplementary LP 67] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi English
Supplementary Reader for Classes 6 and 7.

Extract every section of the story, all characters, key events, simple vocabulary,
and moral — from the text only. Keep everything simple for young learners.

Divide the story into 3 sections if no headings exist.
Each section must be small enough to teach in 15 minutes.

Lesson: {lesson_title}

Return ONLY valid JSON. Raw JSON starting with {{

{{
  "story_sections": [
    {{
      "title": "Part 1 or section name",
      "content_summary": "What happens — very simple words",
      "key_events": ["event1", "event2"],
      "key_vocabulary": ["word1", "word2", "word3"],
      "estimated_teaching_mins": 12
    }}
  ],
  "characters": [
    {{
      "name": "Character name",
      "role": "main / supporting",
      "simple_description": "One simple sentence about this character"
    }}
  ],
  "theme": "What the story is about — one simple sentence",
  "setting": "Where the story happens",
  "moral": "Simple lesson from the story — one sentence",
  "total_vocabulary": ["word1", "word2"]
}}

Story Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=6000,
                system="You are a strict text extractor for Class 6-7 English. Return ONLY valid JSON. No markdown. Raw JSON starting with {",
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
            prompt = f"""Allocate story sections to EXACTLY 3 days for Class 6-7.

- Day 1: Introduce story, characters, setting + first section
- Day 2: Middle section + what happens next
- Day 3: Final section + moral + simple response

Lesson: {lesson_title}

Return ONLY valid JSON. Raw JSON starting with {{

{{
  "day1": {{
    "sections": ["Part 1 title"],
    "focus": "Meet the characters and beginning of story",
    "key_vocabulary": ["word1", "word2", "word3"]
  }},
  "day2": {{
    "sections": ["Part 2 title"],
    "focus": "What happens in the middle",
    "key_vocabulary": ["word4", "word5"]
  }},
  "day3": {{
    "sections": ["Part 3 title"],
    "focus": "How the story ends and what we learn",
    "key_vocabulary": ["word6", "word7"]
  }}
}}

Extracted Sections:
---
{sections_str}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=2000,
                system="Return ONLY valid JSON. No markdown. Raw JSON starting with {",
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
            characters = [c["name"] for c in sections.get("characters", [])]
            theme      = sections.get("theme", "")
            setting    = sections.get("setting", "")
            moral      = sections.get("moral", "")
            vocab      = ", ".join(sections.get("total_vocabulary", [])[:8])

            prompt = f"""Generate ONLY the preamble for this English Supplementary Reader
Lesson Plan for Class {class_num} (Grade 6-7). Stop after Teaching Aids.

Story    : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Supplementary Reader
Duration : 3 Days × 35 Minutes = 105 Minutes Total
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
       Session Duration | Theme | Setting | Moral

<h2>Part 2: Learning Objectives</h2>
4 simple objectives — read story, name characters,
say what happened, learn the moral
Simple language for Class 6-7.

<h2>Part 3: Language Objectives</h2>
3 objectives — new words, simple sentences, short written response

<h2>Part 4: Teaching Aids</h2>
Board, chalk, textbook, notebooks, vocabulary cards

OUTPUT RULES:
- Raw HTML only
{ENGLISH_PREAMBLE_INSTRUCTION}
- Stop after Teaching Aids
- Simple language — Class 6-7 level

Story Text:
---
{text[:1500]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=2500,
                system=ENGLISH_LP_SYSTEM_PROMPT_67,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Supplementary LP 67 preamble error: {e}")
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
            activity     = SUPPLEMENTARY_ACTIVITY_MAP_67.get(day_num, "Retell to partner")
            characters   = [c["name"] for c in sections.get("characters", [])]
            theme        = sections.get("theme", "")
            moral        = sections.get("moral", "")
            setting      = sections.get("setting", "")

            next_preview = (
                f"Day {day_num + 1}: {day_plan.get(f'day{day_num + 1}', {}).get('focus', '')}"
                if day_num < 3 else "Assessment and Review"
            )

            sections_str = "\n".join([f"  ▸ {s}" for s in day_sections])
            chars_str    = ", ".join(characters)
            vocab_str    = ", ".join(day_vocab) if day_vocab else "(from story)"

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi English
Supplementary Reader Lesson Plan for Class {class_num} (Grade 6-7).

Story    : {lesson_title}
Class    : {class_num}
Day      : {day_num} of 3
Duration : 35 minutes

Characters: {chars_str}
Setting  : {setting}
Theme    : {theme}
Moral    : {moral}

TODAY'S SECTIONS:
{sections_str}

Day Focus: {day_focus}
Activity: {activity}
Key Vocabulary: {vocab_str}

GRADE 6-7 RULES:
- Very simple explanations — short sentences
- Students are 11-12 years old
- Activities must be fun — acting, drawing, retelling
- Writing max 3-4 sentences
- Students may answer in Tamil if they don't know English

{ENGLISH_TAMIL_INSTRUCTION_67}
{ENGLISH_CCQ_CFU_INSTRUCTION_67}
{ENGLISH_CSS_RULES}

GENERATE Day {day_num}:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — {lesson_title}: {day_focus}</h3>
<p class="lp-day-meta">Supplementary Day {day_num} of 3 | 35 minutes | Class {class_num}</p>

<!-- [0-4 min] SPARK -->
<div class="lp-section-opening">
  <p class="lp-section-label">⚡ Spark [0–4 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — {'Recap: what happened yesterday in one sentence.' if day_num > 1 else 'Introduce the story with one fun question.'}
   Ask one easy question about today's part of the story.
   Something students can relate to from their own life.]"</p>
  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
    <p>"[3 Tamil sentences — exact same. Simple Tamil.]"</p>
  </div>
  <p class="student-says"><em>2-3 students answer. Teacher accepts all answers warmly.</em></p>

  <div class="lp-teacher-says">
    <strong>Teacher says — Why We Learn This:</strong><br/>
    "[Explain specifically WHY students learn today's topic.
     Give a concrete real-life example from Tamil Nadu daily life.
     Tell them exactly where they will use this knowledge.
     Must be specific to today's sections — not generic.]"
  </div>
</div>

<!-- [4-8 min] VOCABULARY -->
<div class="lp-section-intro">
  <p class="lp-section-label">📚 New Words [4–8 min]</p>
  <div class="vocab-block">
    <strong>New Words — Write on Board:</strong>
    <table>
      <thead><tr><th>Word</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
      <tbody>
        [4-5 simple picturable words from today's section — meaning and Tamil]
      </tbody>
    </table>
  </div>
  <p><em>Students say each word aloud. Teacher shows action/picture if possible.</em></p>
</div>

<!-- [8-20 min] READING + EXPLANATION -->
<div class="lp-section-main">
  <p class="lp-section-label">📖 Reading + Story [8–20 min]</p>

  [FOR EACH section today:]

  <h4>[Section/Part name]</h4>
  <p class="lp-teacher-says"><strong>Teacher reads aloud and explains (English):</strong><br/>
  "[3-4 simple sentences — read slowly and clearly.
   Explain what happens in very simple words.
   Name who does what. Point to characters.]"</p>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
    <p>"[3-4 Tamil sentences — same explanation. Simple Tamil.]"</p>
  </div>

  <div class="cfu-block">
    <strong>🔎 CFU:</strong>
    <p class="lp-teacher-says">"[Who did / What happened — under 6 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[One word or short phrase]"</p>
    <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    <p><em>⏱ Students may answer in Tamil. That is OK.</em></p>
  </div>

  <div class="ccq-block">
    <strong>⚡ CCQ:</strong>
    <p class="lp-teacher-says">"[Simple Why question — under 8 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[1-2 simple sentences]"</p>
    <p><em>⏱ Think for 10 seconds. Students may discuss with neighbour.</em></p>
  </div>

  [REPEAT for each section]
</div>

<!-- [20-28 min] ACTIVITY -->
<div class="lp-section-student-task">
  <p class="lp-section-label">🎯 Activity [20–28 min]</p>
  <div class="activity-block">
    <strong>Activity: {activity}</strong>
    <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 simple sentences — explain activity step by step.
     Fun and clear. Students know exactly what to do.]"</p>
    <p><strong>Step 1:</strong> [Simple instruction]</p>
    <p><strong>Step 2:</strong> [Simple instruction]</p>
    <p><strong>Step 3:</strong> [Show teacher / share with class]</p>
    <p class="student-says"><strong>Expected:</strong> "[Simple output — retell / drawing / acting]"</p>
  </div>
</div>

<!-- [28-32 min] CLOSURE -->
<div class="lp-section-closing">
  <p class="lp-section-label">🔔 Closure [28–32 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — what happened in today's story part.
   {'What is the moral of the story: ' + moral if day_num == 3 else 'What do you think happens next?'}
   Praise the class warmly.]"</p>
  <div class="board-work">
    <strong>Write on Board:</strong><br/>
    Today: [one sentence summary of today's story part]<br/>
    {"Moral: " + moral if day_num == 3 and moral else "Next: " + next_preview}
  </div>
</div>

<!-- [32-35 min] HOMEWORK -->
<div class="homework-block">
  <p class="lp-section-label">📝 Homework [32–35 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 sentences — simple homework. Write 3-4 sentences max. Bring tomorrow.]"</p>
  <div class="board-work">
    <strong>Homework:</strong><br/>
    Task: [Simple written task — 3-4 sentences about today's story section]<br/>
    Example: "[One model sentence from today]"<br/>
    Submit: Tomorrow
  </div>
  <div class="diff-block">
    <strong>Different Tasks:</strong>
    <table>
      <thead><tr><th>Slow Learners</th><th>Average Learners</th><th>Fast Learners</th></tr></thead>
      <tbody>
        <tr>
          <td>Draw one scene from today's story<br/>Write 1 sentence about it</td>
          <td>Answer 2 simple questions<br/>in 1-2 sentences each</td>
          <td>Write 3-4 sentences retelling<br/>today's story in own words</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div>

FINAL CHECKS:
✅ Sections covered: {', '.join(day_sections)}
✅ Vocabulary 4-5 simple words with Tamil
✅ Minimum 3 CFU blocks — simple questions
✅ Activity is fun and concrete
✅ Homework max 3-4 sentences
✅ Tamil in 3 places: Spark + Key Terms + CFU touch
✅ NO inline styles
✅ Raw HTML only — start with <div class="lp-day-block">
❌ NEVER add <style> blocks anywhere in your output
❌ NEVER add inline color styles on any element — no style="color:..." anywhere
❌ NEVER add inline style attributes of any kind inside board-work divs
✅ Do NOT generate Day {day_num + 1}

Story Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=14000,
                system=ENGLISH_LP_SYSTEM_PROMPT_67,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Supplementary LP 67 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 5 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit, lesson_title,
                         sections: dict, day_plan: dict) -> Optional[str]:
        try:
            characters = ", ".join([c["name"] for c in sections.get("characters", [])])
            theme      = sections.get("theme", "")
            moral      = sections.get("moral", "")
            vocab      = ", ".join(sections.get("total_vocabulary", [])[:8])

            prompt = f"""Generate ONLY the Assessment Summary for this English Supplementary
Reader lesson plan for Class {class_num} (Grade 6-7). Keep everything SIMPLE.

Story  : {lesson_title}
Class  : {class_num}
Theme  : {theme}
Moral  : {moral}
Characters: {characters}
Key Vocabulary: {vocab}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Simple Check Questions</h3>
  <table>
    <thead>
      <tr><th>Day</th><th>Story Part</th><th>Simple Question</th><th>Expected Answer</th></tr>
    </thead>
    <tbody>
      [3 rows — very simple who/what/why questions.
       Class 6-7 level — one sentence answers.]
    </tbody>
  </table>

  <h3>Vocabulary — 8 Simple Words</h3>
  <table>
    <thead><tr><th>Word</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
    <tbody>[8 simple words from story text only]</tbody>
  </table>

  <h3>Written Assessment — 3 Levels</h3>
  <table class="diff-table">
    <thead>
      <tr><th>Slow Learners</th><th>Average Learners</th><th>Fast Learners</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Draw one scene from story<br/>Write character names</td>
        <td>Answer 3 simple questions<br/>in 1-2 sentences each</td>
        <td>Write 3-4 sentences retelling the story<br/>Write the moral in own words</td>
      </tr>
    </tbody>
  </table>

  <h3>Completion Checklist</h3>
  <ul>
    <li>☐ All 3 days of notes completed</li>
    <li>☐ All homework submitted</li>
    <li>☐ New words written with meanings</li>
    <li>☐ Written assessment submitted</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Simple language — Class 6-7 level throughout

Story Text:
---
{text[:1500]}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=3500,
                system=ENGLISH_LP_SYSTEM_PROMPT_67,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English Supplementary LP 67 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_supplementary_lp_67_builder = EnglishSupplementaryLPBuilder67()