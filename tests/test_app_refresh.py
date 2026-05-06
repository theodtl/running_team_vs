import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.running_team_vs import app as app_module
from src.running_team_vs.storage import load_processed, load_teams, save_processed, save_teams


class RefreshRouteTest(unittest.TestCase):
    def test_refresh_fetches_and_updates_excel_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            teams_path = base_path / "teams.xlsx"
            processed_path = base_path / "processed_activities.xlsx"

            save_teams(
                pd.DataFrame(
                    [
                        {
                            "team_name": "Team A",
                            "members": "AdaLovelace",
                            "distance": 0.0,
                        }
                    ]
                ),
                teams_path,
            )
            save_processed(pd.DataFrame(columns=["activity_key"]), processed_path)

            activity = {
                "id": "activity-1",
                "athlete": {"firstname": "Ada", "lastname": "Lovelace"},
                "distance": 5000,
                "name": "Morning run",
                "moving_time": 1200,
                "elapsed_time": 1300,
            }

            with (
                patch.object(app_module.config, "TEAMS_PATH", teams_path),
                patch.object(app_module.config, "PROCESSED_PATH", processed_path),
                patch.object(app_module.config, "STRAVA_ACCESS_TOKEN", "token"),
                patch.object(app_module.config, "CLUB_ID", "club"),
                patch.object(app_module.config, "BOOTSTRAP", False),
                patch.object(app_module, "fetch_club_activities", return_value=[activity]) as fetch,
            ):
                client = app_module.create_app().test_client()
                response = client.get("/refresh", follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            fetch.assert_called_once_with("token", "club")
            self.assertEqual(load_teams(teams_path).loc[0, "distance"], 5000.0)
            self.assertEqual(load_processed(processed_path).loc[0, "activity_key"], "activity-1")


if __name__ == "__main__":
    unittest.main()
