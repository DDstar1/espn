from utils import extract_espnfitt, my_print
import db.db_fastapi_utils as db_utils


def parse_height_weight(htwt: str):
    """
    Converts ESPN htwt string into (height_meters, weight_kg)
    Example: "5'11\", 165 lbs"
    """
    height_m = None
    weight_kg = None

    try:
        parts = [p.strip() for p in htwt.split(",")]

        # Height
        if "'" in parts[0]:
            feet, inches = parts[0].replace('"', "").split("'")
            height_m = round((int(feet) * 12 + int(inches)) * 0.0254, 2)

        # Weight
        if len(parts) > 1 and "lbs" in parts[1]:
            lbs = int(parts[1].replace("lbs", "").strip())
            weight_kg = round(lbs * 0.453592, 2)

    except Exception:
        pass

    return height_m, weight_kg


def get_all_players_details(lineups):
    """
    Collect player details from lineups JSON in a single loop.

    Returns:
        List of dictionaries matching DB schema
    """
    my_print(f"\n{'='*60}")
    my_print("COLLECTING PLAYER DETAILS")
    my_print(f"{'='*60}\n")

    all_players = []

    if not lineups:
        my_print("✗ No lineups data provided")
        return []

    my_print(f"✓ Found {len(lineups)} team(s) in lineups")

    for team_idx, team in enumerate(lineups, 1):
        my_print(f"\n{'─'*60}")
        my_print(f"Processing Team {team_idx}")
        my_print(f"{'─'*60}")

        players_map = team.get("playersMap", {})
        player_ids = list(players_map.keys())
        my_print(f"✓ Found {len(player_ids)} player(s)")

        for idx, player_id in enumerate(player_ids, 1):
            my_print(f"\n  [{idx}/{len(player_ids)}] Fetching player ID: {player_id}")
            
            if db_utils.player_exists(int(player_id)):
                my_print(f"  ✓ Player already exists in DB. Skipping.")
                continue

            try:
                player_json = extract_espnfitt(
                    f"https://www.espn.com/football/player/_/id/{player_id}",
                    f"player_{player_id}.json"
                )

                ath = (
                    player_json
                    .get("content", {})
                    .get("player", {})
                    .get("plyrHdr", {})
                    .get("ath", {})
                )

                if not ath:
                    my_print(f"  ✗ No athlete data found")
                    continue

                # === PARSE HEIGHT & WEIGHT ===
                height, weight = None, None
                if ath.get("htwt"):
                    height, weight = parse_height_weight(ath["htwt"])

                player_data = {
                    "espn_id": int(player_id),
                    "name": ath.get("dspNm"),
                    "nationality": ath.get("ctz"),
                    "dob": ath.get("dobRaw"),
                    "height": height,
                    "weight": weight,
                }

                # === LOG ===
                my_print(f"  ✓ Name: {player_data['name']}")
                if player_data["nationality"]:
                    my_print(f"  ✓ Nationality: {player_data['nationality']}")
                if player_data["dob"]:
                    my_print(f"  ✓ DOB: {player_data['dob']}")
                if height:
                    my_print(f"  ✓ Height: {height} m")
                if weight:
                    my_print(f"  ✓ Weight: {weight} kg")

                all_players.append(player_data)
                my_print("  ✓ Player added successfully")

            except Exception as e:
                my_print(f"  ✗ Error fetching player {player_id}: {e}")
                continue

    my_print(f"\n{'='*60}")
    my_print("COLLECTION COMPLETE")
    my_print(f"{'='*60}")
    my_print(f"✓ Total players collected: {len(all_players)}")
    my_print(f"{'='*60}\n")

    return all_players
