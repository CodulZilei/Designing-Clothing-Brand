#!/usr/bin/env python3
"""v1 'Rafinat' — originalul rafinat. Generator final.

Compoziția originalului, curățată:
  * wordmark pe două rânduri în Archivo Black, IMPACT peste UTILAJE, cu lățimi egale
    (aceeași funcție wordmark() ca la v3 'Monograma IU', deci același tratament tipografic);
  * simbolul: roata dințată galbenă centrată în spatele cabinei, încărcătorul frontal
    (nivelul 'simplu' din assets/loader.json, importat, nu redesenat) în față; silueta
    utilajului, lărgită, e decupată din roată, deci între ele rămâne un spațiu liber real;
  * bara galbenă pe toată lățimea logo-ului, groasă cât fusul literelor, terminată în
    3 dungi de avertizare (paralelograme cu aceeași înclinare ca tăietura barei).

Toată geometria e construită cu shapely în coordonate SVG (y în jos) și exportată ca
un singur <path> pe culoare cu fill-rule="evenodd": golurile sunt găuri reale.
Textul vine cu curbe adevărate din tools/text2path.py.

Rulare:  python3 generate_v1.py            (scrie SVG-urile lângă script)
         python3 generate_v1.py --sketch   (variante de studiu în ./_sketch, nu se livrează)
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

from gear import gear_path  # noqa: E402
from text2path import outline  # noqa: E402,F401  (folosit prin v3_geom.type_path)
from shapely.geometry import MultiPolygon, Polygon  # noqa: E402
from v3_geom import (PALETTE, circle, path_el, rect, soften_inner, soften_outer,  # noqa: E402
                     svg_doc, transform, type_path, union)
from generate_v3 import wordmark  # noqa: E402  (tratamentul tipografic aprobat la v3)

Y, K, WH = PALETTE['yellow'], PALETTE['black'], PALETTE['white']

# ------------------------------------------------------------------ încărcătorul (master)
with open(os.path.join(ROOT, 'assets', 'loader.json')) as _f:
    LOADER = json.load(_f)
GROUND = LOADER['ground_y']  # 300


def parse_d(d):
    """M/L/Z path (evenodd) -> shapely geometry."""
    g = Polygon()
    for sub in re.findall(r'M[^M]+', d):
        nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', sub)]
        pts = list(zip(nums[0::2], nums[1::2]))
        if len(pts) >= 3:
            g = g.symmetric_difference(Polygon(pts).buffer(0))
    return g


def polys(g):
    if g.is_empty:
        return []
    return [g] if isinstance(g, Polygon) else [p for p in g.geoms if isinstance(p, Polygon)]


def filled(g):
    """Silueta plină (fără ferestre / butuci)."""
    return union(*[Polygon(p.exterior) for p in polys(g)])


# ------------------------------------------------------------------ simbolul
S = dict(
    level='simplu',
    cx=191.0, cy=152.0,     # centrul roții: centrul cabinei (cabina: x 141..242, y 100..208)
    r_out=146.0, r_root=124.0, teeth=12, rotate=-9.0, tip=0.44, base=0.62,
    # rotate=-9: rotația la care decupajul utilajului cade între dinți (niciun dinte ciuntit);
    # găsită numeric: fiecare dinte rămâne fie întreg (>=96%), fie ascuns complet
    hole=82.0,              # gaura centrală încadrează cabina: colțurile acoperișului (r~72) + spațiul liber
    knock=9.0,              # spațiul liber dintre utilaj și roată (unități loader)
    close=16.0,             # închiderea siluetei: umple golurile înguste dintre piese
    soften=2.0,             # rotunjirea colțurilor roții (se potrivește cu utilajul)
)


def gear_geom(p):
    d = gear_path(p['cx'], p['cy'], p['r_out'], p['r_root'], p['teeth'], 0,
                  p['tip'], p['base'], p['rotate'], ndp=3)
    nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', d)]
    g = Polygon(list(zip(nums[0::2], nums[1::2])))
    if p['soften']:
        g = soften_inner(soften_outer(g, p['soften']), p['soften'])
    if p['hole']:
        g = g.difference(circle(p['cx'], p['cy'], p['hole'], 64))
    return g


def symbol(p=S):
    """(gear, loader) în coordonatele desenului master (viewBox 0 0 520 320, sol la y=300)."""
    loader = parse_d(LOADER['paths'][p['level']])
    sil = filled(loader)
    c = p['close']
    sil = sil.buffer(c, join_style='round', quad_segs=16).buffer(-c, join_style='round', quad_segs=16)
    knock = sil.buffer(p['knock'], join_style='round', quad_segs=16)
    gear = gear_geom(p).difference(knock)
    # curăță așchiile: deschidere mică + elimină fragmentele izolate
    gear = gear.buffer(-1.5).buffer(1.5)
    # din roată rămâne vizibil un singur arc (deasupra utilajului); orice dinte rătăcit
    # care s-ar vedea printre roți, sub șasiu, se elimină
    parts = sorted(polys(gear), key=lambda q: -q.area)
    gear = parts[0] if parts else gear
    return gear, loader


# ------------------------------------------------------------------ dungi + bară
def bar_geom(x0, x1, y0, t, stripe_w, gap, slant):
    """Bara de la x0 la x1 (inclusiv dungile), grosime t, partea de sus la y0.
    Dungile sunt paralelograme '/' (sus mutat spre dreapta cu `slant`); capătul din
    dreapta al ultimei dungi atinge exact x1. Returnează (bara, [dunga1, dunga2, dunga3])."""
    y1 = y0 + t

    def para(xl_bottom, w):
        return Polygon([(xl_bottom, y1), (xl_bottom + w, y1), (xl_bottom + w + slant, y0), (xl_bottom + slant, y0)])

    stripes = []
    right_bottom = x1 - slant  # colțul dreapta-jos al ultimei dungi
    for i in range(3):
        xr = right_bottom - i * (stripe_w + gap)
        stripes.append(para(xr - stripe_w, stripe_w))
    stripes = stripes[::-1]
    # bara: capătul stâng drept, capătul drept tăiat cu aceeași înclinare
    xb = right_bottom - 3 * stripe_w - 3 * gap  # colțul dreapta-jos al barei
    bar = Polygon([(x0, y1), (xb, y1), (xb + slant, y0), (x0, y0)])
    return bar, stripes


# ------------------------------------------------------------------ lockup
L = dict(
    cap1=100.0,          # înălțimea majusculelor IMPACT (unitatea de bază)
    cap2_ratio=0.654,    # UTILAJE / IMPACT (ca la v3: 0.34 / 0.52)
    gap_ratio=0.269,     # spațiul dintre rânduri / cap1 (ca la v3: 0.14 / 0.52)
    sym_gap=1.5,         # spațiul wordmark -> simbol, în unități u (u = spațiul dintre rânduri)
    bar_gap=1.0,         # spațiul UTILAJE -> bară, în u
    bar_t='stem2',       # grosimea barei: 'stem1' (fusul lui IMPACT) sau 'stem2' (UTILAJE) sau număr
    overshoot=0.02,      # vârful dinților depășește puțin linia majusculelor (compensare optică)
    stripe_w=1.6,       # lățimea unei dungi, în grosimi de bară
    stripe_gap=0.45,     # spațiul dintre dungi, în grosimi de bară
    slant=0.85,          # înclinarea, în grosimi de bară
    margin=0.04,
)
STEM = 0.321  # fusul lui I în Archivo Black / înălțimea majusculelor (măsurat)


def lockup(colors, l=L, p=S):
    """colors: gear, loader, t1, t2, bar, s_dark, s_light."""
    cap1 = l['cap1']
    cap2 = cap1 * l['cap2_ratio']
    u = cap1 * l['gap_ratio']
    imp, uti, imp_ops, uti_ops, w_word, tr = wordmark(cap1, u, cap2)
    h_word = cap1 + u + cap2  # UTILAJE baseline

    gear, loader = symbol(p)
    sb = union(gear, loader).bounds
    top = sb[1]
    # scalare: solul utilajului pe linia de bază UTILAJE, vârful roții puțin peste linia majusculelor
    sc = (h_word + l['overshoot'] * cap1) / (GROUND - top)
    dy = h_word - GROUND * sc
    dx = w_word + l['sym_gap'] * u - sb[0] * sc
    gear = transform(gear, sc, dx, dy)
    loader = transform(loader, sc, dx, dy)
    right = union(gear, loader).bounds[2]

    bt = {'stem1': STEM * cap1, 'stem2': STEM * cap2}.get(l['bar_t'], l['bar_t'])
    if not isinstance(bt, (int, float)):
        bt = STEM * cap2
    y_bar = h_word + l['bar_gap'] * u
    bar, stripes = bar_geom(0, right, y_bar, bt, l['stripe_w'] * bt, l['stripe_gap'] * bt, l['slant'] * bt)

    allb = union(gear, loader, imp, uti, bar, *stripes).bounds
    art_w, art_h = allb[2] - allb[0], allb[3] - allb[1]
    m = l['margin'] * art_w / (1 - 2 * l['margin'])
    ox, oy = m - allb[0], m - allb[1]
    vb_w, vb_h = art_w + 2 * m, art_h + 2 * m

    parts = [(gear, colors['gear']), (bar, colors['bar']), (stripes[1], colors['s_light']),
             (loader, colors['loader']), (union(stripes[0], stripes[2]), colors['s_dark'])]
    body = merge_by_color(parts, ox, oy)
    if colors['t1'] == colors['t2']:
        body += type_path(imp_ops + uti_ops, colors['t1'], ox, oy)
    else:
        body += type_path(imp_ops, colors['t1'], ox, oy) + type_path(uti_ops, colors['t2'], ox, oy)
    info = dict(tracking=round(tr, 1), scale=round(sc, 4), bar_t=round(bt, 2), u=round(u, 2),
                vb=(round(vb_w, 1), round(vb_h, 1)))
    return svg_doc(vb_w, vb_h, body, 'Impact Utilaje'), info


def merge_by_color(parts, dx=0, dy=0):
    order, groups = [], {}
    for g, c in parts:
        if c not in groups:
            groups[c] = []
            order.append(c)
        groups[c].append(transform(g, 1, dx, dy))
    return ''.join(path_el(union(*groups[c]), c) for c in order)


def icon(colors, p=S, margin=0.04, size=1000.0):
    """Simbolul singur, centrat într-un pătrat (fundal transparent)."""
    gear, loader = symbol(p)
    b = union(gear, loader).bounds
    w, h = b[2] - b[0], b[3] - b[1]
    sc = size * (1 - 2 * margin) / max(w, h)
    dx = size / 2 - (b[0] + w / 2) * sc
    dy = size / 2 - (b[1] + h / 2) * sc
    body = merge_by_color([(transform(gear, sc, dx, dy), colors['gear']),
                           (transform(loader, sc, dx, dy), colors['loader'])])
    return svg_doc(size, size, body, 'Impact Utilaje')


COLOR = dict(gear=Y, loader=K, t1=K, t2=K, bar=Y, s_dark=K, s_light=Y)
MONO = dict(gear=K, loader=K, t1=K, t2=K, bar=K, s_dark=K, s_light=K)
REVERSE = dict(gear=Y, loader=WH, t1=WH, t2=WH, bar=Y, s_dark=WH, s_light=Y)


def write(name, svg, out=HERE):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, name), 'w') as f:
        f.write(svg)


def sketch():
    out = os.path.join(HERE, '_sketch')
    variants = {
        'a': (dict(S), dict(L)),
        'b': (dict(S, cx=191, cy=152, r_out=146, r_root=124, hole=84, teeth=12), dict(L)),
        'r7': (dict(S, rotate=7.0), dict(L)),
        'c': (dict(S), dict(L, cap2_ratio=0.82, bar_t='stem1')),
        'd': (dict(S, cx=191, cy=152, r_out=146, r_root=124, hole=84, teeth=12), dict(L, cap2_ratio=0.82, bar_t='stem1')),
    }
    for k, (p, l) in variants.items():
        svg, info = lockup(COLOR, l, p)
        write(f's-{k}.svg', svg, out)
        write(f's-{k}-icon.svg', icon(COLOR, p), out)
        print(k, info)


def main():
    if '--sketch' in sys.argv:
        sketch()
        return
    files = {
        'v1-color.svg': lockup(COLOR)[0],
        'v1-mono-black.svg': lockup(MONO)[0],
        'v1-reverse.svg': lockup(REVERSE)[0],
        'v1-icon.svg': icon(COLOR),
        # extra: simbolul pe fundal închis și varianta pentru favicon (încărcătorul 'micro', 16-48 px)
        'v1-icon-reverse.svg': icon(dict(gear=Y, loader=WH)),
        'v1-icon-micro.svg': icon(COLOR, dict(S, level='micro', rotate=15.0)),
    }
    for name, svg in files.items():
        write(name, svg)
        print('wrote', name, len(svg), 'bytes')
    print(lockup(COLOR)[1])


if __name__ == '__main__':
    main()
