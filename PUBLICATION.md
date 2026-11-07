# Publication de l'agenda — guide opérationnel

Ce guide couvre ce qui reste à faire pour mettre l'agenda en ligne. Le site est dans `site/`,
prêt à être déployé tel quel.

**Configuration retenue pour ce lancement** : GitHub Pages, dépôt
`NTAKPE/agenda92`, adresse publique
`https://NTAKPE.github.io/agenda92/`. La procédure complète est dans
`DEPLOIEMENT.md`.

---

## 1. La chaîne de production

```
data/zone-*.json      données brutes par zone (recherche)
        ↓  build.py
export/*.csv *.ics    exports tableur et calendrier
        ↓  make_site.py
site/                 site statique prêt à publier (111 pages)
        ↓  refresh.py  (mensuel)
export/refresh-report.csv   écarts détectés vs pages officielles
```

Commandes, dans cet ordre :

```powershell
python build.py            # consolide data/ -> export/
python make_tracker.py     # regénère export/tracker.html
python make_site.py        # regénère site/
python check_links.py      # vérifie que les 3 688 liens internes résolvent
python check_tracker.py    # vérifie la structure du tracker pré-rendu
python check_countries.py  # vérifie la nomenclature des pays et le périmètre
python refresh.py          # recontrôle les dates contre les pages officielles
```

`refresh.py` **ne modifie jamais** les données : il produit `export/refresh-report.csv`. C'est
voulu. Un changement de date doit être arbitré à la main, puis inscrit dans
`data/changelog.json`, puis publié.

`make_site.py` affiche à la fin la liste des points qui bloquent encore la mise en ligne. Tant
qu'elle n'est pas vide, le site n'est pas publiable tel quel.

---

## 2. Publier le site

Le dossier `site/` est 100 % statique : HTML, CSS, JS et les exports CSV/ICS. Aucune dépendance,
aucun serveur, aucun build côté hébergeur. Deux options, de la plus simple à la plus sérieuse.

### Option A — une URL publique immédiate (gratuit, 2 minutes)

Le dossier `site/` peut être déposé tel quel sur n'importe quel hébergeur statique. Si tu veux une
URL publique tout de suite sans créer de compte, je peux le faire depuis cette session : le site
serait accessible à tous, sur Internet, à une adresse permanente.

### Option B — Cloudflare Pages (recommandé si ça prend)

1. Créer un dépôt Git (GitHub ou GitLab) et y pousser le projet.
2. Dans Cloudflare, **Workers & Pages → Create → Pages → Connect to Git**.
3. Framework preset : *None*. Build command : `python make_site.py`.
   Output directory : `site`.
4. Cloudflare Pages est gratuit, bandeau illimitée, et sert le site en HTTPS.
5. Pour un nom de domaine, ajouter un domaine personnalisé dans l'onglet *Custom domains*.
   Cloudflare Registrar vend les domaines au coût de revient (environ 10-15 €/an pour un .com).

### Option C — GitHub Pages

Pousser `site/` dans un dossier `gh-pages` ou un dépôt séparé, puis *Settings → Pages → deploy from
branch*. Gratuit, mais l'URL est en sous-domaine `github.io` — moins crédible pour une page
partenaire.

### Ce qu'il faut corriger avant de publier

**Déjà fait pour ce lancement** : `SITE_URL` et `CONTACT_EMAIL` sont renseignés par défaut dans
`make_site.py`, et le build le confirme :

```
Aucun point bloquant detecte.
A FAIRE PLUS TARD - 1 point(s) :
  - Formulaire d'intake non branche : la page annonce l'ouverture a venir
      et renvoie vers l'email. Branchez le formulaire Google quand il
      existera (bloc #form-slot dans make_site.py).
```

`SITE_URL` pilote tout ce qui doit être une URL absolue : `canonical`, `og:url`, `og:image`, les
liens de partage (X, LinkedIn, WhatsApp, Telegram), les `<loc>` du `sitemap.xml` et la ligne
`Sitemap:` du `robots.txt`. Sans elle, le site fonctionne mais **le partage social ne fonctionne
pas** : les réseaux sociaux exigent des URL absolues.

Le seul point restant est le formulaire Google : la page « Contribuer » annonce aujourd'hui son
ouverture à venir et renvoie vers l'email. C'est un choix assumé pour ce premier lancement, pas
une page cassée — mais brancher le formulaire reste la prochaine amélioration.

Pour un redéploiement manuel, on peut surcharger les valeurs :

```powershell
$env:SITE_URL = 'https://votre-domaine.com'
$env:CONTACT_EMAIL = 'vous@votre-domaine.com'
python make_site.py
```

