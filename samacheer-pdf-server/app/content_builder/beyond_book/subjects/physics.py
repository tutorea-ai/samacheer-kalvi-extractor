"""Beyond the Book profile: Physics, Classes 11–12.

Values come from measuring the Class 12 Current Electricity LP:
19 days, 5–8.5k chars per day after drops, "Day type:" label on
every day, Day 19 = "Revision · No new content".
"""
from .base import SubjectProfile

PHYSICS = SubjectProfile(
    key="physics",
    display_name="Physics",

    # Reading: numerical practice and closing recap carry no "why" value.
    extra_drop_classes=("lp-section-student-task", "lp-section-closing"),
    max_text_per_day=9000,
    recap_keywords=("revision",),
    building_mode="skip",   # only days with a real-life link get a card (TL review, Oct 29)
    try_this=False,         # safe, honest home experiments are rare in electricity (Oct 29)

    # Cards
    audience="Class 11–12 Tamil Nadu State Board Physics students",
    # (word found in the LP's Day type, what to connect it to). First match wins.
    type_hints=(
        ("formula",     "show what the formula decides in a real device or a real bill: "
                        "what changes for the student when one quantity changes"),
        ("derivation",  "connect to what the final result means in real devices; "
                        "the derivation is the reason the device works the way it does"),
        ("concept",     "connect the idea to something students already see every day "
                        "but have never questioned"),
        ("process",     "this is a lab measurement method: usually no everyday device works "
                        "this way, so prefer the building connection; never claim electricians, "
                        "technicians or other workers use this lab apparatus; beyond_school says "
                        "what precise measurement makes possible"),
        ("application", "the applications are the connection; choose the ones students "
                        "meet themselves, not only industrial ones"),
    ),
)