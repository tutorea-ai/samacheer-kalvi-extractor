"""
science/base/__init__.py
------------------------
Shared constants and helpers for all Science LP and QA builders.

Imported by:
    science/lp/grade_910/physics.py
    science/lp/grade_910/chemistry.py
    science/lp/grade_910/biology.py
    science/lp/grade_910/computer_science.py
    science/lp/grade_67/physics.py
    ... (all grade groups, all disciplines)

v2.0 — May 2026
Changes from v1.0:
    ✅ TAMIL_INSTRUCTION added — same 3-place rule, Science context
    ✅ SCIENCE_SPARK_STYLES added — per-day Science analogy sparks
    ✅ SCIENCE_ACTIVITY_MAP added — unique Science activity per day
    ✅ PREAMBLE_START_INSTRUCTION added — same as SS base
    ✅ CCQ_INSTRUCTION added — Science-flavored concept check questions
    ✅ All v1.0 constants preserved — no breakage
"""

import re


# ============================================================================
# SYSTEM PROMPT — LP
# ============================================================================

SCIENCE_LP_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Science teacher
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
- Teacher talk: maximum 25% of session time (8-9 minutes)
- Student activity / discussion / writing / observation: minimum 75% (26-27 minutes)
- Never let teacher monologue exceed 3 minutes without a student activity
- After every explanation: student responds, writes, observes, calculates, or answers

CONTENT ACCURACY — STRICTLY ENFORCE:
- Use ONLY facts, figures, numbers, formulas, and statistics that appear VERBATIM in the chapter text provided
- NEVER generate, estimate, or invent any number, measurement, formula, or statistic
- If a fact is not explicitly stated in the chapter text, do NOT include it
- This applies to all disciplines: Physics, Chemistry, Biology, Computer Science"""


# ============================================================================
# SYSTEM PROMPT — QA
# ============================================================================

SCIENCE_QA_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Science teacher
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
# PREAMBLE START INSTRUCTION
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
# CCQ INSTRUCTION — Science-flavored
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
   "What is the SI unit of force?"
   "Which gas is produced when zinc reacts with sulphuric acid?"
   "Name the part of the cell that controls all activities."
   These check if students understood the CONTENT just taught.

RULES for CCQs:
- Every CCQ must be about the science concept just explained — not the activity
- Keep each CCQ under 8 words
- Place them RANDOMLY — after explaining a concept, after a diagram, after activity
- No two CCQs should repeat each other
- Tamil version mandatory for every CCQ
- For Chemistry/Physics: include at least 2 formula or unit CCQs per day

FORMAT — use this exact HTML block:
<div class="ccq-block">
  <strong>⚡ CCQ (Concept Check):</strong>
  <p class="teacher-says">"[Short factual question about concept just taught — under 8 words]"</p>
  <p class="student-says"><strong>Expected:</strong> "[Short factual answer — 1-2 sentences max]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
</div>
═══════════════════════════════════════════════════════
"""


# ============================================================================
# TAMIL SCAFFOLDING INSTRUCTION — v2.0
# Science-context version — same 3-place rule as SS base
# ============================================================================

TAMIL_INSTRUCTION = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES — TARGETED ONLY
═══════════════════════════════════════════════════════

Tamil appears in EXACTLY 3 places — nowhere else:

✅ 1. KEY TERMS TABLE — Tamil meaning column only
✅ 2. MAIN EXPLANATION — Tamil mirror paragraph after EVERY English explanation paragraph
       This applies to every subheading in Topic 1 AND Topic 2
✅ 3. OPENING/LEAD QUESTION — Tamil version after English question

❌ NEVER add Tamil to:
   - Activity instructions
   - Group task descriptions
   - Time notes
   - Board work headings
   - Formula derivations or numerical steps
   - Homework task description
   - Student task instructions
   - Closing / recap sections
   - Diagram labels

⚠️ CONTEXT-BASED TRANSLATION — CRITICAL RULE:
Translate meaning and intent — NOT word for word.

