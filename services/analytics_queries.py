"""The 25 SQL practice questions. SQLite dialect (window functions need SQLite >= 3.25).

Each entry: id, level, title, task, concepts, parts=[(label, sql), ...].
Analytical notes for MySQL/PostgreSQL: replace date('now', ...) with CURRENT_DATE - INTERVAL,
strftime with EXTRACT/DATE_FORMAT, and the SQRT-based variance with STDDEV_POP.
"""

Q = []


def add(qid, level, title, task, concepts, parts):
    Q.append({"id": qid, "level": level, "title": title, "task": task, "concepts": concepts,
              "parts": parts if isinstance(parts, list) else [("Result", parts)]})


# ------------------------------------------------------------------ Beginner
add(1, "Beginner", "Players who represent India",
    "Full name, playing role, batting style and bowling style for every Indian player.",
    "SELECT, WHERE, ORDER BY",
    """SELECT full_name, playing_role, batting_style, bowling_style
FROM players
WHERE country = 'India'
ORDER BY full_name""")

add(2, "Beginner", "Matches in the last 30 days",
    "Description, both teams, venue with city and date, most recent first.",
    "View join, date arithmetic, ORDER BY",
    """SELECT description, team1, team2, venue_name || ', ' || city AS venue, match_date
FROM v_match_details
WHERE status = 'Completed'
  AND match_date BETWEEN date('now', '-30 day') AND date('now')
ORDER BY match_date DESC, match_id DESC""")

add(3, "Beginner", "Top 10 ODI run scorers",
    "Player, total runs, batting average and centuries; highest scorer first.",
    "JOIN, ORDER BY, LIMIT",
    """SELECT p.full_name, s.runs AS total_runs, s.batting_avg, s.centuries
FROM player_career_stats s
JOIN players p ON p.player_id = s.player_id
WHERE s.match_format = 'ODI'
ORDER BY s.runs DESC
LIMIT 10""")

add(4, "Beginner", "Venues with capacity above 50,000",
    "Venue, city, country and capacity, largest first.",
    "WHERE with numeric filter",
    """SELECT venue_name, city, country, capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC""")

add(5, "Beginner", "Wins per team",
    "Team name and total wins, most wins first.",
    "JOIN, GROUP BY, COUNT",
    """SELECT t.team_name, COUNT(*) AS total_wins
FROM matches m
JOIN teams t ON t.team_id = m.winner_id
GROUP BY t.team_id, t.team_name
ORDER BY total_wins DESC, t.team_name""")

add(6, "Beginner", "Players per playing role",
    "Count of players for each playing role.",
    "GROUP BY, COUNT",
    """SELECT playing_role, COUNT(*) AS player_count
FROM players
GROUP BY playing_role
ORDER BY player_count DESC""")

add(7, "Beginner", "Highest individual score per format",
    "Highest batting score in Test, ODI and T20I.",
    "MAX, GROUP BY on a view",
    """SELECT match_format, MAX(runs) AS highest_score
FROM v_batting
GROUP BY match_format
ORDER BY CASE match_format WHEN 'Test' THEN 1 WHEN 'ODI' THEN 2 ELSE 3 END""")

add(8, "Beginner", "Series that started in 2024",
    "Series name, host country, match type, start date and planned matches.",
    "Date functions, WHERE",
    """SELECT series_name, host_country, match_type, start_date, total_matches
FROM series
WHERE strftime('%Y', start_date) = '2024'
ORDER BY start_date""")

# -------------------------------------------------------------- Intermediate
add(9, "Intermediate", "All-rounders with 1000+ runs and 50+ wickets",
    "Career runs and wickets (summed over formats) above both thresholds, with the formats played.",
    "GROUP BY, HAVING on two aggregates, GROUP_CONCAT",
    """SELECT p.full_name,
       SUM(s.runs) AS total_runs,
       SUM(s.wickets) AS total_wickets,
       GROUP_CONCAT(s.match_format, ', ') AS formats
FROM player_career_stats s
JOIN players p ON p.player_id = s.player_id
WHERE p.playing_role = 'All-rounder'
GROUP BY p.player_id, p.full_name
HAVING SUM(s.runs) > 1000 AND SUM(s.wickets) > 50
ORDER BY total_runs DESC""")

add(10, "Intermediate", "Last 20 completed matches",
    "Description, teams, winner, margin, victory type and venue; newest first.",
    "View, LIMIT, NULL filtering",
    """SELECT description, team1, team2, winner, victory_margin, victory_type, venue_name
FROM v_match_details
WHERE status = 'Completed' AND winner_id IS NOT NULL
ORDER BY match_date DESC, match_id DESC
LIMIT 20""")

