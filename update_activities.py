#!/usr/bin/env python
"""
Update Strava club activities and persist the local Excel files.

Run manually or with a scheduled task.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.running_team_vs import config
from src.running_team_vs.club_api import fetch_club_activities
from src.running_team_vs.ranking import update_team_distances
from src.running_team_vs.storage import load_processed, load_teams, save_processed, save_teams


def main():
    if not config.STRAVA_ACCESS_TOKEN or not config.STRAVA_ACCESS_TOKEN.strip():
        print("ERROR: STRAVA_ACCESS_TOKEN is not configured in .env")
        return 1

    print("Loading data...")
    df_teams = load_teams(config.TEAMS_PATH)
    df_processed = load_processed(config.PROCESSED_PATH)

    print("Fetching Strava activities...")
    try:
        activities = fetch_club_activities(config.STRAVA_ACCESS_TOKEN, config.CLUB_ID)
    except Exception as e:
        print(f"ERROR: Strava API failed: {e}")
        return 1
    print(f"OK: {len(activities)} activities fetched")

    print("Updating distances...")
    df_teams, df_processed = update_team_distances(
        df_teams, df_processed, activities, count_distances=not config.BOOTSTRAP
    )

    print("Saving data...")
    save_teams(df_teams, config.TEAMS_PATH)
    save_processed(df_processed, config.PROCESSED_PATH)

    print("OK: Distances updated:")
    for _, row in df_teams.iterrows():
        print(f"  {row['team_name']}: {row['distance'] / 1000:.2f} km")

    return 0


if __name__ == "__main__":
    sys.exit(main())
