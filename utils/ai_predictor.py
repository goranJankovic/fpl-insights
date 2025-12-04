import os
import json
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

# -------------------------------------------------
# OpenAI client setup
# -------------------------------------------------

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env file")

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------------------------------
# LOW-LEVEL LLM WRAPPER
# -------------------------------------------------

def ask_llm(prompt: str) -> Dict[str, Any]:
    """
    Sends prompt to LLM and safely parses JSON.
    Handles cases where model returns ```json ... ``` blocks.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert FPL analyst. Always output strict JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    # Remove ```json ... ```
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()

    # Attempt to parse JSON
    try:
        parsed = json.loads(raw)
        return parsed
    except json.JSONDecodeError:
        return {
            "error": "Model returned non-JSON response.",
            "raw_response": raw
        }


# -------------------------------------------------
# BASIC (već dogovoreno): whole-team / player / compare
# -------------------------------------------------

def build_team_prompt(team_json: Dict[str, Any]) -> str:
    """
    Generic prompt za analizu jednog tima kroz celu sezonu.
    """
    return f"""
You are an expert Fantasy Premier League analyst.

You will receive JSON representing one FPL team across all gameweeks
(exported from a local database, not from the official API).

This JSON typically has fields like:
- entry_id
- team_name
- manager
- total_points
- current_overall_rank
- chips (by GW)
- gw_data: array of gameweeks, each containing:
  - gw, points, overall_rank, gw_rank, transfers, transfer_cost, value, bank, chip
  - team: starting, bench, captain_id, vice_id, starting_total, bench_total

USAGE:
- Look at patterns of points, rank movement, chip usage, bench strength.
- Look at most consistent and explosive players in starting XIs.
- Look how aggressive the manager is with transfers and hits.

TASK:
Predict performance for the NEXT gameweek in a realistic way.
Do NOT hallucinate unknown fixtures. You don't know exact opponents or odds,
you only know how this manager's team has performed so far.

Respond STRICTLY with a JSON object:

{{
  "predicted_points": number,
  "key_players": [
    {{
      "id": int,
      "reason": "short explanation"
    }}
  ],
  "weak_spots": [
    "short bullet explanation"
  ],
  "recommended_transfer": "one concise suggestion, or 'none' if you cannot say",
  "confidence": "low|medium|high"
}}

Here is the team JSON:
{json.dumps(team_json)}
"""


def predict_team_performance(team_json: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_team_prompt(team_json)
    return ask_llm(prompt)


def build_player_prompt(player_json: Dict[str, Any]) -> str:
    """
    Prompt za jednog igrača (npr. history iz player_history).
    """
    return f"""
You are an FPL performance analyst.

Below is a JSON object describing a player's:
- basic info (id, name, team, position)
- per-gameweek stats from a local database (goals, assists, total_points, minutes, etc.)

Use ONLY this data. Do NOT invent fixtures, do NOT assume future transfers.

TASK:
Estimate this player's expected FPL points in the next gameweek,
based on trends: recent points, minutes, attacking/defensive returns.

Respond STRICTLY with JSON:

{{
  "expected_points": number,
  "risk_level": "low|medium|high",
  "reasoning": "short explanation using data from the JSON"
}}

Player JSON:
{json.dumps(player_json)}
"""


def predict_player_performance(player_json: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_player_prompt(player_json)
    return ask_llm(prompt)


def build_compare_prompt(team_a: Dict[str, Any], team_b: Dict[str, Any]) -> str:
    """
    Generalni prompt za poređenje dva tima (sezona).
    Ovo je više long-term stil, dok ćemo H2H ispod praviti GW-specific.
    """
    return f"""
You are an expert FPL analyst.

You are comparing TWO teams across their season data.
Each JSON is exported from a local database.

FIELDS:
Both teams have:
- meta: team_name, manager, total_points, current_overall_rank
- gw_data: per-GW history with points, rank, transfers, chips, starting XI etc.

TASK:
Make a SEASON-LONG comparison: who has been stronger so far and why.

Respond STRICTLY with JSON:

{{
  "team_a_better_in": ["short bullets"],
  "team_b_better_in": ["short bullets"],
  "summary": "short paragraph",
  "overall_stronger_team": "A|B|Even"
}}

TEAM A:
{json.dumps(team_a)}

