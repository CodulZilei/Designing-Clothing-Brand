#!/usr/bin/env python3
"""v6 'Plăcuță industrială' generator.

The logo is a riveted equipment identification plate: black plate with rounded
corners, four hex bolt heads, a hazard-stripe band along top and bottom,
IMPACT in Saira Stencil One over UTILAJE in Saira Condensed Black (both lines
the same ink width, as in the approved v3 wordmark).

All geometry is built with shapely in SVG coordinates. Knock-outs (bolt rings,
UTILAJE in the colour file, everything in the one-ink files) are real holes in
the plate path (fill-rule evenodd), never light shapes painted on top.

Run:  python3 generate_v6.py
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'logos', 'v3-monograma'))

from text2path import outline  # noqa: E402,F401
from shapely import affinity  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402
from v3_geom import (PALETTE, path_el, rect, rrect, svg_doc, text_glyphs, transform,  # noqa: E402
                     union)

Y, K, S = PALETTE['yellow'], PALETTE['black'], PALETTE['steel']
STENCIL = 'SairaStencilOne-Regular.ttf'
COND = 'SairaCondensed-Black.ttf'
CAP_RATIO = 0.688  # cap height / em for both Saira cuts

# optical spacing for the tracked UTILAJE line, per gap U-T T-I I-L L-A A-J J-E (x cap height)
UTILAJE_OPTICAL = (-0.08, -0.10, 0.0, -0.16, -0.12, 0.0)


# ------------------------------------------------------------------ primitives
def hexagon(cx, cy, r, rot=0.0):
    return Polygon([(cx + r * math.cos(math.radians(rot + 60 * i)),
                     cy + r * math.sin(math.radians(rot + 60 * i))) for i in range(6)])


def bolt(cx, cy, r, gap, rot):
    """Hex bolt head: solid hex + the ring of plate cut away around it."""
    head = hexagon(cx, cy, r, rot)
    ring = head.buffer(gap, join_style='mitre').difference(head)
    return head, ring


def hazard(x0, y0, x1, y1, sw):
    """Yellow parts of a '/'-leaning hazard band: only whole stripes, centred
    between x0 and x1, so both band ends finish on a full slanted stripe
    (no slivers, clean for vinyl and embroidery)."""
    h = y1 - y0
    period = 2 * sw
    n = int((x1 - x0 - sw - h) / period) + 1
    span = (n - 1) * period + sw + h
    start = (x0 + x1 - span) / 2
    stripes = []
    for i in range(n):
        xa = start + i * period
        stripes.append(Polygon([(xa, y1), (xa + sw, y1), (xa + sw + h, y0), (xa + h, y0)]))
    return union(*stripes)


def loader_geom(level='micro'):
    data = json.load(open(os.path.join(ROOT, 'assets', 'loader.json')))
    d = data['paths'][level]
    g = Polygon()
    for sub in re.findall(r'M[^MZ]*Z', d):
        nums = list(map(float, re.findall(r'-?\d+(?:\.\d+)?', sub)))
        pts = list(zip(nums[0::2], nums[1::2]))
        g = g.symmetric_difference(Polygon(pts).buffer(0))  # even-odd
    return g


# ------------------------------------------------------------------ wordmark
def wordmark(cap1, gap, cap2):
    """IMPACT over UTILAJE, equal ink width; ink starts at x=0, IMPACT cap top at y=0."""
    imp = union(*text_glyphs(STENCIL, 'IMPACT', cap1 / CAP_RATIO, 0, cap1)[0])
    b = imp.bounds
    imp = transform(imp, 1, -b[0], -b[1])
    w1 = b[2] - b[0]
    base2 = cap1 + gap + cap2

    def ut(tr):
        gl, _, _ = text_glyphs(COND, 'UTILAJE', cap2 / CAP_RATIO, 0, base2, tr)
        shift, out = 0.0, []
        for g, adj in zip(gl, [0] + list(UTILAJE_OPTICAL)):
            shift += adj * cap2
            out.append(transform(g, 1, shift, 0))
        return union(*out)

    g0, g1 = ut(0), ut(100)
    w0 = g0.bounds[2] - g0.bounds[0]
    wa = g1.bounds[2] - g1.bounds[0]
    tr = 100 * (w1 - w0) / (wa - w0)
    uti = ut(tr)
    b2 = uti.bounds
    uti = transform(uti, 1, -b2[0], 0)
    return imp, uti, w1, tr


# ------------------------------------------------------------------ plate
P = dict(
    cap1=150, gap=40, cap2_ratio=0.70,
    edge=24,        # plate edge to band / bolt row
    band=46,        # hazard band height
    stripe=34,      # stripe width (horizontal)
    bolt_r=17, bolt_gap=4.5,
    band_bolt=16,   # space between bolt ring and band end
    side=92,        # plate edge to text
    text_gap=44,    # band to text
    radius=26,
)


def plate(p=P, with_loader=False):
    cap2 = p['cap1'] * p['cap2_ratio']
    imp, uti, tw, tr = wordmark(p['cap1'], p['gap'], cap2)
    th = p['cap1'] + p['gap'] + cap2
    e, hb = p['edge'], p['band']
    tx = p['side']
    loader = None
    if with_loader:
        lg = loader_geom('micro')
        lb = lg.bounds
        lh = th * 0.74
        sc = lh / (lb[3] - lb[1])
        lg = transform(lg, sc, 0, 0)
        lb = lg.bounds
        loader_w = lb[2] - lb[0]
        loader = affinity.translate(lg, tx - lb[0], 0)
        tx += loader_w + p['cap1'] * 0.42
    W = tx + tw + p['side']
    ty = e + hb + p['text_gap']
    H = ty + th + p['text_gap'] + hb + e
    if loader is not None:
        lb = loader.bounds
        # centre the machine on the text block, nudged down a touch so it feels grounded
        loader = affinity.translate(loader, 0, ty + th / 2 + th * 0.03 - (lb[1] + lb[3]) / 2)
    body = rrect(0, 0, W, H, *(p['radius'],) * 4)
    imp = transform(imp, 1, tx, ty)
    uti = transform(uti, 1, tx, ty)
    bc = e + hb / 2
    rots = (8, 23, -14, 37)  # each bolt turned a little differently, like a real fitted plate
    heads, rings = [], []
    for (cx, cy), rot in zip([(bc, bc), (W - bc, bc), (bc, H - bc), (W - bc, H - bc)], rots):
        h, r = bolt(cx, cy, p['bolt_r'], p['bolt_gap'], rot)
        heads.append(h)
        rings.append(r)
    bx0 = bc + p['bolt_r'] + p['bolt_gap'] + p['band_bolt']
    bands = union(hazard(bx0, e, W - bx0, e + hb, p['stripe']),
                  hazard(bx0, H - e - hb, W - bx0, H - e, p['stripe']))
    return dict(W=W, H=H, body=body, imp=imp, uti=uti, heads=union(*heads), rings=union(*rings),
                bands=bands, loader=loader, tracking=tr)


def icon_plate(S=500):
    """Square plate, stencil IU, bolts in the corners, short hazard bands."""
    e, hb, br, bg = 26, 64, 22, 5
    body = rrect(0, 0, S, S, *(36,) * 4)
    cap = 214
    iu = union(*text_glyphs(STENCIL, 'IU', cap / CAP_RATIO, 0, cap)[0])
    b = iu.bounds
    iu = transform(iu, 1, (S - (b[2] - b[0])) / 2 - b[0], (S - (b[3] - b[1])) / 2 - b[1])
    bc = e + hb / 2
    heads, rings = [], []
    for (cx, cy), rot in zip([(bc, bc), (S - bc, bc), (bc, S - bc), (S - bc, S - bc)], (8, 23, -14, 37)):
        h, r = bolt(cx, cy, br, bg, rot)
        heads.append(h)
        rings.append(r)
    bx0 = bc + br + bg + 16
    bands = union(hazard(bx0, e, S - bx0, e + hb, 44), hazard(bx0, S - e - hb, S - bx0, S - e, 44))
    return dict(W=S, H=S, body=body, imp=iu, uti=None, heads=union(*heads), rings=union(*rings),
                bands=bands, loader=None)


# ------------------------------------------------------------------ colourways
def render(g, mode, margin_frac=0.04, title=''):
    W, H = g['W'], g['H']
    m = margin_frac * W
    def mv(x):
        return None if x is None else transform(x, 1, m, m)
    body, imp, uti, heads, rings, bands, loader = (mv(g[k]) for k in
                                                   ('body', 'imp', 'uti', 'heads', 'rings', 'bands', 'loader'))
    parts = []
    if mode == 'color':
        # black plate; UTILAJE and the bolt rings are holes; yellow sits on the plate
        plate_g = body.difference(union(uti, rings, heads))
        parts.append(path_el(plate_g, K))
        parts.append(path_el(heads, S))
        parts.append(path_el(union(imp, bands, loader), Y))
    else:
        ink = K if mode == 'mono' else Y
        plate_g = body.difference(union(uti, imp, rings, bands, loader))
        parts.append(path_el(plate_g, ink))
    return svg_doc(W + 2 * m, H + 2 * m, ''.join(parts), title)


def main():
    out = HERE
    g = plate()
    print('UTILAJE tracking:', round(g['tracking'], 1), 'plate', round(g['W'], 1), 'x', round(g['H'], 1))
    files = {
        'v6-color.svg': render(g, 'color', title='Impact Utilaje — plăcuță industrială, color'),
        'v6-mono-black.svg': render(g, 'mono', title='Impact Utilaje — plăcuță industrială, monocrom negru'),
        'v6-reverse.svg': render(g, 'reverse', title='Impact Utilaje — plăcuță industrială, pentru fundal închis'),
    }
    gi = icon_plate()
    files['v6-icon.svg'] = render(gi, 'color', title='Impact Utilaje — simbol plăcuță IU')
    files['v6-icon-reverse.svg'] = render(gi, 'reverse', title='Impact Utilaje — simbol plăcuță IU, fundal închis')
    gl = plate(with_loader=True)
    files['v6-color-utilaj.svg'] = render(gl, 'color', title='Impact Utilaje — plăcuță industrială cu utilaj, color')
    for name, svg in files.items():
        with open(os.path.join(out, name), 'w', encoding='utf-8') as f:
            f.write(svg)
        print('wrote', name, len(svg) // 1024, 'KB')


if __name__ == '__main__':
    main()
