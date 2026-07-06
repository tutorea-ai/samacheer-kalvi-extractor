"""
english/qa/grade_67/english.py
--------------------------------
QA Builder for Samacheer Kalvi English — Classes 6 & 7
Single lesson at a time (Prose OR Poem OR Supplementary — per unit/lesson_choice)

Follows school-level blueprint (same structure as grade_910, simpler content):
  Part I   → Q1–Q25    (25 × 1 mark)  — MCQ: Vocab + Comprehension + Simple Grammar
  Part II  → Q26–Q50   (25 × 1 mark)  — Fill in the Blanks
  Part III → Q51–Q70   (20 × 2 marks) — Short Answer: 2-3 simple sentences
  Part IV  → Q71–Q90   (20 × 5 marks) — Paragraph: 3-4 sentences max
  Part V   → Q91–Q100  (10 × 8 marks) — Simple essay + reading comprehension

Total: 100 questions

API calls: 5 total
  Call 1 → Part I   (MCQ Q1–Q25)
  Call 2 → Part II  (Fill Blanks Q26–Q50)
  Call 3 → Part III (Short Answer Q51–Q70)
  Call 4 → Part IV  (Paragraph Q71–Q90)
  Call 5 → Part V   (Extended Q91–Q100)

v2.0 — July 2026
Reverted to single-lesson-text QA generation (removed prose/poem/supplementary
3-text combination) — same 100-question Part I–V structure retained.
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
# GRADE 67 QA SYSTEM PROMPT
# ============================================================================

GRADE67_QA_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi English teacher
creating a question bank for Classes 6 and 7 Tamil Nadu state board students.

Students are young learners (11-12 years old). Keep ALL questions simple and clear.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags
- Generate questions AND answers based ONLY on the lesson text provided
- NEVER invent facts, events, or vocabulary not in the text
- EVERY question must have a clear complete answer inside answer-reveal div
- NEVER use textarea or input boxes

QUESTION DIFFICULTY — CLASS 6-7 LEVEL:
- Use simple, common English words in questions
- Questions must be straightforward — no tricky phrasing
- Answers should be findable directly from the text
- No complex analysis or inference at this level

QUESTION COMPOSITION — strictly follow across all parts:
  Vocabulary          → ~20% of questions
  Comprehension       → ~40% of questions
  Grammar in context  → ~15% of questions
  Literary devices    → ~15% of questions
  Moral/theme         → ~10% of questions

ANSWER LENGTH RULES:
  1-mark  → one word or one short phrase
  2-mark  → exactly 2 simple sentences, 20-40 words
  5-mark  → exactly 3-4 sentences, 50-80 words, simple paragraph
  8-mark  → exactly 6-8 sentences, 80-120 words, simple essay"""


# ============================================================================
# ENGLISH QA BUILDER — GRADE 67
# ============================================================================