add(11, "Intermediate", "Performance across formats",
    "For players with 2+ formats: runs per format and overall batting average.",
    "Conditional aggregation, HAVING",
    """SELECT full_name,
       SUM(CASE WHEN match_format = 'Test' THEN runs END) AS test_runs,
       SUM(CASE WHEN match_format = 'ODI'  THEN runs END) AS odi_runs,
       SUM(CASE WHEN match_format = 'T20I' THEN runs END) AS t20i_runs,
       ROUND(SUM(runs) * 1.0 / NULLIF(SUM(is_out), 0), 2) AS overall_batting_avg
FROM v_batting
GROUP BY player_id, full_name
HAVING COUNT(DISTINCT match_format) >= 2
ORDER BY overall_batting_avg DESC""")

add(12, "Intermediate", "Home vs away wins",
    "Wins at home (venue country = team country) and away for each team.",
    "UNION ALL, CASE, derived table",
    """WITH team_matches AS (
    SELECT team1_id AS team_id, venue_country, winner_id FROM v_match_details WHERE status = 'Completed'
    UNION ALL
    SELECT team2_id, venue_country, winner_id FROM v_match_details WHERE status = 'Completed'
)
SELECT t.team_name,
       SUM(CASE WHEN tm.venue_country =  t.country AND tm.winner_id = tm.team_id THEN 1 ELSE 0 END) AS home_wins,
       SUM(CASE WHEN tm.venue_country <> t.country AND tm.winner_id = tm.team_id THEN 1 ELSE 0 END) AS away_wins,
       SUM(CASE WHEN tm.venue_country =  t.country THEN 1 ELSE 0 END) AS home_matches,
       SUM(CASE WHEN tm.venue_country <> t.country THEN 1 ELSE 0 END) AS away_matches
FROM team_matches tm
JOIN teams t ON t.team_id = tm.team_id
GROUP BY t.team_id, t.team_name
ORDER BY home_wins + away_wins DESC""")

add(13, "Intermediate", "Partnerships of 100+ (adjacent batters)",
    "Two consecutive batters whose combined runs in an innings reach 100.",
    "Self join on batting position",
    """SELECT a.full_name AS batter_1, b.full_name AS batter_2,
       a.runs + b.runs AS partnership_runs,
       m.description || ' (innings ' || a.innings_no || ')' AS innings,
       m.match_date
FROM v_batting a
JOIN v_batting b ON b.innings_id = a.innings_id AND b.batting_position = a.batting_position + 1
JOIN matches m ON m.match_id = a.match_id
WHERE a.runs + b.runs >= 100
ORDER BY partnership_runs DESC
LIMIT 100""")

add(14, "Intermediate", "Bowling at venues (3+ matches, 4+ overs each)",
    "Average economy, wickets and matches per bowler per venue.",
    "Filter before GROUP BY, HAVING",
    """SELECT bw.full_name, v.venue_name,
       ROUND(AVG(bw.economy), 2) AS avg_economy,
       SUM(bw.wickets) AS total_wickets,
       COUNT(DISTINCT bw.match_id) AS matches_played
FROM v_bowling bw
JOIN venues v ON v.venue_id = bw.venue_id
WHERE bw.overs >= 4
GROUP BY bw.player_id, bw.full_name, bw.venue_id, v.venue_name
HAVING COUNT(DISTINCT bw.match_id) >= 3
ORDER BY avg_economy
LIMIT 100""")

add(15, "Intermediate", "Players in close matches",
    "Close = won by <50 runs or <5 wickets. Avg runs, close matches played, and team wins when batting.",
    "Multi-table join, conditional SUM",
    """SELECT p.full_name,
       ROUND(AVG(bp.runs), 2) AS avg_runs,
       COUNT(DISTINCT m.match_id) AS close_matches_played,
       COUNT(DISTINCT CASE WHEN i.batting_team_id = m.winner_id THEN m.match_id END) AS close_matches_won
FROM batting_performances bp
JOIN innings i ON i.innings_id = bp.innings_id
JOIN matches m ON m.match_id = i.match_id
JOIN players p ON p.player_id = bp.player_id
WHERE (m.victory_type = 'runs' AND m.victory_margin < 50)
   OR (m.victory_type = 'wickets' AND m.victory_margin < 5)
GROUP BY p.player_id, p.full_name
ORDER BY avg_runs DESC
LIMIT 100""")

