#!/usr/bin/env python3
"""g02-dark — NOT FROM HERE.
A stylized Earth (ocean blues, invented continents, cloud swirls) whose left side is
smeared into horizontal pixel streaks; an arcing, 3D-extruded "NOT FROM HERE" above.
Poster 1200x1500, transparent.
Run: python3 graphics/src/g02-dark.py
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_lib import (MICH, MONO_B, ROOT, SIGNATURE, SVG, UNB, extrude, f1, mix, sparkles,  # noqa: E402
                      star4, warped)

ID = "g02-dark"
OUT = os.path.join(ROOT, "graphics", ID + ".svg")
W, H = 1200, 1500
rnd = random.Random(202)
svg = SVG(ID, W, H)

EX, EY, R = 740, 1000, 315
LON0, LAT0 = math.radians(-25), math.radians(18)
LIGHT = np.array([-0.55, -0.5, 0.67])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def project(lon, lat):
    """orthographic projection -> (x, y, visible)"""
    cl = math.cos(lat)
    x = cl * math.sin(lon - LON0)
    y = math.cos(LAT0) * math.sin(lat) - math.sin(LAT0) * cl * math.cos(lon - LON0)
    z = math.sin(LAT0) * math.sin(lat) + math.cos(LAT0) * cl * math.cos(lon - LON0)
    if z < 0:
        k = 1 / math.hypot(x, y)
        x, y = x * k, y * k
    return EX + R * x, EY - R * y, z >= 0


# ------------------------------------------------------------------ geometry (lon/lat)
def blob(lon_c, lat_c, rad, seed, n=90, rough=0.28):
    rr = random.Random(seed)
    ph = [rr.uniform(0, 6.28) for _ in range(5)]
    am = [rough * rr.uniform(0.4, 1) / (k + 1) for k in range(5)]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        f = 1 + sum(am[k] * math.sin((k + 2) * a + ph[k]) for k in range(5))
        lat = lat_c + math.radians(rad) * f * math.sin(a)
        lon = lon_c + math.radians(rad) * f * math.cos(a) / max(math.cos(lat_c), 0.3)
        pts.append((lon, lat))
    return pts


D = math.radians
CONT = [  # lon, lat, radius(deg), seed
    (D(-60), D(44), 17, 1), (D(-42), D(18), 11, 2), (D(-66), D(-6), 8, 3),
    (D(6), D(38), 14, 4), (D(24), D(4), 19, 5), (D(16), D(-26), 11, 6),
    (D(-14), D(64), 9, 7), (D(50), D(46), 14, 8), (D(-92), D(20), 10, 9),
]
DESERT = [(D(22), D(12), 9, 11), (D(-52), D(38), 6, 12), (D(48), D(40), 7, 13)]
ISLES = [(D(rnd.uniform(-110, 60)), D(rnd.uniform(-55, 65)), rnd.uniform(1.6, 3.6), 30 + i) for i in range(26)]

land_polys = [[project(lo, la) for lo, la in blob(*c)] for c in CONT + ISLES]
desert_polys = [[project(lo, la) for lo, la in blob(*c, rough=0.4)] for c in DESERT]


def spiral_cloud(lon_c, lat_c, size, turns, seed):
    rr = random.Random(seed)
    arms = []
    for arm in range(rr.choice((2, 3))):
        pts = []
        for i in range(60):
            t = i / 59
            ang = arm * 2 * math.pi / 3 + t * turns * 2 * math.pi
            rad = math.radians(size) * (0.12 + t)
            lat = lat_c + rad * math.sin(ang)
            lon = lon_c + rad * math.cos(ang) / max(math.cos(lat_c), 0.3)
            pts.append((lon, lat))
        arms.append(pts)
    return arms


cloud_lines = []   # (pts, width, opacity)
for (lo, la, sz, tu, sd) in [(D(-30), D(30), 13, 0.75, 1), (D(8), D(-14), 10, 0.7, 2), (D(32), D(54), 9, 0.8, 4)]:
    for arm in spiral_cloud(lo, la, sz, tu, sd):
        cloud_lines.append(([project(a, b) for a, b in arm], rnd.uniform(7, 12), 0.7))
for k in range(40):  # long band streaks along latitude
    la = D(rnd.uniform(-60, 65))
    lo = D(rnd.uniform(-120, 40))
    span = D(rnd.uniform(14, 45))
    pts = []
    for i in range(30):
        t = i / 29
        pts.append(project(lo + span * t, la + D(3) * math.sin(t * 3 + k)))
    cloud_lines.append((pts, rnd.uniform(4, 13), rnd.uniform(0.35, 0.75)))

OCEAN_HI, OCEAN_MID, OCEAN_LO = "#56B7FF", "#2D6CF0", "#14257E"
LAND_HI, LAND_LO = "#4FD39A", "#1C7A62"
SAND = "#D9B26E"

# ------------------------------------------------------------------ raster twin (for colour sampling)
SC = 1
img = Image.new("RGB", (W, H), (0, 0, 0))
yy, xx = np.mgrid[0:H, 0:W].astype(float)
nx, ny = (xx - EX) / R, -(yy - EY) / R
rr2 = nx * nx + ny * ny
inside = rr2 <= 1
nz = np.sqrt(np.clip(1 - rr2, 0, 1))
lam = np.clip(nx * LIGHT[0] * -1 + ny * -LIGHT[1] + nz * LIGHT[2], 0, 1)   # lambert (light from upper-left)
lam = np.clip(-nx * 0.55 + ny * 0.5 + nz * 0.67, 0, 1)


def hx(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)


ocean = (hx(OCEAN_LO)[None, None] * (1 - lam[..., None]) + hx(OCEAN_HI)[None, None] * lam[..., None])
mask_land = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask_land)
for p in land_polys:
    md.polygon([(x, y) for x, y, _ in p], fill=255)
mask_sand = Image.new("L", (W, H), 0)
ms = ImageDraw.Draw(mask_sand)
for p in desert_polys:
    ms.polygon([(x, y) for x, y, _ in p], fill=255)
mask_cloud = Image.new("L", (W, H), 0)
mc = ImageDraw.Draw(mask_cloud)
for pts, w, op in cloud_lines:
    mc.line([(x, y) for x, y, _ in pts], fill=int(255 * op), width=int(w))
L = np.array(mask_land, float)[..., None] / 255
S = np.array(mask_sand, float)[..., None] / 255 * L
Cm = np.array(mask_cloud, float)[..., None] / 255
land = hx(LAND_LO)[None, None] * (1 - lam[..., None]) + hx(LAND_HI)[None, None] * lam[..., None]
sand = hx(SAND)[None, None] * (0.45 + 0.55 * lam[..., None])
col = ocean * (1 - L) + land * L
col = col * (1 - S) + sand * S
col = col * (1 - Cm) + np.array([235, 240, 255.0])[None, None] * (0.5 + 0.5 * lam[..., None]) * Cm
RAST = np.clip(col, 0, 255)


def sample(x, y):
    x = int(min(max(x, 0), W - 1))
    y = int(min(max(y, 0), H - 1))
    c = RAST[y, x]
    if c.sum() < 260:
        c = c * 0.4 + hx(OCEAN_MID) * 0.6
    return "#%02X%02X%02X" % tuple(int(v) for v in c)


# ------------------------------------------------------------------ defs
svg.d(f'<radialGradient id="{svg.id("ocean")}" cx="{EX - R * 0.42}" cy="{EY - R * 0.4}" r="{R * 1.5}" gradientUnits="userSpaceOnUse">'
      f'<stop offset="0" stop-color="{OCEAN_HI}"/><stop offset="0.45" stop-color="{OCEAN_MID}"/>'
      f'<stop offset="1" stop-color="{OCEAN_LO}"/></radialGradient>')
svg.d(f'<radialGradient id="{svg.id("night")}" cx="{EX - R * 0.45}" cy="{EY - R * 0.42}" r="{R * 1.7}" gradientUnits="userSpaceOnUse">'
      '<stop offset="0.4" stop-color="#07070D" stop-opacity="0"/><stop offset="0.68" stop-color="#0A0A2A" stop-opacity="0.45"/>'
      '<stop offset="0.86" stop-color="#07070D" stop-opacity="0.82"/><stop offset="1" stop-color="#07070D" stop-opacity="0.9"/></radialGradient>')
svg.d(f'<radialGradient id="{svg.id("spec")}" cx="{EX - R * 0.4}" cy="{EY - R * 0.42}" r="{R * 0.7}" gradientUnits="userSpaceOnUse">'
      '<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.35"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>')
svg.d(f'<radialGradient id="{svg.id("atmo")}" cx="{EX}" cy="{EY}" r="{R * 1.16}" gradientUnits="userSpaceOnUse">'
      '<stop offset="0.84" stop-color="#5FF3FF" stop-opacity="0"/><stop offset="0.87" stop-color="#5FF3FF" stop-opacity="0.55"/>'
      '<stop offset="0.93" stop-color="#3D5AFE" stop-opacity="0.18"/><stop offset="1" stop-color="#3D5AFE" stop-opacity="0"/></radialGradient>')
svg.d(f'<filter id="{svg.id("cloudblur")}" x="-0.1" y="-0.1" width="1.2" height="1.2" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="1.6"/></filter>')
svg.d(f'<filter id="{svg.id("soft")}" x="-0.5" y="-0.5" width="2" height="2" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="3"/></filter>')
svg.d(f'<filter id="{svg.id("bloom")}" x="-0.3" y="-0.6" width="1.6" height="2.2" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="14"/></filter>')

# ------------------------------------------------------------------ pixel cut of the planet
BAND = 8
rows = []
cut = {}
phase = rnd.uniform(0, 6)
for y in range(EY - R, EY + R, BAND):
    yc = y + BAND / 2
    half = math.sqrt(max(R * R - (yc - EY) ** 2, 0))
    xl = EX - half
    # smooth clustering of long/short rows
    s = 0.5 + 0.5 * math.sin(yc / 37 + phase) * math.cos(yc / 91 + 1.3)
    depth = (R * 0.55) * (0.15 + 0.85 * s) * rnd.uniform(0.55, 1.0) if half > 6 else 0
    if rnd.random() < 0.18:
        depth = 0
    cut[y] = xl + depth
    rows.append(f'M{f1(cut[y] if depth else xl - 2)} {y}H{EX + R + 4}V{y + BAND}H{f1(cut[y] if depth else xl - 2)}Z')
svg.d(f'<clipPath id="{svg.id("cut")}"><path d="{"".join(rows)}"/></clipPath>')
svg.d(f'<clipPath id="{svg.id("disc")}"><circle cx="{EX}" cy="{EY}" r="{R}"/></clipPath>')

# ------------------------------------------------------------------ earth (vector)
earth = [f'<circle cx="{EX}" cy="{EY}" r="{R}" fill="url(#{svg.id("ocean")})"/>']
lp = "".join("M" + "L".join(f"{f1(x)} {f1(y)}" for x, y, _ in p) + "Z" for p in land_polys)
earth.append(f'<path d="{lp}" fill="{LAND_HI}"/>')
earth.append(f'<path d="{lp}" fill="{LAND_LO}" opacity="0.55" transform="translate(5 6)" clip-path="url(#{svg.id("disc")})"/>')
dp = "".join("M" + "L".join(f"{f1(x)} {f1(y)}" for x, y, _ in p) + "Z" for p in desert_polys)
svg.d(f'<clipPath id="{svg.id("landclip")}"><path d="{lp}"/></clipPath>')
earth.append(f'<g clip-path="url(#{svg.id("landclip")})"><path d="{dp}" fill="{SAND}" opacity="0.9"/></g>')
cl = "".join(f'<path d="M{"L".join(f"{f1(x)} {f1(y)}" for x, y, _ in pts)}" stroke-width="{f1(w)}" opacity="{f1(op, 2)}"/>'
             for pts, w, op in cloud_lines)
earth.append(f'<g fill="none" stroke="#EEF2FF" stroke-linecap="round" stroke-linejoin="round" filter="url(#{svg.id("cloudblur")})">{cl}</g>')
earth.append(f'<circle cx="{EX}" cy="{EY}" r="{R}" fill="url(#{svg.id("spec")})"/>')
earth.append(f'<circle cx="{EX}" cy="{EY}" r="{R}" fill="url(#{svg.id("night")})"/>')

svg.add(f'<circle cx="{EX}" cy="{EY}" r="{R * 1.16}" fill="url(#{svg.id("atmo")})"/>')
svg.add(f'<g clip-path="url(#{svg.id("cut")})"><g clip-path="url(#{svg.id("disc")})">{"".join(earth)}</g></g>')
# lit rim
svg.add(f'<path d="M{f1(EX + R * math.cos(math.radians(160)))} {f1(EY + R * math.sin(math.radians(160)))}" fill="none"/>')
a0, a1 = math.radians(190), math.radians(320)
svg.add(f'<path d="M{f1(EX + (R + 2) * math.cos(a0))} {f1(EY + (R + 2) * math.sin(a0))}A{R + 2} {R + 2} 0 0 1 '
        f'{f1(EX + (R + 2) * math.cos(a1))} {f1(EY + (R + 2) * math.sin(a1))}" fill="none" stroke="#9FF8FF" stroke-width="4" '
        f'stroke-linecap="round" opacity="0.85" clip-path="url(#{svg.id("cut")})"/>')

# ------------------------------------------------------------------ pixel streaks
blocks = []
for y in range(EY - R, EY + R, BAND):
    yc = y + BAND / 2
    half = math.sqrt(max(R * R - (yc - EY) ** 2, 0))
    if half < 6:
        continue
    x = cut[y]
    xl = EX - half
    depth = x - xl
    base = sample(x + 3, yc)
    length = (60 + depth * 2.4) * rnd.uniform(0.6, 1.4) + (rnd.random() < 0.15) * rnd.uniform(150, 360)
    xs = x
    end = max(30, x - length)
    while xs > end:
        bw = rnd.choice((8, 8, 16, 16, 24, 32, 48))
        u = (x - xs) / max(length, 1)
        if rnd.random() < 0.12 + 0.35 * u:
            xs -= bw * rnd.uniform(0.5, 2)
            continue
        src = sample(x + rnd.uniform(1, 30), yc) if rnd.random() < 0.45 else base
        if rnd.random() < 0.06:
            src = rnd.choice(("#5FF3FF", "#FF3DA8", "#F2F4FF"))
        op = max(0.15, 1 - u ** 0.9)
        hh = BAND if rnd.random() > 0.2 else BAND / 2
        blocks.append(f'<rect x="{f1(xs - bw)}" y="{y}" width="{bw}" height="{f1(hh)}" fill="{src}" opacity="{f1(op, 2)}"/>')
        xs -= bw
svg.add('<g>' + "".join(blocks) + '</g>')
# chromatic split lines on a few rows
for y in rnd.sample(range(EY - R + 40, EY + R - 40, BAND), 7):
    x = cut[y]
    ln = rnd.uniform(120, 420)
    c = rnd.choice(("#5FF3FF", "#FF3DA8"))
    svg.add(f'<rect x="{f1(x - ln)}" y="{y + 2}" width="{f1(ln)}" height="3" fill="{c}" opacity="0.75" style="mix-blend-mode:screen"/>')

# ------------------------------------------------------------------ headline
d, bb = warped(UNB, "NOT FROM HERE", 92, 600, 470, sy=1.55, warps=["arc:0.75", "bulge:0.28", "wave:0.05:1:0.25"], steps=8)
x0, y0, x1, y1 = bb
pid, stack = extrude(svg, "word", d, depth=24, dx=0.0, dy=2.1, back="#0B0A33", front="#3530C0")
svg.d(f'<linearGradient id="{svg.id("face")}" x1="0" y1="{f1(y0)}" x2="0" y2="{f1(y1)}" gradientUnits="userSpaceOnUse">'
      '<stop offset="0" stop-color="#FFFFFF"/><stop offset="0.35" stop-color="#C9C3FF"/>'
      '<stop offset="0.75" stop-color="#8C8CFF"/><stop offset="1" stop-color="#6C6CFF"/></linearGradient>')
svg.add(f'<use href="#{pid}" y="16" fill="#4F5BFF" opacity="0.5" filter="url(#{svg.id("bloom")})"/>')
svg.add(stack)
svg.add(f'<use href="#{pid}" x="-6" fill="#5FF3FF" opacity="0.6" style="mix-blend-mode:screen"/>')
svg.add(f'<use href="#{pid}" x="6" y="2" fill="#FF3DA8" opacity="0.55" style="mix-blend-mode:screen"/>')
svg.add(f'<use href="#{pid}" x="-2" y="-3" fill="#F2F4FF"/>')
svg.add(f'<use href="#{pid}" fill="url(#{svg.id("face")})"/>')

# ------------------------------------------------------------------ sparkles + small type
def avoid(px, py):
    return (x0 - 20 < px < x1 + 20 and y0 - 30 < py < y1 + 60) or math.hypot(px - EX, py - EY) < R + 30 or (py > EY - R and px < EX)


svg.add(sparkles(rnd, 40, (40, 120, 1160, 1380), rmin=6, rmax=24, color="#F2F4FF", avoid=avoid, glow_id=svg.id("soft")))
for px, py, r in ((1080, 640, 32), (210, 590, 22)):
    svg.add(f'<circle cx="{px}" cy="{py}" r="{r * 0.5}" fill="#C9C3FF" opacity="0.6" filter="url(#{svg.id("soft")})"/>')
    svg.add(f'<path d="{star4(px, py, r, waist=0.08)}" fill="#F2F4FF"/>')

svg.add(svg.small(MICH, "PLANETA 3 · SECTORUL LOCAL", 16, 60, 92, "#C9C3FF", tracking=240, opacity=0.9))
svg.add(svg.small(MICH, "SEMNAL CORUPT", 16, 1140, 92, "#C9C3FF", anchor="end", tracking=240, opacity=0.9))
svg.add(svg.small(MONO_B, "ERR 0x3A · OBIECT NEIDENTIFICAT ÎN CADRU", 17, 60, 1440, "#C9C3FF", tracking=40, opacity=0.85))
svg.add(svg.small(MICH, SIGNATURE, 14, 1140, 1440, "#C9C3FF", anchor="end", tracking=200, opacity=0.8))

print(OUT, svg.save(OUT))
