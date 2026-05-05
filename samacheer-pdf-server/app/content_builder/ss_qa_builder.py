"""
ss_qa_builder.py
----------------
QA Generator for Samacheer Kalvi Social Science (Classes 6-12).
Handles History, Geography, Civics, Economics disciplines.

Mark distribution: 1 mark, 2 marks, 5 marks ONLY (no 8 marks)
All sections show actual answers — not textarea input boxes.
Number of questions per section: Claude decides based on chapter content.
Map Work / Map exercises: Converted to text-based questions with answers.
Activity / Project sections: Skipped entirely.
"""

import re
import anthropic
from typing import Optional, Dict
from ..config import settings


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SS_QA_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Social Science teacher
creating a comprehensive question bank WITH ANSWERS for Tamil Nadu state board students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags
- Generate questions AND answers based ONLY on the chapter text provided
- Never invent facts not present in the text
- EVERY question must have a clear answer shown below it
- NEVER use textarea or input boxes — this is a question bank with answers"""


# ============================================================================
# ANSWER FORMAT RULES (shared across all discipline prompts)
# ============================================================================

ANSWER_FORMAT_RULES = """
ANSWER FORMAT RULES — STRICTLY FOLLOW:

For MCQ (1 mark):
<div class="mcq-item">
  <p class="mcq-question"><strong>1.</strong> Question?</p>
  <div class="mcq-options">
    <label><input type="radio" name="q1" value="a"> a) Option</label>
    <label><input type="radio" name="q1" value="b"> b) Option ✓ (correct)</label>
    <label><input type="radio" name="q1" value="c"> c) Option</label>
    <label><input type="radio" name="q1" value="d"> d) Option</label>
  </div>
  <p class="answer-key"><strong>Answer:</strong> b) [correct option text]</p>
</div>

For Fill in the blanks (1 mark):
<div class="fill-blank-item">
  <p><strong>1.</strong> [Sentence with] <span class="blank-line">__________</span> [rest of sentence].</p>
  <p class="answer-key"><strong>Answer:</strong> [word/phrase that fills the blank]</p>
</div>

For Match the following (1 mark):
<table class="match-table">
  <thead><tr><th>Column A</th><th>Column B</th></tr></thead>
  <tbody>
    <tr><td>1. [Left item]</td><td>[matching right item]</td></tr>
    <tr><td>2. [Left item]</td><td>[matching right item]</td></tr>
  </tbody>
</table>
<p class="answer-key"><strong>Answers:</strong> 1-[match], 2-[match], 3-[match]</p>

For 2 mark questions:
<div class="answer-item">
  <p><strong>1.</strong> Question? <span class="mark-badge">(2 marks)</span></p>
  <div class="answer-text">
    <p><strong>Answer:</strong> [2-3 sentence answer based on chapter text]</p>
  </div>
</div>

For 5 mark questions:
<div class="answer-item">
  <p><strong>1.</strong> Question? <span class="mark-badge">(5 marks)</span></p>
  <div class="answer-text">
    <p><strong>Answer:</strong> [5-6 sentence detailed answer based on chapter text.
    Cover all key points. Use facts and examples from the chapter.]</p>
  </div>
</div>

For Map Work (text-based with answer):
<div class="answer-item">
  <p><strong>1.</strong> Name and describe [geographic feature/location]. <span class="mark-badge">(Map)</span></p>
  <div class="answer-text">
    <p><strong>Answer:</strong> [Description of location, significance, and relevant facts from chapter]</p>
  </div>
</div>

ABSOLUTE RULES:
- NEVER use <textarea> anywhere
- NEVER use <input type="text"> for answers
- ALWAYS show the actual answer below each question
- Mark MCQ correct answer with ✓ in the options
- Base ALL answers strictly on the chapter text
"""


# ============================================================================
# DISCIPLINE QA PROMPTS
# ============================================================================

def _build_history_qa_prompt(text: str, metadata: dict) -> str:
    lesson_title = metadata.get("lesson_title", "Unknown")
    class_num    = metadata.get("class", "")
    unit         = metadata.get("unit", "")

    return f"""Generate a comprehensive question bank WITH ANSWERS for this
