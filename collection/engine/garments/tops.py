"""Flat-lay mockups: tops of the NEPĂMÂNTEAN collection.

tee_oversized, tee_baby_crop, longsleeve, longsleeve_crop, tank, crop_tank, hoodie,
crop_hoodie, zip_hoodie, crewneck, windbreaker, tshirt_dress, sports_bra.
Interface: see engine/engine.py docstring.  Canvas viewBox 0 0 1000 1100, transparent
background, garment centred.

Every garment is described in centimetres (x from the centre front line, y down from the
high point of the shoulder) and scaled to the canvas, so proportions follow real flat
measurements.  A drawing is a stack of pieces (hood, body, sleeves) rendered back to front;
each piece is painted fill -> prints (body only) -> shading -> folds -> seams/stitching ->
ribbing -> outline, and hardware (zips, drawcords, toggles) goes on top of everything.
"""
import itertools
import math

VB = "0 0 1000 1100"
CX, CY = 500.0, 550.0
AOP_TRIM = "#111114"
HW, HW_DARK = "#C9CCD3", "#8A8F99"
_COUNTER = itertools.count()

OUTLINE = 'fill="none" stroke="#000" stroke-opacity=".35" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"'
SEAM = 'fill="none" stroke="#000" stroke-opacity=".28" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
STITCH = SEAM + ' stroke-dasharray="5 4"'


# ======================================================================
# geometry helpers (centimetre space)
# ======================================================================
def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k)


def unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1.0
    return (dx / L, dy / L)


def cub(p0, p1, p2, p3, n=18):
    out = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def line(p0, p1, n=1):
    return [lerp(p0, p1, i / n) for i in range(n + 1)]


def catmull(pts, n=10):
    """Smooth curve through pts."""
    out = [pts[0]]
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.extend(cub(p1, c1, c2, p2, n)[1:])
    return out


def join(*segs):
    out = []
    for s in segs:
        s = list(s)
        if out and abs(out[-1][0] - s[0][0]) < 1e-6 and abs(out[-1][1] - s[0][1]) < 1e-6:
            out.extend(s[1:])
        else:
            out.extend(s)
    return out


def mx(pts):
    return [(-x, y) for x, y in pts]


def rv(pts):
    return list(pts)[::-1]


def full(half):
    """half runs from the centre line (x=0) to the right end -> left end .. centre .. right end."""
    return join(rv(mx(half)), half)


def closed(right, top):
    """Right half (right HPS .. centre bottom) + mirrored left half + top curve (left -> right)."""
    return join(right, rv(mx(right)), top)


def offset(pts, d):
    """Offset a polyline; positive d = to the right of the walking direction (y down)."""
    out = []
    n = len(pts)
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tx, ty = unit(a, b)
        out.append((pts[i][0] - ty * d, pts[i][1] + tx * d))
    return out


def shift(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]


