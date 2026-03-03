import os
import sys
import time
import subprocess
import psutil
import signal
from datetime import datetime

from utils import WORKER_EXE_NAME, WORKER_PY_NAME


SPAWN_INTERVAL = 5  # seconds between spawn checks
MAX_MEMORY_MB = 500
MAX_PROCESSES = 16

# Platform detection
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

# Global flag to track shutdown
is_shutting_down = False

# Get the directory where this agent executable is located
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
    print(f"🔧 Running as EXE from: {SCRIPT_DIR}")
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"🔧 Running as Python script from: {SCRIPT_DIR}")

print(f"🔧 Agent directory: {SCRIPT_DIR}")
print(f"🔧 Platform: {'Windows' if IS_WINDOWS else 'Linux'}")

# Determine which worker to use
# On Linux, prefer .py since there's no .exe
WORKER_PATH = None
WORKER_SCRIPT = None

exe_path = os.path.join(SCRIPT_DIR, WORKER_EXE_NAME)
py_path = os.path.join(SCRIPT_DIR, WORKER_PY_NAME)

if IS_WINDOWS and os.path.exists(exe_path):
    WORKER_PATH = exe_path
    WORKER_SCRIPT = WORKER_EXE_NAME
    print(f"🔧 Using worker EXE: {WORKER_EXE_NAME}")
elif os.path.exists(py_path):
    WORKER_PATH = py_path
    WORKER_SCRIPT = WORKER_PY_NAME
    print(f"🔧 Using worker Python script: {WORKER_PY_NAME}")
elif IS_LINUX and os.path.exists(exe_path):
    # Fallback: try EXE on Linux (e.g. compiled with PyInstaller)
    WORKER_PATH = exe_path
    WORKER_SCRIPT = WORKER_EXE_NAME
    print(f"🔧 Using worker EXE (Linux): {WORKER_EXE_NAME}")
else:
    print(f"\n❌ ERROR: Worker not found!")
    print(f"   Looking for: {WORKER_EXE_NAME} or {WORKER_PY_NAME}")
    print(f"   In directory: {SCRIPT_DIR}")
    print(f"\n   Current directory contents:")
    try:
        for item in os.listdir(SCRIPT_DIR):
            print(f"      - {item}")
    except Exception as e:
        print(f"      Could not list directory: {e}")
    if IS_WINDOWS:
        print("\nPress Enter to exit...")
        input()
    sys.exit(1)

print(f"🔧 Worker path: {WORKER_PATH}")


# -------------------------
# SIGNAL HANDLER
# -------------------------
def signal_handler(signum, frame):
    """Handle Ctrl+C / SIGTERM gracefully"""
    global is_shutting_down

    if is_shutting_down:
        print(f"\n⚠️  Shutdown already in progress, please wait...")
        return

    print(f"\n\n{'='*70}")
    print(f"🛑 Agent stopped by user at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    kill_all_workers()

    print(f"\n{'='*70}")
    print(f"👋 Agent shutdown complete")
    print(f"{'='*70}\n")

    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# SIGTERM is available on Linux; on Windows it may not fire but register anyway
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)


