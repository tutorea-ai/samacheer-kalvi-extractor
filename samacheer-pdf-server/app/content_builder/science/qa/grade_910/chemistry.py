"""
chemistry.py  (QA Builder)
--------------------------
QA Generator for Samacheer Kalvi Science — Chemistry
Class 9 & 10

v1.0 — May 2026
Modeled on ss/qa/grade_910/history.py structure.

Split (100 questions total):
  Call 1 → Q1–Q25    MCQ (Choose the Correct Answer)
  Call 2 → Q26–Q50   Fill in the Blanks
  Call 3 → Q51–Q75   Choose the Statement (Q51–Q60) + Match (Q61–Q70) + Detail (Q71–Q75)
  Call 4 → Q76–Q100  2-mark (Q76–Q88) + 5-mark (Q89–Q100)

Key rules:
  - All questions from chapter BODY content — not just book-back
  - Every question must have a complete answer shown
  - Answers strictly from Samacheer textbook extracted text
  - No outside knowledge or hallucination
  - Chemistry-specific: include formula, unit, and classification questions
  - No calculation questions — text/concept based only
"""

import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    SCIENCE_QA_SYSTEM_PROMPT,
    DISCIPLINE_CONTEXT,
    ANSWER_FORMAT_RULES,
    QA_DESCRIPTIVE_INSTRUCTION,
    QA_MATCH_INSTRUCTION,
    clean,
    get_qa_header,
)


