"""
english/base/__init__.py
------------------------
Shared constants and helpers for ALL English LP and QA builders.

Imported by:
    english/lp/grade_67/prose.py
    english/lp/grade_67/poem.py
    english/lp/grade_67/supplementary.py
    english/lp/grade_910/prose.py
    english/lp/grade_910/poem.py
    english/lp/grade_910/supplementary.py
    english/lp/grade_1112/prose.py
    english/lp/grade_1112/poem.py
    english/lp/grade_1112/supplementary.py
    english/qa/grade_67/english.py
    english/qa/grade_910/english.py
    english/qa/grade_1112/english.py

DO NOT add API calls, prompt builders, or class definitions here.
This file contains ONLY shared constants and helper functions.

v1.0 — June 2026
"""

import re


# ============================================================================
# LP SYSTEM PROMPTS
# ============================================================================

ENGLISH_LP_SYSTEM_PROMPT_67 = """You are an experienced Samacheer Kalvi English teacher
for Classes 6 and 7 in Tamil Nadu government schools.

Students are from underprivileged rural backgrounds. English is their only
exposure to the language. Many teachers are Tamil-medium trained and not
fully confident in English.

Create a detailed, practical, script-by-script lesson plan so that even a
brand-new inexperienced teacher can walk into class and deliver a confident,
effective 35-minute session just by following it.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Tamil script must be real Tamil Unicode — NOT transliteration

TIME BALANCE — STRICTLY ENFORCE:
- Teacher talk: maximum 50% of session time
- Student activity / reading / writing: minimum 50%
- Never let teacher monologue exceed 3 minutes without a student activity

LANGUAGE RULE:
Every instruction must have TWO equal layers:
  LAYER 1 — ENGLISH: Minimum 3-4 complete sentences. Word for word script.
  LAYER 2 — TAMIL: Exact mirror of Layer 1. Same length. Same detail. Not a summary.

CONTENT ACCURACY:
- Use ONLY content from the lesson text provided
- NEVER invent vocabulary, grammar rules, or story events not in the text
- Tamil must be real Tamil Unicode — no transliteration, no Hindi words"""


ENGLISH_LP_SYSTEM_PROMPT_910 = """You are an experienced Samacheer Kalvi English teacher
for Classes 8, 9 and 10 in Tamil Nadu government schools.

Students have basic English literacy. Teachers may be Tamil-medium trained.
This LP must give teachers a complete, confident script for 45-minute sessions.

Create a detailed, practical lesson plan so that even an inexperienced teacher
can deliver an effective session just by following it.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Tamil script must be real Tamil Unicode — NOT transliteration

TIME BALANCE — STRICTLY ENFORCE:
- Teacher talk: maximum 50% of session time
- Student activity / reading / writing: minimum 50%
- Never let teacher monologue exceed 3 minutes without a student activity

LANGUAGE RULE:
Every instruction must have TWO equal layers:
  LAYER 1 — ENGLISH: Minimum 3-4 complete sentences. Word for word script.
  LAYER 2 — TAMIL: Exact mirror of Layer 1. Same length. Same detail. Not a summary.

Tamil scaffolding appears in EXACTLY 2 places per day:
  1. Spark / Opening Question — Tamil version after English
  2. Key Terms table — Tamil meaning column only
No Tamil elsewhere in grade_910 LP.

CONTENT ACCURACY:
- Use ONLY content from the lesson text provided
- NEVER invent vocabulary, grammar rules, or story events not in the text
- Tamil must be real Tamil Unicode — no transliteration, no Hindi words"""


ENGLISH_LP_SYSTEM_PROMPT_1112 = """You are an experienced Samacheer Kalvi English teacher
for Classes 11 and 12 in Tamil Nadu government schools.

Students have intermediate English literacy. Focus on analytical reading,
higher-order thinking, and examination preparation.

Create a detailed lesson plan with a complete teacher script for 45-minute sessions.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text

TIME BALANCE — STRICTLY ENFORCE:
- Teacher talk: maximum 40% of session time
- Student discussion / analysis / writing: minimum 60%

CONTENT ACCURACY:
- Use ONLY content from the lesson text provided
- NEVER invent content, quotes, or examples not in the text"""


