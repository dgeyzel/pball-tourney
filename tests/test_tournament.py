"""Unit tests for tournament.py module."""
import pytest
import storage
import tournament


class TestRoundRobinSchedule:
    """Tests for round-robin schedule generation."""
    
    def test_generate_schedule_requires_at_least_two_teams(self, temp_data_dir):
        """Test that schedule generation does nothing with fewer than 2 teams."""
        # No teams
        tournament.generate_round_robin_schedule()
        matches = storage.get_matches()
        assert len(matches) == 0
        
        # One team
        storage.add_player("Player 1")
        storage.add_team(1, 1)  # Invalid but tests the count check
        tournament.generate_round_robin_schedule()
        matches = storage.get_matches()
        assert len(matches) == 0
    
    def test_generate_schedule_creates_all_pairings(self, temp_data_dir):
        """Test that schedule includes all possible team pairings."""
        # Create 4 players and 4 teams (each player with every other)
        for i in range(1, 5):
            storage.add_player(f"Player {i}")
        
        # Create 4 teams
        storage.add_team(1, 2)  # Team 1
        storage.add_team(3, 4)  # Team 2
        storage.add_team(1, 3)  # Team 3
        storage.add_team(2, 4)  # Team 4
        
        tournament.generate_round_robin_schedule()
        
        matches = storage.get_matches()
        # With 4 teams, we should have C(4,2) = 6 matches
        assert len(matches) == 6
        
        # Verify all pairings exist
        team_ids = [1, 2, 3, 4]
        expected_pairings = set()
        for i in range(len(team_ids)):
            for j in range(i + 1, len(team_ids)):
                expected_pairings.add((team_ids[i], team_ids[j]))
        
        actual_pairings = set()
        for match in matches:
            if match["status"] != "bye":
                pair = tuple(sorted([match["team1"], match["team2"]]))
                actual_pairings.add(pair)
        
        assert actual_pairings == expected_pairings
    
    def test_generate_schedule_respects_court_capacity(self, temp_data_dir):
        """Test that matches are distributed across rounds based on court capacity."""
        # Create 6 teams
        for i in range(1, 7):
            storage.add_player(f"Player {i}")
        
        storage.add_team(1, 2)
        storage.add_team(3, 4)
        storage.add_team(5, 6)
        storage.add_team(1, 3)
        storage.add_team(2, 4)
        storage.add_team(5, 1)
        
        # Set court capacity to 2
        storage.update_tournament_settings(2)
        
        tournament.generate_round_robin_schedule()
        
        matches = storage.get_matches()
        # With 6 teams, we should have C(6,2) = 15 matches
        
        # Group matches by round
        rounds = {}
        for match in matches:
            if match["status"] != "bye":
                round_num = match["round"]
                if round_num not in rounds:
                    rounds[round_num] = []
                rounds[round_num].append(match)
        
        # Each round should have at most 2 matches (court capacity)
        for round_num, round_matches in rounds.items():
            assert len(round_matches) <= 2
    
    def test_generate_schedule_handles_odd_number_of_teams(self, temp_data_dir):
        """Test that bye rounds are assigned when there's an odd number of teams."""
        # Create 5 teams (odd number)
        for i in range(1, 6):
            storage.add_player(f"Player {i}")
        
        storage.add_team(1, 2)
        storage.add_team(3, 4)
        storage.add_team(5, 1)
        storage.add_team(2, 3)
        storage.add_team(4, 5)
        
        tournament.generate_round_robin_schedule()
        
        matches = storage.get_matches()
        
        # Count bye matches
        bye_matches = [m for m in matches if m["status"] == "bye"]
        # With 5 teams, each should get exactly one bye
        assert len(bye_matches) == 5
        
        # Verify each team gets exactly one bye
        team_byes = {}
        for match in bye_matches:
            team_id = match["team1"]
            team_byes[team_id] = team_byes.get(team_id, 0) + 1
        
        for team_id in range(1, 6):
            assert team_byes.get(team_id, 0) == 1
    
    def test_generate_schedule_updates_tournament_state(self, temp_data_dir):
        """Test that schedule generation updates tournament state."""
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_team(1, 2)
        storage.add_team(1, 1)  # Second team (invalid but for testing)
        
        tournament.generate_round_robin_schedule()
        
        tournament_state = storage.get_tournament()
        assert tournament_state["status"] == "in_progress"
        assert tournament_state["current_round"] == 1
        assert tournament_state["total_rounds"] > 0
    
    def test_generate_schedule_clears_existing_matches(self, temp_data_dir):
        """Test that generating a new schedule clears old matches."""
        # Create initial matches
        storage.save_matches([
            {"id": 1, "round": 1, "team1": 1, "team2": 2, "status": "completed"}
        ])
        
        # Create teams and generate new schedule
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_team(1, 2)
        storage.add_team(1, 1)
        
        tournament.generate_round_robin_schedule()
        
        matches = storage.get_matches()
        # Old match should be gone, new matches should exist
        assert not any(m["id"] == 1 for m in matches)
        assert len(matches) > 0


