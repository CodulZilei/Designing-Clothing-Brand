#!/usr/bin/env python3
"""Generator pentru ilustrația master a încărcătorului frontal (wheel loader).

Desen original, geometric, vedere laterală, orientat spre dreapta (cupa în dreapta).
Trei niveluri de detaliu pe același viewBox 0 0 520 320, linia solului la y=300:
  loader-detaliat.svg  - suprafețe mari (firmă, autovehicule)
  loader-simplu.svg    - varianta implicită pentru logo
  loader-micro.svg     - 16-48 px

Rulare:  python3 assets/loader_gen.py
Necesită shapely (pip install shapely) pentru operațiile booleene.
Toate golurile sunt găuri reale (fill-rule evenodd + winding opus), nu forme albe.
"""
import json
import math
import os
import sys

sys.path.insert(0, '/home/user/Designing-Clothing-Brand/impact-utilaje/tools')

from shapely.geometry import Polygon, Point, LineString, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
VB_W, VB_H = 520, 320
GROUND = 300
INK = '#111111'
QS = 32  # segmente pe sfert de cerc

# ---------------------------------------------------------------- geometrie
R = 52                        # raza roții (ambele roți egale)
RW = (136.0, GROUND - R)      # centrul roții spate
FW = (330.0, GROUND - R)      # centrul roții față
GAP = {'detaliat': 11.0, 'simplu': 14.5, 'micro': 18.0}   # inel liber în jurul anvelopei


def circle(c, r):
    return Point(c).buffer(r, quad_segs=QS)


def bar(pts, w, cap='round'):
    """Bară groasă de-a lungul unei polilinii (lățime w)."""
    return LineString(pts).buffer(w / 2, quad_segs=QS, cap_style=cap, join_style='round')


def rounded(poly, r_out=0.0, r_in=0.0):
    """Rotunjește colțurile convexe (r_out) și concave (r_in)."""
    g = poly
    if r_out:
        g = g.buffer(-r_out, quad_segs=QS, join_style='round').buffer(r_out, quad_segs=QS, join_style='round')
    if r_in:
        g = g.buffer(r_in, quad_segs=QS, join_style='round').buffer(-r_in, quad_segs=QS, join_style='round')
    return g


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def wheel(c, level):
    """Roata: anvelopă + jantă + butuc, cu găuri reale."""
    tire = circle(c, R)
    if level == 'detaliat':
        # câteva crestături de profil, radiale și late (stolli de anvelopă)
        cuts = []
        n = 10
        for i in range(n):
            a = 2 * math.pi * i / n + math.pi / n
            ca, sa = math.cos(a), math.sin(a)
            tx, ty = -sa, ca
            w, dpt = 11.0, 7.0
            r0, r1 = R - dpt, R + 6
            p = lambda r, off: (c[0] + ca * r + tx * off, c[1] + sa * r + ty * off)
            cuts.append(Polygon([p(r0, -w / 2), p(r0, w / 2), p(r1, w / 2), p(r1, -w / 2)]))
        tire = tire.difference(unary_union(cuts))
        tire = tire.difference(circle(c, 33))          # interiorul anvelopei = janta (gol)
        hub = circle(c, 22).difference(circle(c, 7))   # butuc cu gaura axului
        return unary_union([tire, hub])
    if level == 'simplu':
        tire = tire.difference(circle(c, 31))
        hub = circle(c, 16)
        return unary_union([tire, hub])
    # micro: roată plină cu un punct de butuc decupat
    return tire.difference(circle(c, 18))


# puncte cheie comune (aceleași proporții la toate nivelurile)
PIVOT = (264, 170)      # pivotul brațului pe turnul șasiului față
BEND = (366, 176)       # cotul brațului (deasupra roții față)
BPIN = (432, 258)       # bolțul cupei
CYL0 = (252, 146)       # baza cilindrului de basculare
CRANK_TOP = (348, 126)  # vârful pârghiei (bellcrank)
CRANK_PIV = (364, 168)  # pivotul pârghiei pe braț
CRANK_BOT = (388, 188)  # capătul de jos al pârghiei
BRACKET = (428, 204)    # urechea de sus a cupei
FLOOR_Y = 286           # fundul cupei (cupa ușor ridicată)


def bucket_poly():
    top_back = (420, 196)
    heel = (440, FLOOR_Y)
    back = bezier(top_back, (400, 220), (400, 280), heel, 24)
    edge = (494, FLOOR_Y)      # muchia tăietoare
    lip = (452, 192)           # buza de sus (spill guard)
    return Polygon(back + [edge, (497, FLOOR_Y - 6), lip])


def teeth_poly(n, x0, x1, depth):
    """Dinți în dinte de fierăstrău sub muchia tăietoare, cu vârful spre înainte."""
    step = (x1 - x0) / n
    pts = [(x0, FLOOR_Y - 2)]
    for i in range(n):
        xa = x0 + i * step
        pts += [(xa, FLOOR_Y), (xa + step * 0.80, FLOOR_Y + depth), (xa + step, FLOOR_Y)]
    pts += [(x1, FLOOR_Y - 2)]
    return Polygon(pts)


