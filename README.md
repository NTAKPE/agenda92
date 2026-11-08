# Agenda des événements immobiliers en Afrique — 2026-2027

Tracker professionnel destiné aux **investisseurs et financiers**, construit pour répondre à une
question simple : *quand et où le marché immobilier africain se retrouve-t-il, et quels rendez-vous
valent le déplacement ?*

## Le problème de départ

Recenser les événements immobiliers africains paraît simple. Il ne l'est pas, pour trois raisons :

1. **Aucun agenda consolidé n'existe.** Les informations sont éparpillées entre les sites des
   organisateurs, les calendriers de salons, Eventbrite, les portails `allevents`/`eventseye`, la
   presse sectorielle et les réseaux sociaux. Space Kenya (`space.ke/events/`) suit 34 événements
   pour le Kenya seul ; API Events (`apievents.com/events/`) suit une poignée de flagships
   panafricains. Rien ne couvre le continent.
2. **Les sources se contredisent.** L'API Summit 2026 apparaît au 16-17 septembre chez Wesgro et au
   17-18 septembre ailleurs. La 5ᵉ édition d'ARCE se tient au « Palms Convention Center » selon
   Eventbrite et au « Destiny Arena » selon la FIABCI, avec 1 500+ délégués selon l'un et ~2 000
   selon l'autre. Les lieux bougent d'une année sur l'autre — l'API Summit a quitté Johannesburg
   pour Cape Town en 2026.
3. **Le bruit est considérable.** Une salle de cuisine à Accra n'est pas un salon immobilier. Les
   séminaires d'accréditation de 50 personnes en Afrique du Sud ne sont pas des rendez-vous
   d'investisseurs. Une liste « de tout ce qui contient *property* » est inutilisable.

Le livrable assume donc l'incertitude au lieu de la masquer : **chaque ligne porte son statut de
date et ses conflits de sources.**

## Périmètre

- **Géographique (strict)** : uniquement les événements organisés **sur le continent africain**.
  Sont exclus Dubaï, Londres, New York, Atlanta et tout événement hors d'Afrique portant sur
  l'immobilier africain — y compris l'Africa–UAE Real Estate Roadshow et les expos de la diaspora.
  Ces derniers sont listés en `rejected` avec la mention « hors périmètre géographique » pour tracer
  la limite.
- **Horizon** : novembre 2026 → décembre 2027. Les éditions 2028+ déjà annoncées figurent en
  `watchlist`.
- **Angle** : investisseur / financeur. La question posée à chaque événement est *« un fonds
  d'investissement ou un financeur y a-t-il intérêt ? »*.

## Filtre d'inclusion : le test « 2 sur 6 »

Un événement n'est retenu que s'il coche **au moins deux** de ces six cases :

| # | Critère | Ce qu'il exclut |
|---|---|---|
| 1 | **Audience décisionnelle** — investisseurs, financiers, fonds, banques, décideurs publics | le grand public |
| 2 | **Échelle** — ~500+ participants, ou 30+ exposants, ou statut de flagship national | les petits séminaires |
| 3 | **Substance** — logement, foncier, marchés de capitaux, capital institutionnel, rendement | les salons lifestyle |
| 4 | **Continuité** — 3ᵉ édition ou plus, ou rendez-vous annuel ancré | les one-shot |
| 5 | **Influence** — ministres, banques centrales, DFIs, fonds de pension, REITs, private equity | les clubs locaux |
| 6 | **Portée** — multi-pays ou nationale majeure | les salons de ville |

Un événement qui ne coche qu'une case part en `rejected`, avec la raison. C'est ce qui rend le
résultat défendable : on sait *ce qui a été écarté et pourquoi*.

## Catégories

| Catégorie | Signification |
|---|---|
| `flagship_continental` | panafricain ou multi-régions |
| `national_anchor` | le rendez-vous du pays |
| `capital_markets` | orientation finance/capital : REIT, crédit foncier, housing finance, marchés de capitaux |
| `adjacent_construction` | salon construction/matériaux — filtre **plus strict** : présence de promoteurs/investisseurs, un track « real estate », ou une dimension panafricaine |
| `watchlist` | annoncé, édition future, date non fixée |

