#!/usr/bin/env python3
"""Self-check for the v2 'Emblemă' SVGs.

1. File rules: XML parses, xmlns + viewBox, no <text>/<image>/<filter>/gradients/<use>,
   no raster data, only palette colours.
2. Embroidery / vinyl check on the artwork itself: every ink area and every hole must be at
   least MIN units wide (1.2 % of the badge diameter). A part thinner than MIN vanishes under
   erosion by MIN/2; a hole narrower than MIN closes under dilation by MIN/2.

Run:  python3 check_v2.py
"""
import glob
import os
import re
import xml.etree.ElementTree as ET

from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
PALETTE = {'#F2A20A', '#111111', '#4A4F55', '#E6E4DF', '#FFFFFF'}
NS = '{http://www.w3.org/2000/svg}'
DIAMETER = 920.0             # tooth tip to tooth tip
MIN = 0.012 * DIAMETER       # ~11 units


def geom(d):
    g = Polygon()
    for sub in re.split(r'(?=M)', d.strip()):
        n = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', sub)]
        pts = list(zip(n[0::2], n[1::2]))
        if len(pts) >= 3:
            g = g.symmetric_difference(Polygon(pts).buffer(0))
    return g


def parts(g):
    return [g] if g.geom_type == 'Polygon' else list(g.geoms)


def erosion_test(g, r):
    """(parts that vanish, extra pieces from necks) when g is eroded by r."""
    lost, split = 0, 0
    for p in parts(g):
        e = p.buffer(-r)
        k = 0 if e.is_empty else len(parts(e))
        if k == 0 and p.area > 1:
            lost += 1
        elif k > 1:
            # a tapering tip (S terminal, tooth corner) leaves a crumb; only count real pieces
            split += sum(1 for q in sorted(parts(e), key=lambda q: -q.area)[1:] if q.area > 30)
    return lost, split


def thin_report(g, r):
    """Ink: parts thinner than 2r (lost) or with necks thinner than 2r.
    Gaps: the same test on the negative space inside the artwork's hull (counters,
    letters cut out of the ring, tyre rings, gaps between bars and teeth)."""
    neg = g.convex_hull.difference(g)
    return erosion_test(g, r) + erosion_test(neg, r)


def where(g, r):
    """Centres of the thin bits, for debugging."""
    out = []
    for p in parts(g):
        o = p.buffer(-r).buffer(r)
        lost = p.difference(o.buffer(0.5))
        for q in parts(lost) if not lost.is_empty else []:
            if q.area > 4:
                out.append((round(q.centroid.x), round(q.centroid.y), round(q.area)))
    return out


def check(path):
    src = open(path, encoding='utf-8').read()
    errs = []
    root = ET.fromstring(src)
    if root.tag != NS + 'svg':
        errs.append('root is not svg in the SVG namespace')
    vb = root.get('viewBox')
    if not vb or len(vb.split()) != 4:
        errs.append('no viewBox')
    for el in root.iter():
        tag = el.tag.replace(NS, '')
        if tag in ('text', 'tspan', 'image', 'filter', 'linearGradient', 'radialGradient', 'pattern', 'use', 'mask', 'clipPath'):
            errs.append(f'forbidden <{tag}>')
        for attr in ('fill', 'stroke'):
            v = el.get(attr)
            if v and v != 'none' and v.upper() not in PALETTE:
                errs.append(f'colour {v} not in palette')
        if el.get('style'):
            errs.append('inline style attribute')
    if re.search(r'data:image|url\(', src):
        errs.append('raster data or url() reference')
    by_fill = {}
    for el in root.iter(NS + 'path'):
        by_fill.setdefault(el.get('fill').upper(), []).append(geom(el.get('d')))
    w, h = (float(v) for v in vb.split()[2:])
    allg = unary_union([g for gs in by_fill.values() for g in gs])
    x0, y0, x1, y1 = allg.bounds
    margin = min(x0, y0, w - x1, h - y1) / w * 100
    rep = []
    for fill, gs in by_fill.items():
        lost, split, glost, gsplit = thin_report(unary_union(gs), MIN / 2)
        rep.append(f'{fill}: ink<{MIN:.0f}u lost={lost} necks={split}; gaps<{MIN:.0f}u lost={glost} necks={gsplit}')
    return errs, margin, rep


def main():
    ok = True
    for f in sorted(glob.glob(os.path.join(HERE, '*.svg'))):
        errs, margin, rep = check(f)
        ok &= not errs
        print(f'{os.path.basename(f):24s} {"OK " if not errs else "ERR"} margin={margin:.1f}%  ' + ' | '.join(rep))
        for e in errs:
            print('   ', e)
    print('ALL OK' if ok else 'FAILED')


if __name__ == '__main__':
    main()
