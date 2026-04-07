"""
content_builder/qa_builder.py

Generates QA in 4 focused calls — one per mark category.
Each call has one job. No single call gets overwhelmed.

Call 1 → Header + 1-mark questions (Q1  - Q25)
Call 2 → 2-mark questions          (Q26 - Q50)
Call 3 → 5-mark questions          (Q51 - Q75)
Call 4 → 8-mark questions          (Q76 - Q100)
"""

import anthropic
import re
from typing import Optional, Dict
from ..config import settings


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

QA_SYSTEM_PROMPT = """You are an experienced English teacher creating exam-ready question banks for Tamil Nadu Samacheer Kalvi State Board students.

CRITICAL OUTPUT RULES:
- Output ONLY raw HTML body content
- NEVER wrap output in markdown code blocks
- NEVER use backticks anywhere
- Start directly with HTML tags — no preamble text
- Base ALL questions on the lesson text provided
- NEVER invent content not present in the text"""


# ============================================================================
# QA BUILDER CLASS
# ============================================================================

class QABuilder:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model  = settings.ANTHROPIC_MODEL

    def generate(self, text: str, metadata: Dict) -> Optional[str]:
        """
        Main method. Generates complete QA HTML
        using 4 focused calls — one per mark category.
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

        # ── Call 1: Header + 1-mark questions ────────────────────────────────
        print(f"      [QA] Call 1/4: 1-mark questions (Q1-Q25)...")
        part1 = self._call_by_marks(
            text=text,
            lesson_title=lesson_title,
            class_num=class_num,
            unit=unit,
            type_display=type_display,
            has_grammar=has_grammar,
            mark_type=1,
            q_start=1,
            q_end=25,
            include_header=True
        )
        if part1:
            parts.append(self._clean(part1))
            print(f"         ✅ 1-mark done ({len(part1)} chars)")
        else:
            print(f"         ❌ 1-mark failed")

        # ── Call 2: 2-mark questions ──────────────────────────────────────────
        print(f"      [QA] Call 2/4: 2-mark questions (Q26-Q50)...")
        part2 = self._call_by_marks(
            text=text,
            lesson_title=lesson_title,
            class_num=class_num,
            unit=unit,
            type_display=type_display,
            has_grammar=has_grammar,
            mark_type=2,
            q_start=26,
            q_end=50,
            include_header=False
        )
        if part2:
            parts.append(self._clean(part2))
            print(f"         ✅ 2-mark done ({len(part2)} chars)")
        else:
            print(f"         ❌ 2-mark failed")

        # ── Call 3: 5-mark questions ──────────────────────────────────────────
        print(f"      [QA] Call 3/4: 5-mark questions (Q51-Q75)...")
        part3 = self._call_by_marks(
            text=text,
            lesson_title=lesson_title,
            class_num=class_num,
            unit=unit,
            type_display=type_display,
            has_grammar=has_grammar,
            mark_type=5,
            q_start=51,
            q_end=75,
            include_header=False
        )
        if part3:
            parts.append(self._clean(part3))
            print(f"         ✅ 5-mark done ({len(part3)} chars)")
        else:
            print(f"         ❌ 5-mark failed")

        # ── Call 4: 8-mark questions ──────────────────────────────────────────
        print(f"      [QA] Call 4/4: 8-mark questions (Q76-Q100)...")
        part4 = self._call_by_marks(
            text=text,
            lesson_title=lesson_title,
            class_num=class_num,
            unit=unit,
            type_display=type_display,
            has_grammar=has_grammar,
            mark_type=8,
            q_start=76,
            q_end=100,
            include_header=False
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

    # ──────────────────────────────────────────────────────────────────────────
    # SINGLE MARK CATEGORY CALL
    # ──────────────────────────────────────────────────────────────────────────

    def _call_by_marks(
        self,
        text: str,
        lesson_title: str,
        class_num: int,
        unit: int,
        type_display: str,
        has_grammar: bool,
        mark_type: int,
        q_start: int,
        q_end: int,
        include_header: bool
    ) -> Optional[str]:
        try:
            count = q_end - q_start + 1

            # ── Header HTML ───────────────────────────────────────────────────
            header_html = ""
            if include_header:
                header_html = f"""<div class="sk-content-header">
  <h1>Question Bank — {lesson_title}</h1>
  <p class="sk-meta">Class {class_num} | English | Unit {unit} | {type_display}</p>
</div>"""

            # ── Question type guidance per mark ───────────────────────────────
            mark_guidance = {
                1: f"""Generate EXACTLY {count} one-mark questions (Q{q_start} to Q{q_end}).

