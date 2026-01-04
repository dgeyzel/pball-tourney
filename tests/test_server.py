"""Integration tests for server.py HTTP handlers."""
import sys
from pathlib import Path
from io import BytesIO
from unittest.mock import MagicMock
import urllib.parse
import src.server as server
import src.storage as storage

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ResponseTracker:
    """Tracks HTTP response data for testing."""
    def __init__(self):
        self.status_code = None
        self.headers = {}
        self.body = b""
        self.redirect_location = None


def create_handler(path, method='GET', post_data=None):
    """Helper function to create a handler instance for testing."""
    # Create minimal mock objects needed for handler initialization
    mock_request = MagicMock()
    mock_server = MagicMock()

    # Create handler
    handler = server.TournamentHandler(mock_request,
                                       ("127.0.0.1", 8000), mock_server)

    # Set up handler attributes
    handler.path = path
    handler.headers = {}

    if post_data:
        post_bytes = urllib.parse.urlencode(post_data).encode('utf-8')
        handler.rfile = BytesIO(post_bytes)
        handler.headers['Content-Length'] = str(len(post_bytes))
    else:
        handler.rfile = BytesIO()
        handler.headers['Content-Length'] = '0'

    # Create BytesIO for wfile to capture output
    handler.wfile = BytesIO()

    # Create response tracker
    response = ResponseTracker()

    # Wrap methods to track calls
    original_send_response = handler.send_response
    original_send_header = handler.send_header

    def track_send_response(code):
        response.status_code = code
        original_send_response(code)

    def track_send_header(key, value):
        response.headers[key] = value
        original_send_header(key, value)

    handler.send_response = track_send_response
    handler.send_header = track_send_header

    # Capture redirects
    original_send_redirect = handler.send_redirect

    def track_send_redirect(location):
        response.redirect_location = location
        response.status_code = 302
        original_send_redirect(location)
    handler.send_redirect = track_send_redirect

    # Capture error calls
    original_send_error = handler.send_error

    def track_send_error(code, message):
        response.status_code = code
        original_send_error(code, message)
    handler.send_error = track_send_error

    return handler, response


class TestGETEndpoints:
    """Tests for GET request handlers."""

    def test_index_page_returns_200(self, setup_test_data):
        """Test that index page returns 200 OK."""
        handler, response = create_handler('/')
        handler.do_GET()

        body = handler.wfile.getvalue()
        assert response.status_code == 200
        assert b"Pickleball Tournament" in body

    def test_index_page_includes_status(self, setup_test_data):
        """Test that index page includes tournament status."""
        handler, response = create_handler('/')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "Status:" in body or "status" in body.lower()

    def test_index_page_shows_standings(self, setup_test_data):
        """Test that index page displays standings."""
        handler, response = create_handler('/')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "Standings" in body or "standings" in body.lower()

    def test_settings_page_returns_200(self, setup_test_data):
        """Test that settings page returns 200 OK."""
        handler, response = create_handler('/settings')
        handler.do_GET()

        assert response.status_code == 200
        assert b"Tournament Settings" in handler.wfile.getvalue()

    def test_settings_page_shows_court_setting(self, setup_test_data):
        """Test that settings page displays current court count."""
        handler, response = create_handler('/settings')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "num_courts" in body or "Courts" in body

    def test_players_page_returns_200(self, setup_test_data):
        """Test that players page returns 200 OK."""
        handler, response = create_handler('/players')
        handler.do_GET()

        assert response.status_code == 200
        assert b"Players" in handler.wfile.getvalue()

    def test_players_page_shows_player_list(self, setup_test_data):
        """Test that players page displays player list."""
        handler, response = create_handler('/players')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "Alice" in body or "Registered Players" in body

    def test_players_page_has_add_form(self, setup_test_data):
        """Test that players page has form to add players."""
        handler, response = create_handler('/players')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "Add Player" in body
        assert "/add_player" in body

    def test_teams_page_returns_200(self, setup_test_data):
        """Test that teams page returns 200 OK."""
        handler, response = create_handler('/teams')
        handler.do_GET()

        assert response.status_code == 200
        assert b"Teams" in handler.wfile.getvalue()

    def test_teams_page_shows_team_list(self, setup_test_data):
        """Test that teams page displays team list."""
        handler, response = create_handler('/teams')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "Registered Teams" in body or "Teams" in body

    def test_teams_page_has_add_form(self, setup_test_data):
        """Test that teams page has form to create teams."""
        handler, response = create_handler('/teams')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "Form Team" in body or "Create Team" in body
        assert "/add_team" in body

    def test_matches_page_returns_200(self, setup_test_data):
        """Test that matches page returns 200 OK."""
        handler, response = create_handler('/matches')
        handler.do_GET()

        assert response.status_code == 200
        assert b"Matches" in handler.wfile.getvalue()

    def test_matches_page_shows_matches(self, setup_test_data):
        """Test that matches page displays matches."""
        handler, response = create_handler('/matches')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "Round" in body or "Match" in body

    def test_standings_page_returns_200(self, setup_test_data):
        """Test that standings page returns 200 OK."""
        handler, response = create_handler('/standings')
        handler.do_GET()

        assert response.status_code == 200
        assert b"Standings" in handler.wfile.getvalue()

    def test_standings_page_shows_standings_table(self, setup_test_data):
        """Test that standings page displays standings table."""
        handler, response = create_handler('/standings')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "Rank" in body or "Wins" in body or "Losses" in body

    def test_unknown_path_returns_404(self, setup_test_data):
        """Test that unknown paths return 404 error."""
        handler, response = create_handler('/nonexistent')

        # Mock send_error to capture the error
        error_called = []

        def mock_send_error(code, message):
            error_called.append((code, message))

        handler.send_error = mock_send_error
        handler.do_GET()

        assert len(error_called) == 1
        assert error_called[0][0] == 404