Et `deploy_github.py --github-user NTAKPE` fait les deux d'un coup.

### Les signaux déjà en place

Aucune action supplémentaire n'est requise pour le référencement et le partage social :

| Signal | Où |
|---|---|
| 105 visuels de partage 1200×630 (un par événement, un par pays, un par défaut) | `site/assets/og/` |
| Balises Open Graph + Twitter Card + `canonical` | toutes les pages |
| Données structurées JSON-LD (`WebSite`, `Event`) | accueil et 83 fiches |
| Favicon PNG + SVG | `site/assets/` |
| `sitemap.xml` (111 URL) et `robots.txt` | racine du site |
| Flux RSS du journal | `feed.xml` |
| Botons de partage X / LinkedIn / WhatsApp / Telegram + copie du lien | chaque fiche |

Les visuels sont générés par `make_site.py` (Pillow). Si la police système change, ils sont
régénérés au prochain build.

---

## 3. Le formulaire d'intake (Google Forms → Sheets)

C'est le levier qui fait couvrir les 32 pays sans rendez-vous. Mise en place, environ 15 minutes.

### Créer la Sheet

Une feuille Google Sheets, un onglet `signalements`, avec ces colonnes :

| Colonne | Contenu |
|---|---|
| `date_signalement` | automatique |
| `nom_evenement` | texte |
| `edition` | texte |
| `date_debut` | date |
| `date_fin` | date |
| `ville` | texte |
| `pays` | liste (voir §3.2) |
| `lieu` | texte |
| `organisateur` | texte |
| `url_source` | URL |
| `url_billetterie` | URL |
| `effectif` | texte |
| `exposants` | texte |
| `acteurs_capital` | texte |
| `statut_date` | liste : confirmée / probable / à confirmer |
| `notes` | texte libre |

### Créer le formulaire

Google Forms → *Nouveau formulaire*, puis *Répondre → Feuille de calcul* → sélectionner la Sheet
ci-dessus. Un champ par colonne, avec `date_debut` en type Date et `pays` en liste déroulante.

### L'afficher sur le site

Dans `site/contribuer.html`, remplacer le bloc `<div class="notice" id="form-slot">` par :

```html
<iframe src="https://docs.google.com/forms/d/e/VOTRE_ID_DE_FORMULAIRE/view?embedded=1"
        width="100%" height="900" frameborder="0" title="Signaler un événement"
        data-form-url="https://docs.google.com/forms/d/e/VOTRE_ID_DE_FORMULAIRE/view?embedded=1"></iframe>
```

### Traiter les signalements

Chaque envoi crée une ligne dans la Sheet. Le traitement est manuel mais mécanique :

1. Vérifier la date contre la page officielle de l'organisateur.
2. Chercher une seconde source.
3. Si les sources divergent : statut `probable`, et inscrire la contradiction dans `conflicts`.
4. Appliquer le filtre « 2 sur 6 ». Si l'événement ne coche pas deux critères, l'écarter et le dire
   au contributeur.
5. Écrire la fiche dans le fichier `data/zone-<zone>.json` correspondant, au bon format.
6. Relancer `build.py` puis `make_site.py`.
7. Ajouter une entrée dans `data/changelog.json`.

### 3.2 Liste des pays

Les 54 pays du continent, pour normaliser les saisies dès le départ :

Afrique du Nord · Algérie · Égypte · Libye · Maroc · Soudan · Tunisie
Afrique de l'Ouest · Bénin · Burkina Faso · Cap-Vert · Côte d'Ivoire · Gambie · Ghana · Guinée ·
Guinée-Bissau · Liberia · Mali · Mauritanie · Niger · Nigéria · Sénégal · Sierra Leone · Togo
Afrique centrale · Angola · Cameroun · Tchad · Congo · Gabon · Guinée équatoriale · République
centrafricaine · République démocratique du Congo · São Tomé-et-Príncipe
Afrique de l'Est · Burundi · Comores · Djibouti · Érythrée · Éthiopie · Kenya · Madagascar ·
Malawi · Maurice · Mozambique · Ouganda · Rwanda · Seychelles · Somalie · Soudan du Sud ·
Tanzanie · Zambie · Zimbabwe
Afrique australe · Afrique du Sud · Botswana · Eswatini · Lesotho · Namibie

La liste est vérifiée par `check_countries.py`, qui compare aussi les pays réellement
couverts par l'agenda à cette nomenclature et signale tout libellé hors liste.

---

## 4. L'emplacement partenaire

Un seul emplacement, sur toutes les pages. Il est défini par une seule fonction dans
`make_site.py` :

