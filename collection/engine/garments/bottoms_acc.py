"""Flat-lay mockups: bottoms and accessories of the NEPĂMÂNTEAN collection.

shorts, biker_shorts, joggers, leggings, mini_skirt, bucket_hat, cap, beanie,
socks, tote, bandana, drawstring_bag.  Interface: see engine/engine.py docstring.
Canvas viewBox 0 0 1000 1100, transparent background, garment centred.
"""
import itertools
import math
import re

VB = "0 0 1000 1100"
AOP_TRIM = "#111114"
_COUNTER = itertools.count()

# ---------- shared style ----------
OUTLINE = 'fill="none" stroke="#000" stroke-opacity=".35" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"'
SEAM = 'fill="none" stroke="#000" stroke-opacity=".28" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
STITCH = SEAM + ' stroke-dasharray="5 4"'
HW, HW_DARK = "#C9CCD3", "#8A8F99"

# ---------- path helpers (all paths use absolute M/L/C/Q/Z with "x,y" pairs) ----------
_PAIR = re.compile(r"(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)")


def tf(d, fn):
    def rep(m):
        x, y = fn(float(m.group(1)), float(m.group(2)))
        return f"{x:.1f},{y:.1f}"
    return _PAIR.sub(rep, d)


def mx(d):
    """Mirror around the vertical centre line x=500."""
    return tf(d, lambda x, y: (1000 - x, y))


def shift(d, dx, dy):
    return tf(d, lambda x, y: (x + dx, y + dy))


def scl(d, sx, sy, cx, cy):
    return tf(d, lambda x, y: (cx + (x - cx) * sx, cy + (y - cy) * sy))


