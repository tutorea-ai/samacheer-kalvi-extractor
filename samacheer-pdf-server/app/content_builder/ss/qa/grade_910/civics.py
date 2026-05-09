"""
history.py  (QA Builder)
------------------------
QA Generator for Samacheer Kalvi Social Science — History
Class 9 & 10

v2.0 — Teacher feedback + team recommendation (May 2026)

Split (100 questions total):
  Call 1 → Q1–Q25    MCQ (Choose the Correct Answer)
  Call 2 → Q26–Q50   Fill in the Blanks
  Call 3 → Q51–Q75   Choose the Statement (Q51-Q60) + Match the Following (Q61-Q75)
  Call 4 → Q76–Q100  2-mark (Q76-Q95) + 5-mark (Q96-Q100)

Key rules:
  - All questions from chapter BODY content — not just book-back
  - Every question must have a complete answer shown
  - Answers strictly from Samacheer textbook extracted text
  - No outside knowledge or hallucination
  - Match questions: two separate sets of 5 pairs each
"""

import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    SS_QA_SYSTEM_PROMPT,
    DISCIPLINE_CONTEXT,
    clean,
)


class CivicsQA910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Civics QA Builder (910) v2.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate 100-question History QA bank using 4 API calls.

        Call 1 → Q1–Q25   MCQ
        Call 2 → Q26–Q50  Fill in the Blanks
        Call 3 → Q51–Q75  Choose Statement + Match
        Call 4 → Q76–Q100 2-mark + 5-mark
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        disc_context = DISCIPLINE_CONTEXT.get("civics", "")

        total_calls = 4
        print(f"      [Civics QA 910 v2] Generating: {lesson_title}")
        print(f"      [Civics QA 910 v2] 4 calls → 100 questions")

        parts = []

        # ── Call 1: MCQ Q1–Q25 ────────────────────────────────────────────────
        print(f"      [History QA] Call 1/{total_calls}: MCQ (Q1–Q25)...")
        part1 = self._call_mcq(text, lesson_title, class_num, unit, disc_context)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ MCQ done ({len(part1)} chars)")
        else:
            print(f"         ❌ MCQ failed")

        # ── Call 2: Fill in the Blanks Q26–Q50 ───────────────────────────────
        print(f"      [History QA] Call 2/{total_calls}: Fill in the Blanks (Q26–Q50)...")
        part2 = self._call_fill_blanks(text, lesson_title, class_num, unit, disc_context)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ Fill blanks done ({len(part2)} chars)")
        else:
            print(f"         ❌ Fill blanks failed")

        # ── Call 3: Choose Statement + Match Q51–Q75 ──────────────────────────
        print(f"      [History QA] Call 3/{total_calls}: Statement + Match (Q51–Q75)...")
        part3 = self._call_statement_and_match(text, lesson_title, class_num, unit, disc_context)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ Statement + Match done ({len(part3)} chars)")
        else:
            print(f"         ❌ Statement + Match failed")

        # ── Call 4: 2-mark + 5-mark Q76–Q100 ─────────────────────────────────
        print(f"      [History QA] Call 4/{total_calls}: 2-mark + 5-mark (Q76–Q100)...")
        part4 = self._call_descriptive(text, lesson_title, class_num, unit, disc_context)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ Descriptive done ({len(part4)} chars)")
        else:
            print(f"         ❌ Descriptive failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Civics QA 910 v2] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — MCQ Q1–Q25
    # -------------------------------------------------------------------------

    def _call_mcq(self, text, lesson_title, class_num, unit, disc_context) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY MCQ questions Q1 to Q25 for this question bank.
Do NOT generate any other question type.

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | History
{disc_context}

Generate EXACTLY 25 MCQ questions: Q1 to Q25

ANSWER LENGTH: One complete sentence. 10-15 words only.

SOURCE RULE:
- Questions from WITHIN the chapter body — paragraphs, facts, dates, names
- NOT just from book-back exercise questions
- Spread across the FULL chapter — beginning, middle, and end
- Answers strictly from the chapter text — no outside knowledge

HEADER (include only here — not in other calls):
<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — History | Unit {unit} | 100 Questions</p>
</div>

<h2>Section I — Choose the Correct Answer</h2>
<p class="section-note"><em>1 Mark each | Q1–Q25</em></p>

FORMAT for each MCQ:
<div class="qa-item">
  <p class="question"><strong>Q1.</strong> Question text here?</p>
  <div class="mcq-options">
    <span>a) Option one</span>
    <span>b) Option two ✓</span>
    <span>c) Option three</span>
    <span>d) Option four</span>
  </div>
  <p class="answer"><strong>Answer:</strong> b) [correct option text — one complete sentence]</p>
