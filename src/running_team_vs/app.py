from pathlib import Path

from flask import Flask, render_template

from . import config
from .storage import build_team_view, load_activity_log, load_distances, load_processed, load_team_roster

BASE_DIR = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"


def _members_from_team(team):
    members = str(team.get("members", "") or "")
    return [member.strip() for member in members.split(",") if member.strip()]


def _build_member_stats(team_name, members, activity_log):
    stats = []
    team_log = activity_log[activity_log["team_name"] == team_name] if activity_log is not None else None

    for member in members:
        member_log = team_log[team_log["athlete_key"] == member] if team_log is not None else None
        distance = float(member_log["distance"].sum()) if member_log is not None and not member_log.empty else 0.0
        activities = int(len(member_log)) if member_log is not None else 0
        last_activity = ""
        if member_log is not None and not member_log.empty:
            last_activity = str(member_log.iloc[-1].get("activity_name", "") or "")

        stats.append(
            {
                "name": member,
                "distance_km": distance / 1000,
                "activities": activities,
                "last_activity": last_activity,
            }
        )

    return sorted(stats, key=lambda member: member["distance_km"], reverse=True)


def build_dashboard_context(df_teams, df_processed, df_activity_log=None, generated_at=None, static_site=False):
    teams = df_teams.sort_values(by="distance", ascending=False).to_dict(orient="records")
    total_distance = float(df_teams["distance"].sum()) if "distance" in df_teams else 0.0
    leader_distance = float(teams[0]["distance"]) if teams else 0.0

    for team in teams:
        distance = float(team.get("distance", 0) or 0)
        members = _members_from_team(team)
        team["distance_km"] = distance / 1000
        team["progress"] = round((distance / leader_distance) * 100, 1) if leader_distance else 0
        team["member_count"] = len(members)
        team["member_stats"] = _build_member_stats(team["team_name"], members, df_activity_log)
        team["activity_count"] = sum(member["activities"] for member in team["member_stats"])

    runner_up_distance = float(teams[1]["distance"]) if len(teams) > 1 else 0.0
    leader_gap_km = max(leader_distance - runner_up_distance, 0.0) / 1000
    total_members = sum(team["member_count"] for team in teams)

    return {
        "teams": teams,
        "generated_at": generated_at,
        "static_site": static_site,
        "team_count": len(teams),
        "total_members": total_members,
        "total_distance_km": total_distance / 1000,
        "leader": teams[0] if teams else None,
        "leader_gap_km": leader_gap_km,
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
        df_activity_log = load_activity_log(config.ACTIVITY_LOG_PATH)
        df_teams = build_team_view(df_roster, df_distances)

        return render_template("ranking.html", **build_dashboard_context(df_teams, df_processed, df_activity_log))

    return app


app = create_app()