❌ WRONG (word-for-word — gives wrong meaning):
   English: "Atoms cannot be broken"
   Wrong Tamil: "அணுக்கள் உடைக்க முடியாது" ← (unnatural phrasing)

✅ RIGHT (meaning-based — natural Tamil):
   English: "Atoms cannot be broken"
   Right Tamil: "அணுக்களை பிரிக்க இயலாது" ← (correct, natural)

More examples:
   English: "The reaction produces carbon dioxide"
   ❌ Wrong: "எதிர்வினை கார்பன் டை ஆக்சைடை உற்பத்தி செய்கிறது"
   ✅ Right: "இந்த வினையில் கார்பன் டை ஆக்சைடு உருவாகிறது"

   English: "Force is directly proportional to acceleration"
   ❌ Wrong: "விசை நேரடியாக முடுக்கத்திற்கு விகிதாசாரமாக உள்ளது"
   ✅ Right: "விசை அதிகரிக்கும்போது முடுக்கமும் அதிகரிக்கும்"

TAMIL QUALITY RULES — STRICTLY FOLLOW:
- Translate the MEANING — not the words
- Every Tamil sentence must be grammatically correct Tamil
- NO word repetition in Tamil mirror — check each sentence
- NO spelling errors — use standard Tamil Unicode
- Mirror must match English sentence by sentence — same count, same length
- If unsure of a Tamil scientific term, use the English term in Tamil script — never guess
- Read Tamil output once before finishing — check for repeated words
- NO Hindi words ever — pure Tamil only
- Scientific terms like "electron", "mole", "nucleus" may be written as
  எலக்ட்ரான், மோல், நியூக்ளியஸ் — Tamil script transliteration is acceptable
  for terms with no standard Tamil equivalent
═══════════════════════════════════════════════════════
"""


# ============================================================================
# SCIENCE SPARK STYLES — per day, Science-flavored analogies
# Modeled on teacher LP reference (coins, pizza, egg tray, judge's wig style)
# ============================================================================

SCIENCE_SPARK_STYLES = {
    1: {
        "style": "Real-Object Analogy",
        "instruction": """Teacher holds up or describes a familiar everyday object
that directly connects to today's concept.
Use an object students have seen in daily life — not a lab item.
Examples from teacher LP: gold coin vs aluminium coin for atomic theory;
pizza cut into 12 slices for atomic mass unit; bag of mixed coins for isotopes.
Structure:
  Step 1: Show/describe the object — 'Look at this...'
  Step 2: Connect to today's concept — 'This is exactly how [concept] works...'
  Step 3: Big Question — 'So today's question is: [curiosity question]?'
End with a Big Question that makes students want to know the answer.
Allow 2-3 student guesses before moving on.""",
    },
    2: {
        "style": "Previous Day Recap + Real-Life Connection",
        "instruction": """START with a 1-minute rapid-fire recap of yesterday's key concept.
