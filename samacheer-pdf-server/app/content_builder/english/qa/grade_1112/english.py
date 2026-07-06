"""
english/qa/grade_1112/english.py
---------------------------------
QA Builder for Samacheer Kalvi English — Classes 11 & 12
Single lesson at a time (Prose OR Poem OR Supplementary — per unit/lesson_choice)

Follows Higher Secondary blueprint (same structure, analytical content):
  Part I   → Q1–Q25    (25 × 1 mark)  — MCQ: Vocab + Grammar + Literary + Analytical
  Part II  → Q26–Q50   (25 × 1 mark)  — Fill in the Blanks
  Part III → Q51–Q70   (20 × 2 marks) — Short Answer: explanation + inference
  Part IV  → Q71–Q90   (20 × 5 marks) — Essay: analysis + appreciation + evaluation
  Part V   → Q91–Q100  (10 × 8 marks) — Extended: critical analysis + creative writing

Total: 100 questions — analytical, HOTS-heavy, exam-focused

API calls: 5 total
  Call 1 → Part I   (MCQ Q1–Q25)
  Call 2 → Part II  (Fill Blanks Q26–Q50)
  Call 3 → Part III (Short Answer Q51–Q70)
  Call 4 → Part IV  (Essay Q71–Q90)
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
# GRADE 1112 QA SYSTEM PROMPT
# ============================================================================

GRADE1112_QA_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi English examiner
creating a question bank for Classes 11 and 12 Tamil Nadu state board Higher Secondary students.

Students are preparing for public board examinations. Questions must be analytical,
inference-based, and exam-focused.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags
- Generate questions AND answers based ONLY on the lesson text provided
- NEVER invent facts, events, quotes, or vocabulary not in the text
- EVERY question must have a complete model answer inside answer-reveal div
- NEVER use textarea or input boxes

QUESTION DIFFICULTY — CLASS 11-12 LEVEL:
- Higher Order Thinking Skills (HOTS) must dominate — 40% of questions
- Literary analysis, critical thinking, inference, evaluation
- Questions must prepare students for actual board examination style
- Vocabulary questions must test nuanced understanding and usage

QUESTION COMPOSITION — strictly follow across all parts:
  Vocabulary          → ~20% of questions
  Comprehension       → ~40% of questions
  Grammar in context  → ~15% of questions
  Literary devices    → ~15% of questions
  Critical thinking/HOTS → ~10% of questions

KNOWLEDGE LEVELS:
  Knowledge (recall)      → 20%
  Understanding (explain) → 40%
  HOTS (analyse/evaluate/create) → 40%

ANSWER LENGTH RULES:
  1-mark  → one precise word, phrase, or grammatically complete sentence
  2-mark  → exactly 2-3 analytical sentences, 40-60 words
  5-mark  → exactly 5-7 sentences, 100-140 words, well-structured paragraph
  8-mark  → exactly 10-14 sentences, 180-250 words, analytical essay"""


# ============================================================================
# ENGLISH QA BUILDER — GRADE 1112
# ============================================================================

