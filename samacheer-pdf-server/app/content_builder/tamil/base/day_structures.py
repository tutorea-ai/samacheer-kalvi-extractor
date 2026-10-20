"""
tamil/base/day_structures.py
----------------------------
Data-only file: the fixed PEDAGOGICAL pattern for Class 6 Tamil LP, per
lesson type — content-agnostic, same for every lesson of that type.

Derived from the manual LP "Class 6 Tamil · Term 1 · Unit 1 தமிழ்த்தேன்"
(26 periods). That LP is a TEACHING TEMPLATE for every Class 6 lesson, not a
script for Unit 1. Nothing in this file names a Unit 1 topic; the manual's
examples are generalised into instructions (e.g. "show milk, honey and a
flower" -> "bring 2-3 real objects or pictures that match the images in
today's lines").

HOW TAMIL DIFFERS FROM PHYSICS
  - Each lesson is ONE type (poem / prose / supplementary / grammar /
    thirukural). The period pattern comes from the type — no Day Allocator.
  - poem, supplementary, thirukural: FIXED 4 periods (manual LP).
  - prose: one period per teaching section (small ones merged) + one
    period for the book exercises.            (manual: 7 headings + 1 = 8)
  - grammar: one period per sub-topic group (small ones merged); the LAST
    content period also carries the book exercises.  (manual: 4 periods;
    unit-end periods dropped by TL decision 5)
  - Every lesson's last period uses கற்பவை கற்றபின் as the task and மதிப்பீடு
    orally as the check (manual LP), and carries the homework (TL decision 3).
  - Variety: content periods of prose / grammar rotate through option lists
    by occurrence, so consecutive periods do not open the same way.

What is fixed for every lesson:
  - 30-minute period, four blocks (TAMIL_PERIOD_TIMING)
  - one CFU per period (two oral questions) inside சரிபார்த்தலும் நிறைவும்
  - CCQ per new grammar term — கற்கண்டு only
  - நிறைவு வினா every period; homework once, last period, from the book
"""

from typing import Dict, List


# ============================================================================
# THE 30-MINUTE PERIOD (manual LP "The 30-minute period")
# Each row maps to one styled lp-section-* wrapper. Boundaries may move a
# little; the total must stay 30 minutes, contiguous, starting at 0.
# ============================================================================

TAMIL_PERIOD_TIMING = [
    # (section class,             label key, default time, purpose)
    ("lp-section-opening",      "hook",  "0–4",   "one Tamil question with a picture, object or action; accept answers in any language, say them back in Tamil"),
    ("lp-section-main",         "teach", "4–13",  "one small chunk, read or sung by the teacher first; class echoes"),
    ("lp-section-student-task", "do",    "13–23", "pair or group task from the book"),
    ("lp-section-closing",      "close", "23–30", "CFU (two oral questions), நிறைவு வினா, link to the next period"),
]


# ============================================================================
# SHARED OPTION LISTS (generalised from the manual LP)
# ============================================================================

_HOOKS_PERSONAL = [
    ("Personal connection question",
     "Ask one spoken-Tamil question that links today's chunk to the child's own "
     "life (home, family, school, a favourite person or thing). Take 3-4 answers "
     "in any language and say each back in Tamil."),
    ("Picture or object",
     "Show a picture, or bring 2-3 real objects, that match an image or idea in "
     "today's chunk. Ask what comes to mind / which one is like today's idea."),
    ("Action warm-up",
     "A short whole-class action linked to today's chunk (trace letters in the "
     "air, snap fingers, clap a beat, act a word). Then ask one question about it."),
    ("Quick recall + 'why' question",
     "Recall one point from the last period in one minute, then ask a 'why' or "
     "'what if' question that today's chunk answers."),
]

