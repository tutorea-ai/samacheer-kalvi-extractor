"""
physics.py  (QA Builder)
------------------------
QA Generator for Samacheer Kalvi Science — Physics
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
  - Physics-specific: laws, formulas, units, definitions, derivations,
    numerical concepts, real-world applications
  - No calculation questions — concept and text-based only
  - Formula questions test recognition and meaning — not solving
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


class PhysicsQA910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Physics QA Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate 100-question Physics QA bank using 4 API calls.

        Call 1 → Q1–Q25   MCQ
        Call 2 → Q26–Q50  Fill in the Blanks
        Call 3 → Q51–Q75  Choose Statement + Match + Detail
        Call 4 → Q76–Q100 2-mark + 5-mark
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        discipline   = metadata.get("discipline", "physics")
        disc_context = DISCIPLINE_CONTEXT.get(discipline.lower(), "")

        total_calls = 4
        print(f"      [Physics QA 910 v1.0] Generating: {lesson_title}")
        print(f"      [Physics QA 910 v1.0] 4 calls → 100 questions")

        parts = []

        # ── Call 1: MCQ Q1–Q25 ────────────────────────────────────────────────
        print(f"      [Physics QA] Call 1/{total_calls}: MCQ (Q1–Q25)...")
        part1 = self._call_mcq(text, lesson_title, class_num, unit, disc_context, discipline)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ MCQ done ({len(part1)} chars)")
        else:
            print(f"         ❌ MCQ failed")

        # ── Call 2: Fill in the Blanks Q26–Q50 ───────────────────────────────
        print(f"      [Physics QA] Call 2/{total_calls}: Fill in the Blanks (Q26–Q50)...")
        part2 = self._call_fill_blanks(text, lesson_title, class_num, unit, disc_context, discipline)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Fill blanks done ({len(part2)} chars)")
        else:
            print(f"         ❌ Fill blanks failed")

        # ── Call 3: Choose Statement + Match + Detail Q51–Q75 ─────────────────
        print(f"      [Physics QA] Call 3/{total_calls}: Statement + Match + Detail (Q51–Q75)...")
        part3 = self._call_statement_and_match(text, lesson_title, class_num, unit, disc_context, discipline)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Statement + Match + Detail done ({len(part3)} chars)")
        else:
            print(f"         ❌ Statement + Match + Detail failed")

        # ── Call 4: 2-mark + 5-mark Q76–Q100 ─────────────────────────────────
        print(f"      [Physics QA] Call 4/{total_calls}: 2-mark + 5-mark (Q76–Q100)...")
        part4 = self._call_descriptive(text, lesson_title, class_num, unit, disc_context, discipline)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Descriptive done ({len(part4)} chars)")
        else:
            print(f"         ❌ Descriptive failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Physics QA 910 v1.0] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — MCQ Q1–Q25
    # -------------------------------------------------------------------------

    def _call_mcq(self, text, lesson_title, class_num, unit,
                  disc_context, discipline="physics") -> Optional[str]:
        try:
            prompt = f"""Generate ONLY MCQ questions Q1 to Q25 for this question bank.
Do NOT generate any other question type.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
{disc_context}

Generate EXACTLY 25 MCQ questions: Q1 to Q25

ANSWER LENGTH: One complete sentence. 10-15 words only.

SOURCE RULE:
- Questions from WITHIN the chapter body — paragraphs, definitions, laws, formulas
- NOT just from book-back exercise questions
- Spread across the FULL chapter — beginning, middle, and end
- Answers strictly from the chapter text — no outside knowledge
- NEVER invent formulas or values not in the chapter text

PHYSICS MCQ DISTRIBUTION (spread across 25 questions):
- 5 law / principle questions:
    "Which law states that...?" / "Newton's [X] Law says...?"
- 5 definition questions:
    "What is the definition of X?" / "Which term describes Y?"
- 5 formula / unit questions:
    "What is the SI unit of X?" / "Which formula represents Y?"
    Questions test RECOGNITION of formula — not calculation
- 4 scientist / discovery questions:
    "Who formulated X?" / "Which scientist discovered Y?"
- 4 application questions:
    "Which principle explains X?" / "What happens to Y when Z?"
- 2 vector / scalar questions (ONLY if chapter mentions vector/scalar):
    "Is X a scalar or vector quantity?" / "Which of these is a vector?"

HEADER (include only here — not in other calls):
{get_qa_header(lesson_title, class_num, unit, discipline)}

