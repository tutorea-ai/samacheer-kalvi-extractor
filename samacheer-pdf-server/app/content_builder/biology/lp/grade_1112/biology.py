"""
biology.py
----------
LP Builder for Samacheer Kalvi Biology — Class 11 & 12
Disciplines: Botany and Zoology (same file)

v0.2 — Sept 2026 — REBUILT from v0.1's wrong assumption. v0.1 treated
the Classical Genetics manual LP as a per-chapter hardcoded topic
structure (GENETICS_14_DAY_STRUCTURE, routed by lesson_title keyword).
That was wrong: the manual LP is a content-agnostic TEACHING TEMPLATE —
same relationship as SS History's DAY_STRATEGY to an actual chapter.
This version matches that: 14 days and a rotating teaching technique per
day number are FIXED (day_structures.BIOLOGY_DAY_STRATEGY); WHICH TOPICS
land on which day is discovered per-chapter by a real Section Extractor
+ Day Allocator, same mechanism as SS History.

CALL STRUCTURE (16 calls, every chapter, same count regardless of topic):
  Call 0a → Section Extractor (JSON — ALL headings/subheadings in this
                                chapter's text, Biology-enriched with
                                key_terms/diagrams/tamil_terms/ratios)
  Call 0b → Day Allocator      (JSON — REAL API call. Distributes ALL
                                extracted sections across 14 days. Day 14
                                gets NO new sections — revision only.)
  Call 1  → Preamble
  Call 2-15 → Day 1...Day 14   (Day 14 = revision + embedded assessment,
                                no separate trailing Assessment call)

QA (biology/qa/grade_1112/biology.py) is UNCHANGED and UNAFFECTED by
this rebuild — it never depended on day_structures.py.
"""

import json
import re
import anthropic
from typing import Optional
from .....config import settings
from ...base import (
    BIO_LP_SYSTEM_PROMPT,
    PREAMBLE_START_INSTRUCTION,
    TAMIL_INSTRUCTION,
    clean,
)
from ...base.day_structures import BIOLOGY_DAY_STRATEGY, BIOLOGY_STRUCTURE_META


# ============================================================================
# SHARED BUILDER LOGIC — Botany and Zoology use identical logic; only
# discipline name differs (for logging/prompt context).
# ============================================================================