def bbox(d):
    pts = [(float(a), float(b)) for a, b in _PAIR.findall(d)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _off_cubic(p0, p1, p2, p3, dist):
    def n(a, b):
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1
        return -ty / L * dist, tx / L * dist
    n0, n1 = n(p0, p1), n(p2, p3)
    return ((p0[0] + n0[0], p0[1] + n0[1]), (p1[0] + n0[0], p1[1] + n0[1]),
            (p2[0] + n1[0], p2[1] + n1[1]), (p3[0] + n1[0], p3[1] + n1[1]))


def strap(segs, half):
    """Closed band of width 2*half around a chain of cubic segments [(p0,p1,p2,p3), ...]."""
    a = [_off_cubic(*s, half) for s in segs]
    b = [_off_cubic(*s, -half) for s in segs]
    f = lambda p: f"{p[0]:.1f},{p[1]:.1f}"
    d = "M" + f(a[0][0]) + "".join(f" C{f(s[1])} {f(s[2])} {f(s[3])}" for s in a)
    d += " L" + f(b[-1][3]) + "".join(f" C{f(s[2])} {f(s[1])} {f(s[0])}" for s in reversed(b)) + " Z"
    return d


def chain(segs, off=0):
    f = lambda p: f"{p[0]:.1f},{p[1]:.1f}"
    s2 = [_off_cubic(*s, off) for s in segs] if off else segs
    return "M" + f(s2[0][0]) + "".join(f" C{f(s[1])} {f(s[2])} {f(s[3])}" for s in s2)


# ---------- drawing context ----------
class Ctx:
    def __init__(self, key, view, fabric, aop):
        self.p = f"{key}-{view}-{next(_COUNTER)}-"
        self.n = 0
        self.defs = []
        self.aop = aop
        self.fabric = fabric
        self.fill = f"url(#{aop['id']})" if aop else fabric
        self.trim = AOP_TRIM if aop else fabric
        self._g = None

    def uid(self, name):
        self.n += 1
        return f"{self.p}{name}{self.n}"

    def clip(self, d):
        i = self.uid("clip")
        self.defs.append(f'<clipPath id="{i}"><path d="{d}"/></clipPath>')
        return i

    def g(self):
        if self._g is None:
            v, h, hw, hwl, rib = (self.uid(n) for n in ("shv", "shh", "hw", "hwl", "rib"))
            self.defs.append(
                f'<linearGradient id="{v}" x1="0" y1="0" x2="0" y2="1">'
                '<stop offset="0" stop-color="#fff" stop-opacity=".10"/><stop offset=".45" stop-color="#fff" stop-opacity="0"/>'
                '<stop offset=".45" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".18"/></linearGradient>'
                f'<linearGradient id="{h}" x1="0" y1="0" x2="1" y2="0">'
                '<stop offset="0" stop-color="#000" stop-opacity=".12"/><stop offset=".18" stop-color="#000" stop-opacity="0"/>'
                '<stop offset=".82" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".12"/></linearGradient>'
                f'<radialGradient id="{hw}" cx=".38" cy=".35" r=".75"><stop offset="0" stop-color="#F4F5F7"/>'
                f'<stop offset=".35" stop-color="{HW}"/><stop offset="1" stop-color="{HW_DARK}"/></radialGradient>'
                f'<linearGradient id="{hwl}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{HW_DARK}"/>'
                f'<stop offset=".4" stop-color="#EEF0F3"/><stop offset=".6" stop-color="{HW}"/><stop offset="1" stop-color="{HW_DARK}"/></linearGradient>'
                f'<pattern id="{rib}" patternUnits="userSpaceOnUse" width="6" height="12">'
                '<path d="M3,-1 L3,13" stroke="#000" stroke-opacity=".10" stroke-width="1.5"/></pattern>')
            self._g = {"v": v, "h": h, "hw": hw, "hwl": hwl, "rib": rib}
        return self._g

    # --- layers ---
    def shading(self, d, box=None, clip=None):
        g = self.g()
        clip = clip or self.clip(d)
        x0, y0, x1, y1 = box or bbox(d)
        r = f'x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}"'
        return f'<g clip-path="url(#{clip})"><rect {r} fill="url(#{g["v"]})"/><rect {r} fill="url(#{g["h"]})"/></g>'

    def ribbing(self, d, fill=None, angle=0, lines=True, overlay=True):
        g = self.g()
        fill = fill or self.trim
        out = f'<path d="{d}" fill="{fill}"/>'
        if overlay:
            out += f'<path d="{d}" fill="#000" fill-opacity=".12"/>'
        if lines:
            pid = g["rib"]
            if angle:
                pid = self.uid("ribr")
                self.defs.append(f'<pattern id="{pid}" href="#{g["rib"]}" patternTransform="rotate({angle})"/>')
            out += f'<path d="{d}" fill="url(#{pid})"/>'
        return out + self.shading(d)

    def grommet(self, cx, cy, r=9):
        g = self.g()
        return (f'<circle cx="{cx}" cy="{cy}" r="{r + 1.5}" fill="#000" fill-opacity=".25"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{g["hw"]})" stroke="{HW_DARK}" stroke-width="1.2"/>'
                f'<circle cx="{cx}" cy="{cy}" r="{r * .52:.1f}" fill="#141416" stroke="{HW_DARK}" stroke-width="1"/>')

    def aglet(self, x, y, ang, ln=24, w=10):
        g = self.g()
        return (f'<g transform="rotate({ang} {x} {y})"><rect x="{x - w / 2}" y="{y}" width="{w}" height="{ln}" rx="3" '
                f'fill="url(#{g["hwl"]})" stroke="{HW_DARK}" stroke-width="1"/></g>')

    def cord(self, d, color=None, w=8):
        color = color or self.trim
        return (f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="{w + 3}" stroke-linecap="round"/>'
                f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
                f'<path d="{d}" fill="none" stroke="#000" stroke-opacity=".12" stroke-width="{w}" stroke-linecap="round"/>'
                f'<path d="{d}" fill="none" stroke="#fff" stroke-opacity=".18" stroke-width="{w * .3:.1f}" stroke-linecap="round" '
                f'transform="translate(-1 -1)"/>')

    def piece(self, d, *, fill=None, prints="", texture="", folds=(), seams=(), stitches=(), ribs=(),
              post="", hardware="", extra_outline=(), shade=True, shade_boxes=None):
        fill = fill or self.fill
        clip = self.clip(d)
        out = [f'<path d="{d}" fill="{fill}"/>']
        if texture:
            out.append(f'<g clip-path="url(#{clip})">{texture}</g>')
        if prints:
            out.append(f'<g clip-path="url(#{clip})">{prints}</g>')
        if shade:
            for b in (shade_boxes or [None]):
                out.append(self.shading(d, b, clip))
        if folds:
            fl = []
            for f in folds:
                fd, w, op = (f, 8, .06) if isinstance(f, str) else (tuple(f) + (8, .06))[:3]
                fl.append(f'<path d="{fd}" fill="none" stroke="#000" stroke-opacity="{op}" stroke-width="{w}" stroke-linecap="round"/>')
            out.append(f'<g clip-path="url(#{clip})">{"".join(fl)}</g>')
        out += [f'<path d="{s}" {SEAM}/>' for s in seams]
        out += [f'<path d="{s}" {STITCH}/>' for s in stitches]
        for r in ribs:
            r = {"d": r} if isinstance(r, str) else r
            out.append(self.ribbing(r["d"], r.get("fill"), r.get("angle", 0), r.get("lines", True), r.get("overlay", True)))
        out.append(post)
        out.append(hardware)
        for o in [d] + [r if isinstance(r, str) else r["d"] for r in ribs] + list(extra_outline):
            out.append(f'<path d="{o}" {OUTLINE}/>')
        return "".join(out)

    def svg(self, body):
        aop_defs = self.aop["defs"] if self.aop else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB}"><defs>{"".join(self.defs)}{aop_defs}</defs>'
                f'{body}</svg>')


