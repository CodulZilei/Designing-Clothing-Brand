#!/usr/bin/env python3
"""v3 'Monograma IU' — final generator.

The symbol: a black I next to a yellow U whose bowl is half of a gear
(the yellow gear from the original logo becomes the bottom of the U).
Lockup: symbol + two-line wordmark, IMPACT (Archivo Black) over UTILAJE
(Archivo Black, smaller, tracked so both lines have exactly the same ink width).

Run:  python3 generate_v3.py      (writes the SVGs next to this script)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from v3_geom import (PALETTE, circle, path_el, rect, rrect, soften_inner, svg_doc,  # noqa: E402
                     text_geom, text_glyphs, tooth, transform, type_path, union)

Y, K, WH = PALETTE['yellow'], PALETTE['black'], PALETTE['white']
FONT = 'ArchivoBlack-Regular.ttf'

# ------------------------------------------------------------------ symbol
P = dict(
    H=720,          # cap height of the I and the U (top of stems to baseline)
    s=200,          # stem weight, same for the I and both arms of the U
    gap=105,        # space between I and U
    W=640,          # outer width of the U
    teeth=(32, 61, 90, 119, 148),  # tooth angles, degrees, y-down (90 = straight down)
    t_len=76,       # tooth length beyond the root circle
    t_base=118,     # tooth width at the root
    t_tip=88,       # tooth width at the tip
    fillet=12,      # radius of the fillets between teeth
)


def symbol(p=P):
    """Return (I, U) shapely geometries; I's top-left corner at (0, 0), baseline at y = H."""
    H, s, gap, W = p['H'], p['s'], p['gap'], p['W']
    I = rect(0, 0, s, H)
    ux0 = s + gap
    R = W / 2
    cx, cy = ux0 + R, H - R
    outer = union(rect(ux0, 0, ux0 + W, cy), circle(cx, cy, R, 96))
    inner = union(rect(ux0 + s, -10, ux0 + W - s, cy), circle(cx, cy, R - s, 96))
    U = outer.difference(inner)
    T = union(*[tooth(cx, cy, a, R - 25, R + p['t_len'], p['t_base'], p['t_tip']) for a in p['teeth']])
    U = union(U, T)
    if p['fillet']:
        U = soften_inner(U, p['fillet'])
    return I, U


def bounds(*gs):
    b = union(*gs).bounds
    return b  # (minx, miny, maxx, maxy)


# ------------------------------------------------------------------ wordmark
# optical spacing for the tracked second line, per gap U-T, T-I, I-L, L-A, A-J, J-E (x cap height)
UTILAJE_OPTICAL = (-0.10, -0.12, 0.0, -0.22, -0.17, 0.0)

def wordmark(cap1, line_gap, cap2):
    """IMPACT over UTILAJE, both lines the same ink width; ink starts at x = 0, IMPACT cap top at y = 0.
    Returns measuring geometry (shapely) and draw ops for tools/text2path.outline()."""
    size1 = cap1 / 0.688
    size2 = cap2 / 0.688
    base2 = cap1 + line_gap + cap2
    imp, _ = text_geom(FONT, 'IMPACT', size1, 0, cap1)
    b1 = imp.bounds
    imp = transform(imp, 1, -b1[0], 0)
    w1 = b1[2] - b1[0]
    imp_ops = [(FONT, 'IMPACT', size1, -b1[0], cap1)]

    def ut(tr):
        # wide tracking exaggerates open/diagonal shapes (T, L, A, J): pull those pairs in
        gl, _, xs = text_glyphs(FONT, 'UTILAJE', size2, 0, base2, tr)
        shift, out, xs2 = 0.0, [], []
        for g, x, adj in zip(gl, xs, [0] + list(UTILAJE_OPTICAL)):
            shift += adj * cap2
            out.append(transform(g, 1, shift, 0))
            xs2.append(x + shift)
        return union(*out), xs2

    # ink width is linear in tracking: solve exactly
    (g0, _), (g1, _) = ut(0), ut(100)
    w0 = g0.bounds[2] - g0.bounds[0]
    wa = g1.bounds[2] - g1.bounds[0]
    tr = 100 * (w1 - w0) / (wa - w0)
    uti, xs = ut(tr)
    b2 = uti.bounds
    uti = transform(uti, 1, -b2[0], 0)
    uti_ops = [(FONT, ch, size2, x - b2[0], base2) for ch, x in zip('UTILAJE', xs)]
    return imp, uti, imp_ops, uti_ops, w1, tr


