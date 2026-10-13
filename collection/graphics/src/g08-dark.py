#!/usr/bin/env python3
"""g08-dark — ORIZONTUL EVENIMENTELOR. Black hole with a tilted, Doppler-beamed
accretion disk built from ~1500 elliptical streaks, the lensed image of the far side
wrapping over the top, a thin secondary arc underneath, a photon ring and sparse stars.
The shadow is a cut-out (no ink): the dark fabric is the event horizon.
Poster 1200x1500, transparent background.
Run: python3 graphics/src/g08-dark.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cosmos_lib import (CHROME, GOLD, INDIGO, LAV, MAGENTA, MICHROMA, ORANGE, PERI, ROOT,
                        SIGNATURE, SPACE, SPACE_B, blur_filter, linear_grad, n, radial_grad,
                        ramp, star4, text_path, write_svg)

ID = "g08-dark"
OUT = ROOT / "graphics" / f"{ID}.svg"
rnd = random.Random(808)

W, H = 1200, 1500
CX, CY = 600, 585
RSH = 166            # shadow radius
RIN, ROUT = 212, 575  # disk radii
Q = 0.135            # disk inclination squash
TILT = -9            # degrees

GOLD_L = "#FFD98A"
HOT = "#FFF6E4"
DISK_RAMP = [(0, "#FFFFFF"), (0.1, HOT), (0.28, GOLD_L), (0.48, GOLD), (0.7, ORANGE),
             (0.88, "#C42A5C"), (1, "#5B2A9E")]


def lens_radius(r, lo=1.07, hi=1.92):
    u = (r - RIN) / (ROUT - RIN)
    return RSH * (lo + (hi - lo) * u ** 0.85)


def doppler(t):
    """approaching side (left, x<0) brighter and whiter"""
    return 0.62 + 0.5 * (-math.cos(t))


def arc_d(rx, ry, t0, t1):
    """elliptical arc from angle t0 to t1 (t1 > t0) around the local origin"""
    x0, y0 = rx * math.cos(t0), ry * math.sin(t0)
    x1, y1 = rx * math.cos(t1), ry * math.sin(t1)
    large = 1 if (t1 - t0) > math.pi else 0
    return f'M{n(x0)} {n(y0)}A{n(rx)} {n(ry)} 0 {large} 1 {n(x1)} {n(y1)}'


back, front, lens_top, lens_bot = [], [], [], []


def seg(lst, d, col, w, op):
    lst.append(f'<path d="{d}" stroke="{col}" stroke-width="{n(w, 1)}" stroke-opacity="{n(min(op, 1), 2)}"/>')


def split_add(r, ta, tb, col, w, op_fn):
    """split an arc into back (sin<0) and front (sin>=0) halves"""
    # normalise to [0, 2pi)
    ta %= 2 * math.pi
    tb = ta + (tb - ta)
    cuts = [ta]
    for k in range(0, 5):
        c = k * math.pi
        if ta < c < tb:
            cuts.append(c)
    cuts.append(tb)
    for a, b in zip(cuts, cuts[1:]):
        if b - a < 0.01:
            continue
        mid = (a + b) / 2
        target = back if math.sin(mid) < 0 else front
        seg(target, arc_d(r, r * Q, a, b), col, w, op_fn(mid))
        if math.sin(mid) < 0:
            # lensed image of the far side, wrapped over the shadow
            L = lens_radius(r)
            seg(lens_top, arc_d(L, L * 0.98, a, b), col, w * 0.95, op_fn(mid) * 0.95)
        else:
            L = lens_radius(r, 1.03, 1.2)
            if r < RIN + 170:
                seg(lens_bot, arc_d(L, L * 0.96, a, b), col, max(2.5, w * 0.7), op_fn(mid) * 0.55)


# ---------------------------------------------------------------- disk streaks
for i in range(1350):
    u = rnd.random() ** 1.5
    r = RIN + (ROUT - RIN) * u
    t0 = rnd.uniform(0, 2 * math.pi)
    span = rnd.uniform(0.25, 1.5) * (1.2 - 0.5 * u)
    col = ramp(DISK_RAMP, min(1, max(0, u + rnd.gauss(0, 0.06))))
    w = rnd.uniform(2.5, 4.6) if u < 0.6 else rnd.uniform(2.5, 3.4)
    base = rnd.uniform(0.35, 0.85) * (1.05 - 0.55 * u)
    split_add(r, t0, t0 + span, col, w, lambda m, b=base: b * doppler(m))

# bright inner filaments
for i in range(160):
    r = RIN + rnd.uniform(0, 45)
    t0 = rnd.uniform(0, 2 * math.pi)
    split_add(r, t0, t0 + rnd.uniform(0.4, 1.8), rnd.choice([HOT, "#FFFFFF", GOLD_L]),
              rnd.uniform(2.5, 3.2), lambda m: rnd.uniform(0.55, 0.95) * doppler(m))

# hot particles riding the disk
dots_back, dots_front, dots_lens = [], [], []
for i in range(1500):
    u = rnd.random() ** 1.7
    r = RIN + (ROUT - RIN) * u
    t = rnd.uniform(0, 2 * math.pi)
    col = ramp(DISK_RAMP, max(0, u - 0.12))
    rad = min(1.3 + rnd.expovariate(1 / 0.45), 2.8)
    op = min(1, rnd.uniform(0.5, 1) * doppler(t))
    x, y = r * math.cos(t), r * Q * math.sin(t) + rnd.gauss(0, 2 + 6 * u)
    c = f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rad, 2)}" fill="{col}" fill-opacity="{n(op, 2)}"/>'
    (dots_back if math.sin(t) < 0 else dots_front).append(c)
    if math.sin(t) < 0 and rnd.random() < 0.5:
        L = lens_radius(r) + rnd.gauss(0, 3)
        dots_lens.append(f'<circle cx="{n(L * math.cos(t))}" cy="{n(L * 0.98 * math.sin(t))}" r="{n(rad, 2)}" '
                         f'fill="{col}" fill-opacity="{n(op, 2)}"/>')

# ---------------------------------------------------------------- defs
defs = [
    blur_filter(f"{ID}-blur-xl", 34, units_box=(-700, -600, 1400, 1200)),
    blur_filter(f"{ID}-blur-l", 14, units_box=(-700, -600, 1400, 1200)),
    blur_filter(f"{ID}-blur-s", 4, units_box=(-700, -600, 1400, 1200)),
    blur_filter(f"{ID}-blur-title", 16, units_box=(0, 800, 1200, 500)),
    f'<mask id="{ID}-shadow" maskUnits="userSpaceOnUse" x="-700" y="-700" width="1400" height="1400">'
    f'<rect x="-700" y="-700" width="1400" height="1400" fill="#FFFFFF"/>'
    f'<circle cx="0" cy="0" r="{RSH + 1}" fill="#000000"/></mask>',
    radial_grad(f"{ID}-halo", [(0, GOLD, 0), (0.28, GOLD, 0), (0.33, "#FFB25A", 0.22), (0.5, ORANGE, 0.09),
                               (0.75, MAGENTA, 0.03), (1, INDIGO, 0)]),
    radial_grad(f"{ID}-fl", [(0, "#FFFFFF", 0.7), (0.22, "#E8ECFF", 0.26), (1, PERI, 0)]),
    radial_grad(f"{ID}-fl-gold", [(0, "#FFF6E0", 0.7), (0.22, GOLD_L, 0.28), (1, GOLD, 0)]),
    radial_grad(f"{ID}-ray", [(0, "#FFFFFF", 1), (0.25, "#FFFFFF", 0.97), (0.62, "#E9EEFF", 0.6), (1, "#DDE6FF", 0)]),
    radial_grad(f"{ID}-ray-warm", [(0, "#FFFFFF", 1), (0.2, "#FFF6E2", 0.95), (0.6, GOLD_L, 0.55), (1, GOLD, 0)]),
    linear_grad(f"{ID}-title", [(0, "#FFFFFF", 1), (0.42, "#FFF0CC", 1), (0.62, GOLD_L, 1), (1, ORANGE, 1)]),
    linear_grad(f"{ID}-title2", [(0, "#FFF4DA", 1), (0.5, GOLD, 1), (1, ORANGE, 1)]),
    linear_grad(f"{ID}-rule", [(0, ORANGE, 0), (0.5, GOLD, 1), (1, ORANGE, 0)], x2="1", y2="0"),
]

body = []

# ---------------------------------------------------------------- field stars (kept off the disk)
stars = []
cos_t, sin_t = math.cos(math.radians(TILT)), math.sin(math.radians(TILT))
for i in range(260):
    x, y = rnd.uniform(16, W - 16), rnd.uniform(16, 900)
    lx, ly = (x - CX) * cos_t + (y - CY) * sin_t, -(x - CX) * sin_t + (y - CY) * cos_t
    if math.hypot(lx, ly) < 330 or (abs(lx) < ROUT + 20 and abs(ly) < 95):
        continue
    col = rnd.choice([CHROME, CHROME, LAV, "#8FA8FF", GOLD_L])
    stars.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(min(1.3 + rnd.expovariate(1 / 0.35), 2.4), 2)}" '
                 f'fill="{col}" fill-opacity="{n(rnd.uniform(0.3, 0.9), 2)}"/>')
body.append(f'<g id="{ID}-stars">' + "".join(stars) + "</g>")


# ---------------------------------------------------------------- spacetime well (embedding grid)
grid = []
FY, FK = 872, 0.17          # plane height on the poster, perspective squash


def well(rho):
    return 150 * (RIN / rho) ** 1.6


def fpt(rho, a):
    return CX + rho * math.cos(a), FY + rho * FK * math.sin(a) + well(rho)


for i, rho in enumerate([230, 255, 285, 325, 375, 440, 520, 610, 710]):
    pts = [fpt(rho, 2 * math.pi * k / 120) for k in range(121)]
    pts = [(x, y) for (x, y) in pts if 20 < x < W - 20]
    d = "M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts)
    op = 0.5 * (1 - i / 11)
    grid.append(f'<path d="{d}" stroke="{PERI}" stroke-opacity="{n(op, 2)}"/>')
for k in range(28):
    a = 2 * math.pi * k / 28
    pts = [fpt(rho, a) for rho in [230 + j * 12 for j in range(41)]]
    pts = [(x, y) for (x, y) in pts if 20 < x < W - 20]
    if len(pts) < 2:
        continue
    d = "M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts)
    grid.append(f'<path d="{d}" stroke="{PERI}" stroke-opacity="0.3"/>')
body.append(f'<g id="{ID}-well" fill="none" stroke-width="2.5" mask="url(#{ID}-wellmask)">' + "".join(grid) + "</g>")
defs.append(radial_grad(f"{ID}-wellfade", [(0, "#FFFFFF", 1), (0.55, "#FFFFFF", 0.8), (1, "#FFFFFF", 0)]))
defs.append(f'<mask id="{ID}-wellmask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<ellipse cx="{CX}" cy="{FY + 60}" rx="600" ry="190" fill="url(#{ID}-wellfade)"/></mask>')

# ---------------------------------------------------------------- black hole system
body.append(f'<g id="{ID}-hole" transform="translate({CX} {CY}) rotate({TILT})">')
# soft halo and blurred underglow (masked so the horizon stays empty)
body.append(f'<g mask="url(#{ID}-shadow)">')
body.append(f'<circle cx="0" cy="0" r="{n(RSH * 3.3)}" fill="url(#{ID}-halo)"/>')
glow = []
for (rx, ry, col, op, w) in ((370, 50, ORANGE, 0.35, 70), (300, 40, GOLD, 0.45, 50), (230, 30, HOT, 0.5, 30)):
    glow.append(f'<ellipse cx="0" cy="0" rx="{rx}" ry="{ry}" fill="none" stroke="{col}" stroke-width="{w}" '
                f'stroke-opacity="{op}"/>')
for (L, col, op, w) in ((lens_radius(RIN + 80), ORANGE, 0.32, 70), (lens_radius(RIN + 20), GOLD, 0.4, 32)):
    glow.append(f'<path d="{arc_d(L, L * 0.98, math.pi, 2 * math.pi)}" fill="none" stroke="{col}" '
                f'stroke-width="{w}" stroke-opacity="{op}"/>')
body.append(f'<g filter="url(#{ID}-blur-xl)">' + "".join(glow) + "</g>")
# far side of the disk + its lensed image
body.append(f'<g fill="none" stroke-linecap="round">' + "".join(back) + "</g>")
body.append("".join(dots_back))
body.append(f'<g fill="none" stroke-linecap="round" filter="url(#{ID}-blur-s)" opacity="0.7">' + "".join(lens_top[::3]) + "</g>")
body.append(f'<g fill="none" stroke-linecap="round">' + "".join(lens_top) + "</g>")
body.append("".join(dots_lens))
body.append(f'<g fill="none" stroke-linecap="round">' + "".join(lens_bot) + "</g>")
body.append(f'<path d="{arc_d(RSH * 1.09, RSH * 1.05, 0.25, math.pi - 0.25)}" fill="none" stroke="{GOLD_L}" '
            f'stroke-width="3" stroke-opacity="0.85" stroke-linecap="round"/>')
body.append("</g>")

# photon ring
body.append(f'<circle cx="0" cy="0" r="{RSH + 5}" fill="none" stroke="{GOLD}" stroke-width="12" stroke-opacity="0.55" '
            f'filter="url(#{ID}-blur-l)"/>')
body.append(f'<circle cx="0" cy="0" r="{RSH + 3}" fill="none" stroke="{HOT}" stroke-width="4"/>')
body.append(f'<path d="{arc_d(RSH + 3, RSH + 3, math.pi * 0.55, math.pi * 1.45)}" fill="none" stroke="#FFFFFF" '
            f'stroke-width="5" stroke-linecap="round"/>')

# near side of the disk passes in front of the horizon
body.append(f'<g filter="url(#{ID}-blur-l)" fill="none">'
            f'<path d="{arc_d(310, 40, 0.05, math.pi - 0.05)}" stroke="{GOLD}" stroke-width="40" stroke-opacity="0.32"/></g>')
body.append(f'<g fill="none" stroke-linecap="round">' + "".join(front) + "</g>")
body.append("".join(dots_front))
body.append("</g>")


def flare(x, y, rr, kind="", rot=0.0, halo=0.55):
    warm = kind == "-gold"
    ray = f"url(#{ID}-ray-warm)" if warm else f"url(#{ID}-ray)"
    return (f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rr * halo)}" fill="url(#{ID}-fl{kind})"/>'
            f'<path d="{star4(x, y, rr, 0.075, rot)}" fill="{ray}"/>'
            f'<path d="{star4(x, y, rr * 0.38, 0.12, rot + math.pi / 4)}" fill="{ray}" fill-opacity="0.7"/>'
            f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(max(1.6, rr * 0.06))}" fill="#FFFFFF"/>')


body.append(f'<g id="{ID}-flares">')
for (x, y, rr, kind) in ((150, 190, 46, ""), (1060, 150, 30, "-gold"), (1088, 760, 22, ""), (96, 640, 18, "-gold"),
                         (430, 120, 14, ""), (880, 860, 12, "-gold")):
    body.append(flare(x, y, rr, kind))
# a single glint on the approaching side of the disk
body.append(flare(CX - (RIN + 6) * cos_t, CY - (RIN + 6) * sin_t, 70, "", halo=0.5))
body.append("</g>")

# ---------------------------------------------------------------- diagram labels
lab = []


def label(txt, x, y, anchor="start", col=LAV, size=17):
    t = text_path(SPACE, txt, size, x, y, tracking=120, anchor=anchor)
    lab.append(f'<path d="{t["d"]}" fill="{col}"/>')
    return t


def to_world(lx, ly):
    return CX + lx * cos_t - ly * sin_t, CY + lx * sin_t + ly * cos_t


# photon ring -> upper left
px, py = to_world(-RSH * 0.72, -RSH * 0.72)
lab.append(f'<path d="M{n(px)} {n(py)}L{n(px - 150)} {n(py - 150)}H70" fill="none" stroke="{LAV}" stroke-width="2.5" '
           f'stroke-opacity="0.75"/><circle cx="{n(px)}" cy="{n(py)}" r="5" fill="none" stroke="{LAV}" stroke-width="2.5"/>')
label("INEL FOTONIC", 70, py - 162)
label("r = 3GM/c²", 70, py - 130, col=PERI)
# disk -> lower right
dx, dy = to_world(ROUT * 0.7, ROUT * Q * 0.7)
lab.append(f'<path d="M{n(dx)} {n(dy)}L{n(dx + 90)} {n(dy + 120)}H1130" fill="none" stroke="{LAV}" stroke-width="2.5" '
           f'stroke-opacity="0.75"/><circle cx="{n(dx)}" cy="{n(dy)}" r="5" fill="none" stroke="{LAV}" stroke-width="2.5"/>')
label("DISC DE ACREȚIE", 1130, dy + 108, anchor="end")
label("T ≈ 10 MILIOANE K", 1130, dy + 150, anchor="end", col=PERI)
body.append(f'<g id="{ID}-labels">' + "".join(lab) + "</g>")

# ---------------------------------------------------------------- title block
t1 = text_path(MICHROMA, "ORIZONTUL", 100, 0, 0, tracking=260)
s1 = 1040 / t1["width"] * 100
t2 = text_path(MICHROMA, "EVENIMENTELOR", 100, 0, 0, tracking=120)
s2 = 1040 / t2["width"] * 100
Y1 = 1112
l1 = text_path(MICHROMA, "ORIZONTUL", s1, W / 2, Y1, tracking=260)
l2 = text_path(MICHROMA, "EVENIMENTELOR", s2, W / 2, Y1 + s2 * 1.05 + 14, tracking=120)
body.append(f'<g id="{ID}-title">')
body.append(f'<g filter="url(#{ID}-blur-title)" opacity="0.55"><path d="{l1["d"]}" fill="{ORANGE}"/>'
            f'<path d="{l2["d"]}" fill="{ORANGE}"/></g>')
body.append(f'<path d="{l1["d"]}" fill="url(#{ID}-title)"/>')
body.append(f'<path d="{l2["d"]}" fill="url(#{ID}-title2)"/>')
body.append("</g>")
YS = Y1 + s2 * 1.05 + 14 + 78
sub = text_path(SPACE_B, "NU EXISTĂ CALE DE ÎNTOARCERE", 26, W / 2, YS, tracking=330)
sw = sub["width"]
body.append(f'<rect x="80" y="{n(YS - 11)}" width="{n(W / 2 - sw / 2 - 110)}" height="3" fill="url(#{ID}-rule)"/>')
body.append(f'<rect x="{n(W / 2 + sw / 2 + 30)}" y="{n(YS - 11)}" width="{n(W / 2 - sw / 2 - 110)}" height="3" fill="url(#{ID}-rule)"/>')
body.append(f'<path id="{ID}-subtitle" d="{sub["d"]}" fill="{GOLD}"/>')
sig = text_path(SPACE_B, SIGNATURE, 18, W / 2, 1478, tracking=260)
body.append(f'<path id="{ID}-signature" d="{sig["d"]}" fill="{PERI}" fill-opacity="0.85"/>')
coord = text_path(SPACE, "OBIECT 0001 · MASĂ NECUNOSCUTĂ · ULTIMUL SEMNAL 03:33", 15, W / 2, 1430, tracking=140)
body.append(f'<path d="{coord["d"]}" fill="{LAV}" fill-opacity="0.7"/>')

size = write_svg(OUT, body, "".join(defs))
print(OUT, len(back) + len(front) + len(lens_top) + len(lens_bot), "streaks", size // 1024, "KB")
