"""Generate a deterministic SYNTHETIC cricket dataset so every module works offline.

All match results, scores and player names are generated, not real. Venue names and
approximate capacities are real-world facts; everything else is demo data.

Usage:  python scripts/seed_demo_data.py [--reset]
"""
import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config  # noqa: E402
from utils.db_connection import get_connection, init_db  # noqa: E402

TEAMS = {  # name: (country, strength)
    "India": ("India", 0.64), "Australia": ("Australia", 0.62), "England": ("England", 0.58),
    "Pakistan": ("Pakistan", 0.52), "South Africa": ("South Africa", 0.54),
    "New Zealand": ("New Zealand", 0.53), "Sri Lanka": ("Sri Lanka", 0.46),
    "West Indies": ("West Indies", 0.44),
}
VENUES = [  # name, city, country, approx capacity
    ("Narendra Modi Stadium", "Ahmedabad", "India", 132000), ("Eden Gardens", "Kolkata", "India", 66000),
    ("Melbourne Cricket Ground", "Melbourne", "Australia", 100024), ("Sydney Cricket Ground", "Sydney", "Australia", 48000),
    ("Lord's", "London", "England", 31100), ("The Oval", "London", "England", 27500),
    ("Gaddafi Stadium", "Lahore", "Pakistan", 34000), ("National Stadium", "Karachi", "Pakistan", 34228),
    ("Newlands", "Cape Town", "South Africa", 25000), ("Wanderers Stadium", "Johannesburg", "South Africa", 34000),
    ("Eden Park", "Auckland", "New Zealand", 50000), ("Basin Reserve", "Wellington", "New Zealand", 11600),
    ("R. Premadasa Stadium", "Colombo", "Sri Lanka", 35000), ("Galle International Stadium", "Galle", "Sri Lanka", 35000),
    ("Sabina Park", "Kingston", "West Indies", 30000), ("Kensington Oval", "Bridgetown", "West Indies", 28000),
    ("Dubai International Stadium", "Dubai", "UAE", 25000),
]
FIRST = {
    "India": ["Aarav", "Vihaan", "Rohan", "Kabir", "Arjun", "Dev", "Ishan", "Kunal", "Nikhil", "Pranav", "Rahul", "Siddharth", "Tanay", "Yash", "Varun"],
    "Australia": ["Jack", "Liam", "Mitch", "Cooper", "Riley", "Hayden", "Tom", "Ben", "Callum", "Nathan", "Lachlan", "Ryan", "Josh", "Aiden", "Blake"],
    "England": ["Harry", "Oliver", "George", "Jamie", "Charlie", "Tommy", "Freddie", "Sam", "Alfie", "Ollie", "Will", "Ethan", "Archie", "Max", "Theo"],
    "Pakistan": ["Hamza", "Zain", "Faisal", "Imran", "Bilal", "Usman", "Danish", "Saad", "Kamran", "Naveed", "Rizwan", "Tariq", "Adnan", "Shoaib", "Waqas"],
    "South Africa": ["Johan", "Pieter", "Kobus", "Thabo", "Willem", "Dewald", "Ruan", "Hennie", "Sipho", "Gerrit", "Andre", "Keegan", "Morne", "Zander", "Brandon"],
    "New Zealand": ["Finn", "Hamish", "Callan", "Rhys", "Tane", "Aroha", "Josh", "Mason", "Kyle", "Ryder", "Jesse", "Logan", "Cameron", "Dane", "Noah"],
    "Sri Lanka": ["Kasun", "Dilan", "Nuwan", "Chamika", "Lahiru", "Pathum", "Dinesh", "Asitha", "Sachith", "Roshen", "Janith", "Maheesh", "Avishka", "Tharindu", "Kusal"],
    "West Indies": ["Kemar", "Jason", "Devon", "Shai", "Rovman", "Akeal", "Nicholas", "Brandon", "Keacy", "Obed", "Sheldon", "Alzarri", "Romario", "Kyle", "Darren"],
}
LAST = {
    "India": ["Kulkarni", "Iyer", "Mehra", "Rao", "Bhatt", "Chauhan", "Nair", "Sethi", "Verma", "Desai", "Menon", "Pillai", "Joshi", "Kapoor", "Banerjee"],
    "Australia": ["Fletcher", "Harper", "Mason", "Ellis", "Bryant", "Sutton", "Gibbs", "Carmody", "Whitlam", "Pearce", "Dunstan", "Hollis", "Rowe", "Stanton", "Quinn"],
    "England": ["Whitaker", "Bramley", "Hartley", "Cooper", "Ashworth", "Pemberton", "Lockwood", "Radcliffe", "Thornton", "Barlow", "Finch", "Marlow", "Sherwood", "Atkins", "Denholm"],
    "Pakistan": ["Qureshi", "Siddiqui", "Mirza", "Chaudhry", "Farooqi", "Abbasi", "Rana", "Baig", "Lodhi", "Sheikh", "Niazi", "Gillani", "Malik", "Zaidi", "Butt"],
    "South Africa": ["van Zyl", "Botha", "Mkhize", "du Plessis", "Nel", "Pretorius", "Ndlovu", "Steyn", "Coetzee", "Jordaan", "Visser", "Swanepoel", "Dlamini", "Meyer", "Fourie"],
    "New Zealand": ["Hargreaves", "Tamihana", "Walker", "McLeod", "Ngata", "Fraser", "Henare", "Duff", "Rutherford", "Parata", "Keogh", "Brough", "Tuhoe", "Larkin", "Moana"],
    "Sri Lanka": ["Perera", "Fernando", "Jayasuriya", "Wickramasinghe", "Gunawardena", "Senanayake", "Karunathilaka", "Dissanayake", "Rajapaksa", "Weerasinghe", "Samarawickrama", "Amarasinghe", "Bandara", "Silva", "Mendis"],
    "West Indies": ["Lawrence", "Brathwaite", "Holder", "Sealy", "Joseph", "Greaves", "Pinnock", "Edwards", "Clarke", "Walcott", "Marshall", "Gayle", "Bishop", "Haynes", "Roach"],
}
ROLE_PLAN = ["Batsman"] * 5 + ["Wicket-keeper"] + ["All-rounder"] * 3 + ["Bowler"] * 6
BAT_STYLES = ["Right-hand bat", "Left-hand bat"]
BOWL_STYLES = ["Right-arm fast", "Right-arm medium", "Left-arm fast", "Right-arm offbreak",
               "Left-arm orthodox", "Right-arm legbreak"]
