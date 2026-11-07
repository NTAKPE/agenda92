# -*- coding: utf-8 -*-
"""
Re-verification des dates de l'agenda.

Pour chaque evenement date, relit la page source (ticket_url en priorite, sinon source_url)
et compare les dates mentionnees a la date stockee dans export/tracker-data.json.

Sortie :
  export/refresh-report.json   rapport structure
  export/refresh-report.csv    rapport lisible (separateur ';')

Principe : le script ne modifie JAMAIS tracker-data.json. Il signale.
Une page sans date lisible (rendue en JS, ou bloquee) est marquee "non verifiable",
jamais "contredite".
"""
import csv
import json
import os
import re
import ssl
import sys
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "export")
DATA_FILE = os.path.join(OUT, "tracker-data.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DELAY = 1.2  # secondes entre deux requetes, par politesse
TIMEOUT = 20

MONTHS = {
    "january": 1, "jan": 1, "janvier": 1, "janv": 1,
    "february": 2, "feb": 2, "fevrier": 2, "fevr": 2,
    "march": 3, "mars": 3,
    "april": 4, "apr": 4, "avril": 4, "avr": 4,
    "may": 5, "mai": 5,
    "june": 6, "jun": 6, "juin": 6,
    "july": 7, "jul": 7, "juillet": 7, "juil": 7,
    "august": 8, "aug": 8, "aout": 8,
    "september": 9, "sep": 9, "sept": 9, "septembre": 9,
    "october": 10, "oct": 10, "octobre": 10,
    "november": 11, "nov": 11, "novembre": 11,
    "december": 12, "dec": 12, "decembre": 12,
}
MONTH_RE = "|".join(sorted(MONTHS.keys(), key=len, reverse=True))

# 12 November 2026 | 12 Nov 2026 | November 12, 2026 | 12/11/2026 | 12-13 November 2026
RE_DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(%s)[a-z]*\.?\s+(20\d{2})\b" % MONTH_RE, re.I)
RE_MDY = re.compile(r"\b(%s)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(20\d{2})\b" % MONTH_RE, re.I)
RE_NUM = re.compile(r"\b(\d{1,2})[/.](\d{1,2})[/.](20\d{2})\b")
# plages : "12-13 November 2026", "12 to 14 Nov 2026", "12 - 14 novembre 2026"
RE_RANGE_DMY = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|—|to|et|au|à)\s*(\d{1,2})(?:st|nd|rd|th)?\s+"
    r"(?:of\s+)?(%s)[a-z]*\.?\s+(20\d{2})\b" % MONTH_RE, re.I)
# plages inversees : "November 12-14, 2026"
RE_RANGE_MDY = re.compile(
    r"\b(%s)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|–|—|to|et)\s*(\d{1,2})"
    r"(?:st|nd|rd|th)?,?\s+(20\d{2})\b" % MONTH_RE, re.I)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def parse_day_month_year(d, m, y):
    try:
        return date(int(y), MONTHS[norm(m)], int(d))
    except (ValueError, KeyError):
        return None


def extract_dates(text):
    """Retourne l'ensemble des dates explicites trouvees dans le texte."""
    found = set()
    for d, m, y in RE_DMY.findall(text):
        dt = parse_day_month_year(d, m, y)
        if dt:
            found.add(dt)
    for m, d, y in RE_MDY.findall(text):
        dt = parse_day_month_year(d, m, y)
        if dt:
            found.add(dt)
    for d1, d2, m, y in RE_RANGE_DMY.findall(text):
        for d in (d1, d2):
            dt = parse_day_month_year(d, m, y)
            if dt:
                found.add(dt)
    for m, d1, d2, y in RE_RANGE_MDY.findall(text):
        for d in (d1, d2):
            dt = parse_day_month_year(d, m, y)
            if dt:
                found.add(dt)
    for d, m, y in RE_NUM.findall(text):
        try:
            dd, mm = int(d), int(m)
            if 1 <= mm <= 12 and 1 <= dd <= 31:
                found.add(date(int(y), mm, dd))
        except ValueError:
            pass
    return found


