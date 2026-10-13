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
GAP = {'detaliat': 11.0, 'simplu': 14.5, 'micro': 20.0}   # inel liber în jurul anvelopei


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
    """Roata: anvelopă groasă + jantă + butuc, cu găuri reale.
    Anvelopa e masivă (jantă mică), ca la un încărcător real de ~20 t."""
    tire = circle(c, R)
    if level == 'detaliat':
        # câteva crestături de profil rotunjite (stolli de cauciuc, nu dinți de roată dințată)
        bites = []
        n, w, dpt = 10, 11.0, 7.0
        for i in range(n):
            a = 2 * math.pi * i / n + math.pi / n
            ca, sa = math.cos(a), math.sin(a)
            tx, ty = -sa, ca
            p = lambda r, off: (c[0] + ca * r + tx * off, c[1] + sa * r + ty * off)
            rc = R + w / 2 - dpt
            bites.append(circle(p(rc, 0), w / 2).union(
                Polygon([p(rc, -w / 2), p(rc, w / 2), p(R + 8, w / 2), p(R + 8, -w / 2)])))
        tire = tire.difference(unary_union(bites))
        tire = tire.difference(circle(c, 29))          # janta (gol)
        hub = circle(c, 19).difference(circle(c, 6))   # butuc cu gaura axului
        return unary_union([tire, hub])
    if level == 'simplu':
        tire = tire.difference(circle(c, 30))
        return unary_union([tire, circle(c, 15)])
    # micro: roată plină cu un punct de butuc decupat
    return tire.difference(circle(c, 18))


# puncte cheie comune (aceleași proporții la toate nivelurile)
PIVOT = (268, 176)      # pivotul brațului pe turnul șasiului față
BPIN = (438, 258)       # bolțul cupei
# axa brațului: urcă ușor peste roata față (formă de banană), apoi coboară la cupă
BOOM_KEYS = [PIVOT, (300, 174), (336, 172), (372, 177), (404, 214), BPIN]
# în micro brațul e mai gros, așa că axa lui stă cu câțiva pixeli mai sus peste anvelopă
BOOM_KEYS_MICRO = [PIVOT, (300, 170), (336, 167), (370, 173), (404, 214), BPIN]
CYL0 = (260, 140)       # baza cilindrului de basculare (pe turn)
CRANK_TOP = (350, 126)  # vârful pârghiei (bellcrank)
CRANK_PIV = (366, 174)  # pivotul pârghiei pe braț
BRACKET = (432, 202)    # urechea de sus a cupei
FLOOR_Y = 286           # fundul cupei (cupa ușor ridicată)


