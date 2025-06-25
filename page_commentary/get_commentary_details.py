
from pprint import pprint
from utils import parse_commentary_rows
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

field_selector = ".Card.GameInfo .GameInfo__Location__Name--noImg"
state_country_selector = ".Card.GameInfo .Location__Text"
date_selector = ".Card.GameInfo .GameInfo__Meta span"
referee_selector = ".Card.GameInfo .GameInfo__List__Item"
attendance_selector = ".Card.GameInfo .Attendance__Numbers"
commentary_selector ='.MatchCommentary tbody'

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
        pass

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
        pass

    # Extract referee name
    try:
        referee_elem = driver.find_element(By.CSS_SELECTOR, referee_selector)
        details["referee"] = referee_elem.text.strip()
    except NoSuchElementException:
        pass
    
    # Extract referee name
    try:
        attendance_elem = driver.find_element(By.CSS_SELECTOR, attendance_selector)
        details["attendance"] = attendance_elem.text.strip().split(':')[-1].replace(",","")
    except NoSuchElementException:
        pass

    driver.get(commentary_url)
    try:
        tbody = driver.find_element(By.CSS_SELECTOR, commentary_selector)
        rows = tbody.find_elements(By.TAG_NAME, 'tr')
        details["commentary"] = parse_commentary_rows(rows)
    except:
       pass
       print('error at commentary')
       #input('error at commentary')


    pprint(details)
    #input('Comment Details')

    return details

