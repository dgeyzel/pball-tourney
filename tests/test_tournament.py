"""Unit tests for tournament.py module."""
import pytest  # noqa: F401
import src.storage as storage
import src.tournament as tournament


class TestRoundRobinSchedule:
    """Tests for round-robin schedule generation."""

    def test_generate_schedule_requires_at_least_two_teams(
        self, temp_data_dir
    ):
        """Test that schedule generation does nothing with fewer than 2
        teams."""
        # No teams
        tournament.generate_round_robin_schedule()
        matches = storage.get_matches()
        assert len(matches) == 0

        # One team
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_team(1, 2)  # Valid team
        tournament.generate_round_robin_schedule()
        matches = storage.get_matches()
        # Still 0 because we need at least 2 teams for scheduling
        assert len(matches) == 0

    def test_generate_schedule_creates_all_pairings(self, temp_data_dir):
        """Test that schedule includes all possible team pairings."""
        # Create 8 players and 4 teams (each player only in one team)
        for i in range(1, 9):
            storage.add_player(f"Player {i}")

        # Create 4 teams with no overlapping players
        storage.add_team(1, 2)  # Team 1
        storage.add_team(3, 4)  # Team 2
        storage.add_team(5, 6)  # Team 3
        storage.add_team(7, 8)  # Team 4

        tournament.generate_round_robin_schedule()

        matches = storage.get_matches()
        # With 4 teams, 1 court, 6 rounds:
        # Each round has 1 match + 2 byes = 3 activities
        # Total: 6 rounds * 3 activities = 18
        assert len(matches) == 18

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

    def test_generate_schedule_respects_court_capacity(
        self, temp_data_dir
    ):
        """Test that matches are distributed across rounds based on court
        capacity."""
        # Create 12 players for 6 teams (each player only in one team)
        for i in range(1, 13):
            storage.add_player(f"Player {i}")

        storage.add_team(1, 2)   # Team 1
        storage.add_team(3, 4)   # Team 2
        storage.add_team(5, 6)   # Team 3
        storage.add_team(7, 8)   # Team 4
        storage.add_team(9, 10)  # Team 5
        storage.add_team(11, 12)   # Team 6

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

    def test_generate_schedule_handles_odd_number_of_teams(
        self, temp_data_dir
    ):
        """Test that bye rounds are assigned when there's an odd number of
        teams."""
        # Create 10 players for 5 teams (each player only in one team)
        for i in range(1, 11):
            storage.add_player(f"Player {i}")

        storage.add_team(1, 2)   # Team 1
        storage.add_team(3, 4)   # Team 2
        storage.add_team(5, 6)   # Team 3
        storage.add_team(7, 8)   # Team 4
        storage.add_team(9, 10)  # Team 5

        # Set court capacity to 2
        storage.update_tournament_settings(2)

        tournament.generate_round_robin_schedule()

        matches = storage.get_matches()
        tournament_state = storage.get_tournament()

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

        # Verify each team has exactly one activity per round
        for round_num in range(1, tournament_state["total_rounds"] + 1):
            round_matches = [m for m in matches if m["round"] == round_num]
            teams_active = set()
            for match in round_matches:
                if match["status"] == "bye":
                    teams_active.add(match["team1"])
                else:
                    teams_active.add(match["team1"])
                    teams_active.add(match["team2"])

            # All teams should be active in each round
            assert len(teams_active) == 5

    def test_generate_schedule_updates_tournament_state(self, temp_data_dir):
        """Test that schedule generation updates tournament state."""
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_player("Player 3")
        storage.add_player("Player 4")
        storage.add_team(1, 2)  # Team 1
        storage.add_team(3, 4)  # Team 2

        tournament.generate_round_robin_schedule()

        tournament_state = storage.get_tournament()
        assert tournament_state["status"] == "in_progress"
        assert tournament_state["current_round"] == 1
        assert tournament_state["total_rounds"] > 0

    def test_generate_schedule_clears_existing_matches(
        self, temp_data_dir
    ):
        """Test that generating a new schedule clears old matches."""
        # Create initial matches
        storage.save_matches([
            {
                "id": 1,
                "round": 1,
                "team1": 1,
                "team2": 2,
                "status": "completed",
            }
        ])

        # Create teams and generate new schedule
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_player("Player 3")
        storage.add_player("Player 4")
        storage.add_team(1, 2)  # Team 1
        storage.add_team(3, 4)  # Team 2

        tournament.generate_round_robin_schedule()

        matches = storage.get_matches()
        # Old completed match should be gone, new matches should exist
        assert not any(m.get("status") == "completed" for m in matches)
        assert len(matches) > 0

    def test_generate_schedule_8_teams_3_courts(self, temp_data_dir):
        """Test schedule generation with 16 players, 8 teams, and 3 courts.

        Verifies that the schedule has 10 rounds, each team plays 7 matches,
        and each team has 3 byes.
        """
        # Create 16 players
        for i in range(1, 17):
            storage.add_player(f"Player {i}")

        # Create 8 teams with no overlapping players
        storage.add_team(1, 2)    # Team 1
        storage.add_team(3, 4)    # Team 2
        storage.add_team(5, 6)    # Team 3
        storage.add_team(7, 8)    # Team 4
        storage.add_team(9, 10)   # Team 5
        storage.add_team(11, 12)  # Team 6
        storage.add_team(13, 14)  # Team 7
        storage.add_team(15, 16)  # Team 8

        # Set court capacity to 3
        storage.update_tournament_settings(3)

        # Generate the schedule
        tournament.generate_round_robin_schedule()

        matches = storage.get_matches()
        tournament_state = storage.get_tournament()

        # Verify there are 10 rounds total
        assert tournament_state["total_rounds"] == 10

        # Count matches and byes per team
        team_matches = {i: 0 for i in range(1, 9)}  # Teams 1-8
        team_byes = {i: 0 for i in range(1, 9)}     # Teams 1-8

        for match in matches:
            if match["status"] == "bye":
                # Count bye for the team
                team_byes[match["team1"]] += 1
            else:
                # Count matches for both teams
                team_matches[match["team1"]] += 1
                team_matches[match["team2"]] += 1

        # Verify each team plays exactly 7 matches
        for team_id in range(1, 9):
            assert team_matches[team_id] == 7

        # Verify each team has exactly 3 byes
        for team_id in range(1, 9):
            assert team_byes[team_id] == 3

        # Verify that in each round, each team has exactly 1 match or bye
        for round_num in range(1, 11):  # Check rounds 1-10
            round_matches = [m for m in matches if m["round"] == round_num]

            # Track teams playing in this round and teams with byes
            teams_playing = set()
            teams_with_byes = set()

            for match in round_matches:
                if match["status"] == "bye":
                    teams_with_byes.add(match["team1"])
                else:
                    teams_playing.add(match["team1"])
                    teams_playing.add(match["team2"])

            # Every team should be playing or on a bye (not both, not neither)
            for team_id in range(1, 9):
                is_playing = team_id in teams_playing
                has_bye = team_id in teams_with_byes

                # XOR: exactly one of playing or bye, not both and not neither
                condition = (
                    (is_playing or has_bye) and not (is_playing and has_bye)
                )
                assert condition, (
                    f"Team {team_id} in round {round_num} should have exactly "
                    f"one match or one bye, but playing={is_playing}, "
                    f"bye={has_bye}"
                )


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
        assert standings[0]["ties"] == 0

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

    def test_calculate_standings_ignores_scheduled_matches(
        self, temp_data_dir
    ):
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
        assert team_standing["ties"] == 0

    def test_calculate_standings_sorts_correctly(
        self, temp_data_dir
    ):
        """Test that standings are sorted by points, then differential,
        then wins."""
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

    def test_calculate_standings_handles_ties(self, temp_data_dir):
        """Test that standings correctly handle tied matches."""
        # Setup teams
        storage.add_player("Player 1")
        storage.add_player("Player 2")
        storage.add_player("Player 3")
        storage.add_player("Player 4")
        storage.add_team(1, 2)  # Team 1
        storage.add_team(3, 4)  # Team 2

        # Create a tied match
        storage.save_matches([{
            "id": 1,
            "round": 1,
            "team1": 1,
            "team2": 2,
            "score1": 11,
            "score2": 11,
            "winner": None,
            "result": "tie",
            "status": "completed"
        }])

        standings = tournament.calculate_standings()

        # Both teams should have 1 tie and 0.5 points each
        team1_standing = next(s for s in standings if s["team_id"] == 1)
        team2_standing = next(s for s in standings if s["team_id"] == 2)

        assert team1_standing["ties"] == 1
        assert team1_standing["wins"] == 0
        assert team1_standing["losses"] == 0
        assert team1_standing["points"] == 0.5

        assert team2_standing["ties"] == 1
        assert team2_standing["wins"] == 0
        assert team2_standing["losses"] == 0
        assert team2_standing["points"] == 0.5


