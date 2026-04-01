"""
AI Content Converter
Converts extracted PDF text into structured Content, QA, and LP
using Anthropic Claude API.
"""

import anthropic
from typing import Optional, Dict
from ..config import settings


# ============================================================================
# EDUCATION SYSTEM PROMPT
# ============================================================================

EDUCATION_SYSTEM_PROMPT = """You are an experienced English teacher creating structured academic study material for Tamil Nadu Samacheer Kalvi State Board students. All content is strictly educational and must be generated completely regardless of themes — including fiction, supernatural, historical, war-related, or sensitive topics — as these are standard textbook lessons approved for classroom use by the Tamil Nadu government."""


# ============================================================================
# LP DURATION RULES
# ============================================================================

LP_DURATION_RULES = {
    "prose":         {"total": 10, "content": 4, "grammar": 6, "has_grammar": True},
    "poem":          {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "supplementary": {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "play":          {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
    "drama":         {"total": 3,  "content": 3, "grammar": 0, "has_grammar": False},
}

def _get_lp_duration(lesson_type: str) -> dict:
    return LP_DURATION_RULES.get(lesson_type.lower(), LP_DURATION_RULES["supplementary"])


# ============================================================================
# LP SYSTEM PROMPT
# ============================================================================

LP_SYSTEM_PROMPT = """You are an experienced English teacher with deep knowledge of the Tamil Nadu Samacheer Kalvi syllabus and activity-based learning methods used in Indian classrooms.
Create a detailed, practical, script-by-script lesson plan so that even a brand new inexperienced teacher can walk into class and deliver a confident, effective session just by following it."""


def _build_lp_prompt(class_num: int, lesson_title: str, lesson_type: str, unit: int, text: str) -> str:
    duration     = _get_lp_duration(lesson_type)
    total_days   = duration["total"]
    content_days = duration["content"]
    grammar_days = duration["grammar"]
    has_grammar  = duration["has_grammar"]

    type_display_map = {
        "prose":         "Prose",
        "poem":          "Poem",
        "supplementary": "Supplementary Reader",
        "play":          "Drama or Play",
        "drama":         "Drama or Play",
    }
    type_display = type_display_map.get(lesson_type.lower(), "Prose")

    if has_grammar:
        duration_line = f"{total_days} days ({content_days} Content Days + {grammar_days} Grammar Days)"
    else:
        duration_line = f"{total_days} days (Content Only — no grammar section for this lesson type)"

    grammar_section = ""
    if has_grammar:
        grammar_section = f"""
═══════════════════════════════════════════════════════
PART 5: GRAMMAR DAYS (Day {content_days + 1} to Day {total_days})
═══════════════════════════════════════════════════════

IMPORTANT: Grammar days must be based ONLY on the grammar topics and exercises
that are actually present in the grammar section of the lesson text provided below.
Do NOT invent grammar topics. Do NOT use random grammar unrelated to this lesson.

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
Q1: [question] — Answer: [complete sentence]
Q2: [question] — Answer: [complete sentence]
Q3: [question] — Answer: [complete sentence]
Q4: [question] — Answer: [complete sentence]
Q5: [question] — Answer: [complete sentence]
Teacher circulates and says: "[encouraging words]"

[25-30 min] CLOSURE + QUICK REVISION
Teacher says: "[summarize the grammar rule in 2 simple sentences]"
Board Work: [write the rule + one example]
Exit Question: "[one grammar question every student answers before leaving]"
Expected answer: "[complete sentence]"
Teacher says: "[closing + preview of next day]"
Homework: [3-5 grammar practice questions]
Model Answer: "[one complete model answer]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate Day {content_days + 1} through Day {total_days} following this format exactly.
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
Teacher says: "[exact words]"
Board Work: [exactly what appears on board]
Teacher asks: "[question to class]"
Expected student response: "[complete sentence answer]"
Transition: Teacher says: "[exact words to move to next segment]"

[5-15 min] MAIN ACTIVITY
🎯 Objective: [what this segment achieves]
Teacher says: "[exact instructions]"
Board Work: [exactly what appears on board]
Student Activity: [exactly what students do]
Expected student response: "[sample answers]"
If students struggle: Teacher says: "[supportive hint]"
Transition: Teacher says: "[exact words]"

[15-25 min] STUDENT PRACTICE
🎯 Objective: [what this segment achieves]
Teacher says: "[exact instructions]"
Activity Type: [Think-Pair-Share / Group work / Individual / Role play]
Step 1: [exact instruction]
Step 2: [exact instruction]
Step 3: [exact instruction]
Expected output: "[what students should produce]"
Teacher circulates and says: "[what to say]"
Transition: Teacher says: "[exact words]"

[25-30 min] CLOSURE
🎯 Objective: Consolidate learning
Teacher says: "[summarize key points]"
Board Work: [3-5 key words / summary sentence]
Exit Question: "[one question every student must answer]"
Expected answer: "[complete sentence]"
Teacher says: "[closing + preview of next day]"
Homework: [specific, simple task]
Model Answer: "[one complete model answer]"
Teacher says: "Copy this model answer in your notebook as a guide."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate Day 1 through Day {content_days}. Each day covers a different part progressively.
{grammar_section}
═══════════════════════════════════════════════════════
PART 6: ASSESSMENT SUMMARY
═══════════════════════════════════════════════════════
• Day-wise oral assessment questions (one per day)
• Written assessment task for end of lesson
• Differentiated support: slow learners vs advanced learners

Now output as HTML body content ONLY — no <html>, <head>, or <body> tags.

HTML Rules:
- Start: <div class="sk-content-header"><h1>Lesson Plan — {lesson_title}</h1><p class="sk-meta">Class {class_num} | English | Unit {unit} | {type_display} | {duration_line}</p></div>
- <h2> for PART headings
- <h3 class="day-header"> for each Day
- <div class="day-block"> wraps each day
- <div class="time-block"> for each timed segment
- <p class="teacher-says"><strong>Teacher says:</strong> "..."</p>
- <p class="student-says"><strong>Expected response:</strong> "..."</p>
- <div class="board-work"><strong>Board Work:</strong> ...</div>
- <div class="transition"><em>Transition:</em> ...</div>
- <table> for exercises
- <ul><li> for bullet lists

Lesson Text:
---
{text}
---

Output ONLY the HTML body content. Be detailed. Do NOT skip any day. Do NOT shorten."""


# ============================================================================
# HTML WRAPPER
# ============================================================================

def _wrap_html(body_content: str, title: str, content_type: str = "content") -> str:
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
    tr:nth-child(even) td {{ background: #f9f9f9; }}
    blockquote {{
      border-left: 4px solid {accent};
      margin: 16px 0;
      padding: 10px 16px;
      background: #f5f5f5;
      color: #444;
      font-style: italic;
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

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Claude AI Converter initialized — model: {self.model}")

    def generate_all(self, text: str, metadata: Dict) -> Dict[str, Optional[str]]:
        results = {"content": None, "qa": None, "lp": None}
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        subject      = metadata.get("subject", "english")

        print(f"🤖 Claude generating: Content + QA + LP for '{lesson_title}'")

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

        print(f"   📌 Generating LP HTML...")
        lp_html = self._generate_lp(text, metadata)
        if lp_html:
            results["lp"] = _wrap_html(
                lp_html,
                title=f"Lesson Plan — {lesson_title} | Class {class_num}",
                content_type="lp"
            )
            print(f"   ✅ LP HTML ready")
        else:
            print(f"   ❌ LP generation failed")

        return results

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Content generation — split dispatcher
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_content(self, text: str, metadata: Dict) -> Optional[str]:
        lesson_type = metadata.get("lesson_type", "prose")
        # Poems and supplementary are short — use higher threshold to avoid splitting
        threshold = 10000 if lesson_type == "prose" else 20000
        if len(text) <= threshold:
            print(f"      [Content] Short text ({len(text)} chars) → single call")
            return self._generate_single_content(text, metadata, is_continuation=False)
        else:
            print(f"      [Content] Long text ({len(text)} chars) → splitting into 2 parts")
            midpoint = len(text) // 2  # ✅ define midpoint first!
            # Split at sentence boundary (period + newline)
            split_point = text.find('.\n', midpoint)
            if split_point == -1:
                split_point = text.find('\n', midpoint)
            if split_point == -1:
                split_point = midpoint
            # Include the period in part 1
            split_point += 1
            part1 = self._generate_single_content(text[:split_point], metadata, is_continuation=False)
            part2 = self._generate_single_content(text[split_point:], metadata, is_continuation=True)
            if part1 and part2:
                return part1 + "\n\n" + part2
            elif part1:
                return part1
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Single content API call
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_single_content(self, text: str, metadata: Dict, is_continuation: bool = False) -> Optional[str]:
        try:
            class_num    = metadata.get("class", "")
            subject      = metadata.get("subject", "english")
            unit         = metadata.get("unit", "")
            lesson_title = metadata.get("lesson_title", "Unknown")
            lesson_type  = metadata.get("lesson_type", "prose")

            if is_continuation:
                header_instruction = """This is the CONTINUATION of the lesson already started.
DO NOT add any title, header, or <div class="sk-content-header"> block.
DO NOT repeat the lesson name or meta info.
DO NOT add a second Summary box — Summary goes ONLY at the very end of the final part.
IMPORTANT: If the text below contains About the Author, Do You Know, or Glossary sections,
you MUST include them — they are in this part of the text, not in Part 1.
Continue rendering ALL content present in the text below without skipping anything.
Start immediately with whatever content appears first in the text below."""
            else:
                header_instruction = f"""Start with this exact header:
<div class="sk-content-header">
  <h1>{lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | {subject.title()} | Unit {unit}</p>
</div>"""

            prompt = f"""Convert the following Tamil Nadu Samacheer Kalvi Class {class_num} English textbook lesson into clean, polished, interactive HTML.

Lesson: {lesson_title} | Class {class_num} | {subject.title()} | Unit {unit} | Type: {lesson_type}

{header_instruction}

═══════════════════════════════════════════════════════
OUTPUT STRUCTURE
═══════════════════════════════════════════════════════

1. HEADER
{header_instruction}

2. ABOUT THE AUTHOR (only if author info exists in text)
<div class="about-author">
  <div class="author-icon">✍️</div>
  <div>
    <div class="author-title">About the Author</div>
    <div class="author-name">[Author Name]</div>
    <p>[Author details from text]</p>
  </div>
</div>
IMPORTANT: About the Author and Do You Know are ALWAYS two SEPARATE components.
NEVER merge them into one box. Each must be its own distinct HTML block.

3. LESSON CONTENT
- <h2> for main sections, <h3> for subsections
- <p> for all paragraphs
- Keep ALL original content — never skip or summarize
- For inline questions (a. b. c. labeled questions inside the story):
  Use this format:
  <div class="inline-question">
    <p><strong>a. Question text here?</strong></p>
    <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div>
  </div>

4. POEM (only for poem type)
<div class="poem-container">
  <div class="poem-stanza">
    <span class="poem-line">Line one</span>
    <span class="poem-line">Line two</span>
    <span class="poem-line">Line three</span>
    <span class="poem-line">Line four</span>
  </div>
</div>

5. DIALOGUE (for interviews/conversations)
<div class="dialogue-block">
  <div class="speaker">Speaker Name</div>
  <p class="speech">Exact speech from text.</p>
</div>

6. DO YOU KNOW
<div class="do-you-know">
  <div class="dyk-title">Do You Know?</div>
  <p>Content exactly as in text.</p>
</div>

7. GLOSSARY
<div class="glossary-section">
  <h3>Glossary</h3>
  <div class="glossary-grid">
    <div class="glossary-card">
      <div class="word">word</div>
      <span class="word-type">(n/v/adj/adv)</span>
      <div class="word-meaning">meaning from text</div>
    </div>
  </div>
</div>

8. EXERCISES — MATCH THE EXACT COMPONENT TO EACH EXERCISE TYPE:

FILL IN THE BLANKS:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Exercise Letter]. [Title]</div>
  <div class="help-box"><span class="help-box-label">Word Bank:</span> word1 | word2 | word3</div>
  <div class="fill-blank-sentence">1. Sentence with <input class="blank-input" type="text" placeholder="______" /> in it.</div>
  <div class="fill-blank-sentence">2. Another sentence with <input class="blank-input" type="text" placeholder="______" /> blank.</div>
</div>

TRUE OR FALSE:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Exercise Letter]. [Title]</div>
  <div class="true-false-item">
    <span class="tf-number">1.</span>
    <span class="tf-statement">Statement from the lesson.</span>
    <div class="tf-options">
      <button class="tf-btn true-btn">True</button>
      <button class="tf-btn false-btn">False</button>
    </div>
  </div>
  <div class="true-false-item">
    <span class="tf-number">2.</span>
    <span class="tf-statement">False statement needing correction.</span>
    <div class="tf-options">
      <button class="tf-btn true-btn">True</button>
      <button class="tf-btn false-btn">False</button>
    </div>
    <div class="tf-correction">Correction: <input class="blank-input" type="text" placeholder="Write correct answer" /></div>
  </div>
</div>

MULTIPLE CHOICE:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Exercise Letter]. [Title]</div>
  <div class="mcq-item">
    <div class="mcq-question">1. Question from the lesson?</div>
    <div class="mcq-options">
      <label class="mcq-option"><input type="radio" name="q1" /><span class="option-letter">a.</span> Option A</label>
      <label class="mcq-option"><input type="radio" name="q1" /><span class="option-letter">b.</span> Option B</label>
      <label class="mcq-option"><input type="radio" name="q1" /><span class="option-letter">c.</span> Option C</label>
      <label class="mcq-option"><input type="radio" name="q1" /><span class="option-letter">d.</span> Option D</label>
    </div>
  </div>
</div>

MATCH THE FOLLOWING:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Exercise Letter]. Match the Following</div>
  <table class="match-table">
    <thead><tr><th>Column A</th><th>Column B</th><th>Answer</th></tr></thead>
    <tbody>
      <tr><td>1. item one</td><td>a. match one</td><td><input class="match-input" type="text" placeholder="__" /></td></tr>
      <tr><td>2. item two</td><td>b. match two</td><td><input class="match-input" type="text" placeholder="__" /></td></tr>
    </tbody>
  </table>
</div>

SHORT ANSWER (2-5 marks):
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Exercise Letter]. Answer Briefly</div>
  <div style="margin-bottom:20px;">
    <p><strong>1. Question from the lesson?</strong></p>
    <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div>
  </div>
  <div style="margin-bottom:20px;">
    <p><strong>2. Another question?</strong></p>
    <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div>
  </div>
</div>

LONG ANSWER (8+ marks):
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Exercise Letter]. Answer in Detail (100-150 words)</div>
  <div style="margin-bottom:20px;">
    <p><strong>1. Detailed question from the lesson?</strong></p>
    <div class="answer-box long"><textarea placeholder="Write your detailed answer here..."></textarea></div>
  </div>
</div>

9. SUMMARY (always last)
<div class="summary-box">
  <div class="summary-title">📋 Summary</div>
  <ul>
    <li>Key point 1 from the lesson</li>
    <li>Key point 2 from the lesson</li>
    <li>Key point 3 from the lesson</li>
    <li>Key point 4 from the lesson</li>
    <li>Key point 5 from the lesson</li>
  </ul>
</div>

═══════════════════════════════════════════════════════
ABSOLUTE RULES — NEVER BREAK
═══════════════════════════════════════════════════════
✅ Output ONLY HTML body content — NO html/head/body tags
✅ NEVER use underscores ___ for blanks — ALWAYS <input class="blank-input">
✅ NEVER plain list items for MCQ — ALWAYS .mcq-option with radio buttons
✅ NEVER plain paragraphs for glossary — ALWAYS .glossary-card
✅ NEVER plain blockquote for Do You Know — ALWAYS .do-you-know div
✅ NEVER plain text for dialogue — ALWAYS .dialogue-block
✅ NEVER plain text for poems — ALWAYS .poem-container with .poem-stanza
✅ Keep ALL original content — never skip, never summarize
✅ Every exercise from the textbook must appear with correct component
✅ EVERY table MUST have <thead> with <th> column headers — NEVER skip table headers
✅ For Parts of Speech table use headers: Noun | Verb | Adjective | Adverb
✅ For Match table use headers: Column A | Column B | Answer
✅ NEVER generate a table without proper column headings
✅ NEVER leave inline questions (a. b. c.) without an answer textarea
✅ ALWAYS add <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div> after EVERY inline question
✅ NEVER add a Summary box mid-lesson — Summary goes ONLY at the very end after all exercises
✅ ALWAYS render About the Author, Do You Know, Glossary if they appear in the text — NEVER skip them
✅ NEVER merge About the Author and Do You Know into one box — they are ALWAYS separate HTML blocks

Original Lesson Text:
---
{text}
---

Output ONLY the HTML body content. Be complete and thorough."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=EDUCATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            print(f"❌ Content generation error: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: QA generation — split dispatcher
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_qa(self, text: str, metadata: Dict) -> Optional[str]:
        lesson_type = metadata.get("lesson_type", "prose")
        threshold = 10000 if lesson_type == "prose" else 20000
        if len(text) <= threshold:
            print(f"      [QA] Short text ({len(text)} chars) → single call")
            return self._generate_single_qa(text, metadata, start_from=1, target=100)
        else:
            print(f"      [QA] Long text ({len(text)} chars) → splitting into 2 parts")
            midpoint = len(text) // 2  # ✅ define midpoint first!
            # Split at sentence boundary (period + newline)
            split_point = text.find('.\n', midpoint)
            if split_point == -1:
                split_point = text.find('\n', midpoint)
            if split_point == -1:
                split_point = midpoint
            # Include the period in part 1
            split_point += 1
            part1 = self._generate_single_qa(text[:split_point], metadata, start_from=1, target=50)
            part2 = self._generate_single_qa(text[split_point:], metadata, start_from=51, target=50)
            if part1 and part2:
                return part1 + "\n\n" + part2
            elif part1:
                return part1
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Single QA API call
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_single_qa(self, text: str, metadata: Dict, start_from: int = 1, target: int = 100) -> Optional[str]:
        try:
            class_num    = metadata.get("class", "")
            unit         = metadata.get("unit", "")
            lesson_title = metadata.get("lesson_title", "Unknown")
            lesson_type  = metadata.get("lesson_type", "prose")

            duration    = _get_lp_duration(lesson_type)
            has_grammar = duration["has_grammar"]

            type_display_map = {
                "prose":         "Prose",
                "poem":          "Poem",
                "supplementary": "Supplementary Reader",
                "play":          "Drama or Play",
                "drama":         "Drama or Play",
            }
            type_display = type_display_map.get(lesson_type.lower(), "Prose")

            if start_from > 1:
                header_instruction = f"DO NOT add Question Bank header. Continue generating MORE questions directly. Start from Q{start_from} onwards."
            else:
                header_instruction = f"Start with: <div class=\"sk-content-header\"><h1>Question Bank — {lesson_title}</h1><p class=\"sk-meta\">Class {class_num} | English | Unit {unit} | {type_display}</p></div>"

            bank_count = f"Generate EXACTLY {target} questions starting from Q{start_from}. Stop exactly at Q{start_from + target - 1}."

            if has_grammar:
                grammar_bank_instruction = f"""
2. QUESTION BANK 2: GRAMMAR (FROM TEXTBOOK GRAMMAR SECTION)
Base ALL grammar questions on grammar topics ACTUALLY in the lesson text.
Cover: Tense, Voice, Prepositions, Articles, Degrees, Question Tags, Transformation, Parts of Speech.
{bank_count}"""
                output_count = "TWO COMPLETE"
                bank_list    = "1. QUESTION BANK 1: LESSON\n2. QUESTION BANK 2: GRAMMAR"
                divider      = '- Use <hr class="section-divider"> between the two banks'
            else:
                grammar_bank_instruction = ""
                output_count = "ONE COMPLETE"
                bank_list    = f"1. QUESTION BANK 1: LESSON ({type_display.upper()})"
                divider      = ""

            prompt = f"""Create {output_count} exam-ready question bank(s) for:
"{lesson_title}" — Class {class_num} | Unit {unit} | {type_display}

BANKS TO GENERATE:
{bank_list}
{bank_count}

QUESTION TYPES — distribute like this to reach the target count:
- 1-mark questions: Fill in the blank, One word answer, True/False, Choose the correct rhyming word
- 2-mark questions: Short answer (2-3 sentences), explain a line, find the figure of speech
- 5-mark questions: Paragraph answer, central idea, character/theme analysis
- 8-mark questions: Essay type, detailed explanation, appreciation of the poem/passage

TOPICS: Comprehension, Line meaning, Rhyme scheme, Figure of speech, Theme, Vocabulary, Application
IMPORTANT: If the text is short (poem/supplementary), generate MORE 1-mark and 2-mark questions
to reach the target. Use vocabulary, rhyme, figures of speech, true/false, fill-in-blank questions
to pad up to the exact target count. NEVER stop before reaching Q{start_from + target - 1}.
{grammar_bank_instruction}

ANSWER RULES:
- EVERY answer = complete sentence
- NO one-word answers
- Simple English for Tamil-medium students
- Exam-ready format

Output HTML body ONLY. No html/head/body tags.

HTML:
- {header_instruction}
- <h2> for each bank, <h3> for mark sections
- Each Q&A: <div class="qa-item"><p class="question"><strong>Q{start_from}. question</strong></p><p class="answer"><strong>Answer:</strong> sentence.</p></div>
- <div class="marks-badge">1 Mark</div> before each section
{divider}

Lesson Text:
---
{text}
---

Generate EXACTLY {target} questions starting from Q{start_from}.
You MUST reach Q{start_from + target - 1}. This is non-negotiable.
Count every question as you go. After every 10 questions, check your count.
If you run out of comprehension questions, add vocabulary, theme,
value-based and creative questions to reach exactly {target}.
Do NOT stop before Q{start_from + target - 1}.
Do NOT add any header if this is a continuation (start_from > 1)."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=EDUCATION_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            print(f"❌ QA generation error: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: LP generation — split dispatcher
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_lp(self, text: str, metadata: Dict) -> Optional[str]:
        lesson_type = metadata.get("lesson_type", "prose")
        threshold = 10000 if lesson_type == "prose" else 20000
        if len(text) <= threshold:
            print(f"      [LP] Short text ({len(text)} chars) → single call")
            return self._generate_single_lp(text, metadata, is_continuation=False)
        else:
            print(f"      [LP] Long text ({len(text)} chars) → splitting into 2 parts")
            midpoint = len(text) // 2  # ✅ define midpoint first!
            # Split at sentence boundary (period + newline)
            split_point = text.find('.\n', midpoint)
            if split_point == -1:
                split_point = text.find('\n', midpoint)
            if split_point == -1:
                split_point = midpoint
            # Include the period in part 1
            split_point += 1
            part1 = self._generate_single_lp(text[:split_point], metadata, is_continuation=False)
            part2 = self._generate_single_lp(text[split_point:], metadata, is_continuation=True)
            if part1 and part2:
                return part1 + "\n\n" + part2
            elif part1:
                return part1
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE: Single LP API call
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_single_lp(self, text: str, metadata: Dict, is_continuation: bool = False) -> Optional[str]:
        try:
            class_num    = metadata.get("class", "")
            unit         = metadata.get("unit", "")
            lesson_title = metadata.get("lesson_title", "Unknown")
            lesson_type  = metadata.get("lesson_type", "prose")

            if is_continuation:
                prompt = f"""This is CONTINUATION of the lesson plan already started.
DO NOT add General Information, Learning Objectives, or Teaching Aids sections again.
Continue DIRECTLY from where Day content left off.
Generate remaining days and Assessment Summary.
Use same HTML format as before.

Lesson Text (second half):
---
{text}
---"""
            else:
                prompt = _build_lp_prompt(
                    class_num=class_num,
                    lesson_title=lesson_title,
                    lesson_type=lesson_type,
                    unit=unit,
                    text=text
                )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text

        except Exception as e:
            print(f"❌ LP generation error: {e}")
            return None


# Singleton instance
ai_converter = AIContentConverter()