# Running Team VS

Dashboard web pour suivre un challenge Strava en équipes via l'endpoint club.

## Architecture choisie

- `src/running_team_vs/`
  - `config.py` : lecture de la configuration et des chemins
  - `club_api.py` : récupération des activités du club Strava
  - `strava_auth.py` : rafraîchissement automatique du token Strava
  - `storage.py` : lecture et écriture des fichiers Excel
  - `ranking.py` : logique de scoring et de dédoublonnage
  - `app.py` : application Flask pour afficher le classement, sans actualisation côté web
- `web/templates/` : template HTML du dashboard
- `web/static/` : CSS et assets statiques
- `data/` : fichiers de données (`teams.xlsx`, `distances.xlsx`, `processed_activities.xlsx`)
- `docs/` : site statique généré pour GitHub Pages

## Installation

1. Créer un environnement Python 3.11+
2. Installer les dépendances :

```bash
pip install -r requirements.txt
```

3. Créer ou compléter `.env` avec les variables Strava.

Variables utiles :

```env
STRAVA_CLIENT_ID=...
STRAVA_CLIENT_SECRET=...
STRAVA_REFRESH_TOKEN=...
CLUB_ID=1692198
RUNNING_TEAM_VS_BASE_PATH=./data
RUNNING_TEAM_VS_STATIC_OUTPUT=./docs
RUNNING_TEAM_VS_GIT_PUSH=False
```

## Exécution

1. Vérifier que `.env` contient les variables Strava.
2. Lancer la mise à jour complète :

```bash
python update_activities.py
```

Le script récupère les activités Strava, met à jour les fichiers Excel, puis régénère `docs/index.html`.

Pour voir le site, ouvrir `docs/index.html` dans un navigateur.

## Serveur

À terme, le serveur peut lancer une seule commande via cron :

```bash
python /chemin/vers/running_team_vs/update_activities.py
```

Si `RUNNING_TEAM_VS_GIT_PUSH=True`, le script commit et push automatiquement `docs/`, `data/distances.xlsx`, `data/processed_activities.xlsx`, l'état de reset éventuel et l'horodatage de dernière récupération.

Pour publier avec GitHub Pages, configurer `Settings` -> `Pages` avec `Source: GitHub Actions`. Le workflow présent dans `.github/workflows/pages.yml` déploie uniquement le dossier `docs/` déjà généré.

Sur le serveur, il faut que le dépôt local puisse déjà faire `git push` sans intervention interactive, par exemple via une clé SSH ou un token Git configuré côté remote.

`build_static.py` reste disponible si tu veux seulement reconstruire la page depuis les Excel existants, sans appeler Strava.

Pour remettre les compteurs de la course en cours à zéro manuellement, sans toucher au roster, au token Strava, ni aux activités déjà traitées :

```bash
python reset_data.py
```

## Données

- `teams.xlsx` contient le roster : une colonne par équipe, une cellule par participant, au format clé Strava (`PrénomNom` tel que construit par le code).
- `distances.xlsx` contient les scores : `team_name`, `distance`
- `processed_activities.xlsx` doit contenir : `activity_key`

## Notes

La version web affiche uniquement le classement déjà généré. L'actualisation complète est faite par `python update_activities.py`.

Chaque lundi entre 00:00 et 01:00 heure de Paris, le script remet automatiquement les distances à zéro une seule fois pour la date concernée. Le dédoublonnage reste basé sur les champs disponibles dans l'endpoint club Strava.

Les tokens rafraîchis sont stockés dans `data/strava_token.json`, ignoré par Git.