def catmull(keys, n=12):
    """Curbă Catmull-Rom netedă prin punctele cheie."""
    pts = [keys[0]] + list(keys) + [keys[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t +
                                    (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(keys[-1])
    return out


def bucket_poly():
    top_back = (424, 196)
    heel = (440, FLOOR_Y)
    back = bezier(top_back, (403, 220), (400, 282), heel, 24)
    lip = (456, 192)           # buza de sus (spill guard)
    return Polygon(back + [(TEETH_X1, FLOOR_Y), lip])


TEETH_X0, TEETH_X1 = 440, 498


def teeth_poly(n, depth):
    """Dinți de fierăstrău sub muchia tăietoare, cu vârful spre înainte (ca în logo-ul original)."""
    x0, x1 = TEETH_X0, TEETH_X1
    step = (x1 - x0) / n
    pts = [(x0, FLOOR_Y - 3)]
    for i in range(n):
        xa = x0 + i * step
        pts += [(xa, FLOOR_Y), (xa + step, FLOOR_Y + depth)]
    pts += [(x1, FLOOR_Y - 3)]
    return Polygon(pts)


BOOM_W = {'detaliat': 24, 'simplu': 26, 'micro': 32}


def build(level, debug=None):
    gap = GAP[level]
    parts = []

    # ---- corp spate: contragreutate + capotă motor (coboară spre spate) + șasiu spate
    body = Polygon([(150, 152), (42, 166), (24, 186), (24, 246), (60, 256), (120, 262),
                    (240, 266), (240, 206), (150, 206)])
    parts.append(rounded(body, r_out=10))

    # ---- cabina ROPS (acoperiș cu streașină; în micro fără streașină)
    if level == 'micro':
        parts.append(rounded(Polygon([(146, 208), (150, 100), (234, 100), (242, 208)]), r_out=6))
    else:
        cab = Polygon([(146, 208), (152, 114), (230, 114), (242, 208)])
        roof = rounded(box(141, 100, 236, 116), r_out=5)
        parts.append(unary_union([cab, roof]))

    # ---- șasiu față + turnul brațului (în micro turnul se oprește la pivot)
    if level == 'micro':
        tower = Polygon([(232, 266), (232, 160), (262, 158), (292, 200), (292, 266)])
    else:
        tower = Polygon([(234, 266), (231, 132), (266, 130), (276, 142), (277, 168), (330, 178), (330, 266)])
    parts.append(rounded(tower, r_out=8))

    # ---- brațul (boom)
    boom = bar(catmull(BOOM_KEYS_MICRO if level == 'micro' else BOOM_KEYS), BOOM_W[level])
    parts.append(boom)

    # ---- cupa
    parts.append(rounded(bucket_poly(), r_out=4))

    # ---- legătura de basculare (Z-bar): cilindru + pârghie; tija de jos e lipită de braț
    if level in ('detaliat', 'simplu'):
        barrel, rod, crank_w = (20, 12, 17) if level == 'detaliat' else (20, 15, 19)
        mid = (CYL0[0] + (CRANK_TOP[0] - CYL0[0]) * 0.55, CYL0[1] + (CRANK_TOP[1] - CYL0[1]) * 0.55)
        cyl = unary_union([bar([CYL0, mid], barrel), bar([mid, CRANK_TOP], rod)])
        crank = bar([CRANK_TOP, CRANK_PIV], crank_w)
        link = rounded(Polygon([CRANK_PIV, (396, 186), BRACKET, (438, 232), (404, 214), (372, 180)]), r_out=3)
        parts += [cyl, crank, link]
        if debug is not None:
            debug['cyl'], debug['boom'] = cyl, boom

    # ---- dinții cupei (pe muchia tăietoare)
    if level == 'detaliat':
        parts.append(teeth_poly(4, 11))
    elif level == 'simplu':
        parts.append(teeth_poly(4, 12))

    # ---- țeava de eșapament pe capotă (doar detaliat)
    if level == 'detaliat':
        parts.append(rounded(box(108, 142, 120, 162), r_out=3))

    shape = unary_union(parts)
    # rotunjire fină a colțurilor concave (îmbinări curate între piese)
    shape = rounded(shape, r_in=3.0)

    # ---- spațiu liber în jurul roților (inel negativ)
    for c in (RW, FW):
        shape = shape.difference(circle(c, R + gap))

    # ---- fanta dintre cabină și turnul șasiului față (se vede cerul printre ele, ca la utilajul real)
    if level != 'micro':
        sw = 11.0 if level == 'detaliat' else 15.0
        cab_front = lambda y: 230 + (y - 114) * 12 / 94      # muchia frontală a cabinei
        slot = bar([(cab_front(126) + sw / 2, 126), (cab_front(194) + sw / 2, 194)], sw)
        shape = shape.difference(slot)

    # ---- articulația: crestătură în V (vârf rotunjit) între șasiul spate și cel față
    if level != 'micro':
        hw = 11 if level == 'detaliat' else 14
        v = Polygon([(237 - hw, 276), (237, 236), (237 + hw, 276)])
        shape = shape.difference(v.buffer(1.5, quad_segs=QS, join_style='round'))

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
        w = Polygon([(172, 126), (212, 126), (215, 164), (172, 164)])
        shape = shape.difference(rounded(w, r_out=4))

    # ---- detalii negative doar la nivelul detaliat: grila motorului + bolțuri
    if level == 'detaliat':
        slots = [rounded(box(43, y, 66, y + 10), r_out=4.9) for y in (180, 200, 220)]
        pins = [circle(PIVOT, 5), circle(CRANK_PIV, 5)]
        shape = shape.difference(unary_union(slots + pins))

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
