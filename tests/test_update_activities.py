import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pandas as pd

import update_activities
from src.running_team_vs import config
from src.running_team_vs.storage import (
    load_activity_log,
    load_distances,
    load_processed,
    save_activity_log,
    save_distances,
    save_processed,
    save_team_roster,
)


class UpdateActivitiesTest(unittest.TestCase):
    def test_script_fetches_and_updates_separate_distance_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            teams_path = base_path / "teams.xlsx"
            distances_path = base_path / "distances.xlsx"
            processed_path = base_path / "processed_activities.xlsx"
            activity_log_path = base_path / "activities_log.xlsx"
            reset_state_path = base_path / "reset_state.json"
            last_refresh_path = base_path / "last_refresh.json"
            token_state_path = base_path / "strava_token.json"

            save_team_roster(pd.DataFrame({"Team A": ["AdaLovelace"]}), teams_path)
            save_distances(pd.DataFrame([{"team_name": "Team A", "distance": 0.0}]), distances_path)
            save_processed(pd.DataFrame(columns=["activity_key"]), processed_path)
            save_activity_log(pd.DataFrame(columns=["activity_key"]), activity_log_path)

            activity = {
                "id": "ignored-by-design",
                "athlete": {"firstname": "Ada", "lastname": "Lovelace"},
                "distance": 5000,
                "name": "Morning run",
                "moving_time": 1200,
                "elapsed_time": 1300,
            }

            with (
                patch.object(config, "TEAMS_PATH", teams_path),
                patch.object(config, "DISTANCES_PATH", distances_path),
                patch.object(config, "PROCESSED_PATH", processed_path),
                patch.object(config, "ACTIVITY_LOG_PATH", activity_log_path),
                patch.object(config, "RESET_STATE_PATH", reset_state_path),
                patch.object(config, "LAST_REFRESH_PATH", last_refresh_path),
                patch.object(config, "STRAVA_TOKEN_STATE_PATH", token_state_path),
                patch.object(config, "CLUB_ID", "club"),
                patch.object(config, "GIT_PUSH", False),
                patch.object(update_activities, "should_reset_distances", return_value=False),
                patch.object(update_activities, "get_access_token", return_value="token"),
                patch.object(update_activities, "fetch_club_activities", return_value=[activity]) as fetch,
                patch.object(update_activities, "build_static_site", return_value=base_path / "dist") as build_static,
            ):
                self.assertEqual(update_activities.main(), 0)

            fetch.assert_called_once_with("token", "club")
            build_static.assert_called_once_with()
            self.assertTrue(last_refresh_path.exists())
            self.assertEqual(load_distances(distances_path).loc[0, "distance"], 5000.0)
            activity_log = load_activity_log(activity_log_path)
            self.assertEqual(activity_log.loc[0, "athlete_key"], "AdaLovelace")
            self.assertEqual(activity_log.loc[0, "team_name"], "Team A")
            self.assertEqual(activity_log.loc[0, "activity_name"], "Morning run")
            self.assertEqual(
                load_processed(processed_path).loc[0, "activity_key"],
                "Ada|Lovelace|Morning run|5000|1200|1300",
            )

    def test_monday_midnight_paris_resets_distances_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            reset_state_path = base_path / "reset_state.json"
            distances = pd.DataFrame([{"team_name": "Team A", "distance": 1234.0}])
            activity_log = pd.DataFrame([{"activity_key": "activity-1"}])
            now = datetime(2026, 5, 4, 0, 30, tzinfo=ZoneInfo("Europe/Paris"))

            with patch.object(config, "RESET_STATE_PATH", reset_state_path):
                reset_distances, reset_log, did_reset = update_activities.reset_weekly_state_if_needed(
                    distances,
                    activity_log,
                    now=now,
                )
                reset_again, reset_log_again, did_reset_again = update_activities.reset_weekly_state_if_needed(
                    reset_distances,
                    reset_log,
                    now=now,
                )

            self.assertTrue(did_reset)
            self.assertEqual(reset_distances.loc[0, "distance"], 0.0)
            self.assertTrue(reset_log.empty)
            self.assertFalse(did_reset_again)
            self.assertEqual(reset_again.loc[0, "distance"], 0.0)
            self.assertTrue(reset_log_again.empty)

    def test_reset_window_is_monday_00_to_01_paris(self):
        paris = ZoneInfo("Europe/Paris")
        self.assertTrue(update_activities.should_reset_distances(datetime(2026, 5, 4, 0, 59, tzinfo=paris)))
        self.assertFalse(update_activities.should_reset_distances(datetime(2026, 5, 4, 1, 0, tzinfo=paris)))
        self.assertFalse(update_activities.should_reset_distances(datetime(2026, 5, 5, 0, 30, tzinfo=paris)))


if __name__ == "__main__":
    unittest.main()