```python
def sponsor_slot(label="Emplacement partenaire disponible", prefix=""):
```

Remplace le contenu intérieur par le code de l'annonceur. Pour un partenaire payeur, remplacer
typiquement le `<aside class="adslot">` par :

```html
<aside class="adslot">
  <a href="https://partenaire.example">
    <img src="assets/partenaire-300x100.png" alt="Nom du partenaire" width="300" height="100">
  </a>
</aside>
```

et déposer l'image dans `site/assets/`. Penser à `loading="lazy"` sur l'image si le partenaire
en fournit une.

### Ce qui est vendable

- Bannière en tête d'agenda (page d'accueil).
- Emplacement sur les 22 pages pays et les 83 pages événement — c'est là que le trafic
  professionnel se concentre.
- Mention partenaire dans le récapitulatif hebdomadaire des changements.
- Un lien sortant depuis une page qui parle d'un pays ou d'un événement précis : pour un cabinet
  spécialisé en financement immobilier, c'est une contextualisation qu'aucune bannière générique
  n'offre.

**Pas d'AdSense.** Une audience B2B de cette taille ne le rentabilise pas, et l'approbation sur une
page de données est incertaine. Un sponsor unique,-direct, vend mieux et ne dégrade pas
l'expérience.

---

## 5. Le pont Substack

### Le lien à mettre dans chaque numéro

`https://ton-domaine/index.html` — la page d'accueil.

Ne pas mettre seulement « voir l'agenda ». Le clic se gagne avec une raison précise :

- « 3 événements ajoutés, 2 dates changées cette semaine »
- « Before you book the flight : the verified dates for the next 90 days »
- « Le rendez-vous que vous cherchez est peut-être dans les 32 pays où personne ne l'a encore signalé »

### Ce que le Substack apporte à l'agenda

- **Un canal de diffusion fiable**, là où l'agenda n'a qu'une URL à partager.
- **Une audience qui sait à qui elle parle** : les Drs d'investissement, les courtiers, les
  promoteurs, les juristes qui conseillent sur l'immobilier africain.
- **Un moyen de monétiser autrement** : le tracker reste gratuit, l'analyse et le contexte restent
  payants. C'est la bonne répartition — ne jamais mettre le tracker derrière le paywall.

### Le flux RSS

`feed.xml` contient le journal des changements. Il est directement exploitable comme flux
d' syndication dans Substack (*Settings → RSS → Redirect feed*) ou dans n'importe quel agrégateur.

### Le rythme

Une re-vérification **mensuelle** est le minimum. C'est elle qui produit le journal des changements,
et c'est le journal qui donne au lecteur une raison de revenir. Sans re-vérification, l'agenda
devient un document mort en trois mois — et le site perd sa principale raison d'exister.

---

## 6. À faire une fois, pour bien démarrer

Le lancement est prêt : `SITE_URL` et `CONTACT_EMAIL` sont renseignés, le contact est en place et
la page « Contribuer » assume l'ouverture à venir du formulaire.

Dans l'ordre. Tant que les deux premiers points ne sont pas faits, `make_site.py` signale encore
des points bloquants.

- [x] `SITE_URL` et `CONTACT_EMAIL` renseignés — URL publique
      `https://NTAKPE.github.io/agenda92/`
- [ ] Créer le dépôt GitHub `NTAKPE/agenda92` (public) et pousser les deux
      branches — voir `DEPLOIEMENT.md`
- [ ] Activer GitHub Pages : branche `gh-pages`, dossier `/(root)`
- [ ] Tester le partage d'une fiche sur X, LinkedIn et WhatsApp avec l'URL définitive
- [ ] Créer le formulaire Google et la Sheet, puis remplacer le bloc `#form-slot`
- [ ] Remplacer le contenu de `sponsors.html` par l'offre commerciale
- [ ] Inscrire le site sur Google Search Console (sitemap + indexation)
- [ ] Insérer le lien dans les newsletters Substack
- [ ] Faire la première re-vérification (`refresh.py`) et publier le premier journal de changements

### Ce que le build signale

`make_site.py` se termine par un récapitulatif, en deux groupes : ce qui **bloque** la publication,
et ce qui peut attendre.

```
Aucun point bloquant detecte.
A FAIRE PLUS TARD - 1 point(s) :
  - Formulaire d'intake non branche : ...
```

### Contrôle final avant mise en ligne

```powershell
python check_links.py      # 3 688 liens, 0 cassé, 0 page orpheline
python check_tracker.py    # 0 script exécutable en ligne, 83 lignes et 83 détails appariés
python check_countries.py  # 54 pays, nomenclature conforme
```
