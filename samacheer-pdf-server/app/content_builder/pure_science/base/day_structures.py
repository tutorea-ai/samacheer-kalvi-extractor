"""
day_structures.py
------------------
Data-only file: the fixed PEDAGOGICAL pattern for Biology LP (Botany and
Zoology, grade_1112) — content-agnostic, same for every chapter.

REBUILT Sept 2026 — replaces the earlier per-chapter hardcoded-topic
design (GENETICS_14_DAY_STRUCTURE, UNIT_STRUCTURE_MAP). That design
assumed each chapter needed its own manual-LP-derived topic structure,
which was wrong: the Classical Genetics manual LP was a TEMPLATE for
how every Botany/Zoology chapter should be taught, not a script for
that one chapter. See conversation history for the full correction.

What's fixed across every chapter (confirmed):
  - 14 days per chapter
  - Day 14 = revision + embedded graded assessment (no new content,
    no separate trailing Assessment call, no homework, no preview)
  - A rotating TEACHING TECHNIQUE per day number (opening style +
    activity style) — content-agnostic, same shape as SS History's
    DAY_STRATEGY, SPARK_STYLES, ACTIVITY_MAP, just scaled to 14 days
    with genuine variety across all 14 slots (not a 4-5 loop)
  - Tamil in exactly 3 places, CFU/CCQ natural placement, 6-block
    default rhythm with per-day timing flexibility

What's NOT fixed (discovered per-chapter by the Section Extractor +
Day Allocator, same as SS History):
  - Which topics/sections get taught on which day
  - Day count subdivision within each day (how many CFU/CCQ, how the
    6-block rhythm resizes) — driven by how much content each day's
    allocated sections actually need
"""


# ============================================================================
# BIOLOGY DAY STRATEGY — technique rotation, content-agnostic
# Day 14 is intentionally different in shape (revision + assessment, not
# a new-content day) — see _call_content_day's closing-instruction branch
# in biology.py, not this dict, for that logic.
# ============================================================================

