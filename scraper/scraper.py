"""
Core scraping logic for IPL 2026 Player Data.

Uses Playwright for browser automation (Cricbuzz is a JS-rendered SPA)
and BeautifulSoup for HTML parsing.

Key architectural decisions based on Cricbuzz page analysis:
  - The squads page is SPA-style: clicking teams updates content without URL change.
    We must click team names in the sidebar and wait for the player list to render.
  - Player profile links contain role text (e.g., "Ruturaj Gaikwad (Captain) Batsman").
    We clean this in post-processing.
  - Stats tables: Batting is at table index 2, Bowling at table index 3. The "IPL" row
    contains franchise career stats.
  - Player images require broader selectors since they're not always in a standard wrapper.

Flow:
  1. Open squads page → click each team in sidebar → extract player URLs
  2. For each player → navigate to profile page → scrape bio + stats
  3. Download all player images in parallel
  4. Export everything to CSV
"""

import asyncio
import csv
import os
import random
import re
import time
import traceback
from typing import Any

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from config import (
    BASE_URL,
    SQUADS_URL,
    OUTPUT_DIR,
    IMAGES_DIR,
    CSV_PATH,
    CSV_COLUMNS,
    BATTING_ROW_MAP,
    BOWLING_ROW_MAP,
    BATTING_ONLY_LABELS,
    BOWLING_ONLY_LABELS,
    BATTING_HEADER_MAP,
    BOWLING_HEADER_MAP,
    TEAM_NAMES,
    REQUEST_DELAY_MIN,
    REQUEST_DELAY_MAX,
    PAGE_LOAD_TIMEOUT,
    NAVIGATION_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF,
)
from utils import (
    setup_logging,
    sanitize_filename,
    build_image_filename,
    safe_text,
    ensure_dir,
)

logger = setup_logging()


