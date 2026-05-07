import pandas as pd


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
            key = str(member).strip()
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
    new_rows = []
    log_rows = []

    for activity in activities:
        activity_key = build_activity_key(activity)
        if not activity_key or activity_key in known_keys:
            continue

        name_key = build_strava_key(activity)
        distance = float(activity.get("distance", 0) or 0)
        moving_time = int(activity.get("moving_time", 0) or 0)
        elapsed_time = int(activity.get("elapsed_time", 0) or 0)
        activity_name = str(activity.get("name", "")).strip()
        team_name = member_team.get(name_key)

        if team_name:
            mask = df_distances["team_name"] == team_name
            current = df_distances.loc[mask, "distance"].iloc[0] if mask.any() else 0
            if pd.isna(current):
                current = 0
            df_distances.loc[mask, "distance"] = float(current) + distance

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

    if new_rows:
        df_processed = pd.concat([df_processed, pd.DataFrame(new_rows)], ignore_index=True)
    if log_rows:
        df_activity_log = pd.concat([df_activity_log, pd.DataFrame(log_rows)], ignore_index=True)

    return df_distances, df_processed, df_activity_log
