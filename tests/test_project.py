"""Unit + integration tests (stdlib unittest; also discovered by pytest)."""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests  # noqa: E402

import config  # noqa: E402
from api.cricbuzz_client import CricbuzzAPIError, CricbuzzClient, RateLimitError  # noqa: E402
from api.parsers import parse_matches, parse_scorecard, parse_top_stats  # noqa: E402
from scripts.seed_demo_data import seed  # noqa: E402
from services.analytics_queries import Q  # noqa: E402
from services.ingest_service import save_matches  # noqa: E402
from services.player_service import PlayerService  # noqa: E402
from utils.db_connection import get_connection, run_query, run_readonly_query  # noqa: E402
from utils.validators import ValidationError  # noqa: E402

TMP = tempfile.mkdtemp()
DB = str(Path(TMP) / "test.db")
seed(DB)


class FakeResp:
    def __init__(self, status, body=None, bad_json=False):
        self.status_code, self._body, self._bad = status, body or {}, bad_json

    def json(self):
        if self._bad:
            raise ValueError("bad json")
        return self._body


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), 0

    def get(self, *a, **k):
        self.calls += 1
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


class DatabaseTests(unittest.TestCase):
    def test_row_counts(self):
        self.assertEqual(run_query("SELECT COUNT(*) n FROM teams", db_path=DB).n[0], 8)
        self.assertGreater(run_query("SELECT COUNT(*) n FROM matches", db_path=DB).n[0], 400)

    def test_foreign_keys_enforced(self):
        conn = get_connection(DB)
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO innings(match_id,innings_no,batting_team_id) VALUES(999999,1,1)")
        conn.close()

    def test_check_constraint_role(self):
        conn = get_connection(DB)
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO players(full_name,country,playing_role) VALUES('Bad Role','India','Umpire')")
        conn.close()

    def test_scores_add_up(self):
        """Batting runs and bowling runs conceded must agree for every innings."""
        bad = run_query("""SELECT COUNT(*) n FROM innings i
            WHERE (SELECT SUM(runs) FROM batting_performances WHERE innings_id=i.innings_id)
               <> (SELECT SUM(runs_conceded) FROM bowling_performances WHERE innings_id=i.innings_id)""", db_path=DB)
        self.assertEqual(bad.n[0], 0)

    def test_winner_matches_scores(self):
        bad = run_query("""SELECT COUNT(*) n FROM matches m WHERE m.status='Completed'
            AND m.winner_id <> (SELECT batting_team_id FROM innings i WHERE i.match_id=m.match_id ORDER BY
                (SELECT SUM(runs) FROM batting_performances b WHERE b.innings_id=i.innings_id) DESC LIMIT 1)""", db_path=DB)
        self.assertEqual(bad.n[0], 0)


class AnalyticsTests(unittest.TestCase):
    def test_there_are_25_questions(self):
        self.assertEqual([q["id"] for q in Q], list(range(1, 26)))

    def test_every_query_runs_and_returns_rows(self):
        for q in Q:
            for label, sql in q["parts"]:
                with self.subTest(q=q["id"], part=label):
                    self.assertGreater(len(run_query(sql, db_path=DB)), 0)

    def test_q4_only_big_venues(self):
        df = run_query(Q[3]["parts"][0][1], db_path=DB)
        self.assertTrue((df.capacity > 50000).all())
        self.assertNotIn("Eden Park", df.venue_name.tolist())  # exactly 50,000

    def test_q1_only_india(self):
        n = run_query("SELECT COUNT(*) n FROM players WHERE country='India'", db_path=DB).n[0]
        self.assertEqual(len(run_query(Q[0]["parts"][0][1], db_path=DB)), n)

    def test_q17_overall_matches_sum(self):
        df = run_query(Q[16]["parts"][0][1], db_path=DB).set_index("toss_decision")
        self.assertEqual(df.loc["bat", "matches"] + df.loc["bowl", "matches"], df.loc["overall", "matches"])


