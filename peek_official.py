# -*- coding: utf-8 -*-
"""Candidats « site officiel » par evenement.

Pour chaque evenement, liste les sources du registre disponibles (source
principale + sources citees dans l'arbitrage) et signale :
  - « site officiel » quand le nom du registre le dit explicitement ;
  - « candidat » quand le domaine contient un mot distinctif du nom de
    l'evenement ou de l'organisateur.

Le but est de produire une liste lisible a valider, pas de deviner.
"""
import json
import os
import re
import sys
import unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from siteutil import host_of  # noqa: E402

DATA = os.path.join(BASE, "data")
EXPORT = os.path.join(BASE, "export")

# mots trop generiques pour prouver qu'un domaine appartient a l'organisateur
GENERIC = {
    "africa", "african", "capital", "forum", "summit", "conference", "real",
    "estate", "property", "expo", "exhibition", "trade", "show", "market",
    "investment", "invest", "annual", "international", "group", "event",
    "events", "market", "finance", "financing", "housing", "land", "city",
    "cities", "series", "edition", "business", "development", "project",
    "agency", "association", "institute", "center", "centre", "office",
    "news", "media", "daily", "times", "today", "post", "blog",
}


def tokens(text):
    s = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return {w for w in re.split(r"[^a-z0-9]+", s) if len(w) >= 4 and w not in GENERIC}


def host_flat(host):
    return re.sub(r"[^a-z0-9]", "", host.lower())


registry = {}
for fn in sorted(f for f in os.listdir(DATA) if f.endswith(".json") and "changelog" not in f):
    payload = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    for s in payload.get("sources", []):
        url = (s.get("url") or "").strip()
        if url and url not in registry:
            registry[url] = {"name": (s.get("name") or url).strip(),
                             "accessed": s.get("accessed") or "", "file": fn}

raw = json.load(open(os.path.join(EXPORT, "tracker-data.json"), encoding="utf-8"))
events = raw["events"] if isinstance(raw, dict) and "events" in raw else raw

rows = []
for e in events:
    name = e.get("name") or ""
    org = e.get("organizer") or ""
    nt, ot = tokens(name), tokens(org)
    cands = []
    if e.get("source_url"):
        cands.append((e["source_url"], e.get("source_name") or "", "principale"))
    for s in e.get("cited_sources") or []:
        cands.append((s["url"], s.get("name") or "", "citee"))
    if e.get("ticket_url"):
        cands.append((e["ticket_url"], "", "billetterie"))

    official, probable = [], []
    for url, sname, kind in cands:
        if url not in registry:
            continue
        rname = registry[url]["name"]
        label = sname or rname
        low = label.lower()
        h = host_of(url)
        hf = host_flat(h)
        if "site officiel" in low or "site officiel" in rname.lower():
            official.append((url, label, kind, rname))
            continue
        hit = set()
        for w in (nt | ot):
            if w in hf:
                hit.add(w)
        hit = {w for w in hit if w not in GENERIC}
        if hit:
            probable.append((url, label, kind, sorted(hit)))
    rows.append((name, org, official, probable, cands))

print("evenements analyses :", len(rows))
print("avec source « site officiel » explicite :",
      sum(1 for r in rows if r[2]))
print("avec candidat par nom (a valider)      :",
      sum(1 for r in rows if not r[2] and r[3]))
print("sans candidat                          :",
      sum(1 for r in rows if not r[2] and not r[3]))
print()
for name, org, official, probable, cands in rows:
    if official:
        u, lab, kind, rname = official[0]
        print("[OFFICIEL] %-56s %s" % (name[:56], u))
    elif probable:
        u, lab, kind, hit = probable[0]
        print("[candidat] %-56s %s  (%s)" % (name[:56], u, ",".join(hit)))
    else:
        brief = " | ".join("%s [%s]" % (host_of(u), k) for u, l, k in cands)
        print("[AUCUN   ] %-56s %s" % (name[:56], brief[:140]))
