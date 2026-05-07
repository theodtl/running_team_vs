import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import build_static
from src.running_team_vs import config
from src.running_team_vs.storage import save_activity_log, save_distances, save_processed, save_team_roster


class StaticBuildTest(unittest.TestCase):
    def test_build_static_site_writes_static_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            teams_path = base_path / "teams.xlsx"
            distances_path = base_path / "distances.xlsx"
            processed_path = base_path / "processed_activities.xlsx"
            activity_log_path = base_path / "activities_log.xlsx"
            last_refresh_path = base_path / "last_refresh.json"
            output_path = base_path / "dist"

            save_team_roster(pd.DataFrame({"Team A": ["AdaLovelace"]}), teams_path)
            save_distances(pd.DataFrame([{"team_name": "Team A", "distance": 5000.0}]), distances_path)
            save_processed(pd.DataFrame([{"activity_key": "activity-1"}]), processed_path)
            save_activity_log(pd.DataFrame(columns=["activity_key"]), activity_log_path)

            with (
                patch.object(config, "TEAMS_PATH", teams_path),
                patch.object(config, "DISTANCES_PATH", distances_path),
                patch.object(config, "PROCESSED_PATH", processed_path),
                patch.object(config, "ACTIVITY_LOG_PATH", activity_log_path),
                patch.object(config, "LAST_REFRESH_PATH", last_refresh_path),
            ):
                build_static.build_static_site(output_path)

            index = (output_path / "index.html").read_text(encoding="utf-8")
            self.assertIn("Running Team VS", index)
            self.assertIn("Team A", index)
            self.assertIn("Team explorer", index)
            self.assertIn("AdaLovelace", index)
            self.assertIn("Participants", index)
            self.assertNotIn("Activités vues", index)
            self.assertIn("Fin du round", index)
            self.assertIn("data-countdown", index)
            self.assertIn("Europe/Paris", index)
            self.assertIn("static/styles.css", index)
            self.assertIn("?v=", index)
            self.assertNotIn("static/story-track.jpg", index)
            self.assertNotIn("Activités traitées", index)
            self.assertNotIn("Bootstrap", index)
            self.assertNotIn("Mis à jour", index)
            self.assertTrue((output_path / ".nojekyll").exists())
            self.assertTrue((output_path / "static" / "styles.css").exists())
            self.assertFalse((output_path / "static" / "story-track.jpg").exists())

    def test_build_static_site_uses_last_refresh_timestamp(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            teams_path = base_path / "teams.xlsx"
            distances_path = base_path / "distances.xlsx"
            processed_path = base_path / "processed_activities.xlsx"
            activity_log_path = base_path / "activities_log.xlsx"
            last_refresh_path = base_path / "last_refresh.json"
            output_path = base_path / "dist"

            save_team_roster(pd.DataFrame({"Team A": ["AdaLovelace"]}), teams_path)
            save_distances(pd.DataFrame([{"team_name": "Team A", "distance": 5000.0}]), distances_path)
            save_processed(pd.DataFrame([{"activity_key": "activity-1"}]), processed_path)
            save_activity_log(
                pd.DataFrame(
                    [
                        {
                            "activity_key": "activity-1",
                            "team_name": "Team A",
                            "athlete_key": "AdaLovelace",
                            "activity_name": "Morning run",
                            "distance": 5000.0,
                            "moving_time": 1200,
                            "elapsed_time": 1300,
                        }
                    ]
                ),
                activity_log_path,
            )
            last_refresh_path.write_text('{"last_refresh_at": "2026-05-07T14:30:00+02:00"}', encoding="utf-8")

            with (
                patch.object(config, "TEAMS_PATH", teams_path),
                patch.object(config, "DISTANCES_PATH", distances_path),
                patch.object(config, "PROCESSED_PATH", processed_path),
                patch.object(config, "ACTIVITY_LOG_PATH", activity_log_path),
                patch.object(config, "LAST_REFRESH_PATH", last_refresh_path),
            ):
                build_static.build_static_site(output_path)

            index = (output_path / "index.html").read_text(encoding="utf-8")
            self.assertIn("Mis à jour 07/05/2026 14:30 heure de Paris", index)
            self.assertIn("Morning run", index)


if __name__ == "__main__":
    unittest.main()
