from pathlib import Path

from db.sqlite import init_db
from pipeline.fetch import fetch_bootstrap_static, fetch_fixtures, fetch_player_summary
from pipeline.normalize import (
    normalize_teams,
    normalize_players,
    normalize_events,
    normalize_fixtures,
    normalize_player_history,
)
from pipeline.load_to_sqlite import (
    replace_teams,
    replace_players,
    replace_events,
    replace_fixtures,
    replace_player_history,
)
from pipeline.schema_checker import check_schema_change

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def update_fpl_data():
    print("Initializing DB schema...")
    init_db()

    print("Fetching bootstrap-static...")
    bootstrap = fetch_bootstrap_static()
    check_schema_change(RAW_DIR, "bootstrap_static", bootstrap)

    print("Fetching fixtures...")
    fixtures_raw = fetch_fixtures()

    print("Normalizing teams/players/events/fixtures...")
    teams_rows = normalize_teams(bootstrap)
    players_rows = normalize_players(bootstrap)
    events_rows = normalize_events(bootstrap)
    fixtures_rows = normalize_fixtures(fixtures_raw)

    print("Writing teams...")
    replace_teams(teams_rows)

    print("Writing players...")
    replace_players(players_rows)

    print("Writing events...")
    replace_events(events_rows)

    print("Writing fixtures...")
    replace_fixtures(fixtures_rows)

    print("Fetching player history (this might take a while)...")
    all_history_rows = []
    for p in bootstrap["elements"]:
        pid = p["id"]
        summary = fetch_player_summary(pid)
        all_history_rows.extend(normalize_player_history(pid, summary))

    print("Writing player history...")
    replace_player_history(all_history_rows)

    print("Done. fpl.db is updated.")
