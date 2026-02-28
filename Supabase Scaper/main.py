import os
import traceback
from datetime import datetime

from selenium_utils import get_links_of_all_games_played
from json_folder.all_teams import all_teams as team_links_list
#import db.db_supab_utils as db_utils
import db.db_fastapi_utils as db_utils


def main():
    print(f"[PID {os.getpid()}] 🟢 Worker started at {datetime.now().strftime('%H:%M:%S')}")
    
    # Get teams that haven't been scraped yet
    done_set = set(db_utils.get_all_scraped_and_live_teams())
    remaining_teams = [team for team in team_links_list if team not in done_set]
    
    print(f"[PID {os.getpid()}] 📊 {len(remaining_teams)} teams to scrape")

    
    if not remaining_teams:
        print(f"[PID {os.getpid()}] ✅ All teams scraped. Exiting.")
        return
    
    # Process each team
    for idx, team_url in enumerate(remaining_teams, 1):
        print(f"\n[PID {os.getpid()}] [{idx}/{len(remaining_teams)}] 🔍 {team_url}")
        
        try:
            get_links_of_all_games_played(team_url)
            db_utils.set_latest_scraped_team_url(team_url, status="done")
            print(f"[PID {os.getpid()}] ✅ Done")
            
        except Exception as e:
            if str(e) == "two_bots_on_one_team_issue":
                print(f"[PID {os.getpid()}] ⚠️ Two bots detected, skipping")
            else:
                print(f"[PID {os.getpid()}] ❌ Failed: {e}")
                traceback.print_exc()   # 🔥 this prints full stack trace
                input("Error occurred. Press Enter to continue to next team...")  # Pause on error
                db_utils.set_latest_scraped_team_url(team_url, status="failed")
    
    print(f"\n[PID {os.getpid()}] 🔴 Worker finished at {datetime.now().strftime('%H:%M:%S')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[PID {os.getpid()}] ❌ Critical error: {e}")
        traceback.print_exc()