"""
content_builder/extractor.py

One method per section. One Claude call per method.
Story text uses split logic for long lessons (25000+ chars).
All other extractors receive pre-split focused zones from assembler.
"""

import re
import anthropic
from typing import Optional
from ..config import settings


EXTRACTOR_SYSTEM_PROMPT = """You are an experienced English teacher formatting Tamil Nadu Samacheer Kalvi textbook content into clean HTML.

CRITICAL RULES — NEVER BREAK:
- Output ONLY the HTML for the specific section asked
- NEVER add any other section
- NEVER wrap output in markdown code blocks
- NEVER use backticks
- Start directly with the HTML tag — no preamble text
- If the requested content does not exist in the text, return exactly: SECTION_NOT_FOUND"""


class ContentExtractor:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL

    def _call(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Single Claude API call. Returns None on failure."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=EXTRACTOR_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text.strip()
            result = re.sub(r'^```(?:html)?\s*\n', '', result)
            result = re.sub(r'\n```\s*$', '', result)
            result = result.strip()
            if result == "SECTION_NOT_FOUND":
                return None
            return result
        except Exception as e:
            print(f"      ❌ Extractor call failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────────────────────
    # HEADER — no Claude call
    # ──────────────────────────────────────────────────────────────────────────

    def extract_header(self, lesson_title: str, class_num: int,
                       subject: str, unit: int) -> str:
        return f"""<div class="sk-content-header">
  <h1>{lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | {subject.title()} | Unit {unit}</p>
</div>"""

    # ──────────────────────────────────────────────────────────────────────────
    # ABOUT THE AUTHOR / POET
    # ──────────────────────────────────────────────────────────────────────────

    def extract_about_author(self, text: str, is_poet: bool = False) -> Optional[str]:
        label = "About the Poet" if is_poet else "About the Author"
        icon  = "🎭" if is_poet else "✍️"
        prompt = f"""From the text below, extract ONLY the {label} section.

Format as:
<div class="about-author">
  <div class="author-icon">{icon}</div>
  <div>
    <div class="author-title">{label}</div>
    <div class="author-name">[Full name]</div>
    <p>[Birth-Death years if available]</p>
    <p>[Background, nationality, profession]</p>
    <p>[Notable works and achievements]</p>
    <p>[Connection to this lesson]</p>
  </div>
</div>

RULES:
- Include ONLY author/poet information
- Do NOT include glossary words or lesson content
- Do NOT include Do You Know content
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=2000)
        if result:
            print(f"      ✅ Extractor: {label} extracted")
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # STORY TEXT — with split logic for long lessons
    # ──────────────────────────────────────────────────────────────────────────

    def extract_story_text(self, text: str, lesson_type: str = "prose",
                           lesson_title: str = "") -> Optional[str]:
        """
        Extracts story/poem/play text.
        Uses 1, 2, or 3 calls based on text length.

        < 12000 chars  → 1 call
        < 22000 chars  → 2 calls
        >= 22000 chars → 3 calls
        """
        text_len = len(text)

        if text_len < 12000:
            print(f"      [Story] Short ({text_len} chars) → 1 call")
            return self._story_call(text, lesson_type, is_continuation=False)

        elif text_len < 22000:
            print(f"      [Story] Medium ({text_len} chars) → 2 calls")
            split1 = self._find_split(text, 0.5)
            part1  = self._story_call(text[:split1], lesson_type, is_continuation=False)
            part2  = self._story_call(text[split1:], lesson_type, is_continuation=True)
            return self._join_parts([part1, part2])

        else:
            print(f"      [Story] Long ({text_len} chars) → 3 calls")
            split1 = self._find_split(text, 0.33)
            split2 = self._find_split(text, 0.66)
            part1  = self._story_call(text[:split1],        lesson_type, is_continuation=False)
            part2  = self._story_call(text[split1:split2],  lesson_type, is_continuation=True)
            part3  = self._story_call(text[split2:],        lesson_type, is_continuation=True)
            return self._join_parts([part1, part2, part3])

    def _find_split(self, text: str, ratio: float) -> int:
        """Find nearest paragraph boundary to the ratio point."""
        target = int(len(text) * ratio)
        # Try paragraph break first
        split = text.find('\n\n', target)
        if split == -1:
            split = text.find('\n', target)
        if split == -1:
            split = target
        return split

    def _join_parts(self, parts: list) -> Optional[str]:
        """Join non-None parts into single HTML string."""
        valid = [p for p in parts if p]
        if not valid:
            return None
        return "\n\n".join(valid)

    def _story_call(self, text: str, lesson_type: str,
                    is_continuation: bool) -> Optional[str]:
        """Single story extraction call."""

        if lesson_type == "poem":
            format_instructions = """Format the poem as:
<h2>The Poem</h2>
<div class="poem-container">
  <div class="poem-stanza">
    <span class="poem-line">Line one</span>
    <span class="poem-line">Line two</span>
    <span class="poem-line">Line three</span>
    <span class="poem-line">Line four</span>
  </div>
  [repeat for each stanza]
</div>

For inline questions (a. b. c.) within poem:
<div class="inline-question">
  <p><strong>a. Question?</strong></p>
  <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div>
</div>"""

        elif lesson_type in ("play", "drama"):
            format_instructions = """Format as dialogue blocks:
<h2>[Scene Title]</h2>
<div class="dialogue-block">
  <div class="speaker">Character Name</div>
  <p class="speech">Speech text.</p>
</div>
For stage directions:
<p class="stage-direction"><em>[Direction]</em></p>"""

        else:
            format_instructions = """Format as:
<h2>[Lesson Title or first heading]</h2>
<p>[paragraph]</p>
<p>[paragraph]</p>

For dialogue within story:
<div class="dialogue-block">
  <div class="speaker">Speaker Name</div>
  <p class="speech">Speech text.</p>
</div>

For inline questions (a. b. c.):
<div class="inline-question">
  <p><strong>a. Question?</strong></p>
  <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div>
</div>"""

        if is_continuation:
            task = """This is a CONTINUATION of the story already started.
DO NOT add any title, heading, or <h2> at the start.
DO NOT add a summary box.
Continue directly from where the story left off.
Output ONLY the story paragraphs and dialogue."""
        else:
            task = """Extract and format the main story/poem/play content.
Include ALL paragraphs and dialogue — never skip any.
Do NOT include: About Author, Glossary, Exercises, Do You Know, ICT Corner."""

        prompt = f"""{task}

{format_instructions}

RULES:
- Keep ALL original content — never summarize or skip
- Stop before exercises or glossary begin
- Raw HTML only — no markdown code blocks

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=16000)
        if result:
            print(f"         ✅ Story part extracted ({len(result)} chars)")
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # DO YOU KNOW
    # ──────────────────────────────────────────────────────────────────────────

    def extract_do_you_know(self, text: str) -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the Do You Know section.

Format as:
<div class="do-you-know">
  <div class="dyk-title">Do You Know?</div>
  <p>[Content from the Do You Know box]</p>
</div>

RULES:
- Only include Do You Know content
- Do NOT include About Author or any other section
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=1000)
        if result:
            print(f"      ✅ Extractor: Do You Know extracted")
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # GLOSSARY
    # ──────────────────────────────────────────────────────────────────────────

    def extract_glossary(self, text: str) -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the glossary / word meanings.

