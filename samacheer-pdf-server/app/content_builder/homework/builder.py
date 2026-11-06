"""
Homework: task builder.

LP days -> one day of homework per LP day (every day, review days included):
the profile's task pair (Understand, Apply), each with one hidden hint, via
Claude tool calls. Knows nothing about subjects: audience, task guides,
rules and limits all come from the SubjectProfile.

Fail closed: a day whose homework cannot be confirmed by the code checks
and the reviewer is left out (skipped_days), never shipped wrong.
"""
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import anthropic
import httpx

from ...config import settings
from .lp_parser import load_lp, TAMIL_RE
from .subjects import get_profile
from .subjects.base import SubjectProfile

MAX_RETRIES = 2          # re-asks for days whose homework fails the checks
REVIEW_FAILED = "not checked (review call failed)"
HARD_FACTOR = 1.25       # up to 25% over a limit = warning only; beyond = retry
API_ATTEMPTS = 3         # attempts per API call on overload / network errors
API_BACKOFF = 30         # seconds between those attempts

# Pointers to the textbook: every task must be complete on its own.
BOOK_REF_RE = re.compile(
    r"\b(exercises?|examples?|questions?|q\.|evaluation|figures?|fig\.|tables?|pages?|"
    r"sections?)\s*\(?\d", re.I)

# Powers written flat ("× 10−19", "s−1", "m2") instead of as superscripts (10⁻¹⁹, s⁻¹, m²).
FLAT_POWER_RE = re.compile(
    r"10\^"
    r"|\d\.\d+\s*×\s*10\s*\d"
    r"|[×x]\s*10\s*[−-]\s*\d"
    r"|(?<![A-Za-z])(?:m|cm|mm|km|s|C|kg|g|V|K|N|A|J|W|Ω|mol)[−-][1-9]\b"
    r"|(?<![A-Za-z])(?:m|cm|mm|km|s)[23]\b")
POWER_RULE = ("write powers with superscript characters (10⁻¹⁹, m s⁻², m², x³), "
              "never flat (10−19, s−1, m2)")

SYSTEM_TEMPLATE = """You write daily homework for {audience}.
Each lesson day gets exactly {n} tasks, in this order:
{task_list}

Rules:
- Use only what the lesson text teaches. Never add a formula, value, law,
  definition or method the lesson text does not contain.
- On a teaching day, the tasks cover only that day's content, never anything
  from later days.
- On a review day, the tasks may combine any topics taught up to that day
  (listed in its prompt), still only as the lesson text presents them.
- Every task is complete on its own: state every value and condition the
  student needs. Never point to the textbook, its exercises, examples,
  figures, tables, pages or question numbers, and never write "as done in
  class" or "the question above".
- A student does it at home alone with a notebook and pen: no lab
  equipment, no internet, no other people.
- Each task takes about 10 to 15 minutes.
- Every numerical must be solvable from the data given, with consistent
  units and realistic values. Solve it yourself before writing it.
- A task never states the formula or method to use: choosing it is part of
  the homework, and naming it is the hint's job.
- The hint is a nudge for a stuck student: which idea or formula to use, or
  the first step. It never states the answer itself: no final value, no
  worked-out step, and for an explain task never the explanation the
  student must give.
- Ignore classroom instructions in the lesson text (pair work, timings,
  cold-calls, exit tickets), and never copy an in-class question word for word.
- A concept task may use the lesson's own example (often the only one it
  teaches) but must ask something the class did not: a changed condition,
  a 'why', or a comparison. Never bring in a new example the lesson does
  not support.
- Do not repeat a task idea already used on another day of this lesson.
- Never use double quotation marks (") inside a task or hint. For quoted
  speech or a statement to judge, use single quotes: 'A friend says: ...'.
- Write powers with superscript characters: 10⁻¹⁹, m s⁻², m², x³. Never
  write them flat (10−19, s−1, m2). Keep subscripts as the lesson writes them.
- Plain English a student of this age reads easily. {language_rule}{extra_rules}"""

