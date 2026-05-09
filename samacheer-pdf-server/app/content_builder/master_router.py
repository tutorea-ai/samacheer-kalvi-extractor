"""
master_router.py
----------------
Top-level router for all SK-CAP content generation.

Reads:
    metadata["subject"]  → routes to the correct subject router
    mode                 → "lp" or "qa"

Returns:
    Combined HTML string from the correct subject router, or None on failure.

Adding a new subject:
    1. Create folder:        app/content_builder/new_subject/
    2. Build subject router: app/content_builder/new_subject/new_subject_router.py
    3. Add one import+call:  in generate_lp() and generate_qa() below

Subject mapping:
    "SocialScience"  → ss_router
    "English"        → english_router  (already exists)
    "Science"        → science_router  (future)
    "Tamil"          → tamil_router    (future)
    "Maths"          → maths_router    (future)
"""

from typing import Optional


# ============================================================================
# SUBJECT NORMALISATION
# ============================================================================

# Maps all possible subject strings from API → internal key
SUBJECT_MAP = {
    # Social Science variants
    "socialscience":  "ss",
    "social_science": "ss",
    "social science": "ss",
    "ss":             "ss",

    # English variants
    "english":        "english",

    # Future subjects
    "science":        "science",
    "tamil":          "tamil",
    "maths":          "maths",
    "math":           "maths",
    "mathematics":    "maths",
}


def _normalise_subject(raw: str) -> Optional[str]:
    """Normalise subject string to internal key."""
    key = raw.lower().strip().replace("-", "_")
    result = SUBJECT_MAP.get(key)
    if not result:
        print(f"   [Master Router] ❌ Unknown subject: '{raw}'")
    return result


# ============================================================================
# LP ROUTER
# ============================================================================

def generate_lp(text: str, metadata: dict) -> Optional[str]:
    """
    Generate LP HTML for any subject and class.

    Args:
        text:     Clean chapter text from EPUB extractor
        metadata: Dict with subject, class, unit, lesson_title, discipline etc.

    Returns:
        Combined LP HTML string, or None on failure.
    """
    raw_subject = metadata.get("subject", "")
    subject     = _normalise_subject(raw_subject)

    if not subject:
        return None

    print(f"   [Master Router] LP → subject: {subject}")

    if subject == "ss":
        from .ss.ss_router import generate_lp as ss_generate_lp
        return ss_generate_lp(text, metadata)

    elif subject == "english":
        from .english.english_router import generate_lp as english_generate_lp
        return english_generate_lp(text, metadata)

    elif subject == "science":
        try:
            from .science.science_router import generate_lp as science_generate_lp
            return science_generate_lp(text, metadata)
        except ImportError:
            print(f"   [Master Router] ⏳ Science LP builder not yet implemented")
            return None

    elif subject == "tamil":
        try:
            from .tamil.tamil_router import generate_lp as tamil_generate_lp
            return tamil_generate_lp(text, metadata)
        except ImportError:
            print(f"   [Master Router] ⏳ Tamil LP builder not yet implemented")
            return None

    elif subject == "maths":
        try:
            from .maths.maths_router import generate_lp as maths_generate_lp
            return maths_generate_lp(text, metadata)
        except ImportError:
            print(f"   [Master Router] ⏳ Maths LP builder not yet implemented")
            return None

    else:
        print(f"   [Master Router] ❌ No LP router for subject: {subject}")
        return None


# ============================================================================
# QA ROUTER
# ============================================================================

def generate_qa(text: str, metadata: dict) -> Optional[str]:
    """
    Generate QA HTML for any subject and class.

    Args:
        text:     Clean chapter text from EPUB extractor
        metadata: Dict with subject, class, unit, lesson_title, discipline etc.

    Returns:
        Combined QA HTML string, or None on failure.
    """
    raw_subject = metadata.get("subject", "")
    subject     = _normalise_subject(raw_subject)

    if not subject:
        return None

    print(f"   [Master Router] QA → subject: {subject}")

    if subject == "ss":
        from .ss.ss_router import generate_qa as ss_generate_qa
        return ss_generate_qa(text, metadata)

    elif subject == "english":
        from .english.english_router import generate_qa as english_generate_qa
        return english_generate_qa(text, metadata)

    elif subject == "science":
        try:
            from .science.science_router import generate_qa as science_generate_qa
            return science_generate_qa(text, metadata)
        except ImportError:
            print(f"   [Master Router] ⏳ Science QA builder not yet implemented")
            return None

    elif subject == "tamil":
        try:
            from .tamil.tamil_router import generate_qa as tamil_generate_qa
            return tamil_generate_qa(text, metadata)
        except ImportError:
            print(f"   [Master Router] ⏳ Tamil QA builder not yet implemented")
            return None

    elif subject == "maths":
        try:
            from .maths.maths_router import generate_qa as maths_generate_qa
            return maths_generate_qa(text, metadata)
        except ImportError:
            print(f"   [Master Router] ⏳ Maths QA builder not yet implemented")
            return None

    else:
        print(f"   [Master Router] ❌ No QA router for subject: {subject}")
        return None