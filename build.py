# -*- coding: utf-8 -*-
"""
Consolidation de l'agenda des evenements immobiliers en Afrique.

Lit data/zone-*.json, dedoublonne, arbitre les conflits, puis produit :
  export/agenda-immobilier-afrique.csv   (UTF-8 BOM, separateur ';' -> Excel FR)
  export/agenda-immobilier-afrique.ics   (export calendrier)
  export/tracker-data.json               (donnees pour le tracker HTML)
"""
import csv
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "export")
os.makedirs(OUT, exist_ok=True)

MONTHS = {
    "01": "janv.", "02": "fevr.", "03": "mars", "04": "avr.", "05": "mai",
    "06": "juin", "07": "juil.", "08": "aout", "09": "sept.", "10": "oct.",
    "11": "nov.", "12": "dec.",
}

CATEGORY_LABEL = {
    "flagship_continental": "Flagship continental",
    "national_anchor": "Ancre nationale",
    "capital_markets": "Marches de capitaux",
    "adjacent_construction": "Adjacent construction",
    "watchlist": "Watchlist",
}

STATUS_LABEL = {
    "confirmed": "Confirme",
    "probable": "Probable",
    "to_confirm": "A confirmer",
}

# --------------------------------------------------------------------------
# denominations de pays : les sources Fargo selon des langues et des formes
# variables ("Algeria" / "Algérie", "South Africa" / "Afrique du Sud").
# On canonise pour que les filtres du tracker fonctionnent.
# --------------------------------------------------------------------------
COUNTRY_CANON = {
    "algeria": "Algérie", "alger": "Algérie", "algerie": "Algérie", "dz": "Algérie",
    "egypt": "Égypte", "egyptian": "Égypte", "egypte": "Égypte",
    "morocco": "Maroc", "maroc": "Maroc", "moroccan": "Maroc",
    "tunisia": "Tunisie", "tunisie": "Tunisie", "tunisian": "Tunisie",
    "senegal": "Sénégal", "senegalais": "Sénégal",
    "south africa": "Afrique du Sud", "afrique du sud": "Afrique du Sud",
    "sud afrique": "Afrique du Sud", "africa du sud": "Afrique du Sud",
    "tanzania": "Tanzanie", "tanzanien": "Tanzanie",
    "uganda": "Ouganda", "ouganda": "Ouganda",
    "kenya": "Kenya", "kenyan": "Kenya",
    "nigeria": "Nigeria", "nigeria": "Nigeria", "nigerian": "Nigeria",
    "ghana": "Ghana", "ghanaian": "Ghana",
    "cameroon": "Cameroun", "cameroun": "Cameroun", "cameroonian": "Cameroun",
    "cote d'ivoire": "Côte d'Ivoire", "côte d'ivoire": "Côte d'Ivoire",
    "ivory coast": "Côte d'Ivoire", "cote divoire": "Côte d'Ivoire",
    "dr congo": "République démocratique du Congo",
    "drc": "République démocratique du Congo",
    "democratic republic of the congo": "République démocratique du Congo",
    "republique democratique du congo": "République démocratique du Congo",
    "congo kinshasa": "République démocratique du Congo",
    "republic of the congo": "République du Congo",
    "republique du congo": "République du Congo",
    "congo brazzaville": "République du Congo",
    "congo": "Congo",
    "ethiopia": "Éthiopie", "ethiopien": "Éthiopie",
    "botswana": "Botswana",
    "namibia": "Namibie", "namibie": "Namibie",
    "zambia": "Zambie", "zambie": "Zambie",
    "zimbabwe": "Zimbabwe", "zimbabwe": "Zimbabwe",
    "malawi": "Malawi", "malawian": "Malawi",
    "mozambique": "Mozambique", "mozambicain": "Mozambique",
    "angola": "Angola",
    "gabon": "Gabon",
    "equatorial guinea": "Guinée équatoriale", "guinee equatoriale": "Guinée équatoriale",
    "mauritius": "Maurice", "ile maurice": "Maurice",
    "seychelles": "Seychelles",
    "rwanda": "Rwanda",
    "burundi": "Burundi",
    "eritrea": "Érythrée",
    "somalia": "Somalie",
    "djibouti": "Djibouti",
    "comoros": "Comores",
    "madagascar": "Madagascar",
    "togo": "Togo",
    "benin": "Bénin", "bénin": "Bénin",
    "burkina faso": "Burkina Faso",
    "mali": "Mali",
    "niger": "Niger",
    "guinea": "Guinée", "guinée": "Guinée",
    "guinea bissau": "Guinée-Bissau",
    "sierra leone": "Sierra Leone",
    "liberia": "Libéria", "libéria": "Libéria",
    "gambia": "Gambie",
    "cape verde": "Cap-Vert", "cap vert": "Cap-Vert",
    "sao tome and principe": "São Tomé-et-Príncipe",
    "central african republic": "République centrafricaine",
    "lesotho": "Lesotho",
    "eswatini": "Eswatini", "swaziland": "Eswatini",
    "sudan": "Soudan", "soudan": "Soudan",
    "south sudan": "Soudan du Sud",
    "libya": "Libye", "libye": "Libye",
    "mauritania": "Mauritanie", "mauritanie": "Mauritanie",
}
UNKNOWN_COUNTRY = "Non précisé"