def both(*paths):
    """Path plus its mirror image (for symmetric lines)."""
    out = []
    for p in paths:
        out += [p, mx(p)] if isinstance(p, str) else [p, (mx(p[0]),) + tuple(p[1:])]
    return out


def bartack(x, y, ang=0, ln=12):
    return (f'<path d="M{x - ln / 2},{y} L{x + ln / 2},{y}" transform="rotate({ang} {x} {y})" fill="none" '
            f'stroke="#000" stroke-opacity=".38" stroke-width="3.2" stroke-linecap="round"/>')


# =====================================================================
# SHORTS — baggy basketball shorts, elastic waist + drawcord
# =====================================================================
SHORTS_BODY = ("M226,268 C170,292 118,350 104,440 L80,868 Q78,896 108,899 L466,914 Q488,915 489,896 "
               "L496,668 Q500,626 504,668 L511,896 Q512,915 534,914 L892,899 Q922,896 920,868 "
               "L896,440 C882,350 830,292 774,268 Z")
SHORTS_BAND = "M220,200 C400,191 600,191 780,200 L784,278 C600,287 400,287 216,278 Z"


def draw_shorts(view, fabric, prints, aop):
    c = Ctx("shorts", view, fabric, aop)
    panel = "M210,288 C164,420 150,700 166,904"
    folds = both("M300,700 Q330,780 322,885", "M392,560 Q440,604 478,650", "M220,520 Q240,640 236,760",
                 "M140,600 Q150,700 146,820")
    folds += [(f"M{x},284 L{x + 3},{326 + (x % 3) * 8}", 6, .07) for x in range(250, 760, 38)]
    seams = both(panel, "M108,880 L466,895") + ["M500,282 L500,632"]
    stitches = both("M218,292 C172,420 158,700 174,902", "M110,874 L468,889")
    hardware = post = ""
    if view == "front":
        stitches += ["M507,286 L507,560 Q507,600 498,628"]
        post = "".join(bartack(*p) for p in [(196, 316, 70), (168, 470, 85), (804, 316, -70), (832, 470, -85)])
        hardware = (c.grommet(472, 242) + c.grommet(528, 242)
                    + c.cord("M472,242 C466,296 448,340 456,392") + c.cord("M528,242 C536,300 552,344 542,402")
                    + c.aglet(456, 388, 10) + c.aglet(542, 398, -12))
    else:
        seams += ["M214,342 C330,366 420,378 500,380 C580,378 670,366 786,342",
                  "M560,420 L720,420 L720,560 Q720,575 705,575 L575,575 Q560,575 560,560 Z"]
        stitches += ["M216,352 C330,376 420,388 500,390 C580,388 670,376 784,352",
                     "M568,428 L712,428 L712,558 Q712,567 703,567 L577,567 Q568,567 568,558 Z"]
        post = bartack(570, 424, 0, 10) + bartack(710, 424, 0, 10)
    post += f'<path d="M226,246 L774,246" {STITCH} stroke-opacity=".18"/>'
    body = c.piece(SHORTS_BODY, prints=prints, folds=folds, seams=seams, stitches=stitches,
                   ribs=[SHORTS_BAND], post=post, hardware=hardware)
    return c.svg(body)


# =====================================================================
# BIKER SHORTS — girls, fitted, high rise, mid-thigh (self-fabric band)
# =====================================================================
BIKER_BODY = ("M250,182 C400,174 600,174 750,182 C772,262 840,380 846,470 C852,600 840,760 832,898 "
              "Q831,910 818,910 L536,906 Q522,905 522,892 L506,676 Q500,640 494,676 L478,892 Q478,905 464,906 "
              "L182,910 Q169,910 168,898 C160,760 148,600 154,470 C160,380 228,262 250,182 Z")


def draw_biker(view, fabric, prints, aop):
    c = Ctx("biker_shorts", view, fabric, aop)
    band = "M226,292 C400,306 600,306 774,292"
    seams = [band, "M500,300 L500,640"] + both("M182,894 L466,890")
    stitches = ["M228,300 C400,314 600,314 772,300", "M246,194 C400,186 600,186 754,194"]
    stitches += both("M180,884 L468,880", "M180,876 L468,872")
    folds = both("M430,598 Q472,640 492,692", "M210,842 Q300,852 380,842", "M240,330 Q330,346 420,336",
                 "M200,560 Q210,660 204,760")
    if view == "front":
        seams += both("M318,302 C276,450 252,700 266,906")
        stitches += both("M326,302 C284,450 260,700 274,906")
    else:
        seams += ["M226,318 L500,420 L774,318", "M500,420 L500,640"]
        stitches += ["M232,328 L500,430 L768,328"]
    return c.svg(c.piece(BIKER_BODY, prints=prints, folds=folds, seams=seams, stitches=stitches))


