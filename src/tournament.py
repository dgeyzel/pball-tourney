"""Tournament logic: round-robin scheduling and standings calculation.

This module handles the core tournament logic including:
- Generating round-robin schedules (every team plays every other team once)
- Calculating standings based on match results
- Managing match results and winners
"""
import itertools
from src.storage import (
    get_teams,
    get_matches,
    get_tournament,
    save_matches,
    save_tournament,
)


def generate_round_robin_schedule():
    """Generate a complete round-robin schedule respecting court capacity.

    In a round-robin tournament, every team plays every other team once.
    Matches are distributed across rounds based on the number of available
    courts, ensuring no more than num_courts matches are scheduled
    simultaneously.

    If there's an odd number of teams, bye rounds are automatically assigned
    so each team gets exactly one bye.
    """
    # Get current teams and tournament settings
    teams = get_teams()
    tournament = get_tournament()
    num_courts = tournament.get("num_courts", 1)

    # Need at least 2 teams to generate a schedule
    if len(teams) < 2:
        return

    # Clear existing matches if regenerating schedule
    matches = []

    # Generate all possible team pairings using combinations
    # itertools.combinations ensures each pair appears exactly once
    team_ids = [team["id"] for team in teams]
    all_pairings = list(itertools.combinations(team_ids, 2))

    # Distribute pairings across rounds respecting court capacity
    # Each round can have at most num_courts matches
    round_num = 1
    current_round_matches = []  # Track matches in current round

    # Process each team pairing
    for team1_id, team2_id in all_pairings:
        # Check if current round is full (reached court capacity)
        if len(current_round_matches) >= num_courts:
            # Start a new round
            round_num += 1
            current_round_matches = []

        # Create match record
        match = {
            "id": len(matches) + 1,
            "round": round_num,
            "team1": team1_id,
            "team2": team2_id,
            "score1": None,
            "score2": None,
            "winner": None,
            "status": "scheduled"
        }
        matches.append(match)
        current_round_matches.append(match)

    # Handle bye rounds for odd number of teams
    # In round-robin with odd teams, each team gets exactly one bye
    # Distribute byes across existing rounds to minimize total rounds
    if len(teams) % 2 == 1:
        # Track which teams have already received a bye
        team_byes = {team_id: False for team_id in team_ids}

        # Distribute byes across rounds, one per round if possible
        for r in range(1, round_num + 1):
            # Get all matches in this round
            round_matches = [m for m in matches if m["round"] == r]

            # Find which teams are playing in this round
            teams_playing = set()
            for m in round_matches:
                if m["team1"]:
                    teams_playing.add(m["team1"])
                if m["team2"]:
                    teams_playing.add(m["team2"])

            # Find a team that hasn't had a bye and isn't playing this round
            for team_id in team_ids:
                if not team_byes[team_id] and team_id not in teams_playing:
                    # Add bye match for this team in this round
                    bye_match = {
                        "id": len(matches) + 1,
                        "round": r,
                        "team1": team_id,
                        "team2": None,
                        "score1": None,
                        "score2": None,
                        "winner": team_id,
                        "status": "bye"
                    }
                    matches.append(bye_match)
                    team_byes[team_id] = True  # Mark this team as having a bye
                    break

    # Save all generated matches to storage
    save_matches(matches)

    # Update tournament state to reflect the new schedule
    # Total rounds is the highest round number used
    max_round = max([m["round"] for m in matches]) if matches else round_num
    tournament["total_rounds"] = max_round
    tournament["current_round"] = 1              # Start at round 1
    tournament["status"] = "in_progress"         # Tournament is now active
    save_tournament(tournament)


