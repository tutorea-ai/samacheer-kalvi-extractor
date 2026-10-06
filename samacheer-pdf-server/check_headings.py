"""
check_headings.py — diagnostic for the Physics LP per-day text slicing (v2).

Run from the Python server folder (samacheer-pdf-server), venv active:
    python3 check_headings.py

Reads the Class 12 Vol 1 EPUB folder, cuts out Unit 1 (Electrostatics) and
runs the builder's real heading locator for all 37 sections the extractor
found in the live run. No API calls, changes nothing.
"""
import os
import re

from bs4 import BeautifulSoup
from app.content_builder.physics.lp.grade_1112.physics import PhysicsLP1112Builder

ROOT = os.path.expanduser(
    "~/test_m1_and_m2/pdf_extractor/samacheer-kalvi-extractor/samacheer-pdf-server/"
    "storage/epub/class-12-term0-physics-english-vol1/class-12-term0-physics-english-vol1"
)

opf = open(os.path.join(ROOT, "content.opf"), encoding="utf-8").read()
hrefs = dict(re.findall(r'<item[^>]*id="([^"]+)"[^>]*href="([^"]+)"', opf))
hrefs.update({i: h for h, i in re.findall(r'<item[^>]*href="([^"]+)"[^>]*id="([^"]+)"', opf)})
spine = [hrefs[i] for i in re.findall(r'<itemref[^>]*idref="([^"]+)"', opf) if i in hrefs]

full = ""
for h in spine:
    p = os.path.join(ROOT, h)
    if os.path.exists(p) and p.lower().endswith(("html", "htm")):
        html = open(p, encoding="utf-8", errors="ignore").read()
        full += BeautifulSoup(html, "html.parser").get_text("\n") + "\n"

low = full.lower()
vdg = low.find("van de graaff")
end = low.find("current electricity", vdg) if vdg > 0 else -1
text = full[: end if end > 0 else len(full)]
print(f"spine docs={len(spine)}  text up to end of Unit 1 = {len(text)} chars")

HEADS = """Historical background of electric charges
Basic properties of charges
Coulomb's Law
Superposition principle
Electric Field
Electric field due to the system of point charges
Electric field due to continuous charge distribution
Electric field lines
Electric dipole
Electric field due to a dipole
Torque experienced by an electric dipole in the uniform electric field
Electrostatic Potential energy and Electrostatic potential
Electric potential due to a point charge
Electrostatic potential at a point due to an electric dipole
Equi-potential Surface
Relation between electric field and potential
Electrostatic potential energy for collection of point charges
Electrostatic potential energy of a dipole in a uniform electric field
Electric Flux
Electric flux for closed surfaces
Gauss law
Applications of Gauss law
Conductors at electrostatic equilibrium
Electrostatic shielding
Electrostatic induction
Dielectrics or insulators
Induced Electric field inside the dielectric
Dielectric strength
Capacitors
Energy stored in the capacitor
Applications of capacitors
Effect of dielectrics in capacitors
Capacitor in series and parallel
Distribution of charges in a conductor
Action of points or Corona discharge
Lightning arrester or lightning conductor
Van de Graaff Generator""".splitlines()

secs = [{"id": f"S{i}", "number": "", "heading": h} for i, h in enumerate(HEADS)]
pos = PhysicsLP1112Builder._locate_sections(text, secs)

print("\n  #  heading                                              position   chars to next")
located = [(i, pos[s["id"]]) for i, s in enumerate(secs) if pos[s["id"]] is not None]
nxt = {i: (located[k + 1][1] if k + 1 < len(located) else len(text)) for k, (i, _) in enumerate(located)}
for i, s in enumerate(secs):
    p = pos[s["id"]]
    if p is None:
        print(f" {i+1:>2}  {s['heading'][:52]:<52}  NOT FOUND")
    else:
        print(f" {i+1:>2}  {s['heading'][:52]:<52}  {p:>8}   {nxt[i] - p:>8}")

missing = [s["heading"] for s in secs if pos[s["id"]] is None]
if missing:
    print("\nHOW THE MISSING HEADINGS APPEAR (first close line in the text):")
    lines = text.split("\n")
    for h in missing[:8]:
        key = re.findall(r"[a-z]{4,}", h.lower())[:2]
        hit = next((ln for ln in lines if key and all(k in ln.lower() for k in key) and len(ln) < 140), None)
        print(f"  {h[:45]:<45} -> {hit!r}")