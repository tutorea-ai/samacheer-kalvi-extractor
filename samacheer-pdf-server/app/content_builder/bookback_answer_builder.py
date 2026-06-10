"""
bookback_answer_builder.py
--------------------------
Generates model answers for Samacheer Kalvi book-back exercises.
Answers are strictly generated from the extracted chapter text — not outside knowledge.

How it works:
  1. Receives the extracted book-back questions (from EPUB extractor)
  2. Receives the full chapter text
  3. Makes ONE API call — generates answers for all book-back questions
  4. Returns HTML with "Show Answer" toggle for each question
  5. This HTML is injected into the existing content HTML

The toggle works with pure JS — no backend call needed.
Student attempts question first → clicks "Show Answer" → answer revealed.

Used by:
  Content builder — injected after each book-back question block
"""

import re
import anthropic
from typing import Optional
from app.config import settings


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

BOOKBACK_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi teacher
generating model answers for book-back exercise questions.

CRITICAL RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags
- Generate answers STRICTLY from the chapter text provided
- NEVER use outside knowledge or general facts
- NEVER invent content not present in the chapter text
- Every answer must be traceable to the chapter text
- Keep answers concise and exam-appropriate"""


# ============================================================================
# SHOW/HIDE TOGGLE STYLE
# injected once at the top of the book-back section
# ============================================================================

TOGGLE_STYLE = """
<script>
function toggleAnswer(btn) {
  const reveal = btn.nextElementSibling;
  const isVisible = reveal.style.display === 'block';
  reveal.style.display = isVisible ? 'none' : 'block';
  btn.textContent = isVisible ? 'Show Answer' : 'Hide Answer';
  btn.classList.toggle('active', !isVisible);
}
function showAllAnswers() {
  document.querySelectorAll('.answer-reveal').forEach(el => el.style.display = 'block');
  document.querySelectorAll('.show-answer-btn').forEach(btn => {
    btn.textContent = 'Hide Answer';
    btn.classList.add('active');
  });
}
function hideAllAnswers() {
  document.querySelectorAll('.answer-reveal').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.show-answer-btn').forEach(btn => {
    btn.textContent = 'Show Answer';
    btn.classList.remove('active');
  });
}
</script>
<style>
.show-answer-btn {
  background: #006B6B;
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  margin-top: 8px;
  transition: background 0.2s;
}
.show-answer-btn:hover { background: #005555; }
.show-answer-btn.active { background: #B8860B; }
.answer-reveal {
  display: none;
  background: #f0f8f0;
  border-left: 4px solid #006B6B;
  padding: 10px 14px;
  margin-top: 8px;
  border-radius: 0 4px 4px 0;
}
.answer-reveal p { margin: 4px 0; font-size: 14px; }
.answer-reveal strong { color: #006B6B; }
.bookback-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.bookback-controls button {
  background: #f0f0f0;
  border: 1px solid #ccc;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}
.bookback-controls button:hover { background: #e0e0e0; }
.bookback-section-heading {
  margin: 24px 0 12px 0;
  padding-bottom: 6px;
  border-bottom: 2px solid #006B6B;
}
.bookback-section-heading h3 {
  color: #006B6B;
  font-size: 1rem;
  margin: 0;
  font-weight: 700;
}
</style>
"""


# ============================================================================
# BOOKBACK ANSWER BUILDER CLASS
# ============================================================================

class BookbackAnswerBuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL
        print(f"✅ Bookback Answer Builder initialized — model: {self.model}")

    def generate(self, chapter_text: str, bookback_questions: str,
                 metadata: dict) -> Optional[str]:
        """
        Generate model answers for all book-back questions.
        Returns HTML with Show/Hide toggle for each answer.

        Args:
            chapter_text:       Full extracted chapter text from EPUB
            bookback_questions: Extracted book-back questions from EPUB
                                (raw text or HTML of the questions section)
            metadata:           Dict with lesson_title, class, unit, discipline

        Returns:
            HTML string with questions + Show Answer toggles, or None on failure.
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        discipline   = metadata.get("discipline", "").title()

        print(f"      [Bookback] Generating answers: {lesson_title}")

        try:
            prompt = f"""Generate model answers for ALL book-back exercise questions
from this Samacheer Kalvi chapter.

Chapter  : {lesson_title}
Class    : {class_num}
Unit     : {unit}
Subject  : Social Science — {discipline}

CRITICAL SOURCE RULE:
- Answers MUST come STRICTLY from the chapter text provided below
- Do NOT use any outside knowledge
- Do NOT use general historical facts not mentioned in the chapter
- Every answer must be directly supported by the chapter text
- If a question cannot be answered from the chapter text alone,
  say: "Refer to the chapter text for this answer."

ANSWER LENGTH RULES:
- 1-mark (MCQ / Fill blank / Match): One word, phrase, or one sentence max
- 2-mark (Brief answer): 2-3 sentences, 30-50 words
- 5-mark (Detail answer): 5-6 sentences, 80-120 words

OUTPUT FORMAT:
For each question, generate this exact HTML structure:

<div class="bookback-qa-item">
  <p class="bookback-question"><strong>[Question number].</strong> [Question text exactly as given]</p>
  <button class="show-answer-btn" onclick="toggleAnswer(this)">Show Answer</button>
  <div class="answer-reveal">
    <p><strong>Answer:</strong> [Model answer strictly from chapter text]</p>
  </div>
</div>

For MCQ questions, also show which option is correct:
<div class="bookback-qa-item">
  <p class="bookback-question"><strong>1.</strong> [MCQ question]</p>
  <div class="mcq-options-display">
    <span>a) [option]</span>
    <span>b) [option]</span>
    <span>c) [option]</span>
    <span>d) [option]</span>
  </div>
  <button class="show-answer-btn" onclick="toggleAnswer(this)">Show Answer</button>
  <div class="answer-reveal">
    <p><strong>Answer:</strong> [correct option letter]) [correct option text]</p>
    <p><strong>Explanation:</strong> [1-2 sentences from chapter text explaining why]</p>
  </div>
</div>

For Match the Following:
<div class="bookback-qa-item">
  <p class="bookback-question"><strong>[N].</strong> Match the Following</p>
  <table class="match-table">
    [Column A and Column B as given in questions]
  </table>
  <button class="show-answer-btn" onclick="toggleAnswer(this)">Show Answer</button>
  <div class="answer-reveal">
    <p><strong>Answers:</strong> 1-[x], 2-[x], 3-[x], 4-[x], 5-[x]</p>
  </div>
</div>

WRAPPER (include this at the start):
<div class="bookback-answers-section">
  <h2>Book-back Exercises — Questions & Answers</h2>
  <p class="section-note"><em>Answers generated strictly from the Samacheer Kalvi textbook content.
  Attempt each question first, then click "Show Answer" to check.</em></p>

  <div class="bookback-controls">
    <button onclick="showAllAnswers()">Show All Answers</button>
    <button onclick="hideAllAnswers()">Hide All Answers</button>
  </div>

  [All question blocks here — grouped by section with headings]

</div>

SECTION HEADING FORMAT — CRITICAL:
Before each group of questions, add the section heading exactly as it appears
in the book-back section. Use this format:

<div class="bookback-section-heading">
  <h3>I. Choose the Correct Answer</h3>
</div>
[MCQ questions here]

<div class="bookback-section-heading">
  <h3>II. Fill in the Blanks</h3>
</div>
[Fill blank questions here]

<div class="bookback-section-heading">
  <h3>III. Match the Following</h3>
</div>
[Match questions here]

<div class="bookback-section-heading">
  <h3>IV. Answer Briefly</h3>
</div>
[2-mark questions here]

<div class="bookback-section-heading">
  <h3>V. Answer in Detail</h3>
</div>
[5-mark questions here]

IMPORTANT:
- Use the EXACT section heading text from the book-back — do not rename
- If the book-back uses Roman numerals (I, II, III) keep them
- If it uses letters (A, B, C) keep them
- Every section MUST have its heading before the questions
- Never mix questions from different sections under the same heading

RULES:
- Raw HTML only — no markdown, no code fences
- Process EVERY question in the book-back section
- Keep question text exactly as extracted — do not paraphrase questions
- Answers strictly from chapter text only
- Do NOT add any questions not present in the book-back section

INSTRUCTION:
First identify the book-back exercise section from the chapter text below.
Book-back sections typically start with:
"I. Choose the correct answer" or "Section I" or "Exercise" or "Answer the following"
Extract ALL questions from the book-back section and generate model answers for each.

Chapter Text:
---
{chapter_text}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                system=BOOKBACK_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:html)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            raw = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL)

            if not raw:
                print(f"      [Bookback] ❌ Empty response")
                return None

            # Inject toggle styles at the top
            final_html = TOGGLE_STYLE + "\n\n" + raw
            print(f"      [Bookback] ✅ Done — {len(final_html)} chars")
            return final_html

        except Exception as e:
            print(f"      [Bookback] ❌ Error: {e}")
            return None


# ============================================================================
# Singleton instance
# ============================================================================

bookback_answer_builder = BookbackAnswerBuilder()