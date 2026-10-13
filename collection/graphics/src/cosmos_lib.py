"""Shared helpers for the PROCEDURAL COSMOS set (g07, g08, g09, g20, g30, p01, p02, p08).

Every generator imports this module, builds a list of SVG strings and writes the
file with `write_svg`. Nothing here emits <text>, <style> or class attributes;
all ids are passed in already prefixed with the file name.
"""
import math
import os
import random
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]          # .../collection
sys.path.insert(0, str(ROOT / "tools"))
from text2path import outline          # noqa: E402
from warp_text import warp_text        # noqa: E402

import uharfbuzz as hb                 # noqa: E402
from fontTools.pens.svgPathPen import SVGPathPen      # noqa: E402
from fontTools.pens.transformPen import TransformPen  # noqa: E402
from fontTools.ttLib import TTFont     # noqa: E402

FONTS = ROOT / "fonts"

# collection palette
VOID = "#07070D"
INDIGO = "#24228A"
EBLUE = "#3D5AFE"
PERI = "#6C6CFF"
CYAN = "#5FF3FF"
LAV = "#C9C3FF"
CHROME = "#F2F4FF"
GOLD = "#F4B942"
ORANGE = "#FF4D2E"
MAGENTA = "#FF3DA8"
SIGNATURE = "LĂLÂU · NEPĂMÂNTEAN · 2026"


def font(name):
    return str(FONTS / name)


MICHROMA = font("Michroma-Regular.ttf")
SPACE = font("SpaceMono-Regular.ttf")
SPACE_B = font("SpaceMono-Bold.ttf")
UNB_BLACK = font("Unbounded-Black.ttf")
UNB_SEMI = font("Unbounded-SemiBold.ttf")
MONOTON = font("Monoton-Regular.ttf")
PLEX = font("IBMPlexMono-Medium.ttf")


def n(v, nd=1):
    """Compact number formatting."""
    s = f"{v:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def rgb2hex(c):
    c = np.clip(np.round(c), 0, 255).astype(int)
    return "#%02X%02X%02X" % tuple(c)


def mix(a, b, t):
    return rgb2hex(hex2rgb(a) * (1 - t) + hex2rgb(b) * t)


def ramp(stops, t):
    """stops: list of (pos, hex). Returns hex at t (0..1)."""
    t = min(max(t, 0.0), 1.0)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            u = 0 if p1 == p0 else (t - p0) / (p1 - p0)
            return mix(c0, c1, u)
    return stops[-1][1]


def star4(x, y, r, waist=0.08, rot=0.0, nd=1, bow=0.25):
    """Concave four-point sparkle. waist = half-width of the rays at the centre as a
    fraction of r; bow < 1 pulls the edges in towards the ray axes (concave sides)."""
    w = max(r * waist, 0.6)
    ca, sa = math.cos(rot), math.sin(rot)

    def P(u, v):          # local -> world (u along +x, v along +y before rotation)
        return (x + u * ca - v * sa, y + u * sa + v * ca)

    def fmt(p):
        return "%s %s" % (n(p[0], nd), n(p[1], nd))

    tips = [(0, -r), (r, 0), (0, r), (-r, 0)]
    waists = [(w, -w), (w, w), (-w, w), (-w, -w)]
    d = "M" + fmt(P(*tips[0]))
    for k in range(4):
        t0, wk, t1 = tips[k], waists[k], tips[(k + 1) % 4]
        # control points sit close to the ray axes -> needle-like, concave rays
        if t0[0] == 0:
            c1 = (wk[0] * bow, wk[1] * 2.6)
        else:
            c1 = (wk[0] * 2.6, wk[1] * bow)
        if t1[0] == 0:
            c2 = (wk[0] * bow, wk[1] * 2.6)
        else:
            c2 = (wk[0] * 2.6, wk[1] * bow)
        d += "Q" + fmt(P(*c1)) + " " + fmt(P(*wk))
        d += "Q" + fmt(P(*c2)) + " " + fmt(P(*t1))
    return d + "Z"


def radial_grad(gid, stops, cx="50%", cy="50%", r="50%", extra=""):
    """stops: list of (offset 0..1, color, opacity)."""
    s = [f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}"{extra}>']
    for o, c, op in stops:
        s.append(f'<stop offset="{n(o * 100, 1)}%" stop-color="{c}" stop-opacity="{n(op, 3)}"/>')
    s.append("</radialGradient>")
    return "".join(s)


