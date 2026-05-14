import httpx


def fetch_club_activities(access_token: str, club_id: str, per_page: int = 200, max_pages: int = 5) -> list[dict]:
    """Récupère les activités récentes du club Strava avec pagination."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://www.strava.com/api/v3/clubs/{club_id}/activities"
    activities: list[dict] = []

    try:
        with httpx.Client(timeout=10.0) as client:
            for page in range(1, max_pages + 1):
                response = client.get(
                    url,
                    headers=headers,
                    params={"page": page, "per_page": per_page},
                )
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, list):
                    raise RuntimeError("Strava API returned an unexpected response")
                if not data:
                    break

                activities.extend(data)
                if len(data) < per_page:
                    break
    except (httpx.TimeoutException, httpx.RequestError) as e:
        raise RuntimeError(f"Strava API error: {e}") from e

    return activities
