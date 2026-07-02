"""
english/qa/grade_910/english.py
--------------------------------
QA Builder for Samacheer Kalvi English — Classes 8, 9 & 10
Covers ALL units, ALL lesson types (Prose + Poem + Supplementary)

Follows DGE-style blueprint adapted for Tutorea (100 questions):
  Part I   → Q1–Q25    (25 × 1 mark)  — MCQ: Vocab + Grammar + Literature
  Part II  → Q26–Q50   (25 × 1 mark)  — Fill in the Blanks from all 3 texts
  Part III → Q51–Q70   (20 × 2 marks) — Short Answer: Prose + Poem + Sup
  Part IV  → Q71–Q90   (20 × 5 marks) — Essay: Prose + Poem + Sup + Writing
  Part V   → Q91–Q100  (10 × 8 marks) — Extended: Reading comp + Extended writing

Total: 100 questions across all 3 lesson components

API calls: 5 total
  Call 1 → Part I   (MCQ Q1–Q25)
  Call 2 → Part II  (Fill Blanks Q26–Q50)
  Call 3 → Part III (Short Answer Q51–Q70)
  Call 4 → Part IV  (Essay Q71–Q90)
  Call 5 → Part V   (Extended Q91–Q100)

Input (via metadata — packed by processor.py):
  metadata["prose_text"]         — extracted prose lesson text
  metadata["poem_text"]          — extracted poem text
  metadata["supplementary_text"] — extracted supplementary text
  metadata["supp_text"]          — fallback key (Option B defensive coding)

v2.0 — June 2026
Rebuilt to 100 questions — Option B structure
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
- Generate questions AND complete answers based ONLY on the lesson texts provided
- NEVER invent facts, events, quotes, or vocabulary not in the texts
- EVERY question must have a clear complete answer inside answer-reveal div
- NEVER use textarea or input boxes

QUESTION BALANCE — strictly follow across all parts:
  Prose        → ~45% of questions
  Poem         → ~25% of questions
  Supplementary → ~20% of questions
  Grammar/Writing → ~10% of questions

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
        print(f"✅ English QA Builder (910) v2.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate full unit QA — 100 questions across 5 Parts.

        text param is the prose text (fallback).
        All 3 texts come from metadata packed by processor.py.
        """
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        # Extract all 3 lesson texts — Option B defensive coding
        prose_text   = metadata.get("prose_text", "")
        poem_text    = metadata.get("poem_text", "")
        supp_text    = metadata.get("supplementary_text") or metadata.get("supp_text", "")

        # Titles
        prose_title  = metadata.get("prose_title", "Prose")
        poem_title   = metadata.get("poem_title", "Poem")
        supp_title   = metadata.get("supplementary_title", "Supplementary")

        # Fallback — if processor hasn't packed texts yet
        if not prose_text and text:
            prose_text = text
            print(f"      [English QA 910] ⚠️  Only prose_text available — poem/supp empty")

        print(f"      [English QA 910] Generating Unit {unit} QA — Class {class_num}")
        print(f"      [English QA 910] Prose: {prose_title} ({len(prose_text)} chars)")
        print(f"      [English QA 910] Poem: {poem_title} ({len(poem_text)} chars)")
        print(f"      [English QA 910] Supplementary: {supp_title} ({len(supp_text)} chars)")
        print(f"      [English QA 910] 5 API calls: Part I–V | 100 questions total")

        # Build combined context
        context = self._build_context(
            prose_text, poem_text, supp_text,
            prose_title, poem_title, supp_title
        )

        unit_header = get_english_qa_header(
            f"Unit {unit} — {prose_title} / {poem_title} / {supp_title}",
            class_num, unit, "Full Unit"
        )
        parts = [unit_header]

        # Call 1: Part I — MCQ Q1–Q25
        print(f"      [English QA 910] Call 1/5: Part I — MCQ Q1–Q25...")
        part1 = self._call_part1(context, class_num, unit, prose_title, poem_title, supp_title)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ Part I ({len(part1)} chars)")
        else:
            print(f"         ❌ Part I failed")

        # Call 2: Part II — Fill Blanks Q26–Q50
        print(f"      [English QA 910] Call 2/5: Part II — Fill Blanks Q26–Q50...")
        part2 = self._call_part2(context, class_num, unit, prose_title, poem_title, supp_title)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Part II ({len(part2)} chars)")
        else:
            print(f"         ❌ Part II failed")

        # Call 3: Part III — Short Answer Q51–Q70
        print(f"      [English QA 910] Call 3/5: Part III — Short Answer Q51–Q70...")
        part3 = self._call_part3(context, class_num, unit, prose_title, poem_title, supp_title)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Part III ({len(part3)} chars)")
        else:
            print(f"         ❌ Part III failed")

        # Call 4: Part IV — Essay Q71–Q90
        print(f"      [English QA 910] Call 4/5: Part IV — Essay Q71–Q90...")
        part4 = self._call_part4(context, class_num, unit, prose_title, poem_title, supp_title)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Part IV ({len(part4)} chars)")
        else:
            print(f"         ❌ Part IV failed")

        # Call 5: Part V — Extended Q91–Q100
        print(f"      [English QA 910] Call 5/5: Part V — Extended Q91–Q100...")
        part5 = self._call_part5(context, class_num, unit, prose_title, poem_title, supp_title)
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
    # CONTEXT BUILDER
    # =========================================================================

    def _build_context(self, prose_text, poem_text, supp_text,
                       prose_title, poem_title, supp_title) -> str:
        parts = []
        if prose_text:
            parts.append(f"═══ PROSE: {prose_title} ═══\n{prose_text}")
        if poem_text:
            parts.append(f"═══ POEM: {poem_title} ═══\n{poem_text}")
        if supp_text:
            parts.append(f"═══ SUPPLEMENTARY: {supp_title} ═══\n{supp_text}")
        return "\n\n".join(parts)

    # =========================================================================
    # CALL 1 — PART I: MCQ Q1–Q25 (1 mark each)
    # =========================================================================

    def _call_part1(self, context, class_num, unit,
                    prose_title, poem_title, supp_title) -> Optional[str]:
        try:
            prompt = f"""Generate Part I of the English Unit QA — Choose the Correct Answer.

Class {class_num} | Unit {unit}
Prose: {prose_title} | Poem: {poem_title} | Supplementary: {supp_title}

Generate EXACTLY 25 MCQ questions: Q1 to Q25.
All questions based ONLY on the lesson texts provided — no invented content.

DISTRIBUTION — strictly follow:
Q1–Q5   → Vocabulary from Prose (word meaning in context, synonym, antonym)
Q6–Q8   → Vocabulary from Poem (word meaning, poetic term, rhyme scheme)
Q9–Q10  → Vocabulary from Supplementary (word meaning in context)
Q11–Q14 → Comprehension from Prose (who/what/where/when/why)
Q15–Q17 → Comprehension from Poem (theme/mood/stanza meaning/poet intent)
Q18–Q19 → Comprehension from Supplementary (character/event/setting)
Q20–Q22 → Grammar in context (identify tense/voice/speech from prose sentences)
Q23–Q24 → Literary devices (identify alliteration/metaphor/simile/personification)
Q25     → Values/theme/HOTS (message from any lesson — higher order thinking)

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
    Prose Vocab: Q1–Q5 | Poem Vocab: Q6–Q8 | Sup Vocab: Q9–Q10 |
    Prose Comp: Q11–Q14 | Poem Comp: Q15–Q17 | Sup Comp: Q18–Q19 |
    Grammar: Q20–Q22 | Literary Devices: Q23–Q24 | HOTS: Q25
  </em></p>

  [25 MCQ questions Q1–Q25 — each with 4 options a) b) c) d)]
  [Correct answer ONLY inside answer-reveal div — NO tick marks anywhere]

</div>

RULES:
- EXACTLY 25 questions Q1 to Q25 — no skipping
- All 4 options must be plausible — only one correct
- Questions spread across Prose, Poem, Supplementary as distributed above
- Raw HTML only — start with <div class="qa-section" id="section-part1">
- Do NOT stop before Q25

Lesson Texts:
---
{context}
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

    def _call_part2(self, context, class_num, unit,
                    prose_title, poem_title, supp_title) -> Optional[str]:
        try:
            prompt = f"""Generate Part II of the English Unit QA — Fill in the Blanks.