def linear_grad(gid, stops, x1="0", y1="0", x2="0", y2="1", units=None):
    u = f' gradientUnits="{units}"' if units else ""
    s = [f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"{u}>']
    for o, c, op in stops:
        s.append(f'<stop offset="{n(o * 100, 2)}%" stop-color="{c}" stop-opacity="{n(op, 3)}"/>')
    s.append("</linearGradient>")
    return "".join(s)


def blur_filter(fid, std, pad=0.6, units_box=None):
    """Gaussian blur filter. units_box=(x,y,w,h) for userSpaceOnUse region."""
    if units_box:
        x, y, w, h = units_box
        reg = f'filterUnits="userSpaceOnUse" x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"'
    else:
        reg = f'x="-{n(pad)}" y="-{n(pad)}" width="{n(1 + 2 * pad)}" height="{n(1 + 2 * pad)}"'
    return (f'<filter id="{fid}" {reg} color-interpolation-filters="sRGB">'
            f'<feGaussianBlur stdDeviation="{n(std, 2)}"/></filter>')


def text_path(font_path, text, size, x, y, tracking=0, anchor="middle"):
    """Outline a line of text, returns dict(d, width, bbox)."""
    return outline(font_path, text, size, x, y, tracking, anchor)


def arc_text(font_path, text, size, cx, cy, radius, center_deg, tracking=0, outward=True, nd=2):
    """Outline text along a circle.

    outward=True: text sits on top of the circle (reads clockwise, letters point
    away from the centre) -- use for arcs above the centre.
    outward=False: reads counter-clockwise with letters pointing to the centre
    -- use for arcs below the centre so the text reads left-to-right.
    center_deg: angle (SVG convention, 0 = +x, 90 = down) at the middle of the text.
    Returns path d.
    """
    blob = hb.Blob.from_file_path(font_path)
    hfont = hb.Font(hb.Face(blob))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hfont, buf, {"kern": True, "liga": True})
    tt = TTFont(font_path)
    upem = tt["head"].unitsPerEm
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    scale = size / upem
    track = tracking / 1000.0 * upem
    pos = buf.glyph_positions
    infos = buf.glyph_infos
    total = (sum(p.x_advance for p in pos) + track * max(len(pos) - 1, 0)) * scale
    pen = SVGPathPen(gs, ntos=lambda v: n(v, nd))
    # arc length -> angle
    sweep = total / radius
    c0 = math.radians(center_deg)
    start = c0 - sweep / 2 if outward else c0 + sweep / 2
    pen_x = 0.0
    for i, (info, p) in enumerate(zip(infos, pos)):
        name = order[info.codepoint]
        adv = p.x_advance * scale
        # place glyph by its centre to keep it upright relative to the arc
        mid = pen_x * scale + adv / 2
        if outward:
            th = start + mid / radius
            t = (-math.sin(th), math.cos(th))
            up = (math.cos(th), math.sin(th))
        else:
            th = start - mid / radius
            t = (math.sin(th), -math.cos(th))
            up = (-math.cos(th), -math.sin(th))
        px, py = cx + radius * math.cos(th), cy + radius * math.sin(th)
        # font (fx, fy) -> world: p + (fx - adv/2/scale)*s*t + fy*s*up
        ox = px - adv / 2 * t[0]
        oy = py - adv / 2 * t[1]
        # TransformPen matrix (a, b, c, d, e, f): x' = a*x + c*y + e ; y' = b*x + d*y + f
        tr = (scale * t[0], scale * t[1], scale * up[0], scale * up[1], ox, oy)
        gs[name].draw(TransformPen(pen, tr))
        pen_x += p.x_advance + (track if i < len(pos) - 1 else 0)
    return pen.getCommands()


def write_svg(path, body, defs="", viewbox="0 0 1200 1500", extra_attrs=""):
    w, h = viewbox.split()[2:]
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" width="{w}" height="{h}"{extra_attrs}>']
    if defs:
        out.append("<defs>" + defs + "</defs>")
    out.append(body if isinstance(body, str) else "\n".join(body))
    out.append("</svg>\n")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = "\n".join(out)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(data)
    return len(data.encode("utf-8"))


# ---------------------------------------------------------------- seamless helpers

def wrap_offsets(x, y, margin, size=1000):
    """Offsets (dx, dy) at which an element of radius `margin` at (x, y) must be
    repeated so that it wraps around a size x size tile."""
    xs = [0]
    ys = [0]
    if x - margin < 0:
        xs.append(size)
    if x + margin > size:
        xs.append(-size)
    if y - margin < 0:
        ys.append(size)
    if y + margin > size:
        ys.append(-size)
    return [(dx, dy) for dx in xs for dy in ys]


def periodic_noise(size_px, octaves=((2, 1.0), (4, 0.5), (8, 0.25), (16, 0.125)), seed=0):
    """Tileable fractal noise on a size_px x size_px grid in [0, 1].
    Built from random-phase sinusoids with integer frequencies, so it wraps exactly."""
    rng = np.random.default_rng(seed)
    u = np.linspace(0, 1, size_px, endpoint=False)
    X, Y = np.meshgrid(u, u)
    field = np.zeros_like(X)
    for freq, amp in octaves:
        for _ in range(6):
            kx, ky = rng.integers(-freq, freq + 1, size=2)
            if kx == 0 and ky == 0:
                kx = freq
            ph = rng.uniform(0, 2 * math.pi)
            field += amp * np.cos(2 * math.pi * (kx * X + ky * Y) + ph)
    field -= field.min()
    field /= field.max()
    return field


def sample_field(field, x, y, size=1000):
    """Bilinear-free nearest sampling of a periodic field at tile coordinates."""
    m = field.shape[0]
    i = int((y % size) / size * m) % m
    j = int((x % size) / size * m) % m
    return field[i, j]