def cumlen(pts):
    c = [0.0]
    for i in range(1, len(pts)):
        c.append(c[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    return c


def at(pts, cum, L):
    """Point at arc length L plus its fractional index."""
    for i in range(1, len(pts)):
        if cum[i] >= L:
            seg = cum[i] - cum[i - 1] or 1.0
            t = (L - cum[i - 1]) / seg
            return i - 1 + t
    return len(pts) - 1.0


def pt_at(pts, fi):
    i = int(fi)
    if i >= len(pts) - 1:
        return pts[-1]
    return lerp(pts[i], pts[i + 1], fi - i)


def sub(pts, f0, f1, n=16):
    """Sub-curve between fractions (0..1 of arc length)."""
    cum = cumlen(pts)
    return [pt_at(pts, at(pts, cum, cum[-1] * (f0 + (f1 - f0) * k / n))) for k in range(n + 1)]


def resample(pts, n):
    cum = cumlen(pts)
    return [pt_at(pts, at(pts, cum, cum[-1] * k / n)) for k in range(n + 1)]


def shoulder_y(c, x):
    nw, sw, sd = c["nw"], c["sw"], c["sd"]
    t = (x - nw) / (sw - nw)
    return sd * (0.3 * t + 0.7 * t * t) if c.get("sleeve") or c.get("long") else sd * t


# ======================================================================
# canvas transform + svg helpers
# ======================================================================
class Ctx:
    def __init__(self, key, view, layout, fabric, aop):
        self.p = f"{key}-{view}-{next(_COUNTER)}-"
        self.n = 0
        self.s, self.top = layout["s"], layout["top"]
        self.bbox = layout["bbox"]
        self.defs = [aop["defs"]] if aop else []
        self.fabric = fabric
        self.fill = f'url(#{aop["id"]})' if aop else fabric
        self.trim = AOP_TRIM if aop else fabric
        self.aop = bool(aop)
        self.light = _lum(self.trim) > 0.55
        self.hw = []
        x0, y0, x1, y1 = self.bbox
        self.gv, self.gh = self.id("gv"), self.id("gh")
        self.defs.append(
            f'<linearGradient id="{self.gv}" gradientUnits="userSpaceOnUse" x1="0" y1="{y0:.1f}" x2="0" y2="{y1:.1f}">'
            '<stop offset="0" stop-color="#fff" stop-opacity=".10"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset=".45" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".18"/></linearGradient>'
            f'<linearGradient id="{self.gh}" gradientUnits="userSpaceOnUse" x1="{x0:.1f}" y1="0" x2="{x1:.1f}" y2="0">'
            '<stop offset="0" stop-color="#000" stop-opacity=".12"/><stop offset=".18" stop-color="#000" stop-opacity="0"/>'
            '<stop offset=".82" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".12"/></linearGradient>')

    def id(self, tag):
        self.n += 1
        return f"{self.p}{tag}{self.n}"

    def P(self, pt):
        return (CX + pt[0] * self.s, self.top + pt[1] * self.s)

    def d(self, pts, close=True):
        q = [self.P(p) for p in pts]
        s = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in q)
        return s + (" Z" if close else "")

    def u(self, cm):
        return cm * self.s

    def clip(self, *polys):
        cid = self.id("c")
        self.defs.append(f'<clipPath id="{cid}">' + "".join(f'<path d="{self.d(p)}"/>' for p in polys) + "</clipPath>")
        return cid

    def shade_rects(self):
        x0, y0, x1, y1 = self.bbox
        r = f'x="{x0 - 20:.1f}" y="{y0 - 20:.1f}" width="{x1 - x0 + 40:.1f}" height="{y1 - y0 + 40:.1f}"'
        return f'<rect {r} fill="url(#{self.gv})"/><rect {r} fill="url(#{self.gh})"/>'


def _lum(h):
    h = h.lstrip("#")
    if len(h) != 6:
        return 0.0
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ======================================================================
# pieces
# ======================================================================
class Piece:
    def __init__(self, poly):
        self.poly = poly
        self.inner = []      # list of callables(ctx, clip_id) -> markup drawn right after the fill
        self.print_poly = None
        self.shade = []      # extra shading markup callables(ctx)
        self.folds = []      # (pts, width_cm)
        self.seams = []      # pts (open)
        self.stitch = []     # pts (open, dashed)
        self.bands = []      # (edge_a, edge_b, kind)  kind: rib | elastic | flat
        self.band_seams = []  # seam lines drawn on top of bands
        self.outline = []    # open polylines outlined like the silhouette
        self.outline_closed = []


def band_poly(a, b):
    return join(a, rv(b)) + [a[0]]


def render_piece(ctx, pc, prints=""):
    out = []
    cid = ctx.clip(pc.poly)
    out.append(f'<path d="{ctx.d(pc.poly)}" fill="{ctx.fill}"/>')
    for f in pc.inner:
        out.append(f(ctx, cid))
    if prints:
        pid = ctx.clip(pc.print_poly or pc.poly)
        out.append(f'<g clip-path="url(#{pid})">{prints}</g>')
    out.append(f'<g clip-path="url(#{cid})">{ctx.shade_rects()}' + "".join(f(ctx) for f in pc.shade) + "</g>")
    if pc.folds:
        out.append(f'<g clip-path="url(#{cid})" fill="none" stroke="#000" stroke-opacity=".06" stroke-linecap="round">'
                   + "".join(f'<path d="{ctx.d(p, False)}" stroke-width="{w:.1f}"/>' for p, w in pc.folds) + "</g>")
    if pc.seams:
        out.append(f'<g {SEAM}>' + "".join(f'<path d="{ctx.d(p, False)}"/>' for p in pc.seams) + "</g>")
    if pc.stitch:
        out.append(f'<g {STITCH}>' + "".join(f'<path d="{ctx.d(p, False)}"/>' for p in pc.stitch) + "</g>")
    for a, b, kind in pc.bands:
        out.append(render_band(ctx, a, b, kind))
    if pc.band_seams:
        out.append(f'<g {SEAM}>' + "".join(f'<path d="{ctx.d(p, False)}"/>' for p in pc.band_seams) + "</g>")
    out.append(f'<path d="{ctx.d(pc.poly)}" {OUTLINE}/>')
    for p in pc.outline:
        out.append(f'<path d="{ctx.d(p, False)}" {OUTLINE}/>')
    for p in pc.outline_closed:
        out.append(f'<path d="{ctx.d(p)}" {OUTLINE}/>')
    return "".join(out)


def render_band(ctx, a, b, kind):
    """Rib / elastic band between edge a (outer/free edge) and edge b (seam edge); same sample count."""
    poly = band_poly(a, b)
    cid = ctx.clip(poly)
    d = ctx.d(poly)
    o = [f'<path d="{d}" fill="{ctx.trim}"/>', f'<path d="{d}" fill="#000" fill-opacity=".12"/>']
    cum = cumlen(a)
    step = 6.0 / ctx.s
    lines = []
    if kind == "elastic":
        # gathered elastic: wavy pucker strokes
        k = step * 2.2
        L = k / 2
        while L < cum[-1]:
            fi = at(a, cum, L)
            pa, pb = pt_at(a, fi), pt_at(b, fi)
            m = lerp(pa, pb, 0.5)
            tx, ty = unit(pa, pb)
            wob = 0.18 * math.hypot(pb[0] - pa[0], pb[1] - pa[1])
            q = [ctx.P(pa), ctx.P((m[0] - ty * wob, m[1] + tx * wob)), ctx.P(pb)]
            lines.append(f'M{q[0][0]:.1f},{q[0][1]:.1f} Q{q[1][0]:.1f},{q[1][1]:.1f} {q[2][0]:.1f},{q[2][1]:.1f}')
            L += k
        o.append(f'<g clip-path="url(#{cid})"><path d="{" ".join(lines)}" fill="none" stroke="#000" stroke-opacity=".16" stroke-width="2.2" stroke-linecap="round"/>'
                 f'<path d="{ctx.d(lerp_curve(a, b, .5), False)}" {STITCH}/>')
    else:
        L = step / 2
        while L < cum[-1]:
            fi = at(a, cum, L)
            pa, pb = ctx.P(pt_at(a, fi)), ctx.P(pt_at(b, fi))
            lines.append(f"M{pa[0]:.1f},{pa[1]:.1f} L{pb[0]:.1f},{pb[1]:.1f}")
            L += step
        o.append(f'<g clip-path="url(#{cid})"><path d="{" ".join(lines)}" fill="none" stroke="#000" stroke-opacity=".10" stroke-width="1.5"/>')
        if kind == "flat":
            o.append(f'<path d="{ctx.d(lerp_curve(a, b, .5), False)}" {STITCH}/>')
    o.append(ctx.shade_rects() + "</g>")
    o.append(f'<path d="{d}" {OUTLINE}/>')
    return "".join(o)


def lerp_curve(a, b, t):
    return [lerp(p, q, t) for p, q in zip(a, b)]


def lining_fill(poly, alpha=0.38):
    """Inside of the garment seen through an opening: fabric + dark overlay."""
    def f(ctx, cid):
        d = ctx.d(poly)
        return (f'<path d="{d}" fill="{ctx.fill}"/><path d="{d}" fill="#000" fill-opacity="{alpha}"/>')
    return f


# ======================================================================
# garment construction
# ======================================================================
def neck_half(nw, depth, end=None, flat=0.55, steep=0.5):
    """Neckline from centre (0, depth) to the shoulder end (default HPS (nw, 0))."""
    ex, ey = end if end else (nw, 0.0)
    return cub((0, depth), (nw * flat, depth), (ex - (ex - nw) * 0.2 - nw * 0.04, ey + (depth - ey) * steep), (ex, ey), 16)


def sleeve_geo(c):
    s = c["sleeve"]
    SP = (c["sw"], c["sd"])
    a = math.radians(s["ang"])
    dr, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    C1 = add(SP, dr, s["len"])
    C2 = add(C1, n, s["open"])
    return SP, dr, n, C1, C2


def right_half(c, view):
    """Body outline from the right HPS to the centre of the hem (cm)."""
    nw, sw, sd, ch, L = c["nw"], c["sw"], c["sd"], c["ch"], c["L"]
    HPS, SP = (nw, 0.0), (sw, sd)
    hw, dip = c.get("hw", ch), c.get("dip", 0.5)
    hr = c.get("hem_band", 0)
    segs = []
    if view == "back" and c.get("racer"):
        r = c["racer"]
        segs.append(line(HPS, SP, 2))
        segs.append(cub(SP, (sw - 0.3, 6), (r[0] + 1.5, r[1] - 4), r, 14))
        A = (ch, c["ay_back"])
        segs.append(cub(r, (r[0], r[1] + 4.5), (ch - 6, A[1] - 0.6), A, 14))
    elif c.get("sleeve"):
        _, dr, n, C1, C2 = sleeve_geo(c)
        s = c["sleeve"]
        A = (ch, s["ay"])
        segs.append(cub(HPS, (nw + (sw - nw) * .4, sd * .25), (nw + (sw - nw) * .75, sd * .62), SP, 10))
        segs.append(cub(SP, add(add(SP, dr, s["len"] * .35), n, -.5), add(add(SP, dr, s["len"] * .7), n, -.35), C1, 12))
        segs.append(line(C1, C2, 2))
        segs.append(cub(C2, lerp(C2, A, .45), add(A, unit(A, C2), 1.6 + 0.0), A, 10))
    elif c.get("long"):
        A = (ch, c["ay"])
        segs.append(cub(HPS, (nw + (sw - nw) * .4, sd * .25), (nw + (sw - nw) * .75, sd * .62), SP, 10))
        segs.append(cub(SP, (sw + 0.6, sd + 8), (ch, A[1] - 8), A, 10))
    else:  # sleeveless
        A = (ch, c["ay"])
        segs.append(line(HPS, SP, 2))
        c1, c2 = c["arm"]
        segs.append(cub(SP, c1, c2, A, 18))
    top_hem = L - hr
    H = (hw, top_hem)
    if c.get("waist"):
        ww, wy = c["waist"]
        segs.append(catmull([A, (ww, wy), H], 10))
    elif abs(hw - ch) > 0.3:
        segs.append(cub(A, (ch, A[1] + (top_hem - A[1]) * .55), (ch + (hw - ch) * .2, top_hem - 3.5), H, 14))
    else:
        segs.append(line(A, H, 4))
    if hr:
        segs.append(line(H, (hw, L), 2))
        segs.append(line((hw, L), (0, L), 8))
    else:
        segs.append(cub(H, (hw * .66, L + dip * .5), (hw * .3, L + dip), (0, L + dip), 12))
    return join(*segs), A


def hem_curve(c, up=0.0):
    hw, L, dip = c.get("hw", c["ch"]), c["L"], c.get("dip", 0.5)
    half = cub((0, L + dip - up), (hw * .3, L + dip - up), (hw * .66, L + dip * .5 - up), (hw, L - up), 12)
    return full(half)


def build(key, c, view):
    """Return list of pieces (back -> front) and hardware callables for a view."""
    nw, fd, bd, ch, L = c["nw"], c["fd"], c["bd"], c["ch"], c["L"]
    R, A = right_half(c, view)
    neck = c.get("neck", "crew")
    hood = c.get("hood")
    r = c.get("nr", 2.2)
    pieces, hw = [], []
    sh_end = (nw + r * 0.7, shoulder_y(c, nw + r * 0.7)) if neck == "crew" else None

    # ---------------- neck / top edge of the body ----------------
    if hood and view == "front":
        Sf = neck_half(nw, fd, flat=.5, steep=.55)
        body_top = full(Sf)
        body = Piece(closed(R, body_top))
    elif view == "front":
        back_h = neck_half(nw, bd, flat=.6, steep=.4)
        body_top = full(back_h)
        body = Piece(closed(R, body_top))
        if neck == "crew":
            Sf = neck_half(nw, fd, end=sh_end)
            Ef = neck_half(nw, fd - r, flat=.5, steep=.62)
        else:  # bound neckline (tanks, bra): binding on the body side of the edge
            Ef = neck_half(nw, fd, flat=c.get("nflat", .55), steep=c.get("nsteep", .55))
            Sf = neck_half(nw + 0.0, fd + r, end=(nw + r * 0.9, shoulder_y(c, nw + r * 0.9)),
                                                    flat=c.get("nflat", .55), steep=c.get("nsteep", .55))
        Sf2 = resample(Sf, 40)
        Ef2 = resample(Ef, 40)
        body.print_poly = closed(R, full(Sf2))
        inner_poly = join(body_top, rv(full(Ef2)))
        B2 = neck_half(nw, bd + r, flat=.6, steep=.45)
        bpoly = band_poly(resample(full(back_h), 60), resample(full(B2), 60))

        def neck_inside(ctx, cid, inner_poly=inner_poly, bpoly=bpoly, B2=B2, back_h=back_h):
            ic = ctx.clip(inner_poly)
            d = ctx.d(inner_poly)
            o = [f'<path d="{d}" fill="{ctx.fill}"/>',
                 f'<g clip-path="url(#{ic})"><path d="{ctx.d(bpoly)}" fill="{ctx.trim}"/>',
                 f'<path d="{d}" fill="#000" fill-opacity=".34"/>']
            if c.get("neck_label", neck == "crew"):
                lw, lh = 5.6, 2.4
                y0 = bd + r + 0.5
                lab = [(-lw / 2, y0), (lw / 2, y0), (lw / 2, y0 + lh), (-lw / 2, y0 + lh)]
                lc = "#E9E7E0" if _lum(ctx.trim) < .5 else "#26262B"
                tc = "#26262B" if lc == "#E9E7E0" else "#E9E7E0"
                o.append(f'<path d="{ctx.d(lab)}" fill="{lc}" fill-opacity=".9"/>')
                cx_, cy_ = ctx.P((0, y0 + lh / 2))
                o.append(f'<rect x="{cx_ - ctx.u(1.6):.1f}" y="{cy_ - ctx.u(.25):.1f}" width="{ctx.u(3.2):.1f}" height="{ctx.u(.5):.1f}" fill="{tc}" fill-opacity=".7"/>')
            o.append(f'<path d="{ctx.d(full(B2), False)}" {SEAM}/>')
            o.append(f'<path d="{ctx.d(lerp_curve(resample(full(back_h), 40), resample(full(B2), 40), .5), False)}" {STITCH}/>')
            o.append("</g>")
            o.append(f'<path d="{ctx.d(full(Ef2), False)}" {OUTLINE}/>')
            return "".join(o)
        body.inner.append(neck_inside)
        body.bands.append((full(Ef2), full(Sf2), "rib" if neck == "crew" else "flat"))
        body.stitch.append(offset(full(Sf2), -0.6))
    else:  # back view
        back_h = neck_half(nw, bd, flat=.6, steep=.4)
        body_top = full(back_h)
        body = Piece(closed(R, body_top))
        if not hood:
            if neck == "crew":
                Sb = neck_half(nw, bd + r, end=sh_end, flat=.6, steep=.45)
            else:
                Sb = neck_half(nw, bd + r, end=(nw + r * 0.9, shoulder_y(c, nw + r * 0.9)), flat=.6, steep=.45)
                if c.get("racer"):
                    Sb = neck_half(nw, bd + r, end=(nw + r, 0), flat=.25, steep=.55)
            body.bands.append((resample(full(back_h), 50), resample(full(Sb), 50), "rib" if neck == "crew" else "flat"))
            body.stitch.append(offset(resample(full(Sb), 40), 0.6))

    # ---------------- hood ----------------
    if hood:
        hh, hwid = hood["hh"], hood["w"]
        P0 = (nw + 1.6, shoulder_y(c, nw + 1.6))
        outer_r = join(cub((0, -hh), (hwid * .55, -hh), (hwid, -hh + 7), (hwid, -hh + 16), 14),
                       cub((hwid, -hh + 16), (hwid, -hh + 25), (nw + 4.5, -4), P0, 14))
        outer = join(rv(mx(outer_r)), outer_r)
        base = full(neck_half(nw, (fd + 2.5 if view == "front" else bd + 2.5), flat=.5, steep=.5))
        hpoly = join(outer, rv(base))
        hp = Piece(hpoly)
        hp.folds.append((cub((hwid - 4, -hh + 12), (hwid - 6, -hh + 18), (hwid - 5, -10), (hwid - 3.5, -5), 10), 0.9))
        hp.folds.append((cub((-hwid + 4, -hh + 13), (-hwid + 6, -hh + 19), (-hwid + 5, -10), (-hwid + 3, -5), 10), 0.8))
        if view == "front":
            rw = hwid - 2.6
            bot = fd - (1.5 if c.get("zip") else 0.4)
            Oo = join(cub((0, bot), (5.5, bot - 3.5), (rw, -2), (rw, -13), 14),
                      cub((rw, -13), (rw, -hh + 9), (rw * .5, -hh + 2.4), (0, -hh + 2.4), 14))
            ri = rw - 3.0
            Oi = join(cub((0, bot - 2.6), (3.5, bot - 5.5), (ri, -3.5), (ri, -14), 14),
                      cub((ri, -14), (ri, -hh + 11), (ri * .5, -hh + 5.4), (0, -hh + 5.4), 14))
            O_out, O_in = join(rv(mx(Oo)), Oo), join(rv(mx(Oi)), Oi)
            hp.inner.append(lining_fill(O_in + [O_in[0]], .42))
            hp.inner.append(lambda ctx, cid, O_in=O_in, hh=hh, fd=fd: (
                f'<g clip-path="url(#{ctx.clip(O_in)})">'
                f'<path d="{ctx.d([(0, -hh + 5), (0, fd + 2)], False)}" {SEAM}/>'
                f'<path d="{ctx.d([(-.5, -hh + 5), (-.5, fd + 2)], False)}" {STITCH}/>'
                f'<path d="{ctx.d([(.5, -hh + 5), (.5, fd + 2)], False)}" {STITCH}/>'
                f'<path d="{ctx.d(shift(O_in, 0, 1.2))}" fill="none" stroke="#000" stroke-opacity=".18" stroke-width="{ctx.u(1.6):.1f}"/>'
                '</g>'))
            hp.stitch.append(lerp_curve(resample(O_out, 60), resample(O_in, 60), .5))
            hp.outline.extend([O_out, O_in])
            hp.shade.append(lambda ctx, body_top=body_top: f'<path d="{ctx.d(shift(body_top, 0, -.4), False)}" fill="none" stroke="#000" stroke-opacity=".12" stroke-width="{ctx.u(1.6):.1f}"/>')
            if c.get("strings"):
                for sg in (1, -1):
                    oi = resample(Oo, 40)
                    ii = resample(Oi, 40)
                    e = lerp(oi[5], ii[5], .5)
                    e = (sg * abs(e[0]) if sg > 0 else -abs(e[0]), e[1])
                    hw.append(_drawstring(e, sg, c["strings"]))
        else:
            hp.seams.append([(0, -hh), (0, bd)])
            hp.stitch.append([(-.6, -hh + .3), (-.6, bd)])
            hp.stitch.append([(.6, -hh + .3), (.6, bd)])
            hp.shade.append(lambda ctx, body_top=body_top: f'<path d="{ctx.d(shift(body_top, 0, -.4), False)}" fill="none" stroke="#000" stroke-opacity=".12" stroke-width="{ctx.u(1.6):.1f}"/>')
        pieces.append(hp)
        if view == "back":
            body.seams.append(full(neck_half(nw, bd, flat=.6, steep=.4)))

    # ---------------- body details ----------------
    sx = 1 if view == "front" else -1  # fold asymmetry
    hr = c.get("hem_band", 0)
    hwid_ = c.get("hw", ch)
    if hr:
        a_ = resample(line((-hwid_, L), (hwid_, L), 8), 60)
        b_ = resample(line((-hwid_, L - hr), (hwid_, L - hr), 8), 60)
        body.bands.append((a_, b_, c.get("hem_kind", "rib")))
    else:
        body.stitch.append(hem_curve(c, 2.2 if L > 50 else 1.8))
    # folds: underarm drapes + hem ripples
    for sg in (1, -1):
        ax, ay = A
        k = 1.0 if sg == sx else 0.8
        if c.get("sleeve") or c.get("long"):
            body.folds.append(([(sg * (ax - 1.2), ay + 1.5), (sg * (ax - 4), ay + 5.5 * k), (sg * (ax - 7.5 * k), ay + 11 * k)], 0.9))
            body.folds.append(([(sg * (ax - 0.8), ay + 7), (sg * (ax - 3), ay + 11 * k), (sg * (ax - 5 * k), ay + 16 * k)], 0.7))
        bot = L - hr - (0.5 if hr else 0)
        body.folds.append(([(sg * hwid_ * .52, bot), (sg * hwid_ * .55, bot - 4 * k), (sg * hwid_ * .5, bot - 9 * k)], 0.8))
        body.folds.append(([(sg * hwid_ * .2 * k, bot), (sg * hwid_ * .24, bot - 3.5)], 0.7))
    if c.get("sleeve") or c.get("long"):
        body.folds.append(([(-sx * 3, fd + 6), (-sx * 1, fd + 12), (sx * 2, fd + 15)], 0.7) if view == "front" else
                          ([(4, bd + 8), (1, bd + 13), (-2, bd + 16)], 0.6))

    # short sleeves (attached, part of the body silhouette)
    if c.get("sleeve"):
        SP, dr, n, C1, C2 = sleeve_geo(c)
        s = c["sleeve"]
        for sg in (1, -1):
            m = (lambda p: p) if sg > 0 else (lambda p: (-p[0], p[1]))
            arm = cub(SP, (SP[0] - .6, SP[1] + (A[1] - SP[1]) * .35), (A[0] - .9, A[1] - (A[1] - SP[1]) * .25), A, 14)
            body.seams.append([m(p) for p in arm])
            C1i, C2i = add(C1, dr, -s.get("cuff", 0) or 0), add(C2, unit(C2, A), s.get("cuff", 0) or 0)
            if s.get("cuff"):
                a_ = [m(p) for p in line(C1, C2, 12)]
                b_ = [m(p) for p in line(C1i, C2i, 12)]
                body.bands.append((a_, b_, "rib"))
            else:
                h = 2.2 if s["len"] > 15 else 1.6
                body.stitch.append([m(p) for p in line(add(C1, dr, -h), add(C2, unit(C2, A), h), 4)])
            mid = lerp(SP, C1, .55)
            body.folds.append(([m(p) for p in cub(lerp(SP, A, .55), lerp(mid, C2, .5), lerp(C1, C2, .55), lerp(C1, C2, .62), 8)][:7], 0.9))
            body.folds.append(([m(p) for p in line(lerp(C1, C2, .2), add(lerp(C1, C2, .25), dr, -5), 3)], 0.7))
            body.shade.append(lambda ctx, arm=[m(p) for p in arm], sg=sg: (
                f'<path d="{ctx.d(shift(arm, sg * 0.5, 0), False)}" fill="none" stroke="#000" stroke-opacity=".07" stroke-width="{ctx.u(1.4):.1f}"/>'))

    # sleeveless: armhole binding
    if not c.get("sleeve") and not c.get("long"):
        bwid = c.get("ab", r)
        if view == "back" and c.get("racer"):
            rr = c["racer"]
            ar = join(cub((c["sw"], c["sd"]), (c["sw"] - .3, 6), (rr[0] + 1.5, rr[1] - 4), rr, 14),
                      cub(rr, (rr[0], rr[1] + 4.5), (ch - 6, c["ay_back"] - .6), (ch, c["ay_back"]), 14))
        else:
            c1, c2 = c["arm"]
            ar = cub((c["sw"], c["sd"]), c1, c2, A, 24)
        ar = resample(ar, 40)
        inn = offset(ar, -bwid)
        for sg in (1, -1):
            m = (lambda p: p) if sg > 0 else (lambda p: (-p[0], p[1]))
            body.bands.append(([m(p) for p in ar], [m(p) for p in inn], "flat"))

    # long sleeves: separate pieces lying over the body
    sleeves = []
    if c.get("long"):
        ls = c["long"]
        SP = (c["sw"], c["sd"])
        a = math.radians(ls["ang"])
        dr, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
        C1 = add(SP, dr, ls["len"])
        C2 = add(C1, n, ls["cw"])
        U = ls["U"]
        outer = cub(SP, add(SP, (2.6, 1.0)), add(add(SP, dr, ls["len"] * .4), n, -1.6), C1, 16)
        inner = cub(C2, add(lerp(C2, U, .35), n, -0.3), add(lerp(C2, U, .75), n, 0.6), U, 14)
        topc = cub(U, (U[0] + 1.2, U[1] - 9), (SP[0] - 3.2, SP[1] + 7.5), SP, 14)
        spoly = join(outer, line(C1, C2, 2), inner, topc)
        cr = ls.get("cuff", 0)
        for sg in (1, -1):
            m = (lambda p: p) if sg > 0 else (lambda p: (-p[0], p[1]))
            M = lambda pts: [m(p) for p in pts]
            sp = Piece(M(spoly))
            if cr:
                a_ = line(C1, C2, 12)
                b_ = line(add(C1, dr, -cr), add(C2, unit(C2, U), cr), 12)
                sp.bands.append((M(a_), M(b_), ls.get("cuff_kind", "rib")))
            else:
                sp.stitch.append(M(line(add(C1, dr, -2), add(C2, unit(C2, U), 2), 4)))
            # creases: elbow, along the sleeve, gathers above the cuff
            L1 = lerp(SP, C1, .52)
            L2 = lerp(U, C2, .5)
            k = 1 if sg == sx else .85
            sp.folds.append((M(cub(add(L1, n, .8), add(lerp(L1, L2, .3), dr, 2.5 * k), add(lerp(L1, L2, .7), dr, -1.5), add(L2, n, -1.0), 8)), 1.0))
            sp.folds.append((M(cub(add(lerp(SP, C1, .2), n, 2.5), add(lerp(SP, C1, .4), n, 3.5), add(lerp(SP, C1, .6), n, 4.2 * k), add(lerp(SP, C1, .78), n, 3.2), 8)), 0.8))
            cb = cr + 1.0
            for t in (.25, .55, .8):
                p0 = add(lerp(C1, C2, t), dr, -cb)
                sp.folds.append((M([p0, add(add(p0, dr, -3.5 * k), n, .6)]), 0.7))
            sleeves.append((sp, M(spoly), sg))
        # sleeve shadow on the body
        for sp, poly, sg in sleeves:
            body.shade.append(lambda ctx, poly=poly, sg=sg: f'<path d="{ctx.d(shift(poly, -sg * .45, .6))}" fill="#000" fill-opacity=".16"/>')

    # pockets / zip / extras
    if view == "front" and c.get("pocket") == "kangaroo":
        pt, pb, pw, pw2, ps = c["pocket_box"]
        pk = [(-pw2, pb), (-pw2, ps), (-pw, pt), (pw, pt), (pw2, ps), (pw2, pb)]
        body.outline.append(pk)
        body.stitch.append([(-pw2 + .7, pb), (-pw2 + .7, ps + .3), (-pw + .4, pt + .7), (pw - .4, pt + .7), (pw2 - .7, ps + .3), (pw2 - .7, pb)])
        for sg in (1, -1):
            mouth = [(sg * pw, pt), (sg * pw2, ps), (sg * (pw2 - 1.0), ps + .2), (sg * (pw - .4), pt + 1.2)]
            body.shade.append(lambda ctx, mouth=mouth: f'<path d="{ctx.d(mouth)}" fill="#000" fill-opacity=".22"/>')
            body.stitch.append([(sg * (pw - .5), pt + .9), (sg * (pw2 - .8), ps + .1)])
        body.folds.append(([(-pw + 2, pt + 3), (0, pt + 4.5), (pw - 3, pt + 3.2)], 0.8))
    if view == "front" and c.get("pocket") == "split":
        pt, pb, pw, pw2, ps = c["pocket_box"]
        for sg in (1, -1):
            pk = [(sg * 2.2, pt), (sg * pw, pt), (sg * pw2, ps), (sg * pw2, pb)]
            body.outline.append(pk)
            body.seams.append([(sg * 2.2, pt), (sg * 2.2, pb)])
            body.stitch.append([(sg * 2.9, pb), (sg * 2.9, pt + .7), (sg * (pw - .4), pt + .7), (sg * (pw2 - .7), ps + .3), (sg * (pw2 - .7), pb)])
            mouth = [(sg * pw, pt), (sg * pw2, ps), (sg * (pw2 - 1.0), ps + .2), (sg * (pw - .4), pt + 1.2)]
            body.shade.append(lambda ctx, mouth=mouth: f'<path d="{ctx.d(mouth)}" fill="#000" fill-opacity=".22"/>')
    if view == "front" and c.get("zip"):
        top_y = fd - (0.0 if hood else 0.0)
        hw.append(_zipper(top_y, L, c.get("zip_kind", "metal")))
    if c.get("yoke_y"):
        yy = c["yoke_y"] if view == "front" else c.get("yoke_back", c["yoke_y"])
        body.seams.append([(-ch, yy + 1.5), (-ch * .5, yy + .4), (0, yy), (ch * .5, yy + .4), (ch, yy + 1.5)])
        body.stitch.append([(-ch, yy + 2.2), (-ch * .5, yy + 1.1), (0, yy + .7), (ch * .5, yy + 1.1), (ch, yy + 2.2)])
        body.shade.append(lambda ctx, yy=yy: f'<path d="{ctx.d([(-ch, yy + 2.5), (0, yy + 1.4), (ch, yy + 2.5)], False)}" fill="none" stroke="#000" stroke-opacity=".08" stroke-width="{ctx.u(1.6):.1f}"/>')
        if view == "back":
            body.folds.append(([(-6, yy + 1), (0, yy + 2.6), (6, yy + 1)], 1.0))
    if c.get("vee") and view == "front":
        v0 = fd + .3
        body.seams.append([(-2.6, v0 - .6), (0, v0 + 4.2), (2.6, v0 - .6)])
        body.stitch.append([(-1.7, v0 - .2), (0, v0 + 3.1), (1.7, v0 - .2)])
    if c.get("slits"):
        sl = c["slits"]
        hwid2 = c.get("hw", ch)
        for sg in (1, -1):
            body.stitch.append([(sg * (hwid2 - 1.0), L), (sg * (hwid2 - 1.0), L - sl), (sg * (hwid2 - .2), L - sl)])
            body.seams.append([(sg * (hwid2 - 1.6), L - sl - .2), (sg * hwid2, L - sl - .2)])
    if c.get("toggles") and view == "front":
        hw.append(_toggles(c))
    if c.get("underband"):
        ub = c["underband"]
        hwid2 = c.get("hw", ch)
        # already the hem band; add a soft seam stitch above it
        body.stitch.append(line((-hwid2, L - ub - .6), (hwid2, L - ub - .6), 4))

    pieces.append(body)
    for sp, _, _ in sleeves:
        pieces.append(sp)
    return pieces, hw, body


def _drawstring(e, sg, length):
    def f(ctx):
        x, y = e
        pts = cub((x, y), (x + sg * .2, y + length * .35), (x + sg * 1.4, y + length * .7), (x + sg * 1.1, y + length), 16)
        d = ctx.d(pts, False)
        w = ctx.u(1.0)
        end = pts[-1]
        ag = cub(end, add(end, (sg * -.05, 1.2)), add(end, (sg * -.1, 2.4)), add(end, (sg * -.12, 3.6)), 4)
        ex, ey = ctx.P(e)
        col = ctx.trim
        o = [f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="{w + 3:.1f}" stroke-linecap="round"/>',
             f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w:.1f}" stroke-linecap="round"/>',
             f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".12" stroke-width="{w:.1f}" stroke-linecap="round"/>',
             f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity=".10" stroke-width="{w * .3:.1f}" stroke-linecap="round" transform="translate({-w * .2:.1f},0)"/>',
             f'<path d="{ctx.d(ag, False)}" fill="none" stroke="#000" stroke-opacity=".45" stroke-width="{w + 2.4:.1f}" stroke-linecap="round"/>',
             f'<path d="{ctx.d(ag, False)}" fill="none" stroke="{HW}" stroke-width="{w:.1f}" stroke-linecap="round"/>',
             f'<path d="{ctx.d(ag, False)}" fill="none" stroke="{HW_DARK}" stroke-width="{w * .35:.1f}" stroke-linecap="round" transform="translate({w * .22:.1f},0)"/>',
             # eyelet
             f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{ctx.u(.95):.1f}" fill="{HW}" stroke="{HW_DARK}" stroke-width="1.6"/>',
             f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{ctx.u(.5):.1f}" fill="#1a1a1d"/>']
        return "".join(o)
    return f


def _zipper(y0, y1, kind):
    def f(ctx):
        tw = 1.25
        tape = [(-tw, y0), (tw, y0), (tw, y1), (-tw, y1)]
        tape_col = AOP_TRIM if ctx.aop else ctx.fabric
        o = [f'<path d="{ctx.d(tape)}" fill="{tape_col}"/><path d="{ctx.d(tape)}" fill="#000" fill-opacity=".18"/>',
             f'<path d="{ctx.d([(-tw + .35, y0 + .3), (-tw + .35, y1)], False)}" {STITCH}/>',
             f'<path d="{ctx.d([(tw - .35, y0 + .3), (tw - .35, y1)], False)}" {STITCH}/>']
        ta, tb = ctx.P((0, y0 + 2)), ctx.P((0, y1 - .3))
        tooth = max(ctx.u(.32), 2.4)
        tws = ctx.u(.42)
        o.append(f'<path d="M{ta[0] - tws / 2:.1f},{ta[1]:.1f} V{tb[1]:.1f}" stroke="{HW_DARK}" stroke-width="{tws:.1f}" stroke-dasharray="{tooth:.1f} {tooth:.1f}"/>')
        o.append(f'<path d="M{ta[0] + tws / 2:.1f},{ta[1] + tooth:.1f} V{tb[1]:.1f}" stroke="{HW}" stroke-width="{tws:.1f}" stroke-dasharray="{tooth:.1f} {tooth:.1f}"/>')
        o.append(f'<path d="{ctx.d(tape)}" {OUTLINE}/>')
        # slider + pull
        sx_, sy_ = ctx.P((0, y0 + .6))
        sw_, sh_ = ctx.u(1.5), ctx.u(2.6)
        gid = ctx.id("hw")
        ctx.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{HW}"/>'
                        f'<stop offset=".55" stop-color="#E4E6EA"/><stop offset="1" stop-color="{HW_DARK}"/></linearGradient>')
        o.append(f'<rect x="{sx_ - sw_ / 2:.1f}" y="{sy_:.1f}" width="{sw_:.1f}" height="{sh_:.1f}" rx="{sw_ * .3:.1f}" fill="url(#{gid})" stroke="#000" stroke-opacity=".45" stroke-width="1.5"/>')
        pw, ph = ctx.u(1.1), ctx.u(4.2)
        o.append(f'<rect x="{sx_ - pw / 2:.1f}" y="{sy_ + sh_ * .55:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="{pw * .45:.1f}" fill="url(#{gid})" stroke="#000" stroke-opacity=".45" stroke-width="1.5"/>')
        o.append(f'<rect x="{sx_ - pw * .22:.1f}" y="{sy_ + sh_ * .55 + ph * .55:.1f}" width="{pw * .44:.1f}" height="{ph * .3:.1f}" rx="{pw * .2:.1f}" fill="#1a1a1d" fill-opacity=".85"/>')
        return "".join(o)
    return f