TOTALS = {"Test": (240, 460), "ODI": (210, 350), "T20I": (125, 210)}
OVERS = {"Test": [[20, 20, 20, 15, 15], [22, 20, 18, 15, 15]],
         "ODI": [[10, 10, 10, 10, 10], [10, 10, 10, 8, 6, 6]],
         "T20I": [[4, 4, 4, 4, 4], [4, 4, 4, 4, 2, 2]]}
STRIKE = {"Test": 55, "ODI": 88, "T20I": 135}


def _split_total(rng, total, weights):
    """Split an integer total across batters in proportion to noisy weights."""
    noisy = [w * rng.expovariate(1.0) + 0.05 for w in weights]
    s = sum(noisy)
    parts = [int(total * n / s) for n in noisy]
    parts[0] += total - sum(parts)
    return parts


def seed(db_path=None, today=None, seed_value=7):
    rng = random.Random(seed_value)
    today = today or date.today()
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    team_ids = {}
    for name, (country, _) in TEAMS.items():
        cur.execute("INSERT INTO teams(team_name,country) VALUES(?,?)", (name, country))
        team_ids[name] = cur.lastrowid
    venue_ids, venues_by_country = {}, {}
    for name, city, country, cap in VENUES:
        cur.execute("INSERT INTO venues(venue_name,city,country,capacity) VALUES(?,?,?,?)", (name, city, country, cap))
        venue_ids[name] = cur.lastrowid
        venues_by_country.setdefault(country, []).append(venue_ids[name])

    squads = {}  # team -> list of dict
    for tname, (country, _) in TEAMS.items():
        used = set()
        squads[tname] = []
        for k, role in enumerate(ROLE_PLAN):
            while True:
                nm = f"{rng.choice(FIRST[country])} {rng.choice(LAST[country])}"
                if nm not in used:
                    used.add(nm)
                    break
            bowl = None if role in ("Batsman", "Wicket-keeper") and rng.random() < 0.9 else rng.choice(BOWL_STYLES)
            cur.execute(
                "INSERT INTO players(full_name,team_id,country,playing_role,batting_style,bowling_style) VALUES(?,?,?,?,?,?)",
                (nm, team_ids[tname], country, role, rng.choice(BAT_STYLES), bowl))
            skill = {"Batsman": 1.0, "Wicket-keeper": 0.8, "All-rounder": 0.65, "Bowler": 0.22}[role] * rng.uniform(0.8, 1.25)
            squads[tname].append({"id": cur.lastrowid, "role": role, "skill": skill,
                                  "drift": rng.uniform(-0.09, 0.09), "bowl": rng.uniform(0.85, 1.2)})

    # ---- series & matches ----
    names = list(TEAMS)
    start = date(2020, 1, 5)
    cursor_day = start
    series_rows, match_no = [], 0
    pair_cycle = []
    while cursor_day < today + timedelta(days=12):
        if not pair_cycle:
            pair_cycle = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]]
            rng.shuffle(pair_cycle)
        a, b = pair_cycle.pop()
        fmt = rng.choices(["Test", "ODI", "T20I"], weights=[3, 4, 5])[0]
        n = {"Test": rng.choice([2, 3]), "ODI": rng.choice([3, 3, 5]), "T20I": rng.choice([3, 3, 5])}[fmt]
        gap = {"Test": 6, "ODI": 3, "T20I": 2}[fmt]
        neutral = rng.random() < 0.12
        host, away = (a, b) if rng.random() < 0.5 else (b, a)
        host_country = "UAE" if neutral else TEAMS[host][0]
        cur.execute("INSERT INTO series(series_name,host_country,match_type,start_date,total_matches) VALUES(?,?,?,?,?)",
                    (f"{host} vs {away} {fmt} Series {cursor_day.year}", host_country, fmt, cursor_day.isoformat(), n))
        sid = cur.lastrowid
        for k in range(n):
            mdate = cursor_day + timedelta(days=k * gap)
            venue = rng.choice(venues_by_country[host_country])
            match_no += 1
            _make_match(cur, rng, squads, team_ids, sid, k + 1, fmt, host, away, venue, mdate, today)
        cursor_day += timedelta(days=n * gap + rng.randint(3, 8))

    _build_career_stats(cur)
    conn.commit()
    conn.close()
    return match_no


