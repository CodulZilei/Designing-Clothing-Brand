"""Shared helpers for the CRT / GLITCH / SIGNAL graphics (g03, g05, g19, g23, g24, m04, p03, p06, p10).

Everything here writes plain SVG strings: outlined text (no <text>), no <style>, no class,
and every id is prefixed with the file id passed to SVG(fid, ...).
"""
import math
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import uharfbuzz as hb  # noqa: E402
from fontTools.pens.svgPathPen import SVGPathPen  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402
from text2path import outline  # noqa: E402
from warp_text import warp_text  # noqa: E402

PAL = {
    "void": "#07070D",
    "indigo": "#24228A",
    "blue": "#3D5AFE",
    "peri": "#6C6CFF",
    "cyan": "#5FF3FF",
    "lav": "#C9C3FF",
    "white": "#F2F4FF",
    "gold": "#F4B942",
    "orange": "#FF4D2E",
    "magenta": "#FF3DA8",
}

FABRIC_DARK = "#111114"
FABRIC_LIGHT = "#F5F5F2"
FABRIC_LAV = "#C9C3E6"


def font(name):
    return os.path.join(ROOT, "fonts", name + ".ttf")


_num = re.compile(r"-?\d+(?:\.\d+)?(?:e-?\d+)?")


def f1(v, nd=1):
    s = f"{v:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s


def round_d(d, nd=1):
    return _num.sub(lambda m: f1(float(m.group(0)), nd), d)


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(a[i] + (b[i] - a[i]) * t):02X}" for i in range(3))


class SVG:
    def __init__(self, fid, w, h):
        self.fid, self.w, self.h = fid, w, h
        self.defs = []
        self.body = []
        self._atlas = {}

    def id(self, name):
        return f"{self.fid}-{name}"

    def ref(self, name):
        return f"url(#{self.fid}-{name})"

    def add(self, s):
        self.body.append(s)

    def d(self, s):
        self.defs.append(s)

    def tostring(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">']
        if self.defs:
            out.append("<defs>")
            out.extend(self.defs)
            out.append("</defs>")
        out.extend(self.body)
        out.append("</svg>")
        return "\n".join(out)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.tostring())
        return os.path.getsize(path)

    # ---------- text ----------
    def text_d(self, fname, text, size, x, y, anchor="start", tracking=0, warps=None, nd=1):
        """Outlined text path data + bbox."""
        if warps:
            r = warp_text(font(fname), text, size, x, y, warps=warps, tracking=tracking, anchor=anchor, ndp=nd)
            return r["d"], r["bbox"], r["width"]
        r = outline(font(fname), text, size, x, y, tracking, anchor)
        return round_d(r["d"], nd), r["bbox"], r["width"]

    def atlas(self, fname):
        if fname not in self._atlas:
            self._atlas[fname] = GlyphAtlas(self, fname)
        return self._atlas[fname]

    def small(self, fname, text, size, x, y, fill, anchor="start", tracking=0, opacity=None):
        return self.atlas(fname).line(text, size, x, y, fill, anchor, tracking, opacity)


class GlyphAtlas:
    """Defines each glyph once in <defs> (font units, integers) and places it with <use>.
    Keeps dense fine print small in bytes."""

    def __init__(self, svg, fname):
        self.svg = svg
        self.fname = fname
        self.key = re.sub(r"[^a-z0-9]", "", fname.lower())[:6]
        path = font(fname)
        blob = hb.Blob.from_file_path(path)
        self.hbfont = hb.Font(hb.Face(blob))
        self.tt = TTFont(path)
        self.upem = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.defined = {}

    def _glyph(self, gid):
        if gid in self.defined:
            return self.defined[gid]
        name = self.order[gid]
        pen = SVGPathPen(self.gs)
        self.gs[name].draw(pen)
        d = pen.getCommands()
        gidname = None
        if d:
            gidname = self.svg.id(f"{self.key}{gid}")
            # flip y in the def so uses can be placed with plain x/y
            self.svg.d(f'<path id="{gidname}" transform="scale(1 -1)" d="{round_d(d, 0)}"/>')
        self.defined[gid] = gidname
        return gidname

    def shape(self, text, tracking=0):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {"kern": True, "liga": True})
        track = tracking / 1000.0 * self.upem
        items = []
        pen_x = 0.0
        n = len(buf.glyph_infos)
        for i, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
            items.append((info.codepoint, pen_x + pos.x_offset, pos.y_offset))
            pen_x += pos.x_advance + (track if i < n - 1 else 0)
        return items, pen_x

    def width(self, text, size, tracking=0):
        _, w = self.shape(text, tracking)
        return w * size / self.upem

    def line(self, text, size, x, y, fill, anchor="start", tracking=0, opacity=None):
        items, w = self.shape(text, tracking)
        s = size / self.upem
        if anchor == "middle":
            x -= w * s / 2
        elif anchor == "end":
            x -= w * s
        uses = []
        for gid, gx, gy in items:
            ref = self._glyph(gid)
            if ref:
                ya = f' y="{f1(-gy, 0)}"' if gy else ""
                uses.append(f'<use href="#{ref}" x="{f1(gx, 0)}"{ya}/>')
        op = f' opacity="{opacity}"' if opacity is not None else ""
        return (f'<g fill="{fill}"{op} transform="translate({f1(x, 2)} {f1(y, 2)}) scale({f1(s, 5)})">'
                + "".join(uses) + "</g>")

    def wrap(self, text, size, width, tracking=0):
        words = text.split()
        lines, cur = [], ""
        for wd in words:
            t = (cur + " " + wd) if cur else wd
            if self.width(t, size, tracking) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, text, size, x, y, width, leading, fill, tracking=0, justify=True, opacity=None):
        """Wrapped paragraph; returns (svg, y_after). y is the first baseline."""
        out = []
        lines = self.wrap(text, size, width, tracking)
        for i, ln in enumerate(lines):
            last = i == len(lines) - 1
            if justify and not last and " " in ln:
                out.append(self._justified(ln, size, x, y, width, fill, tracking, opacity))
            else:
                out.append(self.line(ln, size, x, y, fill, "start", tracking, opacity))
            y += leading
        return "\n".join(out), y

    def _justified(self, ln, size, x, y, width, fill, tracking, opacity):
        words = ln.split(" ")
        ws = [self.width(wd, size, tracking) for wd in words]
        gap = (width - sum(ws)) / (len(words) - 1)
        out = []
        cx = x
        for wd, ww in zip(words, ws):
            out.append(self.line(wd, size, cx, y, fill, "start", tracking, opacity))
            cx += ww + gap
        return "".join(out)


