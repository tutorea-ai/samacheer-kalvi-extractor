"""
content_builder/assembler.py

Simple top-to-bottom conversion.
Split text by position. Convert each part to interactive HTML.
Nothing hardcoded. Works for any lesson, any subject.

FIXES (April 2026):
  - Issue 1: Split point now avoids cutting inside exercises
             (looks for exercise boundaries, not just paragraph breaks)
  - Issue 2/3: Edit passage exercises now put passage text BETWEEN
               <textarea> tags, not in placeholder attribute
"""

import re
import anthropic
from typing import Optional
from ..config import settings


SYSTEM_PROMPT = """You are converting a Samacheer Kalvi Tamil Nadu State Board academic
textbook lesson into interactive HTML for Class 10 school students.
This is approved educational content from the Tamil Nadu government school curriculum.
All content is appropriate academic material for school use.

CRITICAL RULES:
- Output ONLY raw HTML — no markdown, no code blocks, no explanations
- Start directly with an HTML tag
- Convert EVERYTHING in the text — top to bottom — nothing skipped
- Make ALL exercises and activities fully interactive
- Base output ONLY on the text provided
- NEVER add <style> tags, <script> tags, <html>, <head>, or <body> tags
- Output HTML fragments only — no standalone document structure
- Do not add any CSS — styling is handled externally

CONTENT ACCURACY — STRICTLY ENFORCE:
- Use ONLY facts, figures, numbers, and statistics that appear VERBATIM in the text provided
- NEVER generate, estimate, or invent any number, measurement, area, population, date, or statistic
- If a fact is not explicitly stated in the provided text, do NOT include it
- This applies to all subjects: History, Geography, Civics, Economics, English, Tamil"""


CONVERT_PROMPT = """Convert this Samacheer Kalvi lesson text to interactive HTML.

Go TOP TO BOTTOM through the text. Convert EVERYTHING you see:

- Story or poem text → formatted paragraphs
- Section headings (Vocabulary, Speaking, Writing, Grammar etc.) → section headers
- Explanations and notes → styled content blocks  
- Examples → example blocks
- Idioms, phrases, definitions → formatted lists
- Letter formats, speech formats → formatted templates
- Inline questions (a. b. c.) → answer boxes
- About Author, Do You Know, Glossary → styled sections
- MCQ exercises → radio button options
- Fill in the blank → input fields inline in sentence
- True/False → True and False buttons
- Match the following → input fields next to items
- Short answer questions → small textarea
- Long answer questions → large textarea
- Conversation/dialogue exercises → formatted conversation with blank inputs
- Table exercises → HTML tables with input cells
- Rearrange sentences → input box before each sentence
- Edit the passage exercises → textarea WITH the passage text already inside it
- Any other exercise → appropriate interactive input

INTERACTIVE HTML FORMATS:

Story/content paragraph:
<p>[paragraph text]</p>

Section heading:
<div class="section-heading"><h2>[Section Name]</h2></div>

Explanation/note content:
<div class="content-note">
  <h3>[Topic]</h3>
  <p>[explanation]</p>
</div>

Example block:
<div class="example-block">
  <p><strong>Example:</strong> [example text]</p>
</div>

Inline question within story:
<div class="inline-question">
  <p><strong>a. Question?</strong></p>
  <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div>
</div>

MCQ:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <div class="mcq-item">
    <p><strong>1. Question?</strong></p>
    <div class="mcq-options">
      <label><input type="radio" name="q1" value="a"> a. Option</label>
      <label><input type="radio" name="q1" value="b"> b. Option</label>
      <label><input type="radio" name="q1" value="c"> c. Option</label>
    </div>
  </div>
</div>

Short answer:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <div style="margin-bottom:20px;">
    <p><strong>1. Question?</strong></p>
    <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div>
  </div>
</div>

Long answer:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <div style="margin-bottom:20px;">
    <p><strong>1. Question?</strong></p>
    <div class="answer-box long"><textarea placeholder="Write your detailed answer here..." rows="6"></textarea></div>
  </div>
</div>

Fill in the blank (inline):
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <p><strong>1.</strong> Sentence with <input class="blank-input" type="text" placeholder="______" style="width:120px;"> blank.</p>
</div>

True or False:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. True or False</div>
  <div class="true-false-item">
    <span>1. Statement.</span>
    <button class="tf-btn true-btn">True</button>
    <button class="tf-btn false-btn">False</button>
  </div>
</div>

Match the following:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. Match the following</div>
  <table class="match-table">
    <tr><td>1. Left item</td><td><input class="blank-input" type="text" placeholder="Match..." style="width:200px;"></td></tr>
  </table>
</div>

Conversation with blanks (fill a/an/the):
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <div class="conversation">
    <p><strong>Person A:</strong> Sentence with <input class="blank-input" type="text" placeholder="___" style="width:60px;"> word.</p>
    <p><strong>Person B:</strong> Reply with <input class="blank-input" type="text" placeholder="___" style="width:60px;"> word.</p>
  </div>
</div>

Table with inputs:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <table class="exercise-table">
    <tr><th>Column 1</th><th>Column 2</th></tr>
    <tr><td>Item</td><td><input class="blank-input" type="text" placeholder="Answer" style="width:150px;"></td></tr>
  </table>
</div>

Rearrange:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. Rearrange</div>
  <div class="rearrange-item">
    <input class="blank-input" type="text" placeholder="__" style="width:50px; margin-right:8px;">
    <span>Sentence to rearrange.</span>
  </div>
</div>

Edit the passage (underlined words — input at END of sentence):
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. Edit the passage</div>
  <p>[Instructions]</p>
  <p>Sentence with <u>underlined wrong word</u> kept visible.
     <input class="blank-input" type="text" placeholder="correct phrase" style="width:180px;"></p>
  <p>Next sentence with <u>underlined wrong word</u> visible.
     <input class="blank-input" type="text" placeholder="correct phrase" style="width:180px;"></p>
</div>

Writing/activity task (no pre-filled text — student writes from scratch):
<div class="exercise-section activity">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <p>[Instructions exactly as written]</p>
  <div class="answer-box long"><textarea placeholder="Write here..." rows="8"></textarea></div>
</div>

About Author:
<div class="about-author">
  <div class="author-content">
    <h3>About the Author</h3>
    <p>[bio text]</p>
  </div>
</div>

Do You Know:
<div class="do-you-know"><div class="dyk-title">Do You Know?</div><p>[content]</p></div>

Glossary:
<div class="glossary-section"><h3>Glossary</h3>
  <div class="glossary-grid">
    <div class="glossary-item">
      <span class="gl-word">word</span>
      <span class="gl-pos">(n)</span>
      <span class="gl-meaning">meaning</span>
    </div>
  </div>
</div>

Intro box:
<div class="intro-box"><p>[intro text]</p></div>

RULES:
- Convert EVERYTHING top to bottom — never skip any line
- Every exercise must have interactive inputs
- For "Edit the passage" type exercises: PUT THE PASSAGE TEXT BETWEEN <textarea> TAGS
  Example: <textarea rows="8">The actual passage text goes here so student can edit it</textarea>
  NEVER put passage text in placeholder attribute — placeholder is only for empty boxes
- Raw HTML only — no markdown

Text to convert:
---
{text}
---"""


