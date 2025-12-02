import sqlite3
from typing import List, Dict, Tuple

import numpy as np

from config import DB_PATH, DEFAULT_SIMS, DEFAULT_HISTORY_GW
from models.monte_carlo import PredictionDistribution


def _get_connection():
    """Return a SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_player_row(player_id: int) -> Dict:
    """
    Load player data from the 'players' table.
    """
    conn = _get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE id = ?", (player_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Player {player_id} not found in 'players' table.")

    return dict(row)


def get_player_history_points(player_id: int, last_n: int = DEFAULT_HISTORY_GW) -> List[int]:
    """
    Return the last N gameweeks of total points for a player.
    Used to calculate standard deviation (variance) of form.
    """
    conn = _get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT total_points
        FROM player_history
        WHERE player_id = ?
        ORDER BY gameweek DESC
        LIMIT ?
    """, (player_id, last_n))

    rows = cur.fetchall()
    conn.close()

    return [r["total_points"] for r in rows if r["total_points"] is not None]


def get_player_fixtures_in_gw(player_id: int, gw: int) -> List[Dict]:
    """
    Return all fixtures for a player in a given gameweek.
    Supports:
    - 0 fixtures (blank GW)
    - 1 fixture   (normal GW)
    - 2 fixtures  (double gameweek / DGW)
    """
    conn = _get_connection()
    cur = conn.cursor()

    # Get player's team id
    cur.execute("SELECT team_id FROM players WHERE id = ?", (player_id,))
    team_row = cur.fetchone()
    if not team_row:
        conn.close()
        return []

    team_id = team_row["team_id"]

    # Load all fixtures for this team in the given GW
    cur.execute("""
        SELECT id, event, team_h, team_a,
               difficulty_home, difficulty_away,
               team_h_score, team_a_score, finished, kickoff_time
        FROM fixtures
        WHERE event = ?
          AND (team_h = ? OR team_a = ?)
    """, (gw, team_id, team_id))

    fixtures = [dict(r) for r in cur.fetchall()]
    conn.close()

    return fixtures


def _compute_base_ep_for_fixture(p: Dict, difficulty: int) -> float:
    """
    Compute expected points for a single fixture.
    It uses:
    - points_per_game
    - form
    - expected goals + expected assists (xGI)
    - fixture difficulty adjustment
    """
    ppg = p["points_per_game"] or 0
    form = p["form"] or ppg
    xgi = (p.get("expected_goals", 0) or 0) + (p.get("expected_assists", 0) or 0)

    # Base EP from player performance stats
    base_ep = 0.5 * ppg + 0.3 * form + 0.2 * xgi

    # Difficulty: 1 = very easy, 3 = neutral, 5 = very hard
    # Adjustment: each step changes EP by ±10%
    adj = 1 + (3 - difficulty) * 0.1

    ep = base_ep * adj
    return max(ep, 0.0)


def _compute_player_std_from_history(player_id: int, ep: float) -> float:
    """
    Calculate player's standard deviation.
    Use last N gameweeks if available.
    Otherwise use a fallback variance relative to EP.
    """
    hist = get_player_history_points(player_id)

    if len(hist) >= 3:
        return float(np.std(hist))

    # fallback when we do not have enough history
    return ep * 0.35


def simulate_player_points_advanced(player_id: int, gw: int, n_sims: int) -> np.ndarray:
    """
    Advanced player simulation (v1):
    - Supports DGW (double gameweeks)
    - Each fixture generates its own expected points
    - STD is based on player history
    - Uses normal distribution per fixture (Poisson will come later in v2)
    """
    p = get_player_row(player_id)
    fixtures = get_player_fixtures_in_gw(player_id, gw)

    # Blank GW → return zero for all simulations
    if not fixtures:
        return np.zeros(n_sims)

    # Injured or out → zero points
    if p["status"] in ("i", "o"):
        return np.zeros(n_sims)

    # Compute EP for each fixture in this GW
    fixture_eps = []
    for f in fixtures:
        if f["team_h"] == p["team_id"]:
            difficulty = f["difficulty_home"]
        else:
            difficulty = f["difficulty_away"]

        ep = _compute_base_ep_for_fixture(p, difficulty)
        fixture_eps.append(ep)

    # Total EP for GW is the sum (important for DGW)
    total_ep = sum(fixture_eps)

    # Player variance (STD) from history
    std = _compute_player_std_from_history(player_id, total_ep)

    # If DGW, split STD evenly across fixtures (v1 simplification)
    per_fixture_std = std / max(len(fixtures), 1)

    # Generate samples
    samples_total = np.zeros(n_sims)
    for ep in fixture_eps:
        fixture_samples = np.random.normal(loc=ep, scale=per_fixture_std, size=n_sims)
        fixture_samples = np.clip(fixture_samples, 0, None)
        samples_total += fixture_samples

    return np.clip(samples_total, 0, None)


def predict_team_points_advanced(
    starting: List[int],
    gw: int,
    captain_id: int | None = None,
    vice_captain_id: int | None = None,
    bench: List[int] | None = None,
    triple_captain: bool = False,
    bench_boost: bool = False,
    n_sims: int | None = None,
) -> PredictionDistribution:
    """
    Advanced team simulation (v1):

    Features:
    - Simulate points for all starting XI
    - Bench players are counted only if bench_boost=True
    - Supports DGW for each player
    - Captain → x2 multiplier
    - Triple captain → x3 multiplier
    - Vice captain replaces captain ONLY if captain has zero points in that simulation
    """

    if n_sims is None:
        n_sims = DEFAULT_SIMS

    # Build the list of all players that contribute points
    all_players = list(starting)
    if bench_boost and bench:
        all_players += list(bench)

    # Simulate every player once
    player_samples: Dict[int, np.ndarray] = {}
    for pid in all_players:
        samples = simulate_player_points_advanced(pid, gw, n_sims)
        player_samples[pid] = samples

    # Base sum (all starting players; bench counted only if BB)
    team_samples = np.zeros(n_sims)
    for pid in all_players:
        team_samples += player_samples[pid]

    # Captain / VC logic
    if captain_id is not None and captain_id in player_samples:
        cap_samples = player_samples[captain_id]

        # Default case: captain points
        effective_cap = cap_samples

        if vice_captain_id and vice_captain_id in player_samples:
            vc_samples = player_samples[vice_captain_id]

            # VC replaces captain only if captain has 0 points (means he did not play)
            effective_cap = np.where(cap_samples == 0, vc_samples, cap_samples)

        # Determine multiplier (2x or 3x)
        mult = 3 if triple_captain else 2

        # We already counted cap points once in team_samples,
        # so we add (mult - 1) * effective_cap.
        team_samples += (mult - 1) * effective_cap

    # Build distribution result
    return PredictionDistribution(
        samples=team_samples,
        expected=float(np.mean(team_samples)),
        median=float(np.percentile(team_samples, 50)),
        p25=float(np.percentile(team_samples, 25)),
        p75=float(np.percentile(team_samples, 75)),
        p90=float(np.percentile(team_samples, 90)),
    )
