"""
physics/base/__init__.py
------------------------
Shared constants and helpers for the Physics LP builder (grade_1112).

Imported by:
    physics/lp/grade_1112/physics.py   (PhysicsLP1112Builder)

DO NOT add API calls or builder classes here. This file holds ONLY:
    - prompt constants (system prompt + reusable instruction blocks)
    - pure helper functions (cleaning, validation, repair, JSON parsing)

DECOUPLING NOTE (team convention, Sept 2026):
Physics keeps its own copy of clean() and the instruction blocks instead of
importing from ss/base or biology/base. If clean() gets a bug fix elsewhere,
apply it here manually.

SOURCE OF TRUTH FOR TEACHING STYLE:
Manual LP "Class 12 Physics — Unit 1: Electrostatics" (21 days), used as a
content-agnostic TEMPLATE for every Class 11 and 12 Physics chapter.
Key choices taken from it (confirmed with nanba, Oct 2026):
    - Teaching cycle: familiar experience -> simple English -> Tamil ->
      scientific English -> board diagram / formula -> guided practice
    - CCQ = small closed question fired right after ONE idea
      CFU = whole-class check at the END of a block
      (NOTE: this is the reverse of Biology's definitions — intentional)
    - Tamil: one short code-mixed Tamil line per teaching block
      (not Biology's "exactly 3 places")
    - Every day ends with an Exit Ticket — no homework
    - Five-step numerical routine: Given -> Find -> Formula -> Substitute ->
      Answer with unit

WEB CONTRACT (from ai_converter._wrap_html + lesson-viewer.js):
    - Every day starts with EXACTLY  <div class="lp-day-block">
      (no other attributes — the wrapper injects id="lp-day-N" itself)
    - The day title lives INSIDE the day block (switchLPDay() only hides
      .lp-day-block / .assessment-block; anything outside shows on every tab)
    - One top-level  <div class="assessment-block">  AFTER the last day,
      never nested inside a day
    - Only classes that exist in content-styles.css (see ALLOWED_CLASSES)
    - No MathJax/KaTeX: formulae are plain HTML (<sup>, <sub>, Unicode)
    - Tables: maximum 3 columns (mobile squish bug is still open)

v1.0 — Oct 2026
"""

import json
import re
from html.parser import HTMLParser
from typing import List, Optional, Tuple


# ============================================================================
# MARKERS (backend searches for these to find chapters needing a re-run)
# ============================================================================

LP_DAY_FAILED_MARKER    = "<!-- LP_DAY_FAILED -->"
LP_DAY_TRUNCATED_MARKER = "<!-- LP_DAY_TRUNCATED -->"

DAY_BLOCK_OPEN        = '<div class="lp-day-block">'
ASSESSMENT_BLOCK_OPEN = '<div class="assessment-block">'


# ============================================================================
# CSS CLASSES THAT ARE ACTUALLY STYLED (content-styles.css + _wrap_html)
# Use ONLY these in prompts. Unstyled classes render as plain text.
# ============================================================================

ALLOWED_CLASSES = [
    # day structure
    "lp-day-block", "lp-day-title", "lp-day-meta",
    "lp-section-opening", "lp-section-intro", "lp-section-main",
    "lp-section-student-task", "lp-section-closing",
    "lp-section-label", "lp-time",
    # teacher script / Tamil
    "lp-teacher-says", "lp-tamil-scaffold",
    # checks (CSS added by Node team, Oct 2026)
    "cfu-block", "ccq-block", "cfu-wait-note", "ccq-tamil",
    # physics content boxes
    "formula-box", "board-work", "common-mistakes",
    # tables
    "vocab-block", "diff-block", "diff-table",
    # assessment
    "assessment-block",
]


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