# =====================================================================
# JOGGERS — wide baggy sweatpants, rib waist + drawcord, open hems
# =====================================================================
JOG_BODY = ("M318,146 C270,180 236,250 228,340 L160,1030 Q160,1042 172,1042 L462,1046 Q474,1046 474,1034 "
            "L496,424 Q500,396 504,424 L526,1034 Q526,1046 538,1046 L828,1042 Q840,1042 840,1030 "
            "L772,340 C764,250 730,180 682,146 Z")
JOG_BAND = "M312,86 C430,80 570,80 688,86 L692,152 C570,158 430,158 308,152 Z"


def draw_joggers(view, fabric, prints, aop):
    c = Ctx("joggers", view, fabric, aop)
    folds = both("M360,470 Q338,650 330,860", "M232,900 Q300,922 384,912", "M196,966 Q280,994 430,982",
                 "M420,560 Q440,700 448,880", "M250,620 Q256,720 240,800", "M430,330 Q470,370 490,420")
    folds += [(f"M{x},156 L{x + 2},{196 + (x % 4) * 6}", 6, .07) for x in range(332, 680, 34)]
    seams = both("M168,1018 L464,1022") + ["M500,156 L500,398"]
    stitches = both("M170,1012 L464,1016", "M170,1022 L464,1026")
    post = hardware = ""
    if view == "front":
        seams += both("M300,154 L246,336")
        stitches += both("M308,156 L256,334")
        post = bartack(300, 158, 72) + bartack(246, 334, 72) + bartack(700, 158, -72) + bartack(754, 334, -72)
        stitches += ["M507,158 L507,340 Q507,380 499,398"]
        hardware = (c.grommet(474, 124, 8) + c.grommet(526, 124, 8)
                    + c.cord("M474,124 C468,190 446,236 452,290") + c.cord("M526,124 C534,196 552,240 544,300")
                    + c.aglet(452, 286, 8) + c.aglet(544, 296, -10))
    else:
        seams += ["M560,220 L700,220 L700,368 Q700,384 684,384 L576,384 Q560,384 560,368 Z",
                  "M248,236 C360,262 440,270 500,272 C560,270 640,262 752,236"]
        stitches += ["M568,228 L692,228 L692,366 Q692,376 682,376 L578,376 Q568,376 568,366 Z",
                     "M246,246 C360,272 440,280 500,282 C560,280 640,272 754,246"]
        post = bartack(570, 224, 0, 10) + bartack(690, 224, 0, 10)
    post += f'<path d="M314,118 L686,118" {STITCH} stroke-opacity=".18"/>'
    return c.svg(c.piece(JOG_BODY, prints=prints, folds=folds, seams=seams, stitches=stitches,
                         ribs=[JOG_BAND], post=post, hardware=hardware))


# =====================================================================
# LEGGINGS — high rise, full length (self-fabric band)
# =====================================================================
LEG_BODY = ("M340,70 C440,64 560,64 660,70 C680,150 705,230 718,330 C730,450 745,700 772,1040 "
            "Q772,1052 760,1052 L668,1052 Q656,1052 656,1040 L510,394 Q500,366 490,394 L344,1040 "
            "Q344,1052 332,1052 L240,1052 Q228,1052 228,1040 C255,700 270,450 282,330 C295,230 320,150 340,70 Z")


def draw_leggings(view, fabric, prints, aop):
    c = Ctx("leggings", view, fabric, aop)
    seams = ["M314,176 C420,188 580,188 686,176"] + both("M234,1032 L340,1032")
    stitches = ["M313,184 C420,196 580,196 687,184", "M342,80 C440,74 560,74 658,80"]
    stitches += both("M234,1022 L342,1022", "M234,1014 L342,1014")
    folds = both("M290,700 Q330,712 360,700", "M286,740 Q326,756 368,744", "M240,980 Q290,992 344,984",
                 "M236,940 Q286,950 350,944", "M300,420 Q320,560 320,640", "M440,360 Q470,380 488,410")
    if view == "front":
        seams += ["M500,190 L500,372"]
    else:
        seams += ["M300,240 L500,320 L700,240", "M500,320 L500,372"]
        stitches += ["M304,250 L500,330 L696,250"]
    return c.svg(c.piece(LEG_BODY, prints=prints, folds=folds, seams=seams, stitches=stitches))


# =====================================================================
# MINI SKIRT — A-line, waistband, back zip
# =====================================================================
SKIRT_BAND = "M236,270 C400,262 600,262 764,270 L768,334 C600,342 400,342 232,334 Z"
SKIRT_BODY = ("M234,326 C400,334 600,334 766,326 C800,480 860,680 912,828 Q916,842 900,846 "
              "C700,874 300,874 100,846 Q84,842 88,828 C140,680 200,480 234,326 Z")


