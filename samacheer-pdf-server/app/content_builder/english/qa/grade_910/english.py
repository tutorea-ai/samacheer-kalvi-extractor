"""
english/qa/grade_910/english.py
--------------------------------
QA Builder for Samacheer Kalvi English — Classes 8, 9 & 10
Single lesson at a time (Prose OR Poem OR Supplementary — per unit/lesson_choice)

Follows DGE-style blueprint adapted for Tutorea (100 questions):
  Part I   → Q1–Q25    (25 × 1 mark)  — MCQ: Vocab + Grammar + Literature
  Part II  → Q26–Q50   (25 × 1 mark)  — Fill in the Blanks
  Part III → Q51–Q70   (20 × 2 marks) — Short Answer
  Part IV  → Q71–Q90   (20 × 5 marks) — Essay
  Part V   → Q91–Q100  (10 × 8 marks) — Extended: Reading comp + Extended writing

Total: 100 questions

API calls: 5 total
  Call 1 → Part I   (MCQ Q1–Q25)
  Call 2 → Part II  (Fill Blanks Q26–Q50)
  Call 3 → Part III (Short Answer Q51–Q70)
  Call 4 → Part IV  (Essay Q71–Q90)
  Call 5 → Part V   (Extended Q91–Q100)

v3.0 — July 2026
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
# DGE-STYLE SYSTEM PROMPT
# ============================================================================

DGE_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi English examiner
creating a question bank following the DGE-style blueprint for Classes 8, 9 and 10
Tamil Nadu state board.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags
- Generate questions AND complete answers based ONLY on the lesson text provided
- NEVER invent facts, events, quotes, or vocabulary not in the text
- EVERY question must have a clear complete answer inside answer-reveal div
- NEVER use textarea or input boxes

QUESTION COMPOSITION — strictly follow across all parts:
  Vocabulary          → ~20% of questions
  Comprehension       → ~40% of questions
  Grammar in context  → ~15% of questions
  Literary devices    → ~15% of questions
  Values/HOTS/theme   → ~10% of questions

KNOWLEDGE LEVELS — distribute within each section:
  Knowledge (recall)      → 30%
  Understanding (explain) → 40%
  HOTS (analyse/evaluate) → 30%

ANSWER LENGTH RULES:
  1-mark  → one word, one phrase, or one short sentence
  2-mark  → exactly 2-3 sentences, 30-50 words
  5-mark  → exactly 5-7 sentences, 80-120 words, proper paragraph
  8-mark  → exactly 10-12 sentences, 150-200 words, full essay paragraph"""


# ============================================================================
# ENGLISH QA BUILDER — GRADE 910
# ============================================================================

class EnglishQABuilder910:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English QA Builder (910) v3.0 initialized — model: {self.model}")

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
        print(f"      [English QA 910] Call 1/5: Part I — MCQ Q1–Q25...")
        part1 = self._call_part1(text, class_num, unit, lesson_title, lesson_type)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ Part I ({len(part1)} chars)")
        else:
            print(f"         ❌ Part I failed")

        # Call 2: Part II — Fill Blanks Q26–Q50
        print(f"      [English QA 910] Call 2/5: Part II — Fill Blanks Q26–Q50...")
        part2 = self._call_part2(text, class_num, unit, lesson_title, lesson_type)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Part II ({len(part2)} chars)")
        else:
            print(f"         ❌ Part II failed")

        # Call 3: Part III — Short Answer Q51–Q70
        print(f"      [English QA 910] Call 3/5: Part III — Short Answer Q51–Q70...")
        part3 = self._call_part3(text, class_num, unit, lesson_title, lesson_type)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Part III ({len(part3)} chars)")
        else:
            print(f"         ❌ Part III failed")

        # Call 4: Part IV — Essay Q71–Q90
        print(f"      [English QA 910] Call 4/5: Part IV — Essay Q71–Q90...")
        part4 = self._call_part4(text, class_num, unit, lesson_title, lesson_type)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Part IV ({len(part4)} chars)")
        else:
            print(f"         ❌ Part IV failed")

        # Call 5: Part V — Extended Q91–Q100
        print(f"      [English QA 910] Call 5/5: Part V — Extended Q91–Q100...")
        part5 = self._call_part5(text, class_num, unit, lesson_title, lesson_type)
        if part5:
            parts.append(clean(part5))
            print(f"         ✅ Part V ({len(part5)} chars)")
        else:
            print(f"         ❌ Part V failed")

        if len(parts) <= 1:
            return None

        combined = "\n\n".join(parts)
        print(f"      [English QA 910] ✅ Complete — {len(parts)-1} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 1 — PART I: MCQ Q1–Q25 (1 mark each)
    # =========================================================================

    def _call_part1(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part I of the English Unit QA — Choose the Correct Answer.

Class {class_num} | Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 25 MCQ questions: Q1 to Q25.
All questions based ONLY on the lesson text provided — no invented content.

DISTRIBUTION — strictly follow:
Q1–Q10  → Vocabulary (word meaning in context, synonym, antonym)
Q11–Q18 → Comprehension (who/what/where/when/why, theme, mood)
Q19–Q21 → Grammar in context (identify tense/voice/speech from text sentences)
Q22–Q24 → Literary devices (identify alliteration/metaphor/simile/personification)
Q25     → Values/theme/HOTS (message from the lesson — higher order thinking)

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
    Grammar: Q19–Q21 | Literary Devices: Q22–Q24 | HOTS: Q25
  </em></p>

  [25 MCQ questions Q1–Q25 — each with 4 options a) b) c) d)]
  [Correct answer ONLY inside answer-reveal div — NO tick marks anywhere]

