"""
ss_lp_base.py
-------------
Shared constants and helpers for all SS LP builders.

Imported by:
    ss/lp/grade_910/history.py
    ss/lp/grade_910/civics.py
    ss/lp/grade_910/geography.py
    ss/lp/grade_910/economics.py
    ss/lp/grade_67/history.py
    ss/lp/grade_67/civics.py
    ss/lp/grade_67/geography.py
    ... (all grade groups, all disciplines)

DO NOT add any API calls, prompt builders, or class definitions here.
This file contains ONLY shared constants and the clean() helper.

Usage in each builder:
    from ...base.ss_lp_base import (
        SS_LP_SYSTEM_PROMPT,
        CCQ_INSTRUCTION,
        TAMIL_INSTRUCTION,
        SPARK_STYLES,
        STUDENT_TASK_STYLES,
        FOCUS_MAP,
        ACTIVITY_MAP,
        clean,
    )

v2.0 — May 2026
Changes from v1.0:
    ✅ ACTIVITY_MAP: unique activity per day — no repetition
    ✅ TAMIL_INSTRUCTION: context-based translation rule added
    ✅ STUDENT_TASK_STYLES: student participation increased
    ✅ TIME_BALANCE: teacher 50% / student 50% rule added
    ✅ All existing QA constants preserved — no breakage
"""

import re


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SS_LP_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Social Science teacher
with deep knowledge of Tamil Nadu state board curriculum and activity-based
learning methods used in Indian government schools.

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
- Teacher talk: maximum 50% of session time (17-18 minutes)
- Student activity / discussion / writing: minimum 50% (17-18 minutes)
- Never let teacher monologue exceed 3 minutes without a student activity
- After every explanation: student responds, writes, discusses, or answers

CONTENT ACCURACY — STRICTLY ENFORCE:
- Use ONLY facts, figures, numbers, and statistics that appear VERBATIM in the chapter text provided
- NEVER generate, estimate, or invent any number, measurement, area, population, date, or statistic
- If a fact is not explicitly stated in the chapter text, do NOT include it
- This applies to all disciplines: History, Geography, Civics, Economics"""


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
# CCQ INSTRUCTION BLOCK
# ============================================================================

CCQ_INSTRUCTION = """
═══════════════════════════════════════════════════════
CCQ — CONCEPT CHECK QUESTIONS (CRITICAL RULES)
═══════════════════════════════════════════════════════

You MUST include exactly 10 CCQs spread randomly throughout this day's content.

WHAT IS A CCQ?
A CCQ (Concept Check Question) checks if students understood the SUBJECT MATTER
just taught. It is NOT about instructions or tasks.

⚠️ CRITICAL DIFFERENCE — READ THIS CAREFULLY:

❌ ICQ (Instruction Check Question) — WRONG, DO NOT USE:
   "Do you understand what you need to do?"
   "How many sentences should you write?"
   "Do you know which group you are in?"
   These check if students understood the TASK. We do NOT want these.

✅ CCQ (Concept Check Question) — CORRECT, USE ONLY THESE:
   "What triggered the assassination of Archduke Franz Ferdinand?"
   "Which two alliance systems faced each other in World War I?"
   "Name one consequence of the Treaty of Versailles."
   These check if students understood the CONTENT just taught.

RULES for CCQs:
- Every CCQ must be about the subject matter just explained — not the activity
- Keep each CCQ under 8 words
- Place them RANDOMLY — after explaining a concept, after a flowchart, after activity
- No two CCQs should repeat each other
- Tamil version mandatory for every CCQ

FORMAT — use this exact HTML block:
<div class="ccq-block">
  <strong>⚡ CCQ (Concept Check):</strong>
  <p class="teacher-says">"[Short factual question about content just taught — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Short factual answer — 1-2 sentences]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
