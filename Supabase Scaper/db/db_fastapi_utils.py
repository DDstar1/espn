"""
db_client.py  (drop-in replacement for supabase.py)

All functions have the same signatures and return values as the original
so your scraper workers need zero changes — just replace the import:

    # OLD
    from supabase_client import insert_player, player_exists, ...

    # NEW
    from db_client import insert_player, player_exists, ...
"""

import json
import subprocess
import os
import time
import random
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv
from utils import my_print

load_dotenv()

# ── Worker identity (unchanged from original) ─────────────────────────────────
username = os.getlogin()
try:
    model = subprocess.check_output(
        "wmic computersystem get model", shell=True
    ).decode().split("\n")[1].strip()
    system_model = model.replace(" ", "_")
except Exception:
    system_model = "Unknown"

combined_name = f"{username}---{system_model}"

# ── FastAPI base URL — set API_BASE_URL in your .env ─────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
SCRAPER     = f"{API_BASE_URL}/scraper"
LIVE_MINS   = 60


def _post(endpoint: str, data: dict):
    url = f"{SCRAPER}{endpoint}"
    response = requests.post(url, json=data)
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error for {url}: {e}")
        if response.text:
            print("Response text:", response.text)
        raise

    # Only try JSON if there's content
    if response.text:
        try:
            return response.json()
        except json.JSONDecodeError:
            print("⚠️ Response is not JSON:", response.text)
            return None
    return None  # empty response


def _get(path: str, params: dict = None) -> dict:
    """GET from the FastAPI scraper API and return the JSON response."""
    url = f"{SCRAPER}{path}"
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


# ── Player ────────────────────────────────────────────────────────────────────

def insert_player(data: dict):
    """Upserts a player. Mirrors: supabase.table("player").upsert([data])"""
    _post("/players/upsert", data)


def player_exists(espn_id: int) -> bool:
    """Mirrors: player_exists(espn_id)"""
    result = _get(f"/players/{espn_id}/exists")
    return result["exists"]


# ── Team ──────────────────────────────────────────────────────────────────────

def insert_team(data: dict):
    """
    Inserts a team only if it doesn't exist.
    Mirrors: insert_team(data) — skips if espn_id is None.
    """
    if data.get("espn_id") is None:
        my_print(f"Skipping insert_team: espn_id is None for team: {data.get('name')}")
        return
    _post("/teams/insert", data)


def team_exists(espn_id) -> bool:
    """Mirrors: team_exists(espn_id)"""
    if espn_id is None:
        my_print("Warning: team_exists called with espn_id=None. Skipping check.")
        return False
    result = _get(f"/teams/{espn_id}/exists")
    exists = result["exists"]
    if exists:
        my_print(f"Team with espn_id {espn_id} already exists.")
    return exists


# ── Game Info ─────────────────────────────────────────────────────────────────

def insert_game_info(data: dict):
    """
    Inserts game info only if not already present.
    Mirrors: insert_game_info(data)
    """
    try:
        if not game_info_exists(data["espn_id"]):
            result = _post("/game-info/insert", data)
            my_print("Insert result:", result)
            return result
    except Exception as e:
        my_print(f"Error inserting/updating game_info: {e}")
        my_print(f"data: {data}")


def game_info_exists(espn_id: int) -> bool:
    """Mirrors: game_info_exists(espn_id)"""
    result = _get(f"/game-info/{espn_id}/exists")
    exists = result["exists"]
    if exists:
        my_print(f"Game Info with espn_id {espn_id} already exists.")
    return exists


# ── Team Game History ─────────────────────────────────────────────────────────

def insert_team_game_history(data: dict) -> int:
    """
    Upserts on (espn_team_id, espn_game_info_id) and returns the internal id.
    Mirrors: insert_team_game_history(data) → int
    """
    allowed = ["espn_team_id", "espn_game_info_id", "formation", "goals", "league_stats"]
    filtered = {k: v for k, v in data.items() if k in allowed}
    result = _post("/team-game-history/upsert", filtered)
    return result["id"]