class ChemistryQA910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Chemistry QA Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate 100-question Chemistry QA bank using 4 API calls.

        Call 1 → Q1–Q25   MCQ
        Call 2 → Q26–Q50  Fill in the Blanks
        Call 3 → Q51–Q75  Choose Statement + Match + Detail
        Call 4 → Q76–Q100 2-mark + 5-mark
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        discipline   = metadata.get("discipline", "chemistry")
        disc_context = DISCIPLINE_CONTEXT.get(discipline.lower(), "")

        total_calls = 4
        print(f"      [Chemistry QA 910 v1.0] Generating: {lesson_title}")
        print(f"      [Chemistry QA 910 v1.0] 4 calls → 100 questions")

        parts = []

        # ── Call 1: MCQ Q1–Q25 ────────────────────────────────────────────────
        print(f"      [Chemistry QA] Call 1/{total_calls}: MCQ (Q1–Q25)...")
        part1 = self._call_mcq(text, lesson_title, class_num, unit, disc_context, discipline)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ MCQ done ({len(part1)} chars)")
        else:
            print(f"         ❌ MCQ failed")

        # ── Call 2: Fill in the Blanks Q26–Q50 ───────────────────────────────
        print(f"      [Chemistry QA] Call 2/{total_calls}: Fill in the Blanks (Q26–Q50)...")
        part2 = self._call_fill_blanks(text, lesson_title, class_num, unit, disc_context, discipline)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Fill blanks done ({len(part2)} chars)")
        else:
            print(f"         ❌ Fill blanks failed")

        # ── Call 3: Choose Statement + Match + Detail Q51–Q75 ─────────────────
        print(f"      [Chemistry QA] Call 3/{total_calls}: Statement + Match + Detail (Q51–Q75)...")
        part3 = self._call_statement_and_match(text, lesson_title, class_num, unit, disc_context, discipline)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Statement + Match + Detail done ({len(part3)} chars)")
        else:
            print(f"         ❌ Statement + Match + Detail failed")

        # ── Call 4: 2-mark + 5-mark Q76–Q100 ─────────────────────────────────
        print(f"      [Chemistry QA] Call 4/{total_calls}: 2-mark + 5-mark (Q76–Q100)...")
        part4 = self._call_descriptive(text, lesson_title, class_num, unit, disc_context, discipline)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Descriptive done ({len(part4)} chars)")
        else:
            print(f"         ❌ Descriptive failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Chemistry QA 910 v1.0] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — MCQ Q1–Q25
    # -------------------------------------------------------------------------

    def _call_mcq(self, text, lesson_title, class_num, unit, disc_context, discipline="chemistry") -> Optional[str]:
        try:
            prompt = f"""Generate ONLY MCQ questions Q1 to Q25 for this question bank.
Do NOT generate any other question type.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
{disc_context}

Generate EXACTLY 25 MCQ questions: Q1 to Q25

ANSWER LENGTH: One complete sentence. 10-15 words only.

SOURCE RULE:
- Questions from WITHIN the chapter body — paragraphs, definitions, formulas, properties
- NOT just from book-back exercise questions
- Spread across the FULL chapter — beginning, middle, and end
- Answers strictly from the chapter text — no outside knowledge

CHEMISTRY MCQ DISTRIBUTION (spread across 25 questions):
- 6 definition questions: "Which of the following defines X?"
- 5 formula / unit questions: "What is the unit of X?" / "Which formula represents Y?"
- 5 classification questions: "Which type of X is Y?" / "Y belongs to which category?"
- 5 property / reaction questions: "What happens when X reacts with Y?"
- 4 reason / application questions: "Why is X used as a standard?" / "Where is X applied?"

HEADER (include only here — not in other calls):
{get_qa_header(lesson_title, class_num, unit, discipline)}

Section: id="section-mcq" | Title: "Section I — Choose the Correct Answer" | Note: 1 Mark each | Q1–Q25
Use MCQ format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q1 through Q25
- Every question has 4 options — NO tick marks anywhere
- Every question has complete answer shown inside answer-reveal div
- No calculation questions — concept and text-based only
- Do NOT stop before Q25

Chapter Text:
---
{text}
---

Start at Q1. End at Q25."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=8000,
                system=SCIENCE_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Chemistry QA MCQ error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 2 — Fill in the Blanks Q26–Q50
    # -------------------------------------------------------------------------

    def _call_fill_blanks(self, text, lesson_title, class_num, unit, disc_context, discipline="chemistry") -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Fill in the Blank questions Q26 to Q50.
Do NOT generate MCQ, match, or descriptive questions.
Do NOT repeat any fact already tested in Q1–Q25.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
{disc_context}

Generate EXACTLY 25 Fill in the Blank questions: Q26 to Q50

ANSWER LENGTH: One word, symbol, formula, or short phrase only.

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different facts from Q1–Q25
- Spread across the full chapter
- Answers strictly from chapter text

CHEMISTRY FILL BLANK DISTRIBUTION (spread across 25 questions):
- 6 key term blanks: "[Term] is defined as ________"
- 5 formula blanks: "The formula for X is ________"
- 5 unit blanks: "The SI unit of X is ________"
- 5 property blanks: "X is ________ in nature" / "X has a ________ structure"
- 4 value / number blanks: "Avogadro's number is ________" /
  "The atomic mass of X is ________"

Section: id="section-fill" | Title: "Section II — Fill in the Blanks" | Note: 1 Mark each | Q26–Q50
Use Fill in the Blanks format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q26 through Q50
- Blank must be a key word, formula, unit, or value from the chapter
- Answer shown clearly inside answer-reveal div
- Vary blank positions — not always at the end of the sentence
- Cover different topics from across the full chapter
- Do NOT stop before Q50

Chapter Text:
---
{text}
---

Start at Q26. End at Q50."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=8000,
                system=SCIENCE_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Chemistry QA Fill Blanks error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 3 — Choose the Statement (Q51–Q60) + Match (Q61–Q70) + Detail (Q71–Q75)
    # -------------------------------------------------------------------------

    def _call_statement_and_match(self, text, lesson_title, class_num, unit, disc_context, discipline="chemistry") -> Optional[str]:
        try:
            prompt = f"""Generate three sections in order:
  1. Choose the Correct Statement (Q51–Q60)
  2. Match the Following (Q61–Q70)
  3. Answer in Detail — Short (Q71–Q75)

Do NOT generate MCQ, fill blanks, or long descriptive questions.
Do NOT repeat any fact already tested in Q1–Q50.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
{disc_context}

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different facts from Q1–Q50
- Answers strictly from chapter text

══════════════════════════════════════
PART A: Choose the Correct Statement Q51–Q60
══════════════════════════════════════

Generate EXACTLY 10 questions: Q51 to Q60

Each question: Give 3 statements (i, ii, iii). Only ONE is correct.
Student must identify the correct statement.

CHEMISTRY STATEMENT TYPES (distribute across 10 questions):
- 3 theory statements: one correct fact about a scientific law or theory
- 3 property statements: one correct property of an element or compound
- 2 formula / relationship statements: one correct formula or relationship
- 2 classification statements: one correct classification of a substance

Section: id="section-choose" | Title: "Section III — Choose the Correct Statement"
Note: 1 Mark each | Q51–Q60
Use Choose the Correct Statement format from ANSWER FORMAT RULES above.

{QA_MATCH_INSTRUCTION}

Chapter Text:
---
{text}
---

Start at Q51. End at Q75.
Structure:
- Q51–Q60: Choose the Correct Statement (10 questions)
- Q61–Q70: Match the Following (2 sets of 5 pairs)
- Q71–Q75: Answer in Detail — Short (5 questions, 2 marks each)
Do NOT stop before Q75."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=8000,
                system=SCIENCE_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Chemistry QA Statement + Match error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 4 — 2-mark (Q76–Q88) + 5-mark (Q89–Q100)
    # -------------------------------------------------------------------------

    def _call_descriptive(self, text, lesson_title, class_num, unit, disc_context, discipline="chemistry") -> Optional[str]:
        try:
            prompt = f"""Generate two sections: 2-mark questions (Q76–Q88) and 5-mark questions (Q89–Q100).
Do NOT generate MCQ, fill blanks, or statement questions.
Do NOT repeat facts already tested in Q1–Q75.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
{disc_context}

SOURCE RULE:
- Questions from WITHIN the chapter body
- Each question covers a DIFFERENT major topic from the chapter
- Answers strictly from chapter text — no outside knowledge
- No calculation questions — concept, definition, explanation only

{QA_DESCRIPTIVE_INSTRUCTION}

Chapter Text:
---
{text}
---

Start at Q76. End at Q100."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=12000,
                system=SCIENCE_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Chemistry QA Descriptive error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

chemistry_qa_910_builder = ChemistryQA910Builder()