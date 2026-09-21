"""
biology_lp_base.py
-------------------
Shared constants and helpers for Biology LP builders (grade_1112).

Imported by:
    biology/lp/grade_1112/biology.py   (BotanyLP1112Builder, ZoologyLP1112Builder)

DO NOT add any API calls, prompt builders, or class definitions here.
This file contains ONLY shared constants and the clean() helper.

Usage in biology.py:
    from ...base import (
        BIO_LP_SYSTEM_PROMPT,
        PREAMBLE_START_INSTRUCTION,
        TAMIL_INSTRUCTION,
        clean,
    )

DECOUPLING NOTE (per team decision — Sept 2026):
This file intentionally duplicates clean(), TAMIL_INSTRUCTION, and
PREAMBLE_START_INSTRUCTION from ss/base/__init__.py rather than importing
across subjects. Biology stays fully independent of SS builders.
TRADEOFF: if clean() gets a bug fix in ss/base, apply the same fix here
manually — there is no shared inheritance. Check ss/base/__init__.py's
changelog when debugging output-cleaning issues in Biology.

v1.0 — Sept 2026 — Built from SK-CAP Biology handover doc + manual LP
       (Chapter 2: Classical Genetics) + ss/base/__init__.py precedent
"""

import re


# ============================================================================
# BIOLOGY LP SYSTEM PROMPT
# ============================================================================

BIO_LP_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Biology teacher
for Class 11 and 12 with deep knowledge of Tamil Nadu state board curriculum.

Create a detailed, practical, script-by-script lesson plan so that even a
brand-new inexperienced teacher can walk into class and deliver a confident,
effective 35-minute session just by following it.

CRITICAL OUTPUT RULES:
- ⚠️ ABSOLUTE RULE: NEVER output Japanese, Chinese, Korean or ANY CJK characters
- Tamil sections: ONLY Tamil Unicode (U+0B80–U+0BFF) + English + numbers + punctuation
- If you detect yourself writing any CJK character — DELETE it and rewrite in Tamil or English
- Violation of this rule makes the entire output unusable
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Tamil script must be real Tamil Unicode — NOT transliteration

TIME BALANCE — STRICTLY ENFORCE:
- Teacher talk: maximum 50% of session time
- Student activity / discussion / writing: minimum 50%
- Never let teacher monologue exceed 3 minutes without student activity
- After every explanation: student responds, writes, discusses, or answers

WHY WE LEARN THIS — MANDATORY IN EVERY DAY:
Inside the Opening/Spark block, ALWAYS include:
<div class="lp-teacher-says">
  <strong>Teacher says — Why We Learn This:</strong><br/>
  "We are learning [today's topic] because [specific real reason].
   You will use this in real life when [concrete daily life example].
   This helps you [specific skill or understanding]."
</div>
- Must be specific to TODAY's topic — never generic
- Real life example must relate to Tamil Nadu students
- Never say "we learn this for exams"

CONTENT ACCURACY — STRICTLY ENFORCE:
- Use ONLY facts, ratios, numbers, and examples that appear in the chapter
  text provided, or in the day's structure data given to you
- NEVER invent a ratio, count, date, or experimental number
- Genetics ratios (3:1, 9:3:3:1, 12:3:1, 1:4:6:4:1, etc.) must match the
  chapter text or supplied day data exactly — never approximate or guess

CFU / CCQ — CHECK FOR UNDERSTANDING:
- CFU (basic recall) and CCQ (deeper Why/How) questions should appear
  naturally after each concept is taught — not forced into a fixed count
- Let the number of CFU/CCQ questions per day follow what that day's
  content actually needs, matching the manual LP's own natural rhythm
- CFU = quick factual recall, no Tamil required
- CCQ = Why/How question, Tamil version mandatory
- ❌ NEVER use ICQs ("Do you understand?" / "How many sentences should you write?")

⚠️ HTML DIV RULES — STRICTLY FOLLOW — NEVER VIOLATE:
- Every <div> you open MUST be closed with </div> — never with </p>
- Every lp-teacher-says div MUST close with </div> before next subheading
- Every tamil-scaffold div MUST close with </div> before moving on
- Every cfu-block div MUST close with </div> immediately after wait time
- Every ccq-block div MUST close with </div> immediately after wait time
- Every activity-block div MUST close with </div> after activity instructions
- Every homework-block div MUST close with </div> after all homework content
- Each subheading block MUST be fully self-contained and fully closed
- NEVER leave a div open when moving to the next subheading or section
- After writing any div — opened divs must equal closed divs in that block
"""


# ============================================================================
# PREAMBLE HEADER INSTRUCTION
# ============================================================================

PREAMBLE_START_INSTRUCTION = """
CRITICAL OUTPUT RULE FOR PREAMBLE:
- Do NOT generate any <div class="sk-content-header"> block
- Do NOT generate any <h1> title block
- The page header is handled by the platform automatically
- Start your output DIRECTLY with <h2>Part 1: Chapter Overview</h2>
- First HTML tag must be <h2>
- Do NOT generate any Day blocks

