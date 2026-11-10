"""Homework profile: Social Science (History, Geography, Civics, Economics), Classes 6–10.

Reading values come from BB's Social Science profile (measured on the
Class 6 Term 1 History Unit 2 Human Evolution LP: 5 days, title + meta
inside the block, the meta line's last '|' segment states the day's focus,
Day 5 Map Work & Book-back = Evaluation Day). Unlike BB, Homework keeps
the student tasks, closing and vocabulary: they show the level and the
exact definitions the homework should match.
"""
from .base import SubjectProfile

SOCIALSCIENCE = SubjectProfile(
    key="socialscience",
    display_name="Social Science",
    aliases=("social_science", "social science", "ss"),

    # Reading
    day_type_pattern=r"\|\s*([^|]+?)\s*$",
    extra_drop_classes=("student-says", "activity-block", "diff-block", "diff-table"),
    max_text_per_day=14000,
    review_keywords=("evaluation day",),

    # Homework
    audience="Class 6 Tamil Nadu State Board Social Science students (about 11 years old)",
    apply_style=(
        "A short practical task: draw and label a simple picture described in the lesson, "
        "complete a short timeline or table, sort given items into groups, or write 3 to 4 "
        "sentences. On review days: prefer one task that combines two ideas from the lesson "
        "so far."
    ),
    extra_rules=(
        "\n- Write for an 11-year-old: short sentences and everyday words."
        "\n- Name a place, site, date or find only if the lesson text names it."
        "\n- Early humans are always described with dignity; hunting is about tracking and "
        "gathering food, never killing, weapons in use or blood."
        "\n- A student at home has only a notebook and pen: never ask for a printed map, the "
        "internet or a library. A map task becomes a rough sketch to draw and mark, or a list "
        "of places from the lesson."
        "\n- Model answers use the same short sentences and everyday words a good Class 6 "
        "student would write."
    ),
    limits={"MAX_TASK_WORDS": 50, "MAX_HINT_WORDS": 25, "MAX_ANSWER_WORDS": 120},
    max_sentence_words=25,     # 11-year-olds: catches hard 30-word prose, allows short comma lists
    letter_subscripts=False,   # no subscripts in SS; fill-in blanks like ____ stay as written
)