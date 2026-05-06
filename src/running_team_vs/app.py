from pathlib import Path

from flask import Flask, flash, redirect, render_template, url_for

from . import config
from .club_api import fetch_club_activities
from .ranking import update_team_distances
from .storage import load_processed, load_teams, save_processed, save_teams

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"


def build_dashboard_context(df_teams, df_processed, generated_at=None, static_site=False):
    teams = df_teams.sort_values(by="distance", ascending=False).to_dict(orient="records")
    total_distance = float(df_teams["distance"].sum()) if "distance" in df_teams else 0.0
    leader_distance = float(teams[0]["distance"]) if teams else 0.0

    for team in teams:
        distance = float(team.get("distance", 0) or 0)
        team["distance_km"] = distance / 1000
        team["progress"] = round((distance / leader_distance) * 100, 1) if leader_distance else 0

    return {
        "teams": teams,
        "activities": len(df_processed),
        "bootstrap": config.BOOTSTRAP,
        "generated_at": generated_at,
        "static_site": static_site,
        "team_count": len(teams),
        "total_distance_km": total_distance / 1000,
        "leader": teams[0] if teams else None,
    }


def refresh_data() -> int:
    if not config.STRAVA_ACCESS_TOKEN or not config.STRAVA_ACCESS_TOKEN.strip():
        raise RuntimeError("STRAVA_ACCESS_TOKEN is not configured in .env")

    df_teams = load_teams(config.TEAMS_PATH)
    df_processed = load_processed(config.PROCESSED_PATH)
    activities = fetch_club_activities(config.STRAVA_ACCESS_TOKEN, config.CLUB_ID)

    df_teams, df_processed = update_team_distances(
        df_teams,
        df_processed,
        activities,
        count_distances=not config.BOOTSTRAP,
    )
    save_teams(df_teams, config.TEAMS_PATH)
    save_processed(df_processed, config.PROCESSED_PATH)

    return len(activities)


def create_app():
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=str(STATIC_DIR),
    )
    app.secret_key = "replace-with-secure-key"

    @app.route("/")
    def index():
        if not config.STRAVA_ACCESS_TOKEN or not config.STRAVA_ACCESS_TOKEN.strip():
            flash(
                "Le token Strava n'est pas configure. Renseignez STRAVA_ACCESS_TOKEN dans .env.",
                "warning",
            )

        df_teams = load_teams(config.TEAMS_PATH)
        df_processed = load_processed(config.PROCESSED_PATH)

        return render_template("ranking.html", **build_dashboard_context(df_teams, df_processed))

    @app.route("/refresh")
    def refresh():
        try:
            activity_count = refresh_data()
            flash(f"{activity_count} activites recuperees. Classement actualise.", "success")
        except Exception as e:
            flash(f"Erreur API Strava: {e}", "error")

        return redirect(url_for("index"))

    return app


app = create_app()
