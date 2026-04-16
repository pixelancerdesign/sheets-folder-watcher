#!/usr/bin/env python3
"""
Google Sheets → Local Folder Watcher

Polls a Google Sheet and creates local project folders
when a row's status column changes to the configured trigger value.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
STATE_PATH = BASE_DIR / ".state.json"

# Google Sheets API scope (read-only is enough)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "watcher.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Config & state ────────────────────────────────────────────────────────────

def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"created_projects": {}}


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ── Google Sheets auth ────────────────────────────────────────────────────────

def get_sheets_service(config: dict):
    """Authenticate with service account and return the Sheets API service."""
    sa_path = BASE_DIR / config["service_account_file"]
    creds = service_account.Credentials.from_service_account_file(
        str(sa_path), scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


# ── Folder creation ───────────────────────────────────────────────────────────

def create_project_folders(project_dir: Path, subfolders: list[str]) -> bool:
    """
    Create the project folder and all subfolders.
    Returns True if created, False if already existed.
    """
    if project_dir.exists():
        log.info(f"Already exists, skipping: {project_dir}")
        return False

    project_dir.mkdir(parents=True, exist_ok=True)
    for subfolder in subfolders:
        (project_dir / subfolder).mkdir(exist_ok=True)

    log.info(f"✓ Created: {project_dir}")
    for sf in subfolders:
        log.info(f"    ├── {sf}/")
    return True


# ── Sheet polling ─────────────────────────────────────────────────────────────

def col_index(letter: str) -> int:
    """Convert column letter (A, B, D …) to 0-based index."""
    return ord(letter.upper()) - ord("A")


def poll_once(service, config: dict, state: dict) -> dict:
    spreadsheet_id = config["spreadsheet_id"]
    trigger_value = config["trigger_value"].strip().lower()
    subfolders = config["subfolders"]
    base_path = Path(config["base_path"]).expanduser()

    col_code = col_index(config["columns"]["code"])       # e.g. A → 0
    col_name = col_index(config["columns"]["name"])       # e.g. B → 1
    col_status = col_index(config["columns"]["status"])   # e.g. D → 3

    # Determine how many columns to fetch (up to the furthest needed)
    max_col = max(col_code, col_name, col_status)
    end_col = chr(ord("A") + max_col)  # e.g. index 3 → "D"

    for sheet_name, local_folder in config["sheet_to_folder"].items():
        try:
            range_name = f"'{sheet_name}'!A:{end_col}"
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            rows = result.get("values", [])
        except HttpError as e:
            log.error(f"API error reading sheet '{sheet_name}': {e}")
            continue

        if not rows:
            log.warning(f"Sheet '{sheet_name}' returned no data.")
            continue

        # Skip header row
        for row in rows[1:]:
            # Guard: row must have enough columns
            if len(row) <= max_col:
                continue

            code = str(row[col_code]).strip()
            name = str(row[col_name]).strip().replace(" ", "_")
            status = str(row[col_status]).strip().lower()

            if not code or not name:
                continue

            if status != trigger_value:
                continue

            project_name = f"{code}-{name}"
            state_key = f"{sheet_name}::{project_name}"

            if state_key in state["created_projects"]:
                continue  # already handled

            year = str(datetime.now().year)
            project_dir = base_path / local_folder / year / project_name
            created = create_project_folders(project_dir, subfolders)

            state["created_projects"][state_key] = {
                "created_at": datetime.now().isoformat(),
                "path": str(project_dir),
                "newly_created": created,
            }
            save_state(state)

    return state


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    import sys
    run_once = "--now" in sys.argv

    config = load_config()
    state = load_state()
    interval = config.get("poll_interval_seconds", 300)

    log.info("=" * 60)
    log.info("Sheets folder watcher started")
    log.info(f"Spreadsheet : {config['spreadsheet_id']}")
    log.info(f"Trigger     : status = \"{config['trigger_value']}\"")
    log.info(f"Base path   : {config['base_path']}")
    log.info("Mode        : single poll" if run_once else f"Poll every  : {interval}s")
    log.info("=" * 60)

    service = get_sheets_service(config)

    log.info("Polling…")
    try:
        poll_once(service, config, state)
    except Exception as e:
        log.exception(f"Unexpected error during poll: {e}")

    if run_once:
        log.info("Done.")
        return

    log.info(f"Sleeping {interval}s until next poll.")
    time.sleep(interval)

    while True:
        log.info("Polling…")
        try:
            state = poll_once(service, config, state)
        except Exception as e:
            log.exception(f"Unexpected error during poll: {e}")

        log.info(f"Sleeping {interval}s until next poll.")
        time.sleep(interval)


if __name__ == "__main__":
    main()
