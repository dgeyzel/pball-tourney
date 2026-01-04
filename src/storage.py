"""Data storage operations for tournament data using JSON files."""
import json
from pathlib import Path

# Directory where all tournament data files are stored
DATA_DIR = Path("data")

# Default data structures used when files don't exist or are corrupted
DEFAULT_PLAYERS = []  # Empty list of players
DEFAULT_TEAMS = []    # Empty list of teams
DEFAULT_MATCHES = []  # Empty list of matches
DEFAULT_TOURNAMENT = {
    "current_round": 0,      # Current round number (0 = not started)
    "total_rounds": 0,       # Total number of rounds in tournament
    "status": "setup",       # Tournament status: setup, in_progress, completed
    "num_courts": 1          # Number of courts available
}


def ensure_data_dir():
    """Create data directory if it doesn't exist.

    This ensures the data directory exists before attempting to read or
    write files. The exist_ok=True parameter prevents errors if the
    directory already exists.
    """
    DATA_DIR.mkdir(exist_ok=True)


def load_json(filename, default):
    """Load JSON data from file, return default if file doesn't exist.

    Args:
        filename: Name of the JSON file to load (e.g., "players.json")
        default: Default value to return if file doesn't exist or is corrupted

    Returns:
        Parsed JSON data or the default value if loading fails
    """
    # Ensure data directory exists before attempting to read
    ensure_data_dir()
    filepath = DATA_DIR / filename

    # Check if file exists before trying to read it
    if filepath.exists():
        try:
            # Open and parse the JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted or can't be read, return default value
            return default
    # File doesn't exist, return default value
    return default


def save_json(filename, data):
    """Save data to JSON file.

    Args:
        filename: Name of the JSON file to save to (e.g., "players.json")
        data: Python data structure to serialize to JSON
    """
    # Ensure data directory exists before attempting to write
    ensure_data_dir()
    filepath = DATA_DIR / filename

    # Write data to JSON file with pretty formatting
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        # indent=2 for readable formatting

# ============================================================================
# Player data operations
# ============================================================================


def get_players():
    """Get list of all players from storage.

    Returns:
        List of player dictionaries, each with 'id' and 'name' keys
    """
    return load_json("players.json", DEFAULT_PLAYERS)


def save_players(players):
    """Save players list to storage.

    Args:
        players: List of player dictionaries to save
    """
    save_json("players.json", players)

# ============================================================================
# Team data operations
# ============================================================================


def get_teams():
    """Get list of all teams from storage.

    Returns:
        List of team dictionaries, each with 'id', 'player1', and
        'player2' keys
    """
    return load_json("teams.json", DEFAULT_TEAMS)


def save_teams(teams):
    """Save teams list to storage.

    Args:
        teams: List of team dictionaries to save
    """
    save_json("teams.json", teams)

# ============================================================================
# Match data operations
# ============================================================================


def get_matches():
    """Get list of all matches from storage.

    Returns:
        List of match dictionaries with match details (round, teams,
        scores, etc.)
    """
    return load_json("matches.json", DEFAULT_MATCHES)


def save_matches(matches):
    """Save matches list to storage.

    Args:
        matches: List of match dictionaries to save
    """
    save_json("matches.json", matches)

# ============================================================================
# Tournament state operations
# ============================================================================


def get_tournament():
    """Get tournament state and settings from storage.

    Returns:
        Dictionary containing tournament configuration and current state
    """
    return load_json("tournament.json", DEFAULT_TOURNAMENT)


def save_tournament(tournament):
    """Save tournament state to storage.

    Args:
        tournament: Dictionary containing tournament state to save
    """
    save_json("tournament.json", tournament)


def add_player(name):
    """Add a new player to the tournament.

    Args:
        name: Name of the player to add

    Returns:
        The ID assigned to the new player
    """
    # Get existing players
    players = get_players()

    # Generate new player ID (simple incrementing ID based on current count)
    player_id = len(players) + 1

    # Create player dictionary
    player = {
        "id": player_id,
        "name": name
    }

    # Add player to list and save
    players.append(player)
    save_players(players)
    return player_id


def remove_player(player_id):
    """Remove a player from the tournament by ID.

    Args:
        player_id: ID of the player to remove

    Note: This does not automatically remove teams containing this player.
    """
    # Get existing players
    players = get_players()

    # Filter out the player with the specified ID
    players = [p for p in players if p["id"] != player_id]

    # Save updated list
    save_players(players)


def add_team(player1_id, player2_id):
    """Add a new team to the tournament by pairing two players.

    Args:
        player1_id: ID of the first player
        player2_id: ID of the second player

    Returns:
        The ID assigned to the new team
    """
    # Get existing teams
    teams = get_teams()

    # Generate new team ID (simple incrementing ID based on current count)
    team_id = len(teams) + 1

    # Create team dictionary linking two players
    team = {
        "id": team_id,
        "player1": player1_id,
        "player2": player2_id
    }

    # Add team to list and save
    teams.append(team)
    save_teams(teams)
    return team_id


def remove_team(team_id):
    """Remove a team from the tournament by ID.

    Args:
        team_id: ID of the team to remove

    Note: This does not automatically remove matches involving this team.
    """
    # Get existing teams
    teams = get_teams()

    # Filter out the team with the specified ID
    teams = [t for t in teams if t["id"] != team_id]

    # Save updated list
    save_teams(teams)


def update_tournament_settings(num_courts):
    """Update tournament settings, specifically the number of courts.

    Args:
        num_courts: Number of courts available for simultaneous matches
                   (affects how many matches can be scheduled per round)
    """
    # Get current tournament state
    tournament = get_tournament()

    # Update the number of courts setting
    tournament["num_courts"] = num_courts

    # Save updated tournament state
    save_tournament(tournament)
