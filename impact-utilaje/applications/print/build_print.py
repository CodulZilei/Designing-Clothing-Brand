#!/usr/bin/env python3
"""Impact Utilaje — aplicații PRINT & FIZICE.

Rulare:  python3 applications/print/build_print.py
Generează SVG-uri autonome (logo inline, text convertit în contur) în applications/print/.

Pentru a schimba un logo, modifică doar dicționarul LOGOS de mai jos.
Datele de contact sunt PLACEHOLDER — se înlocuiesc în CONTACT înainte de tipar.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from text2path import outline  # noqa: E402

# ---------------------------------------------------------------- mapping logo
LOGOS = {
    "horizontal":     "logos/v1-rafinat/v1-color.svg",     # logo principal orizontal
    "horizontal_rev": "logos/v1-rafinat/v1-reverse.svg",   # pe fundal închis
    "emblem":         "logos/v2-emblema/v2-color.svg",     # emblemă rotundă (cască)
    "stacked":        "logos/v5-vertical/v5-color.svg",    # pătrat / stivuit
    "icon":           "logos/v3-monograma/v3-icon.svg",    # monogramă IU
    "icon_tile":      "logos/v3-monograma/v3-icon-tile.svg",
    "plate":          "logos/v6-placuta/v6-color.svg",     # plăcuță industrială (utilaj)
}

CONTACT = {
    "name": "Nume Prenume",
    "role": "Funcție",
    "phone": "+40 7XX XXX XXX",
    "email": "contact@domeniu.ro",
    "web": "www.domeniu.ro",
}
SLOGAN = "FORȚĂ ÎN MIȘCARE"

# ---------------------------------------------------------------- paletă
Y, K, G, B, W = "#F2A20A", "#111111", "#4A4F55", "#E6E4DF", "#FFFFFF"

FONT = {
    "black": "ArchivoBlack-Regular.ttf",
    "semi": "Barlow-SemiBold.ttf",
    "reg": "Barlow-Regular.ttf",
    "xb": "Barlow-ExtraBold.ttf",
    "cond": "BarlowCondensed-ExtraBold.ttf",
    "condsemi": "BarlowCondensed-SemiBold.ttf",
}


# ---------------------------------------------------------------- helpers
def T(font, text, size, x, y, fill=K, tracking=0, anchor="start", maxw=None):
    """Text -> <path>. If maxw is given, shrink size to fit."""
    fp = os.path.join(ROOT, "fonts", FONT.get(font, font))
    r = outline(fp, text, size, x, y, tracking, anchor)
    if maxw and r["width"] > maxw:
        size = size * maxw / r["width"]
        r = outline(fp, text, size, x, y, tracking, anchor)
    return '<path fill="%s" d="%s"/>' % (fill, r["d"])


def text_width(font, text, size, tracking=0):
    return outline(os.path.join(ROOT, "fonts", FONT.get(font, font)), text, size, 0, 0, tracking)["width"]


_cache = {}


def _load(key):
    path = LOGOS[key]
    if not os.path.exists(os.path.join(ROOT, path)):
        raise SystemExit("Lipsește fișierul logo: " + path)
    if path not in _cache:
        src = open(os.path.join(ROOT, path), encoding="utf-8").read()
        vb = re.search(r'viewBox="([^"]+)"', src).group(1)
        inner = re.sub(r"^.*?<svg[^>]*>", "", src, flags=re.S)
        inner = re.sub(r"</svg>\s*$", "", inner)
        inner = re.sub(r"<title>.*?</title>", "", inner, flags=re.S)
        _cache[path] = (vb, [float(v) for v in vb.split()], inner.strip())
    return _cache[path]


def logo_aspect(key):
    _, v, _ = _load(key)
    return v[2] / v[3]


def L(key, x, y, w=None, h=None):
    """Inline a logo file as nested <svg>. Give w or h (or both)."""
    vb, v, inner = _load(key)
    ar = v[2] / v[3]
    if w is None:
        w = h * ar
    if h is None:
        h = w / ar
    return '<svg x="%.2f" y="%.2f" width="%.2f" height="%.2f" viewBox="%s">%s</svg>' % (x, y, w, h, vb, inner)


class Doc:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.defs, self.body, self.n = [], [], 0

    def uid(self, p):
        self.n += 1
        return "%s%d" % (p, self.n)

    def add(self, *s):
        self.body.extend(s)

    def hazard(self, x, y, w, h, s=None, c1=Y, c2=K, slant=1):
        """Dungi de avertizare 45° în dreptunghiul (x,y,w,h)."""
        s = s or h * 0.75
        cid = self.uid("hz")
        self.defs.append('<clipPath id="%s"><rect x="%.2f" y="%.2f" width="%.2f" height="%.2f"/></clipPath>' % (cid, x, y, w, h))
        polys = []
        x0 = x - h - 2 * s
        while x0 < x + w + h:
            if slant > 0:
                pts = (x0, y + h, x0 + s, y + h, x0 + s + h, y, x0 + h, y)
            else:
                pts = (x0, y, x0 + s, y, x0 + s + h, y + h, x0 + h, y + h)
            polys.append("M%.2f %.2fL%.2f %.2fL%.2f %.2fL%.2f %.2fZ" % pts)
            x0 += 2 * s
        return ('<g clip-path="url(#%s)"><rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>'
                '<path fill="%s" d="%s"/></g>') % (cid, x, y, w, h, c1, c2, "".join(polys))

    def svg(self, nested=False):
        defs = "<defs>%s</defs>" % "".join(self.defs) if self.defs else ""
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %g %g"><title>%s</title>%s%s</svg>'
                % (self.w, self.h, self.title, defs, "".join(self.body)))

    def nest(self, x, y, w, h, prefix):
        """Return this doc as nested <svg> (ids prefixed to stay unique)."""
        s = self.svg()
        s = re.sub(r'id="([^"]+)"', r'id="%s\1"' % prefix, s)
        s = re.sub(r'url\(#([^)]+)\)', r'url(#%s\1)' % prefix, s)
        s = re.sub(r"<title>.*?</title>", "", s)
        s = s.replace('xmlns="http://www.w3.org/2000/svg" ', "")
        return s.replace("<svg ", '<svg x="%g" y="%g" width="%g" height="%g" ' % (x, y, w, h), 1)

    def save(self, name):
        p = os.path.join(HERE, name)
        open(p, "w", encoding="utf-8").write(self.svg())
        return p


def shadow_filter(d, blur=12, op=0.35):
    fid = d.uid("sh")
    d.defs.append('<filter id="%s" x="-20%%" y="-20%%" width="140%%" height="140%%"><feGaussianBlur stdDeviation="%g"/>'
                  '<feComponentTransfer><feFuncA type="linear" slope="%g"/></feComponentTransfer></filter>' % (fid, blur, op))
    return fid


def lin_grad(d, stops, x2=0, y2=1):
    gid = d.uid("lg")
    st = "".join('<stop offset="%g" stop-color="%s" stop-opacity="%g"/>' % s for s in stops)
    d.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="%g" y2="%g">%s</linearGradient>' % (gid, x2, y2, st))
    return gid


def rad_grad(d, stops):
    gid = d.uid("rg")
    st = "".join('<stop offset="%g" stop-color="%s" stop-opacity="%g"/>' % s for s in stops)
    d.defs.append('<radialGradient id="%s">%s</radialGradient>' % (gid, st))
    return gid


# ================================================================ 1. carte de vizită
def card_front():
    d = Doc(850, 550, "Impact Utilaje — carte de vizită, față")
    d.add('<rect width="850" height="550" fill="%s"/>' % K)
    w = 660
    h = w / logo_aspect("horizontal_rev")
    d.add(L("horizontal_rev", (850 - w) / 2, (550 - 30 - h) / 2, w))
    d.add(d.hazard(0, 520, 850, 30, s=22))
    return d


def card_back():
    d = Doc(850, 550, "Impact Utilaje — carte de vizită, verso")
    d.add('<rect width="850" height="550" fill="%s"/>' % W)
    # bandă dreapta cu monograma
    d.add('<rect x="610" y="0" width="240" height="520" fill="%s"/>' % Y)
    d.add(L("icon", 640, 80, 180))
    d.add(T("cond", "IMPACT", 34, 730, 330, K, tracking=60, anchor="middle"))
    d.add(T("cond", "UTILAJE", 34, 730, 368, K, tracking=60, anchor="middle"))
    # nume + funcție
    x = 64
    d.add(T("black", CONTACT["name"], 46, x, 132, K, maxw=500))
    d.add(T("semi", CONTACT["role"].upper(), 24, x, 172, G, tracking=120))
    d.add('<rect x="%d" y="200" width="70" height="8" fill="%s"/>' % (x, Y))
    rows = [("T", CONTACT["phone"]), ("E", CONTACT["email"]), ("W", CONTACT["web"])]
    for i, (lab, val) in enumerate(rows):
        yy = 285 + i * 66
        d.add('<rect x="%d" y="%d" width="40" height="40" rx="4" fill="%s"/>' % (x, yy - 31, K))
        d.add(T("black", lab, 24, x + 20, yy - 2, Y, anchor="middle"))
        d.add(T("semi", val, 30, x + 60, yy, K, maxw=470))
    d.add(d.hazard(0, 520, 850, 30, s=22))
    return d


def card_presentation(front, back):
    d = Doc(2000, 1250, "Impact Utilaje — cărți de vizită, prezentare")
    g = lin_grad(d, [(0, B, 1), (1, G, 0.55)], 1, 1)
    d.add('<rect width="2000" height="1250" fill="%s"/>' % B)
    d.add('<rect width="2000" height="1250" fill="url(#%s)" opacity=".5"/>' % g)
    f = shadow_filter(d, 18, 0.45)
    for (x, y, rot, doc, p) in [(170, 250, -6, front, "f"), (1030, 420, 4, back, "b")]:
        cw, ch = 850 * 0.95, 550 * 0.95
        d.add('<g transform="rotate(%g %g %g)">' % (rot, x + cw / 2, y + ch / 2))
        d.add('<rect x="%g" y="%g" width="%g" height="%g" fill="%s" filter="url(#%s)"/>' % (x + 10, y + 22, cw, ch, K, f))
        d.add(doc.nest(x, y, cw, ch, p))
        d.add("</g>")
    return d


# ================================================================ 2. antet A4
def letterhead():
    d = Doc(2100, 2970, "Impact Utilaje — antet A4")
    d.add('<rect width="2100" height="2970" fill="%s"/>' % W)
    d.add('<rect x="0" y="0" width="2100" height="26" fill="%s"/>' % Y)
    # header
    lw = 640
    lh = lw / logo_aspect("horizontal")
    d.add(L("horizontal", 150 - lw * 0.04, 120, lw))
    rx = 1950
    lines = [(CONTACT["phone"], "semi", K), (CONTACT["email"], "reg", G), (CONTACT["web"], "reg", G)]
    for i, (t, f, c) in enumerate(lines):
        d.add(T(f, t, 32, rx, 205 + i * 50, c, anchor="end"))
    ly = 120 + lh + 20
    d.add('<rect x="150" y="%g" width="1500" height="4" fill="%s"/>' % (ly + 10, K))
    d.add(d.hazard(1650, ly, 300, 24, s=18))
    # semne de pliere / perforare
    for yy in (1050, 2100):
        d.add('<rect x="0" y="%d" width="50" height="3" fill="%s"/>' % (yy, G))
    d.add('<rect x="0" y="1485" width="30" height="3" fill="%s"/>' % G)
    # footer
    fy = 2640
    d.add(d.hazard(0, fy, 2100, 40, s=30))
    cols = [
        [("Denumire firmă S.R.L.", "xb", K), ("CUI: RO00000000", "reg", G), ("Nr. Reg. Com.: J00/0000/0000", "reg", G)],
        [("Adresă", "xb", K), ("Str. Exemplu nr. 0, Localitate", "reg", G), ("Județ, Cod poștal 000000", "reg", G)],
        [("Contact", "xb", K), ("Telefon: " + CONTACT["phone"], "reg", G), ("Email: " + CONTACT["email"], "reg", G)],
    ]
    xs = [150, 800, 1400]
    for x, col in zip(xs, cols):
        for i, (t, f, c) in enumerate(col):
            d.add(T(f, t, 30, x, fy + 120 + i * 46, c, maxw=560))
    d.add('<rect x="150" y="%d" width="1800" height="2" fill="%s"/>' % (fy + 270, B))
    d.add(T("semi", CONTACT["web"].upper(), 24, 1950, fy + 300 + 3, G, tracking=200, anchor="end"))
    d.add(L("icon", 150, fy + 280, h=34))
    return d


# ================================================================ 3. banner 3×1 m
def banner():
    d = Doc(3000, 1000, "Impact Utilaje — banner de șantier 3×1 m")
    d.add('<rect width="3000" height="1000" fill="%s"/>' % K)
    d.add(d.hazard(0, 0, 3000, 70, s=55))
    d.add(d.hazard(0, 930, 3000, 70, s=55))
    # panou contact
    px = 1960
    d.add('<rect x="%d" y="70" width="%d" height="860" fill="%s"/>' % (px, 3000 - px, Y))
    cx = px + (3000 - px) / 2
    d.add(T("cond", "SUNAȚI-NE", 96, cx, 330, K, tracking=140, anchor="middle"))
    d.add('<rect x="%g" y="372" width="160" height="12" fill="%s"/>' % (cx - 80, K))
    d.add(T("cond", CONTACT["phone"], 190, cx, 600, K, tracking=10, anchor="middle", maxw=920))
    d.add(T("condsemi", CONTACT["web"], 84, cx, 740, K, tracking=40, anchor="middle"))
    # logo + slogan
    lw = 1760
    lh = lw / logo_aspect("horizontal_rev")
    lx, ly = 90, 150
    d.add(L("horizontal_rev", lx, ly, lw))
    d.add(T("cond", SLOGAN, 112, lx + lw * 0.04 + 6, 830, W, tracking=180))
    return d


# ================================================================ 4a. autocolant cască + mockup
def helmet_sticker():
    d = Doc(600, 600, "Impact Utilaje — autocolant cască Ø60 mm")
    d.add('<circle cx="300" cy="300" r="300" fill="%s"/>' % W)
    d.add(L("emblem", 10, 10, 580))
    return d


def helmet_mockup(sticker):
    d = Doc(1400, 1000, "Impact Utilaje — autocolant pe cască, mockup")
    bg = lin_grad(d, [(0, B, 1), (1, G, 0.6)])
    d.add('<rect width="1400" height="1000" fill="%s"/><rect width="1400" height="1000" fill="url(#%s)" opacity=".55"/>' % (B, bg))
    sh = rad_grad(d, [(0, K, 0.45), (1, K, 0)])
    d.add('<ellipse cx="700" cy="800" rx="470" ry="46" fill="url(#%s)"/>' % sh)
    shell = lin_grad(d, [(0, W, 1), (0.7, W, 1), (1, B, 1)], 0.3, 1)
    shade = lin_grad(d, [(0, K, 0), (0.6, K, 0), (1, K, 0.22)], 1, 0.3)
    dome = "M330 740 C330 450 480 260 690 260 C900 260 1050 430 1060 740 Z"
    d.add('<path d="%s" fill="url(#%s)"/>' % (dome, shell))
    d.add('<path d="%s" fill="url(#%s)"/>' % (dome, shade))
    # nervură centrală
    d.add('<path d="M470 420 C540 310 620 282 700 280 C800 278 900 330 970 430 L950 448 C890 365 800 318 700 320 C620 322 550 350 492 438 Z" fill="%s" opacity=".75"/>' % B)
    # bor + cozoroc
    d.add('<path d="M300 740 L1060 740 C1140 740 1210 752 1240 782 C1200 800 1120 800 1030 796 L330 788 C296 786 286 760 300 740 Z" fill="%s"/>' % W)
    d.add('<path d="M300 740 L1060 740 C1140 740 1210 752 1240 782 C1200 800 1120 800 1030 796 L330 788 C296 786 286 760 300 740 Z" fill="%s" opacity=".18"/>' % G)
    d.add('<path d="M335 706 L1056 706 L1060 740 L330 740 Z" fill="%s" opacity=".55"/>' % B)
    # autocolant (ușor comprimat pe orizontală — suprafață curbă)
    d.add('<g transform="translate(565 395) scale(0.86 1)">%s</g>' % sticker.nest(0, 0, 290, 290, "st"))
    d.add('<path d="M330 740 C330 450 480 260 690 260 C600 300 470 420 410 740 Z" fill="%s" opacity=".05"/>' % K)
    d.add(T("semi", "Autocolant rotund Ø60 mm — emblemă", 30, 700, 920, G, anchor="middle"))
    return d


# ================================================================ 4b. autocolant utilaj + mockup
def machine_decal():
    d = Doc(1040, 600, "Impact Utilaje — autocolant utilaj (plăcuță)")
    d.add(L("plate", 0, 0, 1040, 600))
    return d


def machine_mockup(decal):
    d = Doc(1600, 1000, "Impact Utilaje — autocolant pe panou utilaj, mockup")
    d.add('<rect width="1600" height="1000" fill="%s"/>' % Y)
    sh = lin_grad(d, [(0, W, 0.22), (0.35, W, 0), (1, K, 0.25)])
    # panou (ușă de capotă)
    d.add('<rect x="70" y="60" width="1460" height="820" rx="38" fill="%s" opacity=".55"/>' % K)
    d.add('<rect x="76" y="66" width="1448" height="808" rx="34" fill="%s"/>' % Y)
    d.add('<rect x="76" y="66" width="1448" height="808" rx="34" fill="url(#%s)"/>' % sh)
    # grilă de aerisire
    for i in range(8):
        yy = 560 + i * 36
        d.add('<rect x="1190" y="%d" width="260" height="18" rx="9" fill="%s" opacity=".75"/>' % (yy, K))
    # mâner
    d.add('<rect x="1230" y="180" width="180" height="56" rx="28" fill="%s" opacity=".6"/>' % K)
    d.add('<rect x="1250" y="194" width="140" height="28" rx="14" fill="%s"/>' % G)
    # șuruburi
    for (bx, by) in [(120, 110), (1480, 110), (120, 830), (1480, 830)]:
        d.add('<circle cx="%d" cy="%d" r="15" fill="%s"/><circle cx="%d" cy="%d" r="10" fill="%s"/><rect x="%d" y="%d" width="14" height="3" fill="%s"/>'
              % (bx, by, G, bx, by, B, bx - 7, by - 1.5, G))
    # autocolant
    f = shadow_filter(d, 6, 0.35)
    dw, dh = 960, 960 / (1040 / 600)
    dx, dy = 170, 170
    d.add('<rect x="%g" y="%g" width="%g" height="%g" rx="30" fill="%s" filter="url(#%s)"/>' % (dx + 50, dy + 30 + 6, dw - 100, dh - 64, K, f))
    d.add(decal.nest(dx, dy, dw, dh, "dc"))
    d.add(d.hazard(0, 920, 1600, 80, s=60))
    return d


# ================================================================ 5. autoutilitară
def van_decal():
    d = Doc(1200, 700, "Impact Utilaje — autocolant ușă autoutilitară 120×70 cm")
    lw = 1200
    d.add(L("horizontal", 0, 0, lw))
    d.add(T("black", CONTACT["phone"], 104, 600, 520, K, anchor="middle", maxw=1000))
    d.add(T("semi", CONTACT["web"], 64, 600, 630, G, tracking=60, anchor="middle"))
    return d


def van_mockup(decal):
    d = Doc(2400, 1200, "Impact Utilaje — autoutilitară, mockup lateral")
    d.add('<rect width="2400" height="1200" fill="%s"/>' % B)
    d.add('<rect y="1010" width="2400" height="190" fill="%s" opacity=".35"/>' % G)
    sh = rad_grad(d, [(0, K, 0.5), (1, K, 0)])
    d.add('<ellipse cx="1230" cy="1010" rx="1080" ry="40" fill="url(#%s)"/>' % sh)
    body = ("M275 250 L1630 250 Q1675 250 1700 280 L1905 525 L2150 590 Q2215 608 2218 665 L2222 842 Q2222 875 2190 875 "
            "L2020 875 A140 140 0 0 0 1740 875 L700 875 A140 140 0 0 0 420 875 L275 875 Q245 875 245 845 L245 280 Q245 250 275 250 Z")
    cid = d.uid("body")
    d.defs.append('<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, body))
    gb = lin_grad(d, [(0, W, 1), (0.75, W, 1), (1, B, 1)])
    d.add('<path d="%s" fill="url(#%s)"/>' % (body, gb))
    d.add('<g clip-path="url(#%s)">' % cid)
    # dungă de avertizare pe partea inferioară
    d.add(d.hazard(240, 770, 1990, 54, s=40))
    d.add('<rect x="240" y="824" width="1990" height="60" fill="%s"/>' % G)
    # cusături uși
    for x in (880, 1600):
        d.add('<rect x="%d" y="262" width="4" height="508" fill="%s" opacity=".45"/>' % (x, G))
    d.add('<rect x="1880" y="525" width="4" height="245" fill="%s" opacity=".45"/>' % G)
    d.add("</g>")
    # geamuri
    d.add('<path d="M1625 292 L1680 292 L1870 520 L1625 520 Z" fill="%s"/>' % G)
    d.add('<path d="M1640 300 L1672 300 L1700 334 L1640 334 Z" fill="%s" opacity=".25"/>' % W)
    d.add('<path d="M1700 280 L1905 525 L1925 530 L1715 270 Z" fill="%s"/>' % K)
    # oglindă, mânere, far, stop
    d.add('<path d="M1860 470 L1910 470 L1915 540 L1868 540 Z" fill="%s"/>' % K)
    for (x, y) in [(1560, 560), (1830, 580)]:
        d.add('<rect x="%d" y="%d" width="60" height="16" rx="8" fill="%s"/>' % (x, y, G))
    d.add('<path d="M2150 600 Q2205 612 2212 660 L2212 690 L2140 690 Z" fill="%s"/>' % B)
    d.add('<path d="M2160 612 Q2200 622 2205 660 L2160 660 Z" fill="%s"/>' % W)
    d.add('<rect x="248" y="560" width="22" height="150" rx="6" fill="%s"/>' % G)
    # bare de protecție
    d.add('<rect x="2120" y="830" width="110" height="60" rx="14" fill="%s"/>' % K)
    d.add('<rect x="225" y="830" width="110" height="60" rx="14" fill="%s"/>' % K)
    # roți
    for cx in (560, 1880):
        d.add('<circle cx="%d" cy="890" r="118" fill="%s"/><circle cx="%d" cy="890" r="64" fill="%s"/>'
              '<circle cx="%d" cy="890" r="46" fill="%s"/><circle cx="%d" cy="890" r="14" fill="%s"/>'
              % (cx, K, cx, G, cx, B, cx, G))
    # autocolant ușă (pe zona de marfă)
    dw = 660
    dh = dw * 700 / 1200
    d.add(decal.nest(1240 - dw / 2, 330, dw, dh, "vd"))
    return d


# ================================================================ build
def main():
    out = []
    cf, cb = card_front(), card_back()
    out += [cf.save("carte-vizita-fata.svg"), cb.save("carte-vizita-verso.svg")]
    out.append(card_presentation(cf, cb).save("carte-vizita-prezentare.svg"))
    out.append(letterhead().save("antet-a4.svg"))
    out.append(banner().save("banner-santier-3x1m.svg"))
    st = helmet_sticker()
    out.append(st.save("autocolant-casca-60mm.svg"))
    out.append(helmet_mockup(st).save("mockup-casca.svg"))
    md = machine_decal()
    out.append(md.save("autocolant-utilaj.svg"))
    out.append(machine_mockup(md).save("mockup-panou-utilaj.svg"))
    vd = van_decal()
    out.append(vd.save("autocolant-usa-autoutilitara.svg"))
    out.append(van_mockup(vd).save("mockup-autoutilitara.svg"))
    for p in out:
        s = open(p, encoding="utf-8").read()
        assert "<text" not in s, p
    print("\n".join(out))


if __name__ == "__main__":
    main()