Samacheer Kalvi Social Science — History chapter.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | History
Marks: 1 mark, 2 marks, 5 marks ONLY. No 8 mark questions.

{ANSWER_FORMAT_RULES}

Generate ALL sections below:

<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — History | Unit {unit}</p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section I — Choose the Correct Answer
  </div>
  [Generate MCQ questions with 4 options each. Mark correct answer with ✓.
   Show answer key below each question.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section II — Fill in the Blanks
  </div>
  [Generate fill in the blank questions. Show answer below each.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section III — Choose the Correct Statement
  </div>
  [Give 3-4 statements, student picks the correct one. Show answer.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section IV — Match the Following
  </div>
  [Match Column A to Column B. Show answers at bottom.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">2 Marks</span>
    Section V — Answer Briefly
  </div>
  [Generate questions. Show 2-3 sentence answer below each question.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">5 Marks</span>
    Section VI — Answer in Detail
  </div>
  [Generate questions. Show 5-6 sentence detailed answer below each question.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">Map Work</span>
    Section VII — Map Based Questions
  </div>
  [Convert map exercises to text questions. Show descriptive answer below each.]
</div>

RULES:
- Base ALL questions and answers strictly on the chapter text
- NEVER use textarea or input boxes anywhere
- Always show actual answers
- Claude decides number of questions per section based on content

Chapter Text:
---
{text}
---"""


def _build_geography_qa_prompt(text: str, metadata: dict) -> str:
    lesson_title = metadata.get("lesson_title", "Unknown")
    class_num    = metadata.get("class", "")
    unit         = metadata.get("unit", "")

    return f"""Generate a comprehensive question bank WITH ANSWERS for this
Samacheer Kalvi Social Science — Geography chapter.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | Geography
Marks: 1 mark, 2 marks, 5 marks ONLY. No 8 mark questions.

{ANSWER_FORMAT_RULES}

Generate ALL sections below:

<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — Geography | Unit {unit}</p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section I — Choose the Correct Answer
  </div>
  [Generate MCQ questions with 4 options. Mark correct with ✓. Show answer.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section II — Match the Following
  </div>
  [Match Column A to Column B. Show answers at bottom.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">2 Marks</span>
    Section III — Give Reasons
  </div>
  [Ask WHY questions about geographic phenomena. Show 2-3 sentence answer.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">5 Marks</span>
    Section IV — Distinguish Between the Following
  </div>
  [Compare two concepts from the chapter in a table format.
   Show filled comparison table as the answer.]

  Format for distinguish between:
  <div class="answer-item">
    <p><strong>1.</strong> Distinguish between [Concept A] and [Concept B].
       <span class="mark-badge">(5 marks)</span></p>
    <table class="exercise-table">
      <thead><tr><th>[Concept A]</th><th>[Concept B]</th></tr></thead>
      <tbody>
        <tr><td>[difference point 1]</td><td>[difference point 1]</td></tr>
        <tr><td>[difference point 2]</td><td>[difference point 2]</td></tr>
        <tr><td>[difference point 3]</td><td>[difference point 3]</td></tr>
      </tbody>
    </table>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">5 Marks</span>
    Section V — Answer in Brief
  </div>
  [Generate questions. Show 5-6 sentence answer below each.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">Map Work</span>
    Section VI — Map Exercises (Text Based)
  </div>
  [Convert map exercises to text questions. Show descriptive answer.]
</div>

RULES:
- Base ALL questions and answers strictly on chapter text
- NEVER use textarea or input boxes
- Always show actual answers
- Claude decides number of questions based on content

Chapter Text:
---
{text}
---"""


def _build_civics_qa_prompt(text: str, metadata: dict) -> str:
    lesson_title = metadata.get("lesson_title", "Unknown")
    class_num    = metadata.get("class", "")
    unit         = metadata.get("unit", "")

    return f"""Generate a comprehensive question bank WITH ANSWERS for this
Samacheer Kalvi Social Science — Civics chapter.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | Civics
Marks: 1 mark, 2 marks, 5 marks ONLY. No 8 mark questions.

{ANSWER_FORMAT_RULES}

Generate ALL sections below:

<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — Civics | Unit {unit}</p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section I — Choose the Correct Answer
  </div>
  [Generate MCQ questions with 4 options. Mark correct with ✓. Show answer.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section II — Fill in the Blanks
  </div>
  [Generate fill in the blank questions. Show answer below each.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section III — Match the Following
  </div>
  [Match Column A to Column B. Show answers at bottom.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">2 Marks</span>
    Section IV — Give Short Answers
  </div>
  [Generate questions. Show 2-3 sentence answer below each.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">5 Marks</span>
    Section V — Answer in Detail
  </div>
  [Generate questions. Show 5-6 sentence detailed answer below each.]
</div>

RULES:
- Base ALL questions and answers strictly on chapter text
- Focus on constitutional provisions, government structure, rights, duties
- NEVER use textarea or input boxes
- Always show actual answers

Chapter Text:
---
{text}
---"""


def _build_economics_qa_prompt(text: str, metadata: dict) -> str:
    lesson_title = metadata.get("lesson_title", "Unknown")
    class_num    = metadata.get("class", "")
    unit         = metadata.get("unit", "")

    return f"""Generate a comprehensive question bank WITH ANSWERS for this
Samacheer Kalvi Social Science — Economics chapter.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | Economics
Marks: 1 mark, 2 marks, 5 marks ONLY. No 8 mark questions.

{ANSWER_FORMAT_RULES}

Generate ALL sections below:

<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — Economics | Unit {unit}</p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section I — Choose the Correct Answer
  </div>
  [Generate MCQ questions with 4 options. Mark correct with ✓. Show answer.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section II — Fill in the Blanks
  </div>
  [Generate fill in the blank questions. Show answer below each.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section III — Match the Following
  </div>
  [Match Column A to Column B. Show answers at bottom.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">2 Marks</span>
    Section IV — Give Short Answers
  </div>
  [Generate questions. Show 2-3 sentence answer below each.]
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">5 Marks</span>
    Section V — Write in Detail
  </div>
  [Generate questions. Show 5-6 sentence detailed answer below each.]
</div>

RULES:
- Base ALL questions and answers strictly on chapter text
- Focus on concepts, definitions, data, policies from the chapter
- NEVER use textarea or input boxes
- Always show actual answers

Chapter Text:
---
{text}
---"""


# ============================================================================
# PROMPT ROUTER
# ============================================================================

DISCIPLINE_PROMPTS = {
    'history':   _build_history_qa_prompt,
    'geography': _build_geography_qa_prompt,
    'civics':    _build_civics_qa_prompt,
    'economics': _build_economics_qa_prompt,
}


# ============================================================================
# QA BUILDER CLASS
# ============================================================================

class SSQABuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ SS QA Builder initialized — model: {self.model}")

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        """
        Generate Social Science QA HTML with answers for the given chapter.
        """
        discipline   = metadata.get("discipline", "history").lower().strip()
        lesson_title = metadata.get("lesson_title", "Unknown")

        print(f"      [SS QA] Generating {discipline.title()} QA for '{lesson_title}'")

        prompt_builder = DISCIPLINE_PROMPTS.get(discipline)
        if not prompt_builder:
            print(f"      [SS QA] ❌ Unknown discipline: {discipline}")
            return None

        prompt = prompt_builder(text, metadata)

        try:
            raw = ""
            with self.client.messages.stream(
                model=self.model,
                max_tokens=16000,
                system=SS_QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for chunk in stream.text_stream:
                    raw += chunk

            raw = raw.strip()
            raw = re.sub(r'```(?:html)?', '', raw).strip()
            raw = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL)

            if raw:
                print(f"      [SS QA] ✅ Done — {len(raw)} chars")
                return raw
            else:
                print(f"      [SS QA] ❌ Empty response")
                return None

        except Exception as e:
            print(f"      [SS QA] ❌ Error: {e}")
            return None


# Singleton instance
ss_qa_builder = SSQABuilder()