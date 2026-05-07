#!/usr/bin/env python
"""
Update Strava club activities, persist local Excel files and rebuild the static site.

Run manually or with a scheduled task.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))

from src.running_team_vs import config
from src.running_team_vs.club_api import fetch_club_activities
from src.running_team_vs.ranking import update_team_distances
from src.running_team_vs.storage import (
    build_team_view,
    load_activity_log,
    load_distances,
    load_processed,
    load_team_roster,
    save_activity_log,
    save_distances,
    save_processed,
)
from src.running_team_vs.strava_auth import get_access_token
from build_static import build_static_site


PARIS_TZ = ZoneInfo("Europe/Paris")


def should_reset_distances(now=None) -> bool:
    now = now or datetime.now(PARIS_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=PARIS_TZ)
    now = now.astimezone(PARIS_TZ)
    return now.weekday() == 0 and now.hour == 0


def _load_reset_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def reset_weekly_state_if_needed(df_distances, df_activity_log, now=None):
    now = now or datetime.now(PARIS_TZ)
    today = now.astimezone(PARIS_TZ).date().isoformat()
    state = _load_reset_state(config.RESET_STATE_PATH)

    if not should_reset_distances(now) or state.get("last_reset_date") == today:
        return df_distances, df_activity_log, False

    df_distances["distance"] = 0.0
    df_activity_log = df_activity_log.iloc[0:0].copy()
    config.RESET_STATE_PATH.write_text(json.dumps({"last_reset_date": today}, indent=2), encoding="utf-8")
    return df_distances, df_activity_log, True


def save_last_refresh(now=None) -> None:
    now = now or datetime.now(PARIS_TZ)
    config.LAST_REFRESH_PATH.write_text(
        json.dumps({"last_refresh_at": now.astimezone(PARIS_TZ).isoformat(timespec="minutes")}, indent=2),
        encoding="utf-8",
    )


def push_site_update(output_dir: Path) -> bool:
    paths = [
        str(config.DISTANCES_PATH),
        str(config.PROCESSED_PATH),
        str(config.ACTIVITY_LOG_PATH),
        str(output_dir),
    ]
    if config.RESET_STATE_PATH.exists():
        paths.append(str(config.RESET_STATE_PATH))
    if config.LAST_REFRESH_PATH.exists():
        paths.append(str(config.LAST_REFRESH_PATH))

    subprocess.run(["git", "add", *paths], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)
    if diff.returncode == 0:
        print("OK: No Git changes to push")
        return False

    subprocess.run(["git", "commit", "-m", "Update Strava data and site"], check=True)
    subprocess.run(["git", "push"], check=True)
    return True


def main():
    print("Loading data...")
    df_roster = load_team_roster(config.TEAMS_PATH)
    df_distances = load_distances(config.DISTANCES_PATH, roster=df_roster, legacy_teams_path=config.TEAMS_PATH)
    df_processed = load_processed(config.PROCESSED_PATH)
    df_activity_log = load_activity_log(config.ACTIVITY_LOG_PATH)
    df_distances, df_activity_log, did_reset = reset_weekly_state_if_needed(df_distances, df_activity_log)
    if did_reset:
        print("OK: Weekly distance reset applied for Monday 00:00-01:00 Europe/Paris")

    print("Fetching Strava activities...")
    try:
        access_token = get_access_token()
        activities = fetch_club_activities(access_token, config.CLUB_ID)
    except Exception as e:
        print(f"ERROR: Strava API failed: {e}")
        return 1
    print(f"OK: {len(activities)} activities fetched")

    print("Updating distances...")
    df_distances, df_processed, df_activity_log = update_team_distances(
        df_roster,
        df_distances,
        df_processed,
        df_activity_log,
        activities,
    )

    print("Saving data...")
    save_distances(df_distances, config.DISTANCES_PATH)
    save_processed(df_processed, config.PROCESSED_PATH)
    save_activity_log(df_activity_log, config.ACTIVITY_LOG_PATH)
    save_last_refresh()

    print("OK: Distances updated:")
    for _, row in build_team_view(df_roster, df_distances).iterrows():
        print(f"  {row['team_name']}: {row['distance'] / 1000:.2f} km")

    print("Building static site...")
    output_dir = build_static_site()
    print(f"OK: Static site built in {output_dir}")

    if config.GIT_PUSH:
        print("Pushing site update to Git...")
        pushed = push_site_update(output_dir)
        if pushed:
            print("OK: Git update pushed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
