#!/usr/bin/env python3
"""g03-dark — REALITATEA E O SIMULARE.
An original zine poster seen on a CRT: black rounded panel, RGB subpixel + scanline texture,
vignette + bloom, narrow left column (wireframe globe, flower of life, tiny text blocks),
giant posterized eye, huge headline, fine print and a second headline.
Run: python3 graphics/src/g03-dark.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crt_lib import PAL, SVG, ROOT, f1, mix, poly_d, rrect_d, circle_pts, render, FABRIC_DARK  # noqa: E402

FID = "g03-dark"
W, H = 1200, 1500
OUT = os.path.join(ROOT, "graphics", FID + ".svg")
rnd = random.Random(303)

svg = SVG(FID, W, H)
ID = svg.id
mono = svg.atlas("SpaceMono-Bold")
plex = svg.atlas("IBMPlexMono-Medium")

# ---------------------------------------------------------------- panel
PX, PY, PW, PH, PR = 22, 22, 1156, 1456, 74
panel_d = rrect_d(PX, PY, PW, PH, PR)
svg.d(f'<clipPath id="{ID("clip")}"><path d="{panel_d}"/></clipPath>')
svg.d(f'<radialGradient id="{ID("screen")}" cx="600" cy="700" r="900" gradientUnits="userSpaceOnUse">'
      f'<stop offset="0" stop-color="#121232"/><stop offset="0.55" stop-color="#0A0A1A"/>'
      f'<stop offset="1" stop-color="{PAL["void"]}"/></radialGradient>')
svg.d(f'<radialGradient id="{ID("vig")}" cx="600" cy="740" r="1010" gradientUnits="userSpaceOnUse">'
      f'<stop offset="0.52" stop-color="{PAL["void"]}" stop-opacity="0"/>'
      f'<stop offset="0.8" stop-color="{PAL["void"]}" stop-opacity="0.35"/>'
      f'<stop offset="1" stop-color="{PAL["void"]}" stop-opacity="0.92"/></radialGradient>')
svg.d(f'<linearGradient id="{ID("glare")}" x1="0" y1="0" x2="1" y2="1">'
      f'<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.11"/>'
      f'<stop offset="0.6" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>')
svg.d(f'<filter id="{ID("bloom")}" x="-4%" y="-4%" width="108%" height="108%" color-interpolation-filters="sRGB">'
      f'<feGaussianBlur in="SourceGraphic" stdDeviation="7" result="b"/>'
      f'<feColorMatrix in="b" type="matrix" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 0.7 0" result="b2"/>'
      f'<feMerge><feMergeNode in="b2"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
svg.d(f'<filter id="{ID("soft")}" x="-20%" y="-20%" width="140%" height="140%">'
      f'<feGaussianBlur stdDeviation="40"/></filter>')
# CRT textures
svg.d(f'<pattern id="{ID("sub")}" patternUnits="userSpaceOnUse" width="9" height="12">'
      f'<rect x="0" y="0" width="3" height="12" fill="#FF8F9C"/>'
      f'<rect x="3" y="0" width="3" height="12" fill="#9CFFC8"/>'
      f'<rect x="6" y="0" width="3" height="12" fill="#98ACFF"/></pattern>')
svg.d(f'<pattern id="{ID("scan")}" patternUnits="userSpaceOnUse" width="12" height="6">'
      f'<rect x="0" y="3.4" width="12" height="2.6" fill="{PAL["void"]}"/></pattern>')

svg.add(f'<g clip-path="{svg.ref("clip")}">')
svg.add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{svg.ref("screen")}"/>')
# soft phosphor light behind hero elements
svg.add(f'<g filter="{svg.ref("soft")}" opacity="0.55">'
        f'<ellipse cx="760" cy="370" rx="360" ry="200" fill="{PAL["indigo"]}"/>'
        f'<ellipse cx="600" cy="1010" rx="560" ry="150" fill="{PAL["indigo"]}"/>'
        f'<ellipse cx="200" cy="270" rx="140" ry="140" fill="{PAL["indigo"]}"/></g>')

C = []  # content (bloomed)

# ---------------------------------------------------------------- header
TOP = 92
C.append(mono.line("ONYXLAB · NEPĂMÂNTEAN · 2026", 20, 86, TOP, PAL["cyan"]))
C.append(f'<circle cx="548" cy="{TOP - 7}" r="7" fill="{PAL["orange"]}"/>')
C.append(mono.line("REC 03:33:07", 20, 564, TOP, PAL["white"]))
C.append(mono.line("CANAL 03 / ARHIVĂ", 20, 1114, TOP, PAL["cyan"], anchor="end"))
# ruler with ticks
ticks = []
for i in range(0, 104):
    x = 86 + i * 10.0
    hgt = 12 if i % 10 == 0 else (8 if i % 5 == 0 else 5)
    ticks.append(f"M{f1(x)} 112v{hgt}")
C.append(f'<path d="M86 112H1114" stroke="{PAL["white"]}" stroke-width="3" fill="none"/>')
C.append(f'<path d="{"".join(ticks)}" stroke="{PAL["white"]}" stroke-width="2.6" fill="none" opacity="0.8"/>')

# ---------------------------------------------------------------- left column
LX0, LX1 = 86, 316
LCX = (LX0 + LX1) / 2


def sphere_lines(cx, cy, R, tilt, yaw):
    """Wireframe sphere: return list of (points, front) segments."""
    ct, st = math.cos(tilt), math.sin(tilt)
    cyw, syw = math.cos(yaw), math.sin(yaw)

    def proj(lat, lon):
        x = math.cos(lat) * math.cos(lon)
        y = math.sin(lat)
        z = math.cos(lat) * math.sin(lon)
        x, z = x * cyw - z * syw, x * syw + z * cyw   # yaw about y
        y, z = y * ct - z * st, y * st + z * ct       # tilt about x
        return cx + R * x, cy - R * y, z

    curves = []
    for lat in range(-60, 61, 30):
        curves.append([proj(math.radians(lat), math.radians(a)) for a in range(0, 361, 4)])
    for lon in range(0, 180, 30):
        curves.append([proj(math.radians(a), math.radians(lon)) for a in range(0, 361, 4)])
    segs = []
    for c in curves:
        cur, front = [c[0]], c[0][2] >= 0
        for p in c[1:]:
            f = p[2] >= 0
            if f != front:
                cur.append(p)
                segs.append((cur, front))
                cur, front = [p], f
            else:
                cur.append(p)
        segs.append((cur, front))
    return segs


GX, GY, GR = LCX, 262, 98
# orbit ring (back half first)
orb = []
for i in range(0, 361, 3):
    a = math.radians(i)
    x, y = 148 * math.cos(a), 34 * math.sin(a)
    rot = math.radians(-16)
    orb.append((GX + x * math.cos(rot) - y * math.sin(rot), GY + x * math.sin(rot) + y * math.cos(rot), math.sin(a)))
back_orb = [p for p in orb if p[2] < 0]
front_orb = [p for p in orb if p[2] >= 0]
C.append(f'<path d="{poly_d([(p[0], p[1]) for p in back_orb], close=False)}" fill="none" stroke="{PAL["peri"]}" stroke-width="2.6" opacity="0.7"/>')
back, front = [], []
for pts, fr in sphere_lines(GX, GY, GR, math.radians(23.4), math.radians(18)):
    (front if fr else back).append(poly_d([(p[0], p[1]) for p in pts], close=False))
C.append(f'<circle cx="{GX}" cy="{GY}" r="{GR}" fill="{PAL["void"]}" fill-opacity="0.6"/>')
C.append(f'<path d="{"".join(back)}" fill="none" stroke="{PAL["blue"]}" stroke-width="2.6" opacity="0.75"/>')
C.append(f'<path d="{"".join(front)}" fill="none" stroke="{PAL["cyan"]}" stroke-width="3.2" stroke-linecap="round"/>')
C.append(f'<circle cx="{GX}" cy="{GY}" r="{GR}" fill="none" stroke="{PAL["cyan"]}" stroke-width="4.5"/>')
C.append(f'<path d="{poly_d([(p[0], p[1]) for p in front_orb], close=False)}" fill="none" stroke="{PAL["white"]}" stroke-width="3.4"/>')
# satellite on the orbit
sp = front_orb[len(front_orb) * 2 // 3]
C.append(f'<rect x="{f1(sp[0] - 7)}" y="{f1(sp[1] - 7)}" width="14" height="14" transform="rotate(45 {f1(sp[0])} {f1(sp[1])})" fill="{PAL["orange"]}"/>')
# node marker on the globe
C.append(f'<circle cx="{GX + 26}" cy="{GY - 30}" r="6" fill="{PAL["orange"]}"/>'
         f'<circle cx="{GX + 26}" cy="{GY - 30}" r="15" fill="none" stroke="{PAL["orange"]}" stroke-width="3"/>')

y = 408
C.append(mono.line("REȚEAUA GLOBALĂ", 20, LX0, y, PAL["white"]))
C.append(mono.line("NOD 07 · ACTIV", 20, LX0, y + 25, PAL["cyan"]))
C.append(f'<path d="M{LX0} {y + 44}H{LX1}" stroke="{PAL["peri"]}" stroke-width="3"/>')
y += 82
blk = ["GEOMETRIA E", "CODUL SURSĂ.", "TOT RESTUL", "E DECOR."]
for i, ln in enumerate(blk):
    C.append(mono.line(ln, 20, LX0, y + i * 24, PAL["lav"]))
y += len(blk) * 24 + 8

# flower of life
FX, FY, FR = LCX, y + 98, 28
centers = [(0, 0)]
for ring in (1, 2):
    for k in range(6):
        a0 = math.radians(60 * k - 90)
        a1 = math.radians(60 * (k + 1) - 90)
        for j in range(ring):
            t = j / ring
            px = ring * ((1 - t) * math.cos(a0) + t * math.cos(a1))
            py = ring * ((1 - t) * math.sin(a0) + t * math.sin(a1))
            centers.append((px * FR, py * FR))
svg.d(f'<clipPath id="{ID("fol")}"><circle cx="{f1(FX)}" cy="{f1(FY)}" r="{3 * FR}"/></clipPath>')
circ = "".join(f'<circle cx="{f1(FX + cx)}" cy="{f1(FY + cy)}" r="{FR}"/>' for cx, cy in centers)
C.append(f'<g clip-path="{svg.ref("fol")}" fill="none" stroke="{PAL["lav"]}" stroke-width="2.8">{circ}</g>')
C.append(f'<circle cx="{f1(FX)}" cy="{f1(FY)}" r="{3 * FR}" fill="none" stroke="{PAL["white"]}" stroke-width="4"/>')
C.append(f'<circle cx="{f1(FX)}" cy="{f1(FY)}" r="{3 * FR + 9}" fill="none" stroke="{PAL["peri"]}" stroke-width="2.6"/>')
C.append(f'<circle cx="{f1(FX)}" cy="{f1(FY)}" r="{FR}" fill="none" stroke="{PAL["orange"]}" stroke-width="3.6"/>')
y = FY + 3 * FR + 44
C.append(mono.line("FIG. 02", 20, LX0, y, PAL["orange"]))
C.append(mono.line("FLOAREA VIEȚII", 20, LX0, y + 24, PAL["white"]))
LEFT_BOTTOM = y + 24

# vertical divider
C.append(f'<path d="M340 140V{f1(LEFT_BOTTOM + 4)}" stroke="{PAL["peri"]}" stroke-width="3" stroke-dasharray="3 7"/>')

# ---------------------------------------------------------------- the eye
EX0, EX1, ECY = 392, 1092, 372
HU, HL = 168, 112


def upper(t):
    tt = max(min(t, 1), 0)
    return (EX0 + (EX1 - EX0) * tt, ECY - 18 * tt - HU * math.sin(math.pi * tt ** 0.87) ** 0.82)


def lower(t):
    tt = max(min(t, 1), 0)
    return (EX0 + (EX1 - EX0) * tt, ECY - 18 * tt + HL * math.sin(math.pi * tt ** 1.16) ** 1.05)


def normal_up(t, eps=1e-3):
    a, b = upper(t - eps), upper(t + eps)
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return dy / n, -dx / n  # points "up/out"


N = 160
up_pts = [upper(i / N) for i in range(N + 1)]
lo_pts = [lower(i / N) for i in range(N + 1)]
sclera = up_pts + lo_pts[::-1][1:-1]
sclera_d = poly_d(sclera)
svg.d(f'<clipPath id="{ID("eye")}"><path d="{sclera_d}"/></clipPath>')

# line-halftone skin around the eye (posterized line weights)
def skin(x, y):
    e = ((x - 742) / 395) ** 2 + ((y - 360) / 238) ** 2
    b = max(0.0, 1 - e) ** 0.75
    # crease shadow just above the upper lid
    t = (x - EX0) / (EX1 - EX0)
    if 0 <= t <= 1:
        uy = upper(t)[1]
        d = uy - y  # distance above lid
        if 6 < d < 70:
            b *= 0.25 + 0.75 * abs(d - 38) / 32
        ly = lower(t)[1]
        d2 = y - ly
        if 0 < d2 < 50:
            b *= 0.45 + 0.55 * d2 / 50
    # brow bone highlight band
    b *= 1 + 0.25 * math.exp(-((y - 150) / 40) ** 2)
    return min(b, 1.0)


rows = []
for yy in range(146, 600, 9):
    seg = []
    for xi in range(0, 101):
        x = 352 + xi * 7.64
        b = skin(x, yy)
        th = 0 if b < 0.13 else 2.6 + 3.2 * b
        seg.append((x, th))
    # split into runs where th > 0
    run = []
    for x, th in seg + [(0, 0)]:
        if th > 0:
            run.append((x, th))
        elif run:
            if len(run) > 1:
                top = [(x_, yy - t_ / 2) for x_, t_ in run]
                bot = [(x_, yy + t_ / 2) for x_, t_ in run[::-1]]
                rows.append(poly_d(top + bot))
            run = []
svg.d(f'<radialGradient id="{ID("skin")}" cx="742" cy="372" r="420" gradientUnits="userSpaceOnUse">'
      f'<stop offset="0" stop-color="{PAL["lav"]}"/><stop offset="0.55" stop-color="{PAL["peri"]}"/>'
      f'<stop offset="1" stop-color="{PAL["blue"]}"/></radialGradient>')
C.append(f'<path d="{"".join(rows)}" fill="{svg.ref("skin")}"/>')

# sclera: posterized shading (3 flat tones)
eye = [f'<path d="{sclera_d}" fill="#8F8BF2"/>',
       f'<g clip-path="{svg.ref("eye")}">',
       f'<ellipse cx="748" cy="372" rx="318" ry="190" fill="{PAL["lav"]}"/>',
       f'<ellipse cx="755" cy="380" rx="262" ry="170" fill="{PAL["white"]}"/>']
# shadow band under the upper lid
band = [upper(i / N) for i in range(N + 1)]
band2 = [(x, y + 30 + 16 * math.sin(math.pi * (i / N))) for i, (x, y) in enumerate(band)]
eye.append(f'<path d="{poly_d(band + band2[::-1])}" fill="{PAL["lav"]}"/>')
band3 = [(x, y + 12 + 6 * math.sin(math.pi * (i / N))) for i, (x, y) in enumerate(band)]
eye.append(f'<path d="{poly_d(band + band3[::-1])}" fill="#8F8BF2"/>')

IX, IY, IR, PR_ = 752, 360, 140, 60
eye.append(f'<circle cx="{IX}" cy="{IY}" r="{IR}" fill="{PAL["void"]}"/>')
# iris fibres (indigo / electric blue, subtle)
fib = []
for k in range(120):
    a = 2 * math.pi * k / 120 + rnd.uniform(-0.01, 0.01)
    r0 = PR_ + 6 + rnd.uniform(0, 10)
    r1 = IR - 10 - rnd.uniform(0, 24)
    wob = rnd.uniform(-0.05, 0.05)
    fib.append(f"M{f1(IX + r0 * math.cos(a))} {f1(IY + r0 * math.sin(a))}L{f1(IX + r1 * math.cos(a + wob))} {f1(IY + r1 * math.sin(a + wob))}")
eye.append(f'<path d="{"".join(fib[0::2])}" stroke="{PAL["indigo"]}" stroke-width="2.6" fill="none"/>')
eye.append(f'<path d="{"".join(fib[1::2])}" stroke="{PAL["blue"]}" stroke-width="2.6" fill="none" opacity="0.55"/>')
coll = []
for k in range(73):
    a = 2 * math.pi * k / 72
    r = 86 + 7 * math.sin(k * 1.7) + 4 * math.sin(k * 4.3)
    coll.append((IX + r * math.cos(a), IY + r * math.sin(a)))
eye.append(f'<path d="{poly_d(coll)}" fill="none" stroke="{PAL["blue"]}" stroke-width="3"/>')
eye.append(f'<circle cx="{IX}" cy="{IY}" r="{IR}" fill="none" stroke="{PAL["void"]}" stroke-width="10"/>')
eye.append(f'<circle cx="{IX}" cy="{IY}" r="{PR_}" fill="{PAL["void"]}"/>')
# glint: a tiny CRT window reflected in the eye
gx, gy = IX + 30, IY - 74
eye.append(f'<path d="{rrect_d(gx, gy, 52, 42, 10)}" fill="{PAL["white"]}"/>')
eye.append(f'<path d="M{gx + 26} {gy + 4}V{gy + 38}M{gx + 4} {gy + 21}H{gx + 48}" stroke="{PAL["void"]}" stroke-width="4"/>')
eye.append(f'<circle cx="{IX - 46}" cy="{IY + 44}" r="9" fill="{PAL["white"]}"/>')
# lid shadow over the iris top
eye.append(f'<path d="{poly_d(band + band3[::-1])}" fill="{PAL["void"]}" opacity="0.5"/>')
eye.append("</g>")
C.extend(eye)

# caruncle (inner corner) — magenta accent
cx0, cy0 = upper(0)
C.append(f'<path d="M{f1(cx0 - 6)} {f1(cy0)}Q{f1(cx0 + 18)} {f1(cy0 - 22)} {f1(cx0 + 40)} {f1(cy0 - 4)}Q{f1(cx0 + 22)} {f1(cy0 + 20)} {f1(cx0 - 6)} {f1(cy0)}Z" fill="{PAL["magenta"]}"/>')


def band_poly(curve, t0, t1, w0, wm, w1, n=120, side=1.0, normal=None):
    """Variable-width band along a curve; widths at start/mid/end."""
    top, bot = [], []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        u = i / n
        w = (w0 * (1 - u) ** 2 + 2 * wm * u * (1 - u) + w1 * u * u)
        x, y = curve(t)
        nx, ny = normal(t)
        top.append((x + nx * w * side, y + ny * w * side))
        bot.append((x - nx * w * (1 - side), y - ny * w * (1 - side)))
    return poly_d(top + bot[::-1])


# upper lash line, thick
C.append(f'<path d="{band_poly(upper, 0.01, 1.0, 2, 17, 4, normal=normal_up, side=0.7)}" fill="{PAL["white"]}"/>')


def lower_n(t, eps=1e-3):
    a, b = lower(t - eps), lower(t + eps)
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return -dy / n, dx / n  # points down/out


C.append(f'<path d="{band_poly(lower, 0.07, 0.97, 1.5, 5, 1.5, normal=lower_n, side=0.6)}" fill="{PAL["lav"]}"/>')


# crease
def crease(t):
    x, y = upper(t)
    return x + 6, y - 46 - 26 * math.sin(math.pi * t)


def crease_n(t, eps=1e-3):
    a, b = crease(t - eps), crease(t + eps)
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return dy / n, -dx / n


C.append(f'<path d="{band_poly(crease, 0.14, 0.93, 1.3, 4.2, 1.3, normal=crease_n)}" fill="{PAL["white"]}"/>')

# lashes
lash = []
for k in range(34):
    t = 0.1 + 0.88 * k / 33 + rnd.uniform(-0.006, 0.006)
    x, y = upper(t)
    nx, ny = normal_up(t)
    L = 26 + 52 * t ** 1.4 + rnd.uniform(-5, 5)
    sweep = 0.25 + 0.75 * t  # lashes sweep toward the outer corner
    pts_l, pts_r = [], []
    for i in range(9):
        u = i / 8
        # direction rotates toward +x as the lash grows
        ang = math.atan2(ny, nx) + sweep * 0.9 * u * u
        px = x + nx * 8 + math.cos(ang) * L * u
        py = y + ny * 8 + math.sin(ang) * L * u
        wdt = 4.6 * (1 - u) + 1.4
        pa = ang + math.pi / 2
        pts_l.append((px + math.cos(pa) * wdt, py + math.sin(pa) * wdt))
        pts_r.append((px - math.cos(pa) * wdt, py - math.sin(pa) * wdt))
    lash.append(poly_d(pts_l + pts_r[::-1]))
C.append(f'<path d="{"".join(lash)}" fill="{PAL["white"]}"/>')
low = []
for k in range(16):
    t = 0.3 + 0.64 * k / 15
    x, y = lower(t)
    nx, ny = lower_n(t)
    L = 10 + 20 * t
    low.append(f"M{f1(x + nx * 5)} {f1(y + ny * 5)}l{f1(nx * L + 6 * t)} {f1(ny * L)}")
C.append(f'<path d="{"".join(low)}" stroke="{PAL["lav"]}" stroke-width="3" stroke-linecap="round" fill="none"/>')

# targeting brackets around the iris
bx0, by0, bx1, by1 = IX - 182, IY - 172, IX + 182, IY + 172
L_ = 40
br = (f"M{bx0} {by0 + L_}V{by0}H{bx0 + L_}M{bx1 - L_} {by0}H{bx1}V{by0 + L_}"
      f"M{bx1} {by1 - L_}V{by1}H{bx1 - L_}M{bx0 + L_} {by1}H{bx0}V{by1 - L_}")
C.append(f'<path d="{br}" fill="none" stroke="{PAL["orange"]}" stroke-width="5"/>')
C.append(mono.line("SUBIECT: TU · 99,7%", 20, bx1, by1 + 30, PAL["orange"], anchor="end"))
C.append(f'<path d="M{IX - 18} {IY}H{IX + 18}M{IX} {IY - 18}V{IY + 18}" stroke="{PAL["orange"]}" stroke-width="3"/>')

# caption under the eye
C.append(mono.line("FIG. 01 — OCHIUL DE SERVICIU. NU CLIPEȘTE DIN 1999.", 20, 362, 598, PAL["cyan"]))

# two paragraphs under the eye
pA = ("Tramvaiul vine fix când renunți să-l mai aștepți. Nu e noroc: e economie de memorie. "
      "Lumea se randează doar unde te uiți.")
pB = ("Ochiul de pe ecran nu te privește pe tine, ci prin tine. Fiecare deja-vu e un fișier salvat "
      "de două ori.")
colw = (1114 - 362 - 30) / 2
s1, yA = mono.para(pA, 20, 362, 636, colw, 24, PAL["white"], justify=False)
s2, yB = mono.para(pB, 20, 362 + colw + 30, 636, colw, 24, PAL["white"], justify=False)
C += [s1, s2]
PARA_BOTTOM = max(yA, yB)

# ---------------------------------------------------------------- headline
HL1_Y = 912
HL2_Y = HL1_Y + 186
SY = 1.32  # vertical stretch
d1, bb1, w1 = svg.text_d("Unbounded-Black", "REALITATEA E O", 101, 600, 0, anchor="middle", tracking=-8)
d2, bb2, w2 = svg.text_d("Unbounded-Black", "SIMULARE", 152, 600, 0, anchor="middle", tracking=-10)
svg.d(f'<path id="{ID("h1")}" d="{d1}"/>')
svg.d(f'<path id="{ID("h2")}" d="{d2}"/>')


def headline(ref, y, fill, sy, ghost=("cyan", "magenta"), off=6):
    t = f"translate(0 {y}) scale(1 {sy})"
    return (f'<g transform="{t}">'
            f'<use href="#{ID(ref)}" x="{-off}" fill="{PAL[ghost[0]]}"/>'
            f'<use href="#{ID(ref)}" x="{off}" fill="{PAL[ghost[1]]}"/>'
            f'<use href="#{ID(ref)}" fill="{fill}"/></g>')


# glitch tear: a slice of each headline shifted sideways
svg.d(f'<clipPath id="{ID("tearA")}"><rect x="0" y="{HL1_Y - 64}" width="1200" height="18"/></clipPath>')
svg.d(f'<clipPath id="{ID("keepA")}"><path d="M0 0H1200V{HL1_Y - 64}H0ZM0 {HL1_Y - 46}H1200V1500H0Z"/></clipPath>')
svg.d(f'<clipPath id="{ID("tearB")}"><rect x="0" y="{HL2_Y - 92}" width="1200" height="26"/></clipPath>')
svg.d(f'<clipPath id="{ID("keepB")}"><path d="M0 0H1200V{HL2_Y - 92}H0ZM0 {HL2_Y - 66}H1200V1500H0Z"/></clipPath>')
C.append(f'<g clip-path="{svg.ref("keepA")}">{headline("h1", HL1_Y, PAL["white"], SY)}</g>')
C.append(f'<g clip-path="{svg.ref("tearA")}"><g transform="translate(22 0)">{headline("h1", HL1_Y, PAL["white"], SY)}</g></g>')
C.append(f'<g clip-path="{svg.ref("keepB")}">{headline("h2", HL2_Y, PAL["orange"], SY)}</g>')
C.append(f'<g clip-path="{svg.ref("tearB")}"><g transform="translate(-30 0)">{headline("h2", HL2_Y, PAL["orange"], SY)}</g></g>')

# rule + second headline
R2 = HL2_Y + 38
C.append(f'<path d="M86 {R2}H1114" stroke="{PAL["white"]}" stroke-width="3"/>')
d3, bb3, w3 = svg.text_d("Unbounded-Black", "DOAR SEMNALUL E REAL", 63, 600, 0, anchor="middle", tracking=0)
svg.d(f'<path id="{ID("h3")}" d="{d3}"/>')
C.append(headline("h3", R2 + 72, PAL["cyan"], 1.12, ghost=("blue", "magenta"), off=4))
R3 = R2 + 96
C.append(f'<path d="M86 {R3}H1114" stroke="{PAL["white"]}" stroke-width="3"/>')

# three fine-print columns
cols = [("01 / SURSA", "Semnal prins la 03:33 de un televizor alb-negru din Vaslui, pe canalul care nu există. Antena știe."),
        ("02 / PROTOCOL", "Nu clipi. Nu schimba canalul. Dacă vezi aceeași pisică de două ori, anunță pe cineva."),
        ("03 / INSTRUCȚIUNI", "Dacă imaginea începe să tremure, nu e televizorul. Ești tu, trezindu-te.")]
cw = (1028 - 2 * 28) / 3
ys = R3 + 36
for i, (head, p) in enumerate(cols):
    x = 86 + i * (cw + 28)
    C.append(mono.line(head, 20, x, ys, PAL["orange"]))
    s_, _ = mono.para(p, 20, x, ys + 28, cw, 24, PAL["lav"], justify=False)
    C.append(s_)

# footer: barcode + note
FY0 = 1436
bc = []
x = 86
while x < 300:
    w = rnd.choice([3, 3, 4, 6, 8])
    bc.append(f"M{f1(x)} {FY0 - 26}h{w}v30h-{w}Z")
    x += w + rnd.choice([3, 4, 6])
C.append(f'<path d="{"".join(bc)}" fill="{PAL["white"]}"/>')
C.append(mono.line("ARHIVĂ DESECRETIZATĂ · A NU SE DIFUZA DUPĂ 03:33", 20, 1114, FY0, PAL["cyan"], anchor="end"))

svg.add(f'<g filter="{svg.ref("bloom")}">' + "\n".join(C) + "</g>")

# ---------------------------------------------------------------- CRT layers
svg.add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{svg.ref("sub")}" style="mix-blend-mode:multiply" opacity="0.55"/>')
svg.add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{svg.ref("scan")}" opacity="0.5"/>')
# faint rolling interference bands
svg.add(f'<rect x="0" y="520" width="{W}" height="60" fill="#FFFFFF" opacity="0.03"/>'
        f'<rect x="0" y="1240" width="{W}" height="26" fill="#FFFFFF" opacity="0.035"/>')
svg.add(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{svg.ref("vig")}"/>')
svg.add(f'<path d="M22 22H760Q420 400 22 760Z" fill="{svg.ref("glare")}"/>')
svg.add("</g>")
# tube rim
svg.add(f'<path d="{rrect_d(PX + 2, PY + 2, PW - 4, PH - 4, PR - 2)}" fill="none" stroke="{PAL["indigo"]}" stroke-width="4"/>')

if __name__ == "__main__":
    size = svg.save(OUT)
    print(OUT, size)
    if "--render" in sys.argv:
        print(render(OUT, sizes="900", bg=FABRIC_DARK))
