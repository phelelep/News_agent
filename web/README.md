# Site

`build.py` transforme `reports/` en site statique dans `web/_site` (non versionné).
GitHub Actions le republie à chaque push sur `main` (`.github/workflows/pages.yml`).

## Construire en local

```bash
pip install -r web/requirements.txt
python web/build.py
python -m http.server 8000 --directory web/_site
```

## Rumeurs

Le site affiche les fichiers `reports/<Mois>/rumeurs_*.md` écrits par la routine, sans bouton.
Ligne attendue : `- <rumeur> (<proba> %, résolution <JJ/MM/AAAA>) — [Polymarket](lien) · 🟢`.

## Bouton « Add to watchlist »

Le navigateur ne peut pas écrire dans le dépôt : le bouton lance `.github/workflows/watchlist.yml`, qui ajoute le mot à `watchlist.md`.

À faire une fois :

1. **Publication :** Settings → Pages → Source : GitHub Actions.
2. **Token du bouton :** créer un fine-grained token limité à ce dépôt, avec la permission Actions en Read and write. Le coller au premier clic sur chaque appareil.

`rumeurs.yml` (déclenchement manuel de la routine) n'a plus de bouton sur le site.