Teacher asks 2-3 quick questions — students call out answers.
THEN give a real-life connection to today's new concept.
Example style: 'Yesterday we learned X. Now here's the puzzle:
if X is true, how does Y happen in real life?'
End with one curiosity question about today's topic.
Examples from teacher LP: 'If atoms are unbreakable, how does nuclear energy work?'
4-5 students share opinions before teacher reveals today's focus.""",
    },
    3: {
        "style": "Dramatic Teacher Entry / Role Play Hook",
        "instruction": """Teacher enters with a prop, costume element, or dramatic action
that immediately grabs attention and signals today's theme.
Examples from teacher LP: teacher enters wearing fake judge's wig holding a gavel
for 'Chemistry Math Arena' day; teacher brings egg tray for Mole concept.
Structure:
  Step 1: Dramatic entry or action — teacher performs or says something unexpected
  Step 2: Connect the drama to today's concept — explain the analogy
  Step 3: Big Question — challenge students with a concept puzzle
Students get 30 seconds to think — then 3 share responses.
Keep it energetic — this is the highest-energy spark of the week.""",
    },
    4: {
        "style": "Formula Puzzle + Rapid Recall",
        "instruction": """Write an incomplete formula or equation on the board BEFORE class starts.
Students see it when they walk in — it creates immediate curiosity.
Structure:
  Step 1: Point to board — 'Can anyone tell me what the missing part is?'
  Step 2: Run a quick 3-question rapid recall from Days 1-3 — call-and-response style
    Example: 'What is 1 mole equal to?' → Students: '6.023 x 10^23!'
  Step 3: Reveal today's focus — 'Today we APPLY all of this in the Math Arena.'
End with a challenge statement: 'By the end of today, you will be able to
solve [specific type of problem] in under 2 minutes.'
Energy level: competitive and exciting.""",
    },
    5: {
        "style": "Final Departure Shout + Rapid Quiz",
        "instruction": """START with a call-and-response rapid-fire quiz reviewing ALL key facts from Days 1-4.
Teacher reads question → students shout answer together.
Example style from teacher LP:
  Teacher: 'One mole of any gas at STP occupies...?'
  Students: 'TWENTY-TWO POINT FOUR LITERS!'
  Teacher: 'Molecular mass equals...?'
  Students: 'TWO TIMES VAPOUR DENSITY!'
Run 5-6 such call-and-response pairs — keeps energy high.
THEN transition: 'Today we lock everything in. Book-back exercises + final review.'
This day spark activates ALL prior knowledge before evaluation.""",
    },
}


# ============================================================================
# SCIENCE ACTIVITY MAP — unique Science activity per day
# No activity repeats across days — different pedagogy each day
# Modeled on teacher LP: Dalton Says, Board Race, Balloon chant, etc.
# ============================================================================

SCIENCE_ACTIVITY_MAP = {
    1: (
        "ACTIVITY TYPE: Call-and-Response Concept Game (Day 1 only)\n"
        "Teacher shouts a statement or old misconception.\n"
        "Students must shout back the correct scientific update or answer.\n"
        "Example from teacher LP: Teacher shouts 'Dalton Says atoms are indivisible!'\n"
        "Students shout back: 'No! They have subatomic particles!'\n"
        "Run 4-5 rounds covering today's key concepts.\n"
        "After the game: students write 2 sentences — old idea vs new idea.\n"
        "⚠️ Call-and-Response Game is used ONLY on Day 1 — not repeated."
    ),
    2: (
        "ACTIVITY TYPE: Team Sorting / Classification Race (Day 2 only)\n"
        "Teacher holds up or writes a formula, term, or example on board.\n"
        "Students must physically respond — jump left/right, hold up fingers,\n"
        "or call out the category (e.g. Homoatomic/Heteroatomic, Element/Compound).\n"
        "Example from teacher LP: Teacher writes O3, H2O, P4 — students jump left\n"
        "for Homoatomic or right for Heteroatomic, hold up fingers for atomicity.\n"
        "Run 6-8 rounds — fast and energetic.\n"
        "⚠️ Team Sorting Race is used ONLY on Day 2 — not repeated."
    ),
    3: (
        "ACTIVITY TYPE: Rapid Worksheet Race (Day 3 only)\n"
        "Teacher gives 3-4 short calculation or concept questions on the board.\n"
        "Students solve them as fast as possible in their notebooks — index card style.\n"
        "Example from teacher LP: 4 rapid questions on Mole, % composition, VD.\n"
        "After 5 minutes: teacher reads correct answers — students self-check.\n"
        "Students who got all correct stand up and explain one answer to class.\n"
        "⚠️ Rapid Worksheet Race is used ONLY on Day 3 — not repeated."
    ),
    4: (
        "ACTIVITY TYPE: Board Race Tournament (Day 4 only)\n"
        "Divide class into 4 rows/teams. One student per team runs to board per round.\n"
        "Teacher reads a problem — first student to write the correct answer wins the round.\n"
        "Example from teacher LP: Round 1: volume of 14g N2 at STP?\n"
        "Round 2: molecules in 0.5 mol CO2? Round 3: mass of 0.3 mol Al?\n"
        "Run 3-4 rounds. Keep score on board. Winning team = 'Molar Masters'.\n"
        "⚠️ Board Race Tournament is used ONLY on Day 4 — not repeated."
    ),
}