Section: id="section-mcq" | Title: "Section I — Choose the Correct Answer"
Note: 1 Mark each | Q1–Q25
Use MCQ format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q1 through Q25
- Every question has 4 options — NO tick marks anywhere
- Every question has complete answer shown inside answer-reveal div
- No calculation questions — concept and recognition based only
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
            print(f"❌ Physics QA MCQ error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 2 — Fill in the Blanks Q26–Q50
    # -------------------------------------------------------------------------

    def _call_fill_blanks(self, text, lesson_title, class_num, unit,
                          disc_context, discipline="physics") -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Fill in the Blank questions Q26 to Q50.
Do NOT generate MCQ, match, or descriptive questions.
Do NOT repeat any fact already tested in Q1–Q25.

{ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {discipline.title()}
{disc_context}

Generate EXACTLY 25 Fill in the Blank questions: Q26 to Q50

ANSWER LENGTH: One physics term, law name, formula symbol, unit, or short phrase only.

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different facts from Q1–Q25
- Spread across the full chapter
- Answers strictly from chapter text
- NEVER invent formulas, values, or terms not in the chapter

PHYSICS FILL BLANK DISTRIBUTION (spread across 25 questions):
- 6 law / principle name blanks:
    "The law that states X is called ________"
    "________ Law says that every action has an equal and opposite reaction"
- 5 formula symbol blanks:
    "The formula for X is written as ________"
    "In the formula F = ma, 'a' stands for ________"
- 5 unit blanks:
    "The SI unit of force is ________"
    "Momentum is measured in ________"
- 5 definition / term blanks:
    "The tendency of a body to resist change in its state is called ________"
    "________ is defined as the rate of change of linear momentum"
- 4 scientist / value blanks:
    "The universal gravitational constant G was discovered by ________"
    "The value of acceleration due to gravity on Earth is ________ m/s²"

Section: id="section-fill" | Title: "Section II — Fill in the Blanks"
Note: 1 Mark each | Q26–Q50
Use Fill in the Blanks format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q26 through Q50
- Blank must be a key physics term, law name, formula symbol, or unit from chapter
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
            print(f"❌ Physics QA Fill Blanks error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 3 — Choose the Statement (Q51–Q60) + Match (Q61–Q70) + Detail (Q71–Q75)
    # -------------------------------------------------------------------------

    def _call_statement_and_match(self, text, lesson_title, class_num, unit,
                                  disc_context, discipline="physics") -> Optional[str]:
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
- NEVER invent formulas or values not in the chapter

══════════════════════════════════════
PART A: Choose the Correct Statement Q51–Q60
══════════════════════════════════════

Generate EXACTLY 10 questions: Q51 to Q60

Each question: Give 3 statements (i, ii, iii). Only ONE is correct.
Student must identify the correct statement.

PHYSICS STATEMENT TYPES (distribute across 10 questions):
- 3 law statements:
    One correct statement about a physics law or principle
    (other two have wrong conditions or wrong relationships)
- 3 formula / relationship statements:
    One correct formula relationship
    (other two have inverted or wrong relationships)
- 2 application statements:
    One correct real-world application of a physics concept
- 2 definition statements:
    One correct definition of a physics term
    (other two have wrong or incomplete definitions)

Section: id="section-choose" | Title: "Section III — Choose the Correct Statement"
Note: 1 Mark each | Q51–Q60
Use Choose the Correct Statement format from ANSWER FORMAT RULES above.

{QA_MATCH_INSTRUCTION}

PHYSICS MATCH PAIRS — use these types:
- Law → Scientist pairs (e.g. Law of Gravitation → Newton)
- Formula → Quantity pairs (e.g. F = ma → Force)
- Term → Definition pairs (e.g. Inertia → Tendency to resist change)
- Unit → Physical quantity pairs (e.g. Newton → Force)
- Concept → Real-life example pairs (e.g. Rocket propulsion → Newton's 3rd Law)

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
            print(f"❌ Physics QA Statement + Match error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 4 — 2-mark (Q76–Q88) + 5-mark (Q89–Q100)
    # -------------------------------------------------------------------------

    def _call_descriptive(self, text, lesson_title, class_num, unit,
                          disc_context, discipline="physics") -> Optional[str]:
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
- No calculation questions — concept, definition, explanation, derivation only
- NEVER invent formulas or values not in the chapter

PHYSICS DESCRIPTIVE QUESTION TYPES — distribute across both sections:
- Law statement: "State Newton's [X] Law of Motion"
- Definition: "Define X and give one example from daily life"
- Derivation concept: "How is F = ma derived from Newton's Second Law?"
  (answer explains the steps — not a calculation)
- Comparison: "Distinguish between X and Y" (scalar/vector, mass/weight etc.)
- Application: "Explain how X works using [law/principle]"
- Real-life: "Why does X happen? Explain using [concept]"
- Scientist contribution: "What was [Scientist]'s contribution to [topic]?"

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
            print(f"❌ Physics QA Descriptive error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

physics_qa_910_builder = PhysicsQA910Builder()