def _toggles(c):
    def f(ctx):
        o = []
        L, hr, hwid = c["L"], c.get("hem_band", 0), c.get("hw", c["ch"])
        for sg in (1, -1):
            x0, y0 = sg * (hwid - 3.2), L - hr / 2
            cord = cub((x0, y0), (x0 - sg * .3, y0 + 2), (x0 - sg * 1.2, y0 + 4), (x0 - sg * 1.0, y0 + 6.5), 10)
            w = ctx.u(.55)
            o.append(f'<path d="{ctx.d(cord, False)}" fill="none" stroke="#000" stroke-opacity=".4" stroke-width="{w + 2.4:.1f}" stroke-linecap="round"/>')
            o.append(f'<path d="{ctx.d(cord, False)}" fill="none" stroke="{AOP_TRIM}" stroke-width="{w:.1f}" stroke-linecap="round"/>')
            tx, ty = ctx.P((x0 - sg * 1.05, y0 + 5.2))
            tw_, th_ = ctx.u(1.5), ctx.u(2.4)
            o.append(f'<rect x="{tx - tw_ / 2:.1f}" y="{ty - th_ / 2:.1f}" width="{tw_:.1f}" height="{th_:.1f}" rx="{tw_ * .35:.1f}" fill="#1a1a1d" stroke="#000" stroke-opacity=".5" stroke-width="1.5"/>')
            o.append(f'<rect x="{tx - tw_ * .3:.1f}" y="{ty - th_ * .38:.1f}" width="{tw_ * .18:.1f}" height="{th_ * .76:.1f}" rx="2" fill="#fff" fill-opacity=".18"/>')
            ex, ey = ctx.P((x0, y0))
            o.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{ctx.u(.6):.1f}" fill="{HW}" stroke="{HW_DARK}" stroke-width="1.4"/>')
        return "".join(o)
    return f


