#!/usr/bin/env python3
"""Mockup engine for the NEPĂMÂNTEAN collection.

Puts graphics (graphics/*.svg) and all-over patterns (patterns/*.svg) onto garment
drawings (engine/garments/*.py) for every product in products.json, then renders
PNG/JPEG previews with the preinstalled Chromium.

Commands (run from the collection folder):
  python3 engine/engine.py build [--ids B01,F03] [--width 760]   # products -> mockups/svg + mockups/web/*.jpg
  python3 engine/engine.py test --garment tee_oversized          # one garment, placeholder prints in every zone, all views
  python3 engine/engine.py test --all                            # every registered garment
  python3 engine/engine.py sheet [--ids ...] [--out previews/sheet.png] [--cols 6]   # contact sheet of built mockups

Garment modules (engine/garments/*.py) each expose GARMENTS = {key: spec}, where spec is
  {
    "label_ro": "Tricou oversized",
    "views": ["front", "back"],             # accessories may have only ["front"]
    "zones": {"front_center": (x, y, w, h[, rot]), ...},   # canvas coords, see CANVAS
    "aop_tile": 220,                        # size of one pattern tile on this garment (canvas units)
    "draw": draw,                           # draw(view, fabric_hex, prints_markup, aop) -> full <svg> string
  }
draw() must return an <svg xmlns=... viewBox="0 0 1000 1100"> that paints the garment in
fabric_hex (or, when aop is given, fills the printable body with url(#<aop["id"]>) after
emitting aop["defs"] inside its <defs>), renders prints_markup clipped to the garment body
and UNDER its shading/seam layers, and adds shading, seams and outline on top.
"""
import argparse
import importlib
import json
import os
import pkgutil
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CANVAS = (1000, 1100)
NODE_PATH = "/opt/node22/lib/node_modules"
RENDER_JS = os.path.join(ROOT, "tools", "render.js")

sys.path.insert(0, HERE)


# ---------- registry ----------
def registry():
    import garments  # noqa: F401  (package in engine/garments)
    reg = {}
    for m in pkgutil.iter_modules([os.path.join(HERE, "garments")]):
        if m.name.startswith("_") or m.name == "common":
            continue
        mod = importlib.import_module("garments." + m.name)
        for k, spec in getattr(mod, "GARMENTS", {}).items():
            if k in reg:
                raise SystemExit(f"garment {k} defined twice")
            reg[k] = spec
    return reg


# ---------- SVG loading ----------
_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.S)


def load_svg(path):
    """Return (viewBox tuple, inner markup) of an SVG file."""
    src = open(path, encoding="utf-8").read()
    src = re.sub(r"<\?xml[^>]*\?>", "", src)
    src = re.sub(r"<!DOCTYPE[^>]*>", "", src)
    m = _SVG_OPEN.search(src)
    if not m:
        raise ValueError(f"{path}: no <svg> root")
    vb = re.search(r'viewBox\s*=\s*"([^"]+)"', m.group(0))
    if not vb:
        raise ValueError(f"{path}: root <svg> has no viewBox")
    box = tuple(float(v) for v in re.split(r"[\s,]+", vb.group(1).strip()))
    inner = src[m.end():src.rfind("</svg>")]
    return box, inner


def prefix_ids(markup, prefix):
    """Make every id in markup unique so several graphics can live in one SVG."""
    ids = set(re.findall(r'\bid\s*=\s*"([^"]+)"', markup))
    if not ids:
        return markup
    def ref(m):
        return m.group(1) + (prefix + m.group(2) if m.group(2) in ids else m.group(2)) + m.group(3)
    markup = re.sub(r'(\bid\s*=\s*")([^"]+)(")', ref, markup)
    markup = re.sub(r'(url\(\s*#)([^)\s]+)(\s*\))', ref, markup)
    markup = re.sub(r'((?:xlink:)?href\s*=\s*"#)([^"]+)(")', ref, markup)
    return markup


def asset_path(kind, name):
    folder = "graphics" if kind == "graphic" else "patterns"
    return os.path.join(ROOT, folder, name + ".svg")


