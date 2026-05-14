import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (PROJECT_ROOT / path).resolve()


load_dotenv(PROJECT_ROOT / ".env")

BASE_PATH = resolve_project_path(os.getenv("RUNNING_TEAM_VS_BASE_PATH", "./data"))
BASE_PATH.mkdir(parents=True, exist_ok=True)

STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN") or ""
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID") or ""
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET") or ""
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN") or ""
STRAVA_EXPIRES_AT = os.getenv("STRAVA_EXPIRES_AT") or ""
CLUB_ID = os.getenv("CLUB_ID") or "1692198"

TEAMS_PATH = BASE_PATH / "teams.xlsx"
DISTANCES_PATH = BASE_PATH / "distances.xlsx"
PROCESSED_PATH = BASE_PATH / "processed_activities.xlsx"
ACTIVITY_LOG_PATH = BASE_PATH / "activities_log.xlsx"
RESET_STATE_PATH = BASE_PATH / "reset_state.json"
LAST_REFRESH_PATH = BASE_PATH / "last_refresh.json"
STRAVA_TOKEN_STATE_PATH = resolve_project_path(os.getenv("STRAVA_TOKEN_STATE_PATH") or BASE_PATH / "strava_token.json")
STATIC_SITE_OUTPUT_PATH = resolve_project_path(os.getenv("RUNNING_TEAM_VS_STATIC_OUTPUT", "./docs"))
LOG_PATH = resolve_project_path(os.getenv("RUNNING_TEAM_VS_LOG_PATH", "./logs/update_activities.log"))
GIT_PUSH = os.getenv("RUNNING_TEAM_VS_GIT_PUSH", "False").lower() in ("1", "true", "yes")
