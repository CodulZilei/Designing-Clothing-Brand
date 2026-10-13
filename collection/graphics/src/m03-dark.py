#!/usr/bin/env python3
"""m03-dark — the "N" classification badge from the label (g01 / g10) as a small mark:
orbiting N disc inside a ring of outlined text. 600x600, transparent.
Run: python3 graphics/src/m03-dark.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_lib import ROOT, SVG, n_badge, star4  # noqa: E402
from cosmos_lib import MICHROMA, arc_text  # noqa: E402

ID = "m03-dark"
OUT = os.path.join(ROOT, "graphics", ID + ".svg")
svg = SVG(ID, 600, 600)
WH, LAV, KO = "#F2F4FF", "#C9C3FF", "#0A0A16"
C = 300
svg.add(f'<circle cx="{C}" cy="{C}" r="276" fill="none" stroke="{WH}" stroke-width="6"/>')
svg.add(f'<circle cx="{C}" cy="{C}" r="262" fill="none" stroke="{LAV}" stroke-width="2.6"/>')
svg.add(f'<circle cx="{C}" cy="{C}" r="205" fill="none" stroke="{LAV}" stroke-width="2.6"/>')
svg.add(f'<path d="{arc_text(MICHROMA, "CLASIFICAT · NEPĂMÂNTEAN", 25, C, C, 224, -90, tracking=180, outward=True)}" fill="{WH}"/>')
svg.add(f'<path d="{arc_text(MICHROMA, "ONYXLAB · 2026", 22, C, C, 242, 90, tracking=300, outward=False)}" fill="{LAV}"/>')
for a in (180, 0):
    import math
    x = C + 233 * math.cos(math.radians(a))
    svg.add(f'<path d="{star4(x, C, 13, waist=0.12)}" fill="{WH}"/>')
svg.add(n_badge(svg, C, C, 128, WH, KO, ring=WH, sw=5))
print(OUT, svg.save(OUT))
