#!/usr/bin/env python3
"""g07-dark — CÂMP ADÂNC. Spiral galaxy of ~7500 particles on logarithmic arms, dust
lanes, star flares and a dark planet with a cyan rim light.
Poster 1200x1500, transparent background (particles print straight on dark fabric).
Run: python3 graphics/src/g07-dark.py
"""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cosmos_lib import (CHROME, CYAN, EBLUE, GOLD, INDIGO, LAV, MAGENTA, MICHROMA, ORANGE,
                        PERI, ROOT, SIGNATURE, SPACE_B, blur_filter, n, radial_grad, star4,
                        text_path, write_svg)

ID = "g07-dark"
OUT = ROOT / "graphics" / f"{ID}.svg"
rnd = random.Random(707)

W, H = 1200, 1500
CX, CY = 600, 630          # galaxy centre on the poster
R = 600                    # disk radius in the galaxy plane
Q = 0.64                   # inclination squash
PA = math.radians(-24)     # position angle
B = 0.33                   # log-spiral pitch (tan of pitch angle)
R0 = 0.085                 # arm start radius (fraction of R)
T = math.log(1.0 / R0) / B  # angular length of an arm (~1.2 turns)
TH0 = 0.2
LANE = 0.38                # dust lane phase offset (inner edge of the arms)
PLANET = (872, 1078, 172)  # x, y, r

GOLD_L = "#FFD98A"
BLUE_L = "#8FA8FF"
WHITE_W = "#FFF4DE"


def proj(x, y, q=Q):
    """galaxy-plane (units of R) -> poster coords"""
    y *= q
    c, s = math.cos(PA), math.sin(PA)
    return CX + R * (x * c - y * s), CY + R * (x * s + y * c)


def arm_point(k, s, extra_phase=0.0):
    t = s * T
    r = R0 * math.exp(B * t)
    phi = TH0 + k * math.pi + t + extra_phase
    return r, phi


def lane_kill(r, phi):
    """probability of removing a particle that sits in a dust lane"""
    if r < 0.07 or r > 0.98:
        return 0.0
    psi = (phi - math.log(r / R0) / B - TH0) % math.pi
    best = 0.0
    for lane, w, k in ((LANE, 0.10, 0.92), (LANE + 1.55, 0.08, 0.45)):
        d = min(abs(psi - lane), math.pi - abs(psi - lane))
        best = max(best, k * math.exp(-(d / w) ** 2))
    return best * min(1.0, (1.02 - r) * 2.5)


def pick(weights):
    tot = sum(w for _, w in weights)
    u = rnd.random() * tot
    for c, w in weights:
        u -= w
        if u <= 0:
            return c
    return weights[-1][0]


particles = []   # (x, y, r, color, opacity)


def add(x, y, rad, col, op):
    if x < 8 or x > W - 8 or y < 8 or y > 1370:
        return
    px, py, pr = PLANET
    if (x - px) ** 2 + (y - py) ** 2 < (pr + rad + 1) ** 2:
        return
    particles.append((x, y, rad, col, op))


def psize(big=0.02):
    if rnd.random() < big:
        return rnd.uniform(2.5, 3.6)
    return min(1.3 + rnd.expovariate(1 / 0.38), 2.5)


# ----------------------------------------------------------------- bulge / core
for i in range(1200):
    sig = 0.04 if i < 650 else 0.105
    x, y = rnd.gauss(0, sig), rnd.gauss(0, sig)
    r = math.hypot(x, y)
    if r > 0.07 and rnd.random() < lane_kill(r, math.atan2(y, x)) * 0.7:
        continue
    px, py = proj(x, y, q=0.84)
    col = pick([(WHITE_W, 4), (GOLD_L, 5), (GOLD, 4), (CHROME, 1.5), (ORANGE, 0.35 if r > 0.07 else 0)])
    add(px, py, psize(0.015), col, rnd.uniform(0.55, 1.0))

# a short bar through the core
for i in range(220):
    t = rnd.uniform(-1, 1)
    x, y = t * 0.14, rnd.gauss(0, 0.016)
    a = TH0 + 0.5
    xr, yr = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    px, py = proj(xr, yr)
    add(px, py, psize(0), pick([(GOLD_L, 3), (GOLD, 2), (WHITE_W, 2)]), rnd.uniform(0.5, 0.95))

