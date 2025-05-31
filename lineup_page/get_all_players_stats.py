from pprint import pprint, PrettyPrinter
from utils import get_espn_id_from_url
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from lineup_page.get_player_field_pos import get_player_field_positions

pp = PrettyPrinter(indent=2, width=200, compact=True)
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
            for player in rows:
                try:
                    player_name = player.find_element(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]').text.strip()
                    player_espn_url = player.find_element(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]').get_attribute('href')
                    player_espn_id = get_espn_id_from_url(player_espn_url)
                    player_num = player.find_element(By.CSS_SELECTOR, '.SoccerLineUpPlayer__Header__Number').text.strip()

                    # Try to find if the player is inside any of the substitute tables (LineUps__SubstitutesTable)
                    match_found = driver.find_elements(By.XPATH,f"//*[contains(@class, 'LineUps__SubstitutesTable')] //td[contains(., '{player_name}')]")

                    if match_found != []: unused_player = True
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
                    
                    # Collect goals info from expanded stats if available
                    stat_label = player.find_element(By.CSS_SELECTOR, '.LineUpsStats__GoalsOrSaves span:nth-of-type(1)').text.strip().lower()
                    stat_value = int(player.find_element(By.CSS_SELECTOR, '.LineUpsStats__GoalsOrSaves span:nth-of-type(2)').text.strip())
                    goals = stat_value if stat_label == "goals" else 0
                    saves = stat_value if stat_label == "saves" else 0

                    # Other stats ...
                    shots = int(player.find_element(By.CSS_SELECTOR, '.LineUpsStats__Shots .BarLine__Item:nth-of-type(1) .BarLine__Stat').text.strip())
                    shots_on_target = int(player.find_element(By.CSS_SELECTOR, '.LineUpsStats__Shots .BarLine__Item:nth-of-type(2) .BarLine__Stat').text.strip())
                    fouls_committed = int(player.find_element(By.CSS_SELECTOR, '.LineUpsStats__Fouls .BarLine__Item:nth-of-type(1) .BarLine__Stat').text.strip())
                    fouls_against = int(player.find_element(By.CSS_SELECTOR, '.LineUpsStats__Fouls .BarLine__Item:nth-of-type(2) .BarLine__Stat').text.strip())

                    last_row_items = player.find_elements(By.CSS_SELECTOR, '.LineUpsStats__LastRow li')
                    assists = int(last_row_items[0].find_elements(By.TAG_NAME, 'span')[-1].text.strip())
                    offsides = int(last_row_items[1].find_elements(By.TAG_NAME, 'span')[-1].text.strip()) if len(last_row_items) == 3 else 0
                    #yellow_cards = int(last_row_items[-1].find_element(By.CSS_SELECTOR, '.LineUpsStats__Discipline__SubStat:nth-of-type(1) span:nth-of-type(1)').text.strip())
                    #red_cards = int(last_row_items[-1].find_element(By.CSS_SELECTOR, '.LineUpsStats__Discipline__SubStat:nth-of-type(2) span:nth-of-type(1)').text.strip())

                    player_stats = {
                        "player_num": player_num,
                        "espn_id": player_espn_id,
                        "saves": saves,
                        "shots": shots,
                        "shots_on_target": shots_on_target,
                        "fouls_committed": fouls_committed,
                        "fouls_against": fouls_against,
                        "assists": assists,
                        "offsides": offsides,
                        "goals":  len(goals_elems),
                        "yellow_cards": len(yellow_cards_elems),
                        "red_cards": len(red_cards_elems),
                        "unused_player": unused_player,
                    }
                    all_players_stats.append(player_stats)

                    # For this expanded block, no detailed goal time data, so only total goals/cards counts available
                    # You might want to handle detailed times in collapsed section

                except Exception as e:
                    print(f"Skipping expanded row due to error: {e}")

        else:
            rows = table.find_elements(By.CSS_SELECTOR, 'td .SoccerLineUpPlayer')
            for player in rows:
                try:
                    player_name = player.find_element(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]').text.strip()
                    player_espn_url = player.find_element(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]').get_attribute("href")
                    player_espn_id = get_espn_id_from_url(player_espn_url)

                    player_num = player.find_element(By.CSS_SELECTOR, '.SoccerLineUpPlayer__Header__Number').text.strip()

                    #Unused Players
                    # Try to find if the row is inside any of the substitute tables (LineUps__SubstitutesTable)
                    match_found = driver.find_elements(By.XPATH,f"//*[contains(@class, 'LineUps__SubstitutesTable')] //td[contains(., '{player_name}')]")
                    if match_found != []: unused_player = True
                    else: unused_player = False

                    # Goals with time and own goal info
                    goals_elems = player.find_elements(By.CSS_SELECTOR, 'svg[aria-label*="Goal"]')
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
                        "goals":  len(goals_elems),
                        "yellow_cards": len(yellow_cards_elems),
                        "red_cards": len(red_cards_elems),
                        "unused_player":unused_player
                    }
                    all_players_stats.append(player_stats)

                except Exception as e:
                    print(f"Skipping collapsed row due to error: {e}")

    print("ALL PLAYERS FIELD POSITIONS ")
    pprint(get_player_field_positions(driver))
    
    input('positions')
    return {
        "players_stats": all_players_stats,
        "goals": goals_list,
        "cards": fouls_list
    }