class EnglishQABuilder67:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English QA Builder (67) v2.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate full lesson QA — 100 questions across 5 Parts.
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        lesson_type  = metadata.get("lesson_type", "prose")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [English QA] Generating: {lesson_title} ({lesson_type})")
        print(f"      [English QA] 5 API calls: Part I–V | 100 questions")

        unit_header = get_english_qa_header(lesson_title, class_num, unit, lesson_type)
        parts = [unit_header]

        # Call 1: Part I — MCQ Q1–Q25
        print(f"      [English QA 67] Call 1/5: Part I — MCQ Q1–Q25...")
        part1 = self._call_part1(text, class_num, unit, lesson_title, lesson_type)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ Part I ({len(part1)} chars)")
        else:
            print(f"         ❌ Part I failed")

        # Call 2: Part II — Fill Blanks Q26–Q50
        print(f"      [English QA 67] Call 2/5: Part II — Fill Blanks Q26–Q50...")
        part2 = self._call_part2(text, class_num, unit, lesson_title, lesson_type)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Part II ({len(part2)} chars)")
        else:
            print(f"         ❌ Part II failed")

        # Call 3: Part III — Short Answer Q51–Q70
        print(f"      [English QA 67] Call 3/5: Part III — Short Answer Q51–Q70...")
        part3 = self._call_part3(text, class_num, unit, lesson_title, lesson_type)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Part III ({len(part3)} chars)")
        else:
            print(f"         ❌ Part III failed")

        # Call 4: Part IV — Paragraph Q71–Q90
        print(f"      [English QA 67] Call 4/5: Part IV — Paragraph Q71–Q90...")
        part4 = self._call_part4(text, class_num, unit, lesson_title, lesson_type)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Part IV ({len(part4)} chars)")
        else:
            print(f"         ❌ Part IV failed")

        # Call 5: Part V — Extended Q91–Q100
        print(f"      [English QA 67] Call 5/5: Part V — Extended Q91–Q100...")
        part5 = self._call_part5(text, class_num, unit, lesson_title, lesson_type)
        if part5:
            parts.append(clean(part5))
            print(f"         ✅ Part V ({len(part5)} chars)")
        else:
            print(f"         ❌ Part V failed")

        if len(parts) <= 1:
            return None

        combined = "\n\n".join(parts)
        print(f"      [English QA 67] ✅ Complete — {len(parts)-1} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 1 — PART I: MCQ Q1–Q25 (1 mark each)
    # =========================================================================

    def _call_part1(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part I of the English Unit QA for Class {class_num} (Grade 6-7).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 25 MCQ questions: Q1 to Q25.
All questions SIMPLE — suitable for Class 6-7 students (11-12 years old).
All questions based ONLY on the lesson text — no invented content.

DISTRIBUTION — strictly follow:
Q1–Q10  → Vocabulary (what does this word mean? simple meanings)
Q11–Q18 → Comprehension (who/what/where — directly from text)
Q19–Q21 → Simple Grammar (identify noun/verb/adjective from a sentence)
Q22–Q24 → Simple literary device (identify rhyme/repetition/simile)
Q25     → Moral or theme (simple — what do we learn from this lesson)

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT:

<div class="qa-section" id="section-part1">
  <div class="section-header">
    <h2>Part I — Choose the Correct Answer</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-part1')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>25 × 1 Mark = 25 Marks | Q1–Q25 | Choose the correct answer</em></p>
  <p class="section-dist"><em>
    Vocabulary: Q1–Q10 | Comprehension: Q11–Q18 |
    Grammar: Q19–Q21 | Literary Device: Q22–Q24 | Moral/Theme: Q25
  </em></p>

  [25 simple MCQ questions Q1–Q25 — each with 4 options a) b) c) d)]
  [Questions must be simple enough for 11-12 year olds]
  [Correct answer ONLY inside answer-reveal div — NO tick marks]

</div>

