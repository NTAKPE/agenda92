# -*- coding: utf-8 -*-
"""Controle des sources citees affichees sur les fiches evenement.

Trois garanties :
  1. chaque lien affiche vient du registre des sources reellement consultees
     (aucune URL inventee) ;
  2. chaque domaine cite vient du texte d'arbitrage de la fiche ;
  3. les jetons extraits ne sont pas des faux positifs (abbreviations, mois).
"""
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.join(BASE, "export")
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")

sys.path.insert(0, BASE)
from siteutil import cited_domains, host_of, NOT_A_DOMAIN  # noqa: E402

# --- registre des sources consultees (data/zone-*.json) --------------------
registry = {}
for fn in sorted(f for f in os.listdir(DATA)
                 if f.startswith("zone-") and f.endswith(".json")) + ["sources-additionnels.json"]:
    path = os.path.join(DATA, fn)
    if not os.path.exists(path):
        continue
    payload = json.load(open(path, encoding="utf-8"))
    for s in payload.get("sources", []):
        url = (s.get("url") or "").strip()
        if url:
            registry[url] = (s.get("name") or url, s.get("accessed") or "", fn)

raw = json.load(open(os.path.join(EXPORT, "tracker-data.json"), encoding="utf-8"))
events = raw["events"] if isinstance(raw, dict) and "events" in raw else raw

BLOCKLIST = set(NOT_A_DOMAIN) | {
    "novembre", "decembre", "fevrier", "septembre", "octobre", "aout",
    "janvier", "fevr", "avr", "juil", "sept", "dec", "nov", "fr", "com",
}

problems = []
n_links = 0
n_unlinked = 0
fiches_avec_liens = 0
samples = []

for e in events:
    raw_text = " ".join([e.get("conflicts") or "", e.get("notes") or ""]).lower()
    cited = e.get("cited_sources") or []
    unlinked = e.get("cited_unlinked") or []
    n_links += len(cited)
    n_unlinked += len(unlinked)
    if cited:
        fiches_avec_liens += 1

    for s in cited:
        url = s.get("url") or ""
        if url not in registry:
            problems.append("URL hors registre : %s (%s)" % (url, e["name"]))
        if s.get("domain") and s["domain"] not in raw_text:
            problems.append("domaine absent du texte d'arbitrage : %s (%s)"
                            % (s.get("domain"), e["name"]))
        if (s.get("domain") or "") in BLOCKLIST:
            problems.append("jeton suspect : %s (%s)" % (s.get("domain"), e["name"]))

    for d in unlinked:
        if d not in raw_text:
            problems.append("domaine non lie absent du texte : %s (%s)" % (d, e["name"]))
        if d in BLOCKLIST:
            problems.append("jeton suspect (non lie) : %s (%s)" % (d, e["name"]))

    # la page publiee doit porter les memes liens
    slug = re.sub(r"[^a-z0-9]+", "-", e["name"].lower()).strip("-")
    page = os.path.join(SITE, "evenements", slug + ".html")
    if os.path.exists(page):
        html = open(page, encoding="utf-8").read()
        for s in cited:
            if s["url"] not in html:
                problems.append("lien absent de la page : %s (%s)" % (s["url"], e["name"]))
        if e.get("ticket_url") and "Billetterie / inscription" not in html:
            problems.append("billetterie non affichee : %s" % e["name"])

    if cited and len(samples) < 10:
        samples.append((e["name"][:48], " ; ".join(s["name"][:46] for s in cited[:3])))

print("evenements analyses          :", len(events))
print("URL dans le registre         :", len(registry))
print("sources citees rattachees    :", n_links)
print("fiches avec sources rattachees:", fiches_avec_liens)
print("domaines cites sans lien     :", n_unlinked)
print()
for name, src in samples:
    print(" -", name)
    print("     ", src)
print()
if problems:
    print("PROBLEMES (%d) :" % len(problems))
    for p in problems[:40]:
        print("   *", p)
    sys.exit(1)
print("Aucun defaut detecte : toutes les URL affichees proviennent du registre.")
