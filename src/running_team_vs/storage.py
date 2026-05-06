import pandas as pd


def load_teams(path):
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["team_name", "members", "distance"])

    if "distance" not in df.columns:
        df["distance"] = 0.0
    else:
        df["distance"] = df["distance"].fillna(0).astype(float)

    return df


def load_processed(path):
    try:
        df = pd.read_excel(path)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["activity_key"])

    if "activity_key" not in df.columns:
        df["activity_key"] = pd.Series(dtype=str)

    df["activity_key"] = df["activity_key"].fillna("").astype(str)
    return df


def save_teams(df, path):
    df.to_excel(path, index=False)


def save_processed(df, path):
    df.to_excel(path, index=False)