def fetch(url):
    if not url:
        return None, "pas d'url"
    try:
        req = Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en,fr;q=0.8",
        })
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            raw = resp.read(600000)
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype and "text" not in ctype and "json" not in ctype:
                return None, "type non textuel (%s)" % ctype[:40]
            return raw.decode("utf-8", errors="ignore"), None
    except HTTPError as exc:
        return None, "HTTP %s" % exc.code
    except (URLError, TimeoutError, OSError) as exc:
        return None, "reseau: %s" % str(exc)[:60]
    except Exception as exc:  # noqa: BLE001
        return None, "erreur: %s" % str(exc)[:60]


def strip_html(html):
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def main():
    if not os.path.exists(DATA_FILE):
        print("tracker-data.json absent : lance build.py d'abord.", file=sys.stderr)
        return 1
    with open(DATA_FILE, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    events = [e for e in data.get("events", []) if e.get("start")]
    results = []
    print("Re-verification de %d evenements dates\n" % len(events))

    for i, ev in enumerate(events, 1):
        stored_start = datetime.strptime(ev["start"], "%Y-%m-%d").date()
        stored_end = datetime.strptime(ev["end"], "%Y-%m-%d").date() if ev.get("end") else stored_start
        url = ev.get("ticket_url") or ev.get("source_url") or ""
        status, detail = "a-verifier", ""
        candidates = set()

        html, err = fetch(url)
        if html is None:
            status, detail = "non-verifiable", err
        else:
            text = strip_html(html)
            candidates = extract_dates(text)
            # Fenetre etroite : meme annee, a +/- 31 jours de la date stockee.
            # Au-dela, on attrape les dates d'editions voisines citees en
            # pied de page, qui ne sont pas un changement de date.
            near = {d for d in candidates
                    if d.year == stored_start.year
                    and abs((d - stored_start).days) <= 31}
            if stored_start in candidates or stored_end in candidates:
                status = "confirme"
                detail = "date stockee trouvee sur la page"
            elif near:
                # Des dates proches ont ete trouvees sans correspondre a la
                # date stockee : la page a pu etre mise a jour, ou les dates
                # trouvees peuvent provenir d'un autre element (article,
                # edition voisine). On signale sans conclure.
                status = "a-verifier"
                detail = "date(s) a proximite sans correspondance exacte : %s " \
                         "(stockee : %s) - a controler manuellement" % (
                             ", ".join(sorted(d.isoformat() for d in near)),
                             stored_start.isoformat())
            else:
                status = "non-verifiable"
                detail = "aucune date exploitable sur la page (rendu JS ?)"
            if len(candidates) > 40:
                detail += " [%d dates extraites au total]" % len(candidates)

        results.append({
            "name": ev["name"],
            "city": ev.get("city", ""),
            "country": ev.get("country", ""),
            "url": url,
            "stored_start": stored_start.isoformat(),
            "stored_end": stored_end.isoformat(),
            "status": status,
            "detail": detail,
        })
        flag = "." if status == "confirme" else "!"
        print("  [%s] %-62s %s" % (flag, (ev["name"] or "")[:62], status))
        if i < len(events):
            time.sleep(DELAY)

    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    report = {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "totals": counts,
        "results": results,
    }
    with open(os.path.join(OUT, "refresh-report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)

    csv_path = os.path.join(OUT, "refresh-report.csv")
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["Evenement", "Ville", "Pays", "Date stockee", "Date fin",
                    "Statut re-verification", "Detail", "URL"])
        for r in results:
            w.writerow([r["name"], r["city"], r["country"], r["stored_start"],
                        r["stored_end"], r["status"], r["detail"], r["url"]])

    print("\n--- Bilan ---")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print("  %-22s %d" % (k, v))
    print("  -> %s" % csv_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
