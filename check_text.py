# -*- coding: utf-8 -*-
"""Balaye les fichiers de donnees pour y detecter des artefacts de texte.

Un reste de generation automatique ("deserialize", "[object Object]", "None"...)
dans une phrase destinee a etre lue par un humain passe inaperçu. On le
signale plutot que de le publier tel quel.
"""
import glob
import io
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))

# Jetons techniques : sensibles a la casse, pour ne pas confondre « NaN » avec
# le sigle d'une agence de presse.
TECH = re.compile(r"(?<![\w.])NaN(?![\w])|(?<![\w])None(?![\w])|"
                  r"(?<![\w])undefined(?![\w])|(?<![\w])Infinity(?![\w])")
# Artefacts de generation, insensibles a la casse.
PATTERNS = re.compile(
    r"(deserialize|\[object Object\]|\bTODO\b|\bFIXME\b|\bLorem ipsum\b|<<|>>)",
    re.I)

problems = []
for fn in sorted(glob.glob(os.path.join(BASE, "data", "*.json"))):
    if fn.endswith("sites-officiels.json"):
        continue
    raw = io.open(fn, encoding="utf-8").read()
    payload = json.loads(raw)

    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, path + "." + str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, path + "[%d]" % i)
        elif isinstance(node, str):
            if PATTERNS.search(node) or TECH.search(node):
                problems.append("%s %s : %s" % (os.path.basename(fn), path, node[:150]))

    walk(payload, "")

print("fichiers analyses :", len(glob.glob(os.path.join(BASE, "data", "*.json"))))
print("artefacts detectes :", len(problems))
for p in problems:
    print("   *", p)
sys.exit(1 if problems else 0)
