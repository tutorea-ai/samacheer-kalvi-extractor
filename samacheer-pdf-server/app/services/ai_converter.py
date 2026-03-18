"""
AI Content Converter
Converts extracted PDF text into structured Content, QA, and LP
using Anthropic Claude API.

Each public method returns a styled, complete HTML string ready
for deployment as index.html in the Node.js content server.
"""

import anthropic
from typing import Optional, Dict
from ..config import settings


# ============================================================================
# LP DURATION RULES (TL Approved — applies to ALL English classes)
#
# PROSE ONLY has a grammar section in the textbook → gets grammar days
# Poem, Supplementary, Play/Drama → content only, no grammar days
# ============================================================================

LP_DURATION_RULES = {
    "prose":         {"total": 10, "content": 4, "grammar": 6, "has_grammar": True},
    "poem":          {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "supplementary": {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "play":          {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "drama":         {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
}

def _get_lp_duration(lesson_type: str) -> dict:
    """Returns duration breakdown for the lesson type."""
    return LP_DURATION_RULES.get(lesson_type.lower(), LP_DURATION_RULES["supplementary"])


# ============================================================================
# LP SYSTEM PROMPT (TL-approved — do not modify without TL approval)
# ============================================================================

LP_SYSTEM_PROMPT = """You are an experienced English teacher with deep knowledge of the Tamil Nadu Samacheer Kalvi syllabus and activity-based learning methods used in Indian classrooms.
Create a detailed, practical, script-by-script lesson plan so that even a brand new inexperienced teacher can walk into class and deliver a confident, effective session just by following it."""


def _build_lp_prompt(class_num: int, lesson_title: str, lesson_type: str, unit: int, text: str) -> str:
    """
    Builds the full TL-approved LP prompt.

    PROSE:
      - 10 days total: 4 content days + 6 grammar days
      - Grammar days based on the ACTUAL grammar section in the textbook
      - Each day = 30 min scripted session

    POEM / SUPPLEMENTARY / PLAY / DRAMA:
      - 3 days total: all content days, NO grammar days
      - Each day = 30 min scripted session
    """
    duration     = _get_lp_duration(lesson_type)
    total_days   = duration["total"]
    content_days = duration["content"]
    grammar_days = duration["grammar"]
    has_grammar  = duration["has_grammar"]

    # Map lesson type to display name
    type_display_map = {
        "prose":         "Prose",
        "poem":          "Poem",
        "supplementary": "Supplementary Reader",
        "play":          "Drama or Play",
        "drama":         "Drama or Play",
    }
    type_display = type_display_map.get(lesson_type.lower(), "Prose")

    # Duration summary line
    if has_grammar:
        duration_line = f"{total_days} days ({content_days} Content Days + {grammar_days} Grammar Days)"
    else:
        duration_line = f"{total_days} days (Content Only — no grammar section for this lesson type)"

    # Grammar section (only for prose)
    grammar_section = ""
    if has_grammar:
        grammar_section = f"""
═══════════════════════════════════════════════════════
PART 5: GRAMMAR DAYS (Day {content_days + 1} to Day {total_days})
═══════════════════════════════════════════════════════

IMPORTANT: Grammar days must be based ONLY on the grammar topics and exercises
that are actually present in the grammar section of the lesson text provided below.
Do NOT invent grammar topics. Do NOT use random grammar unrelated to this lesson.
Look for the grammar section at the end of the lesson text (vocabulary exercises,
grammar exercises, practice activities) and base ALL grammar days on those.

Grammar days teach grammar using examples and sentences from the lesson text.
Use the SAME 30-minute script format as content days.

For EACH grammar day use this EXACT script format:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAY [N] — GRAMMAR: [Exact Grammar Topic from Textbook]
Duration: 30 Minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[0-5 min] REVIEW + GRAMMAR INTRODUCTION
Teacher says: "[connect today's grammar topic to a sentence from the lesson]"
Board Work: Write the example sentence from the lesson
Teacher says: "[exact simple explanation of the grammar rule]"
Teacher asks: "[question to check if students recognise the pattern]"
Expected student response: "[complete sentence answer]"

[5-15 min] GRAMMAR EXPLANATION + EXAMPLES
Teacher says: "[step by step explanation with examples from the lesson text]"
Board Work: [grammar rule + 3-4 example sentences taken directly from the lesson]
Teacher asks Q1: "[question]" — Expected answer: "[complete sentence]"
Teacher asks Q2: "[question]" — Expected answer: "[complete sentence]"
Teacher asks Q3: "[question]" — Expected answer: "[complete sentence]"
Transition: Teacher says: "[exact words to move to practice]"

[15-25 min] STUDENT PRACTICE EXERCISE
Teacher says: "Now let us practice. Open your notebook and write these."
(Use the ACTUAL exercises from the textbook grammar section if present)
Q1: [question from textbook grammar section] — Answer: [complete sentence]
Q2: [question] — Answer: [complete sentence]
Q3: [question] — Answer: [complete sentence]
Q4: [question] — Answer: [complete sentence]
Q5: [question] — Answer: [complete sentence]
Teacher circulates and says: "[encouraging words while checking notebooks]"
Transition: Teacher says: "[wrap up practice]"

[25-30 min] CLOSURE + QUICK REVISION
Teacher says: "[summarize the grammar rule in 2 simple sentences]"
Board Work: [write the rule + one example to leave on board]
Exit Question: "[one grammar question every student answers before leaving]"
Expected answer: "[complete sentence]"
Teacher says: "[closing + preview of next day]"
Model Example for Homework:
Teacher says: "[show one clear example of the homework grammar task on the board]"
Board Work: [write exactly one model answer — word for word]
Teacher says: "This is one example. Now you do the same at home. Is it clear?"
Expected student response: "Yes sir/madam."
Model Example for Homework:
Teacher says: "[show one clear example of the homework grammar task on the board]"
Board Work: [write exactly one model answer — word for word]
Teacher says: "This is one example. Now you do the same at home. Is it clear?"
Expected student response: "Yes sir/madam."
Homework: [3-5 grammar practice questions from the textbook exercises]
Model Answer for Students:
"[write one complete model answer for the first grammar question —
simple and clear so students can follow the same pattern at home]"
Teacher says: "I will write this model answer on the board. Copy it in your notebook
and use it as a guide when you do your homework at home."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate Day {content_days + 1} through Day {total_days} following this format exactly.
Spread the grammar topics from the textbook across all {grammar_days} grammar days.
"""

    return f"""Class: {class_num}
Unit / Lesson Title: Unit {unit} — {lesson_title}
Text Type: {type_display}
Total Duration: {duration_line}
Each Day: 30 minutes scripted session

LESSON PLAN RULES:
- Every day must be exactly 30 minutes
- Write like a script — teacher can open and follow without any preparation
- Use simple English throughout — suitable for Tamil-medium students
- Every teacher instruction must include EXACT words to say
- Every activity must include expected student responses in complete sentences
- Board work must show EXACTLY what to write word for word

═══════════════════════════════════════════════════════
PART 1: GENERAL INFORMATION
═══════════════════════════════════════════════════════
• Class: {class_num}
• Subject: English
• Unit / Lesson Title: Unit {unit} — {lesson_title}
• Text Type: {type_display}
• Total Days: {duration_line}
• Each Session: 30 minutes

═══════════════════════════════════════════════════════
PART 2: LEARNING OBJECTIVES
═══════════════════════════════════════════════════════
Write clear objectives:
• Knowledge objectives
• Skill objectives (Reading, Writing, Listening, Speaking)
{"• Grammar objectives (specific grammar areas from the textbook grammar section)" if has_grammar else ""}
• Value-based objectives

═══════════════════════════════════════════════════════
PART 3: TEACHING AIDS
═══════════════════════════════════════════════════════
List all materials needed across all {total_days} days.

═══════════════════════════════════════════════════════
PART 4: CONTENT DAYS (Day 1 to Day {content_days})
═══════════════════════════════════════════════════════

For EACH content day use this EXACT script format:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAY [N] — [Topic Focus]
Duration: 30 Minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[0-5 min] WARM UP / REVIEW
🎯 Objective: [what this segment achieves]
Teacher says: "[exact words — greeting, connect to previous day or real life]"
Teacher does: [exact action — write on board, show picture, ask question]
Board Work: [exactly what appears on board]
Teacher asks: "[question to class]"
Expected student response: "[complete sentence]"
Transition: Teacher says: "[exact words to move to next segment]"

[5-15 min] MAIN ACTIVITY
🎯 Objective: [what this segment achieves]
Teacher says: "[exact instructions for the activity]"
Teacher does: [model reading / explanation / demonstration]
Board Work: [exactly what appears on board — key words, sentences]
Student Activity: [exactly what students do — read aloud, answer, discuss]
Expected student response: "[sample answers teacher should expect]"
If students struggle: Teacher says: "[supportive hint or simpler explanation]"
Transition: Teacher says: "[exact words to move to next segment]"

[15-25 min] STUDENT PRACTICE
🎯 Objective: [what this segment achieves]
Teacher says: "[exact instructions]"
Activity Type: [Think-Pair-Share / Group work / Individual / Role play]
Step 1: [exact instruction]
Step 2: [exact instruction]
Step 3: [exact instruction]
Expected output: "[what students should produce]"
Teacher circulates and says: "[what to say while walking around]"
Transition: Teacher says: "[exact words to wrap up activity]"

[25-30 min] CLOSURE
🎯 Objective: Consolidate learning
Teacher says: "[summarize key points of today in simple words]"
Board Work: [write 3-5 key words / summary sentence on board]
Exit Question — Teacher asks: "[one question every student must answer]"
Expected answer: "[complete sentence answer]"
Teacher says: "[closing words + preview of next day]"
Model Example for Homework:
Teacher says: "[show one clear example of the homework task on the board]"
Board Work: [write exactly one model answer — word for word]
Teacher says: "This is one example. Now you do the same at home. Is it clear?"
Expected student response: "Yes sir/madam."
Model Example for Homework:
Teacher says: "[show one clear example of the homework task on the board]"
Board Work: [write exactly one model answer — word for word]
Teacher says: "This is one example. Now you do the same at home. Is it clear?"
Expected student response: "Yes sir/madam."
Homework: [specific, simple task]
Model Answer for Students:
"[write one complete model answer for the homework task — simple sentences,
easy English, so students can refer to this at home when they are stuck]"
Teacher says: "I will write this model answer on the board. Copy it in your notebook
and use it as a guide when you do your homework at home."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate Day 1 through Day {content_days} following this format exactly.
Each day must cover a different part of the lesson text progressively.
{grammar_section}
═══════════════════════════════════════════════════════
PART 6: ASSESSMENT SUMMARY
═══════════════════════════════════════════════════════
• Day-wise oral assessment questions (one per day)
• Written assessment task for end of lesson
• Differentiated support: slow learners vs advanced learners

ADDITIONAL REQUIREMENTS:
• Use simple English throughout — Tamil-medium students must understand
• Every teacher dialogue must be natural and encouraging
• Every student response must be in complete sentences
• Board work must be specific — the ACTUAL words not just "write key words"
• {"Grammar examples must come from the ACTUAL grammar section in the lesson text" if has_grammar else "No grammar section needed for this lesson type"}
• Make it so practical that a first-year teacher feels confident using it

Now output this as HTML body content ONLY — no <html>, <head>, or <body> tags.

HTML Formatting Rules:
- Start with: <div class="sk-content-header"><h1>Lesson Plan — {lesson_title}</h1><p class="sk-meta">Class {class_num} | English | Unit {unit} | {type_display} | {duration_line}</p></div>
- Use <h2> for PART headings
- Use <h3 class="day-header"> for each Day heading
- Use <div class="day-block"> to wrap each day
- Use <div class="time-block"> for each timed segment [0-5 min] etc.
- Use <p class="teacher-says"><strong>Teacher says:</strong> "..."</p> for all teacher dialogue
- Use <p class="student-says"><strong>Expected response:</strong> "..."</p> for student responses
- Use <div class="board-work"><strong>Board Work:</strong> ...</div> for board content
- Use <div class="transition"><em>Transition:</em> ...</div> for transitions
- Use <table> for exercise questions with Answer column
- Use <ul><li> for bullet lists

Lesson Text (ALL teacher dialogue, examples, vocabulary, and grammar exercises must come from this text):
---
{text}
---

Output ONLY the HTML body content. Be detailed. Do NOT skip any day. Do NOT shorten."""


# ============================================================================
# LP SYSTEM PROMPT (TL-approved — do not modify without TL approval)
# ============================================================================

LP_SYSTEM_PROMPT = """You are an experienced English teacher with deep knowledge of the Tamil Nadu Samacheer Kalvi syllabus and activity-based learning methods used in Indian classrooms.
Create a detailed, practical, script-by-script lesson plan so that even a brand new inexperienced teacher can walk into class and deliver a confident, effective session just by following it."""


def _build_lp_prompt(class_num: int, lesson_title: str, lesson_type: str, unit: int, text: str) -> str:
    """
    Builds the full TL-approved LP prompt.
    Each day = 30 min scripted session with exact teacher dialogue,
    expected student responses, timed blocks, and board work.
    Content days + Grammar days split as per TL rules.
    """
    duration = _get_lp_duration(lesson_type)
    total_days     = duration["total"]
    content_days   = duration["content"]
    grammar_days   = duration["grammar"]

    # Map lesson type to display name
    type_display_map = {
        "prose":         "Prose",
        "poem":          "Poem",
        "supplementary": "Supplementary Reader",
        "play":          "Drama or Play",
        "drama":         "Drama or Play",
    }
    type_display = type_display_map.get(lesson_type.lower(), "Prose")

    return f"""Class: {class_num}
Unit / Lesson Title: Unit {unit} — {lesson_title}
Text Type: {type_display}
Total Duration: {total_days} days ({content_days} Content Days + {grammar_days} Grammar Days)
Each Day: 30 minutes scripted session

LESSON PLAN RULES:
- Every day must be exactly 30 minutes
- Write like a script — teacher can open and follow without any preparation
- Use simple English throughout — suitable for Tamil-medium students
- Every teacher instruction must include EXACT words to say
- Every activity must include expected student responses
- Board work must show EXACTLY what to write word for word

═══════════════════════════════════════════════════════
PART 1: GENERAL INFORMATION
═══════════════════════════════════════════════════════
• Class: {class_num}
• Subject: English
• Unit / Lesson Title: Unit {unit} — {lesson_title}
• Text Type: {type_display}
• Total Days: {total_days} ({content_days} Content + {grammar_days} Grammar)
• Each Session: 30 minutes

═══════════════════════════════════════════════════════
PART 2: LEARNING OBJECTIVES
═══════════════════════════════════════════════════════
Write clear objectives:
• Knowledge objectives
• Skill objectives (Reading, Writing, Listening, Speaking)
• Grammar objectives (specific grammar areas from this lesson)
• Value-based objectives

═══════════════════════════════════════════════════════
PART 3: TEACHING AIDS
═══════════════════════════════════════════════════════
List all materials needed across all {total_days} days.

═══════════════════════════════════════════════════════
PART 4: CONTENT DAYS (Day 1 to Day {content_days})
═══════════════════════════════════════════════════════

For EACH content day use this EXACT script format:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAY [N] — [Topic Focus]
Duration: 30 Minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[0-5 min] WARM UP / REVIEW
🎯 Objective: [what this segment achieves]
Teacher says: "[exact words — greeting, connect to previous day or real life]"
Teacher does: [exact action — write on board, show picture, ask question]
Board Work: [exactly what appears on board]
Teacher asks: "[question to class]"
Expected student response: "[what students should say]"
Transition: Teacher says: "[exact words to move to next segment]"

[5-15 min] MAIN ACTIVITY
🎯 Objective: [what this segment achieves]
Teacher says: "[exact instructions for the activity]"
Teacher does: [model reading / explanation / demonstration]
Board Work: [exactly what appears on board — key words, sentences]
Student Activity: [exactly what students do — read aloud, answer, discuss]
Expected student response: "[sample answers teacher should expect]"
If students struggle: Teacher says: "[supportive hint or simpler explanation]"
Transition: Teacher says: "[exact words to move to next segment]"

[15-25 min] STUDENT PRACTICE
🎯 Objective: [what this segment achieves]
Teacher says: "[exact instructions]"
Activity Type: [Think-Pair-Share / Group work / Individual / Role play]
Step 1: [exact instruction]
Step 2: [exact instruction]
Step 3: [exact instruction]
Expected output: "[what students should produce]"
Teacher circulates and says: "[what to say while walking around]"
Transition: Teacher says: "[exact words to wrap up activity]"

[25-30 min] CLOSURE
🎯 Objective: Consolidate learning
Teacher says: "[summarize key points of today in simple words]"
Board Work: [write 3-5 key words / summary sentence on board]
Exit Question — Teacher asks: "[one question every student must answer]"
Expected answer: "[complete sentence answer]"
Teacher says: "[closing words + preview of next day]"
Homework: [specific, simple task]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate Day 1 through Day {content_days} following this format exactly.
Each day must cover a different part of the lesson text progressively.

═══════════════════════════════════════════════════════
PART 5: GRAMMAR DAYS (Day {content_days + 1} to Day {total_days})
═══════════════════════════════════════════════════════

Grammar days teach grammar DIRECTLY from sentences in the lesson text.
Use the SAME 30-minute script format as content days.

Cover these grammar areas spread across {grammar_days} day(s):
• Tenses (identify and use — take example sentences from the lesson)
• Active and Passive Voice
• Articles (a, an, the)
• Prepositions
• Degrees of Comparison
• Question Tags
• Sentence Transformation
• Parts of Speech

For EACH grammar day use this EXACT script format:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAY [N] — GRAMMAR: [Grammar Topic(s)]
Duration: 30 Minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[0-5 min] REVIEW + GRAMMAR INTRODUCTION
Teacher says: "[connect grammar topic to a sentence from the lesson]"
Board Work: Write the example sentence from the lesson
Teacher says: "[exact simple explanation of the grammar rule]"
Teacher asks: "Can anyone tell me what tense/voice/etc. this is?"
Expected student response: "[answer]"

[5-15 min] GRAMMAR EXPLANATION + EXAMPLES
Teacher says: "[step by step explanation with more examples from lesson]"
Board Work: [rule + 3-4 example sentences from the lesson text]
Teacher says: "[check understanding — ask 2-3 oral questions]"
Q1: "[question]" — Expected answer: "[complete sentence]"
Q2: "[question]" — Expected answer: "[complete sentence]"
Q3: "[question]" — Expected answer: "[complete sentence]"

[15-25 min] STUDENT PRACTICE EXERCISE
Teacher says: "Now let us practice. Open your notebook."
Exercise: [5-7 questions using sentences FROM the lesson]
Q1: [question] — Answer: [complete sentence answer]
Q2: [question] — Answer: [complete sentence answer]
Q3: [question] — Answer: [complete sentence answer]
Q4: [question] — Answer: [complete sentence answer]
Q5: [question] — Answer: [complete sentence answer]
Teacher says: "[instruction to check answers together]"

[25-30 min] CLOSURE + QUICK REVISION
Teacher says: "[summarize grammar rule in 2 simple sentences]"
Board Work: [write the rule + one example to leave on board]
Exit Question: "[one grammar question student must answer before leaving]"
Expected answer: "[complete sentence]"
Teacher says: "[closing + preview of next day]"
Homework: [3-5 grammar practice questions]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate Day {content_days + 1} through Day {total_days} following this format exactly.

═══════════════════════════════════════════════════════
PART 6: ASSESSMENT SUMMARY
═══════════════════════════════════════════════════════
• Day-wise oral assessment questions (one per day)
• Written assessment task for end of lesson
• Differentiated support: slow learners vs advanced learners

ADDITIONAL REQUIREMENTS:
• Use simple English throughout — Tamil-medium students must understand
• Every teacher dialogue must be natural and encouraging
• Every student response must be in complete sentences
• Board work must be specific — not just "write key words" but the ACTUAL words
• Grammar examples must come from THIS lesson text — not random sentences
• Make it so practical that a first-year teacher feels confident using it

Now output this as HTML body content ONLY — no <html>, <head>, or <body> tags.

HTML Formatting Rules:
- Start with: <div class="sk-content-header"><h1>Lesson Plan — {lesson_title}</h1><p class="sk-meta">Class {class_num} | English | Unit {unit} | {type_display} | {total_days} Days ({content_days} Content + {grammar_days} Grammar)</p></div>
- Use <h2> for PART headings
- Use <h3 class="day-header"> for each Day heading
- Use <div class="day-block"> to wrap each day
- Use <div class="time-block"> for each timed segment [0-5 min] etc.
- Use <p class="teacher-says"><strong>Teacher says:</strong> "..."</p> for all teacher dialogue
- Use <p class="student-says"><strong>Expected response:</strong> "..."</p> for student responses
- Use <div class="board-work"><strong>Board Work:</strong> ...</div> for board content
- Use <div class="transition"><em>Transition:</em> ...</div> for transitions
- Use <table> for exercise questions with Answer column
- Use <ul><li> for bullet lists

Lesson Text (ALL teacher dialogue, examples, vocabulary, and grammar exercises must come from this text):
---
{text}
---

Output ONLY the HTML body content. Be detailed. Do NOT skip any day. Do NOT shorten."""


# ============================================================================
# HTML WRAPPER
# Wraps AI-generated HTML fragment into a complete styled page.
# ============================================================================

def _wrap_html(body_content: str, title: str, content_type: str = "content") -> str:
    """
    Wraps HTML body content into a full styled HTML page.

    content_type: "content" | "qa" | "lp"
    Each type gets a slightly different accent color for visual distinction.
    """
    accent_colors = {
        "content": "#2E75B6",
        "qa":      "#27AE60",
        "lp":      "#8E44AD",
    }
    accent = accent_colors.get(content_type, "#2E75B6")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="/frontend/css/content-styles.css" />
  <style>
    /* Scoped overrides for this content type */
    .sk-content-header {{
      border-left: 5px solid {accent};
      padding-left: 12px;
      margin-bottom: 24px;
    }}
    .sk-content-header h1 {{
      color: {accent};
      font-size: 1.6rem;
      margin: 0 0 4px 0;
    }}
    .sk-content-header .sk-meta {{
      font-size: 0.85rem;
      color: #777;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
    }}
    th {{
      background: {accent};
      color: white;
      padding: 10px 14px;
      text-align: left;
    }}
    td {{
      padding: 9px 14px;
      border-bottom: 1px solid #eee;
    }}
    tr:nth-child(even) td {{
      background: #f9f9f9;
    }}
    blockquote {{
      border-left: 4px solid {accent};
      margin: 16px 0;
      padding: 10px 16px;
      background: #f5f5f5;
      color: #444;
      font-style: italic;
    }}
    .checklist li::before {{
      content: "✅ ";
    }}
    .schedule-table th {{
      background: {accent};
    }}
  </style>
</head>
<body>
  <div class="sk-lesson-wrapper">
    {body_content}
  </div>
</body>
</html>"""


# ============================================================================
# MAIN CONVERTER CLASS
# ============================================================================

class AIContentConverter:
    """
    Converts raw PDF text into styled HTML for Content, QA, and LP
    using Anthropic Claude API.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Claude AI Converter initialized — model: {self.model}")

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC: Generate all three outputs in one call
    # ──────────────────────────────────────────────────────────────────────────

    def generate_all(self, text: str, metadata: Dict) -> Dict[str, Optional[str]]:
        """
        Master method — generates Content HTML, QA HTML, and LP HTML.

        Args:
            text: Raw text extracted from the PDF lesson
            metadata: {
                'class': int,
                'subject': str,
                'unit': int,
                'lesson_title': str,
                'lesson_type': str,   # prose | poem | supplementary | play
                'term': str,          # term0 | term1 | term2 | term3
                'discipline': str     # for social science (optional)
            }

        Returns:
            {
                'content': <styled HTML string or None>,
                'qa':      <styled HTML string or None>,
                'lp':      <styled HTML string or None>,
            }
        """
        results = {"content": None, "qa": None, "lp": None}

        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num = metadata.get("class", "")
        subject = metadata.get("subject", "english")
        lesson_type = metadata.get("lesson_type", "prose")

        print(f"🤖 Claude generating: Content + QA + LP for '{lesson_title}'")

        # ── Step 1: Content ───────────────────────────────────────────────────
        print(f"   📄 Generating Content HTML...")
        content_html = self._generate_content(text, metadata)
        if content_html:
            results["content"] = _wrap_html(
                content_html,
                title=f"{lesson_title} | Class {class_num} {subject.title()}",
                content_type="content"
            )
            print(f"   ✅ Content HTML ready")
        else:
            print(f"   ❌ Content generation failed")

        # ── Step 2: QA ────────────────────────────────────────────────────────
        print(f"   ❓ Generating QA HTML...")
        qa_html = self._generate_qa(text, metadata)
        if qa_html:
            results["qa"] = _wrap_html(
                qa_html,
                title=f"Q&A — {lesson_title} | Class {class_num}",
                content_type="qa"
            )
            print(f"   ✅ QA HTML ready")
        else:
            print(f"   ❌ QA generation failed")

        # ── Step 3: LP ────────────────────────────────────────────────────────
        print(f"   📌 Generating LP HTML...")
        lp_html = self._generate_lp(text, metadata)
        if lp_html:
            results["lp"] = _wrap_html(
                lp_html,
                title=f"Learning Points — {lesson_title} | Class {class_num}",
                content_type="lp"
            )
            print(f"   ✅ LP HTML ready")
        else:
            print(f"   ❌ LP generation failed")

        return results

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Content generation
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_content(self, text: str, metadata: Dict) -> Optional[str]:
        """Converts raw text into a clean, well-structured HTML content page."""
        try:
            class_num = metadata.get("class", "")
            subject = metadata.get("subject", "english")
            unit = metadata.get("unit", "")
            lesson_title = metadata.get("lesson_title", "Unknown")
            lesson_type = metadata.get("lesson_type", "prose")

            prompt = f"""Convert the following textbook lesson content into clean, well-structured HTML.

Lesson Information:
- Class: {class_num}
- Subject: {subject.title()}
- Unit: {unit}
- Lesson: {lesson_title}
- Type: {lesson_type}

Formatting Rules:
1. Output ONLY the HTML body content — no <html>, <head>, or <body> tags
2. Start with a header div: <div class="sk-content-header"><h1>{lesson_title}</h1><p class="sk-meta">Class {class_num} | {subject.title()} | Unit {unit}</p></div>
3. Use proper heading hierarchy: <h2>, <h3>
4. Wrap paragraphs in <p> tags
5. For poetry: use <div class="poem-stanza"> with <p class="poem-line"> for each line
6. Use <strong> for important terms, <em> for emphasis or foreign words
7. Use <ul><li> for bullet lists where appropriate
8. Format dialogues with <div class="dialogue"> blocks
9. Use <blockquote class="do-you-know"> for "Do You Know?" boxes
10. Remove page numbers and PDF artifacts
11. Keep ALL original content — do not summarize or skip anything
12. Make it readable and student-friendly

Original Text:
---
{text}
---

Output ONLY the HTML body content, nothing else."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,  # Class 10 lessons are long — needs higher limit
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.content[0].text

        except Exception as e:
            print(f"❌ Content generation error: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: QA generation (TL-approved)
    # Prose    → 2 banks: Lesson (100+ Q) + Grammar (100+ Q, from textbook section)
    # Others   → 1 bank:  Lesson (100+ Q) only — no grammar section in textbook
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_qa(self, text: str, metadata: Dict) -> Optional[str]:
        """
        Generates exam-ready question bank HTML.
        Prose → Question Bank 1 (Lesson) + Question Bank 2 (Grammar from textbook)
        Poem / Supplementary / Play → Question Bank 1 (Lesson) only
        All answers in complete sentences, simple English for Tamil-medium students.
        """
        try:
            class_num    = metadata.get("class", "")
            subject      = metadata.get("subject", "english")
            unit         = metadata.get("unit", "")
            lesson_title = metadata.get("lesson_title", "Unknown")
            lesson_type  = metadata.get("lesson_type", "prose")

            duration     = _get_lp_duration(lesson_type)
            has_grammar  = duration["has_grammar"]

            type_display_map = {
                "prose":         "Prose",
                "poem":          "Poem",
                "supplementary": "Supplementary Reader",
                "play":          "Drama or Play",
                "drama":         "Drama or Play",
            }
            type_display = type_display_map.get(lesson_type.lower(), "Prose")

            # ── Grammar Bank section — only for Prose ─────────────────────────
            if has_grammar:
                grammar_bank_instruction = f"""
2. QUESTION BANK 2: GRAMMAR (FROM THE TEXTBOOK GRAMMAR SECTION)

IMPORTANT: Base ALL grammar questions on the grammar topics and exercises that are
ACTUALLY PRESENT in the grammar section of the lesson text provided below.
Do NOT invent grammar topics. Look for the grammar section at the end of the
lesson text (vocabulary exercises, grammar exercises, practice activities).

Cover the grammar areas found in the textbook — typically:
* Tense (identify and use)
* Active and Passive Voice
* Prepositions
* Articles
* Degrees of Comparison
* Question Tags
* Sentence Transformation
* Sentence Correction
* Synonyms and Antonyms
* Parts of Speech

Ensure a wide variety of question types:
* Fill in the blanks
* Rewrite sentences
* Identify errors
* Convert forms
* Create sentences

This bank must also contain AT LEAST 100 questions and answers."""

                output_count = "TWO COMPLETE"
                bank_count = "Each question bank must contain AT LEAST 100 questions and answers."
                bank_list = "1. QUESTION BANK 1: LESSON (PROSE)\n2. QUESTION BANK 2: GRAMMAR (FROM THE TEXTBOOK GRAMMAR SECTION)"
                divider = '- Use <hr class="section-divider"> between the two question banks'

            else:
                grammar_bank_instruction = ""
                output_count = "ONE COMPLETE"
                bank_count = "The question bank must contain AT LEAST 100 questions and answers."
                bank_list = f"1. QUESTION BANK 1: LESSON ({type_display.upper()})"
                divider = ""

            prompt = f"""You are an experienced English teacher familiar with the Tamil Nadu Samacheer Kalvi Class {class_num} syllabus and the needs of students from underprivileged and Tamil-medium backgrounds.

Create {output_count} exam-ready question bank(s) for the lesson "{lesson_title}" (Class {class_num}, Unit {unit}, {type_display}).

OUTPUT REQUIREMENTS
You must generate:
{bank_list}

{bank_count}

QUESTION BANK 1: LESSON ({type_display.upper()})
Cover:
* Comprehension (factual)
* Character analysis (if prose/play)
* Theme and message
* Application and real-life connection
* Vocabulary from the lesson

Structure:
* 1-mark questions
* 2-mark questions
* 5-mark questions
* 8-mark questions
* Additional short questions (to reach 100+ total)
{grammar_bank_instruction}

ANSWER STYLE (VERY IMPORTANT)
* EVERY answer must be a COMPLETE SENTENCE.
* NO one-word answers.
* NO fragments.
* Use SIMPLE ENGLISH (very easy vocabulary).
* Use SHORT sentences.
* Make answers easy for Tamil-medium students to understand.
* Keep answers concise but suitable for scoring marks in exams.

LANGUAGE LEVEL
* Use basic and clear English.
* Avoid complex grammar in answers.
* Prefer clarity over sophistication.

CONSISTENCY CHECK (MANDATORY)
* Proper numbering (1, 2, 3... no missing numbers).
* NO placeholders like "same pattern continues".
* NO skipped answers.
* ALL answers must follow full-sentence format.

Do NOT shorten the response. Do NOT skip any section. Generate the COMPLETE output.

Output as HTML body content ONLY — no <html>, <head>, or <body> tags.

HTML Formatting Rules:
- Start with: <div class="sk-content-header"><h1>Question Bank — {lesson_title}</h1><p class="sk-meta">Class {class_num} | English | Unit {unit} | {type_display}</p></div>
- Use <h2> for each Question Bank heading
- Use <h3> for sub-sections (1-mark questions, 2-mark questions etc.)
- Use <div class="qa-item"> for each Q&A pair:
    <div class="qa-item">
      <p class="question"><strong>Q1. [question]</strong></p>
      <p class="answer"><strong>Answer:</strong> [complete sentence]</p>
    </div>
- Use <div class="marks-badge">1 Mark</div> before each marks section
{divider}
- Clean, well-structured, easy for students to read and study from

Lesson Text (base ALL questions on this — for grammar bank use the grammar section found at the end of the lesson):
---
{text}
---

Output ONLY the HTML body content. Do NOT shorten. Generate ALL 100+ questions."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.content[0].text

        except Exception as e:
            print(f"❌ QA generation error: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: LP generation
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_lp(self, text: str, metadata: Dict) -> Optional[str]:
        """
        Generates a full scripted day-by-day Lesson Plan HTML page.
        TL-approved format — 30 min sessions, exact teacher dialogue,
        student responses, board work, timed blocks.

        Duration (TL approved — applies to ALL English classes):
          Prose         → 10 days (4 content + 6 grammar) — grammar from textbook section
          Poem          → 3 days  (3 content, no grammar)
          Supplementary → 3 days  (3 content, no grammar)
          Play/Drama    → 3 days  (3 content, no grammar)
        """
        try:
            class_num    = metadata.get("class", "")
            subject      = metadata.get("subject", "english")
            unit         = metadata.get("unit", "")
            lesson_title = metadata.get("lesson_title", "Unknown")
            lesson_type  = metadata.get("lesson_type", "prose")

            prompt = _build_lp_prompt(
                class_num=class_num,
                lesson_title=lesson_title,
                lesson_type=lesson_type,
                unit=unit,
                text=text
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,  # Scripted LP is very detailed — needs high limit
                system=LP_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response.content[0].text

        except Exception as e:
            print(f"❌ LP generation error: {e}")
            return None


# Singleton instance
ai_converter = AIContentConverter()