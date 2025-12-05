import pandas as pd
from fonctions import add_new_club_activities

# ================== PARAMÈTRES GÉNÉRAUX ==================

ACCESS_TOKEN = "44e614821ec3ad9aae578fd1860bf40f60adc01f"

BASE_PATH = r"C:\Users\duthilt-Utilisateur\Desktop\ESIEE\Club-Running\teams_vs"
PATH_TEAMS = fr"{BASE_PATH}\teams.xlsx"
PATH_PROCESSED = fr"{BASE_PATH}\processed_activities.xlsx"

# Mettre à True uniquement au début du jeu (lundi 00h00)
BOOTSTRAP = True  # <--- tu changes cette ligne quand tu veux réinitialiser une semaine

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
        club_id="1692198",
        count_distances=False,  # on ne compte pas le passé
    )
else:
    # Mode normal : on ajoute les nouvelles activités aux distances d'équipe
    print("[NORMAL] Mise à jour des équipes avec les nouvelles activités.")

    df_teams, df_processed = add_new_club_activities(
        df_teams=df_teams,
        df_processed=df_processed,
        access_token=ACCESS_TOKEN,
        club_id="1692198",
        count_distances=True,  # on compte les distances
    )

# ================== AFFICHAGE ==================

print("===== Distances par équipe (mètres) =====")
print(df_teams[["team_name", "distance"]])

# ================== SAUVEGARDE ==================

df_teams.to_excel(PATH_TEAMS, index=False)
df_processed.to_excel(PATH_PROCESSED, index=False)

print("Fichiers mis à jour.")
