# /config.py

import os

# --- Main Configuration ---
DEBUG_MODE = False  # SET TO TRUE FOR VERBOSE LOGGING AND NETWORK TRACING
HEADLESS_MODE = False # Set to False to watch the browser in action

# --- File/Directory Paths ---
# Use BIOMED_DATA_DIR env var or default to 'data' in current directory
DATA_DIR = os.getenv("BIOMED_DATA_DIR", "data")
BASE_OUTPUT_DIR = os.path.join(DATA_DIR, "playwright")
PROFILE_DIR = os.path.join(DATA_DIR, "chrome_profile")

# --- Human Behavior Configuration ---
SHORT_PAUSE_MIN, SHORT_PAUSE_MAX = 1.5, 4.5
BIMODAL_WEIGHTS = [0.30, 0.70]
READ_SECONDS_PER_SCREEN, SKIM_SECONDS_PER_SCREEN = 18.0, 3.5
MIN_READ_TIME, MAX_READ_TIME = 15.0, 150.0
MIN_SKIM_TIME, MAX_SKIM_TIME = 4.0, 20.0

SCREENSHOTS_DIR = os.path.join(BASE_OUTPUT_DIR, "screenshots")
LOG_DIR = os.path.join(BASE_OUTPUT_DIR, "logs")
NETWORK_TRACE_FILE = os.path.join(LOG_DIR, "network_trace.log")
MAIN_LOG_FILE = os.path.join(LOG_DIR, "scraper.log")

# --- Endpoints.news Specific Configuration ---
ENDPOINTS_BASE_DIR = os.path.join(BASE_OUTPUT_DIR, "endpoints_articles")
ENDPOINTS_STATE_FILE = "endpoints_login_state.json"
ENDPOINTS_CHANNELS = [
    'ai', 'special', 'deals', 'financing', 'biotech-voices', 
    'cell-gene-tx', 'diagnostics', 'discovery', 'fda-plus', 'pharma', 
    'rd', 'startups', 'weekly'
]

# --- FierceBiotech Specific Configuration ---
FIERCE_BASE_DIR = os.path.join(BASE_OUTPUT_DIR, "fiercebiotech_articles")
FIERCE_CHANNELS = [
    "https://www.fiercebiotech.com/biotech", # Added a general biotech for more articles
    "https://www.fiercebiotech.com/clinical-data",
    "https://www.fiercebiotech.com/venture-capital",
    "https://www.fiercebiotech.com/deals",
    "https://www.fiercebiotech.com/research",
    "https://www.fiercebiotech.com/diagnostics",
    "https://www.fiercebiotech.com/ai-and-machine-learning",
    "https://www.fiercebiotech.com/cro",
    "https://www.fiercebiotech.com/keyword/cell-gene-therapy",
    "https://www.fiercebiotech.com/keyword/biologics",
    "https://www.fiercebiotech.com/special-reports",
    "https://www.fiercebiotech.com/keyword/clinical-development"
]

# --- BioPharmaDive Specific Configuration ---
BIOPHARMA_DIVE_BASE_DIR = os.path.join(BASE_OUTPUT_DIR, "biopharmadive_articles")
BIOPHARMA_DIVE_CHANNELS = [
    "https://www.biopharmadive.com/topic/pharma/",
    "https://www.biopharmadive.com/topic/biotech/",
    "https://www.biopharmadive.com/topic/fda/",
    "https://www.biopharmadive.com/topic/clinical-trials/",
    "https://www.biopharmadive.com/topic/deals/",
    "https://www.biopharmadive.com/topic/drug-pricing/",
    "https://www.biopharmadive.com/topic/gene-therapy/",
    "https://www.biopharmadive.com/press-release/"
]

# --- BioSpace Specific Configuration ---
BIOSPACE_BASE_DIR = os.path.join(BASE_OUTPUT_DIR, "biospace_articles")
BIOSPACE_CHANNELS = [
    "https://www.biospace.com/news/",
    "https://www.biospace.com/drug-development/",
    "https://www.biospace.com/fda/",
    "https://www.biospace.com/drug-delivery/",
    "https://www.biospace.com/deals/",
    "https://www.biospace.com/business/",
    "https://www.biospace.com/job-trends/",
    "https://www.biospace.com/cell-and-gene-therapy/",
    "https://www.biospace.com/cancer/",
    "https://www.biospace.com/search-press-releases/"
]

# Create directories if they don't exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
