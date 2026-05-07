import json
import time
from pathlib import Path

import httpx

from . import config

TOKEN_URL = "https://www.strava.com/oauth/token"
REFRESH_MARGIN_SECONDS = 3600


class StravaAuthError(RuntimeError):
    pass


def _load_token_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _save_token_state(path: Path, token_state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(token_state, indent=2), encoding="utf-8")


def _expires_at(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _token_from_env_and_state() -> dict:
    token_state = _load_token_state(config.STRAVA_TOKEN_STATE_PATH)
    return {
        "access_token": token_state.get("access_token") or config.STRAVA_ACCESS_TOKEN,
        "refresh_token": token_state.get("refresh_token") or config.STRAVA_REFRESH_TOKEN,
        "expires_at": _expires_at(token_state.get("expires_at") or config.STRAVA_EXPIRES_AT),
    }


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    response = httpx.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()

    if not data.get("access_token") or not data.get("refresh_token") or not data.get("expires_at"):
        raise StravaAuthError("Strava did not return a complete token response")

    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": int(data["expires_at"]),
    }


def get_access_token() -> str:
    token_state = _token_from_env_and_state()
    if token_state["access_token"] and token_state["expires_at"] > int(time.time()) + REFRESH_MARGIN_SECONDS:
        return token_state["access_token"]

    if not config.STRAVA_CLIENT_ID or not config.STRAVA_CLIENT_SECRET or not token_state["refresh_token"]:
        if token_state["access_token"]:
            return token_state["access_token"]
        raise StravaAuthError(
            "Configure STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET and STRAVA_REFRESH_TOKEN to refresh Strava tokens"
        )

    refreshed = refresh_access_token(
        config.STRAVA_CLIENT_ID,
        config.STRAVA_CLIENT_SECRET,
        token_state["refresh_token"],
    )
    _save_token_state(config.STRAVA_TOKEN_STATE_PATH, refreshed)
    return refreshed["access_token"]