TEAM B:
{json.dumps(team_b)}
"""


def compare_teams(team_a_json: Dict[str, Any], team_b_json: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_compare_prompt(team_a_json, team_b_json)
    return ask_llm(prompt)


# -------------------------------------------------
# AI H2H PREDICTOR (GW-specific)
# -------------------------------------------------

def build_h2h_prompt(
    team_a: Dict[str, Any],
    team_b: Dict[str, Any],
    gw: int,
    mc_baseline: Optional[Dict[str, float]] = None,
) -> str:
    """
    Prompt za AI H2H predict za KONKRETAN GW.

    mc_baseline je opciono:
      {{
        "team_a_expected": float,
        "team_b_expected": float
      }}
    iz tvog Monte Carlo modela, ako želiš da ga proslediš.
    """
    baseline_txt = json.dumps(mc_baseline) if mc_baseline else "null"

    return f"""
You are an FPL head-to-head match analyst.

You will receive:
- TEAM A JSON
- TEAM B JSON
Each JSON includes season data AND detailed info for each GW:
points, ranks, transfers, chip usage, starting XIs with player-level points.

You will ALSO receive optional Monte Carlo baseline expected points
for this specific gameweek from a separate numeric model.

Gameweek of interest: GW {gw}.

RULES:
- Use ONLY the JSON and the numeric baseline if provided.
- Look especially at the LAST 4-6 gameweeks for each team to understand trends.
- Consider captaincy patterns (aggressive vs safe), bench strength,
  and how often the manager's high-risk decisions paid off.
- Do NOT invent fixtures or odds. You are only predicting RELATIVE outcomes.

TASK:
Predict the H2H outcome for THIS GAMEWEEK, with confidence.

Respond STRICTLY with JSON:

{{
  "gameweek": {gw},
  "team_a_expected_points": number,
  "team_b_expected_points": number,
  "win_probabilities": {{
    "team_a": number,   // 0-100
    "team_b": number,   // 0-100
    "draw": number      // 0-100, all three should roughly sum to 100
  }},
  "key_factors": [
    "short bullet about main factor 1",
    "short bullet about main factor 2"
  ],
  "who_is_favored": "A|B|Even",
  "confidence": "low|medium|high",
  "based_on_monte_carlo": {str(mc_baseline is not None).lower()}
}}

TEAM A JSON:
{json.dumps(team_a)}

TEAM B JSON:
{json.dumps(team_b)}

MONTE CARLO BASELINE (can be null):
{baseline_txt}
"""


def predict_h2h(
    team_a_json: Dict[str, Any],
    team_b_json: Dict[str, Any],
    gw: int,
    mc_baseline: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    prompt = build_h2h_prompt(team_a_json, team_b_json, gw, mc_baseline)
    return ask_llm(prompt)


# -------------------------------------------------
# AI CAPTAINCY ADVISOR
# -------------------------------------------------

def build_captaincy_prompt(
    gw: int,
    squad_players: List[Dict[str, Any]],
    context_team: Dict[str, Any],
) -> str:
    """
    squad_players je lista igrača iz TVOG tima za taj GW, npr:
    [
      {
        "id": 177,
        "name": "Mohamed Salah",
        "team": "LIV",
        "pos": "MID",
        "gw_history": [... per-GW stats objects ...],
        "is_nailed": true/false,
        "injury_flag": "fit|doubt|out"
      },
      ...
    ]

    context_team je npr. tvoj team_stats.json (ceo), da vidi pattern kapitena.
    """
    return f"""
You are an FPL captaincy advisor.

You will receive:
1) Full season context for the manager (TEAM JSON).
2) A list of CANDIDATE PLAYERS from this manager's current squad,
   with per-gameweek stats and simple flags (nailed/injury).

Gameweek of interest: GW {gw}.

RULES:
- Use ONLY the given stats. Do not invent fixtures or odds.
- Focus on recent form (last 4-6 GWs), explosiveness (double-digit hauls),
  consistency (few blanks), and minutes reliability.
- Consider also how this manager usually picks captains (aggressive/safe).

TASK:
Recommend CAPTAIN and VICE-CAPTAIN for this gameweek.

Respond STRICTLY with JSON:

{{
  "gameweek": {gw},
  "suggested_captain": {{
    "id": int,
    "name": "string",
    "reason": "short explanation"
  }},
  "suggested_vice_captain": {{
    "id": int,
    "name": "string",
    "reason": "short explanation"
  }},
  "other_viable_options": [
    {{
      "id": int,
      "name": "string",
      "reason": "short explanation"
    }}
  ],
  "notes": "short extra advice if needed"
}}

TEAM CONTEXT JSON:
{json.dumps(context_team)}

