"""
english/lp/grade_910/poem.py
-----------------------------
LP Builder for Samacheer Kalvi English — Poem
Classes 8, 9 & 10

Lesson structure:
  3 days total — 3 content days (no grammar days)
  Session duration: 45 minutes

API calls: 6 total
  Call 0a → Section Extractor   (JSON — poem stanzas + literary devices)
  Call 0b → Day Allocator       (JSON — stanzas to 3 days)
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

# Poem-specific activity styles per day
POEM_ACTIVITY_MAP_910 = {
    1: "Choral Reading — teacher leads, students repeat line by line",
    2: "Paraphrase Challenge — students rewrite stanza in their own words",
    3: "Literary Device Hunt — students identify and explain devices in notebook",
}


# ============================================================================
# POEM LP BUILDER — GRADE 910
# ============================================================================

class EnglishPoemLPBuilder910:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English Poem LP Builder (910) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [English Poem LP 910] Generating: {lesson_title}")
        print(f"      [English Poem LP 910] 6 API calls: 0a+0b+Preamble+Days1-3+Assessment")

        parts = []

        # Call 0a
        print(f"      [English Poem LP 910] Call 0a/6: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        print(f"         ✅ Extracted {len(sections.get('stanzas', []))} stanzas")

        # Call 0b
        print(f"      [English Poem LP 910] Call 0b/6: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None

        # Call 1
        print(f"      [English Poem LP 910] Call 1/6: Preamble...")
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
            print(f"      [English Poem LP 910] Call {call_num}/6: Day {day_num}...")
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
        print(f"      [English Poem LP 910] Call 5/6: Assessment...")
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
        print(f"      [English Poem LP 910] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 0a — SECTION EXTRACTOR
    # =========================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi English Poem.

Extract every stanza, the poem's theme, key vocabulary, literary devices,
rhyme scheme, and the poet's name — all from the text only.

If stanza numbers are not marked, divide the poem logically into readable stanzas.

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "stanzas": [
    {{
      "number": 1,
      "lines": ["Line 1", "Line 2", "Line 3", "Line 4"],
      "meaning": "What this stanza means in simple words",
      "literary_devices": ["device1 — example from stanza"],
      "key_vocabulary": ["word1", "word2"]
    }}
  ],
  "poet": "Poet name",
  "theme": "Central theme of the poem in one sentence",
  "rhyme_scheme": "ABAB / AABB / Free verse etc.",
  "mood": "The mood or tone of the poem",
  "total_vocabulary": ["word1", "word2"],
  "all_literary_devices": ["Alliteration — example", "Metaphor — example"]
}}

Poem Text:
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
            prompt = f"""Allocate the poem stanzas to EXACTLY 3 days.

RULES:
- Day 1: Introduction to poem + first set of stanzas (reading + basic meaning)
- Day 2: Middle stanzas + literary devices analysis
- Day 3: Final stanzas + full poem appreciation + theme discussion

