"""Persist parsed API data into SQL (idempotent upserts)."""
from datetime import date

from api.parsers import parse_matches
from utils.db_connection import transaction

FORMAT_MAP = {"TEST": "Test", "ODI": "ODI", "T20": "T20I", "T20I": "T20I"}


def _team_id(conn, name):
    conn.execute("INSERT OR IGNORE INTO teams(team_name,country) VALUES(?,?)", (name, name))
    return conn.execute("SELECT team_id FROM teams WHERE team_name=?", (name,)).fetchone()[0]


def _venue_id(conn, ground, city):
    conn.execute("INSERT OR IGNORE INTO venues(venue_name,city,country) VALUES(?,?,?)", (ground, city, "Unknown"))
    return conn.execute("SELECT venue_id FROM venues WHERE venue_name=? AND city=?", (ground, city)).fetchone()[0]


def save_matches(payload, db_path=None):
    """Insert API matches that are not stored yet. Returns the number inserted."""
    rows = parse_matches(payload)
    inserted = 0
    with transaction(db_path) as conn:
        for r in rows:
            fmt = FORMAT_MAP.get(str(r["format"]).upper())
            if not (r["team1"] and r["team2"] and r["venue"] and fmt) or r["team1"] == r["team2"]:
                continue  # skip incomplete rows rather than corrupting the DB
            desc = f"{r['team1']} vs {r['team2']}, {r['description']}"
            t1, t2 = _team_id(conn, r["team1"]), _team_id(conn, r["team2"])
            vid = _venue_id(conn, r["venue"], r["city"] or "Unknown")
            today = date.today().isoformat()
            exists = conn.execute("SELECT 1 FROM matches WHERE description=? AND team1_id=? AND team2_id=? AND match_date=?",
                                  (desc, t1, t2, today)).fetchone()
            if exists:
                continue
            conn.execute("""INSERT INTO matches(description,match_format,team1_id,team2_id,venue_id,match_date,status)
                            VALUES(?,?,?,?,?,?,?)""", (desc, fmt, t1, t2, vid, today, r["state"] or "Live"))
            inserted += 1
    return inserted
