"""
ss_qa_builder.py
----------------
QA Generator for Samacheer Kalvi Social Science (Classes 6-12).
Handles History, Geography, Civics, Economics disciplines.

Each discipline has its own section format following Samacheer syllabus:
  History   → Choose correct, Fill blanks, Correct statement, Match,
               Answer briefly, Answer in detail, Map Work (text-based)
  Geography → Choose correct, Match, Give Reasons, Distinguish between,
               Answer in brief, Answer in paragraph, Map exercises (text-based)
  Civics    → Choose correct, Fill blanks, Match, Give short answers,
               Answer in detail
  Economics → Choose correct, Fill blanks, Match, Give short answers,
               Write in detail

Mark distribution: 1 mark, 2 marks, 5 marks, 8 marks
Number of questions per section: Claude decides based on chapter content.
Map Work / Map exercises: Converted to text-based questions.
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
creating a comprehensive question bank for Tamil Nadu state board students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags
- Generate questions based ONLY on the chapter text provided
- Never invent facts not present in the text"""


# ============================================================================
# DISCIPLINE QA PROMPTS
# ============================================================================

def _build_history_qa_prompt(text: str, metadata: dict) -> str:
    lesson_title = metadata.get("lesson_title", "Unknown")
    class_num    = metadata.get("class", "")
    unit         = metadata.get("unit", "")
    discipline   = metadata.get("discipline", "history").title()

    return f"""Generate a comprehensive question bank for this Samacheer Kalvi
Social Science — History chapter.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | {discipline}

Generate ALL sections below. Claude decides how many questions per section
based on chapter content — enough to cover all key topics thoroughly.

FORMAT:

<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — History | Unit {unit}</p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section I — Choose the Correct Answer
  </div>
  [For each question:]
  <div class="mcq-item">
    <p class="mcq-question"><strong>1.</strong> Question?</p>
    <div class="mcq-options">
      <label><input type="radio" name="h_q1" value="a"> a) Option</label>
      <label><input type="radio" name="h_q1" value="b"> b) Option</label>
      <label><input type="radio" name="h_q1" value="c"> c) Option</label>
      <label><input type="radio" name="h_q1" value="d"> d) Option</label>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section II — Fill in the Blanks
  </div>
  [For each question:]
  <div class="fill-blank-item">
    <p><strong>1.</strong> [Sentence with] <input class="blank-input" type="text"
       placeholder="______" style="width:160px;"> [rest of sentence].</p>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section III — Choose the Correct Statement
  </div>
  [For each question, give 3-4 statements, student picks the correct one:]
  <div class="mcq-item">
    <p class="mcq-question"><strong>1.</strong> Which of the following is correct?</p>
    <div class="mcq-options">
      <label><input type="radio" name="cs_q1" value="a"> a) Statement 1</label>
      <label><input type="radio" name="cs_q1" value="b"> b) Statement 2</label>
      <label><input type="radio" name="cs_q1" value="c"> c) Statement 3</label>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section IV — Match the Following
  </div>
  <table class="match-table">
    <thead>
      <tr><th>Column A</th><th>Column B</th></tr>
    </thead>
    <tbody>
      [For each pair:]
      <tr>
        <td>1. [Left item]</td>
        <td><input class="blank-input" type="text"
            placeholder="Match..." style="width:180px;"></td>
      </tr>
    </tbody>
  </table>
  <p><em>Column B options: [list all right-side items]</em></p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">2 Marks</span>
    Section V — Answer Briefly
  </div>
  [For each question:]
  <div class="answer-item">
    <p><strong>1.</strong> Question? (2 marks)</p>
    <div class="answer-box">
      <textarea placeholder="Write your answer here..." rows="3"></textarea>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">8 Marks</span>
    Section VI — Answer in Detail
  </div>
  [For each question:]
  <div class="answer-item">
    <p><strong>1.</strong> Question? (8 marks)</p>
    <div class="answer-box long">
      <textarea placeholder="Write your detailed answer here..." rows="8"></textarea>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">Map Work</span>
    Section VII — Map Based Questions
  </div>
  <p><em>Answer the following map-based questions in text form.</em></p>
  [For each question — convert map exercises to text description questions:]
  <div class="answer-item">
    <p><strong>1.</strong> Name and describe the location of [place/region from chapter].</p>
    <div class="answer-box">
      <textarea placeholder="Write your answer here..." rows="3"></textarea>
    </div>
  </div>
</div>

RULES:
- Base ALL questions strictly on the chapter text below
- Never invent facts not in the text
- MCQ options must have exactly one correct answer
- Fill blanks must have clear, factual answers from the text
- Map Work: convert to text-based location/description questions
- Raw HTML only

Chapter Text:
---
{text}
---"""


