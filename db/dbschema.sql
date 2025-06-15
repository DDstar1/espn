PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Tracker (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1), 
    latest_scraped_team_url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Player (
    espn_id INTEGER PRIMARY KEY,
    Name TEXT NOT NULL,
    DOB REAL,
    Nationality TEXT,
    Height REAL,
    Weight REAL
);

CREATE TABLE IF NOT EXISTS Team (
    espn_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    logo TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Game_Info (
    espn_id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    referee TEXT NOT NULL,
    place TEXT NOT NULL,
    state TEXT NOT NULL,
    country TEXT NOT NULL,
    commentary TEXT NOT NULL,
    attendance INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS Team_Game_History (
    id INTEGER PRIMARY KEY,
    espn_team_id INTEGER NOT NULL,
    espn_game_info_id INTEGER NOT NULL,
    formation TEXT DEFAULT NULL,
    goals INTEGER NOT NULL,
    FOREIGN KEY (espn_team_id) REFERENCES Team(espn_id),
    FOREIGN KEY (espn_game_info_id) REFERENCES Game_Info(espn_id),
    UNIQUE (espn_team_id, espn_game_info_id)
);

CREATE TABLE IF NOT EXISTS Line_Up_Statistics (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    espn_player_id INTEGER NOT NULL,
    player_num INTEGER ,
    position_x INTEGER ,
    position_y INTEGER ,
    goals INTEGER ,
    saves INTEGER ,
    shots INTEGER ,
    shots_on_target INTEGER ,
    fouls_commited INTEGER ,
    fouls_against INTEGER ,
    assists INTEGER ,
    offsides INTEGER ,
    yellow_cards INTEGER ,
    red_cards INTEGER ,
    unused_player INTEGER ,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (espn_player_id) REFERENCES Player(espn_id)
    UNIQUE (team_game_history_id, espn_player_id)
);

CREATE TABLE IF NOT EXISTS Team_Statistics (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    shot_on_goals INTEGER,
    shot_attempts INTEGER,
    fouls INTEGER,
    goals INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    corner_kicks INTEGER,
    saves INTEGER,
    possession_percent REAL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id)
);

CREATE TABLE IF NOT EXISTS Goals (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    espn_player_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (espn_player_id) REFERENCES Player(espn_id)
    UNIQUE (team_game_history_id, espn_player_id, time)
);

CREATE TABLE IF NOT EXISTS Fouls (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    espn_player_id INTEGER NOT NULL,
    card_type TEXT NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (espn_player_id) REFERENCES Player(espn_id)
    UNIQUE (team_game_history_id, espn_player_id, time)
);

CREATE TABLE IF NOT EXISTS Free_Kick (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    attacker_espn_id INTEGER NOT NULL,
    attacker_style TEXT NOT NULL,
    attacked_from TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (attacker_espn_id) REFERENCES Player(espn_id)
);

CREATE TABLE IF NOT EXISTS Offside (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    espn_player_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (espn_player_id) REFERENCES Player(espn_id)
);
