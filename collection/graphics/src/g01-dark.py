#!/usr/bin/env python3
"""g01-dark — NEPĂMÂNTEAN (hero print).
Warped, 3D-extruded wordmark in Unbounded Black over an indigo-violet vortex of
light streaks converging on a black core; sparkles, chromatic aberration and an
original parody classification label underneath. Poster 1200x1500, transparent.
Run: python3 graphics/src/g01-dark.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_lib import (MICH, MONO, MONO_B, ROOT, SIGNATURE, SVG, UNB, extrude, f1, globe, mix,  # noqa: E402
                      n_badge, notched, sparkles, warped)

ID = "g01-dark"
OUT = os.path.join(ROOT, "graphics", ID + ".svg")
W, H = 1200, 1500
rnd = random.Random(101)
svg = SVG(ID, W, H)

CX, CY = 600, 545
Q, ROT = 0.84, math.radians(-10)
CORE = 104

VOID = "#07070D"
LAV = "#C9C3FF"
CHROME = "#F2F4FF"


def P(r, th):
    x, y = r * math.cos(th), r * math.sin(th) * Q
    c, s = math.cos(ROT), math.sin(ROT)
    return CX + x * c - y * s, CY + x * s + y * c


# ------------------------------------------------------------------ defs
svg.d(f'<radialGradient id="{svg.id("haze")}" cx="{CX}" cy="{CY}" r="600" gradientUnits="userSpaceOnUse" '
      f'gradientTransform="translate({CX} {CY}) rotate(-10) scale(1 {Q}) translate(-{CX} -{CY})">'
      '<stop offset="0" stop-color="#07070D" stop-opacity="1"/>'
      '<stop offset="0.15" stop-color="#07070D" stop-opacity="1"/>'
      '<stop offset="0.19" stop-color="#8A6BFF" stop-opacity="0.75"/>'
      '<stop offset="0.36" stop-color="#4A33D0" stop-opacity="0.42"/>'
      '<stop offset="0.7" stop-color="#24228A" stop-opacity="0.16"/>'
      '<stop offset="1" stop-color="#24228A" stop-opacity="0"/></radialGradient>')
svg.d(f'<filter id="{svg.id("glow")}" x="-0.2" y="-0.2" width="1.4" height="1.4" color-interpolation-filters="sRGB">'
      '<feGaussianBlur stdDeviation="7"/></filter>')
svg.d(f'<filter id="{svg.id("soft")}" x="-0.5" y="-0.5" width="2" height="2" color-interpolation-filters="sRGB">'
      '<feGaussianBlur stdDeviation="3"/></filter>')
svg.d(f'<filter id="{svg.id("bloom")}" x="-0.3" y="-0.6" width="1.6" height="2.2" color-interpolation-filters="sRGB">'
      '<feGaussianBlur stdDeviation="16"/></filter>')

# ------------------------------------------------------------------ vortex
svg.add(f'<ellipse cx="{CX}" cy="{CY}" rx="600" ry="{600 * Q}" transform="rotate(-10 {CX} {CY})" fill="url(#{svg.id("haze")})"/>')


def streak(r0, th0, length, k, wmax, steps=16):
    pts, nor = [], []
    for j in range(steps + 1):
        u = j / steps
        th = th0 + length * u
        r = r0 * math.exp(-k * length * u)
        pts.append(P(r, th))
    for j in range(len(pts)):
        a = pts[max(j - 1, 0)]
        b = pts[min(j + 1, len(pts) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nor.append((-dy / ln, dx / ln))
    left, right = [], []
    for j, (p, nv) in enumerate(zip(pts, nor)):
        u = j / steps
        w = max(1.3, wmax * math.sin(math.pi * u) ** 0.8 / 2)
        left.append((p[0] + nv[0] * w, p[1] + nv[1] * w))
        right.append((p[0] - nv[0] * w, p[1] - nv[1] * w))
    poly = left + right[::-1]
    return "M" + "L".join(f"{f1(x)} {f1(y)}" for x, y in poly) + "Z"


STOPS = [(0.0, "#F2F4FF"), (0.08, "#C9C3FF"), (0.22, "#8F7BFF"), (0.42, "#6A4BFF"),
         (0.65, "#4632C8"), (1.0, "#24228A")]


def ramp(t):
    for (p0, c0), (p1, c1) in zip(STOPS, STOPS[1:]):
        if t <= p1:
            return mix(c0, c1, (t - p0) / (p1 - p0))
    return STOPS[-1][1]


far, near, bright = [], [], []
TINTS = ["#FF3DA8", "#3D5AFE", "#5FF3FF"]
for i in range(1150):
    u = rnd.random() ** 1.25
    r0 = CORE + 14 + u * 480
    th0 = rnd.uniform(0, 2 * math.pi)
    length = rnd.uniform(0.35, 1.3) * (1.45 - 0.75 * u)
    k = rnd.uniform(0.25, 0.5) * (1.3 - 0.5 * u)
    t = (r0 - CORE) / 495
    wmax = 2.8 + 6.5 * t * rnd.uniform(0.4, 1.0)
    col = ramp(min(1, t + rnd.uniform(-0.1, 0.12)))
    if rnd.random() < 0.12:
        col = mix(col, rnd.choice(TINTS), 0.35)
    op = (1.0 - 0.6 * t) * rnd.uniform(0.55, 1.0)
    d = streak(r0, th0, length, k, wmax)
    item = f'<path d="{d}" fill="{col}" opacity="{f1(op, 2)}"/>'
    (far if t > 0.45 else near).append(item)
    if t < 0.3 and rnd.random() < 0.3:
        bright.append(f'<path d="{d}" fill="{col}"/>')

svg.d(f'<linearGradient id="{svg.id("fadeg")}" x1="0" y1="0" x2="0" y2="1500" gradientUnits="userSpaceOnUse">'
      '<stop offset="0.07" stop-color="#FFFFFF" stop-opacity="0"/><stop offset="0.16" stop-color="#FFFFFF"/>'
      '<stop offset="0.66" stop-color="#FFFFFF"/><stop offset="0.75" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>')
svg.d(f'<mask id="{svg.id("fade")}" maskUnits="userSpaceOnUse" x="0" y="0" width="1200" height="1500">'
      f'<rect width="1200" height="1500" fill="url(#{svg.id("fadeg")})"/></mask>')
svg.add(f'<g mask="url(#{svg.id("fade")})">')
svg.add('<g>' + "".join(far) + '</g>')
svg.add(f'<g filter="url(#{svg.id("glow")})" opacity="0.8">' + "".join(bright) + '</g>')
svg.add('<g>' + "".join(near) + '</g>')
svg.add('</g>')

# core: black hole with a photon ring
ell = lambda r: f'cx="{CX}" cy="{CY}" rx="{f1(r)}" ry="{f1(r * Q)}" transform="rotate(-10 {CX} {CY})"'
svg.add(f'<ellipse {ell(CORE + 8)} fill="none" stroke="#B9AEFF" stroke-width="10" opacity="0.7" filter="url(#{svg.id("soft")})"/>')
svg.add(f'<ellipse {ell(CORE)} fill="{VOID}"/>')
svg.add(f'<ellipse {ell(CORE + 3)} fill="none" stroke="#E6E2FF" stroke-width="3"/>')

# ------------------------------------------------------------------ wordmark
TY = 735
d, bb = warped(UNB, "NEPĂMÂNTEAN", 104, 600, TY, sy=1.55,
               warps=["wave:0.11:1.0:0.0", "bulge:0.62"], steps=8)
x0, y0, x1, y1 = bb
pid, stack = extrude(svg, "word", d, depth=28, dx=0.55, dy=2.05, back="#0A0930", front="#2C27A0")

svg.d(f'<linearGradient id="{svg.id("face")}" x1="0" y1="{f1(y0)}" x2="0" y2="{f1(y1)}" gradientUnits="userSpaceOnUse">'
      '<stop offset="0" stop-color="#B4B2FF"/><stop offset="0.38" stop-color="#7C7CFF"/>'
      '<stop offset="0.72" stop-color="#4F63FF"/><stop offset="1" stop-color="#3D5AFE"/></linearGradient>')
svg.d(f'<linearGradient id="{svg.id("gloss")}" x1="0" y1="{f1(y0)}" x2="0" y2="{f1(y1)}" gradientUnits="userSpaceOnUse">'
      '<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.55"/><stop offset="0.3" stop-color="#FFFFFF" stop-opacity="0.08"/>'
      '<stop offset="0.31" stop-color="#FFFFFF" stop-opacity="0"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>')
svg.d(f'<clipPath id="{svg.id("faceclip")}"><use href="#{pid}"/></clipPath>')

# bloom behind the word
svg.add(f'<use href="#{pid}" x="0" y="14" fill="#5B4BFF" opacity="0.55" filter="url(#{svg.id("bloom")})"/>')
svg.add(f'<g>{stack}</g>')
# chromatic aberration ghosts (fringe out on left / right)
svg.add(f'<use href="#{pid}" x="-7" y="-1" fill="#5FF3FF" opacity="0.6" style="mix-blend-mode:screen"/>')
svg.add(f'<use href="#{pid}" x="7" y="2" fill="#FF3DA8" opacity="0.55" style="mix-blend-mode:screen"/>')
# lavender highlight edge, then the face
svg.add(f'<use href="#{pid}" x="-2.2" y="-3" fill="{LAV}"/>')
svg.add(f'<use href="#{pid}" fill="url(#{svg.id("face")})"/>')
svg.add(f'<use href="#{pid}" fill="url(#{svg.id("gloss")})"/>')
# fine horizontal VHS lines across the face
lines = "".join(f'M{f1(x0)} {f1(yy)}H{f1(x1)}' for yy in range(int(y0) + 4, int(y1), 8))
svg.add(f'<g clip-path="url(#{svg.id("faceclip")})"><path d="{lines}" stroke="#24228A" stroke-width="2.6" opacity="0.12"/></g>')

# ------------------------------------------------------------------ sparkles
def avoid(px, py):
    if x0 - 20 < px < x1 + 20 and y0 - 30 < py < y1 + 70:
        return True
    dx, dy = px - CX, (py - CY) / Q
    return math.hypot(dx, dy) < CORE + 30


svg.add(sparkles(rnd, 46, (40, 60, 1160, 1120), rmin=6, rmax=26, color=CHROME, avoid=avoid, glow_id=svg.id("soft")))
for px, py, r in ((168, 318, 34), (1030, 905, 30), (930, 210, 18)):
    from hero_lib import star4
    svg.add(f'<circle cx="{px}" cy="{py}" r="{r * 0.5}" fill="#C9C3FF" opacity="0.6" filter="url(#{svg.id("soft")})"/>')
    svg.add(f'<path d="{star4(px, py, r, waist=0.08)}" fill="{CHROME}"/>')

# ------------------------------------------------------------------ top kicker
svg.add(svg.small(MICH, "TRANSMISIUNE RECEPȚIONATĂ", 17, 60, 70, LAV, tracking=260, opacity=0.9))
svg.add(svg.small(MICH, "NU DE PE PĂMÂNTUL ĂSTA", 17, 1140, 70, LAV, anchor="end", tracking=260, opacity=0.9))
svg.add(f'<path d="M60 92H1140" stroke="{LAV}" stroke-width="2.6" opacity="0.35"/>')

# ------------------------------------------------------------------ classification label
LX, LY, LW, LH = 150, 1190, 900, 214
INK = "#E9E6FF"
svg.add(f'<path d="{notched(LX, LY, LW, LH, 22)}" fill="#0B0A22" fill-opacity="0.55" stroke="{INK}" stroke-width="5"/>')
svg.add(f'<path d="{notched(LX + 11, LY + 11, LW - 22, LH - 22, 15)}" fill="none" stroke="{INK}" stroke-width="2.6" opacity="0.7"/>')
# N badge
bx, by = LX + 118, LY + LH / 2
svg.add(n_badge(svg, bx, by, 68, INK, "#0B0A22", ring=INK))
# divider
svg.add(f'<path d="M{LX + 222} {LY + 30}V{LY + LH - 30}" stroke="{INK}" stroke-width="3"/>')
tx = LX + 250
svg.add(svg.small(MICH, "CLASIFICAT:", 21, tx, LY + 58, LAV, tracking=200))
dd, _, ww = svg.text_d(UNB, "NEPĂMÂNTEAN", 47, tx - 2, LY + 112)
svg.add(f'<path d="{dd}" fill="{INK}"/>')
svg.add(f'<path d="M{tx} {LY + 134}H{LX + LW - 150}" stroke="{INK}" stroke-width="2.6" opacity="0.8"/>')
svg.add(svg.small(MONO_B, "Sub 17 ani doar însoțit de un", 18, tx, LY + 161, INK))
svg.add(svg.small(MONO_B, "extraterestru adult.", 18, tx, LY + 184, INK))
# globe + caption
gx, gy = LX + LW - 82, LY + 86
svg.add(globe(gx, gy, 40, INK, sw=2.6, tilt=-20, lat=3, lon=4))
svg.add(svg.small(MONO_B, "TERRA?", 16, gx, LY + 160, LAV, anchor="middle", tracking=80))
svg.add(svg.small(MONO_B, "NU.", 16, gx, LY + 182, LAV, anchor="middle", tracking=80))
# under-label line
svg.add(svg.small(MICH, "COMISIA INTERGALACTICĂ DE CLASIFICARE", 13.5, LX + 4, LY + LH + 34, LAV, tracking=180, opacity=0.85))
svg.add(svg.small(MICH, SIGNATURE, 13.5, LX + LW - 4, LY + LH + 34, LAV, anchor="end", tracking=180, opacity=0.85))

size = svg.save(OUT)
print(OUT, size)
