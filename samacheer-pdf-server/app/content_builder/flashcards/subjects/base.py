"""
subjects/base.py
----------------
SubjectProfile — everything Flash Cards needs to know about ONE subject.

The engine (lp_parser, builder, renderer) stays subject-free and reads these
values. To add a subject: copy physics.py, change the values, and register
it in subjects/__init__.py.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SubjectProfile:
    key: str                  # request value, lower-case: "physics"
    display_name: str         # shown in prompts: "Physics" ("" → derived from the request value)

    # Filter chips and card typing
    card_types: list          # [(card type key, chip label)] in display order
    type_keywords: list       # [(word found in the LP "Day type", card type)] — first match wins
    type_guide: dict          # card type → what that card should focus on

    # Prompt pieces — builder.py fills these into its shared templates
    audience: str             # "... students preparing for {audience}."
    notation: str             # notation / writing rules at the end of the system prompt
    example_one: str          # good one-thing question, in quotes
    example_two: str          # good question naming two linked things, in quotes
    formula_rule: str         # the "- formula: ..." line of the card prompt
    tip_ideas: str            # kinds of exam advice to suggest in exam_tip
    extra_rules: str = ""     # extra card rules, each starting with "\n- "
    recap_formula_note: str = ""   # appended to the recap "bullets" line
    tip_kind: str = "board-exam"   # "exam_tip: ONE sentence of {tip_kind} advice"

    # Parsing / input options — the defaults are today's (Physics) behaviour
    type_from_meta: bool = False    # no "Day type:" label → match keywords against meta line + title + LP folder name
    title_strip: tuple = ()         # regexes removed from day titles (after "Day N —")
    drop_classes: tuple = ()        # extra LP classes to drop, on top of lp_parser.DROP_CLASSES
    max_text_per_day: int = 0       # chars of day text sent to Claude; 0 = builder default (3,500)
    recap_from_cards: bool = False  # no revision day → build the Chapter Recap from the cards
    flatten_inline: bool = False    # join bold/italic words and table rows into single lines
    drop_line_prefixes: tuple = ()  # lines starting with these (lower-case) are removed, e.g. "preview:"
    aliases: tuple = ()             # other request values for the same subject, e.g. ("social_science", "ss")
    limits: dict = field(default_factory=dict)  # overrides of builder limits, e.g. {"MAX_BULLET_WORDS": 24}
    recap_day: str = "first"        # several revision days: which one feeds the Chapter Recap ("first" / "last")
    board_classes: tuple = ("board-work",)   # class names that hold board notes (Biology 12 also: "lp-board-work")
    recap_from_text: bool = False   # recap reads the revision day's text, not just its objectives + board work
    title_from_focus: tuple = ()    # titles (regex, full match) replaced by the meta table's Focus