Format as:
<div class="glossary-section">
  <h3>Glossary</h3>
  <div class="glossary-grid">
    <div class="glossary-card">
      <div class="word">word</div>
      <span class="word-type">(n)</span>
      <div class="word-meaning">meaning from text</div>
    </div>
    [repeat for every word]
  </div>
</div>

Word types: (n) noun, (v) verb, (adj.) adjective, (adv.) adverb

RULES:
- Include EVERY word in the glossary
- Use exact meanings from text
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=3000)
        if result:
            print(f"      ✅ Extractor: Glossary extracted")
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # EXERCISES
    # ──────────────────────────────────────────────────────────────────────────

    def extract_exercise_mcq(self, text: str, exercise_label: str = "") -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the Multiple Choice exercise.

Format EXACTLY as:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <div class="mcq-item">
    <div class="mcq-question">1. Question?</div>
    <div class="mcq-options">
      <label class="mcq-option"><input type="radio" name="mcq_1" /><span class="option-letter">a.</span> Option A</label>
      <label class="mcq-option"><input type="radio" name="mcq_1" /><span class="option-letter">b.</span> Option B</label>
      <label class="mcq-option"><input type="radio" name="mcq_1" /><span class="option-letter">c.</span> Option C</label>
      <label class="mcq-option"><input type="radio" name="mcq_1" /><span class="option-letter">d.</span> Option D</label>
    </div>
  </div>
  [repeat for every question]