class TestPOSTEndpoints:
    """Tests for POST request handlers."""

    def test_add_player_redirects(self, temp_data_dir):
        """Test that adding a player redirects to players page."""
        handler, response = create_handler('/add_player', 'POST',
                                           {'name': 'Test Player'})

        redirect_location = []

        def mock_send_redirect(location):
            redirect_location.append(location)

        handler.send_redirect = mock_send_redirect
        handler.do_POST()

        assert redirect_location == ['/players']
        assert len(storage.get_players()) > 0

    def test_add_player_creates_player(self, temp_data_dir):
        """Test that POST to add_player actually creates a player."""
        players_before = len(storage.get_players())

        handler, response = create_handler('', '',)
        handler.send_redirect = lambda x: None
        handler.do_POST()

        players_after = storage.get_players()
        assert len(players_after) == players_before + 1
        assert any(p["name"] == "New Player" for p in players_after)

    def test_remove_player_redirects(self, setup_test_data):
        """Test that removing a player redirects to players page."""
        handler, response = create_handler('', '',)

        redirect_location = []

        def mock_send_redirect(location):
            redirect_location.append(location)

        handler.send_redirect = mock_send_redirect
        handler.do_POST()

        assert redirect_location == ['/players']

    def test_remove_player_removes_player(self, setup_test_data):
        """Test that POST to remove_player actually removes the player."""
        players_before = storage.get_players()
        player_count_before = len(players_before)

        handler, response = create_handler('', '',)
        handler.send_redirect = lambda x: None
        handler.do_POST()

        players_after = storage.get_players()
        assert len(players_after) == player_count_before - 1
        assert not any(p["id"] == 1 for p in players_after)

    def test_add_team_redirects(self, setup_test_data):
        """Test that adding a team redirects to teams page."""
        handler, response = create_handler('', '',)

        redirect_location = []

        def mock_send_redirect(location):
            """Mock send_redirect to capture redirect location."""
            redirect_location.append(location)

        handler.send_redirect = mock_send_redirect
        handler.do_POST()

        assert redirect_location == ['/teams']

    def test_add_team_creates_team(self, setup_test_data):
        """Test that POST to add_team actually creates a team."""
        teams_before = len(storage.get_teams())

        handler, response = create_handler('', '',)
        handler.send_redirect = lambda x: None
        handler.do_POST()

        teams_after = storage.get_teams()
        assert len(teams_after) == teams_before + 1

    def test_add_team_rejects_same_player(self, setup_test_data):
        """Test that adding a team with the same player twice is rejected."""
        teams_before = len(storage.get_teams())

        handler, response = create_handler('', '',)
        handler.send_redirect = lambda x: None
        handler.do_POST()

        teams_after = storage.get_teams()
        # Should not create a team with same player
        assert len(teams_after) == teams_before

    def test_remove_team_redirects(self, setup_test_data):
        """Test that removing a team redirects to teams page."""
        handler, response = create_handler('', '',)

        redirect_location = []

        def mock_send_redirect(location):
            redirect_location.append(location)

        handler.send_redirect = mock_send_redirect
        handler.do_POST()

        assert redirect_location == ['/teams']

    def test_remove_team_removes_team(self, setup_test_data):
        """Test that POST to remove_team actually removes the team."""
        teams_before = storage.get_teams()
        team_count_before = len(teams_before)

        handler, response = create_handler('', '',)
        handler.send_redirect = lambda x: None
        handler.do_POST()

        teams_after = storage.get_teams()
        assert len(teams_after) == team_count_before - 1
        assert not any(t["id"] == 1 for t in teams_after)

    def test_update_settings_redirects(self, setup_test_data):
        """Test that updating settings redirects to settings page."""
        handler, response = create_handler('', '',)

        redirect_location = []

        def mock_send_redirect(location):
            redirect_location.append(location)

        handler.send_redirect = mock_send_redirect
        handler.do_POST()

        assert redirect_location == ['/settings']

    def test_update_settings_updates_courts(self, setup_test_data):
        """Test that POST to update_settings actually updates court count."""
        handler, response = create_handler('', '',)
        handler.send_redirect = lambda x: None
        handler.do_POST()

        tournament_data = storage.get_tournament()()()
        assert tournament_data["num_courts"] == 5

    def test_generate_schedule_redirects(self, setup_test_data):
        """Test that generating schedule redirects to matches page."""
        handler, response = create_handler('/generate_schedule', 'POST', {})

        redirect_location = []

        def mock_send_redirect(location):
            redirect_location.append(location)

        handler.send_redirect = mock_send_redirect
        handler.do_POST()

        assert redirect_location == ['/matches']

    def test_generate_schedule_creates_matches(self, setup_test_data):
        """Test that POST to generate_schedule creates matches."""
        # Clear existing matches
        storage.save_matches([])

        handler, response = create_handler('/generate_schedule', 'POST', {})
        handler.send_redirect = lambda x: None
        handler.do_POST()

        matches = storage.get_matches()
        assert len(matches) > 0

    def test_update_match_redirects(self, setup_test_data):
        """Test that updating match redirects to matches page."""
        # Create a scheduled match
        storage.save_matches([{
            "id": 1,
            "round": 1,
            "team1": 1,
            "team2": 2,
            "score1": None,
            "score2": None,
            "winner": None,
            "status": "scheduled"
        }])

        handler, response = create_handler('/update_match', 'POST', {
            'match_id': '1',
            'score1': '11',
            'score2': '9'
        })

        redirect_location = []

        def mock_send_redirect(location):
            redirect_location.append(location)

        handler.send_redirect = mock_send_redirect
        handler.do_POST()

        assert redirect_location == ['/matches']

    def test_update_match_updates_scores(self, setup_test_data):
        """Test that POST to update_match actually updates match scores."""
        # Create a scheduled match
        storage.save_matches([{
            "id": 1,
            "round": 1,
            "team1": 1,
            "team2": 2,
            "score1": None,
            "score2": None,
            "winner": None,
            "status": "scheduled"
        }])

        handler, response = create_handler('/update_match', 'POST', {
            'match_id': '1',
            'score1': '11',
            'score2': '9'
        })
        handler.send_redirect = lambda x: None
        handler.do_POST()

        matches = storage.get_matches()
        match = next(m for m in matches if m["id"] == 1)
        assert match["score1"] == 11
        assert match["score2"] == 9
        assert match["status"] == "completed"

    def test_unknown_post_path_returns_404(self, setup_test_data):
        """Test that unknown POST paths return 404 error."""
        handler, response = create_handler('/nonexistent', 'POST', {})

        error_called = []

        def mock_send_error(code, message):
            error_called.append((code, message))

        handler.send_error = mock_send_error
        handler.do_POST()

        assert len(error_called) == 1
        assert error_called[0][0] == 404


class TestHTMLRendering:
    """Tests for HTML content rendering."""

    def test_all_pages_include_navigation(self, setup_test_data):
        """Test that all pages include navigation links."""
        pages = ['/', '/settings', '/players', '/teams',
                 "/matches", "/standings"]

        for page in pages:
            handler, response = create_handler(page)
            handler.do_GET()

            body = handler.wfile.getvalue().decode('utf-8')
            # Check for common navigation elements
            assert "href" in body or "nav" in body.lower()

    def test_index_page_includes_links(self, setup_test_data):
        """Test that index page includes links to other pages."""
        handler, response = create_handler('/')
        handler.do_GET()

        body = handler.wfile.getvalue().decode('utf-8')
        assert "/settings" in body or "/players" in body

    def test_pages_include_base_html_structure(self, setup_test_data):
        """Test that all pages include proper HTML structure."""
        pages = ['/', '/settings', '/players']

        for page in pages:
            handler, response = create_handler(page)
            handler.do_GET()

            body = handler.wfile.getvalue().decode('utf-8')
            assert "<html" in body.lower()
            assert "<head" in body.lower() or "</head" in body.lower()
            assert "<body" in body.lower() or "</body" in body.lower()
