# Pickleball Tournament Manager

A web-based tournament management application for organizing and tracking pickleball tournaments. This application provides a simple, intuitive interface for managing players, teams, matches, and standings in a round-robin tournament format.

## About This Project

This application was developed using Cursor IDE with AI assistance, demonstrating modern development practices including:

- **AI-Assisted Development**: Created using LLM tools with human oversight for quality assurance
- **Test-Driven Development**: Comprehensive test suite (87 tests) written alongside application code
- **Code Quality**: Follows PEP 8 style guidelines with automated linting
- **Clean Architecture**: Well-organized modular design with clear separation of concerns

## Features

- **Player Management**: Add and remove players from the tournament
- **Team Formation**: Create teams by pairing players together
- **Tournament Settings**: Configure the number of available courts
- **Round-Robin Scheduling**: Automatically generate a complete round-robin schedule that respects court capacity
- **Match Management**: Enter match results and track match status (scheduled, completed, bye)
- **Standings Calculation**: Real-time standings with wins, losses, points, and point differentials
- **Web Interface**: Clean, modern web interface accessible from any browser

## Requirements

- Python 3.6 or higher
- No external dependencies required for running the application (uses only Python standard library)
- pytest>=7.0.0 (for running tests, see Testing section)

## Installation

1. Clone or download this repository
2. Ensure you have Python 3.6+ installed on your system

## Running the Application

1. Open a terminal/command prompt in the project directory
2. Run the server:

   ```bash
   python run_server.py
   ```

   Or use the module directly:

   ```bash
   python -m src.server
   ```

   To specify a custom port:

   ```bash
   python run_server.py 8080
   ```

3. The server will start and display a message like:

   ```text
   Server running at http://localhost:8000/
   Press Ctrl+C to stop the server
   ```

4. Open your web browser and navigate to `http://localhost:8000/`

5. To stop the server, press `Ctrl+C` in the terminal

**Note**: If port 8000 is already in use, the server will automatically try the next available port (8001, 8002, etc.).

## Usage Guide

### 1. Configure Tournament Settings

- Navigate to the **Settings** page
- Set the number of available courts (this determines how many matches can run simultaneously per round)
- Click "Save Settings"

### 2. Add Players

- Go to the **Players** page
- Enter a player name in the form
- Click "Add Player"
- Repeat for all tournament participants
- You can remove players using the "Remove" button next to their name

### 3. Form Teams

- Navigate to the **Teams** page
- Select two players from the dropdown menus
- Click "Create Team"
- Continue until all teams are formed
- You need at least 2 teams to generate a schedule

### 4. Generate Schedule

- Once you have at least 2 teams, go to the **Teams** page
- Click the "Generate Tournament Schedule" button
- The system will create a complete round-robin schedule where every team plays every other team once
- Matches are distributed across rounds based on the number of courts configured

### 5. Enter Match Results

- Go to the **Matches** page
- Find the match you want to update
- Enter the scores for both teams
- Click "Submit"
- The winner is automatically determined based on the higher score
- Completed matches are highlighted in green

### 6. View Standings

- Navigate to the **Standings** page to see the current tournament rankings
- Standings are sorted by:
  1. Points (wins)
  2. Point differential (points for - points against)
  3. Total wins
- The standings update automatically as you enter match results

## Project Structure

```text
pball-tourney/
├── src/               # Source code directory
│   ├── __init__.py    # Package initialization
│   ├── server.py      # HTTP server and web interface
│   ├── tournament.py  # Tournament logic (scheduling, standings)
│   └── storage.py     # Data persistence (JSON file operations)
├── tests/             # Test suite (87 tests total)
│   ├── __init__.py    # Test package initialization
│   ├── conftest.py    # Pytest fixtures and configuration
│   ├── test_storage.py    # Storage module tests (29 tests)
│   ├── test_tournament.py # Tournament logic tests (22 tests)
│   └── test_server.py     # HTTP server integration tests (36 tests)
├── data/              # Data storage directory (created automatically)
│   ├── players.json   # Player data
│   ├── teams.json     # Team data
│   ├── matches.json   # Match data
│   └── tournament.json # Tournament state and settings
├── run_server.py     # Application entry point script
├── requirements.txt   # Python dependencies (pytest>=7.0.0)
├── agents.md          # Development guidelines and instructions
└── README.md          # This documentation
```

## Data Storage

All tournament data is stored in JSON files in the `data/` directory:

- **players.json**: List of all registered players
- **teams.json**: List of all teams (player pairings)
- **matches.json**: All match records with scores and results
- **tournament.json**: Tournament configuration and state

The data directory is created automatically if it doesn't exist. You can back up your tournament data by copying the `data/` directory.

## How It Works

- **Round-Robin Format**: Every team plays every other team exactly once
- **Court Capacity**: Matches are distributed across rounds so that no more than the configured number of courts are used simultaneously
- **Bye Handling**: If there's an odd number of teams, bye rounds are automatically assigned
- **Standings**: Teams are ranked by wins, then point differential, then total wins

## Code Quality

This project follows Python best practices:

- **PEP 8 Compliance**: Code follows Python style guidelines with 79-character line limits
- **Comprehensive Testing**: 87 tests covering all major functionality
- **Type Hints**: Ready for future type checking integration
- **Clean Architecture**: Well-organized modular design with clear separation of concerns

## Testing

The project includes a comprehensive test suite using pytest with 87 tests covering all functionality. All tests pass and are located in the `tests/` directory.

### Installing Test Dependencies

To run the tests, you'll need to install pytest:

```bash
pip install pytest
```

Or install from the requirements file:

```bash
pip install -r requirements.txt
```

### Running Tests

Run all tests:

```bash
pytest
```

Or specify the tests directory explicitly:

```bash
pytest tests/
```

Run tests with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_storage.py
```

Run a specific test function:

```bash
pytest tests/test_storage.py::test_add_player
```

### Test Structure

- **`tests/test_storage.py`**: Unit tests for storage operations (CRUD, file I/O) - 29 tests
- **`tests/test_tournament.py`**: Unit tests for tournament logic (scheduling, standings, match updates) - 22 tests
- **`tests/test_server.py`**: Integration tests for HTTP endpoints (GET/POST requests) - 36 tests
- **`tests/conftest.py`**: Shared pytest fixtures and configuration

All tests use isolated temporary directories to avoid affecting production data. The test suite provides comprehensive coverage of the application's functionality.

## Development Status

This project was developed using Cursor IDE with AI assistance, demonstrating modern development practices:

- **AI-Assisted Development**: Created using LLM tools with human oversight for quality assurance
- **Test-Driven Development**: Comprehensive test suite written alongside the application code
- **Code Quality**: Regular linting and style enforcement following PEP 8 guidelines
- **Continuous Testing**: All changes validated through automated test suite

## Troubleshooting

- **Port already in use**: The server will automatically try the next available port. You can also specify a different port manually: `python run_server.py <port_number>`
- **Data not saving**: Ensure the `data/` directory exists and is writable
- **Schedule not generating**: Make sure you have at least 2 teams formed
- **Tests failing**: Ensure pytest is installed (`pip install -r requirements.txt`) and run `pytest` from the project root

## License

This project is provided as-is for personal or educational use.