class _BiologyLP1112Base:

    discipline: str = "biology"  # overridden by subclasses

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ {self.discipline.title()} LP Builder (1112) v0.2 initialized — model: {self.model}")

    # -------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------

    def generate(self, text: str, metadata: dict) -> Optional[str]:
        lesson_title = metadata.get("lesson_title", "Unknown")
        class_num    = metadata.get("class", "")
        unit         = metadata.get("unit", "")
        month        = metadata.get("month", "")

        total_days = BIOLOGY_STRUCTURE_META["total_days"]  # fixed: 14
        total_api_calls = 2 + total_days  # Section Extractor + Day
                                           # Allocator + Preamble + N days
        print(f"      [{self.discipline.title()} LP 1112] Generating: {lesson_title}")
        print(f"      [{self.discipline.title()} LP 1112] total_days={total_days} "
              f"total_api_calls={total_api_calls}")

        parts = []

        # Call 0a — Section Extractor
        print(f"      [{self.discipline}] Call 0a: Section Extractor...")
        sections = self._call_section_extractor(text, lesson_title)
        if not sections:
            print(f"         ❌ Section Extractor failed — aborting")
            return None
        n_sections = len(sections.get("chapter_sections", []))
        print(f"         ✅ Extracted {n_sections} sections")

        # Call 0b — Day Allocator (REAL API call — judgment required)
        print(f"      [{self.discipline}] Call 0b: Day Allocator...")
        day_plan = self._call_day_allocator(sections, lesson_title)
        if not day_plan:
            print(f"         ❌ Day Allocator failed — aborting")
            return None
        print(f"         ✅ Day plan ready for {len(day_plan)} days")

        # Call 1 — Preamble
        print(f"      [{self.discipline}] Call 1: Preamble...")
        preamble = self._call_preamble(
            text, class_num, unit, lesson_title, month, sections, day_plan
        )
        if preamble:
            parts.append(clean(preamble))
            print(f"         ✅ Preamble ({len(preamble)} chars)")
        else:
            print(f"         ❌ Preamble failed — aborting")
            return None

        # Calls 2..(1+total_days) — Content days
        for day_num in range(1, total_days + 1):
            call_num = day_num + 1
            print(f"      [{self.discipline}] Call {call_num}: Day {day_num}...")
            day_html = self._call_content_day(
                text, class_num, unit, lesson_title,
                day_num, day_plan.get(day_num, {}), day_plan
            )
            if day_html:
                parts.append(clean(day_html))
                print(f"         ✅ Day {day_num} ({len(day_html)} chars)")
            else:
                print(f"         ❌ Day {day_num} failed — continuing")

        # Append anything Call 0a's allocator left unplaced — deterministic,
        # no API call, zero risk to the days already generated. Carried
        # over from the earlier unmapped-content fix (still applies: the
        # Day Allocator can flag sections it couldn't place).
        unmapped = getattr(self, "_last_unmapped_content", [])
        if unmapped:
            items_html = "".join(f"<li>{item}</li>" for item in unmapped)
            note_html = (
                '<div class="lp-additional-content-note">'
                '<h4>Additional Chapter Content</h4>'
                '<p>The following content appears in this chapter but did not '
                'fit the standard 14-day plan. Review and incorporate '
                'where appropriate:</p>'
                f'<ul>{items_html}</ul>'
                '</div>'
            )
            parts.append(note_html)

        if not parts:
            return None

        combined = "\n\n".join(parts)
        print(f"      [{self.discipline.title()} LP 1112] ✅ Complete — "
              f"{len(parts)} parts, {len(combined)} chars")
        return combined

    # =====================================================================
    # CALL 0a — SECTION EXTRACTOR
    #
    # Discovers ALL headings/subheadings from THIS chapter's actual text —
    # no assumption about which topics exist or how many there are. Same
    # role as SS History's Section Extractor, enriched with the Biology-
    # specific fields (key_terms, diagrams, tamil_terms, ratios) that
    # proved valuable in the earlier build and real test run.
    # =====================================================================

    def _call_section_extractor(self, text: str, lesson_title: str) -> Optional[dict]:
        try:
            prompt = f"""You are a STRICT TEXT EXTRACTOR for a Samacheer Kalvi Biology chapter.

YOUR ONLY JOB: Extract EVERY heading and subheading that appears in the
chapter text, in order. Do not assume how many sections there should be —
extract exactly what the text actually contains.

ABSOLUTE RULES:
- Copy EVERY heading/subheading EXACTLY as written — do not paraphrase
- Do NOT skip any heading or subheading — extract ALL of them in order
- Do NOT add anything from general knowledge
- Estimate teaching time per section based on content density
- Capture key terms, specific numbers/ratios, and diagram mentions per
  section — use ONLY what appears verbatim in the text, never invent or
  round a number or ratio
- A chapter with substantial length should have multiple sections; do
  not under-extract by merging distinct headings together

Chapter: {lesson_title}

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting
with {{

{{
  "chapter_sections": [
    {{
      "heading": "EXACT heading text",
      "subheadings": [
        {{"title": "EXACT subheading text", "sub_subheadings": ["EXACT sub-subheading if present"]}}
      ],
      "estimated_teaching_time_mins": 10,
      "key_terms": ["term1", "term2"],
      "specific_numbers_ratios": ["9:3:3:1", "787 tall : 277 dwarf"],
      "diagrams": ["diagram or figure description mentioned in the text, if any"],
      "tamil_terms": [{{"english": "term", "tamil": "தமிழ் சொல்"}}]
    }}
  ],
  "total_estimated_teaching_mins": 0
}}

Chapter Text:
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,  # richer per-section schema than SS
                                    # History's (ratios/diagrams/tamil_terms
                                    # added) — start at the content-day
                                    # tier given LP's earlier Call 0a lesson
                                    # (measure real usage, don't assume)
                system=(
                    "You are a strict text extractor. Return ONLY valid JSON. "
                    "Extract ALL headings/subheadings actually present — never "
                    "invent structure, never invent numbers or ratios. No "
                    "markdown. No code fences. Raw JSON starting with {"
                ),
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            return json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"❌ [{self.discipline}] Section Extractor JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ [{self.discipline}] Section Extractor error: {e}")
            return None

    # =====================================================================
    # CALL 0b — DAY ALLOCATOR (real API call — judgment required, same
    # reason as SS History's: day topics are not known ahead of time)
    #
    # Distributes ALL extracted sections/subheadings across 14 days.
    # Day 14 gets NO new sections — universal rule, revision only.
    # =====================================================================

    def _call_day_allocator(self, sections: dict, lesson_title: str) -> Optional[dict]:
        try:
            sections_str = json.dumps(sections, indent=2)

            prompt = f"""You are a SMART DAY ALLOCATOR for a Samacheer Kalvi Biology lesson plan.

