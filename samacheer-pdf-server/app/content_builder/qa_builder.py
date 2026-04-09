"""
content_builder/qa_builder.py

Generates QA in 4 focused calls — one per mark category.

Fix: Added explicit word count and sentence count per mark type
     so 5-mark and 8-mark answers are clearly different lengths.
"""

import anthropic
import re
from typing import Optional, Dict
from ..config import settings


QA_SYSTEM_PROMPT = """You are an experienced English teacher creating exam-ready question banks for Tamil Nadu Samacheer Kalvi State Board students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Base ALL questions on the lesson text provided
- NEVER invent content not present in the text"""


class QABuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL

    def generate(self, text: str, metadata: Dict) -> Optional[str]:
        """
        Generates complete QA HTML using 4 focused calls.
        One call per mark category.
        """
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        lesson_type  = metadata.get("lesson_type", "prose")

        type_display_map = {
            "prose":         "Prose",
            "poem":          "Poem",
            "supplementary": "Supplementary Reader",
            "play":          "Drama or Play",
            "drama":         "Drama or Play",
        }
        type_display = type_display_map.get(lesson_type.lower(), "Prose")
        has_grammar  = lesson_type.lower() == "prose"

        print(f"      [QA] 4-call approach: 1-mark, 2-mark, 5-mark, 8-mark")

        parts = []

        # Call 1: 1-mark
        print(f"      [QA] Call 1/4: 1-mark questions (Q1-Q25)...")
        part1 = self._call_by_marks(
            text=text, lesson_title=lesson_title,
            class_num=class_num, unit=unit,
            type_display=type_display, has_grammar=has_grammar,
            mark_type=1, q_start=1, q_end=25, include_header=True
        )
        if part1:
            parts.append(self._clean(part1))
            print(f"         ✅ 1-mark done ({len(part1)} chars)")
        else:
            print(f"         ❌ 1-mark failed")

        # Call 2: 2-mark
        print(f"      [QA] Call 2/4: 2-mark questions (Q26-Q50)...")
        part2 = self._call_by_marks(
            text=text, lesson_title=lesson_title,
            class_num=class_num, unit=unit,
            type_display=type_display, has_grammar=has_grammar,
            mark_type=2, q_start=26, q_end=50, include_header=False
        )
        if part2:
            parts.append(self._clean(part2))
            print(f"         ✅ 2-mark done ({len(part2)} chars)")
        else:
            print(f"         ❌ 2-mark failed")

        # Call 3: 5-mark
        print(f"      [QA] Call 3/4: 5-mark questions (Q51-Q75)...")
        part3 = self._call_by_marks(
            text=text, lesson_title=lesson_title,
            class_num=class_num, unit=unit,
            type_display=type_display, has_grammar=has_grammar,
            mark_type=5, q_start=51, q_end=75, include_header=False
        )
        if part3:
            parts.append(self._clean(part3))
            print(f"         ✅ 5-mark done ({len(part3)} chars)")
        else:
            print(f"         ❌ 5-mark failed")

        # Call 4: 8-mark
        print(f"      [QA] Call 4/4: 8-mark questions (Q76-Q100)...")
        part4 = self._call_by_marks(
            text=text, lesson_title=lesson_title,
            class_num=class_num, unit=unit,
            type_display=type_display, has_grammar=has_grammar,
            mark_type=8, q_start=76, q_end=100, include_header=False
        )
        if part4:
            parts.append(self._clean(part4))
            print(f"         ✅ 8-mark done ({len(part4)} chars)")
        else:
            print(f"         ❌ 8-mark failed")

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [QA] ✅ Complete — {len(parts)} parts, {len(combined)} chars total")
        return combined

    def _call_by_marks(
        self, text, lesson_title, class_num, unit,
        type_display, has_grammar, mark_type,
        q_start, q_end, include_header
    ) -> Optional[str]:
        try:
            count = q_end - q_start + 1

            header_html = ""
            if include_header:
                header_html = f"""<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | English | Unit {unit} | {type_display}</p>
</div>"""

            # ── Mark guidance with EXPLICIT answer length ─────────────────────
            mark_guidance = {
                1: f"""Generate EXACTLY {count} one-mark questions (Q{q_start} to Q{q_end}).

ANSWER LENGTH: Maximum 1 complete sentence per answer. 10-15 words only.

Question types — distribute evenly across ALL of these:
- Fill in the blank (one word or short phrase answer)
- Choose the correct answer (state all 4 options in the question)
- True or False (state the fact clearly)
- One-word answer
- One-sentence answer
- Who said this / who is being described

Example format:
Q1. ______ was the chief of all spirits in the island.
Answer: Ariel was the chief of all spirits in the island.

Q2. Who released the spirits from the witch Sycorax?
Answer: Prospero released the spirits from the witch Sycorax.""",

                2: f"""Generate EXACTLY {count} two-mark questions (Q{q_start} to Q{q_end}).

ANSWER LENGTH: Exactly 2-3 complete sentences per answer. 30-50 words only.
Do NOT write more than 3 sentences. Do NOT write less than 2 sentences.

Question types — distribute evenly across ALL of these:
- Short answer (2-3 sentences explaining an event or character)
- Explain a line or phrase from the text in your own words
- Find the figure of speech or literary device and explain it
- Vocabulary — give synonym, antonym, or meaning in context
- Reference to context — who said it and what does it mean briefly

Example format:
Q26. Who was Caliban and what was his role on the island?
Answer: Caliban was the son of the witch Sycorax. He was employed
like a slave to fetch wood and do laborious work for Prospero.""",

                5: f"""Generate EXACTLY {count} five-mark questions (Q{q_start} to Q{q_end}).

ANSWER LENGTH: Exactly 5-7 complete sentences per answer. 80-120 words.
This is a paragraph answer — more detailed than 2-mark but shorter than 8-mark.
Do NOT write more than 7 sentences. Do NOT write less than 5 sentences.

Question types — distribute evenly across ALL of these:
- Paragraph answer describing a character or event in detail
- Explain the central idea or main theme of the lesson
- Compare and contrast two characters or situations from the text
- Explain the significance of a key event in the story
- Value-based question — what lesson or moral does the text teach
- Retell a specific important scene from the story

Example format:
Q51. Write a paragraph about Prospero's character.
Answer: Prospero was a wise and powerful man who had once been
the Duke of Milan. He possessed magical powers that allowed him
to control the winds and the sea. Using his spirits, especially
Ariel, he managed everything on the island. Despite being wronged
by his brother Antonio, he chose forgiveness over revenge. His love
for his daughter Miranda was the driving force behind all his actions.""",

                8: f"""Generate EXACTLY {count} eight-mark questions (Q{q_start} to Q{q_end}).

ANSWER LENGTH: Exactly 10-14 complete sentences per answer. 180-250 words.
This is a detailed essay answer — significantly longer than 5-mark.
Do NOT write less than 10 sentences. Do NOT write less than 180 words.
Every answer must be a proper essay with introduction, body, and conclusion.

Question types — distribute evenly across ALL of these:
- Essay — detailed explanation of the full lesson or a major theme
- Character sketch — comprehensive description of a main character
  with specific examples and quotes from the text
- Summary — complete retelling of the entire lesson in own words
- Creative writing — write a letter, diary entry, or continuation
  of the story with proper detail
- Critical appreciation — analyse the style, theme, and message
  of the lesson in detail
{"- Grammar essay — write a detailed paragraph using specific grammar structures" if has_grammar else ""}

Example format:
Q76. Write a detailed character sketch of Prospero.
Answer: Prospero is the central character of this extract from
Shakespeare's famous play The Tempest. He is portrayed as a man
of great wisdom and extraordinary magical powers. Before coming
to the island, he had been the rightful Duke of Milan, a position
of great power and responsibility. His treacherous brother Antonio,
with the help of the King of Naples, had wrongfully deprived him
of his title and exiled him to the sea...
[continues for 10-14 sentences total]""",
            }

            grammar_note = ""
            if has_grammar and mark_type in (1, 2):
                grammar_note = f"\nAlso include {max(count // 5, 2)} grammar questions from the lesson's grammar section."

            prompt = f"""Generate ONLY {mark_type}-mark questions for this question bank.
Do NOT generate any other mark type.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}

{mark_guidance[mark_type]}
{grammar_note}

HTML FORMAT:
{header_html}
<h2>{mark_type}-Mark Questions</h2>
<div class="marks-badge">{mark_type} Mark{"s" if mark_type > 1 else ""}</div>

Each question MUST follow this EXACT format:
<div class="qa-item">
  <p class="question"><strong>Q[N]. Question text here?</strong></p>
  <p class="answer"><strong>Answer:</strong> Complete answer here following the length requirement above.</p>
</div>

Replace [N] with: Q{q_start}, Q{q_start+1}... Q{q_end}

STRICT RULES:
- Raw HTML only — no markdown, no code blocks
- Generate EXACTLY {count} questions: Q{q_start} through Q{q_end}
- STRICTLY follow the answer length requirement above
- Every answer must be complete sentences — never one word only
- Base ALL questions on the lesson text below
- Do NOT mix in questions from other mark categories
- Do NOT stop before Q{q_end}

Lesson Text:
---
{text}
---

Start at Q{q_start}. End at Q{q_end}. Follow answer length strictly."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=QA_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except Exception as e:
            print(f"❌ QA {mark_type}-mark error: {e}")
            return None

    def _clean(self, raw: str) -> str:
        if not raw:
            return raw
        text = raw.strip()
        text = re.sub(r'^```(?:html)?\s*\n', '', text)
        text = re.sub(r'\n```\s*$', '', text)
        text = re.sub(r'```(?:html)?\s*\n', '', text)
        text = re.sub(r'\n```', '', text)
        first_tag = re.search(r'<(?:div|h[1-6]|section|p|table|hr)', text)
        if first_tag and first_tag.start() > 0:
            preamble = text[:first_tag.start()].strip()
            if preamble and not preamble.startswith('<'):
                text = text[first_tag.start():]
        return text.strip()


# Singleton instance
qa_builder = QABuilder()