#!/usr/bin/env python3
"""v4 „Tipografic dinamic” — generator.

Wordmark italic greu, fără utilaj: IMPACT dominant (Archivo Black Italic), C-ul
înlocuit de o roată dințată deschisă spre dreapta, cu tăietura terminalelor pe
unghiul italicului (10°). Dedesubt UTILAJE (aceeași familie, spațiere largă) și o
bară de viteză galbenă: dungile de avertizare devin bare înclinate pe același
unghi, legate de bara plină la un capăt.

Alinieri: marginea stângă a rândului 2 stă pe prelungirea înclinată a muchiei
stângi a lui I; marginea dreaptă a barei stă pe prelungirea înclinată a
terminalului drept al barei lui T. Toate golurile sunt găuri reale (o singură
cale per culoare, uniune/diferență cu skia-pathops).

Rulare:  python3 generate_v4.py            -> fișierele finale
         python3 generate_v4.py --sketch D -> variante de studiu în D
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, '/home/user/Designing-Clothing-Brand/impact-utilaje/tools')
from v4_lib import (Y, K, W, P, union, diff, inter, poly, rect, circle, translate,  # noqa: E402
                    glyph_run, gear_ring, svg_doc, path_el, cap_height)

ARCHIVO_I = 'Archivo-BlackItalic.ttf'
BARLOW_I = 'BarlowCondensed-ExtraBoldItalic.ttf'
ANGLE = {ARCHIVO_I: 10.0, BARLOW_I: 7.0}


def band_x(path, y0, y1):
    """(xmin, xmax) of `path` inside the horizontal band y0..y1."""
    b = inter(path, rect(-1e5, y0, 1e5, y1)).bounds
    return b[0], b[2]


def gear_c(cx, cy, r_tip, r_root, r_hole, teeth, rotate, d_cut, t, tip=0.40, base=0.58):
    """C-shaped gear: ring (root circle minus hole) cut by an italic line
    x = cx + d_cut - (y - cy)*t (everything right of it removed); only teeth that
    lie entirely left of the cut (with a margin) are kept, so no tooth slivers."""
    def keep(x, y, m):
        return x < cx + d_cut - (y - cy) * t - m

    big = 4 * r_tip
    cut = poly([(cx + d_cut + big * t, cy - big), (cx + big * 3, cy - big),
                (cx + big * 3, cy + big), (cx + d_cut - big * t, cy + big)])
    ring = diff(diff(circle(cx, cy, r_root), circle(cx, cy, r_hole)), cut)
    pitch = 2 * math.pi / teeth
    rot = math.radians(rotate) - math.pi / 2
    teeth_p = []
    margin = 0.35 * (r_tip - r_root)
    for i in range(teeth):
        c = rot + i * pitch
        pts = []
        for ang, r in ((c - pitch * base / 2, r_root - 2), (c - pitch * tip / 2, r_tip),
                       (c + pitch * tip / 2, r_tip), (c + pitch * base / 2, r_root - 2)):
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        if all(keep(x, y, margin) for x, y in pts):
            teeth_p.append(poly(pts))
    return union(ring, *teeth_p)


# optical spacing for the tracked UTILAJE, per gap U-T, T-I, I-L, L-A, A-J, J-E
# (x cap height) — same values as the approved v3 wordmark
UTILAJE_OPTICAL = (-0.10, -0.12, 0.0, -0.22, -0.17, 0.0)

DEFAULT = dict(
    font=ARCHIVO_I, font2=ARCHIVO_I,
    S=1000.0,            # IMPACT size (em)
    # gear-C, in fractions of IMPACT cap height H
    r_tip=0.60, r_root=0.50, r_hole=0.19, teeth=10, rotate='gap', d_cut=0.12,
    c_dx=0.0,             # extra shift of the gear-C (fraction of H)
    t_dx=-0.25,            # extra shift of the T
    a_dx=0.0,            # extra shift of the gear-C+T relative to A (moves both)
    cap2=0.36,           # UTILAJE cap height / H
    track2=260,          # UTILAJE tracking (thousandths of em)
    gap_lines=0.20,      # clear gap between line 1 baseline and line 2 cap top / H
    layout='left',       # 'right': UTILAJE + bar at right ; 'left': bar at left
    bar_gap=0.62,        # gap UTILAJE-bar, in UTILAJE cap heights
    gap_gear=0.08,       # min clear gap gear bottom -> line 2 cap top / H
    stripe_ws=(0.36, 0.48, 0.60), stripe_gap=0.32,   # in line-2 cap heights, outer->inner
    # one-line version
    track_one=40, word_gap=0.38, one_bar_gap=0.16, one_ws=(0.16, 0.16, 0.16), one_sg=0.10,
)


def auto_rotate(r, d, t, teeth, mode):
    """Rotation that makes the teeth symmetric about the C's own axis (the
    bisector of its opening, which the italic cut tilts slightly upward).
    mode 'tooth': a tooth sits on the axis at the back; 'gap': a gap does."""
    def solve(lo, hi):   # r cos(phi) = d - r sin(phi) t  on the outer root circle
        f = lambda p: r * math.cos(p) - d + r * math.sin(p) * t
        for _ in range(60):
            m = (lo + hi) / 2
            if (f(lo) > 0) == (f(m) > 0):
                lo = m
            else:
                hi = m
        return (lo + hi) / 2
    top = solve(-math.pi / 2 - 0.3, 0.0)       # upper terminal (SVG: negative angle)
    bot = solve(0.0, math.pi / 2 + 0.3)
    back = math.degrees((top + bot) / 2) + 180
    pitch = 360 / teeth
    rot = (back + 90) % pitch                  # gear_path: rotate 0 = tooth at -90 deg
    return rot + (pitch / 2 if mode == 'gap' else 0)


def line1(o, base1=None):
    """IMPACT with the gear-C. Cap top at y = 0 unless base1 given."""
    S = o['S']
    f1 = o['font']
    t = math.tan(math.radians(ANGLE[f1]))
    H = cap_height(f1, S)
    base1 = H if base1 is None else base1
    run = glyph_run(f1, 'IMPACT', S, 0, base1)
    by = {g['ch']: g for g in run}
    gC, gT = by['C'], by['T']
    cy = base1 - H / 2
    b = gC['path'].bounds          # sheared oval: bbox centre = centre at mid-height
    cx = (b[0] + b[2]) / 2 + (o['c_dx'] + o['a_dx']) * H
    rot = o['rotate']
    if isinstance(rot, str):
        rot = auto_rotate(o['r_root'] * H, o['d_cut'] * H, t, o['teeth'], rot)
    gear = gear_c(cx, cy, o['r_tip'] * H, o['r_root'] * H, o['r_hole'] * H, o['teeth'],
                  rot, o['d_cut'] * H, t)
    T = translate(gT['path'], (o['t_dx'] + o['a_dx']) * H, 0)
    ink = union(*[g['path'] for g in run if g['ch'] not in 'CT'], T)
    return dict(ink=ink, gear=gear, T=T, by=by, H=H, t=t, base=base1, cx=cx, cy=cy)


def stripes_path(pieces, top, base, t):
    s = (base - top) * t
    return union(*[poly([(a, base), (a + s, top), (b + s, top), (b, base)]) for a, b in pieces])


def build(o):
    """Two-line lockup. Returns dict with paths ink (black type) and acc (yellow)."""
    L = line1(o)
    H, t, base1 = L['H'], L['t'], L['base']
    # ---- alignment lines (x as a function of y, slanted at the italic angle)
    I = L['by']['I']['path']
    ymid = base1 - H / 2
    xIl, _ = band_x(I, ymid - 2, ymid + 2)
    left = lambda y: xIl - (y - ymid) * t
    _, xTr = band_x(L['T'], 0, 0.05 * H)
    yTr = 0.025 * H
    right = lambda y: xTr - (y - yTr) * t

    # ---- line 2
    f2 = o['font2']
    c2 = o['cap2'] * H
    S2 = o['S'] * c2 / cap_height(f2, o['S'])
    top2 = base1 + o['gap_lines'] * H
    if L['gear'].bounds[3] > base1:
        top2 = max(top2, L['gear'].bounds[3] + o['gap_gear'] * H)
    base2 = top2 + c2
    run2 = glyph_run(f2, 'UTILAJE', S2, 0, base2, tracking=o['track2'],
                     extra=[v * c2 for v in UTILAJE_OPTICAL])
    uti = union(*[g['path'] for g in run2])
    ym2 = base2 - c2 * 0.55
    ws = [w * c2 for w in o['stripe_ws']]
    sg = o['stripe_gap'] * c2
    if o['layout'] == 'right':
        xUl, _ = band_x(run2[0]['path'], ym2 - 2, ym2 + 2)
        uti = translate(uti, left(ym2) - xUl, 0)
        xE_top = band_x(uti, top2, top2 + 0.15 * c2)[1]
        xE_bot = band_x(uti, base2 - 0.15 * c2, base2)[1]
        x0_bot = max(xE_bot, xE_top - c2 * t) + o['bar_gap'] * c2
        xs = right(base2)
        pieces = []
        for w in ws:
            pieces.append((xs - w, xs))
            xs -= w + sg
        pieces.append((x0_bot, xs))
    else:
        _, xEr = band_x(run2[-1]['path'], ym2 - 2, ym2 + 2)
        uti = translate(uti, right(ym2) - xEr, 0)
        xU_top = band_x(uti, top2, top2 + 0.15 * c2)[0]
        xU_bot = band_x(uti, base2 - 0.15 * c2, base2)[0]
        x1_bot = min(xU_bot, xU_top - c2 * t) - o['bar_gap'] * c2
        xs = left(base2)
        pieces = []
        for w in ws:
            pieces.append((xs, xs + w))
            xs += w + sg
        pieces.append((xs, x1_bot))
    bars = stripes_path(pieces, top2, base2, t)
    return dict(ink=union(L['ink'], uti), acc=union(L['gear'], bars), gear=L['gear'], H=H)


def build_oneline(o):
    """IMPACT UTILAJE on one line, same cap height; three speed bars lead in at the left."""
    L = line1(o)
    H, t, base1 = L['H'], L['t'], L['base']
    run2 = glyph_run(o['font'], 'UTILAJE', o['S'], 0, base1, tracking=o['track_one'])
    uti = union(*[g['path'] for g in run2])
    gap = o['word_gap'] * H
    # word space measured along the slant: T crossbar end (top) vs U stem (top)
    _, xTr = band_x(L['T'], 0, 0.05 * H)
    xUl, _ = band_x(uti, 0, 0.05 * H)
    uti = translate(uti, xTr + gap - xUl, 0)
    # speed bars before the I, same height as the caps
    ymid = base1 - H / 2
    xIl, _ = band_x(L['by']['I']['path'], ymid - 2, ymid + 2)
    x_end = xIl - (base1 - ymid) * t - o['one_bar_gap'] * H   # at baseline
    ws = [w * H for w in o['one_ws']]
    pieces = []
    xs = x_end
    for w in ws:
        pieces.append((xs - w, xs))
        xs -= w + o['one_sg'] * H
    bars = stripes_path(pieces, 0, base1, t)
    return dict(ink=union(L['ink'], uti), acc=union(L['gear'], bars), H=H)


def build_icon(o):
    L = line1(o)
    return dict(acc=L['gear'], H=L['H'])


def fit_vb(paths, pad_frac=0.04):
    xs0, ys0, xs1, ys1 = [], [], [], []
    for p in paths:
        b = p.bounds
        xs0.append(b[0]); ys0.append(b[1]); xs1.append(b[2]); ys1.append(b[3])
    x0, y0, x1, y1 = min(xs0), min(ys0), max(xs1), max(ys1)
    pad = pad_frac * (x1 - x0)
    return (round(x0 - pad, 2), round(y0 - pad, 2), round(x1 - x0 + 2 * pad, 2), round(y1 - y0 + 2 * pad, 2))


def write(path, layers, title, vb=None):
    vb = vb or fit_vb([p for p, _ in layers])
    body = ''.join(path_el(p, c) for p, c in layers)
    with open(path, 'w') as fh:
        fh.write(svg_doc(vb, body, title))


def sketches(out):
    os.makedirs(out, exist_ok=True)
    variants = {
        'r-tooth': dict(rotate='tooth'),
        'r-gap': dict(rotate='gap'),
        'r-zero': dict(rotate=0.0),
    }
    for k, v in variants.items():
        o = dict(DEFAULT, **v)
        b = build(o)
        write(f'{out}/{k}.svg', [(b['ink'], K), (b['acc'], Y)], k)


TITLE = 'Impact Utilaje'


def icon_vb(path, pad_frac=0.08):
    x0, y0, x1, y1 = path.bounds
    side = max(x1 - x0, y1 - y0) * (1 + 2 * pad_frac)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (round(cx - side / 2, 2), round(cy - side / 2, 2), round(side, 2), round(side, 2))


def main():
    o = dict(DEFAULT)
    b = build(o)
    vb = fit_vb([b['ink'], b['acc']])
    write(f'{HERE}/v4-color.svg', [(b['ink'], K), (b['acc'], Y)], TITLE, vb)
    write(f'{HERE}/v4-mono-black.svg', [(union(b['ink'], b['acc']), K)], TITLE, vb)
    write(f'{HERE}/v4-reverse.svg', [(b['ink'], W), (b['acc'], Y)], TITLE, vb)
    one = build_oneline(o)
    write(f'{HERE}/v4-oneline.svg', [(one['ink'], K), (one['acc'], Y)], TITLE)
    ic = build_icon(o)
    write(f'{HERE}/v4-icon.svg', [(ic['acc'], Y)], TITLE, icon_vb(ic['acc']))


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '--sketch':
        sketches(sys.argv[2])
    else:
        main()
