from selenium.webdriver.common.by import By
import re

def get_player_field_positions(driver, table_elem):
    positions = []

    try:
        formation_fields = table_elem.find_elements(By.CSS_SELECTOR, '.TacticalFormation__Field')
        if not formation_fields:
            print("No formation fields found.")
            return positions

        for field in formation_fields:
            li_elements = field.find_elements(By.TAG_NAME, 'li')
            for li in li_elements:

                try:
                    number_element = li.find_element(By.CSS_SELECTOR, '.headshot-jerseyV2__player-number')
                    player_number = int(number_element.text.strip())
                except:
                    player_number = None

                # Extract transform translate(xpx, ypx)
                style = li.get_attribute("style")
                match = re.search(r'translate\((-?\d+)px,\s*(-?\d+)px\)', style)
                if match:
                    x, y = int(match.group(1)), int(match.group(2))
                else:
                    x = y = None
                    print(f"Style: {style}, Match: {match.groups() if match else None}, Player #: {player_number}")

                positions.append({
                    "position_x": x,
                    "position_y": y,
                    "player_number": player_number
                })

    except Exception as e:
        print(f"Error occurred: {e}")
        return positions

    # Normalization
    if not positions or positions[0]['position_x'] is None or positions[0]['position_y'] is None:
        print("Cannot normalize positions: invalid goalkeeper coordinates.")
        return positions

    # Reference (goalkeeper)
    origin_x = positions[0]['position_x']
    origin_y = positions[0]['position_y']

    # Compute max range from goalkeeper
    max_dx = max(abs(p['position_x'] - origin_x) for p in positions if p['position_x'] is not None)
    max_dy = max(abs(p['position_y'] - origin_y) for p in positions if p['position_y'] is not None)

    for p in positions:
        if p['position_x'] is None or p['position_y'] is None:
            continue  # Skip invalid data
        dx = p['position_x'] - origin_x
        dy = p['position_y'] - origin_y

        # Avoid divide-by-zero
        norm_x = (dx / max_dx * 100) if max_dx != 0 else 0
        norm_y = (dy / max_dy * 100) if max_dy != 0 else 0

        p['position_x'] = round(norm_x)
        p['position_y'] = round(norm_y)

    return positions