class IPLScraper:
    """
    Scrapes IPL 2026 player data from Cricbuzz.
    
    Usage:
        scraper = IPLScraper()
        await scraper.run()
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.context: BrowserContext | None = None
        self.players: list[dict[str, Any]] = []

    # ─────────────────── Browser Lifecycle ──────────────────────────

    async def start_browser(self) -> None:
        """Launch Playwright Chromium browser."""
        logger.info("Launching browser (headless=%s)...", self.headless)
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        self.page = await self.context.new_page()
        self.page.set_default_timeout(PAGE_LOAD_TIMEOUT)
        self.page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
        logger.info("Browser ready.")

    async def stop_browser(self) -> None:
        """Close the browser cleanly."""
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()
        logger.info("Browser closed.")

    # ─────────────────── Helper Methods ────────────────────────────

    async def _random_delay(self, min_sec: float = None, max_sec: float = None) -> None:
        """Human-like random delay between requests."""
        low = min_sec or REQUEST_DELAY_MIN
        high = max_sec or REQUEST_DELAY_MAX
        delay = random.uniform(low, high)
        await asyncio.sleep(delay)

    async def _navigate(self, url: str, retries: int = MAX_RETRIES) -> str:
        """Navigate to URL with retry logic. Returns page HTML."""
        for attempt in range(1, retries + 1):
            try:
                await self.page.goto(url, wait_until="domcontentloaded")
                # Wait extra for JS-rendered content to appear
                await self.page.wait_for_timeout(4000)
                return await self.page.content()
            except Exception as e:
                logger.warning(
                    "Navigation failed (attempt %d/%d): %s — %s",
                    attempt, retries, url, str(e)
                )
                if attempt < retries:
                    backoff = RETRY_BACKOFF ** attempt
                    await asyncio.sleep(backoff)
                else:
                    logger.error("Giving up on URL: %s", url)
                    raise

    @staticmethod
    def _clean_player_name(raw_name: str) -> str:
        """
        Clean player name from Cricbuzz format.
        
        The squad page returns names like:
            "Ruturaj Gaikwad (Captain) Batsman"
            "MS Dhoni  WK-Batsman"
            "Shivam Dube  Batting Allrounder"
        
        We strip the role/category suffix and captain markers.
        """
        # Remove common role suffixes
        role_patterns = [
            r"\s+(Batsman|Bowler|Batting Allrounder|Bowling Allrounder|WK-Batsman|Allrounder)\s*$",
            r"\s*\(Captain\)\s*",
            r"\s*\(c\)\s*",
            r"\s*\(wk\)\s*",
        ]
        name = raw_name.strip()
        for pattern in role_patterns:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE).strip()
        
        # Remove extra whitespace
        name = re.sub(r"\s+", " ", name).strip()
        return name

    @staticmethod
    def _extract_role_from_raw(raw_name: str) -> str:
        """Extract role from the raw player name text on squad page."""
        # Match known roles at the end
        role_match = re.search(
            r"(Batsman|Bowler|Batting Allrounder|Bowling Allrounder|WK-Batsman|Allrounder)\s*$",
            raw_name.strip(),
            re.IGNORECASE,
        )
        return role_match.group(1) if role_match else ""

    # ───────────── Step 1 & 2: Get All Players from All Teams ──────

    async def get_all_team_players(self) -> list[dict[str, str]]:
        """
        Navigate to squads page and iterate through all 10 teams.

        Cricbuzz uses React/Next.js — vanilla JS el.click() does NOT fire
        React synthetic event handlers. We MUST use Playwright's native
        page.click() which dispatches real mouse events.
        """
        logger.info("=" * 60)
        logger.info("Step 1: Navigating to squads page")
        logger.info("=" * 60)

        await self._navigate(SQUADS_URL)
        await self.page.wait_for_timeout(3000)

        all_players = []

        for team_idx, team_name in enumerate(TEAM_NAMES):
            logger.info(
                "\n[%d/%d] Processing team: %s",
                team_idx + 1, len(TEAM_NAMES), team_name
            )

            try:
                clicked = await self._click_team(team_name)
                if not clicked:
                    logger.warning("  ⚠ Could not click team, trying next...")
                    continue

                await self.page.wait_for_timeout(3000)

                players = await self._extract_players_from_dom(team_name)
                all_players.extend(players)

                logger.info(
                    "  ✓ Found %d players for %s", len(players), team_name
                )

            except Exception as e:
                logger.error(
                    "  ✗ Failed to process team %s: %s", team_name, str(e)
                )
                logger.debug(traceback.format_exc())
                continue

        logger.info(
            "\nTotal players found across all teams: %d", len(all_players)
        )
        return all_players

    async def _click_team(self, team_name: str) -> bool:
        """
        Click a team name using Playwright's NATIVE click (not JS eval).

        Cricbuzz is built with React — el.click() in JS does not trigger
        React's synthetic event system. Playwright's page.click() dispatches
        real trusted mouse events that React properly captures.
        """
        # Strategy 1: Playwright get_by_text (most reliable)
        try:
            locator = self.page.get_by_text(team_name, exact=True)
            count = await locator.count()
            if count > 0:
                await locator.first.click()
                logger.info("  Clicked team via: get_by_text")
                return True
        except Exception as e:
            logger.debug("  get_by_text failed: %s", str(e))

        # Strategy 2: Playwright locator with span text selector
        try:
            locator = self.page.locator(f"span:text-is('{team_name}')")
            count = await locator.count()
            if count > 0:
                await locator.first.click()
                logger.info("  Clicked team via: span-locator")
                return True
        except Exception as e:
            logger.debug("  span-locator failed: %s", str(e))

        # Strategy 3: XPath-based locator
        try:
            locator = self.page.locator(f"//span[normalize-space()='{team_name}']")
            count = await locator.count()
            if count > 0:
                await locator.first.click()
                logger.info("  Clicked team via: xpath")
                return True
        except Exception as e:
            logger.debug("  xpath failed: %s", str(e))

        # Strategy 4: CSS + text filter
        try:
            locator = self.page.locator("div").filter(has_text=re.compile(f"^{re.escape(team_name)}$"))
            count = await locator.count()
            if count > 0:
                await locator.first.click()
                logger.info("  Clicked team via: div-filter")
                return True
        except Exception as e:
            logger.debug("  div-filter failed: %s", str(e))

        logger.warning("Could not click team: %s", team_name)
        return False

    async def _extract_players_from_dom(self, team_name: str) -> list[dict[str, str]]:
        """
        Extract player profile links from the current DOM state.
        
        After clicking a team in the sidebar, the right-side content area
        shows player cards. Each player has an anchor tag with href="/profiles/..."
        and possibly an associated image.
        
        Returns list of: [{"name": "...", "url": "...", "role_hint": "...", "img_url": "..."}]
        """
        result = await self.page.evaluate("""
            () => {
                const links = document.querySelectorAll('a[href*="/profiles/"]');
                const seen = new Set();
                const players = [];
                
                for (const link of links) {
                    const href = link.getAttribute('href') || '';
                    
                    // Skip duplicate hrefs
                    if (seen.has(href)) continue;
                    seen.add(href);
                    
                    // Get the visible text — could be just the name or name + role
                    let text = link.textContent.trim();
                    
                    // Skip empty or very short text
                    if (!text || text.length < 2) continue;
                    // Skip very long text (probably a container with lots of content)
                    if (text.length > 120) continue;
                    
                    // Try to find an image associated with this player
                    let imgUrl = '';
                    
                    // Check inside the link itself
                    const img = link.querySelector('img');
                    if (img) {
                        imgUrl = img.src || img.getAttribute('data-src') || '';
                    }
                    
                    // Check sibling or parent elements for images
                    if (!imgUrl) {
                        const parent = link.parentElement;
                        if (parent) {
                            const parentImg = parent.querySelector('img');
                            if (parentImg) {
                                imgUrl = parentImg.src || parentImg.getAttribute('data-src') || '';
                            }
                        }
                    }
                    
                    // Check grandparent for image
                    if (!imgUrl) {
                        const grandparent = link.parentElement?.parentElement;
                        if (grandparent) {
                            const gpImg = grandparent.querySelector('img');
                            if (gpImg) {
                                imgUrl = gpImg.src || gpImg.getAttribute('data-src') || '';
                            }
                        }
                    }
                    
                    players.push({
                        name: text,
                        url: href,
                        img_url: imgUrl
                    });
                }
                
                return players;
            }
        """)

        # Post-process: clean names, add team, build full URLs
        processed = []
        for p in (result or []):
            raw_name = p["name"]
            clean_name = self._clean_player_name(raw_name)
            role_hint = self._extract_role_from_raw(raw_name)

            # Skip if cleaned name is too short (was just role text)
            if len(clean_name) < 2:
                continue

            url = p["url"]
            if url.startswith("/"):
                url = BASE_URL + url

            # Avoid duplicates
            if any(existing["url"] == url for existing in processed):
                continue

            processed.append({
                "name": clean_name,
                "url": url,
                "team": team_name,
                "role_hint": role_hint,
                "img_url": p.get("img_url", ""),
            })

        return processed

    # ─────────────────── Step 3: Scrape Player Profile ─────────────

    async def scrape_player_profile(self, player_info: dict) -> dict[str, str]:
        """
        Navigate to a player's profile page and extract:
        - Personal info (role, batting/bowling style)
        - IPL batting stats (from table at index ~2)
        - IPL bowling stats (from table at index ~3)
        - Player image URL
        """
        name = player_info["name"]
        team = player_info["team"]
        url = player_info["url"]

        logger.info("    → Scraping: %s (%s)", name, team)
        await self._random_delay()

        # Initialize with all columns blank
        data = {col: "" for col in CSV_COLUMNS}
        data["name"] = name
        data["team"] = team

        try:
            html = await self._navigate(url)
            soup = BeautifulSoup(html, "lxml")

            # ── Extract personal info via JavaScript (more reliable) ──
            info = await self._extract_personal_info_js()
            data["role"] = info.get("Role", player_info.get("role_hint", ""))
            data["Batting Style"] = info.get("Batting Style", "")
            data["Bowling Style"] = info.get("Bowling Style", "")

            # ── Extract stats via JavaScript (handles SPA tables better) ──
            tables_data = await self._extract_tables_js()
            self._parse_batting_stats(tables_data, data)
            self._parse_bowling_stats(tables_data, data)

            # ── Extract image URL ──
            img_url = await self._extract_image_js()
            if not img_url:
                img_url = player_info.get("img_url", "")
            data["_img_url"] = img_url  # Internal; not in final CSV

            # ── Build image filename ──
            data["player_image_filename"] = build_image_filename(team, name)

            # Ensure all CSV columns exist (blank if not found)
            for col in CSV_COLUMNS:
                if col not in data:
                    data[col] = ""

        except Exception as e:
            logger.error("    ✗ Failed to scrape %s: %s", name, str(e))
            logger.debug(traceback.format_exc())
            data["player_image_filename"] = build_image_filename(team, name)
            data["_img_url"] = player_info.get("img_url", "")

        return data

    async def _extract_personal_info_js(self) -> dict:
        """
        Extract player personal info using JavaScript.
        Looks for label/value pairs (Role, Batting Style, Bowling Style).
        """
        result = await self.page.evaluate("""
            () => {
                const info = {};
                const allDivs = document.querySelectorAll('div');
                
                for (let i = 0; i < allDivs.length; i++) {
                    const text = allDivs[i].textContent.trim();
                    
                    if (text === 'Role' || text === 'Batting Style' || text === 'Bowling Style') {
                        const next = allDivs[i].nextElementSibling;
                        if (next) {
                            const value = next.textContent.trim();
                            // Ensure we're not picking up a large container's text
                            if (value.length < 60) {
                                info[text] = value;
                            }
                        }
                    }
                }
                
                // Also try to get player name from the page
                const h1 = document.querySelector('h1');
                if (h1) info['playerName'] = h1.textContent.trim();
                
                // Try other name selectors
                const nameEl = document.querySelector('.cb-font-40') 
                             || document.querySelector('.player-name')
                             || document.querySelector('[itemprop="name"]');
                if (nameEl) info['playerNameAlt'] = nameEl.textContent.trim();
                
                return info;
            }
        """)
        return result or {}

    async def _extract_tables_js(self) -> list:
        """
        Extract all table data from the page using JavaScript.
        Returns a list of tables, each with headers and rows.
        """
        result = await self.page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table');
                const result = [];
                
                for (let t = 0; t < tables.length; t++) {
                    const headers = [];
                    const ths = tables[t].querySelectorAll('thead th');
                    for (const th of ths) {
                        headers.push(th.textContent.trim());
                    }
                    
                    const rows = [];
                    const trs = tables[t].querySelectorAll('tbody tr');
                    for (const tr of trs) {
                        const cells = [];
                        const tds = tr.querySelectorAll('td');
                        for (const td of tds) {
                            cells.push(td.textContent.trim());
                        }
                        rows.push(cells);
                    }
                    
                    result.push({
                        index: t,
                        headers: headers,
                        rows: rows
                    });
                }
                
                return result;
            }
        """)
        return result or []

    async def _extract_image_js(self) -> str:
        """
        Extract the player image URL using JavaScript.
        Tries multiple strategies since Cricbuzz image placement varies.
        """
        result = await self.page.evaluate("""
            () => {
                // Strategy 1: Look for player-specific image containers
                const selectors = [
                    '.cb-plyr-img-wrp img',
                    '.cb-plyr-photo img',
                    'img.cb-plyr-img',
                    '.cb-col-100.cb-bg-white img[src*="i1"]',
                ];
                
                for (const sel of selectors) {
                    const img = document.querySelector(sel);
                    if (img && img.src) return img.src;
                }
                
                // Strategy 2: Find any cricket-related image that looks like a headshot
                const allImgs = document.querySelectorAll('img');
                for (const img of allImgs) {
                    const src = img.src || '';
                    if ((src.includes('static.cricbuzz.com') || src.includes('i.cricketcb.com')) &&
                        (src.includes('/i1/') || src.includes('/i2/') || src.includes('player'))) {
                        // Check it's reasonably sized (not a tiny icon)
                        if (img.naturalWidth > 50 || img.width > 50 || 
                            src.includes('152x152') || src.includes('225x225')) {
                            return src;
                        }
                    }
                }
                
                // Strategy 3: Pattern-based search in all img src attributes
                for (const img of allImgs) {
                    const src = img.src || '';
                    if (src.includes('cricbuzz.com/a/img/v1/i1/c')) {
                        return src;
                    }
                }
                
                return '';
            }
        """)
        return result or ""

    def _parse_batting_stats(self, tables_data: list, data: dict) -> None:
        """
        Parse IPL batting stats from extracted table data.

        Cricbuzz uses a TRANSPOSED layout:
            Headers:  ["", "Test", "ODI", "T20", "IPL"]
            Row 0:    ["Matches", "113", "275", "115", "252"]
            Row 1:    ["Innings", "210", "299", "117", "245"]
            ...

        We need to find the IPL COLUMN index, then read each row's
        first cell (stat label) and its IPL column value.
        """
        for table in tables_data:
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            if not rows:
                continue

            # --- TRANSPOSED LAYOUT (IPL is a column header) ---
            ipl_col = self._find_ipl_column(headers)
            if ipl_col is not None:
                row_labels = {row[0].strip() for row in rows if row}
                is_batting = bool(row_labels & BATTING_ONLY_LABELS)
                is_bowling = bool(row_labels & BOWLING_ONLY_LABELS)

                if is_batting and not is_bowling:
                    for row in rows:
                        if not row or len(row) <= ipl_col:
                            continue
                        label = row[0].strip()
                        value = row[ipl_col].strip()
                        csv_col = BATTING_ROW_MAP.get(label)
                        if csv_col:
                            data[csv_col] = value if value and value != "-" else ""
                    logger.info("      ✓ IPL batting stats extracted (transposed)")
                    return

            # --- LEGACY LAYOUT (IPL is a row, stats are columns) ---
            if not headers:
                continue
            has_batting = ("Runs" in headers and ("HS" in headers or "Avg" in headers))
            has_bowling = ("Wkts" in headers or "Wickets" in headers)
            if has_batting and not has_bowling:
                for row in rows:
                    if not row:
                        continue
                    if row[0].strip().upper() in ("IPL", "INDIAN PREMIER LEAGUE"):
                        for idx, header in enumerate(headers):
                            if idx < len(row) and header in BATTING_HEADER_MAP:
                                value = row[idx].strip()
                                data[BATTING_HEADER_MAP[header]] = value if value and value != "-" else ""
                        logger.info("      ✓ IPL batting stats extracted (legacy)")
                        return

        logger.debug("      ○ No IPL batting stats found")

    def _parse_bowling_stats(self, tables_data: list, data: dict) -> None:
        """
        Parse IPL bowling stats — same transposed approach as batting.
        """
        for table in tables_data:
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            if not rows:
                continue

            # --- TRANSPOSED LAYOUT ---
            ipl_col = self._find_ipl_column(headers)
            if ipl_col is not None:
                row_labels = {row[0].strip() for row in rows if row}
                is_bowling = bool(row_labels & BOWLING_ONLY_LABELS)
                is_batting = bool(row_labels & BATTING_ONLY_LABELS)

                if is_bowling and not is_batting:
                    for row in rows:
                        if not row or len(row) <= ipl_col:
                            continue
                        label = row[0].strip()
                        value = row[ipl_col].strip()
                        csv_col = BOWLING_ROW_MAP.get(label)
                        if csv_col:
                            data[csv_col] = value if value and value != "-" else ""
                    logger.info("      ✓ IPL bowling stats extracted (transposed)")
                    return

            # --- LEGACY LAYOUT ---
            if not headers:
                continue
            if "Wkts" in headers or "Wickets" in headers:
                for row in rows:
                    if not row:
                        continue
                    if row[0].strip().upper() in ("IPL", "INDIAN PREMIER LEAGUE"):
                        for idx, header in enumerate(headers):
                            if idx < len(row) and header in BOWLING_HEADER_MAP:
                                value = row[idx].strip()
                                data[BOWLING_HEADER_MAP[header]] = value if value and value != "-" else ""
                        logger.info("      ✓ IPL bowling stats extracted (legacy)")
                        return

        logger.debug("      ○ No IPL bowling stats found")

    @staticmethod
    def _find_ipl_column(headers: list) -> int | None:
        """Find the index of the 'IPL' column in a table header row."""
        for idx, h in enumerate(headers):
            if h.strip().upper() == "IPL":
                return idx
        return None

    # ─────────────────── Step 4: Download Images ───────────────────

    async def download_images(self) -> None:
        """Download all player images in parallel using httpx."""
        ensure_dir(IMAGES_DIR)

        # Build download task list
        downloads = []
        for player in self.players:
            img_url = player.get("_img_url", "")
            filename = player.get("player_image_filename", "")

            if not filename:
                continue

            # Try to build a larger image URL if we have a thumbnail
            if img_url:
                # Cricbuzz pattern: replace size params for higher resolution
                img_url = re.sub(r"\?.*$", "", img_url)  # Remove query params
                img_url = img_url.replace("/152x152/", "/225x225/")

                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif not img_url.startswith("http"):
                    img_url = "https://www.cricbuzz.com" + img_url

            filepath = os.path.join(IMAGES_DIR, filename)
            downloads.append((img_url, filepath, player["name"]))

        # Filter out empty URLs
        downloads = [(url, path, name) for url, path, name in downloads if url]

        if not downloads:
            logger.warning("No images to download.")
            return

        logger.info("\n" + "=" * 60)
        logger.info("Step 4: Downloading %d player images...", len(downloads))
        logger.info("=" * 60)

        # Use httpx with semaphore for controlled concurrent downloads
        semaphore = asyncio.Semaphore(5)
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                "Referer": "https://www.cricbuzz.com/",
            },
        ) as client:
            tasks = [
                self._download_single(client, semaphore, url, path, name)
                for url, path, name in downloads
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        success = sum(1 for r in results if r is True)
        failed = len(downloads) - success
        logger.info("Images: %d downloaded, %d failed", success, failed)

    async def _download_single(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        url: str,
        filepath: str,
        name: str,
    ) -> bool:
        """Download a single image file with retry logic."""
        async with semaphore:
            for attempt in range(MAX_RETRIES):
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200 and len(resp.content) > 100:
                        with open(filepath, "wb") as f:
                            f.write(resp.content)
                        return True
                    else:
                        logger.warning(
                            "  Image HTTP %d for %s (%d bytes)",
                            resp.status_code, name, len(resp.content)
                        )
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(1)
                    else:
                        logger.warning("  Image download failed for %s: %s", name, str(e))

            return False

    # ─────────────────── Step 5: Export CSV ─────────────────────────

    def export_csv(self) -> None:
        """Write all player data to CSV with exact column names from assignment."""
        ensure_dir(OUTPUT_DIR)

        # Remove internal fields (prefixed with _)
        clean_players = []
        for p in self.players:
            clean = {col: p.get(col, "") for col in CSV_COLUMNS}
            clean_players.append(clean)

        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(clean_players)

        logger.info("\n✓ CSV exported: %s (%d players)", CSV_PATH, len(clean_players))

    # ─────────────────── Main Pipeline ─────────────────────────────

    async def run(self) -> None:
        """Execute the full scraping pipeline."""
        start_time = time.time()

        try:
            await self.start_browser()

            # Steps 1 & 2: Get all players from all teams
            all_player_infos = await self.get_all_team_players()

            if not all_player_infos:
                logger.error("No players found! Aborting.")
                return

            # Step 3: Scrape each player's profile
            logger.info("\n" + "=" * 60)
            logger.info("Step 3: Scraping %d player profiles...", len(all_player_infos))
            logger.info("=" * 60)

            for idx, player_info in enumerate(all_player_infos):
                logger.info(
                    "\n  [%d/%d] %s (%s)",
                    idx + 1, len(all_player_infos),
                    player_info["name"], player_info["team"]
                )

                player_data = await self.scrape_player_profile(player_info)
                self.players.append(player_data)

                # Progress checkpoint every 25 players
                if (idx + 1) % 25 == 0:
                    logger.info(
                        "\n  ── Progress: %d/%d players scraped ──",
                        idx + 1, len(all_player_infos)
                    )

            logger.info(
                "\n✓ Profile scraping complete: %d players", len(self.players)
            )

            # Step 4: Download images
            await self.download_images()

            # Step 5: Export CSV
            self.export_csv()

        finally:
            await self.stop_browser()

        elapsed = time.time() - start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        logger.info("\n" + "═" * 60)
        logger.info("  SCRAPING COMPLETE")
        logger.info("  Players: %d", len(self.players))
        logger.info("  Time: %dm %ds", minutes, seconds)
        logger.info("  CSV: %s", CSV_PATH)
        logger.info("  Images: %s", IMAGES_DIR)
        logger.info("═" * 60)
