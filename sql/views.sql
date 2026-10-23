-- Reusable views over the normalised tables.
DROP VIEW IF EXISTS v_match_details;
CREATE VIEW v_match_details AS
SELECT m.match_id, m.description, m.match_format, m.match_date, m.status,
       t1.team_name AS team1, t2.team_name AS team2,
       t1.country AS team1_country, t2.country AS team2_country,
       v.venue_name, v.city, v.country AS venue_country,
       w.team_name AS winner, m.victory_margin, m.victory_type,
       m.toss_winner_id, m.toss_decision, m.winner_id, m.team1_id, m.team2_id, m.venue_id
FROM matches m
JOIN teams  t1 ON t1.team_id = m.team1_id
JOIN teams  t2 ON t2.team_id = m.team2_id
JOIN venues v  ON v.venue_id = m.venue_id
LEFT JOIN teams w ON w.team_id = m.winner_id;

DROP VIEW IF EXISTS v_batting;
CREATE VIEW v_batting AS
SELECT bp.perf_id, bp.player_id, p.full_name, i.match_id, i.innings_id, i.innings_no,
       i.batting_team_id, bp.batting_position, bp.runs, bp.balls_faced, bp.is_out,
       m.match_date, m.match_format,
       CASE WHEN bp.balls_faced > 0 THEN bp.runs * 100.0 / bp.balls_faced END AS strike_rate
FROM batting_performances bp
JOIN innings i ON i.innings_id = bp.innings_id
JOIN matches m ON m.match_id = i.match_id
JOIN players p ON p.player_id = bp.player_id;

DROP VIEW IF EXISTS v_bowling;
CREATE VIEW v_bowling AS
SELECT bw.perf_id, bw.player_id, p.full_name, i.match_id, m.venue_id, m.match_format,
       m.match_date, bw.overs, bw.runs_conceded, bw.wickets,
       CASE WHEN bw.overs > 0 THEN bw.runs_conceded / bw.overs END AS economy
FROM bowling_performances bw
JOIN innings i ON i.innings_id = bw.innings_id
JOIN matches m ON m.match_id = i.match_id
JOIN players p ON p.player_id = bw.player_id;
