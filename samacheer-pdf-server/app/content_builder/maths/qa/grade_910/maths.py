"""
maths/qa/grade_910/maths.py
---------------------------
QA Builder for Samacheer Kalvi — Maths
Class 8, 9 & 10

v1.0 — June 2026

100 questions per chapter — 5 API calls, mirrors grade_67 structure with:
  - Adjusted VSA sub-distribution (10 MCQ + 8 Fill + 5 T/F + 4 Match + 3 One-word)
  - 3-mark section now includes Geometric Construction questions
  - 5-mark section now includes Complex Construction + Verify, Data Handling
  - Higher max_tokens throughout (heavier content = longer answers)
  - Construction answers given as exact step-by-step text instructions

  Call 1 → Q1–Q30    Section A VSA — 1 mark
  Call 2 → Q31–Q55   Section A SA-I — 2 marks
  Call 3 → Q56–Q75   Section B SA-II — 3 marks (includes constructions)
  Call 4 → Q76–Q95   Section C LA — 5 marks (includes constructions + data handling)
  Call 5 → Q96–Q100  HOTS Bonus

Key rules:
  - Questions from chapter BODY — not just book-back
  - Step-by-step working shown for 3-mark and 5-mark answers
  - Construction answers = exact compass/ruler/protractor steps as text
  - Answers strictly from chapter text — no invented formulas or numbers
  - Show/Hide toggle — section-level button only
  - Age-appropriate but exam-rigor language for Class 8-10
  - MUST generate the exact question count requested every time
"""

import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    MATHS_QA_SYSTEM_PROMPT_910,
    MATHS_ANSWER_FORMAT_RULES,
    MATHS_VSA_DISTRIBUTION_910,
    get_maths_qa_header_910,
    clean,
)


