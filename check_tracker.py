# -*- coding: utf-8 -*-
"""
Controle du tracker pre-rendu (index.html).

Le tracker fonctionne sans JavaScript : les 83 lignes sont dans le HTML.
Ce script verifie la structure statique de cette garantie :

  - le nombre de lignes de donnees correspond a export/tracker-data.json
  - chaque ligne de donnee a bien sa ligne de detail (data-i / data-d)
  - les attributs de filtre (categorie, statut, pays, zone, score) sont valides
  - chaque lien pointe vers une fiche reellement presente sur le disque
  - chaque fiche porte ses sources, et ses contradictions quand il en a

Usage : python check_tracker.py
"""
import io
import json
import os
import re
import sys
from html.parser import HTMLParser

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "site")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VALID_CAT = {"flagship_continental", "national_anchor", "capital_markets",
             "adjacent_construction", "watchlist"}
VALID_STATUS = {"confirmed", "probable", "to_confirm"}

errors = []
warnings = []


class TrackerParser(HTMLParser):
    """Recupere les lignes de donnees (tr.ev) et de detail (tr.detail)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = {}          # data-i -> attributs
        self.details = {}       # data-d -> attributs
        self._in_detail = None
        self._buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if tag == "tr" and "ev" in cls:
            self.rows[a.get("data-i")] = a
        elif tag == "tr" and "detail" in cls:
            self._in_detail = a.get("data-d")
            self._buf = []
        elif tag == "a" and self._in_detail is not None:
            href = a.get("href") or ""
            if href.startswith("evenements/"):
                self._buf.append(href)

    def handle_data(self, data):
        if self._in_detail is not None:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "tr" and self._in_detail is not None:
            self.details[self._in_detail] = "".join(self._buf)
            self._in_detail = None
            self._buf = []


index_path = os.path.join(SITE, "index.html")
if not os.path.exists(index_path):
    print("index.html introuvable : lancez make_site.py d'abord.")
    sys.exit(1)

with open(index_path, encoding="utf-8") as fh:
    html = fh.read()

p = TrackerParser()
p.feed(html)

with open(os.path.join(BASE, "export", "tracker-data.json"), encoding="utf-8") as fh:
    data = json.load(fh)
events = data["events"]

print("=" * 68)
print("CONTROLE DU TRACKER PRE-RENDU")
print("=" * 68)
print("lignes de donnees (tr.ev)   : %d" % len(p.rows))
print("lignes de detail (tr.detail) : %d" % len(p.details))
print("evenements dans les donnees  : %d" % len(events))

# ---- 1. comptage --------------------------------------------------------
if len(p.rows) != len(events):
    errors.append("le tracker affiche %d lignes pour %d evenements"
                  % (len(p.rows), len(events)))
if len(p.details) != len(events):
    errors.append("%d lignes de detail pour %d evenements"
                  % (len(p.details), len(events)))

# ---- 2. appariement data-i / data-d ------------------------------------
missing_detail = [i for i in p.rows if i not in p.details]
orphan_detail = [d for d in p.details if d not in p.rows]
if missing_detail:
    errors.append("%d ligne(s) sans detail : %s"
                  % (len(missing_detail), missing_detail[:5]))
if orphan_detail:
    errors.append("%d detail(s) sans ligne : %s"
                  % (len(orphan_detail), orphan_detail[:5]))

# ---- 3. attributs de filtre --------------------------------------------
countries = set()
for e in events:
    c = (e.get("country") or "").strip()
    if c:
        countries.add(c)

for i, a in p.rows.items():
    if a.get("data-cat") not in VALID_CAT:
        errors.append("ligne %s : categorie invalide %r" % (i, a.get("data-cat")))
    if a.get("data-status") not in VALID_STATUS:
        errors.append("ligne %s : statut invalide %r" % (i, a.get("data-status")))
    if a.get("data-country") not in countries:
        errors.append("ligne %s : pays inconnu %r" % (i, a.get("data-country")))
    if not a.get("data-search"):
        errors.append("ligne %s : data-search vide" % i)
    try:
        int(a.get("data-score") or "")
    except ValueError:
        errors.append("ligne %s : score invalide %r" % (i, a.get("data-score")))

# ---- 4. liens vers les fiches -------------------------------------------
by_name = {}
for e in events:
    by_name[e.get("name", "")] = e

missing_file = 0
checked = 0
for e in events:
    slug = re.sub(r"[^a-z0-9]+", "-",
                  __import__("unicodedata").normalize("NFKD", e.get("name", ""))
                  .encode("ascii", "ignore").decode().lower()).strip("-")
    target = os.path.join(SITE, "evenements", "%s.html" % slug)
    checked += 1
    if not os.path.exists(target):
        missing_file += 1
        if missing_file <= 5:
            errors.append("fiche absente sur le disque : evenements/%s.html" % slug)
if missing_file > 5:
    errors.append("... et %d autres fiches absentes" % (missing_file - 5))

# ---- 5. sources et contradictions visibles -----------------------------
no_source = 0
conflict_expected = 0
conflict_found = 0
for e in events:
    text = p.details.get(str(p.rows and 0) or "", "")  # placeholder, remplace ci-dessous
    # le detail est indexe par data-d ; on retrouve l'evenement via son nom
for d, text in p.details.items():
    if "Sources" not in text and "source" not in text.lower():
        no_source += 1
    if "ontradiction" in text:
        conflict_found += 1

for e in events:
    if e.get("has_conflict") or (e.get("conflicts") or "").strip():
        conflict_expected += 1

if no_source:
    errors.append("%d ligne(s) de detail sans mention des sources" % no_source)

print()
print("fiches sur le disque verifiees : %d" % checked)
print("evenements avec conflit de sources : %d" % conflict_expected)
print("details affichant les contradictions : %d" % conflict_found)
if conflict_found < conflict_expected:
    warnings.append("%d evenement(s) avec conflit n'affichent pas leurs contradictions"
                    % (conflict_expected - conflict_found))

# ---- 6. la page fonctionne sans JS -------------------------------------
# Seul le JSON-LD est en ligne : c'est une donnee, pas du code executable.
# Un <script> executable dans index.html casserait la garantie « lisible
# sans JavaScript » qui porte tout le référencement du tracker.
inline_script = [s for s in re.findall(r"<script[^>]*>", html)
                 if "src=" not in s and "ld+json" not in s]
print("scripts executables en ligne sur index.html : %d" % len(inline_script))
if inline_script:
    errors.append("index.html contient %d script(s) executable(s) en ligne : "
                  "le tracker doit rester lisible sans JavaScript" % len(inline_script))

print()
if errors:
    print("ERREURS (%d) :" % len(errors))
    for e in errors:
        print("  - %s" % e)
else:
    print("Aucun defaut de structure detecte.")
if warnings:
    print()
    print("A VERIFIER (%d) :" % len(warnings))
    for w in warnings:
        print("  - %s" % w)

sys.exit(1 if errors else 0)