add(16, "Intermediate", "Batting by year since 2020",
    "Average runs per match and average strike rate per player-year (5+ matches).",
    "strftime, GROUP BY two keys, HAVING",
    """SELECT full_name, strftime('%Y', match_date) AS year,
       ROUND(SUM(runs) * 1.0 / COUNT(DISTINCT match_id), 2) AS avg_runs_per_match,
       ROUND(AVG(strike_rate), 2) AS avg_strike_rate,
       COUNT(DISTINCT match_id) AS matches
FROM v_batting
WHERE match_date >= '2020-01-01' AND match_date <= date('now')
GROUP BY player_id, full_name, strftime('%Y', match_date)
HAVING COUNT(DISTINCT match_id) >= 5
ORDER BY full_name, year""")

# ------------------------------------------------------------------ Advanced
add(17, "Advanced", "Does winning the toss help?",
    "% of matches won by the toss winner, split by toss decision.",
    "CASE, ratio of counts, UNION ALL for an overall row",
    """SELECT toss_decision,
       COUNT(*) AS matches,
       SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END) AS won_after_toss,
       ROUND(100.0 * SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END) / COUNT(*), 2) AS win_pct
FROM matches
WHERE winner_id IS NOT NULL AND toss_winner_id IS NOT NULL
GROUP BY toss_decision
UNION ALL
SELECT 'overall', COUNT(*),
       SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END),
       ROUND(100.0 * SUM(CASE WHEN toss_winner_id = winner_id THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM matches
WHERE winner_id IS NOT NULL AND toss_winner_id IS NOT NULL""")

add(18, "Advanced", "Most economical limited-overs bowlers",
    "ODI + T20I; 10+ matches and 2+ overs per match on average.",
    "Weighted ratio (SUM/SUM), HAVING with expression",
    """SELECT full_name,
       ROUND(SUM(runs_conceded) * 1.0 / SUM(overs), 2) AS economy_rate,
       SUM(wickets) AS total_wickets,
       COUNT(DISTINCT match_id) AS matches,
       ROUND(SUM(overs) / COUNT(DISTINCT match_id), 2) AS avg_overs_per_match
FROM v_bowling
WHERE match_format IN ('ODI', 'T20I')
GROUP BY player_id, full_name
HAVING COUNT(DISTINCT match_id) >= 10 AND SUM(overs) / COUNT(DISTINCT match_id) >= 2
ORDER BY economy_rate
LIMIT 25""")

add(19, "Advanced", "Most consistent batters (since 2022)",
    "Average and standard deviation of runs; 10+ balls faced per counted innings.",
    "Population std-dev from AVG(x*x) - AVG(x)^2",
    """WITH base AS (
    SELECT player_id, full_name, runs FROM v_batting
    WHERE match_date >= '2022-01-01' AND match_date <= date('now') AND balls_faced >= 10
)
SELECT full_name,
       COUNT(*) AS innings,
       ROUND(AVG(runs), 2) AS avg_runs,
       ROUND(SQRT(AVG(runs * runs * 1.0) - AVG(runs) * AVG(runs)), 2) AS std_dev_runs
FROM base
GROUP BY player_id, full_name
HAVING COUNT(*) >= 10
ORDER BY std_dev_runs
LIMIT 25""")

add(20, "Advanced", "Matches and batting average per format",
    "Test/ODI/T20 match counts and averages for players with 20+ matches in total.",
    "COUNT(DISTINCT CASE ...), conditional ratios",
    """SELECT full_name,
       COUNT(DISTINCT CASE WHEN match_format = 'Test' THEN match_id END) AS test_matches,
       COUNT(DISTINCT CASE WHEN match_format = 'ODI'  THEN match_id END) AS odi_matches,
       COUNT(DISTINCT CASE WHEN match_format = 'T20I' THEN match_id END) AS t20_matches,
       ROUND(SUM(CASE WHEN match_format = 'Test' THEN runs END) * 1.0 / NULLIF(SUM(CASE WHEN match_format = 'Test' THEN is_out END), 0), 2) AS test_avg,
       ROUND(SUM(CASE WHEN match_format = 'ODI'  THEN runs END) * 1.0 / NULLIF(SUM(CASE WHEN match_format = 'ODI'  THEN is_out END), 0), 2) AS odi_avg,
       ROUND(SUM(CASE WHEN match_format = 'T20I' THEN runs END) * 1.0 / NULLIF(SUM(CASE WHEN match_format = 'T20I' THEN is_out END), 0), 2) AS t20_avg
FROM v_batting
GROUP BY player_id, full_name
HAVING COUNT(DISTINCT match_id) >= 20
ORDER BY full_name""")

