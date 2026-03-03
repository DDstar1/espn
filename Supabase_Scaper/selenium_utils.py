import os
import traceback
from pprint import PrettyPrinter
import time

import requests


import config
import db.db_fastapi_utils as db_utils
from page_details.get_commentary_details import get_details_and_commentary_of_game
from page_details.get_all_players_stats import get_combined_lineup_stats
from page_details.player_detail import get_all_players_details
from page_details.team_stats import extract_match_stats
from utils import ensure_manager_is_running, extract_espnfitt, extract_all_events_from_seasons, get_team_stats, log_game_time, my_print

pp = PrettyPrinter(indent=2, width=200, compact=True)



def get_links_of_all_games_played(team_url):
    """
    Scrape all games played for a given team URL from ESPN
    and store details in the database.
    
    Args:
        team_url (str): The ESPN team URL to scrape
    """
    my_print("\n" + "="*80)
    my_print(f"🚀 Starting scrape for team: {team_url}")
    my_print("="*80 + "\n")
    
    # ========================================================================
    # STEP 1: Extract Team Information
    # ========================================================================
    my_print("📥 Fetching team results from ESPN...")
    team_results_json = extract_espnfitt(team_url)

    if(not team_results_json):
        my_print(f"⚠️ Failed to fetch team results for team URL {team_url}, skipping...")
        return  # Stop processing if team results are not available


    
    team_logo = team_results_json.get("meta", {}).get("ogMetadata").get("image", "")
    seasons = team_results_json.get("content", {}).get("results", {}).get("seasons", [])
    team_espn_id = team_results_json.get("content", {}).get("results", {}).get("team", {}).get("id")
    team_name = team_results_json.get("content", {}).get("results", {}).get("team", {}).get("displayName")
    

    my_print(f"✅ Team identified: {team_name} (ESPN ID: {team_espn_id})")
    
    # ========================================================================
    # STEP 2: Store Team in Database
    # ========================================================================
    if not db_utils.team_exists(team_espn_id):
        my_print(f"💾 Inserting team '{team_name}' into database...")
        db_utils.insert_team({
            'espn_id': team_espn_id,
            'name': team_name,
            'logo': team_logo
        })
        my_print("✅ Team inserted successfully")
    else:
        my_print(f"ℹ️  Team '{team_name}' already exists in database")
    
    
    # ========================================================================
    # STEP 3: Collect Season Links
    # ========================================================================
    my_print(f"\n📅 Filtering seasons from {config.SCRAPE_END_YR} onwards...")
    season_links = [
        config.BASE_URL + season["link"]
        for season in seasons
        if season.get("value", 0) >= config.SCRAPE_END_YR
    ]
    my_print(f"✅ Found {len(season_links)} relevant season(s)")
    
    # ========================================================================
    # STEP 4: Extract All Games
    # ========================================================================
    my_print("\n🎮 Extracting all games from selected seasons...")
    my_print(f"Seasons: {seasons}")
    my_print(f"Season links: {season_links}")
    all_game_details = extract_all_events_from_seasons(season_links)
    my_print(f"All Games Details: {all_game_details}")
    my_print(f"✅ Found {len(all_game_details)} game(s) to process\n")
    
    # ========================================================================
    # STEP 5: Process Each Game
    # ========================================================================
    for game_idx, both_team_game_detail in enumerate(all_game_details, 1):
        game_start_time = time.perf_counter()

        my_print("\n" + "-"*80)
        my_print(f"🎯 Processing Game {game_idx}/{len(all_game_details)}")
        
        my_print("-"*80)
        my_print(f"Checking if Manager is still running")
        ensure_manager_is_running()
        
        db_utils.set_latest_scraped_team_url(team_url, status="processing")
        espn_game_id = both_team_game_detail["id"]
        
        my_print(f"🆔 Game ID: {espn_game_id}")
        
        # Check if game already processed
        if db_utils.game_info_exists(espn_game_id):
            my_print(f"⏭️  Game {espn_game_id} already exists in database, skipping...")
            continue
        
        # Fetch game data
        my_print("📥 Fetching match stats and commentary...")


        my_both_team_details = []

        commentary_and_matchstats_json = extract_espnfitt(
                f"https://www.espn.co.uk/football/match/_/gameId/{espn_game_id}",
                f"commentary_and_matchstats_{espn_game_id}.json"
            )
        if(not commentary_and_matchstats_json):
            my_print(f"⚠️ Failed to fetch commentary and match stats for game {espn_game_id}, skipping...")
            continue

        
        commentary_gamepackage_dic = commentary_and_matchstats_json.get("content", {}).get("gamepackage", {})
        all_players_lineup_dic = commentary_gamepackage_dic.get("lineUps", [])
        matchstats_gamepackage_dic = commentary_and_matchstats_json.get("content", {}).get("gamepackage", {}).get("mtchStatsGrph", {})

        
        # ====================================================================
        # STEP 5.1: Process Both Teams
        # ====================================================================
        my_print("\n👥 Processing both teams...")
        
        both_team_game_info_raw_score = both_team_game_detail["score"]
        both_team_game_formations = [lineup.get("formation") for lineup in commentary_gamepackage_dic.get("lineUps", []) if lineup.get("formation")]
        my_print("Formations found: ", both_team_game_formations)
        for i, team_game_info in enumerate(both_team_game_detail["competitors"]):
            my_print(team_game_info)
            logo_url = team_game_info.get("logo", "https://secure.espncdn.com/combiner/i?img=/i/teamlogos/default-team-logo-500.png")
            current_team_name = team_game_info.get("displayName")
            team_type = "home" if team_game_info["isHome"] == True else "away"
            
            if not logo_url:
                my_print(f"⚠️ team (missing logo): {current_team_name}")
                
            
            espn_team_id = team_game_info.get("id")
            my_print("raw_score: ", both_team_game_info_raw_score)
            scores = [s.strip() for s in both_team_game_info_raw_score.split("-")]
            
            my_print(f"🏷️  Team Details: {{'espn_id': {espn_team_id}, 'name': '{current_team_name}', 'logo': '{logo_url}'}}")

            # Ensure team exists in database
            db_utils.insert_team({
                'espn_id': espn_team_id,
                'name': current_team_name,
                'logo': logo_url
            })
            
            team_game_history_id = db_utils.get_team_game_history_id(espn_game_id, espn_team_id)  # Get the DB ID for this team's game history

            feed = ((commentary_gamepackage_dic.get("stndngs") or [{}])[0].get("feed") or [])  # Safely extract the first 'feed' from standings

            all_league_entries_list = feed[0].get("entries", []) if feed else []  # Get all team entries from the feed, default empty list
            stats_map_list = feed[0].get("statMap", {}) if feed else {}  # Get stat mapping from the feed, default empty dict
            team_league_stats_json = get_team_stats(espn_team_id, stats_map_list, all_league_entries_list)  # Generate JSON stats for this team

            my_both_team_details.append({
                "team_game_history_id": team_game_history_id,
                "espn_team_id": espn_team_id,
                "espn_game_info_id": espn_game_id,
                "formation": both_team_game_formations[i] if i < len(both_team_game_formations) else None,
                "goals": int(scores[i]),
                "team_type": team_type,
                "league_stats": team_league_stats_json  # <-- add the stats here
            })

        

        my_print(f"✅ Both teams processed: {len(my_both_team_details)} teams")
        my_print(f"✅ Both teams Details: {my_both_team_details}")
        
        # ====================================================================
        # STEP 5.2: Insert Game Info & Commentary
        # ====================================================================
        my_print("\n💬 Inserting game info and commentary...")
        my_print("espn_game_id: {espn_game_id}, commentary_gamepackage_dic : {commentary_gamepackage_dic}")
        game_details = get_details_and_commentary_of_game(espn_game_id, commentary_gamepackage_dic)

        #input("Commentary Done. Press Enter to continue...")

        db_utils.insert_game_info(game_details)
        my_print("✅ Game info inserted")
        
        # ====================================================================
        # STEP 5.3: Insert Team-Game History
        # ====================================================================
        my_print("\n📊 Inserting team-game history...")
        for i, details in enumerate(my_both_team_details):
            inserted_id = db_utils.insert_team_game_history(details)
            
            if inserted_id is None:
                my_print(f"⚠️  Failed to insert team game history for game {details['espn_game_info_id']}")
                continue
            
            my_both_team_details[i]["team_game_history_id"] = inserted_id
            my_print(f"  ✅ Team game history ID: {inserted_id}")
            
    
                
        # ====================================================================
        # STEP 5.4: Insert Players
        # ====================================================================
        my_print("\n👤 Processing and inserting players...")
        my_print(f"✓ Total players in lineup data: {len(all_players_lineup_dic)}")
        my_print(f"First Player is: {all_players_lineup_dic[0] if all_players_lineup_dic else 'No players'}")
        all_players_details_list = get_all_players_details(all_players_lineup_dic)

        #input("Player Details Done. Press Enter to continue...")

        
        for player_dic in all_players_details_list:
            db_utils.insert_player(player_dic)
        
        my_print(f"✅ {len(all_players_details_list)} player(s) processed")
        
        # ====================================================================
        # STEP 5.5: Insert Lineup Statistics
        # ====================================================================
        my_print("\n📈 Processing lineup statistics...")
        try:
            combined_lineup_stats = get_combined_lineup_stats(
                all_players_lineup_dic,
                my_both_team_details[i]["team_game_history_id"]
            )

            #input("Combined lineup statistics extraction complete. Press Enter to continue...")

            
            stats_count = 0
            goals_count = 0
            cards_count = 0
            
            for lineup_stats in combined_lineup_stats:
                for stats in lineup_stats['players_stats']:
                    result = db_utils.insert_line_up_statistics(stats)
                    if(result=="DUPLICATE_KEY"):
                        raise Exception("two_bots_on_one_team_issue")
                    else:   
                        stats_count += 1
                
                for goal in lineup_stats['goals']:
                    db_utils.insert_goal(goal)
                    goals_count += 1
                
                for card in lineup_stats['cards']:
                    db_utils.insert_foul(card)
                    cards_count += 1
            
            my_print(f"✅ Lineup statistics inserted:")
            my_print(f"   • {stats_count} player stat(s)")
            my_print(f"   • {goals_count} goal(s)")
            my_print(f"   • {cards_count} card(s)")
            
        except Exception as e:
            my_print(f"❌ Error while extracting lineup stats: {e}")
            traceback.print_exc()
            
            if str(e) == "two_bots_on_one_team_issue":
                raise
        
        # ====================================================================
        # STEP 5.6: Insert Team Statistics
        # ====================================================================
        my_print("\n📊 Processing team statistics...")
        try:
            home_id = my_both_team_details[0]["team_game_history_id"]
            away_id = my_both_team_details[1]["team_game_history_id"]
            
            if not all(map(db_utils.team_stats_exists, [home_id, away_id])):
                both_team_stats = extract_match_stats(
                    matchstats_gamepackage_dic,
                    my_both_team_details
                )

                #input("Team Stats Done Press Enter to continue...")
                
                for team_stats in both_team_stats:
                    db_utils.insert_team_statistics(team_stats)
                
                my_print(f"✅ Team statistics inserted for both teams")
            else:
                my_print("⏭️  Team statistics already exist, skipping...")
                
        except Exception as e:
            my_print(f"❌ Error while extracting team stats: {e}")
            traceback.print_exc()
        
        my_print(f"\n✅ Game {espn_game_id} processed successfully!")
        
        game_end_time = time.perf_counter()
        duration = game_end_time - game_start_time

        my_print(f"⏱️  Game processed in {duration:.2f} seconds")

        log_game_time(
            game_id=espn_game_id,
            team_name=team_name,
            duration_seconds=duration
        )

        
    
    # ========================================================================
    # COMPLETION
    # ========================================================================
    my_print("\n" + "="*80)
    my_print(f"🎉 SCRAPING COMPLETE: {team_url}")
    my_print(f"📊 Total games processed: {len(all_game_details)}")
    my_print("="*80 + "\n")

   
    