SQUAD PLAYERS JSON:
{json.dumps(squad_players)}
"""


def advise_captaincy(
    gw: int,
    squad_players: List[Dict[str, Any]],
    context_team: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = build_captaincy_prompt(gw, squad_players, context_team)
    return ask_llm(prompt)


# -------------------------------------------------
# AI TRANSFER RECOMMENDER
# -------------------------------------------------

def build_transfer_prompt(
    gw: int,
    current_team: Dict[str, Any],
    squad_state: Dict[str, Any],
    candidate_pool: List[Dict[str, Any]],
) -> str:
    """
    squad_state:
    {
      "bank": float,
      "free_transfers": int,
      "squad_players": [... same_player_structure as above ...]
    }

    candidate_pool:
    lista kandidata iz baze (već prefiltriranih Python kodom):
    [
      {
        "id": ...,
        "name": ...,
        "team": "ARS",
        "pos": "MID",
        "price": 7.5,
        "recent_history": [... last 4-6 GWs from player_history ...]
      },
      ...
    ]
    """
    return f"""
You are an FPL transfer advisor.

You will receive:
- current TEAM JSON (season context),
- squad_state (players currently owned, free transfers, money in the bank),
- candidate_pool: a pre-filtered list of good players from the whole game.

Gameweek of interest: GW {gw}.

RULES:
- Use ONLY the provided JSON data.
- Assume standard FPL rules: 15 players, 1 free transfers usual, minus 4 for extra.
- Focus on upgrading weak spots (injured/out-of-form players)
  to in-form players from the candidate_pool.
- Respect budget (price difference + bank).
- Do NOT suggest wild unrealistic -12 hits by default; keep it reasonable.

TASK:
Suggest 0-1 transfers (or more if team have more free transfers than 1, usually no more than 2 because if team have 1 fts minus 4 for every extra transfers), 
unless the squad_state explicitly shows more FTs.
Explain briefly why.

Respond STRICTLY with JSON:

{{
  "gameweek": {gw},
  "suggested_transfers": [
    {{
      "out_id": int,
      "out_name": "string",
      "in_id": int,
      "in_name": "string",
      "reason": "short explanation"
    }}
  ],
  "hit_cost": 0,  // 0, 4, 8... depending on needed extra transfers
  "rationale": "short summary"
}}

TEAM JSON:
{json.dumps(current_team)}

SQUAD STATE JSON:
{json.dumps(squad_state)}

CANDIDATE POOL JSON:
{json.dumps(candidate_pool)}
"""


def recommend_transfers(
    gw: int,
    current_team: Dict[str, Any],
    squad_state: Dict[str, Any],
    candidate_pool: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prompt = build_transfer_prompt(gw, current_team, squad_state, candidate_pool)
    return ask_llm(prompt)


# -------------------------------------------------
# AI FREE HIT ADVISOR (GW-specific)
# -------------------------------------------------

def build_freehit_prompt(gw: int, candidate_pool: list, budget: float):
    prompt = f"""
        You are an elite Fantasy Premier League strategist.
        
        Build the **best possible FREE HIT squad for GW{gw}** using ONLY the players provided in candidate_pool.
        
        STRICT RULES YOU MUST FOLLOW (NO EXCEPTIONS):
        
        1. **Exactly 15 players** must be selected.
        2. The squad MUST contain:
           - **2 goalkeepers**
           - **5 defenders**
           - **5 midfielders**
           - **3 forwards**
           Any other distribution is INVALID.
        
        3. **NO duplicate players.**
        
        4. **Total price MUST NOT exceed {budget} million.**
        
        5. **You MUST NOT select any player where injury_risk = true.**
           Injury risk definition:
           - Minutes = 0 in last GW
           - OR 0 minutes in 2 of last 3 GWs.
        
        6. Prefer players with:
           - strong last 6-game performance
           - nailed minutes (regular starter)
           - strong attacking or defensive returns
           - favorable fixture in GW{gw}
           - strong xGI trend
        
        7. Respond ONLY in STRICT JSON. No commentary, no backticks.
        
        JSON FORMAT:
        {{
          "gameweek": {gw},
          "squad": [
            {{
              "id": number,
              "name": "...",
              "team": "...",
              "pos": "GK|DEF|MID|FWD",
              "price": number,
              "reason": "why this player is chosen"
            }}
          ],
          "total_price": number,
          "rationale": "overall explanation"
        }}
        
        Here is the candidate_pool:
        {json.dumps(candidate_pool)}
        """
    return prompt



def recommend_freehit_squad(
    gw: int,
    candidate_pool: List[Dict[str, Any]],
    budget: float,
) -> Dict[str, Any]:
    prompt = build_freehit_prompt(gw, candidate_pool, budget)
    return ask_llm(prompt)