PHYS_LP_SYSTEM_PROMPT = """You are an experienced Samacheer Kalvi Physics teacher for Class 11 and 12
with deep knowledge of the Tamil Nadu state board curriculum and of how
Tamil-medium-background students learn Physics in English.

Create a detailed, practical, script-by-script lesson plan so that even a
brand-new, inexperienced teacher can walk into class and deliver a confident,
effective 35-minute session just by following it.

═══════════════════════════════════════════════════════
TEACHING APPROACH — APPLY IN EVERY LESSON
═══════════════════════════════════════════════════════
- The physics stays at FULL Class 11/12 level. Nothing is watered down.
  What changes is the language and the route to each concept.
- Teaching cycle for every new idea:
  Familiar experience -> simple English -> Tamil explanation ->
  scientific English -> board diagram / formula -> guided practice
- Do not equate weak English with weak physics. A student who says
  "distance double... force quarter" already has the physics. Accept the
  physics first, then supply the exam-English sentence.
- Students may answer first in Tamil or broken English; the teacher then
  converts the answer into exam English.
- Build the idea BEFORE writing the equation. Never write a formula and say
  "memorise this" — ask what each symbol represents and which situation the
  formula answers.
- For vectors: decide direction / sign FIRST, magnitude second.
- For numericals: check and convert units FIRST, substitute second.
- Use everyday Tamil Nadu examples (a rubbed balloon, a ceiling fan, a bus in
  a storm, a mixie, a two-wheeler, a well pulley, a cricket ball).

THE TEACHER MUST NOT:
- Read the textbook aloud for long stretches
- Write a formula and say "memorise this"
- Start a numerical by substituting numbers before units and direction
- Rush a dense multi-part section into a few minutes
- Correct every English mistake while a student explains the physics

═══════════════════════════════════════════════════════
TIME BALANCE
═══════════════════════════════════════════════════════
- Teacher talk: at most about half of the 35 minutes
- Never more than 3 minutes of teacher monologue without a student response
  (a CCQ, a prediction, a pair check, a board turn, a calculation)

═══════════════════════════════════════════════════════
CONTENT ACCURACY — STRICTLY ENFORCE
═══════════════════════════════════════════════════════
- Teach ONLY the concepts, sections and facts in the chapter text provided.
  No outside topics, no general-knowledge additions.
- Textbook worked examples: use the textbook's numbers EXACTLY.
- Historical facts, dates, names, experimental values and data tables: ONLY
  if they appear in the chapter text. Never invent them.
- Standard physical constants (e, k = 1/4πε₀, ε₀, μ₀, g, G, c, h, mₑ) may be
  used at their standard textbook values.
- Teacher-made practice numericals (guided practice, CFU, exit ticket) may use
  simple realistic values chosen by you, but every answer you give MUST be
  calculated correctly with the correct unit.
- If a formula in the chapter text is garbled, blank or clearly broken by
  text extraction, you MAY write the standard textbook form of that formula,
  and you MUST add inside its formula-box:
  <p>⚠️ Reconstructed — verify with textbook</p>
- Never invent a formula that is not part of this chapter.

═══════════════════════════════════════════════════════
CRITICAL OUTPUT RULES
═══════════════════════════════════════════════════════
- ⚠️ ABSOLUTE RULE: NEVER output Japanese, Chinese, Korean or ANY CJK character.
- Tamil text: Tamil Unicode (U+0B80–U+0BFF) + English words + numbers + punctuation only.
- Output ONLY raw HTML body content. No <html>, <head>, <body>, <style>, <script>.
- NEVER wrap output in markdown code fences. NEVER use backticks.
- Start directly with an HTML tag — no explanation before or after the HTML.
- NO page numbers anywhere. Refer to content by section number and name
  (for example "1.2.1 Superposition principle").
- NO religious references in any example.
- NO specific student names — use "a student", "Student A", "a pair".
- NO markdown syntax inside HTML (no **bold**, no # headings, no - lists).

═══════════════════════════════════════════════════════
FORMULA FORMAT — PLAIN HTML ONLY (no math renderer on the platform)
═══════════════════════════════════════════════════════
- Use <sup> and <sub>:  r<sup>2</sup>,  q<sub>1</sub>,  10<sup>−19</sup>
- Use Unicode symbols directly: × ÷ − ± ≈ ∝ → ⟹ √ ∞ ° Δ λ θ ω φ Φ ε₀ μ₀ π ρ σ τ Ω
- Use the true minus sign (−) in exponents and negative values.
- Write fractions inline with / and brackets:  E = (1/4πε₀) × (2p/r<sup>3</sup>)
- Vectors: write the symbol in <strong> (for example <strong>F</strong>) and
  say "vector" in words when it matters.
- FORBIDDEN: LaTeX, $...$, \\frac, MathML, <math>, images of formulas,
  matrices, multi-line aligned equations.
- Every KEY formula of the day goes in its own formula-box:
  <div class="formula-box">
    <strong>Coulomb's law</strong>
    <p>F = k q<sub>1</sub>q<sub>2</sub> / r<sup>2</sup></p>
    <p>k = 1/4πε₀ ≈ 9 × 10<sup>9</sup> N m<sup>2</sup> C<sup>−2</sup></p>
  </div>

═══════════════════════════════════════════════════════
ALLOWED CSS CLASSES — USE ONLY THESE
═══════════════════════════════════════════════════════
lp-day-block, lp-day-title, lp-day-meta,
lp-section-opening, lp-section-intro, lp-section-main,
lp-section-student-task, lp-section-closing, lp-section-label, lp-time,
lp-teacher-says, lp-tamil-scaffold,
ccq-block, cfu-block, cfu-wait-note,
formula-box, board-work, common-mistakes,
vocab-block, diff-block, diff-table, assessment-block
Do NOT invent any other class name. Do NOT add id attributes. Do NOT add
inline style attributes.

TABLES: maximum 3 columns, always inside <div class="vocab-block"> (or
diff-block for the 3-level assessment table). Use <thead> and <tbody>.

═══════════════════════════════════════════════════════
⚠️ HTML DIV RULES — NEVER VIOLATE
═══════════════════════════════════════════════════════
- Every <div> you open MUST be closed with </div> — never with </p>.
- Close every lp-teacher-says, lp-tamil-scaffold, ccq-block, cfu-block,
  formula-box, board-work and common-mistakes div before starting the next
  element.
- Close each lp-section-* div before opening the next lp-section-* div.
- Never put a <div> inside a <p>.
- Before finishing: opened divs must equal closed divs.
"""