def draw_skirt(view, fabric, prints, aop):
    c = Ctx("mini_skirt", view, fabric, aop)
    folds = both("M330,520 Q300,680 270,850", "M420,560 Q410,700 400,860", "M232,560 Q200,700 160,836",
                 "M300,380 Q310,450 300,520")
    seams = both("M362,340 L372,458")
    stitches = ["M104,826 C300,852 700,852 896,826", "M240,282 C400,274 600,274 760,282",
                "M236,322 C400,330 600,330 764,322"]
    post = hardware = ""
    loops = "".join(
        f'<rect x="{x - 9}" y="262" width="18" height="78" rx="4" fill="{c.trim}"/>'
        f'<rect x="{x - 9}" y="262" width="18" height="78" rx="4" fill="#000" fill-opacity=".1" stroke="#000" stroke-opacity=".35" stroke-width="2"/>'
        f'<path d="M{x - 9},272 L{x + 9},272 M{x - 9},330 L{x + 9},330" {STITCH}/>' for x in (290, 710))
    post = loops
    if view == "back":
        seams += ["M500,340 L500,862"]
        hardware = (f'<path d="M500,340 L500,560" fill="none" stroke="#000" stroke-opacity=".45" stroke-width="3"/>'
                    f'<rect x="493" y="342" width="14" height="26" rx="3" fill="url(#{c.g()["hwl"]})" stroke="{HW_DARK}" stroke-width="1"/>'
                    f'<path d="M500,368 L500,392" stroke="{HW_DARK}" stroke-width="5" stroke-linecap="round"/>')
        stitches += ["M492,340 L492,566 L508,566 L508,340"]
    band = c.ribbing(SKIRT_BAND, lines=False, overlay=False) + f'<path d="{SKIRT_BAND}" {OUTLINE}/>'
    body = c.piece(SKIRT_BODY, prints=prints, folds=folds, seams=seams, stitches=stitches, hardware=hardware)
    return c.svg(body + band + post)


# =====================================================================
# BUCKET HAT — crown + brim with stitching rows (front view)
# =====================================================================
HAT_BRIM = ("M262,592 C188,610 142,672 138,722 C138,776 300,814 500,816 C700,814 862,776 862,722 "
            "C858,672 812,610 738,592 Z")
HAT_CROWN = "M312,332 C360,302 640,302 688,332 L742,598 C650,640 350,640 258,598 Z"


def draw_bucket(view, fabric, prints, aop):
    c = Ctx("bucket_hat", view, fabric, aop)
    rows = []
    for k in range(1, 7):
        f = 1 - k * 0.075
        rows.append(scl("M138,722 C138,776 300,814 500,816 C700,814 862,776 862,722", f, f * .96 + .04, 500, 610))
    brim = c.piece(HAT_BRIM, stitches=rows,
                   folds=[("M258,604 C350,646 650,646 742,604", 22, .12), ("M200,700 Q230,740 300,770", 8, .05)])
    crown = c.piece(HAT_CROWN, prints=prints,
                    folds=["M400,372 Q500,386 600,372", ("M290,560 Q300,500 296,430", 8, .05),
                           ("M710,560 Q700,500 704,430", 8, .05)],
                    seams=["M320,356 C370,330 630,330 680,356"] + both("M362,342 C354,450 346,540 340,628"),
                    stitches=["M323,366 C372,340 628,340 677,366", "M266,584 C350,622 650,622 734,584"]
                    + both("M370,342 C362,450 354,540 348,628"),
                    hardware=c.grommet(306, 440, 9) + c.grommet(694, 440, 9))
    return c.svg(brim + crown)


# =====================================================================
# CAP — 6-panel dad cap, front view
# =====================================================================
CAP_CROWN = "M220,690 C206,450 320,298 500,292 C680,298 794,450 780,690 C680,720 320,720 220,690 Z"
CAP_VISOR = ("M236,644 C330,712 670,712 764,644 C804,664 824,724 806,782 C780,858 640,888 500,888 "
             "C360,888 220,858 194,782 C176,724 196,664 236,644 Z")
CAP_ZONE = (380, 452, 240, 126)
CAP_SQ = 0.86


