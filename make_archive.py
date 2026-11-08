# -*- coding: utf-8 -*-
"""
Archive le projet en zip, en excluant les dossiers de travail git (.deploy-*).

Usage : python make_archive.py [chemin_du_zip]
"""
import io
import os
import sys
import zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE)
NAME = os.path.basename(BASE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

target = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    PARENT, NAME + ".zip")

EXCLUDE_DIRS = {".deploy-source", ".deploy-pages", "__pycache__", ".git"}
EXCLUDE_FILES = {"peek.py", "peek_history.py"}

if os.path.exists(target):
    os.remove(target)

n_files = 0
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if fn in EXCLUDE_FILES:
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, PARENT).replace(os.sep, "/")
            z.write(full, rel)
            n_files += 1

size = os.path.getsize(target)
print("Archive : %s" % target)
print("  %d fichiers, %.2f Mo" % (n_files, size / (1024 * 1024)))
with zipfile.ZipFile(target) as z:
    bad = z.testzip()
    print("  integrite : %s" % ("OK" if bad is None else "CORROMPU: %s" % bad))
    names = z.namelist()
    for probe in ("%s/site/index.html" % NAME,
                  "%s/site/sitemap.xml" % NAME,
                  "%s/site/assets/og/abuja-real-estate-fest-2026.png" % NAME,
                  "%s/deploy_github.py" % NAME,
                  "%s/DEPLOIEMENT.md" % NAME,
                  "%s/README.md" % NAME,
                  "%s/PUBLICATION.md" % NAME):
        print("  %-62s %s" % (probe, "present" if probe in names else "ABSENT"))
