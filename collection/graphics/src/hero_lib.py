"""Shared helpers for the HERO TYPOGRAPHY & LABELS set (g01, g02, g10, g18, g29, g34, m03, m06).

Builds on crt_lib (SVG container + glyph atlas for fine print) and cosmos_lib (sparkles).
No <text>, <style> or class; every id goes through svg.id() so it carries the file name.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from crt_lib import (FABRIC_DARK, FABRIC_LAV, FABRIC_LIGHT, PAL, ROOT, SVG, f1, font,  # noqa: E402,F401
                     mix, render, round_d)
from cosmos_lib import star4  # noqa: E402,F401
import warp_text as _wt  # noqa: E402

SIGNATURE = "ONYXLAB · NEPĂMÂNTEAN · 2026"
UNB = "Unbounded-Black"
UNB_S = "Unbounded-SemiBold"
MICH = "Michroma-Regular"
MONO = "SpaceMono-Regular"
MONO_B = "SpaceMono-Bold"


# ------------------------------------------------------------------ warped type

def warped(fname, text, size, x, y, warps=(), tracking=0, anchor="middle", sy=1.0, steps=8, nd=1):
    """Outline + optional vertical stretch (sy, about the baseline) + warps.
    Returns (d, bbox)."""
    contours, _ = _wt._shape_contours(font(fname), text, size, x, y, tracking, anchor, steps)
    if sy != 1.0:
        contours = [[(px, y + (py - y) * sy) for px, py in c] for c in contours]
    for spec in warps:
        contours = _wt._apply(contours, spec)
    d = " ".join("M" + " L".join(f"{f1(px, nd)} {f1(py, nd)}" for px, py in c) + " Z" for c in contours if c)
    return d, _wt._bbox(contours)


def extrude(svg, name, d, depth=24, dx=0.9, dy=2.2, back="#0B0A33", front="#3530B0", x=0, y=0):
    """3D extrusion: the glyph path is defined once and stacked with <use>, darkest at the back."""
    pid = svg.id(name)
    svg.d(f'<path id="{pid}" d="{d}"/>')
    out = []
    for i in range(depth, 0, -1):
        t = 1 - (i - 1) / max(depth - 1, 1)
        out.append(f'<use href="#{pid}" x="{f1(x + dx * i, 2)}" y="{f1(y + dy * i, 2)}" fill="{mix(back, front, t ** 1.4)}"/>')
    return pid, "".join(out)


# ------------------------------------------------------------------ small parts

def sparkles(rnd, n, box, rmin=5, rmax=20, color="#F2F4FF", avoid=None, glow_id=None):
    """Four-point sparkles + tiny dots scattered in box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    out = []
    for _ in range(n):
        for _try in range(30):
            px, py = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
            if not avoid or not avoid(px, py):
                break
        r = rmin + (rmax - rmin) * rnd.random() ** 2.2
        if r > rmin + 3:
            out.append(f'<path d="{star4(px, py, r, waist=0.09)}" fill="{color}"/>')
            if glow_id and r > rmax * 0.55:
                out.append(f'<circle cx="{f1(px)}" cy="{f1(py)}" r="{f1(r * 0.45)}" fill="{color}" opacity="0.55" filter="url(#{glow_id})"/>')
        else:
            out.append(f'<circle cx="{f1(px)}" cy="{f1(py)}" r="{f1(rnd.uniform(1.6, 2.6))}" fill="{color}" opacity="{f1(rnd.uniform(0.5, 1), 2)}"/>')
    return "".join(out)


def globe(cx, cy, r, color, sw=2.6, tilt=-18, lat=5, lon=6, opacity=1.0, orbit=False):
    """Wireframe globe (orthographic): outline, latitude chords, meridian ellipses."""
    g = [f'<g fill="none" stroke="{color}" stroke-width="{f1(sw, 2)}" opacity="{f1(opacity, 2)}" '
         f'transform="rotate({tilt} {f1(cx)} {f1(cy)})">']
    g.append(f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(r)}"/>')
    for i in range(1, lat + 1):
        a = -math.pi / 2 + i * math.pi / (lat + 1)
        yy = cy + r * math.sin(a)
        hw = r * math.cos(a)
        g.append(f'<ellipse cx="{f1(cx)}" cy="{f1(yy)}" rx="{f1(hw)}" ry="{f1(hw * 0.16)}"/>')
    for j in range(lon):
        a = j * math.pi / lon + 0.25
        rx = abs(r * math.cos(a))
        if rx > sw:
            g.append(f'<ellipse cx="{f1(cx)}" cy="{f1(cy)}" rx="{f1(rx)}" ry="{f1(r)}"/>')
    g.append(f'<line x1="{f1(cx)}" y1="{f1(cy - r)}" x2="{f1(cx)}" y2="{f1(cy + r)}"/>')
    if orbit:
        g.append(f'<ellipse cx="{f1(cx)}" cy="{f1(cy)}" rx="{f1(r * 1.55)}" ry="{f1(r * 0.38)}"/>')
    g.append("</g>")
    return "".join(g)


def barcode(rnd, x, y, w, h, color, minw=2.6, opacity=1.0):
    bars = []
    cx = x
    while cx < x + w - minw:
        bw = minw * rnd.choice((1, 1, 1, 2, 2, 3))
        if cx + bw > x + w:
            break
        if rnd.random() < 0.55:
            bars.append(f'M{f1(cx)} {f1(y)}h{f1(bw)}v{f1(h)}h-{f1(bw)}Z')
        cx += bw
    return f'<path d="{"".join(bars)}" fill="{color}" opacity="{f1(opacity, 2)}"/>'


