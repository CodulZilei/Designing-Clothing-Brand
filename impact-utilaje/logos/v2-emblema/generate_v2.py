#!/usr/bin/env python3
"""v2 'Emblemă' — round badge generator.

Helmet stickers, embroidered patches, machine doors, avatars.

Construction (the same in every file):
  * yellow layer  = gear ring (teeth outside) with the lettering, the hex bolts
                    and their washers cut out as REAL holes, plus the loader
                    (assets/loader.json, level "simplu") and a short band of
                    hazard bars under it;
  * black base    = one plain disc under the yellow layer (colour version only).
                    It shows through the holes, so the letters read black on
                    yellow and the centre reads as a black disc. That is how a
                    patch is made (black twill + yellow thread) and it leaves no
                    seams between touching colours.
  mono-black = the yellow layer printed in black; every hole reveals the background.
  reverse    = the yellow layer in yellow with the loader in white, no base disc
               (the dark background fills the centre and the letters).

Lettering: Archivo Black (the wordmark face used in v3), outlined from the font,
shaped with HarfBuzz (kerning), every glyph placed rigidly along the arc by its
advance; spacing is measured on the mid-cap circle so it looks even.

Run:  python3 generate_v2.py      (writes the SVGs next to this script)
"""
import json
import math
import os
import re
import sys

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

ROOT = '/home/user/Designing-Clothing-Brand/impact-utilaje'
sys.path.insert(0, ROOT + '/tools')
from text2path import outline  # noqa: E402  (advances cross-checked against it in check_advances())
from gear import gear_path  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = ROOT + '/fonts/ArchivoBlack-Regular.ttf'
Y, K, WH = '#F2A20A', '#111111', '#FFFFFF'

S = 1000.0                 # square viewBox
CX = CY = S / 2
TITLE = 'Impact Utilaje — emblemă'

# ---------------------------------------------------------------- parameters
B = dict(
    r_tip=460,             # gear tooth tips -> 40 units (4 %) clear space
    r_root=424,            # bottom of the gaps between teeth
    teeth=20, tip=0.44, base=0.62,
    r_in=300,              # inner edge of the ring = edge of the black disc
    fillet=4,              # softening of every gear corner (cut / embroidery friendly)
    # top arc
    top='IMPACT UTILAJE', top_cap=64, top_track=105,
    # optical spacing on top of kerning + tracking, per letter pair, in cap heights
    # (open or diagonal sides - T, L, A, J - look looser once tracked)
    # (the arc squeezes the feet of the top line and the heads of the bottom line, so after this
    # every pair is opened, where needed, to keep at least MIN_W of yellow between letters)
    pairs={'UT': -0.05, 'TI': -0.08, 'LA': -0.06, 'AJ': -0.04, 'CT': -0.03, 'PA': -0.02, 'MP': 0.02},
    # bottom arc: word, bolt, word
    bot=('ȘANTIER', 'ROMÂNIA'), bot_cap=50, bot_track=100, bot_bolt_gap=0.55,  # gap word-bolt, x cap
    bolt_r=28, bolt_hole=10, bolt_r_small=22, bolt_hole_small=7,
    # centre
    loader_level='simplu', loader_w=470,
    band_h=38, band_bars=7, band_bar=32, band_gap=28, band_slant=0.62,  # slant = dx / h
    band_gap_y=16,         # air between tyres and hazard band
    group_dy=0,            # optical nudge of loader + band (positive = down)
)

ICON = dict(
    r_tip=460, r_root=408, teeth=12, tip=0.46, base=0.64, r_in=338, fillet=5,
    loader_level='micro', loader_w=556,
    band_h=46, band_bars=4, band_bar=52, band_gap=44, band_slant=0.62, band_gap_y=22,
    group_dy=0,
)


# ---------------------------------------------------------------- geometry helpers
def circle(cx, cy, r, res=96):
    return Point(cx, cy).buffer(r, quad_segs=res)


def union(*gs):
    return unary_union([g for g in gs if g is not None and not g.is_empty])


def soften(g, r):
    """Round convex and concave corners by r (opening then closing)."""
    if r <= 0:
        return g
    g = g.buffer(-r, join_style='mitre').buffer(r, join_style='round', quad_segs=12)
    return g.buffer(r, join_style='round', quad_segs=12).buffer(-r, join_style='mitre')


