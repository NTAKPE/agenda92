# -*- coding: utf-8 -*-
"""Helpers partages entre le generateur de site et les scripts de controle.

Isoles ici pour que les scripts de verification puissent les importer sans
executer le generateur complet.
"""
import re

DOMAIN_RE = re.compile(r"\b((?:[a-z0-9][a-z0-9-]*\.)+[a-z]{2,})\b", re.I)

# Jetons qui ressemblent a un domaine sans en etre un.
NOT_A_DOMAIN = {
    "e.g", "i.e", "etc", "no", "vs", "mr", "mrs", "mme", "mlle", "dr", "prof",
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "sept",
    "oct", "nov", "dec", "st", "rc", "art", "chap", "p.ex",
}


def host_of(url):
    """Hote d'une URL, sans 'www.' — utilise pour nommer une source en clair."""
    if not url:
        return ""
    host = re.sub(r"^https?://", "", str(url)).split("/")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def cited_domains(event, exclude=()):
    """Domaines cites dans le texte d'arbitrage (conflits, signaux et lacunes).

    Aucun lien n'est fabrique : le domaine est affiche tel qu'il est ecrit dans
    la note de verification. C'est la lecture de la source qui reste le seul
    moyen de controler une information.
    """
    text = " ".join([event.get("conflicts") or "", event.get("notes") or ""])
    out = []
    for m in DOMAIN_RE.finditer(text):
        d = m.group(1).lower().strip(".")
        if d.startswith("www."):
            d = d[4:]
        if d in NOT_A_DOMAIN or "." not in d:
            continue
        if d in exclude or d in out:
            continue
        out.append(d)
    return out