</div>
═══════════════════════════════════════════════════════
"""


# ============================================================================
# TAMIL SCAFFOLDING INSTRUCTION — v2.0
# Context-based translation added (teacher feedback May 2026)
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

⚠️ CONTEXT-BASED TRANSLATION — CRITICAL RULE (NEW):
Translate meaning and intent — NOT word for word.

❌ WRONG (word-for-word — gives wrong meaning):
   English: "Discuss with your pair"
   Wrong Tamil: "உங்கள் ஜோடியோடு ஓடு" ← (means "run with your pair")

✅ RIGHT (meaning-based — natural Tamil):
   English: "Discuss with your pair"
   Right Tamil: "உங்கள்짝குடன் கலந்தாலோசியுங்கள்" ← (correct meaning)

More examples:
   English: "The war broke out in 1914"
   ❌ Wrong: "போர் உடைந்தது 1914ல்"
   ✅ Right: "1914ஆம் ஆண்டு போர் வெடித்தது"

   English: "The treaty was signed"
   ❌ Wrong: "உடன்படிக்கை கையொப்பமிடப்பட்டது" (overly formal, confusing)
   ✅ Right: "உடன்படிக்கை ஏற்படுத்தப்பட்டது" (natural, clear)

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
# SPARK STYLES — fixed per day, Claude fills the content
# ============================================================================

SPARK_STYLES = {
    1: {
        "style": "Real-life Analogy",
        "instruction": """Use a real-life analogy or relatable scenario from everyday Indian life
to connect to today's topic. Make it feel close to the student's world.
End with one opening question that sparks curiosity.
Example structure: 'Imagine you are... / Think about when... → Opening question'""",
    },
    2: {
        "style": "Picture / Image + Reflection",
        "instruction": """Describe a specific image or visual related to today's topic
(as if showing it on the board or projector).
Tell the teacher exactly what image to draw or display and what to ask about it.
End with one reflection question students think about before answering.
Example structure: 'Show this image: [describe clearly] → What do you see?
What does this tell us about...?'""",
    },
    3: {
        "style": "Video Clip Description + Discussion (with No-Tech Alternate)",
        "instruction": """Describe a short video clip (60-90 seconds) the teacher can find on YouTube
that directly connects to today's topic. Give the search keywords.
After the clip: ask students 2 quick reaction questions.
Example structure: 'Play this clip: [YouTube search: "..."] →
What did you notice? How does this connect to...?'

⚠️ NO-TECH ALTERNATE (for classes without video facility):
If video is not available, use this instead:
Teacher reads aloud a dramatic 3-4 sentence description of the key event.
Make it vivid — dates, names, action.
Then ask: 'What do you think happened next? How would YOU have reacted?'
End with the same Big Question connecting to today's sections.""",
    },
    4: {
        "style": "Historical Quote / Headline + Reaction",
        "instruction": """Open with a powerful real historical quote OR a dramatic newspaper headline
from the era of today's topic. Write it on the board.
Ask students: What does this tell us? Who said this and why?
Example structure: Board: "[Quote or Headline]" →
Teacher asks: What does this mean? What do you think happened next?'""",
    },
    5: {
        "style": "Rapid Recall Quiz",
        "instruction": """Start with a 5-question rapid-fire quiz reviewing the key facts from Days 1-4.
Read questions aloud — students answer on a slip of paper or call out.
This activates prior knowledge and sets up the evaluation day.
Example structure: '5 quick questions → students write answers →
teacher reveals → quick discussion of any gaps'""",
    },
}


# ============================================================================
# STUDENT TASK STYLES — fixed per day, no consecutive repetition
# v2.0: Student participation time increased, clearer instructions
# ============================================================================

STUDENT_TASK_STYLES = {
    1: {
        "style": "Individual Written Answer",
        "instruction": """Students open their notebooks and write independently — 5 minutes.
Give a clear specific prompt — not open-ended.
Give a time limit. Give a model sentence starter on the board.
Teacher circulates — does NOT explain further. Students work alone.
After 5 minutes: 3-4 students read their answers aloud.
Teacher gives 1-line feedback per student.
Example: 'Write 4 sentences in your notebook: [specific prompt].
Start with: "[starter sentence]..."'
Student talk time: minimum 8 minutes total (writing + sharing).""",
    },
    2: {
        "style": "Quiz Game — Teams Compete",
        "instruction": """Divide class into 4 teams. Run a 6-question quiz game.
Teacher reads question → first team to raise hand answers → correct = 1 point.
Write scores on board after each question.
Questions must be from today's sections only — factual, short-answer.
After quiz: winning team gets appreciation. All teams write 1 missed answer.
Student talk time: minimum 10 minutes total.
Example questions: 'Which country started X?' / 'What year did Y happen?' / 'Name the leader of Z'""",
    },
    3: {
        "style": "Poster Making — Visual Summary",
        "instruction": """Students make a mini-poster in their notebook — 6 minutes.
Poster must show: Title + 3 key facts + 1 drawing/diagram + 1 key term.
Teacher writes the structure on board:
  Box 1: Title (today's topic)
  Box 2: Fact 1, Fact 2, Fact 3
  Box 3: Simple sketch or flowchart
  Box 4: Key term + meaning
After 6 minutes: 3 students show their poster. Class gives 1 positive comment each.
Student activity time: minimum 10 minutes total.""",
    },
    4: {
        "style": "Debate / For & Against",
        "instruction": """Run a structured 2-minute debate on a topic from today's sections.
Split class: Left side = FOR, Right side = AGAINST.
Teacher gives the debate statement on board — directly from today's content.
Round 1: FOR side — 3 students give 1 reason each (30 seconds each).
Round 2: AGAINST side — 3 students give 1 reason each (30 seconds each).
Round 3: Teacher summarises both sides and connects to actual historical outcome.
Example statement: '[Key decision or event from today] — was it right or wrong?'
Student talk time: minimum 10 minutes total.""",
    },
    5: {
        "style": "Self-Assessment Checklist + Test Prep",
        "instruction": """Students use a checklist to self-assess their chapter notes.
Then attempt 2 unseen short-answer questions independently (test conditions — 5 minutes).
Teacher collects for checking.
Checklist on board:
  ☐ I can name all main topics from Days 1-4
  ☐ I can explain 2 causes in my own words
  ☐ I can write 3 key terms with meanings
  ☐ I completed all homework
This prepares students for actual exams.
Student activity time: minimum 10 minutes total.""",
    },
}


