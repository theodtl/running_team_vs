import httpx
import pandas as pd


def _normalize_member_list(members_cell):
    if isinstance(members_cell, str):
        return [m.strip() for m in members_cell.split(",") if m.strip()]
    if isinstance(members_cell, (list, tuple, set)):
        return [str(m).strip() for m in members_cell if str(m).strip()]
    return []


def _build_activity_key(activity: dict) -> str | None:
    if not isinstance(activity, dict):
        return None

    athlete = activity.get("athlete", {}) or {}
    firstname = str(athlete.get("firstname", "")).strip()
    lastname = str(athlete.get("lastname", "")).strip()
    name = str(activity.get("name", "")).strip()
    distance = activity.get("distance", 0)
    moving_time = activity.get("moving_time", 0)
    elapsed_time = activity.get("elapsed_time", 0)
    activity_id = activity.get("id") or activity.get("activity_id")

    if activity_id is not None:
        return str(activity_id)

    if not firstname and not lastname and not name:
        return None

    parts = [firstname, lastname, name, str(distance), str(moving_time), str(elapsed_time)]
    return "|".join(part for part in parts if part)


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
        df_processed["activity_key"] = pd.Series(dtype=str)

    df_processed["activity_key"] = df_processed["activity_key"].fillna("").astype(str)
    known_keys = set(df_processed["activity_key"].tolist())

    if not isinstance(data, list):
        return df_teams, df_processed

    for activity in data:
        activity_key = _build_activity_key(activity)
        if not activity_key or activity_key in known_keys:
            continue

        athlete = activity.get("athlete", {}) or {}
        firstname = str(athlete.get("firstname", "")).strip()
        lastname = str(athlete.get("lastname", "")).strip()
        name_key = firstname + lastname
        distance = activity.get("distance", 0) or 0

        if count_distances:
            for idx, row in df_teams.iterrows():
                members_cell = row.get("members", "")
                members_list = _normalize_member_list(members_cell)

                if name_key in members_list:
                    current = row.get("distance", 0)
                    if pd.isna(current):
                        current = 0
                    df_teams.at[idx, "distance"] = float(current) + float(distance)

        df_processed.loc[len(df_processed)] = {"activity_key": activity_key}
        known_keys.add(activity_key)

    return df_teams, df_processed
