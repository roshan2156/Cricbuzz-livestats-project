"""Create, read, update and delete player records."""
import streamlit as st

import config
from services.player_service import PlayerService
from utils.bootstrap import ensure_database
from utils.validators import ValidationError

st.set_page_config(page_title="CRUD Operations", page_icon="🛠", layout="wide")
ensure_database()
st.title("🛠 CRUD Operations")
svc = PlayerService()

tab_c, tab_r, tab_u, tab_d, tab_s = st.tabs(["Create", "Read", "Update", "Delete", "Career stats"])


def _player_picker(key):
    df = svc.list_players(limit=500)
    options = {f"{r.full_name} ({r.country}) #{r.player_id}": int(r.player_id) for r in df.itertuples()}
    label = st.selectbox("Player", list(options), key=key)
    return options[label]


with tab_c:
    with st.form("create"):
        name = st.text_input("Full name")
        country = st.text_input("Country")
        role = st.selectbox("Playing role", config.PLAYING_ROLES)
        bat = st.text_input("Batting style (optional)")
        bowl = st.text_input("Bowling style (optional)")
        if st.form_submit_button("Add player"):
            try:
                st.success(f"Added player #{svc.create_player(name, country, role, bat, bowl)}")
            except ValidationError as exc:
                st.error(str(exc))

with tab_r:
    c1, c2, c3 = st.columns(3)
    term = c1.text_input("Search name")
    ctry = c2.selectbox("Country", [""] + svc.countries())
    rl = c3.selectbox("Role", [""] + list(config.PLAYING_ROLES))
    st.dataframe(svc.list_players(term, ctry or None, rl or None), use_container_width=True, hide_index=True)

with tab_u:
    pid = _player_picker("upd_pick")
    cur = svc.get_player(pid)
    with st.form("update"):
        name = st.text_input("Full name", cur["full_name"])
        country = st.text_input("Country", cur["country"])
        role = st.selectbox("Playing role", config.PLAYING_ROLES, index=config.PLAYING_ROLES.index(cur["playing_role"]))
        bat = st.text_input("Batting style", cur["batting_style"] or "")
        bowl = st.text_input("Bowling style", cur["bowling_style"] or "")
        if st.form_submit_button("Save changes"):
            try:
                svc.update_player(pid, name, country, role, bat, bowl)
                st.success("Player updated.")
            except ValidationError as exc:
                st.error(str(exc))

with tab_d:
    pid = _player_picker("del_pick")
    cascade = st.checkbox("Also delete this player's match history")
    confirm = st.checkbox("I understand this cannot be undone")
    if st.button("Delete player", disabled=not confirm):
        try:
            svc.delete_player(pid, cascade=cascade)
            st.success("Player deleted. Reload the page to refresh the list.")
        except ValidationError as exc:
            st.error(str(exc))

with tab_s:
    pid = _player_picker("stat_pick")
    st.dataframe(svc.get_career_stats(pid), use_container_width=True, hide_index=True)
    with st.form("stats"):
        fmt = st.selectbox("Format", config.FORMATS)
        matches = st.number_input("Matches", 0, 1000, 0)
        runs = st.number_input("Runs", 0, 50000, 0)
        wickets = st.number_input("Wickets", 0, 2000, 0)
        high = st.number_input("Highest score", 0, 500, 0)
        cent = st.number_input("Centuries", 0, 100, 0)
        if st.form_submit_button("Save career stats"):
            try:
                svc.upsert_career_stats(pid, fmt, matches, runs, wickets, high, cent)
                st.success("Saved.")
            except ValidationError as exc:
                st.error(str(exc))
