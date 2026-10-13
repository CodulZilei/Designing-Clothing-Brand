#!/usr/bin/env python3
"""g09-dark — PLANETA B. An alien shore seen through an arched window: jagged indigo
crags, a mirror-flat liquid plain with gold/blue glitter streaks and rippled reflections,
a huge ringed planet setting low in the sky, glittering stars. Chrome-gradient title
in Unbounded Black overlapping the bottom of the arch.
Poster 1200x1500. The arch is an intentional panel (dark fill inside the frame).
Run: python3 graphics/src/g09-dark.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cosmos_lib import (CHROME, CYAN, EBLUE, GOLD, INDIGO, LAV, MAGENTA, ORANGE, PERI, ROOT,
                        SIGNATURE, SPACE, SPACE_B, UNB_BLACK, blur_filter, linear_grad, mix, n,
                        radial_grad, ramp, star4, text_path, write_svg)

ID = "g09-dark"
OUT = ROOT / "graphics" / f"{ID}.svg"
rnd = random.Random(909)

W, H = 1200, 1500
GOLD_L = "#FFD98A"

# ---------------------------------------------------------------- layout
TS = 1060 / text_path(UNB_BLACK, "PLANETA B", 100, 0, 0)["width"] * 100   # title size
TY = 1318                          # title baseline
TTOP = TY - 0.75 * TS
AX0, AX1 = 84, 1116                # arch sides
AR = (AX1 - AX0) / 2
ACY = 84 + AR                      # centre of the top semicircle
ABOT = TTOP + 52                   # arch bottom (title overlaps it)
SHORE = 930                        # liquid line
PL = (790, 700, 228)               # planet x, y, r
RT = -15                           # ring tilt (deg)


def arch_d(inset=0.0, rc=46):
    x0, x1, r = AX0 + inset, AX1 - inset, AR - inset
    b = ABOT - inset
    rc = max(rc - inset, 4)
    return (f"M{n(x0)} {n(ACY)}A{n(r)} {n(r)} 0 0 1 {n(x1)} {n(ACY)}V{n(b - rc)}"
            f"Q{n(x1)} {n(b)} {n(x1 - rc)} {n(b)}H{n(x0 + rc)}Q{n(x0)} {n(b)} {n(x0)} {n(b - rc)}Z")


def ridge(x0, x1, base, amp, seed, steps=7, rough=0.55, peaks=()):
    """jagged midpoint-displacement ridge; returns list of (x, y). peaks: (x, height) bumps"""
    r = random.Random(seed)
    pts = [(x0, base), (x1, base)]
    a = amp
    for _ in range(steps):
        new = [pts[0]]
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            xm = (xa + xb) / 2 + r.uniform(-0.18, 0.18) * (xb - xa)
            ym = (ya + yb) / 2 + r.uniform(-a, a)
            new += [(xm, ym), (xb, yb)]
        pts = new
        a *= rough
    out = []
    for x, y in pts:
        h = 0
        for (px, ph, pw) in peaks:
            h = max(h, ph * max(0.0, 1 - abs(x - px) / pw) ** 1.25)
        out.append((x, min(y, base + 6) - h))
    return out


def poly_d(pts, bottom):
    return ("M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts) +
            f"L{n(pts[-1][0])} {n(bottom)}L{n(pts[0][0])} {n(bottom)}Z")


def line_d(pts):
    return "M" + "L".join(f"{n(x)} {n(y)}" for x, y in pts)


defs = [
    f'<clipPath id="{ID}-arch"><path d="{arch_d()}"/></clipPath>',
    f'<clipPath id="{ID}-sea"><rect x="0" y="{SHORE}" width="{W}" height="{n(ABOT - SHORE + 10)}"/></clipPath>',
    f'<clipPath id="{ID}-pclip"><circle cx="{PL[0]}" cy="{PL[1]}" r="{PL[2]}"/></clipPath>',
    linear_grad(f"{ID}-sky", [(0, "#06061A", 1), (0.38, "#0F0E3E", 1), (0.66, "#24228A", 1), (0.82, "#4A3FB8", 1),
                              (0.92, "#8A5BC8", 1), (1, "#D07ACB", 1)], y1=str(84), y2=str(SHORE), units="userSpaceOnUse"),
    linear_grad(f"{ID}-liquid", [(0, "#2A2378", 1), (0.12, "#14124A", 1), (0.6, "#0A0A26", 1), (1, "#06061A", 1)],
                y1=str(SHORE), y2=n(ABOT), units="userSpaceOnUse"),
    linear_grad(f"{ID}-far", [(0, "#5A55D8", 1), (1, "#2E2B96", 1)], y1="700", y2=str(SHORE), units="userSpaceOnUse"),
    linear_grad(f"{ID}-mid", [(0, "#2B2A9A", 1), (1, "#16154E", 1)], y1="600", y2=str(SHORE), units="userSpaceOnUse"),
    linear_grad(f"{ID}-near", [(0, "#1B1A6A", 1), (0.5, "#0E0D38", 1), (1, "#09091F", 1)], y1="420", y2=str(SHORE),
                units="userSpaceOnUse"),
    radial_grad(f"{ID}-pbody", [(0, "#FFF1D0", 1), (0.25, GOLD_L, 1), (0.5, "#F09A4A", 1), (0.72, "#C2457E", 1),
                                (0.9, "#4B2C9C", 1), (1, "#2A2280", 1)], cx="32%", cy="28%", r="85%"),
    radial_grad(f"{ID}-pshade", [(0, "#06061A", 0), (0.5, "#06061A", 0), (0.78, "#06061A", 0.55), (1, "#06061A", 0.92)],
                cx="30%", cy="26%", r="90%"),
    radial_grad(f"{ID}-patm", [(0, GOLD, 0), (0.86, GOLD, 0), (0.9, "#FFB86A", 0.45), (0.95, MAGENTA, 0.15), (1, MAGENTA, 0)]),
    radial_grad(f"{ID}-phalo", [(0, GOLD, 0.3), (0.45, "#F09A4A", 0.14), (0.7, MAGENTA, 0.05), (1, MAGENTA, 0)]),
    radial_grad(f"{ID}-hglow", [(0, "#FF9ACD", 0.55), (0.4, MAGENTA, 0.22), (1, PERI, 0)]),
    radial_grad(f"{ID}-fl", [(0, "#FFFFFF", 0.7), (0.22, "#E8ECFF", 0.26), (1, PERI, 0)]),
    radial_grad(f"{ID}-fl-gold", [(0, "#FFF6E0", 0.7), (0.22, GOLD_L, 0.28), (1, GOLD, 0)]),
    radial_grad(f"{ID}-ray", [(0, "#FFFFFF", 1), (0.25, "#FFFFFF", 0.97), (0.62, "#E9EEFF", 0.6), (1, "#DDE6FF", 0)]),
    radial_grad(f"{ID}-ray-warm", [(0, "#FFFFFF", 1), (0.2, "#FFF6E2", 0.95), (0.6, GOLD_L, 0.55), (1, GOLD, 0)]),
    linear_grad(f"{ID}-chrome", [(0, "#FFFFFF", 1), (0.3, "#E6E8FF", 1), (0.5, "#C9C3FF", 1), (0.52, "#24228A", 1),
                                 (0.6, "#2E2BA0", 1), (0.74, "#6C6CFF", 1), (0.86, "#C9C3FF", 1), (1, "#FFFFFF", 1)]),
    linear_grad(f"{ID}-extr", [(0, "#3D5AFE", 1), (1, "#141250", 1)]),
    linear_grad(f"{ID}-rule", [(0, PERI, 0), (0.5, LAV, 1), (1, PERI, 0)], x2="1", y2="0"),
    blur_filter(f"{ID}-blur-l", 26, units_box=(0, 0, W, H)),
    blur_filter(f"{ID}-blur-m", 9, units_box=(0, 0, W, H)),
    blur_filter(f"{ID}-blur-s", 2.2, units_box=(0, 0, W, H)),
    # ripple displacement for reflections
    f'<filter id="{ID}-ripple" filterUnits="userSpaceOnUse" x="0" y="{SHORE - 20}" width="{W}" height="{n(ABOT - SHORE + 40)}" '
    f'color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency="0.004 0.09" numOctaves="2" seed="9"/>'
    f'<feDisplacementMap in="SourceGraphic" scale="26" xChannelSelector="R" yChannelSelector="G"/></filter>',
]

# ---------------------------------------------------------------- sky
sky = [f'<rect x="0" y="0" width="{W}" height="{SHORE + 2}" fill="url(#{ID}-sky)"/>']
stars = []
for i in range(420):
    x, y = rnd.uniform(AX0, AX1), rnd.uniform(90, SHORE - 60)
    if (x - PL[0]) ** 2 + (y - PL[1]) ** 2 < (PL[2] + 6) ** 2:
        continue
    depth = (y - 84) / (SHORE - 84)
    col = rnd.choice([CHROME, CHROME, LAV, "#8FA8FF", GOLD_L, CYAN])
    rad = min(1.3 + rnd.expovariate(1 / 0.35), 2.6)
    stars.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rad, 2)}" fill="{col}" '
                 f'fill-opacity="{n(rnd.uniform(0.35, 1.0) * (1.05 - depth * 0.7), 2)}"/>')
sky.append("".join(stars))
# faint milky band across the sky
band = []
for i in range(520):
    u = rnd.uniform(-1, 1)
    x = 600 + u * 560
    y = 330 - u * 170 + rnd.gauss(0, 34)
    band.append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(min(1.3 + rnd.expovariate(1 / 0.3), 2.2), 2)}" '
                f'fill="{rnd.choice([LAV, CHROME, PERI, "#8FA8FF"])}" fill-opacity="{n(rnd.uniform(0.25, 0.7), 2)}"/>')
sky.append(f'<g filter="url(#{ID}-blur-l)"><path d="M40 560 Q600 330 1160 100" stroke="{PERI}" stroke-width="120" '
           f'stroke-opacity="0.22" fill="none"/></g>')
sky.append("".join(band))
sky.append(f'<ellipse cx="640" cy="{SHORE}" rx="620" ry="150" fill="url(#{ID}-hglow)"/>')

# ---------------------------------------------------------------- planet + rings
px, py, pr = PL


def ring_arcs(half):
    """half='back' -> upper half of the ring ellipses (behind the planet)"""
    out = []
    rr = random.Random(99)
    rx = pr * 1.28
    while rx < pr * 2.3:
        w = rr.uniform(2.5, 6.5)
        if pr * 1.72 < rx < pr * 1.8:      # gap
            rx += 7
            continue
        u = (rx - pr * 1.28) / (pr * 1.02)
        col = ramp([(0, LAV), (0.3, GOLD_L), (0.55, "#F2A35A"), (0.8, LAV), (1, PERI)], u + rr.gauss(0, 0.05))
        op = rr.uniform(0.25, 0.75) * (1 - 0.5 * u)
        ry = rx * 0.2
        a0, a1 = (math.pi, 2 * math.pi) if half == "back" else (0, math.pi)
        x0, y0 = rx * math.cos(a0), ry * math.sin(a0)
        x1, y1 = rx * math.cos(a1), ry * math.sin(a1)
        out.append(f'<path d="M{n(x0)} {n(y0)}A{n(rx)} {n(ry)} 0 0 1 {n(x1)} {n(y1)}" stroke="{col}" '
                   f'stroke-width="{n(w)}" stroke-opacity="{n(op, 2)}"/>')
        rx += w * rr.uniform(0.7, 1.3)
    return f'<g transform="translate({px} {py}) rotate({RT})" fill="none">' + "".join(out) + "</g>"


planet = [f'<circle cx="{px}" cy="{py}" r="{pr * 2.1}" fill="url(#{ID}-phalo)"/>', ring_arcs("back")]
planet.append(f'<circle cx="{px}" cy="{py}" r="{pr + 14}" fill="url(#{ID}-patm)"/>')
planet.append(f'<circle cx="{px}" cy="{py}" r="{pr}" fill="url(#{ID}-pbody)"/>')
bands = []
for i in range(26):
    yy = -pr + (i + rnd.random()) * (2 * pr / 26)
    pts = []
    amp, ph, fr = rnd.uniform(2, 7), rnd.uniform(0, 6.3), rnd.uniform(2, 5)
    for k in range(41):
        x = -pr * 1.1 + k * (2.2 * pr / 40)
        pts.append((x, yy + amp * math.sin(fr * x / pr + ph)))
    col = rnd.choice(["#FFE6B0", "#C2457E", "#7A3FA8", GOLD, "#FFFFFF", "#F09A4A"])
    bands.append(f'<path d="{line_d(pts)}" stroke="{col}" stroke-width="{n(rnd.uniform(3, 12))}" '
                 f'stroke-opacity="{n(rnd.uniform(0.12, 0.35), 2)}" fill="none"/>')
planet.append(f'<g clip-path="url(#{ID}-pclip)"><g transform="translate({px} {py}) rotate({RT})">' + "".join(bands) +
              # ring shadow across the planet
              f'<ellipse cx="0" cy="{n(pr * 0.34)}" rx="{n(pr * 1.6)}" ry="{n(pr * 0.12)}" fill="#0A0930" fill-opacity="0.55"/>'
              f'</g><circle cx="{px}" cy="{py}" r="{pr}" fill="url(#{ID}-pshade)"/></g>')
planet.append(ring_arcs("front"))

# ---------------------------------------------------------------- mountains
far = ridge(AX0 - 20, AX1 + 20, SHORE - 40, 40, 3, steps=6,
            peaks=((330, 150, 300), (640, 90, 160), (860, 110, 190), (1060, 120, 220)))
mid_l = ridge(AX0 - 20, 700, SHORE - 6, 50, 11, steps=6, peaks=((260, 330, 300), (520, 170, 190), (640, 70, 90)))
mid_r = ridge(840, AX1 + 20, SHORE - 6, 40, 17, steps=6, peaks=((1050, 250, 210), (920, 90, 110)))
near_l = ridge(AX0 - 20, 420, SHORE + 4, 30, 23, steps=6, peaks=((150, 470, 250), (330, 200, 140)))
near_r = ridge(960, AX1 + 20, SHORE + 4, 30, 29, steps=6, peaks=((1110, 360, 170), (1000, 120, 70)))

def lit_faces(pts, col, op):
    """low-poly lit faces: from every local peak, the slope facing the planet (right)"""
    out = []
    for i in range(1, len(pts) - 1):
        if not (pts[i][1] < pts[i - 1][1] and pts[i][1] <= pts[i + 1][1]):
            continue
        j = i
        while j + 1 < len(pts) and pts[j + 1][1] >= pts[j][1]:
            j += 1
        if pts[j][1] - pts[i][1] < 25:
            continue
        x0, y0 = pts[i]
        xb = x0 + (pts[j][0] - x0) * 0.25
        yb = pts[j][1] + (SHORE - pts[j][1]) * 0.6
        poly = pts[i:j + 1] + [(xb, yb)]
        out.append(f'<path d="{line_d(poly)}Z" fill="{col}" fill-opacity="{n(op * random.Random(i).uniform(0.6, 1.2), 2)}"/>')
    return "".join(out)


mtn = []
mtn.append(f'<path d="{poly_d(far, SHORE + 2)}" fill="url(#{ID}-far)" fill-opacity="0.85"/>')
mtn.append(lit_faces(far, "#9C9CFF", 0.3))
mtn.append(f'<path d="{line_d(far)}" fill="none" stroke="#B4B4FF" stroke-width="2.5" stroke-opacity="0.5"/>')
for pts in (mid_l, mid_r):
    mtn.append(f'<path d="{poly_d(pts, SHORE + 2)}" fill="url(#{ID}-mid)"/>')
    mtn.append(f'<path d="{line_d(pts)}" fill="none" stroke="{PERI}" stroke-width="3" stroke-opacity="0.75"/>')


def facets(pts, base, n_lines, seed, col):
    """light strata / cracks running down the faces, giving the crags a carved look"""
    r = random.Random(seed)
    out = []
    for _ in range(n_lines):
        i = r.randrange(1, len(pts) - 1)
        x, y = pts[i]
        if y > base - 40:
            continue
        L = r.uniform(30, (base - y) * 0.8)
        dx = r.uniform(-0.35, 0.35) * L
        seg = [(x, y)]
        for k in range(1, 5):
            seg.append((x + dx * k / 4 + r.uniform(-6, 6), y + L * k / 4))
        out.append(f'<path d="{line_d(seg)}" stroke="{col}" stroke-width="{n(r.uniform(2.5, 4))}" '
                   f'stroke-opacity="{n(r.uniform(0.15, 0.45), 2)}" fill="none" stroke-linecap="round"/>')
    return "".join(out)


mtn.append(lit_faces(mid_l, "#6F78FF", 0.35) + lit_faces(mid_r, "#6F78FF", 0.35))
for pts in (near_l, near_r):
    mtn.append(f'<path d="{poly_d(pts, SHORE + 6)}" fill="url(#{ID}-near)"/>')
    mtn.append(f'<path d="{line_d(pts)}" fill="none" stroke="{CYAN}" stroke-width="3" stroke-opacity="0.6"/>')
mtn.append(lit_faces(near_l, "#3D5AFE", 0.4) + lit_faces(near_r, "#3D5AFE", 0.4))

# ---------------------------------------------------------------- liquid plain
sea = [f'<rect x="0" y="{SHORE}" width="{W}" height="{n(ABOT - SHORE + 10)}" fill="url(#{ID}-liquid)"/>']
refl = "".join(planet) + "".join(mtn)
sea.append(f'<g clip-path="url(#{ID}-sea)"><g filter="url(#{ID}-ripple)" opacity="0.55">'
           f'<g transform="translate(0 {2 * SHORE}) scale(1 -1)">' + refl + "</g></g></g>")
streaks = []
for i in range(340):
    t = rnd.random() ** 1.6
    y = SHORE + 6 + t * (ABOT - SHORE - 20)
    persp = 0.4 + 1.6 * t
    if rnd.random() < 0.75:          # glitter column under the planet
        x = px + rnd.gauss(0, 70 + 140 * t)
        col = rnd.choice([GOLD_L, GOLD, "#FFFFFF", "#FFB86A", "#FF9ACD"])
        op = rnd.uniform(0.45, 1.0)
    else:
        x = rnd.uniform(AX0, AX1)
        col = rnd.choice([CYAN, PERI, "#8FA8FF", LAV])
        op = rnd.uniform(0.2, 0.5)
    L = rnd.uniform(8, 60) * persp
    wdt = rnd.uniform(2.5, 3.2 + 2.5 * t)
    streaks.append(f'<rect x="{n(x - L / 2)}" y="{n(y - wdt / 2)}" width="{n(L)}" height="{n(wdt)}" rx="{n(wdt / 2)}" '
                   f'fill="{col}" fill-opacity="{n(op, 2)}"/>')
sea.append(f'<g filter="url(#{ID}-blur-m)" opacity="0.6"><ellipse cx="{px}" cy="{SHORE + 70}" rx="120" ry="60" '
           f'fill="{GOLD}" fill-opacity="0.35"/></g>')
sea.append("".join(streaks))
sea.append(f'<rect x="0" y="{SHORE - 1.5}" width="{W}" height="3" fill="#FF9ACD" fill-opacity="0.75"/>')


def flare(x, y, rr, kind="", rot=0.0, halo=0.55):
    ray = f"url(#{ID}-ray-warm)" if kind == "-gold" else f"url(#{ID}-ray)"
    return (f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rr * halo)}" fill="url(#{ID}-fl{kind})"/>'
            f'<path d="{star4(x, y, rr, 0.075, rot)}" fill="{ray}"/>'
            f'<path d="{star4(x, y, rr * 0.38, 0.12, rot + math.pi / 4)}" fill="{ray}" fill-opacity="0.7"/>'
            f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(max(1.6, rr * 0.06))}" fill="#FFFFFF"/>')


fl = [flare(x, y, r, k) for (x, y, r, k) in ((300, 230, 44, ""), (560, 150, 20, "-gold"), (180, 450, 16, ""),
                                             (1010, 330, 26, ""), (690, 400, 13, "-gold"), (430, 640, 12, ""))]
# sparkles on the liquid
fl += [flare(x, y, r, "-gold") for (x, y, r) in ((760, 1000, 30), (850, 960, 18), (690, 1080, 14))]
fl += [flare(x, y, r, "") for (x, y, r) in ((320, 1040, 16), (1000, 1060, 12))]

# ---------------------------------------------------------------- assemble the window
body = []
body.append(f'<g id="{ID}-window" clip-path="url(#{ID}-arch)">')
body += sky
body.append(f'<g id="{ID}-planet">' + "".join(planet) + "</g>")
body.append(f'<g id="{ID}-crags">' + "".join(mtn) + "</g>")
body.append(f'<g id="{ID}-sea">' + "".join(sea) + "</g>")
body.append(f'<g id="{ID}-flares">' + "".join(fl) + "</g>")
body.append("</g>")
# frame: double rule
body.append(f'<path d="{arch_d()}" fill="none" stroke="{LAV}" stroke-width="4"/>')
body.append(f'<path d="{arch_d(-14, 60)}" fill="none" stroke="{PERI}" stroke-width="2.5" stroke-opacity="0.7"/>')

# small window captions
cap = []
t = text_path(SPACE_B, "VEDERE DIN TABĂRA 3", 16, 600, 196, tracking=200)
cap.append(f'<path d="{t["d"]}" fill="{CHROME}" fill-opacity="0.85"/>')
t = text_path(SPACE, "OXIGEN 4% · VALURI 0 · VREME BUNĂ, ÎN GENERAL", 15, 600, 1440, tracking=140)
cap.append(f'<path d="{t["d"]}" fill="{LAV}" fill-opacity="0.7"/>')
body.append(f'<g id="{ID}-captions">' + "".join(cap) + "</g>")

# ---------------------------------------------------------------- title
tt = text_path(UNB_BLACK, "PLANETA B", TS, W / 2, TY)
body.append(f'<g id="{ID}-title">')
for k in range(12, 0, -1):
    body.append(f'<path d="{tt["d"]}" fill="{mix("#3D5AFE", "#0E0D38", k / 12)}" transform="translate({n(k * 0.7)} {n(k * 1.1)})"/>')
body.append(f'<path d="{tt["d"]}" fill="#07070D" stroke="#07070D" stroke-width="10" stroke-linejoin="round" '
            f'transform="translate(0 2)" opacity="0.5"/>')
body.append(f'<path d="{tt["d"]}" fill="url(#{ID}-chrome)"/>')
body.append(flare(W / 2 - 1060 / 2 + 40, TY - TS * 0.74, 34, ""))
body.append(flare(W / 2 + 1060 / 2 - 22, TY - TS * 0.05, 22, ""))
body.append("</g>")
YS = TY + 70
sub = text_path(SPACE_B, "ÎNCĂ NU E GATA", 28, W / 2, YS, tracking=420)
sw = sub["width"]
body.append(f'<rect x="90" y="{n(YS - 12)}" width="{n(W / 2 - sw / 2 - 130)}" height="3" fill="url(#{ID}-rule)"/>')
body.append(f'<rect x="{n(W / 2 + sw / 2 + 40)}" y="{n(YS - 12)}" width="{n(W / 2 - sw / 2 - 130)}" height="3" fill="url(#{ID}-rule)"/>')
body.append(f'<path id="{ID}-subtitle" d="{sub["d"]}" fill="{GOLD}"/>')
sig = text_path(SPACE_B, SIGNATURE, 18, W / 2, 1478, tracking=260)
body.append(f'<path id="{ID}-signature" d="{sig["d"]}" fill="{PERI}" fill-opacity="0.85"/>')

size = write_svg(OUT, body, "".join(defs))
print(OUT, size // 1024, "KB", "title size", round(TS), "arch bottom", round(ABOT))