</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q1 through Q25
- Every question has 4 options — mark correct with ✓
- Every question has complete answer shown
- Spread question types: dates, names, events, causes, results, treaties
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
            print(f"❌ History QA MCQ error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 2 — Fill in the Blanks Q26–Q50
    # -------------------------------------------------------------------------

    def _call_fill_blanks(self, text, lesson_title, class_num, unit, disc_context) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Fill in the Blank questions Q26 to Q50.
Do NOT generate MCQ, match, or descriptive questions.
Do NOT repeat any fact already tested in Q1–Q25.

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | History
{disc_context}

Generate EXACTLY 25 Fill in the Blank questions: Q26 to Q50

ANSWER LENGTH: One word or short phrase only.

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different facts from Q1–Q25
- Spread across the full chapter
- Answers strictly from chapter text

<h2>Section II — Fill in the Blanks</h2>
<p class="section-note"><em>1 Mark each | Q26–Q50</em></p>

FORMAT for each question:
<div class="qa-item">
  <p class="question"><strong>Q26.</strong> The assassination of Archduke Franz Ferdinand
  took place in <span class="blank-line">__________</span>.</p>
  <p class="answer"><strong>Answer:</strong> Sarajevo</p>
</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q26 through Q50
- Blank must be a key word or phrase from the chapter
- Answer shown clearly below each question
- Vary blank positions — not always at the end
- Cover different topics from across the chapter
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
            print(f"❌ History QA Fill Blanks error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 3 — Choose the Statement (Q51–Q60) + Match (Q61–Q75)
    # -------------------------------------------------------------------------

    def _call_statement_and_match(self, text, lesson_title, class_num, unit, disc_context) -> Optional[str]:
        try:
            prompt = f"""Generate two sections: Choose the Statement (Q51–Q60) and Match the Following (Q61–Q75).
Do NOT generate MCQ, fill blanks, or descriptive questions.
Do NOT repeat any fact already tested in Q1–Q50.

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | History
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

<h2>Section III — Choose the Correct Statement</h2>
<p class="section-note"><em>1 Mark each | Q51–Q60</em></p>

FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q51.</strong> Choose the correct statement:</p>
  <div class="mcq-options">
    <span>i) [Statement one — incorrect]</span>
    <span>ii) [Statement two — correct] ✓</span>
    <span>iii) [Statement three — incorrect]</span>
  </div>
  <p class="answer"><strong>Answer:</strong> ii) [Correct statement text]</p>
</div>

══════════════════════════════════════
PART B: Match the Following Q61–Q75
══════════════════════════════════════

Generate EXACTLY 3 match sets of 5 pairs each: Q61, Q66, Q71
(Q61 = Match Set 1, Q66 = Match Set 2, Q71 = Match Set 3)
Each match set counts as one question but has 5 sub-answers.

<h2>Section IV — Match the Following</h2>
<p class="section-note"><em>1 Mark each | Q61–Q75 | (5 pairs per set)</em></p>

FORMAT for each match set:
<div class="qa-item">
  <p class="question"><strong>Q61.</strong> Match the following:</p>
  <table class="match-table">
    <thead><tr><th>Column A</th><th>Column B</th></tr></thead>
    <tbody>
      <tr><td>1. [Item]</td><td>a) [Match]</td></tr>
      <tr><td>2. [Item]</td><td>b) [Match]</td></tr>
      <tr><td>3. [Item]</td><td>c) [Match]</td></tr>
      <tr><td>4. [Item]</td><td>d) [Match]</td></tr>
      <tr><td>5. [Item]</td><td>e) [Match]</td></tr>
    </tbody>
  </table>
  <p class="answer"><strong>Answers:</strong> 1-[x], 2-[x], 3-[x], 4-[x], 5-[x]</p>
</div>

IMPORTANT for match sets:
- Set 1 (Q61): Match events to dates
- Set 2 (Q66): Match personalities to their roles
- Set 3 (Q71): Match treaties/agreements to their outcomes
- Each set must use DIFFERENT facts from the chapter
- Column B items must be shuffled — not in same order as Column A

RULES:
- Raw HTML only — no markdown, no code fences
- Choose Statement: EXACTLY 10 questions Q51–Q60
- Match: EXACTLY 3 sets (Q61, Q66, Q71) with 5 pairs each
- All answers shown
- Do NOT stop before Q75

Chapter Text:
---
{text}
---

Start at Q51. End at Q75."""

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
            print(f"❌ History QA Statement + Match error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 4 — 2-mark (Q76–Q95) + 5-mark (Q96–Q100)
    # -------------------------------------------------------------------------

    def _call_descriptive(self, text, lesson_title, class_num, unit, disc_context) -> Optional[str]:
        try:
            prompt = f"""Generate two sections: 2-mark questions (Q76–Q95) and 5-mark questions (Q96–Q100).
Do NOT generate MCQ, fill blanks, or statement questions.
Do NOT repeat facts already tested in Q1–Q75.

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | History
{disc_context}

SOURCE RULE:
- Questions from WITHIN the chapter body
- Each question covers a DIFFERENT major topic from the chapter
- Answers strictly from chapter text — no outside knowledge

══════════════════════════════════════
PART A: 2-Mark Questions Q76–Q95
══════════════════════════════════════

Generate EXACTLY 20 questions: Q76 to Q95

ANSWER LENGTH: Exactly 2-3 complete sentences. 30-50 words only.
Do NOT write more than 3 sentences.
Do NOT write less than 2 sentences.

Question types — distribute evenly:
- Short explanation: Explain what/who/how about a key topic
- Reason-based: Why did X happen / What caused Y
- Definition + example: Define X and give one example from chapter
- Compare briefly: One difference between X and Y

<h2>Section V — Answer Briefly</h2>
<p class="section-note"><em>2 Marks each | Q76–Q95 | Answer in 2-3 sentences</em></p>

FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q76.</strong> What were the main causes of World War I?
  <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-text">
    <p class="answer"><strong>Answer:</strong> The main causes of World War I were the
    rivalry between European powers, the formation of opposing alliance systems, and the
    assassination of Archduke Franz Ferdinand in 1914. Militarism, nationalism, and
    imperial competition among European nations also contributed significantly.</p>
  </div>
</div>

══════════════════════════════════════
PART B: 5-Mark Questions Q96–Q100
══════════════════════════════════════

Generate EXACTLY 5 questions: Q96 to Q100

ANSWER LENGTH: Exactly 5-7 complete sentences. 80-120 words.
Do NOT write more than 7 sentences.
Do NOT write less than 5 sentences.
Every answer must be a proper paragraph — not bullet points.

Question types — one of each:
- Q96: Explain in detail — full explanation of a key event or concept
- Q97: Causes and effects — list and explain causes OR consequences
- Q98: Significance — why was X important / what was the impact of Y
- Q99: Compare — detailed comparison between two events or concepts
- Q100: Evaluate — outcomes, successes, or failures of a major event

<h2>Section VI — Answer in Detail</h2>
<p class="section-note"><em>5 Marks each | Q96–Q100 | Answer in 5-7 sentences</em></p>

FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q96.</strong> Explain the consequences of World War I for Europe.
  <span class="mark-badge">(5 marks)</span></p>
  <div class="answer-text">
    <p class="answer"><strong>Answer:</strong> World War I had devastating consequences
    for Europe. The war resulted in the fall of four major empires — the German,
    Austro-Hungarian, Ottoman, and Russian empires. Millions of soldiers and civilians
    lost their lives, and vast areas of land were destroyed. The Treaty of Versailles
    imposed heavy penalties on Germany, including loss of territory and massive reparations.
    New nations emerged from the collapsed empires, redrawing the map of Europe entirely.
    These consequences created deep resentment that eventually led to World War II.</p>
  </div>
</div>

RULES:
- Raw HTML only — no markdown, no code fences
- 2-mark: EXACTLY 20 questions Q76–Q95, strictly 2-3 sentences each
- 5-mark: EXACTLY 5 questions Q96–Q100, strictly 5-7 sentences each
- Every answer complete paragraph — never bullet points
- Each question covers a different chapter topic
- Do NOT stop before Q100

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
            print(f"❌ History QA Descriptive error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

civics_qa_910_builder = CivicsQA910Builder()