Allocate ALL sections AND subheadings to exactly 14 DAYS.

RULES:
- Each of Days 1-13: roughly 15-22 minutes of new content (35 min
  session minus opening/activity/closing time)
- DAY 14 IS REVISION ONLY — it must NOT receive any new section or
  subheading. Day 14 consolidates everything already taught in Days 1-13.
- Keep each main section in ONE day where possible — do not split a
  section across days unless it is genuinely large (>15 mins of content)
- Keep subheadings WITH their main section's day
- EVERY section AND subheading extracted must appear in exactly ONE day
  (Days 1-13 only) — no duplicates, no omissions
- Sections must follow the chapter's own order — do not reorder content
- If total content is too large or too small to fit naturally across 13
  content days, distribute as evenly as reasonable; do not force exactly
  equal minutes per day if content density genuinely varies
- If any section/subheading genuinely cannot be placed in any day (rare —
  e.g. purely introductory front-matter with no teachable content), list
  it under "unmapped_content" instead of forcing it in — do not invent a
  home for it

Return ONLY valid JSON. No explanation. No markdown. Raw JSON starting
with {{

{{
  "days": {{
    "1": {{
      "sections": ["EXACT heading 1"],
      "subheadings": ["EXACT subheading 1", "EXACT subheading 2"],
      "focus": "One sentence — what Day 1 covers",
      "estimated_mins": 20,
      "key_terms": ["term1", "term2"],
      "specific_numbers_ratios": ["..."],
      "diagrams": ["..."],
      "tamil_terms": [{{"english": "term", "tamil": "தமிழ் சொல்"}}]
    }},
    "2": {{ ... same shape ... }},
    ...
    "14": {{
      "sections": [],
      "subheadings": [],
      "focus": "Whole-chapter revision and graded assessment — no new content",
      "estimated_mins": 35,
      "key_terms": [],
      "specific_numbers_ratios": [],
      "diagrams": [],
      "tamil_terms": []
    }}
  }},
  "unmapped_content": []
}}

Include an entry for EVERY day 1 through 14 — Day 14's sections/
subheadings arrays must be empty per the rule above.

Extracted Sections:
---
{sections_str}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,  # 14-day allocation output, similar
                                    # scale reasoning to Section Extractor
                system=(
                    "You are a strict day allocator. Return ONLY valid JSON. "
                    "No markdown. No code fences. Raw JSON starting with { "
                    "Day 14 must never contain new sections or subheadings."
                ),
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()
            raw = re.sub(r'```(?:json)?', '', raw).strip()
            raw = re.sub(r'```', '', raw).strip()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"❌ RAW AROUND ERROR: {raw[max(0, e.pos-100):e.pos+100]}")
                raise

            days_out = parsed.get("days", {})
            unmapped = parsed.get("unmapped_content", [])

            # Completeness check: compare what Call 0a extracted against
            # what Call 0b actually placed. Catches silent omissions the
            # Allocator never self-reported — unmapped_content only
            # catches what the model ADMITS it couldn't place.
            # KNOWN GAP: exact-string match only, and only checks two
            # levels (heading + subheading) — does not reach into
            # sub_subheadings from the Extractor's schema. Acceptable for
            # now; revisit if teachers flag missing granular content.
            # Safe failure direction: a paraphrased (not dropped) item
            # produces a harmless redundant note, never a silent loss.
            extracted_items = set()
            for sec in sections.get("chapter_sections", []):
                extracted_items.add(sec.get("heading", ""))
                for sub in sec.get("subheadings", []):
                    title = sub.get("title", sub) if isinstance(sub, dict) else sub
                    extracted_items.add(title)
            extracted_items.discard("")

            placed_items = set(unmapped)
            for d in days_out.values():
                placed_items.update(d.get("sections", []))
                placed_items.update(d.get("subheadings", []))

            silently_dropped = extracted_items - placed_items
            if silently_dropped:
                print(f"      ⚠️ [{self.discipline}] Completeness check found "
                      f"{len(silently_dropped)} item(s) the Allocator placed "
                      f"nowhere and never flagged — adding to the content note")
                unmapped = list(unmapped) + list(silently_dropped)

            self._last_unmapped_content = unmapped
            if unmapped:
                print(f"      ⚠️ [{self.discipline}] {len(unmapped)} unmapped "
                      f"content item(s) total — will be appended as a "
                      f"chapter note, not lost")
            return {int(k): v for k, v in days_out.items()}
        except json.JSONDecodeError as e:
            print(f"❌ [{self.discipline}] Day Allocator JSON error: {e}")
            return None
        except Exception as e:
            print(f"❌ [{self.discipline}] Day Allocator error: {e}")
            return None

    # =====================================================================
    # CALL 1 — PREAMBLE
    #
    # Objectives are now GENERATED from the extracted sections/day_plan
    # (no fixed per-day learning_objectives list exists anymore, since
    # topics are discovered per-chapter) — same approach as SS History's
    # Preamble, grounded in the real extracted section/key-term data so
    # it isn't free invention.
    # =====================================================================

    def _call_preamble(self, text, class_num, unit, lesson_title, month,
                        sections: dict, day_plan: dict):
        try:
            total_days = BIOLOGY_STRUCTURE_META["total_days"]

            day_summary = ""
            for day_num in sorted(day_plan.keys()):
                d = day_plan[day_num]
                day_summary += (
                    f"  Day {day_num}: {', '.join(d.get('sections', [])) or '(revision)'} "
                    f"— {d.get('focus', '')}\n"
                )

            all_key_terms = []
            all_diagrams = []
            for d in day_plan.values():
                all_key_terms.extend(d.get("key_terms", []))
                all_diagrams.extend(d.get("diagrams", []))
            key_terms_str = ", ".join(all_key_terms[:20]) if all_key_terms else "(none extracted)"
            diagrams_str = "\n".join(f"  - {dg}" for dg in all_diagrams) or "  (none extracted)"

            avoid_list = "\n".join(f"  - {a}" for a in BIOLOGY_STRUCTURE_META.get("avoid", []))

            prompt = f"""Generate ONLY the preamble section of this Biology Lesson Plan.
Do NOT generate any Day blocks. Stop after Teaching Aids.

Chapter    : {lesson_title}
Class      : {class_num}
Unit       : {unit}
Subject    : Biology
Discipline : {self.discipline.title()}
Month      : {month if month else 'As scheduled'}
Duration   : {total_days} Days x 35 Minutes = {total_days * 35} Minutes Total

DAY-WISE PLAN (from Section Extractor + Day Allocator, real chapter content):
{day_summary}

KEY TERMS FOUND IN CHAPTER: {key_terms_str}

DIAGRAMS FOUND IN CHAPTER (for Teaching Aids — use these, do not invent
additional diagrams not in this list):
{diagrams_str}

PEDAGOGICAL PATTERNS TO AVOID:
{avoid_list}

GROUNDING RULE for Value and Skill Objectives (Parts 3 and 4 below):
- Every value objective must connect to a REAL concept from THIS chapter
- Every skill objective must name a REAL activity traceable to one of
  the day topics listed above
- Do NOT write generic objectives that could apply to any Biology chapter
- Each objective must be falsifiable: a reader should be able to say
  "yes, this chapter teaches that" or "no, it doesn't"
- Value objectives often connect to: the scientist's story, ethical
  dimensions, health implications, or Tamil Nadu context where genuinely
  relevant — ground in THIS chapter's content, not Biology in general

Generate EXACTLY these sections in this order:

<h2>Part 1: Chapter Overview</h2>
Table: Class | Subject | Discipline | Unit/Chapter Title | Month |
       Total Teaching Hours | Session Duration | Main Topics Covered
       (use the day-wise plan above)

<h2>Part 2: Learning Objectives</h2>
4-6 chapter-level objectives with action verbs (Explain, Analyze, Solve,
Construct, Distinguish, Predict). MUST trace back to the actual sections
in the day-wise plan above — not invented independently of it.

<h2>Part 3: Value-Based Objectives</h2>
3-4 value objectives grounded in this chapter's actual content. Apply
the GROUNDING RULE above.

<h2>Part 4: Skill Objectives</h2>
3-4 skill objectives specific to this chapter's actual content. Apply
the GROUNDING RULE above.

<h2>Part 5: Teaching Aids</h2>
All materials: board, chalk, chart paper for diagrams listed above,
textbooks, notebooks. Name the specific diagrams found in this chapter.
No page numbers.

OUTPUT RULES:
- Raw HTML only
{PREAMBLE_START_INSTRUCTION}
- Stop after Teaching Aids
- Do NOT invent facts, objectives, or diagrams not present in the
  reference material above or the chapter text excerpt below

Chapter Text (reference, for tone/context only):
---
{text[:3000]}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=BIO_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ [{self.discipline}] Preamble error: {e}")
            return None

    # =====================================================================
    # CLOSING INSTRUCTION — Day 14 rule is now UNIVERSAL (day_num == 14),
    # not read from a per-chapter flag, since it's fixed for every chapter.
    # =====================================================================

    def _get_closing_instruction(self, day_num: int, total_days: int,
                                  next_day_focus: str) -> str:
        if day_num == total_days:
            return f"""
DAY {day_num} — EMBEDDED GRADED ASSESSMENT (REPLACES standard closing):
This is the FINAL day of the chapter — revision only, no new content.
There is NO separate trailing Assessment call — this day's closing IS
the assessment.

Structure the back portion of this day as a graded mini-assessment,
covering the WHOLE chapter (all {total_days} days):
  Section A (1 mark each)  — quick recall across the chapter
  Section B (2 marks each) — short answer
  Section C (3 marks each) — explain / distinguish / solve
  Section D (5 marks each) — detailed answer or worked problem
Base every question on real content from THIS chapter — use the
day-by-day content supplied across this generation, never invent a fact.

Do NOT include:
- Homework tasks (chapter is complete)
- A "preview tomorrow" line (there is no tomorrow for this chapter)
"""
        else:
            preview_line = (
                f'Preview: "Tomorrow we cover — {next_day_focus}"'
                if next_day_focus else
                'Preview: (next day focus not available — omit preview line)'
            )
            return f"""
[30-35 min] Closing:
- 3 rapid-fire recap questions covering today's content
- Key points on board: 3 bullet points summarizing today
- Homework: 2 specific written tasks based on today's content only
- {preview_line}
"""

    # =====================================================================
    # CALLS 2..15 — CONTENT DAYS
    #
    # WHAT to teach comes from day_plan[day_num] (Section Extractor + Day
    # Allocator output — real chapter content, discovered not assumed).
    # HOW to teach it comes from BIOLOGY_DAY_STRATEGY[day_num] (fixed
    # technique rotation — content-agnostic, same for every chapter).
    # =====================================================================

    def _call_content_day(self, text, class_num, unit, lesson_title,
                           day_num: int, day_content: dict, day_plan: dict):
        try:
            total_days = BIOLOGY_STRUCTURE_META["total_days"]
            technique = BIOLOGY_DAY_STRATEGY.get(day_num, {})

            sections    = day_content.get("sections", [])
            subheadings = day_content.get("subheadings", [])
            focus       = day_content.get("focus", "")
            key_terms   = day_content.get("key_terms", [])
            diagrams    = day_content.get("diagrams", [])
            tamil_terms = day_content.get("tamil_terms", [])
            numbers     = day_content.get("specific_numbers_ratios", [])

            next_day_focus = day_plan.get(day_num + 1, {}).get("focus", "")

            sections_str    = "\n".join(f"  - {s}" for s in sections) or "  (revision day — no new sections)"
            subheadings_str = "\n".join(f"      - {s}" for s in subheadings)
            key_terms_str   = ", ".join(key_terms) if key_terms else "(none extracted — use chapter text directly)"
            diagrams_str    = "\n".join(f"  - {d}" for d in diagrams) or "  (none extracted)"
            numbers_str     = ", ".join(numbers) if numbers else "(none extracted)"
            tamil_terms_str = "\n".join(
                f"  - {t.get('english', '')}: {t.get('tamil', '')}" for t in tamil_terms
            ) or "  (none extracted — derive from key terms using TAMIL SCAFFOLDING RULES)"

            closing_instruction = self._get_closing_instruction(
                day_num, total_days, next_day_focus
            )

            prompt = f"""You are writing Day {day_num} of a Samacheer Kalvi Biology Lesson Plan.

REFERENCE: real-life example -> simple English -> Tamil mirror ->
textbook term -> board diagram -> student practice, with CFU/CCQ checks
woven in naturally throughout, not batched at the end.

Chapter    : {lesson_title}
Class      : {class_num}
Unit       : {unit}
Subject    : Biology — {self.discipline.title()}
Day        : {day_num} of {total_days}
Duration   : 35 minutes

═══════════════════════════════════════════════════════
TODAY'S CONTENT (from Section Extractor + Day Allocator — real chapter
text, discovered for THIS chapter, not assumed)
═══════════════════════════════════════════════════════
Sections:
{sections_str}