# -------------------------
# UTILS
# -------------------------
def total_memory_by_workers():
    """Calculate total memory used by all worker processes"""
    total = 0
    count = 0
    worker_name = os.path.basename(WORKER_PATH).lower()

    for proc in psutil.process_iter(['name', 'exe', 'cmdline', 'memory_info', 'pid']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == worker_name:
                mem = proc.info['memory_info'].rss / (1024 * 1024)
                print(f"  Worker PID {proc.info['pid']}: {mem:.2f} MB")
                total += proc.info['memory_info'].rss
                count += 1
            elif proc.info['cmdline'] and any(
                WORKER_PATH.lower() in str(arg).lower()
                for arg in proc.info['cmdline']
            ):
                mem = proc.info['memory_info'].rss / (1024 * 1024)
                print(f"  Worker PID {proc.info['pid']}: {mem:.2f} MB")
                total += proc.info['memory_info'].rss
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    total_mb = total / (1024 * 1024) if total > 0 else 0
    print(f"📊 Total: {count} workers using {total_mb:.2f} MB")
    return total_mb, count


def count_running_workers():
    """Count how many worker processes are running"""
    count = 0
    pids = []
    worker_name = os.path.basename(WORKER_PATH).lower()

    for proc in psutil.process_iter(['name', 'exe', 'cmdline', 'pid']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == worker_name:
                count += 1
                pids.append(proc.info['pid'])
            elif proc.info['cmdline'] and any(
                WORKER_PATH.lower() in str(arg).lower()
                for arg in proc.info['cmdline']
            ):
                count += 1
                pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    print(f"📊 Running workers: {count} (PIDs: {pids})")
    return count


def kill_all_workers():
    """Kill all running worker processes"""
    global is_shutting_down

    if is_shutting_down:
        return

    is_shutting_down = True

    print(f"\n🔪 Terminating all worker processes...")
    worker_name = os.path.basename(WORKER_PATH).lower()
    killed_pids = set()

    for proc in psutil.process_iter(['name', 'exe', 'cmdline', 'pid']):
        try:
            pid = proc.info['pid']
            if pid in killed_pids:
                continue

            should_kill = False

            if proc.info['name'] and proc.info['name'].lower() == worker_name:
                should_kill = True
            elif proc.info['cmdline'] and any(
                WORKER_PATH.lower() in str(arg).lower()
                for arg in proc.info['cmdline']
            ):
                should_kill = True

            if should_kill:
                killed_pids.add(pid)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if killed_pids:
        print(f"  Found {len(killed_pids)} worker(s) to terminate...")
        for pid in killed_pids:
            try:
                print(f"  Terminating worker PID {pid}...")
                process = psutil.Process(pid)
                process.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        print(f"  Waiting for processes to terminate...")
        time.sleep(2)

        for pid in killed_pids:
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    print(f"  Force killing PID {pid}...")
                    process.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        print(f"✅ Terminated {len(killed_pids)} worker(s)")
    else:
        print(f"ℹ️  No workers were running")


def spawn_worker():
    """Spawn a new worker process"""
    print(f"🚀 Spawning new worker...")
    print(f"   Executable: {WORKER_PATH}")

    try:
        if WORKER_SCRIPT.endswith('.py'):
            cmd = [sys.executable, WORKER_PATH]
        else:
            cmd = [WORKER_PATH]

        if IS_WINDOWS:
            # Windows: open in a new console window (EXE) or hidden (script)
            if WORKER_SCRIPT.endswith('.py'):
                creation_flags = subprocess.CREATE_NEW_CONSOLE
            else:
                creation_flags = subprocess.CREATE_NO_WINDOW
            process = subprocess.Popen(
                cmd,
                creationflags=creation_flags,
                cwd=SCRIPT_DIR
            )
        else:
            # Linux: spawn detached from the current terminal
            # Use setsid so the child gets its own process group
            process = subprocess.Popen(
                cmd,
                cwd=SCRIPT_DIR,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True   # equivalent to setsid
            )

        print(f"✅ Worker spawned with PID: {process.pid}")
        log_spawn()
        time.sleep(1)
        return True

    except FileNotFoundError:
        print(f"❌ Worker file not found at: {WORKER_PATH}")
        return False
    except Exception as e:
        print(f"❌ Failed to spawn worker: {e}")
        import traceback
        traceback.print_exc()
        return False


def log_spawn():
    """Log spawn time to file"""
    try:
        if IS_WINDOWS:
            documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
        else:
            # On Linux use ~/.local/share or home directory
            documents_folder = os.path.join(
                os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
            )

        goalgraph_folder = os.path.join(documents_folder, "GoalGraph")
        os.makedirs(goalgraph_folder, exist_ok=True)

        log_file_path = os.path.join(goalgraph_folder, "agent_logs.txt")

        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} - Agent spawned worker\n")
    except Exception as e:
        print(f"⚠️ Could not write to log file: {e}")


# -------------------------
# MAIN AGENT LOOP
# -------------------------
def main():
    print(f"\n{'='*70}")
    print(f"🤖 AGENT STARTED at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")

    print(f"⚙️  Configuration:")
    print(f"   Platform: {'Windows' if IS_WINDOWS else 'Linux'}")
    print(f"   Worker: {WORKER_SCRIPT}")
    print(f"   Worker path: {WORKER_PATH}")
    print(f"   Spawn interval: {SPAWN_INTERVAL} seconds")
    print(f"   Max memory: {MAX_MEMORY_MB} MB")
    print(f"   Max processes: {MAX_PROCESSES}")
    print()

    print("🔍 Checking for existing workers...")
    existing = count_running_workers()

    if existing == 0:
        print("🚀 No existing workers found. Spawning initial worker...")
        if not spawn_worker():
            print("\n❌ Failed to spawn initial worker.")
            if IS_WINDOWS:
                print("Press Enter to exit...")
                input()
            sys.exit(1)
    else:
        print(f"ℹ️  Found {existing} existing worker(s) already running")

    print()

    while True:
        time.sleep(SPAWN_INTERVAL)

        print(f"\n{'='*70}")
        print(f"⏰ Spawn check at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")

        print("🔍 Checking current state...")
        mem, count = total_memory_by_workers()

        print(f"\n📊 Memory: {mem:.2f} MB / {MAX_MEMORY_MB} MB limit")
        print(f"📊 Workers: {count} / {MAX_PROCESSES} max")

        if count == 0:
            print(f"⚠️  No workers running! Spawning new worker...")
            spawn_worker()
        elif count >= MAX_PROCESSES:
            print(f"⏸️  Max workers reached ({MAX_PROCESSES}), waiting...")
        elif mem > MAX_MEMORY_MB:
            print(f"⏸️  Memory limit reached ({mem:.2f} MB > {MAX_MEMORY_MB} MB), waiting...")
        else:
            print(f"✅ Conditions met - spawning new worker!")
            spawn_worker()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Agent error: {e}")
        import traceback
        traceback.print_exc()

        try:
            if not is_shutting_down:
                kill_all_workers()
        except:
            pass

        if IS_WINDOWS:
            print("\nPress Enter to exit...")
            input()

        sys.exit(1)