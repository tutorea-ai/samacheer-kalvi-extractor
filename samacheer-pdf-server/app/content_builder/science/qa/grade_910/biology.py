"""
biology.py  (QA Builder)
------------------------
QA Generator for Samacheer Kalvi Science — Biology
Class 8, 9 & 10

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
  - Biology-specific: structure, function, classification, diagram-label,
    process, comparison (Dicot vs Monocot) question types
  - No calculation questions except RQ if present in chapter
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


class BiologyQA910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Biology QA Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate 100-question Biology QA bank using 4 API calls.

        Call 1 → Q1–Q25   MCQ
        Call 2 → Q26–Q50  Fill in the Blanks
        Call 3 → Q51–Q75  Choose Statement + Match + Detail
        Call 4 → Q76–Q100 2-mark + 5-mark
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        discipline   = metadata.get("discipline", "biology")
        disc_context = DISCIPLINE_CONTEXT.get(discipline.lower(), "")

        total_calls = 4
        print(f"      [Biology QA 910 v1.0] Generating: {lesson_title}")
        print(f"      [Biology QA 910 v1.0] 4 calls → 100 questions")

        parts = []

        # ── Call 1: MCQ Q1–Q25 ────────────────────────────────────────────────
        print(f"      [Biology QA] Call 1/{total_calls}: MCQ (Q1–Q25)...")
        part1 = self._call_mcq(text, lesson_title, class_num, unit, disc_context, discipline)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ MCQ done ({len(part1)} chars)")
        else:
            print(f"         ❌ MCQ failed")

        # ── Call 2: Fill in the Blanks Q26–Q50 ───────────────────────────────
        print(f"      [Biology QA] Call 2/{total_calls}: Fill in the Blanks (Q26–Q50)...")
        part2 = self._call_fill_blanks(text, lesson_title, class_num, unit, disc_context, discipline)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Fill blanks done ({len(part2)} chars)")
        else:
            print(f"         ❌ Fill blanks failed")

        # ── Call 3: Choose Statement + Match + Detail Q51–Q75 ─────────────────
        print(f"      [Biology QA] Call 3/{total_calls}: Statement + Match + Detail (Q51–Q75)...")
        part3 = self._call_statement_and_match(text, lesson_title, class_num, unit, disc_context, discipline)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Statement + Match + Detail done ({len(part3)} chars)")
        else:
            print(f"         ❌ Statement + Match + Detail failed")

        # ── Call 4: 2-mark + 5-mark Q76–Q100 ─────────────────────────────────
        print(f"      [Biology QA] Call 4/{total_calls}: 2-mark + 5-mark (Q76–Q100)...")
        part4 = self._call_descriptive(text, lesson_title, class_num, unit, disc_context, discipline)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Descriptive done ({len(part4)} chars)")
        else:
            print(f"         ❌ Descriptive failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Biology QA 910 v1.0] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — MCQ Q1–Q25
    # -------------------------------------------------------------------------

    def _call_mcq(self, text, lesson_title, class_num, unit, disc_context, discipline="biology") -> Optional[str]:
        try:
            prompt = f"""Generate ONLY MCQ questions Q1 to Q25 for this question bank.
Do NOT generate any other question type.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
{disc_context}

Generate EXACTLY 25 MCQ questions: Q1 to Q25

ANSWER LENGTH: One complete sentence. 10-15 words only.

SOURCE RULE:
- Questions from WITHIN the chapter body — paragraphs, definitions, structures, functions
- NOT just from book-back exercise questions
- Spread across the FULL chapter — beginning, middle, and end
- Answers strictly from the chapter text — no outside knowledge

BIOLOGY MCQ DISTRIBUTION (spread across 25 questions):
- 6 structure identification questions:
    "Which structure is responsible for X?" / "What is the name of Y in a plant cell?"
- 5 function questions:
    "What is the function of X?" / "What does Y do in Z?"
- 5 classification questions:
    "Which type of tissue is X?" / "How is Y classified?"
- 4 comparison questions:
    "What distinguishes Dicot X from Monocot X?" / "Which feature is found in Y but not Z?"
- 3 process questions:
    "Where does X reaction take place?" / "Which stage of Y produces Z?"
- 2 scientist / discovery questions:
    "Who is known as the Father of X?" / "Who discovered Y?"