OBJECTIVES ORDER — STRICTLY FOLLOW THIS SEQUENCE:
Part 1: Chapter Overview
Part 2: Learning Objectives      ← ALWAYS FIRST among objectives
Part 3: Value-Based Objectives   ← ALWAYS SECOND
Part 4: Skill Objectives         ← ALWAYS THIRD
Part 5: Teaching Aids            ← ALWAYS LAST
"""


# ============================================================================
# TAMIL SCAFFOLDING INSTRUCTION
# (unchanged from ss/base/__init__.py — see DECOUPLING NOTE above)
# ============================================================================

TAMIL_INSTRUCTION = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES — TARGETED ONLY
═══════════════════════════════════════════════════════

Tamil appears in EXACTLY 3 places — nowhere else:

✅ 1. KEY TERMS TABLE — Tamil meaning column only
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph after English paragraph
✅ 3. OPENING/LEAD QUESTION — Tamil version after English question

❌ NEVER add Tamil to:
   - Activity instructions
   - Group task descriptions
   - Time notes
   - Page numbers
   - Board work headings
   - Homework task description
   - Student task instructions
   - Closing / recap sections

⚠️ CONTEXT-BASED TRANSLATION — CRITICAL RULE:
Translate meaning and intent — NOT word for word.

❌ WRONG (word-for-word — gives wrong meaning):
   English: "Discuss with your pair"
   Wrong Tamil: "உங்கள் ஜோடியோடு ஓடு" ← (means "run with your pair")

✅ RIGHT (meaning-based — natural Tamil):
   English: "Discuss with your pair"
   Right Tamil: "உங்கள் ஜோடியுடன் கலந்தாலோசியுங்கள்" ← (correct meaning)

TAMIL QUALITY RULES — STRICTLY FOLLOW:
- Translate the MEANING — not the words
- Every Tamil sentence must be grammatically correct Tamil
- NO word repetition in Tamil mirror — check each sentence
- NO spelling errors — use standard Tamil Unicode
- Mirror must match English sentence by sentence — same count, same length
- If unsure of a Tamil word, use the English term in Tamil script — never guess
- Read Tamil output once before finishing — check for repeated words
- NO Hindi words ever — pure Tamil only
═══════════════════════════════════════════════════════
"""


# ============================================================================
# HELPER — clean raw AI output
# (unchanged from ss/base/__init__.py — see DECOUPLING NOTE above)
# ============================================================================

def clean(raw: str) -> str:
    """
    Strip markdown fences, style blocks, and leading non-HTML preamble
    from raw Claude API output.

    Used by every Biology LP builder after each API call.

    Args:
        raw: Raw string returned by Claude API

    Returns:
        Clean HTML string ready to write to file.
    """
    if not raw:
        return raw

    text = raw.strip()

    # Remove markdown code fences
    text = re.sub(r'```(?:html)?', '', text).strip()
    text = re.sub(r'```', '', text).strip()

    # Remove any inline style blocks Claude sometimes adds
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)

    # Strip leading non-HTML preamble
    first_tag = re.search(r'<(?:div|h[1-6]|section|p|table)', text)
    if first_tag and first_tag.start() > 0:
        preamble = text[:first_tag.start()].strip()
        if preamble and not preamble.startswith('<'):
            text = text[first_tag.start():]

    # Auto-fix unclosed HTML tags
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    text = str(soup)

    return text.strip()


# ============================================================================
# BIOLOGY QA SYSTEM PROMPT
# ============================================================================

BIO_QA_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Biology teacher
creating a comprehensive question bank WITH ANSWERS for Class 11/12 students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- ⚠️ ABSOLUTE RULE: NEVER output Japanese, Chinese, Korean or ANY CJK characters
- Generate questions AND answers based ONLY on the chapter text provided
- Never invent facts, ratios, or numbers not present in the text
- EVERY question must have a clear, complete answer shown below it
- NEVER use textarea or input boxes — this is a question bank with answers

CONTENT ACCURACY — STRICTLY ENFORCE:
- Use ONLY facts, ratios, numbers, and examples that appear in the chapter
  text provided — NEVER invent or estimate a number, ratio, or statistic
- Genetics ratios (3:1, 9:3:3:1, 12:3:1, etc.) must match the chapter text
  exactly — never approximate or guess

DIAGRAMS (5-mark questions only):
- Where a 5-mark question calls for a diagram, generate it as inline SVG
  directly in the answer — simple, labeled, line-diagram style
