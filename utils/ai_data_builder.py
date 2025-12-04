import os
import json
from typing import Dict, Any, List
from db.sqlite import get_connection
import requests


# -------------------------------------------------
# LOAD TEAM JSON FROM team_stats.py OUTPUT
# -------------------------------------------------

def load_team_json(entry_id: int) -> Dict[str, Any]:
    path = f"analysis_reports/{entry_id}/team_stats.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"team_stats.json not found for entry {entry_id}. Run team_stats.py first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------------------------
# PLAYER HISTORY & META FROM SQLITE
# -------------------------------------------------

def get_player_meta(player_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id,
               p.first_name,
               p.second_name,
               p.team_id,
               p.element_type,
               t.short_name
        FROM players p
        LEFT JOIN teams t ON p.team_id = t.id
        WHERE p.id = ?
    """, (player_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return {
            "id": player_id,
            "name": f"Unknown {player_id}",
            "team": None,
            "pos": None
        }

    pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

    return {
        "id": row["id"],
        "name": f"{row['first_name']} {row['second_name']}".strip(),
        "team": row["short_name"],
        "pos": pos_map.get(row["element_type"])
    }


def get_player_full_history(player_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM player_history
        WHERE player_id = ?
        ORDER BY gameweek ASC
    """, (player_id,))
    rows = cur.fetchall()
    conn.close()

    history = []
    for r in rows:
        history.append({
            "gw": r["gameweek"],
            "points": r["total_points"],
            "goals": r["goals_scored"],
            "assists": r["assists"],
            "cs": r["clean_sheets"],
            "bonus": r["bonus_points"],
            "minutes": r["minutes"]
        })
    return history

# -------------------------------------------------
# BUILD SQUAD FOR A GIVEN GW
# -------------------------------------------------

def build_squad_for_gw(entry_id: int, gw: int) -> List[Dict[str, Any]]:
    """
    Returns squad for analysis of target GW.
    Uses data from the latest COMPLETED gw strictly before the target GW.

    Example:
        predict GW15 -> use GW14 squad/state
        predict GW20 -> use GW19

    We never use information from the GW being predicted.
    """

    team_json = load_team_json(entry_id)

    # Which gameweeks exist?
    available_gws = sorted(g["gw"] for g in team_json["gw_data"])

    # GAMEWEEK MUST EXIST IN HISTORY (for predictions)
    past_gws = [g for g in available_gws if g < gw]

    if not past_gws:
        raise ValueError(
            f"Cannot analyze GW {gw}: no earlier GW exists for entry {entry_id}. "
            f"Available gameweeks: {available_gws}"
        )

    # We use the last completed GW before the target GW
    use_gw = past_gws[-1]

    gw_block = next(g for g in team_json["gw_data"] if g["gw"] == use_gw)

    squad = []

    # Combine starting + bench
    for section in ["starting", "bench"]:
        for p in gw_block["team"][section]:
            pid = p["id"]
            meta = get_player_meta(pid)
            history = get_player_full_history(pid)

            squad.append({
                "id": pid,
                "name": meta["name"],
                "team": meta["team"],
                "pos": meta["pos"],
                "gw_history": history[-6:],  # last 6 GWs for AI trend
                "is_captain": (pid == gw_block["team"]["captain_id"]),
                "is_vice": (pid == gw_block["team"]["vice_id"]),
                "multiplier": 2 if pid == gw_block["team"]["captain_id"] else 1,
                "last_gw_used": use_gw
            })

    return squad


# -------------------------------------------------
# BUILD GLOBAL CANDIDATE POOL (TOP PLAYERS)
# -------------------------------------------------

def build_candidate_pool(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Pull top players based on total points from SQLite.
    This creates a general pool for transfer/freehit advisors.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, first_name, second_name, team_id, element_type, now_cost
        FROM players
        ORDER BY total_points DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()

    # club short names
    cur.execute("SELECT id, short_name FROM teams")
    teams_map = {r["id"]: r["short_name"] for r in cur.fetchall()}
    conn.close()

    pos_map = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

    pool = []
    for r in rows:
        pid = r["id"]
        full_history = get_player_full_history(pid)

        # Injury risk: no minutes in last game OR last 2 of 3 games
        injury_risk = False
        if full_history:
            # Did not play last GW
            if full_history[-1]["minutes"] == 0:
                injury_risk = True

            # Missed 2 of last 3
            if len(full_history) >= 3:
                last3 = full_history[-3:]
                misses = sum(1 for gw in last3 if gw["minutes"] == 0)
                if misses >= 2:
                    injury_risk = True

        pool.append({
            "id": pid,
            "name": f"{r['first_name']} {r['second_name']}".strip(),
            "team": teams_map.get(r["team_id"]),
            "pos": pos_map.get(r["element_type"]),
            "price": r["now_cost"],
            "recent_history": full_history[-6:],
            "injury_risk": injury_risk
        })

    return pool
