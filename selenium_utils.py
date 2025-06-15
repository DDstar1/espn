from pprint import pprint, PrettyPrinter
import re
import traceback
import config
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from datetime import datetime
from page_lineup.get_all_players_stats import get_all_players_stats
from page_player_detail.player_detail import get_all_players_details
from page_team_stats.team_stats import extract_match_stats
from utils import extract_team_logos_from_detail_page, get_espn_id_from_url, parse_commentary_rows
import db_utils 


pp = PrettyPrinter(indent=2, width=200, compact=True)

# Backup Paths
combined_team_games_bk_path = 'json\\backups\\combined_team_games_bk.json'
team_game_history_bk_path = 'json\\backups\\team_game_history.bk.json'


# CSS selectors for different elements on the webpage
team_select_year_result_btn_years =  "#fittPageContainer > div.pageContent > div > div.page-container.cf > div > div.layout__column.layout__column--1 > section > div > section > div.inline-flex > div.dropdown.dropdown__select--seasons > select:nth-child(2) option"
games_detail_row_selector = ".Table__TR.Table__TR--sm"
games_detail_game_id_url_selector = '.Table__TR.Table__TR--sm .Table__Team.score a[href*="/football/match/_/gameId/"]'
formation_field_selector = ".TacticalFormation__Field"
formation_btn_selector = ".ButtonGroup.flex button"
player_link_selector = ".AnchorLink.SoccerLineUpPlayer__Header__Name"
team_page_logo_selector = "img.Image.Logo.Logo__xxl"
game_detail_page_logos_selector = ".Gamestrip__InfoLogo"

#Game Info Selectors
referee_selector = ".Card.GameInfo .GameInfo__List__Item"
attendance_selector = ".Card.GameInfo .Attendance__Numbers"
state_country_selector = ".Card.GameInfo .Location__Text"
field_selector = ".Card.GameInfo .GameInfo__Location__Name--noImg"
date_selector = ".Card.GameInfo .GameInfo__Meta span"
commentary_selector ='.match-commentary tbody'
formation_selectors = ".LineUps__TabsHeader__Title"
goals_selectors = ".Gamestrip__Score"

#LineUp Stats Selectors
both_team_lineup_selectors = ".Card__Content.LineUps"

#Player Bio
weight_height_selector = "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='HT/WT']/following-sibling::span[contains(text(), 'kg')]"
#just_height_selector = "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='Height']/following-sibling::span[contains(text(), 'm')]"
#just_weight_selector= "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='Weight']/following-sibling::span[contains(text(), 'kg')]"
bday_selector = "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='Birthdate']/following-sibling::span"
nationality_selector = "//section[contains(@class, 'Card') and contains(@class, 'Bio')]//span[.='Nationality']/following-sibling::span"
player_name_selector = ".PlayerHeader__Name"



# Setup Chrome options (optional, for headless mode)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--window-size=1920,1080")  # Set desktop screen size
chrome_options.add_argument("--disable-gpu")  # Recommended for headless on Windows
chrome_options.add_argument("--no-sandbox")  # Recommended in some environments (e.g., Docker)
chrome_options.add_argument("--disable-dev-shm-usage")  # Helps avoid resource issues
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images


# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)

