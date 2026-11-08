# -*- coding: utf-8 -*-
"""Affiche une page du site en texte brut, pour relire la mise en page."""
import io
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1] if len(sys.argv) > 1 else "methodologie.html"
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 3000

path = os.path.join(BASE, "site", name)
html = io.open(path, encoding="utf-8").read()
m = re.search(r"<main.*?</main>", html, re.S)
body = m.group(0) if m else html
body = re.sub(r"<li>", "\n- ", body)
body = re.sub(r"<(tr|h1|h2|h3|p|summary|details|table)>", "\n", body)
body = re.sub(r"<[^>]+>", " ", body)
body = re.sub(r"[ \t]{2,}", " ", body)
lines = [l.strip() for l in body.split("\n") if l.strip()]
out = "\n".join(lines)[:limit]
sys.stdout.buffer.write(out.encode("utf-8", "replace"))
