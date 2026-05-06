import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

import build_static
from src.running_team_vs import config
from src.running_team_vs.storage import save_processed, save_teams


class StaticBuildTest(unittest.TestCase):
    def test_build_static_site_writes_github_pages_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            teams_path = base_path / "teams.xlsx"
            processed_path = base_path / "processed_activities.xlsx"
            output_path = base_path / "dist"

            save_teams(
                pd.DataFrame(
                    [
                        {
                            "team_name": "Team A",
                            "members": "AdaLovelace",
                            "distance": 5000.0,
                        }
                    ]
                ),
                teams_path,
            )
            save_processed(pd.DataFrame([{"activity_key": "activity-1"}]), processed_path)

            with (
                patch.object(config, "TEAMS_PATH", teams_path),
                patch.object(config, "PROCESSED_PATH", processed_path),
            ):
                build_static.build_static_site(output_path)

            index = (output_path / "index.html").read_text(encoding="utf-8")
            self.assertIn("Running Team VS", index)
            self.assertIn("Team A", index)
            self.assertIn("static/styles.css", index)
            self.assertNotIn("static/story-track.jpg", index)
            self.assertNotIn("Activités traitées", index)
            self.assertNotIn("Bootstrap", index)
            self.assertIn("Voir la dernière version", index)
            self.assertIn("heure de Paris", index)
            self.assertIn("refresh=", index)
            self.assertIn('href="./"', index)
            self.assertTrue((output_path / ".nojekyll").exists())
            self.assertTrue((output_path / "static" / "styles.css").exists())
            self.assertFalse((output_path / "static" / "story-track.jpg").exists())


if __name__ == "__main__":
    unittest.main()
