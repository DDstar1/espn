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

# Global flag to track shutdown
is_shutting_down = False

# Get the directory where this agent executable is located
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    SCRIPT_DIR = os.path.dirname(sys.executable)
    print(f"🔧 Running as EXE from: {SCRIPT_DIR}")
else:
    # Running as Python script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"🔧 Running as Python script from: {SCRIPT_DIR}")

print(f"🔧 Agent directory: {SCRIPT_DIR}")

# Determine which worker to use (prefer .exe if it exists)
WORKER_PATH = None
WORKER_SCRIPT = None

exe_path = os.path.join(SCRIPT_DIR, WORKER_EXE_NAME)
py_path = os.path.join(SCRIPT_DIR, WORKER_PY_NAME)

if os.path.exists(exe_path):
    WORKER_PATH = exe_path
    WORKER_SCRIPT = WORKER_EXE_NAME
    print(f"🔧 Using worker EXE: {WORKER_EXE_NAME}")
elif os.path.exists(py_path):
    WORKER_PATH = py_path
    WORKER_SCRIPT = WORKER_PY_NAME
    print(f"🔧 Using worker Python script: {WORKER_PY_NAME}")
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
    print("\nPress Enter to exit...")
    input()
    sys.exit(1)

print(f"🔧 Worker path: {WORKER_PATH}")


# -------------------------
# SIGNAL HANDLER
# -------------------------
def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
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


# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)


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
            # Check by executable name
            if proc.info['name'] and proc.info['name'].lower() == worker_name:
                mem = proc.info['memory_info'].rss / (1024 * 1024)
                print(f"  Worker PID {proc.info['pid']}: {mem:.2f} MB")
                total += proc.info['memory_info'].rss
                count += 1
            # Also check by full path in cmdline
            elif proc.info['cmdline'] and any(WORKER_PATH.lower() in str(arg).lower() for arg in proc.info['cmdline']):
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
            # Check by executable name
            if proc.info['name'] and proc.info['name'].lower() == worker_name:
                count += 1
                pids.append(proc.info['pid'])
            # Also check by full path in cmdline
            elif proc.info['cmdline'] and any(WORKER_PATH.lower() in str(arg).lower() for arg in proc.info['cmdline']):
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
    killed_pids = set()  # Track PIDs to avoid duplicates
    
    # First pass: collect all worker PIDs
    for proc in psutil.process_iter(['name', 'exe', 'cmdline', 'pid']):
        try:
            pid = proc.info['pid']
            
            # Skip if already processed
            if pid in killed_pids:
                continue
            
            should_kill = False
            
            # Check by executable name
            if proc.info['name'] and proc.info['name'].lower() == worker_name:
                should_kill = True
            # Also check by full path in cmdline
            elif proc.info['cmdline'] and any(WORKER_PATH.lower() in str(arg).lower() for arg in proc.info['cmdline']):
                should_kill = True
            
            if should_kill:
                killed_pids.add(pid)
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Second pass: terminate all workers
    if killed_pids:
        print(f"  Found {len(killed_pids)} worker(s) to terminate...")
        for pid in killed_pids:
            try:
                print(f"  Terminating worker PID {pid}...")
                process = psutil.Process(pid)
                process.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Wait for graceful termination
        print(f"  Waiting for processes to terminate...")
        time.sleep(2)
        
        # Force kill any that didn't terminate
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
    """Spawn a new worker process in a new console window"""
    print(f"🚀 Spawning new worker...")
    print(f"   Executable: {WORKER_PATH}")
    
    try:
        if WORKER_SCRIPT.endswith('.py'):
            # Spawn Python script
            process = subprocess.Popen(
                [sys.executable, WORKER_PATH],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=SCRIPT_DIR
            )
        else:
            # Spawn EXE
            process = subprocess.Popen(
                [WORKER_PATH],
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=SCRIPT_DIR
            )
        
        print(f"✅ Worker spawned with PID: {process.pid}")
        
        log_spawn()
        
        # Give it a moment to start
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
        documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
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
    print(f"   Worker: {WORKER_SCRIPT}")
    print(f"   Worker path: {WORKER_PATH}")
    print(f"   Spawn interval: {SPAWN_INTERVAL} seconds")
    print(f"   Max memory: {MAX_MEMORY_MB} MB")
    print(f"   Max processes: {MAX_PROCESSES}")
    print()
    
    # Check initial state
    print("🔍 Checking for existing workers...")
    existing = count_running_workers()
    
    if existing == 0:
        # Spawn the first worker immediately
        print("🚀 No existing workers found. Spawning initial worker...")
        if not spawn_worker():
            print("\n❌ Failed to spawn initial worker. Press Enter to exit...")
            input()
            return
    else:
        print(f"ℹ️  Found {existing} existing worker(s) already running")
    
    print()
    
    # Main monitoring loop
    while True:
        time.sleep(SPAWN_INTERVAL)
        
        print(f"\n{'='*70}")
        print(f"⏰ Spawn check at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        # Check current state
        print("🔍 Checking current state...")
        mem, count = total_memory_by_workers()
        
        # Decide whether to spawn
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
        
        # Try to kill workers even on error
        try:
            if not is_shutting_down:
                kill_all_workers()
        except:
            pass
        
        print("\nPress Enter to exit...")
        input()