# ----------------------------------------------------------------- spiral arms
knots = []
for k in range(2):
    for i in range(2450):
        s = rnd.random() ** 0.8
        r, phi = arm_point(k, s)
        sig = 0.012 + 0.04 * s
        x = r * math.cos(phi) + rnd.gauss(0, sig)
        y = r * math.sin(phi) + rnd.gauss(0, sig)
        rr, pp = math.hypot(x, y), math.atan2(y, x)
        if rnd.random() < lane_kill(rr, pp):
            continue
        g = max(0.0, 0.6 - 0.75 * s)
        col = pick([(GOLD, 2.4 * g + 0.75), (GOLD_L, 1.4 * g + 0.35), (CHROME, 1.5), (BLUE_L, 1.4),
                    (EBLUE, 1.2 + s), (PERI, 0.7 + 0.5 * s), (CYAN, 0.22), (LAV, 0.4), (ORANGE, 0.07)])
        px, py = proj(x, y)
        fade = 1.0 if s < 0.78 else max(0.25, 1 - (s - 0.78) * 3.2)
        add(px, py, psize(0.03), col, rnd.uniform(0.5, 1.0) * fade)
    for j in range(15):
        s = rnd.uniform(0.25, 0.92)
        r, phi = arm_point(k, s, rnd.gauss(0, 0.04))
        knots.append((r * math.cos(phi), r * math.sin(phi), s))

# feathery secondary arms (outer half)
for k in range(2):
    for i in range(360):
        s = rnd.uniform(0.45, 1.0)
        r, phi = arm_point(k, s, math.pi / 2 + 0.35)
        r *= 0.96
        sig = 0.026 + 0.035 * s
        x = r * math.cos(phi) + rnd.gauss(0, sig)
        y = r * math.sin(phi) + rnd.gauss(0, sig)
        if math.hypot(x, y) > 1.04:
            continue
        col = pick([(EBLUE, 3), (PERI, 2), (BLUE_L, 2), (CHROME, 1), (GOLD, 0.5)])
        px, py = proj(x, y)
        add(px, py, psize(0.01), col, rnd.uniform(0.3, 0.7))

# knots: tight clusters, some glowing pink-orange (signal orange accents)
knot_glows = []
for (kx, ky, s) in knots:
    hot = rnd.random() < 0.36
    for _ in range(rnd.randint(16, 34)):
        x = kx + rnd.gauss(0, 0.010)
        y = ky + rnd.gauss(0, 0.010)
        if hot:
            col = pick([(ORANGE, 3), ("#FF7A4D", 2), (MAGENTA, 0.7), (CHROME, 1.5), (GOLD_L, 1)])
        else:
            col = pick([(CHROME, 3), (BLUE_L, 2), (CYAN, 0.8), (EBLUE, 1)])
        px, py = proj(x, y)
        add(px, py, psize(0.05), col, rnd.uniform(0.65, 1.0))
    px, py = proj(kx, ky)
    knot_glows.append((px, py, hot, s))

# ----------------------------------------------------------------- diffuse disk
for i in range(620):
    r = min(rnd.expovariate(1 / 0.24) + 0.06, 1.1)
    phi = rnd.uniform(0, 2 * math.pi)
    if rnd.random() < lane_kill(r, phi) * 0.85:
        continue
    col = pick([(BLUE_L, 2), (EBLUE, 2), (LAV, 1), (GOLD, 1.0 if r < 0.4 else 0.3), (CHROME, 1)])
    px, py = proj(r * math.cos(phi), r * math.sin(phi))
    add(px, py, psize(0), col, rnd.uniform(0.25, 0.6))

# ----------------------------------------------------------------- a distant edge-on galaxy (depth)
DG = (236, 1010, 92, math.radians(-30))
for i in range(330):
    u = rnd.gauss(0, 0.42)
    v = rnd.gauss(0, 0.06) * (1 - min(abs(u), 1) * 0.6)
    if abs(u) > 1.1:
        continue
    x0, y0 = u * DG[2], v * DG[2]
    x = DG[0] + x0 * math.cos(DG[3]) - y0 * math.sin(DG[3])
    y = DG[1] + x0 * math.sin(DG[3]) + y0 * math.cos(DG[3])
    col = pick([(GOLD_L, 3 - 2 * abs(u)), (CHROME, 1.5), (BLUE_L, 1 + abs(u)), (EBLUE, 0.8 + abs(u))])
    add(x, y, min(1.3 + rnd.expovariate(1 / 0.25), 2.2), col, rnd.uniform(0.45, 0.95) * (1 - 0.5 * min(abs(u), 1)))

# ----------------------------------------------------------------- field stars
for i in range(300):
    x, y = rnd.uniform(14, W - 14), rnd.uniform(14, 1350)
    col = pick([(CHROME, 4), (LAV, 2), (BLUE_L, 2), (GOLD_L, 1.2), (CYAN, 0.4)])
    add(x, y, psize(0.04), col, rnd.uniform(0.3, 0.9))

