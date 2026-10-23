# Architecture

```
┌────────────────────────── Streamlit UI (app.py, pages/) ──────────────────────────┐
│ Home │ Live Matches │ Top Players │ SQL Analytics │ CRUD │ Settings               │
└───────┬───────────────┬───────────────┬──────────────┬───────────────┬────────────┘
        │               │               │              │               │
        │        ┌──────▼──────┐        │      ┌───────▼───────┐ ┌─────▼──────────┐
        │        │ api/        │        │      │ services/     │ │ services/      │
        │        │ client +    │        │      │ analytics_    │ │ player_service │
        │        │ parsers     │        │      │ queries (25)  │ │ (CRUD)         │
        │        └──────┬──────┘        │      └───────┬───────┘ └─────┬──────────┘
        │   Cricbuzz API│(RapidAPI)     │              │               │
        │        ┌──────▼──────┐        │      ┌───────▼───────────────▼─────────┐
        └───────►│ingest_service│───────┴─────►│ utils/db_connection (SQLite)    │
                 └─────────────┘               │ sql/schema.sql + views.sql      │
                                               └─────────────────────────────────┘
 config.py (env/.env) feeds every layer; utils/validators guards all writes.
```

Data flow: page -> service -> db_connection -> SQL. API data: client -> parser -> ingest_service -> SQL.

## ER diagram
```
teams 1──* players            teams 1──* matches (team1, team2, toss_winner, winner)
venues 1──* matches           series 1──* matches
matches 1──* innings 1──* batting_performances *──1 players
                     1──* bowling_performances *──1 players
                     1──* fielding_performances *──1 players
players 1──* player_career_stats (PK player_id + match_format)
```

## Normalisation (3NF)
Every non-key column depends only on its table's key: team and venue facts live once in `teams`/`venues`;
match facts reference them by ID; per-innings performance rows hold only performance values. Career
totals are stored separately in `player_career_stats` because the API returns them as aggregates; the
seed script derives them from the performance tables so the two stay consistent.

## Constraints and indexes
CHECK constraints on roles, formats, non-negative runs/overs, `team1_id <> team2_id`; UNIQUE on
(innings, player) and (innings, position); foreign keys enforced (`PRAGMA foreign_keys=ON`).
Indexes cover match date, venue, winner, innings->match, and player lookups on the performance tables.

## API endpoint -> table mapping
| Endpoint | Used for | Tables |
|---|---|---|
| /matches/v1/live, recent, upcoming | match lists | matches, teams, venues (via ingest_service) |
| /mcenter/v1/{id}/scard | scorecard | displayed live; maps to innings + batting/bowling_performances |
| /stats/v1/topstats/0 | top players | displayed live; compare with player_career_stats |
| /stats/v1/player/{id} | player profile | players, player_career_stats |
| /teams/v1/international, /series/v1/international | reference data | teams, series |
Only the matches path has an ingest implementation; the others are displayed live or left as extension points.

## Deployment
- **Streamlit Community Cloud:** push to GitHub, point it at `app.py`, add `RAPIDAPI_KEY` under Secrets
  (export it as an env var in `config.py` usage). SQLite is re-created on first run; data resets on redeploy.
- **Docker:** `FROM python:3.12-slim`, `COPY . .`, `pip install -r requirements.txt`,
  `CMD streamlit run app.py --server.port 8501 --server.address 0.0.0.0`.
- **Render / Railway / Azure / AWS:** deploy the same container; attach a managed PostgreSQL if you need
  persistence, and port `utils/db_connection.py` accordingly.
