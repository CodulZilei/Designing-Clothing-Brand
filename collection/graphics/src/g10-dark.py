#!/usr/bin/env python3
"""g10-dark — CLASIFICAT N. The collection's parody classification label as a large back
print: framed label, giant orbiting "N", title NEPĂMÂNTEAN, a rating scale, rows of
Romanian fine print, barcode, tiny globe and registration marks. White/lavender inks.
Poster 1200x1500, transparent.
Run: python3 graphics/src/g10-dark.py
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_lib import (MICH, MONO, MONO_B, ROOT, SIGNATURE, SVG, UNB, UNB_S, barcode, f1, globe,  # noqa: E402
                      n_badge, notched, reg_mark, rrect, star4)

ID = "g10-dark"
OUT = os.path.join(ROOT, "graphics", ID + ".svg")
rnd = random.Random(1010)
svg = SVG(ID, 1200, 1500)
WH = "#F2F4FF"
LAV = "#C9C3FF"
KO = "#0A0A16"     # knock-out ink (reads as the fabric on dark tees)

FX, FY, FW, FH = 90, 110, 1020, 1290
# ------------------------------------------------------------------ frame + registration
svg.add(f'<path d="{notched(FX, FY, FW, FH, 28)}" fill="none" stroke="{WH}" stroke-width="7"/>')
svg.add(f'<path d="{notched(FX + 14, FY + 14, FW - 28, FH - 28, 20)}" fill="none" stroke="{LAV}" stroke-width="2.6"/>')
for x, y in ((48, 62), (1152, 62), (48, 1448), (1152, 1448)):
    svg.add(reg_mark(x, y, 13, LAV))
for x in (FX + FW / 2,):
    svg.add(f'<path d="M{x} 40V84M{x} 1426V1470" stroke="{LAV}" stroke-width="2.6"/>')

# ------------------------------------------------------------------ header band
svg.add(f'<rect x="{FX + 28}" y="{FY + 28}" width="{FW - 56}" height="70" fill="{LAV}"/>')
svg.add(svg.small(MICH, "COMISIA INTERGALACTICĂ DE CLASIFICARE", 23, 600, FY + 72, KO, anchor="middle", tracking=150))
svg.add(svg.small(MONO_B, "FORMULAR N-01", 15, FX + 30, FY + 122, LAV, tracking=60))
svg.add(svg.small(MONO_B, "EXEMPLAR UNIC · NU SE ÎNDOAIE", 15, FX + FW - 30, FY + 122, LAV, anchor="end", tracking=60))

# ------------------------------------------------------------------ giant N
svg.add(n_badge(svg, 345, 470, 205, WH, KO, ring=WH, sw=8))
for px, py, r in ((168, 300, 22), (548, 640, 16), (520, 268, 12)):
    svg.add(f'<path d="{star4(px, py, r, waist=0.1)}" fill="{WH}"/>')

# ------------------------------------------------------------------ rating scale
SX, SY = 640, 268
svg.add(svg.small(MICH, "SCALA DE CLASIFICARE", 17, SX, SY, LAV, tracking=220))
svg.add(f'<path d="M{SX} {SY + 16}H{FX + FW - 44}" stroke="{LAV}" stroke-width="2.6"/>')
scale = [("T", "TERESTRU", "Pentru toată planeta."),
         ("T+", "TERESTRU CU ATMOSFERĂ", "Doar însoțit de părinți."),
         ("OZN", "OBSERVAT NEIDENTIFICAT", "Doar noaptea, pe câmp."),
         ("N", "NEPĂMÂNTEAN", "Tu. Da, tu.")]
y = SY + 42
for i, (code, name, note) in enumerate(scale):
    hi = code == "N"
    rh = 82
    if hi:
        svg.add(f'<rect x="{SX - 8}" y="{y - 6}" width="{FX + FW - 44 - SX + 16}" height="{rh}" fill="{WH}"/>')
    ink, sub = (KO, KO) if hi else (WH, LAV)
    svg.add(f'<rect x="{SX + 2}" y="{y + 6}" width="64" height="58" rx="6" fill="none" stroke="{ink}" stroke-width="3"/>')
    d, _, w = svg.text_d(UNB_S if len(code) > 1 else UNB, code, 30 if len(code) < 3 else 21, SX + 34, y + 47, anchor="middle")
    svg.add(f'<path d="{d}" fill="{ink}"/>')
    svg.add(svg.small(MICH, name, 15.5, SX + 84, y + 30, ink, tracking=90))
    svg.add(svg.small(MONO_B, note, 17, SX + 84, y + 58, sub))
    if hi:
        cx, cy = FX + FW - 76, y + 35
        svg.add(f'<path d="M{cx - 14} {cy}l10 11l20 -24" fill="none" stroke="{KO}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    else:
        svg.add(f'<path d="M{SX} {y + rh - 2}H{FX + FW - 44}" stroke="{LAV}" stroke-width="2.6" opacity="0.45"/>')
    y += rh + 6
svg.add(svg.small(MONO, "* scala se aplică retroactiv", 15, SX, y + 18, LAV))

# ------------------------------------------------------------------ title
svg.add(svg.small(MICH, "— CLASIFICAT —", 25, 600, 790, LAV, anchor="middle", tracking=520))
d, bb, w = svg.text_d(UNB, "NEPĂMÂNTEAN", 92, 600, 905, anchor="middle")
svg.add(f'<path d="{d}" fill="{WH}"/>')
svg.add(f'<rect x="{FX + 40}" y="938" width="{FW - 80}" height="7" fill="{WH}"/>')

# ------------------------------------------------------------------ fine print rows
rows = [("SPECTATORI", "Sub 17 ani doar însoțit de un extraterestru adult."),
        ("CONȚINUT", "Priviri lungi spre cer. Întrebări existențiale la 3 noaptea."),
        ("LIMBAJ", "Expresii în dialecte de pe Proxima b, nesubtitrate."),
        ("GRAVITAȚIE", "Redusă. Țineți-vă de ceva solid, de preferat de mama."),
        ("EFECTE", "Dor de o planetă pe care n-ai văzut-o niciodată."),
        ("ATENȚIE", "Nu hrăniți farfuriile zburătoare după miezul nopții.")]
ry = 990
for i, (k, v) in enumerate(rows):
    svg.add(svg.small(MICH, k, 15.5, FX + 44, ry, LAV, tracking=120))
    svg.add(svg.small(MONO_B, v, 19.5, FX + 262, ry, WH))
    if i < len(rows) - 1:
        svg.add(f'<path d="M{FX + 44} {ry + 19}H{FX + FW - 44}" stroke="{LAV}" stroke-width="2.6" opacity="0.35"/>')
    ry += 46
svg.add(f'<path d="M{FX + 240} 962V{ry - 30}" stroke="{LAV}" stroke-width="2.6" opacity="0.35"/>')

# ------------------------------------------------------------------ bottom strip
by = 1268
svg.add(f'<path d="M{FX + 40} {by - 14}H{FX + FW - 40}" stroke="{WH}" stroke-width="3"/>')
svg.add(barcode(rnd, FX + 44, by + 6, 230, 58, WH))
svg.add(svg.small(MONO_B, "0 000001 N2026 7", 15, FX + 44 + 115, by + 90, LAV, anchor="middle", tracking=120))
svg.add(svg.small(MICH, "AVIZ NR. 0001 / N / 2026", 17, 625, by + 34, WH, anchor="middle", tracking=140))
svg.add(svg.small(MONO_B, "Valabil în toată galaxia, mai puțin aici.", 16, 625, by + 64, LAV, anchor="middle"))
svg.add(svg.small(MICH, SIGNATURE, 12.5, 625, by + 92, LAV, anchor="middle", tracking=200))
svg.add(globe(FX + FW - 100, by + 44, 44, WH, sw=2.8, tilt=-20, lat=3, lon=4, orbit=True))

print(OUT, svg.save(OUT))
