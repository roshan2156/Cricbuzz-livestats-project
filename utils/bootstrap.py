"""Make sure a populated database exists before any page renders."""
from pathlib import Path

import config
from utils.db_connection import get_connection, init_db


def ensure_database(db_path=None):
    """Create schema and load the synthetic demo data on first run."""
    path = Path(db_path or config.DB_PATH)
    needs_seed = not path.exists()
    if not needs_seed:
        conn = get_connection(db_path)
        try:
            has_table = conn.execute("SELECT name FROM sqlite_master WHERE name='matches'").fetchone()
            needs_seed = not has_table or conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 0
        finally:
            conn.close()
    if needs_seed:
        from scripts.seed_demo_data import seed
        init_db(db_path)
        seed(db_path)
    return True
