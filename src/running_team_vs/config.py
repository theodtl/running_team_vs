import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_PATH = Path(os.getenv("RUNNING_TEAM_VS_BASE_PATH", "./data")).resolve()
BASE_PATH.mkdir(parents=True, exist_ok=True)

STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN") or ""
CLUB_ID = os.getenv("CLUB_ID") or "1692198"
BOOTSTRAP = os.getenv("RUNNING_TEAM_VS_BOOTSTRAP", "False").lower() in ("1", "true", "yes")

TEAMS_PATH = BASE_PATH / "teams.xlsx"
PROCESSED_PATH = BASE_PATH / "processed_activities.xlsx"