Class {class_num} | Unit {unit}
Prose: {prose_title} | Poem: {poem_title} | Supplementary: {supp_title}

Generate EXACTLY 25 Fill in the Blanks questions: Q26 to Q50.
Every sentence must come directly from the lesson texts — exact or near-exact.
The blank must replace a key word (vocabulary, character name, key event word).

DISTRIBUTION — strictly follow:
Q26–Q35 → From Prose (10 questions)
  - Vocabulary blanks (replace difficult or important word)
  - Character name blanks (replace who said / who did)
  - Event completion (what happened / where / when)
  - Grammar-in-context blanks (verb form, preposition, article)

Q36–Q43 → From Poem (8 questions)
  - Word from poem lines (replace key word in a line)
  - Poetic term blanks (rhyme scheme, literary device name)
  - Theme or mood completion

Q44–Q50 → From Supplementary (7 questions)
  - Key event or character blanks
  - Vocabulary from story
  - Setting or moral completion

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
    Prose: Q26–Q35 | Poem: Q36–Q43 | Supplementary: Q44–Q50
  </em></p>

  [25 fill-in-the-blank questions Q26–Q50]
  [Use <span class="blank-line">__________</span> for every blank]
  [Answers inside answer-reveal div only]

</div>

RULES:
- EXACTLY 25 questions Q26 to Q50 — no skipping
- Use <span class="blank-line">__________</span> for the blank
- Raw HTML only — start with <div class="qa-section" id="section-part2">
- All sentences from lesson texts only — no invented sentences
- Distributed across Prose, Poem, Supplementary as above
- Do NOT stop before Q50

