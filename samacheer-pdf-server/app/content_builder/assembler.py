"""
content_builder/assembler.py

Reads sections dict from section_detector.
Calls split_into_zones() to get clean focused text zones.
Passes correct zone to each extractor.
Joins results in correct order.
Python controls structure — Claude fills content.
"""

from typing import Dict
from .extractor import content_extractor
from ..services.section_detector import split_into_zones


class ContentAssembler:

    def assemble(self, text: str, sections: Dict, metadata: Dict) -> str:
        """
        Builds complete content HTML section by section.
        Each extractor receives only its relevant text zone.
        """
        class_num    = metadata.get("class", "")
        subject      = metadata.get("subject", "english")
        unit         = metadata.get("unit", "")
        lesson_title = metadata.get("lesson_title", "Unknown")
        lesson_type  = metadata.get("lesson_type", "prose")
        exercise_types = sections.get("exercise_types", [])

        print(f"      [Assembler] Building: {lesson_title}")

        # ── Split text into clean zones ONCE ──────────────────────────────────
        print(f"      [Assembler] Splitting text into zones...")
        zones = split_into_zones(text)

        parts = []

        # ── 1. Header — no Claude call needed ────────────────────────────────
        print(f"      [Assembler] Building header...")
        parts.append(content_extractor.extract_header(
            lesson_title, class_num, subject, unit
        ))
        print(f"         ✅ Header done")

        # ── 2. About the Author ───────────────────────────────────────────────
        if sections.get("has_about_author"):
            print(f"      [Assembler] Extracting About the Author...")
            result = content_extractor.extract_about_author(
                zones["author_zone"], is_poet=False
            )
            if result:
                parts.append(result)

        # ── 3. About the Poet ─────────────────────────────────────────────────
        if sections.get("has_about_poet"):
            print(f"      [Assembler] Extracting About the Poet...")
            result = content_extractor.extract_about_author(
                zones["author_zone"], is_poet=True
            )
            if result:
                parts.append(result)

        # ── 4. Do You Know ────────────────────────────────────────────────────
        if sections.get("has_do_you_know"):
            print(f"      [Assembler] Extracting Do You Know...")
            result = content_extractor.extract_do_you_know(zones["full_text"])
            if result:
                parts.append(result)

        # ── 5. Story / Poem / Play text ───────────────────────────────────────
        print(f"      [Assembler] Extracting story text...")
        result = content_extractor.extract_story_text(
            zones["story_zone"],
            lesson_type=lesson_type,
            lesson_title=lesson_title
        )
        if result:
            parts.append(result)

        # ── 6. Glossary ───────────────────────────────────────────────────────
        if sections.get("has_glossary"):
            print(f"      [Assembler] Extracting Glossary...")
            result = content_extractor.extract_glossary(zones["glossary_zone"])
            if result:
                parts.append(result)

        # ── 7. Exercises ──────────────────────────────────────────────────────
        if exercise_types:
            print(f"      [Assembler] Extracting exercises: {exercise_types}")
            exercise_parts = self._build_exercises(
                zones["exercise_zone"], exercise_types
            )
            parts.extend(exercise_parts)

        # ── 8. ICT Corner — always after exercises, before summary ────────────
        if sections.get("has_ict_corner"):
            print(f"      [Assembler] Extracting ICT Corner...")
            result = content_extractor.extract_ict_corner(zones["ict_zone"])
            if result:
                parts.append(result)

        # ── 9. Summary — always last ──────────────────────────────────────────
        print(f"      [Assembler] Generating Summary...")
        summary = content_extractor.extract_summary(
            zones["story_zone"], lesson_title
        )
        parts.append(summary)

        final_html = "\n\n".join(parts)
        print(f"      [Assembler] ✅ Complete — {len(parts)} sections, {len(final_html)} chars")
        return final_html

    def _build_exercises(self, exercise_zone: str, exercise_types: list) -> list:
        """
        Calls correct extractor for each exercise type.
        All extractors receive only the exercise zone — clean and focused.
        """
        results = []

        dispatch = {
            "mcq":              content_extractor.extract_exercise_mcq,
            "fill_blank":       content_extractor.extract_exercise_fill_blank,
            "true_false":       content_extractor.extract_exercise_true_false,
            "identify_speaker": content_extractor.extract_exercise_identify_speaker,
            "short_answer":     content_extractor.extract_exercise_short_answer,
            "long_answer":      content_extractor.extract_exercise_long_answer,
            "rearrange":        content_extractor.extract_exercise_rearrange,
            "match":            content_extractor.extract_exercise_match,
        }

        for ex_type in exercise_types:
            extractor_fn = dispatch.get(ex_type)
            if extractor_fn:
                print(f"         → Extracting: {ex_type}")
                result = extractor_fn(exercise_zone)
                if result:
                    results.append(result)
                else:
                    print(f"         ⚠️  {ex_type} not found — skipping")
            else:
                print(f"         ⚠️  Unknown type: {ex_type} — skipping")

        return results


# Singleton instance
content_assembler = ContentAssembler()