Use ALL of these question types — distribute evenly:
- Fill in the blank (one word or short phrase answer)
- Choose the correct answer (state 4 options in the question itself)
- True or False (state the statement clearly)
- One-word answer / one-sentence answer
- Who said this / who is being described
- Name the character / identify the speaker

Every answer must be a COMPLETE SENTENCE even for 1-mark questions.
Example: Q1. ______ was the chief of all spirits. Answer: Ariel was the chief of all spirits.""",

                2: f"""Generate EXACTLY {count} two-mark questions (Q{q_start} to Q{q_end}).

Use ALL of these question types — distribute evenly:
- Short answer (2-3 complete sentences)
- Explain a line or phrase from the text in your own words
- Find the figure of speech or literary device
- Vocabulary — give synonym, antonym, or meaning in context
- Reference to context — who said it and what does it mean
- Compare two characters or events briefly

Every answer must be 2-3 COMPLETE SENTENCES.""",

                5: f"""Generate EXACTLY {count} five-mark questions (Q{q_start} to Q{q_end}).

Use ALL of these question types — distribute evenly:
- Paragraph answer describing a character or event
- Central idea or main theme of the lesson
- Compare and contrast two characters or situations
- Explain the significance of a key event in the story
- Value-based question — what lesson or value does the text teach
- Retell a specific scene or episode from the story

Every answer must be 5-8 COMPLETE SENTENCES.""",

                8: f"""Generate EXACTLY {count} eight-mark questions (Q{q_start} to Q{q_end}).

Use ALL of these question types — distribute evenly:
- Essay — detailed explanation of the full lesson or a major theme
- Character sketch — detailed description of a main character
- Summary — retell the entire lesson in your own words
- Creative writing — write a letter, diary entry, or continuation
- Critical appreciation — analyse the style, theme, and message
{"- Grammar essay — write a paragraph using specific grammar structures from the lesson" if has_grammar else ""}

Every answer must be 10-15 COMPLETE SENTENCES.""",
            }

            grammar_note = ""
            if has_grammar and mark_type in (1, 2):
                grammar_note = f"\nAlso include {max(count // 5, 2)} grammar questions based on the grammar section of the lesson."

            # ── Build prompt ──────────────────────────────────────────────────
            prompt = f"""Generate ONLY {mark_type}-mark questions for this question bank.
Do NOT generate any other mark type in this response.

Lesson: {lesson_title} | Class {class_num} | Unit {unit} | {type_display}

{mark_guidance[mark_type]}
{grammar_note}

HTML FORMAT:
{header_html}
<h2>{mark_type}-Mark Questions</h2>
<div class="marks-badge">{mark_type} Mark{"s" if mark_type > 1 else ""}</div>

Each question MUST follow this exact format:
<div class="qa-item">
  <p class="question"><strong>Q[N]. Question text here?</strong></p>
  <p class="answer"><strong>Answer:</strong> Complete sentence answer here.</p>
</div>

Replace [N] with actual number: Q{q_start}, Q{q_start+1}, Q{q_start+2}... Q{q_end}

STRICT RULES:
- Raw HTML only — no markdown, no code blocks, no backticks
- Generate EXACTLY {count} questions: Q{q_start} through Q{q_end}
- Count every question as you go
- Every answer is a complete sentence — never one word only
- Base ALL questions strictly on the lesson text below
- Do NOT add questions from other mark categories
- Do NOT stop before Q{q_end}

Lesson Text:
---
{text}
---

Start with Q{q_start}. End with Q{q_end}. Count carefully."""

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

    # ──────────────────────────────────────────────────────────────────────────
    # CLEAN OUTPUT
    # ──────────────────────────────────────────────────────────────────────────

    def _clean(self, raw: str) -> str:
        """Strip markdown fences and preamble text."""
        if not raw:
            return raw
        text = raw.strip()
        text = re.sub(r'^```(?:html)?\s*\n', '', text)
        text = re.sub(r'\n```\s*$', '', text)
        text = re.sub(r'```(?:html)?\s*\n', '', text)
        text = re.sub(r'\n```', '', text)
        # Remove preamble before first HTML tag
        first_tag = re.search(r'<(?:div|h[1-6]|section|p|table|hr)', text)
        if first_tag and first_tag.start() > 0:
            preamble = text[:first_tag.start()].strip()
            if preamble and not preamble.startswith('<'):
                text = text[first_tag.start():]
        return text.strip()


# Singleton instance
qa_builder = QABuilder()