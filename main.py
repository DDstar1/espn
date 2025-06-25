import importlib
import json
import config
import time
from selenium_utils import get_links_of_all_games_played
from utils import combined_team_games_bk_path, all_teams_path, get_index_latest_scraped_team

db_utils = importlib.import_module(config.WHICH_DB)

# Load team list once
with open(all_teams_path, 'r') as f:
    team_links_list = json.load(f)



while True:
    # Convert to set for fast lookup
    done_set = set(db_utils.get_all_scraped_and_live_teams())
    
    # Get latest scraped info (a dict with 'scraped_team_url' and 'status')
    latest_scraped_info = db_utils.get_latest_scraped_team_url()
    latest_scraped_team_url = latest_scraped_info["scraped_team_url"]

    # Get index of the latest scraped team, adjusted based on status
    start_index = get_index_latest_scraped_team(latest_scraped_info)

    # Filter the remaining unscraped teams, preserving order
    remaining_teams = [
        team_url for team_url in team_links_list
        if team_url not in done_set
    ]

    if not remaining_teams:
        print("✅ All teams scraped.")
        break

    # Pick the next team to scrape
    team_to_scrape = remaining_teams[0]

    remaining_teams = None
    print(f"\n🔍 Scraping team: {team_to_scrape}")
    games_played = get_links_of_all_games_played(team_to_scrape)
    print(f"\ndone with {team_to_scrape}\n")
    db_utils.set_latest_scraped_team_url(team_to_scrape, status="done")

  