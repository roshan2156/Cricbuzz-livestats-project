"""Central configuration. Secrets come from environment variables / .env only."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "sql"
DATA_DIR = BASE_DIR / "data"

DB_PATH = os.getenv("CRICKET_DB_PATH", str(DATA_DIR / "cricket.db"))

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "cricbuzz-cricket.p.rapidapi.com")
API_BASE_URL = f"https://{RAPIDAPI_HOST}"
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
API_MAX_RETRIES = int(os.getenv("API_MAX_RETRIES", "3"))
API_BACKOFF_SECONDS = float(os.getenv("API_BACKOFF_SECONDS", "1.0"))

# When no API key is set the app falls back to bundled demo payloads.
USE_DEMO_API = os.getenv("USE_DEMO_API", "").lower() in {"1", "true", "yes"} or not RAPIDAPI_KEY

FORMATS = ("Test", "ODI", "T20I")
PLAYING_ROLES = ("Batsman", "Bowler", "All-rounder", "Wicket-keeper")