Lesson Texts:
---
{context}
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

    def _call_part3(self, context, class_num, unit,
                    prose_title, poem_title, supp_title) -> Optional[str]:
        try:
            prompt = f"""Generate Part III of the English Unit QA — Answer Briefly.

Class {class_num} | Unit {unit}
Prose: {prose_title} | Poem: {poem_title} | Supplementary: {supp_title}

Generate EXACTLY 20 questions: Q51 to Q70.
Each answer: EXACTLY 2-3 complete sentences. 30-50 words only. Never bullet points.

DISTRIBUTION — strictly follow:
Q51–Q59 → Prose (9 questions)
  - Q51: Who is the main character? Describe briefly
  - Q52: What happened when [key event]?
  - Q53: Why did [character] [action]?
  - Q54: What does the word [word] mean in this context?
  - Q55: Describe the setting of the prose
  - Q56: What is the central theme? State briefly
  - Q57: How did [character] feel when [event]?
  - Q58: What lesson do we learn from [event/character]?
  - Q59: HOTS — What would you do if you were [character]?

Q60–Q65 → Poem (6 questions)
  - Q60: What is the poem about? State briefly
  - Q61: Explain the meaning of [stanza/line] in your own words
  - Q62: Identify one literary device and explain it
  - Q63: What is the mood/tone of the poem?
  - Q64: What message does the poet convey?
  - Q65: HOTS — Do you agree with the poet's view? Why?

Q66–Q70 → Supplementary (5 questions)
  - Q66: Who are the main characters? Describe briefly
  - Q67: What is the key event in the story?
  - Q68: Why did [character] do [action]?
  - Q69: What is the moral of the story?
  - Q70: HOTS — What values does this story teach?

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
    Prose: Q51–Q59 | Poem: Q60–Q65 | Supplementary: Q66–Q70
  </em></p>

  [20 two-mark questions Q51–Q70]
  [Each answer strictly 2-3 sentences, 30-50 words — never bullet points]

</div>

RULES:
- EXACTLY 20 questions Q51 to Q70 — no skipping
- Every answer: 2-3 sentences, 30-50 words — never more, never bullet points
- All answers inside answer-reveal div
- Distributed across Prose, Poem, Supplementary as above
- Raw HTML only — start with <div class="qa-section" id="section-part3">
- Do NOT stop before Q70

Lesson Texts:
---
{context}
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

    def _call_part4(self, context, class_num, unit,
                    prose_title, poem_title, supp_title) -> Optional[str]:
        try:
            prompt = f"""Generate Part IV of the English Unit QA — Answer in Detail.

