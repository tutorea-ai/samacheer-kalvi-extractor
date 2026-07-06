"""
english/lp/grade_67/poem.py
-----------------------------
LP Builder for Samacheer Kalvi English — Poem
Classes 6 & 7

Lesson structure:
  3 days total — 3 content days (no grammar days)
  Session duration: 35 minutes

API calls: 6 total
  Call 0a → Section Extractor  (JSON — stanzas + simple devices)
  Call 0b → Day Allocator      (JSON — stanzas to 3 days)
  Call 1  → Preamble
  Calls 2–4 → Content Days 1–3
  Call 5  → Assessment Summary

Grade_67 poem focus:
  - Simple literary devices only: rhyme, repetition, basic alliteration
  - No metaphor, personification analysis at this level
  - Choral reading emphasis — students read aloud together
  - Activities: kinesthetic, drawing, acting out

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

# Grade_67 poem activity per day — concrete and kinesthetic
POEM_ACTIVITY_MAP_67 = {
    1: "Choral reading — teacher reads line by line, students repeat together",
    2: "Rhyme hunt — students circle all rhyming words in their textbook",
    3: "Poem illustration — students draw a picture for their favourite stanza",
}


# ============================================================================
# POEM LP BUILDER — GRADE 67
# ============================================================================

class EnglishPoemLPBuilder67:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English Poem LP Builder (67) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [English Poem LP 67] Generating: {lesson_title}")
        print(f"      [English Poem LP 67] 6 API calls: 0a+0b+Preamble+Days1-3+Assessment")

        parts = []

        # Call 0a
        print(f"      [English Poem LP 67] Call 0a/6: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('stanzas', []))} stanzas")

        # Call 0b
        print(f"      [English Poem LP 67] Call 0b/6: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None

        # Call 1
        print(f"      [English Poem LP 67] Call 1/6: Preamble...")
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
            print(f"      [English Poem LP 67] Call {call_num}/6: Day {day_num}...")
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
        print(f"      [English Poem LP 67] Call 5/6: Assessment...")
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
        print(f"      [English Poem LP 67] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi English Poem
for Classes 6 and 7.

Extract every stanza, simple meaning, rhyme scheme, and key vocabulary.
Keep everything simple — suitable for young learners.

SIMPLE DEVICES ONLY for Grade 6-7:
  - Rhyme (words that sound alike at end of lines)
  - Repetition (same word or phrase repeated)
  - Alliteration (same starting sound) — only if very obvious

Do NOT extract complex devices like metaphor, personification,
onomatopoeia etc. — these are too advanced for Grade 6-7.

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "stanzas": [
    {{
      "number": 1,
      "lines": ["Line 1", "Line 2", "Line 3", "Line 4"],
      "simple_meaning": "What this stanza says in very simple words",
      "rhyming_words": ["word1", "word2"],
      "key_vocabulary": ["word1", "word2"]
    }}
  ],
  "poet": "Poet name",
  "theme": "What the poem is about — one simple sentence",
  "rhyme_scheme": "ABAB / AABB / Free verse",
  "simple_devices": ["Rhyme — example", "Repetition — example"],
  "total_vocabulary": ["word1", "word2"],
  "moral": "Simple lesson from the poem — one sentence"
}}

Poem Text:
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
            print(f"❌ Poem Section Extractor JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Poem Section Extractor error: {e}")
            return None

    # =========================================================================
    # CALL 0b — DAY ALLOCATOR
    # =========================================================================

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        try:
            sections_str = json.dumps(sections, indent=2)
            prompt = f"""Allocate the poem stanzas to EXACTLY 3 days for Class 6-7 students.

RULES:
- Day 1: Introduce poem + poet + first stanzas + read aloud + basic meaning
- Day 2: Remaining stanzas + rhyme scheme + simple device (rhyme/repetition)
- Day 3: Full poem reading + simple appreciation + theme in own words

Lesson: {lesson_title}