Subheadings:
{subheadings_str}

Day focus: {focus}
Key terms: {key_terms_str}
Specific numbers/ratios (use EXACTLY as written, never round): {numbers_str}
Diagrams mentioned: 
{diagrams_str}
Tamil terms already identified:
{tamil_terms_str}

═══════════════════════════════════════════════════════
TODAY'S TEACHING TECHNIQUE (fixed rotation — same for every chapter)
═══════════════════════════════════════════════════════
Opening style: {technique.get('spark_style', '')}
Opening instruction: {technique.get('spark_instruction', '')}

Activity style: {technique.get('activity_style', '')}
Activity instruction: {technique.get('activity_instruction', '')}

{TAMIL_INSTRUCTION}

═══════════════════════════════════════════════════════
CFU / CCQ — NATURAL PLACEMENT (not a fixed count)
═══════════════════════════════════════════════════════
Place CFU and CCQ questions naturally after each concept is taught —
count follows what today's content needs, not a fixed number.
CFU = quick factual recall, no Tamil, under 6 words.
CCQ = deeper Why/How, Tamil mandatory, under 8 words.

CFU FORMAT:
<div class="cfu-block">
  <strong>🔎 CFU:</strong>
  <p class="teacher-says">"[Short factual question]?"</p>
  <p class="student-says"><strong>Expected:</strong> "[Answer]"</p>
  <p><em>⏱ Wait 10 seconds. Call on 2-3 students.</em></p>