def reg_mark(cx, cy, r, color, sw=2.6):
    return (f'<g fill="none" stroke="{color}" stroke-width="{sw}"><circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(r)}"/>'
            f'<path d="M{f1(cx - r * 1.6)} {f1(cy)}H{f1(cx + r * 1.6)}M{f1(cx)} {f1(cy - r * 1.6)}V{f1(cy + r * 1.6)}"/></g>'
            f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(r * 0.42)}" fill="{color}"/>')


def n_badge(svg, cx, cy, r, ink, knock, ring=None, sw=None, orbit=True, name="nbadge"):
    """The collection's classification mark: a giant 'N' in a disc crossed by an orbit ring.
    ink = disc colour, knock = colour of the N (fabric / card colour)."""
    sw = sw or max(2.6, r * 0.035)
    ring = ring or ink
    out = [f'<circle cx="{f1(cx)}" cy="{f1(cy)}" r="{f1(r)}" fill="{ink}"/>']
    size = r * 1.38
    d, bb, _ = svg.text_d(UNB, "N", size, cx, cy + size * 0.375, anchor="middle", nd=1)
    out.append(f'<path d="{d}" fill="{knock}"/>')
    if orbit:
        # orbit ring passing behind the disc on top and in front at the bottom
        rx, ry, rot = r * 1.42, r * 0.36, -16
        cid = svg.id(f"{name}-front")
        svg.d(f'<clipPath id="{cid}"><rect x="{f1(cx - rx * 1.2)}" y="{f1(cy)}" width="{f1(rx * 2.4)}" height="{f1(r * 1.2)}" '
              f'transform="rotate({rot} {f1(cx)} {f1(cy)})"/></clipPath>')
        cid2 = svg.id(f"{name}-back")
        svg.d(f'<clipPath id="{cid2}"><path fill-rule="evenodd" d="M{f1(cx - rx * 1.3)} {f1(cy - r * 1.4)}h{f1(rx * 2.6)}v{f1(r * 2.8)}h-{f1(rx * 2.6)}Z'
              f'M{f1(cx + r * 1.08)} {f1(cy)}a{f1(r * 1.08)} {f1(r * 1.08)} 0 1 0 -{f1(r * 2.16)} 0a{f1(r * 1.08)} {f1(r * 1.08)} 0 1 0 {f1(r * 2.16)} 0Z"/></clipPath>')
        ell = f'<ellipse cx="{f1(cx)}" cy="{f1(cy)}" rx="{f1(rx)}" ry="{f1(ry)}" transform="rotate({rot} {f1(cx)} {f1(cy)})"'
        out.insert(0, f'<g clip-path="url(#{cid2})">{ell} fill="none" stroke="{ring}" stroke-width="{f1(sw * 1.4, 2)}"/></g>')
        # front arc: gap ring in knock colour then the ring itself
        out.append(f'<g clip-path="url(#{cid})">{ell} fill="none" stroke="{knock}" stroke-width="{f1(sw * 4.2, 2)}"/>'
                   f'{ell} fill="none" stroke="{ring}" stroke-width="{f1(sw * 1.4, 2)}"/></g>')
        # small moon on the orbit
        a = math.radians(200)
        mx = cx + rx * math.cos(a) * math.cos(math.radians(rot)) - ry * math.sin(a) * math.sin(math.radians(rot))
        my = cy + rx * math.cos(a) * math.sin(math.radians(rot)) + ry * math.sin(a) * math.cos(math.radians(rot))
        out.append(f'<circle cx="{f1(mx)}" cy="{f1(my)}" r="{f1(r * 0.085)}" fill="{ring}"/>')
    return "".join(out)


def rrect(x, y, w, h, r):
    return (f'M{f1(x + r)} {f1(y)}H{f1(x + w - r)}A{f1(r)} {f1(r)} 0 0 1 {f1(x + w)} {f1(y + r)}V{f1(y + h - r)}'
            f'A{f1(r)} {f1(r)} 0 0 1 {f1(x + w - r)} {f1(y + h)}H{f1(x + r)}A{f1(r)} {f1(r)} 0 0 1 {f1(x)} {f1(y + h - r)}'
            f'V{f1(y + r)}A{f1(r)} {f1(r)} 0 0 1 {f1(x + r)} {f1(y)}Z')


def notched(x, y, w, h, c):
    """Rectangle with chamfered (cut) corners."""
    return (f'M{f1(x + c)} {f1(y)}H{f1(x + w - c)}L{f1(x + w)} {f1(y + c)}V{f1(y + h - c)}L{f1(x + w - c)} {f1(y + h)}'
            f'H{f1(x + c)}L{f1(x)} {f1(y + h - c)}V{f1(y + c)}Z')


def check(path, viewbox):
    """Quick technical check of a generated file. Returns list of problems."""
    import re
    import xml.etree.ElementTree as ET
    probs = []
    fid = os.path.basename(path)[:-4]
    data = open(path, encoding="utf-8").read()
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        return [f"{fid}: XML {e}"]
    if root.get("viewBox") != viewbox:
        probs.append(f"{fid}: viewBox {root.get('viewBox')}")
    if "<text" in data or "<style" in data or "class=" in data:
        probs.append(f"{fid}: forbidden element")
    for m in re.finditer(r'\sid="([^"]+)"', data):
        if not m.group(1).startswith(fid + "-"):
            probs.append(f"{fid}: bad id {m.group(1)}")
            break
    if len(data.encode()) > 1_500_000:
        probs.append(f"{fid}: size {len(data.encode())}")
    return probs