def place(graphic_id, zone, prefix):
    """Nested <svg> that fits a graphic into a zone (x, y, w, h[, rot])."""
    x, y, w, h = zone[:4]
    rot = zone[4] if len(zone) > 4 else 0
    path = asset_path("graphic", graphic_id)
    if not os.path.exists(path):
        return placeholder(zone, f"lipsă: {graphic_id}")
    (vx, vy, vw, vh), inner = load_svg(path)
    inner = prefix_ids(inner, prefix)
    if rot:
        # rotate around the zone centre; the graphic is fitted into the rotated box
        cx, cy = x + w / 2, y + h / 2
        rw, rh = (h, w) if rot % 180 else (w, h)
        return (f'<g transform="rotate({rot} {cx} {cy})"><svg x="{cx - rw / 2}" y="{cy - rh / 2}" width="{rw}" height="{rh}" '
                f'viewBox="{vx} {vy} {vw} {vh}" preserveAspectRatio="xMidYMid meet" overflow="visible">{inner}</svg></g>')
    return (f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vx} {vy} {vw} {vh}" '
            f'preserveAspectRatio="xMidYMid meet" overflow="visible">{inner}</svg>')


def placeholder(zone, label):
    x, y, w, h = zone[:4]
    rot = zone[4] if len(zone) > 4 else 0
    cx, cy = x + w / 2, y + h / 2
    fs = max(10, min(w, h) / 7)
    g = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#6C6CFF" fill-opacity=".35" stroke="#FF4D2E" stroke-width="3" stroke-dasharray="10 6"/>'
         f'<text x="{cx}" y="{cy}" font-family="monospace" font-size="{fs:.0f}" fill="#FF4D2E" text-anchor="middle" dominant-baseline="middle">{label}</text>')
    return f'<g transform="rotate({rot} {cx} {cy})">{g}</g>' if rot else g


def aop_fill(pattern_id, tile, prefix):
    """Return {"id", "defs"} for an all-over-print pattern fill, or None."""
    path = asset_path("pattern", pattern_id)
    pid = f"{prefix}aop"
    if not os.path.exists(path):
        defs = (f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{tile}" height="{tile}">'
                f'<rect width="{tile}" height="{tile}" fill="#2B2A8F"/><circle cx="{tile/2}" cy="{tile/2}" r="{tile/5}" fill="#FF4D2E"/></pattern>')
        return {"id": pid, "defs": defs}
    (vx, vy, vw, vh), inner = load_svg(path)
    inner = prefix_ids(inner, prefix)
    th = tile * vh / vw
    defs = (f'<pattern id="{pid}" patternUnits="userSpaceOnUse" width="{tile}" height="{th}" '
            f'viewBox="{vx} {vy} {vw} {vh}" preserveAspectRatio="none">{inner}</pattern>')
    return {"id": pid, "defs": defs}


# ---------- products ----------
def load_products():
    return json.load(open(os.path.join(ROOT, "products.json"), encoding="utf-8"))


def compose(product, view, reg):
    spec = reg.get(product["garment"])
    if spec is None:
        raise KeyError(f'{product["id"]}: unknown garment {product["garment"]}')
    prefix = f'{product["id"]}{view[0]}'
    prints = []
    for i, pr in enumerate(product.get("prints", {}).get(view, [])):
        zone = spec["zones"].get(pr["zone"])
        if zone is None:
            raise KeyError(f'{product["id"]}: garment {product["garment"]} has no zone {pr["zone"]}')
        prints.append(place(pr["graphic"], zone, f"{prefix}{i}-"))
    aop = aop_fill(product["aop"], spec.get("aop_tile", 220), prefix) if product.get("aop") else None
    fabric = product["colors"][0]["hex"] if product.get("colors") else "#111114"
    return spec["draw"](view, fabric, "".join(prints), aop)


def render(svg_paths, out_dir, width):
    if not svg_paths:
        return
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ, NODE_PATH=NODE_PATH)
    for i in range(0, len(svg_paths), 40):
        subprocess.run(["node", RENDER_JS, out_dir, *svg_paths[i:i + 40], "--sizes", str(width), "--bg", "#ECEBE7"],
                       check=True, env=env, stdout=subprocess.DEVNULL)