def get_links_of_all_games_played(team_url_list):
    for index, team_url in enumerate(team_url_list):
        team_games = []
        team_name = team_url.split('/')[-1]
        team_espn_id = get_espn_id_from_url(team_url)
        
        driver.get(team_url)

        
        
        if (db_utils.team_exists(team_espn_id)==False):
            team_logo = driver.find_element(By.CSS_SELECTOR, team_page_logo_selector).get_attribute("src").split('&')[0]
            db_utils.insert_team({'espn_id': team_espn_id, 'name': team_name, 'logo': team_logo})

        year_result_btn_element = driver.find_elements(By.CSS_SELECTOR, team_select_year_result_btn_years)
        texts = [elem.text for elem in year_result_btn_element]
  

        year_result_btn_element_links = [
            config.BASE_URL + elem.get_attribute('data-url')
            for elem in year_result_btn_element
            if int(elem.get_attribute('data-url').split('/')[-1]) >= config.SCRAPE_END_YR
        ]


        if  len(year_result_btn_element_links) == 0:
            #Incase the team result section isnt divided into years
            game_detail_Links = [
                    elem.get_attribute('href')
                    for elem in driver.find_elements(By.CSS_SELECTOR, games_detail_game_id_url_selector)
                ]
            team_games += game_detail_Links
        else:
            for season_link in year_result_btn_element_links:
                driver.get(season_link)
                game_detail_Links = [
                    elem.get_attribute('href')
                    for elem in driver.find_elements(By.CSS_SELECTOR, games_detail_game_id_url_selector)
                ]
                # print(game_detail_Links)  # Optional: For debugging
                team_games += game_detail_Links
        
        for game_detail_url in game_detail_Links:
            espn_game_id = get_espn_id_from_url(game_detail_url)

            if  db_utils.game_info_exists(espn_game_id):
                print(f'Game id {espn_game_id} already in db...skipping')
                continue

            driver.get(game_detail_url)
            logos = driver.find_elements(By.CSS_SELECTOR, game_detail_page_logos_selector)
            formations = driver.find_elements(By.CSS_SELECTOR, formation_selectors)
            goals = driver.find_elements(By.CSS_SELECTOR, goals_selectors)
            
            lineup_url = game_detail_url.replace('match', 'lineups')
            commentary_url = game_detail_url.replace('match', 'commentary')
            game_stats_url = game_detail_url.replace('match', 'matchstats')
            
            both_team_details = []

            for i, logo in enumerate(logos):
                team_espn_id, team_name, logo_url = extract_team_logos_from_detail_page(logo)
                db_utils.insert_team({'espn_id': team_espn_id, 'name': team_name, 'logo': logo_url})

                # Handle missing formation with try-except
                try:
                    formation_text = formations[i].text.strip()
                    if '-' not in formation_text:
                        formation_text = None
                except IndexError:
                    formation_text = None
             
                # Goals extraction (optional: can also add bounds check if needed)
                goals_text = goals[i].text.strip()
                print(goals_text)
                #input("Goals")

                data = {
                    "team_game_history_id":db_utils.get_team_game_history_id(espn_game_id, team_espn_id),
                    "espn_team_id": team_espn_id,
                    "espn_game_info_id": espn_game_id,
                    "formation": formation_text,
                    "goals": goals_text
                    }
                
                both_team_details.append(data)
                print(both_team_details)
                #db_utils.insert_team_game_history(data)

            #input('dsdv')

                    

          
            game_details = get_details_and_commentary_of_game(driver, espn_game_id, commentary_url)
            db_utils.insert_game_info(game_details)

            for i, details in enumerate(both_team_details):
                print(i)
                inserted_id = db_utils.insert_team_game_history(details)
                both_team_details[i]["team_game_history_id"] = inserted_id
                print("Inserted or existing team_game_history_id:", inserted_id)

            print(both_team_details)
            #input("dffd")

            

            #Get and store all playes data and go back to line_up page
            all_players_details_list = get_all_players_details(driver, lineup_url)
            pprint(all_players_details_list)
            for player_dic in all_players_details_list:
                 db_utils.insert_player(player_dic)
            driver.get(lineup_url)            
            

            try:
                all_team_players_tables = driver.find_elements(By.CSS_SELECTOR, both_team_lineup_selectors)
                combined_lineup_stats = get_all_players_stats(driver, all_team_players_tables, both_team_details)
                print(f"combined_lineup_stats is {combined_lineup_stats}")
                for lineup_stats in combined_lineup_stats:
                    players_stats, goals, cards = lineup_stats['players_stats'], lineup_stats['goals'], lineup_stats['cards']
                    for stats in players_stats:
                        db_utils.insert_line_up_statistics(stats)
                    for goal in goals:
                        db_utils.insert_goal(goal)
                    for card in cards:
                        db_utils.insert_foul(card)
                        
                    #input('sdvsdfv')
                    print("ALL PLAYERS MATCH STATS")
                    pprint(lineup_stats)
                    
    
            except Exception as e:
                print(driver.current_url)
                print("Error:", e)
                traceback.print_exc()  # This prints the full traceback including the line number
                input('Line-up error at the above')

            
            
            try:
                home_id = both_team_details[0]["team_game_history_id"]
                away_id = both_team_details[1]["team_game_history_id"]

                print(f"{home_id}, {away_id}")

                if not all(map(db_utils.team_stats_exists, [home_id, away_id])):
                    both_team_stats = extract_match_stats(driver, game_stats_url, both_team_details)
                    print(both_team_stats)
                    #input("Team stats")
                    for team_stats in both_team_stats:
                        db_utils.insert_team_statistics(team_stats)
                else:
                    print("Skipping both team Stats.....already exists")
                    #input("Team stats not")

            except Exception as e:
                print("error as team stats", e)
                traceback.print_exc()
                #input("error as team stats")
             
            #input(f"done with {game_detail_url}")
            
        db_utils.set_latest_scraped_team_url(team_url)


           
            

               