def build(level):
    gap = GAP[level]
    parts = []

    # ---- corp spate: contragreutate + capotă motor (coboară spre spate) + șasiu spate
    body = Polygon([(150, 152), (42, 166), (24, 186), (24, 246), (60, 256), (120, 262),
                    (240, 266), (240, 206), (150, 206)])
    body = rounded(body, r_out=10)
    parts.append(body)

    # ---- cabina ROPS
    cab = Polygon([(146, 208), (152, 114), (230, 114), (242, 208)])
    roof = rounded(box(141, 100, 236, 116), r_out=5)
    parts.append(unary_union([cab, roof]))

    # ---- șasiu față + turnul brațului
    tower = Polygon([(234, 266), (234, 160), (244, 140), (262, 136), (280, 162),
                     (292, 210), (292, 266)])
    parts.append(rounded(tower, r_out=8))

    # ---- brațul (boom): pivot pe turn, trece peste roata față, coboară la cupă
    boom_w = {'detaliat': 24, 'simplu': 26, 'micro': 32}[level]
    parts.append(bar([PIVOT, (320, 168), BEND, BPIN], boom_w))

    # ---- cupa
    parts.append(rounded(bucket_poly(), r_out=4))

    # ---- legătura de basculare (Z-bar): cilindru + pârghie + tijă
    if level in ('detaliat', 'simplu'):
        if level == 'detaliat':
            barrel, rod, crank_w, link_w = 20, 11, 16, 13
        else:
            barrel, rod, crank_w, link_w = 22, 15, 18, 15
        mid = (CYL0[0] + (CRANK_TOP[0] - CYL0[0]) * 0.55, CYL0[1] + (CRANK_TOP[1] - CYL0[1]) * 0.55)
        parts.append(bar([CYL0, mid], barrel))
        parts.append(bar([mid, CRANK_TOP], rod))
        parts.append(bar([CRANK_TOP, CRANK_PIV, CRANK_BOT], crank_w))
        parts.append(bar([CRANK_BOT, BRACKET], link_w))

    # ---- dinții cupei (pe muchia tăietoare)
    if level == 'detaliat':
        parts.append(teeth_poly(4, 442, 500, 11))
    elif level == 'simplu':
        parts.append(teeth_poly(4, 442, 500, 12))

    # ---- țeava de eșapament pe capotă (doar detaliat)
    if level == 'detaliat':
        parts.append(rounded(box(108, 142, 120, 162), r_out=3))

    shape = unary_union(parts)

    # ---- spațiu liber în jurul roților (inel negativ)
    for c in (RW, FW):
        shape = shape.difference(circle(c, R + gap))

    # ---- articulația: crestătură în V între șasiul spate și cel față
    if level != 'micro':
        hw = 11 if level == 'detaliat' else 14
        v = Polygon([(237 - hw, 272), (237, 238), (237 + hw, 272)])
        shape = shape.difference(v)

    # ---- ferestrele cabinei
    if level == 'detaliat':
        w1 = Polygon([(164, 128), (186, 128), (186, 160), (162, 160)])
        w2 = Polygon([(198, 128), (216, 128), (224, 194), (198, 194)])
        shape = shape.difference(rounded(unary_union([w1, w2]), r_out=3))
    elif level == 'simplu':
        w1 = Polygon([(166, 131), (184, 131), (184, 160), (164, 160)])
        w2 = Polygon([(199, 131), (214, 131), (221, 190), (199, 190)])
        shape = shape.difference(rounded(unary_union([w1, w2]), r_out=3))
    else:
        w = Polygon([(168, 132), (214, 132), (220, 182), (168, 182)])
        shape = shape.difference(rounded(w, r_out=4))

    # ---- grila motorului (fante)
    if level == 'detaliat':
        slots = [rounded(box(40, y, 72, y + 10), r_out=4.9) for y in (184, 202, 220)]
        shape = shape.difference(unary_union(slots))

    # ---- roțile
    shape = unary_union([shape, wheel(RW, level), wheel(FW, level)])
    return shape


# ---------------------------------------------------------------- export
def fmt(v):
    s = f"{v:.2f}".rstrip('0').rstrip('.')
    return '0' if s == '-0' else s


def ring_d(coords):
    pts = list(coords)
    if pts[0] == pts[-1]:
        pts = pts[:-1]
    return 'M' + ' L'.join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + ' Z'


def to_d(geom):
    geom = geom.simplify(0.05, preserve_topology=True)
    polys = [geom] if isinstance(geom, Polygon) else list(geom.geoms)
    out = []
    for p in polys:
        p = orient(p, 1.0)   # contur exterior și găuri cu sens opus
        out.append(ring_d(p.exterior.coords))
        for i in p.interiors:
            out.append(ring_d(i.coords))
    return ' '.join(out)


def svg(d, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VB_W} {VB_H}">\n'
            f'  <title>{title}</title>\n'
            f'  <path fill="{INK}" fill-rule="evenodd" d="{d}"/>\n'
            f'</svg>\n')


TITLES = {
    'detaliat': 'Impact Utilaje — încărcător frontal, nivel detaliat',
    'simplu': 'Impact Utilaje — încărcător frontal, nivel simplu',
    'micro': 'Impact Utilaje — încărcător frontal, nivel micro',
}


def main():
    paths = {}
    for level in ('detaliat', 'simplu', 'micro'):
        g = build(level)
        d = to_d(g)
        paths[level] = d
        with open(os.path.join(HERE, f'loader-{level}.svg'), 'w', encoding='utf-8') as f:
            f.write(svg(d, TITLES[level]))
        print(level, 'bounds', [round(v, 1) for v in g.bounds], 'len', len(d))
    return paths


if __name__ == '__main__':
    main()
