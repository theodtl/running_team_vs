🏃‍♂️🏆 Running VS — Jeu Strava en équipes

Objectif : créer un classement hebdomadaire où deux équipes s’affrontent pour courir le plus de kilomètres entre lundi 00h00 et dimanche 23h59, en utilisant uniquement l’API Club Activities de Strava (sans authentification des athlètes).

🚀 Fonctionnement général

Strava ne fournit ni date, ni moyens de filtrer correctement par semaine dans l'endpoint /clubs/{id}/activities.
Pour contourner cette limitation :

On récupère les 50 dernières activités du club.

Pour chaque activité, on génère une clé unique activity_key.

On maintient un fichier processed_activities.xlsx qui contient toutes les activités déjà comptées.

Seules les activités nouvelles sont ajoutées à la distance totale de l’équipe.

Chaque lundi à 00h00, on lance un mode spécial BOOTSTRAP qui :

réinitialise les distances d’équipe,

vide l’historique des activités traitées,

marque toutes les activités présentes comme déjà traitées sans les compter.

Résultat :
🔒 Aucune activité n’est comptée deux fois
🎯 Aucune activité d'avant lundi 00h00 ne pollue la nouvelle semaine

📁 Structure du projet
RunningVS/
│
├── main.py
├── functions.py
│
├── teams.xlsx
├── processed_activities.xlsx
│
└── README.md

📄 Contenu des fichiers
teams.xlsx

Un tableau avec une ligne par équipe :

team_name	members	distance
team1	ThéoD.,LucasH.,NoahB.	0
team2	AlexL.,StanislasD.,RaphC.	0

members = liste des membres séparés par des virgules
Format attendu pour chaque membre : Prénom + Initiale du nom + “.”
Exemple : ThéoD.

processed_activities.xlsx

Contient une seule colonne :

activity_key
Théo
…

Chaque ligne représente une activité déjà comptée → jamais comptée deux fois.

functions.py

Contient la fonction principale :

add_new_club_activities(df_teams, df_processed, access_token, club_id, count_distances)


Elle :

récupère les 50 dernières activités du club,

génère une clé activity_key par activité,

si l’activité n’a jamais été traitée → elle est comptée (ou non selon count_distances),

elle est ajoutée à processed_activities.

main.py

Script à exécuter régulièrement.

Deux modes :

🔹 Mode normal (BOOTSTRAP = False)

Pour une utilisation quotidienne / horaire.
Seules les nouvelles activités sont ajoutées aux distances des équipes.

🔹 Mode BOOTSTRAP (BOOTSTRAP = True)

À exécuter une seule fois au début du jeu, chaque lundi 00h00 :

Remet distance = 0 pour toutes les équipes

Vide processed_activities.xlsx

Marque toutes les activités existantes comme “déjà traitées”

Ne compte pas les distances du passé

Ensuite, repasser BOOTSTRAP = False.

🕒 Cycle d'une semaine
1️⃣ Lundi 00h00 — Début du jeu

Dans main.py :

BOOTSTRAP = True


Exécuter :

python main.py


Puis remettre :

BOOTSTRAP = False

2️⃣ Toute la semaine

Exécuter régulièrement (à la main ou en tâche planifiée) :

python main.py


→ Les distances sont mises à jour dès qu'une activité apparaît dans le club.

3️⃣ Suivi du classement

Ouvrir le fichier teams.xlsx :

team_name	distance (mètres)
team1	12340
team2	8450
🔐 Gestion du token

Le projet utilise un token Strava de type Club Admin, permettant :

GET https://www.strava.com/api/v3/clubs/{club_id}/activities


Aucun token personnel des athlètes n’est requis.

⚠️ Limitations connues

Les activités uploadées en retard (ex : montre non synchronisée pendant 24h) seront comptées lors de la semaine de publication Strava, pas la semaine réelle.

Strava retourne max 50 activités par requête → largement suffisant notre club :).

Strava ne fournit aucune date dans /clubs/{id}/activities, d’où la nécessité du système de “clé + log”.

🛠️ Extensions possibles

Export HTML ou dashboard pour affichage automatique en salle

Ajout d’un classement individuel

Ajout d’une détection automatique du lundi (sans BOOTSTRAP manuel)

Mise en place d’un cron Windows / Linux