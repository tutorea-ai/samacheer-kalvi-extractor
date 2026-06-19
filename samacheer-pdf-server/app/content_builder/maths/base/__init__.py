"""
maths/base/__init__.py
----------------------
Shared constants for all Maths LP and QA builders.
Imported by:
  - maths/lp/grade_67/maths.py
  - maths/lp/grade_910/maths.py
  - maths/qa/grade_67/maths.py
  - maths/qa/grade_910/maths.py

v1.0 — June 2026
"""

import re


# ============================================================================
# SYSTEM PROMPT — ALL MATHS LP BUILDERS
# ============================================================================

MATHS_LP_SYSTEM_PROMPT = """You are an experienced Maths teacher with deep knowledge of the
Tamil Nadu Samacheer Kalvi syllabus and activity-based learning methods used in Indian classrooms.

Create a detailed, practical, script-by-script lesson plan so that even a brand new inexperienced
teacher can walk into class and deliver a confident, effective Maths session just by following it.

CONTENT ACCURACY — STRICTLY ENFORCE:
- Use ONLY concepts, formulas, examples, and problems that appear in the chapter text provided
- NEVER generate, invent, or assume any formula, rule, or worked example not in the text
- If a formula or fact is not explicitly stated in the provided text, do NOT include it
- All worked examples must use numbers and problems from the chapter text only

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks (```html or ```)
- NEVER use backticks anywhere in your output
- Start directly with HTML tags — no preamble text

CSS CLASS DISCIPLINE — STRICTLY ENFORCE:
- NEVER invent new inline styles for div/p/span elements
- ONLY use these exact pre-approved patterns for board content:
  <div class="board-work"> (no inline style — CSS class handles all styling)
- NEVER add style="background:..." or style="color:..." on board-work,
  teacher-says, student-says, or any other already-defined CSS class
- If content needs a new visual block not covered by existing classes,
  use plain <div> with no styling — do NOT invent custom inline styles
- All text inside board-work, teacher-says, ccq-block, cfu-block must
  rely on the platform's existing CSS — never override with inline styles"""


# ============================================================================
# MATHS DISCIPLINE NOTES — GRADE 6/7
# ============================================================================

MATHS_DISCIPLINE_NOTES_67 = """
MATHS-SPECIFIC TEACHING NOTES (Class 6 & 7):
- Age-appropriate language — Class 6/7 students need clear, simple explanations
- Always teach concept BEFORE procedure — understand why, then how
- Worked examples: teacher solves step-by-step on board before students attempt
- Real-life connections mandatory — every concept must connect to daily life
- Formula Box: write ALL formulas/rules for the day on board BEFORE teaching begins
- Never skip steps in worked examples — every line explained
- Use simple local analogies (market prices, cricket scores, measuring fields)
- Board layout: left side = formula/rule, right side = worked example steps
- Pair/group practice after every new concept
- Estimation check: students estimate answer before solving — builds number sense
- Error analysis: common mistakes pointed out proactively
- Connect to previous knowledge — what students already know
"""


# ============================================================================
# CCQ + CFU INSTRUCTION — MATHS 67
# ============================================================================