# ============================================================================
# DISCIPLINE CONTEXT — per discipline focus rules for QA
# ============================================================================

DISCIPLINE_CONTEXT = {
    "physics": """
PHYSICS FOCUS:
- Questions must test laws, definitions, formulas, units, numerical concepts
- Include reason-based questions (why does X happen / what is the effect of Y)
- Include definition questions (define X / what is meant by Y)
- Include application questions (where is X used / give one example of Y)
- Avoid questions that require calculation — text-based only
""",
    "chemistry": """
CHEMISTRY FOCUS:
- Questions must test reactions, properties, definitions, elements, compounds
- Include reason-based questions (why does X react with Y)
- Include definition questions (define X / what is meant by Y)
- Include classification questions (which type of reaction is X)
- Avoid questions that require calculation — text-based only
""",
    "biology": """
BIOLOGY FOCUS:
- Questions must test structures, functions, processes, classifications, diagrams
- Include function questions (what is the role of X / what does Y do)
- Include difference questions (distinguish between X and Y)
- Include process questions (explain how X happens / describe the steps of Y)
- Include diagram-label questions as text (name the parts of X)
""",
    "computer_science": """
COMPUTER SCIENCE FOCUS:
- Questions must test definitions, components, functions, types, applications
- Include definition questions (what is X / define Y)
- Include function questions (what does X do / what is the purpose of Y)
- Include comparison questions (difference between X and Y)
- Include application questions (give one use of X / where is Y used)
""",
}


# ============================================================================
# ANSWER FORMAT RULES
# ============================================================================

ANSWER_FORMAT_RULES = """
ANSWER FORMAT RULES — STRICTLY FOLLOW FOR ALL SECTIONS:

Every question section MUST be wrapped in a section div with a Show Answers button.
The button reveals ALL answers in that section at once.
NO individual show buttons per question.

SECTION IDs to use:
  MCQ (Choose Correct Answer)  → id="section-mcq"
  Fill in the Blanks           → id="section-fill"
  Choose the Statement         → id="section-choose"
  Match the Following          → id="section-match"
  2-mark (Answer Briefly)      → id="section-2mark"
  5-mark (Answer in Detail)    → id="section-5mark"

SECTION WRAPPER FORMAT:
<div class="qa-section" id="section-[id]">
  <div class="section-header">
    <h2>[Section Title]</h2>
    <button class="show-section-btn"
            onclick="toggleSectionAnswers(this, 'section-[id]')"
            style="background:#2563eb; color:#fff; font-weight:700;
                   border:none; border-radius:6px; padding:6px 18px;
                   cursor:pointer; font-size:0.95rem;">
      📋 Show Answers
    </button>
  </div>
  <p class="section-note"><em>[marks info]</em></p>
  [questions here]
</div>

ANSWER REVEAL FORMAT (every answer):
<div class="answer-reveal" style="display:none;">
  <p class="answer"><strong>Answer:</strong> [complete answer here]</p>
</div>

MCQ FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q1.</strong> Question text?</p>
  <div class="mcq-options">
    <span>a) Option one</span><span>b) Option two</span>
    <span>c) Option three</span><span>d) Option four</span>
  </div>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> b) [correct option]</p>
  </div>
</div>

FILL IN BLANKS FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q26.</strong> [Sentence with]
  <span class="blank-line">__________</span> [rest].</p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [word or phrase]</p>
  </div>
</div>

2-MARK FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q71.</strong> Question?
  <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [2-3 sentence answer]</p>
  </div>
</div>

5-MARK FORMAT:
<div class="qa-item">
  <p class="question"><strong>Q86.</strong> Question?
  <span class="mark-badge">(5 marks)</span></p>
  <div class="answer-reveal" style="display:none;">
    <p class="answer"><strong>Answer:</strong> [5-7 sentence paragraph]</p>
  </div>
</div>

ABSOLUTE RULES:
❌ NEVER add tick marks anywhere
❌ NEVER add individual show buttons per question
❌ NEVER show answers directly — always inside answer-reveal div
❌ NEVER use textarea or input
✅ ALWAYS wrap each section in qa-section div with section button
✅ ALWAYS use style="display:none;" on every answer-reveal div
"""