def to_jpeg(png_dir, width):
    from PIL import Image
    for f in os.listdir(png_dir):
        if f.endswith(f"@{width}.png"):
            src = os.path.join(png_dir, f)
            Image.open(src).convert("RGB").save(os.path.join(png_dir, f.replace(f"@{width}.png", ".jpg")), quality=84, optimize=True, progressive=True)
            os.remove(src)


def cmd_build(args):
    reg = registry()
    products = load_products()
    if args.ids:
        want = set(args.ids.split(","))
        products = [p for p in products if p["id"] in want]
    svg_dir = os.path.join(ROOT, "mockups", "svg")
    os.makedirs(svg_dir, exist_ok=True)
    paths = []
    for p in products:
        spec = reg.get(p["garment"])
        if spec is None:
            print(f'skip {p["id"]}: garment {p["garment"]} not implemented yet')
            continue
        for view in spec["views"]:
            path = os.path.join(svg_dir, f'{p["id"]}-{view}.svg')
            open(path, "w", encoding="utf-8").write(compose(p, view, reg))
            paths.append(path)
    web = os.path.join(ROOT, "mockups", "web")
    render(paths, web, args.width)
    to_jpeg(web, args.width)
    print(f"built {len(paths)} views for {len(products)} products -> {web}")


def cmd_test(args):
    reg = registry()
    keys = sorted(reg) if args.all else [args.garment]
    out = os.path.join(ROOT, "previews", "garments")
    os.makedirs(out, exist_ok=True)
    paths = []
    for k in keys:
        spec = reg[k]
        for view in spec["views"]:
            # zone names always start with the view they belong to: front_center, back_neck, front_leg_left ...
            prints = "".join(placeholder(v, z) for z, v in spec["zones"].items() if z.startswith(view + "_"))
            for fabric in (args.fabric or "#111114,#F5F5F2").split(","):
                svg = spec["draw"](view, fabric, prints, None)
                p = os.path.join(out, f"{k}-{view}-{fabric.strip('#')}.svg")
                open(p, "w", encoding="utf-8").write(svg)
                paths.append(p)
            svg = spec["draw"](view, "#111114", "", aop_fill("__demo__", spec.get("aop_tile", 220), f"t{k}"))
            p = os.path.join(out, f"{k}-{view}-aop.svg")
            open(p, "w", encoding="utf-8").write(svg)
            paths.append(p)
    render(paths, out, 520)
    print("\n".join(sorted(f for f in os.listdir(out) if f.endswith(".png"))))


def cmd_sheet(args):
    from PIL import Image, ImageDraw
    web = os.path.join(ROOT, "mockups", "web")
    products = load_products()
    if args.ids:
        want = args.ids.split(",")
        products = [p for p in products if p["id"] in want]
    tiles = []
    for p in products:
        for view in ("front", "back"):
            f = os.path.join(web, f'{p["id"]}-{view}.jpg')
            if os.path.exists(f):
                tiles.append((f'{p["id"]} {view}', f))
    if not tiles:
        raise SystemExit("no mockups built yet")
    tw = 300
    ims = []
    for label, f in tiles:
        im = Image.open(f)
        im = im.resize((tw, int(im.height * tw / im.width)))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 120, 22], fill="#111")
        d.text((6, 5), label, fill="#fff")
        ims.append(im)
    th = max(i.height for i in ims)
    cols = args.cols
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), "#ECEBE7")
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    out = args.out or os.path.join(ROOT, "previews", "sheet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print(out, sheet.size)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build"); b.add_argument("--ids"); b.add_argument("--width", type=int, default=760)
    t = sub.add_parser("test"); t.add_argument("--garment"); t.add_argument("--all", action="store_true"); t.add_argument("--fabric")
    s = sub.add_parser("sheet"); s.add_argument("--ids"); s.add_argument("--out"); s.add_argument("--cols", type=int, default=6)
    a = ap.parse_args()
    {"build": cmd_build, "test": cmd_test, "sheet": cmd_sheet}[a.cmd](a)


if __name__ == "__main__":
    main()
