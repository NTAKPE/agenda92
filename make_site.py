# -*- coding: utf-8 -*-
"""
Generateur du site statique de l'agenda immobilier africain.

Produit dans site/ :
  index.html                 tracker interactif, lignes pre-rendues (fonctionne sans JS)
  evenements/<slug>.html     une page par evenement
  pays/<slug>.html           une page par pays
  methodologie.html          le filtre, les statuts, la methode de verification
  changelog.html             journal des changements
  sponsors.html              emplacement partenaire
  contribuer.html            formulaire d'intake (zones a blanc)
  feed.xml                   flux RSS des changements (pour Substack / agrégateurs)
  sitemap.xml, robots.txt
  assets/site.css, assets/tracker.js

Entree : export/tracker-data.json (produit par build.py)
         data/changelog.json      (journal, a maintenir dans le temps)

Usage :  python make_site.py
"""
import json
import os
import re
import unicodedata
from datetime import date, datetime

from siteutil import host_of

BASE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.join(BASE, "export")
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")

# A definir au deploiement : "https://ton-domaine.com". Vide = URLs relatives,
# ce qui fonctionne en local mais pas pour les partages sur les reseaux sociaux.
SITE_URL = os.environ.get("SITE_URL", "").strip()

# Adresse de contact publiee sur la page « a propos ». Remplacable par la
# variable d'environnement CONTACT_EMAIL.
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "jm.ntakpe@gmail.com").strip()

# Nombre d'Etats africains (nomenclature onusienne). Sert a dire ce que
# l'agenda ne couvre pas encore, sans que ce nombre soit fige a la main.
AFRICA_TOTAL = 54

MONTHS = {
    "01": "janvier", "02": "février", "03": "mars", "04": "avril",
    "05": "mai", "06": "juin", "07": "juillet", "08": "août",
    "09": "septembre", "10": "octobre", "11": "novembre", "12": "décembre",
}

CATEGORY_LABEL = {
    "flagship_continental": "Flagship continental",
    "national_anchor": "Ancre nationale",
    "capital_markets": "Marchés de capitaux",
    "adjacent_construction": "Adjacent construction",
    "watchlist": "Watchlist",
}
STATUS_LABEL = {
    "confirmed": "Date confirmée",
    "probable": "Date probable",
    "to_confirm": "Date à confirmer",
}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def slugify(text):
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "x"