# ============================================================================
# QA MATCH INSTRUCTION
# ============================================================================

QA_MATCH_INSTRUCTION = """
Generate EXACTLY 2 match sets of 5 pairs each.
Match Set 1 — Q61: Contains pairs Q61–Q65 (5 pairs)
Match Set 2 — Q66: Contains pairs Q66–Q70 (5 pairs)
Both sets together cover Q61–Q70 = 10 questions total.

Section: id="section-match" | Title: "Section IV — Match the Following" | Note: 1 Mark each | Q61–Q70

AFTER the 2 match sets, generate EXACTLY 5 detail questions: Q71–Q75
Section: id="section-detail" | Title: "Section V — Answer in Detail (Short)" | Note: 2 Marks each | Q71–Q75
Each answer: 2-3 complete sentences. 30-50 words only.

RULES:
- Match: EXACTLY 2 sets (Q61, Q66) with 5 pairs each — total Q61-Q70
- Detail: EXACTLY 5 questions Q71-Q75 — 2-3 sentences each
- All answers inside answer-reveal div — NO individual show buttons
- Do NOT stop before Q75
"""


# ============================================================================
# QA DESCRIPTIVE INSTRUCTION
# ============================================================================

QA_DESCRIPTIVE_INSTRUCTION = """
══════════════════════════════════════
PART A: 2-Mark Questions Q76–Q88
══════════════════════════════════════

Generate EXACTLY 13 questions: Q76 to Q88
ANSWER LENGTH: Exactly 2-3 complete sentences. 30-50 words only.

Section: id="section-2mark" | Title: "Section VI — Answer Briefly" | Note: 2 Marks each | Q76–Q88

══════════════════════════════════════
PART B: 5-Mark Questions Q89–Q100
══════════════════════════════════════

Generate EXACTLY 12 questions: Q89 to Q100
ANSWER LENGTH: Exactly 5-7 complete sentences. 80-120 words.
Every answer must be a proper paragraph — not bullet points.

Section: id="section-5mark" | Title: "Section VII — Answer in Detail" | Note: 5 Marks each | Q89–Q100

RULES:
- 2-mark: EXACTLY 13 questions Q76–Q88, strictly 2-3 sentences each
- 5-mark: EXACTLY 12 questions Q89–Q100, strictly 5-7 sentences each
- Every answer inside answer-reveal div — NO individual show buttons
- Do NOT stop before Q100
"""


# ============================================================================
# QA HEADER HELPER
# ============================================================================

def get_qa_header(lesson_title: str, class_num, unit: int, discipline: str) -> str:
    return f"""<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Science — {discipline.replace('_', ' ').title()} | Unit {unit} | 100 Questions</p>
</div>"""


# ============================================================================
# CLEAN HELPER
# ============================================================================

def clean(raw: str) -> str:
    """Strip markdown fences and leading non-HTML preamble from Claude output."""
    if not raw:
        return raw

    text = raw.strip()
    text = re.sub(r'```(?:html)?', '', text).strip()
    text = re.sub(r'```', '', text).strip()
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)

    first_tag = re.search(r'<(?:div|h[1-6]|section|p|table)', text)
    if first_tag and first_tag.start() > 0:
        preamble = text[:first_tag.start()].strip()
        if preamble and not preamble.startswith('<'):
            text = text[first_tag.start():]

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    return str(soup).strip()