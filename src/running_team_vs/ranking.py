import unicodedata

import pandas as pd


def normalize_strava_key(value) -> str:
    text = str(value or "").strip().casefold()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return "".join(char for char in text if char.isalnum())


def build_activity_key(activity: dict) -> str | None:
    athlete = activity.get("athlete", {}) or {}
    firstname = str(athlete.get("firstname", "")).strip()
    lastname = str(athlete.get("lastname", "")).strip()
    name = str(activity.get("name", "")).strip()
    distance = activity.get("distance", 0)
    moving_time = activity.get("moving_time", 0)
    elapsed_time = activity.get("elapsed_time", 0)

    if not firstname and not lastname and not name:
        return None

    return "|".join(
        part for part in [firstname, lastname, name, str(distance), str(moving_time), str(elapsed_time)] if part
    )


def build_strava_key(activity: dict) -> str:
    athlete = activity.get("athlete", {}) or {}
    firstname = str(athlete.get("firstname", "")).strip()
    lastname = str(athlete.get("lastname", "")).strip()
    return firstname + lastname


def build_member_team_map(df_roster: pd.DataFrame) -> dict[str, str]:
    member_team: dict[str, str] = {}
    for team_name in df_roster.columns:
        for member in df_roster[team_name].dropna():
            key = normalize_strava_key(member)
            if key:
                member_team[key] = str(team_name)
    return member_team


def ensure_distance_rows(df_distances: pd.DataFrame, team_names) -> pd.DataFrame:
    if "team_name" not in df_distances.columns:
        df_distances["team_name"] = pd.Series(dtype=str)
    if "distance" not in df_distances.columns:
        df_distances["distance"] = 0.0

    df_distances["team_name"] = df_distances["team_name"].fillna("").astype(str)
    df_distances["distance"] = df_distances["distance"].fillna(0).astype(float)

    existing = set(df_distances["team_name"].tolist())
    missing = [{"team_name": str(team_name), "distance": 0.0} for team_name in team_names if str(team_name) not in existing]
    if missing:
        df_distances = pd.concat([df_distances, pd.DataFrame(missing)], ignore_index=True)

    return df_distances


def recalculate_distances_from_log(df_distances: pd.DataFrame, df_activity_log: pd.DataFrame) -> pd.DataFrame:
    df_distances["distance"] = 0.0
    if df_activity_log.empty or "team_name" not in df_activity_log or "distance" not in df_activity_log:
        return df_distances

    logged = df_activity_log.copy()
    logged["team_name"] = logged["team_name"].fillna("").astype(str)
    logged["distance"] = logged["distance"].fillna(0).astype(float)
    distances_by_team = logged[logged["team_name"] != ""].groupby("team_name")["distance"].sum()

    for team_name, distance in distances_by_team.items():
        mask = df_distances["team_name"] == team_name
        if mask.any():
            df_distances.loc[mask, "distance"] = float(distance)

    return df_distances


def update_team_distances(
    df_roster: pd.DataFrame,
    df_distances: pd.DataFrame,
    df_processed: pd.DataFrame,
    df_activity_log: pd.DataFrame,
    activities: list[dict],
):
    df_distances = ensure_distance_rows(df_distances, df_roster.columns)
    member_team = build_member_team_map(df_roster)
    known_keys = set(df_processed["activity_key"].tolist())
    fetched_activity_keys = {
        activity_key for activity in activities if (activity_key := build_activity_key(activity))
    }
    if "activity_key" in df_activity_log:
        df_activity_log = df_activity_log[df_activity_log["activity_key"].isin(fetched_activity_keys)].copy()

    logged_keys = set(df_activity_log["activity_key"].tolist()) if "activity_key" in df_activity_log else set()
    new_rows = []
    log_rows = []

    for activity in activities:
        activity_key = build_activity_key(activity)
        if not activity_key or activity_key in logged_keys or activity_key in known_keys:
            continue

        name_key = build_strava_key(activity)
        distance = float(activity.get("distance", 0) or 0)
        moving_time = int(activity.get("moving_time", 0) or 0)
        elapsed_time = int(activity.get("elapsed_time", 0) or 0)
        activity_name = str(activity.get("name", "")).strip()
        team_name = member_team.get(normalize_strava_key(name_key))

        new_rows.append({"activity_key": activity_key})
        log_rows.append(
            {
                "activity_key": activity_key,
                "team_name": team_name or "",
                "athlete_key": name_key,
                "activity_name": activity_name,
                "distance": distance,
                "moving_time": moving_time,
                "elapsed_time": elapsed_time,
            }
        )
        known_keys.add(activity_key)
        logged_keys.add(activity_key)

    if new_rows:
        df_processed = pd.concat([df_processed, pd.DataFrame(new_rows)], ignore_index=True)
    if log_rows:
        df_activity_log = pd.concat([df_activity_log, pd.DataFrame(log_rows)], ignore_index=True)

    df_distances = recalculate_distances_from_log(df_distances, df_activity_log)

    return df_distances, df_processed, df_activity_log