# ------------------------------------------------------------------ layouts
L = dict(
    cap1=0.52,       # IMPACT cap height as a fraction of the symbol cap height
    cap2=0.34,       # UTILAJE cap height
    sym_gap=0.33,    # space between symbol and wordmark, fraction of symbol cap height
    margin=0.04,     # clear space on every side, fraction of total width
)


def lockup(colors, l=L, p=P):
    """colors: dict I, U, t1, t2 -> fill."""
    I, U = symbol(p)
    H = p['H']
    sb = bounds(I, U)
    cap1, cap2 = l['cap1'] * H, l['cap2'] * H
    line_gap = H - cap1 - cap2
    imp, uti, imp_ops, uti_ops, w, tr = wordmark(cap1, line_gap, cap2)
    tx = sb[2] + l['sym_gap'] * H
    imp = transform(imp, 1, tx, 0)
    uti = transform(uti, 1, tx, 0)
    allb = bounds(I, U, imp, uti)
    art_w = allb[2] - allb[0]
    art_h = allb[3] - allb[1]
    m = l['margin'] * art_w / (1 - 2 * l['margin'])
    dx, dy = m - allb[0], m - allb[1]
    vb_w, vb_h = art_w + 2 * m, art_h + 2 * m
    body = merge_by_color([(I, colors['I']), (U, colors['U'])], dx, dy)
    # type: true curves straight from tools/text2path.py (geometry above was only for measuring)
    if colors['t1'] == colors['t2']:
        body += type_path(imp_ops + uti_ops, colors['t1'], tx + dx, dy)
    else:
        body += type_path(imp_ops, colors['t1'], tx + dx, dy) + type_path(uti_ops, colors['t2'], tx + dx, dy)
    return svg_doc(vb_w, vb_h, body, 'Impact Utilaje'), tr


def merge_by_color(parts, dx=0, dy=0):
    order, groups = [], {}
    for g, c in parts:
        if c not in groups:
            groups[c] = []
            order.append(c)
        groups[c].append(transform(g, 1, dx, dy))
    return ''.join(path_el(union(*groups[c]), c) for c in order)


def icon(colors, p=P, margin=0.04, tile=None, tile_scale=0.64):
    """Square icon. tile=None -> transparent; tile=colour -> rounded-square tile behind."""
    I, U = symbol(p)
    b = bounds(I, U)
    w, h = b[2] - b[0], b[3] - b[1]
    S = 1000.0
    if tile is None:
        inner = S * (1 - 2 * margin)
        sc = inner / max(w, h)
        r_tile = None
    else:
        sc = S * tile_scale / max(w, h)
    dx = S / 2 - (b[0] + w / 2) * sc
    # optical centre: the teeth are lighter than the solid stems, so nudge the mark down a touch
    dy = S / 2 - (b[1] + h / 2) * sc + (0.012 * S if tile else 0)
    body = ''
    if tile is not None:
        m = S * margin
        r_tile = (S - 2 * m) * 0.2
        body += path_el(rrect(m, m, S - m, S - m, r_tile, r_tile, r_tile, r_tile), tile)
    body += merge_by_color([(transform(I, sc, dx, dy), colors['I']), (transform(U, sc, dx, dy), colors['U'])])
    return svg_doc(S, S, body, 'Impact Utilaje')


def main():
    files = {
        'v3-color.svg': lockup(dict(I=K, U=Y, t1=K, t2=K))[0],
        'v3-mono-black.svg': lockup(dict(I=K, U=K, t1=K, t2=K))[0],
        'v3-reverse.svg': lockup(dict(I=WH, U=Y, t1=WH, t2=WH))[0],
        'v3-icon.svg': icon(dict(I=K, U=Y)),
        'v3-icon-tile.svg': icon(dict(I=K, U=K), tile=Y),
        # extras: the symbol alone for dark backgrounds and for one-colour use (embroidery, stamps)
        'v3-icon-reverse.svg': icon(dict(I=WH, U=Y)),
        'v3-icon-mono-black.svg': icon(dict(I=K, U=K)),
    }
    for name, svg in files.items():
        with open(os.path.join(HERE, name), 'w') as f:
            f.write(svg)
        print('wrote', name, len(svg), 'bytes')
    print('UTILAJE tracking:', round(lockup(dict(I=K, U=Y, t1=K, t2=K))[1], 1))


if __name__ == '__main__':
    main()
