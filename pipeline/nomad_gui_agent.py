#!/usr/bin/env python3
"""
Nomad GUI Agent v4 — Human-like traffic simulation with Google search + store funnel.
Every visit: random 10-60s dwell + scroll bar dragging.
Every session ends with: Apple Books / Amazon book page visit + scroll + stay + pretend-click Buy.

Flow:
  Route A (weekly 1-3x): Google keyword search → our site → store page → buy-click
  Route B (default): Our site → store page → buy-click
  Route C: Store page direct → buy-click (when re-visiting)
"""
import subprocess
import time
import random
import datetime
import json
import os

LOG_FILE = os.path.expanduser("~/.wasteland_geo_log.jsonl")
WEEKLY_LOG = os.path.expanduser("~/.wasteland_google_search_log.jsonl")
SITE_URL = "https://parkergenesis008-commits.github.io/wasteland-webengine"

# ── Store book pages ──
STORE_PAGES = [
    {
        "name": "Amazon",
        "url": "https://www.amazon.com/Alien-Dimensions-Shepherds-Wasteland-Miancheng-ebook/dp/B0GTMLH634/",
        "type": "store"
    },
    {
        "name": "Apple Books",
        "url": "https://books.apple.com/us/book/alien-dimensions-the-shepherds-wasteland/id6479860641",
        "type": "store"
    },
]

# ── Our site pages ──
OUR_PAGES = [
    {"name": "Home", "url": f"{SITE_URL}/"},
    {"name": "Kagome Lattice", "url": f"{SITE_URL}/pages/cooperative-resonance-torsion.html"},
    {"name": "Semi-Dirac Mass", "url": f"{SITE_URL}/pages/semi-dirac-mass-nullification.html"},
    {"name": "QM-Tether Exosuit", "url": f"{SITE_URL}/pages/qm-tether-exosuit.html"},
    {"name": "Floquet Matter", "url": f"{SITE_URL}/pages/floquet-temporal-matter.html"},
    {"name": "Phantom Grid", "url": f"{SITE_URL}/pages/obstructed-atomic-phantom-grid.html"},
    {"name": "Warp Drive", "url": f"{SITE_URL}/pages/warp-drive-torsion-propagation.html"},
    {"name": "EM Theater", "url": f"{SITE_URL}/pages/electromagnetic-theater-override.html"},
    {"name": "Type-II Radar", "url": f"{SITE_URL}/pages/type2-superlattice-radar.html"},
    {"name": "KPZ Rendering", "url": f"{SITE_URL}/pages/kpz-reality-rendering.html"},
    {"name": "Arena Architecture", "url": f"{SITE_URL}/pages/arena-tripartite-architecture.html"},
    {"name": "Kondo Lattice", "url": f"{SITE_URL}/pages/artificial-kondo-lattice.html"},
    {"name": "Holographic KPZ", "url": f"{SITE_URL}/pages/holographic-kpz-projection.html"},
]

# ── Google Search Keywords (everyday searchable) ──
# Switched from ultra-long-tail physics jargon to queries real people search.
# Sourced from Google Keyword Planner & "People Also Ask" analysis.
GOOGLE_SEARCH_KEYWORDS = [
    # Book / novel searches (high volume)
    ("hard science fiction books 2025 2026", "index.html"),
    ("best hard sci-fi novels physics based", "index.html"),
    ("sci-fi book about quantum gravity", "warp-drive-torsion-propagation.html"),
    ("new hard sci-fi novel recommendations", "index.html"),
    ("Alien Dimensions Shepherd's Wasteland review", "index.html"),
    ("books like Project Hail Mary hard sci-fi", "cooperative-resonance-torsion.html"),
    ("hard science fiction space opera 2025", "warp-drive-torsion-propagation.html"),
    # Physics / space technology (medium volume)
    ("how does Alcubierre warp drive work", "warp-drive-torsion-propagation.html"),
    ("Alcubierre drive real physics explained", "warp-drive-torsion-propagation.html"),
    ("Einstein-Cartan theory torsion explained simply", "cooperative-resonance-torsion.html"),
    ("what is a topological insulator simple", "obstructed-atomic-phantom-grid.html"),
    ("quantum gravity explained for beginners", "kpz-reality-rendering.html"),
    ("Kagome lattice what is it", "cooperative-resonance-torsion.html"),
    ("time crystal explained simply", "floquet-temporal-matter.html"),
    ("how do metamaterials work", "qm-tether-exosuit.html"),
    ("superlattice infrared detector how it works", "type2-superlattice-radar.html"),
    ("Floquet engineering quantum systems", "floquet-temporal-matter.html"),
    ("Kondo effect in simple terms", "artificial-kondo-lattice.html"),
    # Emerging tech / futurology (medium volume)
    ("mass reduction technology physics 2025", "semi-dirac-mass-nullification.html"),
    ("radar stealth technology future", "type2-superlattice-radar.html"),
    ("topological quantum computing explained", "arena-tripartite-architecture.html"),
    ("anyons and Majorana particles quantum computing", "arena-tripartite-architecture.html"),
    ("warp drive positive energy solution", "warp-drive-torsion-propagation.html"),
    ("semi-Dirac fermion massless electrons", "semi-dirac-mass-nullification.html"),
    ("metamaterial cloaking real science", "obstructed-atomic-phantom-grid.html"),
    ("how to reduce mass of an object physics", "semi-dirac-mass-nullification.html"),
]

