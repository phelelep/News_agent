# Site

`build.py` transforme `reports/` en site statique dans `web/_site` (non versionné).
GitHub Actions le republie à chaque push sur `main` (`.github/workflows/pages.yml`).

## Construire en local

```bash
pip install -r web/requirements.txt
python web/build.py
python -m http.server 8000 --directory web/_site
```

## Bouton « Générer les rumeurs »

Le navigateur ne peut pas appeler l'API de la routine, et aucune clé ne doit se trouver dans le site.
Le bouton lance donc le workflow `.github/workflows/rumeurs.yml`, qui appelle la routine côté GitHub.

Configuration, à faire une fois :

1. **Clé de la routine :** dans le dépôt, Settings → Secrets and variables → Actions, créer le secret `API_KEY`.
2. **Publication :** Settings → Pages → Source : GitHub Actions.
3. **Token du bouton :** créer un fine-grained token limité à ce dépôt, avec la permission Actions en Read and write. Le coller au premier clic sur chaque appareil.

Pour changer de routine, modifier `ROUTINE_ID` dans `rumeurs.yml`.