RULES:
- EXACTLY 25 questions Q1 to Q25 — no skipping
- Keep questions SHORT and SIMPLE — under 12 words each
- All 4 options plausible but clearly only one correct
- Distributed as above
- Raw HTML only — start with <div class="qa-section" id="section-part1">
- Do NOT stop before Q25

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=GRADE67_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 67 Part I error: {e}")
            return None

    # =========================================================================
    # CALL 2 — PART II: FILL IN THE BLANKS Q26–Q50 (1 mark each)
    # =========================================================================

    def _call_part2(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part II of the English Unit QA for Class {class_num} (Grade 6-7).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 25 Fill in the Blanks: Q26 to Q50.
Sentences must come directly from the lesson text — simple and clear.
The blank replaces a key word students should know.

DISTRIBUTION — strictly follow:
Q26–Q35 → Simple vocabulary blanks (10 questions)
Q36–Q43 → Character/event blanks (8 questions)
Q44–Q50 → Simple grammar / moral completion blanks (7 questions)

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT:

<div class="qa-section" id="section-part2">
  <div class="section-header">
    <h2>Part II — Fill in the Blanks</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-part2')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>25 × 1 Mark = 25 Marks | Q26–Q50 | Fill in the blank</em></p>
  <p class="section-dist"><em>
    Vocabulary: Q26–Q35 | Character/Event: Q36–Q43 | Grammar/Moral: Q44–Q50
  </em></p>

  [25 fill-in-the-blank questions Q26–Q50]
  [Use <span class="blank-line">__________</span> for every blank]
  [Simple sentences — Class 6-7 level]

</div>

RULES:
- EXACTLY 25 questions Q26 to Q50 — no skipping
- Use <span class="blank-line">__________</span> for the blank
- Sentences must be simple and short — Class 6-7 level
- All sentences from the lesson text only
- Raw HTML only — start with <div class="qa-section" id="section-part2">
- Do NOT stop before Q50

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=GRADE67_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 67 Part II error: {e}")
            return None

    # =========================================================================
    # CALL 3 — PART III: SHORT ANSWER Q51–Q70 (2 marks each)
    # =========================================================================

    def _call_part3(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part III of the English Unit QA for Class {class_num} (Grade 6-7).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 20 questions: Q51 to Q70.
Each answer: EXACTLY 2 simple sentences. 20-40 words only.
Simple language — Class 6-7 students (11-12 years old).

DISTRIBUTION — strictly follow:
Q51–Q59 → Simple recall (9 questions)
  - Who is the main character/speaker?
  - Where does the lesson take place?
  - What happened at the beginning?
  - What does [word] mean?
  - What did [character] do?

Q60–Q65 → Simple understanding (6 questions)
  - Why did [character] feel happy/sad?
  - What is the lesson about?
  - What lesson do we learn?
  - Name one thing described in the text

Q66–Q70 → Simple personal response (5 questions)
  - Was [character] good or bad? Why?
  - Did you like the lesson? Why?
  - What feeling does the lesson give you?

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT:

<div class="qa-section" id="section-part3">
  <div class="section-header">
    <h2>Part III — Answer Briefly</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-part3')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>20 × 2 Marks = 40 Marks | Q51–Q70 | Answer in 2 simple sentences</em></p>
  <p class="section-dist"><em>
    Recall: Q51–Q59 | Understanding: Q60–Q65 | Personal Response: Q66–Q70
  </em></p>

  [20 two-mark questions Q51–Q70]
  [Each answer: exactly 2 simple sentences, 20-40 words]
  [Simple language — no complex words]

</div>

RULES:
- EXACTLY 20 questions Q51 to Q70 — no skipping
- Every answer: exactly 2 simple sentences, 20-40 words
- Simple language throughout — Class 6-7 level
- All answers inside answer-reveal div
- Raw HTML only — start with <div class="qa-section" id="section-part3">
- Do NOT stop before Q70

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=GRADE67_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 67 Part III error: {e}")
            return None

    # =========================================================================
    # CALL 4 — PART IV: PARAGRAPH Q71–Q90 (5 marks each)
    # =========================================================================

    def _call_part4(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part IV of the English Unit QA for Class {class_num} (Grade 6-7).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 20 questions: Q71 to Q90.
Each answer: EXACTLY 3-4 simple sentences, 50-80 words.
Simple paragraph — never bullet points. Class 6-7 level.

DISTRIBUTION — strictly follow:
Q71–Q80 → Retell / describe (10 questions)
  - Tell the lesson in your own words (simple retell)
  - Describe the main character
  - What happened when [key event]? Tell in your own words
  - What is the lesson about? (simple theme)
  - What did [character] do and why?

Q81–Q86 → Simple opinion / feeling (6 questions)
  - How does the lesson make you feel? Why?
  - What do you like about the lesson?
  - What did you learn from this lesson?
  - Would you like to be like [character]? Why?

Q87–Q90 → Moral / reflection (4 questions)
  - What is the moral? How can you use it in your life?
  - What part of the lesson did you like best? Why?

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT:

<div class="qa-section" id="section-part4">
  <div class="section-header">
    <h2>Part IV — Answer in Detail</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-part4')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>20 × 5 Marks = 100 Marks | Q71–Q90 | Answer in 3-4 sentences</em></p>
  <p class="section-dist"><em>
    Retell/Describe: Q71–Q80 | Opinion/Feeling: Q81–Q86 | Moral/Reflection: Q87–Q90
  </em></p>

  [20 five-mark questions Q71–Q90]
  [Each answer: 3-4 simple sentences, 50-80 words]
  [Simple paragraph — not bullet points]

</div>

RULES:
- EXACTLY 20 questions Q71 to Q90 — no skipping
- Every answer: 3-4 simple sentences, 50-80 words — proper paragraph
- Simple language throughout — Class 6-7 level
- All answers inside answer-reveal div
- Raw HTML only — start with <div class="qa-section" id="section-part4">
- Do NOT stop before Q90

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=16000,
                system=GRADE67_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 67 Part IV error: {e}")
            return None

    # =========================================================================
    # CALL 5 — PART V: EXTENDED Q91–Q100 (8 marks each)
    # =========================================================================

    def _call_part5(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part V of the English Unit QA for Class {class_num} (Grade 6-7).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 10 questions: Q91 to Q100.
Each answer: EXACTLY 6-8 simple sentences, 80-120 words.
Simple essay — Class 6-7 level. No complex analysis.

DISTRIBUTION — strictly follow:
Q91 → Reading Comprehension
  Give a short passage/stanza (3-5 lines) from the lesson text.
  Ask 4 simple sub-questions (2 marks each = 8 marks):
    a) What does [simple word] mean?
    b) Who is speaking / who did this?
    c) What happened here?
    d) What do you think about this?
  Each sub-answer: 1-2 simple sentences.