# ======================================================================
# layout (scale so the garment fills the canvas)
# ======================================================================
def layout(key, c):
    pts = []
    for view in ("front", "back"):
        R, A = right_half(c, view)
        pts += R + mx(R)
    if c.get("hood"):
        pts.append((0, -c["hood"]["hh"]))
    if c.get("long"):
        ls = c["long"]
        SP = (c["sw"], c["sd"])
        a = math.radians(ls["ang"])
        C1 = add(SP, (math.cos(a), math.sin(a)), ls["len"])
        C2 = add(C1, (-math.sin(a), math.cos(a)), ls["cw"])
        pts += [C1, C2, (-C1[0], C1[1]), (-C2[0], C2[1]), (C1[0] + 1.2, C1[1])]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    span = max(abs(x) for x in xs) * 2 + 1
    hgt = max(ys) - min(ys)
    s = min(c.get("wfill", .84) * 1000 / span, .86 * 1100 / hgt)
    top = CY - (min(ys) + max(ys)) / 2 * s
    bbox = (CX - span / 2 * s, top + min(ys) * s, CX + span / 2 * s, top + max(ys) * s)
    return {"s": s, "top": top, "bbox": bbox}


def make(key, c):
    lay = layout(key, c)

    def draw(view, fabric_hex, prints_markup, aop):
        ctx = Ctx(key, view, lay, fabric_hex, aop)
        pieces, hw, body = build(key, c, view)
        out = []
        for pc in pieces:
            out.append(render_piece(ctx, pc, prints_markup if pc is body else ""))
        for f in hw:
            out.append(f(ctx))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}"><defs>{"".join(ctx.defs)}</defs>'
                + "".join(out) + "</svg>")

    zones = {}
    for name, z in c["zones"].items():
        x0, y0, w, h = z[:4]
        zz = (round(CX + x0 * lay["s"], 1), round(lay["top"] + y0 * lay["s"], 1), round(w * lay["s"], 1), round(h * lay["s"], 1))
        zones[name] = zz + tuple(z[4:])
    return {"label_ro": c["label"], "views": ["front", "back"], "zones": zones,
            "aop_tile": c.get("aop_tile", 220), "draw": draw}