Lesson: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting with {{

{{
  "day1": {{
    "stanzas": [1, 2],
    "focus": "Introduction to poem, poet, and first stanzas",
    "activity": "Choral reading and basic meaning"
  }},
  "day2": {{
    "stanzas": [3, 4],
    "focus": "Middle stanzas and literary devices",
    "activity": "Paraphrase and device identification"
  }},
  "day3": {{
    "stanzas": [5, 6],
    "focus": "Final stanzas, full poem appreciation, theme",
    "activity": "Literary device hunt and written response"
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
            poet      = sections.get("poet", "Unknown")
            theme     = sections.get("theme", "")
            rhyme     = sections.get("rhyme_scheme", "")
            devices   = ", ".join(sections.get("all_literary_devices", [])[:6])
            vocab     = ", ".join(sections.get("total_vocabulary", [])[:10])
            stanza_ct = len(sections.get("stanzas", []))

            prompt = f"""Generate ONLY the preamble for this English Poem Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Poem     : {lesson_title}
Poet     : {poet}
Class    : {class_num}
Unit     : {unit}
Subject  : English — Poem
Duration : 3 Days × 45 Minutes = 135 Minutes Total
Stanzas  : {stanza_ct}
Rhyme    : {rhyme}
Theme    : {theme}
Literary Devices: {devices}
Key Vocabulary: {vocab}

Day 1: {day_plan.get('day1', {}).get('focus', '')}
Day 2: {day_plan.get('day2', {}).get('focus', '')}
Day 3: {day_plan.get('day3', {}).get('focus', '')}

Generate EXACTLY these sections:

<h2>Part 1: Lesson Overview</h2>
Table: Class | Subject | Unit | Poem Title | Poet | Total Days |
       Session Duration | Rhyme Scheme | Theme

<h2>Part 2: Learning Objectives</h2>
4 objectives — read aloud, identify devices, explain meaning, appreciate theme
Based on this poem only.

<h2>Part 3: Language Objectives</h2>
3 objectives — vocabulary in context, poetic language, written appreciation

<h2>Part 4: Teaching Aids</h2>
Board, chalk, textbook, notebooks, vocabulary cards

OUTPUT RULES:
- Raw HTML only
{ENGLISH_PREAMBLE_INSTRUCTION}
- Stop after Teaching Aids

Poem Text:
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
            print(f"❌ English Poem LP 910 preamble error: {e}")
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
            activity     = POEM_ACTIVITY_MAP_910.get(day_num, "Individual written response")
            poet         = sections.get("poet", "")
            theme        = sections.get("theme", "")
            rhyme        = sections.get("rhyme_scheme", "")

            # Build stanza content for prompt
            all_stanzas  = sections.get("stanzas", [])
            today_stanza_data = [s for s in all_stanzas if s.get("number") in day_stanzas]
            stanzas_str  = ""
            vocab_today  = []
            devices_today = []
            for s in today_stanza_data:
                stanzas_str += f"\nStanza {s['number']}:\n"
                stanzas_str += "\n".join(s.get("lines", [])) + "\n"
                stanzas_str += f"Meaning: {s.get('meaning', '')}\n"
                vocab_today.extend(s.get("key_vocabulary", []))
                devices_today.extend(s.get("literary_devices", []))

            next_preview = (
                f"Day {day_num + 1}: {day_plan.get(f'day{day_num + 1}', {}).get('focus', '')}"
                if day_num < 3 else "Assessment and Review"
            )

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi English Poem Lesson Plan.

Poem     : {lesson_title}
Poet     : {poet}
Class    : {class_num}
Unit     : {unit}
Day      : {day_num} of 3
Duration : 45 minutes

Theme: {theme}
Rhyme Scheme: {rhyme}

TODAY'S STANZAS (Stanzas {', '.join(map(str, day_stanzas))}):
{stanzas_str}

Day Focus: {day_focus}
Today's Activity: {activity}
Key Vocabulary Today: {', '.join(vocab_today) if vocab_today else '(from stanzas)'}
Literary Devices Today: {', '.join(devices_today) if devices_today else '(from stanzas)'}

{ENGLISH_TAMIL_INSTRUCTION_910}
{ENGLISH_CCQ_CFU_INSTRUCTION_910}
{ENGLISH_CSS_RULES}

GENERATE Day {day_num} using this structure:

<div id="lp-day-{day_num}" class="lp-day-block">
<h3 class="lp-day-title">Day {day_num} — {lesson_title}: Stanzas {', '.join(map(str, day_stanzas))}</h3>
<p class="lp-day-meta">Poem Day {day_num} of 3 | 45 minutes | {lesson_title}</p>

<!-- [0-5 min] SPARK -->
<div class="lp-section-opening">
  <p class="lp-section-label">⚡ Spark / Opening [0–5 min]</p>
  <p class="lp-teacher-says"><strong>Teacher says (English):</strong><br/>
  "[3-4 sentences — {'Recap previous stanzas briefly.' if day_num > 1 else 'Introduce the poem and poet.'}
   Ask a thought-provoking question connecting to today's stanzas' theme.
   Connect to students' real life or emotions.]"</p>
  <div class="lp-tamil-scaffold">
    <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong><br/>
    <p>"[3-4 Tamil sentences — exact same content. Same length.]"</p>
  </div>
  <p class="student-says"><em>2-3 students respond. Teacher acknowledges.</em></p>
</div>

<!-- [5-10 min] VOCABULARY -->
<div class="lp-section-intro">
  <p class="lp-section-label">📚 Vocabulary [5–10 min]</p>
  <div class="vocab-block">
    <strong>Key Words from Today's Stanzas:</strong>
    <table>
      <thead><tr><th>Word</th><th>English Meaning</th><th>Tamil பொருள்</th></tr></thead>
      <tbody>
        [5-6 key words from today's stanzas — meaning and Tamil]
      </tbody>
    </table>
  </div>
</div>

<!-- [10-25 min] READING + EXPLANATION -->
<div class="lp-section-main">
  <p class="lp-section-label">📖 Reading + Explanation [10–25 min]</p>

  [FOR EACH stanza in today's list:]

  <h4>Stanza [N]</h4>
  <div class="board-work">
    <strong>Read aloud (write on board if short):</strong><br/>
    [Stanza lines]
  </div>
  <p class="lp-teacher-says"><strong>Teacher explains (English):</strong><br/>
  "[4-5 sentences — explain what the stanza means in simple words.
   Name any literary devices present. Give a real-life connection.
   Explain any difficult vocabulary in context.]"</p>

  <div class="cfu-block">
    <strong>🔎 CFU:</strong>
    <p class="lp-teacher-says">"[What does this stanza describe — under 8 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[Simple paraphrase of stanza]"</p>
    <p><em>⏱ Wait 10 seconds. Call on 2 students.</em></p>
  </div>

  <div class="ccq-block">
    <strong>⚡ CCQ:</strong>
    <p class="lp-teacher-says">"[Why does the poet use [device/image] here — under 10 words]?"</p>
    <p class="student-says"><strong>Expected:</strong> "[Inference about poet's intent]"</p>
    <p><em>⏱ Wait 20 seconds. Think-pair-share.</em></p>
  </div>

  [REPEAT for each stanza]

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
  "[3-4 sentences — recap today's stanzas. Name key devices found.
   Connect to overall theme. Praise the class.]"</p>
  <div class="board-work">
    <strong>Key Points:</strong><br/>
    1. [Stanza meaning summary]<br/>
    2. [Literary device found]<br/>
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
    Task: [Written task from today's stanzas — paraphrase or device explanation]<br/>
    Length: 3-5 sentences<br/>
    Submit: Tomorrow
  </div>
  <div class="diff-block">
    <strong>Differentiated Tasks:</strong>
    <table>
      <thead><tr><th>Slow Learners</th><th>Average Learners</th><th>Advanced Learners</th></tr></thead>
      <tbody>
        <tr>
          <td>Copy stanza + write one word meaning for each difficult word</td>
          <td>Paraphrase one stanza in 3-4 sentences</td>
          <td>Identify 2 literary devices + explain the effect in 5 sentences</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

</div>

FINAL CHECKS:
✅ All stanzas covered: {', '.join(map(str, day_stanzas))}
✅ Vocabulary table has 5-6 words with Tamil meanings
✅ Minimum 3 CFU + 3 CCQ blocks
✅ Activity is step-by-step with expected output
✅ Tamil ONLY in Spark + Key Terms table
✅ NO inline styles
✅ Raw HTML only — start with <div id="lp-day-{day_num}"
✅ Do NOT generate Day {day_num + 1}

Poem Text:
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
            print(f"❌ English Poem LP 910 Day {day_num} error: {e}")
            return None

    # =========================================================================
    # CALL 5 — ASSESSMENT SUMMARY
    # =========================================================================

    def _call_assessment(self, text, class_num, unit, lesson_title,
                         sections: dict, day_plan: dict) -> Optional[str]:
        try:
            poet    = sections.get("poet", "")
            theme   = sections.get("theme", "")
            devices = ", ".join(sections.get("all_literary_devices", [])[:6])
            vocab   = ", ".join(sections.get("total_vocabulary", [])[:10])

            prompt = f"""Generate ONLY the Assessment Summary for this English Poem lesson plan.

Poem  : {lesson_title}
Poet  : {poet}
Class : {class_num}
Theme : {theme}
Literary Devices: {devices}
Key Vocabulary: {vocab}

Day 1: {day_plan.get('day1', {}).get('focus', '')}
Day 2: {day_plan.get('day2', {}).get('focus', '')}
Day 3: {day_plan.get('day3', {}).get('focus', '')}

<h2>Assessment Summary</h2>
<div class="assessment-block">

  <h3>Day-wise Check Questions</h3>
  <table>
    <thead>
      <tr><th>Day</th><th>Stanzas</th><th>Check Question</th><th>Expected Answer</th></tr>
    </thead>
    <tbody>
      [3 rows — one per day. Questions about meaning, devices, and theme.]
    </tbody>
  </table>

  <h3>Vocabulary List — 10 Words</h3>
  <table>
    <thead><tr><th>Word</th><th>Meaning</th><th>From Stanza</th></tr></thead>
    <tbody>[10 vocabulary words with meanings and stanza reference]</tbody>
  </table>

  <h3>Written Assessment — 3 Levels</h3>
  <table class="diff-table">
    <thead>
      <tr>
        <th>Foundation Level</th>
        <th>Standard Level</th>
        <th>Advanced Level</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Fill blanks with word bank from poem<br/>Answer 1 meaning question</td>
        <td>Paraphrase one stanza (3-4 sentences)<br/>Name 2 literary devices with examples</td>
        <td>Essay — explain theme and poet's message in 8-10 sentences<br/>
            Identify all literary devices used and explain their effect</td>
      </tr>
    </tbody>
  </table>

  <h3>Completion Checklist</h3>
  <ul>
    <li>☐ All 3 days of notes completed</li>
    <li>☐ All homework submitted</li>
    <li>☐ Vocabulary table filled</li>
    <li>☐ Literary devices identified and explained</li>
    <li>☐ Written assessment submitted</li>
  </ul>

</div>

RULES:
- Raw HTML only. Start with <h2>Assessment Summary</h2>
- All content from poem text only

Poem Text:
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
            print(f"❌ English Poem LP 910 assessment error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_poem_lp_910_builder = EnglishPoemLPBuilder910()