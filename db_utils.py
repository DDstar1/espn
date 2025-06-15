import sqlite3

db_name="db/football_stats.db"

conn = sqlite3.connect(db_name)
conn.execute("PRAGMA foreign_keys = ON;")
cursor = conn.cursor()

with open("db/dbschema.sql", "r") as f:
    cursor.executescript(f.read())

def get_db_connection():
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def insert_player(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO Player (espn_id, Name, Nationality, DOB, Height, Weight)
        VALUES (:espn_id, :Name, :Nationality, :DOB, :Height, :Weight)
    """, data)
    conn.commit()
    conn.close()


def insert_team(data):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Team (espn_id, name, logo)
            VALUES (:espn_id, :name, :logo)
        """, data)
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Team with espn_id {data['espn_id']} already exists.")
    except Exception as e:
        print("An error occurred with data", data, e)
    finally:
        conn.close()

def team_exists(espn_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Team WHERE espn_id = ?", (espn_id,))
    exists = cursor.fetchone() is not None
    if exists == True: print(f"Team with espn_id {espn_id} already exists..")
    conn.close()
    return exists


def insert_game_info(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Game_Info (espn_id, date, referee, place, state, country, commentary, attendance)
        VALUES (:espn_id, :date, :referee, :place, :state, :country, :commentary, :attendance)
    """, data)
    conn.commit()
    conn.close()

def game_info_exists(espn_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Game_Info WHERE espn_id = ?", (espn_id,))
    exists = cursor.fetchone() is not None
    if exists == True: print(f"Game Info with espn_id {espn_id} already exists.")
    conn.close()
    return exists


def insert_line_up_statistics(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO Line_Up_Statistics (
            team_game_history_id, espn_player_id, player_num,
            position_x, position_y, goals, saves, shots, shots_on_target,
            fouls_commited, fouls_against, assists, offsides,
            yellow_cards, red_cards, unused_player
        )
        VALUES (
            :team_game_history_id, :espn_player_id, :player_num,
            :position_x, :position_y, :goals, :saves, :shots, :shots_on_target,
            :fouls_commited, :fouls_against, :assists, :offsides,
            :yellow_cards, :red_cards, :unused_player
        )
    """, data)
    conn.commit()
    conn.close()


def insert_team_game_history(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO Team_Game_History (espn_team_id, espn_game_info_id, formation, goals)
            VALUES (:espn_team_id, :espn_game_info_id, :formation, :goals)
        """, data)
        conn.commit()

        if cursor.lastrowid:
            return cursor.lastrowid  # New row inserted
        else:
            # Row already exists, fetch its ID
            cursor.execute("""
                SELECT id FROM Team_Game_History
                WHERE espn_team_id = :espn_team_id AND espn_game_info_id = :espn_game_info_id
            """, data)
            result = cursor.fetchone()
            return result[0] if result else None
    finally:
        conn.close()




def insert_team_statistics(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Team_Statistics (
            team_game_history_id, goals, shot_on_goals,
            shot_attempts, fouls, yellow_cards, red_cards, corner_kicks,
            saves, possession_percent
        )
        VALUES (
            :team_game_history_id, :goals, :shot_on_goals,
            :shot_attempts, :fouls, :yellow_cards, :red_cards, :corner_kicks,
            :saves, :possession_percent
        )
    """, data)
    conn.commit()
    conn.close()


def insert_goal(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO Goals (team_game_history_id, espn_player_id, time)
        VALUES (:team_game_history_id, :espn_player_id, :time)
    """, data)
    conn.commit()
    conn.close()


def insert_foul(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO Fouls (team_game_history_id, espn_player_id, card_type, time)
        VALUES (:team_game_history_id, :espn_player_id, :card_type, :time)
    """, data)
    conn.commit()
    conn.close()


def insert_free_kick(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Free_Kick (
            team_game_history_id, time, attacker_id,
            attacker_style, attacked_from, saved_at
        )
        VALUES (
            :team_game_history_id, :time, :attacker_id,
            :attacker_style, :attacked_from, :saved_at
        )
    """, data)
    conn.commit()
    conn.close()


def insert_offside(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Offside (team_game_history_id, player_id, time)
        VALUES (:team_game_history_id, :player_id, :time)
    """, data)
    conn.commit()
    conn.close()


def get_team_game_history_id(espn_game_info_id, espn_team_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM Team_Game_History WHERE espn_team_id = ? AND espn_game_info_id = ?",
        (espn_team_id, espn_game_info_id)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def player_exists(espn_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM Player WHERE espn_id = ?", (espn_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def player_line_up_stat_exists(team_game_history_id, espn_player_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM Line_Up_Statistics 
        WHERE team_game_history_id = ? AND espn_player_id = ?
    """, (team_game_history_id, espn_player_id))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def team_stats_exists(team_game_history_id):
    print(f"team_game_history_id: {team_game_history_id}, type: {type(team_game_history_id)}")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM Team_Statistics 
        WHERE team_game_history_id = ?
    """, (team_game_history_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

conn.commit()
cursor.close()
conn.close()


def set_latest_scraped_team_url(url):
    """Insert or replace the single team URL in the Tracker table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO Tracker (id, latest_scraped_team_url)
        VALUES (1, ?)
    """, (url,))
    conn.commit()
    conn.close()

def get_latest_scraped_team_url():
    """Retrieve the single team URL from the Tracker table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT latest_scraped_team_url FROM Tracker WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None