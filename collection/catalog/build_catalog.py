#!/usr/bin/env python3
"""Build catalog/index.html (the voting catalog for the 100 pieces) from products.json.

Images are not copied: the Artifact publish maps img/<id>-<view>.jpg to
mockups/web/<id>-<view>.jpg and img/hero.jpg to catalog/hero.jpg.
Prints the `files` mapping (JSON) to pass to the publish call.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WEB = os.path.join(ROOT, "mockups", "web")

products = json.load(open(os.path.join(ROOT, "products.json"), encoding="utf-8"))
keep = ("id", "name", "gender", "garment", "garment_label", "category", "price", "description", "prints", "colors", "technique")
slim = [{k: p[k] for k in keep if k in p} for p in products]

views, files, missing = {}, {}, []
for p in products:
    vs = [v for v in ("front", "back") if os.path.exists(os.path.join(WEB, f'{p["id"]}-{v}.jpg'))]
    if not vs:
        missing.append(p["id"])
    views[p["id"]] = vs or ["front"]
    for v in vs:
        files[f'img/{p["id"]}-{v}.jpg'] = os.path.relpath(os.path.join(WEB, f'{p["id"]}-{v}.jpg'), os.getcwd())
hero = os.path.join(HERE, "hero.jpg")
if os.path.exists(hero):
    files["img/hero.jpg"] = os.path.relpath(hero, os.getcwd())

tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
html = tpl.replace("/*__PRODUCTS__*/[]", json.dumps(slim, ensure_ascii=False)).replace("/*__VIEWS__*/{}", json.dumps(views))
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
json.dump(files, open(os.path.join(HERE, "files.json"), "w"), indent=0)
print(f"index.html written; {len(files)} image files; missing mockups: {missing or 'none'}")
