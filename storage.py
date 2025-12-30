"""Data storage operations for tournament data using JSON files."""
import json
import os
from pathlib import Path

DATA_DIR = Path("data")

# Default data structures
DEFAULT_PLAYERS = []
DEFAULT_TEAMS = []
DEFAULT_MATCHES = []
DEFAULT_TOURNAMENT = {
    "current_round": 0,
    "total_rounds": 0,
    "status": "setup",  # setup, in_progress, completed
    "num_courts": 1
}

def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)

def load_json(filename, default):
    """Load JSON data from file, return default if file doesn't exist."""
    ensure_data_dir()
    filepath = DATA_DIR / filename
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    return default

def save_json(filename, data):
    """Save data to JSON file."""
    ensure_data_dir()
    filepath = DATA_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_players():
    """Get list of all players."""
    return load_json("players.json", DEFAULT_PLAYERS)

def save_players(players):
    """Save players list."""
    save_json("players.json", players)

def get_teams():
    """Get list of all teams."""
    return load_json("teams.json", DEFAULT_TEAMS)

def save_teams(teams):
    """Save teams list."""
    save_json("teams.json", teams)

def get_matches():
    """Get list of all matches."""
    return load_json("matches.json", DEFAULT_MATCHES)

def save_matches(matches):
    """Save matches list."""
    save_json("matches.json", matches)

def get_tournament():
    """Get tournament state."""
    return load_json("tournament.json", DEFAULT_TOURNAMENT)

def save_tournament(tournament):
    """Save tournament state."""
    save_json("tournament.json", tournament)

def add_player(name):
    """Add a new player and return the player ID."""
    players = get_players()
    player_id = len(players) + 1
    player = {
        "id": player_id,
        "name": name
    }
    players.append(player)
    save_players(players)
    return player_id

def remove_player(player_id):
    """Remove a player by ID."""
    players = get_players()
    players = [p for p in players if p["id"] != player_id]
    save_players(players)

def add_team(player1_id, player2_id):
    """Add a new team and return the team ID."""
    teams = get_teams()
    team_id = len(teams) + 1
    team = {
        "id": team_id,
        "player1": player1_id,
        "player2": player2_id
    }
    teams.append(team)
    save_teams(teams)
    return team_id

def remove_team(team_id):
    """Remove a team by ID."""
    teams = get_teams()
    teams = [t for t in teams if t["id"] != team_id]
    save_teams(teams)

def update_tournament_settings(num_courts):
    """Update tournament settings."""
    tournament = get_tournament()
    tournament["num_courts"] = num_courts
    save_tournament(tournament)

