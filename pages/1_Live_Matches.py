"""Live matches and scorecards from the Cricbuzz API."""
import streamlit as st
import pandas as pd

from api.cricbuzz_client import CricbuzzAPIError, CricbuzzClient
from api.parsers import parse_matches, parse_scorecard
from services.ingest_service import save_matches
from utils.bootstrap import ensure_database

st.set_page_config(page_title="Live Matches", page_icon="📺", layout="wide")
ensure_database()
st.title("📺 Live Matches")

client = CricbuzzClient()
if client.demo:
    st.warning("Demo mode: showing a bundled sample payload, not live data.")

source = st.radio("Match list", ["live", "recent", "upcoming"], horizontal=True)
try:
    payload = {"live": client.live_matches, "recent": client.recent_matches,
               "upcoming": client.upcoming_matches}[source]()
except CricbuzzAPIError as exc:
    st.error(f"Could not fetch matches: {exc}")
    st.stop()

matches = parse_matches(payload)
if not matches:
    st.info(f"No {source} matches right now.")
    st.stop()

df = pd.DataFrame(matches)
st.dataframe(df[["series", "description", "format", "team1", "team1_score", "team2", "team2_score",
                 "venue", "city", "status"]], use_container_width=True, hide_index=True)

if st.button("Save these matches to the database"):
    st.success(f"Inserted {save_matches(payload)} new match(es).")

labels = {f"{m['team1']} vs {m['team2']} - {m['description']}": m["match_id"] for m in matches}
choice = st.selectbox("Open scorecard", list(labels))
try:
    batting, bowling = parse_scorecard(client.scorecard(labels[choice]))
except CricbuzzAPIError as exc:
    st.error(f"Scorecard unavailable: {exc}")
    st.stop()
if batting.empty and bowling.empty:
    st.info("Scorecard not published yet.")
else:
    st.subheader("Batting")
    st.dataframe(batting, use_container_width=True, hide_index=True)
    st.subheader("Bowling")
    st.dataframe(bowling, use_container_width=True, hide_index=True)