_TASKS_GENERAL = [
    ("Sentence frame in pairs",
     "Pairs complete a spoken-Tamil sentence frame about today's chunk "
     "(e.g. ___ மாதிரி, ஏன்னா ___ / ___ நமக்கு ___ உதவுது), then 2-3 pairs say theirs."),
    ("Sort the cards",
     "Groups sort 8-12 word or picture cards taken from today's chunk into the "
     "two or three categories the book teaches today, saying each card aloud."),
    ("Label or word web",
     "Children label a simple drawing, or build a word web, using the words and "
     "examples printed in today's chunk."),
    ("Match the cards",
     "Pairs match cards from today's chunk (word to meaning, item to its book "
     "name, example to category), then check together with the teacher."),
]


# ============================================================================
# LESSON PATTERNS
#   "periods"         : FIXED types — the ordered period templates
#   "content_period"  : SECTION types — the template rotated for content periods
#   "final_period"    : SECTION types — the template for the exercises period
# Every template holds: title_hint, focus, hook, teach, do, close.
# Lists of (name, instruction) are rotated by occurrence.
# ============================================================================

TAMIL_LESSON_PATTERNS: Dict[str, Dict] = {

    # ------------------------------------------------------------------
    "poem": {
        "label": "கவிதைப்பேழை",
        "period_rule": "fixed",
        "min_periods": 4, "max_periods": 4,
        "periods": [
            {   # P1
                "title_hint": "பாடலைக் கேட்போம், பாடுவோம்",
                "focus": "The whole poem: listen and sing. Word-wall words introduced.",
                "hook": [_HOOKS_PERSONAL[0]],
                "teach": ("Teacher sings or reads the WHOLE poem with a tune twice; "
                          "class echoes line by line. Put the lesson's word-wall "
                          "words up with a gesture each. One English line on the "
                          "board giving the poem's central idea."),
                "do": [("Antiphonal singing",
                        "One half of the class sings the first half of each line, "
                        "the other half the rest; then swap.")],
                "close": "CFU on what the poet says about the subject of the poem.",
            },
            {   # P2
                "title_hint": "[first part of the poem]",
                "focus": ("The FIRST half of the poem's lines (or the first stanzas): "
                          "meaning in spoken Tamil, using the book's பாடலின் பொருள் "
                          "and சொல்லும் பொருளும். Start memorising the memorisation "
                          "part (மனப்பாடப் பகுதி) if it falls here."),
                "hook": [_HOOKS_PERSONAL[1]],
                "teach": ("Explain each line or image of today's part in spoken Tamil, "
                          "one at a time, with the book word -> spoken meaning. Show "
                          "today's lines in the பாடநூல் வரிகள் box, exactly as printed."),
                "do": [_TASKS_GENERAL[0]],
                "close": ("CFU, then memorisation: write one memorisation couplet on "
                          "the board, erase two words at a time, class says it without "
                          "looking."),
            },
            {   # P3
                "title_hint": "[rest of the poem] + [poetic feature]",
                "focus": ("The REST of the poem's lines, plus the poetic feature the "
                          "book's exercises ask about (இயைபு / எதுகை / மோனை — whichever "
                          "this lesson's மதிப்பீடு uses), with examples ONLY from the poem."),
                "hook": [_HOOKS_PERSONAL[1]],
                "teach": ("Explain today's lines as in the last period. Then the poetic "
                          "feature in one spoken-Tamil sentence with two examples from "
                          "the poem's own lines."),
                "do": [("Find the sound pattern",
                        "Children hunt the poem for words that show today's sound "
                        "pattern; clap when they find a pair; teacher writes the pairs.")],
                "close": "CFU; then the teacher says the start of a line and the class completes it.",
            },
            {   # P4 — last period
                "title_hint": "நூல்வெளி, கற்பவை கற்றபின், மதிப்பீடு",
                "focus": ("நூல்வெளி (poet and book, ONLY as in the lesson text), the "
                          "book's கற்பவை கற்றபின் items, oral மதிப்பீடு."),
                "hook": [("Question from the poet's life",
                          "One personal question linked to a fact in நூல்வெளி "
                          "(e.g. a name, a cause the poet cared about).")],
                "teach": "Retell நூல்வெளி in spoken Tamil, only the facts printed in the lesson text.",
                "do": [("கற்பவை கற்றபின்",
                        "Children do 2-3 of the book's கற்பவை கற்றபின் items in pairs "
                        "(sing with a tune, write, read aloud — as the book says).")],
                "close": "Oral மதிப்பீடு (MCQs, matching, a குறுவினா) as the CFU, then homework.",
            },
        ],
    },

    # ------------------------------------------------------------------
    "prose": {
        "label": "உரைநடை உலகம்",
        "period_rule": "sections",
        "min_periods": 3, "max_periods": 9,     # incl. the exercises period
        "sections_per_period": "one or two teaching sections",
        "content_period": {
            "title_hint": "[the section heading(s) taught today]",
            "focus": "One or two teaching sections of the lesson, in textbook order.",
            "hook": _HOOKS_PERSONAL,
            "teach": ("Teach today's section(s) in spoken Tamil with the book's own "
                      "examples (words, names, lists, tables). Show any printed "
                      "examples in the பாடநூல் வரிகள் box. Use a picture or object for "
                      "every new word. Boxed notes ([பெட்டிச் செய்தி]) of today's "
                      "section are read aloud by the teacher."),
            "do": _TASKS_GENERAL,
            "close": "CFU on today's section; a குறுவினா from the book may be one of the two questions.",
        },
        "final_period": {
            "title_hint": "கற்பவை கற்றபின், மதிப்பீடு",
            "focus": "Revisit the whole lesson through the book's own exercises.",
            "hook": [("Word-wall quiz",
                      "Quick quiz: who can say three words from the word wall and what they mean?")],
            "teach": "Two-minute recap of the lesson's sections, one line each, in spoken Tamil.",
            "do": [("கற்பவை கற்றபின்",
                    "Groups do the book's கற்பவை கற்றபின் items (talk, write, say) "
                    "as the book words them.")],
            "close": "Oral மதிப்பீடு (MCQs, fill-ins, a குறுவினா) as the CFU, then homework.",
        },
    },

    # ------------------------------------------------------------------
    "supplementary": {
        "label": "விரிவானம்",
        "period_rule": "fixed",
        "min_periods": 4, "max_periods": 4,
        "periods": [
            {   # P1
                "title_hint": "[first part of the story / dialogue]",
                "focus": "நுழையும் முன் and the FIRST third of the lesson text.",
                "hook": [_HOOKS_PERSONAL[0]],
                "teach": ("Teacher reads today's part aloud with expression (never a "
                          "child reading cold). Retell it in spoken Tamil, then ask "
                          "one 'how did this change …?' question."),
                "do": [("Retell with a frame",
                        "Pairs retell today's part using a spoken-Tamil frame "
                        "(e.g. அவர் ___ செஞ்சார். அதனால ___ ஆச்சு.).")],
                "close": "CFU on today's part.",
            },
            {   # P2
                "title_hint": "[middle part]",
                "focus": "The MIDDLE third of the lesson text.",
                "hook": [_HOOKS_PERSONAL[1]],
                "teach": ("Read today's part aloud; retell in spoken Tamil. Give the "
                          "English word once for one key term only if it helps."),
                "do": [("Cause and effect chart",
                        "Groups fill a two-column chart: என்ன நடந்தது / அதனால என்ன ஆச்சு, "
                        "with points from today's part only.")],
                "close": "CFU; one question may come from the book's மதிப்பீடு.",
            },
            {   # P3
                "title_hint": "[last part]",
                "focus": "The LAST third of the lesson text and its main message.",
                "hook": [_HOOKS_PERSONAL[3]],
                "teach": ("Read today's part; write the 3-4 key words of its message on "
                          "the board; explain each in spoken Tamil."),
                "do": [("Ask your own question",
                        "Each child writes one question about today's part starting "
                        "with ஏன், எப்படி or எது; pairs swap and answer.")],
                "close": "CFU on the lesson's main message.",
            },
            {   # P4 — last period
                "title_hint": "[reading in roles], கற்பவை கற்றபின்",
                "focus": ("Read the whole lesson again in roles (dialogue -> reader's "
                          "theatre; story -> narrator + characters), then the book's "
                          "கற்பவை கற்றபின் items."),
                "hook": [("Role cards",
                          "Hand out role cards for the lesson's speakers / characters "
                          "and a narrator.")],
                "teach": "Teacher models the first exchange with expression; groups rotate roles.",
                "do": [("Reading in roles + கற்பவை கற்றபின்",
                        "Groups read in roles, then do one or two of the book's "
                        "கற்பவை கற்றபின் items.")],
                "close": "Oral மதிப்பீடு as the CFU; a personal frame linked to the lesson's message; homework.",
            },
        ],
    },

    # ------------------------------------------------------------------
    "grammar": {
        "label": "கற்கண்டு",
        "period_rule": "sections",
        "min_periods": 2, "max_periods": 5,     # the LAST content period carries the exercises
        "sections_per_period": "one sub-topic, or two small related sub-topics",
        "exercises_in_last_content_period": True,
        "content_period": {
            "title_hint": "[the grammar sub-topic(s) taught today]",
            "focus": "One grammar sub-topic (or two small related ones), in textbook order.",
            "hook": [
                ("What if there were no rule?",
                 "Ask what would happen if there were no rule for today's point "
                 "(e.g. for writing, for sounds)."),
                ("Action warm-up", _HOOKS_PERSONAL[2][1]),
                ("Pictures from the book",
                 "Show the pictures the book uses for today's sub-topic and ask what "
                 "each one suggests."),
                ("Build it with cards",
                 "Build one example of today's rule with letter cards in front of the "
                 "class and ask what we get."),
            ],
            "teach": ("Teach each new grammar term with the book's own definition and "
                      "examples (in the பாடநூல் வரிகள் box, exactly as printed), a "
                      "gesture or action that fixes the idea, and ONE CCQ right after "
                      "each new term. Rule boxes from the book may go in a formula-box."),
            "do": [
                ("Sort the letter cards",
                 "Groups sort letter or word cards into the categories taught today, "
                 "saying each card aloud."),
                ("Pairs test each other",
                 "Pairs test each other on today's rule with the book's examples "
                 "(one says, the other answers / snaps / shows)."),
                ("Build and check",
                 "Pairs build examples of today's rule with cards and check them "
                 "against the book's examples."),
            ],
            "close": "CFU on today's rule (two quick oral questions with answers in book Tamil).",
        },
        "final_addition": ("This is the LAST period: in செயல்பாடு also do the book's "
                           "கற்பவை கற்றபின் item; in சரிபார்த்தலும் நிறைவும் use the "
                           "book's மதிப்பீடு orally as the CFU; then homework."),
    },

    # ------------------------------------------------------------------
    "thirukural": {
        "label": "வாழ்வியல்",
        "period_rule": "fixed",
        "min_periods": 4, "max_periods": 4,
        "kural_periods": 3,      # the lesson's kurals are split evenly over P1-P3
        "periods": [
            {   # P1
                "title_hint": "குறள் அறிமுகம், குறள் [range]",
                "focus": "நுழையும் முன் and today's kurals.",
                "hook": [("Say a proverb",
                          "Ask children to say one proverb they know; then: a kural "
                          "says a big idea in very few words.")],
                "teach": ("Read today's kurals with a rhythm (each kural in the "
                          "பாடநூல் வரிகள் box, exactly as printed); class echoes; "
                          "explain each in one spoken-Tamil line using the book's meaning."),
                "do": [("Clap the beat",
                        "Class claps the beat while saying one of today's kurals line by line.")],
                "close": "CFU; pairs match each of today's kurals to its meaning card.",
            },
            {   # P2
                "title_hint": "குறள் [range]",
                "focus": "Today's kurals.",
                "hook": [("Life-situation question",
                          "One question about a real situation that one of today's "
                          "kurals speaks to.")],
                "teach": "As in the last period: read, echo, explain each kural with the book's meaning.",
                "do": [("Role-play",
                        "Pairs act a short everyday situation that one of today's "
                        "kurals speaks to; then the class says that kural together.")],
                "close": "CFU with a spoken-Tamil frame on one kural's idea.",
            },
            {   # P3
                "title_hint": "குறள் [range]",
                "focus": "Today's kurals.",
                "hook": [("Object or picture",
                          "Show an object or picture that matches an image in one of "
                          "today's kurals; ask which they would choose and why.")],
                "teach": "Read, echo, explain each kural; tie the image in the kural to the object shown.",
                "do": [("Apply the kural",
                        "Children change 2-3 everyday sentences or actions so they "
                        "follow one of today's kurals; then say that kural together.")],
                "close": "CFU on why the kural's advice matters.",
            },
            {   # P4 — last period
                "title_hint": "நூல்வெளி, மதிப்பீடு, ஒப்புவித்தல்",
                "focus": ("நூல்வெளி (only as in the lesson text), the book's மதிப்பீடு, "
                          "recitation of the memorisation kurals."),
                "hook": [("Recall race",
                          "Teacher says the first words of a kural; teams finish it.")],
                "teach": "Retell நூல்வெளி in spoken Tamil, only the facts printed in the lesson text.",
                "do": [("மதிப்பீடு in pairs",
                        "Pairs do the book's மதிப்பீடு items (MCQs, fill the missing "
                        "words, நயம் அறிக, match the story to a kural).")],
                "close": ("CFU, then recitation: pairs recite the memorisation kurals, "
                          "then one volunteer per kural; homework."),
            },
        ],
    },
}