def get_details_and_commentary_of_game(driver, espn_id, commentary_url):
    details = {
        "espn_id": espn_id,
        "date": None,
        "referee": None,
        "attendance": None,
        "place": None,
        "state": None,
        "country": None,
        "commentary": None
    }

    # Extract place (stadium name)
    try:
        place_elem = driver.find_element(By.CSS_SELECTOR, field_selector)
        details["place"] = place_elem.text.strip()
    except NoSuchElementException:
        details["place"] = ""

    # Extract datetime and convert to UNIX timestamp
    try:

        #raw_datetime = driver.find_element().text.strip() # e.g., "1:30 AM, 3 April 2024"
        wait = WebDriverWait(driver, 10)
        raw_datetime = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, date_selector))).text.strip()  
        print(raw_datetime)
        if(len(raw_datetime)<20):
            print("time error at", raw_datetime)
            details["date"] = 0
        else:
            dt_obj = datetime.strptime(raw_datetime, "%I:%M %p, %d %B %Y")
            details["date"] = int(dt_obj.timestamp())

    except NoSuchElementException:
        details["date"] = 0
    except Exception as e:
        print(f"time error at {driver.current_url}")
        print(e)
        #input('error')

    # Extract location (e.g., "Saint Paul, Minnesota, USA")
    try:
        location_elem = driver.find_element(By.CSS_SELECTOR, state_country_selector)
        location_parts = [part.strip() for part in location_elem.text.strip().split(",")]
        if len(location_parts) >= 3:
            details["state"] = location_parts[-2]
            details["country"] = location_parts[-1]
        elif len(location_parts) == 2:
            details["state"] = location_parts[0]
            details["country"] = location_parts[1]
        else:
            details["state"] = ""
            details["country"] = ""
    except NoSuchElementException:
        details["state"] = ""
        details["country"] = ""

    # Extract referee name
    try:
        referee_elem = driver.find_element(By.CSS_SELECTOR, referee_selector)
        details["referee"] = referee_elem.text.strip()
    except NoSuchElementException:
        details["referee"] = ""
    
    # Extract referee name
    try:
        attendance_elem = driver.find_element(By.CSS_SELECTOR, attendance_selector)
        details["attendance"] = attendance_elem.text.strip().split(':')[-1]
    except NoSuchElementException:
        details["attendance"] = ""

    driver.get(commentary_url)
    try:
        tbody = driver.find_element(By.CSS_SELECTOR, ".MatchCommentary tbody")
        rows = tbody.find_elements(By.TAG_NAME, 'tr')
        details["commentary"] = parse_commentary_rows(rows)
    except:
       details["commentary"] = ''
       print('error at commentary')
       #input('error at commentary')


    pprint(details)
    #input('Comment Details')

    return details


