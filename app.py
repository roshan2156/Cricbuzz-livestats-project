"""Home page. Run with:  streamlit run app.py"""
import streamlit as st

import config
from utils.bootstrap import ensure_database
from utils.db_connection import run_query

st.set_page_config(page_title="Cricbuzz LiveStats", page_icon="🏏", layout="wide")
ensure_database()

st.title("🏏 Cricbuzz LiveStats")
st.caption("Real-time cricket insights and SQL-based analytics")

counts = run_query(
    "SELECT (SELECT COUNT(*) FROM players) AS players, (SELECT COUNT(*) FROM matches) AS matches,"
    " (SELECT COUNT(*) FROM teams) AS teams, (SELECT COUNT(*) FROM venues) AS venues")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Players", int(counts.players[0]))
c2.metric("Matches", int(counts.matches[0]))
c3.metric("Teams", int(counts.teams[0]))
c4.metric("Venues", int(counts.venues[0]))

if config.USE_DEMO_API:
    st.info("No RAPIDAPI_KEY found, so live pages show bundled demo payloads and the database holds "
            "**synthetic** demo data. Add a key in `.env` for real API calls (see README).")

st.subheader("Pages")
st.markdown("""
| Page | What it does |
|---|---|
| **Live Matches** | Ongoing matches and scorecards from the Cricbuzz API |
| **Top Players** | Top batting and bowling stats (API + database leaderboards) |
| **SQL Analytics** | 25 SQL questions, run live, plus a read-only SQL box |
| **CRUD Operations** | Add, view, update and delete player records |
| **Settings** | Database status, API configuration, re-seed demo data |
""")
st.subheader("Tools used")
st.write("Python, Streamlit, SQLite (portable to MySQL/PostgreSQL), pandas, requests, Cricbuzz API on RapidAPI.")
st.markdown("Documentation lives in `README.md` and the `documentation/` folder.")