REVIEW_TEMPLATE = """You are a strict {subject} teacher in {local_context}, checking
daily homework before students see it. Solve every numerical fully in your
notes before judging it. Flag only real problems:
- a task that needs content the lesson does not teach (on a teaching day:
  anything not in that day's text; on a review day: anything outside the
  topics taught so far)
- a {subject} statement that is wrong, or that contradicts the lesson text
- a numerical that cannot be solved from the data given, or has missing,
  inconsistent or unrealistic values or units
- a task that points to the textbook (an exercise, example, figure, table,
  page or question number) or depends on something it does not give
- a task a student cannot do at home alone with a notebook and pen
- a numerical that repeats an in-class problem from the lesson text with the
  same values, or any task that asks the same question the class already
  answered. A concept task may reuse the lesson's own example (often the only
  one it teaches) when it asks something new about it: never flag that.
- a task that does not match its kind ({kinds})
- a task that states the formula or method to use (that belongs in the hint)
- a hint that states the answer itself: the final value, a worked-out step,
  or (for an explain task) the explanation the student is asked to give.
  Naming the idea or formula to use, or the first step, is the intended
  kind of hint: never flag that.
- a hint that is wrong or misleading, or does not help with its task
Do not flag style, length or wording. For each problem, say in one sentence
what is wrong and how to fix it.
Do your thinking in notes. List in problems only errors you are sure of;
if you conclude a field is fine, do not list it."""

ANSWER_TEMPLATE = """You write the answers to daily homework for {audience}.
Every task below was already checked and approved by teachers: answer it
exactly as written, never change or reinterpret it.

Rules:
- Use only what the lesson text teaches: its formulas, symbols, units,
  values and explanations. Never add a law, formula or fact the lesson
  does not contain.
- Apply tasks: a short worked answer. Put each step on its own line: the
  idea or formula used, the substitution with units, the result. For a
  numerical, end with a line starting 'Final answer:' that gives every
  final value with its unit, one per part ((a), (b), ...). Follow the
  approach the hint suggests.
- Understand tasks: a model answer of 3 to 4 sentences that a good student
  would write, answering every part of the task.
- Work every calculation carefully and check it before writing. Round
  sensibly (2 to 3 significant figures) and keep units throughout.
- Never use double quotation marks ("); use single quotes if you must quote.
- Write powers with superscript characters: 10⁻¹⁹, m s⁻², m², x³. Never
  write them flat (10−19, s−1, m2). Keep subscripts as the lesson writes them.
- Plain English a student of this age reads easily. English only.{extra_rules}"""

ANSWER_REVIEW_TEMPLATE = """You are a strict {subject} teacher in {local_context},
checking the answers to daily homework before students see them.
For every task, FIRST solve it yourself in your notes, using only the lesson
text, before you look at the given answer. THEN compare your result with the
given answer. Flag only real problems:
- a wrong final value, a wrong or missing unit, or a calculation error
- a wrong step or formula, or a skipped step a student would need
- a part of the task, such as (a) or (b), left unanswered
- a statement that is wrong, contradicts the lesson, or uses ideas the
  lesson does not teach
- an answer to a different question from the task as written
Rounding differences within about 2% are not errors. Do not flag style,
length or wording. For each problem, say in one sentence what is wrong and
what the correct result is.
List in problems only errors you are sure of; if an answer is correct, do
not list it."""


def _words(s: str) -> int:
    return len((s or "").split())


