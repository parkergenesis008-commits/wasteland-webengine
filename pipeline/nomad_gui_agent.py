#!/usr/bin/env python3
"""
Nomad GUI Agent v2 — Safe traffic simulation.
Removed: Google search auto-click (blacklist risk).
Core: Direct visits to Amazon/Apple Books + random secondary platforms via direct URL.
Uses Safari with human-like behavioral patterns (random scroll, dwell time, browser switching).
"""
import subprocess
import time
import random
import datetime
import json
import os
import urllib.request

LOG_FILE = os.path.expanduser("~/.wasteland_geo_log.jsonl")
SITE_URL = "https://parkergenesis008-commits.github.io/wasteland-webengine"

# ── Safe targets: direct URLs only, NO Google search manipulation ──
CORE_PLATFORMS = [
    {
        "name": "Amazon",
        "url": "https://www.amazon.com/Alien-Dimensions-Shepherds-Wasteland-Miancheng-ebook/dp/B0GTMLH634/",
        "type": "store"
    },
    {
        "name": "Apple Books",
        "url": "https://books.apple.com/us/book/alien-dimensions-the-shepherds-wasteland/id6479860641",
        "type": "store"
    }
]

# Secondary: our own site pages for organic-looking referral traffic
OUR_PAGES = [
    {"name": "Home", "url": f"{SITE_URL}/"},
    {"name": "Kagome Lattice", "url": f"{SITE_URL}/pages/cooperative-resonance-torsion.html"},
    {"name": "Semi-Dirac Mass", "url": f"{SITE_URL}/pages/semi-dirac-mass-nullification.html"},
    {"name": "QM-Tether Exosuit", "url": f"{SITE_URL}/pages/qm-tether-exosuit.html"},
    {"name": "Floquet Matter", "url": f"{SITE_URL}/pages/floquet-temporal-matter.html"},
    {"name": "Phantom Grid", "url": f"{SITE_URL}/pages/obstructed-atomic-phantom-grid.html"},
]

# ── Browser pool (all safe, no Google) ──
BROWSERS = ["Safari", "Google Chrome", "Firefox"]


def get_todays_history():
    today_str = datetime.date.today().isoformat()
    history = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("timestamp", "").startswith(today_str):
                        history.append(data.get("url"))
        except Exception:
            pass
    return history


def log_exposure(name, url, platform_type, dwell_time):
    ts = datetime.datetime.now().isoformat()
    data = {
        "timestamp": ts,
        "platform": name,
        "url": url,
        "type": platform_type,
        "dwell_seconds": dwell_time,
        "session_id": os.urandom(4).hex()
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")
    return data


def execute_applescript(script):
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.returncode == 0


def random_browser():
    return random.choice(BROWSERS)


def get_target_from_history():
    """Pick a target we haven't visited today. If all visited, pick randomly."""
    history = get_todays_history()
    
    # Try core store pages first (40% chance)
    if random.random() < 0.4:
        candidates = [p for p in CORE_PLATFORMS if p["url"] not in history]
        if candidates:
            return random.choice(candidates), "store"
        return random.choice(CORE_PLATFORMS), "store"
    
    # Otherwise visit our own pages
    candidates = [p for p in OUR_PAGES if p["url"] not in history]
    if candidates:
        return random.choice(candidates), "self"
    return random.choice(OUR_PAGES), "self"


def simulate_human_browsing(browser, url):
    """Open URL in specified browser and simulate human behavior."""
    dwell = random.uniform(25, 75)
    
    if browser == "Safari":
        open_cmd = f'''
        tell application "Safari"
            activate
            make new document with properties {{URL:"{url}"}}
        end tell
        '''
        execute_applescript(open_cmd)
        time.sleep(random.uniform(4, 8))
        
        # Simulate scrolling via keyboard
        scroll_pages = random.randint(1, 4)
        for _ in range(scroll_pages):
            scroll_cmd = '''
            tell application "System Events"
                tell application process "Safari"
                    set frontmost to true
                    delay 0.5
                    keystroke space
                end tell
            end tell
            '''
            execute_applescript(scroll_cmd)
            time.sleep(random.uniform(1.5, 5))
        
    elif browser == "Google Chrome":
        open_cmd = f'''
        tell application "Google Chrome"
            activate
            open location "{url}"
        end tell
        '''
        execute_applescript(open_cmd)
        time.sleep(random.uniform(4, 8))
        
        scroll_pages = random.randint(1, 3)
        for _ in range(scroll_pages):
            scroll_cmd = '''
            tell application "System Events"
                tell application process "Google Chrome"
                    set frontmost to true
                    delay 0.3
                    keystroke space
                end tell
            end tell
            '''
            execute_applescript(scroll_cmd)
            time.sleep(random.uniform(2, 6))
    
    else:  # Firefox
        open_cmd = f'''
        tell application "Firefox"
            activate
            open location "{url}"
        end tell
        '''
        execute_applescript(open_cmd)
        time.sleep(random.uniform(5, 10))
        
        scroll_pages = random.randint(1, 3)
        for _ in range(scroll_pages):
            scroll_cmd = '''
            tell application "System Events"
                tell application process "firefox"
                    set frontmost to true
                    delay 0.5
                    keystroke space
                end tell
            end tell
            '''
            execute_applescript(scroll_cmd)
            time.sleep(random.uniform(2, 5))
    
    # Total dwell time
    remaining = max(0, dwell - (scroll_pages * 3) - 6)
    time.sleep(remaining)
    
    # Close tab
    close_cmd = '''
    tell application "System Events"
        keystroke "w" using command down
    end tell
    '''
    execute_applescript(close_cmd)
    time.sleep(random.uniform(1, 3))
    
    return dwell


def simulate_physical_traffic():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    target, target_type = get_target_from_history()
    browser = random_browser()
    
    print(f"\n=== NOMAD TRAFFIC REPORT v2 ===")
    print(f"1. Target: {target['name']}")
    print(f"2. URL: {target['url']}")
    print(f"3. Type: {target_type}")
    print(f"4. Browser: {browser}")
    print(f"5. Time: {timestamp}")
    
    dwell = simulate_human_browsing(browser, target["url"])
    
    data = log_exposure(target["name"], target["url"], target_type, dwell)
    
    print(f"6. Dwell: {dwell:.0f}s")
    print(f"7. Session: {data['session_id']}")
    print(f"===========================\n")


if __name__ == "__main__":
    simulate_physical_traffic()
