import datetime
import os
import random
import subprocess
import time
import sys
import json

LOG_FILE = os.path.expanduser("~/.wasteland_geo_log.jsonl")
TARGET_DAILY_RUNS = 5

def get_todays_runs():
    today_str = datetime.date.today().isoformat()
    runs = 0
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("timestamp", "").startswith(today_str):
                        runs += 1
        except Exception:
            pass
    return runs

def should_run():
    runs = get_todays_runs()
    if runs >= TARGET_DAILY_RUNS:
        return False
        
    now = datetime.datetime.now()
    end_of_day = now.replace(hour=23, minute=59, second=59)
    # Only run between 8 AM and 11 PM
    if now > end_of_day or now.hour < 8:
        return False
        
    remaining_minutes = (end_of_day - now).total_seconds() / 60.0
    remaining_slots = int(remaining_minutes / 15)
    
    if remaining_slots <= 0:
        return True
        
    remaining_runs = TARGET_DAILY_RUNS - runs
    prob = remaining_runs / remaining_slots
    
    return random.random() <= prob

if __name__ == "__main__":
    if not should_run():
        print("[SILENT]")
        sys.exit(0)
        
    # Jitter (5 seconds to 3 minutes) to evade exact-time detection
    jitter = random.randint(5, 180)
    time.sleep(jitter)
    
    base_dir = os.path.expanduser("~/webengine")
    
    try:
        subprocess.run(["python3", "geo_engine/evolution_simulator.py"], cwd=base_dir, check=True)
        subprocess.run(["python3", "pipeline/render_full_page.py"], cwd=base_dir, check=True)
        result = subprocess.run(["python3", "pipeline/nomad_gui_agent.py"], cwd=base_dir, capture_output=True, text=True, check=True)
        
        commit_cmd = f"git add . && git commit -m 'Auto-Geo-Evolution-{datetime.datetime.now().strftime('%Y-%m-%d-%H%M')}' && git push origin main"
        subprocess.run(commit_cmd, shell=True, cwd=base_dir)
        
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error during execution: {e}")