# ============================================================================
# TOPIC FOCUS MAP — per-day topic guidance (no hardcoded page ranges)
# ============================================================================

FOCUS_MAP = {
    1: (
        "Opening context, background, and the FIRST major topic or cause of the chapter. "
        "Cover only what can be taught well in 25 minutes of content time. "
        "If the first topic is large, teach it fully — do NOT rush into the second topic."
    ),
    2: (
        "Second and third major topics or causes. "
        "Start with a 2-minute recap of Day 1. "
        "If Day 1's topic was large and carried over, complete it first before moving to new topics. "
        "Cover only what can be taught well — do NOT rush."
    ),
    3: (
        "Results, consequences, turning points, or the second half of core content. "
        "Start with a 2-minute recap of Day 2. "
        "If a previous topic was large and not completed, finish it first. "
        "Use anchor charts, graphic organizers, or flowcharts for complex cause-effect concepts."
    ),
    4: (
        "Final sections — analysis, source-based discussion, and chapter consolidation. "
        "Start with a 2-minute recap of Day 3. "
        "If any major topic was not fully covered in a previous day, "
        "open with completing it before moving to consolidation. "
        "Closing must be an OVERALL CHAPTER RECAP — not just Day 4 recap."
    ),
}


# ============================================================================
# ACTIVITY MAP — v2.0
# Each day gets a DIFFERENT activity type — no repetition across days
# Teacher feedback May 2026: "same group discussion every day — change it"
# ============================================================================

ACTIVITY_MAP = {
    1: (
        "ACTIVITY TYPE: Group Discussion (Day 1 only)\n"
        "Divide into 3 groups. Each group gets ONE question from today's sections.\n"
        "Groups discuss for 3 minutes. One student per group shares with class.\n"
        "Teacher adds 2 key points to board after sharing.\n"
        "⚠️ Group Discussion is used ONLY on Day 1 — not repeated on other days."
    ),
    2: (
        "ACTIVITY TYPE: Quiz Game — Teams Compete (Day 2 only)\n"
        "4 teams. 6 questions from today's sections. First hand raised answers.\n"
        "Correct = 1 point. Write scores on board. Energetic and fast-paced.\n"
        "After quiz: each team writes 1 answer they got wrong.\n"
        "⚠️ Quiz Game is used ONLY on Day 2 — not repeated on other days."
    ),
    3: (
        "ACTIVITY TYPE: Poster Making in Notebook (Day 3 only)\n"
        "Students draw a mini-poster in notebook showing today's content visually.\n"
        "Structure: Title + 3 facts + 1 simple sketch/flowchart + 1 key term.\n"
        "6 minutes to make. 3 students show and explain their poster.\n"
        "⚠️ Poster Making is used ONLY on Day 3 — not repeated on other days."
    ),
    4: (
        "ACTIVITY TYPE: Structured Debate — For & Against (Day 4 only)\n"
        "Left side = FOR, Right side = AGAINST on a statement from today's content.\n"
        "3 students per side give 1 reason each (30 seconds each).\n"
        "Teacher summarises both sides. Connects to actual historical outcome.\n"
        "⚠️ Debate is used ONLY on Day 4 — not repeated on other days."
    ),
}


