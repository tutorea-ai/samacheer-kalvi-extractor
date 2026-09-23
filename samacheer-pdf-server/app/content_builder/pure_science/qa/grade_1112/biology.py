"""
biology.py (QA)
----------------
QA Builder for Samacheer Kalvi Biology — Class 11 & 12
Disciplines: Botany and Zoology (same file, per team decision — same
pattern as the LP builder in biology/lp/grade_1112/biology.py)

v0.1 — Sept 2026

MARK-TIER PATTERN (confirmed — NOT SS's MCQ/Fill/Match/Detail split):
  1 mark  — MCQ                              x40
  2 marks — answer in 1-2 sentences          x25
  3 marks — answer in 3-5 sentences          x20
  5 marks — detailed answer + diagram        x15
  Total: 100 questions, 225 marks

CALL STRUCTURE (4 calls, one per tier):
  Call 1 → MCQ            Q1-Q40
  Call 2 → 2-mark         Q41-Q65
  Call 3 → 3-mark         Q66-Q85
  Call 4 → 5-mark+diagram Q86-Q100

SOURCE OF TRUTH: raw chapter text only — independent of the LP pipeline
(no dependency on day_structures.py or the LP's Chapter Analyser output).
Confirmed Sept 2026: QA and LP are fully separate builders.

DIAGRAMS (Call 4 only): generated as inline SVG for every 5-mark question
that calls for one — no topic-gating (Punnett-square-simple through
anatomically-complex all get auto-generated for now). This is a
deliberate first-pass decision: ship and let the testing team's review
of real output drive any per-topic restriction, rather than pre-solving
diagram-accuracy tiering before seeing real results. See conversation
history for the three-tier accuracy test (Punnett square: reliable;
mitosis: conceptually correct but label-incomplete; nephron: structurally
vague) that informed this call — testing team's findings supersede that
informal assessment.

TAMIL: none. Matches SS QA's English-only pattern. Flag if a future
requirement needs Tamil for specific vocabulary.
"""

import json
import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    BIO_QA_SYSTEM_PROMPT,
    BIO_ANSWER_FORMAT_RULES,
    QA_MARK_SPLIT,
    get_qa_header,
    clean,
)


# ============================================================================
# SHARED BUILDER LOGIC — Botany and Zoology use identical call logic;
# only discipline name differs (for logging/header context).
# ============================================================================

