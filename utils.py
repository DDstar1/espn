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




def open_all_players_stats(driver, all_team_players_tables):
    all_players_stats = []

    for table in all_team_players_tables:
        # Click all buttons to expand player stats
        for button in table.find_elements(By.CSS_SELECTOR, 'tr button'):
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception as e:
                print(f"Button click failed: {e}")
        
        if(table.find_elements(By.CSS_SELECTOR, 'tr button')[0].get_attribute('aria-expanded')=='true'):
            # Loop through each row/player
            for row in table.find_elements(By.CSS_SELECTOR, 'tr'):
                try:
                    # Goals or Saves
                    stat_label = row.find_element(By.CSS_SELECTOR, '.LineUpsStats__GoalsOrSaves span:nth-of-type(1)').text.strip().lower()
                    stat_value = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__GoalsOrSaves span:nth-of-type(2)').text.strip())
                    goals = stat_value if stat_label == "goals" else 0
                    saves = stat_value if stat_label == "saves" else 0

                    # Shots and Shots on Target
                    shots = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__Shots .BarLine__Item:nth-of-type(1) .BarLine__Stat').text.strip())
                    shots_on_target = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__Shots .BarLine__Item:nth-of-type(2) .BarLine__Stat').text.strip())

                    # Fouls
                    fouls_committed = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__Fouls .BarLine__Item:nth-of-type(1) .BarLine__Stat').text.strip())
                    fouls_against = int(row.find_element(By.CSS_SELECTOR, '.LineUpsStats__Fouls .BarLine__Item:nth-of-type(2) .BarLine__Stat').text.strip())

                    # Last row stats
                    last_row_items = row.find_elements(By.CSS_SELECTOR, '.LineUpsStats__LastRow li')
                    assists = int(last_row_items[0].find_elements(By.TAG_NAME, 'span')[-1].text.strip())
                    offsides = int(last_row_items[1].find_elements(By.TAG_NAME, 'span')[-1].text.strip()) if len(last_row_items) == 3 else 0
                    yellow_cards = int(last_row_items[-1].find_element(By.CSS_SELECTOR, '.LineUpsStats__Discipline__SubStat:nth-of-type(1) span:nth-of-type(1)').text.strip())
                    red_cards = int(last_row_items[-1].find_element(By.CSS_SELECTOR, '.LineUpsStats__Discipline__SubStat:nth-of-type(2) span:nth-of-type(1)').text.strip())

                    #

                    #Player espn ID
                    player_espn_url = row.find_element(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]')
                    player_espn_id = get_espn_id_from_url(player_espn_url)

                    #Player Num
                    player_num = row.find_element(By.CSS_SELECTOR, '.SoccerLineUpPlayer__Header__Number')
                    
                    # Store player stats
                    player_stats = {
                        "player_num":player_num,
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
                        "red_cards": red_cards
                    }

                    all_players_stats.append(player_stats)

                except Exception as e:
                    print("Some elements not found in this row, skipping...")
        else:
            input('found missing')
              # Loop through each row/player
            for row in table.find_elements(By.CSS_SELECTOR, 'tr'):
                try:
                    # Goals or Saves
                    goal = row.find_element(By.CSS_SELECTOR, 'svg[aria-label*="Goal"]')


                    # Last row stats
                    yellow_card = row.find_element(By.CSS_SELECTOR, 'svg[aria-label*="Red"]')
                    red_card = row.find_element(By.CSS_SELECTOR, 'svg[aria-label*="Yellow"]')

                    #Substitution
                    substitution = row.find_element(By.CSS_SELECTOR, 'svg[aria-label*="Substitution"]')



                    #Player espn ID
                    player_espn_url = row.find_element(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]')
                    player_espn_id = get_espn_id_from_url(player_espn_url)

                    #Player Num
                    player_num = row.find_element(By.CSS_SELECTOR, '.SoccerLineUpPlayer__Header__Number')
                    
                    # Store player stats
                    player_stats = {
                        "player_num":player_num,
                        "espn_id": player_espn_id,
                        "goals": goals,
                        "saves": saves,
                        "yellow_cards": yellow_cards,
                        "red_cards": red_cards
                    }

                    all_players_stats.append(player_stats)

                except NoSuchElementException:
                    print("Some elements not found in this row, skipping...")

    # Print final list of player stat dictionaries
    for idx, player in enumerate(all_players_stats, 1):
        print(f"Player {idx} Stats: {player}")
    
    return all_players_stats