# ============================================================================
# PREAMBLE START INSTRUCTION
# ============================================================================

PREAMBLE_START_INSTRUCTION = """
CRITICAL OUTPUT RULE FOR PREAMBLE:
- Do NOT generate any <div class="sk-content-header"> block
- Do NOT generate any <h1> title block — the platform adds the page header
- Start your output DIRECTLY with <h2>Part 1: Chapter Overview</h2>
- First HTML tag must be <h2>
- Do NOT generate any Day blocks and do NOT use the class lp-day-block
- Do NOT use the class assessment-block

SECTION ORDER — STRICTLY FOLLOW:
Part 1: Chapter Overview          (3-column-max table)
Part 2: Learning Objectives       ← ALWAYS FIRST among objectives
Part 3: Value-Based Objectives
Part 4: Skill Objectives
Part 5: Day-wise Plan             (table: Day | Topic | Main outcome)
Part 6: Teaching Approach for This Chapter (incl. Do / Do Not lists)
Part 7: Teacher's Tamil Scaffolding Sheet (table: English | Simple English | Tamil support)
Part 8: Formula Wall              (table: Quantity / Law | Formula | SI unit)
Part 9: Teaching Aids             ← ALWAYS LAST
"""


# ============================================================================
# TAMIL SCAFFOLDING — code-mixed, one short line per teaching block
# ============================================================================

