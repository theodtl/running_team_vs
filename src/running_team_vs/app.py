from pathlib import Path

from flask import Flask, flash, redirect, render_template, url_for

from . import config
from .club_api import fetch_club_activities
from .ranking import update_team_distances
from .storage import load_processed, load_teams, save_processed, save_teams

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"


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
        teams = df_teams.sort_values(by="distance", ascending=False).to_dict(orient="records")

        return render_template(
            "ranking.html",
            teams=teams,
            activities=len(df_processed),
            bootstrap=config.BOOTSTRAP,
            generated_at=None,
            static_site=False,
        )

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