# ============================================================================
# HELPER — clean raw AI output
# ============================================================================

def clean(raw: str) -> str:
    """
    Strip markdown fences, style blocks, and leading non-HTML preamble
    from raw Claude API output.

    Used by every LP builder after each API call.

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
# QA SYSTEM PROMPT
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
- Base questions on the CHAPTER BODY content — not just book-back exercises"""


# ============================================================================
# ANSWER FORMAT RULES
# ============================================================================

ANSWER_FORMAT_RULES = """
ANSWER FORMAT RULES — STRICTLY FOLLOW FOR ALL SECTIONS:

═══════════════════════════════════════════════════════
SECTION WRAPPER — EVERY SECTION MUST USE THIS STRUCTURE
═══════════════════════════════════════════════════════
Every question section MUST be wrapped in a section div with a Show Answers button.
The button reveals ALL answers in that section at once.
NO individual show buttons per question — section button is the ONLY trigger.

SECTION IDs to use:
  MCQ (Choose Correct Answer)  → id="section-mcq"
  Fill in the Blanks           → id="section-fill"
  Choose the Statement         → id="section-choose"
  Match the Following          → id="section-match"
  2-mark (Answer Briefly)      → id="section-2mark"
  5-mark (Answer in Detail)    → id="section-5mark"

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
  <p class="section-note"><em>[marks info]</em></p>

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

── MCQ (Choose the Correct Answer) ────────────────────
NO tick mark ✓ anywhere in options.
Correct answer shown ONLY inside answer-reveal.

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

── Fill in the Blanks ──────────────────────────────────
<div class="qa-item">
  <p class="question"><strong>Q26.</strong> [Sentence with]
  <span class="blank-line">__________</span> [rest of sentence].</p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [word or phrase]</p>
  </div>
</div>

── Choose the Correct Statement ────────────────────────
NO tick mark ✓ anywhere in statements.
Correct statement shown ONLY inside answer-reveal.

<div class="qa-item">
  <p class="question"><strong>Q51.</strong> Choose the correct statement:</p>
  <div class="mcq-options">
    <span>i) [Statement one]</span>
    <span>ii) [Statement two]</span>
    <span>iii) [Statement three]</span>
  </div>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> ii) [correct statement text]</p>
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

── 2-Mark Questions (Answer Briefly) ──────────────────
<div class="qa-item">
  <p class="question"><strong>Q71.</strong> Question text here?
  <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [2-3 sentence answer — 30-50 words]</p>
  </div>
</div>

── 5-Mark Questions (Answer in Detail) ────────────────
<div class="qa-item">
  <p class="question"><strong>Q91.</strong> Question text here?
  <span class="mark-badge">(5 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [5-7 sentence answer — 80-120 words.
    Complete paragraph — never bullet points.]</p>
  </div>
</div>

═══════════════════════════════════════════════════════
ABSOLUTE RULES — NEVER VIOLATE
═══════════════════════════════════════════════════════
❌ NEVER add tick marks ✓ anywhere in options or statements
❌ NEVER add individual show buttons per question
❌ NEVER show answers directly — always inside answer-reveal div
❌ NEVER use <textarea> or <input> anywhere
✅ ALWAYS wrap each section in qa-section div with section button
✅ ALWAYS use style="display:none;" on every answer-reveal div
✅ ALWAYS put complete answer inside answer-reveal
✅ Section button is the ONLY way answers are revealed
"""


# ============================================================================
# QA HEADER HELPER — dynamic, used by all QA builders
# ============================================================================

def get_qa_header(lesson_title: str, class_num, unit, discipline: str) -> str:
    """
    Generates the QA page header dynamically.
    Used by ALL SS QA builders — never hardcode discipline name.
    """
    return f"""<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — {discipline.title()} | Unit {unit} | 100 Questions</p>
</div>"""


# ============================================================================
# DISCIPLINE CONTEXT
# ============================================================================

