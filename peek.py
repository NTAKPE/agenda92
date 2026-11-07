# -*- coding: utf-8 -*-
"""Inspecte une fiche dans export/tracker-data.json (diagnostic)."""
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

needle = sys.argv[1] if len(sys.argv) > 1 else "Abuja Real Estate Fest 2026"

with open(os.path.join(BASE, "export", "tracker-data.json"), encoding="utf-8") as fh:
    data = json.load(fh)
events = data["events"]

hits = [e for e in events if needle.lower() in e.get("name", "").lower()]
print("Correspondances pour %r : %d" % (needle, len(hits)))
for e in hits:
    print("=" * 70)
    print("nom      :", e.get("name"))
    print("date     :", e.get("start"), "| statut:", e.get("status"),
          "| has_conflict:", e.get("has_conflict"))
    print("source   :", e.get("source_name"), "|", e.get("source_url"))
    conf = e.get("conflicts")
    print("conflicts type=%s len=%s" % (type(conf).__name__,
                                        len(conf) if hasattr(conf, "__len__") else "n/a"))
    print("conflicts contenu :", json.dumps(conf, ensure_ascii=False)[:700])
    print("notes    :", json.dumps(e.get("notes"), ensure_ascii=False)[:300])
