import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from fonctions import add_new_club_activities

# ================== PARAMÈTRES GÉNÉRAUX ==================

load_dotenv()

ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN", "")
if not ACCESS_TOKEN:
    raise RuntimeError("STRAVA_ACCESS_TOKEN doit être défini dans les variables d'environnement")

CLUB_ID = os.getenv("CLUB_ID", "1692198")
BASE_PATH = Path(os.getenv("RUNNING_TEAM_VS_BASE_PATH", "./data")).resolve()
BASE_PATH.mkdir(parents=True, exist_ok=True)
PATH_TEAMS = BASE_PATH / "teams.xlsx"
PATH_PROCESSED = BASE_PATH / "processed_activities.xlsx"

# Mettre à True uniquement au début du jeu (lundi 00h00) ou via la variable d'environnement
BOOTSTRAP = os.getenv("RUNNING_TEAM_VS_BOOTSTRAP", "False").lower() in ("1", "true", "yes")

# ================== CHARGEMENT DES DONNÉES ==================

# Chargement des équipes (1 ligne = 1 équipe)
# colonnes attendues :
#   - team_name : str
#   - members   : str => "ThéoD.,LucasH.,NoahB."
#   - distance  : float (peut être absent au premier run)
df_teams = pd.read_excel(PATH_TEAMS)

if "distance" not in df_teams.columns:
    df_teams["distance"] = 0.0
else:
    df_teams["distance"] = df_teams["distance"].fillna(0).astype(float)

# Chargement des activités déjà traitées
try:
    df_processed = pd.read_excel(PATH_PROCESSED)
except FileNotFoundError:
    df_processed = pd.DataFrame(columns=["activity_key"])

# ================== LOGIQUE BOOTSTRAP / NORMAL ==================

if BOOTSTRAP:
    # Mode "début de jeu" (lundi 00h00) :
    # - on remet les distances d'équipe à 0
    # - on vide les activités traitées
    # - on marque les activités existantes comme déjà vues SANS compter les distances
    print("[BOOTSTRAP] Réinitialisation des distances et des activités traitées.")

    df_teams["distance"] = 0.0
    df_processed = pd.DataFrame(columns=["activity_key"])

    df_teams, df_processed = add_new_club_activities(
        df_teams=df_teams,
        df_processed=df_processed,
        access_token=ACCESS_TOKEN,
        club_id=CLUB_ID,
        count_distances=False,  # on ne compte pas le passé
    )
else:
    # Mode normal : on ajoute les nouvelles activités aux distances d'équipe
    print("[NORMAL] Mise à jour des équipes avec les nouvelles activités.")

    df_teams, df_processed = add_new_club_activities(
        df_teams=df_teams,
        df_processed=df_processed,
        access_token=ACCESS_TOKEN,
        club_id=CLUB_ID,
        count_distances=True,  # on compte les distances
    )

# ================== AFFICHAGE ==================

print("===== Distances par équipe (mètres) =====")
print(df_teams[["team_name", "distance"]])

# ================== SAUVEGARDE ==================

df_teams.to_excel(PATH_TEAMS, index=False)
df_processed.to_excel(PATH_PROCESSED, index=False)

print("Fichiers mis à jour.")