def draw_cap(view, fabric, prints, aop):
    c = Ctx("cap", view, fabric, aop)
    V = lambda d: scl(d, 1, CAP_SQ, 500, 700)          # low-profile crown
    zx, zy, zw, zh = CAP_ZONE
    top = 700 - 408 * CAP_SQ
    seams = both(V("M496,298 C390,312 300,420 276,690")) + [f"M500,{top + 8:.0f} L500,{zy - 8}", f"M500,{zy + zh + 8} L500,664"]
    stitches = both(V("M484,304 C384,322 298,430 286,690")) + [
        f"M{x},{top + 12:.0f} L{x},{zy - 10}" for x in (492, 508)] + [f"M{x},{zy + zh + 10} L{x},662" for x in (492, 508)]
    eyelets = ""
    for ex, ey in ((392, 368), (608, 368), (300, 476), (700, 476)):
        ey = 700 + (ey - 700) * CAP_SQ
        eyelets += (f'<circle cx="{ex}" cy="{ey:.0f}" r="8" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="4"/>'
                    f'<circle cx="{ex}" cy="{ey:.0f}" r="4.5" fill="#000" fill-opacity=".55"/>')
    crown = c.piece(V(CAP_CROWN), prints=prints, seams=seams, stitches=stitches, post=eyelets,
                    folds=[("M360,610 Q390,636 380,672", 8, .06), ("M640,610 Q610,636 620,672", 8, .06),
                           ("M262,540 Q300,580 290,630", 10, .05), ("M738,540 Q700,580 710,630", 10, .05)])
    rows = [scl("M214,672 C190,712 186,750 194,782 C220,858 360,888 500,888 C640,888 780,858 806,782 C814,750 810,712 786,672",
                1 - k * 0.024, 1 - k * 0.07, 500, 690) for k in range(1, 7)]
    visor = c.piece(CAP_VISOR, stitches=rows,
                    folds=[("M236,650 C330,718 670,718 764,650", 22, .14), ("M300,800 Q500,840 700,800", 30, .04)])
    t = top
    btn = c.piece(f"M484,{t:.0f} C484,{t - 20:.0f} 516,{t - 20:.0f} 516,{t:.0f} C516,{t + 10:.0f} 484,{t + 10:.0f} 484,{t:.0f} Z",
                  shade=False, post=f'<ellipse cx="500" cy="{t - 8:.0f}" rx="8" ry="4" fill="#fff" fill-opacity=".12"/>')
    return c.svg(crown + visor + btn)


# =====================================================================
# BEANIE — cuffed, ribbed knit (front view)
# =====================================================================
BEANIE_BODY = "M205,664 C198,420 290,206 500,200 C710,206 802,420 795,664 Z"
BEANIE_CUFF = "M184,648 C330,630 670,630 816,648 L824,862 C670,884 330,884 176,862 Z"


def draw_beanie(view, fabric, prints, aop):
    c = Ctx("beanie", view, fabric, aop)
    ribs = []
    for i in range(0, 99):
        x = 206 + i * 6
        top = 500 + (x - 500) * 0.12
        ribs.append(f"M{x},668 C{500 + (x - 500) * 1.04:.1f},470 {500 + (x - 500) * 0.8:.1f},280 {top:.1f},198")
    tex = (f'<path d="{" ".join(ribs)}" fill="none" stroke="#000" stroke-opacity=".10" stroke-width="1.5"/>')
    tex += f'<path d="{BEANIE_CUFF}" fill="#000" fill-opacity=".06"/><path d="{BEANIE_CUFF}" fill="url(#{c.g()["rib"]})"/>'
    tex += "".join(f'<path d="M{x},640 L{x},880" stroke="#fff" stroke-opacity=".035" stroke-width="2"/>' for x in range(186, 820, 12))
    union = BEANIE_BODY + " " + BEANIE_CUFF
    body = c.piece(union, prints=prints, texture=tex,
                   shade_boxes=[bbox(BEANIE_BODY), bbox(BEANIE_CUFF)],
                   folds=[("M200,656 C330,640 670,640 800,656", 16, .14), ("M470,214 Q500,236 530,214", 6, .08),
                          ("M440,226 Q470,260 500,250", 6, .06), ("M300,560 Q320,600 300,640", 8, .05),
                          ("M700,560 Q680,600 700,640", 8, .05), ("M178,858 C330,878 670,878 822,858", 10, .10)],
                   seams=["M186,652 C330,634 670,634 814,652"],
                   post='<path d="M188,662 C330,644 670,644 812,662" fill="none" stroke="#fff" stroke-opacity=".10" stroke-width="5" stroke-linecap="round"/>',
                   extra_outline=[BEANIE_BODY])
    return c.svg(body)


# =====================================================================
# SOCKS — crew pair (front view), AOP body, solid cuff/heel/toe on AOP
# =====================================================================
SOCK = ("M0,0 L190,0 L192,470 C196,520 222,560 215,610 C208,665 170,690 120,690 L-200,690 "
        "C-265,690 -295,650 -295,605 C-295,555 -260,520 -205,515 L-60,505 C-20,500 0,470 0,430 Z")
