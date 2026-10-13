#!/usr/bin/env python3
"""Source of truth for the 100 pieces of the NEPĂMÂNTEAN collection.

Run `python3 products.py` to regenerate products.json (read by engine/engine.py and the catalog page).
Each row: id, name, garment, fabric (or AOP pattern), front prints, back prints, price in lei, description.
Prints are "graphic@zone" (graphic file in graphics/, zone defined by the garment).
"""
import json
import os

FABRICS = {
    "negru": ("Negru", "#111114"),
    "negru-spalat": ("Negru spălat", "#2A2A2E"),
    "bleumarin": ("Bleumarin", "#1B2140"),
    "carbune": ("Cărbune", "#3A3B40"),
    "mov": ("Mov închis", "#3B2558"),
    "alb": ("Alb", "#F5F5F2"),
    "melanj": ("Gri melanj", "#A7A8AB"),
    "lavanda": ("Lavandă", "#C9C3E6"),
    "bleu": ("Bleu", "#B9D3EF"),
    "roz": ("Roz prăfuit", "#E6C4CF"),
    "crem": ("Crem", "#ECE5D6"),
}

PATTERNS = {
    "p01": "Câmp de stele", "p02": "Galaxie", "p03": "Scanline", "p04": "Geometrie sacră", "p05": "Ochi",
    "p06": "Glitch", "p07": "Planete", "p08": "Nebuloasă", "p09": "Grilă", "p10": "Static",
}

GARMENT_LABEL = {
    "tee_oversized": "Tricou oversized", "tee_baby_crop": "Baby tee", "longsleeve": "Bluză cu mânecă lungă",
    "longsleeve_crop": "Bluză crop cu mânecă lungă", "tank": "Maiou", "crop_tank": "Crop top",
    "hoodie": "Hanorac oversized", "crop_hoodie": "Hanorac crop", "zip_hoodie": "Hanorac cu fermoar",
    "crewneck": "Bluză crewneck", "windbreaker": "Geacă windbreaker", "tshirt_dress": "Rochie-tricou",
    "sports_bra": "Bustieră sport", "shorts": "Pantaloni scurți", "biker_shorts": "Pantaloni biker",
    "joggers": "Pantaloni jogger", "leggings": "Colanți", "mini_skirt": "Fustă mini",
    "bucket_hat": "Pălărie bucket", "cap": "Șapcă", "beanie": "Fes", "socks": "Șosete",
    "tote": "Geantă tote", "bandana": "Bandană", "drawstring_bag": "Sac sport",
}

CATEGORY = {
    "tee_oversized": "tricouri", "tee_baby_crop": "tricouri", "tank": "tricouri", "crop_tank": "tricouri",
    "longsleeve": "bluze", "longsleeve_crop": "bluze", "crewneck": "bluze",
    "hoodie": "hanorace", "crop_hoodie": "hanorace", "zip_hoodie": "hanorace",
    "windbreaker": "geci", "tshirt_dress": "rochii-fuste", "mini_skirt": "rochii-fuste",
    "sports_bra": "sport", "biker_shorts": "sport", "leggings": "sport",
    "shorts": "pantaloni", "joggers": "pantaloni",
    "bucket_hat": "accesorii", "cap": "accesorii", "beanie": "accesorii", "socks": "accesorii",
    "tote": "accesorii", "bandana": "accesorii", "drawstring_bag": "accesorii",
}

