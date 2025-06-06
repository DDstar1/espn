from pprint import pprint, PrettyPrinter
import db_utils
from utils import get_espn_id_from_url
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from page_lineup.get_player_field_pos import get_player_field_positions


# ---------------------------
# Selectors as constants
# ---------------------------
SELECTOR_EXPAND_BUTTONS = 'tr button'
SELECTOR_ARIA_EXPANDED_BUTTON = 'td button'
SELECTOR_PLAYER_LINK = 'a[href^="https://africa.espn.com/football/player/_/id/"]'
SELECTOR_PLAYER_NUMBER = '.SoccerLineUpPlayer__Header__Number'
SELECTOR_SUBSTITUTE_TABLE_XPATH = "//*[contains(@class, 'LineUps__SubstitutesTable')] //td[contains(., '{}')]"
SELECTOR_GOAL_SVG = 'svg[aria-label*="Goal"]'
SELECTOR_YELLOW_CARD_SVG = 'svg[aria-label*="Yellow"]'
SELECTOR_RED_CARD_SVG = 'svg[aria-label*="Red"]'
SELECTOR_GOALS_OR_SAVES_LABEL = '.LineUpsStats__GoalsOrSaves span:nth-of-type(1)'
SELECTOR_GOALS_OR_SAVES_VALUE = '.LineUpsStats__GoalsOrSaves span:nth-of-type(2)'
SELECTOR_SHOTS_TOTAL = '.LineUpsStats__Shots .BarLine__Item:nth-of-type(1) .BarLine__Stat'
SELECTOR_SHOTS_ON_TARGET = '.LineUpsStats__Shots .BarLine__Item:nth-of-type(2) .BarLine__Stat'
SELECTOR_FOULS_COMMITTED = '.LineUpsStats__Fouls .BarLine__Item:nth-of-type(1) .BarLine__Stat'
SELECTOR_FOULS_AGAINST = '.LineUpsStats__Fouls .BarLine__Item:nth-of-type(2) .BarLine__Stat'
SELECTOR_LAST_ROW_ITEMS = '.LineUpsStats__LastRow li'


pp = PrettyPrinter(indent=2, width=200, compact=True)


def extract_card_and_goal_data(player, player_espn_id, goals_list, fouls_list):
    """Extract goals and cards data for a player"""
    try:
        # Goals with time and own goal info
        goals_elems = player.find_elements(By.CSS_SELECTOR, SELECTOR_GOAL_SVG)
        for g in goals_elems:
            time = g.get_attribute("aria-label").split('minute')[-1].strip()
            own_goal = "OwnGoalIcon" in g.get_attribute("class")
            goals_list.append({
                "team_game_history_id": None,
                "player_id": player_espn_id,
                "time": time,
                "own_goal": own_goal
            })
    except Exception as e:
        print(f"Failed to extract goals: {e}")
        goals_elems = []

    try:
        # Yellow cards with time
        yellow_cards_elems = player.find_elements(By.CSS_SELECTOR, SELECTOR_YELLOW_CARD_SVG)
        for yc in yellow_cards_elems:
            time = yc.get_attribute("aria-label").split('minute')[-1].strip()
            fouls_list.append({
                "team_game_history_id": None,
                "player_id": player_espn_id,
                "card": "yellow",
                "time": time
            })
    except Exception as e:
        print(f"Failed to extract yellow cards: {e}")
        yellow_cards_elems = []

    try:
        # Red cards with time
        red_cards_elems = player.find_elements(By.CSS_SELECTOR, SELECTOR_RED_CARD_SVG)
        for rc in red_cards_elems:
            time = rc.get_attribute("aria-label").split('minute')[-1].strip()
            fouls_list.append({
                "team_game_history_id": None,
                "player_id": player_espn_id,
                "card": "red",
                "time": time
            })
    except Exception as e:
        print(f"Failed to extract red cards: {e}")
        red_cards_elems = []

    return goals_elems, yellow_cards_elems, red_cards_elems


