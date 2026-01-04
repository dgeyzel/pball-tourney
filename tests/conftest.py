"""Pytest configuration and shared fixtures for tournament tests."""
import pytest
import sys
import src.storage as storage  # noqa: E402
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory and patch storage.DATA_DIR to use it.

    This fixture ensures each test uses an isolated data directory, preventing
    tests from interfering with each other or with production data.
    """
    temp_dir = tmp_path / "data"
    temp_dir.mkdir()

    # Patch the DATA_DIR in the storage module
    with patch.object(storage, 'DATA_DIR', temp_dir):
        yield temp_dir


@pytest.fixture
def sample_players():
    """Fixture providing sample player data for tests."""
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
        {"id": 3, "name": "Charlie"},
        {"id": 4, "name": "Diana"},
        {"id": 5, "name": "Eve"},
    ]


@pytest.fixture
def sample_teams(sample_players):
    """Fixture providing sample team data for tests."""
    return [
        {"id": 1, "player1": 1, "player2": 2},  # Alice & Bob
        {"id": 2, "player1": 3, "player2": 4},  # Charlie & Diana
        {"id": 3, "player1": 2, "player2": 5},  # Bob & Eve (changed to avoid duplicate assignments)
    ]


@pytest.fixture
def sample_matches():
    """Fixture providing sample match data for tests."""
    return [
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
            "round": 1,
            "team1": 1,
            "team2": 3,
            "score1": None,
            "score2": None,
            "winner": None,
            "status": "scheduled"
        },
    ]


@pytest.fixture
def sample_tournament():
    """Fixture providing sample tournament state for tests."""
    return {
        "current_round": 1,
        "total_rounds": 3,
        "status": "in_progress",
        "num_courts": 2
    }


@pytest.fixture
def setup_test_data(
    temp_data_dir,
    sample_players,
    sample_teams,
    sample_matches,
    sample_tournament
):
    """Fixture that sets up complete test data in the temporary directory.

    This fixture creates all necessary JSON files with sample data,
    making it easy to test functions that read from storage.
    """
    import json

    # Save all sample data to JSON files
    with open(temp_data_dir / "players.json", 'w') as f:
        json.dump(sample_players, f)

    with open(temp_data_dir / "teams.json", 'w') as f:
        json.dump(sample_teams, f)

    with open(temp_data_dir / "matches.json", 'w') as f:
        json.dump(sample_matches, f)

    with open(temp_data_dir / "tournament.json", 'w') as f:
        json.dump(sample_tournament, f)

    return {
        "players": sample_players,
        "teams": sample_teams,
        "matches": sample_matches,
        "tournament": sample_tournament
    }


@pytest.fixture
def http_client():
    """Fixture for creating an HTTP test client.

    Returns a helper function that can make requests to the server.
    """
    import urllib.request
    import urllib.parse
    import socketserver
    import threading
    import time

    class TestClient:
        def __init__(self, handler_class, port=0):
            self.port = port
            self.handler_class = handler_class
            self.server = None
            self.thread = None

        def start(self):
            """Start the test server in a background thread."""
            self.server = socketserver.TCPServer(
                ("", self.port), self.handler_class
            )
            self.port = self.server.server_address[1]
            self.thread = threading.Thread(
                target=self.server.serve_forever, daemon=True
            )
            self.thread.start()
            # Give server a moment to start
            time.sleep(0.1)

        def stop(self):
            """Stop the test server."""
            if self.server:
                self.server.shutdown()

        def get(self, path):
            """Make a GET request to the server."""
            url = f"http://localhost:{self.port}{path}"
            req = urllib.request.Request(url)
            try:
                with urllib.request.urlopen(req) as response:
                    return {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body": response.read().decode('utf-8')
                    }
            except urllib.error.HTTPError as e:
                return {
                    "status": e.code,
                    "headers": dict(e.headers),
                    "body": (
                        e.read().decode('utf-8') if hasattr(e, 'read') else ""
                    )
                }

        def post(self, path, data):
            """Make a POST request to the server."""
            url = f"http://localhost:{self.port}{path}"
            post_data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(
                url, data=post_data, method='POST'
            )
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            try:
                with urllib.request.urlopen(req) as response:
                    return {
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body": (
                            response.read().decode('utf-8')
                            if hasattr(response, 'read') else ""
                        )
                    }
            except urllib.error.HTTPError as e:
                return {
                    "status": e.code,
                    "headers": dict(e.headers),
                    "body": (
                        e.read().decode('utf-8') if hasattr(e, 'read') else ""
                    )
                }

    return TestClient