TAMIL_INSTRUCTION = """
═══════════════════════════════════════════════════════
TAMIL SCAFFOLDING RULES (Physics — code-mixed style)
═══════════════════════════════════════════════════════

WHERE Tamil appears:
✅ 1. OPENING — Tamil version of the opening / hook question
✅ 2. EVERY TEACHING BLOCK — ONE short Tamil line (1–2 sentences) that
      explains the block's key idea, placed right after the English
      explanation or the formula-box
✅ 3. KEY STATEMENTS that students commonly misunderstand may get their
      Tamil line inside the same block (still only one Tamil line per block)

WHERE Tamil must NOT appear:
❌ CCQ and CFU blocks
❌ Activity / pair-work instructions
❌ Exit ticket
❌ board-work and formula-box content
❌ Time labels, section labels, headings
❌ The assessment block

STYLE — CODE-MIXED, MEANING-BASED:
- Tamil script for the sentence; physics terms students will meet in the exam
  stay in English (Latin script) with a Tamil suffix where natural:
  "charge-ஐ", "field-ல்", "force-ன்", "dipole-க்கு".
- Translate the MEANING, never word-for-word.
- Short and spoken — how a Tamil Nadu teacher actually explains in class.

EXAMPLES (from the approved manual LP):
  English: Rubbing does not create charge; it transfers charge.
  Tamil:   Rubbing மூலம் charge புதிதாக உருவாகாது; charge ஒரு object-லிருந்து
           இன்னொரு object-க்கு transfer ஆகிறது.

  English: Distance increases, force decreases — as the square of distance.
  Tamil:   Distance அதிகமானால் force குறையும் — ஆனால் distance SQUARE ஆக
           பயன்படுத்தப்படுகிறது என்பதை மறக்காதீர்கள்.

  English: Battery disconnected -> Q constant. Battery connected -> V constant.
  Tamil:   Battery துண்டிக்கப்பட்டால் Q மாறாது. Battery இணைக்கப்பட்டே இருந்தால் V மாறாது.

MARKUP — use exactly this:
<div class="lp-tamil-scaffold">
  <strong>தமிழில்:</strong> [one or two code-mixed Tamil sentences]
</div>

QUALITY RULES:
- Grammatically correct Tamil; standard Tamil Unicode spelling
- No word repetition within the line
- NO Hindi words. NO whole sentences in Latin-script Tanglish.
- NO CJK characters — ever
- If unsure of a Tamil word, keep the English term — never guess
═══════════════════════════════════════════════════════
"""


# ============================================================================
# CCQ / CFU — manual LP definitions (reverse of Biology — intentional)
# ============================================================================

CCQ_CFU_INSTRUCTION = """
═══════════════════════════════════════════════════════
CCQ AND CFU — THEY ARE DIFFERENT. USE BOTH CORRECTLY.
═══════════════════════════════════════════════════════

CCQ — Concept Checking Question
- Fired the INSTANT one new term or idea has been taught, before moving on.
- Small, closed, ONE right answer. Best form: "X or Y?"
- Deliberately avoids reusing the word just defined — it checks the concept,
  not vocabulary recall.
  ✅ "If distance doubles, does force become half?"   (No — one-fourth)
  ❌ "What does Coulomb's law say?"
- 1–3 CCQs per teaching block. If a CCQ fails, the teacher re-explains that
  one idea immediately.

CCQ MARKUP — exactly this:
<div class="ccq-block">
  <div class="lp-teacher-says">
    <strong>CCQ:</strong> "[closed question]"<br/>
    <strong>Answer:</strong> "[short correct answer]"
  </div>
  <p class="cfu-wait-note">If wrong: re-explain this one idea now.</p>
</div>

CFU — Check for Understanding
- Fired at the END of a whole block, before the class moves on.
- Broader than a CCQ: students apply, predict, rank, classify, reconstruct or
  calculate using what the block covered.
- Checks the WHOLE CLASS, not one student. Methods: cold-call 2–3 students,
  thumbs up/down, show of hands, pairs check in 60 seconds, mini-whiteboard /
  notebook answer held up, unaided 60-second recall, a student explains on the
  board.
- EXACTLY ONE CFU at the end of every teaching block (opening and closing
  blocks included).

CFU MARKUP — exactly this:
<div class="cfu-block">
  <div class="lp-teacher-says">
    <strong>CFU:</strong> [method + exact task, e.g. "Pairs rank points P, Q, R
    by field strength in 60 seconds, then 2 pairs share."]<br/>
    <strong>Look for:</strong> [what a correct response looks like]
  </div>
  <p class="cfu-wait-note">Decide: move on, or re-teach this block.</p>
</div>

❌ NEVER use instruction-check questions ("Do you understand?",
   "How many lines should you write?")
❌ No Tamil inside CCQ or CFU blocks
═══════════════════════════════════════════════════════
"""


# ============================================================================
# NUMERICALS, DERIVATIONS, COMMON MISTAKES
# ============================================================================

