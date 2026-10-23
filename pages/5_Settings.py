"""Settings and system status."""
import streamlit as st

import config
from utils.bootstrap import ensure_database
from utils.db_connection import run_query

st.set_page_config(page_title="Settings", page_icon="⚙", layout="wide")
ensure_database()
st.title("⚙ Settings")

st.subheader("API")
st.write("API key configured:", "yes" if config.RAPIDAPI_KEY else "no (demo mode)")
st.write("Host:", config.RAPIDAPI_HOST)
st.caption("Set RAPIDAPI_KEY in a local .env file. The key is never shown or stored in the database.")

st.subheader("Database")
st.write("File:", config.DB_PATH)
tables = ["teams", "venues", "players", "series", "matches", "innings", "batting_performances",
          "bowling_performances", "fielding_performances", "player_career_stats"]
counts = {t: int(run_query(f"SELECT COUNT(*) AS n FROM {t}").n[0]) for t in tables}
st.dataframe({"table": list(counts), "rows": list(counts.values())}, hide_index=True)

st.subheader("Reset demo data")
st.warning("This deletes the database file and regenerates the synthetic dataset.")
if st.button("Re-seed demo data"):
    from pathlib import Path
    from scripts.seed_demo_data import seed
    from utils.db_connection import init_db
    Path(config.DB_PATH).unlink(missing_ok=True)
    init_db()
    st.success(f"Re-seeded {seed()} matches.")