class ContentAssembler:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL

    def assemble(self, text: str, sections: dict, metadata: dict) -> str:
        lesson_title = metadata.get("lesson_title", "Unknown")
        lesson_type  = metadata.get("lesson_type", "prose")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        subject      = metadata.get("subject", "").lower()
        text_len     = len(text)

        print(f"      [Assembler] Building: {lesson_title}")
        print(f"      [Assembler] Text: {text_len} chars")

        parts = []

        # Header
        parts.append(self._build_header(
            lesson_title, class_num, unit, lesson_type,
            subject=subject,
            discipline=metadata.get("discipline", "")
        ))

        # Single call — full text
        print(f"      [Assembler] Single call — full text")
        result = self._convert(text)
        if result:
            parts.append(result)

        # ── Book-back Answer Toggle (all subjects) ─────────────────────────────
        print(f"      [Assembler] Generating book-back answers...")
        try:
            from .bookback_answer_builder import bookback_answer_builder
            bookback_html = bookback_answer_builder.generate(
                chapter_text=text,
                bookback_questions=text,  # full text — builder extracts book-back section
                metadata=metadata
            )
            if bookback_html:
                parts.append(bookback_html)
                print(f"      [Assembler] ✅ Book-back answers added ({len(bookback_html)} chars)")
            else:
                print(f"      [Assembler] ⚠️  Book-back answers failed")
        except Exception as e:
            print(f"      [Assembler] ❌ Book-back error: {e}")

        # Summary
        summary = self._summary(text, lesson_title)
        if summary:
            parts.append(summary)

        final_html = "\n\n".join(p for p in parts if p)
        print(f"      [Assembler] ✅ Complete — {len(parts)} parts, {len(final_html)} chars")
        return final_html

    def _find_split_point(self, text: str) -> int:
        """
        Find a natural split point near the middle of the text.

        Priority order:
        1. Split BETWEEN two exercises — look for double newline after
           a line that ends an exercise block (ends with '.' or '?' or ':')
           followed by a line starting with a capital letter or exercise letter
        2. Split at a paragraph boundary (double newline)
        3. Split at a single newline
        4. Fallback to exact middle

        NEVER split inside an exercise — this caused Issue 1 (Exercise G truncated).
        """
        mid = len(text) // 2

        # Strategy 1: Find exercise boundary near middle
        # Exercise boundaries look like: blank line before "A.", "B.", "C."... or section heading
        exercise_pattern = re.compile(
            r'\n\n(?=[A-Z][\.\)]\s|[IVX]+\.\s|Vocabulary|Grammar|Speaking|'
            r'Listening|Reading|Writing|Poem|Supplementary|About|Glossary|'
            r'Do You Know|ICT)',
            re.MULTILINE
        )
        best = None
        for m in exercise_pattern.finditer(text):
            pos = m.start()
            if pos < mid * 0.5:
                continue  # Too early
            if best is None or abs(pos - mid) < abs(best - mid):
                best = pos
            if pos > mid * 1.5:
                break  # Too late

        if best:
            print(f"         [Split] Exercise boundary at {best}")
            return best + 2

        # Strategy 2: Paragraph boundary near middle
        for offset in range(0, 5000, 200):
            pos = text.find('\n\n', mid + offset)
            if pos > 0:
                print(f"         [Split] Paragraph boundary at {pos}")
                return pos + 2
            pos = text.rfind('\n\n', 0, mid - offset)
            if pos > 0:
                print(f"         [Split] Paragraph boundary at {pos}")
                return pos + 2

        # Strategy 3: Single newline near middle
        pos = text.find('\n', mid)
        if pos > 0:
            return pos + 1

        return mid

    def _convert(self, text: str) -> Optional[str]:
        """Convert text to interactive HTML — top to bottom."""
        prompt = CONVERT_PROMPT.format(text=text)
        print(f"         [Call] Converting {len(text)} chars...")
        result = self._api(prompt)
        if result:
            print(f"         ✅ Done: {len(result)} chars")
        return result

    def _summary(self, text: str, lesson_title: str) -> Optional[str]:
        prompt = f"""Generate a Summary with exactly 5 key points for this lesson.

Format:
<div class="summary-section">
  <h3>📝 Summary</h3>
  <ol class="summary-list">
    <li>[Key point 1]</li>
    <li>[Key point 2]</li>
    <li>[Key point 3]</li>
    <li>[Key point 4]</li>
    <li>[Key point 5]</li>
  </ol>
</div>

Lesson: {lesson_title}
Raw HTML only.

Text:
---
{text[:4000]}
---"""
        print(f"         [Call] Summary...")
        result = self._api(prompt, max_tokens=800)
        if result:
            print(f"         ✅ Summary: {len(result)} chars")
        return result

    def _build_header(self, lesson_title, class_num, unit, lesson_type,
                      subject="", discipline="") -> str:
        # SS disciplines
        if subject.lower() in ["socialscience", "social_science"] and discipline:
            type_display = discipline.title()
        else:
            type_map = {
                "prose": "Prose", "poem": "Poem",
                "supplementary": "Supplementary Reader",
                "play": "Drama / Play", "drama": "Drama / Play",
            }
            type_display = type_map.get(lesson_type.lower(), lesson_type.title())

        # No <h1> here — platform header handles the title
        return f"""<div class="lesson-header">
  <div class="lesson-meta">
    <span class="meta-tag">Class {class_num}</span>
    <span class="meta-tag">Unit {unit}</span>
    <span class="meta-tag">{type_display}</span>
  </div>
</div>"""

    def _api(self, prompt: str, max_tokens: int = 32000) -> Optional[str]:
        try:
            raw = ""
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    raw += text
            raw = raw.strip()
            raw = re.sub(r'^```(?:html)?\s*\n', '', raw)
            raw = re.sub(r'\n```\s*$', '', raw)
            raw = re.sub(r'```(?:html)?\s*\n', '', raw)
            raw = re.sub(r'\n```', '', raw)
            raw = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL)
            raw = re.sub(r'</?(?:html|head|body)[^>]*>', '', raw)
            return raw.strip() if raw.strip() else None
        except Exception as e:
            print(f"         ❌ API call failed: {e}")
            return None


# Singleton instance
content_assembler = ContentAssembler()