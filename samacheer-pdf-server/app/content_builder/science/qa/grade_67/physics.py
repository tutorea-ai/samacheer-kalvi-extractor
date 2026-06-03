"""
physics.py  (QA Builder — Grade 6/7)
--------------------------------------
QA Generator for Samacheer Kalvi Science — Physics
Class 6 & 7

v1.0 — May 2026
Modeled on ss/qa/grade_67 pattern.

Split (100 questions total):
  Call 1 → Q1–Q25    MCQ
  Call 2 → Q26–Q50   Fill in the Blanks
  Call 3 → Q51–Q75   Choose Statement + Match + Detail
  Call 4 → Q76–Q100  2-mark + 5-mark

Key rules:
  - Age-appropriate for Class 6/7 (11-13 years)
  - Simple language — no complex terminology
  - Answers from chapter text only
  - Physics focus: measurements, force, motion, basic laws
  - No calculation questions — concept and observation based
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

AGE_NOTE = """
AGE-APPROPRIATE RULES — CLASS 6/7:
- Simple, clear language — 11-13 year olds
- Short questions — under 10 words
- Short answers — 1-2 sentences for 2-mark, 3-5 sentences for 5-mark
- Real-life Indian examples in questions where possible
- No complex terminology without explanation
- Physics focus: observation, measurement, basic force/motion concepts
"""


class PhysicsQA67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Physics QA Builder (67) v1.0 initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        discipline   = metadata.get("discipline", "physics")
        disc_context = DISCIPLINE_CONTEXT.get(discipline.lower(), "")

        print(f"      [Physics QA 67 v1.0] Generating: {lesson_title}")
        parts = []

        for call_num, (method, label) in enumerate([
            (self._call_mcq, "MCQ Q1–Q25"),
            (self._call_fill_blanks, "Fill Blanks Q26–Q50"),
            (self._call_statement_and_match, "Statement+Match Q51–Q75"),
            (self._call_descriptive, "Descriptive Q76–Q100"),
        ], 1):
            print(f"      [Physics QA 67] Call {call_num}/4: {label}...")
            result = method(text, lesson_title, class_num, unit, disc_context, discipline)
            if result:
                parts.append(clean(result))
                print(f"         ✅ Done ({len(result)} chars)")
            else:
                print(f"         ❌ Failed")

        if not parts:
            return None
        combined = "\n\n".join(parts)
        print(f"      [Physics QA 67 v1.0] ✅ Complete — {len(combined)} chars")
        return combined

    def _call_mcq(self, text, lesson_title, class_num, unit, disc_context, discipline) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY MCQ Q1–Q25 for Class 6/7 Physics.

{ANSWER_FORMAT_RULES}
{AGE_NOTE}

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | Physics
{disc_context}

HEADER (here only):
{get_qa_header(lesson_title, class_num, unit, discipline)}

Generate EXACTLY 25 MCQs: Q1–Q25
Distribution:
- 7 definition questions: "What is X?" / "Which of these defines Y?"
- 6 observation questions: "What happens when X?" / "Which object Y?"
- 5 unit questions: "What is the unit of X?" / "Which unit measures Y?"
- 4 classification questions: "Which type of X is Y?"
- 3 real-life questions: "Which example shows X in daily life?"

Section: id="section-mcq" | Title: "Section I — Choose the Correct Answer"
Note: 1 Mark each | Q1–Q25

RULES: Raw HTML only. 25 questions. 4 options each. No tick marks. Age-appropriate.
Every answer inside answer-reveal div with style="display:none;"

Chapter Text:
---
{text}
---
Start Q1. End Q25."""

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
            print(f"❌ Physics QA 67 MCQ error: {e}")
            return None

    def _call_fill_blanks(self, text, lesson_title, class_num, unit, disc_context, discipline) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Fill Blanks Q26–Q50 for Class 6/7 Physics.

{ANSWER_FORMAT_RULES}
{AGE_NOTE}

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | Physics
{disc_context}

Generate EXACTLY 25 Fill Blanks: Q26–Q50
Distribution:
- 7 key term blanks: "[Subject] is measured using ________"
- 6 unit blanks: "The SI unit of X is ________"
- 5 definition blanks: "The tendency of X to Y is called ________"
- 4 process blanks: "When X happens, Y ________"
- 3 scientist/law blanks: "________ Law states that X"

Section: id="section-fill" | Title: "Section II — Fill in the Blanks"
Note: 1 Mark each | Q26–Q50

RULES: Raw HTML only. 25 questions. Simple answers. Age-appropriate.

Chapter Text:
---
{text}
---
Start Q26. End Q50."""

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
            print(f"❌ Physics QA 67 Fill Blanks error: {e}")
            return None

    def _call_statement_and_match(self, text, lesson_title, class_num, unit, disc_context, discipline) -> Optional[str]:
        try:
            prompt = f"""Generate three sections: Choose Statement (Q51–Q60), Match (Q61–Q70), Detail (Q71–Q75).
Class 6/7 Physics. Age-appropriate. No repeats from Q1–Q50.

{ANSWER_FORMAT_RULES}
{AGE_NOTE}

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | Physics
{disc_context}

Q51–Q60: Choose Correct Statement (10 questions)
Each: 3 statements (i, ii, iii). One correct. Simple language for Class 6/7.
Types: definition / observation / real-life / classification statements.
Section: id="section-choose" | Title: "Section III — Choose the Correct Statement"

{QA_MATCH_INSTRUCTION}

Physics Match Pairs:
- Term → Definition / Unit → Quantity / Tool → Measurement / Law → Effect / Object → Property

Start Q51. End Q75. Raw HTML only."""

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
            print(f"❌ Physics QA 67 Statement+Match error: {e}")
            return None

    def _call_descriptive(self, text, lesson_title, class_num, unit, disc_context, discipline) -> Optional[str]:
        try:
            prompt = f"""Generate 2-mark (Q76–Q88) and 5-mark (Q89–Q100) for Class 6/7 Physics.
Age-appropriate. No repeats from Q1–Q75.

{ANSWER_FORMAT_RULES}
{AGE_NOTE}

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | Physics
{disc_context}

2-mark answers: 2-3 simple sentences. 30-50 words.
5-mark answers: 4-6 simple sentences. 60-100 words. No bullet points.

Question types: define / explain / observe / compare / give examples / real-life application

{QA_DESCRIPTIVE_INSTRUCTION}

Start Q76. End Q100. Raw HTML only.

Chapter Text:
---
{text}
---"""

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
            print(f"❌ Physics QA 67 Descriptive error: {e}")
            return None


physics_qa_67_builder = PhysicsQA67Builder()