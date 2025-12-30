"""HTTP server for pickleball tournament webapp using Python's built-in http.server.

This module implements a simple web server that serves HTML pages for managing
a pickleball tournament. It handles both GET requests (displaying pages) and
POST requests (processing form submissions).
"""
import http.server
import socketserver
import urllib.parse
import sys
from pathlib import Path
import storage
import tournament

# Default port for the web server
DEFAULT_PORT = 8000

class TournamentHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the tournament webapp.
    
    This class handles all incoming HTTP requests and routes them to the
    appropriate page handler or action handler.
    """
    
    def do_GET(self):
        """Handle GET requests - display pages to the user.
        
        Routes different URL paths to their corresponding page handlers.
        """
        # Parse the URL to get the path component
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Route to appropriate page handler based on path
        if path == '/' or path == '/index':
            self.serve_index()          # Main tournament overview page
        elif path == '/settings':
            self.serve_settings()      # Tournament settings page
        elif path == '/players':
            self.serve_players()        # Player management page
        elif path == '/teams':
            self.serve_teams()          # Team management page
        elif path == '/matches':
            self.serve_matches()        # Match schedule and results page
        elif path == '/standings':
            self.serve_standings()      # Tournament standings page
        else:
            # Unknown path - return 404 error
            self.send_error(404, "Page not found")
    
    def do_POST(self):
        """Handle POST requests - process form submissions.
        
        Reads form data from the request, performs the requested action,
        and redirects the user to the appropriate page.
        """
        # Parse the URL to get the path component
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        # Read POST data from the request body
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        # Parse form data (application/x-www-form-urlencoded format)
        post_params = urllib.parse.parse_qs(post_data)
        
        # Route to appropriate action handler based on path
        if path == '/add_player':
            # Add a new player to the tournament
            name = post_params.get('name', [''])[0]
            if name:
                storage.add_player(name)
            self.send_redirect('/players')
            
        elif path == '/remove_player':
            # Remove a player from the tournament
            player_id = int(post_params.get('player_id', ['0'])[0])
            if player_id:
                storage.remove_player(player_id)
            self.send_redirect('/players')
            
        elif path == '/add_team':
            # Create a new team by pairing two players
            player1_id = int(post_params.get('player1', ['0'])[0])
            player2_id = int(post_params.get('player2', ['0'])[0])
            # Validate: both players must be selected and different
            if player1_id and player2_id and player1_id != player2_id:
                storage.add_team(player1_id, player2_id)
            self.send_redirect('/teams')
            
        elif path == '/remove_team':
            # Remove a team from the tournament
            team_id = int(post_params.get('team_id', ['0'])[0])
            if team_id:
                storage.remove_team(team_id)
            self.send_redirect('/teams')
            
        elif path == '/update_settings':
            # Update tournament settings (number of courts)
            num_courts = int(post_params.get('num_courts', ['1'])[0])
            if num_courts > 0:
                storage.update_tournament_settings(num_courts)
            self.send_redirect('/settings')
            
        elif path == '/generate_schedule':
            # Generate the round-robin tournament schedule
            tournament.generate_round_robin_schedule()
            self.send_redirect('/matches')
            
        elif path == '/update_match':
            # Update match result with scores
            match_id = int(post_params.get('match_id', ['0'])[0])
            # Parse scores (handle empty strings as None)
            score1 = int(post_params.get('score1', ['0'])[0]) if post_params.get('score1', [''])[0] else None
            score2 = int(post_params.get('score2', ['0'])[0]) if post_params.get('score2', [''])[0] else None
            # Validate: match ID and both scores must be provided
            if match_id and score1 is not None and score2 is not None:
                tournament.update_match_result(match_id, score1, score2)
            self.send_redirect('/matches')
        else:
            # Unknown path - return 404 error
            self.send_error(404, "Page not found")
    
    def send_redirect(self, location):
        """Send HTTP 302 redirect response to the specified location.
        
        Args:
            location: URL path to redirect to (e.g., '/players')
        """
        self.send_response(302)  # HTTP 302 Found (temporary redirect)
        self.send_header('Location', location)
        self.end_headers()
    
    def serve_index(self):
        """Serve the main tournament overview page.
        
        Displays tournament status, current standings (top 5), and upcoming matches.
        """
        # Load tournament data
        tournament_state = storage.get_tournament()
        standings = tournament.calculate_standings()
        matches = storage.get_matches()
        current_round = tournament_state.get("current_round", 0)
        
        # Get upcoming matches (scheduled matches from current round, limit to 5)
        upcoming_matches = [m for m in matches if m["round"] == current_round and m["status"] == "scheduled"][:5]
        
        html = self.get_base_html("Tournament Overview", f"""
        <div class="container">
            <h1>Pickleball Tournament</h1>
            
            <div class="status-bar">
                <span>Status: <strong>{tournament_state.get('status', 'setup').replace('_', ' ').title()}</strong></span>
                <span>Courts: <strong>{tournament_state.get('num_courts', 1)}</strong></span>
                <span>Round: <strong>{current_round} / {tournament_state.get('total_rounds', 0)}</strong></span>
            </div>
            
            <div class="nav-links">
                <a href="/settings">Settings</a>
                <a href="/players">Players</a>
                <a href="/teams">Teams</a>
                <a href="/matches">Matches</a>
                <a href="/standings">Standings</a>
            </div>
            
            <div class="content-grid">
                <div class="card">
                    <h2>Current Standings</h2>
                    {self.render_standings_table(standings[:5])}
                    <a href="/standings" class="view-all">View All Standings →</a>
                </div>
                
                <div class="card">
                    <h2>Upcoming Matches</h2>
                    {self.render_matches_list(upcoming_matches)}
                    <a href="/matches" class="view-all">View All Matches →</a>
                </div>
            </div>
        </div>
        """)
        self.send_html(html)
    
    def serve_settings(self):
        """Serve the tournament settings page."""
        tournament_state = storage.get_tournament()
        num_courts = tournament_state.get("num_courts", 1)
        
        html = self.get_base_html("Tournament Settings", f"""
        <div class="container">
            <h1>Tournament Settings</h1>
            
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/players">Players</a>
                <a href="/teams">Teams</a>
                <a href="/matches">Matches</a>
            </div>
            
            <div class="card">
                <h2>Court Configuration</h2>
                <form method="POST" action="/update_settings">
                    <div class="form-group">
                        <label for="num_courts">Number of Courts:</label>
                        <input type="number" id="num_courts" name="num_courts" value="{num_courts}" min="1" required>
                    </div>
                    <button type="submit" class="btn-primary">Save Settings</button>
                </form>
                <p class="info">Each round will have at most this many matches scheduled simultaneously.</p>
            </div>
        </div>
        """)
        self.send_html(html)
    
    def serve_players(self):
        """Serve the players management page.
        
        Displays a form to add new players and a table of all registered players
        with options to remove them.
        """
        # Get all registered players
        players = storage.get_players()
        
        # Build HTML table rows for each player
        players_list = ""
        for player in players:
            players_list += f"""
            <tr>
                <td>{player['name']}</td>
                <td>
                    <form method="POST" action="/remove_player" style="display:inline;">
                        <input type="hidden" name="player_id" value="{player['id']}">
                        <button type="submit" class="btn-danger">Remove</button>
                    </form>
                </td>
            </tr>
            """
        
        html = self.get_base_html("Players", f"""
        <div class="container">
            <h1>Players</h1>
            
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/settings">Settings</a>
                <a href="/teams">Teams</a>
                <a href="/matches">Matches</a>
            </div>
            
            <div class="card">
                <h2>Add Player</h2>
                <form method="POST" action="/add_player">
                    <div class="form-group">
                        <label for="name">Player Name:</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <button type="submit" class="btn-primary">Add Player</button>
                </form>
            </div>
            
            <div class="card">
                <h2>Registered Players ({len(players)})</h2>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {players_list if players_list else '<tr><td colspan="2">No players registered yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
        """)
        self.send_html(html)
    
    def serve_teams(self):
        """Serve the teams management page.
        
        Displays a form to create teams by selecting two players, a table of
        all registered teams, and a button to generate the schedule (if 2+ teams exist).
        """
        # Get all players and teams
        players = storage.get_players()
        teams = storage.get_teams()
        
        # Build HTML option elements for player dropdowns
        player_options = ""
        for player in players:
            player_options += f'<option value="{player["id"]}">{player["name"]}</option>'
        
        # Build HTML table rows for each team
        teams_list = ""
        for team in teams:
            # Look up player names for this team
            player1 = next((p for p in players if p["id"] == team["player1"]), None)
            player2 = next((p for p in players if p["id"] == team["player2"]), None)
            # Format team name as "Player1 & Player2"
            team_name = f"{player1['name']} & {player2['name']}" if player1 and player2 else "Unknown"
            teams_list += f"""
            <tr>
                <td>{team_name}</td>
                <td>
                    <form method="POST" action="/remove_team" style="display:inline;">
                        <input type="hidden" name="team_id" value="{team['id']}">
                        <button type="submit" class="btn-danger">Remove</button>
                    </form>
                </td>
            </tr>
            """
        
        html = self.get_base_html("Teams", f"""
        <div class="container">
            <h1>Teams</h1>
            
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/players">Players</a>
                <a href="/matches">Matches</a>
            </div>
            
            <div class="card">
                <h2>Form Team</h2>
                <form method="POST" action="/add_team">
                    <div class="form-group">
                        <label for="player1">Player 1:</label>
                        <select id="player1" name="player1" required>
                            <option value="">Select Player</option>
                            {player_options}
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="player2">Player 2:</label>
                        <select id="player2" name="player2" required>
                            <option value="">Select Player</option>
                            {player_options}
                        </select>
                    </div>
                    <button type="submit" class="btn-primary">Create Team</button>
                </form>
            </div>
            
            <div class="card">
                <h2>Registered Teams ({len(teams)})</h2>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Team</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {teams_list if teams_list else '<tr><td colspan="2">No teams formed yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
            
            {f'<div class="card"><form method="POST" action="/generate_schedule"><button type="submit" class="btn-primary btn-large">Generate Tournament Schedule</button></form></div>' if len(teams) >= 2 else ''}
        </div>
        """)
        self.send_html(html)
    
    def serve_matches(self):
        """Serve the matches page.
        
        Displays all matches organized by round. Shows different UI for:
        - Scheduled matches: form to enter scores
        - Completed matches: scores and winner indicator
        - Bye matches: special display for bye rounds
        """
        # Load tournament data
        matches = storage.get_matches()
        teams = storage.get_teams()
        players = storage.get_players()
        tournament_state = storage.get_tournament()
        
        # Group matches by round number for organized display
        rounds = {}
        for match in matches:
            round_num = match["round"]
            if round_num not in rounds:
                rounds[round_num] = []
            rounds[round_num].append(match)
        
        # Build HTML for each round
        rounds_html = ""
        for round_num in sorted(rounds.keys()):
            round_matches = rounds[round_num]
            matches_html = ""
            
            # Build HTML for each match in this round
            for match in round_matches:
                # Get team names (or "Bye" if no opponent)
                team1_name = tournament.get_team_name(match["team1"]) if match["team1"] else "Bye"
                team2_name = tournament.get_team_name(match["team2"]) if match["team2"] else "Bye"
                
                # Display different UI based on match status
                if match["status"] == "bye":
                    # Bye match - special display
                    matches_html += f"""
                    <tr class="bye-match">
                        <td>{team1_name}</td>
                        <td>BYE</td>
                        <td>-</td>
                    </tr>
                    """
                elif match["status"] == "completed":
                    # Completed match - show scores and winner indicator (★)
                    winner_indicator = "★" if match["winner"] == match["team1"] else ""
                    winner_indicator2 = "★" if match["winner"] == match["team2"] else ""
                    matches_html += f"""
                    <tr class="completed-match">
                        <td>{team1_name} {winner_indicator}</td>
                        <td>{team2_name} {winner_indicator2}</td>
                        <td>{match.get('score1', 0)} - {match.get('score2', 0)}</td>
                    </tr>
                    """
                else:
                    # Scheduled match - show form to enter scores
                    matches_html += f"""
                    <tr class="scheduled-match">
                        <td>{team1_name}</td>
                        <td>{team2_name}</td>
                        <td>
                            <form method="POST" action="/update_match" style="display:inline;">
                                <input type="hidden" name="match_id" value="{match['id']}">
                                <input type="number" name="score1" placeholder="Score" min="0" required style="width:60px;">
                                <span> - </span>
                                <input type="number" name="score2" placeholder="Score" min="0" required style="width:60px;">
                                <button type="submit" class="btn-primary">Submit</button>
                            </form>
                        </td>
                    </tr>
                    """
            
            rounds_html += f"""
            <div class="card">
                <h2>Round {round_num}</h2>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Team 1</th>
                            <th>Team 2</th>
                            <th>Score / Result</th>
                        </tr>
                    </thead>
                    <tbody>
                        {matches_html}
                    </tbody>
                </table>
            </div>
            """
        
        html = self.get_base_html("Matches", f"""
        <div class="container">
            <h1>Matches</h1>
            
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/standings">Standings</a>
            </div>
            
            {rounds_html if rounds_html else '<div class="card"><p>No matches scheduled yet. Go to Teams page to generate the schedule.</p></div>'}
        </div>
        """)
        self.send_html(html)
    
    def serve_standings(self):
        """Serve the standings page.
        
        Displays a table of all teams ranked by their tournament performance,
        showing wins, losses, points, and point differentials.
        """
        # Calculate current standings (already sorted by rank)
        standings = tournament.calculate_standings()
        teams = storage.get_teams()
        
        # Build HTML table rows for standings
        standings_html = ""
        rank = 1
        for standing in standings:
            # Get formatted team name
            team_name = tournament.get_team_name(standing["team_id"])
            # Format point differential with + or - sign
            standings_html += f"""
            <tr>
                <td>{rank}</td>
                <td>{team_name}</td>
                <td>{standing['wins']}</td>
                <td>{standing['losses']}</td>
                <td>{standing['points']}</td>
                <td>{standing['points_for']}</td>
                <td>{standing['points_against']}</td>
                <td>{standing['point_differential']:+d}</td>
            </tr>
            """
            rank += 1
        
        html = self.get_base_html("Standings", f"""
        <div class="container">
            <h1>Tournament Standings</h1>
            
            <div class="nav-links">
                <a href="/">Home</a>
                <a href="/matches">Matches</a>
            </div>
            
            <div class="card">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Team</th>
                            <th>Wins</th>
                            <th>Losses</th>
                            <th>Points</th>
                            <th>Points For</th>
                            <th>Points Against</th>
                            <th>Point Differential</th>
                        </tr>
                    </thead>
                    <tbody>
                        {standings_html if standings_html else '<tr><td colspan="8">No matches completed yet.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
        """)
        self.send_html(html)
    
    def render_standings_table(self, standings):
        """Render a compact standings table for a subset of teams.
        
        Used on the index page to show top teams. Displays abbreviated
        statistics (wins, losses, points only).
        
        Args:
            standings: List of standing dictionaries (can be a subset)
        
        Returns:
            HTML string containing the standings table
        """
        if not standings:
            return "<p>No standings yet.</p>"
        
        # Build compact table with abbreviated headers
        html = "<table class='data-table'><thead><tr><th>Team</th><th>W</th><th>L</th><th>Pts</th></tr></thead><tbody>"
        for standing in standings:
            team_name = tournament.get_team_name(standing["team_id"])
            html += f"<tr><td>{team_name}</td><td>{standing['wins']}</td><td>{standing['losses']}</td><td>{standing['points']}</td></tr>"
        html += "</tbody></table>"
        return html
    
    def render_matches_list(self, matches):
        """Render a simple list of matches.
        
        Used on the index page to show upcoming matches in a simple format.
        
        Args:
            matches: List of match dictionaries
        
        Returns:
            HTML string containing the matches list
        """
        if not matches:
            return "<p>No upcoming matches.</p>"
        
        # Build unordered list of matches
        html = "<ul class='matches-list'>"
        for match in matches:
            team1_name = tournament.get_team_name(match["team1"])
            team2_name = tournament.get_team_name(match["team2"])
            html += f"<li>{team1_name} vs {team2_name} (Round {match['round']})</li>"
        html += "</ul>"
        return html
    
    def get_base_html(self, title, content):
        """Generate base HTML template with embedded CSS.
        
        Creates a complete HTML page with:
        - Page title
        - Embedded CSS styles for the entire application
        - The provided content inserted into the body
        
        Args:
            title: Page title to display in browser tab
            content: HTML content to insert into the page body
        
        Returns:
            Complete HTML document as a string
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Pickleball Tournament</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: white;
            margin-bottom: 20px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        
        .status-bar {{
            background: rgba(255, 255, 255, 0.9);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        
        .status-bar span {{
            font-size: 1.1em;
        }}
        
        .nav-links {{
            background: rgba(255, 255, 255, 0.9);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }}
        
        .nav-links a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 4px;
            transition: background 0.3s;
        }}
        
        .nav-links a:hover {{
            background: #f0f0f0;
        }}
        
        .content-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        .form-group {{
            margin-bottom: 15px;
        }}
        
        .form-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #555;
        }}
        
        .form-group input,
        .form-group select {{
            width: 100%;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            transition: border-color 0.3s;
        }}
        
        .form-group input:focus,
        .form-group select:focus {{
            outline: none;
            border-color: #667eea;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .btn-primary:hover {{
            background: #5568d3;
        }}
        
        .btn-large {{
            padding: 15px 30px;
            font-size: 1.1em;
            width: 100%;
        }}
        
        .btn-danger {{
            background: #e74c3c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 0.9em;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .btn-danger:hover {{
            background: #c0392b;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        .data-table th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #555;
            border-bottom: 2px solid #ddd;
        }}
        
        .data-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        .data-table tr:hover {{
            background: #f8f9fa;
        }}
        
        .scheduled-match {{
            background: #fff3cd;
        }}
        
        .completed-match {{
            background: #d4edda;
        }}
        
        .bye-match {{
            background: #e2e3e5;
        }}
        
        .view-all {{
            display: inline-block;
            margin-top: 15px;
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}
        
        .view-all:hover {{
            text-decoration: underline;
        }}
        
        .matches-list {{
            list-style: none;
            padding: 0;
        }}
        
        .matches-list li {{
            padding: 10px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 4px solid #667eea;
        }}
        
        .info {{
            margin-top: 10px;
            color: #666;
            font-size: 0.9em;
            font-style: italic;
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>"""
    
    def send_html(self, html):
        """Send an HTML response to the client.
        
        Args:
            html: HTML content to send as a string
        """
        self.send_response(200)  # HTTP 200 OK
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        # Write HTML content as UTF-8 encoded bytes
        self.wfile.write(html.encode('utf-8'))

def main():
    """Start the HTTP server and begin serving requests.
    
    Handles port selection from command line arguments or uses default.
    Automatically tries next available port if the requested port is in use.
    """
    # Get port from command line argument or use default
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}. Using default port {DEFAULT_PORT}.")
            port = DEFAULT_PORT
    
    # Try to bind to the port, try next ports if unavailable
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            # Create TCP server listening on all interfaces ("") at the specified port
            with socketserver.TCPServer(("", port), TournamentHandler) as httpd:
                print(f"Server running at http://localhost:{port}/")
                print("Press Ctrl+C to stop the server")
                try:
                    # Start serving requests (blocks until interrupted)
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    # User pressed Ctrl+C - stop the server gracefully
                    print("\nServer stopped.")
                return
        except OSError as e:
            # Port is already in use - try next port
            if e.winerror == 10048 or "Address already in use" in str(e):
                if attempt < max_attempts - 1:
                    print(f"Port {port} is already in use. Trying port {port + 1}...")
                    port += 1
                else:
                    # Couldn't find an available port after max attempts
                    print(f"Could not find an available port after {max_attempts} attempts.")
                    print("Please close the application using port 8000 or specify a different port:")
                    print(f"  python server.py <port_number>")
                    sys.exit(1)
            else:
                # Some other error occurred - re-raise it
                raise

if __name__ == "__main__":
    main()

