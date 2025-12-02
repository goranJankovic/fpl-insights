import requests

def fetch_team(entry_id: int) -> dict:
    url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/"
    return requests.get(url).json()

def fetch_team_history(entry_id: int) -> dict:
    url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/history/"
    return requests.get(url).json()

def get_team_current_history(entry_id: int):
    history = fetch_team_history(entry_id)
    return history.get("current", [])