add(21, "Advanced", "Weighted player ranking by format",
    "Batting + bowling + fielding points; top 5 per format.",
    "CTEs, LEFT JOINs, COALESCE, ROW_NUMBER() OVER (PARTITION BY ...)",
    """WITH bat AS (
    SELECT player_id, match_format, SUM(runs) AS runs,
           SUM(runs) * 1.0 / NULLIF(SUM(is_out), 0) AS bat_avg,
           SUM(runs) * 100.0 / NULLIF(SUM(balls_faced), 0) AS sr
    FROM v_batting GROUP BY player_id, match_format
), bowl AS (
    SELECT player_id, match_format, SUM(wickets) AS wkts,
           SUM(runs_conceded) * 1.0 / NULLIF(SUM(wickets), 0) AS bowl_avg,
           SUM(runs_conceded) * 1.0 / NULLIF(SUM(overs), 0) AS econ
    FROM v_bowling GROUP BY player_id, match_format
), field AS (
    SELECT f.player_id, m.match_format, SUM(f.catches) AS catches, SUM(f.stumpings) AS stumpings
    FROM fielding_performances f
    JOIN innings i ON i.innings_id = f.innings_id
    JOIN matches m ON m.match_id = i.match_id
    GROUP BY f.player_id, m.match_format
), scored AS (
    SELECT p.full_name, bat.match_format,
           COALESCE(bat.runs,0) * 0.01 + COALESCE(bat.bat_avg,0) * 0.5 + COALESCE(bat.sr,0) * 0.3 AS batting_points,
           COALESCE(bowl.wkts,0) * 2 + (50 - COALESCE(bowl.bowl_avg,50)) * 0.5 + (6 - COALESCE(bowl.econ,6)) * 2 AS bowling_points,
           COALESCE(field.catches,0) * 3 + COALESCE(field.stumpings,0) * 5 AS fielding_points
    FROM bat
    JOIN players p ON p.player_id = bat.player_id
    LEFT JOIN bowl  ON bowl.player_id  = bat.player_id AND bowl.match_format  = bat.match_format
    LEFT JOIN field ON field.player_id = bat.player_id AND field.match_format = bat.match_format
), ranked AS (
    SELECT *, batting_points + bowling_points + fielding_points AS total_points,
           ROW_NUMBER() OVER (PARTITION BY match_format ORDER BY batting_points + bowling_points + fielding_points DESC) AS rank_in_format
    FROM scored
)
SELECT match_format, rank_in_format, full_name,
       ROUND(batting_points, 1) AS batting_points, ROUND(bowling_points, 1) AS bowling_points,
       fielding_points, ROUND(total_points, 1) AS total_points
FROM ranked
WHERE rank_in_format <= 5
ORDER BY match_format, rank_in_format""")

_H2H_BASE = """WITH finished AS (
    SELECT match_id, venue_id, winner_id, victory_margin, victory_type,
           MIN(team1_id, team2_id) AS team_a, MAX(team1_id, team2_id) AS team_b
    FROM matches
    WHERE status = 'Completed' AND winner_id IS NOT NULL AND match_date >= date('now', '-3 year')
), pairs AS (
    SELECT team_a, team_b FROM finished GROUP BY team_a, team_b HAVING COUNT(*) >= 5
)"""

