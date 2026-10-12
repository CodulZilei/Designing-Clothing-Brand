#!/usr/bin/env python3
"""Outline text and bend it (arc, wave/flag, bulge, perspective, rise), for warped
streetwear lettering such as wavy 3D slogans.

Usage:
  python3 warp_text.py FONT "TEXT" --size 200 [--x 600] [--y 400] [--anchor middle]
         [--tracking 0] [--warp wave:0.18:1.0:0] [--warp bulge:0.35] [--steps 10] [--json]

Warps are applied in the order given; each works on the text's own bounding box
(u = 0..1 left→right, v = 0..1 top→bottom), and amounts are fractions of the
text height:
  arc:B                 bend the whole line up (B>0) or down (B<0) like a rainbow
  wave:A:CYCLES:PHASE   sine wave (flag); A amplitude, CYCLES across the width, PHASE in turns
  bulge:S               swell the middle vertically (S>0) or pinch it (S<0)
  fisheye:S             swell from the centre in both directions
  perspective:P         top narrower than bottom (P>0) or wider (P<0), P = 0..0.9
  rise:R                tilt: right end higher (R>0)

From Python:  from warp_text import warp_text; r = warp_text(font, text, size, x, y, warps=[...])
returns {"d": path, "bbox": [x0, y0, x1, y1], "width": w}. Curves are flattened to
short line segments (--steps per curve) so the warp stays smooth; the result is a
plain polygon path with fill-rule nonzero (counters stay open).
"""
import argparse
import json
import math
import sys

import uharfbuzz as hb
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


class FlattenPen(BasePen):
    def __init__(self, glyph_set, steps=10):
        super().__init__(glyph_set)
        self.steps = steps
        self.contours = []
        self.cur = None

    def _moveTo(self, p):
        self.cur = [p]
        self.contours.append(self.cur)

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((
                mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
                mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                             mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        self.cur = None

    _endPath = _closePath


def _shape_contours(font_path, text, size, x, y, tracking, anchor, steps):
    blob = hb.Blob.from_file_path(font_path)
    font = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    tt = TTFont(font_path)
    upem = tt["head"].unitsPerEm
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = size / upem
    track = tracking / 1000.0 * upem
    pos = buf.glyph_positions
    width = (sum(p.x_advance for p in pos) + track * max(len(pos) - 1, 0)) * scale
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    pen = FlattenPen(gs, steps)
    pen_x = 0.0
    for i, (info, p) in enumerate(zip(buf.glyph_infos, pos)):
        t = (scale, 0, 0, -scale, x + (pen_x + p.x_offset) * scale, y - p.y_offset * scale)
        gs[order[info.codepoint]].draw(TransformPen(pen, t))
        pen_x += p.x_advance + (track if i < len(pos) - 1 else 0)
    return pen.contours, width


def _bbox(contours):
    xs = [p[0] for c in contours for p in c]
    ys = [p[1] for c in contours for p in c]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)


def _apply(contours, spec):
    x0, y0, x1, y1 = _bbox(contours)
    w, h = max(x1 - x0, 1e-6), max(y1 - y0, 1e-6)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    kind, *args = spec.split(":")
    a = [float(v) for v in args]

    def f(px, py):
        u, v = (px - x0) / w, (py - y0) / h
        if kind == "arc":
            return px, py - a[0] * h * (1 - (2 * u - 1) ** 2)
        if kind == "wave":
            amp, cyc = a[0], (a[1] if len(a) > 1 else 1.0)
            ph = a[2] if len(a) > 2 else 0.0
            return px, py + amp * h * math.sin(2 * math.pi * (u * cyc + ph))
        if kind == "bulge":
            return px, cy + (py - cy) * (1 + a[0] * (1 - (2 * u - 1) ** 2))
        if kind == "fisheye":
            dx, dy = (px - cx) / (w / 2), (py - cy) / (h / 2)
            r2 = min(dx * dx + dy * dy, 1.0)
            k = 1 + a[0] * (1 - r2)
            return cx + (px - cx) * k, cy + (py - cy) * k
        if kind == "perspective":
            k = 1 - a[0] * (1 - v)
            return cx + (px - cx) * k, py
        if kind == "rise":
            return px, py - a[0] * h * (u - 0.5)
        raise ValueError("unknown warp " + kind)

    return [[f(px, py) for px, py in c] for c in contours]


def warp_text(font_path, text, size, x=0.0, y=0.0, warps=(), tracking=0.0, anchor="start", steps=10, ndp=2):
    contours, width = _shape_contours(font_path, text, size, x, y, tracking, anchor, steps)
    for spec in warps:
        contours = _apply(contours, spec)
    fmt = lambda v: f"{v:.{ndp}f}".rstrip("0").rstrip(".")
    d = " ".join("M" + " L".join(f"{fmt(px)} {fmt(py)}" for px, py in c) + " Z" for c in contours if c)
    return {"d": d, "bbox": [round(v, 2) for v in _bbox(contours)], "width": round(width, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("text")
    ap.add_argument("--size", type=float, default=200)
    ap.add_argument("--x", type=float, default=0)
    ap.add_argument("--y", type=float, default=0)
    ap.add_argument("--tracking", type=float, default=0)
    ap.add_argument("--anchor", default="start", choices=["start", "middle", "end"])
    ap.add_argument("--warp", action="append", default=[])
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--fill", default="#6C6CFF")
    ap.add_argument("--json", action="store_true")
    o = ap.parse_args()
    r = warp_text(o.font, o.text, o.size, o.x, o.y, o.warp, o.tracking, o.anchor, o.steps)
    if o.json:
        json.dump(r, sys.stdout)
    else:
        sys.stdout.write(f'<path fill="{o.fill}" d="{r["d"]}"/>\n')


if __name__ == "__main__":
    main()