def calculate_standings():
    """Calculate current tournament standings based on completed matches.

    Standings are calculated by:
    1. Counting wins and losses for each team
    2. Calculating points for/against and point differential
    3. Sorting by points, then point differential, then total wins

    Returns:
        List of standing dictionaries, sorted by rank (best first)
    """
    teams = get_teams()
    matches = get_matches()

    standings = []

    # Calculate statistics for each team
    for team in teams:
        team_id = team["id"]
        wins = 0
        losses = 0
        points_for = 0      # Total points scored by this team
        points_against = 0  # Total points scored against this team

        # Process all matches to find this team's results
        for match in matches:
            # Skip bye matches (they don't affect standings)
            if match["status"] == "bye":
                continue

            # Only count completed matches
            if match["status"] != "completed":
                continue

            # Check if this team is participating in this match
            is_team1 = match["team1"] == team_id
            is_team2 = match["team2"] == team_id

            # Skip if this team is not in the match
            if not (is_team1 or is_team2):
                continue

            # Get scores from the match
            score1 = match.get("score1", 0) or 0
            score2 = match.get("score2", 0) or 0

            # Update statistics based on which team this is
            if is_team1:
                # This team is team1, so score1 is their score
                points_for += score1
                points_against += score2
                if match["winner"] == team_id:
                    wins += 1
                else:
                    losses += 1
            elif is_team2:
                # This team is team2, so score2 is their score
                points_for += score2
                points_against += score1
                if match["winner"] == team_id:
                    wins += 1
                else:
                    losses += 1

        # Calculate point differential (used for tie-breaking)
        point_differential = points_for - points_against
        points = wins  # Simple scoring: 1 point per win, 0 per loss

        # Add this team's standing to the list
        standings.append({
            "team_id": team_id,
            "wins": wins,
            "losses": losses,
            "points": points,
            "points_for": points_for,
            "points_against": points_against,
            "point_differential": point_differential
        })

    # Sort standings:
    # 1. By points (descending - most wins first)
    # 2. By point differential (descending - better differential first)
    # 3. By total wins (descending - more wins first)
    standings.sort(
        key=lambda x: (-x["points"], -x["point_differential"], -x["wins"])
    )

    return standings


def get_team_name(team_id):
    """Get formatted team name from team ID.

    Args:
        team_id: ID of the team

    Returns:
        Formatted string like "Player1 & Player2" or "Team {id}" if not found
    """
    teams = get_teams()

    # Find the team with matching ID
    for team in teams:
        if team["id"] == team_id:
            # Get the players in this team
            players = get_team_players(team_id)
            # Format as "Player1 & Player2"
            return f"{players[0]['name']} & {players[1]['name']}"

    # Team not found, return generic name
    return f"Team {team_id}"


def get_team_players(team_id):
    """Get player objects for a specific team.

    Args:
        team_id: ID of the team

    Returns:
        List of two player dictionaries, or empty list if team not found
    """
    from src import storage
    teams = get_teams()
    players = storage.get_players()

    # Find the team and look up its players
    for team in teams:
        if team["id"] == team_id:
            # Find player1 and player2 by their IDs
            player1 = next(
                (p for p in players if p["id"] == team["player1"]), None
            )
            player2 = next(
                (p for p in players if p["id"] == team["player2"]), None
            )
            return [player1, player2] if player1 and player2 else []

    # Team not found
    return []


def update_match_result(match_id, score1, score2):
    """Update match result with scores and determine the winner.

    Args:
        match_id: ID of the match to update
        score1: Score for team1
        score2: Score for team2

    The winner is determined by the higher score. The match status
    is updated to "completed" after scores are entered.
    """
    matches = get_matches()

    # Find the match by ID and update it
    for match in matches:
        if match["id"] == match_id:
            # Update scores
            match["score1"] = score1
            match["score2"] = score2

            # Determine winner based on scores (higher score wins)
            if score1 > score2:
                match["winner"] = match["team1"]
            elif score2 > score1:
                match["winner"] = match["team2"]
            else:
                # Tie - no winner assigned (could be handled differently)
                match["winner"] = None

            # Mark match as completed
            match["status"] = "completed"
            break

    # Save updated matches to storage
    save_matches(matches)


def get_matches_by_round(round_num):
    """Get all matches for a specific round.

    Args:
        round_num: Round number to get matches for

    Returns:
        List of match dictionaries for the specified round
    """
    matches = get_matches()
    return [m for m in matches if m["round"] == round_num]