</div>

RULES:
- Include EVERY question
- Unique name per question: name="mcq_1", name="mcq_2" etc.
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=3000)
        if result:
            print(f"      ✅ Extractor: MCQ extracted")
        return result

    def extract_exercise_fill_blank(self, text: str, exercise_label: str = "") -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the Fill in the Blanks exercise.

Format EXACTLY as:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. [Title]</div>
  <div class="help-box"><span class="help-box-label">Word Bank:</span> word1 | word2 | word3</div>
  <div class="fill-blank-sentence">1. Sentence with <input class="blank-input" type="text" placeholder="______" /> here.</div>
  [repeat for every sentence]
</div>

RULES:
- Every item its own <div class="fill-blank-sentence">
- ALWAYS use <input class="blank-input"> — NEVER underscores
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=3000)
        if result:
            print(f"      ✅ Extractor: Fill in Blanks extracted")
        return result

    def extract_exercise_true_false(self, text: str, exercise_label: str = "") -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the True or False exercise.

Format EXACTLY as:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. True or False</div>
  <div class="true-false-item">
    <span class="tf-number">1.</span>
    <span class="tf-statement">Statement.</span>
    <div class="tf-options">
      <button class="tf-btn true-btn">True</button>
      <button class="tf-btn false-btn">False</button>
    </div>
  </div>
  [repeat for every statement]
</div>

RULES:
- Include EVERY statement
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=2000)
        if result:
            print(f"      ✅ Extractor: True/False extracted")
        return result

    def extract_exercise_identify_speaker(self, text: str, exercise_label: str = "") -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the Identify the Speaker exercise.

Format EXACTLY as:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. Identify the Speaker</div>
  <div style="margin-bottom:16px;">
    <p><strong>1. "[Quote from text]"</strong></p>
    <p>Speaker: <input class="blank-input" type="text" placeholder="Write the speaker's name" style="width:220px;" /></p>
  </div>
  [repeat for every quote]
</div>

RULES:
- Include EVERY quote
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=2000)
        if result:
            print(f"      ✅ Extractor: Identify Speaker extracted")
        return result

    def extract_exercise_short_answer(self, text: str, exercise_label: str = "") -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the Short Answer exercise (1-2 sentences).

Format EXACTLY as:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. Answer in one or two sentences</div>
  <div style="margin-bottom:20px;">
    <p><strong>1. Question?</strong></p>
    <div class="answer-box"><textarea placeholder="Write your answer here..."></textarea></div>
  </div>
  [repeat for every question]
</div>

RULES:
- Include EVERY question
- Do NOT include Long Answer questions
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=3000)
        if result:
            print(f"      ✅ Extractor: Short Answer extracted")
        return result

    def extract_exercise_long_answer(self, text: str, exercise_label: str = "") -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the Long Answer / Paragraph exercise.

Format EXACTLY as:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. Answer in a paragraph (100-150 words)</div>
  <div style="margin-bottom:20px;">
    <p><strong>1. Question?</strong></p>
    <div class="answer-box long"><textarea placeholder="Write your detailed answer here..."></textarea></div>
  </div>
  [repeat for every question]