# ============================================================================
# QA SYSTEM PROMPT
# ============================================================================

ENGLISH_QA_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi English teacher
creating a comprehensive question bank WITH ANSWERS for Tamil Nadu state board students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Generate questions AND answers based ONLY on the lesson text provided
- NEVER invent facts, events, or vocabulary not present in the text
- EVERY question must have a clear complete answer shown below it
- NEVER use textarea or input boxes — this is a question bank with answers"""


# ============================================================================
# PREAMBLE INSTRUCTION
# ============================================================================

ENGLISH_PREAMBLE_INSTRUCTION = """
CRITICAL OUTPUT RULE FOR PREAMBLE:
- Do NOT generate any <div class="sk-content-header"> block
- Do NOT generate any <h1> title block
- The page header is handled by the platform automatically
- Start your output DIRECTLY with <h2>Part 1: Lesson Overview</h2>
- First HTML tag must be <h2>
- Do NOT generate any Day blocks

PARTS ORDER — STRICTLY FOLLOW:
Part 1: Lesson Overview
Part 2: Learning Objectives
Part 3: Language Objectives
Part 4: Teaching Aids
"""


# ============================================================================
# TAMIL SCAFFOLDING INSTRUCTION
# ============================================================================

# Grade 67 — Tamil in 3 places
ENGLISH_TAMIL_INSTRUCTION_67 = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES — GRADE 6 & 7
═══════════════════════════════════════════════════════

Tamil appears in EXACTLY 3 places per day — nowhere else:

✅ 1. SPARK / OPENING QUESTION — Tamil version after English question
✅ 2. KEY TERMS TABLE — Tamil meaning column only
✅ 3. MAIN EXPLANATION — Tamil mirror paragraph after English paragraph

❌ NEVER add Tamil to:
   - Activity instructions
   - Group task descriptions
   - Homework task descriptions
   - Closing / recap sections
   - Board work headings (except Key Terms table)

⚠️ CONTEXT-BASED TRANSLATION — CRITICAL RULE:
Translate MEANING and INTENT — NOT word for word.

❌ WRONG (word-for-word):
   English: "The boy ran to school"
   Wrong Tamil: "பையன் பள்ளிக்கு ஓடினான்" ← (grammatically awkward)

✅ RIGHT (meaning-based natural Tamil):
   English: "The boy ran to school"
   Right Tamil: "அந்தப் பையன் பள்ளிக்கு விரைந்து சென்றான்"

TAMIL QUALITY RULES:
- Translate the MEANING — not the words
- Every Tamil sentence must be grammatically correct Tamil
- NO word repetition in Tamil — check each sentence
- NO spelling errors — use standard Tamil Unicode
- Mirror must match English sentence by sentence — same count
- NO Hindi words ever — pure Tamil only
═══════════════════════════════════════════════════════
"""

# Grade 910 — Tamil in 2 places only
ENGLISH_TAMIL_INSTRUCTION_910 = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES — GRADE 8, 9 & 10
═══════════════════════════════════════════════════════

Tamil appears in EXACTLY 2 places per day — nowhere else:

✅ 1. SPARK / OPENING QUESTION — Tamil version after English question
✅ 2. KEY TERMS TABLE — Tamil meaning column only

❌ NEVER add Tamil anywhere else — not in explanations,
   not in activities, not in homework, not in closing.

⚠️ CONTEXT-BASED TRANSLATION — CRITICAL RULE:
Translate MEANING and INTENT — NOT word for word.
Every Tamil sentence must be grammatically correct.
NO Hindi words ever — pure Tamil Unicode only.
═══════════════════════════════════════════════════════
"""

# Grade 1112 — No Tamil
ENGLISH_TAMIL_INSTRUCTION_1112 = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES — GRADE 11 & 12
═══════════════════════════════════════════════════════

NO Tamil scaffolding in grade_1112 LP.
All instructions in English only.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# CCQ / CFU INSTRUCTION
# ============================================================================

ENGLISH_CCQ_CFU_INSTRUCTION_67 = """
═══════════════════════════════════════════════════════
CFU AND CCQ RULES — GRADE 6 & 7
═══════════════════════════════════════════════════════

