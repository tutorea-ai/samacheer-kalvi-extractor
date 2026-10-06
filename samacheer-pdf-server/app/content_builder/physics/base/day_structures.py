"""
physics/base/day_structures.py
------------------------------
Data-only file: the fixed PEDAGOGICAL pattern for Physics LP (Class 11 & 12)
— content-agnostic, same for every chapter.

Derived from the manual LP "Class 12 Physics — Unit 1: Electrostatics"
(21 days). That LP is a TEACHING TEMPLATE for every Physics chapter, not a
script for Electrostatics. Nothing in this file names an Electrostatics topic.

HOW PHYSICS DIFFERS FROM BIOLOGY'S day_structures.py
  - Day count is NOT fixed. The Day Allocator (Call 0b) decides it from the
    chapter's own numbered subsections, within PHYSICS_STRUCTURE_META bounds.
  - Technique is chosen by DAY TYPE, not by day number. The manual picks its
    hooks and activities from what the day is teaching (a concept, a formula
    with numericals, a derivation, a step-by-step process, a comparison, a
    real-world application). Rotating by day number would give a derivation
    day a "pair sort" just because it happened to be Day 5.
  - Variety inside a type: the n-th day of the same type uses option n of that
    type's lists (see get_day_strategy), so two consecutive numerical days do
    not open and practise the same way.
  - The last day is always revision (PHYSICS_REVISION_DAY_STRATEGY), followed
    by a separate top-level Assessment block (PHYSICS_ASSESSMENT_STRUCTURE).

What is fixed for every chapter:
  - 35-minute day, default block timing (PHYSICS_DEFAULT_TIMING), resizable
  - 5 styled sections per day: opening / intro / main / student-task / closing
  - CCQ after each idea, one CFU at the end of each block
  - One code-mixed Tamil line per teaching block
  - Five-step numerical routine on every numerical day
  - Exit ticket every day (no homework)

What is NOT fixed (decided per chapter by Call 0a + Call 0b):
  - total number of days
  - which subsections land on which day
  - each day's type
"""

from typing import Dict, Tuple


# ============================================================================
# DEFAULT 35-MINUTE TIMING (manual LP "Recommended recurring structure")
# Each row maps to one styled lp-section-* wrapper. Boundaries may move when
# a day needs more board time — the total must stay 35 minutes, contiguous.
# ============================================================================

PHYSICS_DEFAULT_TIMING = [
    # (section class,             default time, purpose)
    ("lp-section-opening",      "0–5 min",   "Recall yesterday / hook / prediction"),
    ("lp-section-intro",        "5–13 min",  "Explain today's concept with Tamil scaffolding"),
    ("lp-section-main",         "13–23 min", "Board diagram / formula / worked example / derivation"),
    ("lp-section-student-task", "23–30 min", "Student activity / guided numerical / pair work"),
    ("lp-section-closing",      "30–35 min", "CFU / exam-oriented question + exit ticket"),
]


# ============================================================================
# DAY TYPES — the allocator tags every content day with exactly one of these
# ============================================================================