def get_team_game_history_id(espn_game_info_id: int, espn_team_id: int):
    """Mirrors: get_team_game_history_id(espn_game_info_id, espn_team_id)"""
    try:
        result = _get("/team-game-history/id", params={
            "espn_game_info_id": espn_game_info_id,
            "espn_team_id":      espn_team_id,
        })
        return result["id"]
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise


# ── Team Statistics ───────────────────────────────────────────────────────────

def insert_team_statistics(data: dict):
    """Mirrors: insert_team_statistics(data)"""
    allowed = [
        "team_game_history_id", "shot_on_goals", "shot_attempts", "fouls",
        "goals", "yellow_cards", "red_cards", "corner_kicks", "saves",
        "possession_percent",
    ]
    filtered = {k: v for k, v in data.items() if k in allowed}
    _post("/team-statistics/insert", filtered)


def team_stats_exists(team_game_history_id: int) -> bool:
    """Mirrors: team_stats_exists(team_game_history_id)"""
    my_print(f"team_game_history_id: {team_game_history_id}, type: {type(team_game_history_id)}")
    result = _get(f"/team-statistics/{team_game_history_id}/exists")
    return result["exists"]


# ── Line Up Statistics ────────────────────────────────────────────────────────

def insert_line_up_statistics(data: dict):
    """
    Upserts lineup stats.
    Mirrors: insert_line_up_statistics(data) → None | "DUPLICATE_KEY"
    """
    try:
        _post("/lineup-statistics/upsert", data)
        return None
    except requests.HTTPError as e:
        # Map a 409 Conflict back to the original "DUPLICATE_KEY" sentinel
        if e.response.status_code == 409:
            return "DUPLICATE_KEY"
        raise


def player_line_up_stat_exists(team_game_history_id, espn_player_id) -> bool:
    """Mirrors: player_line_up_stat_exists(team_game_history_id, espn_player_id)"""
    if team_game_history_id is None or espn_player_id is None:
        return False
    result = _get("/lineup-statistics/exists", params={
        "team_game_history_id": team_game_history_id,
        "espn_player_id":       espn_player_id,
    })
    return result["exists"]


# ── Match Events ──────────────────────────────────────────────────────────────

def insert_goal(data: dict):
    """Mirrors: insert_goal(data)"""
    _post("/goals/upsert", data)


def insert_foul(data: dict):
    """Mirrors: insert_foul(data)"""
    _post("/fouls/upsert", data)


def insert_free_kick(data: dict):
    """Mirrors: insert_free_kick(data)"""
    _post("/free-kicks/insert", data)


def insert_offside(data: dict):
    """Mirrors: insert_offside(data)"""
    _post("/offsides/insert", data)


# ── Tracker ───────────────────────────────────────────────────────────────────

def set_latest_scraped_team_url(url: str, status: str):
    """Mirrors: set_latest_scraped_team_url(url, status)"""
    full_url = f"{API_BASE_URL}/tracker/upsert"
    print(f"POSTing to: {full_url} with url={url}, status={status}")
    _post("/tracker/upsert", {
        "scraped_team_url": url,
        "status":           status,
        "worker":           combined_name,
    })


def get_latest_scraped_team_url() -> dict:
    """
    Mirrors: get_latest_scraped_team_url()
    Returns: {"status": str | None, "scraped_team_url": str | None}
    """
    result = _get("/tracker/next")
    scraped_team_url = result.get("scraped_team_url")
    status           = result.get("status")

    if scraped_team_url:
        my_print(f"Found URL with status '{status}': {scraped_team_url}")

    return {"status": status, "scraped_team_url": scraped_team_url}


def get_all_scraped_and_live_teams() -> list:
    """
    Mirrors: get_all_scraped_and_live_teams()
    Includes the original randomised sleep before fetching.
    """
    random_seconds = random.randint(1, 10) * 0.5
    my_print(f"Waiting for {random_seconds} seconds before fetching next team url")
    time.sleep(random_seconds)

    return _get("/tracker/active-urls")