class EnglishQABuilder1112:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ English QA Builder (1112) v2.0 initialized — model: {self.model}")

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
        print(f"      [English QA 1112] Call 1/5: Part I — MCQ Q1–Q25...")
        part1 = self._call_part1(text, class_num, unit, lesson_title, lesson_type)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ Part I ({len(part1)} chars)")
        else:
            print(f"         ❌ Part I failed")

        # Call 2: Part II — Fill Blanks Q26–Q50
        print(f"      [English QA 1112] Call 2/5: Part II — Fill Blanks Q26–Q50...")
        part2 = self._call_part2(text, class_num, unit, lesson_title, lesson_type)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Part II ({len(part2)} chars)")
        else:
            print(f"         ❌ Part II failed")

        # Call 3: Part III — Short Answer Q51–Q70
        print(f"      [English QA 1112] Call 3/5: Part III — Short Answer Q51–Q70...")
        part3 = self._call_part3(text, class_num, unit, lesson_title, lesson_type)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Part III ({len(part3)} chars)")
        else:
            print(f"         ❌ Part III failed")

        # Call 4: Part IV — Essay Q71–Q90
        print(f"      [English QA 1112] Call 4/5: Part IV — Essay Q71–Q90...")
        part4 = self._call_part4(text, class_num, unit, lesson_title, lesson_type)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Part IV ({len(part4)} chars)")
        else:
            print(f"         ❌ Part IV failed")

        # Call 5: Part V — Extended Q91–Q100
        print(f"      [English QA 1112] Call 5/5: Part V — Extended Q91–Q100...")
        part5 = self._call_part5(text, class_num, unit, lesson_title, lesson_type)
        if part5:
            parts.append(clean(part5))
            print(f"         ✅ Part V ({len(part5)} chars)")
        else:
            print(f"         ❌ Part V failed")

        if len(parts) <= 1:
            return None

        combined = "\n\n".join(parts)
        print(f"      [English QA 1112] ✅ Complete — {len(parts)-1} parts, {len(combined)} chars")
        return combined

    # =========================================================================
    # CALL 1 — PART I: MCQ Q1–Q25 (1 mark each)
    # =========================================================================

    def _call_part1(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part I of the English Unit QA for Class {class_num} (Grade 11-12).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 25 MCQ questions: Q1 to Q25.
Higher Secondary level — analytical, inference-based, exam-focused.
All questions based ONLY on the lesson text — no invented content.

DISTRIBUTION — strictly follow:
Q1–Q10  → Vocabulary (nuanced meanings, connotation, usage in context, figurative language)
Q11–Q18 → Comprehension (inference, implication, author's/poet's intent, theme, imagery)
Q19–Q21 → Grammar in context (identify/correct tense/voice/speech/clause from text)
Q22–Q24 → Literary devices (identify and name device — metaphor/irony/symbolism etc.)
Q25     → Critical thinking (evaluate theme/values/relevance of the lesson — HOTS)

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

  [25 analytical MCQ questions Q1–Q25 — each with 4 options a) b) c) d)]
  [Higher Secondary level — questions test inference and analysis]
  [Correct answer ONLY inside answer-reveal div — NO tick marks]

</div>

