"""Concept Canvas: contract v1 in code.

The single Python source of the Node contract ("Concept Canvas — JSON
Contract v1"): templates, field limits, icons and the formula check.
Change anything here only together with the contract doc and the Node team.

validate_day() returns (problems, warnings):
  problems -> the day is retried, then skipped (fail closed)
  warnings -> small issues already fixed in place (e.g. unknown icon removed)
"""
import re
from typing import Dict, List, Tuple

from .subjects.base import SubjectProfile

CONTRACT_VERSION = 1
MODULE = "concept_canvas"

# ── Templates: extra day fields and extra step fields they require ──
TEMPLATE_DAY_FIELDS: Dict[str, Tuple[str, ...]] = {
    "step_build": (),
    "process_flow": (),
    "cycle": (),
    "compare": ("left_title", "right_title"),
    "timeline": (),
    "concept_map": ("center",),
}
TEMPLATE_STEP_FIELDS: Dict[str, Tuple[str, ...]] = {
    "compare": ("side",),
    "timeline": ("time",),
}

# ── Hard limits (characters). No tolerance: Node's layout depends on them ──
DAY_LIMITS = {"title": 40, "caption": 100, "left_title": 25, "right_title": 25, "center": 30}
STEP_LIMITS = {"label": 25, "text": 80, "time": 20}
MIN_STEPS, MAX_STEPS = 3, 6
MAX_FORMULA = 120

# ── Icons by group (same list as the contract doc) ──
ICONS: Dict[str, Tuple[str, ...]] = {
    "physics": ("battery", "resistor", "bulb", "wire", "switch", "ammeter",
                "voltmeter", "electron", "magnet", "lightning", "thermometer", "clock",
                "galvanometer"),
    "biology": ("cell", "dna", "chromosome", "leaf", "seed"),
    "general": ("idea", "question", "check", "warning", "book", "person",
                "globe", "sun", "water", "calendar", "star"),
}


def allowed_icons(profile: SubjectProfile) -> Tuple[str, ...]:
    out: List[str] = []
    for g in profile.icon_groups:
        out.extend(ICONS.get(g, ()))
    return tuple(out)


# ── Formula (LaTeX) check: what KaTeX will render ──
LATEX_COMMANDS = set("""
frac dfrac sqrt times cdot div pm mp propto approx neq ne leq le geq ge
sum int oint infty partial nabla to rightarrow leftarrow Rightarrow leftrightarrow
left right text mathrm mathbf vec overline bar hat dot ddot prime circ degree
quad qquad log ln sin cos tan exp lim cdots ldots parallel perp angle
implies iff Longrightarrow longrightarrow ll gg sim simeq equiv therefore because
alpha beta gamma delta epsilon varepsilon zeta eta theta kappa lambda mu nu xi
pi rho sigma tau phi varphi chi psi omega
Gamma Delta Theta Lambda Xi Pi Sigma Phi Psi Omega
""".split())
_CMD = re.compile(r"\\([A-Za-z]+)")
_TAMIL = re.compile(r"[\u0B80-\u0BFF]")
_RELATION = re.compile(r"=|<|>|\\(propto|approx|leq|geq|le|ge|neq|ne|equiv|sim|simeq)\b")
_TEXT_ARG = re.compile(r"\\text\{([^{}]*)\}")


def check_formula(f: str) -> List[str]:
    probs: List[str] = []
    if "$" in f:
        probs.append("formula contains '$' (send bare LaTeX)")
    if len(f) > MAX_FORMULA:
        probs.append(f"formula too long ({len(f)} > {MAX_FORMULA})")
    depth = 0
    for ch in f:
        depth += ch == "{"
        depth -= ch == "}"
        if depth < 0:
            break
    if depth != 0:
        probs.append("formula has unbalanced braces")
    unknown = sorted({c for c in _CMD.findall(f) if c not in LATEX_COMMANDS})
    if unknown:
        probs.append(f"formula uses unsupported commands: {unknown}")
    if not _RELATION.search(f):
        probs.append("formula is not a relation (needs =, \\propto, <, > …); put words in text")
    for t in _TEXT_ARG.findall(f):
        if len(t.split()) > 1:
            probs.append(f"formula has words in \\text{{{t}}}; put words in text")
    return probs