class TestStandingsCalculation:
    """Tests for standings calculation."""
    
    def test_calculate_standings_empty_with_no_matches(self, temp_data_dir):
        """Test that standings are empty when no matches are completed."""
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_team(1, 2)
        
        standings = tournament.calculate_standings()
        assert len(standings) == 1  # One team
        assert standings[0]["wins"] == 0
        assert standings[0]["losses"] == 0
    
    def test_calculate_standings_counts_wins_and_losses(self, setup_test_data):
        """Test that standings correctly count wins and losses."""
        # Add a completed match
        matches = storage.get_matches()
        if matches:
            match = matches[0]
            match["status"] = "completed"
            match["score1"] = 11
            match["score2"] = 9
            match["winner"] = match["team1"]
            storage.save_matches(matches)
        
        standings = tournament.calculate_standings()
        
        # Find the winning team
        winning_team = next(s for s in standings if s["team_id"] == 1)
        assert winning_team["wins"] > 0 or winning_team["losses"] > 0
    
    def test_calculate_standings_calculates_points(self, temp_data_dir):
        """Test that standings calculate points for/against correctly."""
        # Setup teams and matches
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_player("Player 3")
        storage.add_player("Player 4")
        storage.add_team(1, 2)  # Team 1
        storage.add_team(3, 4)  # Team 2
        
        # Create a completed match
        storage.save_matches([{
            "id": 1,
            "round": 1,
            "team1": 1,
            "team2": 2,
            "score1": 11,
            "score2": 7,
            "winner": 1,
            "status": "completed"
        }])
        
        standings = tournament.calculate_standings()
        
        team1_standing = next(s for s in standings if s["team_id"] == 1)
        team2_standing = next(s for s in standings if s["team_id"] == 2)
        
        assert team1_standing["points_for"] == 11
        assert team1_standing["points_against"] == 7
        assert team1_standing["point_differential"] == 4
        
        assert team2_standing["points_for"] == 7
        assert team2_standing["points_against"] == 11
        assert team2_standing["point_differential"] == -4
    
    def test_calculate_standings_ignores_scheduled_matches(self, temp_data_dir):
        """Test that standings only count completed matches."""
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_team(1, 2)
        
        # Create both scheduled and completed matches
        storage.save_matches([
            {
                "id": 1,
                "round": 1,
                "team1": 1,
                "team2": 2,
                "score1": None,
                "score2": None,
                "winner": None,
                "status": "scheduled"
            },
            {
                "id": 2,
                "round": 2,
                "team1": 1,
                "team2": 2,
                "score1": 11,
                "score2": 9,
                "winner": 1,
                "status": "completed"
            }
        ])
        
        standings = tournament.calculate_standings()
        team_standing = standings[0]
        
        # Should only count the completed match
        assert team_standing["wins"] == 1
        assert team_standing["points_for"] == 11
    
    def test_calculate_standings_ignores_bye_matches(self, temp_data_dir):
        """Test that standings ignore bye matches."""
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_team(1, 2)
        
        storage.save_matches([
            {
                "id": 1,
                "round": 1,
                "team1": 1,
                "team2": None,
                "score1": None,
                "score2": None,
                "winner": 1,
                "status": "bye"
            }
        ])
        
        standings = tournament.calculate_standings()
        team_standing = standings[0]
        
        # Bye should not count as a win
        assert team_standing["wins"] == 0
        assert team_standing["losses"] == 0
    
    def test_calculate_standings_sorts_correctly(self, temp_data_dir):
        """Test that standings are sorted by points, then differential, then wins."""
        # Setup multiple teams
        for i in range(1, 5):
            storage.add_player(f"Player {i}")
        
        storage.add_team(1, 2)  # Team 1
        storage.add_team(3, 4)  # Team 2
        
        # Create matches with different results
        storage.save_matches([
            {
                "id": 1,
                "round": 1,
                "team1": 1,
                "team2": 2,
                "score1": 11,
                "score2": 9,
                "winner": 1,
                "status": "completed"
            },
            {
                "id": 2,
                "round": 2,
                "team1": 1,
                "team2": 2,
                "score1": 11,
                "score2": 8,
                "winner": 1,
                "status": "completed"
            }
        ])
        
        standings = tournament.calculate_standings()
        
        # Team 1 should be first (more wins)
        assert standings[0]["team_id"] == 1
        assert standings[0]["wins"] == 2
        assert standings[1]["wins"] == 0


