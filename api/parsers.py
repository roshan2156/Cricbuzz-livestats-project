"""Turn raw Cricbuzz JSON into flat Python rows. Missing keys never crash the app."""
import pandas as pd


def _score(block):
    inn = (block or {}).get("inngs1") or {}
    if not inn:
        return ""
    return f"{inn.get('runs', 0)}/{inn.get('wickets', 0)} ({inn.get('overs', 0)} ov)"


def parse_matches(payload):
    """typeMatches -> seriesMatches -> matches  =>  list of flat dicts."""
    rows = []
    for tm in (payload or {}).get("typeMatches", []) or []:
        for sm in tm.get("seriesMatches", []) or []:
            wrap = sm.get("seriesAdWrapper") or {}
            for m in wrap.get("matches", []) or []:
                info, score = m.get("matchInfo", {}), m.get("matchScore", {})
                venue = info.get("venueInfo", {})
                rows.append({
                    "match_id": info.get("matchId"),
                    "series": info.get("seriesName", wrap.get("seriesName", "")),
                    "description": info.get("matchDesc", ""),
                    "format": info.get("matchFormat", ""),
                    "team1": (info.get("team1") or {}).get("teamName", ""),
                    "team2": (info.get("team2") or {}).get("teamName", ""),
                    "team1_score": _score(score.get("team1Score")),
                    "team2_score": _score(score.get("team2Score")),
                    "venue": venue.get("ground", ""),
                    "city": venue.get("city", ""),
                    "state": info.get("state", ""),
                    "status": info.get("status", ""),
                })
    return rows


def parse_scorecard(payload):
    """Return (batting_df, bowling_df) with an 'innings' column."""
    bat, bowl = [], []
    for inn in (payload or {}).get("scorecard", []) or []:
        label = f"{inn.get('batTeamName', '?')} - innings {inn.get('inningsId', '?')}"
        for b in inn.get("batsman", []) or []:
            bat.append({"innings": label, "batter": b.get("name"), "runs": b.get("runs", 0),
                        "balls": b.get("balls", 0), "fours": b.get("fours", 0),
                        "sixes": b.get("sixes", 0), "dismissal": b.get("outdec", "")})
        for b in inn.get("bowler", []) or []:
            bowl.append({"innings": label, "bowler": b.get("name"), "overs": b.get("overs", 0),
                         "runs": b.get("runs", 0), "wickets": b.get("wickets", 0),
                         "economy": b.get("economy", 0)})
    return pd.DataFrame(bat), pd.DataFrame(bowl)


def parse_top_stats(payload):
    """headers + values[].values  =>  DataFrame with numeric columns coerced."""
    headers = (payload or {}).get("headers", []) or []
    rows = [r.get("values", []) for r in (payload or {}).get("values", []) or []]
    rows = [r for r in rows if len(r) == len(headers)]
    df = pd.DataFrame(rows, columns=headers)
    for col in df.columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().all():
            df[col] = converted
    return df