Class {class_num} | Unit {unit}
Prose: {prose_title} | Poem: {poem_title} | Supplementary: {supp_title}

Generate EXACTLY 20 questions: Q71 to Q90.
Each answer: EXACTLY 5-7 sentences, 80-120 words. Proper paragraph — never bullet points.

DISTRIBUTION — strictly follow:
Q71–Q80 → Prose (10 questions — highest weightage)
  - Q71: Summarise the prose in your own words
  - Q72: Describe the main character in detail with evidence from text
  - Q73: Explain the significance of the key event in the prose
  - Q74: What is the central theme? Explain with examples from text
  - Q75: How does [character] change/develop through the story?
  - Q76: What values does this prose teach? Explain with examples
  - Q77: Compare two characters from the prose
  - Q78: Describe the setting and how it affects the story
  - Q79: What is the author's message? Do you agree? Why?
  - Q80: HOTS — If you were [character], what would you do differently?

Q81–Q86 → Poem (6 questions)
  - Q81: Write an appreciation of the poem (theme, mood, devices, language)
  - Q82: Explain the theme of the poem with examples from the text
  - Q83: Identify and explain 3 literary devices used in the poem
  - Q84: Paraphrase the poem stanza by stanza in your own words
  - Q85: What is the poet's message? Explain with reference to the poem
  - Q86: HOTS — How does this poem relate to your own life or experience?

Q87–Q90 → Supplementary (4 questions)
  - Q87: Retell the story in your own words
  - Q88: Describe the main character and their importance to the story
  - Q89: What moral or lesson does this story teach? Explain with examples
  - Q90: HOTS — How would the story change if [key event] had not happened?

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
    Prose: Q71–Q80 | Poem: Q81–Q86 | Supplementary: Q87–Q90
  </em></p>

  [20 five-mark questions Q71–Q90]
  [Each answer strictly 5-7 sentences, 80-120 words, proper paragraph]

</div>

RULES:
- EXACTLY 20 questions Q71 to Q90 — no skipping
- Every answer: 5-7 sentences, 80-120 words — proper paragraph, never bullet points
- All answers inside answer-reveal div
- Distributed across Prose, Poem, Supplementary as above
- Raw HTML only — start with <div class="qa-section" id="section-part4">
- Do NOT stop before Q90