def _build_geography_qa_prompt(text: str, metadata: dict) -> str:
    lesson_title = metadata.get("lesson_title", "Unknown")
    class_num    = metadata.get("class", "")
    unit         = metadata.get("unit", "")
    discipline   = metadata.get("discipline", "geography").title()

    return f"""Generate a comprehensive question bank for this Samacheer Kalvi
Social Science — Geography chapter.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | {discipline}

FORMAT:

<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — Geography | Unit {unit}</p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section I — Choose the Correct Answer
  </div>
  <div class="mcq-item">
    <p class="mcq-question"><strong>1.</strong> Question?</p>
    <div class="mcq-options">
      <label><input type="radio" name="g_q1" value="a"> a) Option</label>
      <label><input type="radio" name="g_q1" value="b"> b) Option</label>
      <label><input type="radio" name="g_q1" value="c"> c) Option</label>
      <label><input type="radio" name="g_q1" value="d"> d) Option</label>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section II — Match the Following
  </div>
  <table class="match-table">
    <thead>
      <tr><th>Column A</th><th>Column B</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>1. [Left item]</td>
        <td><input class="blank-input" type="text"
            placeholder="Match..." style="width:180px;"></td>
      </tr>
    </tbody>
  </table>
  <p><em>Column B options: [list all right-side items]</em></p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">2 Marks</span>
    Section III — Give Reasons
  </div>
  [For each question — student explains WHY something happens:]
  <div class="answer-item">
    <p><strong>1.</strong> Give reasons: Why [phenomenon from chapter]? (2 marks)</p>
    <div class="answer-box">
      <textarea placeholder="Write your answer here..." rows="3"></textarea>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">5 Marks</span>
    Section IV — Distinguish Between the Following
  </div>
  [For each question — student compares two concepts:]
  <div class="answer-item">
    <p><strong>1.</strong> Distinguish between [Concept A] and [Concept B]. (5 marks)</p>
    <table class="exercise-table">
      <thead>
        <tr><th>[Concept A]</th><th>[Concept B]</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><textarea placeholder="Write differences..." rows="4"
              style="width:100%;"></textarea></td>
          <td><textarea placeholder="Write differences..." rows="4"
              style="width:100%;"></textarea></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">5 Marks</span>
    Section V — Answer in Brief
  </div>
  <div class="answer-item">
    <p><strong>1.</strong> Question? (5 marks)</p>
    <div class="answer-box long">
      <textarea placeholder="Write your answer here..." rows="5"></textarea>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">8 Marks</span>
    Section VI — Answer in a Paragraph
  </div>
  <div class="answer-item">
    <p><strong>1.</strong> Question? (8 marks)</p>
    <div class="answer-box long">
      <textarea placeholder="Write your detailed paragraph answer here..."
          rows="8"></textarea>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">Map Work</span>
    Section VII — Map Exercises (Text Based)
  </div>
  <p><em>Answer the following map-based questions in text form.</em></p>
  <div class="answer-item">
    <p><strong>1.</strong> Name and locate [geographic feature from chapter]
       on the map of India. Describe its significance.</p>
    <div class="answer-box">
      <textarea placeholder="Write your answer here..." rows="3"></textarea>
    </div>
  </div>
</div>

RULES:
- Base ALL questions strictly on the chapter text
- Give Reasons: ask WHY questions about geographic phenomena
- Distinguish Between: pick two clearly contrasting concepts from the chapter
- Map exercises: convert to text-based description/location questions
- Raw HTML only

Chapter Text:
---
{text}
---"""


