from selenium.webdriver.common.by import By
import re

def get_player_field_positions(driver):
    positions = []

    try:
        formation_fields = driver.find_elements(By.CSS_SELECTOR, '.TacticalFormation__Field')
        
        if not formation_fields:
            print("No formation fields found.")
            return positions

        for field in formation_fields:
            li_elements = field.find_elements(By.TAG_NAME, 'li')
            for li in li_elements:
                # Extract transform translate(xpx, ypx)
                style = li.get_attribute("style")
                match = re.search(r'translate\((\d+)px, (\d+)px\)', style)
                if match:
                    x, y = int(match.group(1)), int(match.group(2))
                else:
                    x = y = None

                # Extract player number
                try:
                    number_element = li.find_element(By.CSS_SELECTOR, '.headshot-jerseyV2__player-number')
                    player_number = int(number_element.text.strip())
                except:
                    player_number = None  # Fallback if number not found

                positions.append({
                    "x": x,
                    "y": y,
                    "player_number": player_number
                })

    except Exception as e:
        print(f"Error occurred: {e}")

    return positions