# ---------- geometry helpers ----------

def rrect_d(x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    return (f"M{f1(x + r)} {f1(y)}H{f1(x + w - r)}A{f1(r)} {f1(r)} 0 0 1 {f1(x + w)} {f1(y + r)}"
            f"V{f1(y + h - r)}A{f1(r)} {f1(r)} 0 0 1 {f1(x + w - r)} {f1(y + h)}"
            f"H{f1(x + r)}A{f1(r)} {f1(r)} 0 0 1 {f1(x)} {f1(y + h - r)}V{f1(y + r)}"
            f"A{f1(r)} {f1(r)} 0 0 1 {f1(x + r)} {f1(y)}Z")


def poly_d(pts, close=True, nd=1):
    if not pts:
        return ""
    s = "M" + " L".join(f"{f1(p[0], nd)} {f1(p[1], nd)}" for p in pts)
    return s + ("Z" if close else "")


def crt_screen_pts(cx, cy, w, h, bulge=0.04, corner=0.16, n=48):
    """Classic CRT tube face: a rounded rectangle whose sides bow outward slightly."""
    pts = []
    hw, hh = w / 2, h / 2
    rc = corner * min(w, h)
    # superellipse-ish construction: go around the perimeter
    def side(p0, p1, normal, amount, steps):
        res = []
        for i in range(steps):
            t = i / steps
            x = p0[0] + (p1[0] - p0[0]) * t
            y = p0[1] + (p1[1] - p0[1]) * t
            b = amount * math.sin(math.pi * t)
            res.append((x + normal[0] * b, y + normal[1] * b))
        return res

    def corner_arc(c, a0, a1, steps):
        return [(c[0] + rc * math.cos(a0 + (a1 - a0) * i / steps), c[1] + rc * math.sin(a0 + (a1 - a0) * i / steps))
                for i in range(steps)]

    bx, by = bulge * w, bulge * h
    l, r, t, b = cx - hw, cx + hw, cy - hh, cy + hh
    pts += side((l + rc, t), (r - rc, t), (0, -1), by, n)
    pts += corner_arc((r - rc, t + rc), -math.pi / 2, 0, 10)
    pts += side((r, t + rc), (r, b - rc), (1, 0), bx, n)
    pts += corner_arc((r - rc, b - rc), 0, math.pi / 2, 10)
    pts += side((r - rc, b), (l + rc, b), (0, 1), by, n)
    pts += corner_arc((l + rc, b - rc), math.pi / 2, math.pi, 10)
    pts += side((l, b - rc), (l, t + rc), (-1, 0), bx, n)
    pts += corner_arc((l + rc, t + rc), math.pi, 1.5 * math.pi, 10)
    return pts


def circle_pts(cx, cy, r, n=96, a0=0.0):
    return [(cx + r * math.cos(a0 + 2 * math.pi * i / n), cy + r * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def scanline_pattern(svg, name, period=6, dark=2.6, color="#07070D", opacity=0.5, w=1200):
    pid = svg.id(name)
    svg.d(f'<pattern id="{pid}" patternUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{period}">'
          f'<rect x="0" y="{f1(period - dark)}" width="{w}" height="{dark}" fill="{color}" fill-opacity="{opacity}"/></pattern>')
    return pid


def subpixel_pattern(svg, name, stripe=3, colors=("#FF8A8A", "#8AFFB4", "#8AA8FF"), h=1500):
    pid = svg.id(name)
    period = stripe * 3
    rects = "".join(f'<rect x="{i * stripe}" y="0" width="{stripe}" height="{h}" fill="{c}"/>' for i, c in enumerate(colors))
    svg.d(f'<pattern id="{pid}" patternUnits="userSpaceOnUse" x="0" y="0" width="{period}" height="{h}">{rects}</pattern>')
    return pid


# ---------- rendering ----------

def render(svg_path, out_dir=None, sizes="900", bg=FABRIC_DARK):
    out_dir = out_dir or os.path.join(ROOT, "previews", "graphics")
    env = dict(os.environ, NODE_PATH="/opt/node22/lib/node_modules")
    r = subprocess.run(["node", os.path.join(ROOT, "tools", "render.js"), out_dir, svg_path, "--sizes", sizes, "--bg", bg],
                       capture_output=True, text=True, env=env)
    if r.returncode:
        print(r.stderr)
    return r.stdout.strip().splitlines()