class MathsQA910Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Maths QA Builder (910) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("display_title") or metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [Maths QA 910 v1] Generating: {lesson_title}")
        print(f"      [Maths QA 910 v1] 5 calls → 100 questions")

        parts = []

        # ── Call 1: VSA 1-mark Q1–Q30 ─────────────────────────────────────────
        print(f"      [Maths QA] Call 1/5: VSA 1-mark (Q1–Q30)...")
        part1 = self._call_vsa(text, lesson_title, class_num, unit)
        if part1:
            parts.append(clean(part1))
            print(f"         ✅ VSA done ({len(part1)} chars)")
        else:
            print(f"         ❌ VSA failed")

        # ── Call 2: SA-I 2-mark Q31–Q55 ──────────────────────────────────────
        print(f"      [Maths QA] Call 2/5: SA-I 2-mark (Q31–Q55)...")
        part2 = self._call_sa1(text, lesson_title, class_num, unit)
        if part2:
            parts.append(clean(part2))
            print(f"         ✅ SA-I done ({len(part2)} chars)")
        else:
            print(f"         ❌ SA-I failed")

        # ── Call 3: SA-II 3-mark Q56–Q75 (incl. constructions) ───────────────
        print(f"      [Maths QA] Call 3/5: SA-II 3-mark (Q56–Q75)...")
        part3 = self._call_sa2(text, lesson_title, class_num, unit)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ SA-II done ({len(part3)} chars)")
        else:
            print(f"         ❌ SA-II failed")

        # ── Call 4: LA 5-mark Q76–Q95 (incl. constructions + data) ───────────
        print(f"      [Maths QA] Call 4/5: LA 5-mark (Q76–Q95)...")
        part4 = self._call_la(text, lesson_title, class_num, unit)
        if part4:
            parts.append(clean(part4))
            print(f"         ✅ LA done ({len(part4)} chars)")
        else:
            print(f"         ❌ LA failed")

        # ── Call 5: HOTS Q96–Q100 ─────────────────────────────────────────────
        print(f"      [Maths QA] Call 5/5: HOTS Bonus (Q96–Q100)...")
        part5 = self._call_hots(text, lesson_title, class_num, unit)
        if part5:
            parts.append(clean(part5))
            print(f"         ✅ HOTS done ({len(part5)} chars)")
        else:
            print(f"         ❌ HOTS failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [Maths QA 910 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — VSA 1-mark Q1–Q30
    # -------------------------------------------------------------------------

    def _call_vsa(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section A VSA 1-mark questions Q1 to Q30.
Do NOT generate any other section.
You MUST generate the FULL 30 questions — do not stop early.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 8-10 — exam-focused, precise language.

{MATHS_VSA_DISTRIBUTION_910}

SOURCE RULE:
- Questions from WITHIN the chapter body — concepts, formulas, definitions, examples
- NOT just from book-back exercise questions
- Spread across the FULL chapter — all topics covered
- Answers strictly from chapter text — no outside knowledge

HEADER (include ONLY in this call):
{get_maths_qa_header_910(lesson_title, class_num, unit)}

SECTION STRUCTURE:
<div class="qa-section" id="section-vsa">
  <div class="section-header">
    <h2>Section A — Very Short Answer (VSA)</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-vsa')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>1 Mark each | Q1–Q30 | Bloom's Level: Remember / Understand</em></p>
  <p class="section-note"><em>Exam: 20 questions asked — answer all 20</em></p>

  [Q1–Q10: MCQ with 4 options]
  [Q11–Q18: Fill in the Blanks]
  [Q19–Q23: True or False with reason in answer]
  [Q24–Q27: Match one term to one definition/value]
  [Q28–Q30: One-word / one-line answer]

</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 30 questions: Q1 through Q30 — generate ALL of them, do not stop early
- Follow distribution EXACTLY: 10 MCQ + 8 Fill + 5 T/F + 4 Match + 3 One-word
- MCQ: NO tick marks in options — correct answer only inside answer-reveal
- T/F: answer includes one-sentence reason from chapter text
- Spread questions across ALL chapter topics
- Do NOT stop before Q30 — verify you have written all 30 before finishing

Chapter Text:
---
{text}
---

Start at Q1. End at Q30."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=10000,
                system=MATHS_QA_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 910 VSA error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 2 — SA-I 2-mark Q31–Q55
    # -------------------------------------------------------------------------

    def _call_sa1(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section A SA-I 2-mark questions Q31 to Q55.
Do NOT generate any other section.
Do NOT repeat any concept already tested in Q1–Q30.
You MUST generate the FULL 25 questions — do not stop early.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 8-10 — exam-focused, precise language.

Generate EXACTLY 25 questions: Q31 to Q55

QUESTION TYPES — distribute across 25 questions:
- Direct computation (8 questions): Solve a straightforward calculation
- Convert and write (5 questions): Convert between forms, simplify, standard form
- Verify property (5 questions): Verify a property with a given pair/set of numbers
- Simple word problem (5 questions): One-step real-life scenario
- Simple expression evaluation (2 questions): Short BODMAS-style expressions

ANSWER FORMAT for 2-mark:
- Show working step by step (1-2 steps)
- End with ∴ Answer: [final answer with units]

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different concepts from Q1–Q30
- Use actual numbers and examples from chapter text
- No invented formulas — only what appears in chapter

SECTION STRUCTURE:
<div class="qa-section" id="section-sa1">
  <div class="section-header">
    <h2>Section A — Short Answer I (SA-I)</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-sa1')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>2 Marks each | Q31–Q55 | Bloom's Level: Understand / Apply</em></p>
  <p class="section-note"><em>Exam: Answer any 6 of 8 questions asked (6 × 2 = 12 marks)</em></p>

  [Q31–Q55: 25 questions — step-by-step answers]

</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q31 through Q55 — generate ALL of them
- Every answer shows working + ∴ Answer with units
- Spread across ALL chapter topics
- Do NOT stop before Q55 — verify all 25 are written before finishing

Chapter Text:
---
{text}
---

Start at Q31. End at Q55."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=12000,
                system=MATHS_QA_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 910 SA-I error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 3 — SA-II 3-mark Q56–Q75 (includes constructions)
    # -------------------------------------------------------------------------

    def _call_sa2(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section B SA-II 3-mark questions Q56 to Q75.
Do NOT generate any other section.
Do NOT repeat any concept already tested in Q1–Q55.
You MUST generate the FULL 20 questions — do not stop early.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 8-10 — exam-focused, precise language.

Generate EXACTLY 20 questions: Q56 to Q75

QUESTION TYPES — distribute across 20 questions:
- Two-step word problems (5 questions): Multi-operation real-life problems
- Verify property — extended (4 questions): Verify property with 3 numbers, all steps labeled
- BODMAS — medium level (4 questions): Nested brackets, intermediate difficulty
- Basic Geometric Construction (5 questions — ONLY if chapter has construction content,
  otherwise replace with 5 more word/property/BODMAS questions distributed evenly):
  Construct perpendicular bisector, angle bisector, or specific angle.
  ANSWER must give EXACT step-by-step construction instructions as text:
  "Step 1: Draw line segment AB = X cm using ruler.
   Step 2: With A as center, open compass to more than half of AB, draw an arc.
   Step 3: ... Step 4: ... ∴ Construction complete: [describe final result]"
- Compare and represent (2 questions): Compare/order 3-4 numbers, plot on number line

ANSWER FORMAT for 3-mark — MANDATORY (non-construction):
Step 1: [First operation — state what and why]
Step 2: [Second operation — show calculation]
Step 3: [Third step or verification/conclusion]
∴ Answer: [Final answer with units or statement]

SOURCE RULE:
- Questions from WITHIN the chapter body
- If chapter has NO geometric construction content, skip construction questions
  entirely and replace with additional word problems / property verification
- Use actual numbers from chapter exercises
- No invented formulas — only from chapter text
- Bloom's level: Apply / Analyse

SECTION STRUCTURE:
<div class="qa-section" id="section-sa2">
  <div class="section-header">
    <h2>Section B — Short Answer II (SA-II)</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-sa2')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>3 Marks each | Q56–Q75 | Bloom's Level: Apply / Analyse</em></p>
  <p class="section-note"><em>Exam: Answer any 5 of 7 questions asked (5 × 3 = 15 marks)</em></p>

  [Q56–Q75: 20 questions — full step-by-step working shown]

</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 20 questions: Q56 through Q75 — generate ALL of them
- Every non-construction answer shows EXACTLY 3 steps + ∴ Answer
- Construction answers give exact compass/ruler steps as text
- Verify property questions: show LHS and RHS separately, conclude equal/not equal
- Do NOT stop before Q75 — verify all 20 are written before finishing

Chapter Text:
---
{text}
---

Start at Q56. End at Q75."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=16000,
                system=MATHS_QA_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 910 SA-II error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 4 — LA 5-mark Q76–Q95 (includes constructions + data handling)
    # -------------------------------------------------------------------------

    def _call_la(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section C LA 5-mark questions Q76 to Q95.
Do NOT generate any other section.
Do NOT repeat any concept already tested in Q1–Q75.
You MUST generate the FULL 20 questions — do not stop early.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 8-10 — exam-focused, rigorous language.

Generate EXACTLY 20 questions: Q76 to Q95

QUESTION TYPES — distribute across 20 questions:
- Multi-step word problems (7 questions): 3-4 operations, real-life context, full working
- Full BODMAS with proof (4 questions): Complex nested brackets, every step labeled with rule
- Property application and proof (4 questions): Prove/disprove a property, find unknowns
- Complex Construction + Verify (3 questions — ONLY if chapter has construction content,
  otherwise replace with 3 more multi-step word problems):
  Construct a triangle/quadrilateral with given conditions; measure and verify a property.
  ANSWER gives exact construction steps as text, then states the verification result.
- Data Handling and Statistics (2 questions — ONLY if chapter has data/statistics content,
  otherwise replace with 2 more property application questions):
  Draw description of bar graph/histogram from given data; find mean/median/mode; interpret.

ANSWER FORMAT for 5-mark — MANDATORY (non-construction):
Given: [State all given information]
To find: [State what is being asked]
Step 1: [First operation — state what and why]
Step 2: [Second operation — show calculation]
Step 3: [Third step]
Step 4: [Fourth step if needed]
∴ Answer: [Final answer with units + one concluding sentence]

SOURCE RULE:
- Questions from WITHIN the chapter body
- If chapter has NO construction content, skip construction questions entirely
- If chapter has NO data/statistics content, skip those questions entirely
- Each question covers a DIFFERENT major topic
- Use actual numbers, scenarios, formulas from chapter text only
- Bloom's level: Analyse / Evaluate

SECTION STRUCTURE:
<div class="qa-section" id="section-la">
  <div class="section-header">
    <h2>Section C — Long Answer (LA)</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-la')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>5 Marks each | Q76–Q95 | Bloom's Level: Analyse / Evaluate</em></p>
  <p class="section-note"><em>Exam: Answer any 4 of 5 questions asked (4 × 5 = 20 marks)</em></p>

  [Q76–Q95: 20 questions — full working with Given/To find/Steps/Answer]

</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 20 questions: Q76 through Q95 — generate ALL of them
- Every non-construction answer: Given + To find + minimum 4 steps + ∴ Answer
- Multi-step problems must use realistic Indian context
- Do NOT stop before Q95 — verify all 20 are written before finishing

Chapter Text:
---
{text}
---

Start at Q76. End at Q95."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=18000,
                system=MATHS_QA_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 910 LA error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 5 — HOTS Bonus Q96–Q100
    # -------------------------------------------------------------------------

    def _call_hots(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section HOTS Bonus questions Q96 to Q100.
Do NOT generate any other section.
These are enrichment questions — beyond standard syllabus difficulty.
You MUST generate the FULL 5 questions — do not stop early.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 8-10 — challenging, exam-stretch level.

Generate EXACTLY 5 questions: Q96 to Q100

QUESTION TYPES — one of each:
- Q96: Open-ended problem — no single correct answer, multiple valid strategies
- Q97: Cross-chapter application — connect this chapter's concept with another
  chapter or earlier-grade concept in one rich problem
- Q98: Puzzle / Pattern — number puzzle, pattern extension, or magic-square style
  problem beyond textbook scope
- Q99: Create and justify — student creates their own problem/construction with
  conditions and verifies the result
- Q100: Error analysis — spot the mistake in a given (wrong) solution and correct it

ANSWER FORMAT for HOTS:
- Show one complete model answer/approach
- Note if multiple valid approaches exist
- For error analysis: identify the error clearly, then show correct solution
- For creative tasks: give one complete example with justification

SOURCE RULE:
- Based on concepts from chapter text
- Numbers and contexts may extend slightly beyond textbook examples
- But all formulas/rules used must be from chapter only
- Bloom's level: Evaluate / Create

SECTION STRUCTURE:
<div class="qa-section" id="section-hots">
  <div class="section-header">
    <h2>HOTS — Higher Order Thinking Skills (Bonus / Enrichment)</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-hots')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>5–8 Marks each | Q96–Q100 | Bloom's Level: Evaluate / Create</em></p>
  <p class="section-note"><em>Optional / Bonus — for advanced students and internal assessment</em></p>

  [Q96–Q100: 5 HOTS questions — full reasoning shown]

</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 5 questions: Q96 through Q100 — generate ALL of them
- Every question has a complete model answer with reasoning
- Do NOT stop before Q100

Chapter Text:
---
{text}
---

Start at Q96. End at Q100."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=8000,
                system=MATHS_QA_SYSTEM_PROMPT_910,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 910 HOTS error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

maths_qa_910_builder = MathsQA910Builder()