"""Run the 25 SQL practice questions and a read-only custom query box."""
import streamlit as st

from services.analytics_queries import Q
from utils.bootstrap import ensure_database
from utils.db_connection import run_query, run_readonly_query

st.set_page_config(page_title="SQL Analytics", page_icon="🔍", layout="wide")
ensure_database()
st.title("🔍 SQL Queries & Analytics")

tab_q, tab_custom = st.tabs(["25 practice questions", "Custom SQL (read-only)"])

with tab_q:
    level = st.radio("Level", ["All", "Beginner", "Intermediate", "Advanced"], horizontal=True)
    items = [q for q in Q if level in ("All", q["level"])]
    pick = st.selectbox("Question", items, format_func=lambda q: f"Q{q['id']} - {q['title']}")
    st.markdown(f"**Task:** {pick['task']}")
    st.caption(f"Concepts: {pick['concepts']}")
    for label, sql in pick["parts"]:
        st.markdown(f"##### {label}")
        with st.expander("Show SQL"):
            st.code(sql, language="sql")
        try:
            df = run_query(sql)
        except Exception as exc:  # show DB problems instead of crashing the page
            st.error(f"Query failed: {exc}")
            continue
        st.caption(f"{len(df)} row(s)")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download CSV", df.to_csv(index=False), f"q{pick['id']}_{label[:12]}.csv",
                           key=f"dl{pick['id']}{label}")

with tab_custom:
    st.write("Tables: teams, venues, players, series, matches, innings, batting_performances, "
             "bowling_performances, fielding_performances, player_career_stats. "
             "Views: v_match_details, v_batting, v_bowling.")
    text = st.text_area("SELECT query", "SELECT * FROM v_match_details ORDER BY match_date DESC LIMIT 10", height=140)
    if st.button("Run"):
        try:
            st.dataframe(run_readonly_query(text), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Could not run query: {exc}")
