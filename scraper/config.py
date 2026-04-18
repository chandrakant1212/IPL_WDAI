"""
Configuration for IPL 2026 Player Data Scraper.
Contains all constants, column definitions, and scraping settings.
"""

# ──────────────────────────── Base URLs ────────────────────────────
BASE_URL = "https://www.cricbuzz.com"
SQUADS_URL = f"{BASE_URL}/cricket-series/9241/indian-premier-league-2026/squads"

# ──────────────────────────── Output Paths ─────────────────────────
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "player_images")

CSV_FILENAME = "ipl_2026_players.csv"
CSV_PATH = os.path.join(OUTPUT_DIR, CSV_FILENAME)

# ──────────────────────────── CSV Column Definitions ───────────────
# Exact column names as specified in the assignment
CSV_COLUMNS = [
    # Basic info
    "name",
    "role",
    "Batting Style",
    "Bowling Style",
    "team",
    
    # Batting stats
    "bat_matches",
    "bat_innings",
    "bat_runs",
    "bat_balls",
    "bat_highest",
    "bat_average",
    "bat_sr",
    "bat_not_out",
    "bat_fours",
    "bat_sixes",
    "bat_ducks",
    "bat_50s",
    "bat_100s",
    "bat_200s",
    "bat_300s",
    "bat_400s",
    
    # Bowling stats
    "bowl_matches",
    "bowl_innings",
    "bowl_balls",
    "bowl_runs",
    "bowl_maidens",
    "bowl_wickets",
    "bowl_avg",
    "bowl_eco",
    "bowl_sr",
    "bowl_bbi",
    "bowl_bbm",
    "bowl_4w",
    "bowl_5w",
    "bowl_10w",
    
    # Image filename
    "player_image_filename",
]

# Mapping of Cricbuzz batting table headers → our CSV column names
# Cricbuzz batting headers: ["", "M", "Inn", "NO", "Runs", "HS", "Avg", "BF", "SR", "100s", "200s", "50s", "4s", "6s", "0s"]
# (Index 0 is the format name like "IPL")
BATTING_HEADER_MAP = {
    "M": "bat_matches",
    "Inn": "bat_innings",
    "NO": "bat_not_out",
    "Runs": "bat_runs",
    "HS": "bat_highest",
    "Avg": "bat_average",
    "BF": "bat_balls",
    "SR": "bat_sr",
    "100s": "bat_100s",
    "200s": "bat_200s",
    "50s": "bat_50s",
    "4s": "bat_fours",
    "6s": "bat_sixes",
    "0s": "bat_ducks",
}

# Additional batting columns that may not appear in table but are in assignment
EXTRA_BATTING_COLS = {
    "bat_300s": "",  # Rarely seen on Cricbuzz — leave blank
    "bat_400s": "",  # Rarely seen on Cricbuzz — leave blank
}

# Mapping of Cricbuzz bowling table headers → our CSV column names
# Cricbuzz bowling headers: ["", "M", "Inn", "B", "Runs", "Wkts", "BBI", "BBM", "Econ", "Avg", "SR", "5W", "10W"]
BOWLING_HEADER_MAP = {
    "M": "bowl_matches",
    "Inn": "bowl_innings",
    "B": "bowl_balls",
    "Runs": "bowl_runs",
    "Wkts": "bowl_wickets",
    "BBI": "bowl_bbi",
    "BBM": "bowl_bbm",
    "Econ": "bowl_eco",
    "Avg": "bowl_avg",
    "SR": "bowl_sr",
    "5W": "bowl_5w",
    "10W": "bowl_10w",
}

# Extra bowling columns not in Cricbuzz table
EXTRA_BOWLING_COLS = {
    "bowl_maidens": "",  # Not shown in summary table
    "bowl_4w": "",       # Not shown in summary table
}

# ──────────────────────────── Scraping Settings ────────────────────
REQUEST_DELAY_MIN = 1.0        # Minimum delay between requests (seconds)
REQUEST_DELAY_MAX = 2.5        # Maximum delay between requests (seconds)
PAGE_LOAD_TIMEOUT = 30000      # Page load timeout (ms)
NAVIGATION_TIMEOUT = 30000     # Navigation timeout (ms)
MAX_RETRIES = 3                # Max retries for failed requests
RETRY_BACKOFF = 2.0            # Exponential backoff multiplier

# ──────────────────────────── Team Names ───────────────────────────
# Official team names for the 10 IPL 2026 teams
TEAM_NAMES = [
    "Chennai Super Kings",
    "Delhi Capitals",
    "Gujarat Titans",
    "Royal Challengers Bengaluru",
    "Punjab Kings",
    "Kolkata Knight Riders",
    "Sunrisers Hyderabad",
    "Rajasthan Royals",
    "Lucknow Super Giants",
    "Mumbai Indians",
]