PHYSICS_DAY_TYPES: Dict[str, Dict] = {

    # ------------------------------------------------------------------
    "concept": {
        "label": "Concept",
        "allocator_hint": (
            "Mainly definitions, properties, qualitative ideas, rules or laws "
            "explained in words (little or no calculation)."
        ),
        "opening_options": [
            ("Familiar experience question",
             "Ask about an everyday experience connected to today's idea "
             "(something students have seen, felt or done). Let 3-4 students "
             "answer from experience BEFORE naming the physics."),
            ("Prediction by show of hands",
             "Pose a yes/no or this-or-that prediction about today's idea. "
             "Take a show of hands, record the class prediction on the board, "
             "and promise to check it later in the lesson."),
            ("Invisible-but-measurable analogy",
             "Use an analogy for something students cannot see directly but "
             "can see the effect of (like wind moving leaves). Ask for one more "
             "example of their own before linking it to today's quantity."),
            ("Recall + 'what if' question",
             "Recall yesterday's key idea in one minute, then ask a 'what if' "
             "question that yesterday's idea cannot answer alone — today's "
             "lesson answers it."),
        ],
        "main_focus": (
            "Build the idea from the familiar experience -> simple English -> "
            "Tamil line -> scientific English. Put each key statement or rule "
            "in a formula-box (even if it is a statement, not an equation). "
            "Draw a labelled board diagram for every concept that can be drawn. "
            "Fire a CCQ immediately after each new term."
        ),
        "activity_options": [
            ("Pair predict",
             "Give pairs 3-4 short situations from today's content; they predict "
             "the outcome (e.g. attract/repel, increase/decrease, yes/no) in "
             "their notebooks, then the teacher cold-calls pairs before revealing."),
            ("Classify / sort",
             "Give 4-6 examples or statements from today's content; pairs sort "
             "them into two or three categories taught today, with a one-line "
             "reason for one item."),
            ("True / false thumbs",
             "Read 4 statements one at a time (mix of true and common-wrong); "
             "whole class shows thumbs up/down before each reveal; teacher "
             "corrects each misconception immediately."),
            ("Diagram labelling",
             "Students draw today's key diagram from memory and label every "
             "part / direction taught today; teacher checks 2-3 notebooks aloud."),
        ],
        "exit_ticket_style": "2 fill-in-the-blank statements + 1 'true or false, and why?'",
    },

    # ------------------------------------------------------------------
    "formula_numerical": {
        "label": "Formula + Numerical",
        "allocator_hint": (
            "Introduces or applies a law/formula and has solved examples or "
            "clear numerical use (how a quantity scales, calculations)."
        ),
        "opening_options": [
            ("Prediction before the law",
             "Ask students to predict how one quantity changes when another "
             "changes (stronger or weaker? bigger or smaller?). Record the "
             "prediction; confirm it once the formula is built."),
            ("One-minute formula recall",
             "Revisit yesterday's formula for one minute: students say what "
             "each symbol means (not just the letters), then bridge to today."),
            ("Real-life quantity hook",
             "Start from a real situation where today's quantity matters and "
             "ask 'how much?' or 'how big?' — the formula is the tool to answer it."),
        ],
        "main_focus": (
            "Build the proportionality in words first, THEN write the formula "
            "in a formula-box with every symbol and SI unit named. Show how the "
            "result changes when each variable doubles / triples / halves "
            "(a short list on the board). Model ONE worked example with the "
            "five-step routine (Given -> Find -> Formula -> Substitute -> "
            "Answer with unit), converting units first. Use the textbook's own "
            "solved example where one exists, with its exact numbers."
        ),
        "activity_options": [
            ("Guided numerical in pairs",
             "Pairs solve one similar numerical using the five-step routine "
             "written on the board as a checklist. One pair narrates its "
             "solution aloud; the class checks each step."),
            ("Error hunt",
             "Put a deliberately wrong solution on the board (forgot to square, "
             "forgot unit conversion, wrong sign or wrong unit). Pairs find the "
             "exact mistake and explain why it is wrong."),
            ("Scaling table",
             "Students complete a 3-column table: Change made | New value as a "
             "fraction of old | Reason — for 3-4 changes (×2, ×3, ÷2 ...)."),
            ("Rank the cases",
             "Give 3 cases (P, Q, R) with different values; students rank them "
             "from largest to smallest result WITHOUT full calculation, using "
             "the formula's proportionality, then verify one by calculation."),
        ],
        "exit_ticket_style": "1 'what happens if X doubles?' + 1 short calculation with unit",
    },

    # ------------------------------------------------------------------
    "derivation": {
        "label": "Derivation",
        "allocator_hint": (
            "Contains a derivation or proof the textbook works through "
            "(an expression derived step by step)."
        ),
        "opening_options": [
            ("Recall the starting result",
             "Ask students to recall the formula or law today's derivation "
             "starts from (and what each symbol means). Write it at the top of "
             "the board — it is Step 0."),
            ("Why should this be true?",
             "State today's final result as a claim and ask: 'Why should this "
             "be true? What would we need to prove it?' Collect 2-3 ideas "
             "before deriving."),
            ("Picture first",
             "Draw the physical set-up of today's derivation on the board and "
             "ask students to mark directions / distances / angles they think "
             "will matter."),
        ],
        "main_focus": (
            "Draw and label the diagram first. Derive in numbered steps inside "
            "ONE board-work block, following the textbook's own route and "
            "symbols. After the board-work, the teacher script gives a one-line "
            "reason for every step. Put the final result in a formula-box and "
            "state the exam weightage (2, 3 or 5 marks) if it is a common "
            "derivation question. Fire a CCQ after each tricky step."
        ),
        "activity_options": [
            ("Step-card ordering",
             "Write the derivation's key steps on separate cards (or numbered "
             "lines in jumbled order on the board); pairs put them back in the "
             "correct order and justify one transition."),
            ("Fill the missing step",
             "Rewrite the derivation on the board with one or two steps blanked "
             "out; students fill them in individually, then compare in pairs."),
            ("Student explains a step",
             "Two students come to the board; each explains one step of the "
             "derivation in their own words (Tamil or English allowed first, "
             "then teacher supplies the exam sentence)."),
        ],
        "exit_ticket_style": "Write the final result + the reason for one key step",
    },

    # ------------------------------------------------------------------
    "process_sequence": {
        "label": "Process / Working",
        "allocator_hint": (
            "Describes a step-by-step process or the working of a device / "
            "method (an ordered sequence of stages)."
        ),
        "opening_options": [
            ("Can we do it without...?",
             "Ask a provocative 'can we do X without Y?' question about today's "
             "process (e.g. charge without touching, measure without seeing). "
             "Take guesses before teaching."),
            ("Mystery outcome",
             "Describe only the final outcome of today's process and ask "
             "students how it might have happened — today reveals the steps."),
        ],
        "main_focus": (
            "Teach the process as numbered stages in ONE board-work block "
            "(stage -> what happens -> why). Draw a labelled diagram of the "
            "set-up / device. After each stage, a CCQ on what changed and what "
            "did not. State the exact exam wording for the process's purpose "
            "or principle."
        ),
        "activity_options": [
            ("Step-card ordering",
             "Shuffled stage cards (or jumbled numbered lines on the board); "
             "pairs restore the correct order, then one pair narrates the full "
             "sequence aloud."),
            ("Narrate the process",
             "One student narrates the whole process from a diagram they draw "
             "themselves; the class follows and corrects any skipped stage."),
            ("Arrow flow-chart",
             "Students draw the process as a flow-chart (stage -> stage) in "
             "their notebooks from memory; teacher checks 2-3 aloud."),
        ],
        "exit_ticket_style": "List the stages in order + one 'why does this stage matter?'",
    },

    # ------------------------------------------------------------------
    "comparison": {
        "label": "Comparison",
        "allocator_hint": (
            "Centres on two or more look-alike quantities, cases or "
            "arrangements that students confuse and must distinguish."
        ),
        "opening_options": [
            ("Are these the same?",
             "Put the two look-alike terms on the board and ask directly: "
             "'Are these the same quantity?' Take a show of hands before teaching."),
            ("Which is which?",
             "Give two contrasting real examples and ask students which "
             "belongs to which case before naming the difference."),
        ],
        "main_focus": (
            "Teach each side clearly, then build a comparison table on the "
            "board (max 3 columns: Feature | Case A | Case B) inside a "
            "vocab-block. Name the single most common confusion in a "
            "common-mistakes box. CCQs should be 'A or B?' questions."
        ),
        "activity_options": [
            ("Comparison table from memory",
             "Students copy and complete the comparison table from memory "
             "before checking it against the board."),
            ("Sort the statements",
             "Give 4-6 statements; pairs decide whether each describes case A, "
             "case B or both."),
            ("Which case applies?",
             "Give 3 short situations; students decide which case applies to "
             "each and what stays constant / changes."),
        ],
        "exit_ticket_style": "One-sentence difference + one 'which case is this?' situation",
    },

    # ------------------------------------------------------------------
    "application": {
        "label": "Application",
        "allocator_hint": (
            "Mostly real-world devices, uses, phenomena or applications of "
            "earlier ideas (the textbook's applications sections)."
        ),
        "opening_options": [
            ("Everyday device hook",
             "Start from a device or event students know (a ceiling fan, a bus "
             "in a storm, a camera flash, a mobile charger) and ask why it "
             "works the way it does."),
            ("Safety question",
             "Pose a real safety question connected to today's application "
             "('why is it safer to...?') and let students reason before teaching."),
        ],
        "main_focus": (
            "Connect each application back to the specific principle from "
            "earlier days (name the day's idea it uses). Describe the working "
            "with a labelled board diagram. Use ONLY facts and numbers that "
            "appear in the chapter text. State the exact exam wording for "
            "the application's purpose."
        ),
        "activity_options": [
            ("Name the principle",
             "Give 3-4 applications; pairs name the physics principle each one "
             "uses and say it in one sentence."),
            ("Cold-call chain",
             "Cold-call students one after another, each naming a different "
             "application or a different stage of the device, without repeating."),
            ("Explain-why scenario",
             "Give one real scenario; pairs write a 2-3 sentence explanation "
             "using today's principle, then 2 pairs read theirs aloud."),
        ],
        "exit_ticket_style": "Name one application + the principle it uses",
    },
}