# ----------------------------------------------------------------- defs
px, py, pr = PLANET
la = math.atan2(CY - py, CX - px)
ux, uy = math.cos(la), math.sin(la)

defs = [
    blur_filter(f"{ID}-blur-arm", 13, units_box=(-200, -200, 1600, 1900)),
    blur_filter(f"{ID}-blur-lane", 7, units_box=(-200, -200, 1600, 1900)),
    blur_filter(f"{ID}-blur-rim", 4.5, pad=0.5),
    blur_filter(f"{ID}-blur-atm", 13, pad=0.8),
    radial_grad(f"{ID}-core", [(0, "#FFFFFF", 1), (0.1, "#FFF6E2", 0.95), (0.28, GOLD_L, 0.62),
                               (0.55, GOLD, 0.24), (0.8, ORANGE, 0.06), (1, ORANGE, 0)]),
    radial_grad(f"{ID}-halo", [(0, GOLD, 0.32), (0.3, "#D9953F", 0.16), (0.65, PERI, 0.07), (1, INDIGO, 0)]),
    radial_grad(f"{ID}-disk", [(0, PERI, 0.16), (0.5, EBLUE, 0.08), (0.85, INDIGO, 0.05), (1, INDIGO, 0)]),
    radial_grad(f"{ID}-kn-hot", [(0, "#FF9A6C", 0.6), (0.45, ORANGE, 0.2), (1, MAGENTA, 0)]),
    radial_grad(f"{ID}-kn-cool", [(0, "#E4EBFF", 0.5), (0.45, BLUE_L, 0.17), (1, EBLUE, 0)]),
    radial_grad(f"{ID}-fl-white", [(0, "#FFFFFF", 0.7), (0.22, "#E8ECFF", 0.26), (1, PERI, 0)]),
    radial_grad(f"{ID}-fl-gold", [(0, "#FFF6E0", 0.7), (0.22, GOLD_L, 0.28), (1, GOLD, 0)]),
    radial_grad(f"{ID}-fl-blue", [(0, "#FFFFFF", 0.7), (0.22, BLUE_L, 0.3), (1, EBLUE, 0)]),
    # rays fade towards their tips (bounding box of a star4 path is centred on the star)
    radial_grad(f"{ID}-ray", [(0, "#FFFFFF", 1), (0.25, "#FFFFFF", 0.97), (0.62, "#E9EEFF", 0.6), (1, "#DDE6FF", 0)]),
    radial_grad(f"{ID}-ray-warm", [(0, "#FFFFFF", 1), (0.2, "#FFF6E2", 0.95), (0.6, GOLD_L, 0.55), (1, GOLD, 0)]),
    radial_grad(f"{ID}-planet", [(0, "#232675", 0.9), (0.4, "#17174A", 0.7), (0.8, "#111130", 0.25), (1, "#111130", 0)],
                cx=n(px + ux * pr * 0.8), cy=n(py + uy * pr * 0.8), r=n(pr * 1.6),
                extra=' gradientUnits="userSpaceOnUse"'),
    f'<clipPath id="{ID}-pclip"><circle cx="{n(px)}" cy="{n(py)}" r="{n(pr)}"/></clipPath>',
    f'<mask id="{ID}-pmask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
    f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>'
    f'<circle cx="{n(px)}" cy="{n(py)}" r="{n(pr + 0.5)}" fill="#000000"/></mask>',
]

# dust-lane mask for the glow layers: black blurred spiral strokes
lane_segs = []
for k in range(2):
    pts = []
    for i in range(140):
        s = 0.02 + i / 139 * 0.86
        r, phi = arm_point(k, s, LANE)
        r *= 1.0
        pts.append((proj(r * math.cos(phi), r * math.sin(phi)), s))
    for (a, sa), (b, sb) in zip(pts, pts[1:]):
        wdt = 5 + 13 * sa
        op = min(1.0, max(0.0, (sa - 0.06) * 3.0)) * (1 - max(0, sa - 0.6) * 2.2) * 0.75
        lane_segs.append(f'<path d="M{n(a[0])} {n(a[1])}L{n(b[0])} {n(b[1])}" stroke="#000000" '
                         f'stroke-width="{n(wdt)}" stroke-opacity="{n(max(op, 0) * 0.9, 2)}" stroke-linecap="round"/>')
