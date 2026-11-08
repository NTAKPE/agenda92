# -*- coding: utf-8 -*-
"""Controle de conformite du fichier iCalendar (RFC 5545)."""
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ICS = os.path.join(BASE, "export", "agenda-immobilier-afrique.ics")

raw = open(ICS, "rb").read()
problems = []

# 1. CRLF partout
if b"\r\n" not in raw:
    problems.append("aucun CRLF")
if re.search(rb"(?<!\r)\n", raw):
    problems.append("LF isole trouve")
if b"\r\r" in raw:
    problems.append("CR isole trouve")

text = raw.decode("utf-8")
lines = text.split("\r\n")

# 2. lignes de 75 octets maximum
for i, line in enumerate(lines, 1):
    n = len(line.encode("utf-8"))
    if n > 75:
        problems.append("ligne %d : %d octets (> 75)" % (i, n))

# 3. structure
if lines[0] != "BEGIN:VCALENDAR" or lines[-2] != "END:VCALENDAR":
    problems.append("enveloppe VCALENDAR incorrecte")

events = [l for l in lines if l == "BEGIN:VEVENT"]
uids = [l for l in lines if l.startswith("UID:")]
if len(events) != len(uids):
    problems.append("%d VEVENT pour %d UID" % (len(events), len(uids)))
if len(set(uids)) != len(uids):
    dup = [u for u in set(uids) if uids.count(u) > 1]
    problems.append("UID dupliques : %s" % dup[:3])

# 4. champs obligatoires
for i, line in enumerate(lines):
    if line == "BEGIN:VEVENT":
        block = lines[i:i + 20]
        for field in ("UID:", "DTSTAMP:", "DTSTART", "SUMMARY:"):
            if not any(b.startswith(field) for b in block):
                problems.append("VEVENT sans %s (ligne %d)" % (field, i + 1))
                break

# 5. sequence d'echappement : un seul point-virgule initial
for i, line in enumerate(lines, 1):
    if line.startswith(("DESCRIPTION:", "SUMMARY:", "LOCATION:")):
        body = line.split(":", 1)[1]
        if body.startswith(";"):
            problems.append("point-virgule initial non echappe (ligne %d)" % i)

print("fichier            :", ICS)
print("taille             :", len(raw), "octets")
print("lignes             :", len(lines))
print("VEVENT             :", len(events))
print("UID uniques        :", len(set(uids)))
print("plus longue ligne  :", max(len(l.encode('utf-8')) for l in lines), "octets")
print()
if problems:
    print("PROBLEMES (%d) :" % len(problems))
    for p in problems[:20]:
        print("   *", p)
    sys.exit(1)
print("Conforme RFC 5545.")
