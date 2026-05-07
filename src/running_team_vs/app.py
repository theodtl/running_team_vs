from pathlib import Path

from flask import Flask, render_template

from . import config
from .storage import build_team_view, load_distances, load_processed, load_team_roster

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
        "generated_at": generated_at,
        "static_site": static_site,
        "team_count": len(teams),
        "total_distance_km": total_distance / 1000,
        "leader": teams[0] if teams else None,
    }


def create_app():
    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=str(STATIC_DIR),
    )
    app.secret_key = "replace-with-secure-key"

    @app.route("/")
    def index():
        df_roster = load_team_roster(config.TEAMS_PATH)
        df_distances = load_distances(config.DISTANCES_PATH, roster=df_roster, legacy_teams_path=config.TEAMS_PATH)
        df_processed = load_processed(config.PROCESSED_PATH)
        df_teams = build_team_view(df_roster, df_distances)

        return render_template("ranking.html", **build_dashboard_context(df_teams, df_processed))

    return app


app = create_app()
