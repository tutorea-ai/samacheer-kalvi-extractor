"""
economics.py  (QA Builder)
--------------------------
QA Generator for Samacheer Kalvi Social Science — Economics
Class 6 & 7

v1.0 — Adapted from grade_67 civics QA (June 2026)

Split (100 questions total):
  Call 1 → Q1–Q25    MCQ (Choose the Correct Answer)
  Call 2 → Q26–Q50   Fill in the Blanks
  Call 3 → Q51–Q70   Choose the Statement (Q51-Q60) + Match the Following (Q61-Q70)
  Call 4 → Q71–Q100  2-mark (Q71-Q85) + 5-mark (Q86-Q100)

Key rules:
  - All questions from chapter BODY content — not just book-back
  - Every question must have a complete answer shown
  - Answers strictly from Samacheer textbook extracted text
  - No outside knowledge or hallucination
  - Match questions: two separate sets of 5 pairs each
  - Age-appropriate language for Class 6/7 (11-13 years)
  - Class 6/7 Economics: basic needs, resources, livelihoods, markets
  - NO complex economic jargon — simple, clear vocabulary
"""

import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    SS_QA_SYSTEM_PROMPT,
    DISCIPLINE_CONTEXT,
    ANSWER_FORMAT_RULES,
    QA_DESCRIPTIVE_INSTRUCTION,
    QA_MATCH_INSTRUCTION,
    clean,
    get_qa_header,
)


