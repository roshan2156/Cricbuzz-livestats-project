"""CRUD operations for players and their career statistics."""
import sqlite3

import pandas as pd

from utils.db_connection import run_query, transaction
from utils.validators import ValidationError, validate_career_stats, validate_player


class PlayerService:
    """Data-access object for the players and player_career_stats tables."""

    def __init__(self, db_path=None):
        self.db_path = db_path

    # ---- Create ----
    def create_player(self, full_name, country, playing_role, batting_style=None, bowling_style=None):
        data = validate_player(full_name, country, playing_role, batting_style, bowling_style)
        try:
            with transaction(self.db_path) as conn:
                team = conn.execute("SELECT team_id FROM teams WHERE country=?", (data["country"],)).fetchone()
                cur = conn.execute(
                    """INSERT INTO players(full_name,team_id,country,playing_role,batting_style,bowling_style)
                       VALUES(?,?,?,?,?,?)""",
                    (data["full_name"], team[0] if team else None, data["country"], data["playing_role"],
                     data["batting_style"], data["bowling_style"]))
                return cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Could not add player (duplicate or invalid data): {exc}") from exc

    # ---- Read ----
    def get_player(self, player_id):
        df = run_query("SELECT * FROM players WHERE player_id=?", (player_id,), self.db_path)
        return None if df.empty else df.iloc[0].to_dict()

    def list_players(self, search="", country=None, role=None, limit=200):
        sql = "SELECT player_id, full_name, country, playing_role, batting_style, bowling_style FROM players WHERE 1=1"
        params = []
        if search:
            sql += " AND full_name LIKE ?"
            params.append(f"%{search.strip()}%")
        if country:
            sql += " AND country=?"
            params.append(country)
        if role:
            sql += " AND playing_role=?"
            params.append(role)
        sql += " ORDER BY full_name LIMIT ?"
        params.append(int(limit))
        return run_query(sql, tuple(params), self.db_path)

    # ---- Update ----
    def update_player(self, player_id, full_name, country, playing_role, batting_style=None, bowling_style=None):
        data = validate_player(full_name, country, playing_role, batting_style, bowling_style)
        try:
            with transaction(self.db_path) as conn:
                cur = conn.execute(
                    """UPDATE players SET full_name=?, country=?, playing_role=?, batting_style=?, bowling_style=?
                       WHERE player_id=?""",
                    (data["full_name"], data["country"], data["playing_role"], data["batting_style"],
                     data["bowling_style"], player_id))
                if cur.rowcount == 0:
                    raise ValidationError(f"No player with id {player_id}.")
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"Update violates a constraint: {exc}") from exc

    # ---- Delete ----
    def delete_player(self, player_id, cascade=False):
        """Delete a player. Refuses when match history exists unless cascade=True."""
        with transaction(self.db_path) as conn:
            history = conn.execute("SELECT COUNT(*) FROM batting_performances WHERE player_id=?", (player_id,)).fetchone()[0]
            if history and not cascade:
                raise ValidationError(f"Player has {history} batting records. Tick 'also delete match history' to remove them.")
            cur = conn.execute("DELETE FROM players WHERE player_id=?", (player_id,))
            if cur.rowcount == 0:
                raise ValidationError(f"No player with id {player_id}.")

    # ---- Career stats (CRUD on stats rows) ----
    def get_career_stats(self, player_id):
        return run_query("SELECT * FROM player_career_stats WHERE player_id=? ORDER BY match_format",
                         (player_id,), self.db_path)

    def upsert_career_stats(self, player_id, match_format, matches, runs, wickets, highest_score, centuries):
        validate_career_stats(match_format, matches, runs, wickets, highest_score, centuries)
        with transaction(self.db_path) as conn:
            if not conn.execute("SELECT 1 FROM players WHERE player_id=?", (player_id,)).fetchone():
                raise ValidationError(f"No player with id {player_id}.")
            conn.execute(
                """INSERT INTO player_career_stats(player_id,match_format,matches,runs,wickets,highest_score,centuries)
                   VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(player_id,match_format) DO UPDATE SET matches=excluded.matches, runs=excluded.runs,
                   wickets=excluded.wickets, highest_score=excluded.highest_score, centuries=excluded.centuries""",
                (player_id, match_format, int(matches), int(runs), int(wickets), int(highest_score), int(centuries)))

    def delete_career_stats(self, player_id, match_format):
        with transaction(self.db_path) as conn:
            cur = conn.execute("DELETE FROM player_career_stats WHERE player_id=? AND match_format=?",
                               (player_id, match_format))
            if cur.rowcount == 0:
                raise ValidationError("No such career-stats row.")

    def countries(self):
        df = run_query("SELECT DISTINCT country FROM players ORDER BY country", db_path=self.db_path)
        return df["country"].tolist() if not df.empty else []


__all__ = ["PlayerService", "ValidationError", "pd"]
