import pandas as pd

ACTIVITY_LOG_COLUMNS = [
    "activity_key",
    "team_name",
    "athlete_key",
    "activity_name",
    "distance",
    "moving_time",
    "elapsed_time",
]


def _split_members(members_cell):
    if isinstance(members_cell, str):
        return [m.strip() for m in members_cell.split(",") if m.strip()]
    if isinstance(members_cell, (list, tuple, set)):
        return [str(m).strip() for m in members_cell if str(m).strip()]
    return []


def _legacy_teams_to_roster(df):
    teams = {}
    for _, row in df.iterrows():
        team_name = str(row.get("team_name", "")).strip()
        if team_name:
            teams[team_name] = _split_members(row.get("members", ""))
    return pd.DataFrame.from_dict(teams, orient="index").transpose() if teams else pd.DataFrame()


def load_team_roster(path):
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        return pd.DataFrame()

    if {"team_name", "members"}.issubset(df.columns):
        return _legacy_teams_to_roster(df)

    return df.dropna(how="all")


def save_team_roster(df, path):
    df.to_excel(path, index=False)


def load_distances(path, roster=None, legacy_teams_path=None):
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["team_name", "distance"])

        if legacy_teams_path:
            try:
                legacy = pd.read_excel(legacy_teams_path)
            except FileNotFoundError:
                legacy = pd.DataFrame()
            if {"team_name", "distance"}.issubset(legacy.columns):
                df = legacy[["team_name", "distance"]].copy()

    if "distance" not in df.columns:
        df["distance"] = 0.0
    else:
        df["distance"] = df["distance"].fillna(0).astype(float)
    if "team_name" not in df.columns:
        df["team_name"] = pd.Series(dtype=str)

    if roster is not None:
        existing = set(df["team_name"].fillna("").astype(str))
        missing = [{"team_name": str(team_name), "distance": 0.0} for team_name in roster.columns if str(team_name) not in existing]
        if missing:
            df = pd.concat([df, pd.DataFrame(missing)], ignore_index=True)

    df["team_name"] = df["team_name"].fillna("").astype(str)
    return df[["team_name", "distance"]]


def save_distances(df, path):
    df.to_excel(path, index=False)


def build_team_view(roster, distances):
    rows = []
    distances_by_team = dict(zip(distances["team_name"], distances["distance"], strict=False))
    for team_name in roster.columns:
        members = [str(member).strip() for member in roster[team_name].dropna() if str(member).strip()]
        rows.append(
            {
                "team_name": str(team_name),
                "members": ", ".join(members),
                "distance": float(distances_by_team.get(str(team_name), 0) or 0),
            }
        )
    return pd.DataFrame(rows, columns=["team_name", "members", "distance"])


def load_teams(path):
    roster = load_team_roster(path)
    distances = load_distances(path.with_name("distances.xlsx"), roster=roster, legacy_teams_path=path)
    return build_team_view(roster, distances)


def save_teams(df, path):
    if {"team_name", "members"}.issubset(df.columns):
        save_team_roster(_legacy_teams_to_roster(df), path)
    else:
        save_team_roster(df, path)


def load_processed(path):
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["activity_key"])

    if "activity_key" not in df.columns:
        df["activity_key"] = pd.Series(dtype=str)

    df["activity_key"] = df["activity_key"].fillna("").astype(str)
    return df


def save_processed(df, path):
    df.to_excel(path, index=False)


def load_activity_log(path):
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=ACTIVITY_LOG_COLUMNS)

    for column in ACTIVITY_LOG_COLUMNS:
        if column not in df.columns:
            df[column] = "" if column not in {"distance", "moving_time", "elapsed_time"} else 0

    df["activity_key"] = df["activity_key"].fillna("").astype(str)
    df["team_name"] = df["team_name"].fillna("").astype(str)
    df["athlete_key"] = df["athlete_key"].fillna("").astype(str)
    df["activity_name"] = df["activity_name"].fillna("").astype(str)
    df["distance"] = df["distance"].fillna(0).astype(float)
    df["moving_time"] = df["moving_time"].fillna(0).astype(int)
    df["elapsed_time"] = df["elapsed_time"].fillna(0).astype(int)

    return df[ACTIVITY_LOG_COLUMNS]


def save_activity_log(df, path):
    df.to_excel(path, index=False)
