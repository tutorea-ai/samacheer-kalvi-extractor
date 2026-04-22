"""
content_builder/assembler.py

Simple top-to-bottom conversion.
Split text by position. Convert each part to interactive HTML.
Nothing hardcoded. Works for any lesson, any subject.
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
- Base output ONLY on the text provided"""


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

Writing/activity task:
<div class="exercise-section activity">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <p>[Instructions exactly as written]</p>
  <div class="answer-box long"><textarea placeholder="Write here..." rows="8"></textarea></div>
</div>

About Author:
<div class="about-author"><h3>About the Author</h3><p>[bio]</p></div>

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
        text_len     = len(text)

        print(f"      [Assembler] Building: {lesson_title}")
        print(f"      [Assembler] Text: {text_len} chars")

        parts = []

        # Header
        parts.append(self._build_header(lesson_title, class_num, unit, lesson_type))

        # Split text and convert each part
        if text_len < 15000:
            # Short — 1 call
            print(f"      [Assembler] Short → 1 call")
            result = self._convert(text)
            if result:
                parts.append(result)
        else:
            # Long — split at natural boundary near middle
            mid = self._find_split_point(text)
            part1_text = text[:mid]
            part2_text = text[mid:]
            print(f"      [Assembler] Long → 2 calls (split at {mid})")

            result1 = self._convert(part1_text)
            result2 = self._convert(part2_text)
            if result1: parts.append(result1)
            if result2: parts.append(result2)

        # Summary
        summary = self._summary(text, lesson_title)
        if summary:
            parts.append(summary)

        final_html = "\n\n".join(p for p in parts if p)
        print(f"      [Assembler] ✅ Complete — {len(parts)} parts, {len(final_html)} chars")
        return final_html

    def _find_split_point(self, text: str) -> int:
        """Find a natural split point near the middle of the text.
        Split at a paragraph boundary — never in the middle of a sentence."""
        mid = len(text) // 2
        # Look for paragraph break near middle
        for offset in range(0, 3000, 100):
            # Try after middle
            pos = text.find('\n\n', mid + offset)
            if pos > 0:
                return pos + 2
            # Try before middle
            pos = text.rfind('\n\n', 0, mid - offset)
            if pos > 0:
                return pos + 2
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

    def _build_header(self, lesson_title, class_num, unit, lesson_type) -> str:
        type_map = {
            "prose": "Prose", "poem": "Poem",
            "supplementary": "Supplementary Reader",
            "play": "Drama / Play", "drama": "Drama / Play",
        }
        type_display = type_map.get(lesson_type.lower(), "Prose")
        return f"""<div class="lesson-header">
  <div class="lesson-meta">
    <span class="meta-tag">Class {class_num}</span>
    <span class="meta-tag">Unit {unit}</span>
    <span class="meta-tag">{type_display}</span>
  </div>
  <h1 class="lesson-main-title">{lesson_title}</h1>
</div>"""

    def _api(self, prompt: str, max_tokens: int = 16000) -> Optional[str]:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            raw = re.sub(r'^```(?:html)?\s*\n', '', raw)
            raw = re.sub(r'\n```\s*$', '', raw)
            raw = re.sub(r'```(?:html)?\s*\n', '', raw)
            raw = re.sub(r'\n```', '', raw)
            return raw.strip() if raw.strip() else None
        except Exception as e:
            print(f"         ❌ API call failed: {e}")
            return None


# Singleton instance
content_assembler = ContentAssembler()