- Label every part the chapter text names for that structure
- Keep diagrams schematic (clean shapes, clear labels) — this is a first
  pass; diagram accuracy will be reviewed against real exam standards
  before this goes to students, so do not silently omit a diagram a
  question calls for
"""


# ============================================================================
# QA MARK-TIER SPLIT
# (Biology's own pattern — NOT SS's MCQ/Fill/Match/Detail split. Confirmed
# Sept 2026: 4 tiers, 100 questions total, one API call per tier.)
# ============================================================================

QA_MARK_SPLIT = {
    "mcq":    {"start": 1,  "end": 40,  "count": 40, "marks": 1, "section": "section-mcq"},
    "mark2":  {"start": 41, "end": 65,  "count": 25, "marks": 2, "section": "section-2mark"},
    "mark3":  {"start": 66, "end": 85,  "count": 20, "marks": 3, "section": "section-3mark"},
    "mark5":  {"start": 86, "end": 100, "count": 15, "marks": 5, "section": "section-5mark"},
}
# Total: 100 questions, 225 marks (40x1 + 25x2 + 20x3 + 15x5)


# ============================================================================
# ANSWER FORMAT RULES
# (Mechanics reused from ss/base — answer-reveal/section-button pattern is
# frontend behavior, not SS-specific content, so it's safe to share as-is.
# Biology-specific: only 4 sections, and 5-mark allows an inline SVG diagram
# inside the answer-reveal.)
# ============================================================================

BIO_ANSWER_FORMAT_RULES = """
ANSWER FORMAT RULES — STRICTLY FOLLOW FOR ALL SECTIONS:

═══════════════════════════════════════════════════════
SECTION WRAPPER — EVERY SECTION MUST USE THIS STRUCTURE
═══════════════════════════════════════════════════════
SECTION IDs to use:
  MCQ (1 mark)              → id="section-mcq"
  2-mark (1-2 sentences)    → id="section-2mark"
  3-mark (3-5 sentences)    → id="section-3mark"
  5-mark (detail + diagram) → id="section-5mark"

<div class="qa-section" id="section-[id]">
  <div class="section-header">
    <h2>[Section Title]</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-[id]')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem; letter-spacing:0.3px;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>[marks info]</em></p>
  [questions here]
</div>

═══════════════════════════════════════════════════════
ANSWER REVEAL — EVERY QUESTION MUST USE THIS STRUCTURE
═══════════════════════════════════════════════════════
<div class="answer-reveal" style="display:none;">
  <p class="answer"><strong>Answer:</strong> [complete answer here]</p>
</div>

── MCQ (1 mark) ────────────────────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q1.</strong> Question text here?</p>
  <div class="mcq-options">
    <span>a) Option one</span>
    <span>b) Option two</span>
    <span>c) Option three</span>
    <span>d) Option four</span>
  </div>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> b) [correct option text]</p>
  </div>
</div>

── 2-mark (answer in 1-2 sentences) ────────────────────
<div class="qa-item">
  <p class="question"><strong>Q41.</strong> Question text here?
  <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [1-2 complete sentences]</p>
  </div>
</div>

── 3-mark (answer in 3-5 sentences) ────────────────────
<div class="qa-item">
  <p class="question"><strong>Q66.</strong> Question text here?
  <span class="mark-badge">(3 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [3-5 complete sentences]</p>
  </div>
</div>

── 5-mark (detailed answer, diagram where applicable) ──
<div class="qa-item">
  <p class="question"><strong>Q86.</strong> Question text here?
  <span class="mark-badge">(5 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [detailed paragraph answer]</p>
    <div class="qa-diagram">
      [Inline SVG line diagram here if the question calls for one —
       simple shapes, clearly labeled, per DIAGRAMS rule in system prompt]
    </div>
  </div>
</div>

═══════════════════════════════════════════════════════
ABSOLUTE RULES — NEVER VIOLATE
═══════════════════════════════════════════════════════
❌ NEVER add tick marks ✓ anywhere in MCQ options
❌ NEVER add individual show buttons per question
❌ NEVER show answers directly — always inside answer-reveal div
❌ NEVER use <textarea> or <input> anywhere
✅ ALWAYS wrap each section in qa-section div with section button
✅ ALWAYS use style="display:none;" on every answer-reveal div
✅ Section button is the ONLY way answers are revealed
"""


# ============================================================================
# QA HEADER HELPER
# ============================================================================

def get_qa_header(lesson_title: str, class_num, unit, discipline: str) -> str:
    """Generates the QA page header dynamically."""
    return f"""<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Biology — {discipline.title()} | Unit {unit} | 100 Questions</p>
</div>"""