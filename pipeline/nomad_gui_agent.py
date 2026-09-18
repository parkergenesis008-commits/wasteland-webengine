#!/usr/bin/env python3
"""
Nomad GUI Agent v5 — DISARMED (2026-09-18)

变更（P0-2 演练）:
  * 第三方商店（Amazon / Apple Books）自动化访问 + "模拟购买点击" **已永久移除**。
    理由：对 Amazon/Apple 的自动化点击明确违反其条款，且对 SEO 零正向作用。
  * 整条 nomad 默认关闭：NOMAD_ENABLED != "1" 时直接退出，不发任何网络请求。
    理由：自访 + 自点 Google 结果属于操纵信号，且会把自访写进本地日志，
          使"曝光"报告失真（历史周报/月报即为此产物）。

保留：本站页面的人工化阅读模拟（滚动 / 停留），仅供显式 NOMAL_ENABLED=1 时使用。
重新启用前必须先在 GA4 把本机 IP 设为 internal traffic 排除，否则自访污染真实数据。
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

# ── 政策硬开关（2026-09-18, P0-2）─────────────────────────────
# NOMAD_ENABLED 默认 "0"：不发任何网络请求。见文件头说明。
NOMAD_ENABLED = os.environ.get("NOMAD_ENABLED", "0") == "1"
# 第三方商店自动化：永久 False。以下两处代码仍被本开关挡住，双保险。
STORE_AUTOMATION_ENABLED = False

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
    # 书/购买意图(2026-09-09 v2:高月搜索量,直连可购页/书页)
    ("books like Project Hail Mary", "index.html"),
    ("books like The Three-Body Problem", "index.html"),
    ("hard science fiction books 2026", "index.html"),
    ("best hard sci-fi novels physics based", "index.html"),
    ("new sci-fi novels must read 2026", "index.html"),
    ("Alien Dimensions Shepherd's Wasteland Miancheng Yu", "index.html"),
    ("sci-fi book about quantum gravity", "warp-drive-torsion-propagation.html"),
    ("hard sci-fi recommendations reddit", "index.html"),
    ("Alcubierre drive book fiction", "book.html"),
    ("hard science fiction space opera", "index.html"),
    # 物理科普(中量;教育流量 → 文章页 → 侧栏/正文链回书页)
    ("how does Alcubierre warp drive work", "warp-drive-torsion-propagation.html"),
    ("Einstein-Cartan theory explained simply", "cooperative-resonance-torsion.html"),
    ("what is a topological insulator simple", "obstructed-atomic-phantom-grid.html"),
    ("time crystal explained simply", "floquet-temporal-matter.html"),
    ("how do metamaterials work", "qm-tether-exosuit.html"),
    ("Kondo effect simple explanation", "artificial-kondo-lattice.html"),
    ("warp drive positive energy solution", "warp-drive-torsion-propagation.html"),
    # 新兴科技(中量)
    ("mass reduction technology physics", "semi-dirac-mass-nullification.html"),
    ("radar stealth technology future", "type2-superlattice-radar.html"),
    ("topological quantum computing explained", "arena-tripartite-architecture.html"),
    ("superlattice infrared detector how it works", "type2-superlattice-radar.html"),
    ("quantum gravity explained for beginners", "kpz-reality-rendering.html"),
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
    """Google 搜索点击:每天保底 1 次(当日 0 次 → 必做),≥1 后各次 50%,上限 2/天。"""
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
    if today_count == 0:
        return True   # 当日尚无 → 保底执行
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
    if not STORE_AUTOMATION_ENABLED:
        print("  ⏭  商店漏斗已停用（第三方自动化访问 + 模拟购买点击已于 2026-09-18 移除）")
        return None, 0

    store = random.choice(STORE_PAGES)
    store_name = store["name"]
    store_url = store["url"]

    print(f"  📖 Funnel to store: {store_name}")

    browser_open_url(browser, store_url)

    # Scroll through the book page
    scroll_count = random.randint(2, 4)
    dwell = simulate_page_reading(browser, scroll_count=scroll_count)

    # 2026-09-18: "模拟购买点击"整段已物理删除（违反 Amazon/Apple 条款，且无 SEO 作用）。
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
    # 落地页取关键词映射(2026-09-09 修复:原为 random.choice 无视 kw_entry[1],
    # 导致 "time crystal" 搜词点到 KPZ 页;书/购买意图词应落首页/书页)
    fname = kw_entry[1] if len(kw_entry) > 1 else "index.html"
    roots = [p["url"] for p in OUR_PAGES if "/pages/" not in p["url"]]
    base = (roots[0] if roots else OUR_PAGES[0]["url"]).rstrip("/")
    SPECIAL = {"index.html": {"name": "Home", "url": base + "/"},
               "book.html": {"name": "Book", "url": base + "/book.html"}}
    matched = [p for p in OUR_PAGES if p["url"].rstrip("/").endswith("/" + fname)]
    target_page = (matched[0] if matched
                   else SPECIAL.get(fname) if SPECIAL.get(fname) and SPECIAL.get(fname)["url"]
                   else random.choice(OUR_PAGES))
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

    # 2026-09-18: 不再写入捏造的 exposure_rate（自访不是曝光；报告已改为只统计可核实事实）
    log_exposure(target_page["name"], target_url, "self_visit_simulated", dwell_site)

    print(f"  📄 Read: {target_page['name']} ({dwell_site:.0f}s)")

    # ── Step 4: Close（商店漏斗已于 2026-09-18 移除）──
    browser_close_tab()

    print(f"  ✅ Google Route complete: \"{query}\" → {target_page['name']}")


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
    # 2026-09-18: 同上，去掉捏造的 exposure_rate
    log_exposure(target["name"], target_url, "self_visit_simulated", dwell_site)

    print(f"  Dwell: {dwell_site:.0f}s")

    # ── 商店漏斗已于 2026-09-18 移除 ──
    browser_close_tab()

    print(f"  ✅ Direct Route complete: {target['name']}")


# ═══════════════════════════════════════════
#  Route C: Store Direct (fallback)
# ═══════════════════════════════════════════

def simulate_store_direct_route(browser):
    """已停用（2026-09-18）：不再自动化访问第三方商店页。"""
    print("  ⏭  Route C 已停用（第三方商店自动化已移除）")


# ═══════════════════════════════════════════
#  Main entry point
# ═══════════════════════════════════════════

def simulate_physical_traffic():
    if not NOMAD_ENABLED:
        print("\u23ed  Nomad 已关闭（NOMAD_ENABLED != 1）：不发任何网络请求，跳过流量模拟。")
        print("   如需启用，请先在 GA4 把本机 IP 设为 internal traffic 排除，防止自访污染真实数据。")
        return

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    browser = random_browser()

    print(f"\n{'='*50}")
    print(f"NOMAD v4 — {timestamp}")
    print(f"Browser: {browser}")
    print(f"{'='*50}")

    # Decide route
    do_google = should_do_google_search()

    if do_google:
        print("Route A: Google Search → Site")
        simulate_google_search_route(browser)
    else:
        print("Route B: Site")
        simulate_direct_site_route(browser)

    today_count = get_todays_google_search_count()
    weekly = get_weekly_google_search_count()
    print(f"\n📊 Google Searches Today: {today_count}/2")
    print(f"📊 Google Searches This Week: {weekly}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    simulate_physical_traffic()