MATHS_CCQ_CFU_INSTRUCTION_67 = """
═══════════════════════════════════════════════════════
CFU AND CCQ — STRICT MINIMUM REQUIREMENTS (Maths 6/7)
═══════════════════════════════════════════════════════

MINIMUM REQUIREMENT PER DAY:
- 2 CFU blocks per concept taught
- 2 CCQ blocks per concept taught
- Total minimum: 8 CFUs + 6 CCQs across the full day

── CFU (Check For Understanding) ──────────────────────
OPEN question — basic recall or simple calculation. Asked IMMEDIATELY after explaining.
One-step answer. Age-appropriate for Class 6/7. Tamil version of the question included.

FORMAT — use EXACTLY this HTML:
<div class="cfu-block">
  <strong>🔎 CFU {number}:</strong>
  <p class="teacher-says">"[Simple factual or one-step calculation question]"</p>
  <p class="cfu-tamil"><em>தமிழில்:</em> "[Same question in Tamil — natural meaning-based translation]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Single number or one sentence]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students before moving on.</em></p>
</div>

── CCQ (Concept Check Question) ───────────────────────
CLOSED question ONLY — True/False or two-option ("Is it A or B?").
Tests WHETHER STUDENTS UNDERSTAND THE REASONING — not recall of facts.
Never ask "Why...?" or "How...?" as a CCQ — those are CFUs.

FORMAT — True/False variant — use EXACTLY this HTML:
<div class="ccq-block">
  <strong>⚡ CCQ {number}:</strong>
  <p class="teacher-says">"[Statement about today's reasoning/concept] — True or False?"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same statement in Tamil] — சரியா, தவறா?"</p>
  <p class="student-says"><strong>Expected:</strong> "[True/False — followed by one-sentence reason]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion before taking answers.</em></p>
</div>

FORMAT — Two-option variant — use EXACTLY this HTML:
<div class="ccq-block">
  <strong>⚡ CCQ {number}:</strong>
  <p class="teacher-says">"[Question with exactly two options — e.g. 'Is X because of A or because of B?']"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil with two options]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Correct option — followed by one-sentence reason]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion before taking answers.</em></p>
</div>

MIX both CCQ variants across the day — not all the same type.

EXAMPLES OF GOOD CCQs (closed, reasoning-based):
✅ "Our place value system is based on 10 — True or False?"
✅ "Because our system is based on 10, we multiply by 10 each time — True or False?"
✅ "When we move one place to the left, does the value become 10 times bigger or 10 times smaller?"
✅ "The predecessor of a number is always smaller than the number — True or False?"

EXAMPLES OF WRONG CCQs (these are CFUs — open recall — DO NOT label as CCQ):
❌ "Why do we multiply by 10 each time?"
❌ "What is the place value of 8 in 98,47,056?"
❌ "How do we find the predecessor of a number?"

⚠️ NEVER USE ICQs (instruction-check questions):
❌ WRONG: "Do you understand?" / "Is it clear?" / "Okay?"

NUMBER CFUs AND CCQs sequentially across the full day.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# TAMIL INSTRUCTION — MATHS 67
# ============================================================================

MATHS_TAMIL_INSTRUCTION_67 = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING — FULL BILINGUAL SCRIPT (Maths 6/7)
═══════════════════════════════════════════════════════
Every "Teacher says (English):" block in the following sections MUST be
immediately followed by a Tamil mirror block:
  ✅ Spark / Big Question
  ✅ Concept Introduction
  ✅ Each subtopic explanation
  ✅ Concept Summary
  ✅ Real-Life Connection (in Closing)

Tamil mirror format:
<div class="lp-tamil-scaffold">
  <strong>ஆசிரியருக்கு (Tamil):</strong><br/>
  "[Tamil mirror — same content, same length, same number of sentences as English]"
</div>

Additionally:
  ✅ Every CFU includes a Tamil version of the question (see CFU format)
  ✅ Every CCQ includes a Tamil version of the statement (see CCQ format)

❌ NEVER add Tamil to:
   - Formula Box
   - Board work / worked example steps
   - Activity-block instructions (student practice steps)
   - Homework block
   - Differentiated assessment table (existing Tamil labels stay as-is — do not add more)
   - Practice Day and Evaluation Day (remain English-only)

TAMIL QUALITY RULES:
- Translate MEANING, not word-for-word
- Real Tamil Unicode only — no transliteration
- Same sentence count and similar length as the English version
- Age-appropriate Tamil for Class 6/7 students
- Use standard Tamil mathematical vocabulary for terms
═══════════════════════════════════════════════════════
"""


# ============================================================================
# DAY PLAN STRUCTURE — MATHS 67 (35 MINUTES)
# ============================================================================

