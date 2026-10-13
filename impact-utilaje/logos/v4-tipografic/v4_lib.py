"""Geometry helpers for the v4 'Tipografic dinamic' wordmark.

Everything is built with skia-pathops (real Bézier curves, real boolean
operations) in SVG coordinates (y grows downward). Each colour is exported as
ONE <path> whose contours come out of a union/simplify, so counters and cut-outs
are true holes in the geometry: no white shapes painted on top.
"""
import math
import sys

import pathops
import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

sys.path.insert(0, '/home/user/Designing-Clothing-Brand/impact-utilaje/tools')
from gear import gear_path  # noqa: E402,F401
from text2path import outline  # noqa: E402,F401

FONTS = '/home/user/Designing-Clothing-Brand/impact-utilaje/fonts'
Y = '#F2A20A'   # Galben Impact
K = '#111111'   # Negru Utilaj
G = '#4A4F55'   # Gri Oțel
C = '#E6E4DF'   # Gri Beton
W = '#FFFFFF'   # Alb
PALETTE = (Y, K, G, C, W)

_font_cache = {}


def _font(name):
    if name not in _font_cache:
        path = f'{FONTS}/{name}'
        blob = hb.Blob.from_file_path(path)
        tt = TTFont(path)
        _font_cache[name] = (hb.Font(hb.Face(blob)), tt, tt.getGlyphSet(), tt.getGlyphOrder())
    return _font_cache[name]


def cap_height(font, size):
    _, tt, _, _ = _font(font)
    return tt['OS/2'].sCapHeight * size / tt['head'].unitsPerEm


# ------------------------------------------------------------------ paths
def P():
    return pathops.Path()


def union(*paths):
    ps = [p for p in paths if p is not None]
    if not ps:
        return P()
    out = pathops.Path()
    for p in ps:
        out.addPath(p)
    out.simplify(fix_winding=True)
    return out


def diff(a, b):
    return pathops.op(a, b, pathops.PathOp.DIFFERENCE, fix_winding=True)


def inter(a, b):
    return pathops.op(a, b, pathops.PathOp.INTERSECTION, fix_winding=True)


def poly(pts):
    p = P()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def rect(x0, y0, x1, y1):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def circle(cx, cy, r):
    k = 0.5522847498 * r
    p = P()
    p.moveTo(cx + r, cy)
    p.cubicTo(cx + r, cy + k, cx + k, cy + r, cx, cy + r)
    p.cubicTo(cx - k, cy + r, cx - r, cy + k, cx - r, cy)
    p.cubicTo(cx - r, cy - k, cx - k, cy - r, cx, cy - r)
    p.cubicTo(cx + k, cy - r, cx + r, cy - k, cx + r, cy)
    p.close()
    return p


def transform(path, a=1, b=0, c=0, d=1, e=0, f=0):
    """Affine transform x' = a x + c y + e ; y' = b x + d y + f."""
    out = P()
    path.draw(TransformPen(out.getPen(), (a, b, c, d, e, f)))
    return out


def translate(path, dx, dy):
    return transform(path, 1, 0, 0, 1, dx, dy)


def shear(path, angle_deg, y_ref):
    """Italic shear: points above y_ref move right (SVG y-down)."""
    t = math.tan(math.radians(angle_deg))
    # x' = x - t*(y - y_ref) = x - t*y + t*y_ref
    return transform(path, 1, 0, -t, 1, t * y_ref, 0)


def bounds(path):
    return path.bounds  # (xmin, ymin, xmax, ymax)


def parallelogram(x_base_left, y_base, width, height, angle_deg):
    """Forward-slanted bar: bottom edge from x_base_left to +width at y_base,
    top edge shifted right by height*tan(angle)."""
    s = height * math.tan(math.radians(angle_deg))
    return poly([(x_base_left, y_base), (x_base_left + s, y_base - height),
                 (x_base_left + s + width, y_base - height), (x_base_left + width, y_base)])


def to_d(path, ndp=2):
    pen = SVGPathPen(None, ntos=lambda v: (f'{v:.{ndp}f}').rstrip('0').rstrip('.') if '.' in f'{v:.{ndp}f}' else f'{v:.{ndp}f}')
    path.draw(pen)
    return pen.getCommands()


# ------------------------------------------------------------------ type
def glyph_run(font, text, size, x=0.0, y=0.0, tracking=0.0, extra=None):
    """Shape `text` (kerning on) and return a list of glyph dicts:
    {'ch', 'path', 'x' (pen position), 'adv'} in SVG coordinates, baseline at y.
    `tracking` in thousandths of an em; `extra` = per-gap extra space in user
    units (list, len(text)-1) for optical spacing."""
    hbfont, tt, gs, order = _font(font)
    upem = tt['head'].unitsPerEm
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, {'kern': True, 'liga': False})
    sc = size / upem
    tr = tracking / 1000.0 * size
    out = []
    pen_x = x
    n = len(buf.glyph_infos)
    for i, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
        name = order[info.codepoint]
        p = P()
        t = (sc, 0, 0, -sc, pen_x + pos.x_offset * sc, y - pos.y_offset * sc)
        gs[name].draw(TransformPen(p.getPen(), t))
        p.simplify(fix_winding=True)
        adv = pos.x_advance * sc
        out.append({'ch': text[info.cluster], 'path': p, 'x': pen_x, 'adv': adv})
        pen_x += adv
        if i < n - 1:
            pen_x += tr + (extra[i] if extra else 0)
    return out


def run_path(run):
    return union(*[g['path'] for g in run])


# ------------------------------------------------------------------ gear letter
def gear_ring(cx, cy, r_tip, r_root, r_hole, teeth, tip=0.40, base=0.58, rotate=0.0):
    """Gear with true circular roots (gear polygon ∪ root circle) and a round hole."""
    g = P()
    d = gear_path(cx, cy, r_tip, r_root, teeth, 0, tip, base, rotate, ndp=4)
    # parse the simple 'M x y L x y ... Z' path from gear.py
    toks = d.replace('M', ' ').replace('L', ' ').replace('Z', ' ').split()
    pts = [(float(toks[i]), float(toks[i + 1])) for i in range(0, len(toks), 2)]
    g = poly(pts)
    body = union(g, circle(cx, cy, r_root))
    if r_hole > 0:
        body = diff(body, circle(cx, cy, r_hole))
    return body


def svg_doc(vb, body, title=None):
    x0, y0, w, h = vb
    t = f'<title>{title}</title>' if title else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:g} {y0:g} {w:g} {h:g}">'
            f'{t}{body}</svg>\n')


def path_el(path, fill):
    return f'<path fill="{fill}" fill-rule="evenodd" d="{to_d(path)}"/>'