Return ONLY valid JSON. Raw JSON starting with {{

{{
  "day1": {{
    "stanzas": [1, 2],
    "focus": "Introduction and first stanzas — simple meaning",
    "activity": "Choral reading"
  }},
  "day2": {{
    "stanzas": [3, 4],
    "focus": "More stanzas and rhyme scheme",
    "activity": "Rhyme hunt"
  }},
  "day3": {{
    "stanzas": [5, 6],
    "focus": "Final stanzas and simple appreciation",
    "activity": "Poem illustration"
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
            print(f"❌ Poem Day Allocator JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ Poem Day Allocator error: {e}")
            return None

    # =========================================================================
    # CALL 1 — PREAMBLE
    # =========================================================================

    def _call_preamble(self, text, class_num, unit, lesson_title,
                       sections: dict, day_plan: dict) -> Optional[str]:
        try:
            poet     = sections.get("poet", "Unknown")
            theme    = sections.get("theme", "")
            rhyme    = sections.get("rhyme_scheme", "")
            devices  = ", ".join(sections.get("simple_devices", [])[:3])
            vocab    = ", ".join(sections.get("total_vocabulary", [])[:8])
            moral    = sections.get("moral", "")

            prompt = f"""Generate ONLY the preamble for this English Poem Lesson Plan
for Class {class_num} (Grade 6-7). Stop after Teaching Aids.

Poem     : {lesson_title}
Poet     : {poet}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Poem
Duration : 3 Days × 35 Minutes = 105 Minutes Total
Theme    : {theme}
Moral    : {moral}
Rhyme    : {rhyme}
Simple Devices: {devices}
Key Vocabulary: {vocab}

Day 1: {day_plan.get('day1', {}).get('focus', '')}
Day 2: {day_plan.get('day2', {}).get('focus', '')}
Day 3: {day_plan.get('day3', {}).get('focus', '')}

Generate EXACTLY these sections:

<h2>Part 1: Lesson Overview</h2>
Table: Class | Subject | Unit | Poem Title | Poet | Total Days |
       Session Duration | Rhyme Scheme | Theme

<h2>Part 2: Learning Objectives</h2>
4 simple objectives — read aloud, find rhyming words,
say meaning, enjoy the poem
Simple language for Class 6-7.

<h2>Part 3: Language Objectives</h2>
3 objectives — new words, rhyme awareness, short written response

<h2>Part 4: Teaching Aids</h2>
Board, chalk, textbook, notebooks, coloured chalk for rhyme marking

OUTPUT RULES:
- Raw HTML only
{ENGLISH_PREAMBLE_INSTRUCTION}
- Stop after Teaching Aids
- Simple language — Class 6-7 level

Poem Text:
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
            print(f"❌ English Poem LP 67 preamble error: {e}")
            return None

    # =========================================================================
    # CALLS 2–4 — CONTENT DAYS 1–3
    # =========================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                          day_num: int, day_data: dict,
                          sections: dict, day_plan: dict) -> Optional[str]:
        try:
            day_stanzas  = day_data.get("stanzas", [])
            day_focus    = day_data.get("focus", "")
            activity     = POEM_ACTIVITY_MAP_67.get(day_num, "Choral reading")
            poet         = sections.get("poet", "")
            theme        = sections.get("theme", "")
            rhyme        = sections.get("rhyme_scheme", "")
            moral        = sections.get("moral", "")

            # Build stanza content
            all_stanzas   = sections.get("stanzas", [])
            today_stanzas = [s for s in all_stanzas if s.get("number") in day_stanzas]
            stanzas_str   = ""
            vocab_today   = []
            rhymes_today  = []
            for s in today_stanzas:
                stanzas_str += f"\nStanza {s['number']}:\n"
                stanzas_str += "\n".join(s.get("lines", [])) + "\n"
                stanzas_str += f"Simple Meaning: {s.get('simple_meaning', '')}\n"
                vocab_today.extend(s.get("key_vocabulary", []))
                rhymes_today.extend(s.get("rhyming_words", []))

            next_preview = (
                f"Day {day_num + 1}: {day_plan.get(f'day{day_num + 1}', {}).get('focus', '')}"
                if day_num < 3 else "Assessment and Review"
            )

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi English Poem
Lesson Plan for Class {class_num} (Grade 6-7).

Poem     : {lesson_title}
Poet     : {poet}
Class    : {class_num}
Day      : {day_num} of 3
Duration : 35 minutes

Theme : {theme}
Moral : {moral}
Rhyme : {rhyme}

TODAY'S STANZAS (Stanzas {', '.join(map(str, day_stanzas))}):
{stanzas_str}

Day Focus: {day_focus}
Activity: {activity}
Key Vocabulary Today: {', '.join(vocab_today) if vocab_today else '(from stanzas)'}
Rhyming Words Today: {', '.join(rhymes_today) if rhymes_today else '(from stanzas)'}

GRADE 6-7 RULES:
- Keep explanations very simple — short sentences
- Focus on rhyme and repetition only — no complex devices
- Activities must be fun and concrete — choral reading, drawing, finding words
- Writing max 2-3 sentences
- Students may answer in Tamil if they don't know English answer

{ENGLISH_TAMIL_INSTRUCTION_67}
{ENGLISH_CCQ_CFU_INSTRUCTION_67}
{ENGLISH_CSS_RULES}

GENERATE Day {day_num}:

<div class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — {lesson_title}: Stanzas {', '.join(map(str, day_stanzas))}</h3>
<p class="lp-day-meta">Poem Day {day_num} of 3 | 35 minutes | Class {class_num}</p>

<!-- [0-4 min] SPARK -->
<div class="lp-section-opening">
  <p class="lp-section-label">⚡ Spark [0–4 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — {'Recap yesterday stanzas in one sentence.' if day_num > 1 else 'Introduce poem and poet simply.'}
   Ask one easy fun question about today's stanzas theme.
   Connect to something students know from daily life.]"</p>
  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
    <p>"[3 Tamil sentences — exact same. Simple Tamil.]"</p>
  </div>
  <p class="student-says"><em>2-3 students answer. Teacher says "Very good!" and moves on.</em></p>
</div>

<!-- [4-8 min] VOCABULARY -->
<div class="lp-section-intro">
  <p class="lp-section-label">📚 New Words [4–8 min]</p>
  <div class="vocab-block">
    <strong>New Words from Today's Stanzas:</strong>
    <table>
      <thead><tr><th>Word</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
      <tbody>
        [4-5 simple words from today's stanzas — simple meaning and Tamil]
      </tbody>
    </table>
  </div>
  <p><em>Students say each word aloud after teacher — 2 times.</em></p>
</div>

<!-- [8-20 min] READING + EXPLANATION -->
<div class="lp-section-main">
  <p class="lp-section-label">📖 Reading + Meaning [8–20 min]</p>

  [FOR EACH stanza today:]

  <h4>Stanza [N]</h4>
  <div class="board-work">
    <strong>Teacher reads aloud slowly:</strong><br/>
    [Stanza lines — if short, write on board]
  </div>

  <p class="lp-teacher-says"><strong>Teacher explains (English):</strong><br/>
  "[3-4 simple sentences — what does this stanza say.
   Use very simple words. Point to rhyming words.
   Give a simple real-life connection.]"</p>

  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
    <p>"[3-4 Tamil sentences — same explanation. Simple Tamil.]"</p>
  </div>

  <div class="cfu-block">
    <strong>🔎 CFU:</strong>
    <p class="lp-teacher-says">"[What does this stanza tell us — under 6 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[One simple sentence]"</p>
    <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
    <p><em>⏱ Students may answer in Tamil. That is OK.</em></p>
  </div>

  [REPEAT for each stanza]

  {"<p><em>Point to rhyming words: " + ', '.join(rhymes_today[:4]) + " — say them aloud together.</em></p>" if rhymes_today else ""}
</div>

<!-- [20-28 min] ACTIVITY -->
<div class="lp-section-student-task">
  <p class="lp-section-label">🎯 Activity [20–28 min]</p>
  <div class="activity-block">
    <strong>Activity: {activity}</strong>
    <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
    "[3-4 simple sentences — explain activity clearly.
     What to do step by step. How long. Show teacher when done.]"</p>
    <p><strong>Step 1:</strong> [Simple instruction]</p>
    <p><strong>Step 2:</strong> [Simple instruction]</p>
    <p><strong>Step 3:</strong> [Share with class]</p>
  </div>
</div>

<!-- [28-32 min] CLOSURE -->
<div class="lp-section-closing">
  <p class="lp-section-label">🔔 Closure [28–32 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 simple sentences — what stanzas did we read.
   What rhyming words did we find. Praise the class.]"</p>
  <div class="board-work">
    <strong>Remember:</strong><br/>
    Rhyming words: {', '.join(rhymes_today[:4]) if rhymes_today else '[from stanzas]'}<br/>
    {"Moral: " + moral if day_num == 3 and moral else "Preview: " + next_preview}
  </div>
</div>

<!-- [32-35 min] HOMEWORK -->
<div class="homework-block">
  <p class="lp-section-label">📝 Homework [32–35 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3 sentences — simple homework. Write 2-3 sentences only. Bring tomorrow.]"</p>
  <div class="board-work">
    <strong>Homework:</strong><br/>
    Task: [Simple task — copy one stanza OR write 2 sentences about what it means]<br/>
    Submit: Tomorrow
  </div>
  <div class="diff-block">
    <strong>Different Tasks:</strong>
    <table>
      <thead><tr><th>Slow Learners</th><th>Average Learners</th><th>Fast Learners</th></tr></thead>
      <tbody>
        <tr>
          <td>Copy one stanza neatly<br/>Circle the rhyming words</td>
          <td>Write meaning of one stanza<br/>in 2 simple sentences</td>
          <td>Write 3-4 sentences about<br/>what the poem is about</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div>

FINAL CHECKS:
✅ Stanzas covered: {', '.join(map(str, day_stanzas))}
✅ Vocabulary table has 4-5 simple words with Tamil
✅ Minimum 3 CFU blocks — simple questions
✅ Activity is fun and concrete
✅ Homework max 2-3 sentences
✅ Tamil in 3 places: Spark + Key Terms + CFU touch
✅ NO inline styles
✅ Raw HTML only — start with <div class="lp-day-block">
❌ NEVER add <style> blocks anywhere in your output
❌ NEVER add inline color styles on any element — no style="color:..." anywhere
❌ NEVER add inline style attributes of any kind inside board-work divs
✅ Do NOT generate Day {day_num + 1}

Poem Text:
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
            print(f"❌ English Poem LP 67 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 5 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit, lesson_title,
                         sections: dict, day_plan: dict) -> Optional[str]:
        try:
            poet    = sections.get("poet", "")
            theme   = sections.get("theme", "")
            moral   = sections.get("moral", "")
            devices = ", ".join(sections.get("simple_devices", [])[:3])
            vocab   = ", ".join(sections.get("total_vocabulary", [])[:8])

            prompt = f"""Generate ONLY the Assessment Summary for this English Poem lesson plan
for Class {class_num} (Grade 6-7). Keep everything SIMPLE.

Poem  : {lesson_title}
Poet  : {poet}
Theme : {theme}
Moral : {moral}
Simple Devices: {devices}
Key Vocabulary: {vocab}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Simple Check Questions</h3>
  <table>
    <thead>
      <tr><th>Day</th><th>Stanzas</th><th>Simple Question</th><th>Expected Answer</th></tr>
    </thead>
    <tbody>
      [3 rows — very simple questions about meaning and rhyme.
       Class 6-7 level — one sentence answers.]
    </tbody>
  </table>

  <h3>Vocabulary — 8 Simple Words</h3>
  <table>
    <thead><tr><th>Word</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
    <tbody>[8 simple words from poem with meanings and Tamil]</tbody>
  </table>

  <h3>Written Assessment — 3 Levels</h3>
  <table class="diff-table">
    <thead>
      <tr><th>Slow Learners</th><th>Average Learners</th><th>Fast Learners</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Copy one stanza neatly<br/>Circle 2 rhyming words</td>
        <td>Write meaning of one stanza in 2 sentences<br/>Name one rhyming pair</td>
        <td>Write 3-4 sentences about the poem's theme<br/>Name one simple device with example</td>
      </tr>
    </tbody>
  </table>

  <h3>Completion Checklist</h3>
  <ul>
    <li>☐ All 3 days of notes completed</li>
    <li>☐ All homework submitted</li>
    <li>☐ New words written with meanings</li>
    <li>☐ Rhyming words identified and circled</li>
    <li>☐ Written assessment submitted</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- Simple language — Class 6-7 level throughout

Poem Text:
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
            print(f"❌ English Poem LP 67 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_poem_lp_67_builder = EnglishPoemLPBuilder67()