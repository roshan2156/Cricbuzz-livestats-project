-- Cricbuzz LiveStats schema (3NF). SQLite dialect; types map cleanly to MySQL/PostgreSQL.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    team_id     INTEGER PRIMARY KEY,
    team_name   TEXT NOT NULL UNIQUE,
    country     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id    INTEGER PRIMARY KEY,
    venue_name  TEXT NOT NULL,
    city        TEXT NOT NULL,
    country     TEXT NOT NULL,
    capacity    INTEGER CHECK (capacity IS NULL OR capacity > 0),
    UNIQUE (venue_name, city)
);

CREATE TABLE IF NOT EXISTS players (
    player_id      INTEGER PRIMARY KEY,
    full_name      TEXT NOT NULL,
    team_id        INTEGER REFERENCES teams(team_id) ON DELETE SET NULL,
    country        TEXT NOT NULL,
    playing_role   TEXT NOT NULL CHECK (playing_role IN ('Batsman','Bowler','All-rounder','Wicket-keeper')),
    batting_style  TEXT,
    bowling_style  TEXT,
    UNIQUE (full_name, country)
);

CREATE TABLE IF NOT EXISTS series (
    series_id    INTEGER PRIMARY KEY,
    series_name  TEXT NOT NULL,
    host_country TEXT NOT NULL,
    match_type   TEXT NOT NULL CHECK (match_type IN ('Test','ODI','T20I')),
    start_date   TEXT NOT NULL,
    total_matches INTEGER NOT NULL CHECK (total_matches > 0)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id      INTEGER PRIMARY KEY,
    series_id     INTEGER REFERENCES series(series_id) ON DELETE SET NULL,
    description   TEXT NOT NULL,
    match_format  TEXT NOT NULL CHECK (match_format IN ('Test','ODI','T20I')),
    team1_id      INTEGER NOT NULL REFERENCES teams(team_id),
    team2_id      INTEGER NOT NULL REFERENCES teams(team_id),
    venue_id      INTEGER NOT NULL REFERENCES venues(venue_id),
    match_date    TEXT NOT NULL,
    toss_winner_id INTEGER REFERENCES teams(team_id),
    toss_decision  TEXT CHECK (toss_decision IN ('bat','bowl')),
    winner_id      INTEGER REFERENCES teams(team_id),
    victory_margin INTEGER,
    victory_type   TEXT CHECK (victory_type IN ('runs','wickets')),
    status         TEXT NOT NULL DEFAULT 'Completed',
    CHECK (team1_id <> team2_id)
);

CREATE TABLE IF NOT EXISTS innings (
    innings_id    INTEGER PRIMARY KEY,
    match_id      INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    innings_no    INTEGER NOT NULL CHECK (innings_no BETWEEN 1 AND 4),
    batting_team_id INTEGER NOT NULL REFERENCES teams(team_id),
    UNIQUE (match_id, innings_no)
);

CREATE TABLE IF NOT EXISTS batting_performances (
    perf_id     INTEGER PRIMARY KEY,
    innings_id  INTEGER NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id   INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    batting_position INTEGER NOT NULL CHECK (batting_position BETWEEN 1 AND 11),
    runs        INTEGER NOT NULL CHECK (runs >= 0),
    balls_faced INTEGER NOT NULL CHECK (balls_faced >= 0),
    fours       INTEGER NOT NULL DEFAULT 0,
    sixes       INTEGER NOT NULL DEFAULT 0,
    is_out      INTEGER NOT NULL DEFAULT 1 CHECK (is_out IN (0,1)),
    UNIQUE (innings_id, player_id),
    UNIQUE (innings_id, batting_position)
);

CREATE TABLE IF NOT EXISTS bowling_performances (
    perf_id     INTEGER PRIMARY KEY,
    innings_id  INTEGER NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id   INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    overs       REAL NOT NULL CHECK (overs >= 0),
    runs_conceded INTEGER NOT NULL CHECK (runs_conceded >= 0),
    wickets     INTEGER NOT NULL CHECK (wickets BETWEEN 0 AND 10),
    UNIQUE (innings_id, player_id)
);

CREATE TABLE IF NOT EXISTS fielding_performances (
    perf_id     INTEGER PRIMARY KEY,
    innings_id  INTEGER NOT NULL REFERENCES innings(innings_id) ON DELETE CASCADE,
    player_id   INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    catches     INTEGER NOT NULL DEFAULT 0 CHECK (catches >= 0),
    stumpings   INTEGER NOT NULL DEFAULT 0 CHECK (stumpings >= 0),
    UNIQUE (innings_id, player_id)
);

-- Career aggregates per player per format (what the Cricbuzz stats endpoints return).
CREATE TABLE IF NOT EXISTS player_career_stats (
    player_id    INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    match_format TEXT NOT NULL CHECK (match_format IN ('Test','ODI','T20I')),
    matches      INTEGER NOT NULL DEFAULT 0,
    runs         INTEGER NOT NULL DEFAULT 0,
    batting_avg  REAL,
    strike_rate  REAL,
    centuries    INTEGER NOT NULL DEFAULT 0,
    highest_score INTEGER NOT NULL DEFAULT 0,
    wickets      INTEGER NOT NULL DEFAULT 0,
    bowling_avg  REAL,
    economy      REAL,
    PRIMARY KEY (player_id, match_format)
);

CREATE INDEX IF NOT EXISTS idx_matches_date    ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_venue   ON matches(venue_id);
CREATE INDEX IF NOT EXISTS idx_matches_winner  ON matches(winner_id);
CREATE INDEX IF NOT EXISTS idx_innings_match   ON innings(match_id);
CREATE INDEX IF NOT EXISTS idx_bat_player      ON batting_performances(player_id);
CREATE INDEX IF NOT EXISTS idx_bat_innings     ON batting_performances(innings_id);
CREATE INDEX IF NOT EXISTS idx_bowl_player     ON bowling_performances(player_id);
CREATE INDEX IF NOT EXISTS idx_players_country ON players(country);
CREATE INDEX IF NOT EXISTS idx_players_role    ON players(playing_role);
CREATE INDEX IF NOT EXISTS idx_series_start    ON series(start_date);