</div>

RULES:
- Include EVERY question
- Do NOT include Short Answer questions
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=2000)
        if result:
            print(f"      ✅ Extractor: Long Answer extracted")
        return result

    def extract_exercise_rearrange(self, text: str, exercise_label: str = "") -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the Rearrange the Sentences exercise.

Format EXACTLY as:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. Rearrange in correct order</div>
  <div class="rearrange-item">
    <input class="blank-input" type="text" placeholder="__" style="width:50px; margin-right:8px;" />
    <span>First sentence.</span>
  </div>
  <div class="rearrange-item">
    <input class="blank-input" type="text" placeholder="__" style="width:50px; margin-right:8px;" />
    <span>Second sentence.</span>
  </div>
  [repeat for every sentence]
</div>

⚠️ CRITICAL:
- EVERY sentence MUST have <input class="blank-input"> BEFORE the <span>
- NEVER use dashes before sentences
- Every sentence in its own <div class="rearrange-item">
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=2000)
        if result:
            print(f"      ✅ Extractor: Rearrange extracted")
        return result

    def extract_exercise_match(self, text: str, exercise_label: str = "") -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the Match the Following exercise.

Format EXACTLY as:
<div class="exercise-section">
  <div class="exercise-title"><span class="ex-badge">Exercise</span> [Letter]. Match the Following</div>
  <table class="match-table">
    <thead>
      <tr><th>Column A</th><th>Column B</th><th>Answer</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>1. Item</td>
        <td>a. Match</td>
        <td><input class="match-input" type="text" placeholder="__" /></td>
      </tr>
      [repeat for every pair]
    </tbody>
  </table>
</div>

RULES:
- Include EVERY pair
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=2000)
        if result:
            print(f"      ✅ Extractor: Match extracted")
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # ICT CORNER
    # ──────────────────────────────────────────────────────────────────────────

    def extract_ict_corner(self, text: str) -> Optional[str]:
        prompt = f"""From the text below, extract ONLY the ICT Corner section.

Format as:
<div class="ict-corner">
  <div class="ict-title">🖥️ ICT Corner</div>
  <p>[ICT Corner content]</p>
  <ol>
    <li>[Step 1 if exists]</li>
    <li>[Step 2 if exists]</li>
  </ol>
  <p><a href="[URL]" target="_blank">Click here to access</a></p>
</div>

RULES:
- Include URL link if present
- If not found, return SECTION_NOT_FOUND

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=1000)
        if result:
            print(f"      ✅ Extractor: ICT Corner extracted")
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────────────────

    def extract_summary(self, text: str, lesson_title: str = "") -> str:
        prompt = f"""Based on the lesson text below, generate a Summary section with exactly 5 key points.

Format as:
<div class="summary-box">
  <div class="summary-title">📋 Summary</div>
  <ul>
    <li>[Key point 1 — one clear sentence]</li>
    <li>[Key point 2 — one clear sentence]</li>
    <li>[Key point 3 — one clear sentence]</li>
    <li>[Key point 4 — one clear sentence]</li>
    <li>[Key point 5 — one clear sentence]</li>
  </ul>
</div>

RULES:
- Exactly 5 points
- Each point one clear sentence
- Simple English for Class 10 students
- Cover the most important events or ideas

Text:
---
{text}
---"""
        result = self._call(prompt, max_tokens=1000)
        if result:
            print(f"      ✅ Extractor: Summary generated")
            return result

        # Fallback
        return f"""<div class="summary-box">
  <div class="summary-title">📋 Summary</div>
  <ul>
    <li>This lesson is an important literary extract from the textbook.</li>
    <li>The story involves key characters and significant events.</li>
    <li>Important themes and values are explored throughout.</li>
    <li>Students develop vocabulary and language skills.</li>
    <li>The lesson builds reading and comprehension abilities.</li>
  </ul>
</div>"""


# Singleton instance
content_extractor = ContentExtractor()