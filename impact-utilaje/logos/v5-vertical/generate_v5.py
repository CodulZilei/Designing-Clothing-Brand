#!/usr/bin/env python3
"""v5 'Vertical' — stacked / square lockup.

Symbol: a large yellow gear with the black wheel loader ('simplu' level from
assets/loader.json) driving across its lower part like a seal. The gear is cut
back around the loader with a real knockout gap (boolean difference, not a
white outline), so the mark also works in one colour.
Below: IMPACT over UTILAJE in Archivo Black, both lines the same ink width
(same treatment as v3), then a short hazard-stripe underline.

Icon: the gear with the 'micro' loader inside it, sized for a circular crop.

Run:  python3 generate_v5.py      (writes the SVGs next to this script)
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
from gear import gear_path  # noqa: E402,F401
from shapely.geometry import Polygon  # noqa: E402
from v3_geom import (PALETTE, circle, path_el, rect, soften_inner, svg_doc,  # noqa: E402
                     tooth, transform, type_path, union)
from generate_v3 import wordmark  # noqa: E402  (shared two-line wordmark, equal widths)

Y, K, WH = PALETTE['yellow'], PALETTE['black'], PALETTE['white']

# ------------------------------------------------------------------ loader (imported, not redrawn)
with open(os.path.join(ROOT, 'assets', 'loader.json')) as f:
    LD = json.load(f)
L_BBOX = LD['content_bbox']          # [24, 100, 498, 300] in the 520x320 master
L_WHEELS = LD['wheel_centers']
L_WR = LD['wheel_radius']


def loader_geom(level):
    """Parse the M/L/Z path data of one level into shapely, even-odd."""
    d = LD['paths'][level]
    g = Polygon()
    for sub in re.findall(r'M[^M]+', d):
        pts = [tuple(map(float, p)) for p in re.findall(r'(-?[\d.]+)[ ,](-?[\d.]+)', sub)]
        if len(pts) >= 3:
            g = g.symmetric_difference(Polygon(pts).buffer(0))
    return g


def solid(g):
    """The silhouette with every hole filled (windows, hubs) — used for knockouts."""
    polys = [g] if isinstance(g, Polygon) else list(g.geoms)
    return union(*[Polygon(p.exterior) for p in polys])


# ------------------------------------------------------------------ gear
def gear(cx, cy, R, teeth=12, root=0.86, hole=0.0, t_base=None, t_tip=None, rot=0.0, fillet=0.0):
    """Shapely gear: R = tip radius. Teeth are trapezoids on a root disc."""
    r_root = R * root
    pitch = 2 * math.pi * r_root / teeth
    tb = t_base if t_base is not None else pitch * 0.56
    tt = t_tip if t_tip is not None else pitch * 0.40
    g = circle(cx, cy, r_root, 128)
    T = [tooth(cx, cy, rot + i * 360 / teeth, r_root - 4, R, tb, tt) for i in range(teeth)]
    g = union(g, *T)
    if fillet:
        g = soften_inner(g, fillet)
    if hole:
        g = g.difference(circle(cx, cy, R * hole, 128))
    return g


# ------------------------------------------------------------------ symbol
S = dict(
    R=500.0,          # gear tip radius
    teeth=12,
    root=0.86,
    hole=0.0,         # hub hole as fraction of R (0 = solid disc; a hub would hide behind the cab)
    rot=-90,          # a tooth at top centre and one at bottom centre; side teeth clear the ground cut
    l_w=1.18,         # loader content width as a multiple of the gear diameter
    l_ground=0.60,    # loader ground line (= gear split), fraction of R below the gear centre
    l_dx=0.0,         # horizontal nudge of the loader, fraction of R
    gap=0.045,        # knockout gap, fraction of R
)


def symbol(p=S, level='simplu'):
    """Return (gear_geom, loader_geom) with the gear centre at (0, 0)."""
    R = p['R']
    lg = loader_geom(level)
    lw = L_BBOX[2] - L_BBOX[0]
    sc = p['l_w'] * 2 * R / lw
    lcx = (L_BBOX[0] + L_BBOX[2]) / 2
    dx = -lcx * sc + p['l_dx'] * R
    dy = p['l_ground'] * R - LD['ground_y'] * sc
    ld = transform(lg, sc, dx, dy)
    g = gear(0, 0, R, p['teeth'], p['root'], p['hole'], rot=p['rot'], fillet=R * 0.02)
    lb = ld.bounds
    ground = p['l_ground'] * R
    wheel_y = L_WHEELS[0][1] * sc + dy
    # knockout: the loader silhouette plus the pocket under its chassis, grown by the gap
    knock = union(solid(ld), rect(lb[0] + R * 0.1, wheel_y, lb[2] - R * 0.1, ground))
    knock = knock.buffer(p['gap'] * R, join_style='round', quad_segs=16)
    # close the narrow pockets (arm / bucket) so no yellow slivers survive
    knock = knock.buffer(R * 0.10, join_style='round').buffer(-R * 0.10, join_style='round')
    # the gear is split along the ground line: the part below becomes the ground the loader drives on
    knock = union(knock, rect(-2 * R, ground, 2 * R, ground + p['gap'] * R))
    g = g.difference(knock)
    # remove slivers thinner than ~0.1R (tooth tips peeking past the loader) without
    # rounding the real teeth: opening, then grow back with mitred corners and clip to the original
    r = R * 0.05
    opened = g.buffer(-r, join_style='mitre').buffer(r, join_style='round', quad_segs=16)
    g = g.intersection(opened.buffer(r, join_style='mitre'))
    if not isinstance(g, Polygon):
        g = union(*[q for q in g.geoms if q.area > (R * 0.12) ** 2])
    return g, ld


# ------------------------------------------------------------------ hazard stripes
def hazard(cx, y0, h, n=7, sw_k=0.9, slant=1.0):
    """Diagonal-stripe bar made of n whole parallelograms (odd n: yellow at both ends),
    centred on cx by its ink. Returns (yellow_geom, black_geom, ink_width)."""
    sw = h * sw_k
    k = slant * h
    W = n * sw + k
    x0 = cx - W / 2
    ys, ks = [], []
    for i in range(n):
        x = x0 + i * sw
        pg = Polygon([(x + k, y0), (x + k + sw, y0), (x + sw, y0 + h), (x, y0 + h)])
        (ys if i % 2 == 0 else ks).append(pg)
    return union(*ys), union(*ks), W


# ------------------------------------------------------------------ lockup
LAY = dict(
    word_w=1.00,      # wordmark ink width as a multiple of the symbol width
    gap_sym=0.45,     # symbol -> IMPACT, in IMPACT cap heights
    gap_bar=0.42,     # UTILAJE -> hazard bar, in IMPACT cap heights
    bar_n=7,          # stripes in the hazard bar (odd)
    bar_h=0.30,       # hazard bar height, in IMPACT cap heights
    margin=0.04,
)


def lockup(colors, p=S, lay=LAY):
    """colors: gear, loader, type, bar_a (yellow stripes), bar_b (black stripes, None = omit)."""
    G, Ld = symbol(p)
    sb = union(G, Ld).bounds
    sym_w = sb[2] - sb[0]
    # wordmark built at a nominal cap height then scaled to the target width
    cap1 = 100.0
    imp, uti, imp_ops, uti_ops, w1, tr = wordmark(cap1, 0.27 * cap1, 0.654 * cap1)
    target_w = lay['word_w'] * sym_w
    k = target_w / w1
    word_h = union(imp, uti).bounds[3] * k
    cap1k = cap1 * k
    # vertical stack, centred on x = 0 (symbol is placed on its bbox centre)
    sym_dx = -(sb[0] + sb[2]) / 2
    sym_dy = -sb[1]
    y_word = (sb[3] - sb[1]) + lay['gap_sym'] * cap1k
    y_bar = y_word + word_h + lay['gap_bar'] * cap1k
    bar_h = lay['bar_h'] * cap1k
    hy, hk, _ = hazard(0, y_bar, bar_h, lay['bar_n'])
    total_h = y_bar + bar_h
    total_w = max(sym_w, target_w)
    m = lay['margin'] * total_w / (1 - 2 * lay['margin'])
    vb_w, vb_h = total_w + 2 * m, total_h + 2 * m
    ox, oy = vb_w / 2, m
    body = ''
    parts = [(transform(G, 1, sym_dx, sym_dy), colors['gear']),
             (transform(Ld, 1, sym_dx, sym_dy), colors['loader']),
             (hy, colors['bar_a'])]
    if colors.get('bar_b'):
        parts.append((hk, colors['bar_b']))
    body += merge_by_color(parts, ox, oy)
    # type: true curves via text2path, scaled with a group-free approach (re-outline at final size)
    sz = k
    ops = [(f, t, s * sz, x * sz - target_w / 2 + ox, yb * sz + y_word + oy) for f, t, s, x, yb in imp_ops + uti_ops]
    body += type_path(ops, colors['type'])
    return svg_doc(vb_w, vb_h, body, 'Impact Utilaje'), dict(tracking=tr, vb=(vb_w, vb_h))


def merge_by_color(parts, dx=0, dy=0):
    order, groups = [], {}
    for g, c in parts:
        if c not in groups:
            groups[c] = []
            order.append(c)
        groups[c].append(transform(g, 1, dx, dy))
    return ''.join(path_el(union(*groups[c]), c) for c in order)


# ------------------------------------------------------------------ icon
I = dict(
    R=500.0, teeth=10, root=0.84, hole=0.0, rot=-90 + 18,
    l_w=0.74,        # loader width as a multiple of the gear diameter
    l_cy=0.06,       # vertical offset of the loader bbox centre, fraction of R (down)
    gap=0.06,
)


def icon_geom(p=I, level='micro'):
    R = p['R']
    lg = loader_geom(level)
    lw = L_BBOX[2] - L_BBOX[0]
    lh = L_BBOX[3] - L_BBOX[1]
    sc = p['l_w'] * 2 * R / lw
    dx = -(L_BBOX[0] + L_BBOX[2]) / 2 * sc
    dy = -(L_BBOX[1] + L_BBOX[3]) / 2 * sc + p['l_cy'] * R
    ld = transform(lg, sc, dx, dy)
    g = gear(0, 0, R, p['teeth'], p['root'], p['hole'], rot=p['rot'], fillet=R * 0.02)
    knock = solid(ld).buffer(p['gap'] * R, join_style='round', quad_segs=16)
    if p.get('split', False):  # tried: cuts side teeth into wedges inside a circle, so off by default
        # same idea as the lockup: the gear is split along the loader's ground line
        ground = LD['ground_y'] * sc + dy
        knock = union(knock, rect(-2 * R, ground, 2 * R, ground + p['gap'] * R))
    g = g.difference(knock)
    return g, ld, sc * lh


def icon(colors, p=I, margin=0.04, knockout=False):
    """Square icon, 1000x1000, gear inscribed (fits a circular avatar crop).
    knockout=True: loader is negative space in the gear (single colour)."""
    G, Ld, _ = icon_geom(p)
    Sz = 1000.0
    sc = Sz * (1 - 2 * margin) / (2 * p['R'])
    G = transform(G, sc, Sz / 2, Sz / 2)
    Ld = transform(Ld, sc, Sz / 2, Sz / 2)
    if knockout:
        # gear with the loader silhouette cut out; loader's own holes come back as gear islands
        gk = gear(0, 0, p['R'], p['teeth'], p['root'], 0, rot=p['rot'], fillet=p['R'] * 0.02)
        gk = transform(gk, sc, Sz / 2, Sz / 2)
        body = path_el(gk.difference(Ld), colors['gear'])
    else:
        body = merge_by_color([(G, colors['gear']), (Ld, colors['loader'])])
    return svg_doc(Sz, Sz, body, 'Impact Utilaje')


def main():
    color = dict(gear=Y, loader=K, type=K, bar_a=Y, bar_b=K)
    files = {
        'v5-color.svg': lockup(color),
        'v5-mono-black.svg': lockup(dict(gear=K, loader=K, type=K, bar_a=K, bar_b=None)),
        'v5-reverse.svg': lockup(dict(gear=Y, loader=WH, type=WH, bar_a=Y, bar_b=None)),
    }
    out = {n: s for n, (s, _) in files.items()}
    out['v5-icon.svg'] = icon(dict(gear=Y, loader=K))
    out['v5-icon-reverse.svg'] = icon(dict(gear=Y, loader=WH))
    out['v5-icon-mono-black.svg'] = icon(dict(gear=K, loader=K))
    out['v5-icon-negativ.svg'] = icon(dict(gear=Y), knockout=True)
    for name, svg in out.items():
        with open(os.path.join(HERE, name), 'w') as f:
            f.write(svg)
        print('wrote', name, len(svg), 'bytes')
    print('UTILAJE tracking:', round(files['v5-color.svg'][1]['tracking'], 1), 'viewBox', files['v5-color.svg'][1]['vb'])


if __name__ == '__main__':
    main()
