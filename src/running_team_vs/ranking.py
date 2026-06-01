import unicodedata

import pandas as pd


def normalize_strava_key(value) -> str:
    text = str(value or "").strip().casefold()
    text = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return "".join(char for char in text if char.isalnum())


def _distance_key(value) -> str:
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return "0.000"


def _time_key(value) -> str:
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return "0"


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
        part
        for part in [
            firstname,
            lastname,
            name,
            str(distance),
            str(moving_time),
            str(elapsed_time),
        ]
        if part
    )


def build_strava_key(activity: dict) -> str:
    athlete = activity.get("athlete", {}) or {}
    firstname = str(athlete.get("firstname", "")).strip()
    lastname = str(athlete.get("lastname", "")).strip()
    return firstname + lastname


def build_activity_fingerprint(activity: dict) -> str:
    return "|".join(
        [
            normalize_strava_key(build_strava_key(activity)),
            _distance_key(activity.get("distance", 0)),
            _time_key(activity.get("moving_time", 0)),
            _time_key(activity.get("elapsed_time", 0)),
        ]
    )


def build_logged_fingerprint(row) -> str:
    return "|".join(
        [
            normalize_strava_key(row.get("athlete_key", "")),
            _distance_key(row.get("distance", 0)),
            _time_key(row.get("moving_time", 0)),
            _time_key(row.get("elapsed_time", 0)),
        ]
    )


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
    missing = [
        {"team_name": str(team_name), "distance": 0.0}
        for team_name in team_names
        if str(team_name) not in existing
    ]
    if missing:
        df_distances = pd.concat([df_distances, pd.DataFrame(missing)], ignore_index=True)

    return df_distances


def recalculate_distances_from_log(
    df_distances: pd.DataFrame,
    df_activity_log: pd.DataFrame,
) -> pd.DataFrame:
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

    logged_fingerprints = {
        build_logged_fingerprint(row): index
        for index, row in df_activity_log.iterrows()
    }

    new_processed_rows = []

    for activity in activities:
        activity_key = build_activity_key(activity)
        if not activity_key:
            continue

        name_key = build_strava_key(activity)
        activity_name = str(activity.get("name", "")).strip()
        team_name = member_team.get(normalize_strava_key(name_key))
        fingerprint = build_activity_fingerprint(activity)

        if fingerprint in logged_fingerprints:
            index = logged_fingerprints[fingerprint]
            df_activity_log.loc[index, "activity_name"] = activity_name
            df_activity_log.loc[index, "athlete_key"] = name_key
            if team_name:
                df_activity_log.loc[index, "team_name"] = team_name

            if activity_key not in known_keys:
                new_processed_rows.append({"activity_key": activity_key})
                known_keys.add(activity_key)
            continue

        if activity_key in known_keys:
            continue

        row = {
            "activity_key": activity_key,
            "team_name": team_name or "",
            "athlete_key": name_key,
            "activity_name": activity_name,
            "distance": float(activity.get("distance", 0) or 0),
            "moving_time": int(activity.get("moving_time", 0) or 0),
            "elapsed_time": int(activity.get("elapsed_time", 0) or 0),
        }

        df_activity_log = pd.concat(
            [df_activity_log, pd.DataFrame([row])],
            ignore_index=True,
        )
        logged_fingerprints[fingerprint] = len(df_activity_log) - 1
        new_processed_rows.append({"activity_key": activity_key})
        known_keys.add(activity_key)

    if new_processed_rows:
        df_processed = pd.concat(
            [df_processed, pd.DataFrame(new_processed_rows)],
            ignore_index=True,
        )

    df_distances = recalculate_distances_from_log(df_distances, df_activity_log)

    return df_distances, df_processed, df_activity_log
