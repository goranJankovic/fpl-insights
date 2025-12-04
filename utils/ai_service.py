import json
from typing import Dict, Any, List, Optional

from utils.ai_data_builder import (
    load_team_json,
    build_squad_for_gw,
    build_candidate_pool,
)
from utils.ai_predictor import (
    predict_h2h,
    advise_captaincy,
    recommend_transfers,
    recommend_freehit_squad,
)


# -------------------------------------------------
# AI SERVICE LAYER — clean and simple public API
# -------------------------------------------------


# -------------------------------------------------
# 1) H2H PREDICTION
# -------------------------------------------------

def h2h_prediction(entry_a: int, entry_b: int, gw: int,
                   mc_baseline: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    AI H2H predictor for a specific GW.

    Args:
        entry_a: ID prvog FPL tima
        entry_b: ID drugog FPL tima
        gw: gameweek koji analiziramo
        mc_baseline: opciono {"team_a_expected": x, "team_b_expected": y}

    Returns:
        Dict sa AI predikcijom H2H meča.
    """
    teamA = load_team_json(entry_a)
    teamB = load_team_json(entry_b)

    result = predict_h2h(teamA, teamB, gw, mc_baseline)
    return result



# -------------------------------------------------
# 2) CAPTAINCY ADVICE
# -------------------------------------------------

def captaincy_advice(entry_id: int, gw: int) -> Dict[str, Any]:
    """
    AI captaincy advisor for given GW.
    Uses squad of last completed GW before the target GW.
    """
    team_json = load_team_json(entry_id)
    squad = build_squad_for_gw(entry_id, gw)

    # Friendly for debugging:
    print(f"[AI] Captaincy analysis for GW{gw}, using squad from GW{squad[0]['last_gw_used']}.")

    return advise_captaincy(gw, squad, team_json)


# -------------------------------------------------
# 3) TRANSFER ADVICE
# -------------------------------------------------

def transfer_advice(entry_id: int, gw: int,
                    candidate_pool_size: int = 60) -> Dict[str, Any]:
    """
    AI transfer advisor.
    Uses last completed GW before target GW.
    """
    team_json = load_team_json(entry_id)
    squad = build_squad_for_gw(entry_id, gw)

    # Determine budget state from last GW before target
    use_gw = squad[0]["last_gw_used"]
    last_gw_block = next(g for g in team_json["gw_data"] if g["gw"] == use_gw)

    squad_state = {
        "bank": last_gw_block["bank"],
        "free_transfers": last_gw_block["transfers"],
        "squad_players": squad,
        "source_gw": use_gw
    }

    candidate_pool = build_candidate_pool(limit=candidate_pool_size)

    print(f"[AI] Transfer advice for GW{gw}, using GW{use_gw} squad & bank data.")

    return recommend_transfers(gw, team_json, squad_state, candidate_pool)


# -------------------------------------------------
# 4) FREE HIT ADVICE
# -------------------------------------------------
def freehit_advice(gw: int,
                   candidate_pool_size: int = 120,
                   budget: float = 100.0) -> Dict[str, Any]:

    candidate_pool = build_candidate_pool(limit=candidate_pool_size)

    print(f"[AI] Free Hit team generation for GW{gw} using {candidate_pool_size} candidates.")

    result = recommend_freehit_squad(gw, candidate_pool, budget)

    # ---------- VALIDATION ----------
    errors = validate_freehit_squad(result["squad"])
    if errors:
        return {
            "error": "Invalid squad returned by AI.",
            "issues": errors,
            "ai_output": result
        }

    return result



# -------------------------------------------------
# 5) ENTRY-POINT HELPERS (OPTIONAL)
# -------------------------------------------------

def pretty_print(obj: Dict[str, Any]):
    """Nice print in terminal."""
    print(json.dumps(obj, indent=2))

def validate_freehit_squad(squad: list):
    errors = []

    pos_count = {"GK": 0, "DEF": 0, "MID": 0, "FWD": 0}
    seen = set()

    for p in squad:
        # count positions
        if p["pos"] not in pos_count:
            errors.append(f"Invalid position for {p['name']}: {p['pos']}")
        else:
            pos_count[p["pos"]] += 1

        # duplicate
        if p["id"] in seen:
            errors.append(f"Duplicate player: {p['name']}")
        seen.add(p["id"])

    if pos_count["GK"] != 2:
        errors.append(f"Expected 2 GKs, got {pos_count['GK']}")
    if pos_count["DEF"] != 5:
        errors.append(f"Expected 5 DEFs, got {pos_count['DEF']}")
    if pos_count["MID"] != 5:
        errors.append(f"Expected 5 MIDs, got {pos_count['MID']}")
    if pos_count["FWD"] != 3:
        errors.append(f"Expected 3 FWDs, got {pos_count['FWD']}")

    return errors