Q92 → Simple essay — Write about the main character (80-120 words)
Q93 → Simple essay — What is the lesson about? What did you learn? (80-120 words)
Q94 → Simple essay — Write about the lesson and what it says (80-120 words)
Q95 → Simple essay — Write about your favourite part of the lesson (80-120 words)
Q96 → Creative — Write 3-4 sentences: What would you do if you were [character]?
Q97 → Creative — Draw a story map in words: beginning, middle, end
Q98 → Simple — Write what you liked most about this lesson and why
Q99 → Values — What good things did you learn from this lesson?
Q100 → Reflection — How would you use this lesson's message in your own life?

{ENGLISH_ANSWER_FORMAT_RULES}

SECTION FORMAT:

<div class="qa-section" id="section-part5">
  <div class="section-header">
    <h2>Part V — Extended Writing</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-part5')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>10 × 8 Marks = 80 Marks | Q91–Q100 | Simple essay 80-120 words</em></p>
  <p class="section-dist"><em>
    Q91: Reading Comprehension | Q92–Q95: Essays |
    Q96–Q97: Creative | Q98–Q100: Values and Reflection
  </em></p>

  <!-- Q91: Reading Comprehension -->
  <div class="qa-item">
    <p class="question"><strong>Q91.</strong> Read the passage and answer the questions:
    <span class="mark-badge">(8 marks)</span></p>
    <div class="passage-block">
      <p><em>"[Extract 3-5 simple lines from the lesson text — easy to read]"</em></p>
    </div>
    <p><strong>a)</strong> What does '[simple word]' mean?</p>
    <p><strong>b)</strong> Who is speaking or who did this?</p>
    <p><strong>c)</strong> What happened here?</p>
    <p><strong>d)</strong> What do you think about this?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answers:</strong></p>
      <p><strong>a)</strong> [simple 1-sentence answer]</p>
      <p><strong>b)</strong> [simple 1-sentence answer]</p>
      <p><strong>c)</strong> [simple 1-2 sentence answer]</p>
      <p><strong>d)</strong> [simple 1-2 sentence personal response]</p>
    </div>
  </div>

  [Q92–Q100 — simple essay questions with model answers]
  [Each answer: 6-8 simple sentences, 80-120 words]
  [Use simple words throughout — Class 6-7 level]

</div>

RULES:
- EXACTLY 10 questions Q91 to Q100 — no skipping
- Q91 must include an actual passage/stanza from the lesson text
- Q92–Q100 answers: 6-8 simple sentences, 80-120 words
- Use simple language throughout — no complex words or analysis
- All answers inside answer-reveal div
- Raw HTML only — start with <div class="qa-section" id="section-part5">
- Do NOT stop before Q100

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=16000,
                system=GRADE67_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 67 Part V error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_qa_67_builder = EnglishQABuilder67()