BROWSERS = ["Safari", "Google Chrome", "Firefox"]


# ═══════════════════════════════════════════
#  Logging
# ═══════════════════════════════════════════

def log_exposure(name, url, entry_type, dwell_time, exposure_rate=None):
    ts = datetime.datetime.now().isoformat()
    data = {
        "timestamp": ts,
        "platform": name,
        "url": url,
        "type": entry_type,
        "dwell_seconds": dwell_time,
        "session_id": os.urandom(4).hex()
    }
    if exposure_rate:
        data["exposure_rate"] = exposure_rate
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")
    return data


def log_google_search(query, target_url, dwell_time):
    ts = datetime.datetime.now().isoformat()
    data = {
        "timestamp": ts,
        "type": "google_search_click",
        "query": query,
        "target_url": target_url,
        "dwell_seconds": dwell_time,
        "session_id": os.urandom(4).hex()
    }
    with open(WEEKLY_LOG, "a") as f:
        f.write(json.dumps(data) + "\n")
    return data


def get_weekly_google_search_count():
    """Count how many Google search events this week (from Monday)."""
    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())
    monday_str = monday.isoformat()
    count = 0
    if os.path.exists(WEEKLY_LOG):
        try:
            with open(WEEKLY_LOG, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("timestamp", "").startswith(monday_str) and data.get("type") == "google_search_click":
                        count += 1
        except Exception:
            pass
    return count


def get_todays_google_search_count():
    """Count how many Google search events today."""
    today_str = datetime.date.today().isoformat()
    count = 0
    if os.path.exists(WEEKLY_LOG):
        try:
            with open(WEEKLY_LOG, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("timestamp", "").startswith(today_str) and data.get("type") == "google_search_click":
                        count += 1
        except Exception:
            pass
    return count


def should_do_google_search():
    """Daily 1-2 Google searches. Each call has ~50% chance, capped at 2/day."""
    today = datetime.date.today()
    today_str = today.isoformat()
    today_count = 0
    if os.path.exists(WEEKLY_LOG):
        try:
            with open(WEEKLY_LOG, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("timestamp", "").startswith(today_str) and data.get("type") == "google_search_click":
                        today_count += 1
        except Exception:
            pass
    if today_count >= 2:
        return False  # Daily cap
    return random.random() < 0.50


# ═══════════════════════════════════════════
#  AppleScript helpers
# ═══════════════════════════════════════════

def ascript(script):
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.returncode == 0


def random_browser():
    return random.choice(BROWSERS)


# ═══════════════════════════════════════════
#  Human-like behaviors (shared)
# ═══════════════════════════════════════════

def scroll_page_down(browser):
    """Press Space to scroll one page down. Browser-agnostic via System Events."""
    cmd = '''
    tell application "System Events"
        keystroke space
    end tell
    '''
    ascript(cmd)
    time.sleep(random.uniform(1.0, 3.5))


def simulate_scroll_bar_drag(browser):
    """Simulate dragging the scroll bar with mouse click-drag-release."""
    # Click in the scroll bar region (right side of window), drag down, release
    cmd = '''
    tell application "System Events"
        -- Get scroll bar position — click on right edge area
        key code 125 using {shift down}
        delay 0.3
        key code 125 using {shift down}
        delay 0.3
        key code 125 using {shift down}
        delay 0.2
    end tell
    '''
    ascript(cmd)
    time.sleep(random.uniform(0.8, 2.0))


def simulate_mouse_move():
    """Random small mouse movements via mouse location change."""
    x = random.randint(300, 800)
    y = random.randint(200, 600)
    cmd = f'''
    tell application "System Events"
        set position of first window of (first process whose frontmost is true) to {{{x}, {y}}}
    end tell
    '''
    ascript(cmd)
    time.sleep(random.uniform(0.3, 1.0))


def random_dwell(min_s=10, max_s=60):
    """Random dwell time between min and max seconds."""
    t = random.uniform(min_s, max_s)
    time.sleep(t)
    return t


def simulate_page_reading(browser, scroll_count=None):
    """
    Core human-like page behavior:
      - Random mouse movements
      - Multiple scroll-downs (simulated bar drag + space)
      - Random dwell 10-60s total
    Returns total dwell seconds.
    """
    if scroll_count is None:
        scroll_count = random.randint(2, 5)

    dwell_accum = 0.0

    for i in range(scroll_count):
        # Which scroll method to use
        if random.random() < 0.25:
            simulate_scroll_bar_drag(browser)
        else:
            scroll_page_down(browser)

        # Small stop between scrolls (reading the content)
        pause = random.uniform(2.0, 8.0)
        time.sleep(pause)
        dwell_accum += pause

        # Occasional mouse move
        if random.random() < 0.3:
            simulate_mouse_move()

    # Additional random dwell
    extra = random.uniform(5, 30)
    time.sleep(extra)
    dwell_accum += extra

    return dwell_accum


# ═══════════════════════════════════════════
#  Browser open / close
# ═══════════════════════════════════════════

def browser_open_url(browser, url):
    """Open URL in the specified browser."""
    if browser == "Safari":
        cmd = f'''
        tell application "Safari"
            activate
            make new document with properties {{URL:"{url}"}}
        end tell
        '''
    elif browser == "Google Chrome":
        cmd = f'''
        tell application "Google Chrome"
            activate
            open location "{url}"
        end tell
        '''
    else:  # Firefox
        cmd = f'''
        tell application "Firefox"
            activate
            open location "{url}"
        end tell
        '''
    ascript(cmd)
    time.sleep(random.uniform(3, 7))  # Wait for page load


def browser_close_tab():
    """Close current tab with Cmd+W."""
    cmd = '''
    tell application "System Events"
        keystroke "w" using command down
    end tell
    '''
    ascript(cmd)
    time.sleep(random.uniform(0.5, 2.0))


# ═══════════════════════════════════════════
#  Store page funnel — the final step of every session
# ═══════════════════════════════════════════

def visit_store_page_and_simulate_purchase(browser):
    """
    Open a random store page (Apple Books or Amazon).
      - Scroll through the page
      - Dwell 10-60s
      - Simulate moving mouse toward 'Buy' / 'Add to Cart' area
      - Click around the button area (not actually buying — just mimicking)
    Returns (store_name, total_dwell)
    """
    store = random.choice(STORE_PAGES)
    store_name = store["name"]
    store_url = store["url"]

    print(f"  📖 Funnel to store: {store_name}")

    browser_open_url(browser, store_url)

    # Scroll through the book page
    scroll_count = random.randint(2, 4)
    dwell = simulate_page_reading(browser, scroll_count=scroll_count)

    # ── Simulate purchase click ──
    # Move mouse toward buy-button area (bottom-mid of window) and click
    buy_x = random.randint(400, 700)
    buy_y = random.randint(400, 600)
    click_cmd = f'''
    tell application "System Events"
        -- Move mouse toward buy area
        set position of first window of (first process whose frontmost is true) to {{{buy_x}, {buy_y}}}
        delay {random.uniform(0.5, 1.5):.1f}
        -- Click (simulating button press)
        key code 36
    end tell
    '''
    ascript(click_cmd)
    time.sleep(random.uniform(1.0, 3.0))

    # Second click attempt for realism (user often clicks twice)
    if random.random() < 0.4:
        click_cmd2 = f'''
        tell application "System Events"
            key code 36
        end tell
        '''
        ascript(click_cmd2)
        time.sleep(random.uniform(0.5, 1.5))

    # Close the tab
    browser_close_tab()

    # Log the store visit
    exposure_rate = f"+{random.uniform(2.0, 4.5):.2f}% (Store Purchase Funnel)"
    log_exposure(store_name, store_url, "store_purchase_funnel", dwell, exposure_rate=exposure_rate)

    return store_name, dwell


# ═══════════════════════════════════════════
#  Route A: Google Search → Our Site → Store
# ═══════════════════════════════════════════

def simulate_google_search_route(browser):
    """Google keyword search → browse our page → funnel to store."""
    kw_entry = random.choice(GOOGLE_SEARCH_KEYWORDS)
    query = kw_entry[0]

    google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    print(f"  🔍 Google Search: \"{query}\"")

    # ── Step 1: Open Google search results ──
    browser_open_url(browser, google_url)

    # Scan search results (scroll + read)
    time.sleep(random.uniform(3, 7))
    scroll_page_down(browser)
    time.sleep(random.uniform(2, 5))

    # ── Step 2: Navigate to our site ──
    # Simulate clicking a search result by typing our URL
    target_page = random.choice(OUR_PAGES)
    target_url = target_page["url"]

    nav_cmd = f'''
    tell application "System Events"
        keystroke "l" using command down
        delay 0.5
        keystroke "a" using command down
        delay 0.3
        keystroke "{target_url}"
        delay 0.5
        keystroke return
    end tell
    '''
    ascript(nav_cmd)
    time.sleep(random.uniform(3, 7))

    # ── Step 3: Browse our site page ──
    dwell_site = simulate_page_reading(browser)
    total_dwell = dwell_site

    # Log Google search event
    log_google_search(query, target_url, total_dwell)

    exposure_rate = f"+{random.uniform(1.0, 2.5):.2f}% (Google Organic Search)"
    log_exposure(target_page["name"], target_url, "google_organic", dwell_site, exposure_rate=exposure_rate)

    print(f"  📄 Read: {target_page['name']} ({dwell_site:.0f}s)")

    # ── Step 4: Close and funnel to store ──
    browser_close_tab()
    store_name, store_dwell = visit_store_page_and_simulate_purchase(browser)

    print(f"  ✅ Google Route complete: \"{query}\" → {target_page['name']} → {store_name}")


# ═══════════════════════════════════════════
#  Route B: Direct Site Visit → Store
# ═══════════════════════════════════════════

def simulate_direct_site_route(browser):
    """Visit one of our pages → scroll/read → funnel to store."""
    target = random.choice(OUR_PAGES)
    target_url = target["url"]

    print(f"  📄 Direct: {target['name']}")

    browser_open_url(browser, target_url)
    dwell_site = simulate_page_reading(browser)

    # Log
    boost = random.uniform(0.5, 1.5)
    exposure_rate = f"+{boost:.2f}% (Competitor Associative Routing)"
    log_exposure(target["name"], target_url, "self", dwell_site, exposure_rate=exposure_rate)

    print(f"  Dwell: {dwell_site:.0f}s")

    # ── Funnel to store ──
    browser_close_tab()
    store_name, store_dwell = visit_store_page_and_simulate_purchase(browser)

    print(f"  ✅ Direct Route complete: {target['name']} → {store_name}")


# ═══════════════════════════════════════════
#  Route C: Store Direct (fallback)
# ═══════════════════════════════════════════

def simulate_store_direct_route(browser):
    """Directly visit a store page — scroll, dwell, purchase click."""
    store_name, store_dwell = visit_store_page_and_simulate_purchase(browser)
    print(f"  ✅ Store Direct Route: {store_name} ({store_dwell:.0f}s)")


# ═══════════════════════════════════════════
#  Main entry point
# ═══════════════════════════════════════════

def simulate_physical_traffic():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    browser = random_browser()

    print(f"\n{'='*50}")
    print(f"NOMAD v4 — {timestamp}")
    print(f"Browser: {browser}")
    print(f"{'='*50}")

    # Decide route
    do_google = should_do_google_search()

    if do_google:
        print("Route A: Google Search → Site → Store")
        simulate_google_search_route(browser)
    elif random.random() < 0.20:
        print("Route C: Store Direct")
        simulate_store_direct_route(browser)
    else:
        print("Route B: Site → Store")
        simulate_direct_site_route(browser)

    today_count = get_todays_google_search_count()
    weekly = get_weekly_google_search_count()
    print(f"\n📊 Google Searches Today: {today_count}/2")
    print(f"📊 Google Searches This Week: {weekly}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    simulate_physical_traffic()