# Accept a few likely spellings from the allocator
DAY_TYPE_ALIASES = {
    "formula": "formula_numerical",
    "numerical": "formula_numerical",
    "formula+numerical": "formula_numerical",
    "formula_and_numerical": "formula_numerical",
    "process": "process_sequence",
    "sequence": "process_sequence",
    "working": "process_sequence",
    "compare": "comparison",
    "applications": "application",
    "definition": "concept",
    "conceptual": "concept",
    "proof": "derivation",
}

DEFAULT_DAY_TYPE = "concept"


def normalize_day_type(value: str) -> str:
    """Map an allocator-supplied day type to a known key (default: concept)."""
    key = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key in PHYSICS_DAY_TYPES:
        return key
    return DAY_TYPE_ALIASES.get(key, DEFAULT_DAY_TYPE)


def get_day_strategy(day_type: str, occurrence: int) -> Dict[str, str]:
    """
    Return the technique for a content day.

    day_type   : one of PHYSICS_DAY_TYPES (normalized first)
    occurrence : 0 for the first day of this type in the chapter, 1 for the
                 second, ... — rotates through each option list so repeated
                 day types do not repeat the same hook / activity.
    """
    key = normalize_day_type(day_type)
    t = PHYSICS_DAY_TYPES[key]
    o_name, o_instr = t["opening_options"][occurrence % len(t["opening_options"])]
    a_name, a_instr = t["activity_options"][occurrence % len(t["activity_options"])]
    return {
        "day_type": key,
        "day_type_label": t["label"],
        "opening_style": o_name,
        "opening_instruction": o_instr,
        "main_focus": t["main_focus"],
        "activity_style": a_name,
        "activity_instruction": a_instr,
        "exit_ticket_style": t["exit_ticket_style"],
    }