class TestMatchResults:
    """Tests for match result updates."""

    def test_update_match_result_sets_scores(self, setup_test_data):
        """Test that update_match_result sets scores correctly."""
        # Get a scheduled match
        matches = storage.get_matches()
        scheduled_match = next(
            (m for m in matches if m["status"] == "scheduled"), None
        )

        if scheduled_match:
            tournament.update_match_result(scheduled_match["id"], 11, 9)

            updated_matches = storage.get_matches()
            updated_match = next(
                m for m in updated_matches if m["id"] == scheduled_match["id"]
            )

            assert updated_match["score1"] == 11
            assert updated_match["score2"] == 9
            assert updated_match["status"] == "completed"

    def test_update_match_result_determines_winner_team1(
        self, setup_test_data
    ):
        """Test that update_match_result sets winner when team1
        wins."""
        matches = storage.get_matches()
        scheduled_match = next(
            (m for m in matches if m["status"] == "scheduled"), None
        )

        if scheduled_match:
            tournament.update_match_result(scheduled_match["id"], 11, 9)

            updated_matches = storage.get_matches()
            updated_match = next(
                m for m in updated_matches if m["id"] == scheduled_match["id"]
            )

            assert updated_match["winner"] == scheduled_match["team1"]

    def test_update_match_result_determines_winner_team2(
        self, setup_test_data
    ):
        """Test that update_match_result sets winner when team2 wins."""
        matches = storage.get_matches()
        scheduled_match = next(
            (m for m in matches if m["status"] == "scheduled"), None
        )

        if scheduled_match:
            tournament.update_match_result(scheduled_match["id"], 9, 11)

            updated_matches = storage.get_matches()
            updated_match = next(
                m for m in updated_matches if m["id"] == scheduled_match["id"]
            )

            assert updated_match["winner"] == scheduled_match["team2"]

    def test_update_match_result_handles_tie(self, setup_test_data):
        """Test that update_match_result handles ties."""
        matches = storage.get_matches()
        scheduled_match = next(
            (m for m in matches if m["status"] == "scheduled"), None
        )

        if scheduled_match:
            tournament.update_match_result(scheduled_match["id"], 11, 11)

            updated_matches = storage.get_matches()
            updated_match = next(
                m for m in updated_matches if m["id"] == scheduled_match["id"]
            )

            assert updated_match["winner"] is None
            assert updated_match["result"] == "tie"
            assert updated_match["status"] == "completed"


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_team_name_formats_correctly(self, setup_test_data):
        """Test that get_team_name formats team name correctly."""
        team_name = tournament.get_team_name(1)
        assert " & " in team_name
        assert "Alice" in team_name or "Bob" in team_name

    def test_get_team_name_handles_nonexistent_team(
        self, temp_data_dir
    ):
        """Test that get_team_name handles nonexistent team ID."""
        team_name = tournament.get_team_name(999)
        assert team_name == "Team 999"

    def test_get_team_players_returns_players(self, setup_test_data):
        """Test that get_team_players returns correct player
        list."""
        players = tournament.get_team_players(1)
        assert len(players) == 2
        assert all("name" in p for p in players)
        assert all("id" in p for p in players)

    def test_get_team_players_handles_nonexistent_team(
        self, temp_data_dir
    ):
        """Test that get_team_players returns empty list for
        nonexistent team."""
        players = tournament.get_team_players(999)
        assert players == []

    def test_get_matches_by_round_filters_correctly(
        self, setup_test_data
    ):
        """Test that get_matches_by_round returns only matches for
        specified round."""
        # Add matches in different rounds
        matches = storage.get_matches()
        if matches:
            round1_matches = tournament.get_matches_by_round(1)
            assert all(m["round"] == 1 for m in round1_matches)

            round2_matches = tournament.get_matches_by_round(2)
            assert all(m["round"] == 2 for m in round2_matches)
