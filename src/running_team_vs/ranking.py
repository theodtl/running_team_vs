import pandas as pd


def _normalize_member_list(members_cell):
    if isinstance(members_cell, str):
        return [m.strip() for m in members_cell.split(",") if m.strip()]
    if isinstance(members_cell, (list, tuple, set)):
        return [str(m).strip() for m in members_cell if str(m).strip()]
    return []


def build_activity_key(activity: dict) -> str | None:
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

    return "|".join(
        part for part in [firstname, lastname, name, str(distance), str(moving_time), str(elapsed_time)] if part
    )


def update_team_distances(df_teams: pd.DataFrame, df_processed: pd.DataFrame, activities: list[dict], count_distances: bool = True):
    known_keys = set(df_processed["activity_key"].tolist())
    new_rows = []

    for activity in activities:
        activity_key = build_activity_key(activity)
        if not activity_key or activity_key in known_keys:
            continue

        athlete = activity.get("athlete", {}) or {}
        firstname = str(athlete.get("firstname", "")).strip()
        lastname = str(athlete.get("lastname", "")).strip()
        name_key = firstname + lastname
        distance = float(activity.get("distance", 0) or 0)

        if count_distances:
            for idx, row in df_teams.iterrows():
                members_list = _normalize_member_list(row.get("members", ""))
                if name_key in members_list:
                    current = row.get("distance", 0)
                    if pd.isna(current):
                        current = 0
                    df_teams.at[idx, "distance"] = float(current) + distance

        new_rows.append({"activity_key": activity_key})
        known_keys.add(activity_key)

    if new_rows:
        df_processed = pd.concat([df_processed, pd.DataFrame(new_rows)], ignore_index=True)

    return df_teams, df_processed
