#!/usr/bin/env python
"""Build the GitHub Pages static site into dist/."""

import shutil
from datetime import datetime
from pathlib import Path

from flask import render_template

from src.running_team_vs import config
from src.running_team_vs.app import build_dashboard_context, create_app
from src.running_team_vs.storage import load_processed, load_teams

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
STATIC_DIR = BASE_DIR / "web" / "static"


def build_static_site(output_dir: Path = DIST_DIR) -> Path:
    df_teams = load_teams(config.TEAMS_PATH)
    df_processed = load_processed(config.PROCESSED_PATH)

    app = create_app()
    with app.test_request_context("/"):
        context = build_dashboard_context(
            df_teams,
            df_processed,
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
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
