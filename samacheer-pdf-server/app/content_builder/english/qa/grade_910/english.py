"""
english/qa/grade_910/english.py
--------------------------------
QA Builder for Samacheer Kalvi English — All lesson types
Classes 8, 9 & 10

QA Structure (100 questions, 5 API calls):
  Call 1 → Section I:   MCQ Q1–Q25                (1 mark each)
  Call 2 → Section II:  Fill in the Blanks Q26–Q50 (1 mark each)
  Call 3 → Section III: Choose Statement Q51–Q60   (1 mark each)
            Section IV:  Match Q61–Q70              (1 mark each)
  Call 4 → Section V:   2-mark Q71–Q90             (2 marks each)
  Call 5 → Section VI:  5-mark Q91–Q100            (5 marks each)

v1.0 — June 2026
"""

import anthropic
from typing import Optional

from .....config import settings
from ...base import (
    ENGLISH_QA_SYSTEM_PROMPT,
    ENGLISH_ANSWER_FORMAT_RULES,
    get_english_qa_header,
    clean,
)


# ============================================================================
# ENGLISH QA BUILDER — GRADE 910
# ============================================================================

class EnglishQABuilder910:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English QA Builder (910) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        lesson_type  = metadata.get("lesson_type", "prose")

        print(f"      [English QA 910] Generating: {lesson_title}")
        print(f"      [English QA 910] 5 API calls: MCQ + Fill + Choose/Match + 2mark + 5mark")

        parts = [get_english_qa_header(lesson_title, class_num, unit, lesson_type)]

        # Call 1: MCQ Q1–Q25
        print(f"      [English QA 910] Call 1/5: MCQ Q1–Q25...")
        mcq = self._call_mcq(text, lesson_title, class_num, unit, lesson_type)
        if mcq:
            parts.append(clean(mcq))
            print(f"         ✅ MCQ ({len(mcq)} chars)")
        else:
            print(f"         ❌ MCQ failed")

        # Call 2: Fill in the Blanks Q26–Q50
        print(f"      [English QA 910] Call 2/5: Fill Q26–Q50...")
        fill = self._call_fill(text, lesson_title, class_num, unit, lesson_type)
        if fill:
            parts.append(clean(fill))
            print(f"         ✅ Fill ({len(fill)} chars)")
        else:
            print(f"         ❌ Fill failed")

        # Call 3: Choose Statement Q51–Q60 + Match Q61–Q70
        print(f"      [English QA 910] Call 3/5: Choose+Match Q51–Q70...")
        choose_match = self._call_choose_match(text, lesson_title, class_num, unit, lesson_type)
        if choose_match:
            parts.append(clean(choose_match))
            print(f"         ✅ Choose+Match ({len(choose_match)} chars)")
        else:
            print(f"         ❌ Choose+Match failed")

        # Call 4: 2-mark Q71–Q90
        print(f"      [English QA 910] Call 4/5: 2-mark Q71–Q90...")
        mark2 = self._call_2mark(text, lesson_title, class_num, unit, lesson_type)
        if mark2:
            parts.append(clean(mark2))
            print(f"         ✅ 2-mark ({len(mark2)} chars)")
        else:
            print(f"         ❌ 2-mark failed")

        # Call 5: 5-mark Q91–Q100
        print(f"      [English QA 910] Call 5/5: 5-mark Q91–Q100...")
        mark5 = self._call_5mark(text, lesson_title, class_num, unit, lesson_type)
        if mark5:
            parts.append(clean(mark5))
            print(f"         ✅ 5-mark ({len(mark5)} chars)")
        else:
            print(f"         ❌ 5-mark failed")

        if len(parts) <= 1:
            return None

        combined = "\n\n".join(parts)
        print(f"      [English QA 910] ✅ Complete — {len(parts)-1} sections, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 1 — MCQ Q1–Q25
    # =========================================================================

    def _call_mcq(self, text, lesson_title, class_num, unit, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Section I — Choose the Correct Answer for this English lesson QA.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {lesson_type.title()}

Generate EXACTLY 25 MCQ questions: Q1 to Q25.
Every question must be based ONLY on the lesson text provided — no invented content.

Question types — distribute evenly across 25 questions:
- Vocabulary in context (what does the word X mean in this passage?)
- Comprehension (who / what / where / when from the text)
- Character identification (who said / who did)
- Theme or mood (what is the mood / main theme)
- Literary device identification (this is an example of?)

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT — use EXACTLY this:

<div class="qa-section" id="section-mcq">
  <div class="section-header">
    <h2>Section I — Choose the Correct Answer</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-mcq')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>1 Mark each | Q1–Q25 | Choose the correct answer</em></p>

  [25 MCQ questions here — Q1 through Q25]

</div>

RULES:
- EXACTLY 25 questions — Q1 to Q25 — no skipping
- Raw HTML only — start with <div class="qa-section" id="section-mcq">
- All 4 options plausible — only one correct
- Correct answer ONLY inside answer-reveal div — NO tick marks anywhere
- ALL content from lesson text only
- Do NOT stop before Q25

Lesson Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=10000,
                system=ENGLISH_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 MCQ error: {e}")
            return None

    # =========================================================================
    # CALL 2 — FILL IN THE BLANKS Q26–Q50
    # =========================================================================

    def _call_fill(self, text, lesson_title, class_num, unit, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Section II — Fill in the Blanks for this English lesson QA.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {lesson_type.title()}

Generate EXACTLY 25 Fill in the Blanks questions: Q26 to Q50.
Every sentence must come directly from the lesson text — exact or near-exact.
The blank must replace a key word (vocabulary, character name, key event word).

Question types — distribute evenly:
- Vocabulary blanks (replace difficult or important word)
- Character name blanks (replace who said / who did)
- Event completion (what happened / where / when)
- Grammar-in-context blanks (replace verb form, preposition, article)

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT:

<div class="qa-section" id="section-fill">
  <div class="section-header">
    <h2>Section II — Fill in the Blanks</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-fill')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>1 Mark each | Q26–Q50 | Fill in the blank</em></p>

  [25 fill-in-the-blank questions here — Q26 through Q50]

</div>

RULES:
- EXACTLY 25 questions — Q26 to Q50 — no skipping
- Use <span class="blank-line">__________</span> for the blank
- Raw HTML only — start with <div class="qa-section" id="section-fill">
- All sentences from lesson text only
- Answers inside answer-reveal div only
- Do NOT stop before Q50
- You MUST generate the FULL 25 questions — do not stop early
- Do NOT stop before Q50 — verify you have written all 25 before finishing

Lesson Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=10000,
                system=ENGLISH_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 Fill error: {e}")
            return None

    # =========================================================================
    # CALL 3 — CHOOSE STATEMENT Q51–Q60 + MATCH Q61–Q70
    # =========================================================================

    def _call_choose_match(self, text, lesson_title, class_num, unit, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Section III and Section IV for this English lesson QA.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {lesson_type.title()}

═══════════════════════════════════════════════════════
SECTION III — CHOOSE THE CORRECT STATEMENT (Q51–Q60)
═══════════════════════════════════════════════════════

Generate EXACTLY 10 questions: Q51 to Q60.
Each question gives 3 statements about the lesson — student picks the correct one.
Statements must be specific and testable — based on lesson text only.

FORMAT:

<div class="qa-section" id="section-choose">
  <div class="section-header">
    <h2>Section III — Choose the Correct Statement</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-choose')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>1 Mark each | Q51–Q60 | Choose the correct statement</em></p>

  [10 choose-correct-statement questions — Q51 through Q60]
  [Use mcq-options div with i) ii) iii) format]
  [NO tick marks — correct answer only in answer-reveal]

</div>

═══════════════════════════════════════════════════════
SECTION IV — MATCH THE FOLLOWING (Q61–Q70)
═══════════════════════════════════════════════════════

Generate EXACTLY 10 questions: Q61 to Q70.
Q61 = Match Set 1 (5 pairs from lesson)
Q62–Q65 = Individual pair questions from Set 1
Q66 = Match Set 2 (5 pairs from lesson)
Q67–Q70 = Individual pair questions from Set 2

Match pairs must come from lesson text:
- Character → action or quote
- Word → meaning
- Event → outcome or location
- Literary device → example from text

FORMAT:

<div class="qa-section" id="section-match">
  <div class="section-header">
    <h2>Section IV — Match the Following</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-match')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>1 Mark each | Q61–Q70 | Match the following</em></p>

  <!-- SET 1: Q61–Q65 -->
  [Q61 = match table with 5 pairs]
  [Q62 = "From Set 1, what does [item 1] match with?"]
  [Q63 = "From Set 1, what does [item 2] match with?"]
  [Q64 = "From Set 1, what does [item 3] match with?"]
  [Q65 = "From Set 1, what does [item 4] match with?"]

  <!-- SET 2: Q66–Q70 -->
  [Q66 = match table with 5 pairs]
  [Q67 = "From Set 2, what does [item 1] match with?"]
  [Q68 = "From Set 2, what does [item 2] match with?"]
  [Q69 = "From Set 2, what does [item 3] match with?"]
  [Q70 = "From Set 2, what does [item 4] match with?"]

</div>

{ENGLISH_ANSWER_FORMAT_RULES}

RULES:
- Q51 through Q70 — ALL 20 must appear in output
- No tick marks anywhere
- All content from lesson text only
- Raw HTML only — start with <div class="qa-section" id="section-choose">
- You MUST generate ALL questions Q51–Q70 — do not stop early

Lesson Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=ENGLISH_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 Choose+Match error: {e}")
            return None

    # =========================================================================
    # CALL 4 — 2-MARK QUESTIONS Q71–Q90
    # =========================================================================

    def _call_2mark(self, text, lesson_title, class_num, unit, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Section V — Answer Briefly for this English lesson QA.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {lesson_type.title()}

Generate EXACTLY 20 questions: Q71 to Q90.
Each answer: EXACTLY 2-3 complete sentences. 30-50 words only.

Question types — distribute across 20 questions:
- Comprehension: Explain what happened when / where / why
- Character: Describe [character]'s role / what [character] did
- Vocabulary: What does [word] mean in this context?
- Theme/message: What does this [event/line/stanza] suggest about [theme]?
- Literary: Identify and explain [device] used in [line/passage]
Each type used approximately 4 times.

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT:

<div class="qa-section" id="section-2mark">
  <div class="section-header">
    <h2>Section V — Answer Briefly</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-2mark')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>2 Marks each | Q71–Q90 | Answer in 2-3 sentences</em></p>

  [20 two-mark questions here — Q71 through Q90]

</div>

RULES:
- EXACTLY 20 questions — Q71 to Q90 — no skipping
- Every answer: strictly 2-3 sentences, 30-50 words — never bullet points
- All answers inside answer-reveal div
- All content from lesson text only
- Raw HTML only — start with <div class="qa-section" id="section-2mark">
- You MUST generate the FULL 20 questions — do NOT stop before Q90

Lesson Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=14000,
                system=ENGLISH_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 2-mark error: {e}")
            return None

    # =========================================================================
    # CALL 5 — 5-MARK QUESTIONS Q91–Q100
    # =========================================================================

    def _call_5mark(self, text, lesson_title, class_num, unit, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Section VI — Answer in Detail for this English lesson QA.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {lesson_type.title()}

Generate EXACTLY 10 questions: Q91 to Q100.
Each answer: EXACTLY 5-7 complete sentences. 80-120 words. Proper paragraph — never bullet points.

Question types — distribute across 10 questions:
- Summary: Summarise the [prose/poem/story] in your own words
- Character analysis: Describe [character] with evidence from text
- Theme: Explain the theme of the [lesson] with examples
- Event analysis: Explain the significance of [key event]
- Appreciation: What do you like / what lesson do you learn from this?
- Literary analysis: Explain the effect of [device] in the text
- Comparative: How does [character/event A] differ from [character/event B]?

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT:

<div class="qa-section" id="section-5mark">
  <div class="section-header">
    <h2>Section VI — Answer in Detail</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-5mark')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>5 Marks each | Q91–Q100 | Answer in 5-7 sentences</em></p>

  [10 five-mark questions here — Q91 through Q100]

</div>

RULES:
- EXACTLY 10 questions — Q91 to Q100 — no skipping
- Every answer: strictly 5-7 sentences, 80-120 words — proper paragraph, never bullets
- All answers inside answer-reveal div
- All content from lesson text only
- Raw HTML only — start with <div class="qa-section" id="section-5mark">
- You MUST generate the FULL 10 questions — do NOT stop before Q100
- Do NOT stop before Q100 — verify you have written all 10 before finishing

Lesson Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=14000,
                system=ENGLISH_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 5-mark error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_qa_910_builder = EnglishQABuilder910()