# id, name, garment, fabric-or-pattern, front, back, price, description
ROWS = [
    # ---------------- BĂIEȚI ----------------
    ("B01", "Nepământean", "tee_oversized", "negru", "m01-dark@front_chest_left", "g01-dark@back_center", 179, "Piesa-manifest a colecției: litere 3D ondulate deasupra unui vârtej violet, cu eticheta de clasificare „N”."),
    ("B02", "Not From Here", "tee_oversized", "negru-spalat", "m06-dark@front_chest_center", "g02-dark@back_center", 179, "Pământul se topește în pixeli, iar textul se arcuiește deasupra lui."),
    ("B03", "Realitatea e o simulare", "tee_oversized", "negru", "g03-dark@front_center", "", 179, "Afiș de ecran CRT cu ochi, geometrie sacră și text mărunt de conspirație."),
    ("B04", "Câmp adânc", "tee_oversized", "negru", "m02-dark@front_chest_left", "g07-dark@back_center", 179, "Galaxie spirală din mii de particule aurii și albastre."),
    ("B05", "Orizontul evenimentelor", "tee_oversized", "carbune", "g08-dark@front_center", "", 179, "Gaură neagră cu disc de acreție. Nu există cale de întoarcere."),
    ("B06", "Planeta B", "tee_oversized", "negru", "m01-dark@front_chest_left", "g09-dark@back_center", 179, "Peisaj extraterestru cu apă aurie și o planetă cu inele pe cer."),
    ("B07", "Semnal pierdut", "tee_oversized", "alb", "g05-light@front_center", "", 179, "Mira TV spartă în benzi de glitch. Canal 404."),
    ("B08", "Duceți-mă acasă", "tee_oversized", "bleumarin", "m05-dark@front_chest_left", "g11-dark@back_center", 179, "OZN cu rază de tractare. Pentru cine simte că nu e de aici."),
    ("B09", "Vizitator", "tee_oversized", "negru", "g22-dark@front_center", "", 179, "Cap de extraterestru cromat, cu linii de scanare."),
    ("B10", "404 Realitate", "tee_oversized", "melanj", "g19-light@front_center", "", 179, "Realitatea nu a fost găsită. Fereastră de eroare pixelată."),
    ("B11", "Cerul cade peste cartier", "tee_oversized", "negru", "m06-dark@front_chest_center", "g16-dark@back_center", 179, "Ploaie de meteoriți peste blocurile din cartier."),
    ("B12", "Ascultăm cerul", "tee_oversized", "negru-spalat", "g17-dark@front_center", "", 179, "Radiotelescop care prinde un semnal la 03:17."),
    ("B13", "Nu suntem singuri", "tee_oversized", "alb", "m05-light@front_chest_left", "g29-light@back_center", 179, "Varianta discretă: un OZN mic și un mesaj scurt."),
    ("B14", "Pământul e doar o escală", "tee_oversized", "negru", "m03-dark@front_chest_left", "g34-dark@back_center", 179, "Panou de plecări: Marte întârziat, Saturn la timp, Acasă anulat."),
    ("B15", "Gaura de vierme", "longsleeve", "negru", "g20-dark@front_center", "m06-dark@back_neck", 199, "Tunel de inele cyan și violet care se pierd în depărtare."),
    ("B16", "Transmisie", "longsleeve", "alb", "g24-light@front_center", "", 199, "Ecran de osciloscop cu oră și sursă necunoscută."),
    ("B17", "Geometrie sacră", "longsleeve", "negru", "m01-dark@front_chest_left", "g06-dark@back_center", 199, "Cubul lui Metatron în linii cromate, cu un ochi în centru."),
    ("B18", "Orizont 2099", "longsleeve", "bleumarin", "g30-dark@front_center", "", 199, "Grilă retro-futuristă, munți din sârmă și o planetă care răsare."),
    ("B19", "Hanorac Nepământean", "hoodie", "negru", "m06-dark@front_chest_center", "g01-dark@back_center", 349, "Piesa-manifest pe hanorac greu, oversized."),
    ("B20", "Ochiul", "hoodie", "negru", "g04-dark@front_center", "", 349, "Iris generat din sute de fibre, cu text mic: te văd."),
    ("B21", "Static", "hoodie", "carbune", "m04-dark@front_chest_left", "g23-dark@back_center", 349, "Tot ce vezi e static: ecran CRT plin de zgomot."),
    ("B22", "Pierdut în orbită", "hoodie", "bleumarin", "m01-dark@front_chest_left", "g12-dark@back_center", 349, "Astronaut cu cablul tăiat, deasupra curburii Pământului."),
    ("B23", "Clasificat N", "hoodie", "negru-spalat", "m03-dark@front_chest_left", "g10-dark@back_center", 349, "Eticheta de clasificare inventată de noi, în format mare."),
    ("B24", "Vede tot", "hoodie", "negru", "m04-dark@front_chest_left", "g21-dark@back_center", 349, "Ochi în triunghi, cu raze și glitch."),
    ("B25", "Protocol de contact", "hoodie", "melanj", "m05-light@front_chest_left", "g32-light@back_center", 349, "Instrucțiuni tehnice pentru primul contact, în 4 pași."),
    ("B26", "Globul", "zip_hoodie", "negru", "m01-dark@front_chest_left", "g33-dark@back_center", 379, "Emblema mare: glob din sârmă, stea și orbite."),
    ("B27", "Câmp de stele", "zip_hoodie", "aop:p01", "", "", 399, "Imprimeu complet cu stele sclipitoare pe negru."),
    ("B28", "Buletin intergalactic", "zip_hoodie", "carbune", "m03-dark@front_chest_left", "g18-dark@back_center", 379, "Carte de identitate pentru vizitatori din altă galaxie."),
    ("B29", "Harta cerului", "crewneck", "bleumarin", "g14-dark@front_center", "", 299, "Cerul deasupra Bucureștiului, cu constelații și coordonate."),
    ("B30", "Doar cerul e real", "crewneck", "negru", "g31-dark@front_center", "", 299, "Nori, raze și un glitch fin."),
    ("B31", "Fazele lunii", "crewneck", "carbune", "g15-dark@front_center", "", 299, "Luna știe. Faze cu cratere, în coloană."),
    ("B32", "Galaxie", "shorts", "aop:p02", "", "", 199, "Pantaloni scurți cu imprimeu complet de galaxie."),
    ("B33", "Glitch", "shorts", "aop:p06", "", "", 199, "Benzi RGB deplasate, ca un semnal stricat."),
    ("B34", "Static", "shorts", "aop:p10", "", "", 199, "Zgomot TV cu nuanță albastră."),
    ("B35", "Nepământean", "joggers", "negru", "m06-dark@front_leg_left", "", 279, "Pantaloni largi cu textul colecției pe piciorul stâng."),
    ("B36", "Grilă", "joggers", "aop:p09", "", "", 299, "Imprimeu complet cu grilă cyan pe negru."),
    ("B37", "Semnal", "joggers", "carbune", "m04-dark@front_leg_left", "", 279, "Ochiul pixelat pe picior, restul curat."),
    ("B38", "Nebuloasă", "windbreaker", "aop:p08", "", "", 399, "Geacă ușoară cu nebuloasă violet și albastră."),
    ("B39", "Scanline", "windbreaker", "aop:p03", "", "", 399, "Benzi cyan-indigo cu linii de scanare."),
    ("B40", "Câmp adânc", "tank", "negru", "g07-dark@front_center", "", 139, "Maiou cu galaxia spirală pe piept."),
    # ---------------- FETE ----------------
    ("F01", "Fată de pe altă planetă", "tee_baby_crop", "alb", "g25-light@front_center", "", 149, "Litere cu cratere de lună, o planetă mică și sclipiri."),
    ("F02", "Cosmic baby", "tee_baby_crop", "roz", "g28-light@front_center", "", 149, "Text cromat Y2K cu stele."),
    ("F03", "Înger sau extraterestră", "tee_baby_crop", "negru", "g26-dark@front_center", "", 149, "Inimă-planetă cu aureolă și antene."),
    ("F04", "Luna e a mea", "tee_baby_crop", "lavanda", "g27-light@front_center", "", 149, "Semilună, stele și scris elegant."),
    ("F05", "Întoarcerea lui Saturn", "tee_baby_crop", "bleu", "g13-light@front_center", "", 149, "Saturn cromat cu inele lucioase."),
    ("F06", "Sclipire", "tee_baby_crop", "negru", "m02-dark@front_chest_center", "", 139, "O singură stea cromată, pe mijloc."),
    ("F07", "404", "tee_baby_crop", "alb", "g19-light@front_center", "", 149, "Realitatea nu a fost găsită, în varianta crop."),
    ("F08", "Nu suntem singuri", "tee_baby_crop", "negru", "g29-dark@front_center", "", 149, "OZN mic, mesaj scurt."),
    ("F09", "Ochiul", "tee_oversized", "negru", "g04-dark@front_center", "", 179, "Irisul mare, pe tricou oversized."),
    ("F10", "Harta cerului", "tee_oversized", "crem", "g14-light@front_center", "", 179, "Harta cerului în bleumarin pe crem."),
    ("F11", "Geometrie sacră", "tee_oversized", "negru", "m01-dark@front_chest_left", "g06-dark@back_center", 179, "Cubul lui Metatron pe spate."),
    ("F12", "Nepământean", "tee_oversized", "mov", "", "g01-dark@back_center", 179, "Piesa-manifest pe mov închis."),
    ("F13", "Fazele lunii", "tee_oversized", "alb", "g15-light@front_center", "", 179, "Fazele lunii în negru pe alb."),
    ("F14", "Nepământean", "crop_hoodie", "negru", "m06-dark@front_chest_center", "g01-dark@back_center", 299, "Hanorac crop cu piesa-manifest pe spate."),
    ("F15", "Cosmic baby", "crop_hoodie", "roz", "g28-light@front_center", "", 299, "Text cromat pe roz prăfuit."),
    ("F16", "Galaxie", "crop_hoodie", "negru", "g07-dark@front_center", "", 299, "Galaxia spirală pe piept."),
    ("F17", "Luna e a mea", "crop_hoodie", "crem", "g27-light@front_center", "", 299, "Semilună și scris elegant pe crem."),
    ("F18", "Saturn", "crop_hoodie", "negru", "g13-dark@front_center", "", 299, "Saturn cromat pe negru."),
    ("F19", "Orizontul evenimentelor", "hoodie", "negru", "m02-dark@front_chest_left", "g08-dark@back_center", 349, "Gaura neagră pe spate, sclipire pe piept."),
    ("F20", "Doar cerul e real", "hoodie", "alb", "m01-light@front_chest_left", "g31-light@back_center", 349, "Nori și raze pe hanorac alb."),
    ("F21", "Vizitator", "hoodie", "mov", "g22-dark@front_center", "", 349, "Extraterestrul cromat pe mov închis."),
    ("F22", "Câmp de stele", "mini_skirt", "aop:p01", "", "", 179, "Fustă mini cu stele sclipitoare."),
    ("F23", "Geometrie sacră", "mini_skirt", "aop:p04", "", "", 179, "Floarea vieții în linii pe indigo."),
    ("F24", "Planete", "mini_skirt", "aop:p07", "", "", 179, "Planete și luni presărate pe bleumarin."),
    ("F25", "Glitch", "mini_skirt", "aop:p06", "", "", 179, "Benzi RGB deplasate."),
    ("F26", "Nebuloasă", "biker_shorts", "aop:p08", "", "", 169, "Pantaloni biker cu nebuloasă."),
    ("F27", "Grilă", "biker_shorts", "aop:p09", "", "", 169, "Grilă cyan pe negru."),
    ("F28", "Ochi", "biker_shorts", "aop:p05", "", "", 169, "Ochi repetați, posterizați."),
    ("F29", "Galaxie", "leggings", "aop:p02", "", "", 189, "Colanți cu galaxie pe toată lungimea."),
    ("F30", "Scanline", "leggings", "aop:p03", "", "", 189, "Benzi cyan-indigo cu linii de scanare."),
    ("F31", "Static", "leggings", "aop:p10", "", "", 189, "Zgomot TV cu nuanță albastră."),
    ("F32", "Câmp de stele", "crop_tank", "aop:p01", "", "", 129, "Crop top cu stele sclipitoare."),
    ("F33", "Ochi", "crop_tank", "alb", "m04-light@front_chest_center", "", 129, "Ochiul pixelat, mic, pe alb."),
    ("F34", "Nebuloasă", "crop_tank", "aop:p08", "", "", 129, "Crop top cu nebuloasă."),
    ("F35", "Nepământean", "tshirt_dress", "negru", "g01-dark@front_center", "", 229, "Rochie-tricou largă cu piesa-manifest în față."),
    ("F36", "Semnal pierdut", "tshirt_dress", "alb", "g05-light@front_center", "", 229, "Mira TV spartă pe rochie-tricou albă."),
    ("F37", "Galaxie", "tshirt_dress", "aop:p02", "", "", 249, "Rochie-tricou cu imprimeu complet de galaxie."),
    ("F38", "Planete", "sports_bra", "aop:p07", "", "", 149, "Bustieră sport cu planete."),
    ("F39", "Geometrie sacră", "sports_bra", "aop:p04", "", "", 149, "Bustieră sport cu floarea vieții."),
    ("F40", "Harta cerului", "longsleeve_crop", "negru", "g14-dark@front_center", "", 179, "Harta cerului în alb pe negru, croială crop."),
    # ---------------- UNISEX / ACCESORII ----------------
    ("U01", "Câmp de stele", "bucket_hat", "aop:p01", "", "", 149, "Pălărie bucket cu stele."),
    ("U02", "Galaxie", "bucket_hat", "aop:p02", "", "", 149, "Pălărie bucket cu galaxie."),
    ("U03", "Glitch", "bucket_hat", "aop:p06", "", "", 149, "Pălărie bucket cu benzi RGB."),
    ("U04", "Ochi", "bucket_hat", "aop:p05", "", "", 149, "Pălărie bucket cu ochi repetați."),
    ("U05", "Globul", "cap", "negru", "m01-dark@front_panel", "", 139, "Șapcă cu emblema glob, brodată."),
    ("U06", "OZN", "cap", "bleumarin", "m05-dark@front_panel", "", 139, "Șapcă cu OZN mic, brodat."),
    ("U07", "Nepământean", "cap", "alb", "m06-light@front_panel", "", 139, "Șapcă albă cu textul colecției."),
    ("U08", "Sclipire", "beanie", "negru", "m02-dark@front_cuff", "", 119, "Fes cu stea brodată."),
    ("U09", "Globul", "beanie", "mov", "m01-dark@front_cuff", "", 119, "Fes mov cu emblema glob."),
    ("U10", "Câmp de stele", "socks", "aop:p01", "", "", 79, "Șosete cu stele."),
    ("U11", "Ochi", "socks", "aop:p05", "", "", 79, "Șosete cu ochi."),
    ("U12", "Planete", "socks", "aop:p07", "", "", 79, "Șosete cu planete."),
    ("U13", "Grilă", "socks", "aop:p09", "", "", 79, "Șosete cu grilă cyan."),
    ("U14", "Realitatea e o simulare", "tote", "negru", "g03-dark@front_center", "", 99, "Geantă tote cu afișul CRT."),
    ("U15", "Harta cerului", "tote", "crem", "g14-light@front_center", "", 99, "Geantă tote naturală cu harta cerului."),
    ("U16", "Pământul e doar o escală", "tote", "negru", "g34-dark@front_center", "", 99, "Geantă tote cu panoul de plecări."),
    ("U17", "Geometrie sacră", "bandana", "aop:p04", "", "", 79, "Bandană cu floarea vieții."),
    ("U18", "Nebuloasă", "bandana", "aop:p08", "", "", 79, "Bandană cu nebuloasă."),
    ("U19", "Galaxie", "drawstring_bag", "aop:p02", "", "", 119, "Sac sport cu galaxie."),
    ("U20", "Static", "drawstring_bag", "aop:p10", "", "", 119, "Sac sport cu zgomot TV."),
]


