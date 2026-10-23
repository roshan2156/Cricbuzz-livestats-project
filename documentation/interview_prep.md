# Interview & Viva Preparation (50 questions)

## Project and design
1. **What does the project do?** A Streamlit dashboard joining live Cricbuzz API data with a SQL database for scorecards, player stats, 25 analytics queries and CRUD.
2. **Why separate `api/`, `services/`, `utils/`, `pages/`?** Each layer has one job, so the UI can change without touching SQL, and the API client can be mocked in tests.
3. **Why keep all connections in `db_connection.py`?** One place to change engine, enable foreign keys, and enforce commit/rollback; the assignment asks for it too.
4. **How is it database-agnostic?** Standard SQL tables/constraints, one connection module, and the few SQLite-only functions are listed in the README.
5. **Why a demo mode?** The project runs offline and in CI without a paid key; the same code path serves real data once a key is set.
6. **Why synthetic data and how do you keep it honest?** Real history needs the API; the generator keeps scores internally consistent (batting runs = bowling runs conceded, winner = higher total) and a test checks it.
7. **How are secrets protected?** Environment variables / `.env` (git-ignored); the key is never stored or displayed.
8. **How would you scale this?** Move to PostgreSQL, cache API calls, schedule ingestion, add pagination and indexes on hot columns.

## Database
9. **Why 3NF?** It removes duplication of team/venue data and prevents update anomalies.
10. **Primary vs foreign key?** PK uniquely identifies a row; FK references another table's PK and keeps data valid.
11. **What does `ON DELETE CASCADE` do here?** Deleting a match removes its innings and performances; deleting a player removes their rows, so the service blocks that unless confirmed.
12. **Why `PRAGMA foreign_keys=ON`?** SQLite ignores foreign keys by default.
13. **Why is career-stats a separate table?** The API returns aggregates; storing them avoids recomputing and mirrors the endpoint.
14. **Which indexes did you add and why?** Match date/venue/winner and performance-table player/innings columns, because analytics filter and join on them.
15. **What is a view and why use one?** A stored query; `v_batting` etc. avoid repeating the same 3-table join in 25 queries.
16. **What is a CHECK constraint?** A rule evaluated on write, e.g. role must be one of four values.
17. **UNIQUE (innings_id, batting_position)?** Prevents two batters in the same slot.
18. **What is a transaction?** A group of statements that commit together or roll back together; `transaction()` does this.

## SQL
19. **WHERE vs HAVING?** WHERE filters rows before grouping; HAVING filters groups after aggregation.
20. **INNER vs LEFT JOIN?** Inner keeps matches only; left keeps all left rows (used for winners that may be NULL and optional bowling stats in Q21).
21. **What is a window function?** Computes across related rows without collapsing them (`ROW_NUMBER`, `LAG`).
22. **How did you rank per format in Q21?** `ROW_NUMBER() OVER (PARTITION BY match_format ORDER BY total DESC)`.
23. **How did you get "previous quarter" in Q25?** `LAG(avg_runs) OVER (PARTITION BY player ORDER BY quarter)`.
24. **How do you compute standard deviation without STDDEV?** `SQRT(AVG(x*x) - AVG(x)^2)` for population variance.
25. **Why `NULLIF(SUM(is_out),0)`?** Avoids divide-by-zero for players never dismissed.
26. **Batting average vs runs per innings?** Average divides by dismissals, so not-outs matter; hence the `is_out` column.
27. **How did you find home vs away (Q12)?** `UNION ALL` each match from both teams' view, then compare venue country with team country.
28. **How did you pair teams regardless of order (Q22/Q24)?** `MIN(a,b)` and `MAX(a,b)` normalise the pair.
29. **What is a CTE?** A named temporary result (`WITH ...`) that makes multi-step logic readable.
30. **Why `UNION ALL` instead of `UNION`?** No de-duplication cost; we want every row.
31. **How do you optimise a slow query?** Check the plan (`EXPLAIN QUERY PLAN`), add indexes on join/filter columns, filter early, avoid functions on indexed columns.
32. **What is the fan-out problem?** Joining two one-to-many tables multiplies rows and inflates SUMs; aggregate separately first (a bug I hit and fixed in a test).

## Python
33. **Why context managers for connections?** They guarantee commit/rollback and closing even on exceptions.
34. **Why custom exceptions (`CricbuzzAPIError`, `ValidationError`)?** Callers can catch specific failures and show friendly messages.
35. **What is exponential backoff?** Waiting 1s, 2s, 4s... between retries so a struggling server can recover.
36. **Why not retry on 401/403?** A wrong key will not fix itself; fail fast with a clear message.
37. **Why parse defensively with `.get()`?** Third-party JSON can omit keys; the UI should not crash.
38. **Why dependency injection (`session=`, `sleep=`)?** Tests run without network or real delays.
39. **PEP 8 benefits?** Consistent, readable code across a team.
40. **Why a service class for CRUD?** Keeps validation and SQL out of the UI and makes it unit-testable.

## Streamlit
41. **How does multipage work?** Files in `pages/` become sidebar pages beside `app.py`.
42. **Why does the script rerun on every interaction?** Streamlit's execution model; use forms/session state to control it.
43. **Why `st.form` for CRUD?** Batches inputs so the app only reruns on submit.
44. **When use `st.cache_data`?** For expensive pure reads like API calls; add a TTL for live data.
45. **How do you stop a bad custom query?** Single `SELECT/WITH` only, plus a read-only SQLite connection.

## API and system design
46. **How does RapidAPI authenticate?** Two headers: `x-rapidapi-key` and `x-rapidapi-host`.
47. **How do you respect rate limits?** Retry with backoff on 429, cache results, avoid polling faster than needed.
48. **How would you add real-time updates?** Poll every N seconds with `st_autorefresh` or move to a background worker writing to the DB.
49. **How would you make ingestion idempotent?** Upsert on a natural key (match id) so re-runs never duplicate rows; the current match save skips existing description/teams/date.
50. **What are the weaknesses of this project?** Endpoint paths untested against a live key, simplified innings model, SQLite concurrency limits, no authentication on CRUD.