</div>

RULES:
- EXACTLY 25 questions Q1 to Q25 — no skipping
- All 4 options must be plausible — only one correct
- Questions distributed as above
- Raw HTML only — start with <div class="qa-section" id="section-part1">
- Do NOT stop before Q25

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=DGE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 Part I error: {e}")
            return None

    # =========================================================================
    # CALL 2 — PART II: FILL IN THE BLANKS Q26–Q50 (1 mark each)
    # =========================================================================

    def _call_part2(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part II of the English Unit QA — Fill in the Blanks.

Class {class_num} | Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 25 Fill in the Blanks questions: Q26 to Q50.
Every sentence must come directly from the lesson text — exact or near-exact.
The blank must replace a key word (vocabulary, character name, key event word).

DISTRIBUTION — strictly follow:
Q26–Q35 → Vocabulary blanks (replace difficult or important word)
Q36–Q43 → Character/event blanks (who said / who did / what happened)
Q44–Q50 → Grammar-in-context blanks (verb form, preposition, article)

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
    Vocabulary: Q26–Q35 | Character/Event: Q36–Q43 | Grammar: Q44–Q50
  </em></p>

  [25 fill-in-the-blank questions Q26–Q50]
  [Use <span class="blank-line">__________</span> for every blank]
  [Answers inside answer-reveal div only]

</div>

RULES:
- EXACTLY 25 questions Q26 to Q50 — no skipping
- Use <span class="blank-line">__________</span> for the blank
- Raw HTML only — start with <div class="qa-section" id="section-part2">
- All sentences from the lesson text only — no invented sentences
- Do NOT stop before Q50

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=DGE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 Part II error: {e}")
            return None

    # =========================================================================
    # CALL 3 — PART III: SHORT ANSWER Q51–Q70 (2 marks each)
    # =========================================================================

    def _call_part3(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part III of the English Unit QA — Answer Briefly.

Class {class_num} | Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 20 questions: Q51 to Q70.
Each answer: EXACTLY 2-3 complete sentences. 30-50 words only. Never bullet points.

DISTRIBUTION — strictly follow:
Q51–Q58 → Knowledge/recall (8 questions)
  - Who/what/where/when questions directly from the text
  - Word meanings in context
  - Describe the setting/character briefly

Q59–Q66 → Understanding/explain (8 questions)
  - Why did [character] [action]?
  - What is the central theme? State briefly
  - Explain a literary device used in the text
  - What message does the lesson convey?

Q67–Q70 → HOTS (4 questions)
  - What would you do if you were [character]?
  - Do you agree with [viewpoint in the text]? Why?
  - What values does this lesson teach?
  - How does this lesson relate to real life?

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
  <p class="section-note"><em>20 × 2 Marks = 40 Marks | Q51–Q70 | Answer in 2-3 sentences</em></p>
  <p class="section-dist"><em>
    Knowledge: Q51–Q58 | Understanding: Q59–Q66 | HOTS: Q67–Q70
  </em></p>

  [20 two-mark questions Q51–Q70]
  [Each answer strictly 2-3 sentences, 30-50 words — never bullet points]

</div>

RULES:
- EXACTLY 20 questions Q51 to Q70 — no skipping
- Every answer: 2-3 sentences, 30-50 words — never more, never bullet points
- All answers inside answer-reveal div
- Distributed as above
- Raw HTML only — start with <div class="qa-section" id="section-part3">
- Do NOT stop before Q70

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=14000,
                system=DGE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 Part III error: {e}")
            return None

    # =========================================================================
    # CALL 4 — PART IV: ESSAY Q71–Q90 (5 marks each)
    # =========================================================================

    def _call_part4(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part IV of the English Unit QA — Answer in Detail.

Class {class_num} | Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 20 questions: Q71 to Q90.
Each answer: EXACTLY 5-7 sentences, 80-120 words. Proper paragraph — never bullet points.

DISTRIBUTION — strictly follow:
Q71–Q76 → Knowledge/Understanding essays (6 questions)
  - Summarise the lesson in your own words
  - Describe the main character in detail with evidence from text
  - Explain the significance of the key event
  - What is the central theme? Explain with examples from text
  - Describe the setting and how it affects the lesson
  - Explain a literary device used and its effect

Q77–Q84 → Analysis/Evaluation essays (8 questions)
  - How does [character] change/develop through the lesson?
  - What values does this lesson teach? Explain with examples
  - Compare two characters/ideas from the lesson
  - What is the author's/poet's message? Do you agree? Why?
  - Analyse the structure/technique used in the lesson
  - Discuss the mood/tone and how it is created
  - Explain how the title connects to the content
  - Critically examine one key decision/action in the lesson

Q85–Q90 → HOTS/creative essays (6 questions)
  - If you were [character], what would you do differently?
  - How does this lesson relate to your own life or experience?
  - What would change if [key event] had not happened?
  - Write a short creative response connected to the lesson's theme
  - Evaluate the relevance of this lesson today
  - What is the most important lesson learnt? Why?

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
  <p class="section-note"><em>20 × 5 Marks = 100 Marks | Q71–Q90 | Answer in 5-7 sentences</em></p>
  <p class="section-dist"><em>
    Knowledge/Understanding: Q71–Q76 | Analysis/Evaluation: Q77–Q84 | HOTS/Creative: Q85–Q90
  </em></p>

  [20 five-mark questions Q71–Q90]
  [Each answer strictly 5-7 sentences, 80-120 words, proper paragraph]

</div>

RULES:
- EXACTLY 20 questions Q71 to Q90 — no skipping
- Every answer: 5-7 sentences, 80-120 words — proper paragraph, never bullet points
- All answers inside answer-reveal div
- Distributed as above
- Raw HTML only — start with <div class="qa-section" id="section-part4">
- Do NOT stop before Q90

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=18000,
                system=DGE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 Part IV error: {e}")
            return None

    # =========================================================================
    # CALL 5 — PART V: EXTENDED Q91–Q100 (8 marks each)
    # =========================================================================

    def _call_part5(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part V of the English Unit QA — Extended Writing.

Class {class_num} | Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 10 questions: Q91 to Q100.
Each answer: EXACTLY 10-12 sentences, 150-200 words. Full essay paragraph.

DISTRIBUTION — strictly follow:
Q91 → Reading Comprehension
  Extract a meaningful passage/stanza (5-8 lines) from the lesson text.
  Ask 4 sub-questions (2 marks each = 8 marks):
    a) What does [word/phrase] mean in this context?
    b) Who said this / to whom, or what is being described?
    c) Why did [character/event] happen?
    d) What does this passage reveal about [theme/character]?
  Each sub-answer: 1-2 sentences.

