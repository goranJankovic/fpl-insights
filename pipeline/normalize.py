from typing import Any, Dict, Iterable, List, Tuple

def _parse_float(value):
    try:
        if value in ("", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

def normalize_teams(bootstrap: Dict[str, Any]) -> List[Tuple]:
    teams = []
    for t in bootstrap["teams"]:
        teams.append((
            t["id"],
            t["code"],
            t["name"],
            t["short_name"],
            t["strength"],
            t["strength_overall_home"],
            t["strength_overall_away"],
            t["strength_attack_home"],
            t["strength_attack_away"],
            t["strength_defence_home"],
            t["strength_defence_away"],
            _parse_float(t.get("form")),
            t.get("draw"),
            t.get("win"),
            t.get("loss"),
            t.get("points"),
            t.get("position"),
            t.get("played"),
        ))
    return teams

def normalize_players(bootstrap: Dict[str, Any]) -> List[Tuple]:
    rows = []
    for p in bootstrap["elements"]:
        rows.append((
            p["id"],
            p["first_name"],
            p["second_name"],
            p["team"],
            p["element_type"],
            float(p["now_cost"]) / 10.0,
            p["total_points"],
            p["goals_scored"],
            p["assists"],
            p["clean_sheets"],
            _parse_float(p["selected_by_percent"]),
            p["minutes"],
            _parse_float(p["form"]),
            _parse_float(p["points_per_game"]),
            p["status"],
            p.get("chance_of_playing_next_round"),
            p["transfers_in_event"],
            p["transfers_out_event"],
            bool(p["in_dreamteam"]),
            p["saves"],
            p["yellow_cards"],
            p["red_cards"],
            p["bonus"],
            p["bps"],
            _parse_float(p["influence"]),
            _parse_float(p["creativity"]),
            _parse_float(p["threat"]),
            _parse_float(p["ict_index"]),
            _parse_float(p.get("expected_goals")),
            _parse_float(p.get("expected_assists")),
            _parse_float(p.get("expected_goal_involvements")),
            _parse_float(p.get("expected_goals_conceded")),
            _parse_float(p.get("expected_goals_per_90")),
            _parse_float(p.get("saves_per_90")),
            _parse_float(p.get("expected_assists_per_90")),
            _parse_float(p.get("expected_goal_involvements_per_90")),
            _parse_float(p.get("expected_goals_conceded_per_90")),
            _parse_float(p.get("goals_conceded_per_90")),
            p.get("starts"),
            _parse_float(p.get("starts_per_90")),
            _parse_float(p.get("clean_sheets_per_90")),
        ))
    return rows

# --- gameweeks --- #
def normalize_events(bootstrap: Dict[str, Any]) -> List[Tuple]:
    rows = []
    for e in bootstrap["events"]:
        rows.append((
            e["id"],
            e["name"],
            e["deadline_time"],
            e.get("average_entry_score"),
            int(e.get("finished", False)),
            e.get("most_captained"),
            e.get("most_transferred_in"),
        ))
    return rows

def normalize_fixtures(fixtures: Iterable[Dict[str, Any]]) -> List[Tuple]:
    rows = []
    for f in fixtures:
        rows.append((
            f["id"],
            f.get("event"),
            f["team_h"],
            f["team_a"],
            f.get("team_h_score"),
            f.get("team_a_score"),
            f.get("team_h_difficulty"),
            f.get("team_a_difficulty"),
            int(f.get("finished", False)),
            f.get("kickoff_time"),
        ))
    return rows

def normalize_player_history(player_id: int, player_summary: Dict[str, Any]) -> List[Tuple]:
    rows = []
    for gw in player_summary.get("history", []):
        rows.append((
            player_id,
            gw["round"],
            gw.get("minutes", 0),
            gw["total_points"],
            gw["goals_scored"],
            gw["assists"],
            gw["clean_sheets"],
            gw.get("opponent_team"),
            gw.get("team_h_score"),
            gw.get("team_a_score"),
            gw.get("was_home", True),
            gw.get("bonus", 0),
            _parse_float(gw.get("expected_goals")),
            _parse_float(gw.get("expected_assists")),
            gw.get("transfers_in", 0),
            gw.get("transfers_out", 0),
            gw.get("kickoff_time"),
        ))
    return rows
