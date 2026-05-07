🏃‍♂️🏆 Running VS — Jeu Strava en équipes

Objectif : créer un classement hebdomadaire où deux équipes s’affrontent pour courir le plus de kilomètres entre lundi 00h00 et dimanche 23h59, en utilisant uniquement l’API Club Activities de Strava (sans authentification des athlètes).

🚀 Fonctionnement général

Strava ne fournit ni date, ni moyens de filtrer correctement par semaine dans l'endpoint /clubs/{id}/activities.
Pour contourner cette limitation :

On récupère les activités récentes du club avec pagination.

Pour chaque activité, on génère une clé unique activity_key.

On maintient un fichier processed_activities.xlsx qui contient toutes les activités déjà comptées.

Seules les activités nouvelles sont ajoutées à la distance totale de l’équipe.

Chaque lundi entre 00h00 et 01h00, heure de Paris, le script détecte automatiquement le début de semaine et :

réinitialise les distances d’équipe une seule fois pour la date concernée.

Résultat :
🔒 Aucune activité n’est comptée deux fois
🎯 Aucune activité d'avant lundi 00h00 ne pollue la nouvelle semaine

📄 Contenu des fichiers
teams.xlsx

Un tableau de roster avec une colonne par équipe :

Team 1	Team 2
TheoD.	AlexL.
LucasH.	StanislasD.
NoahB.	RaphC.

Chaque cellule contient la clé Strava du participant.

distances.xlsx

Contient les scores :

team_name	distance
Team 1	0
Team 2	0

processed_activities.xlsx

Contient une seule colonne :

activity_key

Chaque ligne représente une activité déjà comptée → jamais comptée deux fois.

functions.py

La logique actuelle vit dans src/running_team_vs/.

update_activities.py

Script à exécuter régulièrement, à la main ou via cron.

Il :

récupère ou rafraîchit le token Strava,

récupère les activités du club avec pagination,

génère une clé activity_key par activité,

si l’activité n’a jamais été traitée → elle est comptée,

elle est ajoutée à processed_activities.

Le flux principal est update_activities.py + src/running_team_vs/.

Le script reconstruit aussi le site statique dans docs/index.html.

Si RUNNING_TEAM_VS_GIT_PUSH=True, le script commit et push automatiquement les fichiers nécessaires pour GitHub Pages.

L'heure affichée sur la page correspond à la dernière récupération Strava réussie, stockée dans data/last_refresh.json.

🕒 Cycle d'une semaine
1️⃣ Lundi 00h00-01h00 — Début du jeu

Exécuter ou laisser le cron exécuter :

python update_activities.py

Le reset des distances est automatique.

2️⃣ Toute la semaine

Exécuter régulièrement (à la main ou en tâche planifiée) :

python update_activities.py


→ Les distances sont mises à jour dès qu'une activité apparaît dans le club.

3️⃣ Suivi du classement

Ouvrir le dashboard ou le fichier distances.xlsx :

team_name	distance (mètres)
team1	12340
team2	8450
🔐 Gestion du token

Le projet utilise OAuth Strava avec refresh automatique.

Variables nécessaires :

STRAVA_CLIENT_ID
STRAVA_CLIENT_SECRET
STRAVA_REFRESH_TOKEN

Variables optionnelles :

STRAVA_ACCESS_TOKEN
STRAVA_EXPIRES_AT

Le token permet :

GET https://www.strava.com/api/v3/clubs/{club_id}/activities

Les nouveaux tokens sont stockés dans data/strava_token.json, fichier ignoré par Git.


Aucun token personnel des athlètes n’est requis.

⚠️ Limitations connues

Les activités uploadées en retard (ex : montre non synchronisée pendant 24h) seront comptées lors de leur apparition dans l'endpoint club, pas forcément la semaine réelle.

Strava est paginé. Le projet récupère plusieurs pages.

Strava ne fournit aucune date dans /clubs/{id}/activities, d’où la nécessité du système de “clé + log”.

🛠️ Extensions possibles

Export HTML ou dashboard pour affichage automatique en salle

Ajout d’un classement individuel

Mise en place d’un mapping d'alias si les clés Strava changent
