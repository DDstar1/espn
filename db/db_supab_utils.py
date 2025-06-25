from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

load_dotenv()  # This loads the variables from .env into the environment

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

LIVE_MINS = 10

def filter_data(data, allowed_fields):
    return {k: v for k, v in data.items() if k in allowed_fields}


def insert_player(data):
    supabase.table("player").upsert([data]).execute()


def player_exists(espn_id):
    response = supabase.table("player").select("espn_id").eq("espn_id", espn_id).execute()
    return len(response.data) > 0


def insert_team(data):
    if data["espn_id"] is None:
        print(f"Skipping insert_team: espn_id is None for team: {data.get('name')}")
        return
    if not team_exists(data["espn_id"]):
        supabase.table("team").insert(data).execute()


def team_exists(espn_id):
    if espn_id is None:
        print("Warning: team_exists called with espn_id=None. Skipping check.")
        return False  # or raise an Exception depending on desired behavior

    response = supabase.table("team").select("espn_id").eq("espn_id", espn_id).execute()
    exists = len(response.data) > 0
    if exists:
        print(f"Team with espn_id {espn_id} already exists.")
    return exists


def insert_game_info(data):
    try:
        if not game_info_exists(data["espn_id"]):
            supabase.table("game_info").insert(data).execute()
    except Exception as e:
        print(f"Error inserting/updating game_info: {e}")
        print(f"data: {data}")
        input("Press Enter to continue...")  # Pause for debugging

def game_info_exists(espn_id):
    response = supabase.table("game_info").select("espn_id").eq("espn_id", espn_id).execute()
    exists = len(response.data) > 0
    if exists:
        print(f"Game Info with espn_id {espn_id} already exists.")
    return exists


def insert_line_up_statistics(data):
    try:
        supabase.table("line_up_statistics").upsert([data]).execute()
    except Exception as e:
        print(f"Error inserting/updating line_up_statistics: {e}")
        print(f"data: {data}")
        input("Press Enter to continue...")


def insert_team_game_history(data):
    filtered_data = filter_data(data,  ["espn_team_id","espn_game_info_id","formation","goals"])

    try:
        response = supabase.table("team_game_history").upsert([filtered_data]).execute()
    except Exception as e:
        print(f"Error inserting/updating team_game_history: {e}")
        print(f"filtered_data: {filtered_data}")
        input("Press Enter to continue...")  # Pause for debugging

    if response.data:
        return response.data[0].get("id")
    else:
        result = supabase.table("team_game_history") \
            .select("id") \
            .eq("espn_team_id", data["espn_team_id"]) \
            .eq("espn_game_info_id", data["espn_game_info_id"]) \
            .execute()
        return result.data[0].get("id") if result.data else None


def insert_team_statistics(data):
    data = filter_data(data,  ["team_game_history_id","shot_on_goals","shot_attempts","fouls","goals", "yellow_cards", "red_cards","corner_kicks","saves","possession_percent"])
    supabase.table("team_statistics").insert(data).execute()


def insert_goal(data):
    supabase.table("goals").upsert([data]).execute()


def insert_foul(data):
    supabase.table("fouls").upsert([data]).execute()


def insert_free_kick(data):
    supabase.table("free_Kick").insert(data).execute()


def insert_offside(data):
    supabase.table("offside").insert(data).execute()


def get_team_game_history_id(espn_game_info_id, espn_team_id):
    result = supabase.table("team_game_history") \
        .select("id") \
        .eq("espn_team_id", espn_team_id) \
        .eq("espn_game_info_id", espn_game_info_id) \
        .execute()
    return result.data[0].get("id") if result.data else None

        


def player_line_up_stat_exists(team_game_history_id, espn_player_id):
    result = supabase.table("line_up_statistics") \
        .select("id") \
        .eq("team_game_history_id", team_game_history_id) \
        .eq("espn_player_id", espn_player_id) \
        .execute()
    return len(result.data) > 0


def team_stats_exists(team_game_history_id):
    print(f"team_game_history_id: {team_game_history_id}, type: {type(team_game_history_id)}")
    result = supabase.table("team_statistics") \
        .select("id") \
        .eq("team_game_history_id", team_game_history_id) \
        .execute()
    return len(result.data) > 0


def set_latest_scraped_team_url(url, status):
    supabase.table("tracker").upsert(
        {
            "scraped_team_url": url,
            "status": status,
            "scraped_at": datetime.utcnow().isoformat()
        },
        on_conflict=["scraped_team_url"]  # 🔥 this is what prevents duplicates
    ).execute()





def get_latest_scraped_team_url():
    """
    Return a dict containing:
    - the oldest 'processing' team URL scraped more than 5 minutes ago,
    or
    - the latest 'processing' team URL newer than 3 minutes ago,
    or
    - the latest 'done' team URL.
    """
    now = datetime.now(timezone.utc)
    live_minutes_win = now - timedelta(minutes=LIVE_MINS)

    # Step 1: Try oldest 'processing' older than 5 mins
    result = supabase.table("tracker") \
        .select("scraped_team_url") \
        .eq("status", "processing") \
        .lte("scraped_at", live_minutes_win.isoformat()) \
        .order("scraped_at", desc=False) \
        .limit(1) \
        .execute()

    if result.data:
        print(f"Found 'processing' older than {LIVE_MINS} mins")
        print(result.data[0]["scraped_team_url"])
      
        return {
            "status": "stale processing",
            "scraped_team_url": result.data[0]["scraped_team_url"]
        }

    # Step 2: Try most recent 'processing' within last 3 mins
    recent_processing = supabase.table("tracker") \
        .select("scraped_team_url") \
        .eq("status", "processing") \
        .gte("scraped_at", live_minutes_win.isoformat()) \
        .order("scraped_at", desc=True) \
        .limit(1) \
        .execute()

    if recent_processing.data:
        print(f"Found recent 'processing' within {LIVE_MINS} mins")
        print(recent_processing.data[0]["scraped_team_url"])
        return {
            "status": "live processing",
            "scraped_team_url": recent_processing.data[0]["scraped_team_url"]
        }

    # Step 3: Fallback to latest 'done'
    fallback_result = supabase.table("tracker") \
        .select("scraped_team_url") \
        .eq("status", "done") \
        .order("scraped_at", desc=True) \
        .limit(1) \
        .execute()

    if fallback_result.data:
        print("Fallback to 'done'")
        print(fallback_result.data[0]["scraped_team_url"])
        return {
            "status": "done",
            "scraped_team_url": fallback_result.data[0]["scraped_team_url"]
        }

    # Nothing found
    print("No suitable team URL found.")
    return {
        "status": None,
        "scraped_team_url": None
    }




def get_all_scraped_and_live_teams():
    """
    Return a list of all team URLs that:
    - are marked as 'done', OR
    - are marked as 'processing' but scraped less than 5 minutes ago.
    """
    now = datetime.now(timezone.utc)
    live_minutes_win = (now - timedelta(minutes=LIVE_MINS)).isoformat()

    # Get all 'done' team URLs
    done_result = supabase.table("tracker") \
        .select("scraped_team_url") \
        .eq("status", "done") \
        .execute()

    # Get 'live processing' team URLs (scraped within last 5 minutes)
    live_processing_result = supabase.table("tracker") \
        .select("scraped_team_url") \
        .eq("status", "processing") \
        .gte("scraped_at", live_minutes_win) \
        .execute()

    # Combine and return
    done_urls = [row["scraped_team_url"] for row in done_result.data] if done_result.data else []
    live_urls = [row["scraped_team_url"] for row in live_processing_result.data] if live_processing_result.data else []

    return done_urls + live_urls
