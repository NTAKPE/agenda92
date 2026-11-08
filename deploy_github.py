# -*- coding: utf-8 -*-
"""
Preparation et publication du site sur GitHub Pages.

Fonctionnement :
  1. regenere site/ avec SITE_URL = https://<user>.github.io/<repo>/
  2. prepare un depot git local 'main' contenant les sources (scripts, data, docs)
  3. prepare un depot git local 'gh-pages' contenant le site construit
  4. pousse les deux branches vers https://github.com/<user>/<repo>.git

Le push demande une authentification GitHub. Elle n'est demandee qu'une fois :
git-credential-manager (deja installe avec Git pour Windows) ouvre une fenetre
de navigateur, et le jeton reste en cache pour les pushes suivants.

Usage :
    python deploy_github.py --github-user MONPSEUDO [--repo agenda92]
                            [--push] [--contact-email vous@exemple.com]

Sans --push, le script prepare tout et affiche la commande exacte a lancer.
"""
import argparse
import io
import os
import shutil
import stat
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GIT = "git"


def run(args, cwd=None, check=True, capture=False, env=None):
    """Lance une commande git et renvoie (code, sortie)."""
    proc = subprocess.run(args, cwd=cwd, capture_output=capture,
                          text=True, encoding="utf-8", errors="replace", env=env)
    if check and proc.returncode != 0:
        out = (proc.stdout or "") + (proc.stderr or "")
        raise SystemExit("ECHEC de %s :\n%s" % (" ".join(args), out.strip()))
    return proc.returncode, (proc.stdout or ""), (proc.stderr or "")


