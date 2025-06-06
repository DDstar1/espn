from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
import time

def extract_match_stats(driver, url, both_team_data):
    # ==== SELECTORS ====
    XPATH_TEXT_LABEL = '//span[text()="{}"]'
    XPATH_TEXT_CONTAINER = 'following-sibling::div'
    XPATH_TEXT_VALUES = './span'

    # ==== STAT LABELS TO EXTRACT ====
    stat_labels = [
        "Possession",
        "Shots on Goal",
        "Shot Attempts",
        "Fouls",
        "Yellow Cards",
        "Red Cards",
        "Corner Kicks",
        "Saves"
    ]

    # ==== MAP TO DB-FRIENDLY KEYS ====
    label_db_keys = {
        "Possession": "possession_percent",
        "Shots on Goal": "shot_on_goals",
        "Shot Attempts": "shot_attempts",
        "Fouls": "fouls",
        "Yellow Cards": "yellow_cards",
        "Red Cards": "red_cards",
        "Corner Kicks": "corner_kicks",
        "Saves": "saves"
    }

    # ==== NAVIGATE TO PAGE ====
    driver.get(url)
    time.sleep(5)  # wait for JS content to load

    def extract_stat(label):
        try:
            label_element = driver.find_element(By.XPATH, XPATH_TEXT_LABEL.format(label))
            containers = label_element.find_elements(By.XPATH, XPATH_TEXT_CONTAINER)
            values = []
            for container in containers[:2]:
                spans = container.find_elements(By.XPATH, XPATH_TEXT_VALUES)
                if spans:
                    values.append(spans[0].text.replace('%', '').strip())
            return values
        except Exception as e:
            print(f"Error extracting {label}:", e)
            return [None, None]

    # ==== COLLECT RAW STATS ====
    raw_stats = {}
    for label in stat_labels:
        raw_stats[label] = extract_stat(label)
        
    

    # ==== ZIP INTO TWO DICTS WITH DB-FRIENDLY KEYS ====
    team1_stats = {}
    team2_stats = {}
    for label, values in raw_stats.items():
        db_key = label_db_keys.get(label, label)  # fallback to original label if not mapped
        team1_stats[db_key] = values[0] if len(values) > 0 else ""
        team2_stats[db_key] = values[1] if len(values) > 1 else ""



    # ==== MERGE WITH EXISTING TEAM DATA ====
    if both_team_data and len(both_team_data) == 2:
        merged_data = []
        for team_data, stat_data in zip(both_team_data, [team1_stats, team2_stats]):
            merged = {**team_data, **stat_data}
            merged_data.append(merged)
        return merged_data
    else:
        return [team1_stats, team2_stats]
