"""Unit tests for storage.py module."""
import json
import src.storage as storage


class TestDataDirectory:
    """Tests for data directory creation."""

    def test_ensure_data_dir_creates_directory(self, temp_data_dir):
        """Test that ensure_data_dir creates the directory if it doesn't
        exist."""
        # Remove directory if it exists
        if temp_data_dir.exists():
            temp_data_dir.rmdir()

        # Call ensure_data_dir
        storage.ensure_data_dir()

        # Verify directory was created
        assert temp_data_dir.exists()
        assert temp_data_dir.is_dir()

    def test_ensure_data_dir_idempotent(self, temp_data_dir):
        storage.ensure_data_dir()
        storage.ensure_data_dir()
        storage.ensure_data_dir()

        # Should still exist and be a directory
        assert temp_data_dir.exists()
        assert temp_data_dir.is_dir()


class TestJSONOperations:
    """Tests for JSON file loading and saving."""

    def test_load_json_returns_default_when_file_missing(self, temp_data_dir):
        """Test that load_json returns default value when file doesn't
        exist."""
        default = {"test": "value"}
        result = storage.load_json("nonexistent.json", default)
        assert result == default

    def test_load_json_loads_existing_file(self, temp_data_dir):
        """Test that load_json loads data from existing file."""
        test_data = {"key": "value", "number": 42}
        filepath = temp_data_dir / "test.json"

        with open(filepath, 'w') as f:
            json.dump(test_data, f)

        result = storage.load_json("test.json", {})
        assert result == test_data

    def test_load_json_handles_corrupted_file(self, temp_data_dir):
        """Test that load_json returns default when file is corrupted."""
        filepath = temp_data_dir / "corrupted.json"
        filepath.write_text("not valid json {")

        default = {"default": True}
        result = storage.load_json("corrupted.json", default)
        assert result == default

    def test_save_json_creates_file(self, temp_data_dir):
        """Test that save_json creates a new file."""
        test_data = {"test": "data"}
        storage.save_json("test_save.json", test_data)

        filepath = temp_data_dir / "test_save.json"
        assert filepath.exists()

        with open(filepath, 'r') as f:
            loaded = json.load(f)
        assert loaded == test_data

    def test_save_json_overwrites_existing_file(self, temp_data_dir):
        """Test that save_json overwrites existing file."""
        filepath = temp_data_dir / "overwrite.json"
        filepath.write_text('{"old": "data"}')

        new_data = {"new": "data"}
        storage.save_json("overwrite.json", new_data)

        with open(filepath, 'r') as f:
            loaded = json.load(f)
        assert loaded == new_data


class TestPlayerOperations:
    """Tests for player CRUD operations."""

    def test_get_players_returns_empty_list_initially(self, temp_data_dir):
        """Test that get_players returns empty list when no players exist."""
        players = storage.get_players()
        assert players == []

    def test_get_players_returns_existing_players(self, setup_test_data):
        """Test that get_players returns saved players."""
        players = storage.get_players()
        assert len(players) > 0
        assert players[0]["name"] == "Alice"

    def test_add_player_creates_new_player(self, temp_data_dir):
        """Test that add_player creates a new player with correct ID."""
        player_id = storage.add_player("Test Player")

        assert player_id == 1
        players = storage.get_players()
        assert len(players) == 1
        assert players[0]["id"] == 1
        assert players[0]["name"] == "Test Player"

    def test_add_player_increments_id(self, temp_data_dir):
        """Test that add_player assigns sequential IDs."""
        id1 = storage.add_player("Player 1")
        id2 = storage.add_player("Player 2")
        id3 = storage.add_player("Player 3")

        assert id1 == 1
        assert id2 == 2
        assert id3 == 3

        players = storage.get_players()
        assert len(players) == 3
        assert [p["id"] for p in players] == [1, 2, 3]

    def test_remove_player_removes_player(self, setup_test_data):
        """Test that remove_player removes the specified player."""
        players_before = storage.get_players()
        assert len(players_before) > 0

        storage.remove_player(1)

        players_after = storage.get_players()
        assert len(players_after) == len(players_before) - 1
        assert not any(p["id"] == 1 for p in players_after)

    def test_remove_player_handles_nonexistent_id(self, setup_test_data):
        """Test that remove_player handles nonexistent player ID gracefully."""
        players_before = storage.get_players()
        count_before = len(players_before)

        storage.remove_player(999)  # Nonexistent ID

        players_after = storage.get_players()
        assert len(players_after) == count_before  # No change

    def test_save_players_persists_data(self, temp_data_dir):
        """Test that save_players saves player data to file."""
        players = [
            {"id": 1, "name": "Player 1"},
            {"id": 2, "name": "Player 2"}
        ]
        storage.save_players(players)

        # Verify by loading again
        loaded = storage.get_players()
        assert loaded == players


