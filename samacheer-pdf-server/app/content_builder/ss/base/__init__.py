"""
ss_lp_base.py
-------------
Shared constants and helpers for all SS LP builders.

Imported by:
    ss/lp/grade_910/history.py
    ss/lp/grade_910/civics.py
    ss/lp/grade_910/geography.py
    ss/lp/grade_910/economics.py
    ss/lp/grade_8/history.py
    ss/lp/grade_8/civics.py
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
- Tamil script must be real Tamil Unicode — NOT transliteration"""


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
# TAMIL SCAFFOLDING INSTRUCTION
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

⚠️ WRONG vs RIGHT EXAMPLE:

❌ WRONG (Tamil added to activity instructions):
   <div class="activity-block">
     <strong>Activity:</strong>
     <p>Divide into 3 groups. Each group answers one question.</p>
     <p>குழுவாக பிரியுங்கள். ஒவ்வொரு குழுவும் ஒரு கேள்விக்கு பதில் சொல்லுங்கள்.</p>
   </div>

✅ RIGHT (Tamil only in key terms and main explanation):
   <div class="activity-block">
     <strong>Activity:</strong>
     <p>Divide into 3 groups. Each group answers one question.</p>
     [NO Tamil here]
   </div>

   <p class="teacher-says"><strong>Teacher says (English):</strong><br/>
   "The Triple Alliance was formed between Germany, Austria-Hungary, and Italy..."</p>
   <div class="tamil-scaffold">
     <strong>ஆசிரியருக்கு (Tamil):</strong>
     <p>"ட்ரிபிள் அலையன்ஸ் என்பது ஜெர்மனி, ஆஸ்திரியா-ஹங்கேரி மற்றும் இத்தாலி இடையே..."</p>
   </div>

Tamil mirror rule (where Tamil IS used):
- Same sentences. Same detail. Same length as English.
- NOT a summary. Full mirror.
- Real Tamil Unicode script only — never transliteration.
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
        "style": "Video Clip Description + Discussion",
        "instruction": """Describe a short video clip (60-90 seconds) the teacher can find on YouTube
that directly connects to today's topic. Give the search keywords.
After the clip: ask students 2 quick reaction questions.
Example structure: 'Play this clip: [YouTube search: "..."] →
What did you notice? How does this connect to...?'""",
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
# ============================================================================

STUDENT_TASK_STYLES = {
    1: {
        "style": "Individual Written Answer",
        "instruction": """Students open their notebooks and write independently.
Give a clear specific prompt — not open-ended.
Give a time limit. Give a model sentence starter on the board.
Example: 'Write 4 sentences in your notebook: [specific prompt].
Start with: "[starter sentence]..."'""",
    },
    2: {
        "style": "Group Discussion with Prompts",
        "instruction": """Divide class into groups of 4-5. Give each group a specific discussion prompt.
Each group discusses for 3 minutes, then one student shares with the class.
Give written prompts on board — not open-ended.
Example: 'Group 1: Discuss why... | Group 2: Explain how... | Group 3: Give reasons for...'
After sharing, teacher adds key points to board.""",
    },
    3: {
        "style": "Think-Pair-Share",
        "instruction": """Give students a specific question or prompt.
Step 1: Think independently (1 min) — write one answer in notebook.
Step 2: Pair with neighbour (2 min) — share and improve each other's answer.
Step 3: Share with class — 3-4 pairs share their combined answer.
Teacher consolidates on board.""",
    },
    4: {
        "style": "Peer Assessment — Swap Notebooks",
        "instruction": """Students write their answer to a given prompt (3 mins).
Then swap notebook with neighbour.
Teacher reads out model answer. Students mark their neighbour's work.
Discuss: what was good, what was missing.
This builds critical reading and self-correction habits.""",
    },
    5: {
        "style": "Self-Assessment Checklist + Test Prep",
        "instruction": """Students use a checklist to self-assess their chapter notes.
Then attempt 2 unseen short-answer questions independently (test conditions).
Teacher collects for checking.
This prepares students for actual exams.""",
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
# ACTIVITY STYLES — per day
# ============================================================================

ACTIVITY_MAP = {
    1: "Flowchart on board showing cause→event→result chain. Large group discussion after.",
    2: "Group activity: 3 groups answer 3 different questions. Each group shares with class. Active note-taking.",
    3: "Bucket activity: Red/Yellow/Green groups each get a different focus. Map pointing if relevant. Pair discussion.",
    4: "Source analysis OR timeline activity. Students present their own flowchart prepared during the lesson.",
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

    # Strip any leading non-HTML preamble text
    first_tag = re.search(r'<(?:div|h[1-6]|section|p|table)', text)
    if first_tag and first_tag.start() > 0:
        preamble = text[:first_tag.start()].strip()
        if preamble and not preamble.startswith('<'):
            text = text[first_tag.start():]

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
