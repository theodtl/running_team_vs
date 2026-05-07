#!/usr/bin/env python
"""Build the static site into dist/."""

import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import render_template

from src.running_team_vs import config
from src.running_team_vs.app import build_dashboard_context, create_app
from src.running_team_vs.storage import build_team_view, load_distances, load_processed, load_team_roster

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "web" / "static"


def build_static_site(output_dir: Path | None = None) -> Path:
    output_dir = output_dir or config.STATIC_SITE_OUTPUT_PATH
    df_roster = load_team_roster(config.TEAMS_PATH)
    df_distances = load_distances(config.DISTANCES_PATH, roster=df_roster, legacy_teams_path=config.TEAMS_PATH)
    df_teams = build_team_view(df_roster, df_distances)
    df_processed = load_processed(config.PROCESSED_PATH)

    app = create_app()
    with app.test_request_context("/"):
        context = build_dashboard_context(
            df_teams,
            df_processed,
            generated_at=datetime.now(ZoneInfo("Europe/Paris")).strftime("%d/%m/%Y %H:%M"),
            static_site=True,
        )
        html = render_template("ranking.html", **context)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    (output_dir / "index.html").write_text(html, encoding="utf-8")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copytree(STATIC_DIR, output_dir / "static")

    return output_dir


def main() -> int:
    output_dir = build_static_site()
    print(f"Static site built in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
