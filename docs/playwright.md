# Playwright Scraper Module

The Playwright module is a modular web scraping framework designed to scrape biomedical news websites using Headless Chrome.

## Features

- **Modular Design**: Easy to add new scrapers via a registry.
- **Asyncio**: Uses asynchronous execution for performance.
- **Headless/Headed Mode**: Can run visibly (for debugging) or headlessly.
- **Logging**: Detailed logging of scraping activities and network traces (in debug mode).
- **Screenshots**: Captures screenshots on errors.

## Supported Scrapers

- `endpoints`: Endpoints News
- `fierce`: Fierce Biotech
- `biopharma`: BioPharma Dive
- `biospace`: BioSpace

## Usage

This module is currently run as a standalone script.

### Prerequisites

You may need to install playwright and its browsers:

```bash
uv add playwright
uv run playwright install chromium
```

### Running a Scraper

```bash
# Run the 'endpoints' scraper
python src/biomed_tools/playwright/main.py endpoints

# Run in debug mode (verbose logs + network trace)
python src/biomed_tools/playwright/main.py endpoints --debug

# Run in headed mode (watch the browser)
python src/biomed_tools/playwright/main.py endpoints --no-headless
```

## Configuration

Configuration is handled in `src/biomed_tools/playwright/config.py`.
- **Output Directory**: `output/` (contains logs, screenshots, and article data).
- **Behavior**: Simulates human behavior with random pauses and scrolling.

## Output

- **Logs**: `output/logs/scraper.log`
- **Network Trace**: `output/logs/network_trace.log` (if debug)
- **Screenshots**: `output/screenshots/` (on error)
- **Articles**: Saved to specific subdirectories in `output/` depending on the scraper.
