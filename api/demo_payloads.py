"""Offline sample payloads shaped like the Cricbuzz responses (used when no API key is set)."""
import copy

_LIVE = {"typeMatches": [{"matchType": "International", "seriesMatches": [{"seriesAdWrapper": {
    "seriesId": 9001, "seriesName": "Demo Series: India vs Australia ODI",
    "matches": [{
        "matchInfo": {"matchId": 90011, "seriesName": "Demo Series: India vs Australia ODI",
                      "matchDesc": "2nd ODI", "matchFormat": "ODI",
                      "team1": {"teamName": "India"}, "team2": {"teamName": "Australia"},
                      "venueInfo": {"ground": "Eden Gardens", "city": "Kolkata"},
                      "state": "In Progress", "status": "India need 41 runs in 38 balls"},
        "matchScore": {"team1Score": {"inngs1": {"runs": 247, "wickets": 8, "overs": 50.0}},
                       "team2Score": {"inngs1": {"runs": 207, "wickets": 4, "overs": 41.4}}}}]}}]}]}

_SCORECARD = {"scorecard": [{"inningsId": 1, "batTeamName": "Australia", "score": 247, "wickets": 8, "overs": 50.0,
    "batsman": [{"name": "Demo Opener", "runs": 82, "balls": 91, "fours": 8, "sixes": 2, "outdec": "c Keeper b Bowler"},
                {"name": "Demo Number Three", "runs": 61, "balls": 70, "fours": 5, "sixes": 1, "outdec": "lbw b Spinner"}],
    "bowler": [{"name": "Demo Bowler", "overs": 10.0, "runs": 48, "wickets": 3, "economy": 4.8}]}]}

_TOP = {"headers": ["Player", "Team", "Matches", "Runs", "Average"], "values": [
    {"values": ["Demo Batter A", "India", "40", "2100", "55.3"]},
    {"values": ["Demo Batter B", "Australia", "38", "1980", "52.1"]},
    {"values": ["Demo Batter C", "England", "42", "1875", "47.9"]}]}

_PAYLOADS = {"live": _LIVE, "recent": _LIVE, "upcoming": {"typeMatches": []},
             "scorecard": _SCORECARD, "top_stats": _TOP, "player": {"name": "Demo Player"},
             "teams": {"list": []}, "series": {"seriesMapProto": []}}


def get(key):
    return copy.deepcopy(_PAYLOADS.get(key, {}))
