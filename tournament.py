"""Tournament logic: round-robin scheduling and standings calculation."""
import itertools
from storage import get_teams, get_matches, get_tournament, save_matches, save_tournament

def generate_round_robin_schedule():
    """Generate round-robin schedule respecting court capacity."""
    teams = get_teams()
    tournament = get_tournament()
    num_courts = tournament.get("num_courts", 1)
    
    if len(teams) < 2:
        return
    
    # Clear existing matches if regenerating
    matches = []
    
    # Generate all possible team pairings
    team_ids = [team["id"] for team in teams]
    all_pairings = list(itertools.combinations(team_ids, 2))
    
    # Distribute pairings across rounds respecting court capacity
    round_num = 1
    current_round_matches = []
    
    for team1_id, team2_id in all_pairings:
        # Check if we need to start a new round
        if len(current_round_matches) >= num_courts:
            round_num += 1
            current_round_matches = []
        
        match = {
            "id": len(matches) + 1,
            "round": round_num,
            "team1": team1_id,
            "team2": team2_id,
            "score1": None,
            "score2": None,
            "winner": None,
            "status": "scheduled"  # scheduled, completed, bye
        }
        matches.append(match)
        current_round_matches.append(match)
    
    # Handle bye rounds for odd number of teams
    # In round-robin with odd teams, each team gets one bye
    # Distribute byes across existing rounds to minimize total rounds
    if len(teams) % 2 == 1:
        team_byes = {team_id: False for team_id in team_ids}
        # Distribute byes across rounds, one per round if possible
        for r in range(1, round_num + 1):
            round_matches = [m for m in matches if m["round"] == r]
            # Find a team that hasn't had a bye and isn't playing this round
            teams_playing = set()
            for m in round_matches:
                if m["team1"]:
                    teams_playing.add(m["team1"])
                if m["team2"]:
                    teams_playing.add(m["team2"])
            
            for team_id in team_ids:
                if not team_byes[team_id] and team_id not in teams_playing:
                    # Add bye to this round
                    bye_match = {
                        "id": len(matches) + 1,
                        "round": r,
                        "team1": team_id,
                        "team2": None,  # Bye
                        "score1": None,
                        "score2": None,
                        "winner": team_id,  # Bye is automatic win
                        "status": "bye"
                    }
                    matches.append(bye_match)
                    team_byes[team_id] = True
                    break
    
    save_matches(matches)
    
    # Update tournament state
    # Total rounds is the highest round number used
    max_round = max([m["round"] for m in matches]) if matches else round_num
    tournament["total_rounds"] = max_round
    tournament["current_round"] = 1
    tournament["status"] = "in_progress"
    save_tournament(tournament)

def calculate_standings():
    """Calculate current tournament standings."""
    teams = get_teams()
    matches = get_matches()
    
    standings = []
    
    for team in teams:
        team_id = team["id"]
        wins = 0
        losses = 0
        points_for = 0
        points_against = 0
        
        for match in matches:
            if match["status"] == "bye":
                # Byes don't count toward standings
                continue
            
            if match["status"] != "completed":
                continue
            
            # Check if this team is in the match
            is_team1 = match["team1"] == team_id
            is_team2 = match["team2"] == team_id
            
            if not (is_team1 or is_team2):
                continue
            
            # Get scores
            score1 = match.get("score1", 0) or 0
            score2 = match.get("score2", 0) or 0
            
            if is_team1:
                points_for += score1
                points_against += score2
                if match["winner"] == team_id:
                    wins += 1
                else:
                    losses += 1
            elif is_team2:
                points_for += score2
                points_against += score1
                if match["winner"] == team_id:
                    wins += 1
                else:
                    losses += 1
        
        point_differential = points_for - points_against
        points = wins  # 1 point per win, 0 per loss
        
        standings.append({
            "team_id": team_id,
            "wins": wins,
            "losses": losses,
            "points": points,
            "points_for": points_for,
            "points_against": points_against,
            "point_differential": point_differential
        })
    
    # Sort standings: points (desc), then point differential (desc), then head-to-head
    standings.sort(key=lambda x: (-x["points"], -x["point_differential"], -x["wins"]))
    
    return standings

def get_team_name(team_id):
    """Get team name from team ID."""
    teams = get_teams()
    for team in teams:
        if team["id"] == team_id:
            players = get_team_players(team_id)
            return f"{players[0]['name']} & {players[1]['name']}"
    return f"Team {team_id}"

def get_team_players(team_id):
    """Get player objects for a team."""
    from storage import get_players
    teams = get_teams()
    players = get_players()
    
    for team in teams:
        if team["id"] == team_id:
            player1 = next((p for p in players if p["id"] == team["player1"]), None)
            player2 = next((p for p in players if p["id"] == team["player2"]), None)
            return [player1, player2] if player1 and player2 else []
    return []

def update_match_result(match_id, score1, score2):
    """Update match result and determine winner."""
    matches = get_matches()
    
    for match in matches:
        if match["id"] == match_id:
            match["score1"] = score1
            match["score2"] = score2
            
            # Determine winner (higher score wins)
            if score1 > score2:
                match["winner"] = match["team1"]
            elif score2 > score1:
                match["winner"] = match["team2"]
            else:
                # Tie - could handle differently, for now no winner
                match["winner"] = None
            
            match["status"] = "completed"
            break
    
    save_matches(matches)

def get_matches_by_round(round_num):
    """Get all matches for a specific round."""
    matches = get_matches()
    return [m for m in matches if m["round"] == round_num]