# ============================================================================
# PREAMBLE — key-content table per type (built in Python from extractor data)
# Maximum 3 columns.
# ============================================================================

KEY_CONTENT_TABLES: Dict[str, Dict] = {
    "poem":          {"title": "பாடல் கருத்துகள்",
                      "columns": ["பாடல் சொல் / வரி", "பேச்சுத் தமிழில் பொருள்", "English"]},
    "prose":         {"title": "பாடப் பகுதிகள்",
                      "columns": ["தலைப்பு", "முக்கியக் கருத்து", "பாடநூல் எடுத்துக்காட்டு"]},
    "supplementary": {"title": "முக்கியக் கருத்துகள்",
                      "columns": ["நிகழ்வு / கருத்து", "பேச்சுத் தமிழில் விளக்கம்", "English"]},
    "grammar":       {"title": "இலக்கணக் கருத்துகள்",
                      "columns": ["இலக்கணச் சொல்", "விளக்கம்", "பாடநூல் எடுத்துக்காட்டு"]},
    "thirukural":    {"title": "குறள்கள் ஒரு பார்வை",
                      "columns": ["எண் · அதிகாரம்", "ஆசிரியர் விளக்கம் (பேச்சுத் தமிழ்)", "English"]},
}

WORD_WALL_COLUMNS = ["பாடநூல் சொல்", "பேச்சுத் தமிழில் பொருள்", "English"]


