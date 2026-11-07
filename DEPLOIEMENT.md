# Déploiement sur GitHub Pages — pas à pas

Ce document décrit la mise en ligne du site sur une adresse `github.io`, sans
hébergement payant et sans outil supplémentaire. Le script `deploy_github.py`
prépare tout ; il reste deux commandes à lancer dans votre terminal, parce
qu'elles demandent une authentification GitHub que seul vous pouvez faire.

**Configuration retenue** : pseudo `NTAKPE`, dépôt
`NTAKPE/agenda92`, adresse publique
`https://NTAKPE.github.io/agenda92/`, contact
`jm.ntakpe@gmail.com`. Ces valeurs sont déjà les valeurs par défaut du
script — aucune option n'est obligatoire.

---

## Ce qui est déjà fait

- Le site est construit et vérifié : 111 pages, 3 687 liens internes sans
  casse, 83 événements, 22 pays.
- `deploy_github.py` sait construire le site avec la bonne URL publique,
  préparer les deux dépôts git (`main` pour les sources, `gh-pages` pour le
  site) et pousser.
- Le `.ics` est conforme RFC 5545 (CRLF strict), et un `.gitattributes`
  empêche git de convertir les fins de ligne à l'arrivée.

## Ce qu'il reste à faire

### 1. Créer le dépôt sur GitHub

Sur <https://github.com/new> :

| Champ | Valeur |
|---|---|
| Owner | `NTAKPE` (votre compte) |
| Repository name | `agenda92` |
| Visibility | **Public** — obligatoire pour GitHub Pages sur un compte gratuit |

Ne cochez **pas** « Add a README », « Add .gitignore » ni « Choose a license » :
le dépôt doit rester vide, le script s'occupe du premier commit.

### 2. Lancer le script de préparation

Depuis PowerShell, dans le dossier du projet :

```powershell
python deploy_github.py
```

Le script affiche les deux commandes de push. Elles n'ont pas encore été
lancées.

### 3. Pousser (une seule authentification)

```powershell
git -C .deploy-source push -u origin main
git -C .deploy-pages  push -u origin gh-pages
```

À la première commande, **git-credential-manager** ouvre une fenêtre de
navigateur pour vous connecter à GitHub. Vous cliquez sur le compte, vous
autorisez, vous revenez au terminal. C'est la seule fois : le jeton reste en
cache, et les mises à jour suivantes se font sans intervention.

### 4. Activer GitHub Pages

Dans le dépôt : **Settings → Pages**.

| Champ | Valeur |
|---|---|
| Build and deployment → Source | Deploy from a branch |
| Branch | `gh-pages` / `/(root)` |

Enregistrez. La première publication prend une à deux minutes. L'adresse
finale s'affiche en haut de la page :

```
https://NTAKPE.github.io/agenda92/
```

### 5. Vérifier

```powershell
python check_links.py
```

Puis, dans le navigateur, ouvrez l'adresse publique et vérifiez que le bouton
de partage produit un lien vers le domaine définitif.

---

## Mettre à jour le site plus tard

Le cycle mensuel, à partir du dossier du projet :

```powershell
python refresh.py                      # re-vérification des dates
#   ... arbitrer les écarts, corriger data/zone-*.json, data/changelog.json ...
python deploy_github.py
git -C .deploy-source push -u origin main
git -C .deploy-pages  push -u origin gh-pages
```

Aucune authentification n'est redemandée.

---

## Passer plus tard à un nom de domaine

Rien dans le code n'est lié à `github.io`. Le jour où vous achetez un
domaine, il suffit de :

1. pointer le domaine vers GitHub Pages (un enregistrement CNAME dans les
   réglages du dépôt, section *Pages → Custom domain*) ;
2. relancer le build avec la nouvelle URL :

```powershell
$env:SITE_URL = 'https://votre-domaine.com'
python make_site.py
```

3. repousser la branche `gh-pages`.

Les URL absolues (canonical, Open Graph, partage social, sitemap) sont
générées à partir de `SITE_URL` : elles se mettent à jour toutes seules.

---

## Dépannage

| Symptôme | Cause probable | Correction |
|---|---|---|
| « GitHub Pages is currently disabled. You must first add content to your repository » | le dépôt est vide : Pages exige que la branche de publication contienne déjà des fichiers | c'est normal au départ — **pousser d'abord** (étape 3), puis activer Pages (étape 4). L'option réapparaît une fois `gh-pages` remplie |
| `remote: Repository not found` | le dépôt n'existe pas ou n'est pas public | créer le dépôt à l'étape 1 |
| `Permission denied (publickey)` ou invite à saisir un mot de passe | authentification non faite | relancer le push, laisser le navigateur s'ouvrir |
| `Pages failed to build` | branche ou dossier mal réglé | vérifier `gh-pages` et `/(root)` dans Settings → Pages |
| Page blanche / lien cassé | `.nojekyll` manquant | il est écrit par le script ; relancer `deploy_github.py` |
| Le partage sur X ou LinkedIn ne fonctionne pas | URL encore relatives | vérifier que `SITE_URL` était défini au build |

### Ordre impératif

Pages ne peut pas être activé sur un dépôt vide. L'ordre est donc :

1. créer le dépôt (vide, public) ;
2. pousser `main` et `gh-pages` ;
3. activer Pages sur `gh-pages` / `/(root)`.

Si vous avez déjà tenté d'activer Pages avant le push, ce n'est pas bloquant : poussez,
rechargez la page *Settings → Pages*, le sélecteur de branche sera alors disponible.