BIOLOGY_DAY_STRATEGY = {
    1: {
        "spark_style": "Real-life analogy + big question",
        "spark_instruction": (
            "Open with a relatable real-life scenario connecting to today's "
            "topic (family, school, farming, local Tamil Nadu context). End "
            "with one big question that sparks curiosity. 3-5 students share "
            "in large group before moving on."
        ),
        "activity_style": "Pair sort / classify",
        "activity_instruction": (
            "Give pairs a short list of examples related to today's content. "
            "They classify/sort each item into categories from today's "
            "lesson, using notes. Pairs share, teacher corrects on board."
        ),
    },
    2: {
        "spark_style": "Previous-day recap + connecting question",
        "spark_instruction": (
            "Start with a 1-minute recap: 2-3 students each name one thing "
            "from yesterday. Then pose a question connecting yesterday's "
            "idea to today's new content."
        ),
        "activity_style": "Small-group discussion (3 groups, 3 questions)",
        "activity_instruction": (
            "Divide class into 3 groups. Each group gets one question from "
            "today's content, discusses for 3 minutes using notes/textbook, "
            "one student per group shares. Teacher adds key points to board."
        ),
    },
    3: {
        "spark_style": "Describe-and-draw hook",
        "spark_instruction": (
            "Describe a structure/process students will see today without "
            "showing it yet ('imagine a structure that does X'). Ask them "
            "to predict what it might look like before revealing the real "
            "answer."
        ),
        "activity_style": "Quiz game — teams compete",
        "activity_instruction": (
            "Split into 4 teams. Run a short rapid-fire quiz (5-6 questions) "
            "from today's content. First hand raised answers; correct = 1 "
            "point. Track scores on board."
        ),
    },
    4: {
        "spark_style": "Mini-demonstration or vivid scenario (no-tech friendly)",
        "spark_instruction": (
            "Describe a short, vivid real-world scenario or simple in-class "
            "demonstration (something with everyday materials) that connects "
            "to today's concept. Ask what students think will happen / why."
        ),
        "activity_style": "Poster / diagram-making in notebook",
        "activity_instruction": (
            "Students sketch a mini diagram or concept poster in their "
            "notebook summarizing today's content — title, 2-3 key facts, "
            "one simple sketch. A few students show and explain theirs."
        ),
    },
    5: {
        "spark_style": "Puzzle / riddle framing",
        "spark_instruction": (
            "Pose today's core concept as a puzzle or mystery students must "
            "resolve ('why does X happen even though Y?'). Let pairs guess "
            "before revealing the textbook explanation."
        ),
        "activity_style": "Structured debate / for-and-against",
        "activity_instruction": (
            "Give a debatable statement drawn from today's content. Split "
            "the class into two sides; each side gives short reasons; "
            "teacher summarizes and connects back to the actual science."
        ),
    },
    6: {
        "spark_style": "Compare-and-contrast opener",
        "spark_instruction": (
            "Present two contrasting real examples relevant to today's "
            "topic and ask students which is which, or what's different "
            "between them, before naming the underlying concept."
        ),
        "activity_style": "Role-play / narrator activity",
        "activity_instruction": (
            "One or two students narrate a process from today's content "
            "step-by-step in their own words (acting as a 'narrator' or "
            "'process guide') while the class follows along and corrects."
        ),
    },
    7: {
        "spark_style": "Previous-day recap + real-life connection",
        "spark_instruction": (
            "Quick recap of yesterday (2-3 students), then connect directly "
            "into today's topic with a real-life question that bridges the "
            "two ideas."
        ),
        "activity_style": "Board relay",
        "activity_instruction": (
            "Students take turns coming to the board in short bursts to "
            "complete a diagram, table, or list from today's content, one "
            "piece at a time, with the class guiding each turn."
        ),
    },
    8: {
        "spark_style": "Physical demonstration hook",
        "spark_instruction": (
            "Use a simple, concrete physical demonstration (everyday "
            "materials, a gesture, or an analogy acted out) that makes "
            "today's concept tangible before naming it formally."
        ),
        "activity_style": "Predict-observe-explain",
        "activity_instruction": (
            "Present a scenario from today's content. Students predict the "
            "outcome individually, then the teacher reveals the real "
            "outcome, then students explain why in pairs."
        ),
    },
    9: {
        "spark_style": "Student-led recap + provocative question",
        "spark_instruction": (
            "A student volunteer stands and recaps yesterday's key idea in "
            "3-4 sentences. Teacher follows with a provocative or surprising "
            "question that leads into today's content."
        ),
        "activity_style": "Concept card sort / match",
        "activity_instruction": (
            "Give pairs or small groups a set of terms/concepts from "
            "today's content to match or sort correctly (term-to-meaning, "
            "cause-to-effect, or similar), then check together."
        ),
    },
    10: {
        "spark_style": "Everyday Tamil Nadu context hook",
        "spark_instruction": (
            "Open with a hook grounded in everyday Tamil Nadu life "
            "(agriculture, local food, common household observation) that "
            "connects naturally to today's biological concept."
        ),
        "activity_style": "Think-pair-share with worksheet",
        "activity_instruction": (
            "Students answer 2-3 short structured questions individually, "
            "then compare with a partner, then a few pairs share with the "
            "class. Teacher clarifies any mismatches."
        ),
    },
    11: {
        "spark_style": "Consolidation framing",
        "spark_instruction": (
            "Frame today explicitly as connecting several related ideas "
            "together ('today we build one big picture out of pieces we've "
            "seen'). Ask students what connections they already suspect."
        ),
        "activity_style": "Collaborative reference-table building",
        "activity_instruction": (
            "As a class, build one consolidated reference table or map on "
            "the board covering today's (and optionally recent) related "
            "concepts, with students contributing rows/entries."
        ),
    },
    12: {
        "spark_style": "Real-world application hook",
        "spark_instruction": (
            "Open with a real-world problem or application where today's "
            "concept matters practically (health, agriculture, industry) "
            "and ask students to guess how it connects before explaining."
        ),
        "activity_style": "Apply-it task",
        "activity_instruction": (
            "Give a short practical scenario. Students work in pairs to "
            "propose how today's concept explains or solves it, then share "
            "with the class."
        ),
    },
    13: {
        "spark_style": "Exception / 'what if the rule breaks' hook",
        "spark_instruction": (
            "Introduce today by asking what happens when a normal rule or "
            "pattern (from earlier days, if relevant) doesn't hold — today's "
            "content often deals with an exception, special case, or a "
            "less typical situation."
        ),
        "activity_style": "Compare-contrast chart",
        "activity_instruction": (
            "Students build a two-column chart contrasting today's special "
            "case against the general/typical case from earlier in the "
            "chapter, then share key differences."
        ),
    },
    14: {
        "spark_style": "Rapid recall quiz -> revision framing",
        "spark_instruction": (
            "Open with a fast recall quiz sampling ideas from across the "
            "whole chapter (5-6 quick questions). Frame today explicitly as "
            "revision plus a graded check of the whole chapter."
        ),
        "activity_style": "Ratio-rally / whole-chapter game review",
        "activity_instruction": (
            "A fast-paced pair or team activity reviewing key facts/ratios/"
            "terms from across the entire chapter, followed by the embedded "
            "graded assessment (see closing-instruction rule — Day 14 is "
            "revision + assessment, never new content)."
        ),
    },
}


# ============================================================================
# UNIVERSAL STRUCTURE META — same for every Botany/Zoology chapter, no
# per-unit-type routing needed anymore (see module docstring)
# ============================================================================

BIOLOGY_STRUCTURE_META = {
    "total_days": 14,
    "has_separate_assessment_call": False,  # Day 14 embeds the assessment
    "teaching_pattern": (
        "Real-life example -> simple English -> Tamil explanation -> "
        "textbook term -> diagram -> student practice"
    ),
    "tamil_scaffolding_rule": (
        "Tamil in exactly 3 places per day: key terms table, ONE main "
        "explanation mirror (the single most important sub-part if a day "
        "covers several), opening question. Meaning-based, not "
        "word-for-word."
    ),
    "avoid": [
        "Reading the textbook aloud for 35 minutes",
        "Making students copy definitions for the whole period",
        "Introducing a complex diagram or structure before building up to it",
        "Asking students to memorise a fact without understanding what it means",
        "Cramming too many new terms into a single day",
        "Correcting every English mistake while a student explains the biology",
    ],
}