def section(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def force_rmtree(path):
    """Supprime un dossier, attributs en lecture seule compris.

    Git marque ses objets en lecture seule sous Windows : sans lever
    l'attribut, shutil.rmtree echoue avec un PermissionError.
    """
    if not os.path.isdir(path):
        return

    def _fix(exc_func, target, exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            exc_func(target)
        except Exception:
            pass

    try:
        shutil.rmtree(path, onexc=_fix)       # Python 3.12+
    except TypeError:
        shutil.rmtree(path, onerror=_fix)     # Python 3.11 et anterieur


def clear_dir_except(path, keep=(".git",)):
    """Vide un dossier de travail en conservant certains entrees.

    Permet de regenerer le contenu d'un depot deja initialise sans perdre
    son historique git : sans cela, chaque execution recreerait un commit
    racine orphelin et le push suivant serait refuse (pas d'ancetre commun).
    """
    if not os.path.isdir(path):
        return
    for entry in os.listdir(path):
        if entry in keep:
            continue
        target = os.path.join(path, entry)
        if os.path.isdir(target) and not os.path.islink(target):
            force_rmtree(target)
        else:
            try:
                os.chmod(target, stat.S_IWRITE)
                os.remove(target)
            except OSError:
                pass


def commit_all(folder, message, author):
    """Ajoute et valide les modifications ; renvoie False si rien n'a change."""
    run([GIT, "add", "-A"], cwd=folder)
    code, out, _ = run([GIT, "status", "--porcelain"], cwd=folder, check=False, capture=True)
    if not (out or "").strip():
        return False
    run([GIT, "-c", "user.name=%s" % author, "-c", "user.email=%s@users.noreply.github.com" % author,
         "commit", "-m", message], cwd=folder)
    return True


def main():
    ap = argparse.ArgumentParser(description="Deploie l'agenda sur GitHub Pages.")
    ap.add_argument("--github-user", default="NTAKPE",
                    help="votre pseudo GitHub (determine l'URL)")
    ap.add_argument("--repo", default="agenda92",
                    help="nom du depot (defaut : agenda92)")
    ap.add_argument("--contact-email", default="jm.ntakpe@gmail.com",
                    help="adresse de contact publiee sur le site")
    ap.add_argument("--push", action="store_true",
                    help="pousse effectivement les branches (demande une authentification)")
    args = ap.parse_args()

    user = args.github_user.strip()
    repo = args.repo.strip()
    site_url = "https://%s.github.io/%s/" % (user, repo)
    remote = "https://github.com/%s/%s.git" % (user, repo)

    section("1. Rebuild du site avec l'URL publique")
    env = dict(os.environ)
    env["SITE_URL"] = site_url
    if args.contact_email:
        env["CONTACT_EMAIL"] = args.contact_email.strip()
    code, out, err = run([sys.executable, "make_site.py"], cwd=BASE, check=False,
                          capture=True, env=env)
    print((out or "")[-1400:])
    if code != 0:
        print(err)
        raise SystemExit("Le build a echoue.")
    print("URL publique retenue : %s" % site_url)

    # ---- depot des sources (branche main) --------------------------------
    section("2. Depot des sources (branche main)")
    src_dir = os.path.join(BASE, ".deploy-source")
    src_exists = os.path.isdir(os.path.join(src_dir, ".git"))
    if not src_exists:
        force_rmtree(src_dir)
        os.makedirs(src_dir)

    ignore = [
        "site/", "export/", ".deploy-source/", ".deploy-pages/",
        "__pycache__/", "*.pyc", ".DS_Store",
    ]
    with open(os.path.join(src_dir, ".gitignore"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(ignore) + "\n")
    # Aucune conversion de fin de ligne : les fichiers sont stockes tels
    # quels, ce qui evite les conversions CRLF/LF a l'aller-retour et garde
    # les donnees JSON et le .ics identiques a la source.
    with open(os.path.join(src_dir, ".gitattributes"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("* -text\n")

    keep_root = ["build.py", "make_tracker.py", "make_site.py", "refresh.py",
                 "deploy_github.py", "siteutil.py",
                 "check_links.py", "check_tracker.py", "check_countries.py",
                 "check_numbers.py", "check_figures.py", "check_cited.py",
                 "check_ics.py", "make_archive.py", "peek.py", "peek_history.py",
                 "README.md", "PUBLICATION.md", "DEPLOIEMENT.md"]
    for fn in keep_root:
        src = os.path.join(BASE, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(src_dir, fn))
    for sub in ("data",):
        s = os.path.join(BASE, sub)
        d = os.path.join(src_dir, sub)
        if os.path.isdir(s):
            if os.path.isdir(d):
                shutil.rmtree(d)
            shutil.copytree(s, d, ignore=shutil.ignore_patterns("__pycache__"))

    if src_exists:
        changed = commit_all(src_dir,
                             "Mise a jour des sources et des scripts de controle",
                             user)
        print("  sources mises a jour dans .deploy-source (%s)"
              % ("modifications" if changed else "aucun changement"))
    else:
        run([GIT, "init", "-b", "main"], cwd=src_dir)
        run([GIT, "config", "user.name", user], cwd=src_dir)
        run([GIT, "config", "user.email", "%s@users.noreply.github.com" % user], cwd=src_dir)
        run([GIT, "add", "-A"], cwd=src_dir)
        run([GIT, "commit", "-m",
             "Agenda des evenements immobiliers en Afrique - sources et donnees"], cwd=src_dir)
        run([GIT, "remote", "add", "origin", remote], cwd=src_dir)
        print("  sources pretes dans .deploy-source (branche main)")

    # ---- depot du site construit (branche gh-pages) ----------------------
    section("3. Depot du site construit (branche gh-pages)")
    pages_dir = os.path.join(BASE, ".deploy-pages")
    pages_exists = os.path.isdir(os.path.join(pages_dir, ".git"))
    if pages_exists:
        clear_dir_except(pages_dir, keep=(".git",))
    else:
        force_rmtree(pages_dir)
    shutil.copytree(os.path.join(BASE, "site"), pages_dir)
    # Jekyll ne doit pas interpreter le site : branche et underscores neutres
    with open(os.path.join(pages_dir, ".nojekyll"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("")
    readme = ("# Agenda des evenements immobiliers en Afrique\n\n"
              "Site statique publie sur GitHub Pages depuis la branche `gh-pages`.\n"
              "Source et scripts de production : branche `main`.\n")
    with open(os.path.join(pages_dir, "README.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(readme)
    # Servir les fichiers a l'identique : pas de conversion de fin de ligne,
    # ce qui compte pour le .ics (CRLF obligatoire au sens de la RFC 5545).
    with open(os.path.join(pages_dir, ".gitattributes"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("* -text\n")

    if pages_exists:
        changed = commit_all(
            pages_dir,
            "Publication du site - edition du %s" % __import__("datetime").date.today().isoformat(),
            user)
        print("  site mis a jour dans .deploy-pages (%s)"
              % ("modifications" if changed else "aucun changement"))
    else:
        run([GIT, "init", "-b", "gh-pages"], cwd=pages_dir)
        run([GIT, "config", "user.name", user], cwd=pages_dir)
        run([GIT, "config", "user.email", "%s@users.noreply.github.com" % user], cwd=pages_dir)
        run([GIT, "add", "-A"], cwd=pages_dir)
        run([GIT, "commit", "-m",
             "Publication du site - edition du %s" % __import__("datetime").date.today().isoformat()],
            cwd=pages_dir)
        run([GIT, "remote", "add", "origin", remote], cwd=pages_dir)
        n_files = sum(len(filenames) for _, _dirnames, filenames in os.walk(pages_dir))
        print("  site pret dans .deploy-pages (branche gh-pages, %d fichiers)" % n_files)

    # ---- push ------------------------------------------------------------
    section("4. Envoi vers GitHub")
    if not args.push:
        print("Push non demande (--push absent).")
        print()
        print("Lancez ceci dans VOTRE terminal, depuis le dossier du projet :")
        print()
        print('  cd "%s"' % BASE)
        print('  git -C .deploy-source push -u origin main')
        print('  git -C .deploy-pages  push -u origin gh-pages')
        print()
        print("git-credential-manager va ouvrir une fenetre de navigateur pour")
        print("vous connecter a GitHub. C'est la seule fois : le jeton reste en")
        print("cache, et les mises a jour suivantes se font sans intervention.")
        print()
        print(" ensuite, dans les reglages du depot > Pages :")
        print("   Source : Deploy from a branch")
        print("   branche : gh-pages  /  dossier : / (root)")
        print()
        print("URL finale : %s" % site_url)
        return

    for label, folder, branch in (("sources (main)", src_dir, "main"),
                                   ("site (gh-pages)", pages_dir, "gh-pages")):
        print("  push des %s ..." % label)
        code, out, err = run([GIT, "push", "-u", "origin", branch], cwd=folder,
                              check=False, capture=True)
        if code != 0:
            print((out or "") + (err or ""))
            raise SystemExit("Le push de la branche %s a echoue." % branch)
        print("  branche %s poussee." % branch)

    print()
    print("Branches envoyees. Il reste a activer Pages dans les reglages du")
    print("depot : branche gh-pages, dossier / (root).")
    print("URL finale : %s" % site_url)


if __name__ == "__main__":
    main()
