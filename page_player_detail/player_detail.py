from pprint import pprint
import re
from selenium.webdriver.common.by import By
import db_utils
from utils import get_espn_id_from_url
from datetime import datetime

#LineUp Stats Selectors
both_team_lineup_selectors = ".Card__Content.LineUps"

#Player Bio
weight_height_selector = "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='HT/WT']/following-sibling::span[contains(text(), 'kg')]"
just_height_selector = "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='Height']/following-sibling::span[contains(text(), 'm')]"
just_weight_selector= "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='Weight']/following-sibling::span[contains(text(), 'kg')]"
bday_selector = "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='Birthdate']/following-sibling::span"
nationality_selector = "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='Nationality']/following-sibling::span"
player_name_selector = ".PlayerHeader__Name"


def get_all_players_details(driver, lineup_url):
    driver.get(lineup_url)
    print(lineup_url)
    all_team_players_tables = driver.find_elements(By.CSS_SELECTOR, both_team_lineup_selectors)
    all_players_details_list = []
    try:
        if(all_team_players_tables == [] ):
            print(f"No line ups for game {lineup_url}")
            return []
        home_players = all_team_players_tables[0]
        away_players = all_team_players_tables[1]
        all_team_players_tables_combined = home_players.find_elements(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]') + away_players.find_elements(By.CSS_SELECTOR, 'a[href^="https://africa.espn.com/football/player/_/id/"]')
        combined_player_links = [player.get_attribute('href').replace("player/", "player/bio/") for player in all_team_players_tables_combined]
    except:
        print(combined_player_links)
        print(driver.current_url)
        input('line up error at the above')
    
    #Save all Players details 
    for link in combined_player_links:
        print(link)

        player_espn_id = get_espn_id_from_url(link)
       
       #Skip player if already in db
        if(db_utils.player_exists(player_espn_id)==True): 
            print("Player already in db..Skipping")
            continue

        
        player_data = {
            "espn_id": None,
            "Name": None,
            "Nationality": None,
            "DOB": None,
            "Height": None,
            "Weight": None
        }

        
        driver.get(link)
        # Extract PLAYER ESPN ID and check whether if he is already in db
        player_data["espn_id"] = player_espn_id

        # Extract HT/WT and parse
        try:
            htwt_text = driver.find_element(By.XPATH, weight_height_selector).text.strip()
            ht_match = re.search(r'([\d\.]+)\s*m', htwt_text)
            wt_match = re.search(r'([\d\.]+)\s*kg', htwt_text)
            height = float(ht_match.group(1)) if ht_match else None
            weight = float(wt_match.group(1)) if wt_match else None
        except Exception:
            try:
                height_text = driver.find_element(By.XPATH, just_height_selector).text.strip()
                weight_text = driver.find_element(By.XPATH, just_weight_selector).text.strip()
                height = float(re.search(r'([\d\.]+)', height_text).group(1)) if height_text else None
                weight = float(re.search(r'([\d\.]+)', weight_text).group(1)) if weight_text else None
            except Exception:
                height = None
                weight = None

        player_data["Height"] = height
        player_data["Weight"] = weight


        # Extract DOB and convert to UNIX timestamp
        try:
            bday_text = driver.find_element(By.XPATH, bday_selector).text.strip().split(' ')[0]  # e.g., "18/2/2000"
            dob_dt = datetime.strptime(bday_text, "%d/%m/%Y")
            player_data["DOB"] = int(dob_dt.timestamp())
        except Exception as e:
            player_data["DOB"] = None

        # Extract nationality
        try:
            nationality = driver.find_element(By.XPATH, nationality_selector).text.strip()
            player_data["Nationality"] = nationality
        except:
            player_data["Nationality"] = None

        # Extract Player Name
        player_name = driver.find_element(By.CSS_SELECTOR, player_name_selector).text.strip()
        player_data['Name'] = player_name.replace('\n', ' ').lower()

        pprint("Player appened to list")
        all_players_details_list.append(player_data)
    
    return all_players_details_list
    