SOCK_CUFF = "M0,0 L190,0 L190,84 L0,84 Z"
SOCK_HEEL = "M193,500 C198,530 222,560 215,610 C208,665 170,690 120,690 L84,690 C92,600 130,540 193,500 Z"
SOCK_TOE = "M-205,515 C-260,520 -295,555 -295,605 C-295,650 -265,690 -200,690 C-178,640 -180,560 -205,515 Z"


def _sock(c, ox, oy, prints=""):
    d = shift(SOCK, ox, oy)
    trims = [{"d": shift(SOCK_HEEL, ox, oy), "lines": False, "overlay": not c.aop},
             {"d": shift(SOCK_TOE, ox, oy), "lines": False, "overlay": not c.aop},
             {"d": shift(SOCK_CUFF, ox, oy)}]
    folds = [shift(p, ox, oy) for p in ("M10,440 Q50,480 34,530", "M-40,520 Q-20,560 -50,600",
                                        "M60,150 Q70,300 60,420", "M140,200 Q150,320 140,440")]
    stitches = [shift("M0,96 L190,96", ox, oy)]
    post = f'<path d="{shift("M-205,515 C-180,560 -178,640 -200,690", ox, oy)}" {SEAM}/>'
    post += f'<path d="{shift("M193,500 C130,540 92,600 84,690", ox, oy)}" {SEAM}/>'
    return c.piece(d, prints=prints, folds=folds, stitches=stitches, ribs=trims, post=post)


def draw_socks(view, fabric, prints, aop):
    c = Ctx("socks", view, fabric, aop)
    return c.svg(_sock(c, 435, 170) + _sock(c, 645, 244, prints))


# =====================================================================
# TOTE — flat tote with two handles
# =====================================================================
TOTE_BODY = "M178,352 L822,352 L828,1050 Q828,1062 816,1062 L184,1062 Q172,1062 172,1050 Z"
_HANDLE = [((330, 412), (330, 190), (390, 92), (500, 92)), ((500, 92), (610, 92), (670, 190), (670, 412))]


def draw_tote(view, fabric, prints, aop):
    c = Ctx("tote", view, fabric, aop)
    h = strap(_HANDLE, 22)
    hb = shift(h, 0, -30)
    tone = "#000" if fabric.lower() > "#888888" else "#fff"
    back = c.piece(hb, fill=c.trim, post=f'<path d="{hb}" fill="#000" fill-opacity=".18"/>',
                   stitches=[shift(chain(_HANDLE, 15), 0, -30), shift(chain(_HANDLE, -15), 0, -30)])
    body = c.piece(TOTE_BODY, prints=prints,
                   folds=both("M300,430 Q320,520 296,600", "M200,980 Q260,1010 300,1056", "M400,420 Q420,470 410,520"),
                   stitches=["M180,406 L820,406", "M186,1046 L814,1046"])
    boxes = ""
    for x in (330, 670):
        boxes += (f'<path d="M{x - 15},364 L{x + 15},364 L{x + 15},402 L{x - 15},402 Z M{x - 15},364 L{x + 15},402 '
                  f'M{x + 15},364 L{x - 15},402" {STITCH}/>')
    front = c.piece(h, fill=c.trim, stitches=[chain(_HANDLE, 15), chain(_HANDLE, -15)], post=boxes,
                    folds=[("M480,92 L520,92", 10, .05)])
    _ = tone
    return c.svg(back + body + front)


# =====================================================================
# BANDANA — square, rolled hem
# =====================================================================
BANDANA = ("M170,214 Q340,206 500,212 Q660,218 830,212 Q838,380 834,550 Q830,720 836,886 "
           "Q660,894 500,888 Q340,882 168,888 Q162,720 166,550 Q170,380 170,214 Z")


def draw_bandana(view, fabric, prints, aop):
    c = Ctx("bandana", view, fabric, aop)
    hem = scl(BANDANA, 1 - 32 / 668, 1 - 32 / 676, 500, 550)
    crease = ('<path d="M500,214 L500,888 M168,550 L834,550" fill="none" stroke="#fff" stroke-opacity=".07" stroke-width="3"/>'
              '<path d="M504,214 L504,888 M168,554 L834,554" fill="none" stroke="#000" stroke-opacity=".07" stroke-width="5"/>')
    body = c.piece(BANDANA, prints=prints, stitches=[hem],
                   folds=["M200,260 Q300,300 330,380", "M800,840 Q700,800 670,720", ("M180,500 Q260,520 300,600", 10, .04),
                          ("M820,600 Q740,580 700,500", 10, .04), ("M500,214 L500,888", 14, .03), ("M168,550 L834,550", 14, .03)],
                   post=crease)
    return c.svg(body)


# =====================================================================
# DRAWSTRING BAG — gym sack with cords
# =====================================================================
BAG_BODY = ("M200,232 Q260,240 320,230 Q380,240 440,230 Q500,240 560,230 Q620,240 680,230 Q740,240 800,232 "
            "L806,980 Q806,992 794,992 L206,992 Q194,992 194,980 Z")
