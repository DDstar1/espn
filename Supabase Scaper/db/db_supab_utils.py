import ast
import random
import subprocess
from supabase import create_client, Client
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import time

from utils import my_print

load_dotenv()  # This loads the variables from .env into the environment

username = os.getlogin()  # logged-in user
# Get the system manufacturer/model (Windows)
try:
    model = subprocess.check_output("wmic computersystem get model", shell=True).decode().split("\n")[1].strip()
    system_model = f"{model}".replace(" ", "_")
except Exception:
    system_model = "Unknown"

# Combine with +
combined_name = f"{username}---{system_model}"

supabase: Client = create_client("https://vxsflheqcgeafumytqgm.supabase.co", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ4c2ZsaGVxY2dlYWZ1bXl0cWdtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYzOTA4NjYsImV4cCI6MjA2MTk2Njg2Nn0.AuIqGGY2DzrJVqcj9yX5wGnp4kggXHuAUJBHtHCSmws")

LIVE_MINS = 60

def filter_data(data, allowed_fields):
    return {k: v for k, v in data.items() if k in allowed_fields}


def insert_player(data):
    supabase.table("player").upsert([data]).execute()


def player_exists(espn_id):
    response = supabase.table("player").select("espn_id").eq("espn_id", espn_id).execute()
    return len(response.data) > 0


def insert_team(data):
    if data["espn_id"] is None:
        my_print(f"Skipping insert_team: espn_id is None for team: {data.get('name')}")
        return
    if not team_exists(data["espn_id"]):
        supabase.table("team").insert(data).execute()


def team_exists(espn_id):
    if espn_id is None:
        my_print("Warning: team_exists called with espn_id=None. Skipping check.")
        return False  # or raise an Exception depending on desired behavior

    response = supabase.table("team").select("espn_id").eq("espn_id", espn_id).execute()
    exists = len(response.data) > 0
    if exists:
        my_print(f"Team with espn_id {espn_id} already exists.")
    return exists


def insert_game_info(data):
    try:
        if not game_info_exists(data["espn_id"]):
            result = supabase.table("game_info").insert(data).execute()
            my_print("Insert result:", result)
            return result
    except Exception as e:
        my_print(f"Error inserting/updating game_info: {e}")
        my_print(f"data: {data}")
       

def game_info_exists(espn_id):
    response = supabase.table("game_info").select("espn_id").eq("espn_id", espn_id).execute()
    exists = len(response.data) > 0
    if exists:
        my_print(f"Game Info with espn_id {espn_id} already exists.")
    return exists


def insert_line_up_statistics(data):
    try:
        supabase.table("line_up_statistics").upsert([data]).execute()
        return None
    except Exception as e:
        err = getattr(e, "args", [None])[0]
        try:
            err_dict = ast.literal_eval(err) if isinstance(err, str) else err
            if isinstance(err_dict, dict) and err_dict.get("code") == "23505":
                return "DUPLICATE_KEY"
        except Exception:
            pass
        # Other errors: raise immediately
        raise




def insert_team_game_history(data):
    filtered_data = filter_data(
        data,
        ["espn_team_id", "espn_game_info_id", "formation", "goals", "league_stats"]
    )

    # Always upsert first
    supabase.table("team_game_history") \
        .upsert(filtered_data, on_conflict="espn_team_id,espn_game_info_id") \
        .execute()

    # ALWAYS fetch after
    result = supabase.table("team_game_history") \
        .select("id") \
        .eq("espn_team_id", data["espn_team_id"]) \
        .eq("espn_game_info_id", data["espn_game_info_id"]) \
        .single() \
        .execute()

    return result.data["id"]

       




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
    # HARD GUARD — never query with invalid IDs
    if team_game_history_id is None or espn_player_id is None:
        return False

    result = (
        supabase.table("line_up_statistics")
        .select("id")
        .eq("team_game_history_id", team_game_history_id)
        .eq("espn_player_id", espn_player_id)
        .limit(1)
        .execute()
    )

    return bool(result.data)

def team_stats_exists(team_game_history_id):
    my_print(f"team_game_history_id: {team_game_history_id}, type: {type(team_game_history_id)}")
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
        "scraped_at": datetime.utcnow().isoformat(),
        "worker": combined_name
    },
    on_conflict=["scraped_team_url"]  # prevents duplicates
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
        my_print(f"Found 'processing' older than {LIVE_MINS} mins")
        my_print(result.data[0]["scraped_team_url"])
      
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
        my_print(f"Found recent 'processing' within {LIVE_MINS} mins")
        my_print(recent_processing.data[0]["scraped_team_url"])
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
        my_print("Fallback to 'done'")
        my_print(fallback_result.data[0]["scraped_team_url"])
        return {
            "status": "done",
            "scraped_team_url": fallback_result.data[0]["scraped_team_url"]
        }

    # Nothing found
    my_print("No suitable team URL found.")
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

    # Randomized sleep between 1 and 200 seconds
    #random_seconds = random.randint(1, 19) * 15
    random_seconds = random.randint(1, 19) * 15
    my_print(f"Waiting for {random_seconds} seconds before fetching next team url")
    time.sleep(random_seconds)

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
