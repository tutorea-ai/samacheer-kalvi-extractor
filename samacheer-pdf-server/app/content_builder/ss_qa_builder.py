"""
ss_qa_builder.py
----------------
QA Generator for Samacheer Kalvi Social Science (Classes 6-12).
Handles History, Geography, Civics, Economics disciplines.

v2.0 — Teacher feedback + team recommendation (May 2026)

Key changes from v1:
  ✅ 100 questions per chapter — no book-back dependency
  ✅ Same 4-call approach as English qa_builder.py
  ✅ Split:
       Call 1 → Q1–Q50   (1-mark, Part A — MCQ, True/False, One-word)
       Call 2 → Q51–Q75  (1-mark, Part B — Fill blanks, Match, Statement)
       Call 3 → Q76–Q88  (2-mark — Answer Briefly)
       Call 4 → Q89–Q100 (5-mark — Answer in Detail)
  ✅ All questions from chapter content — not book-back exercises
  ✅ "Book-inside" emphasis — questions from within the chapter body
  ✅ Discipline context injected so questions stay subject-relevant
  ✅ Works for all classes (not just Class 10)
  ✅ No 8-mark questions — SS max is 5 marks
  ✅ Uniform structure across all disciplines (like English QA)
  ✅ Streaming used for large calls

Mark distribution per 100 questions:
  Q1–Q50   → 1-mark (Part A: MCQ / True-False / One-word)       50 questions
  Q51–Q75  → 1-mark (Part B: Fill blanks / Match / Statement)    25 questions
  Q76–Q88  → 2-mark (Answer Briefly)                             13 questions
  Q89–Q100 → 5-mark (Answer in Detail)                           12 questions

Note: If team feedback says fewer 1-mark questions are needed,
      adjust Q_SPLIT constants below — no other changes required.
"""

import re
import anthropic
from typing import Optional, Dict
from ..config import settings


# ============================================================================
# SPLIT CONSTANTS — adjust here if mark distribution changes
# ============================================================================

Q_1MARK_A_START = 1
Q_1MARK_A_END   = 50    # Call 1: MCQ, True/False, One-word

Q_1MARK_B_START = 51
Q_1MARK_B_END   = 75    # Call 2: Fill blanks, Match, Statement

Q_2MARK_START   = 76
Q_2MARK_END     = 88    # Call 3: Answer Briefly

Q_5MARK_START   = 89
Q_5MARK_END     = 100   # Call 4: Answer in Detail


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SS_QA_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Social Science teacher
creating a comprehensive question bank WITH ANSWERS for Tamil Nadu state board students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Generate questions AND answers based ONLY on the chapter text provided
- Never invent facts not present in the text
- EVERY question must have a clear complete answer shown below it
- NEVER use textarea or input boxes — this is a question bank with answers
- Base questions on the CHAPTER BODY content — not just book-back exercises
- Emphasise "book-inside" questions — from within the chapter paragraphs,
  headings, facts, dates, names, and concepts"""


# ============================================================================
# DISCIPLINE CONTEXT — injected into every call for subject-relevance
# ============================================================================

DISCIPLINE_CONTEXT = {
    "history": """
HISTORY FOCUS:
- Questions must test dates, events, causes, consequences, treaties, personalities
- Include chronology questions (what came first / what happened after)
- Include cause-effect questions (why did X happen / what resulted from Y)
- Include map-related questions as text (which country / where did it happen)
- Include source-based questions if any quote or extract appears in the chapter
- Avoid vague questions — be specific about which event, which year, which person
""",
    "geography": """
GEOGRAPHY FOCUS:
- Questions must test physical features, locations, climate, resources, human activities
- Include map-based questions as text (where is X located / which river flows through Y)
- Include distinguish-between questions (difference between X and Y)
- Include reason-based questions (why does X happen in Y region)
- Include data/statistics from the chapter if any are present
- Be specific — name the actual rivers, mountains, regions, states from the chapter
""",
    "civics": """
CIVICS FOCUS:
- Questions must test constitutional provisions, government structure, rights, duties
- Include definition questions (what is X / define Y)
- Include function questions (what does X body do / what is the role of Y)
- Include comparison questions (difference between X and Y institution)
- Include value-based questions (why is X right important / what does Y duty mean)
- Be specific — reference actual articles, amendments, institutions from the chapter
""",
    "economics": """
