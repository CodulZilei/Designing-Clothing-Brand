#!/usr/bin/env python3
"""m06 — NEPĂMÂNTEAN one-line wordmark in Michroma, tracked wide. viewBox 0 0 1200 240.
Run: python3 graphics/src/m06-dark.py   (writes m06-dark.svg and m06-light.svg)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_lib import MICH, ROOT, SVG, star4  # noqa: E402

INKS = {"dark": ("#F2F4FF", "#C9C3FF"), "light": ("#07070D", "#3D5AFE")}


def build(variant):
    fid = f"m06-{variant}"
    ink, acc = INKS[variant]
    svg = SVG(fid, 1200, 240)
    d, bb, w = svg.text_d(MICH, "NEPĂMÂNTEAN", 66, 600, 0, anchor="middle", tracking=330)
    top, bot = bb[1], bb[3]
    dy = 120 - (top + bot) / 2 + 4
    svg.add(f'<path d="{d}" fill="{ink}" transform="translate(0 {dy:.1f})"/>')
    x0, x1 = bb[0], bb[2]
    yc = dy - 66 * 0.75 / 2
    for x in (x0 - 44, x1 + 44):
        svg.add(f'<path d="{star4(x, yc, 13, waist=0.12)}" fill="{acc}"/>')
    out = os.path.join(ROOT, "graphics", fid + ".svg")
    print(out, svg.save(out), bb)


if __name__ == "__main__":
    for v in (sys.argv[1:] or ["dark", "light"]):
        build(v)