Les salons adjacents sont isolés et non mélangés : ils pèsent lourd sur la faisabilité et la marge
des projets, mais ce ne sont pas des événements immobiliers.

## Statuts de date

| Statut | Signification |
|---|---|
| `confirmed` | date trouvée sur la page officielle, recoupée par une seconde source |
| `probable` | date cohérente mais source unique, ou sources divergentes sur le jour/le lieu |
| `to_confirm` | annoncé sans date fiable — à revérifier avant tout engagement |

Tout changement de date ou de lieu est conservé dans `conflicts` avec les deux versions et leurs
sources. Ces conflits ne sont pas un défaut : ils localisent l'information fragile.

## Les sources affichées

Chaque zone a noté, dans `data/zone-*.json`, les pages réellement lues avec leur URL et la date de
consultation. `data/sources-additionnels.json` complète le registre pour les pages citées dans un
arbitrage et vérifiées à part.

Au moment de générer le site, `build.py` relève les domaines cités dans l'arbitrage de chaque fiche
(contradictions, signaux et lacunes) et les rapproche du registre. Ce qui correspond devient un lien
portant son nom et sa date de consultation ; ce qui ne correspond pas reste écrit en clair, sans
jamais de lien deviné. `check_cited.py` vérifie que chaque URL affichée provient bien du registre.

Résultat au 6 novembre 2026 : 265 URL au registre, 39 sources rattachées à 20 fiches, 14 domaines
cités sans page de référence. Chaque fiche affiche aussi le lien de billetterie de l'organisateur
lorsqu'il existe (30 événements sur 83).

## Arborescence

```
agenda-immobilier-afrique/
├── build.py                 consolidation, dédoublonnage, arbitrages
├── make_tracker.py          tracker autonome (une page, données inline)
├── make_site.py             génération du site statique (111 pages)
├── deploy_github.py         préparation et envoi vers GitHub Pages
├── refresh.py               re-vérification des dates vs pages officielles
├── check_links.py           intégrité des liens internes
├── check_tracker.py         structure du tracker pré-rendu (lisibilité sans JS)
├── check_countries.py       nomenclature des 54 pays et périmètre réel
├── check_cited.py           chaque source affichée vient du registre des pages lues
├── check_numbers.py         chiffres du journal recalculés depuis les données
├── check_figures.py         chiffres de documentation
├── peek.py                  inspection ponctuelle d'une fiche
├── siteutil.py              fonctions partagées (domaine, sources citées)
├── data/                    un JSON par zone + changelog.json + registre des sources
├── export/                  CSV, ICS, tracker HTML, rapports de re-vérification
├── site/                    site statique prêt à publier
│   ├── index.html                 tracker interactif, 83 lignes pré-rendues
│   ├── evenements/                83 fiches événement
│   ├── pays/                      22 pages pays
│   ├── methodologie.html          le filtre, les statuts, la méthode
│   ├── a-propos.html              ligne éditoriale, sources, politique de correction
│   ├── changelog.html             journal des changements
│   ├── sponsors.html              emplacement partenaire et grille tarifaire
│   ├── contribuer.html            formulaire d'intake (zones à blanc)
│   ├── feed.xml, sitemap.xml, robots.txt
│   └── assets/  site.css, tracker.js, favicon.svg/png, og/ (105 visuels 1200×630)
├── README.md                ce document
├── PUBLICATION.md           guide de mise en ligne (hébergement, formulaire, partenaire, Substack)
└── DEPLOIEMENT.md           pas à pas GitHub Pages, pas à pas
```

Le site est **entièrement pré-rendu** : les pages événement ne contiennent aucun `<script>`, et les
83 lignes du tracker sont dans le HTML statique. Le JavaScript ne fait que filtrer des lignes déjà
présentes — il améliore l'usage, il ne porte pas le contenu. C'est ce qui rend les pages
indexables et la navigation fonctionnelle sans JavaScript.