Lesson Texts:
---
{context}
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

    def _call_part5(self, context, class_num, unit,
                    prose_title, poem_title, supp_title) -> Optional[str]:
        try:
            prompt = f"""Generate Part V of the English Unit QA — Extended Writing.

Class {class_num} | Unit {unit}
Prose: {prose_title} | Poem: {poem_title} | Supplementary: {supp_title}

Generate EXACTLY 10 questions: Q91 to Q100.
Each answer: EXACTLY 10-12 sentences, 150-200 words. Full essay paragraph.

DISTRIBUTION — strictly follow:
Q91 → Reading Comprehension (Prose-based)
  Extract a meaningful passage (5-8 lines) from the prose.
  Ask 4 sub-questions (2 marks each = 8 marks):
    a) What does [word/phrase] mean in this context?
    b) Who said this / to whom?
    c) Why did [character] [action in passage]?
    d) What does this passage reveal about [theme/character]?
  Each sub-answer: 1-2 sentences.

Q92 → Reading Comprehension (Poem-based)
  Extract a stanza from the poem.
  Ask 4 sub-questions:
    a) Explain the meaning of this stanza
    b) Identify one literary device used here
    c) What emotion does the poet express?
    d) How does this stanza connect to the poem's theme?

Q93 → Essay — Prose theme or character (150-200 words)
Q94 → Essay — Prose moral or values (150-200 words)
Q95 → Essay — Poem appreciation (theme, mood, devices, 150-200 words)
Q96 → Essay — Poem message and relevance (150-200 words)
Q97 → Essay — Supplementary story retell with moral (150-200 words)
Q98 → Creative writing — Letter / diary entry / speech connected to any lesson theme
Q99 → Comparative essay — Connect theme across prose and poem
Q100 → HOTS — Personal reflection on values learned from this unit

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
    Q91: Reading Comp (Prose) | Q92: Reading Comp (Poem) |
    Q93–Q94: Prose Essays | Q95–Q96: Poem Essays |
    Q97: Supplementary | Q98: Creative | Q99: Comparative | Q100: Reflection
  </em></p>

  <!-- Q91: Reading Comprehension — Prose -->
  <div class="qa-item">
    <p class="question"><strong>Q91.</strong> Read the following passage and answer the questions:
    <span class="mark-badge">(8 marks)</span></p>
    <div class="passage-block">
      <p><em>"[Extract 5-8 meaningful lines from the prose lesson — exact text]"</em></p>
    </div>
    <p><strong>a)</strong> What does '[word/phrase]' mean in this context?</p>
    <p><strong>b)</strong> Who said this / to whom was this said?</p>
    <p><strong>c)</strong> Why did [character] [action from passage]?</p>
    <p><strong>d)</strong> What does this passage reveal about [theme/character]?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answers:</strong></p>
      <p><strong>a)</strong> [1-2 sentence answer]</p>
      <p><strong>b)</strong> [1-2 sentence answer]</p>
      <p><strong>c)</strong> [2-3 sentence answer]</p>
      <p><strong>d)</strong> [2-3 sentence answer connecting to theme]</p>
    </div>
  </div>

  <!-- Q92: Reading Comprehension — Poem -->
  <div class="qa-item">
    <p class="question"><strong>Q92.</strong> Read the following stanza and answer the questions:
    <span class="mark-badge">(8 marks)</span></p>
    <div class="passage-block">
      <p><em>"[Extract one complete stanza from the poem — exact lines]"</em></p>
    </div>
    <p><strong>a)</strong> Explain the meaning of this stanza in your own words.</p>
    <p><strong>b)</strong> Identify one literary device used in this stanza and explain it.</p>
    <p><strong>c)</strong> What emotion does the poet express here?</p>
    <p><strong>d)</strong> How does this stanza connect to the overall theme of the poem?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answers:</strong></p>
      <p><strong>a)</strong> [2-3 sentence paraphrase]</p>
      <p><strong>b)</strong> [device name + example + explanation]</p>
      <p><strong>c)</strong> [1-2 sentence answer]</p>
      <p><strong>d)</strong> [2-3 sentence answer]</p>
    </div>
  </div>

  [Q93–Q100 — essay and extended writing questions with full model answers]
  [Each answer: 10-12 sentences, 150-200 words, proper essay paragraph]

</div>

RULES:
- EXACTLY 10 questions Q91 to Q100 — no skipping
- Q91 and Q92 must include actual passages/stanzas from the lesson texts
- Q93–Q100 answers: 10-12 sentences, 150-200 words, proper essay paragraphs
- All answers inside answer-reveal div
- Raw HTML only — start with <div class="qa-section" id="section-part5">
- Do NOT stop before Q100

Lesson Texts:
---
{context}
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