def _make_match(cur, rng, squads, team_ids, sid, num, fmt, t1, t2, venue_id, mdate, today):
    upcoming = mdate > today
    toss_winner = rng.choice([t1, t2])
    decision = rng.choice(["bat", "bowl"])
    bat_first = toss_winner if decision == "bat" else (t2 if toss_winner == t1 else t1)
    bat_second = t2 if bat_first == t1 else t1
    desc = f"{t1} vs {t2}, Match {num}"
    status = "Upcoming" if upcoming else "Completed"
    if upcoming:
        cur.execute(
            "INSERT INTO matches(series_id,description,match_format,team1_id,team2_id,venue_id,match_date,status) VALUES(?,?,?,?,?,?,?,?)",
            (sid, desc, fmt, team_ids[t1], team_ids[t2], venue_id, mdate.isoformat(), status))
        return
    s1, s2 = TEAMS[bat_first][1], TEAMS[bat_second][1]
    first_wins = rng.random() < s1 / (s1 + s2)
    lo, hi = TOTALS[fmt]
    total1 = rng.randint(lo, hi)
    if first_wins:
        margin = rng.randint(3, 140 if fmt != "T20I" else 70)
        total2 = max(30, total1 - margin)
        winner, vtype, w2 = bat_first, "runs", 10
    else:
        wk_left = rng.randint(2, 7)
        w2 = 10 - wk_left
        total2 = total1 + rng.randint(1, 8)
        margin, winner, vtype = wk_left, bat_second, "wickets"
    cur.execute(
        """INSERT INTO matches(series_id,description,match_format,team1_id,team2_id,venue_id,match_date,
           toss_winner_id,toss_decision,winner_id,victory_margin,victory_type,status)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (sid, desc, fmt, team_ids[t1], team_ids[t2], venue_id, mdate.isoformat(), team_ids[toss_winner],
         decision, team_ids[winner], margin, vtype, status))
    mid = cur.lastrowid
    years = (mdate - date(2020, 1, 1)).days / 365.0
    for ino, (bt, ft, total, wk) in enumerate([(bat_first, bat_second, total1, 10), (bat_second, bat_first, total2, w2)], 1):
        cur.execute("INSERT INTO innings(match_id,innings_no,batting_team_id) VALUES(?,?,?)", (mid, ino, team_ids[bt]))
        iid = cur.lastrowid
        _make_innings(cur, rng, squads, bt, ft, iid, fmt, total, wk, years)


def _pick_xi(rng, squad):
    pool = [p for p in squad if rng.random() < 0.93]
    by = lambda r: [p for p in pool if p["role"] == r]  # noqa: E731
    bats, wks, alls, bowls = by("Batsman"), by("Wicket-keeper"), by("All-rounder"), by("Bowler")
    rng.shuffle(bats), rng.shuffle(alls), rng.shuffle(bowls)
    xi = bats[:4] + wks[:1] + alls[:2] + bowls[:4]
    for p in squad:  # top up to 11
        if len(xi) >= 11:
            break
        if p not in xi:
            xi.append(p)
    order = {"Batsman": 0, "Wicket-keeper": 1, "All-rounder": 2, "Bowler": 3}
    return sorted(xi[:11], key=lambda p: order[p["role"]])


def _make_innings(cur, rng, squads, bat_team, field_team, iid, fmt, total, wickets, years):
    xi = _pick_xi(rng, squads[bat_team])
    n_bat = min(11, wickets + 1)
    batters = xi[:n_bat]
    weights = [max(0.05, p["skill"] * (1 + p["drift"] * years)) * (1.25 if k < 5 else 1.0) for k, p in enumerate(batters)]
    runs = _split_total(rng, total, weights)
    for k, (p, r) in enumerate(zip(batters, runs), 1):
        sr = STRIKE[fmt] * rng.uniform(0.7, 1.3) * (0.8 if p["role"] == "Bowler" else 1.0)
        balls = max(1, int(round(r * 100 / sr))) if r else rng.randint(1, 6)
        cur.execute(
            """INSERT INTO batting_performances(innings_id,player_id,batting_position,runs,balls_faced,fours,sixes,is_out)
               VALUES(?,?,?,?,?,?,?,?)""",
            (iid, p["id"], k, r, balls, r // 9, r // 30, 0 if k == n_bat else 1))
    # bowling & fielding by the fielding side
    fxi = _pick_xi(rng, squads[field_team])
    bowlers = sorted(fxi, key=lambda p: -(p["bowl"] * (1.5 if p["role"] == "Bowler" else 1.0 if p["role"] == "All-rounder" else 0.2)))
    plan = rng.choice(OVERS[fmt])
    bowlers = bowlers[:len(plan)]
    runs_split = _split_total(rng, total, [o * rng.uniform(0.7, 1.4) for o in plan])
    wk_split = [0] * len(plan)
    for _ in range(wickets):
        wk_split[rng.choices(range(len(plan)), weights=[o * b["bowl"] for o, b in zip(plan, bowlers)])[0]] += 1
    for p, o, rc, wk in zip(bowlers, plan, runs_split, wk_split):
        cur.execute("INSERT INTO bowling_performances(innings_id,player_id,overs,runs_conceded,wickets) VALUES(?,?,?,?,?)",
                    (iid, p["id"], float(o), rc, min(wk, 10)))
    catches, stumps = {}, {}
    keeper = next((p for p in fxi if p["role"] == "Wicket-keeper"), None)
    for _ in range(wickets):
        x = rng.random()
        if x < 0.62:
            f = rng.choice(fxi)
            catches[f["id"]] = catches.get(f["id"], 0) + 1
        elif x < 0.70 and keeper:
            stumps[keeper["id"]] = stumps.get(keeper["id"], 0) + 1
    for pid in set(catches) | set(stumps):
        cur.execute("INSERT INTO fielding_performances(innings_id,player_id,catches,stumpings) VALUES(?,?,?,?)",
                    (iid, pid, catches.get(pid, 0), stumps.get(pid, 0)))


def _build_career_stats(cur):
    cur.execute("DELETE FROM player_career_stats")
    cur.execute("""
        INSERT INTO player_career_stats(player_id,match_format,matches,runs,batting_avg,strike_rate,centuries,highest_score,wickets,bowling_avg,economy)
        SELECT p.player_id, m.match_format,
               COUNT(DISTINCT m.match_id),
               COALESCE(SUM(bp.runs),0),
               ROUND(SUM(bp.runs)*1.0/NULLIF(SUM(bp.is_out),0),2),
               ROUND(SUM(bp.runs)*100.0/NULLIF(SUM(bp.balls_faced),0),2),
               SUM(CASE WHEN bp.runs>=100 THEN 1 ELSE 0 END),
               COALESCE(MAX(bp.runs),0),
               COALESCE((SELECT SUM(bw.wickets) FROM bowling_performances bw JOIN innings i2 ON i2.innings_id=bw.innings_id
                         JOIN matches m2 ON m2.match_id=i2.match_id WHERE bw.player_id=p.player_id AND m2.match_format=m.match_format),0),
               (SELECT ROUND(SUM(bw.runs_conceded)*1.0/NULLIF(SUM(bw.wickets),0),2) FROM bowling_performances bw JOIN innings i2 ON i2.innings_id=bw.innings_id
                         JOIN matches m2 ON m2.match_id=i2.match_id WHERE bw.player_id=p.player_id AND m2.match_format=m.match_format),
               (SELECT ROUND(SUM(bw.runs_conceded)/NULLIF(SUM(bw.overs),0),2) FROM bowling_performances bw JOIN innings i2 ON i2.innings_id=bw.innings_id
                         JOIN matches m2 ON m2.match_id=i2.match_id WHERE bw.player_id=p.player_id AND m2.match_format=m.match_format)
        FROM players p
        JOIN batting_performances bp ON bp.player_id=p.player_id
        JOIN innings i ON i.innings_id=bp.innings_id
        JOIN matches m ON m.match_id=i.match_id
        GROUP BY p.player_id, m.match_format""")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="delete the existing database first")
    args = ap.parse_args()
    if args.reset and Path(config.DB_PATH).exists():
        Path(config.DB_PATH).unlink()
    print("Seeded matches:", seed())
