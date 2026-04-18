"""
Utility functions for the IPL 2026 scraper.
Handles filename sanitization, logging, and common helpers.
"""

import logging
import os
import re
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure and return the project logger with console + file output."""
    logger = logging.getLogger("ipl_scraper")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers on re-import
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-7s │ %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (logs to scraper directory)
    log_dir = os.path.dirname(os.path.abspath(__file__))
    file_handler = logging.FileHandler(
        os.path.join(log_dir, "scraper.log"), mode="w", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def sanitize_filename(name: str) -> str:
    """
    Convert a name into a clean, filesystem-safe filename.
    
    Examples:
        "Virat Kohli"    → "virat-kohli"
        "MS Dhoni (C)"   → "ms-dhoni-c"
        "André Russell"  → "andre-russell"
    """
    # Normalize unicode characters
    import unicodedata
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    
    # Lowercase and replace non-alphanumeric with hyphens
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")  # Remove leading/trailing hyphens
    
    return name


def build_image_filename(team_name: str, player_name: str) -> str:
    """
    Build the image filename in the format: team-name__player-name.jpg
    
    Example: "Chennai Super Kings", "MS Dhoni" → "chennai-super-kings__ms-dhoni.jpg"
    """
    team_part = sanitize_filename(team_name)
    player_part = sanitize_filename(player_name)
    return f"{team_part}__{player_part}.jpg"


def safe_text(element, default: str = "") -> str:
    """Safely extract text from a BeautifulSoup element."""
    if element is None:
        return default
    text = element.get_text(strip=True)
    return text if text else default


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
