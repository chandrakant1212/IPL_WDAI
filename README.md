# IPL 2026 Player Data Scraper + Simple UI + Prompting Task

A complete solution for scraping IPL 2026 player data from [Cricbuzz](https://www.cricbuzz.com/cricket-series/9241/indian-premier-league-2026/squads), presenting it in a clean UI, and classifying players using AI.

---

## 📁 Project Structure

```
├── scraper/                    # Python scraper (Playwright + BeautifulSoup)
│   ├── main.py                 # Entry point — run this to scrape
│   ├── scraper.py              # Core scraping logic
│   ├── config.py               # Configuration & column definitions
│   ├── utils.py                # Helper functions
│   └── requirements.txt        # Python dependencies
├── player_images/              # Downloaded player images (auto-generated)
├── output/
│   └── ipl_2026_players.csv    # Generated CSV (auto-generated)
├── ui/
│   ├── index.html              # Player profile card UI
│   ├── style.css               # Premium dark theme styling
│   └── script.js               # Hardcoded player data + rendering
├── prompt.txt                  # ChatGPT prompt for A/B/C classification
└── README.md                   # This file
```

---

## 🛠️ Tech Stack

| Component        | Technology                      |
|------------------|---------------------------------|
| Scraper          | Python 3.11+ / Playwright       |
| HTML parsing     | BeautifulSoup4 / lxml           |
| Image downloads  | httpx (async)                   |
| CSV export       | Python csv module                |
| Frontend UI      | Plain HTML + CSS + JavaScript   |

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone / navigate to project folder
cd scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (one-time)
playwright install chromium
```

### 2. Run the Scraper

```bash
# Standard headless run (recommended)
python main.py

# Show browser window for debugging
python main.py --visible

# Enable detailed debug logging
python main.py --debug
```

The scraper will:
- Visit all 10 IPL team squad pages
- Scrape ~200+ player profiles (bio + batting/bowling stats)
- Download player images to `/player_images/`
- Export CSV to `/output/ipl_2026_players.csv`

**Estimated runtime:** 15-25 minutes (depends on network speed)

### 3. View the UI

Simply open `ui/index.html` in any browser:

```bash
# Windows
start ui\index.html

# macOS
open ui/index.html

# Or use Live Server in VS Code
```

The UI shows a hardcoded player card with image, bio, and stats.

### 4. Use the ChatGPT Prompt

1. Open [ChatGPT](https://chat.openai.com)
2. Upload the generated `output/ipl_2026_players.csv`
3. Paste the contents of `prompt.txt`
4. ChatGPT will classify players into A/B/C categories and return the updated CSV

---

## 📊 CSV Columns

### Basic Info
`name`, `role`, `Batting Style`, `Bowling Style`, `team`

### Batting Stats (IPL career)
`bat_matches`, `bat_innings`, `bat_runs`, `bat_balls`, `bat_highest`, `bat_average`, `bat_sr`, `bat_not_out`, `bat_fours`, `bat_sixes`, `bat_ducks`, `bat_50s`, `bat_100s`, `bat_200s`, `bat_300s`, `bat_400s`

### Bowling Stats (IPL career)
`bowl_matches`, `bowl_innings`, `bowl_balls`, `bowl_runs`, `bowl_maidens`, `bowl_wickets`, `bowl_avg`, `bowl_eco`, `bowl_sr`, `bowl_bbi`, `bowl_bbm`, `bowl_4w`, `bowl_5w`, `bowl_10w`

### Image
`player_image_filename`

---

## 🖼️ Image Naming Convention

Images are saved as:
```
team-name__player-name.jpg
```

Example: `chennai-super-kings__ms-dhoni.jpg`

---

## ⚠️ Notes

- The scraper uses Playwright (headless Chromium) because Cricbuzz content is JavaScript-rendered
- Random delays (1-2.5s) between requests to avoid rate limiting
- Missing data fields are left blank (never fails the run)
- Retry logic with exponential backoff for network errors
- Logs are saved to `scraper/scraper.log`

---

## 🏗️ Built With

- **Python 3.11** — Core language
- **Playwright** — Browser automation for JS-rendered pages
- **BeautifulSoup4** — HTML parsing
- **httpx** — Async HTTP client for image downloads
- **HTML/CSS/JS** — Lightweight frontend UI
