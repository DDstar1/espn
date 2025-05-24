from pprint import pprint
import re
import config
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from utils import extract_team_logos_from_detail_page, get_espn_id_from_url, parse_commentary_rows
import db_utils 


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

# Player Bio Selectors
player_position_selector = "//span[@class='Bio__Label ttu mr2 dib clr-gray-04' and text()='Position ']/following-sibling::span[@class='dib flex-uniform mr3 clr-gray-01']"
player_birthdate_selector = "//span[@class='Bio__Label ttu mr2 dib clr-gray-04' and text()='Birthdate']/following-sibling::span[@class='dib flex-uniform mr3 clr-gray-01']"
player_nationality_selector = "//span[@class='Bio__Label ttu mr2 dib clr-gray-04' and text()='Nationality']/following-sibling::span[@class='dib flex-uniform mr3 clr-gray-01']"
player_ht_wt_selector = "//span[@class='Bio__Label ttu mr2 dib clr-gray-04' and text()='HT/WT']/following-sibling::span[@class='dib flex-uniform mr3 clr-gray-01']"
player_name_selector = ".PlayerHeader__Name"

#Game Info Selectors
referee_selector = ".Card.GameInfo .GameInfo__List__Item"
attendance_selector = ".Card.GameInfo .Attendance__Numbers"
state_country_selector = ".Card.GameInfo .Location__Text"
field_selector = ".Card.GameInfo .GameInfo__Location__Name--noImg"
date_selector = ".Card.GameInfo .GameInfo__Meta span"
commentary_selector ='.match-commentary tbody'

# Setup Chrome options (optional, for headless mode)
chrome_options = Options()
#chrome_options.add_argument("--headless")  # Runs Chrome in the background
chrome_options.add_argument('--blink-settings=imagesEnabled=false')


# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)

def get_links_of_all_games_played(team_url_list):
    
    combined_team_games = []
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
            driver.get(game_detail_url)
            logos = driver.find_elements(By.CSS_SELECTOR, game_detail_page_logos_selector)

            for logo in logos:
                if (db_utils.team_exists(team_espn_id)==False):
                    team_espn_id, team_name, logo_url = extract_team_logos_from_detail_page(logo)
                    db_utils.insert_team({'espn_id': team_espn_id, 'name': team_name, 'logo': logo_url})

            if(db_utils.game_info_exists(espn_game_id)==False):
                game_details = get_details_of_game(driver, espn_game_id)
                db_utils.insert_game_info(game_details)
               







def get_details_of_all_games_played(team_data_list):
    for data in team_data_list:
        team_name = data['team name']
        team_games_url = data['team games']
        team_url= data['team url']
        found_team_id = re.search(r'/id/(\d+)', team_url)
        if found_team_id:
            team_id = int(found_team_id.group(1))
        else:
            raise Exception("ID not found in URL") 
        
        for game_url in team_games_url:
            driver.get(game_url)
            game_id = game_url.split("/gameId/")[1].split("/")[0]

            db_utils.insert_team({'espn_id':team_id,'name':team_name})
            db_utils.insert_team_game_history({'team_id':team_id,'game_info_id':game_id})


            




def get_details_of_game(driver, espn_id):
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
        input('error')

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

    current_url = driver.current_url
    commentary_url = current_url.replace('match', 'commentary')
    driver.get(commentary_url)
    try:
        tbody = driver.find_element(By.CSS_SELECTOR, ".MatchCommentary tbody")
        rows = tbody.find_elements(By.TAG_NAME, 'tr')
        details["commentary"] = parse_commentary_rows(rows)
    except:
       details["commentary"] = ''
       print('error at commentary')
       #input('error at commentary')


    #pprint(details)

    return details