defs.append(f'<mask id="{ID}-dust" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>'
            f'<g fill="none" filter="url(#{ID}-blur-lane)">' + "".join(lane_segs) + "</g></mask>")

body = []
deg = math.degrees(PA)

# ---- diffuse glow layers (masked by planet and dust lanes)
body.append(f'<g id="{ID}-glow" mask="url(#{ID}-pmask)"><g mask="url(#{ID}-dust)">')
body.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{n(R * 1.1)}" ry="{n(R * 1.1 * Q)}" fill="url(#{ID}-disk)" '
            f'transform="rotate({n(deg)} {CX} {CY})"/>')
blobs = []
for k in range(2):
    for i in range(520):
        s = rnd.random() ** 0.85
        r, phi = arm_point(k, s)
        sig = 0.01 + 0.03 * s
        x = r * math.cos(phi) + rnd.gauss(0, sig)
        y = r * math.sin(phi) + rnd.gauss(0, sig)
        g = max(0.0, 0.62 - s)
        col = pick([(EBLUE, 2 + s), (PERI, 2), (BLUE_L, 1.3), (LAV, 0.6), (GOLD, 2.6 * g), ("#B57BFF", 0.3)])
        bx, by = proj(x, y)
        blobs.append(f'<circle cx="{n(bx)}" cy="{n(by)}" r="{n(rnd.uniform(10, 20) * (0.75 + 0.6 * s))}" fill="{col}" '
                     f'fill-opacity="{n(rnd.uniform(0.06, 0.12) * (1.15 - 0.5 * max(0, s - 0.7)), 3)}"/>')
body.append(f'<g filter="url(#{ID}-blur-arm)">' + "".join(blobs) + "</g>")
for (kx, ky, hot, s) in knot_glows:
    body.append(f'<circle cx="{n(kx)}" cy="{n(ky)}" r="{n(rnd.uniform(16, 28))}" '
                f'fill="url(#{ID}-kn-{"hot" if hot else "cool"})"/>')
body.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{n(R * 0.62)}" ry="{n(R * 0.62 * 0.78)}" fill="url(#{ID}-halo)" '
            f'transform="rotate({n(deg)} {CX} {CY})"/>')
body.append(f'<ellipse cx="{DG[0]}" cy="{DG[1]}" rx="{n(DG[2] * 0.9)}" ry="{n(DG[2] * 0.16)}" fill="url(#{ID}-halo)" '
            f'transform="rotate({n(math.degrees(DG[3]))} {DG[0]} {DG[1]})"/>')
body.append(f'<circle cx="{DG[0]}" cy="{DG[1]}" r="16" fill="url(#{ID}-fl-gold)"/>')
body.append("</g></g>")

# ---- particles, grouped by colour to keep the file small
groups = {}
for (x, y, rad, col, op) in particles:
    groups.setdefault(col, []).append(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rad, 2)}" opacity="{n(op, 2)}"/>')
body.append(f'<g id="{ID}-particles">')
for col, items in groups.items():
    body.append(f'<g fill="{col}">' + "".join(items) + "</g>")
body.append("</g>")

# ---- core glow on top of the particles (dust lanes cut through it)
body.append(f'<g mask="url(#{ID}-dust)"><ellipse cx="{CX}" cy="{CY}" rx="{n(R * 0.27)}" ry="{n(R * 0.27 * 0.82)}" '
            f'fill="url(#{ID}-core)" transform="rotate({n(deg)} {CX} {CY})"/></g>')
body.append(f'<circle cx="{CX}" cy="{CY}" r="5" fill="#FFFFFF"/>')


def flare(x, y, rr, kind="white", rot=0.0, halo=0.5, warm=False):
    ray = f"url(#{ID}-ray-warm)" if warm else f"url(#{ID}-ray)"
    return (f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(rr * halo)}" fill="url(#{ID}-fl-{kind})"/>'
            f'<path d="{star4(x, y, rr, 0.075, rot)}" fill="{ray}"/>'
            f'<path d="{star4(x, y, rr * 0.38, 0.12, rot + math.pi / 4)}" fill="{ray}" fill-opacity="0.7"/>'
            f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(max(1.6, rr * 0.06))}" fill="#FFFFFF"/>')


# ---- glitter: small flares on bright arm particles
bright = [p for p in particles if p[2] > 2.5 and p[4] > 0.75
          and 0.12 < math.hypot(p[0] - CX, (p[1] - CY) / 0.75) / R < 0.95]
rnd.shuffle(bright)
body.append(f'<g id="{ID}-glitter">')
for (x, y, rad, col, op) in bright[:60]:
    kind = "gold" if col in (GOLD, GOLD_L, WHITE_W) else "blue"
    body.append(flare(x, y, rnd.uniform(8, 16), kind, warm=(kind == "gold")))