# ============================================================================
# ASSESSMENT BLOCK (manual LP "Assessment pointers") — per type
# ============================================================================

ASSESSMENT_STRUCTURE: Dict[str, List[str]] = {
    "_all": [
        "Answers to the book's MCQs (சரியான விடை), in book Tamil",
        "Answers to the book's fill-ins / matching / join-and-split items",
        "Model answers to the book's குறுவினா, in book Tamil",
        "சிந்தனை வினா: what kinds of answers to accept",
        "Differentiation: one line of support for children who struggle, one stretch task",
    ],
    "poem":       ["Recitation check: the memorisation part (மனப்பாடப் பகுதி)"],
    "thirukural": ["Recitation check: the memorisation kurals",
                   "நயம் அறிக: the எதுகை / மோனை words, from the kurals' own lines"],
    "grammar":    ["One worked example of the lesson's main rule, from the book"],
}


def assessment_items(lesson_type: str) -> List[str]:
    return ASSESSMENT_STRUCTURE["_all"] + ASSESSMENT_STRUCTURE.get(lesson_type, [])


# ============================================================================
# TEACHING META (manual LP "Teaching in spoken Tamil with English support")
# ============================================================================

TAMIL_STRUCTURE_META = {
    "teaching_pattern": "Tamil first -> picture or action -> English last",
    "pacing_rule": (
        "One small chunk per period. Merge consecutive SMALL teaching sections "
        "(a few lines, a box, a short list) into the same period when they belong "
        "together. Never split one section across periods."
    ),
    "min_section_chars": 450,     # sections shorter than this are merged forward
    "avoid": [
        "Asking a child to read cold",
        "Long teacher monologue (more than 3 minutes without a student response)",
        "English glosses after every line",
        "Paraphrasing or 'correcting' a poem or kural line",
        "Adding facts, stories or religious examples that are not in the lesson text",
    ],
    "instead": [
        "Teacher reads or sings first, class echoes, then pairs",
        "A picture, object or action for every new word",
        "Think, pair, share: strongest language first, then Tamil",
        "Spoken-Tamil sentence frames for children's answers",
        "Restate every child's answer in Tamil with the key term",
    ],
}