class TestMatchResults:
    """Tests for match result updates."""
    
    def test_update_match_result_sets_scores(self, setup_test_data):
        """Test that update_match_result sets scores correctly."""
        # Get a scheduled match
        matches = storage.get_matches()
        scheduled_match = next((m for m in matches if m["status"] == "scheduled"), None)
        
        if scheduled_match:
            tournament.update_match_result(scheduled_match["id"], 11, 9)
            
            updated_matches = storage.get_matches()
            updated_match = next(m for m in updated_matches if m["id"] == scheduled_match["id"])
            
            assert updated_match["score1"] == 11
            assert updated_match["score2"] == 9
            assert updated_match["status"] == "completed"
    
    def test_update_match_result_determines_winner_team1(self, setup_test_data):
        """Test that update_match_result sets winner when team1 wins."""
        matches = storage.get_matches()
        scheduled_match = next((m for m in matches if m["status"] == "scheduled"), None)
        
        if scheduled_match:
            tournament.update_match_result(scheduled_match["id"], 11, 9)
            
            updated_matches = storage.get_matches()
            updated_match = next(m for m in updated_matches if m["id"] == scheduled_match["id"])
            
            assert updated_match["winner"] == scheduled_match["team1"]
    
    def test_update_match_result_determines_winner_team2(self, setup_test_data):
        """Test that update_match_result sets winner when team2 wins."""
        matches = storage.get_matches()
        scheduled_match = next((m for m in matches if m["status"] == "scheduled"), None)
        
        if scheduled_match:
            tournament.update_match_result(scheduled_match["id"], 9, 11)
            
            updated_matches = storage.get_matches()
            updated_match = next(m for m in updated_matches if m["id"] == scheduled_match["id"])
            
            assert updated_match["winner"] == scheduled_match["team2"]
    
    def test_update_match_result_handles_tie(self, setup_test_data):
        """Test that update_match_result handles ties (no winner)."""
        matches = storage.get_matches()
        scheduled_match = next((m for m in matches if m["status"] == "scheduled"), None)
        
        if scheduled_match:
            tournament.update_match_result(scheduled_match["id"], 11, 11)
            
            updated_matches = storage.get_matches()
            updated_match = next(m for m in updated_matches if m["id"] == scheduled_match["id"])
            
            assert updated_match["winner"] is None
            assert updated_match["status"] == "completed"


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_get_team_name_formats_correctly(self, setup_test_data):
        """Test that get_team_name formats team name correctly."""
        team_name = tournament.get_team_name(1)
        assert " & " in team_name
        assert "Alice" in team_name or "Bob" in team_name
    
    def test_get_team_name_handles_nonexistent_team(self, temp_data_dir):
        """Test that get_team_name handles nonexistent team ID."""
        team_name = tournament.get_team_name(999)
        assert team_name == "Team 999"
    
    def test_get_team_players_returns_players(self, setup_test_data):
        """Test that get_team_players returns correct player list."""
        players = tournament.get_team_players(1)
        assert len(players) == 2
        assert all("name" in p for p in players)
        assert all("id" in p for p in players)
    
    def test_get_team_players_handles_nonexistent_team(self, temp_data_dir):
        """Test that get_team_players returns empty list for nonexistent team."""
        players = tournament.get_team_players(999)
        assert players == []
    
    def test_get_matches_by_round_filters_correctly(self, setup_test_data):
        """Test that get_matches_by_round returns only matches for specified round."""
        # Add matches in different rounds
        matches = storage.get_matches()
        if matches:
            round1_matches = tournament.get_matches_by_round(1)
            assert all(m["round"] == 1 for m in round1_matches)
            
            round2_matches = tournament.get_matches_by_round(2)
            assert all(m["round"] == 2 for m in round2_matches)