BAG_TAB = "M194,890 L284,992 L206,992 Q194,992 194,980 Z"


def draw_bag(view, fabric, prints, aop):
    c = Ctx("drawstring_bag", view, fabric, aop)
    gather = [(f"M{x},238 Q{x + 6},300 {x + (x - 500) * .05:.1f},{360 + abs(x - 500) * .1:.1f}", 7, .07)
              for x in range(232, 790, 36)]
    folds = gather + both(("M260,700 Q300,820 280,960", 10, .05), ("M380,600 Q400,700 380,800", 8, .04))
    body = c.piece(BAG_BODY, prints=prints, folds=folds, seams=["M198,304 L802,304"],
                   stitches=["M198,312 L802,312"],
                   ribs=[{"d": BAG_TAB, "lines": False, "overlay": not aop}, {"d": mx(BAG_TAB), "lines": False, "overlay": not aop}],
                   post=f'<path d="M212,912 L270,980 M788,912 L730,980" {STITCH}/>')
    cords = (c.cord("M206,246 C150,130 320,70 500,70 C680,70 850,130 794,246")
             + c.cord("M210,250 C170,150 330,96 500,96 C670,96 830,150 790,250")
             + c.cord("M200,256 C170,450 172,800 214,968") + c.cord("M800,256 C830,450 828,800 786,968")
             + c.cord("M214,968 C210,1000 196,1020 190,1050") + c.cord("M786,968 C790,1000 804,1020 810,1050")
             + c.grommet(214, 968, 11) + c.grommet(786, 968, 11)
             + f'<circle cx="203" cy="1018" r="14" fill="{c.trim}" stroke="#000" stroke-opacity=".35" stroke-width="2"/>'
             + f'<circle cx="797" cy="1018" r="14" fill="{c.trim}" stroke="#000" stroke-opacity=".35" stroke-width="2"/>')
    exits = (f'<path d="M200,236 L214,236 L214,296 L200,296 Z" fill="#000" fill-opacity=".25"/>'
             f'<path d="M786,236 L800,236 L800,296 L786,296 Z" fill="#000" fill-opacity=".25"/>')
    return c.svg(body + exits + cords)


GARMENTS = {
    "shorts": {"label_ro": "Pantaloni scurți", "views": ["front", "back"], "aop_tile": 200, "draw": draw_shorts,
               "zones": {"front_leg_left": (640, 690, 120, 120)}},
    "biker_shorts": {"label_ro": "Pantaloni biker", "views": ["front", "back"], "aop_tile": 190, "draw": draw_biker,
                     "zones": {"front_leg_left": (600, 700, 110, 110), "back_waist": (430, 200, 140, 64)}},
    "joggers": {"label_ro": "Pantaloni jogger", "views": ["front", "back"], "aop_tile": 180, "draw": draw_joggers,
                "zones": {"front_leg_left": (630, 440, 64, 400, 270)}},
    "leggings": {"label_ro": "Colanți", "views": ["front", "back"], "aop_tile": 170, "draw": draw_leggings,
                 "zones": {"front_leg_left": (566, 430, 96, 96), "back_waist": (440, 90, 120, 64)}},
    "mini_skirt": {"label_ro": "Fustă mini", "views": ["front", "back"], "aop_tile": 200, "draw": draw_skirt,
                   "zones": {"front_center": (390, 450, 220, 180)}},
    "bucket_hat": {"label_ro": "Pălărie bucket", "views": ["front"], "aop_tile": 170, "draw": draw_bucket,
                   "zones": {"front_center": (402, 400, 196, 150)}},
    "cap": {"label_ro": "Șapcă", "views": ["front"], "aop_tile": 170, "draw": draw_cap,
            "zones": {"front_panel": CAP_ZONE}},
    "beanie": {"label_ro": "Fes", "views": ["front"], "aop_tile": 170, "draw": draw_beanie,
               "zones": {"front_cuff": (410, 686, 180, 140)}},
    "socks": {"label_ro": "Șosete", "views": ["front"], "aop_tile": 140, "draw": draw_socks,
              "zones": {"front_leg": (680, 380, 120, 150)}},
    "tote": {"label_ro": "Geantă tote", "views": ["front"], "aop_tile": 200, "draw": draw_tote,
             "zones": {"front_center": (265, 470, 470, 505)}},
    "bandana": {"label_ro": "Bandană", "views": ["front"], "aop_tile": 190, "draw": draw_bandana,
                "zones": {"front_center": (380, 430, 240, 240), "front_corner": (700, 748, 100, 100)}},
    "drawstring_bag": {"label_ro": "Sac sport", "views": ["front"], "aop_tile": 200, "draw": draw_bag,
                       "zones": {"front_center": (300, 420, 400, 460)}},
}