</div>

CCQ FORMAT:
<div class="ccq-block">
  <strong>⚡ CCQ:</strong>
  <p class="teacher-says">"[Why/How question]?"</p>
  <p class="student-says"><strong>Expected:</strong> "[1-2 sentence answer]"</p>
  <p class="ccq-tamil"><em>தமிழில்:</em> "[Same question in Tamil]"</p>
  <p><em>⏱ Wait 15 seconds. Pair discussion first.</em></p>
</div>
❌ NEVER use ICQs ("Do you understand?" / "How many marks is this?")

═══════════════════════════════════════════════════════
GENERATE Day {day_num} using this HTML structure
═══════════════════════════════════════════════════════

<h3 class="lp-day-title">Day {day_num} — {', '.join(sections) if sections else 'Revision and Assessment'}</h3>

<div class="lp-day-meta-table">
  <table>
    <tr>
      <th>Focus</th>
      <td>{focus}</td>
    </tr>
  </table>
</div>

<div class="lp-day-block" data-day="{day_num}" data-total-days="{total_days}" id="day-{day_num}">

  <div class="lp-section-opening">
    <h4>[0-5 min] Opening — {technique.get('spark_style', '')}</h4>
    <p class="teacher-says"><strong>Teacher says:</strong><br/>
    "[Deliver today's opening per the OPENING INSTRUCTION above, adapted
     to today's actual content]"</p>
    <p class="lead-tamil"><em>தமிழில்:</em> "[Opening question in Tamil —
    meaning-based — this is Tamil place 3 of 3]"</p>
    <div class="lp-teacher-says">
      <strong>Teacher says — Why We Learn This:</strong><br/>
      "[Specific to TODAY's actual content — real reason, concrete Tamil
       Nadu student example, never a generic exam reason]"
    </div>
  </div>

  <div class="lp-section-main">
    <h4>[5-22 min] {', '.join(sections) if sections else 'Whole-Chapter Revision'}</h4>

    <div class="lp-vocab-block">
      <strong>Key Terms — Write on Board:</strong>
      <table>
        <thead><tr><th>Term</th><th>Meaning</th><th>Tamil பொருள்</th></tr></thead>
        <tbody>
          [Key terms from the list above with meanings and Tamil —
           this is Tamil place 1 of 3]
        </tbody>
      </table>
    </div>

    <p class="teacher-says"><strong>Teacher explains (English):</strong><br/>
    "[Explanation using today's content above — real numbers/ratios
     exactly as given, real examples, simple language]"</p>

    <div class="lp-tamil-scaffold">
      <strong>ஆசிரியருக்கு (Tamil — exact mirror):</strong>
      <p>"[Same explanation in Tamil — this is Tamil place 2 of 3. If
          today covers multiple sub-parts, mirror ONLY the single most
          important explanation, not every sub-part]"</p>
    </div>

    <div class="lp-board-work">
      <strong>Draw on Board:</strong><br/>
      [Diagram from the list above, or a simple relevant diagram —
       step by step while explaining]
    </div>

    [Weave CFU/CCQ blocks naturally through this section as concepts
     land — see CFU/CCQ NATURAL PLACEMENT above]
  </div>

  <div class="lp-section-activity">
    <h4>[22-30 min] Student Activity — {technique.get('activity_style', '')}</h4>
    <div class="lp-activity-block">
      <strong>Activity:</strong>
      <p>[Follow the ACTIVITY INSTRUCTION above, grounded in today's
         actual content — students active, not teacher-led]</p>
    </div>
  </div>

  <div class="lp-section-exam-prep">
    <h4>[30-33 min] Exam-Oriented Questions</h4>
    <p>[2-3 questions in the style this content typically appears in
       exams — short answer / diagram-based / ratio problem]</p>
  </div>

  <div class="lp-section-closing">
    <h4>[33-35 min] Closing</h4>
    {closing_instruction}
  </div>