# ============================================================================
# LAST DAY — whole-chapter revision (no new content), then the separate
# top-level Assessment block. Mirrors the manual LP's final day.
# ============================================================================

PHYSICS_REVISION_DAY_STRATEGY = {
    "title": "Whole-Chapter Revision + Exam Practice",
    "blocks": [
        ("lp-section-opening", "0–7 min", "Formula Recall Race",
         "Teacher writes only the NAMES of the chapter's key formulae / laws on "
         "the board; students write each matching formula from memory. Score "
         "it as a class (how many did most students get right?)."),
        ("lp-section-intro", "7–14 min", "Classify the quantities",
         "Students sort the chapter's quantities into two columns using a "
         "classification that fits THIS chapter (vector / scalar is the "
         "default; use fundamental / derived, or another chapter-relevant "
         "split if that fits better). Reveal together; students self-correct."),
        ("lp-section-main", "14–21 min", "\"Which formula?\" — situation-based",
         "Give 4-5 real exam-style SITUATIONS (not formula names); for each, "
         "a different student names the formula or principle that answers it "
         "and why. This is more exam-realistic than reciting equations."),
        ("lp-section-student-task", "21–30 min", "Numerical practice with step marking",
         "Students solve 1-2 numericals from across the chapter independently. "
         "Mark each step separately: formula ✓, unit conversion ✓, "
         "substitution ✓, final answer with unit ✓ — never only the final answer."),
        ("lp-section-closing", "30–35 min", "\"I can...\" checklist exit ticket",
         "Students tick an 'I can...' checklist covering every major idea of "
         "the chapter, then complete: 'The topic I most need to practise is "
         "______.' Tell students the graded assessment is in the Assessment tab."),
    ],
    "rules": [
        "NO new content — every item comes from the days already taught",
        "Cover ideas from ALL days, not just the last few",
        "CFU at the end of each block; CCQs optional; Tamil optional",
        "No homework; the exit ticket is the checklist",
    ],
}


