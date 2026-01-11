"""Tournament logic: round-robin scheduling and standings calculation.

This module handles the core tournament logic including:
- Generating round-robin schedules (every team plays every other team once)
- Calculating standings based on match results
- Managing match results and winners
"""
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
    The number of rounds is based on court availability and team count.
    Each team has exactly one activity (match or bye) per round.

    Total matches = ((n^2) - n)/2 where n = number of teams
    If courts ≤ n/2: rounds = ceil(total_matches / courts)
    If courts > n/2: rounds = ceil(total_matches / (n/2))
    """
    import math

    # Get current teams and tournament settings
    teams = get_teams()
    tournament = get_tournament()
    num_courts = tournament.get("num_courts", 1)

    # Need at least 2 teams to generate a schedule
    if len(teams) < 2:
        return

    # Clear existing matches if regenerating schedule
    matches = []
    team_ids = [team["id"] for team in teams]
    n = len(team_ids)

    # Calculate total matches and rounds
    total_matches = (n * (n - 1)) // 2

    if num_courts <= n // 2:
        total_rounds = math.ceil(total_matches / num_courts)
    else:
        total_rounds = math.ceil(total_matches / (n // 2))

    # Create a standard round-robin schedule using the circle method
    # This ensures all pairings are created without conflicts
    round_robin_matches = _create_round_robin_circle(team_ids)

    # Distribute the round-robin matches across tournament rounds
    teams_in_round = {r: set() for r in range(1, total_rounds + 1)}

    # Collect all matches from RR schedule
    all_rr_matches = []
    for rr_round_matches in round_robin_matches:
        for match_pair in rr_round_matches:
            if len(match_pair) == 2:  # actual match
                all_rr_matches.append(match_pair)

    # Place matches in tournament rounds, ensuring no team conflicts
    for team1_id, team2_id in all_rr_matches:
        # Find a round where both teams available and there's court capacity
        placed = False
        for tournament_round in range(1, total_rounds + 1):
            # Check if both teams are available
            if (team1_id in teams_in_round[tournament_round] or
                    team2_id in teams_in_round[tournament_round]):
                continue

            # Check court capacity
            current_matches = len([
                m for m in matches
                if m["round"] == tournament_round and m["status"] != "bye"
            ])
            if num_courts <= n // 2:
                max_matches = num_courts
            else:
                max_matches = n // 2

            if current_matches >= max_matches:
                continue

            # Place the match
            match = {
                "id": len(matches) + 1,
                "round": tournament_round,
                "team1": team1_id,
                "team2": team2_id,
                "score1": None,
                "score2": None,
                "winner": None,
                "result": None,  # 'win', 'loss', or 'tie'
                "status": "scheduled"
            }
            matches.append(match)
            teams_in_round[tournament_round].add(team1_id)
            teams_in_round[tournament_round].add(team2_id)
            placed = True
            break

        assert placed, (
            f"Could not place match between teams {team1_id} and {team2_id}"
        )

    # Assign byes to ensure each team has exactly one activity per round
    for round_num in range(1, total_rounds + 1):
        teams_with_activity = teams_in_round[round_num]
        teams_needing_bye = [
            team_id for team_id in team_ids
            if team_id not in teams_with_activity
        ]

        # Assign byes to teams that need them
        for team_id in teams_needing_bye:
            bye_match = {
                "id": len(matches) + 1,
                "round": round_num,
                "team1": team_id,
                "team2": None,
                "score1": None,
                "score2": None,
                "winner": team_id,
                "result": "bye",  # bye matches have special result
                "status": "bye"
            }
            matches.append(bye_match)
            teams_in_round[round_num].add(team_id)

    # Validate the schedule
    _validate_schedule(team_ids, matches, total_rounds)

    # Save all generated matches to storage
    save_matches(matches)

    # Update tournament state to reflect the new schedule
    tournament["total_rounds"] = total_rounds
    tournament["current_round"] = 1              # Start at round 1
    tournament["status"] = "in_progress"         # Tournament is now active
    save_tournament(tournament)

    # Distribute the round-robin matches across tournament rounds
    # Since RR rounds don't have team conflicts, we can assign them
    # sequentially to tournament rounds
    teams_in_round = {r: set() for r in range(1, total_rounds + 1)}

    tournament_round = 1
    for rr_round_matches in round_robin_matches:
        # Assign all matches from this RR round to the current tournament round
        for match_pair in rr_round_matches:
            if len(match_pair) == 2:  # actual match
                team1_id, team2_id = match_pair

                # Check court capacity for this tournament round
                current_matches = len([
                    m for m in matches
                    if m["round"] == tournament_round and m["status"] != "bye"
                ])
                if num_courts <= n // 2:
                    max_matches = num_courts
                else:
                    max_matches = n // 2

                if current_matches >= max_matches:
                    # Move to next tournament round
                    tournament_round += 1
                    if tournament_round > total_rounds:
                        tournament_round = 1

                # Place the match
                match = {
                    "id": len(matches) + 1,
                    "round": tournament_round,
                    "team1": team1_id,
                    "team2": team2_id,
                    "score1": None,
                    "score2": None,
                    "winner": None,
                    "status": "scheduled"
                }
                matches.append(match)
                teams_in_round[tournament_round].add(team1_id)
                teams_in_round[tournament_round].add(team2_id)

        # Move to next tournament round for next RR round
        tournament_round += 1
        if tournament_round > total_rounds:
            tournament_round = 1

    # Assign byes to ensure each team has exactly one activity per round
    for round_num in range(1, total_rounds + 1):
        teams_with_activity = teams_in_round[round_num]
        teams_needing_bye = [
            team_id for team_id in team_ids
            if team_id not in teams_with_activity
        ]

        # Assign byes to teams that need them
        for team_id in teams_needing_bye:
            bye_match = {
                "id": len(matches) + 1,
                "round": round_num,
                "team1": team_id,
                "team2": None,
                "score1": None,
                "score2": None,
                "winner": team_id,
                "result": "bye",  # bye matches have special result
                "status": "bye"
            }
            matches.append(bye_match)
            teams_in_round[round_num].add(team_id)


def _create_round_robin_circle(team_ids):
    """Create a round-robin schedule using the circle method.

    Returns a list of rounds, where each round is a list of
    (team1, team2) tuples.
    For odd number of teams, includes (team, None) for byes.
    """
    teams = team_ids.copy()
    n = len(teams)

    if n % 2 == 1:
        # Odd number of teams, add a dummy team for byes
        teams.append(None)
        n += 1

    rounds = []
    for _ in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            team1 = teams[i]
            team2 = teams[n - 1 - i]
            if team1 is not None and team2 is not None:
                round_matches.append((min(team1, team2), max(team1, team2)))
            elif team1 is not None:
                round_matches.append((team1,))  # bye as single-element tuple
        rounds.append(round_matches)

        # Rotate teams (keep first team fixed, rotate the rest)
        teams = [teams[0]] + teams[-1:] + teams[1:-1]

    return rounds


def _validate_schedule(team_ids, matches, total_rounds):
    """Validate that the generated schedule meets all requirements."""
    n = len(team_ids)

    # Check 1: Total matches should be ((n^2) - n)/2
    actual_matches = len([m for m in matches if m["status"] != "bye"])
    expected_matches = (n * (n - 1)) // 2
    assert actual_matches == expected_matches, (
        f"Expected {expected_matches} matches, got {actual_matches}"
    )

    # Check 2: Each team should have exactly one activity per round
    team_activities_per_round = {
        team_id: {r: 0 for r in range(1, total_rounds + 1)}
        for team_id in team_ids
    }

    for match in matches:
        round_num = match["round"]
        if match["status"] == "bye":
            team_activities_per_round[match["team1"]][round_num] += 1
        else:
            team_activities_per_round[match["team1"]][round_num] += 1
            team_activities_per_round[match["team2"]][round_num] += 1

    for team_id in team_ids:
        for round_num in range(1, total_rounds + 1):
            activities = team_activities_per_round[team_id][round_num]
            assert activities == 1, (
                f"Team {team_id} has {activities} activities "
                f"in round {round_num}"
            )

    # Check 3: Each team pair should play exactly once
    team_pairings = set()
    for match in matches:
        if match["status"] != "bye":
            pair = tuple(sorted([match["team1"], match["team2"]]))
            assert pair not in team_pairings, f"Duplicate pairing: {pair}"
            team_pairings.add(pair)

    expected_pairings = set()
    for i in range(len(team_ids)):
        for j in range(i + 1, len(team_ids)):
            expected_pairings.add((team_ids[i], team_ids[j]))

    assert team_pairings == expected_pairings, (
        "Not all team pairings are scheduled exactly once"
    )


def calculate_standings():
    """Calculate current tournament standings based on completed matches.

    Standings are calculated by:
    1. Counting wins, losses, and ties for each team
    2. Calculating points for/against and point differential
    3. Awarding 1 point for wins, 0.5 points for ties
    4. Sorting by points, then point differential, then total wins

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
        ties = 0
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
                if match.get("result") == "tie":
                    ties += 1
                elif match["winner"] == team_id:
                    wins += 1
                else:
                    losses += 1
            elif is_team2:
                # This team is team2, so score2 is their score
                points_for += score2
                points_against += score1
                if match.get("result") == "tie":
                    ties += 1
                elif match["winner"] == team_id:
                    wins += 1
                else:
                    losses += 1

        # Calculate point differential (used for tie-breaking)
        point_differential = points_for - points_against
        points = wins + (ties * 0.5)  # 1 point per win, 0.5 points per tie

        # Add this team's standing to the list
        standings.append({
            "team_id": team_id,
            "wins": wins,
            "losses": losses,
            "ties": ties,
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

    The winner is determined by the higher score. Ties are also supported.
    The match status is updated to "completed" after scores are entered.
    """
    matches = get_matches()

    # Find the match by ID and update it
    for match in matches:
        if match["id"] == match_id:
            # Update scores
            match["score1"] = score1
            match["score2"] = score2

            # Determine winner and result based on scores (higher score wins)
            if score1 > score2:
                match["winner"] = match["team1"]
                match["result"] = "win"  # team1 won
            elif score2 > score1:
                match["winner"] = match["team2"]
                match["result"] = "win"  # team2 won
            else:
                # Tie - no winner assigned, but mark as tie
                match["winner"] = None
                match["result"] = "tie"

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