NUMERICAL_ROUTINE_INSTRUCTION = """
═══════════════════════════════════════════════════════
NUMERICAL ROUTINE — FIVE STEPS, EVERY TIME
═══════════════════════════════════════════════════════
Given -> Find -> Formula -> Substitute -> Answer with unit
- Convert units BEFORE substituting (μC -> C, cm -> m, mm -> m, g -> kg).
- For vector quantities, decide direction / sign BEFORE magnitude.
- The teacher models the routine aloud; later in the day students do it.

WORKED EXAMPLE MARKUP:
<div class="board-work">
  <strong>Worked Example:</strong> [problem statement]<br/>
  Given: [quantities with units, converted to SI]<br/>
  Find: [unknown]<br/>
  Formula: [formula]<br/>
  Substitute: [numbers in]<br/>
  Answer: [value with unit]
</div>

ERROR HUNT (use on numerical days when it fits):
Put a deliberately wrong solution on the board (forgot to square r, forgot
μC -> C, wrong sign, wrong unit). Students find and explain the mistake.
═══════════════════════════════════════════════════════
"""

DERIVATION_INSTRUCTION = """
═══════════════════════════════════════════════════════
DERIVATIONS — STEP BY STEP, WITH REASONS
═══════════════════════════════════════════════════════
- Build the physical picture first (diagram on board), then derive.
- Write each step on its own line inside ONE board-work div, numbered.
- After the board-work, the teacher script explains WHY each step follows
  (one short reason per step), in simple English.
- Put the final result in a formula-box.
- Tell students when a derivation is a likely 2-, 3- or 5-mark exam question.
- Follow the chapter text's own derivation route and symbols. Do not swap in
  a different method.

DERIVATION MARKUP:
<div class="board-work">
  <strong>Derivation: [name]</strong><br/>
  Step 1: [line]<br/>
  Step 2: [line]<br/>
  ...<br/>
  Result: [final expression]
</div>
═══════════════════════════════════════════════════════
"""

COMMON_MISTAKES_INSTRUCTION = """
═══════════════════════════════════════════════════════
COMMON MISTAKES — AT LEAST ONE PER DAY
═══════════════════════════════════════════════════════
Name the specific misconception students make with today's content
(e.g. "distance doubles -> force is ¼, NOT ½", "dipole moment points from
− to +, not + to −", "V and U are not the same quantity").

MARKUP:
<div class="common-mistakes">
  <strong>⚠️ Common mistake:</strong>
  <p>[the mistake] — [the correct idea]</p>
</div>
═══════════════════════════════════════════════════════
"""


# ============================================================================
# HELPER — clean raw AI output
# ============================================================================

_CJK_RE = re.compile(
    "["
    "぀-ヿ"   # Hiragana, Katakana
    "㐀-䶿"   # CJK Ext A
    "一-鿿"   # CJK Unified
    "가-힯"   # Hangul syllables
    "ᄀ-ᇿ"   # Hangul Jamo
    "豈-﫿"   # CJK compatibility
    "＀-￯"   # Half/full-width forms
    "]+"
)


def strip_cjk(text: str) -> Tuple[str, int]:
    """Remove any CJK characters. Returns (clean_text, number_removed)."""
    if not text:
        return text, 0
    removed = sum(len(m) for m in _CJK_RE.findall(text))
    return (_CJK_RE.sub("", text), removed) if removed else (text, 0)


def clean(raw: str) -> str:
    """
    Strip markdown fences, <style>/<script> blocks, leading non-HTML preamble
    and CJK characters from raw Claude output, then let BeautifulSoup repair
    unclosed non-div tags.

    Div structure is NOT trusted to BeautifulSoup alone — run
    normalize_day_html() / normalize_assessment_html() afterwards.
    """
    if not raw:
        return raw

    text = raw.strip()

    # Markdown code fences
    text = re.sub(r"```(?:html|HTML)?", "", text).strip()

    # Style / script blocks and document-level tags
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"</?(?:html|head|body)\b[^>]*>", "", text, flags=re.IGNORECASE)

    # Leading prose before the first tag
    first_tag = re.search(r"<(?:div|h[1-6]|section|p|table|ul|ol)\b", text)
    if first_tag and first_tag.start() > 0:
        preamble = text[: first_tag.start()].strip()
        if preamble and not preamble.startswith("<"):
            text = text[first_tag.start():]

    # Trailing prose after the last closing tag ("Let me know if...")
    last_close = None
    for m in re.finditer(r"</[a-zA-Z0-9]+\s*>|<!--.*?-->", text, flags=re.DOTALL):
        last_close = m
    if last_close:
        tail = text[last_close.end():].strip()
        if tail and "<" not in tail:
            text = text[: last_close.end()]

    # CJK safety net
    text, n_cjk = strip_cjk(text)
    if n_cjk:
        print(f"      ⚠️ [Physics LP] Removed {n_cjk} CJK character(s) from output")

    # Repair unclosed inline/table tags (keeps attribute order and class text)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    text = str(soup)

    return text.strip()