PHYSICS_ASSESSMENT_STRUCTURE = {
    "sections": [
        # (label, marks each, number of questions, guidance)
        ("Section A", 1, 6, "Quick recall: definitions, SI units, statements of laws, facts from the chapter"),
        ("Section B", 2, 4, "Short answers: distinguish / state properties / short reasoning"),
        ("Section C", 3, 3, "Explain a process, a short derivation, or a numerical with the five-step routine"),
        ("Section D", 5, 2, "Long derivation or detailed explanation of a working / principle"),
    ],
    "differentiated_levels": [
        "Foundation (needs support)",
        "Standard",
        "Advanced",
    ],
    "numerical_marking": "Formula ✓ | Unit conversion ✓ | Substitution ✓ | Answer with unit ✓",
}


# ============================================================================
# UNIVERSAL STRUCTURE META
# ============================================================================

PHYSICS_STRUCTURE_META = {
    # Day count bounds INCLUDING the final revision day
    "min_days": 3,
    "max_days": 22,

    # Pacing rule given to the Day Allocator (manual LP: ~1 subsection/day)
    "pacing_rule": (
        "About ONE numbered textbook subsection (x.y or x.y.z) per day. "
        "Merge consecutive SMALL subsections (roughly 12 minutes of teaching "
        "or less each) into one day when they belong together. A dense "
        "subsection, a major derivation, or a subsection with several solved "
        "examples gets its own day. Never split one subsection across days."
    ),
    "content_minutes_per_day": 22,   # teaching minutes available after opening/closing

    "teaching_pattern": (
        "Familiar experience -> simple English -> Tamil explanation -> "
        "scientific English -> board diagram / formula -> guided practice"
    ),
    "numerical_routine": "Given -> Find -> Formula -> Substitute -> Answer with unit",
    "tamil_scaffolding_rule": (
        "One short code-mixed Tamil line per teaching block (plus the opening "
        "question in Tamil). No Tamil in CCQ, CFU, activities, exit ticket, "
        "board-work, formula-box or the assessment."
    ),
    "avoid": [
        "Reading the textbook aloud for long stretches",
        "Writing a formula and saying 'memorise this' instead of asking what each symbol means",
        "Starting a numerical by substituting numbers before units and direction / sign",
        "Rushing a dense multi-part section into one hurried block",
        "Correcting every English mistake while a student is explaining the physics",
    ],
    "instead": [
        "Draw, ask questions, use everyday examples",
        "Let students answer in Tamil or broken English first, then convert to exam English",
        "Drill the five-step numerical routine on every numerical day",
        "Make students draw diagrams and decide direction before calculating magnitude",
        "Revisit yesterday's formula for one minute at the start of each lesson",
    ],

    # Textbook parts that are NOT teaching content (extractor excludes them)
    "non_teaching_parts": [
        "Summary", "Concept map", "Evaluation", "Book-back exercises",
        "Multiple choice questions", "Short answer questions",
        "Long answer questions", "Numerical problems", "Conceptual questions",
        "Answers", "ICT corner", "Glossary", "Reference books",
        "Learning objectives box", "Activity boxes that only repeat the text",
    ],
}


def expected_day_range(chapter_chars: int) -> Tuple[int, int]:
    """
    Rough sanity range for total days from chapter length — used ONLY to log
    a warning, never to override the allocator. Calibrated on the manual LP
    (Electrostatics, roughly one day per 6-12k characters of teaching text).
    """
    lo = max(PHYSICS_STRUCTURE_META["min_days"], chapter_chars // 14000)
    hi = min(PHYSICS_STRUCTURE_META["max_days"], max(lo, chapter_chars // 5000 + 2))
    return int(lo), int(hi)