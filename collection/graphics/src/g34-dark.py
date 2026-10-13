#!/usr/bin/env python3
"""g34-dark — PĂMÂNTUL E DOAR O ESCALĂ. A split-flap departures board panel (every
character on its own split tile, amber/white) under a two-line headline.
The board is a deliberate panel. Poster 1200x1500.
Run: python3 graphics/src/g34-dark.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_lib import MICH, MONO, MONO_B, ROOT, SIGNATURE, SVG, UNB, f1, rrect  # noqa: E402

ID = "g34-dark"
OUT = os.path.join(ROOT, "graphics", ID + ".svg")
rnd = random.Random(3434)
svg = SVG(ID, 1200, 1500)
AMBER = "#F4B942"
WH = "#F2F4FF"
LAV = "#C9C3FF"
ORANGE = "#FF4D2E"
CYAN = "#5FF3FF"

# ------------------------------------------------------------------ defs
svg.d(f'<linearGradient id="{svg.id("top")}" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0" stop-color="#2A2A38"/><stop offset="1" stop-color="#1C1C27"/></linearGradient>')
svg.d(f'<linearGradient id="{svg.id("bot")}" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0" stop-color="#15151E"/><stop offset="1" stop-color="#0F0F16"/></linearGradient>')
svg.d(f'<linearGradient id="{svg.id("panel")}" x1="0" y1="0" x2="0" y2="1">'
      '<stop offset="0" stop-color="#14141E"/><stop offset="1" stop-color="#0B0B12"/></linearGradient>')
svg.d(f'<filter id="{svg.id("glow")}" x="-0.3" y="-0.3" width="1.6" height="1.6" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation="4"/></filter>')

TW, TH, PITCH = 42, 64, 45


def tile(x, y, ch, color, size=48):
    h2 = TH / 2
    out = [f'<path d="M{f1(x)} {f1(y + h2)}V{f1(y + 5)}Q{f1(x)} {f1(y)} {f1(x + 5)} {f1(y)}H{f1(x + TW - 5)}Q{f1(x + TW)} {f1(y)} {f1(x + TW)} {f1(y + 5)}V{f1(y + h2)}Z" fill="url(#{svg.id("top")})"/>',
           f'<path d="M{f1(x)} {f1(y + h2)}V{f1(y + TH - 5)}Q{f1(x)} {f1(y + TH)} {f1(x + 5)} {f1(y + TH)}H{f1(x + TW - 5)}Q{f1(x + TW)} {f1(y + TH)} {f1(x + TW)} {f1(y + TH - 5)}V{f1(y + h2)}Z" fill="url(#{svg.id("bot")})"/>']
    if ch.strip():
        out.append(svg.small(MONO_B, ch, size, x + TW / 2, y + h2 + size * 0.36, color, anchor="middle"))
        out.append(f'<rect x="{f1(x)}" y="{f1(y + h2)}" width="{TW}" height="{f1(h2)}" fill="#000000" opacity="0.16"/>')
    out.append(f'<rect x="{f1(x)}" y="{f1(y + h2 - 1.5)}" width="{TW}" height="3" fill="#050508"/>')
    out.append(f'<rect x="{f1(x - 2)}" y="{f1(y + h2 - 4)}" width="3" height="8" fill="#3A3A4A"/>'
               f'<rect x="{f1(x + TW - 1)}" y="{f1(y + h2 - 4)}" width="3" height="8" fill="#3A3A4A"/>')
    return "".join(out)


def word(x, y, text, n, color, size=48):
    text = text.ljust(n)[:n]
    return "".join(tile(x + i * PITCH, y, ch, color, size) for i, ch in enumerate(text))


# ------------------------------------------------------------------ headline
svg.add(svg.small(MICH, "TERMINAL ORION · POARTA 7", 16, 600, 168, LAV, anchor="middle", tracking=420, opacity=0.85))
d1, b1, w1 = svg.text_d(UNB, "PĂMÂNTUL E", 112, 600, 322, anchor="middle")
d2, b2, w2 = svg.text_d(UNB, "DOAR O ESCALĂ", 112, 600, 0, anchor="middle")
# fit line 2 to the width of line 1
s2 = 112 * w1 / w2
d2, b2, w2 = svg.text_d(UNB, "DOAR O ESCALĂ", s2, 600, 324 + s2 * 0.75 + 34, anchor="middle")
svg.add(f'<path d="{d1}" fill="{WH}"/>')
svg.add(f'<path d="{d2}" fill="{AMBER}"/>')
TB = b2[3]

# ------------------------------------------------------------------ board
BX, BY, BW = 56, TB + 60, 1088
cols = [("ORĂ", 5), ("DESTINAȚIE", 7), ("STARE", 9)]
GAP = 34
total = sum(n for _, n in cols) * PITCH - 3 + GAP * 2
x0 = 600 - total / 2
colx = []
x = x0
for _, n in cols:
    colx.append(x)
    x += n * PITCH + GAP
rows = [("21:07", "MARTE", "ÎNTÂRZIAT", AMBER),
        ("22:40", "SATURN", "LA TIMP", WH),
        ("23:13", "LUNA", "ÎMBARCARE", AMBER),
        ("00:00", "ACASĂ", "ANULAT", ORANGE),
        ("", "", "", WH),
        ("", "", "", WH)]
HEAD = 92
ROWP = 84
BH = HEAD + 60 + len(rows) * ROWP + 64
svg.add(f'<path d="{rrect(BX, BY, BW, BH, 24)}" fill="url(#{svg.id("panel")})" stroke="#2C2C3C" stroke-width="5"/>')
svg.add(f'<path d="{rrect(BX + 12, BY + 12, BW - 24, BH - 24, 16)}" fill="none" stroke="#20202C" stroke-width="3"/>')
# header bar
hy = BY + 26
svg.add(f'<rect x="{BX + 26}" y="{hy}" width="{BW - 52}" height="{HEAD - 20}" rx="10" fill="{AMBER}"/>')
# small departing-saucer pictogram
px, py = BX + 74, hy + 36
svg.add(f'<g transform="rotate(-14 {px} {py})"><ellipse cx="{px}" cy="{py + 4}" rx="30" ry="9" fill="#0B0B12"/>'
        f'<path d="M{px - 15} {py}C{px - 14} {py - 22} {px + 14} {py - 22} {px + 15} {py}Z" fill="#0B0B12"/></g>'
        f'<path d="M{px - 30} {py + 22}H{px - 58}M{px - 26} {py + 30}H{px - 46}" stroke="#0B0B12" stroke-width="4" stroke-linecap="round"/>')
svg.add(svg.small(MICH, "PLECĂRI · DEPARTURES", 30, BX + 128, hy + 49, "#0B0B12", tracking=160))
svg.add(svg.small(MONO_B, "23:59", 34, BX + BW - 48, hy + 50, "#0B0B12", anchor="end", tracking=40))
# column heads
chy = BY + HEAD + 52
for (name, n), cx in zip(cols, colx):
    svg.add(svg.small(MICH, name, 16, cx + 2, chy, LAV, tracking=200))
svg.add(f'<path d="M{BX + 26} {chy + 16}H{BX + BW - 26}" stroke="#2C2C3C" stroke-width="3"/>')
ry = chy + 34
for t, dst, st, c in rows:
    svg.add(word(colx[0], ry, t, 5, WH))
    svg.add(word(colx[1], ry, dst, 7, WH))
    svg.add(word(colx[2], ry, st, 9, c))
    ry += ROWP
# status lamp on the boarding row + footer
lamp_y = chy + 34 + 2 * ROWP + TH / 2
svg.add(f'<circle cx="{BX + BW - 30}" cy="{f1(lamp_y)}" r="7" fill="{CYAN}" filter="url(#{svg.id("glow")})"/>'
        f'<circle cx="{BX + BW - 30}" cy="{f1(lamp_y)}" r="5" fill="{CYAN}"/>')
fy = BY + BH - 30
svg.add(svg.small(MONO_B, "Îmbarcarea se închide când îți amintești de unde vii.", 17, BX + 30, fy, LAV))
svg.add(svg.small(MONO_B, "PAGINA 1/1", 17, BX + BW - 30, fy, LAV, anchor="end", tracking=60))

# ------------------------------------------------------------------ bottom line
by = BY + BH + 70
svg.add(svg.small(MONO_B, "Vă mulțumim că ați ales planeta Pământ. Nu uitați bagajele cosmice.", 17, 600, by, LAV, anchor="middle"))
svg.add(svg.small(MICH, SIGNATURE, 14, 600, by + 42, LAV, anchor="middle", tracking=240, opacity=0.8))

print(OUT, svg.save(OUT), "board bottom", BY + BH)