class CrudTests(unittest.TestCase):
    def setUp(self):
        self.svc = PlayerService(DB)

    def test_full_lifecycle(self):
        pid = self.svc.create_player("Test Player", "India", "Batsman", "Right-hand bat")
        self.assertEqual(self.svc.get_player(pid)["full_name"], "Test Player")
        self.svc.update_player(pid, "Test Player Jr", "India", "All-rounder")
        self.assertEqual(self.svc.get_player(pid)["playing_role"], "All-rounder")
        self.svc.upsert_career_stats(pid, "ODI", 10, 400, 5, 90, 0)
        self.svc.upsert_career_stats(pid, "ODI", 11, 450, 5, 90, 0)  # upsert, not duplicate
        self.assertEqual(len(self.svc.get_career_stats(pid)), 1)
        self.svc.delete_player(pid)
        self.assertIsNone(self.svc.get_player(pid))

    def test_validation(self):
        with self.assertRaises(ValidationError):
            self.svc.create_player("", "India", "Batsman")
        with self.assertRaises(ValidationError):
            self.svc.create_player("Valid Name", "India", "Umpire")
        with self.assertRaises(ValidationError):
            self.svc.upsert_career_stats(1, "ODI", 1, 50, 0, 80, 0)  # highest > runs

    def test_duplicate_rejected(self):
        self.svc.create_player("Dup Person", "Pakistan", "Bowler")
        with self.assertRaises(ValidationError):
            self.svc.create_player("Dup Person", "Pakistan", "Bowler")

    def test_delete_with_history_needs_cascade(self):
        pid = int(run_query("SELECT player_id FROM batting_performances LIMIT 1", db_path=DB).player_id[0])
        with self.assertRaises(ValidationError):
            self.svc.delete_player(pid)

    def test_update_missing_player(self):
        with self.assertRaises(ValidationError):
            self.svc.update_player(987654, "Nobody Here", "India", "Batsman")


class ApiTests(unittest.TestCase):
    def client(self, responses):
        sess = FakeSession(responses)
        return CricbuzzClient(api_key="k", session=sess, demo=False, sleep=lambda s: None), sess

    def test_success(self):
        c, _ = self.client([FakeResp(200, {"ok": 1})])
        self.assertEqual(c.live_matches(), {"ok": 1})

    def test_retry_then_success(self):
        c, s = self.client([requests.ConnectionError("down"), FakeResp(503), FakeResp(200, {"ok": 1})])
        self.assertEqual(c.live_matches(), {"ok": 1})
        self.assertEqual(s.calls, 3)

    def test_rate_limit_exhausted(self):
        c, _ = self.client([FakeResp(429)] * config.API_MAX_RETRIES)
        with self.assertRaises(RateLimitError):
            c.live_matches()

    def test_bad_key_no_retry(self):
        c, s = self.client([FakeResp(403)])
        with self.assertRaises(CricbuzzAPIError):
            c.live_matches()
        self.assertEqual(s.calls, 1)

    def test_bad_json(self):
        c, _ = self.client([FakeResp(200, bad_json=True)])
        with self.assertRaises(CricbuzzAPIError):
            c.live_matches()

    def test_network_failure(self):
        c, _ = self.client([requests.Timeout("t")] * config.API_MAX_RETRIES)
        with self.assertRaises(CricbuzzAPIError):
            c.live_matches()

    def test_demo_mode_needs_no_network(self):
        c = CricbuzzClient(demo=True)
        self.assertEqual(len(parse_matches(c.live_matches())), 1)
        bat, bowl = parse_scorecard(c.scorecard(1))
        self.assertFalse(bat.empty and bowl.empty)
        self.assertEqual(len(parse_top_stats(c.top_stats())), 3)


class ParserAndIngestTests(unittest.TestCase):
    def test_parsers_survive_garbage(self):
        self.assertEqual(parse_matches({}), [])
        self.assertEqual(parse_matches({"typeMatches": [{"seriesMatches": [{}]}]}), [])
        self.assertTrue(parse_top_stats({"headers": ["a"], "values": [{"values": ["1", "2"]}]}).empty)

    def test_ingest_is_idempotent(self):
        payload = CricbuzzClient(demo=True).live_matches()
        self.assertEqual(save_matches(payload, DB), 1)
        self.assertEqual(save_matches(payload, DB), 0)


class ReadonlyGuardTests(unittest.TestCase):
    def test_select_ok(self):
        self.assertEqual(len(run_readonly_query("SELECT * FROM teams;", DB)), 8)

    def test_rejects_writes_and_multi_statements(self):
        for bad in ("DELETE FROM teams", "DROP TABLE teams", "SELECT 1; DELETE FROM teams", "", "PRAGMA table_info(teams)"):
            with self.subTest(sql=bad), self.assertRaises(ValueError):
                run_readonly_query(bad, DB)

    def test_readonly_connection_blocks_cte_write(self):
        with self.assertRaises(Exception):
            run_readonly_query("WITH x AS (SELECT 1) DELETE FROM teams", DB)


if __name__ == "__main__":
    unittest.main()