class TestTeamOperations:
    """Tests for team CRUD operations."""

    def test_get_teams_returns_empty_list_initially(self, temp_data_dir):
        """Test that get_teams returns empty list when no teams exist."""
        teams = storage.get_teams()
        assert teams == []

    def test_get_teams_returns_existing_teams(self, setup_test_data):
        """Test that get_teams returns saved teams."""
        teams = storage.get_teams()
        assert len(teams) > 0
        assert teams[0]["player1"] == 1
        assert teams[0]["player2"] == 2

    def test_add_team_creates_new_team(self, setup_test_data):
        """Test that add_team creates a new team."""
        team_id = storage.add_team(4, 5)

        teams = storage.get_teams()
        assert len(teams) == 4  # 3 from fixture + 1 new
        assert teams[-1]["id"] == team_id
        assert teams[-1]["player1"] == 4
        assert teams[-1]["player2"] == 5

    def test_add_team_increments_id(self, setup_test_data):
        """Test that add_team assigns sequential IDs."""
        id1 = storage.add_team(4, 5)
        id2 = storage.add_team(1, 5)

        assert id1 == 4  # 3 teams from fixture, so next is 4
        assert id2 == 5

        teams = storage.get_teams()
        assert teams[-2]["id"] == id1
        assert teams[-1]["id"] == id2

    def test_remove_team_removes_team(self, setup_test_data):
        """Test that remove_team removes the specified team."""
        teams_before = storage.get_teams()
        assert len(teams_before) > 0

        storage.remove_team(1)

        teams_after = storage.get_teams()
        assert len(teams_after) == len(teams_before) - 1
        assert not any(t["id"] == 1 for t in teams_after)

    def test_remove_team_handles_nonexistent_id(self, setup_test_data):
        """Test that remove_team handles nonexistent team ID gracefully."""
        teams_before = storage.get_teams()
        count_before = len(teams_before)

        storage.remove_team(999)  # Nonexistent ID

        teams_after = storage.get_teams()
        assert len(teams_after) == count_before  # No change

    def test_save_teams_persists_data(self, temp_data_dir):
        """Test that save_teams saves team data to file."""
        teams = [
            {"id": 1, "player1": 1, "player2": 2},
            {"id": 2, "player1": 3, "player2": 4}
        ]
        storage.save_teams(teams)

        # Verify by loading again
        loaded = storage.get_teams()
        assert loaded == teams


class TestMatchOperations:
    """Tests for match data operations."""

    def test_get_matches_returns_empty_list_initially(self, temp_data_dir):
        """Test that get_matches returns empty list when no matches exist."""
        matches = storage.get_matches()
        assert matches == []

    def test_get_matches_returns_existing_matches(self, setup_test_data):
        """Test that get_matches returns saved matches."""
        matches = storage.get_matches()
        assert len(matches) > 0
        assert matches[0]["round"] == 1

    def test_save_matches_persists_data(self, temp_data_dir):
        """Test that save_matches saves match data to file."""
        matches = [
            {
                "id": 1,
                "round": 1,
                "team1": 1,
                "team2": 2,
                "score1": 11,
                "score2": 9,
                "winner": 1,
                "status": "completed"
            }
        ]
        storage.save_matches(matches)

        # Verify by loading again
        loaded = storage.get_matches()
        assert loaded == matches


class TestTournamentOperations:
    """Tests for tournament state operations."""

    def test_get_tournament_returns_default_initially(self, temp_data_dir):
        """Test that get_tournament returns default when no tournament data
        exists."""
        tournament = storage.get_tournament()
        assert tournament["status"] == "setup"
        assert tournament["current_round"] == 0
        assert tournament["total_rounds"] == 0
        assert tournament["num_courts"] == 1

    def test_get_tournament_returns_existing_data(self, setup_test_data):
        """Test that get_tournament returns saved tournament data."""
        tournament = storage.get_tournament()
        assert tournament["status"] == "in_progress"
        assert tournament["current_round"] == 1
        assert tournament["total_rounds"] == 3
        assert tournament["num_courts"] == 2

    def test_update_tournament_settings_updates_courts(self, setup_test_data):
        """Test that update_tournament_settings updates num_courts."""
        storage.update_tournament_settings(5)

        tournament = storage.get_tournament()
        assert tournament["num_courts"] == 5

    def test_update_tournament_settings_preserves_other_fields(
            self, setup_test_data):
        """Test that update_tournament_settings preserves other tournament
        fields."""
        original = storage.get_tournament()
        original_status = original["status"]
        original_round = original["current_round"]

        storage.update_tournament_settings(3)

        updated = storage.get_tournament()
        assert updated["num_courts"] == 3
        assert updated["status"] == original_status
        assert updated["current_round"] == original_round

    def test_save_tournament_persists_data(self, temp_data_dir):
        """Test that save_tournament saves tournament data to file."""
        tournament = {
            "current_round": 2,
            "total_rounds": 5,
            "status": "in_progress",
            "num_courts": 3
        }
        storage.save_tournament(tournament)

        # Verify by loading again
        loaded = storage.get_tournament()
        assert loaded == tournament