# Variantes de denomination designant le MEME evenement. Plutot que de
# relever le seuil de similarite (risque de fusion a tort), ces alias sont
# listes explicitement : chaque cle canonique regroupe les formulations
# rencontrees dans les sources.
NAME_ALIASES = {
    "fhs africa": "fhs-africa",
    "future hospitality summit africa": "fhs-africa",
    "africa hotel investment summit": "fhs-africa",
    "ahif": "fhs-africa",
    "eapi summit": "eapi-summit",
    "east africa property investment summit": "eapi-summit",
    "east africa api summit": "eapi-summit",
    "api summit": "api-summit",
    "africa property investment summit": "api-summit",
    "abuja real estate fest": "abuja-real-estate-fest",
    "lagos real estate fest": "lagos-real-estate-fest",
    "buildexpo africa": "buildexpo-africa",
    "buildexpo kenya": "buildexpo-kenya",
    "africa build show": "africa-build-show",
    "africa international housing show": "aihs",
    "capital legacy forum": "capital-legacy-forum",
    "new africa capital forum": "capital-legacy-forum",
}


def alias_key(name):
    """Cle canonique d'un evenement, en tenant compte des alias connus."""
    low = norm_key(name)
    for phrase, canon in NAME_ALIASES.items():
        if phrase in low:
            return canon
    return low


def canon_country(value):
    """Ramene une denomination de pays a sa forme canonique."""
    raw = (value or "").strip()
    if not raw:
        return UNKNOWN_COUNTRY
    key = re.sub(r"\s+", " ", raw.lower()).strip(" .,;")
    if key in COUNTRY_CANON:
        return COUNTRY_CANON[key]
    key2 = re.sub(r"[^\w\s']", "", key)
    if key2 in COUNTRY_CANON:
        return COUNTRY_CANON[key2]
    # variante accentuee : on retire les diacritiques avant de re-essayer
    ascii_key = unicodedata.normalize("NFKD", key)
    ascii_key = "".join(c for c in ascii_key if not unicodedata.combining(c))
    if ascii_key in COUNTRY_CANON:
        return COUNTRY_CANON[ascii_key]
    # les valeurs manifestement non geographiques sont regroupees
    low = raw.lower()
    if low in ("à confirmer", "a confirmer", "inconnu", "unknown", "n/a", "-", "none"):
        return UNKNOWN_COUNTRY
    return raw


# --------------------------------------------------------------------------
# utilitaires
# --------------------------------------------------------------------------


