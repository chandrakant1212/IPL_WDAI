"""
IPL 2026 Player Data Scraper — Main Entry Point.

Usage:
    python main.py                  # Run with default settings (headless)
    python main.py --visible        # Show browser window for debugging
    python main.py --debug          # Enable debug logging

Output:
    ../output/ipl_2026_players.csv  — Player data CSV
    ../player_images/               — Downloaded player images
"""

import argparse
import asyncio
import sys
import os

# Ensure scraper package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import IPLScraper
from utils import setup_logging


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="IPL 2026 Player Data Scraper — Cricbuzz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Show the browser window (non-headless mode)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser.parse_args()


async def main() -> None:
    """Run the scraping pipeline."""
    args = parse_args()
    
    # Configure logging
    level = "DEBUG" if args.debug else "INFO"
    logger = setup_logging(level)
    
    logger.info("=" * 60)
    logger.info("  IPL 2026 Player Data Scraper")
    logger.info("  Source: Cricbuzz.com")
    logger.info("=" * 60)

    scraper = IPLScraper(headless=not args.visible)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
