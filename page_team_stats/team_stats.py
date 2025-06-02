from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import time

def extract_match_stats(url):
    try:
        possession_label = driver.find_element(By.XPATH, XPATH_TEXT_LABEL.format("Possession"))
    except NoSuchElementException:
        return []

    # ==== SELECTORS ====
    XPATH_TEXT_LABEL = '//span[text()="{}"]'
    XPATH_TEXT_CONTAINER = 'following-sibling::div'
    XPATH_TEXT_VALUES = './span'

    # ==== SETUP SELENIUM ====
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(), options=options)

    # ==== NAVIGATE ====
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
            return ["", ""]

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

    # ==== COLLECT RAW STATS ====
    raw_stats = {}
    for label in stat_labels:
        if label == "Possession":
            try:
                possession_label = driver.find_element(By.XPATH, XPATH_TEXT_LABEL.format("Possession"))
                possession_container = possession_label.find_element(By.XPATH, XPATH_TEXT_CONTAINER)
                possession_spans = possession_container.find_elements(By.XPATH, XPATH_TEXT_VALUES)
                values = [span.text.replace('%', '').strip() for span in possession_spans]
                raw_stats[label] = values
            except Exception as e:
                print("Error extracting Possession:", e)
                raw_stats[label] = ["", ""]
        else:
            raw_stats[label] = extract_stat(label)

    # ==== ZIP INTO TWO DICTS ====
    team1_stats = {}
    team2_stats = {}
    for stat, values in raw_stats.items():
        team1_stats[stat] = values[0] if len(values) > 0 else ""
        team2_stats[stat] = values[1] if len(values) > 1 else ""

    # ==== CLEANUP ====
    driver.quit()

    return [team1_stats, team2_stats]

# === Example Usage ===
url = "https://africa.espn.com/football/matchstats/_/gameId/699766"
team_stats = extract_match_stats(url)
print(team_stats)