def norm_key(s):
    """Normalise pour comparer deux noms d'evenements."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(20\d\d|edition|editions|e?dition|eme|eme edition|the)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_date(value):
    if not value:
        return None
    s = str(value).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return datetime.strptime(s, "%Y-%m-%d").date()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def fmt_fr(d):
    if not d:
        return ""
    return "%d %s %d" % (d.day, MONTHS[d.strftime("%m")], d.year)


def fmt_range(start, end):
    if not start:
        return ""
    if not end or end == start:
        return fmt_fr(start)
    if start.year == end.year and start.month == end.month:
        return "%d-%d %s %d" % (start.day, end.day, MONTHS[start.strftime("%m")], start.year)
    if start.year == end.year:
        return "%d %s - %d %s %d" % (
            start.day, MONTHS[start.strftime("%m")],
            end.day, MONTHS[end.strftime("%m")], start.year,
        )
    return "%s - %s" % (fmt_fr(start), fmt_fr(end))


def as_text(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return " ; ".join(str(x).strip() for x in v if str(x).strip())
    return str(v).strip()


def fold(text):
    """Repli pour le HTML : echappe les caracteres critiques."""
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;").replace("'", "&#39;")
    )


def ics_escape(text):
    out = str(text or "")
    out = out.replace("\\", "\\\\")
    out = out.replace(";", r"\;")
    out = out.replace(",", r"\,")
    out = out.replace("\r\n", r"\n")
    out = out.replace("\n", r"\n")
    return out


# --------------------------------------------------------------------------
# chargement
# --------------------------------------------------------------------------

zones = []
files = sorted(f for f in os.listdir(DATA) if f.startswith("zone-") and f.endswith(".json"))
for fn in files:
    path = os.path.join(DATA, fn)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        print("  ! fichier illisible %s : %s" % (fn, exc), file=sys.stderr)
        continue
    payload["_file"] = fn
    zones.append(payload)
    print("  lu %-28s zone=%-28s evenements=%d" % (
        fn, payload.get("zone", "?"), len(payload.get("events", []))))

# --------------------------------------------------------------------------
# normalisation + dedoublonnage
# --------------------------------------------------------------------------

FIELDS = [
    "name", "edition", "category", "start", "end", "date_display",
    "date_status", "city", "country", "venue", "organizer", "attendees",
    "exhibitors", "investor_score", "investor_why", "capital_actors",
    "themes", "ticket_url", "source_url", "source_name", "last_verified",
    "conflicts",
]

records = []
for z in zones:
    for ev in z.get("events", []):
        rec = {f: ev.get(f) for f in FIELDS}
        rec["zone"] = z.get("zone", "?")
        rec["country"] = canon_country(rec.get("country"))
        rec["start_dt"] = parse_date(rec["start"])
        rec["end_dt"] = parse_date(rec["end"])
        if rec["start_dt"] and not rec["end_dt"]:
            rec["end_dt"] = rec["start_dt"]
        rec["category"] = rec["category"] or "national_anchor"
        rec["date_status"] = rec["date_status"] or "to_confirm"
        rec["investor_score"] = rec["investor_score"] or 0
        try:
            rec["investor_score"] = int(rec["investor_score"])
        except (TypeError, ValueError):
            rec["investor_score"] = 0
        if not rec["date_display"]:
            rec["date_display"] = fmt_range(rec["start_dt"], rec["end_dt"])
        rec["conflicts"] = rec["conflicts"] or []
        rec["_key"] = (
            alias_key(rec["name"]),
            (rec["country"] or "").lower(),
            rec["start_dt"].isoformat() if rec["start_dt"] else "",
        )
        records.append(rec)

# dedoublonnage : meme cle -> on garde la fiche la plus riche et on fusionne
merged = {}
for rec in records:
    key = rec["_key"]
    if key not in merged:
        merged[key] = rec
        continue
    keep, drop = rec, merged[key]
    filled = lambda r: sum(1 for f in FIELDS if r.get(f) not in (None, "", [], 0))
    if filled(drop) > filled(keep):
        keep, drop = drop, keep
    for c in drop["conflicts"]:
        if c not in keep["conflicts"]:
            keep["conflicts"].append(c)
    if not keep.get("source_url") and drop.get("source_url"):
        keep["source_url"] = drop["source_url"]
        keep["source_name"] = drop.get("source_name")
    keep["conflicts"].append(
        "doublon fusionne : %s (%s) et %s (%s)" % (
            keep.get("name"), keep.get("zone"), drop.get("name"), drop.get("zone")
        )
    )
    merged[key] = keep

records = list(merged.values())


def name_tokens(text):
    """Jetons significatifs d'un nom d'evenement (hors mots d'edition)."""
    stop = {"edition", "editions", "annual", "conference", "summit", "forum",
            "expo", "exhibition", "show", "international", "africa", "the",
            "african", "annual", "mast", "master", "conference", "days"}
    toks = [t for t in norm_key(text).split() if len(t) >= 4 and t not in stop]
    return set(toks)


def similarity(a, b):
    """Jaccard sur les jetons de nom."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


# Deuxieme passe : meme pays, meme ville, meme date de depart et noms proches.
# Capture les variantes de denomination du meme evenement ("AIHS 2027 - 21st
# Africa International Housing Show" vs "Africa International Housing Show").
def second_pass(records):
    out = []
    for rec in records:
        merged_into = None
        for kept in out:
            if rec["country"] != kept["country"]:
                continue
            if not rec["start_dt"] or not kept["start_dt"]:
                continue
            if rec["start_dt"] != kept["start_dt"]:
                continue
            if (rec["city"] or "").lower() != (kept["city"] or "").lower():
                continue
            if similarity(rec["name"], kept["name"]) >= 0.55:
                merged_into = kept
                break
        if merged_into is None:
            out.append(rec)
            continue
        keep, drop = merged_into, rec
        filled = lambda r: sum(1 for f in FIELDS if r.get(f) not in (None, "", [], 0))
        if filled(drop) > filled(keep):
            keep, drop = drop, keep
            out[out.index(merged_into)] = keep
        for c in drop["conflicts"]:
            if c not in keep["conflicts"]:
                keep["conflicts"].append(c)
        for c in drop["hard_conflicts"]:
            if c not in keep["hard_conflicts"]:
                keep["hard_conflicts"].append(c)
        for c in drop["soft_notes"]:
            if c not in keep["soft_notes"]:
                keep["soft_notes"].append(c)
        keep["conflicts"].append(
            "variante de denomination fusionnee : %s (identique a %s, meme pays/ville/date)"
            % (drop.get("name"), keep.get("name"))
        )
    return out


# --------------------------------------------------------------------------
# arbitrage : date non confirmee mais conflit declare -> on degrade le statut
# --------------------------------------------------------------------------
# Distinguer deux choses tres differentes :
#   - une CONTRADICTION entre sources ("12 nov (A) vs 19 nov (B)") -> conflit dur
#   - une LACUNE ("effectif non communique") -> simple signal, pas un conflit
# Le declassement confirmed -> probable ne se produit que sur une contradiction.
CONTRA_MARKERS = (
    " vs ", "alors que", "plutot que", "plutôt que", "tandis que",
    "et non", "contredit", "contrediction", "incompatible", "differe de",
)
RE_DAYMONTH = re.compile(
    r"\b(\d{1,2})\s+(janvier|fevrier|février|mars|avril|mai|juin|juillet|aout|août|"
    r"septembre|octobre|novembre|decembre|décembre)\s+(20\d{2})\b", re.I)
RE_ISO = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


def classify_conflict(text):
    """Retourne 'hard' pour une contradiction entre sources, 'soft' sinon."""
    low = str(text or "").lower()
    if any(m in low for m in CONTRA_MARKERS):
        return "hard"
    dates = set(RE_DAYMONTH.findall(low)) | set(RE_ISO.findall(low))
    if len(dates) >= 2:
        return "hard"
    return "soft"


for rec in records:
    hard = [c for c in rec["conflicts"] if classify_conflict(c) == "hard"]
    soft = [c for c in rec["conflicts"] if classify_conflict(c) == "soft"]
    rec["hard_conflicts"] = hard
    rec["soft_notes"] = soft
    if hard and rec["date_status"] == "confirmed":
        rec["date_status"] = "probable"
    rec["conflict_count"] = len(hard)

# La seconde passe de dedoublonnage s'execute apres la classification, car
# elle fusionne les listes de conflits deja categorisees.
records = second_pass(records)
for rec in records:
    rec["hard_conflicts"] = [c for c in rec["conflicts"] if classify_conflict(c) == "hard"]
    rec["soft_notes"] = [c for c in rec["conflicts"] if classify_conflict(c) == "soft"]
    rec["conflict_count"] = len(rec["hard_conflicts"])
    if rec["hard_conflicts"] and rec["date_status"] == "confirmed":
        rec["date_status"] = "probable"

# --------------------------------------------------------------------------
# tri : par date, puis score investisseur decroissant
# --------------------------------------------------------------------------

def sort_key(rec):
    d = rec["start_dt"] or date(2099, 12, 31)
    return (d, -rec["investor_score"], rec["name"] or "")

records.sort(key=sort_key)

dated = [r for r in records if r["start_dt"]]
undated = [r for r in records if not r["start_dt"]]
undated.sort(key=lambda r: (-r["investor_score"], r["name"] or ""))

# --------------------------------------------------------------------------
# ecriture du tracker HTML
# --------------------------------------------------------------------------

for rec in records:
    rec["month"] = rec["start_dt"].strftime("%Y-%m") if rec["start_dt"] else ""
    rec["category_label"] = CATEGORY_LABEL.get(rec["category"], rec["category"])
    rec["status_label"] = STATUS_LABEL.get(rec["date_status"], rec["date_status"])
    rec["why_text"] = as_text(rec["investor_why"])
    rec["actors_text"] = as_text(rec["capital_actors"])
    rec["themes_text"] = as_text(rec["themes"])
    rec["conflicts_text"] = as_text(rec["hard_conflicts"])
    rec["notes_text"] = as_text(rec["soft_notes"])
    rec["has_conflict"] = bool(rec["hard_conflicts"])
    rec["display_date"] = rec["date_display"] or "Date a confirmer"

# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------

CSV_COLS = [
    ("Date debut", lambda r: r["start_dt"].isoformat() if r["start_dt"] else ""),
    ("Date fin", lambda r: r["end_dt"].isoformat() if r["end_dt"] else ""),
    ("Date affichee", lambda r: r["display_date"]),
    ("Statut date", lambda r: r["status_label"]),
    ("Evenement", lambda r: r["name"] or ""),
    ("Edition", lambda r: r["edition"] or ""),
    ("Categorie", lambda r: r["category_label"]),
    ("Ville", lambda r: r["city"] or ""),
    ("Pays", lambda r: r["country"] or ""),
    ("Zone", lambda r: r["zone"] or ""),
    ("Lieu", lambda r: r["venue"] or ""),
    ("Organisateur", lambda r: r["organizer"] or ""),
    ("Participants", lambda r: r["attendees"] or ""),
    ("Exposants", lambda r: r["exhibitors"] or ""),
    ("Score investisseur", lambda r: r["investor_score"]),
    ("Acteurs du capital", lambda r: r["actors_text"]),
    ("Themes", lambda r: r["themes_text"]),
    ("Pertinence investisseur", lambda r: r["why_text"]),
    ("Billetterie", lambda r: r["ticket_url"] or ""),
    ("Source", lambda r: r["source_name"] or ""),
    ("Source URL", lambda r: r["source_url"] or ""),
    ("Conflits de sources", lambda r: as_text(r["hard_conflicts"])),
    ("Signaux et lacunes", lambda r: as_text(r["soft_notes"])),
    ("Verifie le", lambda r: r["last_verified"] or ""),
]

csv_path = os.path.join(OUT, "agenda-immobilier-afrique.csv")
with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.writer(fh, delimiter=";")
    writer.writerow([c[0] for c in CSV_COLS])
    for rec in records:
        writer.writerow([c[1](rec) for c in CSV_COLS])
print("  -> %s (%d lignes)" % (csv_path, len(records)))

# --------------------------------------------------------------------------
# ICS
# --------------------------------------------------------------------------

ics_path = os.path.join(OUT, "agenda-immobilier-afrique.ics")
lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Agenda immobilier Afrique//FR",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:Agenda immobilier Afrique 2026-2027",
    "X-WR-TIMEZONE:Africa/Lagos",
]
now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
for rec in dated:
    start = rec["start_dt"]
    end = rec["end_dt"] or start
    # DTEND est exclusif dans le format iCalendar
    end_excl = end + timedelta(days=1)
    summary = rec["name"] or "Evenement"
    if rec["edition"]:
        summary += " - %s" % rec["edition"]
    loc = ", ".join([x for x in [rec["venue"], rec["city"], rec["country"]] if x])
    desc_parts = []
    if rec["why_text"]:
        desc_parts.append(rec["why_text"])
    if rec["themes_text"]:
        desc_parts.append("Themes : %s" % rec["themes_text"])
    if rec["actors_text"]:
        desc_parts.append("Acteurs du capital : %s" % rec["actors_text"])
    if rec["conflicts_text"]:
        desc_parts.append("Conflits de sources : %s" % rec["conflicts_text"])
    if rec["notes_text"]:
        desc_parts.append("Signaux et lacunes : %s" % rec["notes_text"])
    desc_parts.append("Statut de la date : %s" % rec["status_label"])
    desc_parts.append("Source : %s %s" % (rec["source_name"] or "", rec["source_url"] or ""))
    desc_parts.append("Verifie le %s" % (rec["last_verified"] or ""))
    desc = "\n".join(desc_parts)

    # L'UID doit distinguer les editions successives d'un meme evenement
    # (ex. Abuja Real Estate Fest 2026 et 2027) : la date de debut est donc
    # integratee. Sans cela, l'import calendrier ecrase une edition.
    uid_slug = re.sub(r"[^a-zA-Z0-9]+", "-", norm_key(rec["name"])).strip("-") or "event"
    uid_date = start.strftime("%Y%m%d")
    lines += [
        "BEGIN:VEVENT",
        "UID:%s-%s@agenda-immobilier-afrique" % (uid_slug, uid_date),
        "DTSTAMP:%s" % now,
        "DTSTART;VALUE=DATE:%s" % start.strftime("%Y%m%d"),
        "DTEND;VALUE=DATE:%s" % end_excl.strftime("%Y%m%d"),
        "SUMMARY:%s" % ics_escape(summary),
        "LOCATION:%s" % ics_escape(loc),
        "DESCRIPTION:%s" % ics_escape(desc),
        "STATUS:%s" % ("CONFIRMED" if rec["date_status"] == "confirmed" else "TENTATIVE"),
        "CATEGORIES:%s" % ics_escape(rec["category_label"]),
        "URL:%s" % (rec["ticket_url"] or rec["source_url"] or ""),
        "END:VEVENT",
    ]
lines.append("END:VCALENDAR")


def fold_ics(lines):
    """RFC 5545 : une ligne iCalendar ne doit pas depasser 75 octets.
    Les suites sont precedees d'une espace."""
    out = []
    for line in lines:
        raw = line.encode("utf-8")
        if len(raw) <= 75:
            out.append(line)
            continue
        # on decoupe la ligne sans couper un caractere multi-octets
        chunks = []
        current = ""
        for ch in line:
            if len((current + ch).encode("utf-8")) > 74:
                chunks.append(current)
                current = ""
            current += ch
        if current:
            chunks.append(current)
        out.append(chunks[0])
        for ch in chunks[1:]:
            # la ligne de continuation porte une espace de prefixe : elle doit
            # donc tenir dans 75 octets elle aussi (74 + 1)
            out.append(" " + ch)
    return out


lines = fold_ics(lines)
with open(ics_path, "w", encoding="utf-8", newline="") as fh:
    fh.write("\r\n".join(lines) + "\r\n")
print("  -> %s (%d evenements dates)" % (ics_path, len(dated)))

# --------------------------------------------------------------------------
# JSON pour le tracker HTML
# --------------------------------------------------------------------------

payload = {
    "generated": "2026-11-06",
    "totals": {
        "all": len(records),
        "dated": len(dated),
        "undated": len(undated),
    },
    "events": [
        {
            "name": r["name"] or "",
            "edition": r["edition"] or "",
            "category": r["category"],
            "category_label": r["category_label"],
            "status": r["date_status"],
            "status_label": r["status_label"],
            "start": r["start_dt"].isoformat() if r["start_dt"] else "",
            "end": r["end_dt"].isoformat() if r["end_dt"] else "",
            "display_date": r["display_date"],
            "month": r["month"],
            "city": r["city"] or "",
            "country": r["country"] or "",
            "zone": r["zone"] or "",
            "venue": r["venue"] or "",
            "organizer": r["organizer"] or "",
            "attendees": r["attendees"] or "",
            "exhibitors": r["exhibitors"] or "",
            "score": r["investor_score"],
            "why": r["why_text"],
            "actors": r["actors_text"],
            "themes": r["themes_text"],
            "ticket_url": r["ticket_url"] or "",
            "source_name": r["source_name"] or "",
            "source_url": r["source_url"] or "",
            "conflicts": r["conflicts_text"],
            "notes": r["notes_text"],
            "has_conflict": r["has_conflict"],
            "last_verified": r["last_verified"] or "",
        }
        for r in records
    ],
}
json_path = os.path.join(OUT, "tracker-data.json")
with open(json_path, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=1)
print("  -> %s" % json_path)

# --------------------------------------------------------------------------
# rapport console
# --------------------------------------------------------------------------

print("\n--- Synthese ---")
by_cat = {}
for r in records:
    by_cat.setdefault(r["category_label"], []).append(r)
for cat, rs in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
    print("  %-26s %d" % (cat, len(rs)))
by_status = {}
for r in records:
    by_status[r["status_label"]] = by_status.get(r["status_label"], 0) + 1
print("  statuts : %s" % by_status)
print("  dates : %d  |  non dates : %d" % (len(dated), len(undated)))
print("  pays couverts : %s" % ", ".join(sorted({r["country"] for r in records if r["country"]})))
with_conflicts = [r for r in records if r["hard_conflicts"]]
print("  evenements avec contradiction entre sources : %d" % len(with_conflicts))
print("  evenements avec simple signal / lacune : %d" % len([r for r in records if r["soft_notes"]]))
for r in with_conflicts[:12]:
    print("   - %s : %s" % (r["name"], r["conflicts_text"][:160]))