def rings_from_d(d):
    """M/L/Z path data -> list of point lists."""
    out = []
    for sub in re.split(r'(?=M)', d.strip()):
        nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', sub)]
        pts = list(zip(nums[0::2], nums[1::2]))
        if len(pts) >= 3:
            out.append(pts)
    return out


def evenodd(rings):
    g = Polygon()
    for r in rings:
        g = g.symmetric_difference(Polygon(r).buffer(0))
    return g


class _FlattenPen(BasePen):
    def __init__(self, glyphset, steps=12):
        super().__init__(glyphset)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            m = 1 - t
            self.cur.append((m ** 3 * p0[0] + 3 * m * m * t * p1[0] + 3 * m * t * t * p2[0] + t ** 3 * p3[0],
                             m ** 3 * p0[1] + 3 * m * m * t * p1[1] + 3 * m * t * t * p2[1] + t ** 3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            m = 1 - t
            self.cur.append((m * m * p0[0] + 2 * m * t * p1[0] + t * t * p2[0],
                             m * m * p0[1] + 2 * m * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.cur) >= 3:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


_TT = TTFont(FONT)
_UPEM = _TT['head'].unitsPerEm
_CAP = _TT['OS/2'].sCapHeight / _UPEM
_GS = _TT.getGlyphSet()
_ORDER = _TT.getGlyphOrder()


def shape_word(text, cap):
    """One item per HarfBuzz cluster: (geometry with baseline y=0 and pen at x=0, advance).
    Kerning is folded into the advances, exactly as text2path.outline() lays them out."""
    size = cap / _CAP
    sc = size / _UPEM
    font = hb.Font(hb.Face(hb.Blob.from_file_path(FONT)))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {'kern': True, 'liga': True})
    clusters = {}
    order = []
    pen_x = 0.0
    for info, p in zip(buf.glyph_infos, buf.glyph_positions):
        pen = _FlattenPen(_GS)
        _GS[_ORDER[info.codepoint]].draw(TransformPen(pen, (sc, 0, 0, -sc, (pen_x + p.x_offset) * sc, -p.y_offset * sc)))
        g = Polygon()
        for c in pen.contours:
            g = g.symmetric_difference(Polygon(c).buffer(0))
        if info.cluster not in clusters:
            clusters[info.cluster] = [Polygon(), pen_x * sc, 0.0]
            order.append(info.cluster)
        cl = clusters[info.cluster]
        cl[0] = cl[0].union(g)
        cl[2] += p.x_advance * sc
        pen_x += p.x_advance
    items = []
    for n, k in enumerate(order):
        g, x, adv = clusters[k]
        end = order[n + 1] if n + 1 < len(order) else len(text)   # uharfbuzz clusters = code point indices
        ch = text[k:end]
        items.append((embroidery_safe(affinity.translate(g, -x, 0)), adv, ch))
    return items, size


MIN_W = 0.012 * 920          # thinnest line or gap allowed: 1.2 % of the badge diameter


def inradius(p, hi=60.0):
    """Radius of the largest circle that fits inside p (bisection on erosion)."""
    lo = 0.0
    for _ in range(14):
        mid = (lo + hi) / 2
        if p.buffer(-mid).is_empty:
            hi = mid
        else:
            lo = mid
    return lo


def embroidery_safe(g, w=MIN_W):
    """Archivo Black is very heavy, so at badge sizes the counters of A, R, Â and the
    accents (comma of Ș, circumflex of Â) drop under the embroidery minimum.
    Open counters that are narrower than w and thicken accents thinner than w,
    by just the missing amount (the letters keep their shape)."""
    r = w / 2 + 0.25
    out = []
    for p in ([g] if g.geom_type == 'Polygon' else list(g.geoms)):
        ir = inradius(Polygon(p.exterior))
        if ir < r and not p.interiors:
            p = p.buffer(r - ir, join_style='round', quad_segs=12)
        for hole in list(p.interiors):
            h = Polygon(hole)
            ir = inradius(h)
            if ir < r:
                # grow the counter towards whichever side has the most ink to spare
                d = r - ir
                best = None
                for dy in (0.0, -d, d, -d / 2, d / 2):
                    q = p.difference(affinity.translate(h.buffer(d, join_style='round', quad_segs=12), 0, dy))
                    thin = q.difference(q.buffer(-r + 0.25).buffer(r - 0.25)).area
                    if best is None or thin < best[0] - 1e-6:
                        best = (thin, q)
                p = best[1]
        out.append(p)
    return unary_union(out)


def check_advances(text, cap):
    """Cross-check: summed cluster advances == text2path.outline() width (same shaping)."""
    items, size = shape_word(text, cap)
    w = sum(it[1] for it in items)
    ref = outline(FONT, text, size)['width']
    assert abs(w - ref) < 0.05, (text, w, ref)
    return w


def hex_bolt(r, hole, res=48):
    """Hex head with a round washer hole; flat side facing up (local coords, centre at 0,0)."""
    hx = Polygon([(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(0, 360, 60)])
    hx = soften(hx, r * 0.12)
    ring = hx.difference(circle(0, 0, hole, res)) if hole else hx
    return hx, ring


def lay_arc(items, track, r_base, r_ref, theta_c, top, extra=None):
    """items: [(geometry or None, advance)]; geometry has baseline y = 0, pen x = 0.
    Places each item rigidly; its advance centre sits on the r_ref circle.
    top=True: reads clockwise over the top, letters point outward.
    top=False: reads counter-clockwise along the bottom, letters point inward.
    extra[i] = additional space after item i.
    Returns (list of placed geometries, (angle_first_edge, angle_last_edge) in degrees)."""
    xs, W = advance_positions(items, track, extra)
    out = []
    for (g, adv), x0 in zip([(it[0], it[1]) for it in items], xs):
        s = x0 + adv / 2 - W / 2
        if top:
            th = math.radians(theta_c) + s / r_ref
            ux, uy = math.cos(th), math.sin(th)
            tx, ty = -uy, ux
            m = [tx, -ux, ty, -uy, CX + r_base * ux, CY + r_base * uy]
        else:
            th = math.radians(theta_c) - s / r_ref
            ux, uy = math.cos(th), math.sin(th)
            tx, ty = uy, -ux
            m = [tx, ux, ty, uy, CX + r_base * ux, CY + r_base * uy]
        if g is not None:
            g = affinity.affine_transform(affinity.translate(g, -adv / 2, 0), m)
        out.append(g)
    half = math.degrees(W / 2 / r_ref)
    return out, (theta_c - half, theta_c + half)


def advance_positions(items, track, extra=None):
    xs, x = [], 0.0
    for i, it in enumerate(items):
        xs.append(x)
        x += it[1]
        if i < len(items) - 1:
            x += track + (extra[i] if extra else 0.0)
    return xs, x


def pair_extra(chars, pairs, cap):
    return [pairs.get(a + b, 0.0) * cap for a, b in zip(chars, chars[1:] + [''])]


def place_at(g, r, theta):
    """Put a local shape (centre 0,0, 'up' = -y) at radius r, angle theta, 'up' pointing outward."""
    th = math.radians(theta)
    ux, uy = math.cos(th), math.sin(th)
    tx, ty = -uy, ux
    return affinity.affine_transform(g, [tx, -ux, ty, -uy, CX + r * ux, CY + r * uy])


# ---------------------------------------------------------------- parts
def gear_ring(p):
    d = gear_path(CX, CY, p['r_tip'], p['r_root'], p['teeth'], tip=p['tip'], base=p['base'], rotate=0, ndp=3)
    g = evenodd(rings_from_d(d))
    g = soften(g, p['fillet'])
    return g.difference(circle(CX, CY, p['r_in']))


_LOADER = json.load(open(ROOT + '/assets/loader.json'))


def loader(level):
    """The master drawing (paths imported verbatim) and its content bbox."""
    return evenodd(rings_from_d(_LOADER['paths'][level])), _LOADER['content_bbox']


def hazard_band(n, w, gap, h, slant):
    """n whole parallelogram bars leaning forward ('/'), local: top-left of the band at (0,0)."""
    dx = h * slant
    bars = []
    for i in range(n):
        x = i * (w + gap)
        bars.append(Polygon([(x, h), (x + dx, 0), (x + dx + w, 0), (x + w, h)]))
    return union(*bars), n * w + (n - 1) * gap + dx


def centre_group(p):
    """Loader standing on the hazard band, centred in the disc. Returns (loader, band)."""
    L, (x0, y0, x1, y1) = loader(p['loader_level'])
    sc = p['loader_w'] / (x1 - x0)
    lh = (y1 - y0) * sc
    band, bw = hazard_band(p['band_bars'], p['band_bar'], p['band_gap'], p['band_h'], p['band_slant'])
    gh = lh + p['band_gap_y'] + p['band_h']
    top = CY - gh / 2 + p['group_dy']
    L = affinity.affine_transform(L, [sc, 0, 0, sc, CX - (x0 + x1) / 2 * sc, top - y0 * sc])
    band = affinity.translate(band, CX - bw / 2, top + lh + p['band_gap_y'])
    return L, band


def neighbour_gaps(glyphs, chars):
    """Closest distance between consecutive letters (on an arc the feet of the top
    line and the heads of the bottom line converge, so this is checked, not assumed)."""
    out = []
    seq = [(g, c) for g, c in zip(glyphs, chars) if g is not None and not g.is_empty]
    for (g1, c1), (g2, c2) in zip(seq, seq[1:]):
        out.append((c1 + c2, round(g1.distance(g2), 1)))
    return out


def open_tight_pairs(glyphs, extra, w=MIN_W + 0.6):
    """Add space after item i wherever letters i and i+1 are closer than w. Returns True if changed."""
    changed = False
    for i in range(len(glyphs) - 1):
        a, b = glyphs[i], glyphs[i + 1]
        if a is None or b is None:
            continue
        d = a.distance(b)
        if d < w:
            extra[i] += (w - d) / 0.85 + 0.2   # the arc passes on ~0.9 of a shift to the tight edge
            changed = True
    return changed


def lettering(p):
    """Top + bottom arcs and the bolts. Returns (cut, fill, info): cut = area removed from the
    ring, fill = what stays yellow inside the cut (the bolt centres)."""
    band_mid = (p['r_root'] + p['r_in']) / 2
    cut, fill = [], []
    pairs = p.get('pairs', {})

    # top: IMPACT UTILAJE, cap height centred on the band, spacing on the mid-cap circle
    items, size = shape_word(p['top'], p['top_cap'])
    check_advances(p['top'], p['top_cap'])
    track = p['top_track'] / 1000 * size
    ex = pair_extra([it[2] for it in items], pairs, p['top_cap'])
    for _ in range(8):
        glyphs, (t0, t1) = lay_arc(items, track, band_mid - p['top_cap'] / 2, band_mid, 270, True, ex)
        if not open_tight_pairs(glyphs, ex):
            break
    cut += [g for g in glyphs if g is not None]
    gaps_top = neighbour_gaps(glyphs, [it[2] for it in items])

    # bottom: ȘANTIER (bolt) ROMÂNIA, letters pointing inward. ROMÂNIA is ~25 units wider than
    # ȘANTIER, so the bolt between them cannot sit at 6 o'clock while the line stays centred.
    # Split the difference: the line turns by half of it (bolt ~1 degree off the axis, the line's
    # ends ~1 degree off symmetric) - both well below what the eye can see.
    w1, size2 = shape_word(p['bot'][0], p['bot_cap'])
    w2, _ = shape_word(p['bot'][1], p['bot_cap'])
    for w in p['bot']:
        check_advances(w, p['bot_cap'])
    track2 = p['bot_track'] / 1000 * size2
    bs = p['bolt_r_small'] * 2 * math.cos(math.radians(30))   # flat-to-flat width of the small bolt
    gap = p['bot_bolt_gap'] * p['bot_cap'] - track2               # track is added on both sides of the slot
    items2 = w1 + [(None, gap, ''), (None, bs, '*'), (None, gap, '')] + w2
    ex2 = pair_extra([it[2] for it in items2], pairs, p['bot_cap'])
    k = [i for i, it in enumerate(items2) if it[2] == '*'][0]
    for _ in range(8):
        xs, W = advance_positions(items2, track2, ex2)
        s_bolt = xs[k] + bs / 2 - W / 2
        theta_c = 90 + 0.5 * math.degrees(s_bolt / band_mid)
        placed, (b0, b1) = lay_arc(items2, track2, band_mid + p['bot_cap'] / 2, band_mid, theta_c, False, ex2)
        if not open_tight_pairs(placed, ex2):
            break
    cut += [g for g in placed if g is not None]
    gaps_bot = neighbour_gaps(placed, [it[2] for it in items2])
    th_bolt = theta_c - math.degrees(s_bolt / band_mid)
    hx, ring = hex_bolt(p['bolt_r_small'], p['bolt_hole_small'])
    cut.append(place_at(hx, band_mid, th_bolt))
    fill.append(place_at(hx.difference(ring), band_mid, th_bolt))

    # side bolts: mirror images of each other, half-way between the arcs (mean of both gaps)
    a = ((t1 - 360 + b0) / 2 + (180 - t0 + 180 - b1) / 2) / 2
    right, left = a, 180 - a
    hx, ring = hex_bolt(p['bolt_r'], p['bolt_hole'])
    for th in (right, left):
        cut.append(place_at(hx, band_mid, th))
        fill.append(place_at(hx.difference(ring), band_mid, th))
    info = dict(top_span=round(t1 - t0, 1), bottom_span=round(b1 - b0, 1),
                side_bolts=(round(right, 1), round(left, 1)), bottom_bolt=round(th_bolt, 2),
                gaps_right=(round(t1 - 360, 1), round(b0, 1)), gaps_left_mirrored=(round(180 - t0, 1), round(180 - b1, 1)),
                tightest_top=sorted(gaps_top, key=lambda v: v[1])[:3], tightest_bottom=sorted(gaps_bot, key=lambda v: v[1])[:3])
    return union(*cut), union(*fill), info


# ---------------------------------------------------------------- export
def _fmt(v):
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s == '-0' else s


def to_d(g, tol=0.12):
    g = g.simplify(tol, preserve_topology=True)
    polys = [g] if isinstance(g, Polygon) else [q for q in getattr(g, 'geoms', []) if isinstance(q, Polygon)]
    out = []
    for q in polys:
        if q.is_empty:
            continue
        q = orient(q, sign=-1.0)
        for ring in [q.exterior] + list(q.interiors):
            cs = list(ring.coords)[:-1]
            out.append('M' + ' L'.join(f'{_fmt(x)} {_fmt(y)}' for x, y in cs) + ' Z')
    return ' '.join(out)


def path_el(g, fill):
    return f'<path fill="{fill}" fill-rule="evenodd" d="{to_d(g)}"/>' if not g.is_empty else ''


def svg_doc(body, title=TITLE):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_fmt(S)} {_fmt(S)}">'
            f'<title>{title}</title>{body}</svg>\n')


def build_badge(p=B):
    ring = gear_ring(p)
    cut, fill, info = lettering(p)
    ring = union(ring.difference(cut), fill)
    L, band = centre_group(p)
    return ring, L, band, info


def build_icon(p=ICON):
    ring = gear_ring(p)
    L, band = centre_group(p)
    return ring, L, band


def write(name, svg):
    with open(os.path.join(HERE, name), 'w') as f:
        f.write(svg)
    print('wrote', name, len(svg), 'bytes')


def main():
    ring, L, band, info = build_badge()
    base = circle(CX, CY, B['r_root'] - 2)          # hidden under the ring, visible through the holes
    yellow = union(ring, L, band)
    write('v2-color.svg', svg_doc(path_el(base, K) + path_el(yellow, Y)))
    write('v2-mono-black.svg', svg_doc(path_el(yellow, K)))
    write('v2-reverse.svg', svg_doc(path_el(union(ring, band), Y) + path_el(L, WH)))

    iring, iL, iband = build_icon()
    ibase = circle(CX, CY, ICON['r_root'] - 2)
    write('v2-icon.svg', svg_doc(path_el(ibase, K) + path_el(union(iring, iL, iband), Y), 'Impact Utilaje — emblemă, simbol'))
    # extras for one-colour and dark-background use of the small symbol
    write('v2-icon-mono-black.svg', svg_doc(path_el(union(iring, iL, iband), K), 'Impact Utilaje — emblemă, simbol'))
    write('v2-icon-reverse.svg', svg_doc(path_el(union(iring, iband), Y) + path_el(iL, WH), 'Impact Utilaje — emblemă, simbol'))
    print('layout:', info)


if __name__ == '__main__':
    main()
