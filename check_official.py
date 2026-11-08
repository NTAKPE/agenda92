# -*- coding: utf-8 -*-
"""Controle du site officiel affiche sur chaque fiche.

Garantit trois choses :
  1. chaque fiche affiche bien une ligne « site officiel » (identifié ou non) ;
  2. chaque URL affichée comme site officiel provient du registre des pages
     lues, ou du lien de billetterie de l'événement ;
  3. la mention d'indépendance est présente sur chaque fiche.
"""
import json
import os
import re
import sys
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
EXPORT = os.path.join(BASE, "export")
SITE = os.path.join(BASE, "site")

registry = {}
for fn in sorted(os.listdir(DATA)):
    if not fn.endswith(".json") or fn in ("changelog.json", "sites-officiels.json"):
        continue
    payload = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    for s in payload.get("sources", []):
        url = (s.get("url") or "").strip()
        if url:
            registry[url] = True

raw = json.load(open(os.path.join(EXPORT, "tracker-data.json"), encoding="utf-8"))
events = raw["events"] if isinstance(raw, dict) and "events" in raw else raw

problems = []
with_site = 0


def slugify(text):
    """Meme regle que make_site.py, pour retrouver le nom de fichier."""
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "x"


for e in events:
    slug = slugify(e["name"])
    page = os.path.join(SITE, "evenements", slug + ".html")
    if not os.path.exists(page):
        problems.append("fiche absente : %s" % e["name"])
        continue
    html = open(page, encoding="utf-8").read()
    if 'class="officiel"' not in html:
        problems.append("bloc site officiel absent : %s" % e["name"])
    if "agenda n&#39;organise ni ne finance" not in html and "agenda n'organise ni ne finance" not in html:
        problems.append("mention d'independance absente : %s" % e["name"])
    off = e.get("official_site") or {}
    if off.get("url"):
        with_site += 1
        if off["url"] not in registry and off["url"] != e.get("ticket_url"):
            problems.append("URL hors registre : %s (%s)" % (off["url"], e["name"]))
        if off["url"] not in html:
            problems.append("URL non affichee : %s (%s)" % (off["url"], e["name"]))
    else:
        if "non identifi" not in html:
            problems.append("site non identifie non signale : %s" % e["name"])

print("fiches analysees          :", len(events))
print("avec site officiel        :", with_site)
print("site non identifie        :", len(events) - with_site)
print("URL au registre           :", len(registry))
print()
if problems:
    print("PROBLEMES (%d) :" % len(problems))
    for p in problems[:30]:
        print("   *", p)
    sys.exit(1)
print("Chaque fiche indique le site officiel et l'indépendance de l'agenda.")
