#!/usr/bin/env python3
"""Exploration for v3 'Monograma IU': several I+U fusions drawn in code,
laid out on one contact sheet (v3-sketches.svg) with 32 px / 16 px stand-ins.

Run:  python3 sketches_v3.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v3_geom import (PALETTE, circle, path_el, poly, rect, rrect, svg_doc, text_geom,  # noqa: E402
                     tooth, transform, union)

Y, K = PALETTE['yellow'], PALETTE['black']


def u_round(x0, x1, top, bottom, s):
    """Round-bottomed U (outer width x1-x0, stem s)."""
    R = (x1 - x0) / 2
    cx, cy = x0 + R, bottom - R
    outer = union(rect(x0, top, x1, cy), circle(cx, cy, R))
    inner = union(rect(x0 + s, top - 10, x1 - s, cy), circle(cx, cy, R - s))
    return outer.difference(inner), (cx, cy, R)


# A: I + U whose bowl is half a gear
def sk_a():
    s = 190
    I = rect(90, 120, 90 + s, 820)
    U, (cx, cy, R) = u_round(350, 910, 120, 820, s)
    teeth = union(*[tooth(cx, cy, a, R - 20, R + 75, 115, 78) for a in (12, 51, 90, 129, 168)])
    return [(I, K), (union(U, teeth), Y)]


# B: gear with a slot cut from the top = U, I standing in the slot
def sk_b():
    cx, cy, R, r = 500, 560, 330, 160
    ring = union(circle(cx, cy, R), *[tooth(cx, cy, -90 + i * 36, R - 20, R + 85, 120, 80) for i in range(10)])
    slot = union(circle(cx, cy, r), rect(cx - r, 0, cx + r, cy))
    U = ring.difference(slot)
    I = rect(cx - 82, 100, cx + 82, cy + 40)
    return [(U, Y), (I, K)]


# C: I with a pin hole (lift arm) + U drawn as a bucket in profile, sharp cutting lip
def sk_c():
    s = 190
    I = rect(80, 150, 80 + s, 860).difference(circle(80 + s / 2, 265, 42))
    x0, R = 340, 280
    cx, cy = x0 + R, 860 - R
    outer = union(rect(x0, 150, x0 + 2 * R, cy), circle(cx, cy, R),
                  poly([(x0 + 2 * R - s, cy), (x0 + 2 * R - s, 300), (x0 + 2 * R + 70, 90), (x0 + 2 * R, cy)]))
    inner = union(rect(x0 + s, 100, x0 + 2 * R - s, cy), circle(cx, cy, R - s))
    # clip the left arm and the region above the lip
    U = outer.difference(inner).difference(poly([(x0 + 2 * R - s, 0), (x0 + 2 * R - s, 300), (x0 + 2 * R + 70, 90), (1000, 0)]))
    U = U.difference(rect(x0 - 5, 0, x0 + s + 5, 150))
    return [(I, K), (U, Y)]


# D: I + U as a bucket seen from the front, teeth along the cutting edge
def sk_d():
    s = 190
    I = rect(90, 110, 90 + s, 790)
    outer = rrect(350, 110, 910, 790, 0, 0, 210, 210)
    inner = rrect(350 + s, 60, 910 - s, 790 - s, 0, 0, 40, 40)
    U = outer.difference(inner)
    teeth = union(*[rect(x, 770, x + 74, 880).difference(poly([(x - 1, 880), (x + 37, 860), (x + 75, 880)]))
                    for x in (392, 535, 678, 821)])
    teeth = union(*[poly([(x, 780), (x + 80, 780), (x + 66, 885), (x + 14, 885)]) for x in (395, 535, 675, 815)])
    return [(I, K), (union(U, teeth), Y)]


# E: big U with the I as a hydraulic cylinder standing in the counter
def sk_e():
    s = 200
    U, (cx, cy, R) = u_round(110, 890, 100, 900, s)
    barrel = rrect(cx - 95, 470, cx + 95, 720, 18, 18, 95, 95)
    rod = rect(cx - 38, 250, cx + 38, 480)
    eye = circle(cx, 210, 72).difference(circle(cx, 210, 28))
    I = union(barrel, rod, eye)
    return [(U, K), (I, Y)]


# F: hex nut with IU knocked out
def sk_f():
    import math
    hexa = poly([(500 + 470 * math.cos(math.radians(a)), 500 + 470 * math.sin(math.radians(a))) for a in range(0, 360, 60)])
    t, w = text_geom('ArchivoBlack-Regular.ttf', 'IU', 470, 500, 500 + 470 * 0.688 / 2, -10, 'middle')
    return [(hexa.difference(t), K)]


# G: ligature - U's left arm rises as the I / lift arm, right arm is the bucket lip
def sk_g():
    s = 210
    x0, x1 = 170, 830
    R = (x1 - x0) / 2
    cx, cy = x0 + R, 880 - R
    outer = union(rect(x0, 100, x0 + s, cy), rect(x1 - s, 360, x1, cy), circle(cx, cy, R),
                  poly([(x1 - s, 360), (x1 + 40, 280), (x1, 400)]))
    inner = union(rect(x0 + s, 0, x1 - s, cy), circle(cx, cy, R - s))
    U = outer.difference(inner).difference(circle(x0 + s / 2, 210, 45))
    return [(U, K)]


# H: I + U with gear teeth on the whole outer contour of the U (rack + pinion)
def sk_h():
    s = 190
    I = rect(90, 120, 90 + s, 820)
    U, (cx, cy, R) = u_round(350, 910, 120, 820, s)
    teeth = [tooth(cx, cy, a, R - 20, R + 70, 105, 72) for a in (0, 45, 90, 135, 180)]
    for yy in (230, 400):
        teeth.append(poly([(910 - 20, yy - 52), (910 + 70, yy - 36), (910 + 70, yy + 36), (910 - 20, yy + 52)]))
    return [(I, K), (union(U, *teeth), Y)]


SKETCHES = [
    ('A', 'ROATĂ-U', sk_a),
    ('B', 'FANTĂ ÎN ROATĂ', sk_b),
    ('C', 'CUPĂ PROFIL', sk_c),
    ('D', 'CUPĂ FAȚĂ', sk_d),
    ('E', 'CILINDRU ÎN U', sk_e),
    ('F', 'PIULIȚĂ', sk_f),
    ('G', 'LIGATURĂ BRAȚ', sk_g),
    ('H', 'U ANGRENAJ', sk_h),
]


def sheet(sketches, cols=4, out='v3-sketches.svg', extra_rows=None):
    cell, gap, label_h = 1000, 80, 260
    rows = (len(sketches) + cols - 1) // cols
    W = cols * cell + (cols + 1) * gap
    H = rows * (cell + label_h) + (rows + 1) * gap
    body = [f'<path fill="{PALETTE["concrete"]}" d="M0 0 H{W} V{H} H0 Z"/>']
    for i, (code, name, fn) in enumerate(sketches):
        c, r = i % cols, i // cols
        ox = gap + c * (cell + gap)
        oy = gap + r * (cell + label_h + gap)
        body.append(f'<path fill="{PALETTE["white"]}" d="M{ox} {oy} h{cell} v{cell} h-{cell} Z"/>')
        parts = fn()
        for g, col in parts:
            body.append(path_el(transform(g, 1, ox, oy), col))
        # label
        lab, _ = text_geom('IBMPlexMono-SemiBold.ttf', f'{code}  {name}', 58, ox, oy + cell + 90)
        body.append(path_el(lab, PALETTE['steel']))
        # 32 px and 16 px stand-ins (sheet renders at 1200 px wide -> 1 px = W/1200 units)
        px = W / 1200.0
        allg = union(*[g for g, _ in parts])
        for k, size in enumerate((32, 16)):
            sc = size * px / 1000.0
            bx = ox + cell - (size * px) - (0 if k == 0 else 32 * px + 30)
            body.append(path_el(transform(allg, sc, bx, oy + cell + 120), K))
        for k, size in enumerate((32,)):
            sc = size * px / 1000.0
            bx = ox
            for g, col in parts:
                body.append(path_el(transform(g, sc, bx, oy + cell + 120), col))
    with open(os.path.join(HERE, out), 'w') as f:
        f.write(svg_doc(W, H, ''.join(body)))
    print('wrote', out)


if __name__ == '__main__':
    sheet(SKETCHES)