def get_all_players_stats(driver, all_team_players_tables, both_team_details):
    teams_combined = []
    
    for i, table in enumerate(all_team_players_tables):
        espn_game_info_id = both_team_details[i]["espn_game_info_id"] 
        espn_team_id = both_team_details[i]["espn_team_id"]
        team_game_history_id = db_utils.get_team_game_history_id(espn_game_info_id, espn_team_id)
        all_players_stats = []
        goals_list = []
        fouls_list = []
        
        # Expand all buttons
        buttons = table.find_elements(By.CSS_SELECTOR, SELECTOR_EXPAND_BUTTONS)
        for button in buttons:
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception as e:
                print(f"Button click failed: {e}")

        # Check if expanded
        try:
            expanded = table.find_elements(By.CSS_SELECTOR, SELECTOR_ARIA_EXPANDED_BUTTON)[0].get_attribute('aria-expanded') == 'true'
        except IndexError:
            expanded = False

        rows = table.find_elements(By.CSS_SELECTOR, 'tr')

        for player in rows:
            try:
                # Get player ESPN ID first
                player_link_elem = player.find_element(By.CSS_SELECTOR, SELECTOR_PLAYER_LINK)
                player_espn_url = player_link_elem.get_attribute("href")
                player_espn_id = get_espn_id_from_url(player_espn_url)
                player_name = player_link_elem.text.strip()
                
                print(f"Processing player: {player_name} (ID: {player_espn_id})")

                # Check if player already exists in database
                if db_utils.player_line_up_stat_exists(team_game_history_id, player_espn_id):
                    print(f"Player {player_espn_id} already has stats for this game {team_game_history_id}...skipping")
                    continue

                # Initialize player stats
                player_stats = {
                    "team_game_history_id": team_game_history_id,
                    "player_num": None,
                    "espn_player_id": player_espn_id,
                    "saves": None,
                    "shots": None,
                    "shots_on_target": None,
                    "fouls_commited": None,
                    "fouls_against": None,
                    "assists": None,
                    "offsides": None,
                    "goals": None,
                    "yellow_cards": None,
                    "red_cards": None,
                    "unused_player": None,
                    "position_x": None,
                    "position_y": None,
                }

                # Get player number
                try:
                    player_num = player.find_element(By.CSS_SELECTOR, SELECTOR_PLAYER_NUMBER).text.strip()
                    player_stats["player_num"] = player_num
                except Exception as e:
                    print(f"Failed to extract player number for {player_name}: {e}")

                # Check if player is unused (substitute)
                try:
                    match_found = driver.find_elements(By.XPATH, SELECTOR_SUBSTITUTE_TABLE_XPATH.format(player_name))
                    unused_player = bool(match_found)
                    player_stats["unused_player"] = unused_player
                except Exception as e:
                    print(f"Failed to check if player is unused: {e}")

                # Extract goals and cards data
                goals_elems, yellow_cards_elems, red_cards_elems = extract_card_and_goal_data(
                    player, player_espn_id, goals_list, fouls_list
                )

                # Set basic stats
                player_stats["goals"] = len(goals_elems)
                player_stats["yellow_cards"] = len(yellow_cards_elems)
                player_stats["red_cards"] = len(red_cards_elems)

                # If expanded, get detailed stats
                if expanded:
                    try:
                        # Collect goals/saves info from expanded stats
                        stat_label = player.find_element(By.CSS_SELECTOR, SELECTOR_GOALS_OR_SAVES_LABEL).text.strip().lower()
                        stat_value = int(player.find_element(By.CSS_SELECTOR, SELECTOR_GOALS_OR_SAVES_VALUE).text.strip())
                        goals = stat_value if stat_label == "goals" else 0
                        saves = stat_value if stat_label == "saves" else 0

                        # Other detailed stats
                        shots = int(player.find_element(By.CSS_SELECTOR, SELECTOR_SHOTS_TOTAL).text.strip())
                        shots_on_target = int(player.find_element(By.CSS_SELECTOR, SELECTOR_SHOTS_ON_TARGET).text.strip())
                        fouls_commited = int(player.find_element(By.CSS_SELECTOR, SELECTOR_FOULS_COMMITTED).text.strip())
                        fouls_against = int(player.find_element(By.CSS_SELECTOR, SELECTOR_FOULS_AGAINST).text.strip())

                        last_row_items = player.find_elements(By.CSS_SELECTOR, SELECTOR_LAST_ROW_ITEMS)
                        assists = int(last_row_items[0].find_elements(By.TAG_NAME, 'span')[-1].text.strip())
                        offsides = int(last_row_items[1].find_elements(By.TAG_NAME, 'span')[-1].text.strip()) if len(last_row_items) == 3 else 0

                        # Update player stats with detailed info
                        player_stats.update({
                            "saves": saves,
                            "shots": shots,
                            "shots_on_target": shots_on_target,
                            "fouls_commited": fouls_commited,
                            "fouls_against": fouls_against,
                            "assists": assists,
                            "offsides": offsides,
                        })

                    except Exception as e:
                        print(f"Failed to extract detailed stats for {player_name}: {e}")

                all_players_stats.append(player_stats)

            except NoSuchElementException:
                print("Player link not found in this row, skipping...")
                continue
            except Exception as e:
                print(f"Error processing player row: {e}")
                continue

        print("ALL PLAYERS FIELD POSITIONS ")
        # Create a lookup dictionary for positions
        try:
            player_pos = get_player_field_positions(driver, table) 
            position_lookup = {str(p['player_number']): {'position_x': p['position_x'], 'position_y': p['position_y']} for p in player_pos}
            print(position_lookup)

            # Combine with all_players_stats
            for player in all_players_stats:
                player_num = player['player_num']
                if player_num:
                    position = position_lookup.get(player_num, {'position_x': None, 'position_y': None})
                    player.update(position)
        except Exception as e:
            print(f"Failed to get player positions: {e}")
    
        #input('positions')
        teams_combined.append({
            "players_stats": all_players_stats,
            "goals": goals_list,
            "cards": fouls_list
        })
        
    return teams_combined