DISCIPLINE_CONTEXT = {
    "history": """
HISTORY FOCUS:
- Questions must test dates, events, causes, consequences, treaties, personalities
- Include chronology questions (what came first / what happened after)
- Include cause-effect questions (why did X happen / what resulted from Y)
- Include map-related questions as text (which country / where did it happen)
- Avoid vague questions — be specific about which event, which year, which person
""",
    "geography": """
GEOGRAPHY FOCUS:
- Questions must test physical features, locations, climate, resources, human activities
- Include map-based questions as text (where is X located / which river flows through Y)
- Include distinguish-between questions (difference between X and Y)
- Include reason-based questions (why does X happen in Y region)
""",
    "civics": """
CIVICS FOCUS:
- Questions must test constitutional provisions, government structure, rights, duties
- Include definition questions (what is X / define Y)
- Include function questions (what does X body do / what is the role of Y)
- Include comparison questions (difference between X and Y institution)
""",
    "economics": """
ECONOMICS FOCUS:
- Questions must test concepts, definitions, data, policies, economic terms
- Include definition questions (what is GDP / define inflation)
- Include reason questions (why does X affect Y / what causes Z)
- Include data questions if statistics or figures appear in the chapter
""",
}


# ============================================================================
# QA QUESTION SPLIT — shared across all disciplines and grade groups
# ============================================================================

QA_SPLIT = {
    "mcq":     {"start": 1,  "end": 25, "count": 25, "section": "section-mcq"},
    "fill":    {"start": 26, "end": 50, "count": 25, "section": "section-fill"},
    "choose":  {"start": 51, "end": 60, "count": 10, "section": "section-choose"},
    "match":   {"start": 61, "end": 70, "count": 10, "section": "section-match",
                "sets": 2, "pairs_per_set": 5},
    "mark2":   {"start": 71, "end": 85, "count": 15, "section": "section-2mark"},
    "mark5":   {"start": 86, "end": 100, "count": 15, "section": "section-5mark"},
}

# Descriptive section instruction — used by ALL QA builders in Call 4
QA_DESCRIPTIVE_INSTRUCTION = """
══════════════════════════════════════
PART A: 2-Mark Questions Q76–Q88
══════════════════════════════════════

Generate EXACTLY 13 questions: Q76 to Q88

ANSWER LENGTH: Exactly 2-3 complete sentences. 30-50 words only.
Do NOT write more than 3 sentences.
Do NOT write less than 2 sentences.

Question types — distribute evenly:
- Short explanation: Explain what/who/how about a key topic
- Reason-based: Why did X happen / What caused Y
- Definition + example: Define X and give one example from chapter
- Compare briefly: One difference between X and Y

Section: id="section-2mark" | Title: "Section VI — Answer Briefly" | Note: 2 Marks each | Q76–Q88 | Answer in 2-3 sentences
Use 2-Mark format from ANSWER FORMAT RULES above.

══════════════════════════════════════
PART B: 5-Mark Questions Q89–Q100
══════════════════════════════════════

Generate EXACTLY 12 questions: Q89 to Q100

ANSWER LENGTH: Exactly 5-7 complete sentences. 80-120 words.
Do NOT write more than 7 sentences.
Do NOT write less than 5 sentences.
Every answer must be a proper paragraph — not bullet points.

Question types — distribute across 12 questions:
- Explain in detail — full explanation of a key event or concept
- Causes and effects — list and explain causes OR consequences
- Significance — why was X important / what was the impact of Y
- Compare — detailed comparison between two events or concepts
- Evaluate — outcomes, successes, or failures of a major event
Each type used 3 times across the 12 questions.

Section: id="section-5mark" | Title: "Section VII — Answer in Detail" | Note: 5 Marks each | Q89–Q100 | Answer in 5-7 sentences
Use 5-Mark format from ANSWER FORMAT RULES above.

RULES:
- Raw HTML only — no markdown, no code fences
- 2-mark: EXACTLY 13 questions Q76–Q88, strictly 2-3 sentences each
- 5-mark: EXACTLY 12 questions Q89–Q100, strictly 5-7 sentences each
- Every answer inside answer-reveal div — NO individual show buttons
- Every answer complete paragraph — never bullet points
- Each question covers a different chapter topic
- Do NOT stop before Q100
"""

