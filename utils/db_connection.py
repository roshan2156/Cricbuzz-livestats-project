"""Single place that opens database connections (SQLite by default)."""
import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

import config


def get_connection(db_path=None):
    """Return a new SQLite connection with foreign keys and Row access enabled."""
    path = db_path or config.DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # SQLite builds do not always ship math functions; MySQL/PostgreSQL have SQRT natively.
    conn.create_function("SQRT", 1, lambda x: None if x is None or x < 0 else math.sqrt(x))
    return conn


@contextmanager
def transaction(db_path=None):
    """Commit on success, roll back on any error, always close."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_query(sql, params=(), db_path=None):
    """Run a SELECT and return a DataFrame."""
    conn = get_connection(db_path)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def init_db(db_path=None):
    """Create tables, indexes and views from the sql/ folder."""
    conn = get_connection(db_path)
    try:
        for name in ("schema.sql", "views.sql"):
            conn.executescript((config.SQL_DIR / name).read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def run_readonly_query(sql, db_path=None, max_rows=1000):
    """Run user-typed SQL safely: a single SELECT/WITH statement on a read-only connection."""
    cleaned = (sql or "").strip().rstrip(";").strip()
    if not cleaned:
        raise ValueError("Query is empty.")
    if ";" in cleaned:
        raise ValueError("Only one statement is allowed.")
    if cleaned.split(None, 1)[0].lower() not in ("select", "with"):
        raise ValueError("Only SELECT queries are allowed here.")
    path = Path(db_path or config.DB_PATH).resolve()
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.create_function("SQRT", 1, lambda x: None if x is None or x < 0 else math.sqrt(x))
    try:
        return pd.read_sql_query(cleaned, conn).head(max_rows)
    finally:
        conn.close()