# ======================================================================
# garment specs (cm, flat measurements; x from centre front, y from HPS)
# ======================================================================
SPECS = {
    "tee_oversized": dict(
        label="Tricou oversized", nw=10, fd=10, bd=2.5, sw=31, sd=3.5, ch=33, L=74, dip=.6, nr=2.4,
        sleeve=dict(ang=31, len=23, open=22, ay=29.5),
        zones={"front_center": (-15, 18, 30, 38), "front_chest_left": (7, 15, 9, 9),
               "front_chest_center": (-7.5, 14.5, 15, 9), "back_center": (-16, 9.5, 32, 40),
               "back_neck": (-5, 6, 10, 3)}),
    "tee_baby_crop": dict(
        label="Baby tee", nw=8.5, fd=7.5, bd=2, sw=17.5, sd=4.5, ch=22, L=40, waist=(20.3, 30), hw=20.8, dip=.3, nr=1.6,
        sleeve=dict(ang=24, len=12.5, open=10.2, ay=17.5, cuff=1.6),
        zones={"front_center": (-10, 12, 20, 21), "front_chest_center": (-6.5, 10.5, 13, 7),
               "front_chest_left": (4.5, 10.5, 6.5, 6.5), "back_center": (-10, 7.5, 20, 23),
               "back_neck": (-4, 4.3, 8, 2.4)}),
    "tshirt_dress": dict(
        label="Rochie-tricou", nw=9.5, fd=9.5, bd=2.5, sw=28, sd=4, ch=29, L=90, hw=31.5, dip=.8, nr=2.2, slits=9,
        sleeve=dict(ang=31, len=21, open=19, ay=26.5),
        zones={"front_center": (-14, 17, 28, 36), "front_chest_left": (6.5, 14.5, 8.5, 8.5),
               "front_chest_center": (-7, 14, 14, 8.5), "back_center": (-15, 9, 30, 40),
               "back_neck": (-5, 5.8, 10, 3)}),
    "longsleeve": dict(
        label="Bluză cu mânecă lungă", nw=9.5, fd=9.5, bd=2.5, sw=29.5, sd=4, ch=30.5, ay=26, L=74, nr=2.2,
        long=dict(ang=77, len=62, cw=10.5, U=(22.5, 28), cuff=6),
        zones={"front_center": (-14, 17, 28, 36), "front_chest_left": (6.5, 14.5, 9, 9),
               "front_chest_center": (-7.5, 14, 15, 9), "back_center": (-15, 9.5, 30, 40),
               "back_neck": (-5, 6, 10, 3)}),
    "longsleeve_crop": dict(
        label="Bluză crop cu mânecă lungă", nw=8.5, fd=8, bd=2, sw=18, sd=4.5, ch=22, ay=17, L=42,
        waist=(20, 31), hw=20.6, dip=.3, nr=1.6, wfill=.80,
        long=dict(ang=70, len=59, cw=8.2, U=(16.2, 19.5), cuff=0),
        zones={"front_center": (-9, 12, 18, 20), "front_chest_center": (-6, 10.5, 12, 7),
               "front_chest_left": (4, 10.5, 6.5, 6.5), "back_center": (-9.5, 7, 19, 23),
               "back_neck": (-4, 4.2, 8, 2.4)}),
    "tank": dict(
        label="Maiou", nw=10.5, fd=13, bd=3, sw=18, sd=2.5, ch=33, ay=30, L=74, dip=.6, nr=1.8, ab=1.8,
        neck="bound", arm=((18.3, 15), (21.5, 29.2)), nflat=.6, nsteep=.6,
        zones={"front_center": (-14.5, 19, 29, 36), "front_chest_left": (6, 16.5, 8, 8),
               "back_center": (-14.5, 10, 29, 40), "back_neck": (-5, 6.5, 10, 3)}),
    "crop_tank": dict(
        label="Crop top", nw=7.6, fd=13, bd=10.5, sw=8.9, sd=0, ch=19.5, ay=15.5, L=31, waist=(18.6, 25), hw=18.9, dip=.3,
        nr=.9, ab=.9, neck="bound", arm=((9.1, 8.5), (12, 15)), nflat=.68, nsteep=.75, wfill=.80,
        zones={"front_chest_center": (-5, 15.3, 10, 5.5), "front_center": (-8, 15.3, 16, 12.5),
               "back_center": (-8, 13, 16, 13.5), "back_neck": (-3.5, 12, 7, 2)}),
    "sports_bra": dict(
        label="Bustieră sport", nw=6.4, fd=12.5, bd=9.5, sw=10.6, sd=0, ch=16.8, ay=15, ay_back=20, L=29, hw=16.2,
        nr=1.0, ab=1.0, neck="bound", arm=((11.1, 7.5), (12.6, 14.6)), racer=(3.4, 15.5), nflat=.62, nsteep=.75,
        hem_band=6, hem_kind="rib", wfill=.78, underband=6,
        zones={"front_center": (-5.5, 14.5, 11, 6.5)}),
    "hoodie": dict(
        label="Hanorac oversized", nw=10, fd=9, bd=2.5, sw=32, sd=4.5, ch=33, ay=28, L=72, hw=31.5, hem_band=7,
        hood=dict(hh=33, w=16), strings=24, pocket="kangaroo", pocket_box=(43, 65, 13, 20, 54),
        long=dict(ang=77, len=60, cw=11.8, U=(23.5, 30), cuff=7),
        zones={"front_center": (-14, 18.5, 28, 23), "front_chest_left": (7, 14.5, 9, 9),
               "front_chest_center": (-7, 13.5, 14, 8), "back_center": (-16, 9, 32, 40),
               "back_neck": (-5, 5, 10, 3)}),
    "crop_hoodie": dict(
        label="Hanorac crop", nw=9.5, fd=8.5, bd=2.3, sw=29, sd=4, ch=30, ay=25, L=47, hw=28.8, hem_band=6,
        hood=dict(hh=30, w=14.8), strings=20,
        long=dict(ang=77, len=55, cw=11, U=(21.5, 27), cuff=6.5),
        zones={"front_center": (-12.5, 15, 25, 23), "front_chest_center": (-6.5, 13, 13, 7),
               "front_chest_left": (6, 13, 8, 8), "back_center": (-14, 8, 28, 30),
               "back_neck": (-4.5, 4.7, 9, 2.7)}),
    "zip_hoodie": dict(
        label="Hanorac cu fermoar", nw=10, fd=8.5, bd=2.5, sw=32, sd=4.5, ch=33, ay=28, L=72, hw=31.5, hem_band=7,
        hood=dict(hh=33, w=16), strings=22, zip=True, pocket="split", pocket_box=(44, 65, 12, 19.5, 55),
        long=dict(ang=77, len=60, cw=11.8, U=(23.5, 30), cuff=7),
        zones={"front_chest_left": (4.2, 14, 9, 9), "back_center": (-16, 9, 32, 40),
               "back_neck": (-5, 5, 10, 3)}),
    "crewneck": dict(
        label="Bluză crewneck", nw=9.5, fd=9, bd=2.5, sw=31, sd=4.5, ch=32, ay=27, L=70, hw=30.5, hem_band=6.5,
        nr=2.8, vee=True, long=dict(ang=77, len=60, cw=11.5, U=(23, 29), cuff=7),
        zones={"front_center": (-14, 17, 28, 34), "front_chest_left": (7, 15, 9, 9),
               "front_chest_center": (-7.5, 15, 15, 9), "back_center": (-15, 9.5, 30, 40),
               "back_neck": (-5, 6.5, 10, 3)}),
    "windbreaker": dict(
        label="Geacă windbreaker", nw=10.5, fd=8, bd=2.5, sw=32.5, sd=5, ch=34, ay=29, L=72, hw=33, hem_band=3.5,
        hem_kind="elastic", hood=dict(hh=34, w=16.5), strings=0, zip=True, toggles=True, yoke_y=27, yoke_back=17,
        long=dict(ang=76, len=61, cw=12, U=(25, 31), cuff=4.5, cuff_kind="elastic"), aop_tile=260,
        zones={"front_chest_left": (4.5, 13, 9, 9), "back_center": (-15, 21, 30, 36),
               "back_neck": (-5, 5, 10, 3)}),
}

GARMENTS = {k: make(k, v) for k, v in SPECS.items()}
