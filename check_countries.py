# -*- coding: utf-8 -*-
"""
Controle de coherence du perimetre geographique.

- Recupere les pays reellement couverts par l'agenda (export/tracker-data.json).
- Les compare a la liste canonique des 54 Etats africains.
- Verifie que chaque pays couvert figure bien dans la liste (pas de libelle hors nomenclature).
- Calcule le nombre exact de pays non couverts (a injecter dans le site).
- Verifie que la liste publiee dans PUBLICATION.md contient bien 54 pays.

Usage : python check_countries.py
"""
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Liste canonique des 54 Etats africains, dans l'ordre des regions onusiennes.
AFRICA_54 = [
    # Afrique du Nord (6)
    "Algérie", "Égypte", "Libye", "Maroc", "Soudan", "Tunisie",
    # Afrique de l'Ouest (16)
    "Bénin", "Burkina Faso", "Cap-Vert", "Côte d'Ivoire", "Gambie", "Ghana",
    "Guinée", "Guinée-Bissau", "Liberia", "Mali", "Mauritanie", "Niger",
    "Nigéria", "Sénégal", "Sierra Leone", "Togo",
    # Afrique centrale (9)
    "Angola", "Cameroun", "Tchad", "Congo", "Gabon", "Guinée équatoriale",
    "République centrafricaine", "République démocratique du Congo",
    "São Tomé-et-Príncipe",
    # Afrique de l'Est (18)
    "Burundi", "Comores", "Djibouti", "Érythrée", "Éthiopie", "Kenya",
    "Madagascar", "Malawi", "Maurice", "Mozambique", "Ouganda", "Rwanda",
    "Seychelles", "Somalie", "Soudan du Sud", "Tanzanie", "Zambie", "Zimbabwe",
    # Afrique australe (5)
    "Afrique du Sud", "Botswana", "Eswatini", "Lesotho", "Namibie",
]


def norm(text):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(text or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower().replace("'", " ").replace("-", " ")
    return re.sub(r"\s+", " ", t).strip()


CANON_MAP = {norm(c): c for c in AFRICA_54}

with open(os.path.join(BASE, "export", "tracker-data.json"), encoding="utf-8") as fh:
    data = json.load(fh)

events = data["events"] if isinstance(data, dict) and "events" in data else data
if isinstance(events, dict):
    events = list(events.values())

covered = {}
for e in events:
    c = (e.get("country") or "").strip()
    if not c or c in ("Non précisé", "À confirmer", "Inconnu"):
        continue
    covered.setdefault(c, 0)
    covered[c] += 1

print("=" * 68)
print("PERIMETRE GEOGRAPHIQUE")
print("=" * 68)
print("Liste canonique : %d pays" % len(AFRICA_54))
assert len(AFRICA_54) == 54, "la liste canonique doit contenir 54 pays"
print("Pays couverts par l'agenda : %d" % len(covered))
print("Pays non couverts : %d" % (54 - len(covered)))

unknown = []
for c in sorted(covered):
    if norm(c) in CANON_MAP:
        print("  OK   %-34s %2d evenement(s)" % (CANON_MAP[norm(c)], covered[c]))
    else:
        unknown.append(c)
        print("  HORS  %-34s %2d evenement(s)  <-- absent de la nomenclature" % (c, covered[c]))

if unknown:
    print()
    print("!! %d libelle(s) hors nomenclature :" % len(unknown))
    for u in unknown:
        print("   -", u)

# ---- controle de la liste publiee dans PUBLICATION.md ----------------------
pub = os.path.join(BASE, "PUBLICATION.md")
if os.path.exists(pub):
    with open(pub, encoding="utf-8") as fh:
        text = fh.read()
    block = re.search(
        r"Les 54 pays du continent.*?(?=\n---|\n##\s)", text, re.S)
    if block:
        # les pays sont repartis sur plusieurs lignes et certains noms sont
        # coupes en fin de ligne (« République\ncentrafricaine ») : on recolle
        # les lignes qui portent le separateur, puis on decoupe dessus.
        lines = []
        for l in block.group(0).splitlines():
            if "·" not in l:
                continue
            l = l.strip()
            # une ligne qui demarre par un nom de region ouvre une nouvelle
            # serie : il lui faut un separateur, sinon elle se colle au
            # dernier pays de la ligne precedente.
            if l.startswith("Afrique "):
                l = "· " + l
            lines.append(l)
        raw = " ".join(lines)
        regions = {"afrique du nord", "afrique de l ouest", "afrique centrale",
                   "afrique de l est", "afrique australe"}
        names = set()
        for part in raw.split("·"):
            part = part.strip().strip(".,")
            if not part:
                continue
            key = norm(part)
            if key in regions or key.startswith("les 54 pays"):
                continue
            names.add(key)
        missing = [c for c in AFRICA_54 if norm(c) not in names]
        extra = [n for n in names if n not in CANON_MAP]
        print()
        print("PUBLICATION.md : %d pays lists" % len(names))
        if missing:
            print("  MANQUANTS : %s" % ", ".join(missing))
        if extra:
            print("  EN TROP   : %s" % ", ".join(sorted(extra)))
        if not missing and not extra:
            print("  conforme")

print()
print("A injecter dans make_site.py : pays non couverts = %d" % (54 - len(covered)))
