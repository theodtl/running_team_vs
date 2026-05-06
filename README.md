# Running Team VS

Dashboard web pour suivre un challenge Strava en équipes via l'endpoint club.

## Architecture choisie

- `src/running_team_vs/`
  - `config.py` : lecture de la configuration et des chemins
  - `club_api.py` : récupération des activités du club Strava
  - `storage.py` : lecture et écriture des fichiers Excel
  - `ranking.py` : logique de scoring et de dédoublonnage
  - `app.py` : application Flask pour afficher le classement
- `web/templates/` : template HTML du dashboard
- `web/static/` : CSS et assets statiques
- `data/` : fichiers de données (`teams.xlsx`, `processed_activities.xlsx`)

## Installation

1. Créer un environnement Python 3.11+
2. Installer les dépendances :

```bash
pip install -r requirements.txt
```

3. Copier `.env.sample` en `.env` et renseigner `STRAVA_ACCESS_TOKEN`.

## Exécution

1. Copier `.env.sample` en `.env` et renseigner `STRAVA_ACCESS_TOKEN`.
2. Lancer le dashboard :

```bash
python run.py
```

Puis ouvrir `http://127.0.0.1:5000`.

> Si tu préfères utiliser Flask directement :
> `python -m flask --app src.running_team_vs.app run`

## Publication GitHub Pages

GitHub Pages sert uniquement des fichiers statiques. Le projet genere donc un site dans `dist/`, puis le workflow `.github/workflows/pages.yml` publie ce dossier.

1. Sur GitHub, ouvrir `Settings` -> `Pages`.
2. Dans `Build and deployment`, choisir `Source: GitHub Actions`.
3. Dans `Settings` -> `Secrets and variables` -> `Actions`, ajouter le secret `STRAVA_ACCESS_TOKEN`.
4. Optionnel : ajouter la variable `CLUB_ID` si le club change.
5. Pousser la branche `main`, ou lancer manuellement `Deploy GitHub Pages` depuis l'onglet `Actions`.

Le site sera disponible a l'adresse :

```text
https://theodtl.github.io/running_team_vs/
```

Pour tester le rendu statique en local :

```bash
python update_activities.py
python build_static.py
```

## Données

- `teams.xlsx` doit contenir : `team_name`, `members`, `distance`
- `processed_activities.xlsx` doit contenir : `activity_key`

## Notes

La version web est pensée pour afficher un classement en temps réel. Le code se base sur l'API club limitée de Strava et construit une clé de dédoublonnage à partir des champs disponibles.