class EconomicsQA67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Economics QA Builder (67) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate 100-question Economics QA bank using 4 API calls.

        Call 1 → Q1–Q25   MCQ
        Call 2 → Q26–Q50  Fill in the Blanks
        Call 3 → Q51–Q70  Choose Statement + Match
        Call 4 → Q71–Q100 2-mark + 5-mark
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        discipline   = metadata.get("discipline", "economics")
        disc_context = DISCIPLINE_CONTEXT.get(discipline.lower(), "")

        total_calls = 4
        print(f"      [Economics QA 67 v1] Generating: {lesson_title}")
        print(f"      [Economics QA 67 v1] 4 calls → 100 questions (2-mark:15, 5-mark:15)")

        parts = []

        # ── Call 1: MCQ Q1–Q25 ────────────────────────────────────────────────
        print(f"      [Economics QA] Call 1/{total_calls}: MCQ (Q1–Q25)...")
        part1 = self._call_mcq(text, lesson_title, class_num, unit, disc_context, discipline)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ MCQ done ({len(part1)} chars)")
        else:
            print(f"         ❌ MCQ failed")

        # ── Call 2: Fill in the Blanks Q26–Q50 ───────────────────────────────
        print(f"      [Economics QA] Call 2/{total_calls}: Fill in the Blanks (Q26–Q50)...")
        part2 = self._call_fill_blanks(text, lesson_title, class_num, unit, disc_context, discipline)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Fill blanks done ({len(part2)} chars)")
        else:
            print(f"         ❌ Fill blanks failed")

        # ── Call 3: Choose Statement + Match Q51–Q70 ──────────────────────────
        print(f"      [Economics QA] Call 3/{total_calls}: Statement + Match (Q51–Q70)...")
        part3 = self._call_statement_and_match(text, lesson_title, class_num, unit, disc_context, discipline)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Statement + Match done ({len(part3)} chars)")
        else:
            print(f"         ❌ Statement + Match failed")

        # ── Call 4: 2-mark + 5-mark Q71–Q100 ─────────────────────────────────
        print(f"      [Economics QA] Call 4/{total_calls}: 2-mark + 5-mark (Q71–Q100)...")
        part4 = self._call_descriptive(text, lesson_title, class_num, unit, disc_context, discipline)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Descriptive done ({len(part4)} chars)")
        else:
            print(f"         ❌ Descriptive failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Economics QA 67 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — MCQ Q1–Q25
    # -------------------------------------------------------------------------

    def _call_mcq(self, text, lesson_title, class_num, unit, disc_context, discipline="economics") -> Optional[str]:
        try:
            prompt = f"""Generate ONLY MCQ questions Q1 to Q25 for this question bank.
Do NOT generate any other question type.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
Note    : Class 6/7 — basic needs, resources, livelihoods, markets.
          Use age-appropriate, simple language for questions and answers.
{disc_context}

Generate EXACTLY 25 MCQ questions: Q1 to Q25

ANSWER LENGTH: One complete sentence. 10-15 words only.

SOURCE RULE:
- Questions from WITHIN the chapter body — paragraphs, facts, examples
- NOT just from book-back exercise questions
- Spread across the FULL chapter — beginning, middle, and end
- Answers strictly from the chapter text — no outside knowledge
- Simple language appropriate for Class 6/7

CLASS 6/7 ECONOMICS QUESTION TYPES — distribute evenly:
- Definition questions: What are basic needs? What is a market?
- Example questions: Which is an example of a natural resource?
- Livelihood questions: How do farmers earn their living?
- Trade questions: What happens in a market?
- Resource questions: What is the difference between renewable and non-renewable resources?

HEADER (include only here — not in other calls):
{get_qa_header(lesson_title, class_num, unit, discipline)}

Section: id="section-mcq" | Title: "Section I — Choose the Correct Answer" | Note: 1 Mark each | Q1–Q25
Use MCQ format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q1 through Q25
- Every question has 4 options — NO tick marks
- Every question has complete answer shown inside answer-reveal
- Simple vocabulary appropriate for Class 6/7
- Do NOT stop before Q25

Chapter Text:
---
{text}
---

Start at Q1. End at Q25."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=8000,
                system=SS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Economics QA 67 MCQ error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 2 — Fill in the Blanks Q26–Q50
    # -------------------------------------------------------------------------

    def _call_fill_blanks(self, text, lesson_title, class_num, unit, disc_context, discipline="economics") -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Fill in the Blank questions Q26 to Q50.
Do NOT generate MCQ, match, or descriptive questions.
Do NOT repeat any fact already tested in Q1–Q25.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
Note    : Class 6/7 — basic needs, resources, livelihoods, markets.
          Use age-appropriate, simple language.
{disc_context}

Generate EXACTLY 25 Fill in the Blank questions: Q26 to Q50

ANSWER LENGTH: One word or short phrase only.

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different facts from Q1–Q25
- Spread across the full chapter
- Answers strictly from chapter text
- Simple vocabulary appropriate for Class 6/7

CLASS 6/7 ECONOMICS BLANK TYPES:
- Key terms: Food, shelter, and clothing are called _______ needs
- Resources: Water and soil are examples of _______ resources
- Livelihoods: People who grow crops are called _______
- Markets: The place where goods are bought and sold is called a _______

Section: id="section-fill" | Title: "Section II — Fill in the Blanks" | Note: 1 Mark each | Q26–Q50
Use Fill in the Blanks format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q26 through Q50
- Blank must be a key term or concept from the chapter
- Answer shown clearly inside answer-reveal
- Vary blank positions — not always at the end
- Simple vocabulary throughout
- Do NOT stop before Q50

Chapter Text:
---
{text}
---

Start at Q26. End at Q50."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=8000,
                system=SS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Economics QA 67 Fill Blanks error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 3 — Choose the Statement (Q51–Q60) + Match (Q61–Q70)
    # -------------------------------------------------------------------------

    def _call_statement_and_match(self, text, lesson_title, class_num, unit, disc_context, discipline="economics") -> Optional[str]:
        try:
            prompt = f"""Generate two sections: Choose the Statement (Q51–Q60) and Match the Following (Q61–Q70).
Do NOT generate MCQ, fill blanks, or descriptive questions.
Do NOT repeat any fact already tested in Q1–Q50.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
Note    : Class 6/7 — basic needs, resources, livelihoods, markets.
          Use age-appropriate, simple language.
{disc_context}

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different facts from Q1–Q50
- Answers strictly from chapter text
- Simple vocabulary appropriate for Class 6/7

══════════════════════════════════════
PART A: Choose the Correct Statement Q51–Q60
══════════════════════════════════════

Generate EXACTLY 10 questions: Q51 to Q60

Each question: Give 3 statements (i, ii, iii). Only ONE is correct.
Student must identify the correct statement.
Keep statements simple and clear for Class 6/7.

CLASS 6/7 ECONOMICS STATEMENT TYPES:
- Resource statements: "Coal is a non-renewable resource because..."
- Livelihood statements: "Farmers depend on the land because..."
- Market statements: "In a market, buyers and sellers..."
- Needs statements: "Basic needs are important because..."

Section: id="section-choose" | Title: "Section III — Choose the Correct Statement" | Note: 1 Mark each | Q51–Q60
Use Choose the Correct Statement format from ANSWER FORMAT RULES above.

══════════════════════════════════════
PART B: Match the Following Q61–Q70
══════════════════════════════════════

{QA_MATCH_INSTRUCTION}

CLASS 6/7 ECONOMICS MATCH THEMES:
- Set 1 (Q61): Match key economic terms to their meanings
- Set 2 (Q66): Match livelihoods/occupations to their products OR resources to their types
- Keep matching items simple for Class 6/7

RULES:
- Raw HTML only — no markdown, no code fences
- Choose Statement: EXACTLY 10 questions Q51–Q60
- All answers inside answer-reveal div — NO individual show buttons
- Do NOT stop before Q70

Chapter Text:
---
{text}
---

Start at Q51. End at Q75.
Structure:
- Q51-Q60: Choose the Correct Statement (10 questions)
- Q61-Q70: Match the Following (2 sets of 5 pairs)
- Q71-Q75: Answer in Detail — 5 short detail questions (2 marks each)
Do NOT stop before Q75."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=8000,
                system=SS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Economics QA 67 Statement + Match error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 4 — 2-mark (Q71–Q85) + 5-mark (Q86–Q100)
    # -------------------------------------------------------------------------

    def _call_descriptive(self, text, lesson_title, class_num, unit, disc_context, discipline="economics") -> Optional[str]:
        try:
            prompt = f"""Generate two sections: 2-mark questions (Q76–Q88) and 5-mark questions (Q89–Q100).
Do NOT generate MCQ, fill blanks, or statement questions.
Do NOT repeat facts already tested in Q1–Q75.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
Note    : Class 6/7 — basic needs, resources, livelihoods, markets.
          Use age-appropriate, simple language.
{disc_context}

SOURCE RULE:
- Questions from WITHIN the chapter body
- Each question covers a DIFFERENT major topic from the chapter
- Answers strictly from chapter text — no outside knowledge
- Simple, clear language appropriate for Class 6/7 students

CLASS 6/7 ECONOMICS QUESTION FOCUS:
- What are the basic needs of human beings?
- What is the difference between renewable and non-renewable resources?
- How do people earn their livelihoods?
- What is the role of markets in our daily life?
- Why is it important to save and use resources wisely?

{QA_DESCRIPTIVE_INSTRUCTION}

Chapter Text:
---
{text}
---

Start at Q76. End at Q100."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=12000,
                system=SS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Economics QA 67 Descriptive error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

economics_qa_67_builder = EconomicsQA67Builder()