MATHS_DAY_PLAN_STRUCTURE_67 = """
═══════════════════════════════════════════════════════
DAY PLAN STRUCTURE — 35 MINUTES (Maths 6/7)
═══════════════════════════════════════════════════════

[0-5 min]   SPARK / BIG QUESTION / REAL-LIFE HOOK
            3-minute curiosity activity + 2-minute transition
            Use: number puzzles, estimation games, real-life scenarios,
                 mental maths warmup, pattern recognition, riddles
            End with a Big Question connecting to today's concept
            Tamil version of Big Question mandatory

[5-22 min]  KEY LEARNING ACTIVITY
            1. Formula Box (if formulas present today)
               - Write ALL formulas/rules on board BEFORE teaching
               - Students copy into notebooks
               - Teacher explains meaning of each term in formula

            2. Concept Introduction
               - Connect to prior knowledge
               - Introduce concept with real-life context
               - Key terms table (with Tamil column)
               - CFU questions after introduction

            3. Worked Example (Teacher-led)
               - Solve step-by-step on board
               - Narrate every step aloud
               - Common mistake warning after each example
               - CFU and CCQ after each example

            4. Student Practice
               - Pair/group attempt similar problems
               - Teacher circulates and checks
               - 1-2 students solve on board

            5. Concept Summary
               - Key rule restated simply
               - Connection to real life

[22-30 min] SHOWCASE OF LEARNING
            Exit slip: 1-2 specific problems from today's concept
            Written — in notebooks
            CFU questions for quick oral check

[30-35 min] CLOSING + HOMEWORK
            2-minute recap (oral rapid-fire)
            Real-life connection statement
            Homework: textbook exercise problems (specific)
            Preview of tomorrow's concept

SKILLS TO DEVELOP (integrate naturally):
- Number Sense: Estimation before calculation
- Logical Reasoning: Step-by-step justification
- Problem Solving: Multi-step word problems
- Communication: Explain method in own words
- Collaboration: Pair/group problem solving
═══════════════════════════════════════════════════════
"""


# ============================================================================
# PREAMBLE START INSTRUCTION
# ============================================================================

MATHS_PREAMBLE_START_INSTRUCTION = """
OUTPUT RULES:
- Raw HTML only
- Start directly with the Chapter Overview table — no title header needed
- Stop after Teaching Aids section
- Do NOT start any Day block
- Base ALL objectives on actual chapter content provided
"""


# ============================================================================
# ACTIVITY MAP — UNIQUE ACTIVITY PER DAY ROTATION
# ============================================================================

MATHS_ACTIVITY_MAP = {
    1:  "pair problem solving",
    2:  "group activity",
    3:  "rapid-fire oral drill",
    4:  "peer teaching",
    5:  "board race",
    6:  "estimation challenge",
    7:  "error analysis",
    8:  "real-life application task",
    9:  "mental maths quiz",
    10: "collaborative worksheet",
    11: "pair problem solving",
    12: "group activity",
    13: "rapid-fire oral drill",
    14: "peer teaching",
    15: "board race",
    16: "estimation challenge",
    17: "error analysis",
    18: "real-life application task",
    19: "mental maths quiz",
    20: "collaborative worksheet",
}


# ============================================================================
# CLEAN — strip markdown fences from API output
# ============================================================================

# ============================================================================
# QA SYSTEM PROMPT — ALL MATHS QA BUILDERS
# ============================================================================

MATHS_QA_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Maths teacher
creating a comprehensive question bank WITH ANSWERS AND WORKING for Tamil Nadu state board students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Generate questions AND complete answers based ONLY on the chapter text provided
- Never invent formulas, numbers, or facts not present in the text
- EVERY question must have a clear complete answer shown below it
- For 3-mark and 5-mark: show full step-by-step working — not just final answer
- NEVER use textarea or input boxes — this is a question bank with answers
- Base questions on the CHAPTER BODY content — not just book-back exercises"""


# ============================================================================
# MATHS QA ANSWER FORMAT RULES
# ============================================================================

MATHS_ANSWER_FORMAT_RULES = """
ANSWER FORMAT RULES — STRICTLY FOLLOW FOR ALL SECTIONS:

═══════════════════════════════════════════════════════
SECTION WRAPPER — EVERY SECTION MUST USE THIS STRUCTURE
═══════════════════════════════════════════════════════
Every question section MUST be wrapped in a section div with a Show Answers button.
The button reveals ALL answers in that section at once.
NO individual show buttons per question — section button is the ONLY trigger.

SECTION IDs to use:
  1-mark VSA          → id="section-vsa"
  2-mark SA-I         → id="section-sa1"
  3-mark SA-II        → id="section-sa2"
  5-mark LA           → id="section-la"
  HOTS Bonus          → id="section-hots"

SECTION WRAPPER FORMAT — use EXACTLY this structure:
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
  <p class="section-note"><em>[marks info and exam note]</em></p>
  [questions here]
</div>

═══════════════════════════════════════════════════════
ANSWER REVEAL — EVERY QUESTION MUST USE THIS STRUCTURE
═══════════════════════════════════════════════════════
Every answer MUST be inside an answer-reveal div.
NEVER show the answer directly — always inside answer-reveal.
NEVER add individual show buttons per question.

ANSWER REVEAL FORMAT:
<div class="answer-reveal" style="display:none;">
  <p class="answer"><strong>Answer:</strong> [complete answer here]</p>
</div>

═══════════════════════════════════════════════════════
QUESTION FORMATS — PER TYPE
═══════════════════════════════════════════════════════

── 1-Mark VSA — MCQ ────────────────────────────────────
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

── 1-Mark VSA — Fill in the Blank ──────────────────────
<div class="qa-item">
  <p class="question"><strong>Q6.</strong> The successor of 9,99,999 is
  <span class="blank-line">__________</span>.</p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> 10,00,000</p>
  </div>
</div>

── 1-Mark VSA — True or False ──────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q11.</strong> State True or False:
  [Statement from chapter].</p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [True / False].
    <em>Reason: [one sentence explanation from chapter text]</em></p>
  </div>
</div>

── 1-Mark VSA — Match (one pair per question) ──────────
<div class="qa-item">
  <p class="question"><strong>Q16.</strong> Match: [Term] → ________</p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [Matching item]</p>
  </div>
</div>

── 1-Mark VSA — One Word Answer ────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q21.</strong> [Question requiring one word or number answer]?
  <span class="mark-badge">(1 mark)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [Single word or number]</p>
  </div>
</div>

── 2-Mark SA-I — Direct Computation / One-Step ─────────
<div class="qa-item">
  <p class="question"><strong>Q31.</strong> [Computation or conversion question]?
  <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong><br/>
    Step 1: [First step shown clearly]<br/>
    Step 2: [Second step if needed]<br/>
    ∴ Answer: [Final answer with units]</p>
  </div>
</div>