def esc(text):
    return (str(text if text is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def clip(text, limit=155):
    """Tronque proprement un texte de meta description.

    Coupe sur un mot entier et ajoute une ellipse, plutot que de trancher
    au milieu d'un mot ou d'une parenthese.
    """
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(t) <= limit:
        return t
    cut = t[:limit].rsplit(" ", 1)[0].rstrip(" ,;:.·—-«»()[]\"'")
    if len(cut) < limit * 0.6:      # mot tres long : on coupe net
        cut = t[:limit].rstrip()
    return cut + "…"


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def fmt_gen_date(value):
    """'2026-11-06' -> '6 novembre 2026'. Une date ISO brute fait amateur."""
    d = parse_iso(value)
    if not d:
        return str(value or "")
    return "%d %s %d" % (d.day, MONTHS["%02d" % d.month], d.year)


def fmt_date_fr(value):
    d = parse_iso(value)
    if not d:
        return ""
    return "%d %s %d" % (d.day, MONTHS["%02d" % d.month], d.year)


def fmt_range_fr(start, end):
    s, e = parse_iso(start), parse_iso(end)
    if not s:
        return "Date non annoncée"
    if not e or e == s:
        return fmt_date_fr(start)
    if s.year == e.year and s.month == e.month:
        return "%d-%d %s %d" % (s.day, e.day, MONTHS["%02d" % s.month], s.year)
    if s.year == e.year:
        return "%d %s - %d %s %d" % (s.day, MONTHS["%02d" % s.month],
                                     e.day, MONTHS["%02d" % e.month], s.year)
    return "%s - %s" % (fmt_date_fr(start), fmt_date_fr(end))


def quarter_of(value):
    d = parse_iso(value)
    if not d:
        return ""
    return "T%d %d" % ((d.month - 1) // 3 + 1, d.year)


def score_bars(score):
    out = []
    for i in range(1, 6):
        cls = "on" if i <= (score or 0) else ""
        out.append('<s class="%s"></s>' % cls)
    return '<span class="score" title="Score %s/5">%s</span>' % (score or 0, "".join(out))


def status_badge(status):
    cls = {"confirmed": "b-confirmed", "probable": "b-probable",
           "to_confirm": "b-to_confirm"}.get(status, "b-to_confirm")
    return '<span class="badge %s">%s</span>' % (cls, esc(STATUS_LABEL.get(status, status)))


def category_badge(cat):
    return '<span class="cat">%s</span>' % esc(CATEGORY_LABEL.get(cat, cat))


def share_buttons(url, text):
    """Boutons de partage : c'est ainsi qu'une fiche se diffuse dans un WhatsApp
    ou une mailing list, c'est-a-dire dans les canaux ou l'audience est reellement.

    Les parametres sont encodes en percent-encoding : sans cela, un espace ou
    un accent casse le lien de partage. L'URL passee doit etre absolue
    (page_canonical) pour que X, LinkedIn et Telegram la relisent."""
    from urllib.parse import quote
    u = esc(quote(str(url), safe=":/"))
    t = esc(quote(str(text), safe=""))
    wa = esc(quote("%s %s" % (text, url), safe=""))
    return (
        '<div class="share">'
        '<span class="share-label">Partager</span>'
        '<a class="share-btn" rel="noopener" target="_blank" '
        'href="https://twitter.com/intent/tweet?text=%s&url=%s">X</a>'
        '<a class="share-btn" rel="noopener" target="_blank" '
        'href="https://www.linkedin.com/sharing/share-offsite/?url=%s">LinkedIn</a>'
        '<a class="share-btn" rel="noopener" target="_blank" '
        'href="https://wa.me/?text=%s">WhatsApp</a>'
        '<a class="share-btn" rel="noopener" target="_blank" '
        'href="https://t.me/share/url?url=%s&text=%s">Telegram</a>'
        '<button class="share-btn" type="button" data-copy="%s">Copier le lien</button>'
        '</div>'
    ) % (t, u, u, wa, u, t, esc(str(url)))


def event_jsonld(e, page_url):
    """Schema.org Event : permet a Google d'afficher la date en resultat enrichi."""
    if not e.get("start"):
        return None
    end = e.get("end") or e.get("start")
    ld = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": e.get("name"),
        "startDate": e.get("start"),
        "endDate": end,
        "eventStatus": "https://schema.org/EventScheduled",
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "description": (e.get("why") or "")[:280],
        "url": page_url,
    }
    if e.get("venue"):
        ld["location"] = {
            "@type": "Place",
            "name": e["venue"],
            "address": {
                "@type": "PostalAddress",
                "addressLocality": e.get("city", ""),
                "addressCountry": e.get("country", ""),
            },
        }
    if e.get("organizer"):
        ld["organizer"] = {"@type": "Organization", "name": e["organizer"]}
    if e.get("source_url"):
        ld["sameAs"] = e["source_url"]
    return ld


def sponsor_slot(label="Emplacement partenaire disponible", prefix=""):
    """Emplacement publicitaire louable, present sur toutes les pages."""
    return (
        '<aside class="adslot" aria-label="Emplacement partenaire">'
        '<span class="adslot-label">Espace partenaire</span>'
        '<p class="adslot-title">%s</p>'
        '<p class="adslot-note">Emplacement réservé — réservé aux acteurs du marché immobilier '
        'africain (banques, cabinets, promoteurs, fournisseurs de données). '
        '<a href="%ssponsors.html">En savoir plus</a></p>'
        '</aside>' % (esc(label), prefix)
    )


# --------------------------------------------------------------------------
# donnees
# --------------------------------------------------------------------------

with open(os.path.join(EXPORT, "tracker-data.json"), "r", encoding="utf-8") as fh:
    payload = json.load(fh)
EVENTS = payload["events"]

# Date de la derniere passe de re-verification : elle vient du rapport
# ecrit par refresh.py, pas d'une date saisie a la main. En son absence, on
# retombe sur la date d'edition des donnees.
REFRESH_DATE = ""
_refresh_report = os.path.join(EXPORT, "refresh-report.json")
if os.path.exists(_refresh_report):
    try:
        with open(_refresh_report, "r", encoding="utf-8") as fh:
            _r = json.load(fh)
        REFRESH_DATE = str(_r.get("generated") or "")[:10]
    except (ValueError, OSError):
        REFRESH_DATE = ""

changelog_path = os.path.join(DATA, "changelog.json")
if os.path.exists(changelog_path):
    with open(changelog_path, "r", encoding="utf-8") as fh:
        CHANGELOG = json.load(fh)
else:
    CHANGELOG = []

# zones a blanc : negative findings agreges par zone
negative = []
for fn in sorted(os.listdir(DATA)):
    if not (fn.startswith("zone-") and fn.endswith(".json")):
        continue
    with open(os.path.join(DATA, fn), "r", encoding="utf-8") as fh:
        z = json.load(fh)
    for n in z.get("negative_findings", []):
        negative.append((z.get("zone", "?"), n))
    for r in z.get("rejected", []):
        negative.append((z.get("zone", "?"), "ECARTE — %s : %s" % (r.get("name", ""), r.get("reason", ""))))

COUNTRIES = {}
for e in EVENTS:
    COUNTRIES.setdefault(e["country"], []).append(e)
for lst in COUNTRIES.values():
    lst.sort(key=lambda e: (e["start"] or "9999-99-99", e["name"]))

# Une page pays « Non précisé » n'a aucun sens pour un lecteur : ces
# événements restent dans l'agenda mais ne génèrent pas de page pays.
UNKNOWN = "Non précisé"
REAL_COUNTRIES = {c: v for c, v in COUNTRIES.items() if c != UNKNOWN}
ORPHAN_EVENTS = COUNTRIES.get(UNKNOWN, [])

# Pays africains sans aucun rendez-vous documente : c'est ce que la page
# « contribuer » propose de completer. Derive, jamais saisi a la main.
UNCOVERED_COUNTRIES = max(0, AFRICA_TOTAL - len(REAL_COUNTRIES))


# --------------------------------------------------------------------------
# visuels de partage (Open Graph) et favicon
# --------------------------------------------------------------------------

def _font(size, bold=False):
    """Police systeme pour la generation d'images."""
    from PIL import ImageFont
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:  # noqa: BLE001
                pass
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_og_image(path, title, subtitle, kicker="AGENDA IMMOBILIER AFRIQUE"):
    """Carte de partage 1200x630, style du site."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (14, 17, 22))
    d = ImageDraw.Draw(img)
    # bandeau lateral accent
    d.rectangle([0, 0, 14, H], fill=(240, 163, 60))
    # trame discrete
    for x in range(0, W, 40):
        d.line([(x, 0), (x, H)], fill=(22, 27, 34), width=1)
    d.rectangle([0, H - 8, W, H], fill=(240, 163, 60))

    d.text((70, 64), kicker, font=_font(24, True), fill=(240, 163, 60))
    d.text((70, 110), "2026-2027", font=_font(24), fill=(110, 123, 140))

    f_title = _font(54, True)
    lines = _wrap(d, title, f_title, W - 140)[:4]
    y = 200
    for ln in lines:
        d.text((70, y), ln, font=f_title, fill=(230, 237, 243))
        y += 68

    if subtitle:
        f_sub = _font(30)
        for ln in _wrap(d, subtitle, f_sub, W - 140)[:2]:
            d.text((70, y + 12), ln, font=f_sub, fill=(154, 167, 182))
            y += 42

    d.text((70, H - 92),
           "%d evenements  |  %d pays  |  dates verifiees et sources contradictoires"
           % (len(EVENTS), len(REAL_COUNTRIES)),
           font=_font(23), fill=(110, 123, 140))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG", optimize=True)
    return True


def make_favicon(path_png, path_svg):
    """Favicon simple : bloc orange + point d'accent."""
    try:
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (64, 64), (14, 17, 22, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([4, 4, 60, 60], radius=12, fill=(240, 163, 60))
        d.rectangle([16, 16, 48, 22], fill=(14, 17, 22))
        d.rectangle([16, 28, 38, 34], fill=(14, 17, 22))
        d.rectangle([16, 40, 48, 46], fill=(14, 17, 22))
        img.save(path_png, "PNG")
    except ImportError:
        pass
    with open(path_svg, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            '<rect x="4" y="4" width="56" height="56" rx="12" fill="#f0a33c"/>'
            '<rect x="16" y="16" width="32" height="6" fill="#0e1116"/>'
            '<rect x="16" y="28" width="22" height="6" fill="#0e1116"/>'
            '<rect x="16" y="40" width="32" height="6" fill="#0e1116"/></svg>'
        )


# --------------------------------------------------------------------------
# gabarit de page
# --------------------------------------------------------------------------

def abs_url(path):
    """URL absolue si SITE_URL est renseigne, sinon chemin relatif.
    SITE_URL = "https://ton-domaine.com"  ->  a definir au moment du deploiement."""
    if not path:
        return SITE_URL
    if SITE_URL:
        return SITE_URL.rstrip("/") + "/" + path.lstrip("/")
    return path


def page_canonical(path, prefix=""):
    """URL canonique resolvable depuis la page courante.
    Absolue si SITE_URL est renseigne, sinon relative a la profondeur."""
    if SITE_URL:
        return SITE_URL.rstrip("/") + "/" + str(path).lstrip("/")
    return prefix + str(path)


def og_image_url(og_image, prefix=""):
    """URL du visuel de partage, resolvable depuis la page courante.

    Les visuels sont stockes a la racine du site. En local, il faut prependre
    le prefixe de profondeur (« ../ ») pour que le chemin resolve depuis une
    page de sous-repertoire. Avec SITE_URL renseignee, l'URL absolue ne porte
    pas de prefixe : « ../assets/... » y serait invalide.
    """
    if SITE_URL:
        return SITE_URL.rstrip("/") + "/" + str(og_image).lstrip("/")
    return prefix + str(og_image)


def page(title, description, body, extra_head="", extra_class="", prefix="",
         og_image="assets/og-default.png", og_title=None, jsonld=None, canonical=None,
         og_type="website"):
    """prefix : '' a la racine, '../' dans un sous-repertoire.
    canonical : chemin propre a la page, relatif a la racine du site."""
    gen = fmt_gen_date(payload.get("generated", ""))
    og_title = og_title or title
    canonical = page_canonical(canonical or "index.html", prefix)
    # le visuel est stocke a la racine du site : depuis un sous-repertoire,
    # il faut remonter d'un niveau, sinon l'image de partage est cassee.
    og_img = og_image_url(og_image, prefix)
    ld = ""
    if jsonld:
        ld = ('<script type="application/ld+json">%s</script>'
              % json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/"))
    return """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:type" content="%s">
<meta property="og:site_name" content="Agenda immobilier Afrique">
<meta property="og:locale" content="fr">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="%s">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%s">
<meta name="twitter:description" content="%s">
<meta name="twitter:image" content="%s">
<meta name="theme-color" content="#0e1116">
<link rel="icon" href="%sassets/favicon.svg" type="image/svg+xml">
<link rel="alternate icon" href="%sassets/favicon.png" sizes="32x32">
<link rel="apple-touch-icon" href="%sassets/favicon.png">
<link rel="alternate" type="application/rss+xml" title="Journal des changements" href="%sfeed.xml">
<link rel="stylesheet" href="%sassets/site.css">
%s
%s
</head>
<body class="%s">
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="%sindex.html">
      <span class="brand-mark">Agenda</span>
      <span class="brand-text">Immobilier Afrique<br><small>2026-2027</small></span>
    </a>
    <nav class="site-nav">
      <a href="%sindex.html">Agenda</a>
      <a href="%schangelog.html">Changements</a>
      <a href="%smethodologie.html">Méthodologie</a>
      <a href="%sa-propos.html">À propos</a>
      <a href="%ssponsors.html">Partenaires</a>
      <a href="%scontribuer.html">Contribuer</a>
    </nav>
  </div>
</header>
%s
<footer class="site-foot">
  <div class="wrap">
    <p><b>Agenda des événements immobiliers en Afrique</b> — un outil de travail à destination des
    investisseurs et financiers. Les dates non confirmées sont signalées explicitement : vérifiez
    toujours sur le site officiel avant de déplacer ou de payer.</p>
    <p>Édition du %s · %d événements retenus · %d pays · dernière passe de re-vérification : %s.</p>
    <p>Les sources et les contradictions entre sources sont consultables sur chaque fiche.
    <a href="%smethodologie.html">Comprendre la méthode</a> ·
    <a href="%sa-propos.html">À propos et politique de correction</a> ·
    <a href="%schangelog.html">Journal des changements</a> ·
    <a href="%scontribuer.html">Signaler un événement</a>.</p>
  </div>
</footer>
</body>
</html>
""" % (esc(title), esc(description), esc(canonical), esc(og_type), esc(og_title),
       esc(description), esc(canonical), esc(og_img), esc(og_title), esc(description),
       esc(og_img), prefix, prefix, prefix, prefix, prefix,
       ld, extra_head, extra_class,
       prefix, prefix, prefix, prefix, prefix, prefix, prefix,
       body,
       gen, len(EVENTS), len(REAL_COUNTRIES), fmt_gen_date(REFRESH_DATE or gen),
       prefix, prefix, prefix, prefix)


# --------------------------------------------------------------------------
# feuille de style
# --------------------------------------------------------------------------

CSS = """/* Agenda immobilier Afrique - feuille de style unique */
:root{
  --bg:#0e1116; --panel:#161b22; --panel2:#1c2330; --line:#2a3240;
  --ink:#e6edf3; --ink2:#9aa7b6; --ink3:#6e7b8c;
  --accent:#f0a33c; --accent2:#4da3ff;
  --ok:#3fb950; --warn:#d29922; --todo:#8b949e; --danger:#f85149;
  --radius:10px;
}
@media (prefers-color-scheme: light){
  :root{
    --bg:#f6f7f9; --panel:#ffffff; --panel2:#f0f2f5; --line:#dfe3e8;
    --ink:#1a1f27; --ink2:#5a6573; --ink3:#8a95a3;
    --accent:#b9700d; --accent2:#0a68c9;
    --ok:#1a7f37; --warn:#9a6700; --todo:#6e7781; --danger:#cf222e;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  font-size:14px;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--accent2);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}

.site-head{background:var(--panel);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:30}
/* L'en-tete etant colle en haut, un element amene au bord superieur de la
   fenetre passe dessous : le clic touche alors l'en-tete au lieu de la cible.
   scroll-padding-top reserve la hauteur de l'en-tete pour tout defilement
   programmatique (scrollIntoView, focus clavier, ancres). */
html{scroll-padding-top:132px}
@media (max-width:640px){html{scroll-padding-top:176px}}
.site-head .wrap{display:flex;flex-wrap:wrap;gap:18px;align-items:center;justify-content:space-between;padding-top:12px;padding-bottom:12px}
.brand{display:flex;gap:10px;align-items:center;color:var(--ink)}
.brand:hover{text-decoration:none}
.brand-mark{background:var(--accent);color:#1a1f27;font-weight:800;font-size:12px;letter-spacing:.08em;
  text-transform:uppercase;padding:4px 8px;border-radius:6px}
.brand-text{font-weight:700;line-height:1.15;letter-spacing:-.01em}
.brand-text small{color:var(--ink3);font-weight:400;font-size:11px}
.site-nav{display:flex;flex-wrap:wrap;gap:16px}
.site-nav a{color:var(--ink2);font-size:13.5px}
.site-nav a:hover{color:var(--ink)}

main{padding:34px 0 70px}
h1{margin:0 0 10px;font-size:30px;letter-spacing:-.02em;line-height:1.2}
h2{font-size:19px;letter-spacing:-.01em;margin:34px 0 12px}
h3{font-size:15px;margin:22px 0 8px}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);
  font-weight:700;margin:0 0 6px}
.lede{margin:0 0 22px;color:var(--ink2);max-width:74ch}
.muted{color:var(--ink3)}

.stats{display:flex;flex-wrap:wrap;gap:30px;margin:20px 0 26px}
.stat b{display:block;font-size:24px;letter-spacing:-.02em;line-height:1.2}
.stat span{font-size:11px;color:var(--ink3);text-transform:uppercase;letter-spacing:.07em}

.notice{margin:0 0 24px;padding:13px 15px;border:1px solid var(--line);
  border-left:3px solid var(--warn);border-radius:0 var(--radius) var(--radius) 0;
  background:var(--panel);color:var(--ink2);font-size:13px}
.notice b{color:var(--ink)}

.toolbar{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:12px;margin-bottom:18px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
input[type=search],select{background:var(--bg);border:1px solid var(--line);color:var(--ink);
  padding:8px 10px;border-radius:8px;font-size:13px;font-family:inherit;outline:none}
input[type=search]{min-width:220px;flex:1 1 220px}
input[type=search]:focus,select:focus{border-color:var(--accent2)}
.btn{background:var(--panel2);border:1px solid var(--line);color:var(--ink2);padding:8px 12px;
  border-radius:8px;font-size:12.5px;cursor:pointer;font-family:inherit;white-space:nowrap}
.btn:hover{border-color:var(--accent);color:var(--ink)}
.count{margin-left:auto;color:var(--ink3);font-size:12.5px;white-space:nowrap}
.count b{color:var(--ink)}

table{width:100%;border-collapse:collapse;background:var(--panel);
  border:1px solid var(--line);border-radius:var(--radius);overflow:hidden}
thead th{background:var(--panel2);text-align:left;font-size:11px;letter-spacing:.06em;
  text-transform:uppercase;color:var(--ink3);padding:10px 12px;font-weight:600;
  border-bottom:1px solid var(--line);white-space:nowrap}
tbody td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}
tbody tr:last-child td{border-bottom:none}
tbody tr.ev{cursor:pointer}
tbody tr.ev:hover{background:var(--panel2)}
tbody tr.open{background:var(--panel2)}
.detail td{background:var(--panel2);padding:0 12px 16px 12px;border-bottom:1px solid var(--line)}
.detail.hide{display:none}
.ev-name{font-weight:600;color:var(--ink)}
.ev-name a{color:var(--ink)}
.ev-name a:hover{color:var(--accent)}
.ev-edition{display:block;color:var(--ink3);font-size:11.5px;font-weight:400;margin-top:1px}
.date-cell{white-space:nowrap}
.date-main{font-weight:600;font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:2px 7px;border-radius:99px;font-size:10.5px;
  font-weight:600;letter-spacing:.03em;white-space:nowrap;border:1px solid transparent}
.b-confirmed{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 40%,transparent);
  background:color-mix(in srgb,var(--ok) 12%,transparent)}
.b-probable{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 40%,transparent);
  background:color-mix(in srgb,var(--warn) 12%,transparent)}
.b-to_confirm{color:var(--todo);border-color:var(--line);background:var(--panel2)}
.cat{display:inline-block;font-size:10.5px;color:var(--ink2);background:var(--panel2);
  border:1px solid var(--line);padding:2px 7px;border-radius:5px;white-space:nowrap}
.score{display:inline-flex;gap:2px;vertical-align:middle}
.score s{width:5px;height:13px;border-radius:1px;background:var(--line);text-decoration:none}
.score s.on{background:var(--accent)}
.conflicts{display:inline-block;margin-top:5px;font-size:11px;color:var(--danger);
  border:1px solid color-mix(in srgb,var(--danger) 40%,transparent);
  background:color-mix(in srgb,var(--danger) 10%,transparent);padding:1px 6px;border-radius:5px}
.notes{display:inline-block;margin-top:5px;font-size:11px;color:var(--ink3);
  border:1px solid var(--line);background:var(--panel2);padding:1px 6px;border-radius:5px}
.meta{font-size:12px;color:var(--ink2)}
.meta div{margin-bottom:3px}

.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.block{border:1px solid var(--line);border-radius:8px;padding:13px 15px;background:var(--panel)}
.block h3{margin:0 0 8px;font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink3)}
.block p{margin:0 0 8px}
.block ul{margin:0;padding-left:18px}
.block li{margin-bottom:4px}

.adslot{border:1px dashed var(--line);border-radius:var(--radius);padding:16px 18px;
  background:var(--panel);margin:26px 0}
.adslot-label{display:inline-block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink3);border:1px solid var(--line);border-radius:99px;padding:2px 8px;margin-bottom:8px}
.adslot-title{margin:0 0 4px;font-weight:700;font-size:16px;color:var(--ink)}
.adslot-note{margin:0;font-size:12.5px;color:var(--ink2)}

.event-hero{border:1px solid var(--line);border-radius:var(--radius);background:var(--panel);padding:22px}
.event-hero h1{margin-bottom:8px}
.kv{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px 22px;margin-top:18px}
.kv div{border-top:1px solid var(--line);padding-top:9px}
.kv dt{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);margin:0 0 3px}
.kv dd{margin:0;font-size:13.5px}
.cta-row{margin-top:16px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.cta-row .btn{background:var(--accent);border-color:var(--accent);color:#12161c;font-weight:600;
  padding:9px 15px;font-size:13px;text-decoration:none}
.cta-row .btn:hover{filter:brightness(1.08);color:#12161c}
.cta-note{font-size:11.5px;color:var(--ink3)}
.pill-row{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.pill{font-size:12px;border:1px solid var(--line);border-radius:99px;padding:3px 10px;color:var(--ink2);background:var(--panel2)}

.changes{list-style:none;margin:0;padding:0}
.changes li{border-left:2px solid var(--line);padding:0 0 20px 18px;position:relative}
.changes li:before{content:"";position:absolute;left:-5px;top:7px;width:8px;height:8px;
  border-radius:50%;background:var(--accent)}
.changes time{display:block;font-size:11.5px;color:var(--ink3);letter-spacing:.04em;margin-bottom:3px}
.changes p{margin:0 0 4px}

.share{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:24px 0 0;padding-top:16px;
  border-top:1px solid var(--line)}
.share-label{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3);margin-right:4px}
.share-btn{display:inline-block;border:1px solid var(--line);background:var(--panel2);
  color:var(--ink2);border-radius:7px;padding:5px 11px;font-size:12.5px;cursor:pointer;
  font-family:inherit;line-height:1.4}
.share-btn:hover{border-color:var(--accent2);color:var(--ink);text-decoration:none}
.share-btn.ok{border-color:var(--ok);color:var(--ok)}

.chips{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 24px}
.chip{font-size:12.5px;border:1px solid var(--line);border-radius:99px;padding:4px 12px;
  background:var(--panel);color:var(--ink2)}
.chip:hover{border-color:var(--accent2);color:var(--ink2);text-decoration:none}

.empty{padding:40px;text-align:center;color:var(--ink3)}
.site-foot{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--ink3);font-size:12.5px}
.site-foot p{margin:0 0 6px;max-width:80ch}
.site-foot b{color:var(--ink2)}
.hide{display:none}
@media (max-width:1400px){ .hide-md{display:none} }
@media (max-width:1100px){ .hide-sm{display:none} }
@media (max-width:760px){ .hide-xs{display:none} }
@media (max-width:640px){
  h1{font-size:24px}
  .site-nav{gap:12px;font-size:12.5px}
}
@media print{
  .site-head,.toolbar,.adslot,.site-foot{display:none}
  body{background:#fff;color:#000}
}
"""

# --------------------------------------------------------------------------
# script de filtrage : agit sur des lignes deja presentes dans le HTML
# --------------------------------------------------------------------------

TRACKER_JS = """(function(){
  var rows = Array.prototype.slice.call(document.querySelectorAll('tr.ev'));
  var q = document.getElementById('q');
  var filters = {
    cat: document.getElementById('f-cat'),
    status: document.getElementById('f-status'),
    country: document.getElementById('f-country'),
    zone: document.getElementById('f-zone'),
    score: document.getElementById('f-score')
  };
  var shown = document.getElementById('shown');
  var total = document.getElementById('total');
  if(total) total.textContent = rows.length;

  function haystack(tr){
    if(tr._hay) return tr._hay;
    tr._hay = (tr.getAttribute('data-search') || '').toLowerCase();
    return tr._hay;
  }

  function apply(){
    var state = {q: q ? q.value.trim().toLowerCase() : ''};
    for(var k in filters){ if(filters[k]) state[k] = filters[k].value; }
    var n = 0;
    rows.forEach(function(tr){
      var ok = true;
      if(state.q && haystack(tr).indexOf(state.q) === -1) ok = false;
      if(ok && state.cat && tr.getAttribute('data-cat') !== state.cat) ok = false;
      if(ok && state.status && tr.getAttribute('data-status') !== state.status) ok = false;
      if(ok && state.country && tr.getAttribute('data-country') !== state.country) ok = false;
      if(ok && state.zone && tr.getAttribute('data-zone') !== state.zone) ok = false;
      if(ok && state.score && parseInt(tr.getAttribute('data-score')||'0',10) < parseInt(state.score,10)) ok = false;
      tr.hidden = !ok;
      var d = document.querySelector('tr.detail[data-d="'+tr.getAttribute('data-i')+'"]');
      if(d) d.hidden = !ok;
      if(ok) n++;
    });
    if(shown) shown.textContent = n;
    var empty = document.getElementById('empty');
    if(empty) empty.classList.toggle('hide', n > 0);
  }

  if(q) q.addEventListener('input', function(){ apply(); });
  for(var k in filters){
    if(filters[k]) filters[k].addEventListener('change', apply);
  }
  var reset = document.getElementById('reset');
  if(reset) reset.addEventListener('click', function(){
    if(q) q.value = '';
    for(var k in filters){ if(filters[k]) filters[k].value = (k==='score' ? '0' : ''); }
    apply();
  });

  Array.prototype.forEach.call(document.querySelectorAll('th[data-sort]'), function(th){
    th.addEventListener('click', function(){
      var key = th.getAttribute('data-sort');
      var dir = th.getAttribute('data-dir') === 'asc' ? -1 : 1;
      var tbody = document.getElementById('rows');
      var sorted = rows.slice().sort(function(a,b){
        var va = a.getAttribute('data-'+key) || '', vb = b.getAttribute('data-'+key) || '';
        if(key === 'score'){ va = parseInt(va||'0',10); vb = parseInt(vb||'0',10); }
        if(va < vb) return -1*dir;
        if(va > vb) return 1*dir;
        return 0;
      });
      sorted.forEach(function(tr){
        var d = document.querySelector('tr.detail[data-d="'+tr.getAttribute('data-i')+'"]');
        tbody.appendChild(tr);
        if(d) tbody.appendChild(d);
      });
      Array.prototype.forEach.call(document.querySelectorAll('th[data-sort]'), function(o){
        o.removeAttribute('data-dir');
      });
      th.setAttribute('data-dir', dir === 1 ? 'asc' : 'desc');
    });
  });

  var tbody = document.getElementById('rows');
  if(tbody) tbody.addEventListener('click', function(ev){
    var tr = ev.target.closest ? ev.target.closest('tr.ev') : null;
    if(!tr) return;
    if(ev.target.tagName === 'A') return;
    var d = document.querySelector('tr.detail[data-d="'+tr.getAttribute('data-i')+'"]');
    if(d){ d.classList.toggle('hide'); tr.classList.toggle('open'); }
  });

  apply();

  // Copie du lien de la fiche courante
  var copyBtn = document.querySelector('[data-copy]');
  if(copyBtn){
    copyBtn.addEventListener('click', function(){
      var url = copyBtn.getAttribute('data-copy');
      var done = function(){
        copyBtn.textContent = 'Lien copié';
        copyBtn.classList.add('ok');
        setTimeout(function(){ copyBtn.textContent = 'Copier le lien'; copyBtn.classList.remove('ok'); }, 2000);
      };
      if(navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(url).then(done, function(){});
      } else {
        var ta = document.createElement('textarea');
        ta.value = url; ta.setAttribute('readonly',''); ta.style.position='absolute'; ta.style.left='-9999px';
        document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); done(); } catch(err) {}
        document.body.removeChild(ta);
      }
    });
  }
})();
"""


# --------------------------------------------------------------------------
# fragments de table
# --------------------------------------------------------------------------

def event_row(e, index, with_link=True, prefix=""):
    display = fmt_range_fr(e["start"], e["end"])
    href = "%sevenements/%s.html" % (prefix, slugify(e["name"]))
    title = e["name"]
    if with_link:
        title = '<a href="%s">%s</a>' % (href, esc(e["name"]))
    else:
        title = esc(e["name"])
    edition = '<span class="ev-edition">%s</span>' % esc(e["edition"]) if e.get("edition") else ""
    scale = esc(e.get("attendees") or "")
    if e.get("exhibitors"):
        scale += '<br><span class="muted">%s exposants</span>' % esc(e["exhibitors"])
    flag = ""
    if e.get("has_conflict"):
        flag = '<div class="conflicts">conflit de sources</div>'
    elif e.get("notes"):
        flag = '<div class="notes">signalement</div>'
    search = " ".join([e.get("name", ""), e.get("edition", ""), e.get("city", ""),
                       e.get("country", ""), e.get("venue", ""), e.get("organizer", ""),
                       e.get("themes", ""), e.get("actors", ""), e.get("why", "")])
    return (
        '<tr class="ev" data-i="%d" data-cat="%s" data-status="%s" data-country="%s" '
        'data-zone="%s" data-score="%s" data-start="%s" data-name="%s" data-city="%s" '
        'data-search="%s">'
        '<td class="date-cell"><div class="date-main">%s</div>'
        '<div>%s</div>%s</td>'
        '<td><div class="ev-name">%s</div>%s</td>'
        '<td>%s</td>'
        '<td>%s<br><span class="muted">%s</span></td>'
        '<td class="hide-sm meta">%s</td>'
        '<td class="hide-sm">%s</td>'
        '<td class="hide-md meta">%s</td>'
        '<td class="hide-xs meta"><a href="%s">fiche</a></td>'
        '</tr>'
    ) % (
        index, esc(e.get("category", "")), esc(e.get("status", "")),
        esc(e.get("country", "")), esc(e.get("zone", "")),
        e.get("score", 0) or 0, esc(e.get("start") or ""),
        esc((e.get("name") or "").lower()), esc((e.get("city") or "").lower()),
        esc(search), esc(display), status_badge(e.get("status", "")), flag,
        title, edition, category_badge(e.get("category", "")),
        esc(e.get("city") or ""), esc(e.get("country") or ""),
        scale, score_bars(e.get("score", 0)),
        esc(e.get("actors") or ""), href,
    )


def detail_block(e):
    conflicts = e.get("conflicts") or ""
    notes = e.get("notes") or ""
    blocks = []
    blocks.append(
        '<div class="block"><h3>Pertinence investisseur</h3><p>%s</p>'
        '%s%s</div>' % (
            esc(e.get("why") or "—"),
            ('<p style="margin-bottom:0"><b>Thèmes :</b> %s</p>' % esc(e["themes"])) if e.get("themes") else "",
            ('<p style="margin-bottom:0"><b>Acteurs du capital :</b> %s</p>' % esc(e["actors"])) if e.get("actors") else "",
        )
    )
    org = [("Organisateur", e.get("organizer")), ("Lieu", e.get("venue")),
           ("Zone", e.get("zone")),
           ("Vérifié le", fmt_date_fr(e.get("last_verified")) or e.get("last_verified"))]
    org_html = "".join('<div><b>%s :</b> %s</div>' % (k, esc(v) if v else "—") for k, v in org)
    blocks.append('<div class="block"><h3>Organisation</h3><div class="meta">%s</div></div>' % org_html)
    src = ""
    if e.get("source_url"):
        src += '<li><a href="%s" rel="noopener">%s</a></li>' % (esc(e["source_url"]), esc(e.get("source_name") or e["source_url"]))
    else:
        src += '<li>%s</li>' % esc(e.get("source_name") or "—")
    if e.get("ticket_url"):
        src += '<li><a href="%s" rel="noopener">Billetterie / inscription</a></li>' % esc(e["ticket_url"])
    extra = ""
    if conflicts:
        extra += '<p style="margin:10px 0 0"><b style="color:var(--danger)">Contradictions entre sources :</b> %s</p>' % esc(conflicts)
    if notes:
        extra += '<p style="margin:6px 0 0"><b>Signaux et lacunes :</b> %s</p>' % esc(notes)
    blocks.append('<div class="block"><h3>Sources</h3><ul>%s</ul>%s</div>' % (src, extra))
    return '<div class="grid2">%s</div>' % "".join(blocks)


def events_table(events, with_details=True, sortable=True, prefix=""):
    rows = []
    for i, e in enumerate(events):
        rows.append(event_row(e, i, prefix=prefix))
        if with_details:
            rows.append('<tr class="detail hide" data-d="%d"><td colspan="8">%s</td></tr>'
                        % (i, detail_block(e)))
    return "<table>\n%s\n</table>" % ("\n".join(rows))


# --------------------------------------------------------------------------
# ecriture
# --------------------------------------------------------------------------

def write(path, content):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)


def build():
    if os.path.isdir(SITE):
        for root, dirs, files in os.walk(SITE, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                p = os.path.join(root, d)
                if p != SITE:
                    os.rmdir(p)
    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)

    with open(os.path.join(SITE, "assets", "site.css"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(CSS)
    with open(os.path.join(SITE, "assets", "tracker.js"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(TRACKER_JS)

    # ---- favicon et visuels de partage ---------------------------------
    make_favicon(os.path.join(SITE, "assets", "favicon.png"),
                 os.path.join(SITE, "assets", "favicon.svg"))
    make_og_image(os.path.join(SITE, "assets", "og-default.png"),
                  "Les événements immobiliers de l'Afrique, vérifiés",
                  "Dates, lieux et sources — avec le statut de confirmation de chaque rendez-vous.")
    for e in EVENTS:
        sub = " · ".join([x for x in [
            fmt_range_fr(e.get("start"), e.get("end")),
            e.get("city", ""), e.get("country", "")] if x])
        make_og_image(os.path.join(SITE, "assets", "og", "%s.png" % slugify(e["name"])),
                      e.get("name") or "Événement", sub)
    for country, evs in REAL_COUNTRIES.items():
        make_og_image(os.path.join(SITE, "assets", "og", "pays-%s.png" % slugify(country)),
                      "Événements immobiliers — %s" % country,
                      "%d rendez-vous sur l'horizon 2026-2027, dates et sources." % len(evs))

    # ---- index : tracker pre-rendu -------------------------------------
    cats = sorted({e["category"] for e in EVENTS})
    stats = sorted({e["status"] for e in EVENTS})
    zones = sorted({e["zone"] for e in EVENTS if e.get("zone")})

    opts_cat = "".join('<option value="%s">%s</option>' % (esc(c), esc(CATEGORY_LABEL.get(c, c))) for c in cats)
    opts_status = "".join('<option value="%s">%s</option>' % (esc(s), esc(STATUS_LABEL.get(s, s))) for s in stats)
    # Le filtre propose aussi les evenements dont le pays n'est pas confirme :
    # les cacher rendrait impossible de les trouver, or ils sont dans l'agenda.
    filter_countries = sorted(REAL_COUNTRIES) + ([UNKNOWN] if ORPHAN_EVENTS else [])
    opts_country = "".join('<option value="%s">%s</option>' % (esc(c), esc(c))
                           for c in filter_countries)
    opts_zone = "".join('<option value="%s">%s</option>' % (esc(z), esc(z)) for z in zones)

    dated = [e for e in EVENTS if e.get("start")]
    to_confirm = [e for e in EVENTS if e.get("status") == "to_confirm"]
    conflicts = [e for e in EVENTS if e.get("has_conflict")]

    body = """
<main>
 <div class="wrap">
  <p class="eyebrow">Suivi de marché · Afrique</p>
  <h1>Agenda des événements immobiliers en Afrique — 2026-2027</h1>
  <p class="lede">Un agenda de travail destiné aux investisseurs et financiers. Les dates non
  confirmées sont signalées explicitement&nbsp;: vérifiez toujours sur le site officiel avant de
  déplacer ou de payer. Chaque fiche indique sa source et les contradictions entre sources.</p>

  <div class="stats">
   <div class="stat"><b>%d</b><span>événements retenus</span></div>
   <div class="stat"><b>%d</b><span>datés</span></div>
   <div class="stat"><b>%d</b><span>date à confirmer</span></div>
   <div class="stat"><b>%d</b><span>avec conflit de sources</span></div>
   <div class="stat"><b>%d</b><span>pays couverts</span></div>
  </div>

  <p class="meta" style="margin:-12px 0 20px">Dernière vérification&nbsp;: %s —
  <a href="changelog.html">voir le journal des changements</a> ·
  <a href="a-propos.html">à propos de cet agenda et de sa ligne éditoriale</a></p>

  <div class="notice"><b>Périmètre.</b> Uniquement les événements organisés sur le continent
  africain. Les rendez-vous organisés hors d'Afrique (Dubaï, Londres, New York) et les expos de la
  diaspora sont exclus, même s'ils portent sur l'immobilier africain. Filtre d'inclusion&nbsp;:
  à moins deux des six critères (audience décisionnelle, échelle, substance, continuité, influence,
  portée). <a href="methodologie.html">La méthode en détail</a>.</div>

  %s

  <div class="chips">
   %s
  </div>
  <div class="toolbar">
   <input type="search" id="q" placeholder="Rechercher un événement, une ville, un organisateur, un thème…">
   <select id="f-cat"><option value="">Toutes catégories</option>%s</select>
   <select id="f-status"><option value="">Tous les statuts</option>%s</select>
   <select id="f-country"><option value="">Tous les pays</option>%s</select>
   <select id="f-zone"><option value="">Toutes les zones</option>%s</select>
   <select id="f-score"><option value="0">Score investisseur ≥ 0</option>
    <option value="3">≥ 3</option><option value="4">≥ 4</option><option value="5">= 5</option></select>
   <button class="btn" id="reset">Réinitialiser</button>
   <a class="btn" href="agenda-immobilier-afrique.csv">CSV</a>
   <a class="btn" href="agenda-immobilier-afrique.ics">ICS</a>
   <span class="count"><b id="shown">%d</b> / <span id="total">%d</span> affichés</span>
  </div>

  %s
  <div class="empty hide" id="empty">Aucun événement ne correspond aux filtres.</div>

  %s
 </div>
</main>
""" % (
        len(EVENTS), len(dated), len(to_confirm), len(conflicts), len(REAL_COUNTRIES),
        fmt_gen_date(payload.get("generated", "")),
        sponsor_slot(),
        "".join('<a class="chip" href="pays/%s.html">%s</a>' % (slugify(c), esc(c)) for c in sorted(REAL_COUNTRIES)),
        opts_cat, opts_status, opts_country, opts_zone,
        len(EVENTS), len(EVENTS),
        events_table(EVENTS),
        sponsor_slot("Emplacement partenaire — soutien à la vérification continue des dates"),
    )
    write("index.html", page(
        "Agenda des événements immobiliers en Afrique 2026-2027",
        "Agenda vérifié des événements immobiliers en Afrique pour investisseurs et financiers : "
        "%d événements dans %d pays, avec le statut de date de chaque rendez-vous et ses sources."
        % (len(EVENTS), len(REAL_COUNTRIES)),
        body,
        og_image="assets/og-default.png",
        og_title="Agenda des événements immobiliers en Afrique 2026-2027",
        canonical="index.html",
        jsonld={
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Agenda des événements immobiliers en Afrique",
            "url": abs_url("index.html"),
            "inLanguage": "fr",
            "description": "Agenda vérifié des événements immobiliers en Afrique.",
        }))

    # tracker JS injecte a la fin de index.html
    idx_path = os.path.join(SITE, "index.html")
    with open(idx_path, "r", encoding="utf-8") as fh:
        html = fh.read()
    html = html.replace("</body>", '<script src="assets/tracker.js"></script>\n</body>')
    with open(idx_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(html)

    # ---- pages par evenement -------------------------------------------
    og_made = []
    by_country = {}
    for e in EVENTS:
        by_country.setdefault(e["country"], []).append(e)

    for e in EVENTS:
        slug = slugify(e["name"])
        prefix = "../"
        country_link = ""
        if e.get("country") and e["country"] != UNKNOWN:
            country_link = (' · <a href="%spays/%s.html">Autres événements en %s</a>'
                            % (prefix, slugify(e["country"]), esc(e["country"])))
        related_same_country = [x for x in by_country.get(e["country"], []) if x is not e][:8]
        related_same_cat = [x for x in EVENTS
                            if x.get("category") == e.get("category") and x is not e][:6]
        related = []
        for x in related_same_country + related_same_cat:
            if x not in related:
                related.append(x)
        related = related[:8]

        rel_html = ""
        if related:
            items = "".join(
                '<li><a href="%s">%s</a> <span class="muted">— %s</span></li>'
                % (slugify(x["name"]) + ".html", esc(x["name"]), esc(x.get("display_date", "")))
                for x in related)
            rel_html = '<h3>Événements proches</h3><ul class="meta">%s</ul>' % items

        conflict_block = ""
        if e.get("conflicts"):
            conflict_block = ('<div class="notice"><b>Contradictions entre sources.</b> %s</div>'
                              % esc(e["conflicts"]))
        if e.get("notes"):
            conflict_block += ('<div class="notice"><b>Signaux et lacunes.</b> %s</div>'
                               % esc(e["notes"]))

        # Lien de billetterie : quand l'organisateur publie une URL de vente,
        # elle est affichee telle quelle — c'est la seule source d'inscription
        # verifiee pour l'evenement.
        cta_row = ""
        if e.get("ticket_url"):
            cta_row = ('<p class="cta-row"><a class="btn" href="%s" rel="noopener" target="_blank">'
                       'Billetterie / inscription</a>'
                       '<span class="cta-note">lien de l\'organisateur, non verifie pour le tarif</span></p>'
                       % esc(e["ticket_url"]))

        # Bloc « Sources » : la source principale, la billetterie, et les sources
        # reellement citees dans l'arbitrage. Les URL viennent du registre des
        # pages consultees ; un domaine cite sans page referencee reste en
        # clair, il n'est jamais transforme en lien devine.
        src_items = []
        if e.get("source_url"):
            src_items.append('<li><a href="%s" rel="noopener" target="_blank">%s</a></li>'
                             % (esc(e["source_url"]), esc(e.get("source_name") or e["source_url"])))
        elif e.get("source_name"):
            src_items.append("<li>%s</li>" % esc(e["source_name"]))
        if e.get("ticket_url") and e["ticket_url"] != e.get("source_url"):
            src_items.append('<li><a href="%s" rel="noopener" target="_blank">Billetterie / inscription</a>'
                             ' <span class="muted">%s</span></li>'
                             % (esc(e["ticket_url"]), esc(host_of(e["ticket_url"]))))
        for s in e.get("cited_sources") or []:
            src_items.append('<li><a href="%s" rel="noopener" target="_blank">%s</a>'
                             ' <span class="muted">%s</span></li>'
                             % (esc(s.get("url") or ""), esc(s.get("name") or ""),
                                esc(fmt_date_fr(s.get("accessed") or ""))))
        src_items = "".join(src_items) or "<li>—</li>"

        unlinked = e.get("cited_unlinked") or []
        cited_note = ""
        if unlinked:
            cited_note = ('<p class="meta muted" style="margin-top:8px">Domaines cités dans '
                          'l\'arbitrage, sans page de référence publiée ici : %s</p>'
                          % esc(", ".join(unlinked)))

        body_ev = """
<main><div class="wrap">
 <p class="eyebrow">%s · %s</p>
 <div class="event-hero">
  <h1>%s</h1>
  <div class="pill-row">%s %s</div>
  <p class="lede" style="margin-bottom:0">%s</p>
  <dl class="kv">
   <div><dt>Date</dt><dd>%s</dd></div>
   <div><dt>Statut de la date</dt><dd>%s</dd></div>
   <div><dt>Ville</dt><dd>%s</dd></div>
   <div><dt>Pays</dt><dd>%s</dd></div>
   <div><dt>Lieu</dt><dd>%s</dd></div>
   <div><dt>Organisateur</dt><dd>%s</dd></div>
   <div><dt>Échelle</dt><dd>%s</dd></div>
   <div><dt>Score investisseur</dt><dd>%s</dd></div>
   <div><dt>Vérifié le</dt><dd>%s</dd></div>
  </dl>
%s
 </div>

 %s

 <h2>Pourquoi un investisseur devrait s'y rendre</h2>
 <div class="grid2">
  <div class="block"><h3>Pertinence</h3><p>%s</p></div>
  <div class="block"><h3>Acteurs du capital</h3><p>%s</p></div>
  <div class="block"><h3>Thèmes</h3><p>%s</p></div>
  <div class="block"><h3>Sources</h3><ul class="meta">%s</ul>%s</div>
 </div>

 %s
 %s
 %s
 %s
 <p><a href="%sindex.html">← Retour à l'agenda complet</a>%s</p>
</div></main>
""" % (
            esc(e.get("category_label") or ""), esc(e.get("country") or ""),
            esc(e.get("name") or ""),
            category_badge(e.get("category", "")), status_badge(e.get("status", "")),
            esc(e.get("why") or ""),
            esc(fmt_range_fr(e.get("start"), e.get("end"))),
            status_badge(e.get("status", "")),
            esc(e.get("city") or ""), esc(e.get("country") or ""),
            esc(e.get("venue") or "—"), esc(e.get("organizer") or "—"),
            esc(" · ".join(x for x in [e.get("attendees") or "", e.get("exhibitors") or ""] if x) or "—")
            + ('<br><span class="muted" style="font-size:11px">chiffres de l\'organisateur, non audités</span>'
               if (e.get("attendees") or e.get("exhibitors")) else ""),
            score_bars(e.get("score", 0)),
            esc(fmt_date_fr(e.get("last_verified")) or e.get("last_verified") or "—"),
            cta_row,
            conflict_block,
            esc(e.get("why") or "—"),
            esc(e.get("actors") or "—"),
            esc(e.get("themes") or "—"),
            src_items,
            cited_note,
            share_buttons(page_canonical("evenements/%s.html" % slug, prefix),
                          "%s — %s" % (e.get("name", ""), fmt_range_fr(e.get("start"), e.get("end")))),
            '<p class="meta"><a href="%scontribuer.html">Une erreur sur cette fiche&nbsp;? Signalez-la</a> '
            '— la correction est tracée dans le journal des changements.</p>' % prefix,
            sponsor_slot(prefix=prefix),
            rel_html,
            prefix,
            country_link,
        )
        ev_url = page_canonical("evenements/%s.html" % slug, prefix)
        write("evenements/%s.html" % slug, page(
            "%s — %s" % (e.get("name", ""), fmt_range_fr(e.get("start"), e.get("end"))),
            "%s : %s, %s. %s" % (e.get("name", ""), fmt_range_fr(e.get("start"), e.get("end")),
                                 e.get("country", ""), clip(e.get("why"), 140)),
            body_ev, prefix="../",
            og_image="assets/og/%s.png" % slug,
            og_title="%s — %s" % (e.get("name", ""), fmt_range_fr(e.get("start"), e.get("end"))),
            og_type="article",
            canonical="evenements/%s.html" % slug,
            jsonld=event_jsonld(e, ev_url)))

    # ---- pages par pays -------------------------------------------------
    for country, evs in REAL_COUNTRIES.items():
        slug = slugify(country)
        prefix = "../"
        by_q = {}
        for e in evs:
            by_q.setdefault(quarter_of(e.get("start")) or "Sans date", []).append(e)
        sections = ""
        for q_label in sorted(by_q, key=lambda x: (x == "Sans date", x)):
            items = "".join(
                '<tr><td class="date-cell">%s</td><td><a href="../evenements/%s.html">%s</a>%s</td>'
                '<td>%s</td><td>%s</td><td class="hide-sm">%s</td></tr>'
                % (esc(fmt_range_fr(x.get("start"), x.get("end"))),
                   slugify(x["name"]), esc(x["name"]),
                   ('<span class="ev-edition">%s</span>' % esc(x["edition"])) if x.get("edition") else "",
                   status_badge(x.get("status", "")),
                   category_badge(x.get("category", "")),
                   score_bars(x.get("score", 0)))
                for x in by_q[q_label])
            sections += ('<h3>%s</h3><table><thead><tr><th>Date</th><th>Événement</th>'
                         '<th>Statut</th><th>Catégorie</th><th class="hide-sm">Score</th></tr></thead>'
                         '<tbody>%s</tbody></table>' % (esc(q_label), items))

        warning = ""
        if len(evs) <= 2:
            warning = ('<div class="notice"><b>Couverture faible.</b> Seulement %d événement(s) '
                       'documenté(s) pour ce pays sur l\'horizon. Les sources publiques y sont rares : '
                       'si vous connaissez un rendez-vous local, <a href="%scontribuer.html">signalez-le</a>.'
                       '</div>' % (len(evs), prefix))

        prefix = "../"
        prefix = "../"
        body_co = """
<main><div class="wrap">
 <p class="eyebrow">Par pays</p>
 <h1>Événements immobiliers — %s</h1>
 <p class="lede">%d événement(s) retenu(s) sur l'horizon novembre 2026 – décembre 2027, avec le
 statut de date et les sources. Les événements sans date sont annoncés mais pas encore fixées.</p>
 %s
 <div class="stats">
  <div class="stat"><b>%d</b><span>événements</span></div>
  <div class="stat"><b>%d</b><span>datés</span></div>
  <div class="stat"><b>%d</b><span>à confirmer</span></div>
 </div>
 %s
 %s
 %s
 <p><a href="%sindex.html">← Agenda complet</a> ·
 <a href="%scontribuer.html">Signaler un événement manquant</a></p>
</div></main>
""" % (
            esc(country), len(evs), warning,
            len(evs), len([x for x in evs if x.get("start")]),
            len([x for x in evs if x.get("status") == "to_confirm"]),
            sections,
            '<div class="chips">%s</div>' % "".join(
                '<a class="chip" href="%s.html">%s</a>' % (slugify(c), esc(c))
                for c in sorted(REAL_COUNTRIES) if c != country),
            sponsor_slot(prefix=prefix),
            prefix, prefix,
        )
        write("pays/%s.html" % slug, page(
            "Événements immobiliers en %s — 2026-2027" % country,
            "Agenda des événements immobiliers en %s : %d rendez-vous vérifiés, dates, lieux, "
            "sources et statut de confirmation." % (country, len(evs)),
            body_co, prefix="../",
            og_image="assets/og/pays-%s.png" % slug,
            og_title="Événements immobiliers en %s — 2026-2027" % country,
            og_type="article",
            canonical="pays/%s.html" % slug))

    # ---- a propos -------------------------------------------------------
    about_body = """
<main><div class="wrap">
 <p class="eyebrow">À propos</p>
 <h1>Qui fait quoi, et dans quelles conditions</h1>
 <p class="lede">Un agenda immobilier africain n'a de valeur que si l'on sait qui l'a construit, avec
 quelles sources, et ce qu'il se passe quand une information est fausse. Cette page répond aux trois.</p>

 <h2>La ligne éditoriale</h2>
 <p>Un événement n'entre dans cet agenda que s'il est susceptible d'être pertinent pour quelqu'un
 qui décide d'y engager de l'argent : un investisseur, un financier, un promoteur, un conseil.
 Les salons de preuves, les événements lifestyle, les manifestations à audience grand public et les
 rendez-vous organisés hors d'Afrique sont exclus — cette dernière exclusion étant la plus
 discutable, et c'est pourquoi <a href="methodologie.html">la méthode</a> l'explique en détail.</p>

 <h2>Les sources</h2>
 <div class="grid2">
  <div class="block"><h3>Primaires</h3><p>La page de l'organisateur, la billetterie officielle, la
  page de l'événement sur la plateforme de billetterie. C'est la source qui fait foi pour la date
  et le lieu.</p></div>
  <div class="block"><h3>Secondaires</h3><p>La presse sectorielle, les portails d'agenda, les
  associations professionnelles. Utilisées pour recouper, et pour signaler une divergence.</p></div>
  <div class="block"><h3>Chiffres</h3><p>Les effectifs affichés sont ceux publiés par
  l'organisateur et ne sont pas audités. Ils sont signalés comme tels sur chaque fiche.</p></div>
  <div class="block"><h3>Ce que nous ne faisons pas</h3><p>Nous ne payment pas pour figurer dans
  l'agenda, et l'emplacement partenaire ne conditionne aucune mention d'événement. La seule
  influence possible d'un partenaire est sur l'emplacement, jamais sur la sélection.</p></div>
 </div>

 <h2>Politique de correction</h2>
 <p>Les événements se déplacent. Un agenda qui ne le dit pas devient un piège. La règle est simple&nbsp;:</p>
 <ol class="meta">
  <li>Une erreur constatée est corrigée et inscrite dans le
  <a href="changelog.html">journal des changements</a>, avec la date de correction et l'ancienne
  valeur.</li>
  <li>Les dates sont recontrôlées contre les pages officielles au moins une fois par mois&nbsp;;
  les corrections issues de ce contrôle sont tracées de la même façon.</li>
  <li>Quand deux sources se contredisent et que l'arbitrage n'est pas certain, la contradiction est
  <b>conservée et affichée</b> sur la fiche, avec les deux versions et leurs sources. Elle n'est
  jamais lissée.</li>
  <li>Une fiche porte toujours la date de sa dernière vérification.</li>
 </ol>
 <p><b>Signaler une erreur&nbsp;:</b> le <a href="contribuer.html">formulaire</a> sert aussi à cela.
 Un événement qui n'a pas sa place, ou une date fausse, se signalent de la même façon.</p>

 <h2>Ce que l'agenda ne couvre pas</h2>
 <p>Un agenda exhaustif sur %d pays n'existe pas, et n'existera pas tout de suite : dans de nombreux
 pays, l'information n'est pas publiée en ligne. Les zones où rien n'a été trouvé sont
 <b>documentées publiquement</b> dans la <a href="methodologie.html">méthodologie</a> plutôt que
 passées sous silence — c'est le point de départ du formulaire de contribution.</p>

 <h2>Contact</h2>
 <p>Pour une question, une correction, ou une demande de partenariat&nbsp;:
 <a href="mailto:%s">%s</a>.</p>

 %s
 <p><a href="index.html">← Agenda complet</a></p>
</div></main>
""" % (AFRICA_TOTAL, esc(CONTACT_EMAIL), esc(CONTACT_EMAIL),
       sponsor_slot("Soutenez la vérification continue des dates"))
    write("a-propos.html", page(
        "À propos — agenda des événements immobiliers en Afrique",
        "Ligne éditoriale, sources, politique de correction et zones non couvertes de l'agenda "
        "des événements immobiliers en Afrique.",
        about_body,
        canonical="a-propos.html",
        og_type="article"))

    # ---- methodologie ---------------------------------------------------
    method_body = """
<main><div class="wrap">
 <p class="eyebrow">Méthodologie</p>
 <h1>Comment cet agenda est construit</h1>
 <p class="lede">Un agenda d'événements immobiliers qui se contente de lister ne vaut rien : les
 sources se contredisent, les dates changent, et le bruit est énorme. Cette page décrit les règles
 appliquées, afin que chaque ligne puisse être auditée.</p>

 <h2>Le filtre « 2 sur 6 »</h2>
 <p>Un événement n'est retenu que s'il coche <b>au moins deux</b> de ces six critères&nbsp;:</p>
 <div class="grid2">
  <div class="block"><h3>1 · Audience décisionnelle</h3><p>Investisseurs, financiers, fonds, banques,
  institutions, décideurs publics. Ce qui exclut le grand public.</p></div>
  <div class="block"><h3>2 · Échelle</h3><p>~500+ participants, ou 30+ exposants, ou statut de
  flagship national ou régional. Ce qui exclut les petits séminaires.</p></div>
  <div class="block"><h3>3 · Substance</h3><p>Logement, foncier, marchés de capitaux, capital
  institutionnel, financement, rendements. Ce qui exclut les salons lifestyle.</p></div>
  <div class="block"><h3>4 · Continuité</h3><p>3ᵉ édition ou plus, ou rendez-vous annuel ancré et
  stable. Ce qui exclut les one-shot.</p></div>
  <div class="block"><h3>5 · Influence</h3><p>Ministres, banques centrales, DFIs, fonds de pension,
  REITs, private equity, grandes banques présents ou annoncés.</p></div>
  <div class="block"><h3>6 · Portée</h3><p>Multi-pays ou nationale majeure. Ce qui exclut les salons
  de ville.</p></div>
 </div>
 <p>Ce qui ne coche qu'un seul critère est écarté — et consigné avec sa raison. C'est ce qui rend le
 résultat défendable&nbsp;: on sait ce qui a été écarté et pourquoi.</p>

 <h2>Les statuts de date</h2>
 <div class="grid2">
  <div class="block"><h3>Date confirmée</h3><p>Trouvée sur la page officielle de l'événement et
  recoupée par une seconde source.</p></div>
  <div class="block"><h3>Date probable</h3><p>Cohérente, mais une seule source, ou des sources qui
  divergent sur le jour ou le lieu.</p></div>
  <div class="block"><h3>Date à confirmer</h3><p>Événement annoncé sans date fiable. À revérifier
  avant tout engagement.</p></div>
  <div class="block"><h3>Contradiction / signalement</h3><p>Une contradiction entre sources est
  conservée et tracée ; une simple lacune d'information est signalée séparément.</p></div>
 </div>

 <h2>Ce qui est exclu, et pourquoi</h2>
 <div class="grid2">
  <div class="block"><h3>Hors du continent</h3><p>Les rendez-vous organisés hors d'Afrique — Dubaï,
  Londres, New York — et les expos de la diaspora, même s'ils portent sur l'immobilier africain.
  Une part importante du capital se mobilise là, et c'est précisément pourquoi il faut le savoir :
  l'agenda les signale comme exclus.</p></div>
  <div class="block"><h3>Adjacent construction</h3><p>Les salons de construction et de matériaux ne
  sont pas des événements immobiliers, mais ils pèsent sur la faisabilité et la marge des projets.
  Ils sont isolés avec un filtre plus strict : présence de promoteurs ou d'investisseurs, un track
  « real estate », ou une dimension panafricaine.</p></div>
 </div>

 <h2>La vérification continue</h2>
 <p>Un agenda publié une fois est un document mort. Les dates sont recontrôlées périodiquement
  contre les pages officielles&nbsp;: le script de rafraîchissement relit chaque source, compare les
  dates trouvées et signale les écarts, sans jamais modifier les données à l'insu du lecteur. Le
  <a href="changelog.html">journal des changements</a> conserve la trace de chaque écart.</p>

 <h2>Les zones à blanc</h2>
 <p>L'agenda ne couvre pas uniformément le continent, et il le dit. %d mentions d'information
 introuvable ou d'événement écarté sont tracées dans les fichiers de données.</p>
 <ul class="meta">%s</ul>

 %s
 <p><a href="index.html">← Agenda complet</a></p>
</div></main>
""" % (
        len(negative),
        "".join('<li><b>%s</b> — %s</li>' % (esc(z), esc(n)) for z, n in negative[:80]),
        sponsor_slot("Soutenez la vérification continue des dates"),
    )
    write("methodologie.html", page(
        "Méthodologie — agenda des événements immobiliers en Afrique",
        "Filtre d'inclusion, statuts de date, exclusions et méthode de vérification continue "
        "de l'agenda des événements immobiliers en Afrique.",
        method_body,
        canonical="methodologie.html",
        og_type="article"))

    # ---- changelog ------------------------------------------------------
    entries = []
    for c in CHANGELOG:
        entries.append(
            '<li><time datetime="%s">%s</time><p><b>%s</b></p><p class="meta">%s</p></li>'
            % (esc(c.get("date", "")), esc(c.get("date_display", "")), esc(c.get("title", "")),
               esc(c.get("detail", "")))
        )
    if not entries:
        entries.append('<li><p class="muted">Aucune modification enregistrée pour l\'instant.</p></li>')
    cl_body = """
<main><div class="wrap">
 <p class="eyebrow">Journal</p>
 <h1>Journal des changements</h1>
 <p class="lede">Ce qui bouge dans l'agenda : dates corrigées, lieux modifiés, événements ajoutés
 ou retirés. C'est la partie qui justifie de revenir — un agenda ne vaut que s'il vous prévient
 qu'il a changé.</p>
 <ul class="changes">%s</ul>
 %s
 <p><a href="index.html">← Agenda complet</a> ·
 <a href="feed.xml">Flux RSS</a></p>
</div></main>
""" % ("\n".join(entries), sponsor_slot())
    write("changelog.html", page(
        "Journal des changements — agenda immobilier Afrique",
        "Historique des corrections de dates, de lieux et d'ajouts dans l'agenda des événements "
        "immobiliers en Afrique.",
        cl_body,
        canonical="changelog.html",
        og_type="article"))

    # ---- sponsors --------------------------------------------------------
    sponsor_body = """
<main><div class="wrap">
 <p class="eyebrow">Partenaires</p>
 <h1>Emplacement partenaire</h1>
 <p class="lede">L'agenda est gratuit et sans publicité programmatique. Un seul emplacement, en
 haut de page et sur les fiches événement, est réservé à un partenaire — de préférence un acteur du
 marché immobilier africain qui veut être identifié là où les investisseurs préparent leurs
 déplacements.</p>

 <h2>Ce que l'emplacement apporte</h2>
 <div class="grid2">
  <div class="block"><h3>Audience qualifiée</h3><p>Des investisseurs, financiers, courtiers et
  promoteurs qui consultent l'agenda avant de réserver un vol et de payer une billet.</p></div>
  <div class="block"><h3>Placement contextuel</h3><p>Bannière en en-tête de l'agenda, sur les pages
  pays et sur chaque fiche événement. La marque est associée à l'information, pas à un bandeau
  générique.</p></div>
  <div class="block"><h3>Visibilité des données</h3><p>Un lien sortant depuis une page qui parle
  d'un pays, d'une ville ou d'un événement précis. Les pages pays et événement sont les points
  d'entrée naturels d'une campagne de marque.</p></div>
  <div class="block"><h3>Newsletter</h3><p>Mention partenaire dans le récapitulatif hebdomadaire
  des changements, qui est le format le plus lu.</p></div>
 </div>

 <h2>Partenaires ciblés</h2>
 <ul class="meta">
  <li>Banques et institutions de financement immobilier présentes en Afrique</li>
  <li>Cabinets d'avocats et de conseil en capital marché sur le continent</li>
  <li>Fournisseurs de données immobilières et de recherche (valuation, indices)</li>
  <li>Associations de promoteurs et d'organisateurs de salons</li>
  <li>Assureurs, fonds et acteurs du titre foncier, proptech</li>
 </ul>

 <h2>Formats et tarifs</h2>
 <div class="grid2">
  <div class="block"><h3>Bannière d'agenda</h3><p>En-tête de la page d'accueil, visible sur
  toutes les pages. Format 1200×120, newsletter 300×100, mention dans le récapitulatif
  hebdomadaire. <b>Tarifs sur demande</b> —par an.</p></div>
  <div class="block"><h3>Fiche partenaire</h3><p>Un bloc dédié sur les %d pages pays et les %d
  fiches événement, positionné sur les événements de votre marché. Format 300×250, texte libre.
  <b>Tarifs sur demande</b> —par an.</p></div>
  <div class="block"><h3>Parrainage d'un pays</h3><p>Vous sponsorisez la page d'un pays
  (Kenya, Ghana, Côte d'Ivoire…) et vous êtes cité comme partenaire de couverture sur les
  événements qui y figurent. <b>Tarifs sur demande</b> —par an.</p></div>
  <div class="block"><h3>Parrainage du journal</h3><p>Votre mention dans le récapitulatif
  hebdomadaire des changements, le format le plus lu. <b>Tarifs sur demande</b> —par an.</p></div>
 </div>
 <p class="meta">Les tarifs sont indicatifs et donnes sur devis selon le périmètre. L'emplacement
 n'achète jamais une mention d'événement : la sélection reste indépendante du financement.</p>

 %s
 <p><a href="index.html">← Agenda complet</a> ·
 <a href="a-propos.html">Ligne éditoriale et politique de correction</a></p>
</div></main>
""" % (len(REAL_COUNTRIES), len(EVENTS), sponsor_slot("Votre marque ici"))
    write("sponsors.html", page(
        "Partenaires — agenda immobilier Afrique",
        "Emplacement partenaire disponible sur l'agenda des événements immobiliers en Afrique : "
        "audience qualifiée d'investisseurs et de financiers.",
        sponsor_body,
        canonical="sponsors.html"))

    # ---- contribuer ------------------------------------------------------
    from urllib.parse import quote
    signal_subject = quote("Signalement - Agenda immobilier Afrique")
    signal_mailto = "mailto:%s?subject=%s" % (CONTACT_EMAIL, signal_subject)
    contribute_body = """
<main><div class="wrap">
 <p class="eyebrow">Contribution</p>
 <h1>Signaler un événement</h1>
 <p class="lede">L'agenda ne couvre pas uniformément le continent&nbsp;: %d pays n'ont aujourd'hui
 aucun rendez-vous immobilier institutionnel documenté. Si vous connaissez un salon, un sommet ou
 une conférence sur votre marché, le signaler prend deux minutes et élargit la carte.</p>

 <h2>Ce qu'il faut fournir</h2>
 <div class="grid2">
  <div class="block"><h3>Minimum utile</h3><ul class="meta">
   <li>Nom exact de l'événement</li>
   <li>Date (ou « à confirmer »)</li>
   <li>Ville et pays</li>
   <li>Lien vers la page officielle</li>
  </ul></div>
  <div class="block"><h3>Utile en plus</h3><ul class="meta">
   <li>Édition (2ᵉ, 3ᵉ…)</li>
   <li>Lieu et salle</li>
   <li>Organisateur</li>
   <li>Effectif attendu, exposants</li>
   <li>Présence attendue de fonds, DFIs, banques, ministres</li>
   <li>Site de billetterie</li>
  </ul></div>
 </div>

 <h2>Formulaire</h2>
 <p>Le dispositif d'intake est adossé à une feuille de travail&nbsp;: chaque signalement crée une
 ligne, et chaque ligne est fusionnée dans l'agenda après vérification de la date et du statut de
 confirmation.</p>

 <div class="notice" id="form-slot">
  <b>Le formulaire est en cours de mise en place.</b> L'intake arrive&nbsp;: chaque signalement
  créera une ligne dans une feuille de travail, et chaque ligne sera vérifiée — date recoupée,
  statut de confirmation arbitré — avant d'entrer dans l'agenda.
  <br><br>
  En attendant, la <a href="methodologie.html">méthodologie</a> publie la liste des
  %d pays qui n'ont aujourd'hui aucun rendez-vous immobilier institutionnel documenté&nbsp;:
  c'est là que votre signalement compte le plus.
  <br><br>
  Vous connaissez un salon, un sommet ou une conférence sur votre marché&nbsp;? Un email
  suffit pour l'instant&nbsp;:
  <a href="%s">%s</a>.
  Le nom exact de l'événement, la date, la ville, le pays et le lien de la page officielle
  suffisent&nbsp;; le reste est vérifié de notre côté.
 </div>

 <h2>Comment votre signalement est traité</h2>
 <ol class="meta">
  <li>La fiche rejoint la file de vérification, avec son statut « à confirmer ».</li>
  <li>La date est croisée avec la page officielle de l'organisateur, et avec au moins une seconde
  source quand c'est possible.</li>
  <li>Si les sources divergent, l'événement est publié avec un statut « date probable » et le
  conflit est tracé sur la fiche — il n'est pas masqué.</li>
  <li>L'événement passe ensuite le filtre « 2 sur 6 » : audience décisionnelle, échelle, substance,
  continuité, influence, portée. S'il n'en coche pas deux, il est écarté avec la raison, et vous en
  êtes informé.</li>
 </ol>

 %s
 <p><a href="index.html">← Agenda complet</a></p>
</div></main>
""" % (UNCOVERED_COUNTRIES, UNCOVERED_COUNTRIES,
       esc(signal_mailto), esc(CONTACT_EMAIL), sponsor_slot())
    write("contribuer.html", page(
        "Signaler un événement — agenda immobilier Afrique",
        "Formulaire de contribution à l'agenda des événements immobiliers en Afrique : "
        "aidez à couvrir les %d pays où aucun rendez-vous n'est documenté." % UNCOVERED_COUNTRIES,
        contribute_body,
        canonical="contribuer.html",
        og_type="article"))

    # ---- flux RSS, sitemap, robots ---------------------------------------
    rss_items = []
    for c in CHANGELOG[:40]:
        rss_items.append(
            "<item><title>%s</title><pubDate>%s</pubDate>"
            "<description>%s</description></item>"
            % (esc(c.get("title", "")), esc(c.get("date", "")), esc(c.get("detail", "")))
        )
    rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>Journal des changements — agenda immobilier Afrique</title>
<link>changelog.html</link>
<description>Corrections de dates et ajouts dans l'agenda des événements immobiliers en Afrique.</description>
<language>fr</language>
%s
</channel></rss>
""" % "\n".join(rss_items)
    write("feed.xml", rss)

    urls = [("index.html", "1.0"), ("methodologie.html", "0.8"), ("changelog.html", "0.8"),
            ("a-propos.html", "0.7"), ("sponsors.html", "0.5"), ("contribuer.html", "0.5")]
    for e in EVENTS:
        urls.append(("evenements/%s.html" % slugify(e["name"]), "0.7"))
    for c in REAL_COUNTRIES:
        urls.append(("pays/%s.html" % slugify(c), "0.8"))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, prio in urls:
        sm.append("  <url><loc>%s</loc><priority>%s</priority></url>"
                  % (esc(abs_url(path)), prio))
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm))

    robots = "User-agent: *\nAllow: /\n"
    if SITE_URL:
        robots += "Sitemap: %s\n" % abs_url("sitemap.xml")
    else:
        robots += "# SITE_URL non defini : decommentez la ligne ci-dessous au deploiement\n"
        robots += "# Sitemap: https://ton-domaine/sitemap.xml\n"
    write("robots.txt", robots)

    # ---- copies des exports ---------------------------------------------
    for fn in ("agenda-immobilier-afrique.csv", "agenda-immobilier-afrique.ics",
               "refresh-report.csv"):
        src = os.path.join(EXPORT, fn)
        if os.path.exists(src):
            with open(src, "rb") as r, open(os.path.join(SITE, fn), "wb") as w:
                w.write(r.read())

    print("Site genere dans %s" % SITE)
    print("  index.html            tracker pre-rendu (%d lignes)" % len(EVENTS))
    print("  evenements/           %d pages" % len(EVENTS))
    print("  pays/                 %d pages" % len(REAL_COUNTRIES))
    print("  methodologie.html, changelog.html, a-propos.html, sponsors.html, contribuer.html")
    print("  feed.xml, sitemap.xml, robots.txt")
    print("  total : %d fichiers html" % (1 + len(EVENTS) + len(REAL_COUNTRIES) + 5))

    # ---- ce qui manque pour une mise en ligne reelle ---------------------
    blocking = []
    advisory = []
    if not SITE_URL:
        blocking.append(
            "SITE_URL non defini : les URL absolues (canonical, og:url, og:image,\n"
            "      sitemap, robots) restent relatives et les boutons de partage\n"
            "      social ne fonctionnent pas. Renseignez la variable d'environnement\n"
            "      SITE_URL=https://votre-domaine puis relancez make_site.py.")
    if CONTACT_EMAIL == "contact@example.com":
        blocking.append(
            "Adresse de contact placeholder : renseignez CONTACT_EMAIL (variable\n"
            "      d'environnement) et relancez make_site.py.")
    try:
        with open(os.path.join(SITE, "contribuer.html"), encoding="utf-8") as fh:
            contrib_html = fh.read()
    except OSError:
        contrib_html = ""
    if "forms.google.com" not in contrib_html:
        advisory.append(
            "Formulaire d'intake non branche : la page annonce l'ouverture a venir\n"
            "      et renvoie vers l'email. Branchez le formulaire Google quand il\n"
            "      existera (bloc #form-slot dans make_site.py).")
    if blocking:
        print("")
        print("AVANT PUBLICATION - %d point(s) bloquant(s) :" % len(blocking))
        for b in blocking:
            print("  - %s" % b)
    else:
        print("")
        print("Aucun point bloquant detecte.")
    if advisory:
        print("")
        print("A FAIRE PLUS TARD - %d point(s) :" % len(advisory))
        for a in advisory:
            print("  - %s" % a)


if __name__ == "__main__":
    build()