HEADER (include only here — not in other calls):
{get_qa_header(lesson_title, class_num, unit, discipline)}

Section: id="section-mcq" | Title: "Section I — Choose the Correct Answer" | Note: 1 Mark each | Q1–Q25
Use MCQ format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q1 through Q25
- Every question has 4 options — NO tick marks anywhere
- Every question has complete answer shown inside answer-reveal div
- Spread questions across all major sections of the chapter
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
            print(f"❌ Biology QA MCQ error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 2 — Fill in the Blanks Q26–Q50
    # -------------------------------------------------------------------------

    def _call_fill_blanks(self, text, lesson_title, class_num, unit, disc_context, discipline="biology") -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Fill in the Blank questions Q26 to Q50.
Do NOT generate MCQ, match, or descriptive questions.
Do NOT repeat any fact already tested in Q1–Q25.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
{disc_context}

Generate EXACTLY 25 Fill in the Blank questions: Q26 to Q50

ANSWER LENGTH: One biological term, structure name, or short phrase only.

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different facts from Q1–Q25
- Spread across the full chapter
- Answers strictly from chapter text

BIOLOGY FILL BLANK DISTRIBUTION (spread across 25 questions):
- 6 structure name blanks:
    "The waterproof band in root endodermis is called ________"
- 5 function blanks:
    "________ cells in monocot leaves help the leaf roll inward during drought"
- 5 scientist / term blanks:
    "________ is known as the Father of Plant Anatomy"
- 5 location blanks:
    "Glycolysis occurs in the ________"
    "The Light Reaction takes place in the ________"
- 4 classification blanks:
    "Plastids that store starch and oils are called ________"

Section: id="section-fill" | Title: "Section II — Fill in the Blanks" | Note: 1 Mark each | Q26–Q50
Use Fill in the Blanks format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q26 through Q50
- Blank must be a key biological term, structure, or scientist name from the chapter
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
            print(f"❌ Biology QA Fill Blanks error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 3 — Choose the Statement (Q51–Q60) + Match (Q61–Q70) + Detail (Q71–Q75)
    # -------------------------------------------------------------------------

    def _call_statement_and_match(self, text, lesson_title, class_num, unit, disc_context, discipline="biology") -> Optional[str]:
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

BIOLOGY STATEMENT TYPES (distribute across 10 questions):
- 3 structure-function statements:
    One correct statement about what a biological structure does
- 3 comparison statements:
    One correct statement about Dicot vs Monocot difference
- 2 process statements:
    One correct statement about where/how a biological process occurs
- 2 classification statements:
    One correct statement about which type/category something belongs to

Section: id="section-choose" | Title: "Section III — Choose the Correct Statement"
Note: 1 Mark each | Q51–Q60
Use Choose the Correct Statement format from ANSWER FORMAT RULES above.

{QA_MATCH_INSTRUCTION}

BIOLOGY MATCH PAIRS — use these types:
- Structure → Function pairs (e.g. Casparian Strip → Blocks apoplast pathway)
- Scientist → Discovery pairs (e.g. Nehemiah Grew → Father of Plant Anatomy)
- Organelle → Location pairs (e.g. Krebs Cycle → Mitochondrial Matrix)
- Structure → Plant type pairs (e.g. Bulliform Cells → Monocot Leaf)
- Process → Product pairs (e.g. Light Reaction → ATP and NADPH)

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
            print(f"❌ Biology QA Statement + Match error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 4 — 2-mark (Q76–Q88) + 5-mark (Q89–Q100)
    # -------------------------------------------------------------------------

    def _call_descriptive(self, text, lesson_title, class_num, unit, disc_context, discipline="biology") -> Optional[str]:
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

BIOLOGY DESCRIPTIVE QUESTION TYPES — distribute across both sections:
- Structure-function: "Explain the function of X in Y"
- Comparison: "Distinguish between Dicot X and Monocot X" (table or points)
- Process: "Describe the steps of X" / "Explain how X occurs"
- Diagram-based (text): "Name and describe the parts of X"
- Microscopic Detective: "A plant slide shows X features. Identify and justify."
- Scientist contribution: "Who discovered X and what was their contribution?"

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
            print(f"❌ Biology QA Descriptive error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

biology_qa_910_builder = BiologyQA910Builder()