# ============================================================================
# HELPER — div balancing (comment-aware)
# ============================================================================

_DIV_TOKEN_RE = re.compile(
    r"(<!--.*?-->)|(<div\b[^>]*>)|(</div\s*>)",
    flags=re.DOTALL | re.IGNORECASE,
)


def balance_divs(fragment: str) -> str:
    """
    Make a fragment's <div> structure balanced:
      - drops surplus </div> that would close something outside the fragment
      - appends missing </div> at the end
    HTML comments are ignored (markers can contain arbitrary text).
    """
    if not fragment:
        return fragment

    out = []
    depth = 0
    pos = 0
    dropped = 0
    for m in _DIV_TOKEN_RE.finditer(fragment):
        out.append(fragment[pos:m.start()])
        pos = m.end()
        if m.group(1):                 # comment
            out.append(m.group(1))
        elif m.group(2):               # <div ...>
            depth += 1
            out.append(m.group(2))
        else:                          # </div>
            if depth == 0:
                dropped += 1           # surplus close — drop it
                continue
            depth -= 1
            out.append(m.group(3))
    out.append(fragment[pos:])
    result = "".join(out)

    if depth > 0:
        result += "</div>" * depth
    if dropped or depth:
        print(f"      ⚠️ [Physics LP] Div repair: dropped {dropped} stray </div>, "
              f"added {depth} missing </div>")
    return result


def _matching_close_index(html: str, open_end: int) -> Optional[Tuple[int, int]]:
    """
    Given the end index of an opening <div ...>, return (start, end) of the
    </div> that closes it, or None if it never closes.
    """
    depth = 1
    for m in _DIV_TOKEN_RE.finditer(html, open_end):
        if m.group(1):
            continue
        if m.group(2):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return m.start(), m.end()
    return None


# ============================================================================
# HELPER — make a day / assessment fragment match the web contract exactly
# ============================================================================

_DAY_OPEN_RE = re.compile(
    r"""<div\b[^>]*\bclass\s*=\s*["'][^"']*\blp-day-block\b[^"']*["'][^>]*>""",
    flags=re.IGNORECASE,
)
_ASSESS_OPEN_RE = re.compile(
    r"""<div\b[^>]*\bclass\s*=\s*["'][^"']*\bassessment-block\b[^"']*["'][^>]*>""",
    flags=re.IGNORECASE,
)


def _wrap_single_block(html: str, open_re: re.Pattern, exact_open: str,
                       label: str) -> str:
    """
    Shared logic: guarantee the fragment is exactly ONE wrapper div opened
    with `exact_open`, with all content inside it.
      - content before the wrapper is moved inside (after the opening tag)
      - extra wrapper openings are demoted to plain <div>
      - content after the wrapper closes is moved inside
    """
    html = (html or "").strip()
    matches = list(open_re.finditer(html))

    if not matches:
        print(f"      ⚠️ [Physics LP] No {label} wrapper found — wrapping output")
        return exact_open + "\n" + balance_divs(html) + "\n</div>"

    # Demote extra openings (each would create an extra tab / block)
    if len(matches) > 1:
        print(f"      ⚠️ [Physics LP] {len(matches) - 1} extra {label} opening(s) "
              f"demoted to plain <div>")
        first = matches[0]
        head, tail = html[: first.end()], html[first.end():]
        tail = open_re.sub("<div>", tail)
        html = head + tail
        matches = [first]

    first = matches[0]
    prefix = html[: first.start()].strip()
    body = html[first.end():]

    # Balance everything after the opening, treating the wrapper as open
    inner_and_after = balance_divs(exact_open + body)[len(exact_open):]
    full = exact_open + inner_and_after

    close = _matching_close_index(full, len(exact_open))
    if close is None:                      # cannot happen after balancing
        full += "</div>"
        close = (len(full) - 6, len(full))

    inner = full[len(exact_open): close[0]]
    suffix = full[close[1]:].strip()

    if prefix:
        inner = "\n" + prefix + "\n" + inner
    if suffix:
        inner = inner + "\n" + suffix + "\n"

    return exact_open + inner + "</div>"


