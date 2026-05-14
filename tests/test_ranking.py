import unittest

import pandas as pd

from src.running_team_vs.ranking import normalize_strava_key, update_team_distances


class RankingTest(unittest.TestCase):
    def test_normalize_strava_key_ignores_accents_and_case(self):
        self.assertEqual(normalize_strava_key("ThéoD."), "theod")
        self.assertEqual(normalize_strava_key("ThéoD."), normalize_strava_key("theod."))

    def test_update_team_distances_matches_accented_strava_key_to_roster(self):
        roster = pd.DataFrame({"Team A": ["TheoD."]})
        distances = pd.DataFrame([{"team_name": "Team A", "distance": 0.0}])
        processed = pd.DataFrame(columns=["activity_key"])
        activity_log = pd.DataFrame(columns=["activity_key"])
        activities = [
            {
                "athlete": {"firstname": "Théo", "lastname": "D."},
                "distance": 1000,
                "name": "Afternoon Run",
                "moving_time": 360,
                "elapsed_time": 360,
            }
        ]

        distances, processed, activity_log = update_team_distances(
            roster,
            distances,
            processed,
            activity_log,
            activities,
        )

        self.assertEqual(distances.loc[0, "distance"], 1000.0)
        self.assertEqual(activity_log.loc[0, "team_name"], "Team A")
        self.assertEqual(activity_log.loc[0, "athlete_key"], "ThéoD.")

    def test_update_team_distances_removes_deleted_strava_activity_from_current_race(self):
        roster = pd.DataFrame({"Team A": ["TheoD."]})
        distances = pd.DataFrame([{"team_name": "Team A", "distance": 1000.0}])
        activity_key = "Théo|D.|Afternoon Run|1000|360|360"
        processed = pd.DataFrame([{"activity_key": activity_key}])
        activity_log = pd.DataFrame(
            [
                {
                    "activity_key": activity_key,
                    "team_name": "Team A",
                    "athlete_key": "ThéoD.",
                    "activity_name": "Afternoon Run",
                    "distance": 1000.0,
                    "moving_time": 360,
                    "elapsed_time": 360,
                }
            ]
        )

        distances, processed, activity_log = update_team_distances(
            roster,
            distances,
            processed,
            activity_log,
            activities=[],
        )

        self.assertEqual(distances.loc[0, "distance"], 0.0)
        self.assertTrue(activity_log.empty)
        self.assertEqual(processed.loc[0, "activity_key"], activity_key)


if __name__ == "__main__":
    unittest.main()