def _build_civics_qa_prompt(text: str, metadata: dict) -> str:
    lesson_title = metadata.get("lesson_title", "Unknown")
    class_num    = metadata.get("class", "")
    unit         = metadata.get("unit", "")
    discipline   = metadata.get("discipline", "civics").title()

    return f"""Generate a comprehensive question bank for this Samacheer Kalvi
Social Science — Civics chapter.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | {discipline}

FORMAT:

<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — Civics | Unit {unit}</p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section I — Choose the Correct Answer
  </div>
  <div class="mcq-item">
    <p class="mcq-question"><strong>1.</strong> Question?</p>
    <div class="mcq-options">
      <label><input type="radio" name="c_q1" value="a"> a) Option</label>
      <label><input type="radio" name="c_q1" value="b"> b) Option</label>
      <label><input type="radio" name="c_q1" value="c"> c) Option</label>
      <label><input type="radio" name="c_q1" value="d"> d) Option</label>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section II — Fill in the Blanks
  </div>
  <div class="fill-blank-item">
    <p><strong>1.</strong> [Sentence with] <input class="blank-input" type="text"
       placeholder="______" style="width:160px;"> [rest of sentence].</p>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section III — Match the Following
  </div>
  <table class="match-table">
    <thead>
      <tr><th>Column A</th><th>Column B</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>1. [Left item]</td>
        <td><input class="blank-input" type="text"
            placeholder="Match..." style="width:180px;"></td>
      </tr>
    </tbody>
  </table>
  <p><em>Column B options: [list all right-side items]</em></p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">2 Marks</span>
    Section IV — Give Short Answers
  </div>
  <div class="answer-item">
    <p><strong>1.</strong> Question? (2 marks)</p>
    <div class="answer-box">
      <textarea placeholder="Write your answer here..." rows="3"></textarea>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">8 Marks</span>
    Section V — Answer in Detail
  </div>
  <div class="answer-item">
    <p><strong>1.</strong> Question? (8 marks)</p>
    <div class="answer-box long">
      <textarea placeholder="Write your detailed answer here..." rows="8"></textarea>
    </div>
  </div>
</div>

RULES:
- Base ALL questions strictly on the chapter text
- Civics questions should focus on constitutional provisions,
  government structure, rights, duties, policies
- Never invent facts not in the text
- Raw HTML only

Chapter Text:
---
{text}
---"""


def _build_economics_qa_prompt(text: str, metadata: dict) -> str:
    lesson_title = metadata.get("lesson_title", "Unknown")
    class_num    = metadata.get("class", "")
    unit         = metadata.get("unit", "")
    discipline   = metadata.get("discipline", "economics").title()

    return f"""Generate a comprehensive question bank for this Samacheer Kalvi
Social Science — Economics chapter.

Chapter: {lesson_title} | Class {class_num} | Unit {unit} | {discipline}

FORMAT:

<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | Social Science — Economics | Unit {unit}</p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section I — Choose the Correct Answer
  </div>
  <div class="mcq-item">
    <p class="mcq-question"><strong>1.</strong> Question?</p>
    <div class="mcq-options">
      <label><input type="radio" name="e_q1" value="a"> a) Option</label>
      <label><input type="radio" name="e_q1" value="b"> b) Option</label>
      <label><input type="radio" name="e_q1" value="c"> c) Option</label>
      <label><input type="radio" name="e_q1" value="d"> d) Option</label>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section II — Fill in the Blanks
  </div>
  <div class="fill-blank-item">
    <p><strong>1.</strong> [Sentence with] <input class="blank-input" type="text"
       placeholder="______" style="width:160px;"> [rest of sentence].</p>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">1 Mark</span>
    Section III — Match the Following
  </div>
  <table class="match-table">
    <thead>
      <tr><th>Column A</th><th>Column B</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>1. [Left item]</td>
        <td><input class="blank-input" type="text"
            placeholder="Match..." style="width:180px;"></td>
      </tr>
    </tbody>
  </table>
  <p><em>Column B options: [list all right-side items]</em></p>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">2 Marks</span>
    Section IV — Give Short Answers
  </div>
  <div class="answer-item">
    <p><strong>1.</strong> Question? (2 marks)</p>
    <div class="answer-box">
      <textarea placeholder="Write your answer here..." rows="3"></textarea>
    </div>
  </div>
</div>

<div class="qa-section">
  <div class="qa-section-title">
    <span class="qa-badge">8 Marks</span>
    Section V — Write in Detail
  </div>
  <div class="answer-item">
    <p><strong>1.</strong> Question? (8 marks)</p>
    <div class="answer-box long">
      <textarea placeholder="Write your detailed answer here..." rows="8"></textarea>
    </div>
  </div>
</div>

RULES:
- Base ALL questions strictly on the chapter text
- Economics questions should focus on concepts, definitions,
  data, policies, impacts described in the chapter
- Never invent facts not in the text
- Raw HTML only

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
        Generate Social Science QA HTML for the given chapter.

        Args:
            text:     Clean chapter text from EPUB extractor
            metadata: Dict with class, unit, lesson_title, discipline etc.

        Returns:
            Raw HTML string (body content only), or None on failure.
        """
        discipline   = metadata.get("discipline", "history").lower().strip()
        lesson_title = metadata.get("lesson_title", "Unknown")

        print(f"      [SS QA] Generating {discipline.title()} QA for '{lesson_title}'")

        # Get discipline-specific prompt builder
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

            # Strip any rogue markdown
            raw = re.sub(r'```(?:html)?', '', raw).strip()

            # Strip any rogue style tags
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