## Utiliser

**Le tracker** — ouvrir `export/tracker.html`. Recherche plein texte, filtres par catégorie, statut
de date, pays et zone, seuil de score investisseur, tri par date ou par score. Chaque ligne se
déplie pour le détail : pertinence investisseur, thèmes, acteurs du capital, sources, conflits.

**Le calendrier** — importer `export/agenda-immobilier-afrique.ics` (Google Calendar, Outlook,
Apple Calendar). Les événements à date `probable` y entrent en `TENTATIVE`, les confirmés en
`CONFIRMED`. Les événements sans date n'y figurent pas.

**Le tableur** — `export/agenda-immobilier-afrique.csv`, 25 colonnes, une ligne par événement, avec
les conflits, l'URL source et les sources citées dans l'arbitrage.

**Rafraîchir et contrôler** —

```powershell
python build.py            # reconsolide data/ -> export/
python make_tracker.py     # regénère export/tracker.html
python make_site.py        # regénère site/ (111 pages)
python check_links.py      # 3 688 liens internes vérifiés
python check_tracker.py    # structure du tracker pré-rendu
python check_countries.py  # nomenclature et périmètre
python check_cited.py      # chaque source affichée vient du registre des pages lues
python check_ics.py        # conformité RFC 5545 de l'export calendrier
python refresh.py          # relit les pages officielles et signale les écarts
```

`refresh.py` ne modifie jamais les données : il produit `refresh-report.csv` et signale, par
événement, `confirme`, `a-verifier` ou `non-verifiable`. Une page sans date lisible (rendue en
JavaScript, ou bloquée) est marquée « non vérifiable », jamais « contredite ».

`make_site.py` signale à la fin ce qui bloque encore une mise en ligne : `SITE_URL` non défini,
adresse de contact placeholder, formulaire d'intake non branché.

**Publier** — voir `DEPLOIEMENT.md` pour la mise en ligne pas à pas (GitHub Pages), et
`PUBLICATION.md` pour le formulaire d'intake Google Forms → Sheets, l'emplacement partenaire et le
pont avec le Substack.

**Adresse publique retenue pour ce lancement** :
`https://NTAKPE.github.io/agenda92/` — le build l'écrit dans les URL absolues
(canonical, Open Graph, partage social, sitemap, robots).

## Ce que contient la version du 6 novembre 2026

**83 événements retenus**, dans **22 pays**, après consolidation de 97 fiches sources
(5 zones de recherche) et rejet documenté de **97 événements** qui ne passaient pas le filtre.

| | |
|---|---|
| Flagship continental | 8 |
| Ancre nationale | 17 |
| Marchés de capitaux | 16 |
| Adjacent construction | 13 |
| Watchlist (date non fixée) | 29 |
| Date confirmée | 11 |
| Date probable (sources divergentes) | 39 |
| Date à confirmer | 33 |
| Avec contradiction entre sources | 49 |

**Répartition par pays** : Kenya 15, Nigeria 11, Ghana 9, Afrique du Sud 7, Égypte 6, Algérie 5,
Tanzanie 4, Maroc 4, puis Ouganda, Zambie, Éthiopie, Côte d'Ivoire, Sénégal, Maurice et Tunisie
(2 chacun), puis Botswana, Namibie, République démocratique du Congo, Cameroun, Zimbabwe, Gabon et
Congo (1 chacun). Un événement — l'Africa Urban Forum — n'a pas de pays confirmé et reste
séparément filtrable.

**Répartition par zone** : Afrique de l'Est & Corne 21, Afrique de l'Ouest 20, Continental / finance /
adjacent 18, Maghreb & Afrique du Nord 13, Afrique australe & centrale 11.

