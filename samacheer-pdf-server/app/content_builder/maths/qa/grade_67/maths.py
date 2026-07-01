"""
maths/qa/grade_67/maths.py
--------------------------
QA Builder for Samacheer Kalvi — Maths
Class 6 & 7

v1.0 — June 2026

100 questions per chapter — 5 API calls:
  Call 1 → Q1–Q30    Section A VSA — 1 mark
                      (8 MCQ + 8 Fill + 5 T/F + 5 Match + 4 One-word)
  Call 2 → Q31–Q55   Section A SA-I — 2 marks
                      (Direct compute, one-step, identify, convert)
  Call 3 → Q56–Q80   Section B SA-II — 3 marks
                      (Two-step, word problems, verify property, patterns)
  Call 4 → Q81–Q95   Section C LA — 5 marks
                      (Multi-step, real-life, compare, proof)
  Call 5 → Q96–Q100  HOTS Bonus
                      (Open-ended, puzzle, project, create & justify)

Key rules:
  - Questions from chapter BODY — not just book-back
  - Step-by-step working shown for 3-mark and 5-mark answers
  - Answers strictly from chapter text — no invented formulas or numbers
  - Show/Hide toggle — section-level button only (no per-question buttons)
  - Bloom's level increases across sections (Remember → Create)
  - Age-appropriate language for Class 6/7 (11-13 years)
  - Same pattern applies for both grade_67 and grade_910
"""

import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    MATHS_QA_SYSTEM_PROMPT,
    MATHS_ANSWER_FORMAT_RULES,
    MATHS_VSA_DISTRIBUTION,
    get_maths_qa_header,
    clean,
)