# Match section instruction — used by ALL QA builders in Call 3
QA_MATCH_INSTRUCTION = """
═══════════════════════════════════════════════════════
SECTION IV — MATCH THE FOLLOWING (Q61–Q70)
═══════════════════════════════════════════════════════

Generate this section using EXACTLY this HTML structure.
Every question from Q61 to Q70 MUST appear — no skipping.

<div class="qa-section" id="section-match">
  <div class="section-header">
    <h2>Section IV — Match the Following</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-match')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>1 Mark each | Q61–Q70</em></p>

  <!-- SET 1: Q61–Q65 -->
  <div class="qa-item">
    <p class="question"><strong>Q61.</strong> Match the following (Set 1):</p>
    <table class="match-table">
      <thead><tr><th>Column A</th><th>Column B</th></tr></thead>
      <tbody>
        <tr><td>1. [Item from chapter]</td><td>a) [Match from chapter]</td></tr>
        <tr><td>2. [Item from chapter]</td><td>b) [Match from chapter]</td></tr>
        <tr><td>3. [Item from chapter]</td><td>c) [Match from chapter]</td></tr>
        <tr><td>4. [Item from chapter]</td><td>d) [Match from chapter]</td></tr>
        <tr><td>5. [Item from chapter]</td><td>e) [Match from chapter]</td></tr>
      </tbody>
    </table>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answers:</strong> 1-[x], 2-[x], 3-[x], 4-[x], 5-[x]</p>
    </div>
  </div>

  <div class="qa-item">
    <p class="question"><strong>Q62.</strong> From Set 1 above — what does [Column A item 1] match with?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answer:</strong> [Column B match]</p>
    </div>
  </div>

  <div class="qa-item">
    <p class="question"><strong>Q63.</strong> From Set 1 above — what does [Column A item 2] match with?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answer:</strong> [Column B match]</p>
    </div>
  </div>

  <div class="qa-item">
    <p class="question"><strong>Q64.</strong> From Set 1 above — what does [Column A item 3] match with?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answer:</strong> [Column B match]</p>
    </div>
  </div>

  <div class="qa-item">
    <p class="question"><strong>Q65.</strong> From Set 1 above — what does [Column A item 4] match with?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answer:</strong> [Column B match]</p>
    </div>
  </div>

  <!-- SET 2: Q66–Q70 -->
  <div class="qa-item">
    <p class="question"><strong>Q66.</strong> Match the following (Set 2):</p>
    <table class="match-table">
      <thead><tr><th>Column A</th><th>Column B</th></tr></thead>
      <tbody>
        <tr><td>1. [Item from chapter]</td><td>a) [Match from chapter]</td></tr>
        <tr><td>2. [Item from chapter]</td><td>b) [Match from chapter]</td></tr>
        <tr><td>3. [Item from chapter]</td><td>c) [Match from chapter]</td></tr>
        <tr><td>4. [Item from chapter]</td><td>d) [Match from chapter]</td></tr>
        <tr><td>5. [Item from chapter]</td><td>e) [Match from chapter]</td></tr>
      </tbody>
    </table>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answers:</strong> 1-[x], 2-[x], 3-[x], 4-[x], 5-[x]</p>
    </div>
  </div>

  <div class="qa-item">
    <p class="question"><strong>Q67.</strong> From Set 2 above — what does [Column A item 1] match with?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answer:</strong> [Column B match]</p>
    </div>
  </div>

  <div class="qa-item">
    <p class="question"><strong>Q68.</strong> From Set 2 above — what does [Column A item 2] match with?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answer:</strong> [Column B match]</p>
    </div>
  </div>

  <div class="qa-item">
    <p class="question"><strong>Q69.</strong> From Set 2 above — what does [Column A item 3] match with?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answer:</strong> [Column B match]</p>
    </div>
  </div>

  <div class="qa-item">
    <p class="question"><strong>Q70.</strong> From Set 2 above — what does [Column A item 4] match with?</p>
    <div class="answer-reveal" style="display:none;">
      <p class="answer"><strong>Answer:</strong> [Column B match]</p>
    </div>
  </div>

</div>

⚠️ ABSOLUTE RULES:
- Q61 through Q70 — ALL 10 must appear in output
- Q61 = Set 1 match table
- Q62, Q63, Q64, Q65 = individual pair questions from Set 1
- Q66 = Set 2 match table
- Q67, Q68, Q69, Q70 = individual pair questions from Set 2
- NEVER skip any question number between Q61 and Q70
- All items from chapter text only — never invent

═══════════════════════════════════════════════════════
SECTION V — ANSWER IN DETAIL SHORT (Q71–Q75)
═══════════════════════════════════════════════════════

AFTER the match section, generate EXACTLY 5 questions: Q71–Q75

Section: id="section-detail" | Title: "Section V — Answer in Detail (Short)"
Note: 2 Marks each | Q71–Q75
Each answer: 2-3 complete sentences. 30-50 words only.

FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q71.</strong> Question text?
  <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [2-3 sentence answer]</p>
  </div>
</div>

RULES:
- EXACTLY 5 questions Q71–Q75
- All answers inside answer-reveal div
- Do NOT stop before Q75
"""