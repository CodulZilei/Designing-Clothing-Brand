#!/usr/bin/env python3
"""g18-dark — BULETIN INTERGALACTIC. A fictional, tilted holographic ID card for an
alien: photo box with a grey-alien silhouette, fields, signature squiggle, machine
readable lines and a globe emblem. The card is a deliberate panel (its shape is the print).
Poster 1200x1500.
Run: python3 graphics/src/g18-dark.py
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_lib import (MICH, MONO_B, ROOT, SIGNATURE, SVG, UNB, f1, globe, n_badge, rrect,  # noqa: E402
                      sparkles, star4)

ID = "g18-dark"
OUT = os.path.join(ROOT, "graphics", ID + ".svg")
rnd = random.Random(1818)
svg = SVG(ID, 1200, 1500)
VOID = "#0B0A2A"
IND = "#24228A"
LAV = "#C9C3FF"
WH = "#F2F4FF"

CW, CH = 1000, 640
CX0, CY0 = 100, 420      # card top-left before rotation
ROT = -7

# ------------------------------------------------------------------ defs
svg.d(f'<linearGradient id="{svg.id("holo")}" x1="0" y1="0" x2="{CW}" y2="{CH}" gradientUnits="userSpaceOnUse">'
      '<stop offset="0" stop-color="#7FF6FF"/><stop offset="0.28" stop-color="#C9C3FF"/>'
      '<stop offset="0.5" stop-color="#FFA6DA"/><stop offset="0.72" stop-color="#B3B8FF"/>'
      '<stop offset="1" stop-color="#7FF0FF"/></linearGradient>')
svg.d(f'<linearGradient id="{svg.id("sheen")}" x1="0" y1="0" x2="{CW}" y2="{CH * 0.6}" gradientUnits="userSpaceOnUse">'
      '<stop offset="0.18" stop-color="#FFFFFF" stop-opacity="0"/><stop offset="0.3" stop-color="#FFFFFF" stop-opacity="0.55"/>'
      '<stop offset="0.36" stop-color="#FFFFFF" stop-opacity="0"/><stop offset="0.62" stop-color="#FFFFFF" stop-opacity="0"/>'
      '<stop offset="0.7" stop-color="#FFFFFF" stop-opacity="0.35"/><stop offset="0.76" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>')
svg.d(f'<linearGradient id="{svg.id("photo")}" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0" stop-color="#3D5AFE"/><stop offset="1" stop-color="#1A1866"/></linearGradient>')
svg.d(f'<radialGradient id="{svg.id("head")}" cx="0.4" cy="0.3" r="0.8">'
      '<stop offset="0" stop-color="#D9DCE8"/><stop offset="0.6" stop-color="#A3A8BC"/><stop offset="1" stop-color="#6E7389"/></radialGradient>')
svg.d(f'<filter id="{svg.id("glow")}" x="-0.3" y="-0.3" width="1.6" height="1.6" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="30"/></filter>')
svg.d(f'<filter id="{svg.id("soft")}" x="-0.5" y="-0.5" width="2" height="2" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="3"/></filter>')
svg.d(f'<clipPath id="{svg.id("card")}"><path d="{rrect(0, 0, CW, CH, 40)}"/></clipPath>')
svg.d(f'<clipPath id="{svg.id("photoclip")}"><path d="{rrect(40, 150, 250, 300, 16)}"/></clipPath>')

# ------------------------------------------------------------------ card
c = []
c.append(f'<path d="{rrect(0, 0, CW, CH, 40)}" fill="url(#{svg.id("holo")})"/>')
inner = []
# guilloche
gl = []
for k in range(18):
    pts = []
    for i in range(81):
        x = i / 80 * CW
        y = 60 + k * 33 + 14 * math.sin(x / 61 + k * 0.7) + 8 * math.sin(x / 23 - k)
        pts.append(f"{f1(x)} {f1(y)}")
    gl.append("M" + "L".join(pts))
inner.append(f'<path d="{"".join(gl)}" fill="none" stroke="{IND}" stroke-width="2.6" opacity="0.1"/>')
# rosette (spirograph)
ro = []
rx0, ry0 = 800, 300
for k in range(24):
    a = k * 180 / 24
    ro.append(f'<ellipse cx="{rx0}" cy="{ry0}" rx="150" ry="52" transform="rotate({f1(a)} {rx0} {ry0})"/>')
inner.append(f'<g fill="none" stroke="#FFFFFF" stroke-width="2.6" opacity="0.4">{"".join(ro)}</g>')
inner.append(f'<path d="{rrect(0, 0, CW, CH, 40)}" fill="url(#{svg.id("sheen")})"/>')
c.append(f'<g clip-path="url(#{svg.id("card")})">{"".join(inner)}</g>')
c.append(f'<path d="{rrect(14, 14, CW - 28, CH - 28, 28)}" fill="none" stroke="#FFFFFF" stroke-width="3" opacity="0.7"/>')

# header
d, _, _ = svg.text_d(UNB, "BULETIN INTERGALACTIC", 47, 40, 92)
c.append(f'<path d="{d}" fill="{VOID}"/>')
c.append(svg.small(MICH, "CARTE DE IDENTITATE PROVIZORIE · FEDERAȚIA SISTEMELOR LOCALE", 13, 42, 124, IND, tracking=80))
c.append(globe(915, 72, 42, VOID, sw=3, tilt=-18, lat=3, lon=4, orbit=True))

# photo
c.append(f'<path d="{rrect(40, 150, 250, 300, 16)}" fill="url(#{svg.id("photo")})"/>')
ph = []
hx, hy = 165, 180
ph.append(f'<path d="M{hx - 120} 450C{hx - 115} 395 {hx - 70} 372 {hx - 22} 365L{hx - 16} 330L{hx + 16} 330L{hx + 22} 365'
          f'C{hx + 70} 372 {hx + 115} 395 {hx + 120} 450Z" fill="#7C8198"/>')
ph.append(f'<path d="M{hx} 190C{hx + 70} 190 {hx + 92} 232 {hx + 90} 268C{hx + 86} 310 {hx + 38} 352 {hx} 356'
          f'C{hx - 38} 352 {hx - 86} 310 {hx - 90} 268C{hx - 92} 232 {hx - 70} 190 {hx} 190Z" fill="url(#{svg.id("head")})"/>')
for s in (-1, 1):
    ex = hx + s * 40
    ph.append(f'<path d="M{hx + s * 10} 286C{hx + s * 14} 258 {ex + s * 28} 246 {ex + s * 40} 252C{ex + s * 42} 276 {hx + s * 34} 300 {hx + s * 10} 286Z" fill="#07070D"/>')
    ph.append(f'<circle cx="{ex + s * 12}" cy="262" r="5" fill="#F2F4FF" opacity="0.9"/>')
ph.append(f'<path d="M{hx - 8} 325Q{hx} 329 {hx + 8} 325" fill="none" stroke="#4A4E62" stroke-width="3" stroke-linecap="round"/>')
ph.append("".join(f'<rect x="40" y="{y}" width="250" height="2.6" fill="#07070D" opacity="0.25"/>' for y in range(154, 450, 7)))
c.append(f'<g clip-path="url(#{svg.id("photoclip")})">{"".join(ph)}</g>')
c.append(f'<path d="{rrect(40, 150, 250, 300, 16)}" fill="none" stroke="{VOID}" stroke-width="3"/>')
c.append(svg.small(MONO_B, "FOTO NEVERIFICATĂ", 13, 165, 474, IND, anchor="middle", tracking=60))

# fields
FX = 330


def field(label, value, x, y, vsize=33):
    return (svg.small(MICH, label, 13.5, x, y, IND, tracking=120)
            + svg.small(MONO_B, value, vsize, x, y + 40, VOID))


c.append(field("NUME / NAME", "NECUNOSCUT", FX, 172))
c.append(field("PLANETA / PLANET", "???", FX, 250))
c.append(field("DATA SOSIRII", "01.01.2099", FX, 328))
c.append(field("OCHI", "2 (MARI)", FX + 320, 250, 30))
c.append(field("GRAVITAȚIE", "0,38 g", FX + 320, 328, 30))
c.append(svg.small(MICH, "SEMNĂTURA TITULARULUI", 13.5, FX, 410, IND, tracking=120))
sq = []
for i in range(120):
    t = i / 119
    x = FX + 10 + t * 300
    y = 448 - 18 * math.sin(t * 13) * (1 - t * 0.6) - 10 * math.sin(t * 31) + 6 * t
    sq.append(f"{f1(x)} {f1(y)}")
c.append(f'<path d="M{"L".join(sq)}M{FX + 40} 470Q{FX + 170} 455 {FX + 300} 466" fill="none" stroke="{VOID}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
c.append(n_badge(svg, 880, 420, 40, VOID, "#D9D4FF", ring=VOID, sw=3.2))
c.append(svg.small(MONO_B, "N-01", 13, 880, 492, IND, anchor="middle", tracking=80))

# machine readable zone
c.append(f'<g clip-path="url(#{svg.id("card")})"><rect x="0" y="508" width="{CW}" height="{CH - 508}" fill="#FFFFFF" opacity="0.5"/></g>')
for i, ln in enumerate(["IDXNEP<<NEPAMANTEAN<<<<<<<<<<<<<",
                        "NECUNOSCUT<<<<<<<<<<<<<<<<<<<<<<",
                        "20990101<<???<<<<<<<<<<<<<<<<<<6"]):
    c.append(svg.small(MONO_B, ln, 27, 500, 546 + i * 34, VOID, anchor="middle", tracking=180))

svg.add(f'<path d="{rrect(CX0 + 30, CY0 + 50, CW - 60, CH - 40, 40)}" fill="#8F7BFF" opacity="0.5" filter="url(#{svg.id("glow")})" transform="rotate({ROT} 600 {CY0 + CH / 2})"/>')
svg.add(f'<g transform="rotate({ROT} 600 {CY0 + CH / 2}) translate({CX0} {CY0})">'
        f'<path d="{rrect(0, 0, CW, CH, 40)}" fill="#3B2FA8" transform="translate(7 10)"/>'
        f'<path d="{rrect(0, 0, CW, CH, 40)}" fill="#6C6CFF" transform="translate(3.5 5)"/>{"".join(c)}</g>')

# ------------------------------------------------------------------ poster type around the card
svg.add(svg.small(MICH, "DOCUMENT DE CĂLĂTORIE", 18, 600, 250, LAV, anchor="middle", tracking=520))
svg.add(svg.small(MICH, "SPECIMEN · NU E VALABIL PE PĂMÂNT", 15, 600, 290, LAV, anchor="middle", tracking=300, opacity=0.75))
svg.add(svg.small(MONO_B, "Pierderea acestui act se anunță la cea mai apropiată farfurie zburătoare.", 17, 600, 1225, LAV, anchor="middle"))
svg.add(svg.small(MICH, SIGNATURE, 14, 600, 1272, LAV, anchor="middle", tracking=240, opacity=0.8))


def avoid(px, py):
    return 140 < py < 1270 and 60 < px < 1140


svg.add(sparkles(rnd, 26, (40, 60, 1160, 1440), rmin=6, rmax=22, color=WH, avoid=avoid, glow_id=svg.id("soft")))
for px, py, r in ((1090, 360, 30), (110, 1150, 24)):
    svg.add(f'<path d="{star4(px, py, r, waist=0.08)}" fill="{WH}"/>')

print(OUT, svg.save(OUT))
