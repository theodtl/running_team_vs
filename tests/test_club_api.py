import unittest
from unittest.mock import patch

from src.running_team_vs.club_api import fetch_club_activities


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers, params):
        self.calls.append(params)
        return FakeResponse(self.pages[params["page"] - 1])


class ClubApiTest(unittest.TestCase):
    def test_fetch_club_activities_reads_pages_until_short_page(self):
        fake_client = FakeClient(
            [
                [{"name": "a"}, {"name": "b"}],
                [{"name": "c"}],
            ]
        )

        with patch("src.running_team_vs.club_api.httpx.Client", return_value=fake_client):
            activities = fetch_club_activities("token", "club", per_page=2, max_pages=5)

        self.assertEqual(activities, [{"name": "a"}, {"name": "b"}, {"name": "c"}])
        self.assertEqual(fake_client.calls, [{"page": 1, "per_page": 2}, {"page": 2, "per_page": 2}])


if __name__ == "__main__":
    unittest.main()
