"""Top batting and bowling stats."""
import streamlit as st

import config
from api.cricbuzz_client import CricbuzzAPIError, CricbuzzClient
from api.parsers import parse_top_stats
from utils.bootstrap import ensure_database
from utils.db_connection import run_query

st.set_page_config(page_title="Top Players", page_icon="🏆", layout="wide")
ensure_database()
st.title("🏆 Top Player Stats")

tab_db, tab_api = st.tabs(["Database leaderboards", "Live from API"])

with tab_db:
    fmt = st.selectbox("Format", config.FORMATS, index=1)
    board = st.selectbox("Leaderboard", ["Most runs", "Highest score", "Most wickets", "Best batting average"])
    sql = {
        "Most runs": "SELECT p.full_name AS player, p.country, s.runs AS value FROM player_career_stats s "
                     "JOIN players p USING(player_id) WHERE s.match_format=? ORDER BY s.runs DESC LIMIT 10",
        "Highest score": "SELECT p.full_name AS player, p.country, s.highest_score AS value FROM player_career_stats s "
                         "JOIN players p USING(player_id) WHERE s.match_format=? ORDER BY s.highest_score DESC LIMIT 10",
        "Most wickets": "SELECT p.full_name AS player, p.country, s.wickets AS value FROM player_career_stats s "
                        "JOIN players p USING(player_id) WHERE s.match_format=? ORDER BY s.wickets DESC LIMIT 10",
        "Best batting average": "SELECT p.full_name AS player, p.country, s.batting_avg AS value FROM player_career_stats s "
                                "JOIN players p USING(player_id) WHERE s.match_format=? AND s.matches>=20 "
                                "ORDER BY s.batting_avg DESC LIMIT 10",
    }[board]
    df = run_query(sql, (fmt,))
    left, right = st.columns([1, 1])
    left.dataframe(df, use_container_width=True, hide_index=True)
    right.bar_chart(df.set_index("player")["value"])

with tab_api:
    client = CricbuzzClient()
    if client.demo:
        st.warning("Demo mode: sample payload.")
    stat = st.selectbox("Stat", ["mostRuns", "highestScore", "mostWickets"])
    try:
        api_df = parse_top_stats(client.top_stats(stat))
    except CricbuzzAPIError as exc:
        st.error(f"API error: {exc}")
    else:
        if api_df.empty:
            st.info("No data returned.")
        else:
            st.dataframe(api_df, use_container_width=True, hide_index=True)
