from utils import my_print


def extract_match_stats(data, both_team_details):
    """
    Extracts team statistics from match data and merges them with base team dictionaries.
    """

    my_print(f"\n{'='*60}")
    my_print("EXTRACTING MATCH STATISTICS")
    my_print(f"{'='*60}\n")

    # Mapping from API names to desired keys
    stat_mapping = {
        "Possession": "possession_percent",   # FLOAT
        "Shots on Goal": "shots_on_goal",      # INT
        "Shot Attempts": "shot_attempts",      # INT
        "Fouls": "fouls",                      # INT
        "Yellow Cards": "yellow_cards",        # INT
        "Red Cards": "red_cards",              # INT
        "Corner Kicks": "corner_kicks",        # INT
        "Saves": "saves"                       # INT
    }

    FLOAT_FIELDS = {"possession_percent"}

    my_print(f"✓ Stat mapping initialized with {len(stat_mapping)} categories")

    # Extract stats from API data
    try:
        stats_data = data["stats"][0]["data"]
        my_print(f"✓ Found {len(stats_data)} stat entries in data")
    except (KeyError, IndexError) as e:
        my_print(f"✗ Error accessing stats data: {e}")
        return both_team_details

    team1_data = both_team_details[0].copy()
    team2_data = both_team_details[1].copy()

    team1_name = team1_data.get("name", "Team 1")
    team2_name = team2_data.get("name", "Team 2")

    my_print(f"\n{'─'*60}")
    my_print(f"Processing stats for: {team1_name} vs {team2_name}")
    my_print(f"{'─'*60}\n")

    stats_processed = 0

    for stat in stats_data:
        stat_name = stat.get("name")

        if stat_name not in stat_mapping:
            my_print(f"  ⊘ Skipping unmapped stat: {stat_name}")
            continue

        key = stat_mapping[stat_name]
        values = stat.get("values", [])

        if len(values) < 2:
            my_print(f"  ✗ Insufficient values for {stat_name}")
            continue

        try:
            raw_team1 = values[0]
            raw_team2 = values[1]

            if key in FLOAT_FIELDS:
                team1_value = float(raw_team1)
                team2_value = float(raw_team2)
            else:
                team1_value = int(float(raw_team1))
                team2_value = int(float(raw_team2))

            team1_data[key] = team1_value
            team2_data[key] = team2_value

            if key in FLOAT_FIELDS:
                my_print(
                    f"  ✓ {stat_name:.<20} "
                    f"{team1_name}: {team1_value}% | {team2_name}: {team2_value}%"
                )
            else:
                my_print(
                    f"  ✓ {stat_name:.<20} "
                    f"{team1_name}: {team1_value} | {team2_name}: {team2_value}"
                )

            stats_processed += 1

        except (ValueError, TypeError) as e:
            my_print(f"  ✗ Error converting values for {stat_name}: {e}")

    my_print(f"\n{'='*60}")
    my_print("EXTRACTION COMPLETE")
    my_print(f"{'='*60}")
    my_print(f"✓ Successfully processed {stats_processed}/{len(stat_mapping)} mapped stats")
    my_print(f"{'='*60}\n")

    

    return [team1_data, team2_data]
