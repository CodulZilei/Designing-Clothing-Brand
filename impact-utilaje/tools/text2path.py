#!/usr/bin/env python3
"""Turn a line of text into an outlined SVG path, shaped with HarfBuzz (kerning included).

Usage:
  python3 text2path.py FONT.ttf "TEXT" --size 100 [--x 0] [--y 0] [--tracking 0] [--fill "#000"] [--anchor start|middle|end] [--json]

Prints a <path d="..."/> element whose baseline starts at (x, y), sized so that
1 em = --size user units. --tracking adds extra space between letters, in
thousandths of an em (like letter-spacing in design tools). --json prints
{"d": ..., "width": ..., "ascent": ..., "capHeight": ..., "bbox": [x0, y0, x1, y1]}
so a layout script can position the text exactly.

Fonts live in ../fonts. Every logo file must use outlined text from this tool
(no <text> elements), so print shops can open the SVG without the fonts.
"""
import argparse
import json
import sys

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


def outline(font_path, text, size, x=0.0, y=0.0, tracking=0.0, anchor="start"):
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})

    tt = TTFont(font_path)
    upem = tt["head"].unitsPerEm
    glyph_set = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = size / upem
    track_units = tracking / 1000.0 * upem

    infos, positions = buf.glyph_infos, buf.glyph_positions
    total_adv = sum(p.x_advance for p in positions) + track_units * max(len(positions) - 1, 0)
    width = total_adv * scale
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width

    svg_pen = SVGPathPen(glyph_set)
    bounds_pen = BoundsPen(glyph_set)
    pen_x = 0.0
    for i, (info, pos) in enumerate(zip(infos, positions)):
        name = order[info.codepoint]
        gx = pen_x + pos.x_offset
        gy = pos.y_offset
        # font units are y-up; SVG is y-down
        t = (scale, 0, 0, -scale, x + gx * scale, y - gy * scale)
        glyph_set[name].draw(TransformPen(svg_pen, t))
        glyph_set[name].draw(TransformPen(bounds_pen, t))
        pen_x += pos.x_advance + (track_units if i < len(positions) - 1 else 0)

    os2 = tt["OS/2"] if "OS/2" in tt else None
    cap = getattr(os2, "sCapHeight", 0) if os2 else 0
    return {
        "d": svg_pen.getCommands(),
        "width": round(width, 3),
        "ascent": round(tt["hhea"].ascent * scale, 3),
        "capHeight": round((cap or 0) * scale, 3),
        "bbox": [round(v, 3) for v in (bounds_pen.bounds or (0, 0, 0, 0))],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("text")
    ap.add_argument("--size", type=float, default=100)
    ap.add_argument("--x", type=float, default=0)
    ap.add_argument("--y", type=float, default=0)
    ap.add_argument("--tracking", type=float, default=0)
    ap.add_argument("--fill", default="#111111")
    ap.add_argument("--anchor", default="start", choices=["start", "middle", "end"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = outline(a.font, a.text, a.size, a.x, a.y, a.tracking, a.anchor)
    if a.json:
        json.dump(r, sys.stdout)
    else:
        sys.stdout.write('<path fill="%s" d="%s"/>\n' % (a.fill, r["d"]))


if __name__ == "__main__":
    main()
