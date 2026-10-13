#!/usr/bin/env python3
"""g20-dark — GAURA DE VIERME. 48 distorted, twisting rings recede into a bright
vanishing point (magenta outside -> periwinkle -> cyan -> white core), joined by
spiralling wireframe ribs; tapered star streaks fly outward. Wavy, extruded
Unbounded Black title.
Poster 1200x1500, transparent background.
Run: python3 graphics/src/g20-dark.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cosmos_lib import (CHROME, CYAN, EBLUE, INDIGO, LAV, MAGENTA, PERI, ROOT, SIGNATURE,
                        SPACE, SPACE_B, UNB_BLACK, blur_filter, linear_grad, mix, n, radial_grad,
                        ramp, star4, text_path, warp_text, write_svg)

ID = "g20-dark"
OUT = ROOT / "graphics" / f"{ID}.svg"
rnd = random.Random(2020)

W, H = 1200, 1500
VP = (648, 520)          # vanishing point
OC = (600, 610)          # centre of the outermost ring
RMAX = 545
NR = 48
NP = 180                 # points per ring
RAMP = [(0, "#FFFFFF"), (0.05, "#D8FDFF"), (0.13, CYAN), (0.38, "#7C8CFF"), (0.6, PERI), (0.8, "#B04BE0"),
        (1, MAGENTA)]


def ring_pts(k):
    s = (1 - k / NR) ** 2.15            # 1 outer .. ~0 inner
    R = 8 + (RMAX - 8) * s
    cx = VP[0] + (OC[0] - VP[0]) * s ** 0.8
    cy = VP[1] + (OC[1] - VP[1]) * s ** 0.8
    ph1, ph2 = k * 0.21, -k * 0.13 + 1.1
    a1 = 0.06 + 0.03 * math.sin(k * 0.4)
    pts = []
    for i in range(NP):
        th = 2 * math.pi * i / NP
        r = R * (1 + a1 * math.sin(3 * th + ph1) + 0.035 * math.sin(5 * th + ph2) + 0.02 * math.sin(2 * th - k * 0.3))
        pts.append((cx + r * math.cos(th), cy + 0.9 * r * math.sin(th)))
    return s, pts


def closed_d(pts, nd=1):
    return "M" + "L".join(f"{n(x, nd)} {n(y, nd)}" for x, y in pts) + "Z"


rings = [ring_pts(k) for k in range(NR)]

defs = [
    blur_filter(f"{ID}-blur-glow", 7, units_box=(0, 0, W, H)),
    blur_filter(f"{ID}-blur-xl", 30, units_box=(0, 0, W, H)),
    blur_filter(f"{ID}-blur-title", 14, units_box=(0, 950, W, 550)),
    radial_grad(f"{ID}-core", [(0, "#FFFFFF", 1), (0.12, "#F2FEFF", 0.95), (0.3, CYAN, 0.55), (0.6, EBLUE, 0.15),
                               (1, INDIGO, 0)]),
    radial_grad(f"{ID}-tunnel", [(0, PERI, 0.0), (0.25, EBLUE, 0.16), (0.7, INDIGO, 0.12), (0.92, "#4A1B7A", 0.08),
                                 (1, "#4A1B7A", 0)]),
    radial_grad(f"{ID}-fl", [(0, "#FFFFFF", 0.7), (0.22, "#E8FDFF", 0.3), (1, CYAN, 0)]),
    radial_grad(f"{ID}-ray", [(0, "#FFFFFF", 1), (0.25, "#FFFFFF", 0.97), (0.62, "#E0FBFF", 0.6), (1, "#CFF8FF", 0)]),
    linear_grad(f"{ID}-face", [(0, "#FFFFFF", 1), (0.35, "#D9FCFF", 1), (0.62, CYAN, 1), (1, "#7C8CFF", 1)]),
    linear_grad(f"{ID}-rule", [(0, MAGENTA, 0), (0.5, MAGENTA, 1), (1, MAGENTA, 0)], x2="1", y2="0"),
]

body = []

# ---------------------------------------------------------------- tunnel body glow
body.append(f'<ellipse cx="{OC[0]}" cy="{OC[1]}" rx="{RMAX + 30}" ry="{n((RMAX + 30) * 0.9)}" fill="url(#{ID}-tunnel)"/>')

# ---------------------------------------------------------------- star streaks (behind the rings)
streaks_back, streaks_front = [], []
for i in range(420):
    a = rnd.uniform(0, 2 * math.pi)
    d = 40 + (rnd.random() ** 0.9) * 820
    L = d * rnd.uniform(0.1, 0.32)
    w = rnd.uniform(2.5, 3.2) + d / 820 * rnd.uniform(0.5, 3.5)
    ca, sa = math.cos(a), math.sin(a)
    x1, y1 = VP[0] + ca * d, VP[1] + sa * d
    x0, y0 = VP[0] + ca * (d - L), VP[1] + sa * (d - L)
    if not (24 < x1 < W - 24 and 24 < y1 < 1110):
        continue
    nx, ny = -sa * w / 2, ca * w / 2
    col = rnd.choice([CHROME, CHROME, CYAN, LAV, "#A9B4FF", MAGENTA if d > 450 else CYAN])
    op = rnd.uniform(0.35, 0.95) * min(1, d / 160)
    p = (f'<path d="M{n(x0)} {n(y0)}L{n(x1 + nx)} {n(y1 + ny)}A{n(w / 2)} {n(w / 2)} 0 0 0 {n(x1 - nx)} {n(y1 - ny)}Z" '
         f'fill="{col}" fill-opacity="{n(op, 2)}"/>')
    (streaks_front if d > 520 and rnd.random() < 0.6 else streaks_back).append(p)
body.append(f'<g id="{ID}-streaks">' + "".join(streaks_back) + "</g>")

# ---------------------------------------------------------------- ribs (longitudinal wireframe)
ribs = []
for j in range(30):
    i0 = int(j * NP / 30)
    pts = []
    for k, (s, pts_k) in enumerate(rings[:-6]):
        pts.append(pts_k[(i0 + k * 2) % NP])          # twist as we go in
    d = "M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts)
    ribs.append(f'<path d="{d}" stroke="{PERI if j % 2 else "#9B5CFF"}" stroke-opacity="0.32"/>')
body.append(f'<g id="{ID}-ribs" fill="none" stroke-width="2.5" stroke-linejoin="round">' + "".join(ribs) + "</g>")

# ---------------------------------------------------------------- rings
glow, crisp = [], []
for k, (s, pts) in enumerate(rings):
    col = ramp(RAMP, s)
    w = 2.5 + 4.2 * s
    fade = 1.0 if k > 2 else 0.45 + 0.27 * k
    op = (0.95 - 0.25 * s) * fade
    d = closed_d(pts)
    glow.append(f'<path d="{d}" stroke="{col}" stroke-width="{n(w * 3.2)}" stroke-opacity="{n(op * 0.5, 2)}"/>')
    dash = ""
    if k % 5 == 2 and s > 0.15:
        per = 2 * math.pi * (8 + (RMAX - 8) * s)
        seg = per / rnd.choice([18, 24, 36])
        dash = f' stroke-dasharray="{n(seg * 0.62)} {n(seg * 0.38)}"'
    crisp.append(f'<path d="{d}" stroke="{col}" stroke-width="{n(w)}" stroke-opacity="{n(op, 2)}"{dash}/>')
    # a hot inner edge on every 3rd ring (light caught on the rim)
    if k % 3 == 0 and s > 0.08:
        crisp.append(f'<path d="{d}" stroke="#FFFFFF" stroke-width="2.5" stroke-opacity="{n(0.35 * fade, 2)}" '
                     f'transform="translate({n((VP[0] - OC[0]) * 0.01)} {n((VP[1] - OC[1]) * 0.01)})"/>')
body.append(f'<g id="{ID}-ring-glow" fill="none" filter="url(#{ID}-blur-glow)">' + "".join(glow) + "</g>")
body.append(f'<g id="{ID}-rings" fill="none" stroke-linejoin="round">' + "".join(crisp) + "</g>")

# beads of light riding a few rings
beads = []
for k, (s, pts) in enumerate(rings):
    if s < 0.06:
        continue
    for _ in range(int(3 + 9 * s)):
        x, y = pts[rnd.randrange(NP)]
        col = ramp(RAMP, max(0, s - 0.15))
        beads.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rnd.uniform(2, 3.6) * (0.6 + s), 2)}" fill="{col}" '
                     f'fill-opacity="{n(rnd.uniform(0.7, 1), 2)}"/>')
        if rnd.random() < 0.25:
            beads.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(1.6 + s, 2)}" fill="#FFFFFF"/>')
body.append(f'<g id="{ID}-beads">' + "".join(beads) + "</g>")

# ---------------------------------------------------------------- vanishing point
body.append(f'<circle cx="{VP[0]}" cy="{VP[1]}" r="150" fill="url(#{ID}-core)"/>')
body.append(f'<g filter="url(#{ID}-blur-xl)"><circle cx="{VP[0]}" cy="{VP[1]}" r="46" fill="#FFFFFF" fill-opacity="0.8"/></g>')
body.append(f'<path d="{star4(VP[0], VP[1], 190, 0.035)}" fill="url(#{ID}-ray)"/>')
body.append(f'<path d="{star4(VP[0], VP[1], 70, 0.08, math.pi / 4)}" fill="url(#{ID}-ray)" fill-opacity="0.8"/>')
body.append(f'<circle cx="{VP[0]}" cy="{VP[1]}" r="9" fill="#FFFFFF"/>')
body.append(f'<g id="{ID}-streaks-front">' + "".join(streaks_front) + "</g>")


def flare(x, y, rr, halo=0.55):
    return (f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rr * halo)}" fill="url(#{ID}-fl)"/>'
            f'<path d="{star4(x, y, rr, 0.075)}" fill="url(#{ID}-ray)"/>'
            f'<path d="{star4(x, y, rr * 0.38, 0.12, math.pi / 4)}" fill="url(#{ID}-ray)" fill-opacity="0.7"/>'
            f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(max(1.6, rr * 0.06))}" fill="#FFFFFF"/>')


body.append(f'<g id="{ID}-flares">' + "".join(flare(*f) for f in ((120, 150, 40), (1080, 120, 26), (1110, 880, 30),
                                                                    (90, 760, 18), (380, 330, 14))) + "</g>")

# ---------------------------------------------------------------- title: wavy, extruded
def fit(text, width, tracking=0):
    return width / text_path(UNB_BLACK, text, 100, 0, 0, tracking=tracking)["width"] * 100


s1, s2 = fit("GAURA DE", 860, 20), fit("VIERME", 1010, 20)
B1, B2 = 1188, 1362
t1 = warp_text(UNB_BLACK, "GAURA DE", s1, W / 2, B1, warps=["wave:0.1:1:0.1", "bulge:0.1"], tracking=20,
               anchor="middle", steps=8)
t2 = warp_text(UNB_BLACK, "VIERME", s2, W / 2, B2, warps=["wave:0.08:1:0.6", "bulge:0.14"], tracking=20,
               anchor="middle", steps=8)
body.append(f'<g id="{ID}-title">')
body.append(f'<g filter="url(#{ID}-blur-title)" opacity="0.7"><path d="{t1["d"]}" fill="{MAGENTA}"/>'
            f'<path d="{t2["d"]}" fill="{MAGENTA}"/></g>')
for t in (t1, t2):
    for k in range(14, 0, -1):
        col = mix("#FF3DA8", "#2A0F5C", k / 14)
        body.append(f'<path d="{t["d"]}" fill="{col}" transform="translate({n(k * 0.45)} {n(k * 1.05)})"/>')
    body.append(f'<path d="{t["d"]}" fill="url(#{ID}-face)"/>')
body.append("</g>")

YS = 1432
sub = text_path(SPACE_B, "EXPRES · DUS-ÎNTORS", 26, W / 2, YS, tracking=360)
sw = sub["width"]
body.append(f'<rect x="90" y="{n(YS - 11)}" width="{n(W / 2 - sw / 2 - 130)}" height="3" fill="url(#{ID}-rule)"/>')
body.append(f'<rect x="{n(W / 2 + sw / 2 + 40)}" y="{n(YS - 11)}" width="{n(W / 2 - sw / 2 - 130)}" height="3" fill="url(#{ID}-rule)"/>')
body.append(f'<path id="{ID}-subtitle" d="{sub["d"]}" fill="{CYAN}"/>')
sig = text_path(SPACE_B, SIGNATURE, 17, W / 2, 1484, tracking=260)
body.append(f'<path id="{ID}-signature" d="{sig["d"]}" fill="{PERI}" fill-opacity="0.85"/>')
# timetable fine print in the corners
for txt, x, y, anc in (("PLECARE 03:33", 70, 70, "start"), ("SOSIRE IERI", 1130, 70, "end")):
    t = text_path(SPACE, txt, 17, x, y, tracking=160, anchor=anc)
    body.append(f'<path d="{t["d"]}" fill="{LAV}" fill-opacity="0.8"/>')

size = write_svg(OUT, body, "".join(defs))
print(OUT, size // 1024, "KB")
