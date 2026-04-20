"""
Configuration for IPL 2026 Player Data Scraper.
"""

BASE_URL = "https://www.cricbuzz.com"
SQUADS_URL = f"{BASE_URL}/cricket-series/9241/indian-premier-league-2026/squads"

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "player_images")

CSV_FILENAME = "ipl_2026_players.csv"
CSV_PATH = os.path.join(OUTPUT_DIR, CSV_FILENAME)

CSV_COLUMNS = [
    "name", "role", "Batting Style", "Bowling Style", "team",
    "bat_matches", "bat_innings", "bat_runs", "bat_balls", "bat_highest",
    "bat_average", "bat_sr", "bat_not_out", "bat_fours", "bat_sixes",
    "bat_ducks", "bat_50s", "bat_100s", "bat_200s", "bat_300s", "bat_400s",
    "bowl_matches", "bowl_innings", "bowl_balls", "bowl_runs", "bowl_maidens",
    "bowl_wickets", "bowl_avg", "bowl_eco", "bowl_sr", "bowl_bbi", "bowl_bbm",
    "bowl_4w", "bowl_5w", "bowl_10w",
    "player_image_filename",
]

# ──────────────────────────────────────────────────────────────────
# Cricbuzz table layout (TRANSPOSED):
#
#   Headers:  ["", "Test", "ODI", "T20", "IPL"]
#   Rows:     ["Matches", "113",  "275", "115", "252"]
#             ["Innings", "210",  "299", "117", "245"]
#             ["Runs",    "8848", ...                 ]
#
# The ROW LABEL (first cell) is the stat name.
# The IPL VALUE is in the column whose header = "IPL".
# ──────────────────────────────────────────────────────────────────

# Row label → CSV column for BATTING table
BATTING_ROW_MAP = {
    "Matches":  "bat_matches",
    "Mat":      "bat_matches",
    "M":        "bat_matches",
    "Innings":  "bat_innings",
    "Inn":      "bat_innings",
    "Runs":     "bat_runs",
    "Balls":    "bat_balls",
    "BF":       "bat_balls",
    "Highest":  "bat_highest",
    "HS":       "bat_highest",
    "Average":  "bat_average",
    "Avg":      "bat_average",
    "SR":       "bat_sr",
    "Not Out":  "bat_not_out",
    "NO":       "bat_not_out",
    "Fours":    "bat_fours",
    "4s":       "bat_fours",
    "Sixes":    "bat_sixes",
    "6s":       "bat_sixes",
    "Ducks":    "bat_ducks",
    "0s":       "bat_ducks",
    "50s":      "bat_50s",
    "100s":     "bat_100s",
    "200s":     "bat_200s",
    "300s":     "bat_300s",
    "400s":     "bat_400s",
}

# Row label → CSV column for BOWLING table
BOWLING_ROW_MAP = {
    "Matches":  "bowl_matches",
    "Mat":      "bowl_matches",
    "M":        "bowl_matches",
    "Innings":  "bowl_innings",
    "Inn":      "bowl_innings",
    "Balls":    "bowl_balls",
    "B":        "bowl_balls",
    "Runs":     "bowl_runs",
    "Maidens":  "bowl_maidens",
    "Wickets":  "bowl_wickets",
    "Wkts":     "bowl_wickets",
    "Avg":      "bowl_avg",
    "Average":  "bowl_avg",
    "Econ":     "bowl_eco",
    "Economy":  "bowl_eco",
    "SR":       "bowl_sr",
    "BBI":      "bowl_bbi",
    "BBM":      "bowl_bbm",
    "4w":       "bowl_4w",
    "5w":       "bowl_5w",
    "5W":       "bowl_5w",
    "10w":      "bowl_10w",
    "10W":      "bowl_10w",
}

# Row labels unique to batting (used to tell batting vs bowling tables apart)
BATTING_ONLY_LABELS = {"Highest", "HS", "Fours", "4s", "Sixes", "6s", "Ducks", "0s", "50s", "100s", "200s"}
# Row labels unique to bowling
BOWLING_ONLY_LABELS = {"Wickets", "Wkts", "BBI", "BBM", "Econ", "Economy", "Maidens", "4w", "5w", "5W", "10w", "10W"}

# LEGACY mapping (old-style tables where stats are columns, kept as fallback)
BATTING_HEADER_MAP = {
    "M": "bat_matches", "Inn": "bat_innings", "NO": "bat_not_out",
    "Runs": "bat_runs", "HS": "bat_highest", "Avg": "bat_average",
    "BF": "bat_balls", "SR": "bat_sr", "100s": "bat_100s",
    "200s": "bat_200s", "50s": "bat_50s", "4s": "bat_fours",
    "6s": "bat_sixes", "0s": "bat_ducks",
}

BOWLING_HEADER_MAP = {
    "M": "bowl_matches", "Inn": "bowl_innings", "B": "bowl_balls",
    "Runs": "bowl_runs", "Wkts": "bowl_wickets", "BBI": "bowl_bbi",
    "BBM": "bowl_bbm", "Econ": "bowl_eco", "Avg": "bowl_avg",
    "SR": "bowl_sr", "5W": "bowl_5w", "10W": "bowl_10w",
}

REQUEST_DELAY_MIN = 1.0
REQUEST_DELAY_MAX = 2.5
PAGE_LOAD_TIMEOUT = 30000
NAVIGATION_TIMEOUT = 30000
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

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