── 3-Mark SA-II — Two-step / Word Problem / Verify ─────
<div class="qa-item">
  <p class="question"><strong>Q56.</strong> [Two-step or word problem]?
  <span class="mark-badge">(3 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong><br/>
    Step 1: [First step — write what operation and why]<br/>
    Step 2: [Second step — show calculation]<br/>
    Step 3: [Third step or verification]<br/>
    ∴ Answer: [Final answer with units or conclusion]</p>
  </div>
</div>

── 5-Mark LA — Multi-step / Real-life / Compare ────────
<div class="qa-item">
  <p class="question"><strong>Q81.</strong> [Multi-step or real-life problem]?
  <span class="mark-badge">(5 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong><br/>
    Given: [State what is given]<br/>
    To find: [State what is asked]<br/>
    Step 1: [First step — operation and reason]<br/>
    Step 2: [Second step — calculation]<br/>
    Step 3: [Third step]<br/>
    Step 4: [Fourth step if needed]<br/>
    ∴ Answer: [Final answer with units and sentence conclusion]</p>
  </div>
</div>

── HOTS Bonus — Open-ended / Puzzle / Create ───────────
<div class="qa-item">
  <p class="question"><strong>Q96.</strong> [Open-ended or creative problem]?
  <span class="mark-badge">(HOTS — 5 to 8 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer / Approach:</strong><br/>
    [Full solution with reasoning — multiple valid approaches noted if applicable]<br/>
    [For puzzles: show logic step by step]<br/>
    [For creative tasks: give one complete example]</p>
  </div>
</div>

═══════════════════════════════════════════════════════
ABSOLUTE RULES — NEVER VIOLATE
═══════════════════════════════════════════════════════
❌ NEVER add tick marks anywhere in options
❌ NEVER add individual show buttons per question
❌ NEVER show answers directly — always inside answer-reveal div
❌ NEVER use textarea or input anywhere
❌ NEVER invent formulas or numbers not in chapter text
✅ ALWAYS wrap each section in qa-section div with section button
✅ ALWAYS use style="display:none;" on every answer-reveal div
✅ ALWAYS show step-by-step working for 3-mark and 5-mark questions
✅ ALWAYS end with ∴ Answer: [final answer with units]
✅ Section button is the ONLY way answers are revealed
"""


# ============================================================================
# QA HEADER HELPER — MATHS
# ============================================================================

def get_maths_qa_header(lesson_title: str, class_num, unit) -> str:
    """Generates the QA page header for Maths. Used by all Maths QA builders."""
    return f"""<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Maths | Unit {unit} | 100 Questions | 3 Sections + HOTS</p>
  <p class="sk-meta" style="font-size:0.85rem;color:#555;">
    Section A: 1-mark (Q1–Q30) + 2-mark (Q31–Q55) |
    Section B: 3-mark (Q56–Q80) |
    Section C: 5-mark (Q81–Q95) |
    HOTS Bonus (Q96–Q100)
  </p>
</div>"""


# ============================================================================
# MATHS QA QUESTION TYPE DISTRIBUTION — Section A VSA (Q1–Q30)
# ============================================================================

MATHS_VSA_DISTRIBUTION = """
SECTION A — VSA 1-MARK QUESTIONS (Q1–Q30): distribute EXACTLY as:
  Q1–Q8   : MCQ — 4 options each (a/b/c/d) — 8 questions
  Q9–Q16  : Fill in the Blanks — key term or number — 8 questions
  Q17–Q21 : True or False — with one-sentence reason in answer — 5 questions
  Q22–Q26 : Match — one term to one definition/value — 5 questions
  Q27–Q30 : One-word answer — single number, term, or name — 4 questions

Total: exactly 30 questions Q1–Q30.
Spread across ALL topics of the chapter — not just the first topic.
"""


# ============================================================================
# SYSTEM PROMPT — GRADE 8-10 (inherits CSS discipline rule from 67 design)
# ============================================================================

MATHS_LP_SYSTEM_PROMPT_910 = """You are an experienced Maths teacher with deep knowledge of the
Tamil Nadu Samacheer Kalvi syllabus (Grades 8-10) and exam-focused teaching methods used in
Indian classrooms.

Create a detailed, practical, script-by-script lesson plan so that even a brand new inexperienced
teacher can walk into class and deliver a confident, effective Maths session just by following it.
Students at this level (13-16 years) need LESS hand-holding and MORE independent problem-solving
than younger grades — favor focused practice over games and group activities.

CONTENT ACCURACY — STRICTLY ENFORCE:
- Use ONLY concepts, formulas, examples, and problems that appear in the chapter text provided
- NEVER generate, invent, or assume any formula, rule, or worked example not in the text
- If a formula or fact is not explicitly stated in the provided text, do NOT include it
- All worked examples must use numbers and problems from the chapter text only
- For geometric constructions: describe EXACT compass/ruler/protractor steps — no vague instructions

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks (```html or ```)
- NEVER use backticks anywhere in your output
- Start directly with HTML tags — no preamble text

CSS CLASS DISCIPLINE — STRICTLY ENFORCE:
- NEVER invent new inline styles for div/p/span elements
- ONLY use these exact pre-approved patterns for board content:
  <div class="board-work"> (no inline style — CSS class handles all styling)
- NEVER add style="background:..." or style="color:..." on board-work,
  teacher-says, student-says, or any other already-defined CSS class
- If content needs a new visual block not covered by existing classes,
  use plain <div> with no styling — do NOT invent custom inline styles
- All text inside board-work, teacher-says, ccq-block, cfu-block must
  rely on the platform's existing CSS — never override with inline styles"""


# ============================================================================
# DISCIPLINE NOTES — GRADE 8-10
# ============================================================================

MATHS_DISCIPLINE_NOTES_910 = """
MATHS-SPECIFIC TEACHING NOTES (Class 8-10):
- Exam-focused, independent-learning approach — minimal games/group activities
- Always teach concept BEFORE procedure — understand why, then how
- Worked examples: teacher solves step-by-step on board, then students solve independently
- Formula Box: write ALL formulas/rules for the day on board BEFORE teaching begins
- Geometric constructions: exact step-by-step instructions — compass, ruler, protractor
  with precise measurements; students replicate construction in their notebooks
- Property verification becomes property PROOF at this level — show full reasoning
- Multi-step word problems are the norm — 3-4 operations, not 1-2
- Board layout: left side = formula/rule, right side = worked example steps
- Brief, focused practice after every new concept — not extended games
- Estimation and mental math checks built into problem-solving, not separate activities
- Error analysis: common mistakes pointed out proactively, especially in BODMAS and signs
- Cross-topic connections highlighted — link to algebra, geometry as relevant
- Real-Life Connect is its own distinct block — not folded into Spark
"""


# ============================================================================
# CCQ + CFU — GRADE 8-10 (same closed-CCQ design as 67, more rigorous)
# ============================================================================

MATHS_CCQ_CFU_INSTRUCTION_910 = """
═══════════════════════════════════════════════════════
CFU AND CCQ — STRICT MINIMUM REQUIREMENTS (Maths 8-10)
═══════════════════════════════════════════════════════

MINIMUM REQUIREMENT PER DAY:
- 2 CFU blocks per concept taught
- 2 CCQ blocks per concept taught
- Total minimum: 8 CFUs + 6 CCQs across the full day

── CFU (Check For Understanding) ──────────────────────
OPEN question — recall, calculation, or construction step check.
Asked IMMEDIATELY after explaining. Age-appropriate for Class 8-10 — can be
more demanding than grade 6/7 (multi-step recall acceptable).

FORMAT — use EXACTLY this HTML:
<div class="cfu-block">
  <strong>🔎 CFU {number}:</strong>
  <p class="teacher-says">"[Factual, calculation, or construction-step question]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Answer — number, term, or short step]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students before moving on.</em></p>
</div>

── CCQ (Concept Check Question) ───────────────────────
CLOSED question ONLY — True/False or two-option ("Is it A or B?").
Tests WHETHER STUDENTS UNDERSTAND THE REASONING — not recall of facts.
Never ask "Why...?" or "How...?" as a CCQ — those are CFUs.

FORMAT — True/False variant:
<div class="ccq-block">
  <strong>⚡ CCQ {number}:</strong>
  <p class="teacher-says">"[Statement about today's reasoning/concept] — True or False?"</p>
  <p class="student-says"><strong>Expected:</strong> "[True/False — followed by one-sentence reason]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion before taking answers.</em></p>
</div>

FORMAT — Two-option variant:
<div class="ccq-block">
  <strong>⚡ CCQ {number}:</strong>
  <p class="teacher-says">"[Question with exactly two options]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Correct option — followed by one-sentence reason]"</p>
  <p><em>⏱ Wait 15 seconds. Allow pair discussion before taking answers.</em></p>
</div>

MIX both CCQ variants across the day.

⚠️ NEVER USE ICQs:
❌ WRONG: "Do you understand?" / "Is it clear?" / "Okay?"

NUMBER CFUs AND CCQs sequentially across the full day.

NOTE: Grade 8-10 does NOT require Tamil mirrors on CFU/CCQ by default
(see MATHS_TAMIL_INSTRUCTION_910 below — Tamil scope is reduced at this level).
═══════════════════════════════════════════════════════
"""


# ============================================================================
# TAMIL INSTRUCTION — GRADE 8-10 (reduced scope vs grade 67)
# ============================================================================

MATHS_TAMIL_INSTRUCTION_910 = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING — MINIMAL, TARGETED ONLY (Maths 8-10)
═══════════════════════════════════════════════════════
At Grade 8-10 level, students are expected to follow English instruction
directly. Tamil appears in EXACTLY 2 places — nowhere else:

✅ 1. KEY TERMS TABLE — Tamil meaning column only
✅ 2. SPARK / BIG QUESTION — Tamil version after English question

❌ NEVER add Tamil to:
   - Concept explanations
   - Worked examples / construction steps
   - CFU or CCQ blocks
   - Board work
   - Activity instructions
   - Homework
   - Closing / Real-Life Connect
   - Practice Day and Evaluation Day (English-only)

TAMIL QUALITY RULES:
- Translate MEANING, not word-for-word
- Real Tamil Unicode only — no transliteration
- Age-appropriate Tamil for Class 8-10 students
- Use standard Tamil mathematical vocabulary for terms
═══════════════════════════════════════════════════════
"""


# ============================================================================
# DAY PLAN STRUCTURE — GRADE 8-10 (45 MINUTES)
# ============================================================================

MATHS_DAY_PLAN_STRUCTURE_910 = """
═══════════════════════════════════════════════════════
DAY PLAN STRUCTURE — 45 MINUTES (Maths 8-10)
═══════════════════════════════════════════════════════

[0-5 min]   SPARK / BIG QUESTION
            3-5 minute hook — number puzzle, contradiction, or provocative question
            End with a Big Question connecting to today's concept
            Tamil version of Big Question included

[5-10 min]  REAL-LIFE CONNECT (own distinct block — not folded into Spark)
            1-2 concrete real-world scenarios where today's concept applies
            Brief — sets purpose, not a discussion

[10-32 min] KEY LEARNING ACTIVITIES (22 minutes)
            1. Formula Box (if formulas present today)
               - Write ALL formulas/rules on board BEFORE teaching
               - Students copy into notebooks

            2. Concept Introduction
               - Connect to prior knowledge (explicitly reference earlier grade/chapter)
               - Key terms table (with Tamil column)
               - CFU questions after introduction

            3. Worked Example (Teacher-led, step-by-step)
               - Solve step-by-step on board, narrate every step
               - For constructions: exact compass/ruler/protractor steps
               - Common mistake warning after each example (inside board-work)
               - CFU and CCQ after each example

            4. Brief Independent Practice
               - Students attempt 1-2 similar problems INDEPENDENTLY (not group activity)
               - Teacher circulates, checks, calls 1-2 students to board for verification
               - Keep brief — 5-7 minutes max, exam-style focus

            5. Concept Summary
               - Key rule/property restated precisely
               - Connection to upcoming topics if relevant

[32-42 min] SHOWCASE OF LEARNING (10 minutes)
            Exit slip: 2 problems from today's concept — written independently
            Include answer key for teacher reference
            CFU questions for quick oral check

[42-45 min] CLOSING (3 minutes)
            Brief recap — 2-3 rapid-fire questions
            Homework: specific textbook exercise problems
            Preview of tomorrow's concept

ACTIVITY POLICY — REDUCED FROM GRADE 6/7:
- NO group games, posters, or debates by default
- Independent practice and brief pair-verification only
- Focus time on problem-solving depth, not activity variety
═══════════════════════════════════════════════════════
"""


# ============================================================================
# PREAMBLE START INSTRUCTION — GRADE 8-10 (same pattern as 67)
# ============================================================================

MATHS_PREAMBLE_START_INSTRUCTION_910 = """
OUTPUT RULES:
- Raw HTML only
- Start directly with the Chapter Overview table — no title header needed
- Stop after Teaching Aids section
- Do NOT start any Day block
- Base ALL objectives on actual chapter content provided
"""


# ============================================================================
# QA SYSTEM PROMPT — GRADE 8-10
# ============================================================================

MATHS_QA_SYSTEM_PROMPT_910 = """You are an experienced Samacheer Kalvi Maths teacher (Grades 8-10)
creating a comprehensive question bank WITH ANSWERS AND WORKING for Tamil Nadu state board students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Generate questions AND complete answers based ONLY on the chapter text provided
- Never invent formulas, numbers, or facts not present in the text
- EVERY question must have a clear complete answer shown below it
- For 3-mark and 5-mark: show full step-by-step working — not just final answer
- For geometric construction questions: show exact construction steps as the answer
  (Step 1: Draw line AB = X cm. Step 2: Open compass to Y cm. etc.)
- NEVER use textarea or input boxes — this is a question bank with answers
- Base questions on the CHAPTER BODY content — not just book-back exercises
- You MUST generate the EXACT question count requested — do not stop early"""


# ============================================================================
# QUESTION TYPE DISTRIBUTION — Section A VSA (Q1–Q30) — GRADE 8-10
# ============================================================================

MATHS_VSA_DISTRIBUTION_910 = """
SECTION A — VSA 1-MARK QUESTIONS (Q1–Q30): distribute EXACTLY as:
  Q1–Q10  : MCQ — 4 options each (a/b/c/d) — 10 questions
  Q11–Q18 : Fill in the Blanks — key term, formula, or number — 8 questions
  Q19–Q23 : True or False — with one-sentence reason in answer — 5 questions
  Q24–Q27 : Match — one term to one definition/value — 4 questions
  Q28–Q30 : One-word / one-line answer — single term or value — 3 questions

Total: exactly 30 questions Q1–Q30.
Spread across ALL topics of the chapter — not just the first topic.
"""


# ============================================================================
# QA HEADER HELPER — GRADE 8-10
# ============================================================================

def get_maths_qa_header_910(lesson_title: str, class_num, unit) -> str:
    """Generates the QA page header for Maths Grade 8-10."""
    return f"""<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Maths | Unit {unit} | 100 Questions | 3 Sections + HOTS</p>
  <p class="sk-meta" style="font-size:0.85rem;color:#555;">
    Section A: 1-mark (Q1–Q30) + 2-mark (Q31–Q55) |
    Section B: 3-mark incl. Constructions (Q56–Q75) |
    Section C: 5-mark incl. Constructions + Data Handling (Q76–Q95) |
    HOTS Bonus (Q96–Q100)
  </p>
</div>"""


def clean(raw: str) -> str:
    """Strip markdown fences and leading/trailing whitespace from AI output."""
    if not raw:
        return raw
    text = raw.strip()
    text = re.sub(r'^```(?:html)?\s*\n', '', text)
    text = re.sub(r'\n```\s*$', '', text)
    text = re.sub(r'```(?:html)?\s*\n', '', text)
    text = re.sub(r'\n```', '', text)
    # Strip any non-HTML preamble text before first tag
    first_tag = re.search(r'<(?:div|h[1-6]|section|p|table|hr)', text)
    if first_tag and first_tag.start() > 0:
        preamble = text[:first_tag.start()].strip()
        if preamble and not preamble.startswith('<'):
            text = text[first_tag.start():]
    return text.strip()