class _BiologyQA1112Base:
    """
    Shared implementation for Botany and Zoology QA builders.
    Subclasses set self.discipline for logging/prompt context only —
    all method logic is identical, same pattern as the LP builder.
    """

    discipline: str = "biology"  # overridden by subclasses

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ {self.discipline.title()} QA Builder (1112) v0.1 initialized — model: {self.model}")

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [{self.discipline.title()} QA 1112] Generating: {lesson_title}")
        print(f"      [{self.discipline.title()} QA 1112] 4 calls: "
              f"MCQ(1-40) + 2mark(41-65) + 3mark(66-85) + 5mark(86-100)")

        parts = [get_qa_header(lesson_title, class_num, unit, self.discipline)]

        # Call 1 — MCQ
        print(f"      [{self.discipline}] Call 1: MCQ (Q1-Q40)...")
        mcq_html = self._call_mcq(text, lesson_title, class_num, unit)
        if mcq_html:
            parts.append(clean(mcq_html))
            print(f"         ✅ MCQ ({len(mcq_html)} chars)")
        else:
            print(f"         ❌ MCQ failed — aborting")
            return None

        # Call 2 — 2-mark
        print(f"      [{self.discipline}] Call 2: 2-mark (Q41-Q65)...")
        mark2_html = self._call_mark2(text, lesson_title, class_num, unit)
        if mark2_html:
            parts.append(clean(mark2_html))
            print(f"         ✅ 2-mark ({len(mark2_html)} chars)")
        else:
            print(f"         ❌ 2-mark failed — continuing")

        # Call 3 — 3-mark
        print(f"      [{self.discipline}] Call 3: 3-mark (Q66-Q85)...")
        mark3_html = self._call_mark3(text, lesson_title, class_num, unit)
        if mark3_html:
            parts.append(clean(mark3_html))
            print(f"         ✅ 3-mark ({len(mark3_html)} chars)")
        else:
            print(f"         ❌ 3-mark failed — continuing")

        # Call 4 — 5-mark + diagram
        print(f"      [{self.discipline}] Call 4: 5-mark + diagram (Q86-Q100)...")
        mark5_html = self._call_mark5(text, lesson_title, class_num, unit)
        if mark5_html:
            parts.append(clean(mark5_html))
            print(f"         ✅ 5-mark ({len(mark5_html)} chars)")
        else:
            print(f"         ❌ 5-mark failed — continuing")

        if len(parts) <= 1:  # only the header, everything failed
            return None

        combined = "\n\n".join(parts)
        print(f"      [{self.discipline.title()} QA 1112] ✅ Complete — "
              f"{len(parts)} parts, {len(combined)} chars")
        return combined

    # =====================================================================
    # SHARED — call Claude, verify the item count, retry once if short
    # =====================================================================

    def _generate_with_count_check(self, prompt: str, max_tokens: int,
                                    expected_count: int, tier_name: str) -> Optional[str]:
        """
        Calls Claude with `prompt`, then counts qa-item blocks in the raw
        HTML returned. If the count doesn't match `expected_count`, retries
        once. Whichever attempt is used last is returned as-is — a short
        section is still more useful than discarding the whole tier.
        """
        raw = None
        for attempt in range(2):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=BIO_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            actual = raw.count('class="qa-item"')
            if actual == expected_count:
                return raw
            if attempt == 0:
                print(f"⚠️ [{self.discipline}] {tier_name} returned {actual}/{expected_count} "
                      f"questions — retrying")
            else:
                print(f"⚠️ [{self.discipline}] {tier_name} still returned {actual}/{expected_count} "
                      f"questions after retry — using partial result")
        return raw

    # =====================================================================
    # CALL 1 — MCQ (Q1-Q40, 1 mark each)
    # =====================================================================

    def _call_mcq(self, text, lesson_title, class_num, unit):
        try:
            tier = QA_MARK_SPLIT["mcq"]
            prompt = f"""Generate the MCQ section of a Biology question bank.

Chapter : {lesson_title}
Class   : {class_num}
Unit    : {unit}

Generate EXACTLY {tier['count']} multiple-choice questions,
Q{tier['start']}-Q{tier['end']}, {tier['marks']} mark each.

Base every question and every option on facts that actually appear in
the chapter text below. Never invent a fact, number, or ratio.

{BIO_ANSWER_FORMAT_RULES}

Use the MCQ format from ANSWER FORMAT RULES above.
Section: id="section-mcq" | Title: "Section I — Choose the Correct Answer"
Note: {tier['marks']} Mark each | Q{tier['start']}-Q{tier['end']}

RULES:
- Raw HTML only — start with <div class="qa-section" id="section-mcq">
- You MUST generate EXACTLY {tier['count']} questions, numbered Q{tier['start']}
  through Q{tier['end']} inclusive. Count them before finishing.
- Do NOT stop early. If you are unsure of a distinct {tier['count']}th topic,
  generate a comprehensive/integrative question covering the whole chapter
  rather than omitting a question.
- Cover a spread of topics across the whole chapter, not just the start

Chapter Text:
---
{text}
---"""
            return self._generate_with_count_check(
                prompt, max_tokens=8000, expected_count=tier['count'],
                tier_name="MCQ (Call 1)"
            )
        except Exception as e:
            print(f"❌ [{self.discipline}] MCQ error: {e}")
            return None

    # =====================================================================
    # CALL 2 — 2-MARK (Q41-Q65, answer in 1-2 sentences)
    # =====================================================================

    def _call_mark2(self, text, lesson_title, class_num, unit):
        try:
            tier = QA_MARK_SPLIT["mark2"]
            prompt = f"""Generate the 2-mark section of a Biology question bank.

Chapter : {lesson_title}
Class   : {class_num}
Unit    : {unit}

Generate EXACTLY {tier['count']} questions, Q{tier['start']}-Q{tier['end']},
{tier['marks']} marks each. ANSWER LENGTH: exactly 1-2 complete sentences —
not more, not less.

Base every question and answer on facts that actually appear in the
chapter text below. Never invent a fact, number, or ratio.

{BIO_ANSWER_FORMAT_RULES}

Use the 2-mark format from ANSWER FORMAT RULES above.
Section: id="section-2mark" | Title: "Section II — Answer Briefly"
Note: {tier['marks']} Marks each | Q{tier['start']}-Q{tier['end']} | Answer in 1-2 sentences

RULES:
- Raw HTML only — start with <div class="qa-section" id="section-2mark">
- You MUST generate EXACTLY {tier['count']} questions, numbered Q{tier['start']}
  through Q{tier['end']} inclusive. Count them before finishing.
- Do NOT stop early. If you are unsure of a distinct {tier['count']}th topic,
  generate a comprehensive/integrative question covering the whole chapter
  rather than omitting a question.
- Each question covers a different part of the chapter

Chapter Text:
---
{text}
---"""
            return self._generate_with_count_check(
                prompt, max_tokens=6000, expected_count=tier['count'],
                tier_name="2-mark (Call 2)"
            )
        except Exception as e:
            print(f"❌ [{self.discipline}] 2-mark error: {e}")
            return None

    # =====================================================================
    # CALL 3 — 3-MARK (Q66-Q85, answer in 3-5 sentences)
    # =====================================================================

    def _call_mark3(self, text, lesson_title, class_num, unit):
        try:
            tier = QA_MARK_SPLIT["mark3"]
            prompt = f"""Generate the 3-mark section of a Biology question bank.

Chapter : {lesson_title}
Class   : {class_num}
Unit    : {unit}

Generate EXACTLY {tier['count']} questions, Q{tier['start']}-Q{tier['end']},
{tier['marks']} marks each. ANSWER LENGTH: exactly 3-5 complete sentences.

Base every question and answer on facts that actually appear in the
chapter text below. Never invent a fact, number, or ratio.

{BIO_ANSWER_FORMAT_RULES}

Use the 3-mark format from ANSWER FORMAT RULES above.
Section: id="section-3mark" | Title: "Section III — Answer in Detail (Short)"
Note: {tier['marks']} Marks each | Q{tier['start']}-Q{tier['end']} | Answer in 3-5 sentences

RULES:
- Raw HTML only — start with <div class="qa-section" id="section-3mark">
- You MUST generate EXACTLY {tier['count']} questions, numbered Q{tier['start']}
  through Q{tier['end']} inclusive. Count them before finishing.
- Do NOT stop early. If you are unsure of a distinct {tier['count']}th topic,
  generate a comprehensive/integrative question covering the whole chapter
  rather than omitting a question.
- Include distinguish/compare, reason-based, and explain-type questions

Chapter Text:
---
{text}
---"""
            return self._generate_with_count_check(
                prompt, max_tokens=7000, expected_count=tier['count'],
                tier_name="3-mark (Call 3)"
            )
        except Exception as e:
            print(f"❌ [{self.discipline}] 3-mark error: {e}")
            return None

    # =====================================================================
    # CALL 4 — 5-MARK + DIAGRAM (Q86-Q100, detailed answer)
    # =====================================================================

    def _call_mark5(self, text, lesson_title, class_num, unit):
        try:
            tier = QA_MARK_SPLIT["mark5"]
            prompt = f"""Generate the 5-mark section of a Biology question bank.

Chapter : {lesson_title}
Class   : {class_num}
Unit    : {unit}

Generate EXACTLY {tier['count']} questions, Q{tier['start']}-Q{tier['end']},
{tier['marks']} marks each. ANSWER LENGTH: a detailed paragraph answer.

Base every question and answer on facts that actually appear in the
chapter text below. Never invent a fact, number, or ratio.

Where a question is naturally diagram-based (structures, cross-sections,
cycles, processes with distinct stages/parts), include a simple labeled
inline SVG line diagram inside that question's answer-reveal, per the
DIAGRAMS rule in your system instructions. Not every 5-mark question
needs a diagram — only ones where a diagram genuinely helps the answer
(e.g. "describe the structure of X" or "explain the stages of Y").

{BIO_ANSWER_FORMAT_RULES}

Use the 5-mark format from ANSWER FORMAT RULES above.
Section: id="section-5mark" | Title: "Section IV — Answer in Detail"
Note: {tier['marks']} Marks each | Q{tier['start']}-Q{tier['end']} | Detailed answer, diagram where applicable

RULES:
- Raw HTML only — start with <div class="qa-section" id="section-5mark">
- You MUST generate EXACTLY {tier['count']} questions, numbered Q{tier['start']}
  through Q{tier['end']} inclusive. Count them before finishing.
- Do NOT stop early. If you are unsure of a distinct {tier['count']}th topic,
  generate a comprehensive/integrative question covering the whole chapter
  rather than omitting a question.
- Cover the chapter's major topics — the questions most likely to
  actually appear as 5-mark board exam questions

Chapter Text:
---
{text}
---"""
            return self._generate_with_count_check(
                prompt, max_tokens=16000,  # highest tier: longest answers +
                                            # inline SVG diagrams for several
                                            # questions — start here given
                                            # LP's Call 0a lesson (measure
                                            # real usage before trusting a
                                            # lower number)
                expected_count=tier['count'], tier_name="5-mark (Call 4)"
            )
        except Exception as e:
            print(f"❌ [{self.discipline}] 5-mark error: {e}")
            return None


# ============================================================================
# BOTANY / ZOOLOGY BUILDERS
# ============================================================================

class BotanyQA1112Builder(_BiologyQA1112Base):
    discipline = "botany"


class ZoologyQA1112Builder(_BiologyQA1112Base):
    discipline = "zoology"


# ============================================================================
# Singleton instances — exact names per team spec
# ============================================================================

botany_qa_1112_builder = BotanyQA1112Builder()
zoology_qa_1112_builder = ZoologyQA1112Builder()