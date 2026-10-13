"""Shared geometry helpers for the v3 'Monograma IU' generator.

Everything is built as shapely geometry in SVG coordinates (y grows downward)
and exported as one <path> per colour with fill-rule="evenodd", so counters and
cut-outs are real holes in the outline (never white shapes painted on top).
"""
import math
import sys

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

sys.path.insert(0, '/home/user/Designing-Clothing-Brand/impact-utilaje/tools')
from text2path import outline  # noqa: E402,F401  (re-exported for the generator)
from gear import gear_path  # noqa: E402,F401

FONTS = '/home/user/Designing-Clothing-Brand/impact-utilaje/fonts'
PALETTE = {
    'yellow': '#F2A20A',
    'black': '#111111',
    'steel': '#4A4F55',
    'concrete': '#E6E4DF',
    'white': '#FFFFFF',
}


# ---------------------------------------------------------------- primitives
def rect(x0, y0, x1, y1):
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def circle(cx, cy, r, res=64):
    return Point(cx, cy).buffer(r, quad_segs=res)


def poly(pts):
    return Polygon(pts)


def arc_pts(cx, cy, r, a0, a1, n=None):
    """Points on an arc from angle a0 to a1 (degrees, y-down so 90 = straight down)."""
    if n is None:
        n = max(4, int(abs(a1 - a0) / 2.5))
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def rrect(x0, y0, x1, y1, tl=0, tr=0, br=0, bl=0):
    """Rectangle with an individual radius per corner."""
    pts = []
    if tl:
        pts += arc_pts(x0 + tl, y0 + tl, tl, 180, 270)
    else:
        pts.append((x0, y0))
    if tr:
        pts += arc_pts(x1 - tr, y0 + tr, tr, 270, 360)
    else:
        pts.append((x1, y0))
    if br:
        pts += arc_pts(x1 - br, y1 - br, br, 0, 90)
    else:
        pts.append((x1, y1))
    if bl:
        pts += arc_pts(x0 + bl, y1 - bl, bl, 90, 180)
    else:
        pts.append((x0, y1))
    return Polygon(pts)


def tooth(cx, cy, ang, r_in, r_out, w_base, w_tip):
    """Trapezoid tooth pointing away from (cx, cy) at angle `ang` (degrees, y-down)."""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    b = (cx + ux * r_in, cy + uy * r_in)
    t = (cx + ux * r_out, cy + uy * r_out)
    return Polygon([
        (b[0] + nx * w_base / 2, b[1] + ny * w_base / 2),
        (t[0] + nx * w_tip / 2, t[1] + ny * w_tip / 2),
        (t[0] - nx * w_tip / 2, t[1] - ny * w_tip / 2),
        (b[0] - nx * w_base / 2, b[1] - ny * w_base / 2),
    ])


def union(*gs):
    return unary_union([g for g in gs if g is not None and not g.is_empty])


def round_corners(g, r):
    """Soften every corner of a shape (outer and inner) by radius r."""
    if r <= 0:
        return g
    return g.buffer(-r, join_style='round', quad_segs=16).buffer(2 * r, join_style='round', quad_segs=16).buffer(-r, join_style='round', quad_segs=16)


def soften_outer(g, r):
    """Round convex corners only (opening = erode then dilate)."""
    return g.buffer(-r, join_style='mitre').buffer(r, join_style='round', quad_segs=16)


def soften_inner(g, r):
    """Round concave corners only (closing = dilate then erode)."""
    return g.buffer(r, join_style='round', quad_segs=16).buffer(-r, join_style='mitre')


# ---------------------------------------------------------------- text as shapely
class _FlattenPen(BasePen):
    def __init__(self, glyphset, steps=10):
        super().__init__(glyphset)
        self.contours = []
        self.cur = []
        self.steps = steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                             mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                             mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.cur) >= 3:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def text_geom(font_file, text, size, x=0.0, y=0.0, tracking=0.0, anchor='start'):
    """Shaped (HarfBuzz, kerned) text as a shapely geometry; baseline at y."""
    glyphs, width, _ = text_glyphs(font_file, text, size, x, y, tracking, anchor)
    return unary_union(glyphs), width


def text_glyphs(font_file, text, size, x=0.0, y=0.0, tracking=0.0, anchor='start'):
    """Like text_geom but returns one geometry per glyph (for optical spacing tweaks)."""
    font_path = f'{FONTS}/{font_file}'
    blob = hb.Blob.from_file_path(font_path)
    font = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {'kern': True, 'liga': True})
    tt = TTFont(font_path)
    upem = tt['head'].unitsPerEm
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    sc = size / upem
    tr = tracking / 1000.0 * upem
    pos = buf.glyph_positions
    width = (sum(p.x_advance for p in pos) + tr * max(len(pos) - 1, 0)) * sc
    if anchor == 'middle':
        x -= width / 2
    elif anchor == 'end':
        x -= width
    glyphs, xs = [], []
    pen_x = 0.0
    for i, (info, p) in enumerate(zip(buf.glyph_infos, pos)):
        xs.append(x + (pen_x + p.x_offset) * sc)
        pen = _FlattenPen(gs)
        t = (sc, 0, 0, -sc, x + (pen_x + p.x_offset) * sc, y - p.y_offset * sc)
        gs[order[info.codepoint]].draw(TransformPen(pen, t))
        g = Polygon()
        for c in pen.contours:
            g = g.symmetric_difference(Polygon(c).buffer(0))  # even-odd
        glyphs.append(g)
        pen_x += p.x_advance + (tr if i < len(pos) - 1 else 0)
    return glyphs, width, xs


# ---------------------------------------------------------------- export
def _fmt(v):
    s = f'{v:.2f}'.rstrip('0').rstrip('.')
    return '0' if s == '-0' else s


def to_d(g, tol=0.1):
    if g.is_empty:
        return ''
    g = g.simplify(tol, preserve_topology=True)
    polys = [g] if isinstance(g, Polygon) else list(getattr(g, 'geoms', []))
    out = []
    for p in polys:
        if not isinstance(p, Polygon) or p.is_empty:
            continue
        p = orient(p, sign=-1.0)  # exterior clockwise on screen, holes counter-clockwise
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)[:-1]
            out.append('M' + ' L'.join(f'{_fmt(x)} {_fmt(y)}' for x, y in cs) + ' Z')
    return ' '.join(out)


def path_el(g, fill, tol=0.1):
    d = to_d(g, tol)
    return f'<path fill="{fill}" fill-rule="evenodd" d="{d}"/>' if d else ''


def type_path(ops, fill, dx=0.0, dy=0.0):
    """Outlined type with true curves, via tools/text2path.outline().
    ops: list of (font_file, text, size, x, y). Glyph counters are real holes
    (TrueType winding), so the default nonzero fill rule is used."""
    d = ' '.join(outline(f'{FONTS}/{ff}', t, size, x + dx, y + dy)['d'] for ff, t, size, x, y in ops)
    return f'<path fill="{fill}" d="{d}"/>' if d else ''


def transform(g, scale=1.0, dx=0.0, dy=0.0):
    g = affinity.scale(g, scale, scale, origin=(0, 0))
    return affinity.translate(g, dx, dy)


def svg_doc(vb_w, vb_h, body, title=None):
    t = f'<title>{title}</title>' if title else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_fmt(vb_w)} {_fmt(vb_h)}">'
            f'{t}{body}</svg>\n')
