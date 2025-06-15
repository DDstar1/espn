import json
from selenium_utils import get_links_of_all_games_played
from utils import combined_team_games_bk_path ,all_teams_path, get_index_latest_scraped_team
import db_utils

# Open the file and load its contents
with open(all_teams_path, 'r') as f:
    team_links_list = json.load(f)

latest_scraped_team = db_utils.get_latest_scraped_team_url()
latest_scraped_team_index = get_index_latest_scraped_team(latest_scraped_team)

# Select the first 2 teams
team_links_of_interest = team_links_list[latest_scraped_team_index:20]

# Scrape game data
games_played = get_links_of_all_games_played(team_links_of_interest)

with open(combined_team_games_bk_path, 'r') as f:
    team_game_data_of_interest = json.load(f)[:20]

#games_played_details = get_details_of_all_games_played(team_game_data_of_interest)






