import logging
import time
from datetime import datetime
import json
import os
import re
import subprocess
import sys
import psutil
import requests
from json_folder.all_teams import all_teams as team_links_list
import traceback
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# -------------------------
# CONFIG
# -------------------------
MANAGER_PY_NAME = "manager.py"
MANAGER_EXE_NAME = "manager.exe"
WORKER_PY_NAME = "main.py"        # Name of the Python worker file
WORKER_EXE_NAME = "espn_scraper.exe"  # Name of the EXE worker file



# -------------------------
# LOGGING CONFIG
# -------------------------
LOG_FILE = "espn_scraper.log"

# Ensure log directory exists
if os.path.dirname(LOG_FILE):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,  # log everything as INFO
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),  # log to file
        logging.StreamHandler(sys.stdout)                 # log to console
    ]
)


def my_print(string, should_print=True, log_enabled=True):
    if should_print==True: print(string)
    if log_enabled: logging.info(string)
    else: pass




def extract_espnfitt(url: str, output_file_name: str | None = None, log_enabled: bool = False):
    """
    Extract __espnfitt__ JSON data from ESPN pages safely with retry handling.
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    # 🔁 Create session with retry strategy
    session = requests.Session()

    retry_strategy = Retry(
        total=3,                      # retry 3 times
        backoff_factor=2,             # 2s → 4s → 8s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        # ⏳ Small delay to reduce blocking risk
        time.sleep(1.5)

        response = session.get(url, headers=HEADERS, timeout=25)
        response.raise_for_status()

    except requests.exceptions.ReadTimeout:
        print(f"⏳ Timeout while fetching {url}")
        return None

    except requests.exceptions.ConnectionError:
        print(f"🔌 Connection error for {url}")
        return None

    except requests.exceptions.HTTPError as e:
        print(f"🌐 HTTP error for {url}: {e}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed for {url}: {e}")
        traceback.print_exc()
        return None

    html = response.text

    # 🔍 Extract __espnfitt__
    match = re.search(
        r"window\['__espnfitt__'\]\s*=\s*({.*?});",
        html,
        re.DOTALL
    )

    if not match:
        print(f"⚠️ __espnfitt__ not found in {url}")
        return None

    try:
        data = json.loads(match.group(1))
        data = data.get("page", {})
    except json.JSONDecodeError:
        print(f"❌ JSON parsing failed for {url}")
        return None

    # 💾 Optional file logging
    if log_enabled:
        if output_file_name is None:
            url_parts = url.rstrip('/').split('/')
            last_segment = url_parts[-1] if url_parts else "data"
            filename_base = last_segment[-20:] if len(last_segment) >= 20 else last_segment
            output_file_name = f"json_folder/ESPN/{filename_base}.json"
        else:
            output_file_name = f"json_folder/ESPN/{output_file_name}"

        output_dir = os.path.dirname(output_file_name)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        try:
            with open(output_file_name, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save file: {e}")

    return data

def extract_all_events_from_seasons(all_seasons_list):
    """
    Extract full event objects from all season URLs (__espnfitt__)
    """
    all_events = []

    for season_url in all_seasons_list:
        my_print(f"📅 Processing season: {season_url}")

        try:
            team_results_json = extract_espnfitt(season_url,f"season.json")
        except Exception as e:
            my_print(f"⚠️ Failed to fetch season {season_url}: {e}")
            continue

        events = (
            team_results_json
            .get("content", {})
            .get("results", {})
            .get("events", [])
        )

        for event in events:
            # Optional safety: ensure it looks like a match
            if event.get("id") and event.get("link"):
                all_events.append(event)

    return all_events


        

  


def get_espn_id_from_url(url):
    match = re.search(r'/id/(\d+)', url)
    if not match:
        match = re.search(r'/gameId/(\d+)', url)
    if match:
        return int(match.group(1))
    else:
        raise Exception("ID not found in URL")

    






    

def get_index_latest_scraped_team(latest_scraped_team):
    team_url = latest_scraped_team["scraped_team_url"]
    status = latest_scraped_team["status"]

    try:
        index = team_links_list.index(team_url)
        return index + 1 if status == "done" or status == "live processing"  else index
    except ValueError:
        return 0  # If URL not found, start from beginning




def get_current_exe_name():
    """
    Returns the name of the current executable file (even if running as .exe).
    """
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller-built EXE
        return os.path.basename(sys.executable)
    else:
        # Running as a .py script
        return os.path.basename(sys.argv[0])
    


    
def kill_if_too_many_instances(max_instances=2):
    exe_name = get_current_exe_name()
    try:
        result = subprocess.run(
            ["tasklist"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        count = sum(
            1 for line in result.stdout.splitlines()
            if exe_name.lower() in line.lower()
        )

        my_print(f"🧩 Found {count} instance(s) of {exe_name}")

        if count > max_instances:
            my_print(f"⚠️ More than {max_instances} instances of {exe_name} detected. Exiting.")
            sys.exit(0)

    except Exception as e:
        my_print(f"❌ Error checking tasklist: {e}")
        sys.exit(1)



def log_game_time(game_id, team_name, duration_seconds):
    LOG_FILE = "game_processing_time.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    line = (
        f"[{timestamp}] "
        f"Game ID: {game_id} | "
        f"Team: {team_name} | "
        f"Duration: {duration_seconds:.2f} seconds\n"
    )

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


# standings_utils.py

def get_team_stats(team_id: str,  stat_map, entries):
    """
    Return a dict of stats for a specific team_id

    Args:
        entries (list): List of team entries from standings JSON
        stat_map (dict): Mapping of stat keys to their indexes
        team_id (str): ESPN team ID to find

    Returns:
        dict: A dictionary of stat_name -> value
        None: If the team ID is not found
    """

    for entry in entries:
        if entry["team"]["id"] == str(team_id):
            stats_list = entry.get("stats", [])
            
            # Map each stat key to its value using statMap
            team_stats = {
                key: stats_list[info["i"]]  # get value at index
                for key, info in stat_map.items()
                if info["i"] < len(stats_list)  # safety check
            }
            return team_stats
    return None



def ensure_manager_is_running():
    """
    Checks whether manager.py or manager.exe is running.
    If not found, terminates the current worker process immediately.
    """

    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            name = (proc.info['name'] or "").lower()
            cmdline = " ".join(proc.info.get('cmdline') or []).lower()

            # manager.exe case
            if MANAGER_EXE_NAME in name:
                return True

            # manager.py case
            if MANAGER_PY_NAME in cmdline:
                return True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # ❌ Manager not found → kill this worker
    print("🛑 Manager not running. Worker exiting.")
    try:
        psutil.Process(os.getpid()).terminate()
    except Exception:
        os._exit(1)