add(22, "Advanced", "Head-to-head prediction analysis (last 3 years)",
    "Pairs with 5+ meetings: wins, win %, average margins, and bat-first vs bowl-first by venue.",
    "CTE chain, MIN/MAX pair normalisation, conditional AVG",
    [("Head-to-head summary", _H2H_BASE + """
SELECT ta.team_name AS team_a, tb.team_name AS team_b, COUNT(*) AS matches,
       SUM(CASE WHEN f.winner_id = f.team_a THEN 1 ELSE 0 END) AS wins_a,
       SUM(CASE WHEN f.winner_id = f.team_b THEN 1 ELSE 0 END) AS wins_b,
       ROUND(100.0 * SUM(CASE WHEN f.winner_id = f.team_a THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_pct_a,
       ROUND(100.0 * SUM(CASE WHEN f.winner_id = f.team_b THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_pct_b,
       ROUND(AVG(CASE WHEN f.winner_id = f.team_a AND f.victory_type = 'runs'    THEN f.victory_margin END), 1) AS a_avg_run_margin,
       ROUND(AVG(CASE WHEN f.winner_id = f.team_a AND f.victory_type = 'wickets' THEN f.victory_margin END), 1) AS a_avg_wkt_margin,
       ROUND(AVG(CASE WHEN f.winner_id = f.team_b AND f.victory_type = 'runs'    THEN f.victory_margin END), 1) AS b_avg_run_margin,
       ROUND(AVG(CASE WHEN f.winner_id = f.team_b AND f.victory_type = 'wickets' THEN f.victory_margin END), 1) AS b_avg_wkt_margin
FROM (SELECT mm.match_id, mm.winner_id, mm.victory_margin, mm.victory_type,
             MIN(mm.team1_id, mm.team2_id) AS team_a, MAX(mm.team1_id, mm.team2_id) AS team_b
      FROM matches mm
      WHERE mm.status = 'Completed' AND mm.winner_id IS NOT NULL AND mm.match_date >= date('now', '-3 year')) f
JOIN (SELECT team_a, team_b FROM (SELECT MIN(team1_id, team2_id) AS team_a, MAX(team1_id, team2_id) AS team_b
                                   FROM matches WHERE status = 'Completed' AND winner_id IS NOT NULL
                                     AND match_date >= date('now', '-3 year')
                                   GROUP BY 1, 2 HAVING COUNT(*) >= 5)) p
  ON p.team_a = f.team_a AND p.team_b = f.team_b
JOIN teams ta ON ta.team_id = f.team_a
JOIN teams tb ON tb.team_id = f.team_b
GROUP BY f.team_a, f.team_b
ORDER BY matches DESC, team_a"""),
     ("Bat first vs bowl first by venue", _H2H_BASE + """
SELECT ta.team_name AS team_a, tb.team_name AS team_b, v.venue_name,
       COUNT(*) AS matches,
       SUM(CASE WHEN i.batting_team_id = f.winner_id THEN 1 ELSE 0 END) AS batting_first_wins,
       SUM(CASE WHEN i.batting_team_id <> f.winner_id THEN 1 ELSE 0 END) AS bowling_first_wins
FROM finished f
JOIN pairs p ON p.team_a = f.team_a AND p.team_b = f.team_b
JOIN innings i ON i.match_id = f.match_id AND i.innings_no = 1
JOIN venues v ON v.venue_id = f.venue_id
JOIN teams ta ON ta.team_id = f.team_a
JOIN teams tb ON tb.team_id = f.team_b
GROUP BY f.team_a, f.team_b, f.venue_id, v.venue_name
ORDER BY team_a, team_b, matches DESC""")])

add(23, "Advanced", "Recent form and momentum",
    "Last 10 innings per player: last-5 vs last-10 average, strike-rate trend, 50+ scores, consistency, form label.",
    "ROW_NUMBER() newest-first, conditional aggregates, CASE classification",
    """WITH recent AS (
    SELECT player_id, full_name, runs, strike_rate,
           ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY match_date DESC, match_id DESC) AS rn
    FROM v_batting
), last10 AS (SELECT * FROM recent WHERE rn <= 10), stats AS (
    SELECT player_id, full_name,
           COUNT(*) AS innings,
           AVG(CASE WHEN rn <= 5 THEN runs END) AS avg_last5,
           AVG(runs) AS avg_last10,
           AVG(CASE WHEN rn <= 5 THEN strike_rate END) AS sr_last5,
           AVG(CASE WHEN rn >  5 THEN strike_rate END) AS sr_prev5,
           SUM(CASE WHEN runs >= 50 THEN 1 ELSE 0 END) AS scores_50_plus,
           SQRT(AVG(runs * runs * 1.0) - AVG(runs) * AVG(runs)) AS std_dev
    FROM last10 GROUP BY player_id, full_name HAVING COUNT(*) = 10
)
SELECT full_name,
       ROUND(avg_last5, 1) AS avg_last5, ROUND(avg_last10, 1) AS avg_last10,
       ROUND(sr_last5 - sr_prev5, 1) AS strike_rate_change,
       scores_50_plus,
       ROUND(std_dev, 1) AS consistency_std_dev,
       CASE WHEN avg_last5 >= 40 AND scores_50_plus >= 3 THEN 'Excellent Form'
            WHEN avg_last10 >= 28 THEN 'Good Form'
            WHEN avg_last10 >= 18 THEN 'Average Form'
            ELSE 'Poor Form' END AS form
FROM stats
ORDER BY avg_last5 DESC""")