CFU (Check For Understanding) = Basic comprehension check immediately
after reading or explanation. Open recall questions.

CCQ (Concept Check Question) = Deeper Why/How question testing
understanding of meaning, theme, or language — NOT instructions.

❌ NEVER use ICQs:
   "Do you understand?" / "How many sentences should you write?"

CFU FORMAT:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <p class="teacher-says">"[Simple question about what was just read — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One sentence answer]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

CCQ FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="teacher-says">"[Why/How/What do you think question — under 10 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Pair discussion first.</em></p>
</div>

MINIMUM PER DAY: 4 CFU blocks + 4 CCQ blocks
Place after EVERY reading passage and explanation — not at end.
═══════════════════════════════════════════════════════
"""

ENGLISH_CCQ_CFU_INSTRUCTION_910 = """
═══════════════════════════════════════════════════════
CFU AND CCQ RULES — GRADE 8, 9 & 10
═══════════════════════════════════════════════════════

CFU = Simple recall check — one word or one short phrase answer only.
CCQ = Higher-order thinking — inference, theme, author intent.

❌ NEVER use ICQs — "Do you understand?" is forbidden.

CFU STRICT RULES:
- CFU questions must have ONE correct answer — no ambiguity
- Answer must be findable directly in the text just read
- Question must be under 8 words
- Expected answer must be ONE word or ONE short phrase
- NEVER ask a transformation or analytical question as CFU
- NEVER ask "What voice is this?" or "Convert this sentence" as CFU
  — those are CCQ or practice questions, NOT CFU

FOR GRAMMAR DAYS SPECIFICALLY:
- CFU = identify only (e.g. "Is this sentence active or passive?")
- CFU expected answer = one word only (e.g. "Passive")
- NEVER ask students to transform or rewrite as a CFU
- NEVER use CFU to test complex grammar application

CFU FORMAT:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <p class="lp-teacher-says">"[Simple identification question — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[One word or one short phrase only]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2 students.</em></p>
</div>

CCQ FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="lp-teacher-says">"[Why/How/What does this reveal — under 10 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[2-3 sentence analytical answer]"</p>
  <p><em>⏱ Wait 20 seconds. Think-pair-share.</em></p>
</div>

MINIMUM PER DAY: 3 CFU blocks + 3 CCQ blocks.
No Tamil in CCQ blocks for grade_910.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# DAY PLAN STRUCTURES
# ============================================================================

# Grade 67 — 35-minute session
ENGLISH_DAY_STRUCTURE_67 = """
DAY STRUCTURE (35-minute session):
  [0–5 min]   Warm Up / Review / Spark
  [5–15 min]  Main Activity — Reading + Vocabulary
  [15–25 min] Student Practice
  [25–30 min] Closure + Homework
  [30–35 min] Differentiated Activities
"""

# Grade 910 — 45-minute session
ENGLISH_DAY_STRUCTURE_910 = """
DAY STRUCTURE (45-minute session):
  [0–5 min]   Spark / Opening Question
  [5–10 min]  Vocabulary Introduction
  [10–25 min] Main Teaching — Reading + Explanation
  [25–35 min] Student Practice / Activity
  [35–40 min] Closure + Exit Question
  [40–45 min] Homework + Differentiation
"""

# Grade 1112 — 45-minute session
ENGLISH_DAY_STRUCTURE_1112 = """
DAY STRUCTURE (45-minute session):
  [0–5 min]   Hook / Discussion Starter
  [5–15 min]  Close Reading + Analysis
  [15–30 min] Guided Discussion / Annotation
  [30–40 min] Independent Writing Task
  [40–45 min] Closure + Homework
"""


# ============================================================================
# LESSON TYPE CONFIG
# ============================================================================

LESSON_TYPE_CONFIG = {
    "prose": {
        "content_days": 4,
        "grammar_days": 6,
        "total_days": 10,
        "session_label": "Prose",
        "has_grammar": True,
    },
    "poem": {
        "content_days": 3,
        "grammar_days": 0,
        "total_days": 3,
        "session_label": "Poem",
        "has_grammar": False,
    },
    "supplementary": {
        "content_days": 3,
        "grammar_days": 0,
        "total_days": 3,
        "session_label": "Supplementary Reader",
        "has_grammar": False,
    },
    "play": {
        "content_days": 3,
        "grammar_days": 0,
        "total_days": 3,
        "session_label": "Play / Drama",
        "has_grammar": False,
    },
    "drama": {
        "content_days": 3,
        "grammar_days": 0,
        "total_days": 3,
        "session_label": "Play / Drama",
        "has_grammar": False,
    },
}