RULES:
- EXACTLY 25 questions Q1 to Q25 — no skipping
- Questions must be analytical — not just factual recall
- All 4 options must be plausible — requires careful reading to choose correctly
- Distributed as above
- Raw HTML only — start with <div class="qa-section" id="section-part1">
- Do NOT stop before Q25

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=GRADE1112_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 1112 Part I error: {e}")
            return None

    # =========================================================================
    # CALL 2 — PART II: FILL IN THE BLANKS Q26–Q50 (1 mark each)
    # =========================================================================

    def _call_part2(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part II of the English Unit QA for Class {class_num} (Grade 11-12).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 25 Fill in the Blanks: Q26 to Q50.
Higher Secondary level — sentences from the text, blanks test precise knowledge.

DISTRIBUTION — strictly follow:
Q26–Q35 → Vocabulary in context (10 questions)
  - Literary device name blanks
  - Key vocabulary in context
  - Author's/poet's technique blanks

Q36–Q43 → Character/theme blanks (8 questions)
  - Character trait or motivation blanks
  - Theme or imagery completion
  - Tone or mood blanks

Q44–Q50 → Grammar-in-context blanks (7 questions)
  - Narrative/technique blanks
  - Thematic vocabulary blanks

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
    Vocabulary: Q26–Q35 | Character/Theme: Q36–Q43 | Grammar: Q44–Q50
  </em></p>

  [25 fill-in-the-blank questions Q26–Q50]
  [Use <span class="blank-line">__________</span> for every blank]
  [Higher Secondary level — precise, analytical blanks]

</div>

RULES:
- EXACTLY 25 questions Q26 to Q50 — no skipping
- Use <span class="blank-line">__________</span> for the blank
- Sentences from the lesson text — blanks test analytical knowledge
- Distributed as above
- Raw HTML only — start with <div class="qa-section" id="section-part2">
- Do NOT stop before Q50

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=12000,
                system=GRADE1112_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 1112 Part II error: {e}")
            return None

    # =========================================================================
    # CALL 3 — PART III: SHORT ANSWER Q51–Q70 (2 marks each)
    # =========================================================================

    def _call_part3(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part III of the English Unit QA for Class {class_num} (Grade 11-12).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 20 questions: Q51 to Q70.
Each answer: EXACTLY 2-3 analytical sentences, 40-60 words.
Higher Secondary level — inference, analysis, critical thinking.

DISTRIBUTION — strictly follow:
Q51–Q59 → Knowledge/Understanding (9 questions)
  - Explain the significance of [key event or symbol]
  - What does [word/phrase] reveal about [character/theme]?
  - Analyse the author's/poet's use of [technique] in [passage]
  - What is the implied meaning of [statement]?
  - How does [character's] behaviour reflect the theme?

Q60–Q65 → Analysis (6 questions)
  - Explain the irony/conflict in [situation]
  - What is the social/moral message of the lesson?
  - Explain the tone with supporting evidence
  - What does [symbol/image] represent?

Q66–Q70 → HOTS (5 questions)
  - Compare two characters/ideas briefly
  - Evaluate the relevance of this lesson to modern life
  - How does the language create a particular effect?
  - Evaluate the moral relevance of the lesson

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
  <p class="section-note"><em>20 × 2 Marks = 40 Marks | Q51–Q70 | Answer in 2-3 analytical sentences</em></p>
  <p class="section-dist"><em>
    Knowledge/Understanding: Q51–Q59 | Analysis: Q60–Q65 | HOTS: Q66–Q70
  </em></p>

  [20 two-mark analytical questions Q51–Q70]
  [Each answer: 2-3 sentences, 40-60 words — analytical, not just factual]

</div>

RULES:
- EXACTLY 20 questions Q51 to Q70 — no skipping
- Every answer: 2-3 analytical sentences, 40-60 words
- Answers must demonstrate analysis — not just recall
- All answers inside answer-reveal div
- Raw HTML only — start with <div class="qa-section" id="section-part3">
- Do NOT stop before Q70

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=14000,
                system=GRADE1112_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 1112 Part III error: {e}")
            return None

    # =========================================================================
    # CALL 4 — PART IV: ESSAY Q71–Q90 (5 marks each)
    # =========================================================================

    def _call_part4(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part IV of the English Unit QA for Class {class_num} (Grade 11-12).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 20 questions: Q71 to Q90.
Each answer: EXACTLY 5-7 analytical sentences, 100-140 words.
Well-structured paragraph — never bullet points. Higher Secondary board exam style.

DISTRIBUTION — strictly follow:
Q71–Q80 → Analysis essays (10 questions)
  - Critically analyse the theme of the lesson with textual evidence
  - Examine the character/speaker — traits, development, significance
  - Analyse the author's/poet's technique and its effect
  - Discuss the social/historical context reflected in the lesson
  - How does the author/poet use [symbol/motif] to convey meaning?
  - Evaluate the values portrayed in this lesson
  - Compare the attitudes of two characters/ideas
  - Analyse the climax/turning point — how does it resolve the central conflict?
  - What is the author's/poet's message? How effectively is it conveyed?
  - HOTS — Critically evaluate the relevance of this lesson today

Q81–Q86 → Appreciation essays (6 questions)
  - Write a critical appreciation of the lesson
  - Analyse the use of imagery and its thematic significance
  - Discuss the structure and form of the lesson and their effect
  - Examine the tone and mood — how do they develop through the lesson?
  - Analyse three literary devices and explain their effect

Q87–Q90 → HOTS essays (4 questions)
  - Critically analyse the plot/argument structure
  - Discuss the theme and its relevance to contemporary society
  - HOTS — Evaluate the moral and philosophical message of the lesson
  - HOTS — How does this lesson reflect the author's/poet's worldview?

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
  <p class="section-note"><em>20 × 5 Marks = 100 Marks | Q71–Q90 | Analytical essay 100-140 words</em></p>
  <p class="section-dist"><em>
    Analysis: Q71–Q80 | Appreciation: Q81–Q86 | HOTS: Q87–Q90
  </em></p>

  [20 five-mark analytical essay questions Q71–Q90]
  [Each answer: 5-7 sentences, 100-140 words — well-structured analytical paragraph]

</div>

RULES:
- EXACTLY 20 questions Q71 to Q90 — no skipping
- Every answer: 5-7 analytical sentences, 100-140 words — proper paragraph
- Answers must include textual evidence and analysis
- All answers inside answer-reveal div
- Raw HTML only — start with <div class="qa-section" id="section-part4">
- Do NOT stop before Q90

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=18000,
                system=GRADE1112_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 1112 Part IV error: {e}")
            return None

    # =========================================================================
    # CALL 5 — PART V: EXTENDED Q91–Q100 (8 marks each)
    # =========================================================================

    def _call_part5(self, text, class_num, unit, lesson_title, lesson_type) -> Optional[str]:
        try:
            prompt = f"""Generate Part V of the English Unit QA for Class {class_num} (Grade 11-12).

Unit {unit} | Lesson: {lesson_title} ({lesson_type})

Generate EXACTLY 10 questions: Q91 to Q100.
Each answer: EXACTLY 10-14 analytical sentences, 180-250 words.
Critical essay — Higher Secondary board exam standard.

DISTRIBUTION — strictly follow:
Q91 → Critical Reading (8 marks)
  Extract a significant passage/stanza (6-10 lines) from the lesson text.
  Ask 4 analytical sub-questions (2 marks each):
    a) What does [complex word/phrase] connote in this context?
    b) Identify and explain the literary device used here
    c) What does this passage reveal about [theme/character/society]?
    d) How does this passage contribute to the overall meaning of the lesson?

Q92 → Critical essay — Analyse the theme of the lesson (180-250 words)
Q93 → Critical essay — Evaluate the characterisation/speaker's voice (180-250 words)
Q94 → Critical appreciation — Full literary appreciation of the lesson (180-250 words)
Q95 → Critical essay — The author's/poet's technique and its effect (180-250 words)
Q96 → Critical essay — Narrative/argumentative craft in the lesson (180-250 words)
Q97 → Comparative essay — Connect the lesson's theme to another lesson or real life
Q98 → Creative/argumentative — Write a critical response to [theme/issue from lesson]
Q99 → Reflection — How does this lesson contribute to your understanding of [universal theme]?
Q100 → HOTS — Critically evaluate the enduring relevance of this lesson

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
  <p class="section-note"><em>10 × 8 Marks = 80 Marks | Q91–Q100 | Critical essay 180-250 words</em></p>
  <p class="section-dist"><em>
    Q91: Critical Reading | Q92–Q96: Critical Essays |
    Q97: Comparative | Q98: Argumentative | Q99–Q100: Reflection/HOTS
  </em></p>

  <!-- Q91: Critical Reading -->
  <div class="qa-item">
    <p class="question"><strong>Q91.</strong> Read the passage carefully and answer the questions:
    <span class="mark-badge">(8 marks)</span></p>
    <div class="passage-block">
      <p><em>"[Extract 6-10 significant lines from the lesson text — rich in literary technique]"</em></p>
    </div>
    <p><strong>a)</strong> What does '[complex word/phrase]' connote in this context?</p>
    <p><strong>b)</strong> Identify and explain the literary device used in this passage.</p>
    <p><strong>c)</strong> What does this passage reveal about [theme/character/society]?</p>
    <p><strong>d)</strong> How does this passage contribute to the overall meaning of the lesson?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answers:</strong></p>
      <p><strong>a)</strong> [precise analytical answer — connotation explained]</p>
      <p><strong>b)</strong> [device named + explained + effect]</p>
      <p><strong>c)</strong> [2-3 sentence analytical answer with evidence]</p>
      <p><strong>d)</strong> [2-3 sentence answer linking to overall theme/structure]</p>
    </div>
  </div>

  [Q92–Q100 — critical essays with full model answers]
  [Each answer: 10-14 sentences, 180-250 words — analytical essay standard]
  [Include textual evidence in every essay answer]

</div>

RULES:
- EXACTLY 10 questions Q91 to Q100 — no skipping
- Q91 must include an actual passage/stanza from the lesson text
- Q92–Q100 answers: 10-14 sentences, 180-250 words — analytical essays
- Every essay must include textual evidence and critical analysis
- All answers inside answer-reveal div
- Raw HTML only — start with <div class="qa-section" id="section-part5">
- Do NOT stop before Q100

Lesson Text ({lesson_type.title()}: {lesson_title}):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model, max_tokens=18000,
                system=GRADE1112_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ English QA 1112 Part V error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

english_qa_1112_builder = EnglishQABuilder1112()