class MathsQA67Builder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Maths QA Builder (67) v1.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate 100-question Maths QA bank using 5 API calls.

        Call 1 → Q1–Q30   VSA 1-mark
        Call 2 → Q31–Q55  SA-I 2-mark
        Call 3 → Q56–Q80  SA-II 3-mark
        Call 4 → Q81–Q95  LA 5-mark
        Call 5 → Q96–Q100 HOTS Bonus
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        print(f"      [Maths QA 67 v1] Generating: {lesson_title}")
        print(f"      [Maths QA 67 v1] 5 calls → 100 questions")

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

        # ── Call 3: SA-II 3-mark Q56–Q80 ─────────────────────────────────────
        print(f"      [Maths QA] Call 3/5: SA-II 3-mark (Q56–Q80)...")
        part3 = self._call_sa2(text, lesson_title, class_num, unit)
        if part3:
            parts.append(clean(part3))
            print(f"         ✅ SA-II done ({len(part3)} chars)")
        else:
            print(f"         ❌ SA-II failed")

        # ── Call 4: LA 5-mark Q81–Q95 ─────────────────────────────────────────
        print(f"      [Maths QA] Call 4/5: LA 5-mark (Q81–Q95)...")
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
        print(f"      [Maths QA 67 v1] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — VSA 1-mark Q1–Q30
    # -------------------------------------------------------------------------

    def _call_vsa(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section A VSA 1-mark questions Q1 to Q30.
Do NOT generate any other section.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 6/7 — use age-appropriate, simple language.

{MATHS_VSA_DISTRIBUTION}

SOURCE RULE:
- Questions from WITHIN the chapter body — concepts, formulas, definitions, examples
- NOT just from book-back exercise questions
- Spread across the FULL chapter — all topics covered
- Answers strictly from chapter text — no outside knowledge
- Language simple and clear for Class 6/7 students

HEADER (include ONLY in this call — not in other calls):
{get_maths_qa_header(lesson_title, class_num, unit)}

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
  <p class="section-note"><em>Exam: 14 questions asked — answer all 14</em></p>

  [Q1–Q8: MCQ with 4 options]
  [Q9–Q16: Fill in the Blanks]
  [Q17–Q21: True or False with reason in answer]
  [Q22–Q26: Match one term to one definition/value]
  [Q27–Q30: One-word answer]

</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 30 questions: Q1 through Q30
- Follow distribution EXACTLY: 8 MCQ + 8 Fill + 5 T/F + 5 Match + 4 One-word
- MCQ: NO tick marks in options — correct answer only inside answer-reveal
- T/F: answer includes one-sentence reason from chapter text
- Match: one term per question — not a full table
- Spread questions across ALL chapter topics — not just first topic
- Do NOT stop before Q30

Chapter Text:
---
{text}
---

Start at Q1. End at Q30."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=8000,
                system=MATHS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 67 VSA error: {e}")
            if 'overloaded' in str(e).lower():
                import time
                print(f"         ⏳ API overloaded — waiting 30 seconds and retrying...")
                time.sleep(30)
                try:
                    raw = ""
                    with self.client.messages.stream(
                        model=self.model, max_tokens=8000,
                        system=MATHS_QA_SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        for chunk in stream.text_stream:
                            raw += chunk
                    return raw.strip() or None
                except Exception as e2:
                    print(f"❌ Maths QA 67 VSA retry failed: {e2}")
            return None

    # -------------------------------------------------------------------------
    # Call 2 — SA-I 2-mark Q31–Q55
    # -------------------------------------------------------------------------

    def _call_sa1(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section A SA-I 2-mark questions Q31 to Q55.
Do NOT generate any other section.
Do NOT repeat any concept already tested in Q1–Q30.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 6/7 — use age-appropriate, simple language.

Generate EXACTLY 25 questions: Q31 to Q55

QUESTION TYPES — distribute across 25 questions:
- Direct computation (8 questions): Solve a straightforward calculation
- One-step word problem (6 questions): Simple real-life scenario, one operation
- Identify and state (5 questions): Identify a property, rule, or pattern and state it
- Convert and write (6 questions): Convert between forms (words↔numerals, units, systems)

ANSWER FORMAT for 2-mark:
- Show working step by step (1-2 steps)
- End with ∴ Answer: [final answer with units]
- 1-2 steps maximum — these are 2-mark questions

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different concepts from Q1–Q30
- Use actual numbers and examples from chapter text
- No invented formulas — only what appears in chapter
- Language simple and clear for Class 6/7

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
- EXACTLY 25 questions: Q31 through Q55
- Every answer shows working + ∴ Answer with units
- Spread across ALL chapter topics
- Do NOT stop before Q55

Chapter Text:
---
{text}
---

Start at Q31. End at Q55."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=10000,
                system=MATHS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 67 SA-I error: {e}")
            if 'overloaded' in str(e).lower():
                import time
                print(f"         ⏳ API overloaded — waiting 30 seconds and retrying...")
                time.sleep(30)
                try:
                    raw = ""
                    with self.client.messages.stream(
                        model=self.model, max_tokens=10000,
                        system=MATHS_QA_SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        for chunk in stream.text_stream:
                            raw += chunk
                    return raw.strip() or None
                except Exception as e2:
                    print(f"❌ Maths QA 67 SA-I retry failed: {e2}")
            return None

    # -------------------------------------------------------------------------
    # Call 3 — SA-II 3-mark Q56–Q80
    # -------------------------------------------------------------------------

    def _call_sa2(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section B SA-II 3-mark questions Q56 to Q80.
Do NOT generate any other section.
Do NOT repeat any concept already tested in Q1–Q55.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 6/7 — use age-appropriate, simple language.

Generate EXACTLY 25 questions: Q56 to Q80

QUESTION TYPES — distribute across 25 questions:
- Two-step problems (8 questions): Require exactly 2 operations to solve
- Simple word problems (7 questions): Real-life context, 2-3 steps
- Verify property (5 questions): Verify a mathematical property with given numbers
- Pattern continuation (5 questions): Identify rule and extend pattern

ANSWER FORMAT for 3-mark — MANDATORY:
Step 1: [First operation — state what and why]
Step 2: [Second operation — show calculation]
Step 3: [Third step or verification/conclusion]
∴ Answer: [Final answer with units or statement]

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different concepts from Q1–Q55
- Use actual numbers from chapter exercises
- No invented formulas — only from chapter text
- Language simple and clear for Class 6/7
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
  <p class="section-note"><em>3 Marks each | Q56–Q80 | Bloom's Level: Apply / Analyse</em></p>
  <p class="section-note"><em>Exam: Answer any 5 of 7 questions asked (5 × 3 = 15 marks)</em></p>

  [Q56–Q80: 25 questions — full 3-step working shown]

</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 25 questions: Q56 through Q80
- Every answer shows EXACTLY 3 steps + ∴ Answer
- Word problems must have real-life context relevant to Class 6/7
- Verify property questions: show LHS and RHS separately, conclude equal/not equal
- Pattern questions: show the identified rule, then next 3 terms
- Do NOT stop before Q80

Chapter Text:
---
{text}
---

Start at Q56. End at Q80."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=12000,
                system=MATHS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 67 SA-II error: {e}")
            if 'overloaded' in str(e).lower():
                import time
                print(f"         ⏳ API overloaded — waiting 30 seconds and retrying...")
                time.sleep(30)
                try:
                    raw = ""
                    with self.client.messages.stream(
                        model=self.model, max_tokens=12000,
                        system=MATHS_QA_SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        for chunk in stream.text_stream:
                            raw += chunk
                    return raw.strip() or None
                except Exception as e2:
                    print(f"❌ Maths QA 67 SA-II retry failed: {e2}")
            return None

    # -------------------------------------------------------------------------
    # Call 4 — LA 5-mark Q81–Q95
    # -------------------------------------------------------------------------

    def _call_la(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section C LA 5-mark questions Q81 to Q95.
Do NOT generate any other section.
Do NOT repeat any concept already tested in Q1–Q80.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 6/7 — use age-appropriate, simple language.

Generate EXACTLY 15 questions: Q81 to Q95

QUESTION TYPES — distribute across 15 questions:
- Multi-step word problems (5 questions): 4-5 operations, real-life context
- Real-life application (4 questions): Practical scenario using chapter concepts
- Compare and contrast (3 questions): Compare two methods, systems, or values
- Proof or verification (3 questions): Prove or verify a property/rule with full working

ANSWER FORMAT for 5-mark — MANDATORY:
Given: [State all given information]
To find: [State what is being asked]
Step 1: [First operation — state what and why]
Step 2: [Second operation — show calculation]
Step 3: [Third step]
Step 4: [Fourth step if needed]
∴ Answer: [Final answer with units + one concluding sentence]

SOURCE RULE:
- Questions from WITHIN the chapter body
- Different major topics from Q1–Q80
- Each question covers a DIFFERENT chapter topic
- Use actual numbers, scenarios, formulas from chapter text only
- Language appropriate for Class 6/7 — avoid overly complex vocabulary
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
  <p class="section-note"><em>5 Marks each | Q81–Q95 | Bloom's Level: Analyse / Evaluate</em></p>
  <p class="section-note"><em>Exam: Answer any 4 of 5 questions asked (4 × 5 = 20 marks)</em></p>

  [Q81–Q95: 15 questions — full working with Given/To find/Steps/Answer]

</div>

RULES:
- Raw HTML only — no markdown, no code fences
- EXACTLY 15 questions: Q81 through Q95
- Every answer: Given + To find + minimum 4 steps + ∴ Answer with sentence
- Multi-step problems must use realistic Indian context (market, budget, measurement)
- Compare questions: show both sides clearly, conclude with statement
- Proof questions: show full algebraic or numerical verification
- Do NOT stop before Q95

Chapter Text:
---
{text}
---

Start at Q81. End at Q95."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=12000,
                system=MATHS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 67 LA error: {e}")
            if 'overloaded' in str(e).lower():
                import time
                print(f"         ⏳ API overloaded — waiting 30 seconds and retrying...")
                time.sleep(30)
                try:
                    raw = ""
                    with self.client.messages.stream(
                        model=self.model, max_tokens=12000,
                        system=MATHS_QA_SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        for chunk in stream.text_stream:
                            raw += chunk
                    return raw.strip() or None
                except Exception as e2:
                    print(f"❌ Maths QA 67 LA retry failed: {e2}")
            return None

    # -------------------------------------------------------------------------
    # Call 5 — HOTS Bonus Q96–Q100
    # -------------------------------------------------------------------------

    def _call_hots(self, text, lesson_title, class_num, unit) -> Optional[str]:
        try:
            prompt = f"""Generate ONLY Section HOTS Bonus questions Q96 to Q100.
Do NOT generate any other section.
These are enrichment questions — beyond standard syllabus difficulty.

{MATHS_ANSWER_FORMAT_RULES}

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | Maths
Note    : Class 6/7 — challenging but still age-appropriate.

Generate EXACTLY 5 questions: Q96 to Q100

QUESTION TYPES — one of each:
- Q96: Open-ended puzzle — multiple valid approaches, students choose method
- Q97: Real-world project question — apply chapter concept to a real scenario
- Q98: Create and justify — student creates their own example and proves it works
- Q99: Error analysis — spot the mistake in a given (wrong) solution and correct it
- Q100: Higher-order thinking — connect two concepts from the chapter creatively

ANSWER FORMAT for HOTS:
- Show one complete model answer/approach
- Note if multiple valid approaches exist
- For puzzles: show the logic, not just the answer
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
- EXACTLY 5 questions: Q96 through Q100
- Every question has a complete model answer with reasoning
- Questions must be genuinely challenging — not just harder computation
- Age-appropriate for Class 6/7 even if challenging
- Do NOT stop before Q100

Chapter Text:
---
{text}
---

Start at Q96. End at Q100."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=6000,
                system=MATHS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ Maths QA 67 HOTS error: {e}")
            if 'overloaded' in str(e).lower():
                import time
                print(f"         ⏳ API overloaded — waiting 30 seconds and retrying...")
                time.sleep(30)
                try:
                    raw = ""
                    with self.client.messages.stream(
                        model=self.model, max_tokens=6000,
                        system=MATHS_QA_SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": prompt}]
                    ) as stream:
                        for chunk in stream.text_stream:
                            raw += chunk
                    return raw.strip() or None
                except Exception as e2:
                    print(f"❌ Maths QA 67 HOTS retry failed: {e2}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

maths_qa_67_builder = MathsQA67Builder()