ECONOMICS FOCUS:
- Questions must test concepts, definitions, data, policies, economic terms
- Include definition questions (what is GDP / define inflation)
- Include reason questions (why does X affect Y / what causes Z)
- Include data questions if statistics or figures appear in the chapter
- Include application questions (give an example of X in Indian context)
- Be specific — reference actual policies, schemes, numbers from the chapter
""",
}


# ============================================================================
# QA BUILDER CLASS
# ============================================================================

class SSQABuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ SS QA Builder v2.0 initialized — model: {self.model}")

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate 100-question SS QA bank using 4 API calls.

        Call 1 → Q1–Q50   (1-mark Part A: MCQ / True-False / One-word)
        Call 2 → Q51–Q75  (1-mark Part B: Fill blanks / Match / Statement)
        Call 3 → Q76–Q88  (2-mark: Answer Briefly)
        Call 4 → Q89–Q100 (5-mark: Answer in Detail)

        Args:
            text:     Clean chapter text from EPUB extractor
            metadata: Dict with class, unit, lesson_title, discipline etc.

        Returns:
            Combined HTML string, or None on failure.
        """
        discipline   = metadata.get("discipline", "history").lower().strip()
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")

        disc_context = DISCIPLINE_CONTEXT.get(discipline, DISCIPLINE_CONTEXT["history"])
        disc_display = discipline.title()

        total_calls = 4
        print(f"      [SS QA v2] Generating: {disc_display} | {lesson_title}")
        print(f"      [SS QA v2] 4 calls: 1m-PartA + 1m-PartB + 2m + 5m → 100 questions")

        parts = []

        # ── Call 1: 1-mark Part A (Q1–Q50) ───────────────────────────────────
        print(f"      [SS QA] Call 1/{total_calls}: 1-mark Part A (Q{Q_1MARK_A_START}–Q{Q_1MARK_A_END})...")
        part1 = self._call_1mark_part_a(
            text, lesson_title, class_num, unit, disc_display, disc_context
        )
        if part1:
            parts.append(self._clean(part1))
            print(f"         ✅ 1-mark Part A done ({len(part1)} chars)")
        else:
            print(f"         ❌ 1-mark Part A failed")

        # ── Call 2: 1-mark Part B (Q51–Q75) ──────────────────────────────────
        print(f"      [SS QA] Call 2/{total_calls}: 1-mark Part B (Q{Q_1MARK_B_START}–Q{Q_1MARK_B_END})...")
        part2 = self._call_1mark_part_b(
            text, lesson_title, class_num, unit, disc_display, disc_context
        )
        if part2:
            parts.append(self._clean(part2))
            print(f"         ✅ 1-mark Part B done ({len(part2)} chars)")
        else:
            print(f"         ❌ 1-mark Part B failed")

        # ── Call 3: 2-mark (Q76–Q88) ─────────────────────────────────────────
        print(f"      [SS QA] Call 3/{total_calls}: 2-mark (Q{Q_2MARK_START}–Q{Q_2MARK_END})...")
        part3 = self._call_2mark(
            text, lesson_title, class_num, unit, disc_display, disc_context
        )
        if part3:
            parts.append(self._clean(part3))
            print(f"         ✅ 2-mark done ({len(part3)} chars)")
        else:
            print(f"         ❌ 2-mark failed")

        # ── Call 4: 5-mark (Q89–Q100) ────────────────────────────────────────
        print(f"      [SS QA] Call 4/{total_calls}: 5-mark (Q{Q_5MARK_START}–Q{Q_5MARK_END})...")
        part4 = self._call_5mark(
            text, lesson_title, class_num, unit, disc_display, disc_context
        )
        if part4:
            parts.append(self._clean(part4))
            print(f"         ✅ 5-mark done ({len(part4)} chars)")
        else:
            print(f"         ❌ 5-mark failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [SS QA v2] ✅ Complete — {len(parts)} parts, {len(combined)} chars")
        return combined

    # -------------------------------------------------------------------------
    # Call 1 — 1-mark Part A: MCQ / True-False / One-word (Q1–Q50)
    # -------------------------------------------------------------------------

    def _call_1mark_part_a(self, text, lesson_title, class_num, unit,
                           disc_display, disc_context) -> Optional[str]:
        count = Q_1MARK_A_END - Q_1MARK_A_START + 1
        try:
            prompt = f"""Generate ONLY 1-mark Part A questions for this question bank.
Do NOT generate any 2-mark or 5-mark questions.

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {disc_display}
{disc_context}

Generate EXACTLY {count} questions: Q{Q_1MARK_A_START} to Q{Q_1MARK_A_END}

QUESTION TYPES — distribute evenly across ALL three types:
  Type 1: MCQ (Choose the correct answer) — 4 options, mark correct with ✓
  Type 2: True or False — state a fact, student marks T or F
  Type 3: One-word / One-sentence answer — direct factual question

ANSWER LENGTH: Maximum 1 complete sentence. 10–15 words only.

SOURCE RULE:
- Questions must come from WITHIN the chapter body — paragraphs, headings,
  facts, dates, names, events described in the text
- NOT just from book-back exercise questions
- Spread questions across the FULL chapter — beginning, middle, and end

HTML FORMAT — use these exact formats:

For MCQ:
<div class="qa-item">
  <p class="question"><strong>Q1.</strong> Which country declared war first in World War I?</p>
  <div class="mcq-options">
    <span>a) France</span>
    <span>b) Austria-Hungary ✓</span>
    <span>c) Russia</span>
    <span>d) Germany</span>
  </div>
  <p class="answer"><strong>Answer:</strong> b) Austria-Hungary declared war first in World War I.</p>
</div>

For True or False:
<div class="qa-item">
  <p class="question"><strong>Q2.</strong> True or False: The Treaty of Versailles was signed in 1919.</p>
  <p class="answer"><strong>Answer:</strong> True. The Treaty of Versailles was signed in 1919.</p>
</div>

For One-word/One-sentence:
<div class="qa-item">
  <p class="question"><strong>Q3.</strong> Who assassinated Archduke Franz Ferdinand?</p>
  <p class="answer"><strong>Answer:</strong> Gavrilo Princip assassinated Archduke Franz Ferdinand.</p>
</div>

HEADER (include only at the start of this call):
<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — {disc_display} | Unit {unit} | 100 Questions</p>
</div>

<h2>1-Mark Questions — Part A</h2>
<p class="section-note"><em>MCQ | True or False | One-word Answer</em></p>

STRICT RULES:
- Raw HTML only — no markdown, no code fences
- Generate EXACTLY {count} questions: Q{Q_1MARK_A_START} through Q{Q_1MARK_A_END}
- Every question must have a complete answer shown
- NEVER use textarea or input boxes
- Distribute question types evenly — not all MCQ or all True/False
- Spread questions across the full chapter content
- Do NOT stop before Q{Q_1MARK_A_END}

Chapter Text:
---
{text}
---

Start at Q{Q_1MARK_A_START}. End at Q{Q_1MARK_A_END}. Follow answer length strictly."""

            raw = ""
            with self.client.messages.stream(
                model=self.model, max_tokens=16000,
                system=SS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk
            return raw.strip() or None
        except Exception as e:
            print(f"❌ SS QA 1-mark Part A error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 2 — 1-mark Part B: Fill blanks / Match / Statement (Q51–Q75)
    # -------------------------------------------------------------------------

    def _call_1mark_part_b(self, text, lesson_title, class_num, unit,
                           disc_display, disc_context) -> Optional[str]:
        count = Q_1MARK_B_END - Q_1MARK_B_START + 1
        try:
            prompt = f"""Generate ONLY 1-mark Part B questions for this question bank.
Do NOT generate any 2-mark or 5-mark questions.
Do NOT repeat any question from Q1–Q50 (Part A).

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {disc_display}
{disc_context}

Generate EXACTLY {count} questions: Q{Q_1MARK_B_START} to Q{Q_1MARK_B_END}

QUESTION TYPES — distribute evenly across ALL three types:
  Type 1: Fill in the blank — one key word or phrase missing
  Type 2: Match the following — Column A to Column B (5 pairs per match set)
  Type 3: Choose the correct statement — 3 statements, one is correct

ANSWER LENGTH: Maximum 1 complete sentence. 10–15 words only.

SOURCE RULE:
- Questions must come from WITHIN the chapter body
- Different facts from those tested in Q1–Q50
- Spread across the full chapter

HTML FORMAT — use these exact formats:

For Fill in the blank:
<div class="qa-item">
  <p class="question"><strong>Q51.</strong> The assassination of Archduke Franz Ferdinand took place
  in <span class="blank-line">__________</span>.</p>
  <p class="answer"><strong>Answer:</strong> The assassination took place in Sarajevo.</p>
</div>

For Match the following (group 5 pairs together as one question):
<div class="qa-item">
  <p class="question"><strong>Q56.</strong> Match the following:</p>
  <table class="match-table">
    <thead><tr><th>Column A</th><th>Column B</th></tr></thead>
    <tbody>
      <tr><td>1. Triple Alliance</td><td>a) Germany, France, Russia</td></tr>
      <tr><td>2. Triple Entente</td><td>b) Germany, Austria-Hungary, Italy</td></tr>
      <tr><td>3. Treaty of Versailles</td><td>c) 1919</td></tr>
      <tr><td>4. Archduke Franz Ferdinand</td><td>d) Austria-Hungary</td></tr>
      <tr><td>5. League of Nations</td><td>e) Woodrow Wilson</td></tr>
    </tbody>
  </table>
  <p class="answer"><strong>Answers:</strong> 1-b, 2-a, 3-c, 4-d, 5-e</p>
</div>

For Choose the correct statement:
<div class="qa-item">
  <p class="question"><strong>Q62.</strong> Choose the correct statement:</p>
  <div class="mcq-options">
    <span>a) World War I began in 1918</span>
    <span>b) The League of Nations was proposed by Woodrow Wilson ✓</span>
    <span>c) Russia joined the Triple Alliance</span>
  </div>
  <p class="answer"><strong>Answer:</strong> b) The League of Nations was proposed by Woodrow Wilson.</p>
</div>

<h2>1-Mark Questions — Part B</h2>
<p class="section-note"><em>Fill in the Blanks | Match the Following | Correct Statement</em></p>

STRICT RULES:
- Raw HTML only — no markdown, no code fences
- Generate EXACTLY {count} questions: Q{Q_1MARK_B_START} through Q{Q_1MARK_B_END}
- Every question must have a complete answer shown
- NEVER use textarea or input boxes
- Do NOT repeat questions from Part A
- Do NOT stop before Q{Q_1MARK_B_END}

Chapter Text:
---
{text}
---

Start at Q{Q_1MARK_B_START}. End at Q{Q_1MARK_B_END}."""

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
            print(f"❌ SS QA 1-mark Part B error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 3 — 2-mark: Answer Briefly (Q76–Q88)
    # -------------------------------------------------------------------------

    def _call_2mark(self, text, lesson_title, class_num, unit,
                    disc_display, disc_context) -> Optional[str]:
        count = Q_2MARK_END - Q_2MARK_START + 1
        try:
            prompt = f"""Generate ONLY 2-mark questions for this question bank.
Do NOT generate any 1-mark or 5-mark questions.

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {disc_display}
{disc_context}

Generate EXACTLY {count} questions: Q{Q_2MARK_START} to Q{Q_2MARK_END}

ANSWER LENGTH: Exactly 2–3 complete sentences per answer. 30–50 words only.
Do NOT write more than 3 sentences. Do NOT write less than 2 sentences.

QUESTION TYPES — distribute evenly:
  - Short explanation: Explain what/who/how about a key topic
  - Reason-based: Why did X happen / What caused Y
  - Definition + example: Define X and give one example from the chapter
  - Compare briefly: State one difference between X and Y

SOURCE RULE:
- Questions must come from WITHIN the chapter body
- Test understanding, not just recall
- Spread across the full chapter — beginning, middle, and end

HTML FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q76.</strong> What were the main causes of World War I?
  <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-text">
    <p class="answer"><strong>Answer:</strong> The main causes of World War I were rivalry
    between European powers, the assassination of Archduke Franz Ferdinand, and the alliance
    system that pulled nations into conflict. Militarism, nationalism, and imperial competition
    also contributed significantly to the outbreak of war.</p>
  </div>
</div>

<h2>2-Mark Questions — Answer Briefly</h2>
<p class="section-note"><em>Answer in 2–3 sentences (30–50 words)</em></p>

STRICT RULES:
- Raw HTML only — no markdown, no code fences
- Generate EXACTLY {count} questions: Q{Q_2MARK_START} through Q{Q_2MARK_END}
- STRICTLY follow the 2–3 sentence answer length
- Every answer must use complete sentences
- NEVER use textarea or input boxes
- Do NOT mix in 1-mark or 5-mark questions
- Do NOT stop before Q{Q_2MARK_END}

Chapter Text:
---
{text}
---

Start at Q{Q_2MARK_START}. End at Q{Q_2MARK_END}. Follow answer length strictly."""

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
            print(f"❌ SS QA 2-mark error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Call 4 — 5-mark: Answer in Detail (Q89–Q100)
    # -------------------------------------------------------------------------

    def _call_5mark(self, text, lesson_title, class_num, unit,
                    disc_display, disc_context) -> Optional[str]:
        count = Q_5MARK_END - Q_5MARK_START + 1
        try:
            prompt = f"""Generate ONLY 5-mark questions for this question bank.
Do NOT generate any 1-mark or 2-mark questions.

Chapter : {lesson_title} | Class {class_num} | Unit {unit} | {disc_display}
{disc_context}

Generate EXACTLY {count} questions: Q{Q_5MARK_START} to Q{Q_5MARK_END}

ANSWER LENGTH: Exactly 5–7 complete sentences per answer. 80–120 words.
This is a paragraph answer — detailed but focused.
Do NOT write more than 7 sentences. Do NOT write less than 5 sentences.

QUESTION TYPES — distribute evenly:
  - Explain in detail: Full explanation of a key event, concept, or person
  - Causes and effects: List and explain causes OR consequences of a major event
  - Significance: Why was X important / What was the impact of Y
  - Compare: Detailed comparison between two concepts, events, or people
  - Evaluate: What were the outcomes / successes / failures of X

SOURCE RULE:
- Questions must come from WITHIN the chapter body
- Each question must test a DIFFERENT major topic from the chapter
- Spread across the full chapter — do not cluster on one section
- Answers must be based strictly on chapter content — no outside facts

HTML FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q89.</strong> Explain the consequences of World War I for Europe.
  <span class="mark-badge">(5 marks)</span></p>
  <div class="answer-text">
    <p class="answer"><strong>Answer:</strong> World War I had devastating consequences for Europe.
    The war resulted in the fall of four major empires — the German, Austro-Hungarian, Ottoman,
    and Russian empires. Millions of soldiers and civilians lost their lives, and vast areas of
    land were destroyed. The Treaty of Versailles imposed heavy penalties on Germany, including
    loss of territory, military restrictions, and massive reparations. New nations were created
    from the collapsed empires, redrawing the map of Europe entirely. These consequences created
    deep resentment and instability that eventually contributed to the outbreak of World War II.</p>
  </div>
</div>

<h2>5-Mark Questions — Answer in Detail</h2>
<p class="section-note"><em>Answer in 5–7 sentences (80–120 words)</em></p>

STRICT RULES:
- Raw HTML only — no markdown, no code fences
- Generate EXACTLY {count} questions: Q{Q_5MARK_START} through Q{Q_5MARK_END}
- STRICTLY follow the 5–7 sentence answer length (80–120 words)
- Every answer must be a proper paragraph — not bullet points
- NEVER use textarea or input boxes
- Each question must cover a different topic from the chapter
- Do NOT mix in 1-mark or 2-mark questions
- Do NOT stop before Q{Q_5MARK_END}

Chapter Text:
---
{text}
---

Start at Q{Q_5MARK_START}. End at Q{Q_5MARK_END}. Follow answer length strictly."""

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
            print(f"❌ SS QA 5-mark error: {e}")
            return None

    # -------------------------------------------------------------------------
    # Helper — clean raw AI output
    # -------------------------------------------------------------------------

    def _clean(self, raw: str) -> str:
        if not raw:
            return raw
        text = raw.strip()
        # Remove markdown code fences
        text = re.sub(r'```(?:html)?', '', text).strip()
        text = re.sub(r'```', '', text).strip()
        # Remove any inline style blocks
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        # Strip any leading non-HTML preamble text
        first_tag = re.search(r'<(?:div|h[1-6]|section|p|table)', text)
        if first_tag and first_tag.start() > 0:
            preamble = text[:first_tag.start()].strip()
            if preamble and not preamble.startswith('<'):
                text = text[first_tag.start():]
        return text.strip()


# ============================================================================
# Singleton instance
# ============================================================================

ss_qa_builder = SSQABuilder()