add(24, "Advanced", "Best batting partnerships",
    "Pairs batting at adjacent positions in 5+ partnerships: average, 50+ count, best, success rate.",
    "Self join, pair normalisation with MIN/MAX, conditional counts",
    """WITH partnerships AS (
    SELECT MIN(a.player_id, b.player_id) AS p1, MAX(a.player_id, b.player_id) AS p2,
           a.runs + b.runs AS runs
    FROM v_batting a
    JOIN v_batting b ON b.innings_id = a.innings_id AND b.batting_position = a.batting_position + 1
)
SELECT pl1.full_name AS player_1, pl2.full_name AS player_2,
       COUNT(*) AS partnerships,
       ROUND(AVG(runs), 1) AS avg_partnership,
       SUM(CASE WHEN runs > 50 THEN 1 ELSE 0 END) AS over_50,
       MAX(runs) AS highest,
       ROUND(100.0 * SUM(CASE WHEN runs > 50 THEN 1 ELSE 0 END) / COUNT(*), 1) AS success_rate_pct
FROM partnerships pt
JOIN players pl1 ON pl1.player_id = pt.p1
JOIN players pl2 ON pl2.player_id = pt.p2
GROUP BY p1, p2
HAVING COUNT(*) >= 5
ORDER BY success_rate_pct DESC, avg_partnership DESC
LIMIT 25""")

_QTR = """WITH q AS (
    SELECT player_id, full_name,
           strftime('%Y', match_date) || '-Q' || ((CAST(strftime('%m', match_date) AS INTEGER) + 2) / 3) AS quarter,
           COUNT(DISTINCT match_id) AS matches,
           AVG(runs) AS avg_runs, AVG(strike_rate) AS avg_sr
    FROM v_batting
    WHERE match_date <= date('now')
    GROUP BY player_id, full_name, quarter
    HAVING COUNT(DISTINCT match_id) >= 3
), eligible AS (
    SELECT player_id FROM q GROUP BY player_id HAVING COUNT(*) >= 6
), tl AS (
    SELECT q.*, LAG(avg_runs) OVER (PARTITION BY q.player_id ORDER BY quarter) AS prev_runs,
           LAG(avg_sr)   OVER (PARTITION BY q.player_id ORDER BY quarter) AS prev_sr,
           ROW_NUMBER() OVER (PARTITION BY q.player_id ORDER BY quarter) AS qn,
           COUNT(*)     OVER (PARTITION BY q.player_id) AS total_q
    FROM q JOIN eligible e ON e.player_id = q.player_id
)"""

add(25, "Advanced", "Quarterly performance evolution",
    "Quarterly averages, quarter-on-quarter change, trend, and career phase (6+ quarters, 3+ matches each).",
    "LAG(), window COUNT, CTE chain, CASE classification",
    [("Quarter-by-quarter trend", _QTR + """
SELECT full_name, quarter, matches, ROUND(avg_runs, 1) AS avg_runs, ROUND(avg_sr, 1) AS avg_strike_rate,
       ROUND(avg_runs - prev_runs, 1) AS runs_change,
       CASE WHEN prev_runs IS NULL THEN 'first quarter'
            WHEN avg_runs > prev_runs * 1.10 THEN 'Improving'
            WHEN avg_runs < prev_runs * 0.90 THEN 'Declining'
            ELSE 'Stable' END AS trend
FROM tl
ORDER BY full_name, quarter
LIMIT 300"""),
     ("Career phase", _QTR + """
SELECT full_name, total_q AS quarters,
       ROUND(AVG(CASE WHEN qn <= 3 THEN avg_runs END), 1) AS first_3_avg,
       ROUND(AVG(CASE WHEN qn > total_q - 3 THEN avg_runs END), 1) AS last_3_avg,
       CASE WHEN AVG(CASE WHEN qn > total_q - 3 THEN avg_runs END) > AVG(CASE WHEN qn <= 3 THEN avg_runs END) * 1.10 THEN 'Career Ascending'
            WHEN AVG(CASE WHEN qn > total_q - 3 THEN avg_runs END) < AVG(CASE WHEN qn <= 3 THEN avg_runs END) * 0.90 THEN 'Career Declining'
            ELSE 'Career Stable' END AS career_phase
FROM tl
GROUP BY player_id, full_name, total_q
ORDER BY last_3_avg DESC""")])