# ── Day validation ──
def _text_ok(name: str, value, limit: int, probs: List[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        probs.append(f"{name} is empty")
        return
    if len(value) > limit:
        probs.append(f"{name} too long ({len(value)} > {limit}): {value!r}")
    if "\\" in value or "$" in value:
        probs.append(f"{name} contains LaTeX; put formulas only in 'formula'")
    if "=" in value:
        probs.append(f"{name} contains an equation; put it in 'formula', keep text to words")
    if _TAMIL.search(value):
        probs.append(f"{name} contains Tamil (English only)")


def validate_day(day: Dict, profile: SubjectProfile) -> Tuple[List[str], List[str]]:
    """Check one day against the contract. Fixes small issues in place."""
    probs: List[str] = []
    warns: List[str] = []

    tpl = day.get("template")
    if tpl not in profile.allowed_templates:
        probs.append(f"template {tpl!r} not allowed for {profile.key}")
        return probs, warns

    if not isinstance(day.get("day"), int):
        probs.append("day is not an integer")
    _text_ok("title", day.get("title"), DAY_LIMITS["title"], probs)
    _text_ok("caption", day.get("caption"), DAY_LIMITS["caption"], probs)
    for f in TEMPLATE_DAY_FIELDS[tpl]:
        _text_ok(f, day.get(f), DAY_LIMITS[f], probs)

    steps = day.get("steps")
    if not isinstance(steps, list) or not (MIN_STEPS <= len(steps) <= MAX_STEPS):
        n = len(steps) if isinstance(steps, list) else 0
        probs.append(f"needs {MIN_STEPS}-{MAX_STEPS} steps, got {n}")
        return probs, warns

    icons = allowed_icons(profile)
    prev_icon = None
    for i, s in enumerate(steps, 1):
        tag = f"step {i}"
        if not isinstance(s, dict):
            probs.append(f"{tag} is not an object")
            continue
        _text_ok(f"{tag} label", s.get("label"), STEP_LIMITS["label"], probs)
        _text_ok(f"{tag} text", s.get("text"), STEP_LIMITS["text"], probs)
        for f in TEMPLATE_STEP_FIELDS.get(tpl, ()):
            if f == "side":
                if s.get("side") not in ("left", "right"):
                    probs.append(f"{tag} side must be 'left' or 'right'")
            else:
                _text_ok(f"{tag} {f}", s.get(f), STEP_LIMITS[f], probs)

        if "formula" in s:
            if not profile.formulas:
                s.pop("formula")
                warns.append(f"{tag} formula removed (formulas off for {profile.key})")
            elif not isinstance(s["formula"], str) or not s["formula"].strip():
                s.pop("formula")
                warns.append(f"{tag} empty formula removed")
            else:
                probs += [f"{tag} {p}" for p in check_formula(s["formula"])]

        if "icon" in s and s["icon"] not in icons:
            warns.append(f"{tag} icon {s['icon']!r} not in list, removed")
            s.pop("icon")
        this_icon = s.get("icon")
        if this_icon and this_icon == prev_icon:
            warns.append(f"{tag} icon {this_icon!r} repeats the previous step, removed")
            s.pop("icon")
        prev_icon = this_icon

        if "highlight" in s and s["highlight"] is not True:
            s.pop("highlight")

    hl = [s for s in steps if isinstance(s, dict) and s.get("highlight") is True]
    for s in hl[:-1]:
        s.pop("highlight")
    if len(hl) > 1:
        warns.append(f"{len(hl)} highlight steps, kept only the last")
    if tpl in ("step_build", "process_flow") and hl and steps[-1] is not hl[-1]:
        probs.append("the highlight must be the last step: step_build and process_flow end on the key idea")

    if tpl == "compare":
        sides = {s.get("side") for s in steps if isinstance(s, dict)}
        if sides != {"left", "right"}:
            probs.append("compare needs points on both sides")

    return probs, warns