def normalize_day_html(html: str) -> str:
    """
    Enforce the day-block web contract on ONE generated day:
      - exactly one opening, written exactly as <div class="lp-day-block">
      - day title and everything else inside it
      - no 'assessment-block' anywhere inside a day
      - balanced divs
    """
    html = re.sub(r"\bassessment-block\b", "lp-section-closing", html or "")
    return _wrap_single_block(html, _DAY_OPEN_RE, DAY_BLOCK_OPEN, "lp-day-block")


def normalize_assessment_html(html: str) -> str:
    """
    Enforce the assessment web contract:
      - exactly one top-level <div class="assessment-block">
      - no lp-day-block inside it (would add a phantom day tab)
      - balanced divs
    """
    html = _DAY_OPEN_RE.sub("<div>", html or "")
    return _wrap_single_block(html, _ASSESS_OPEN_RE, ASSESSMENT_BLOCK_OPEN,
                              "assessment-block")


def normalize_preamble_html(html: str) -> str:
    """Preamble must contain no day or assessment wrappers, and balanced divs."""
    html = _DAY_OPEN_RE.sub("<div>", html or "")
    html = _ASSESS_OPEN_RE.sub("<div>", html)
    return balance_divs(html)


# ============================================================================
# HELPER — structural checks (used to decide on a retry)
# ============================================================================

_REQUIRED_DAY_PARTS = [
    ("lp-section-opening",      "opening section"),
    ("lp-section-intro",        "introduction section"),
    ("lp-section-main",         "main teaching section"),
    ("lp-section-student-task", "student task section"),
    ("lp-section-closing",      "closing section"),
    ("ccq-block",               "at least one CCQ"),
    ("cfu-block",               "at least one CFU"),
    ("lp-tamil-scaffold",       "Tamil scaffolding"),
]


def check_day_structure(html: str, is_revision_day: bool = False) -> List[str]:
    """
    Return a list of problems found in a normalized day fragment.
    Empty list = structurally fine.
    """
    problems = []
    if not html:
        return ["empty output"]

    if html.count(DAY_BLOCK_OPEN) != 1:
        problems.append(f"expected 1 day opening, found {html.count(DAY_BLOCK_OPEN)}")

    required = _REQUIRED_DAY_PARTS
    if is_revision_day:
        # Revision day keeps the 5 sections and CFUs; CCQ/Tamil optional
        required = [p for p in _REQUIRED_DAY_PARTS
                    if p[0] not in ("ccq-block", "lp-tamil-scaffold")]

    for cls, label in required:
        if cls not in html:
            problems.append(f"missing {label} ({cls})")

    if not re.search(r"exit\s*ticket", html, re.IGNORECASE):
        problems.append("missing exit ticket")

    timing = check_time_labels(html)
    if timing:
        problems.append(timing)

    if re.search(r"\$[^$\n]{1,80}\$|\\frac|<math\b", html):
        problems.append("LaTeX / MathML found — formulas must be plain HTML")

    return problems


def check_time_labels(html: str) -> Optional[str]:
    """
    Time labels must run 0 → 35 contiguously, in order.
    Returns a problem string, or None when the sequence is clean.
    (Minor problem — logged, does not trigger a retry.)
    """
    ranges = [(int(a), int(b)) for a, b in re.findall(
        r'class="lp-time">\s*(\d+)\s*[–—-]\s*(\d+)', html or "")]
    if not ranges:
        return None
    issues = []
    if ranges[0][0] != 0:
        issues.append(f"starts at {ranges[0][0]}")
    if ranges[-1][1] != 35:
        issues.append(f"ends at {ranges[-1][1]}")
    for (a1, b1), (a2, b2) in zip(ranges, ranges[1:]):
        if a2 != b1:
            issues.append(f"{a1}–{b1} then {a2}–{b2}")
    return ("time labels not contiguous (" + "; ".join(issues[:4]) + ")") if issues else None


