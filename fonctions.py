import httpx
import pandas as pd


def add_new_club_activities(
    df_teams: pd.DataFrame,
    df_processed: pd.DataFrame,
    access_token: str,
    club_id: str = "1692198",
    count_distances: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Récupère les dernières activités du club Strava et :

      - si count_distances=True :
            ajoute la distance aux équipes correspondantes
      - dans tous les cas :
            enregistre les activités comme 'traitées' dans df_processed
            (pour éviter de les recompter plus tard).

    df_teams : DataFrame avec au moins les colonnes :
        - team_name : str
        - members   : str (ex: "ThéoD.,LucasH.")
        - distance  : float (total en mètres)

    df_processed : DataFrame avec au moins la colonne :
        - activity_key : str

    Retourne :
        df_teams, df_processed mis à jour.
    """

    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://www.strava.com/api/v3/clubs/{club_id}/activities"

    with httpx.Client() as client:
        response = client.get(
            url,
            headers=headers,
            params={"page": 1, "per_page": 50},  # on récupère jusqu'à 50 dernières activités
        )
        response.raise_for_status()
        data = response.json()

    if not isinstance(df_processed, pd.DataFrame):
        df_processed = pd.DataFrame(columns=["activity_key"])

    if "activity_key" not in df_processed.columns:
        df_processed["activity_key"] = []

    known_keys = set(df_processed["activity_key"].tolist())

    for activity in data:
        firstname = activity["athlete"]["firstname"]
        lastname = activity["athlete"]["lastname"]      # ex: "D."
        name_key = firstname + lastname                # ex: "ThéoD."
        distance = activity["distance"]                # en mètres

        # clé pseudo-unique de l'activité avec ce qu'on a à dispo
        activity_key = (
            f"{firstname}|{lastname}|{activity['name']}|"
            f"{distance}|{activity['moving_time']}|{activity['elapsed_time']}"
        )

        # si déjà traitée, on ignore
        if activity_key in known_keys:
            continue

        # si on doit compter les distances dans ce run
        if count_distances:
            for idx, row in df_teams.iterrows():
                members_cell = row.get("members", "")

                if isinstance(members_cell, str):
                    members_list = [m.strip() for m in members_cell.split(",") if m.strip()]
                elif isinstance(members_cell, (list, tuple, set)):
                    members_list = list(members_cell)
                else:
                    members_list = []

                if name_key in members_list:
                    current = row.get("distance", 0)
                    if pd.isna(current):
                        current = 0
                    df_teams.at[idx, "distance"] = current + distance

        # dans tous les cas, on marque l'activité comme traitée
        df_processed.loc[len(df_processed)] = {"activity_key": activity_key}
        known_keys.add(activity_key)

    return df_teams, df_processed
