# 🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics

A multi-page Streamlit app that combines the Cricbuzz Cricket API (via RapidAPI) with a relational SQL
database: live scorecards, top-player stats, 25 SQL analytics questions, and form-based CRUD.

**Live app:** https://cricbuzz-livestats-project-54pxbamwtkuqopebgqrbu6.streamlit.app/

**Data sources.** Live Matches, scorecards and the API tab of Top Players come from the Cricbuzz Cricket API
(RapidAPI). The SQL analytics, leaderboards and CRUD pages run on the SQL database, which is pre-loaded with a
generated sample dataset (`scripts/seed_demo_data.py`) so all 25 queries have enough history to work with.
Matches you save from the Live Matches page are added to the same database.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then add your RAPIDAPI_KEY
streamlit run app.py
```

The first launch creates `data/cricket.db` and seeds it automatically.
Run the tests with `python -m unittest discover -s tests -v` (or `pytest`).

## API setup
1. Subscribe to the free Basic plan of **Cricbuzz Cricket** on RapidAPI (100 requests/day).
2. Put the key in `.env` as `RAPIDAPI_KEY=...` (on Streamlit Cloud: App settings > Secrets). Requests send `x-rapidapi-key` and `x-rapidapi-host` headers.
3. The endpoint paths live in `api/cricbuzz_client.py` (`ENDPOINTS`). Check them against your RapidAPI
   page, since providers can change paths. The parsers in `api/parsers.py` ignore missing keys, so small
   schema differences degrade gracefully instead of crashing.

## Database setup
- SQLite by default (zero setup). Schema: `sql/schema.sql`; views: `sql/views.sql`.
- Connections are opened only in `utils/db_connection.py`. To move to MySQL/PostgreSQL, change that file
  and replace the few SQLite-specific functions in `services/analytics_queries.py`
  (`date('now', ...)`, `strftime`, `GROUP_CONCAT`, `MIN/MAX(a,b)` as `LEAST/GREATEST`).

## Features by page
| Page | Highlights |
|---|---|
| Home | Project summary, live row counts, navigation |
| Live Matches | Live/recent/upcoming lists, scorecards, "save to DB" |
| Top Players | DB leaderboards with charts + API top stats |
| SQL Analytics | 25 questions (beginner to advanced), SQL shown, CSV download, read-only custom SQL |
| CRUD Operations | Create/read/update/delete players, upsert career stats, validation, delete-protection |
| Settings | API/DB status, re-seed demo data |

## Folder structure
```
cricbuzz_livestats/
├── app.py                  Home page (entry point)
├── config.py               Settings from environment / .env
├── requirements.txt  .env.example  .gitignore
├── pages/                  Streamlit pages (1_Live_Matches ... 5_Settings)
├── api/                    cricbuzz_client (requests + retry), parsers, demo_payloads
├── services/               player_service (CRUD), ingest_service (API->SQL), analytics_queries (25 SQL)
├── utils/                  db_connection, validators, bootstrap
├── sql/                    schema.sql, views.sql
├── scripts/                seed_demo_data.py
├── tests/                  test_project.py (29 tests)
├── documentation/          architecture, API mapping, interview prep, deployment
├── data/                   SQLite file (git-ignored)
└── assets/ models/         reserved for screenshots / future dataclasses
```

## Notes
- Synthetic innings are simplified: every match has 2 innings (even Tests), overs are whole numbers,
  and a "partnership" is the sum of two adjacent batters' runs, as the assignment defines it.
- The free API plan allows 100 requests per day.

## Future improvements
Scheduled API ingestion, player comparison charts, authentication for CRUD, Docker image,
PostgreSQL profile, caching of API calls, richer match-state parsing.
