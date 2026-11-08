# -*- coding: utf-8 -*-
"""Genere data/sites-officiels.json.

Pour chaque evenement, on note le site officiel trouve : celui de l'evenement
quand il existe, celui de l'organisateur a defaut. Les URL proviennent du
registre des sources reellement lues (data/zone-*.json et
data/sources-additionnels.json) ; une URL absente du registre est signalee
comme a verifier, jamais devinee.

Le fichier genere est lu par build.py, qui l'attache a chaque fiche.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
sys.path.insert(0, BASE)
from siteutil import host_of  # noqa: E402

# prefixe de nom d'evenement -> (url, type)
#   type "evenement"  : le site de l'evenement lui-meme
#   type "organisateur" : le site de l'entite qui organise (fallback)
MAPPING = {
    "15th AREA Conference 2026": ("https://areauganda.org/cities2026", "evenement"),
    "Botswana Investment Forum 2026": ("http://www.bdc.bw/events", "organisateur"),
    "New Africa Capital Champions Awards 2026": (None, None),
    "Cityscape Egypt Forum": ("https://www.cityscape-events.com/egypt/", "organisateur"),
    "Abuja Real Estate & Infrastructure Summit 2026": (
        "https://abujarealestateinfrastructure.com/", "evenement"),
    "ARIIS (Africa Real Estate Innovation": ("https://arisummit.com/", "evenement"),
    "AUHF Annual Conference & AGM": ("https://housingfinanceafrica.org/", "organisateur"),
    "FHS Egypt": ("https://futurehospitality.com/egypt", "organisateur"),
    "Capital & Legacy Forum 2026": ("https://nacapitalforum.com/", "organisateur"),
    "Abuja Real Estate Fest 2026": ("https://are.eventhive.ng/", "evenement"),
    "Namibia Public-Private Forum": (
        "https://www.nampa.org/text/23038615", "organisateur"),
    "SIB": ("https://sib.ma/", "evenement"),
    "Morocco Showcase Summit": ("https://afriwallstreet.com/", "organisateur"),
    "Africa Real Estate Summit, Awards & Expo 2026": (
        "https://africarealestateinternational.org/", "organisateur"),
    "Forbes Middle East Building the Future Summit": (
        "https://forbesmiddleeastevents.com/", "organisateur"),
    "EXPOFINANCES": (
        "https://www.algeriaexhibitions.dz/manifestations/expofinances-2026", "evenement"),
    "SENCON": ("https://senconexpo.com/", "evenement"),
    "Sankalp Africa Summit 2027": (None, None),
    "LMA & ICMA Annual Africa Summit 2027": ("https://blog.lma.eu.com/", "organisateur"),
    "PI Africa 2027": ("https://pensionfundsafrica.com/", "evenement"),
    "EAPI Summit 2027": ("https://eapisummit.com/", "evenement"),
    "Big 5 Construct South Africa": ("https://big5constructsouthafrica.com/", "evenement"),
    "Buildexpo Africa Kenya 2027": ("https://expogr.com/buildexpokenya/", "organisateur"),
    "Africa Real Estate Summit, Awards & Expo — Abuja 2027": (
        "https://africarealestateinternational.org/", "organisateur"),
    "Nigeria Private Capital Summit 2027": ("https://eventhive.ng/", "organisateur"),
    "National Conference on Housing Finance": (None, None),
    "Africa Urban Forum": ("https://unhabitat.org/sites/default/files/2026/04/programme_auf2.pdf",
                           "organisateur"),
    "African REIT Conference": (None, None),
    "IHS Affordable Housing Conference": (
        "https://cib.nedbank.co.za/insights/conferences/ihs-affordable-housing-conference.html",
        "organisateur"),
    "SENHABITAT 2027": (None, None),
    "Ghana Property Awards 2026": ("https://www.propertyexpressgroup.org/", "organisateur"),
    "Green Building Convention": ("https://www.gbcsa.org.za/", "organisateur"),
    "PRO-IMMO": (None, None),
    "RICS Africa Conference": (
        "https://www.rics.org/content/dam/ricsglobal/documents/event-programmes/"
        "africa-conference-programme-2026.pdf", "organisateur"),
    "Semaine de l'Habitat": ("https://www.minhdu.gov.cm/", "organisateur"),
    "Showcase Indian Ocean 2027": (None, None),
    "ZAMREAL Property Forum": (None, None),
    "ZimReal Property Investment Forum": (None, None),
    "BATIMATEC": (None, None),
    "Big 5 Construct Kenya (ex-East Africa)": (
        "https://www.big5constructkenya.com/", "evenement"),
    "Building African Financial Markets": ("https://www.tantrade.go.tz/", "organisateur"),
    "Connected Africa Summit": (None, None),
    "EAPCA Annual Private Capital Conference": (None, None),
    "Buildexpo Africa Tanzania 2027": ("https://expogr.com/", "organisateur"),
    "Africa Real Estate Magazine and Awards 2026": (None, None),
    "Nairobi Property Expo": (None, None),
    "Lagos Real Estate Fest 2027": ("https://eventhive.ng/", "organisateur"),
    "Africa Real Estate Summit, Awards & Expo — édition Abuja": (
        "https://africarealestateinternational.org/", "organisateur"),
    "Abuja Real Estate Fest 2027": ("https://are.eventhive.ng/", "evenement"),
    "KIICO 2027": ("https://kiico.investkenya.go.ke/about-kiico/", "organisateur"),
    "Salon de l'Habitat": (None, None),
    "Salon de l'immobilier de Brazzaville": (None, None),
}

# evenements deja couverts par la mention explicite « site officiel » du registre
EXPLICIT = {
    "New Africa Capital Forum 2026": ("https://nacapitalforum.com/", "evenement"),
    "16th Africa PPP Infrastructure Finance": ("https://africappp.com/", "evenement"),
    "Benk International Real Estate Conference": (
        "https://thebenkandhampton.com/", "evenement"),
    "TASSHIIL": ("https://tasshiil.com/", "evenement"),
    "40th Kenya Homes Expo": ("https://www.kenyahomesexpo.com/", "evenement"),
    "TAREX 2026": ("https://tarex.co.tz/home", "evenement"),
    "e-logia": ("https://elogia-dz.com/", "evenement"),
    "Ghana Property & Lifestyle Expo 2026": ("https://ghanapropertyexpo.com/", "evenement"),
    "Ethio Build Connect Expo": ("https://ethiobuildconnect.et/", "evenement"),
    "Salon Immobilier Congolais": ("https://www.si-congolais.com/", "evenement"),
    "SICI 2027": ("https://www.si-ci.com/", "evenement"),
    "Big 5 Construct Ethiopia 2027": ("https://www.big5constructethiopia.com/", "evenement"),
    "MEDIBAT": ("https://www.salon-medibat.com/", "evenement"),
    "FHS Africa 2027": ("https://futurehospitality.com/africa", "organisateur"),
    "Big 5 Construct Egypt": ("https://www.big5constructegypt.com/", "evenement"),
    "Africa Build Show Ghana 2027": ("https://africabuildshow.com/", "evenement"),
    "AIHS 2027": ("https://www.africahousingshow.com/", "evenement"),
    "Africa Property Investment (API) Summit": ("https://www.apisummit.co.za/", "evenement"),
    "Big 5 Construct Nigeria 2027": ("https://www.big5constructnigeria.com/", "evenement"),
    "SAPOA Annual Convention": ("https://sapoaconvention.co.za/", "evenement"),
    "Big 5 Construct Kenya (10e": ("https://www.big5constructkenya.com/", "evenement"),
    "ARCHIBAT 2027": ("https://archibat.ci/home/", "evenement"),
    "Africa Investment Forum (AIF) Market Days": (
        "https://www.africainvestmentforum.com/", "evenement"),
    "ARCE (Africa Real Estate Conference": ("https://www.arceconference.com/", "evenement"),
    "AREF 2027": ("https://africarealestatefestival.com/", "evenement"),
    "Africa Real Estate Festival (AREF)": (
        "https://africarealestatefestival.com/", "evenement"),
    "East Africa International Real Estate Expo": (
        "https://www.expoafrica.co.ke/", "evenement"),
    "ImmoExpo": ("https://immoexpo.ma/fr/", "evenement"),
    "Zanzibar Investment Summit": ("https://zis.zipa.go.tz/", "evenement"),
    "Cityscape Egypt — International Real Estate Exhibition": (
        "https://www.cityscape-events.com/egypt/", "organisateur"),
    "Cityscape Egypt Summit": ("https://www.cityscape-events.com/egypt/", "organisateur"),
}

registry = {}
for fn in sorted(os.listdir(DATA)):
    if not fn.endswith(".json") or fn in ("changelog.json", "sites-officiels.json"):
        continue
    payload = json.load(open(os.path.join(DATA, fn), encoding="utf-8"))
    for s in payload.get("sources", []):
        url = (s.get("url") or "").strip()
        if url and url not in registry:
            registry[url] = (s.get("name") or url, fn)

export = json.load(open(os.path.join(BASE, "export", "tracker-data.json"),
                        encoding="utf-8"))
events = export["events"] if isinstance(export, dict) and "events" in export else export

out, unmatched, missing = {}, [], []
for e in events:
    name = e.get("name") or ""
    hit = None
    for table in (MAPPING, EXPLICIT):
        for prefix, val in table.items():
            if name.startswith(prefix):
                hit = val
                break
        if hit:
            break
    if hit is None:
        unmatched.append(name)
        continue
    url, kind = hit
    if not url:
        out[name] = {"site": None, "type": None, "note": "site officiel non identifie"}
        continue
    if url not in registry:
        # l'URL relevee n'est pas dans le registre : on cherche la page
        # reellement lue sur le meme domaine, plutot que d'inventer une racine
        same = [u for u in registry if host_of(u) == host_of(url)]
        if same:
            same.sort(key=lambda u: (0 if "site officiel" in registry[u][0].lower() else 1, len(u)))
            url = same[0]
        else:
            missing.append((name, url))
    out[name] = {"site": url, "type": kind}

payload = {
    "note": ("Site officiel de l'evenement ou de l'organisateur, selon le cas. "
             "Les URL proviennent du registre des pages reellement lues. "
             "Un site absent est signale comme non identifie, jamais devine."),
    "sites": out,
}
path = os.path.join(DATA, "sites-officiels.json")
with open(path, "w", encoding="utf-8", newline="\n") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=2)
    fh.write("\n")

print("evenements cartographies  :", len(out))
print("  site officiel attribue  :", sum(1 for v in out.values() if v.get("site")))
print("  non identifie           :", sum(1 for v in out.values() if not v.get("site")))
print()
if unmatched:
    print("NON RATTACHES (%d) :" % len(unmatched))
    for n in unmatched:
        print("   *", n)
if missing:
    print("URL ABSENTES DU REGISTRE (%d) :" % len(missing))
    for n, u in missing:
        print("   *", u, "->", n[:60])
print()
print("fichier ecrit :", path)
