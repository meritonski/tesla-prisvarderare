"""
Konfiguration för EV Price Estimator

Den här filen innehåller ALLA inställningar.
Ingen annan fil ska ha hårdkodade värden.
"""

from pathlib import Path


# ==========================================
# MAPPAR
# ==========================================

ROOT = Path(__file__).parent

DATA_DIR = ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

HISTORY_DIR = DATA_DIR / "history"


RAW_DATABASE = RAW_DATA_DIR / "ev_market_database.csv"

RANKED_DATABASE = PROCESSED_DATA_DIR / "ev_market_ranked.csv"

CARS_FILE = ROOT / "cars.json"



# ==========================================
# SCRAPER
# ==========================================

HEADLESS = True

MAX_SEARCH_PAGES = 25

MAX_DETAIL_PAGES_PER_SEARCH = 250

SEARCH_PAGE_DELAY_MS = 4000

DETAIL_PAGE_DELAY_MS = 1500

BETWEEN_DETAILS_DELAY_MS = 1000

TIMEOUT_MS = 60000



# ==========================================
# ANALYS
# ==========================================

MIN_YEAR = 2015

MAX_YEAR = 2026

MIN_PRICE = 50000

MAX_PRICE = 2500000

MIN_MILEAGE = 100

MAX_MILEAGE = 500000



# ==========================================
# OUTLIERS
# ==========================================

MIN_GROUP_SIZE_FOR_OUTLIERS = 8

IQR_MULTIPLIER = 1.75



# ==========================================
# ALGORITM
# ==========================================

YEAR_WEIGHT = 22000

KM_PLUS = 450

KM_MINUS = 900

YEAR_SCALE = 2.0

KM_SCALE = 50000



# ==========================================
# RISKMODELL
# ==========================================

FIRST_WARNING_KM = 80000

SECOND_WARNING_KM = 120000

THIRD_WARNING_KM = 160000

BATTERY_GUARANTEE_YEARS = 8



# ==========================================
# GITHUB ACTIONS
# ==========================================

UPDATE_WEEKDAY = "FRIDAY"



# ==========================================
# APP
# ==========================================

NUMBER_OF_SIMILAR_CARS = 3

DEFAULT_PRICE = 400000

DEFAULT_MILEAGE = 75000



# ==========================================
# VISNING
# ==========================================

APP_TITLE = "Elbilsvärderaren"

APP_SUBTITLE = (
    "Värdera en elbil genom en statistisk marknadsmodell "
    "som analyserar verkliga annonser."
)