</div>

═══════════════════════════════════════════════════════
FINAL CHECKS BEFORE FINISHING
═══════════════════════════════════════════════════════
✅ Day wrapper div has EXACTLY ONE id attribute: id="day-{day_num}" —
   do NOT add any other id (e.g. never both id="lp-day-{day_num}" AND
   id="day-{day_num}")
✅ Content matches TODAY'S CONTENT above — do not invent or borrow a
   different day's topic
✅ Every number/ratio used is from "Specific numbers/ratios" above —
   none invented or rounded
✅ Tamil appears in EXACTLY 3 places: key terms table, ONE main
   explanation mirror (even if today covers multiple sub-parts), opening
   question — nowhere else
✅ CFU/CCQ count follows content — not padded to hit a number
✅ Every cfu-block/ccq-block closes with </div> — never </p>
✅ Every lp-tamil-scaffold div closes with </div> before moving on
✅ {"Day is FINAL — embedded assessment present, NO homework, NO preview" if day_num == total_days else f"Homework present (2 tasks) and preview names Day {day_num + 1}'s focus"}
✅ Raw HTML only — start with <h3 class="lp-day-title">Day {day_num}
✅ Every <div> opened is closed with </div> — never with </p>
✅ Do NOT generate Day {day_num + 1}

Chapter Text (use ONLY this — no general knowledge):
---
{text}
---"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                system=BIO_LP_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            print(f"❌ [{self.discipline}] Day {day_num} error: {e}")
            return None


# ============================================================================
# BOTANY / ZOOLOGY BUILDERS
# ============================================================================

class BotanyLP1112Builder(_BiologyLP1112Base):
    discipline = "botany"


class ZoologyLP1112Builder(_BiologyLP1112Base):
    discipline = "zoology"


# ============================================================================
# Singleton instances — unchanged names, router/import path unaffected
# ============================================================================

botany_lp_1112_builder = BotanyLP1112Builder()
zoology_lp_1112_builder = ZoologyLP1112Builder()