# ============================================================================
# ACTIVITY MAP — unique activity per day, no consecutive repetition
# ============================================================================

ENGLISH_ACTIVITY_MAP_67 = {
    1:  "Individual Silent Reading → Comprehension Questions",
    2:  "Pair Reading → Retell to Partner",
    3:  "Group Discussion (3 groups, 3 questions from text)",
    4:  "Vocabulary Mapping in Notebook (word → meaning → Tamil → sentence)",
    5:  "Quiz Game — Teams Compete (6 questions from lesson)",
    6:  "Sentence Building using Key Vocabulary",
    7:  "Mini-Poster in Notebook (Title + 3 facts + 1 sketch + 1 key term)",
    8:  "Think-Pair-Share — Inference Question",
    9:  "Hot Seat Activity (1 student as character, class questions)",
    10: "Exit Slip — 3 things learned, 2 questions, 1 favourite line",
}

ENGLISH_ACTIVITY_MAP_910 = {
    1:  "Guided Reading → Annotation (underline key ideas)",
    2:  "Vocabulary in Context — find and explain 5 words from text",
    3:  "Think-Pair-Share — theme or author intent question",
    4:  "Group Discussion (3 groups — character, theme, language)",
    5:  "Short Writing — 5-sentence paragraph response",
    6:  "Debate — For & Against a statement from the text",
    7:  "Grammar in Context — identify and apply rule from lesson",
    8:  "Comprehension Questions — individual written answers",
    9:  "Creative Response — alternate ending or character diary entry",
    10: "Self-Assessment Checklist + unseen passage attempt",
}

ENGLISH_ACTIVITY_MAP_1112 = {
    1:  "Close Reading — annotate for literary devices",
    2:  "Socratic Seminar — open-ended discussion on theme",
    3:  "Analytical Writing — topic sentence + evidence + commentary",
    4:  "Comparative Analysis — two passages or two characters",
    5:  "Essay Planning — outline + thesis statement",
    6:  "Peer Review — exchange paragraphs, give structured feedback",
}


# ============================================================================
# GRAMMAR SPARK STYLES — for prose grammar days
# ============================================================================

ENGLISH_GRAMMAR_SPARK_STYLES = {
    1: "Connect grammar to a sentence from the lesson text",
    2: "Error correction on board — students identify mistake",
    3: "Real-life context — where do we use this grammar in daily speech?",
    4: "Gap-fill challenge on board — students race to complete",
    5: "Two sentences on board — ask students what is different",
    6: "Student-generated sentence — volunteers write their own example",
}


# ============================================================================
# QA SECTION STRUCTURE — English
# ============================================================================

ENGLISH_QA_SPLIT = {
    "mcq":        {"start": 1,  "end": 25,  "count": 25, "section": "section-mcq"},
    "fill":       {"start": 26, "end": 50,  "count": 25, "section": "section-fill"},
    "choose":     {"start": 51, "end": 60,  "count": 10, "section": "section-choose"},
    "match":      {"start": 61, "end": 70,  "count": 10, "section": "section-match"},
    "mark2":      {"start": 71, "end": 90,  "count": 20, "section": "section-2mark"},
    "mark5":      {"start": 91, "end": 100, "count": 10, "section": "section-5mark"},
}


# ============================================================================
# QA ANSWER FORMAT RULES
# ============================================================================