# ============================================================================
# ACCESSORS
# ============================================================================

def get_pattern(lesson_type: str) -> Dict:
    """Pattern for a normalized lesson type (falls back to prose)."""
    return TAMIL_LESSON_PATTERNS.get(lesson_type, TAMIL_LESSON_PATTERNS["prose"])


def _pick(options, occurrence: int):
    if isinstance(options, list):
        return options[occurrence % len(options)]
    return options


def get_period_strategy(lesson_type: str, period_index: int, total_periods: int,
                        occurrence: int = 0) -> Dict[str, str]:
    """
    Teaching strategy for one period.
      period_index : 0-based
      occurrence   : for section types, how many content periods came before
                     this one (rotates hooks / tasks)
    """
    p = get_pattern(lesson_type)
    is_last = period_index == total_periods - 1

    if p["period_rule"] == "fixed":
        tpl = p["periods"][min(period_index, len(p["periods"]) - 1)]
        extra = ""
    elif lesson_type == "grammar":
        tpl = p["content_period"]
        extra = p["final_addition"] if is_last else ""
    else:   # prose
        tpl = p["final_period"] if is_last else p["content_period"]
        extra = ""

    hook_name, hook_instr = _pick(tpl["hook"], occurrence)
    do_name, do_instr = _pick(tpl["do"], occurrence)
    return {
        "lesson_type": lesson_type,
        "lesson_label": p["label"],
        "title_hint": tpl["title_hint"],
        "focus": tpl["focus"],
        "hook_style": hook_name,
        "hook_instruction": hook_instr,
        "teach_instruction": tpl["teach"],
        "do_style": do_name,
        "do_instruction": do_instr,
        "close_instruction": tpl["close"],
        "last_period_note": extra,
        "is_last": is_last,
    }


def split_evenly(items: List, parts: int) -> List[List]:
    """
    Split items into `parts` consecutive groups, sizes differing by at most
    one, larger groups LAST (manual LP: 10 kurals -> 3, 3, 4).
    """
    parts = max(1, min(parts, len(items))) if items else 1
    base, extra = divmod(len(items), parts)
    sizes = [base] * (parts - extra) + [base + 1] * extra
    out, i = [], 0
    for s in sizes:
        out.append(items[i: i + s])
        i += s
    return out