Q92 → Essay — Theme or character analysis (150-200 words)
Q93 → Essay — Moral or values conveyed (150-200 words)
Q94 → Essay — Appreciation (style, tone, devices, language, 150-200 words)
Q95 → Essay — Message and relevance to modern life (150-200 words)
Q96 → Essay — Retell/summarise the lesson with critical comment (150-200 words)
Q97 → Creative writing — Letter / diary entry / speech connected to the lesson's theme
Q98 → Comparative essay — Connect the lesson's theme to another lesson or real life
Q99 → Essay — Analyse a key literary/narrative technique used (150-200 words)
Q100 → HOTS — Personal reflection on values learned from this lesson

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
  <p class="section-note"><em>10 × 8 Marks = 80 Marks | Q91–Q100 | Extended writing 150-200 words</em></p>
  <p class="section-dist"><em>
    Q91: Reading Comprehension | Q92–Q96: Essays |
    Q97: Creative | Q98: Comparative | Q99: Technique Analysis | Q100: Reflection
  </em></p>

  <!-- Q91: Reading Comprehension -->
  <div class="qa-item">
    <p class="question"><strong>Q91.</strong> Read the following passage and answer the questions:
    <span class="mark-badge">(8 marks)</span></p>
    <div class="passage-block">
      <p><em>"[Extract 5-8 meaningful lines from the lesson text — exact text]"</em></p>
    </div>
    <p><strong>a)</strong> What does '[word/phrase]' mean in this context?</p>
    <p><strong>b)</strong> Who said this / to whom was this said, or what is being described?</p>
    <p><strong>c)</strong> Why did [character/event] happen?</p>
    <p><strong>d)</strong> What does this passage reveal about [theme/character]?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answers:</strong></p>
      <p><strong>a)</strong> [1-2 sentence answer]</p>
      <p><strong>b)</strong> [1-2 sentence answer]</p>
      <p><strong>c)</strong> [2-3 sentence answer]</p>
      <p><strong>d)</strong> [2-3 sentence answer connecting to theme]</p>
    </div>
  </div>

  [Q92–Q100 — essay and extended writing questions with full model answers]
  [Each answer: 10-12 sentences, 150-200 words, proper essay paragraph]

</div>

RULES:
- EXACTLY 10 questions Q91 to Q100 — no skipping
- Q91 must include an actual passage/stanza from the lesson text
- Q92–Q100 answers: 10-12 sentences, 150-200 words, proper essay paragraphs
- All answers inside answer-reveal div
- Raw HTML only — start with <div class="qa-section" id="section-part5">
- Do NOT stop before Q100

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=18000,
                system=DGE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 910 Part V error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_qa_910_builder = EnglishQABuilder910()
