"""
subjects/base.py
----------------
SubjectProfile — everything Flash Cards needs to know about ONE subject.

The engine (lp_parser, builder, renderer) stays subject-free and reads these
values. To add a subject: copy physics.py, change the values, and register
it in subjects/__init__.py.
"""

from dataclasses import dataclass


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