**Les rendez-vous les plus déterminants pour un investisseur** (score 5/5, date fixée) : 16ᵉ Africa PPP
Infrastructure Finance Summit (Nairobi, 11-13 nov. 2026), LMA & ICMA Annual Africa Summit (Le Cap,
17-18 mars 2027), PI Africa — 10ᵉ Africa Pension Funds & Alternative Investments Conference (Maurice,
17-19 mars 2027), EAPI Summit (Nairobi, 12-13 mai 2027), AIHS 21ᵉ Africa International Housing Show
(Abuja, 12-17 juil. 2027), API Summit (Le Cap, 15-16 sept. 2027).

**Densité** : l'horizon démarre au quatrième trimestre 2026 (25 événements entre le 1ᵉʳ novembre et
le 31 décembre), puis 7 événements au T1 2027, 7 au T2, 9 au T3 et 3 au T4.

### Les zones à blanc

L'agenda ne couvre pas uniformément le continent, et le tracker le dit. **97 événements ont été
écartés avec une raison explicite**, et **74 mentions d'information introuvable** documentent les
angles morts. Sur les 54 États africains, **22 sont couverts et 32 n'ont aucun rendez-vous
documenté** :

- **Aucun rendez-vous immobilier institutionnel trouvé** : Libye, Soudan, Bénin, Burkina Faso,
  Cap-Vert, Gambie, Guinée, Guinée-Bissau, Liberia, Mali, Mauritanie, Niger, Sierra Leone, Togo,
  Angola, Tchad, Guinée équatoriale, République centrafricaine, São Tomé-et-Príncipe, Burundi,
  Comores, Djibouti, Érythrée, Madagascar, Malawi, Mozambique, Rwanda, Seychelles, Somalie,
  Soudan du Sud, Eswatini, Lesotho.
- **Le Maghreb est structurellement plus pauvre que l'Afrique de l'Ouest en matière de finance
  immobilière** : aucun salon REIT, crédit foncier coté ou family office immobilier n'a été trouvé
  dans la zone. Le rendez-vous y est le crédit/leasing (TASHIL à Alger), pas l'investissement
  institutionnel.
- **L'Afrique du Sud est saturée mais peu lisible** : le calendrier immobilier sud-africain est
  majoritairement constitué de séminaires de formation et d'accréditation (IEASA, SAIF, CFA) et de
  webinaires de 50 personnes, écartés au titre du filtre.
- **Les pays de la Corne sont couverts par le capital, pas par l'événement** : la Somalie n'a qu'un
  forum repéré en juillet 2026 (hors horizon), et la présence rwandaise ou éthiopienne se lit dans
  les programmes des fonds, pas dans des conférences dédiées.
- **L'Égypte a un creux institutionnel** : l'Egypt Economic Summit, longtemps le sommet de référence
  du pays, semble dormant depuis décembre 2021.

Ces zones ne sont pas des oublis : ce sont des constats, et ils font partie du livrable.

### Un arbitrage d'exemple

L'Abuja Real Estate Fest 2026 illustre la valeur du dispositif. Trois sources donnent le **12 novembre**
2026 (le site dédié de l'événement `are.eventhive.ng`, la billetterie officielle Eventbrite, et le
post LinkedIn d'origine), une seule donne le **19 novembre** (la page portfolio de l'organisateur sur
eventhive.ng). Le tracker conserve le conflit avec son arbitrage plutôt que de trancher
silencieusement — et l'erreur de la page portfolio est exactement le type de piège qu'un agenda
automatique sans vérification commettrait.

## Limites assumées

- Les sources publiques ne couvrent pas uniformément le continent. Les marchés anglophones
  (Nigeria, Ghana, Kenya, Afrique du Sud) sont bien documentés ; le Maghreb francophone et
  l'Afrique centrale le sont beaucoup moins. Les zones sans donnée sont tracées dans
  `negative_findings`.
- Les dates « à confirmer » représentent une part réelle du corpus, pas une lacune de méthode.
- Les chiffres d'affluence sont ceux des organisateurs, rarement audités — le site le signale sur
  chaque fiche.
- Les tarifs ne sont pas collectés : ils changent et sont souvent affichés dynamiquement.
  `ticket_url` pointe vers la page de billetterie officielle.