class HomeworkBuilder:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        print(f"✅ Homework Builder initialized — model: {self.model}")

    # ── Fields ───────────────────────────────────────────────
    @staticmethod
    def _fields(p: SubjectProfile) -> List[str]:
        out = []
        for key, _, _ in p.tasks:
            out.append(f"{key}_task")
            if p.hints:
                out.append(f"{key}_hint")
                if p.tamil_hint:
                    out.append(f"{key}_hint_ta")
        return out

    # ── Prompt pieces ────────────────────────────────────────
    def _system(self, p: SubjectProfile) -> str:
        audience = p.audience or f"{p.display_name or p.key} students"
        task_list = "\n".join(f"{i}. {label} task: {guide}"
                              for i, (_, label, guide) in enumerate(p.tasks, 1))
        language_rule = ("Each hint also gets a hint_ta field: the same hint in simple written "
                         "Tamil, technical terms in English. Everything else is English."
                         if p.tamil_hint else "English only: no Tamil anywhere.")
        return SYSTEM_TEMPLATE.format(audience=audience, n=len(p.tasks), task_list=task_list,
                                      language_rule=language_rule, extra_rules=p.extra_rules)

    def _homework_tool(self, p: SubjectProfile) -> dict:
        props = {"day": {"type": "integer"}}
        for key, label, guide in p.tasks:
            props[f"{key}_task"] = {"type": "string", "description":
                f"The {label} task. {guide} Complete on its own, every value given. "
                f"No double quotation marks; use single quotes for quoted speech. "
                f"Max {p.limit('MAX_TASK_WORDS')} words."}
            if p.hints:
                props[f"{key}_hint"] = {"type": "string", "description":
                    f"A nudge for the {label} task: which idea or formula to use, or the first "
                    f"step. Never the answer. No double quotation marks. "
                    f"Max {p.limit('MAX_HINT_WORDS')} words."}
                if p.tamil_hint:
                    props[f"{key}_hint_ta"] = {"type": "string", "description":
                        f"The {label} hint in simple written Tamil, technical terms in English."}
        return {
            "name": "write_homework",
            "description": "Return the homework for each lesson day.",
            "input_schema": {
                "type": "object",
                "properties": {"days": {"type": "array", "items": {
                    "type": "object", "properties": props, "required": list(props)}}},
                "required": ["days"],
            },
        }

    def _review_tool(self, p: SubjectProfile) -> dict:
        return {
            "name": "review_homework",
            "description": "Return one review per day.",
            "input_schema": {
                "type": "object",
                "properties": {"reviews": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "day": {"type": "integer"},
                        "notes": {"type": "string", "description":
                                  "Your working: solve each numerical, check each task and hint "
                                  "against the lesson. Think here, never in problems."},
                        "problems": {"type": "array", "description":
                                     "Only confirmed errors. Empty when the homework is correct.",
                                     "items": {"type": "object", "properties": {
                                         "field": {"type": "string", "enum": self._fields(p)},
                                         "problem": {"type": "string", "description":
                                                     "One sentence: what is wrong and how to fix it."},
                                     }, "required": ["field", "problem"]}},
                    },
                    "required": ["day", "notes", "problems"],
                }}},
                "required": ["reviews"],
            },
        }

    @staticmethod
    def _scope(d: Dict, topics: List[Tuple[int, str, str]]) -> str:
        if not d["is_review"]:
            return "Teaching day: the tasks cover only this day's content."
        so_far = [f"- Day {n}: {t}" + (f" ({ty})" if ty else "")
                  for n, t, ty in topics if n <= d["day"]]
        return ("REVIEW day: the tasks may combine any of these topics taught so far:\n"
                + "\n".join(so_far))

    def _days_prompt(self, batch: List[Dict], feedback: Dict[int, List[str]],
                     used: List[str], topics: List[Tuple[int, str, str]]) -> str:
        parts = [f"Write the homework for each of these {len(batch)} lesson days. "
                 f"Use each day's number as its day."]
        if used:
            parts.append("Other days of this lesson already have these tasks. Do not repeat "
                         "their ideas:\n" + "\n".join(f"- {u}" for u in used))
        for d in batch:
            block = [f"\n=== DAY {d['day']}: {d['title']} ===",
                     f"Day type: {d['day_type'] or '-'}",
                     self._scope(d, topics)]
            if d["day"] in feedback:
                block.append("Your previous homework for this day had problems — fix them: "
                             + "; ".join(feedback[d["day"]]))
            block.append("Lesson text:\n" + d["text"])
            parts.append("\n".join(block))
        return "\n".join(parts)

    # ── Checks ───────────────────────────────────────────────
    def _check(self, h: dict, p: SubjectProfile) -> List[str]:
        """Returns hard problems. Small length overflows go to h['warnings'] instead."""
        probs: List[str] = []
        warns: List[str] = []

        def length(field: str, value: str, limit: int):
            n = _words(value)
            if n > limit * HARD_FACTOR:
                probs.append(f"{field} too long ({n} words, max {limit})")
            elif n > limit:
                warns.append(f"{field} slightly long ({n} words, max {limit})")

        for key, label, _ in p.tasks:
            task = (h.get(f"{key}_task") or "").strip()
            if not task:
                probs.append(f"{key}_task is empty")
                continue
            length(f"{key}_task", task, p.limit("MAX_TASK_WORDS"))
            ref = BOOK_REF_RE.search(task)
            if ref:
                probs.append(f'{key}_task points to the textbook ("{ref.group(0)}…") — '
                             f"write the question out in full")
            if TAMIL_RE.search(task):
                probs.append(f"{key}_task must be in English")
            flat = FLAT_POWER_RE.search(task + " " + (h.get(f"{key}_hint") or ""))
            if flat:
                probs.append(f'{key} has a flat power ("{flat.group(0)}") — {POWER_RULE}')
            if not p.hints:
                continue
            hint = (h.get(f"{key}_hint") or "").strip()
            if not hint:
                probs.append(f"{key}_hint is empty")
                continue
            length(f"{key}_hint", hint, p.limit("MAX_HINT_WORDS"))
            if hint.lower() == task.lower():
                probs.append(f"{key}_hint only repeats the task — give a nudge")
            if TAMIL_RE.search(hint):
                probs.append(f"{key}_hint must be in English")
            if p.tamil_hint and not TAMIL_RE.search(h.get(f"{key}_hint_ta") or ""):
                probs.append(f"{key}_hint_ta must be written in Tamil")
        h["warnings"] = warns
        return probs

    def _review(self, days: List[Dict], homework: Dict[int, dict],
                topics: List[Tuple[int, str, str]], p: SubjectProfile) -> Dict[int, List[str]]:
        """Check homework against the lesson. Returns {day: [problems]} for flagged days."""
        if not days:
            return {}
        subject = p.display_name or p.key
        kinds = "; ".join(f"{label}: {guide}" for _, label, guide in p.tasks)
        system = REVIEW_TEMPLATE.format(subject=subject, local_context=p.local_context, kinds=kinds)
        parts = [f"Check the homework for these {len(days)} days. Return one review per day."]
        for d in days:
            hw = {f: homework[d["day"]].get(f, "") for f in self._fields(p)}
            parts.append(f"\n=== DAY {d['day']}: {d['title']} ===\n{self._scope(d, topics)}\n"
                         f"Homework:\n" + json.dumps(hw, ensure_ascii=False, indent=1)
                         + "\nLesson text:\n" + d["text"])
        data = self._call_tool(system, "\n".join(parts), self._review_tool(p), 8000)
        if data is None:
            # Fail closed: unchecked homework goes back for another attempt, never straight out.
            print("      ⚠️  Review call failed — homework sent back, not accepted unchecked")
            return {d["day"]: [REVIEW_FAILED] for d in days}
        out: Dict[int, List[str]] = {}
        seen = set()
        reviews = data.get("reviews", [])
        if isinstance(reviews, str):
            try:
                reviews = json.loads(reviews)
            except ValueError:
                reviews = []
        for r in reviews if isinstance(reviews, list) else []:
            if not isinstance(r, dict):
                continue
            try:
                n = int(r.get("day"))
            except (TypeError, ValueError):
                continue
            seen.add(n)
            probs = [f"[{x.get('field', '?')}] {x['problem']}"
                     for x in (r.get("problems") or [])
                     if isinstance(x, dict) and x.get("problem")]
            if probs:
                out[n] = probs
        # A day the reviewer left out was never checked: send it back, never pass it.
        for d in days:
            if d["day"] not in seen:
                out[d["day"]] = [REVIEW_FAILED]
        return out

    @staticmethod
    def _days_from(data) -> Dict[int, dict]:
        """Writer reply -> {day: homework}. Handles the list arriving as a JSON string
        and day numbers arriving as text."""
        raw = (data or {}).get("days", [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except ValueError:
                return {}
        out: Dict[int, dict] = {}
        for h in raw if isinstance(raw, list) else []:
            if not isinstance(h, dict):
                continue
            try:
                out[int(h.get("day"))] = h
            except (TypeError, ValueError):
                continue
        return out

    @staticmethod
    def _soft(probs: List[str]) -> bool:
        """Only length issues: still usable after the last retry."""
        return all("too long" in x for x in probs)

    # ── Generation ───────────────────────────────────────────
    def _generate_days(self, days: List[Dict], topics: List[Tuple[int, str, str]],
                       p: SubjectProfile):
        system, tool = self._system(p), self._homework_tool(p)
        pending = {d["day"]: d for d in days}
        done: Dict[int, dict] = {}
        last: Dict[int, tuple] = {}
        feedback: Dict[int, List[str]] = {}

        for attempt in range(MAX_RETRIES + 1):
            todo = [pending[k] for k in sorted(pending)]
            if not todo:
                break
            if attempt:
                print(f"   🔁 Retry {attempt}: days {[d['day'] for d in todo]}")
            for i in range(0, len(todo), p.batch_size):
                batch = todo[i:i + p.batch_size]
                in_batch = {d["day"] for d in batch}
                used = [f"Day {n}: " + " | ".join(" ".join((h.get(f"{k}_task") or "").split()[:15])
                                                  for k, _, _ in p.tasks)
                        for n, h in sorted(done.items()) if n not in in_batch]
                data = self._call_tool(system, self._days_prompt(batch, feedback, used, topics),
                                       tool, 6000)
                got = self._days_from(data)
                if not got:
                    print(f"      ⚠️  Writer returned no usable days for {sorted(in_batch)}: "
                          f"{str(data)[:300]!r}")
                checked: Dict[int, tuple] = {}
                for d in batch:
                    n = d["day"]
                    h = got.get(n)
                    if h is None:
                        feedback[n] = ["the homework was missing — write it"]
                        continue
                    checked[n] = (h, self._check(h, p))

                # Review every day whose only code issues are small length overflows.
                to_review = [d for d in batch
                             if d["day"] in checked and self._soft(checked[d["day"]][1])]
                verdicts = self._review(to_review, {n: v[0] for n, v in checked.items()}, topics, p)
                for n, rprobs in verdicts.items():
                    if n in checked:
                        checked[n][1].extend(f"review: {x}" for x in rprobs)

                for n, (h, probs) in checked.items():
                    last[n] = (h, probs)
                    if probs:
                        # A failed review call is not the homework's fault: retry without blaming it.
                        fb = [x for x in probs if REVIEW_FAILED not in x]
                        if fb:
                            feedback[n] = fb
                        else:
                            feedback.pop(n, None)
                        print(f"      day {n} — {'; '.join(probs)}")
                    else:
                        done[n] = h
                        pending.pop(n, None)
                        feedback.pop(n, None)

        skipped = []
        for n in sorted(pending):
            h, probs = last.get(n, (None, ["no homework returned"]))
            if h is not None and self._soft(probs):
                h["warnings"] = h.get("warnings", []) + probs
                done[n] = h
            else:
                skipped.append({"day": n, "reasons": probs})
        return done, skipped

    def generate(self, lp_path: str, lesson: Dict, only_days: Optional[List[int]] = None) -> Dict:
        p = get_profile(lesson.get("subject", ""))
        lp = load_lp(lp_path, lesson.get("subject", ""))
        topics = [(d["day"], d["title"], d["day_type"]) for d in lp["days"]]
        days = lp["days"]
        if only_days:
            days = [d for d in days if d["day"] in only_days]
        title = lesson.get("title", "")
        print(f"[Homework] {title} — {len(days)} days (profile: {p.key})")
        cut = [d["day"] for d in days if d["truncated"]]
        if cut:
            print(f"   ⚠️  Lesson text cut for days {cut} — raise the profile's limit if needed")

        done, skipped = self._generate_days(days, topics, p)

        out_days = []
        for d in days:
            h = done.get(d["day"])
            if h is None:
                continue
            tasks = []
            for key, label, _ in p.tasks:
                t = {"kind": key, "label": label, "task": (h.get(f"{key}_task") or "").strip()}
                if p.hints:
                    t["hint"] = (h.get(f"{key}_hint") or "").strip()
                    if p.tamil_hint:
                        t["hint_ta"] = (h.get(f"{key}_hint_ta") or "").strip()
                tasks.append(t)
            out_days.append({
                "day": d["day"],
                "title": d["title"],
                "day_type": d["day_type"],
                "is_review": d["is_review"],
                "tasks": tasks,
                "warnings": h.get("warnings", []),
            })

        return {
            "lesson": lesson,
            "subject": p.key,
            "task_kinds": [{"key": k, "label": l} for k, l, _ in p.tasks],
            "days": out_days,
            "skipped_days": skipped,
            "model": self.model,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }

    # ── Answers (a separate pass over already-approved tasks) ─
    @staticmethod
    def _by_day(data, key: str) -> Dict[int, dict]:
        """Tool reply -> {day: item} for data[key]. Handles the list arriving as a JSON
        string and day numbers arriving as text."""
        raw = (data or {}).get(key, [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except ValueError:
                return {}
        out: Dict[int, dict] = {}
        for item in raw if isinstance(raw, list) else []:
            if not isinstance(item, dict):
                continue
            try:
                out[int(item.get("day"))] = item
            except (TypeError, ValueError):
                continue
        return out

    def _answer_system(self, p: SubjectProfile) -> str:
        audience = p.audience or f"{p.display_name or p.key} students"
        return ANSWER_TEMPLATE.format(audience=audience, extra_rules=p.extra_rules)

    def _answer_tool(self, p: SubjectProfile) -> dict:
        props = {"day": {"type": "integer"}}
        for key, label, _ in p.tasks:
            props[f"{key}_answer"] = {"type": "string", "description":
                f"The answer to the {label} task, only if it is listed for this day. "
                f"Steps on separate lines. No double quotation marks. "
                f"Max {p.limit('MAX_ANSWER_WORDS')} words."}
        return {
            "name": "write_answers",
            "description": "Return the answers for each lesson day.",
            "input_schema": {
                "type": "object",
                "properties": {"answers": {"type": "array", "items": {
                    "type": "object", "properties": props, "required": ["day"]}}},
                "required": ["answers"],
            },
        }

    def _answer_review_tool(self, p: SubjectProfile) -> dict:
        return {
            "name": "review_answers",
            "description": "Return one review per day.",
            "input_schema": {
                "type": "object",
                "properties": {"reviews": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "day": {"type": "integer"},
                        "notes": {"type": "string", "description":
                                  "Your own full solution of each task first, then the "
                                  "comparison with the given answer. Think here, never in problems."},
                        "problems": {"type": "array", "description":
                                     "Only confirmed errors. Empty when every answer is correct.",
                                     "items": {"type": "object", "properties": {
                                         "field": {"type": "string",
                                                   "enum": [f"{k}_answer" for k, _, _ in p.tasks]},
                                         "problem": {"type": "string", "description":
                                                     "One sentence: what is wrong and what the "
                                                     "correct result is."},
                                     }, "required": ["field", "problem"]}},
                    },
                    "required": ["day", "notes", "problems"],
                }}},
                "required": ["reviews"],
            },
        }

    def _answers_prompt(self, days: List[int], wanted: Dict[int, List[str]],
                        tasks: Dict[int, Dict[str, dict]], lp_days: Dict[int, Dict],
                        topics: List[Tuple[int, str, str]], feedback: Dict[int, List[str]],
                        given: Optional[Dict[tuple, str]] = None) -> str:
        if given is None:
            parts = [f"Write the answers for the tasks below, for {len(days)} lesson days. "
                     f"Use each day's number as its day, and fill only the answer fields listed."]
        else:
            parts = [f"Check the answers below, for {len(days)} lesson days. "
                     f"Return one review per day."]
        for n in days:
            d = lp_days[n]
            block = [f"\n=== DAY {n}: {d['title']} ===", self._scope(d, topics)]
            for k in wanted[n]:
                t = tasks[n][k]
                block.append(f"[{k}_answer] {t['label']} task: {t['task']}")
                if t.get("hint"):
                    block.append(f"   Hint given to students: {t['hint']}")
                if given is not None:
                    block.append(f"   Given answer:\n{given[(n, k)]}")
            if given is None and n in feedback:
                block.append("Your previous answers for this day had problems — fix them: "
                             + "; ".join(feedback[n]))
            block.append("Lesson text:\n" + d["text"])
            parts.append("\n".join(block))
        return "\n".join(parts)

    def _check_answer(self, a: str, p: SubjectProfile) -> List[str]:
        if not a:
            return ["answer is empty"]
        probs = []
        n, limit = _words(a), p.limit("MAX_ANSWER_WORDS")
        if n > limit * HARD_FACTOR:
            probs.append(f"answer too long ({n} words, max {limit})")
        if TAMIL_RE.search(a):
            probs.append("answer must be in English")
        flat = FLAT_POWER_RE.search(a)
        if flat:
            probs.append(f'answer has a flat power ("{flat.group(0)}") — {POWER_RULE}')
        return probs

    def _review_answers(self, keys: List[tuple], given: Dict[tuple, str],
                        tasks: Dict[int, Dict[str, dict]], lp_days: Dict[int, Dict],
                        topics: List[Tuple[int, str, str]], p: SubjectProfile) -> Dict[tuple, List[str]]:
        """Reviewer solves each task itself, then compares. Returns {(day, kind): [problems]}."""
        if not keys:
            return {}
        by_day: Dict[int, List[str]] = {}
        for n, k in keys:
            by_day.setdefault(n, []).append(k)
        days = sorted(by_day)
        subject = p.display_name or p.key
        system = ANSWER_REVIEW_TEMPLATE.format(subject=subject, local_context=p.local_context)
        prompt = self._answers_prompt(days, by_day, tasks, lp_days, topics, {}, given)
        data = self._call_tool(system, prompt, self._answer_review_tool(p), 12000)
        if data is None:
            print("      ⚠️  Answer review call failed — answers sent back, not accepted unchecked")
            return {key: [REVIEW_FAILED] for key in keys}
        reviews = self._by_day(data, "reviews")
        out: Dict[tuple, List[str]] = {}
        for n in days:
            r = reviews.get(n)
            if r is None:
                # A day the reviewer left out was never checked: send it back.
                for k in by_day[n]:
                    out[(n, k)] = [REVIEW_FAILED]
                continue
            for x in r.get("problems") or []:
                if not (isinstance(x, dict) and x.get("problem")):
                    continue
                k = str(x.get("field", "")).replace("_answer", "")
                if k in by_day[n]:
                    out.setdefault((n, k), []).append(x["problem"])
        return out

    def generate_answers(self, lp_path: str, deck: Dict) -> Dict:
        """Fill missing answers in a homework deck, in place. Tasks and hints are never
        changed. Unconfirmed answers are left out and listed in deck['answers_pending']."""
        subject = deck.get("subject") or (deck.get("lesson") or {}).get("subject", "")
        p = get_profile(subject)
        if not p.answers:
            return {"wanted": 0, "made": 0, "pending": []}
        lp = load_lp(lp_path, subject)
        topics = [(d["day"], d["title"], d["day_type"]) for d in lp["days"]]
        lp_days = {d["day"]: d for d in lp["days"]}
        tasks = {d["day"]: {t["kind"]: t for t in d["tasks"]} for d in deck.get("days", [])}

        pending: Dict[int, List[str]] = {}
        for n, by_kind in tasks.items():
            keys = [k for k, t in by_kind.items() if not (t.get("answer") or "").strip()]
            if keys and n in lp_days:
                pending[n] = keys
        wanted = sum(len(v) for v in pending.values())
        deck["answers"] = True
        if not wanted:
            deck["answers_pending"] = []
            return {"wanted": 0, "made": 0, "pending": []}
        print(f"[Homework answers] {wanted} answers for days {sorted(pending)}")

        system, tool = self._answer_system(p), self._answer_tool(p)
        feedback: Dict[int, List[str]] = {}
        last: Dict[tuple, tuple] = {}
        made = 0

        for attempt in range(MAX_RETRIES + 1):
            todo = sorted(pending)
            if not todo:
                break
            if attempt:
                print(f"   🔁 Answer retry {attempt}: days {todo}")
            for i in range(0, len(todo), p.batch_size):
                batch = todo[i:i + p.batch_size]
                data = self._call_tool(system, self._answers_prompt(
                    batch, pending, tasks, lp_days, topics, feedback), tool, 8000)
                got = self._by_day(data, "answers")
                if not got:
                    print(f"      ⚠️  Answer writer returned nothing usable for {batch}: "
                          f"{str(data)[:300]!r}")

                cand: Dict[tuple, str] = {}
                probs: Dict[tuple, List[str]] = {}
                for n in batch:
                    for k in pending[n]:
                        a = ((got.get(n) or {}).get(f"{k}_answer") or "").strip()
                        cand[(n, k)] = a
                        probs[(n, k)] = self._check_answer(a, p)

                to_review = [key for key, pr in probs.items() if cand[key] and self._soft(pr)]
                for key, rp in self._review_answers(to_review, cand, tasks, lp_days, topics, p).items():
                    probs[key].extend(f"review: {x}" for x in rp)

                for n in batch:
                    feedback.pop(n, None)
                for (n, k), pr in probs.items():
                    last[(n, k)] = (cand[(n, k)], pr)
                    if pr:
                        fb = [f"[{k}_answer] {x}" for x in pr if REVIEW_FAILED not in x]
                        if fb:
                            feedback.setdefault(n, []).extend(fb)
                        print(f"      day {n} {k} — {'; '.join(pr)}")
                    else:
                        tasks[n][k]["answer"] = cand[(n, k)]
                        made += 1
                        pending[n].remove(k)
                for n in batch:
                    if not pending[n]:
                        pending.pop(n)

        still = []
        for n in sorted(pending):
            for k in pending[n]:
                a, pr = last.get((n, k), ("", ["no answer returned"]))
                if a and self._soft(pr):
                    tasks[n][k]["answer"] = a        # only a small length overflow
                    made += 1
                else:
                    still.append({"day": n, "kind": k, "reasons": pr})
        deck["answers_pending"] = still
        print(f"   ✅ Answers: {made}/{wanted} confirmed"
              + (f", pending {[(s['day'], s['kind']) for s in still]}" if still else ""))
        return {"wanted": wanted, "made": made, "pending": still}

    # ── API ──────────────────────────────────────────────────
    def _call_tool(self, system: str, prompt: str, tool: dict, max_tokens: int) -> Optional[dict]:
        for attempt in range(1, API_ATTEMPTS + 1):
            try:
                resp = self.client.messages.create(
                    model=self.model, max_tokens=max_tokens, system=system,
                    tools=[tool], tool_choice={"type": "tool", "name": tool["name"]},
                    messages=[{"role": "user", "content": prompt}],
                )
                if resp.stop_reason == "max_tokens":
                    print("         ⚠️  Output cut off at max_tokens — response may be incomplete")
                for block in resp.content:
                    if block.type == "tool_use":
                        return block.input
                return None
            except (httpx.HTTPError, anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
                print(f"         ⚠️  Network error (attempt {attempt}): {e}")
            except anthropic.APIStatusError as e:
                if e.status_code not in (429, 500, 502, 503, 529):
                    raise
                print(f"         ⚠️  API {e.status_code} (attempt {attempt})")
            if attempt < API_ATTEMPTS:
                time.sleep(API_BACKOFF)
        return None


homework_builder = HomeworkBuilder()