# -*- coding: utf-8 -*-
"""Controle d'integrite des liens internes du site statique genere."""
import glob
import os
import re
import sys
from urllib.parse import unquote

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "site")

if not os.path.isdir(SITE):
    print("site/ absent : lance make_site.py d'abord.", file=sys.stderr)
    raise SystemExit(1)

files = []
for root, dirs, names in os.walk(SITE):
    for n in names:
        p = os.path.join(root, n)
        files.append(os.path.relpath(p, SITE).replace(os.sep, "/"))
fileset = set(files)

html_files = [f for f in files if f.endswith(".html")]
href_re = re.compile(r'(?:href|src)=["\']([^"\'#?]+)')

# Base publique du site, lue dans le canonical de l'accueil. Les URL
# absolues pointeant vers cette base sont verifiees comme les liens
# relatifs : le controle ne doit pas dependre du mode de build.
SITE_BASE = ""
try:
    with open(os.path.join(SITE, "index.html"), encoding="utf-8") as fh:
        m = re.search(r'<link rel="canonical" href="(https?://[^/]+/[^"]*)"',
                      fh.read())
    if m:
        SITE_BASE = m.group(1).rsplit("/", 1)[0] + "/"
except OSError:
    pass


def internal(target):
    """Renvoie (chemin, depuis_racine), ou (None, False) si le lien est externe.

    Une URL absolue sur la base du site est deja relative a la racine :
    elle ne doit pas etre resolue depuis le sous-repertoire de la page.
    """
    if SITE_BASE and target.startswith(SITE_BASE):
        return target[len(SITE_BASE):], True
    if target.startswith(("http://", "https://", "mailto:", "data:", "javascript:", "//")):
        return None, False
    return target, False


def resolve(base, target, rooted):
    if rooted:
        return os.path.normpath(target).replace(os.sep, "/")
    return os.path.normpath(os.path.join(base, target)).replace(os.sep, "/")


broken = {}
total = 0
for f in html_files:
    with open(os.path.join(SITE, f), encoding="utf-8") as fh:
        content = fh.read()
    base = os.path.dirname(f)
    for m in href_re.findall(content):
        target, rooted = internal(m)
        if target is None:
            continue
        target = unquote(target)
        if not target:
            continue
        total += 1
        p = resolve(base, target, rooted)
        if p not in fileset:
            broken.setdefault(f, []).append(m)

# pages orphelines : aucune page ne pointe vers elles
referenced = set()
for f in html_files:
    with open(os.path.join(SITE, f), encoding="utf-8") as fh:
        content = fh.read()
    base = os.path.dirname(f)
    for m in href_re.findall(content):
        target, rooted = internal(m)
        if target is None:
            continue
        referenced.add(resolve(base, unquote(target), rooted))

orphans = [f for f in html_files if f not in referenced]

print("fichiers html          : %d" % len(html_files))
print("base publique         : %s" % (SITE_BASE or "(relative, build local)"))
print("liens internes verifies: %d" % total)
print("pages avec liens casses: %d" % len(broken))
for f, lst in list(broken.items())[:15]:
    print("   %s -> %s" % (f, lst[:5]))
print("pages orphelines       : %d" % len(orphans))
for f in orphans[:15]:
    print("   %s" % f)

raise SystemExit(1 if broken else 0)