def parse_prints(s):
    out = []
    for part in filter(None, s.split(",")):
        g, z = part.split("@")
        out.append({"graphic": g, "zone": z})
    return out


def build():
    products = []
    for pid, name, garment, fab, front, back, price, desc in ROWS:
        gender = {"B": "baieti", "F": "fete", "U": "unisex"}[pid[0]]
        p = {
            "id": pid, "name": name, "gender": gender, "garment": garment,
            "garment_label": GARMENT_LABEL[garment], "category": CATEGORY[garment],
            "price": price, "description": desc,
            "prints": {"front": parse_prints(front), "back": parse_prints(back)},
        }
        if fab.startswith("aop:"):
            pat = fab[4:]
            p["aop"] = pat
            p["colors"] = [{"name": "Imprimeu " + PATTERNS[pat], "hex": "#111114"}]
            p["technique"] = "Imprimeu complet (all-over, sublimare)"
        else:
            n, h = FABRICS[fab]
            p["colors"] = [{"name": n, "hex": h}]
            techs = []
            for pr in p["prints"]["front"] + p["prints"]["back"]:
                small = pr["graphic"].startswith("m") and garment in ("cap", "beanie")
                techs.append("broderie" if small else "DTG")
            p["technique"] = " + ".join(sorted(set(techs))) if techs else "—"
        products.append(p)
    assert len(products) == 100, len(products)
    assert len({p["id"] for p in products}) == 100
    return products


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ps = build()
    json.dump(ps, open(os.path.join(here, "products.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    graphics = sorted({pr["graphic"] for p in ps for v in ("front", "back") for pr in p["prints"][v]})
    patterns = sorted({p["aop"] for p in ps if p.get("aop")})
    zones = {}
    for p in ps:
        for v in ("front", "back"):
            for pr in p["prints"][v]:
                zones.setdefault(p["garment"], set()).add(pr["zone"])
    print(len(ps), "products;", len(graphics), "graphic files;", len(patterns), "patterns")
    print("graphics:", " ".join(graphics))
    print("zones used per garment:")
    for g in sorted(zones):
        print(f"  {g}: {', '.join(sorted(zones[g]))}")
    from collections import Counter
    print(Counter(p["gender"] for p in ps), Counter(p["garment"] for p in ps).most_common())
