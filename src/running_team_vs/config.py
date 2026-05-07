import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_PATH = Path(os.getenv("RUNNING_TEAM_VS_BASE_PATH", "./data")).resolve()
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
STRAVA_TOKEN_STATE_PATH = Path(os.getenv("STRAVA_TOKEN_STATE_PATH") or BASE_PATH / "strava_token.json").resolve()
STATIC_SITE_OUTPUT_PATH = Path(os.getenv("RUNNING_TEAM_VS_STATIC_OUTPUT", "./docs")).resolve()
GIT_PUSH = os.getenv("RUNNING_TEAM_VS_GIT_PUSH", "False").lower() in ("1", "true", "yes")
