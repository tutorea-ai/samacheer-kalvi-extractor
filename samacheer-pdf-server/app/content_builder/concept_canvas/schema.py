"""Concept Canvas: contract v1 in code.

The single Python source of the Node contract ("Concept Canvas — JSON
Contract v1"): templates, field limits, icons and the formula check.
Change anything here only together with the contract doc and the Node team.

validate_day() returns (problems, warnings):
  problems -> the day is retried, then skipped (fail closed)
  warnings -> small issues already fixed in place (e.g. unknown icon removed)
"""
import re
from collections import Counter
from functools import reduce
from itertools import product
from math import gcd
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
    "punnett": ("parent_1", "parent_1_label", "parent_2", "parent_2_label",
                "gametes_1", "gametes_2", "grid", "phenotypes", "ratio"),
}
TEMPLATE_STEP_FIELDS: Dict[str, Tuple[str, ...]] = {
    "compare": ("side",),
    "timeline": ("time",),
    "punnett": ("phase",),
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
        if f in DAY_LIMITS:          # punnett's structured fields are checked in check_punnett
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
            elif f == "phase":
                continue                     # checked in check_punnett
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

    if tpl == "punnett":
        p2, w2 = check_punnett(day)
        probs += p2
        warns += w2

    return probs, warns


# ── Punnett square (contract version 2) ──
PUNNETT_PHASES = ("parents", "gametes", "grid", "ratio")
LETHAL = "Lethal"                 # drawn in the grid, never counted in the ratio
MAX_PARENT, MAX_PHENOTYPE, MAX_RATIO = 12, 20, 30
# An allele is a letter plus optional digits (T, t, R₁, R₂); digits become subscripts.
_SUBDIGITS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
_ALLELE = re.compile(r"[A-Za-z][0-9₀-₉]*")
_GENOTYPE = re.compile(r"^(?:[A-Za-z][0-9₀-₉]*)+$")
_LABELLED = re.compile(r"^\s*([A-Za-z0-9₀-₉]+)\s*\((.+)\)\s*$")    # "Tt (Tall F1)"


def _tokens(genotype: str) -> List[str]:
    return [a.translate(_SUBDIGITS) for a in _ALLELE.findall(genotype)]


def _dom_first(alleles) -> List[str]:
    return sorted(alleles, key=lambda a: (a[0].islower(), a))


def _norm(genotype: str, order: List[str]) -> str:
    """Group alleles by gene in `order`, dominant (capital) first: tTyY -> TtYy, R2R1 -> R₁R₂."""
    by: Dict[str, List[str]] = {}
    for a in _tokens(genotype):
        by.setdefault(a[0].lower(), []).append(a)
    return "".join("".join(_dom_first(by.get(g, []))) for g in order)


def _gametes(parent: str, order: List[str]) -> List[str]:
    toks = _tokens(parent)
    alleles = [_dom_first({a for a in toks if a[0].lower() == g}) for g in order]
    return sorted({"".join(p) for p in product(*alleles)})


def _parent_from(gametes: List[str], order: List[str]):
    """The one genotype whose gametes are exactly this set (R₁, R₂ -> R₁R₂), or None."""
    genes = []
    for i, g in enumerate(order):
        alleles = {_tokens(x)[i] for x in gametes}
        if not 1 <= len(alleles) <= 2 or any(a[0].lower() != g for a in alleles):
            return None
        a = _dom_first(alleles)
        genes.append(a * 2 if len(a) == 1 else a)
    parent = "".join("".join(x) for x in genes)
    return parent if sorted(gametes) == _gametes(parent, order) else None


def check_punnett(day: Dict) -> Tuple[List[str], List[str]]:
    """Verify a punnett day mechanically. Fixes letter order in place."""
    probs: List[str] = []
    warns: List[str] = []

    # Parents ("Tt (Tall F1)" is split into genotype + label for free)
    for key in ("parent_1", "parent_2"):
        v = day.get(key)
        m = _LABELLED.match(v) if isinstance(v, str) else None
        if m:
            day[key] = m.group(1)
            day.setdefault(f"{key}_label", m.group(2).strip())
            warns.append(f"{key} label moved to {key}_label")
        v = day.get(key)
        if (not isinstance(v, str) or not _GENOTYPE.match(v) or len(v) > MAX_PARENT
                or len(_tokens(v)) % 2):
            probs.append(f"{key} must be alleles only (T, t, R1), two per gene, max {MAX_PARENT}: {v!r}")
        lab = day.get(f"{key}_label")
        if lab is not None and (not isinstance(lab, str) or not lab.strip() or len(lab) > MAX_PHENOTYPE):
            probs.append(f"{key}_label must be 1-{MAX_PHENOTYPE} characters")
    if probs:
        return probs, warns
    order = list(dict.fromkeys(a[0].lower() for a in _tokens(day["parent_1"])))
    if set(order) != {a[0].lower() for a in _tokens(day["parent_2"])}:
        probs.append("both parents must carry the same genes")
    if len(order) > 2:
        probs.append("at most two genes (a 4 x 4 grid)")
    for key in ("parent_1", "parent_2"):
        for g in order:
            if sum(a[0].lower() == g for a in _tokens(day[key])) != 2:
                probs.append(f"{key} needs exactly two alleles for gene {g.upper()}")
    if probs:
        return probs, warns
    for key in ("parent_1", "parent_2"):
        n = _norm(day[key], order)
        if n != day[key]:
            warns.append(f"{key} {day[key]!r} written as {n!r}")
            day[key] = n

    # Gametes. One known slip is fixed in place: an F₂ grid drawn under the P-generation
    # parents (R₁R₁ × R₂R₂ with R₁, R₂ gametes on both sides). Only when BOTH parents fail,
    # both derive from their gametes, and the two derived genotypes are identical; then
    # the parents are just the grid's header. Anything else goes to the retry (fail closed).
    pairs = (("gametes_1", "parent_1"), ("gametes_2", "parent_2"))
    norm: Dict[str, List[str]] = {}
    for key, pkey in pairs:
        g = day.get(key)
        if not isinstance(g, list) or not all(isinstance(x, str) for x in g):
            probs.append(f"{key} must be a list of gametes")
            continue
        got = [_norm(x, order) for x in g]
        if len(got) == len(set(got)) and all(len(_tokens(x)) == len(order) for x in got):
            norm[key] = got
    if probs:
        return probs, warns
    if (len(norm) == 2
            and all(sorted(norm[k]) != _gametes(day[p], order) for k, p in pairs)):
        derived = [_parent_from(norm[k], order) for k, _ in pairs]
        if derived[0] and derived[0] == derived[1]:
            for (_, pkey), d in zip(pairs, derived):
                warns.append(f"{pkey} {day[pkey]!r} changed to {d!r} to match its gametes")
                day[pkey] = d
                lab = day.pop(f"{pkey}_label", None)
                if lab is not None:
                    warns.append(f"{pkey}_label {lab!r} removed: parent derived from gametes")
    for key, pkey in pairs:
        parent = day[pkey]
        if key not in norm or sorted(norm[key]) != _gametes(parent, order):
            probs.append(f"{key} {day[key]} are not the gametes of {parent} "
                         f"(expected {_gametes(parent, order)})")
        else:
            day[key] = norm[key]
    if probs:
        return probs, warns

    # Grid: every cell = row gamete + column gamete
    g1, g2 = day["gametes_1"], day["gametes_2"]
    grid = day.get("grid")
    if not (isinstance(grid, list) and len(grid) == len(g2)
            and all(isinstance(r, list) and len(r) == len(g1) for r in grid)):
        probs.append(f"grid must be {len(g2)} rows x {len(g1)} columns")
        return probs, warns
    reordered = False
    for r, rg in enumerate(g2):
        for c, cg in enumerate(g1):
            want = _norm(rg + cg, order)
            cell = grid[r][c]
            if not isinstance(cell, str) or len(_tokens(cell)) != 2 * len(order) or _norm(cell, order) != want:
                probs.append(f"grid[{r}][{c}] is {cell!r}, should be {want!r}")
            elif cell != want:
                grid[r][c] = want
                reordered = True
    if reordered:
        warns.append("grid genotypes rewritten dominant letter first")
    if probs:
        return probs, warns

    # Phenotypes: every cell has one; keys normalised; unused removed
    ph = day.get("phenotypes")
    if not isinstance(ph, dict):
        probs.append("phenotypes must map every genotype in the grid to a trait")
        return probs, warns
    ph = {_norm(k, order): v for k, v in ph.items() if isinstance(k, str)}
    cells = [x for row in grid for x in row]
    missing = sorted({x for x in cells if x not in ph})
    if missing:
        probs.append(f"phenotypes missing for {missing}")
    for k, v in ph.items():
        if not isinstance(v, str) or not v.strip() or len(v) > MAX_PHENOTYPE:
            probs.append(f"phenotype for {k} must be 1-{MAX_PHENOTYPE} characters")
    unused = [k for k in ph if k not in cells]
    for k in unused:
        ph.pop(k)
    if unused:
        warns.append(f"unused phenotypes removed: {unused}")
    day["phenotypes"] = ph
    if probs:
        return probs, warns

    # Ratio: must match the real phenotype counts (Lethal excluded), any order
    counts = Counter(ph[x] for x in cells if ph[x] != LETHAL)
    nums = list(counts.values())
    k = reduce(gcd, nums) if nums else 1
    want_ratio = sorted(n // k for n in nums)
    r = day.get("ratio")
    try:
        got_ratio = sorted(int(x) for x in str(r).split(":"))
    except ValueError:
        got_ratio = None
    if not isinstance(r, str) or len(r) > MAX_RATIO or got_ratio != want_ratio:
        probs.append(f"ratio {r!r} does not match the grid (phenotype counts {dict(counts)})")

    # Steps: exactly the four phases in order; the ratio step is the highlight
    steps = day.get("steps") or []
    phases = [s.get("phase") for s in steps if isinstance(s, dict)]
    if phases != list(PUNNETT_PHASES):
        probs.append(f"punnett needs 4 steps with phases {list(PUNNETT_PHASES)}, got {phases}")
    elif steps[-1].get("highlight") is not True:
        for s in steps:
            s.pop("highlight", None)
        steps[-1]["highlight"] = True
        warns.append("highlight moved to the ratio step")
    return probs, warns