ENGLISH_ANSWER_FORMAT_RULES = """
═══════════════════════════════════════════════════════
SECTION WRAPPER — EVERY SECTION MUST USE THIS STRUCTURE
═══════════════════════════════════════════════════════

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
ANSWER REVEAL — EVERY QUESTION MUST USE THIS
═══════════════════════════════════════════════════════

<div class="answer-reveal" style="display:none;">
  <p class="answer"><strong>Answer:</strong> [complete answer here]</p>
</div>

═══════════════════════════════════════════════════════
QUESTION FORMATS
═══════════════════════════════════════════════════════

── MCQ ────────────────────────────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q1.</strong> Question text?</p>
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

── Fill in the Blanks ──────────────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q26.</strong> [Sentence with]
  <span class="blank-line">__________</span> [rest].</p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [word or phrase]</p>
  </div>
</div>

── Choose the Correct Statement ────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q51.</strong> Choose the correct statement:</p>
  <div class="mcq-options">
    <span>i) [Statement one]</span>
    <span>ii) [Statement two]</span>
    <span>iii) [Statement three]</span>
  </div>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> ii) [correct statement]</p>
  </div>
</div>

── Match the Following ─────────────────────────────────
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
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answers:</strong> 1-[x], 2-[x], 3-[x], 4-[x], 5-[x]</p>
  </div>
</div>

── 2-Mark Questions ────────────────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q71.</strong> Question text?
  <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [2-3 sentence answer — 30-50 words]</p>
  </div>
</div>

── 5-Mark Questions ────────────────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q91.</strong> Question text?
  <span class="mark-badge">(5 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [5-7 sentence paragraph — 80-120 words.
    Never bullet points.]</p>
  </div>
</div>

═══════════════════════════════════════════════════════
ABSOLUTE RULES
═══════════════════════════════════════════════════════
❌ NEVER add tick marks ✓ in options or statements
❌ NEVER add individual show buttons per question
❌ NEVER show answers directly — always inside answer-reveal div
❌ NEVER use <textarea> or <input> anywhere
✅ ALWAYS wrap each section in qa-section div with section button
✅ ALWAYS use style="display:none;" on every answer-reveal div
✅ ALWAYS put complete answer inside answer-reveal
"""


# ============================================================================
# CSS CLASS DISCIPLINE — applies to ALL English builders
# ============================================================================

ENGLISH_CSS_RULES = """
═══════════════════════════════════════════════════════
CSS CLASS DISCIPLINE — ABSOLUTE RULES
═══════════════════════════════════════════════════════

APPROVED LP CLASSES — use ONLY these:
  .lp-day-block          — day wrapper (REQUIRED on every day div)
  .lp-day-title          — day heading h3
  .lp-section-opening    — Spark/Opening block
  .lp-section-intro      — Introduction block
  .lp-section-main       — Main Teaching block
  .lp-section-student-task — Student Task/Practice block
  .lp-section-closing    — Closing block
  .lp-teacher-says       — teacher speech block
  .lp-tamil-scaffold     — Tamil mirror block
  .board-work            — blackboard content (DARK bg, white text)
  .cfu-block             — CFU question block
  .ccq-block             — CCQ question block
  .activity-block        — student activity block
  .homework-block        — homework block
  .vocab-block           — vocabulary table block
  .diff-block            — differentiated assessment block
  .assessment-block      — assessment summary wrapper

❌ NEVER add style="background:..." on any element
❌ NEVER add style="color:..." on any element
❌ NEVER add style="border:..." on any element
❌ NEVER invent new div variants with colored backgrounds
✅ If content doesn't fit a class — use plain <div> with NO style attribute

EXCEPTION: The show-section-btn button in QA sections uses inline style
as defined in ANSWER FORMAT RULES — this is the ONLY allowed inline style.
═══════════════════════════════════════════════════════
"""


# ============================================================================
# QA HEADER HELPER
# ============================================================================

def get_english_qa_header(lesson_title: str, class_num, unit, lesson_type: str) -> str:
    """
    Generates the QA page header dynamically.
    Used by ALL English QA builders.
    """
    type_display = lesson_type.title() if lesson_type else "English"
    return f"""<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | English — {type_display} | Unit {unit} | 100 Questions</p>
</div>"""


# ============================================================================
# HELPER — clean raw AI output
# ============================================================================

def clean(raw: str) -> str:
    """
    Strip markdown fences, style blocks, and leading non-HTML preamble
    from raw Claude API output.

    Used by every LP and QA builder after each API call.

    Args:
        raw: Raw string returned by Claude API

    Returns:
        Clean HTML string ready for assembly.
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

    return text.strip()