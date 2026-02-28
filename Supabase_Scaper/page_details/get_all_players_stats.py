import re
import db.db_fastapi_utils as db_utils
from utils import my_print


def parse_minute(minute_str):
    """
    Converts:
    "84'" → 84
    "90'+3'" → 93
    """
    if not minute_str:
        return None

    nums = list(map(int, re.findall(r"\d+", minute_str)))
    return sum(nums) if nums else None


def get_sub_minute(player_info):
    for ev in player_info.get("plyrPlys", []):
        if ev.get("substitution"):
            return parse_minute(ev.get("minute"))
    return None


def safe_int_or_none(value, default=0):
    """Convert value to int safely (handles strings like '2.0' or floats)"""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def get_combined_lineup_stats(lineups_json, team_game_history_id):
    """
    Extract and combine player lineup statistics from match data.
    """
    my_print(f"\n{'='*60}")
    my_print("EXTRACTING COMBINED LINEUP STATISTICS")
    my_print(f"{'='*60}\n")
    my_print(f"Team Game History ID: {team_game_history_id}")
    
    combined_stats = []

    for team_idx, team in enumerate(lineups_json, 1):
        my_print(f"\n{'─'*60}")
        my_print(f"Processing Team {team_idx}")
        my_print(f"{'─'*60}")
        
        players_map = team.get("playersMap", {})
        unused_players = set(team.get("unused", []))
        
        total_players = len(players_map)
        unused_count = len(unused_players)
        my_print(f"✓ Total players: {total_players}")
        my_print(f"✓ Unused players: {unused_count}")

        players_stats = []
        goals_list = []
        cards_list = []
        skipped_count = 0

        for player_num, (player_id, player_info) in enumerate(players_map.items(), 1):
            my_print(f"\n  [{player_num}/{total_players}] Player ID: {player_id}")
            
            # Skip player if already in DB
            if db_utils.player_line_up_stat_exists(team_game_history_id, player_id):
                my_print(f"  ⊘ Player already exists in DB - skipping")
                skipped_count += 1
                continue

            stats = player_info.get("stats", {})
            is_unused = player_id in unused_players
            
            player_stats = {
                "team_game_history_id": team_game_history_id,
                "player_num": safe_int_or_none(player_info.get("nmbr")),
                "formation_position": safe_int_or_none(player_info.get("frmtnPlc")),
                "espn_player_id": player_id,

                "saves": safe_int_or_none(stats.get("saves")),
                "shots": safe_int_or_none(stats.get("totalShots")),
                "shots_on_target": safe_int_or_none(stats.get("shotsOnTarget")),
                "fouls_commited": safe_int_or_none(stats.get("foulsCommitted")),
                "fouls_suffered": safe_int_or_none(stats.get("foulsSuffered")),
                "assists": safe_int_or_none(stats.get("goalAssists")),
                "offsides": safe_int_or_none(stats.get("offsides")),
                "goals": safe_int_or_none(stats.get("totalGoals")),
                "yellow_cards": safe_int_or_none(stats.get("yellowCards")),
                "red_cards": safe_int_or_none(stats.get("redCards")),

                "subbed_out_in_min": get_sub_minute(player_info),
                "subbed_in_player": player_info.get("subbedInPlayer"),

                "unused_player": is_unused,
            }

            my_print(f"  ✓ Jersey #: {player_stats['player_num']}")
            if is_unused:
                my_print(f"  ⚠ Status: UNUSED")
            
            for dic in player_info.get("plyrPlys", []):
                minute = parse_minute(dic.get("minute"))

                if dic.get("goal"):
                    goals_list.append({
                        "team_game_history_id": team_game_history_id,
                        "espn_player_id": player_id,
                        "time": str(minute),
                        "own_goal": dic.get("ownGoal", False)
                    })

                if dic.get("yellowCard"):
                    cards_list.append({
                        "team_game_history_id": team_game_history_id,
                        "espn_player_id": player_id,
                        "card_type": "yellow",
                        "time": str(minute)
                    })

                if dic.get("redCard"):
                    cards_list.append({
                        "team_game_history_id": team_game_history_id,
                        "espn_player_id": player_id,
                        "card_type": "red",
                        "time": str(minute)
                    })

            players_stats.append(player_stats)

        my_print(f"\n{'─'*60}")
        my_print(f"Team {team_idx} Summary:")
        my_print(f"  • Players processed: {len(players_stats)}")
        my_print(f"  • Players skipped: {skipped_count}")
        my_print(f"  • Total goals: {len(goals_list)}")
        my_print(f"  • Total cards: {len(cards_list)}")
        my_print(f"{'─'*60}")

        combined_stats.append({
            "players_stats": players_stats,
            "goals": goals_list,
            "cards": cards_list
        })

    my_print(f"\n{'='*60}")
    my_print("EXTRACTION COMPLETE")
    my_print(f"{'='*60}")
    my_print(f"✓ Teams processed: {len(combined_stats)}")
    
    total_players = sum(len(team["players_stats"]) for team in combined_stats)
    total_goals = sum(len(team["goals"]) for team in combined_stats)
    total_cards = sum(len(team["cards"]) for team in combined_stats)
    
    my_print(f"✓ Total players: {total_players}")
    my_print(f"✓ Total goals: {total_goals}")
    my_print(f"✓ Total cards: {total_cards}")
    my_print(f"{'='*60}\n")


    return combined_stats
