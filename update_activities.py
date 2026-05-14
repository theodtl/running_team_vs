#!/usr/bin/env python
"""
Update Strava club activities, persist local Excel files and rebuild the static site.

Run manually or with a scheduled task.
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))

from src.running_team_vs import config
from src.running_team_vs.club_api import fetch_club_activities
from src.running_team_vs.ranking import update_team_distances
from src.running_team_vs.storage import (
    build_team_view,
    load_activity_log,
    load_distances,
    load_processed,
    load_team_roster,
    save_activity_log,
    save_distances,
    save_processed,
)
from src.running_team_vs.strava_auth import get_access_token
from build_static import build_static_site


PARIS_TZ = ZoneInfo("Europe/Paris")
LOGGER = logging.getLogger(__name__)


def setup_logging(log_path: Path | None = None) -> Path:
    log_path = log_path or config.LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        force=True,
    )
    logging.captureWarnings(True)
    LOGGER.info("Logging to %s", log_path)
    return log_path


def should_reset_distances(now=None) -> bool:
    now = now or datetime.now(PARIS_TZ)
    if now.tzinfo is None:
        now = now.replace(tzinfo=PARIS_TZ)
    now = now.astimezone(PARIS_TZ)
    return now.weekday() == 0 and now.hour == 0


def _load_reset_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def reset_weekly_state_if_needed(df_distances, df_activity_log, now=None):
    now = now or datetime.now(PARIS_TZ)
    today = now.astimezone(PARIS_TZ).date().isoformat()
    state = _load_reset_state(config.RESET_STATE_PATH)

    if not should_reset_distances(now) or state.get("last_reset_date") == today:
        return df_distances, df_activity_log, False

    df_distances["distance"] = 0.0
    df_activity_log = df_activity_log.iloc[0:0].copy()
    config.RESET_STATE_PATH.write_text(json.dumps({"last_reset_date": today}, indent=2), encoding="utf-8")
    return df_distances, df_activity_log, True


def save_last_refresh(now=None) -> None:
    now = now or datetime.now(PARIS_TZ)
    config.LAST_REFRESH_PATH.write_text(
        json.dumps({"last_refresh_at": now.astimezone(PARIS_TZ).isoformat(timespec="minutes")}, indent=2),
        encoding="utf-8",
    )


def run_hidden(args, **kwargs):
    if sys.platform == "win32":
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
    return subprocess.run(args, **kwargs)


def run_git(args, *, check=True, log_output=True):
    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    result = run_hidden(
        ["git", *args],
        cwd=config.PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    if log_output and result.stdout:
        LOGGER.info(result.stdout.strip())
    if log_output and result.stderr:
        log_method = LOGGER.error if check and result.returncode else LOGGER.info
        log_method(result.stderr.strip())

    if check and result.returncode:
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result


def pull_remote_updates() -> None:
    LOGGER.info("Pulling remote Git changes...")
    run_git(["pull", "--rebase", "--autostash"])


def git_worktree_is_clean() -> bool:
    result = run_git(["status", "--porcelain"], check=True, log_output=False)
    return not result.stdout.strip()


def prepare_git_push() -> bool:
    if not git_worktree_is_clean():
        LOGGER.warning(
            "Git working tree is not clean before update; automatic pull/commit/push skipped. "
            "Commit or stash local changes, then rerun the script."
        )
        return False

    pull_remote_updates()
    return True


def push_site_update(output_dir: Path) -> bool:
    paths = [
        str(config.TEAMS_PATH),
        str(config.DISTANCES_PATH),
        str(config.PROCESSED_PATH),
        str(config.ACTIVITY_LOG_PATH),
        str(output_dir),
    ]
    if config.RESET_STATE_PATH.exists():
        paths.append(str(config.RESET_STATE_PATH))
    if config.LAST_REFRESH_PATH.exists():
        paths.append(str(config.LAST_REFRESH_PATH))

    run_git(["add", *paths])
    diff = run_git(["diff", "--cached", "--quiet"], check=False)
    if diff.returncode == 0:
        LOGGER.info("OK: No Git changes to push")
        return False

    run_git(["commit", "-m", "Update Strava data and site"])
    run_git(["push"])
    return True


def run_update():
    git_push_enabled = config.GIT_PUSH
    if git_push_enabled:
        git_push_enabled = prepare_git_push()

    LOGGER.info("Loading data...")
    df_roster = load_team_roster(config.TEAMS_PATH)
    df_distances = load_distances(config.DISTANCES_PATH, roster=df_roster, legacy_teams_path=config.TEAMS_PATH)
    df_processed = load_processed(config.PROCESSED_PATH)
    df_activity_log = load_activity_log(config.ACTIVITY_LOG_PATH)
    df_distances, df_activity_log, did_reset = reset_weekly_state_if_needed(df_distances, df_activity_log)
    if did_reset:
        LOGGER.info("OK: Weekly distance reset applied for Monday 00:00-01:00 Europe/Paris")

    LOGGER.info("Fetching Strava activities...")
    try:
        access_token = get_access_token()
        activities = fetch_club_activities(access_token, config.CLUB_ID)
    except Exception as e:
        LOGGER.exception("ERROR: Strava API failed: %s", e)
        return 1
    LOGGER.info("OK: %s activities fetched", len(activities))

    LOGGER.info("Updating distances...")
    df_distances, df_processed, df_activity_log = update_team_distances(
        df_roster,
        df_distances,
        df_processed,
        df_activity_log,
        activities,
    )

    LOGGER.info("Saving data...")
    save_distances(df_distances, config.DISTANCES_PATH)
    save_processed(df_processed, config.PROCESSED_PATH)
    save_activity_log(df_activity_log, config.ACTIVITY_LOG_PATH)
    save_last_refresh()

    LOGGER.info("OK: Distances updated:")
    for _, row in build_team_view(df_roster, df_distances).iterrows():
        LOGGER.info("  %s: %.2f km", row["team_name"], row["distance"] / 1000)

    LOGGER.info("Building static site...")
    output_dir = build_static_site()
    LOGGER.info("OK: Static site built in %s", output_dir)

    if git_push_enabled:
        LOGGER.info("Pushing site update to Git...")
        pushed = push_site_update(output_dir)
        if pushed:
            LOGGER.info("OK: Git update pushed")
    elif config.GIT_PUSH:
        LOGGER.warning("Git push was skipped because the repository was not ready for automatic updates")

    return 0


def main():
    setup_logging()
    try:
        return run_update()
    except Exception:
        LOGGER.exception("ERROR: Update failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