body.append("</g>")

# ---- hero flares (composed by hand)
HERO = [(190, 236, 58, "white"), (1036, 196, 38, "blue"), (96, 880, 30, "gold"), (1100, 640, 22, "white"),
        (392, 1238, 27, "blue"), (760, 104, 19, "gold"), (284, 520, 14, "white"), (650, 1290, 15, "gold"),
        (1132, 1000, 13, "blue"), (60, 470, 12, "white")]
body.append(f'<g id="{ID}-flares">')
for (x, y, rr, kind) in HERO:
    body.append(flare(x, y, rr, kind, halo=0.55, warm=(kind == "gold")))
# nucleus diffraction spikes
body.append(f'<path d="{star4(CX, CY, 165, 0.03)}" fill="url(#{ID}-ray-warm)" fill-opacity="0.8"/>')
body.append("</g>")

# ---- dark planet with a cyan rim light
body.append(f'<g id="{ID}-planet">')
body.append(f'<circle cx="{n(px)}" cy="{n(py)}" r="{n(pr)}" fill="url(#{ID}-planet)"/>')
bands = []
for i in range(6):
    yy = py - pr + (i + 0.6) * (2 * pr / 6) + rnd.uniform(-8, 8)
    bands.append(f'<ellipse cx="{n(px)}" cy="{n(yy)}" rx="{n(pr * 1.15)}" ry="{n(rnd.uniform(4, 9))}" '
                 f'fill="{PERI}" fill-opacity="{n(rnd.uniform(0.02, 0.045), 3)}" '
                 f'transform="rotate(-16 {n(px)} {n(py)})"/>')
body.append(f'<g clip-path="url(#{ID}-pclip)">' + "".join(bands) + "</g>")


def crescent(off_, rad):
    """lit crescent: circle(rad) at the planet centre minus the same circle shifted
    `off_` away from the light, built from the two intersecting arcs."""
    c = (px, py)
    ci = (px - ux * off_, py - uy * off_)
    m = (px - ux * off_ / 2, py - uy * off_ / 2)
    h = math.sqrt(rad * rad - (off_ / 2) ** 2)
    vx, vy = -uy, ux
    p1 = (m[0] + vx * h, m[1] + vy * h)
    p2 = (m[0] - vx * h, m[1] - vy * h)

    def sweep(cen, a, b, via):
        ang = lambda p: math.atan2(p[1] - cen[1], p[0] - cen[0])
        a0, a1, av = ang(a), ang(b), ang(via)
        return 1 if (av - a0) % (2 * math.pi) < (a1 - a0) % (2 * math.pi) else 0

    s1 = sweep(c, p1, p2, (c[0] + ux * rad, c[1] + uy * rad))
    s2 = sweep(ci, p2, p1, (ci[0] + ux * rad, ci[1] + uy * rad))
    return (f'M{n(p1[0], 2)} {n(p1[1], 2)}A{n(rad)} {n(rad)} 0 1 {s1} {n(p2[0], 2)} {n(p2[1], 2)}'
            f'A{n(rad)} {n(rad)} 0 0 {s2} {n(p1[0], 2)} {n(p1[1], 2)}Z')


body.append(f'<path d="{crescent(40, pr + 8)}" fill="{CYAN}" fill-opacity="0.3" filter="url(#{ID}-blur-atm)"/>')
body.append(f'<path d="{crescent(14, pr + 1)}" fill="{CYAN}" fill-opacity="0.8" filter="url(#{ID}-blur-rim)"/>')
body.append(f'<path d="{crescent(6.5, pr)}" fill="#C8FCFF"/>')
body.append("</g>")

# ---- fine print
t = text_path(MICHROMA, "CÂMP ADÂNC · 13,8 MILIARDE DE ANI-LUMINĂ", 27, W / 2, 1446, tracking=120)
body.append(f'<path id="{ID}-caption" d="{t["d"]}" fill="{LAV}"/>')
body.append(f'<rect x="{n(W / 2 - 24)}" y="1392" width="48" height="3" fill="{GOLD}"/>')
sig = text_path(SPACE_B, SIGNATURE, 19, W / 2, 1490, tracking=260)
body.append(f'<path id="{ID}-signature" d="{sig["d"]}" fill="{PERI}" fill-opacity="0.85"/>')

size = write_svg(OUT, body, "".join(defs))
print(OUT, len(particles), "particles", size // 1024, "KB")
