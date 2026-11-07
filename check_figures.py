# -*- coding: utf-8 -*-
"""Chiffres exacts pour la documentation (README / PUBLICATION)."""
import io
import json
import os
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

with open(os.path.join(BASE, "export", "tracker-data.json"), encoding="utf-8") as fh:
    events = json.load(fh)["events"]

cats = Counter(e.get("category") for e in events)
stats = Counter(e.get("status") for e in events)
zones = Counter(e.get("zone") for e in events)
pays = Counter(e.get("country") for e in events if e.get("country"))
scores = Counter(e.get("score") for e in events)

LABEL = {
    "flagship_continental": "Flagship continental",
    "national_anchor": "Ancre nationale",
    "capital_markets": "Marchés de capitaux",
    "adjacent_construction": "Adjacent construction",
    "watchlist": "Watchlist (date non fixée)",
}
STATUS = {"confirmed": "Date confirmée", "probable": "Date probable (sources divergentes)",
          "to_confirm": "Date à confirmer"}

print("CATEGORIES")
for k in ["flagship_continental", "national_anchor", "capital_markets",
          "adjacent_construction", "watchlist"]:
    print("  %-28s %d" % (LABEL[k], cats.get(k, 0)))
print()
print("STATUTS")
for k in ["confirmed", "probable", "to_confirm"]:
    print("  %-36s %d" % (STATUS[k], stats.get(k, 0)))
print("  %-36s %d" % ("Avec contradiction entre sources",
                       sum(1 for e in events if e.get("has_conflict"))))
print()
print("PAYS (%d distincts)" % len(pays))
print("  " + ", ".join("%s %d" % (c, n) for c, n in pays.most_common()))
print()
print("ZONES")
for z, n in zones.most_common():
    print("  %-36s %d" % (z, n))
print()
print("SCORES : %s" % dict(sorted(scores.items())))
print("datedes : %d" % len([e for e in events if e.get("start")]))
print("avec lieu : %d" % len([e for e in events if e.get("venue")]))
print("avec source_url : %d" % len([e for e in events if e.get("source_url")]))
print("avec ticket_url : %d" % len([e for e in events if e.get("ticket_url")]))
print()
print("SCORE 5 ET DATE FIXEE")
for e in sorted(events, key=lambda x: (x.get("name") or "")):
    if e.get("score") == 5 and e.get("start"):
        print("  %-62s %s %s" % (e.get("name")[:60], e.get("display_date"),
                                  e.get("country")))
print()
# densite par trimestre
from collections import defaultdict
q = defaultdict(int)
for e in events:
    if not e.get("start"):
        continue
    y, m = int(e["start"][:4]), int(e["start"][5:7])
    q["T%d %d" % ((m - 1) // 3 + 1, y)] += 1
print("DENSITE PAR TRIMESTRE : %s" % dict(sorted(q.items())))
