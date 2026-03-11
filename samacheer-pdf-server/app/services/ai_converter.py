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
# LP DURATION RULES (by lesson type)
# Automatically determines number of days based on lesson type.
# ============================================================================

LP_DURATION_RULES = {
    "prose":         8,
    "poem":          3,
    "supplementary": 4,
    "play":          5,
    "drama":         5,
}

def _get_lp_duration(lesson_type: str) -> int:
    """Returns the correct number of days for the lesson type."""
    return LP_DURATION_RULES.get(lesson_type.lower(), 4)


# ============================================================================
# LP SYSTEM PROMPT (TL-approved — do not modify without TL approval)
# ============================================================================

LP_SYSTEM_PROMPT = """You are an experienced English teacher with deep knowledge of the Tamil Nadu Samacheer Kalvi syllabus and activity-based learning methods used in Indian classrooms.
Create a detailed and practical lesson plan for the following so that even inexperienced teachers can go to class confidently."""


def _build_lp_prompt(class_num: int, lesson_title: str, lesson_type: str, unit: int, text: str) -> str:
    """
    Builds the full LP prompt using the TL-approved lesson plan format.
    Duration is automatically calculated based on lesson type.
    """
    duration_days = _get_lp_duration(lesson_type)

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
Duration: {duration_days} days

Duration Rules (already applied above):
• Prose – 8 days
• Poem – 3 days
• Supplementary Reader – 4 days
• Drama / Play – 5 days

The lesson plan should be suitable for a real classroom in a Tamil Nadu government or private school.

Include the following sections:

1. General Information
• Class
• Subject: English
• Unit / Lesson Title
• Duration (number of days)

2. Learning Objectives
Write clear objectives under:
• Knowledge objectives
• Skill objectives (Reading, Writing, Listening, Speaking)
• Value-based or life skill objectives if relevant

3. Teaching Aids / Learning Materials
Examples:
• Textbook
• Blackboard / whiteboard
• Flashcards
• Pictures
• Worksheets
• Audio or video if relevant

4. Pre-Reading / Warm-up Activity
• Short engaging activity
• Connects lesson to students' real-life experience
• Prediction or brainstorming activity

5. Vocabulary Introduction
• List important new words
• Simple meanings suitable for the grade level
• Example sentences

6. Reading Stage
Include:
• Teacher model reading
• Silent reading
• Pair reading or group reading
• Pronunciation guidance

7. Comprehension Questions
Create questions at three levels:
• Literal questions (Remembering / Understanding)
• Inferential questions (Applying / Analyzing)
• Critical thinking questions (Evaluating / Creating)
Ensure questions follow Bloom's Taxonomy.

8. Language Focus
Identify grammar or language patterns from the text and provide a short practice activity.

9. Activity-Based Learning
Include interactive activities such as:
• Think–Pair–Share
• Group discussion
• Role play
• Vocabulary games
• Short writing activity
• Creative response to the text

10. Differentiated Instruction
• Support strategies for slow learners
• Enrichment activities for advanced learners

11. Assessment
Include:
• Oral questions
• Quick written task
• Exit ticket or recap activity

12. Homework / Follow-up Task

DAY-WISE LESSON PLAN FORMAT
Create a day-by-day lesson plan for exactly {duration_days} days.
For EACH DAY include:
- Day Number
- Topic Focus
- Time Allocation
- Teacher Activities
- Student Activities
- Teaching Aids
- Board Work (write exactly what will appear on the board)
- Assessment Questions
- Closure / Recap

Additional Requirements:
• Include at least one engaging classroom activity per day.
• Connect the lesson to real-life situations wherever possible.
• Ensure the lesson plan reflects activity-based learning.
• Use clear, practical classroom language.
• Make the plan easy for teachers to follow.

Output ONLY the HTML body content — no <html>, <head>, or <body> tags.

Formatting Rules:
- Start with: <div class="sk-content-header"><h1>Lesson Plan — {lesson_title}</h1><p class="sk-meta">Class {class_num} | English | Unit {unit} | {type_display} | {duration_days} Days</p></div>
- Use <h2> for the 12 main sections
- Use <h3> for Day headings (e.g. Day 1, Day 2...)
- Use <table> for day-wise plan (columns: Activity, Duration, Description)
- Use <ul><li> for bullet lists
- Use <div class="board-work"> for Board Work sections
- Make it detailed, practical, and classroom-ready

Lesson Text (use this as the basis for all activities, vocabulary, and questions):
---
{text}
---

Output ONLY the HTML body content."""


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
                max_tokens=4000,
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
    # PRIVATE: QA generation
    # ──────────────────────────────────────────────────────────────────────────

    def _generate_qa(self, text: str, metadata: Dict) -> Optional[str]:
        """Generates a structured Questions & Answers HTML page for the lesson."""
        try:
            class_num = metadata.get("class", "")
            subject = metadata.get("subject", "english")
            unit = metadata.get("unit", "")
            lesson_title = metadata.get("lesson_title", "Unknown")
            lesson_type = metadata.get("lesson_type", "prose")

            prompt = f"""Generate a comprehensive Questions & Answers (Q&A) document for this textbook lesson.

Lesson Information:
- Class: {class_num}
- Subject: {subject.title()}
- Unit: {unit}
- Lesson: {lesson_title}
- Type: {lesson_type}

Output ONLY the HTML body content — no <html>, <head>, or <body> tags.

Structure:
1. Header: <div class="sk-content-header"><h1>Questions & Answers — {lesson_title}</h1><p class="sk-meta">Class {class_num} | {subject.title()} | Unit {unit}</p></div>

2. Section A — Comprehension Questions (5-7 questions)
   - Use <div class="qa-item"><p class="question"><strong>Q1. ...</strong></p><p class="answer"><strong>Answer:</strong> ...</p></div>
   - Questions should test understanding of the lesson

3. Section B — Vocabulary Questions (4-5 questions)
   - Word meanings, fill in the blanks, match the following
   - Use appropriate HTML tables for match-the-following

4. Section C — Short Answer Questions (4-5 questions, 2-3 sentences each)

5. Section D — Long Answer / Essay Questions (2-3 questions, paragraph answers)

6. Section E — Think and Reflect (2-3 higher-order thinking questions)

Rules:
- All answers must be based ONLY on the provided lesson text
- Keep answers student-friendly and exam-appropriate
- Use <h2> for section headings
- Number questions clearly

Lesson Text:
---
{text}
---

Output ONLY the HTML body content."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
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
        Generates a detailed Lesson Plan HTML page using the TL-approved prompt.
        Duration is automatically set based on lesson type:
          Prose = 8 days | Poem = 3 days | Supplementary = 4 days | Play/Drama = 5 days
        """
        try:
            class_num   = metadata.get("class", "")
            subject     = metadata.get("subject", "english")
            unit        = metadata.get("unit", "")
            lesson_title = metadata.get("lesson_title", "Unknown")
            lesson_type  = metadata.get("lesson_type", "prose")

            # Build the full TL-approved prompt
            prompt = _build_lp_prompt(
                class_num=class_num,
                lesson_title=lesson_title,
                lesson_type=lesson_type,
                unit=unit,
                text=text
            )

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,   # LP is detailed — needs more tokens than content/qa
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