def is_critical(problems: List[str]) -> bool:
    """Problems serious enough to justify one retry of the day call."""
    critical_words = ("empty output", "expected 1 day opening",
                      "closing section", "main teaching section",
                      "missing exit ticket")
    return any(any(w in p for w in critical_words) for p in problems)


def count_day_blocks(html: str) -> int:
    """Number of day tabs the web wrapper will create."""
    return (html or "").count('<div class="lp-day-block"')


def count_assessment_blocks(html: str) -> int:
    return (html or "").count('<div class="assessment-block"')


# ============================================================================
# HELPER — placeholders / markers
# ============================================================================

def failed_day_block(day_num: int, total_days: int, title: str = "",
                     reason: str = "") -> str:
    """
    Visible placeholder that keeps tab numbering correct when a day fails.
    Contains LP_DAY_FAILED_MARKER so the backend can find and re-run it.
    """
    safe_title = re.sub(r"[<>]", "", title or "")
    safe_reason = re.sub(r"[<>]", "", reason or "generation error")
    return (
        f"{DAY_BLOCK_OPEN}\n"
        f"{LP_DAY_FAILED_MARKER}\n"
        f'<h3 class="lp-day-title">Day {day_num} of {total_days}'
        f'{" — " + safe_title if safe_title else ""}</h3>\n'
        f'<div class="common-mistakes">\n'
        f"  <strong>⚠️ This day could not be generated.</strong>\n"
        f"  <p>Please regenerate this lesson plan. ({safe_reason})</p>\n"
        f"</div>\n"
        f"</div>"
    )


def mark_truncated(day_html: str) -> str:
    """Insert the truncation marker just inside the day block."""
    if LP_DAY_TRUNCATED_MARKER in day_html:
        return day_html
    if day_html.startswith(DAY_BLOCK_OPEN):
        return (DAY_BLOCK_OPEN + "\n" + LP_DAY_TRUNCATED_MARKER
                + day_html[len(DAY_BLOCK_OPEN):])
    return LP_DAY_TRUNCATED_MARKER + "\n" + day_html


# ============================================================================
# HELPER — JSON parsing for Call 0a / 0b
# ============================================================================

def parse_json_response(raw: str) -> dict:
    """
    Parse a JSON object from model output. Strips code fences and any prose
    around the outermost {...}. Raises json.JSONDecodeError on failure.
    """
    if raw is None:
        raise json.JSONDecodeError("empty response", "", 0)
    text = re.sub(r"```(?:json|JSON)?", "", raw).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise json.JSONDecodeError("no JSON object found", text, 0)
    text = text[start: end + 1]
    # Strip CJK defensively (can appear in tamil fields)
    text, _ = strip_cjk(text)
    return json.loads(text)


# ============================================================================
# HELPER — chapter title
# ============================================================================

_SMALL_WORD_SUFFIXES = ("and", "of")


def get_display_title(metadata: dict) -> str:
    """
    Prefer metadata['display_title'] (added by backend, Oct 2026).
    Fallback: parse the filename-style lesson_title, e.g.
      "Class11-physics-1-NatureofPhysicalWorldandMeasurement"
      -> "Nature of Physical World and Measurement"
    """
    title = (metadata or {}).get("display_title")
    if title and str(title).strip():
        return str(title).strip()

    raw = str((metadata or {}).get("lesson_title", "") or "").strip()
    if not raw:
        return "Physics Chapter"

    parts = raw.split("-")
    if len(parts) >= 4 and parts[0].lower().startswith("class"):
        raw = "-".join(parts[3:])

    words = re.findall(r"[A-Z][a-z]*|[a-z]+|\d+", raw) or [raw]
    fixed = []
    for w in words:
        split_done = False
        for suf in _SMALL_WORD_SUFFIXES:
            if len(w) > len(suf) + 2 and w.endswith(suf) and w[0].isupper():
                fixed.extend([w[: -len(suf)], suf])
                split_done = True
                break
        if not split_done:
            fixed.append(w)
    return " ".join(fixed).strip() or "Physics Chapter"