PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Player (
    espn_id INTEGER PRIMARY KEY,
    Name TEXT NOT NULL,
    DOB REAL NOT NULL,
    Nationality TEXT NOT NULL,
    Height REAL NOT NULL,
    Weight REAL NOT NULL
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
    FOREIGN KEY (espn_team_id) REFERENCES Team(espn_id),
    FOREIGN KEY (espn_game_info_id) REFERENCES Game_Info(espn_id)
);

CREATE TABLE IF NOT EXISTS Line_Up_Statistics (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    position TEXT NOT NULL,
    player_num INTEGER NOT NULL,
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    role TEXT NOT NULL,
    goals INTEGER NOT NULL,
    shots INTEGER NOT NULL,
    shot_on_target INTEGER NOT NULL,
    fouls_commited INTEGER NOT NULL,
    fouls_against INTEGER NOT NULL,
    assists INTEGER NOT NULL,
    offsides INTEGER NOT NULL,
    yellow_cards INTEGER NOT NULL,
    red_cards INTEGER NOT NULL,
    unused_player INTEGER NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (player_id) REFERENCES Player(espn_id)
);

CREATE TABLE IF NOT EXISTS Team_Statistics (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    formation TEXT NOT NULL,
    goals INTEGER NOT NULL,
    shot_on_goals INTEGER NOT NULL,
    shot_attempts INTEGER NOT NULL,
    fouls INTEGER NOT NULL,
    yellow_card INTEGER NOT NULL,
    red_card INTEGER NOT NULL,
    corner_kicks INTEGER NOT NULL,
    saves INTEGER NOT NULL,
    possession_percent REAL NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id)
);

CREATE TABLE IF NOT EXISTS Goals (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (player_id) REFERENCES Player(espn_id)
    UNIQUE (team_game_history_id, player_id, time)
);

CREATE TABLE IF NOT EXISTS Fouls (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    card TEXT NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (player_id) REFERENCES Player(espn_id)
    UNIQUE (team_game_history_id, player_id, time)
);

CREATE TABLE IF NOT EXISTS Free_Kick (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    attacker_id INTEGER NOT NULL,
    attacker_style TEXT NOT NULL,
    attacked_from TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (attacker_id) REFERENCES Player(espn_id)
);

CREATE TABLE IF NOT EXISTS Offside (
    id INTEGER PRIMARY KEY,
    team_game_history_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY (team_game_history_id) REFERENCES Team_Game_History(id),
    FOREIGN KEY (player_id) REFERENCES Player(espn_id)
);
