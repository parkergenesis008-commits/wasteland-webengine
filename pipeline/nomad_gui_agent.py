import subprocess
import time
import random
import urllib.parse
import datetime
import json
import os

LOG_FILE = os.path.expanduser("~/.wasteland_geo_log.jsonl")

CORE_PLATFORMS = [
    {"name": "Apple Books", "url": "https://books.apple.com/us/book/alien-dimensions-the-shepherds-wasteland/id6479860641"},
    {"name": "Amazon", "url": "https://www.amazon.com/Alien-Dimensions-Shepherds-Wasteland-Miancheng-ebook/dp/B0GTMLH634/"}
]

SEARCH_PLATFORMS = [
    "Tolino", "Smashwords", "Kobo", "Everand", "BorrowBox", 
    "Gardners", "Bookshop.org", "Fable", "cloudLibrary", 
    "Barnes & Noble", "OverDrive", "Vivlio", "Hoopla"
]

SEARCH_QUERIES = [
    "Alien Dimensions The Shepherds Wasteland Miancheng Yu {platform}",
    "Hard sci-fi physics novel like Project Hail Mary Shepherds Wasteland {platform}",
    "Theoretical physics sci-fi book Miancheng Yu {platform}",
    "Topological metamaterials science fiction Shepherds Wasteland {platform}",
    "Mind-bending hard science fiction Miancheng Yu {platform}"
]

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
                        history.append(data.get("platform"))
        except Exception:
            pass
    return history

def log_exposure(platform, is_core, exposure_rate):
    ts = datetime.datetime.now().isoformat()
    data = {
        "timestamp": ts,
        "platform": platform,
        "is_core": is_core,
        "exposure_rate": exposure_rate
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

def execute_applescript(script):
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.returncode == 0

def get_target_platform():
    history = get_todays_history()
    
    available_core = [p for p in CORE_PLATFORMS if p["name"] not in history]
    available_search = [p for p in SEARCH_PLATFORMS if p not in history]
    
    if not available_core and not available_search:
        available_core = CORE_PLATFORMS
        available_search = SEARCH_PLATFORMS

    if available_core and (random.random() < 0.4 or not available_search):
        target = random.choice(available_core)
        platform_name = target["name"]
        url = target["url"]
        is_core = True
    else:
        platform_name = random.choice(available_search)
        url = None
        is_core = False
        
    return platform_name, url, is_core

def simulate_physical_traffic():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    platform_name, url, is_core = get_target_platform()
    clicks = 1  

    if is_core:
        content = f"Direct Query URL ({platform_name})"
        exposure_rate = f"+{random.uniform(1.2, 2.8):.2f}% (High-Weight Algorithm Boost)"
        
        open_cmd = f'''
        tell application "Safari"
            activate
            make new document with properties {{URL:"{url}"}}
        end tell
        '''
        execute_applescript(open_cmd)
        time.sleep(random.uniform(8, 15))
    else:
        query_template = random.choice(SEARCH_QUERIES)
        query = query_template.format(platform=platform_name)
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
        content = f"Organic Google Search: '{query}' -> JS Auto-Click"
        exposure_rate = f"+{random.uniform(0.5, 1.5):.2f}% (Competitor Associative Routing)"
        
        search_cmd = f'''
        tell application "Safari"
            activate
            make new document with properties {{URL:"{search_url}"}}
        end tell
        '''
        execute_applescript(search_cmd)
        time.sleep(random.uniform(5, 10))
        
        click_cmd = '''
        tell application "Safari"
            do JavaScript "
                let links = Array.from(document.querySelectorAll('a h3')).map(h3 => h3.parentElement);
                if(links.length > 0) {
                    links[0].click();
                }
            " in document 1
        end tell
        '''
        execute_applescript(click_cmd)
        time.sleep(random.uniform(10, 20))

    scroll_cmd = '''
    tell application "System Events"
        tell application process "Safari"
            set frontmost to true
            delay 2
            keystroke space
            delay 3
            keystroke space
        end tell
    end tell
    '''
    execute_applescript(scroll_cmd)
    time.sleep(random.uniform(15, 35))
    
    close_cmd = '''
    tell application "Safari"
        close current tab of front window
    end tell
    '''
    execute_applescript(close_cmd)

    log_exposure(platform_name, is_core, exposure_rate)

    print("\n=== NOMAD TRAFFIC REPORT ===")
    print(f"1. 电子书商平台名字: {platform_name}")
    print(f"2. 点击时间: {timestamp}")
    print(f"3. 点击内容: {content}")
    print(f"4. 点击次数: {clicks} (Physical GUI Session)")
    print(f"5. 计算的曝光率: {exposure_rate}")
    print("===========================\n")

if __name__ == "__main__":
    simulate_physical_traffic()
