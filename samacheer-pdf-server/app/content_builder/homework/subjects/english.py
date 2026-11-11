"""Homework profile: English, Classes 6–12.

Reading values come from BB's English profile (measured on the Class 6
Term 1 Unit 1 Sea Turtles prose LP: 6 days, 3 'Content Day' and 3
'Grammar Day', title + meta inside the block, titles prefixed with a lesson
code up to a colon, no revision day; poem LPs have no day label). Unlike BB,
Homework keeps the student tasks, closing and vocabulary: the word meanings
and exercises show the level the homework should match.
"""
from .base import SubjectProfile

ENGLISH = SubjectProfile(
    key="english",
    display_name="English",

    # Reading
    day_type_pattern=r"^\s*(Content|Grammar)\s+Day",
    title_strip=(r"^Day\s+\d+(\s+of\s+\d+)?\s*[—–:-]\s*",
                 r"^[^:]{0,80}(Prose|Poem|Supplementary|Play|Drama)[^:]{0,40}:\s*"),
    extra_drop_classes=("student-says", "activity-block", "diff-block"),
    max_text_per_day=14000,
    review_keywords=(),        # English LPs have no revision day

    # Homework
    audience="Class 6 Tamil Nadu State Board English students (about 11 years old)",
    apply_style=(
        "On a Content Day (the story text): a short writing task linked to the text, such as "
        "3 to 4 sentences, a short letter or a description. On a Grammar Day: a practice "
        "exercise of 4 to 5 items, each written out in full on its own line (fill a blank, "
        "choose the right word, or rewrite a sentence), so every item has one definite answer. "
        "On a poem day (no day label): a few lines of the student's own on the poem's theme, "
        "or finding and using rhyming words."
    ),
    extra_rules=(
        "\n- Understand tasks: on a Content Day or poem day, explain a character, event, feeling "
        "or word meaning from the text in the student's own words; on a Grammar Day, explain the "
        "rule in their own words and give one example of their own."
        "\n- Write for an 11-year-old: short sentences and everyday words."
        "\n- Name a place, organisation, date or number only if the lesson text names it."
        "\n- Quote at most a few words of the story or poem; never copy a passage or a full line "
        "of a poem."
        "\n- A grammar exercise uses new sentences, never the lesson's own examples or exercise "
        "sentences."
        "\n- In answers to a grammar exercise, give each item's answer on its own line, numbered "
        "like the task."
    ),
    answer_review_rules=(
        "\n- When an answer contains lines of poetry: the rhyme pair it names must be the pair "
        "it actually uses; every rhyme must be a true rhyme (tail / sail, not gleam / seems); "
        "the number of lines must be within what the task asks (this overrides the extra "
        "sentence allowance); every line must be grammatical. Flag any line that breaks this."
    ),
    limits={"MAX_TASK_WORDS": 70, "MAX_HINT_WORDS": 25, "MAX_ANSWER_WORDS": 120},
    max_sentence_words=25,
    letter_subscripts=False,   # fill-in blanks like ____ stay as written
)