import json
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


combined_team_games_bk_path = 'json\\backups\\combined_team_games_bk.json'
team_game_history_bk_path = 'json\\backups\\team_game_history.bk.json'

all_teams_path = 'json\\all_teams.json'

import json

def backup_to_json_file(file_path, new_data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    combined = existing_data + new_data

    # Deduplicate using JSON string representation
    seen = set()
    unique_data = []
    for item in combined:
        item_str = json.dumps(item, sort_keys=True)
        if item_str not in seen:
            seen.add(item_str)
            unique_data.append(item)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, indent=4, ensure_ascii=False)




def is_team_url_in_combined_team_games_bk(team_url):
    # If the file doesn't exist, return False
    if not os.path.exists(combined_team_games_bk_path):
        return False

    # Load the JSON data
    with open(combined_team_games_bk_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return False

    # Extract all team URLs using list comprehension
    team_urls = [team["team url"] for team in data]

    # Check if the provided team_url exists
    return team_url in team_urls

def get_espn_id_from_url(url):
    match = re.search(r'/id/(\d+)', url)
    if not match:
        match = re.search(r'/gameId/(\d+)', url)
    if match:
        return int(match.group(1))
    else:
        raise Exception("ID not found in URL")

    

def extract_team_logos_from_detail_page(logo_parent):
    try:
        img = logo_parent.find_element(By.TAG_NAME, 'img')
        logo_url = img.get_attribute('src').split('&')[0]
    except:
        logo_url = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/default-team-logo-500.png"
    
    a = logo_parent.find_element(By.TAG_NAME, 'a')
    team_espn_id = get_espn_id_from_url(a.get_attribute('href'))
    team_name = a.get_attribute('href').split("/")[-1]

    return team_espn_id, team_name, logo_url
        



def parse_commentary_rows(rows):
    all_comments = []
    # for row in rows:
    #     try:
    #         timestamp = row.find_element(By.CLASS_NAME, 'time-stamp').text.strip()
    #         if not timestamp:
    #             timestamp = "-"
    #     except: timestamp = "-"
            
    #     try:
    #         icon_type = row.get_attribute('data-type').strip()
    #     except: icon_type = "unknown"
            
    #     try:
    #         comment = row.find_element(By.CLASS_NAME, 'game-details').text.strip()
    #     except: comment = ""
            
    #     if comment:
    #         structured_line = f"[{timestamp}] [{icon_type}] {comment}"
    #         all_comments.append(structured_line)

    for row in rows:
        try:
            timestamp = row.find_element(By.CSS_SELECTOR, ".MatchCommentary__Comment__Timestamp span").text
            try:
                svg = row.find_element(By.CSS_SELECTOR, ".MatchCommentary__Comment__PlayIcon svg")
                aria_label = svg.get_attribute("aria-label")
            except:
                aria_label = ''
            comment = row.find_element(By.CSS_SELECTOR, ".MatchCommentary__Comment__GameDetails span").text
            all_comments.append(f"[{timestamp}] [{aria_label}] {comment}")
        except Exception as e:
            print(f"Skipping row due to error")
            input('sdv')

    return "\n".join(all_comments)




def get_all_players_stats(driver, all_team_players_tables):
    all_players_stats = []
    goals_list = []
    fouls_list = []

    for table in all_team_players_tables:
        # Expand all buttons (same as before)
        buttons = table.find_elements(By.CSS_SELECTOR, 'tr button')
        for button in buttons:
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception as e:
                print(f"Button click failed: {e}")

        try:
            expanded = table.find_elements(By.CSS_SELECTOR, 'td button')[0].get_attribute('aria-expanded') == 'true'
        except IndexError:
            expanded = False

        if expanded:
            rows = table.find_elements(By.CSS_SELECTOR, 'tr')
            for row in rows:
                try:

                    # Try to find if the row is inside any of the substitute tables (LineUps__SubstitutesTable)
                    unused_player_tables = driver.find_elements(By.CSS_SELECTOR, '.LineUps__SubstitutesTable')
                    for unused_table in unused_player_tables:
                        match_found = unused_table.find_elements(By.XPATH, f".//td[contains(., '{row.text.strip()}')]")
                        if match_found:
                            unused_player = True
                            break  # No need to keep checking once found
                        else: unused_player = False
                    
                    player_espn_url = row.find_element(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]').get_attribute('href')
                    player_espn_id = get_espn_id_from_url(player_espn_url)
                    player_num = row.find_element(By.CSS_SELECTOR, '.SoccerLineUpPlayer__Header__Number').text.strip()

                    # Collect goals info from expanded stats if available
                    stat_label = row.find_element(By.CSS_SELECTOR, '.LineUpsStats__GoalsOrSaves span:nth-of-type(1)').text.strip().lower()
                    stat_value = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__GoalsOrSaves span:nth-of-type(2)').text.strip())
                    goals = stat_value if stat_label == "goals" else 0
                    saves = stat_value if stat_label == "saves" else 0

                    # Other stats ...
                    shots = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__Shots .BarLine__Item:nth-of-type(1) .BarLine__Stat').text.strip())
                    shots_on_target = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__Shots .BarLine__Item:nth-of-type(2) .BarLine__Stat').text.strip())
                    fouls_committed = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__Fouls .BarLine__Item:nth-of-type(1) .BarLine__Stat').text.strip())
                    fouls_against = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__Fouls .BarLine__Item:nth-of-type(2) .BarLine__Stat').text.strip())

                    last_row_items = row.find_elements(By.CSS_SELECTOR, '.LineUpsStats__LastRow li')
                    assists = int(last_row_items[0].find_elements(By.TAG_NAME, 'span')[-1].text.strip())
                    offsides = int(last_row_items[1].find_elements(By.TAG_NAME, 'span')[-1].text.strip()) if len(last_row_items) == 3 else 0
                    yellow_cards = int(last_row_items[-1].find_element(By.CSS_SELECTOR, '.LineUpsStats__Discipline__SubStat:nth-of-type(1) span:nth-of-type(1)').text.strip())
                    red_cards = int(last_row_items[-1].find_element(By.CSS_SELECTOR, '.LineUpsStats__Discipline__SubStat:nth-of-type(2) span:nth-of-type(1)').text.strip())

                    player_stats = {
                        "player_num": player_num,
                        "espn_id": player_espn_id,
                        "goals": goals,
                        "saves": saves,
                        "shots": shots,
                        "shots_on_target": shots_on_target,
                        "fouls_committed": fouls_committed,
                        "fouls_against": fouls_against,
                        "assists": assists,
                        "offsides": offsides,
                        "yellow_cards": yellow_cards,
                        "red_cards": red_cards,
                        "unused_player": unused_player,
                    }
                    all_players_stats.append(player_stats)

                    # For this expanded block, no detailed goal time data, so only total goals/cards counts available
                    # You might want to handle detailed times in collapsed section

                except Exception as e:
                    print(f"Skipping expanded row due to error: {e}")

        else:
            players = table.find_elements(By.CSS_SELECTOR, 'td .SoccerLineUpPlayer')
            unused_player_tables = driver.find_elements(By.CSS_SELECTOR, '.LineUps__SubstitutesTable')

            for player in players:
                try:
                    player_espn_url = player.find_element(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]').get_attribute("href")
                    player_espn_id = get_espn_id_from_url(player_espn_url)

                    player_num = player.find_element(By.CSS_SELECTOR, '.SoccerLineUpPlayer__Header__Number').text.strip()

                    #Unused Players
                    # Try to find if the row is inside any of the substitute tables (LineUps__SubstitutesTable)
                    unused_player_tables = driver.find_elements(By.CSS_SELECTOR, '.LineUps__SubstitutesTable')
                    for unused_table in unused_player_tables:
                        match_found = unused_table.find_elements(By.XPATH, f".//td[contains(., '{row.text.strip()}')]")
                        if match_found:
                            unused_player = True
                            break  # No need to keep checking once found
                        else: unused_player = False

                    # Goals with time and own goal info
                    goals_elems = player.find_elements(By.CSS_SELECTOR, 'svg[aria-label*="Goal"]')
                    goals_count = len(goals_elems)
                    for g in goals_elems:
                        time = g.get_attribute("aria-label").split('minute')[-1].strip()
                        own_goal = "OwnGoalIcon" in g.get_attribute("class")
                        goals_list.append({
                            "team_game_history_id": None,
                            "player_id": player_espn_id,
                            "time": time,
                            "own_goal": own_goal  # You can store this or ignore based on schema
                        })

                    # Cards with time
                    yellow_cards_elems = player.find_elements(By.CSS_SELECTOR, 'svg[aria-label*="Yellow"]')
                    for yc in yellow_cards_elems:
                        time = yc.get_attribute("aria-label").split('minute')[-1].strip()
                        fouls_list.append({
                            "team_game_history_id": None,
                            "player_id": player_espn_id,
                            "card": "yellow",
                            "time": time
                        })

                    red_cards_elems = player.find_elements(By.CSS_SELECTOR, 'svg[aria-label*="Red"]')
                    for rc in red_cards_elems:
                        time = rc.get_attribute("aria-label").split('minute')[-1].strip()
                        fouls_list.append({
                            "team_game_history_id":None,
                            "player_id": player_espn_id,
                            "card": "red",
                            "time": time
                        })

                    player_stats = {
                        "player_num": player_num,
                        "espn_id": player_espn_id,
                        "goals": goals_count,
                        "yellow_cards": len(yellow_cards_elems),
                        "red_cards": len(red_cards_elems),
                        "unused_player":unused_player
                    }
                    all_players_stats.append(player_stats)

                except Exception as e:
                    print(f"Skipping collapsed row due to error: {e}")

    return {
        "players_stats": all_players_stats,
        "goals": goals_list,
        "cards": fouls_list
    }
