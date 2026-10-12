#!/usr/bin/env python3
"""Generate a clean gear (cog) outline as an SVG path.

Usage:
  python3 gear.py --cx 200 --cy 200 --r-outer 120 --r-root 100 --teeth 10 [--hole 60] [--tip 0.42] [--base 0.6] [--rotate 0] [--json]

--r-outer  radius at the tooth tips
--r-root   radius at the bottom of the gaps between teeth
--teeth    number of teeth
--hole     radius of the centre hole (0 = solid); drawn as a second subpath with
           the opposite winding, so fill-rule nonzero and evenodd both cut it out
--tip      tooth width at the tip, as a fraction of the angular pitch
--base     tooth width at the root, as a fraction of the angular pitch (> tip gives trapezoid teeth)
--rotate   rotation in degrees (0 puts a tooth centred at 12 o'clock)

Prints <path d="..."/> or, with --json, {"d": ...}.
"""
import argparse
import json
import math


def gear_path(cx, cy, r_outer, r_root, teeth, hole=0.0, tip=0.42, base=0.6, rotate=0.0, ndp=2):
    pitch = 2 * math.pi / teeth
    rot = math.radians(rotate) - math.pi / 2  # tooth at 12 o'clock
    pts = []
    for i in range(teeth):
        c = rot + i * pitch
        for ang, r in ((c - pitch * base / 2, r_root), (c - pitch * tip / 2, r_outer),
                       (c + pitch * tip / 2, r_outer), (c + pitch * base / 2, r_root)):
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    f = lambda v: f"{v:.{ndp}f}".rstrip("0").rstrip(".")
    d = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"
    if hole > 0:
        # counter-clockwise circle (opposite winding to the clockwise outline)
        d += (f" M{f(cx + hole)} {f(cy)} A{f(hole)} {f(hole)} 0 1 0 {f(cx - hole)} {f(cy)}"
              f" A{f(hole)} {f(hole)} 0 1 0 {f(cx + hole)} {f(cy)} Z")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cx", type=float, default=0)
    ap.add_argument("--cy", type=float, default=0)
    ap.add_argument("--r-outer", type=float, required=True)
    ap.add_argument("--r-root", type=float, required=True)
    ap.add_argument("--teeth", type=int, required=True)
    ap.add_argument("--hole", type=float, default=0)
    ap.add_argument("--tip", type=float, default=0.42)
    ap.add_argument("--base", type=float, default=0.6)
    ap.add_argument("--rotate", type=float, default=0)
    ap.add_argument("--fill", default="#F2A20A")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    d = gear_path(a.cx, a.cy, a.r_outer, a.r_root, a.teeth, a.hole, a.tip, a.base, a.rotate)
    if a.json:
        print(json.dumps({"d": d}))
    else:
        print(f'<path fill="{a.fill}" fill-rule="evenodd" d="{d}"/>')


if __name__ == "__main__":
    main()
