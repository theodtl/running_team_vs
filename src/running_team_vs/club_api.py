import httpx


def fetch_club_activities(access_token: str, club_id: str, page: int = 1, per_page: int = 50) -> list[dict]:
    """Récupère les activités récentes du club Strava."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://www.strava.com/api/v3/clubs/{club_id}/activities"

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                url,
                headers=headers,
                params={"page": page, "per_page": per_page},
            )
            response.raise_for_status()
            data = response.json()
    except (httpx.TimeoutException, httpx.RequestError) as e:
        print(f"Strava API error: {e}")
        return []

    if not isinstance(data, list):
        return []

    return data
