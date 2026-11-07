# -*- coding: utf-8 -*-
"""Recalcule les chiffres du journal (changelog) depuis les donnees reelles."""
import io
import json
import os
import sys
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

AFRICA_54 = [
    "Algérie", "Égypte", "Libye", "Maroc", "Soudan", "Tunisie",
    "Bénin", "Burkina Faso", "Cap-Vert", "Côte d'Ivoire", "Gambie", "Ghana",
    "Guinée", "Guinée-Bissau", "Liberia", "Mali", "Mauritanie", "Niger",
    "Nigéria", "Sénégal", "Sierra Leone", "Togo",
    "Angola", "Cameroun", "Tchad", "Congo", "Gabon", "Guinée équatoriale",
    "République centrafricaine", "République démocratique du Congo",
    "São Tomé-et-Príncipe",
    "Burundi", "Comores", "Djibouti", "Érythrée", "Éthiopie", "Kenya",
    "Madagascar", "Malawi", "Maurice", "Mozambique", "Ouganda", "Rwanda",
    "Seychelles", "Somalie", "Soudan du Sud", "Tanzanie", "Zambie", "Zimbabwe",
    "Afrique du Sud", "Botswana", "Eswatini", "Lesotho", "Namibie",
]


def norm(t):
    t = unicodedata.normalize("NFKD", str(t or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower().replace("'", " ").replace("-", " ").strip()


# ---- 1. fiches sources et rejets dans data/zone-*.json -------------------
DATA = os.path.join(BASE, "data")
fiches = 0
rejets = 0
negatifs = 0
for fn in sorted(os.listdir(DATA)):
    if not (fn.startswith("zone-") and fn.endswith(".json")):
        continue
    with open(os.path.join(DATA, fn), encoding="utf-8") as fh:
        z = json.load(fh)
    fiches += len(z.get("events", []))
    rejets += len(z.get("rejected", []))
    negatifs += len(z.get("negative_findings", []))
    print("%-26s events=%-4d rejected=%-4d negative=%d"
          % (fn, len(z.get("events", [])), len(z.get("rejected", [])),
             len(z.get("negative_findings", []))))

print()
print("fiches sources brutes : %d" % fiches)
print("rejets documentes     : %d" % rejets)
print("constats negatifs    : %d" % negatifs)

# ---- 2. retenus et pays couverts ----------------------------------------
with open(os.path.join(BASE, "export", "tracker-data.json"), encoding="utf-8") as fh:
    events = json.load(fh)["events"]

retenus = len(events)
pays_couverts = set()
for e in events:
    c = (e.get("country") or "").strip()
    if c and c != "Non précisé":
        pays_couverts.add(norm(c))

canon = {norm(c): c for c in AFRICA_54}
non_couverts = [canon[k] for k in canon if k not in pays_couverts]

print()
print("evenements retenus    : %d" % retenus)
print("pays couverts         : %d" % len(pays_couverts))
print("pays non couverts     : %d" % len(non_couverts))
print("liste                 : %s" % ", ".join(non_couverts))

# ---- 3. repartition des statuts -----------------------------------------
from collections import Counter
st = Counter(e.get("status") for e in events)
conf = sum(1 for e in events if e.get("has_conflict"))
print()
print("statuts   : %s" % dict(st))
print("avec conflit de sources : %d" % conf)
