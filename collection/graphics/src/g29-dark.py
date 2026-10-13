#!/usr/bin/env python3
"""g29 — NU SUNTEM SINGURI. Minimal: a small, elegant UFO line icon and the line
"NU SUNTEM SINGURI" in Michroma, widely tracked; lots of negative space, composition
small and centred near the top of the poster viewBox.
Run: python3 graphics/src/g29-dark.py   (writes g29-dark.svg and g29-light.svg)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_lib import MICH, MONO_B, ROOT, SVG, f1, star4  # noqa: E402

INKS = {
    "dark": dict(line="#C9C3FF", title="#F2F4FF", beam="#6C6CFF", accent="#5FF3FF", sub="#C9C3FF"),
    "light": dict(line="#24228A", title="#07070D", beam="#3D5AFE", accent="#3D5AFE", sub="#24228A"),
}


def build(variant):
    fid = f"g29-{variant}"
    k = INKS[variant]
    svg = SVG(fid, 1200, 1500)
    cx, cy = 600, 300
    sw = 4.5
    g = [f'<g fill="none" stroke="{k["line"]}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">']
    # dome
    g.append(f'<path d="M{cx - 54} {cy - 6}C{cx - 52} {cy - 70} {cx + 52} {cy - 70} {cx + 54} {cy - 6}"/>')
    g.append(f'<path d="M{cx - 26} {cy - 44}C{cx - 16} {cy - 54} {cx - 4} {cy - 56} {cx + 6} {cy - 55}" opacity="0.7"/>')
    # saucer
    g.append(f'<ellipse cx="{cx}" cy="{cy + 6}" rx="128" ry="28"/>')
    g.append(f'<path d="M{cx - 128} {cy + 6}C{cx - 120} {cy + 44} {cx + 120} {cy + 44} {cx + 128} {cy + 6}"/>')
    g.append("</g>")
    for i in range(5):
        t = (i - 2) / 2.6
        x = cx + 92 * t
        y = cy + 6 + 28 * math.sqrt(max(1 - (92 * t / 128) ** 2, 0)) + 6
        g.append(f'<circle cx="{f1(x)}" cy="{f1(y)}" r="4.6" fill="{k["accent"] if i == 2 else k["line"]}"/>')
    # beam
    g.append(f'<path d="M{cx - 30} {cy + 52}L{cx - 78} {cy + 150}M{cx + 30} {cy + 52}L{cx + 78} {cy + 150}" stroke="{k["beam"]}" '
             f'stroke-width="3" stroke-dasharray="3 11" stroke-linecap="round" fill="none"/>')
    g.append(f'<path d="M{cx - 78} {cy + 160}Q{cx} {cy + 176} {cx + 78} {cy + 160}" stroke="{k["beam"]}" stroke-width="3" fill="none" stroke-linecap="round"/>')
    # tiny stars
    for px, py, r in ((cx - 190, cy - 70, 13), (cx + 175, cy - 96, 9), (cx + 210, cy + 64, 7)):
        g.append(f'<path d="{star4(px, py, r, waist=0.12)}" fill="{k["line"]}"/>')
    svg.add("".join(g))
    svg.add(svg.small(MICH, "NU SUNTEM SINGURI", 33, cx, cy + 270, k["title"], anchor="middle", tracking=430))
    svg.add(f'<path d="M{cx - 24} {cy + 312}H{cx + 24}" stroke="{k["line"]}" stroke-width="2.6"/>')
    svg.add(svg.small(MONO_B, "SEMNAL CONFIRMAT · 2026", 14, cx, cy + 350, k["sub"], anchor="middle", tracking=300))
    out = os.path.join(ROOT, "graphics", fid + ".svg")
    print(out, svg.save(out))


if __name__ == "__main__":
    for v in (sys.argv[1:] or ["dark", "light"]):
        build(v)
