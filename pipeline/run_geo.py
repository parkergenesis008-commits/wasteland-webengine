#!/usr/bin/env python3
"""
Wasteland GEO Pipeline v2 — Unified deployment command.
Phases:
  1. Random content update (pick 1-2 lore pages, add timestamp freshness)
  2. Build site (generate all pages + sitemap + robots)
  3. Git commit & push to GitHub Pages
  3b. IndexNow ping (Google + Bing) to trigger crawl
  4. Optional: Nomad traffic visit (safe: Amazon/Apple direct only)
  
Usage:
  python3 pipeline/run_geo.py                  # Full deploy
  python3 pipeline/run_geo.py --build-only     # Build only, no deploy
  python3 pipeline/run_geo.py --nomad-only     # Nomad traffic only
"""
import argparse
import datetime
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

# Ensure common PATH entries for cron environments (minimal PATH)
_ENV = os.environ.copy()
_PATH_ENTRIES = ["/usr/bin", "/bin", "/usr/local/bin", "/opt/homebrew/bin"]
_EXISTING_PATH = _ENV.get("PATH", "")
for _p in _PATH_ENTRIES:
    if _p not in _EXISTING_PATH:
        _EXISTING_PATH = f"{_p}:{_EXISTING_PATH}"
_ENV["PATH"] = _EXISTING_PATH
_GIT_CMD = "git"  # Will resolve after PATH fix

BASE_DIR = os.path.expanduser("~/webengine")
PAGES_DIR = os.path.join(BASE_DIR, "pages")
LOG_FILE = os.path.expanduser("~/.wasteland_geo_log.jsonl")
BUILD_SCRIPT = os.path.join(BASE_DIR, "pipeline/build_site.py")
NOMAD_SCRIPT = os.path.join(BASE_DIR, "pipeline/nomad_gui_agent.py")
SITEMAP_URL = "https://parkergenesis008-commits.github.io/wasteland-webengine/sitemap.xml"
SITE_HOST = "parkergenesis008-commits.github.io"
SITE_PATH = "/wasteland-webengine"
# Bing IndexNow key(2026-09-09 生成;key 文件随仓库部署在站内,keyLocation 指向子路径)
INDEXNOW_KEY = "b816cd07e940228a2cc47203a94c093a"
INDEXNOW_LOG = os.path.expanduser("~/.wasteland_indexnow.log")

LORES = [
    "artificial-kondo-lattice", "floquet-temporal-matter",
    "semi-dirac-mass-nullification", "qm-tether-exosuit",
    "arena-tripartite-architecture", "obstructed-atomic-phantom-grid",
    "holographic-kpz-projection", "kpz-reality-rendering",
    "type2-superlattice-radar", "electromagnetic-theater-override",
    "cooperative-resonance-torsion"
]


def get_todays_deploy_count():
    """How many full deploys today? Limit to 1 per day to avoid spam."""
    today_str = datetime.date.today().isoformat()
    count = 0
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get("deploy_time", "").startswith(today_str):
                        count += 1
        except: pass
    return count


def log_deploy():
    ts = datetime.datetime.now().isoformat()
    data = {"deploy_time": ts, "type": "full_deploy"}
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")


def should_run():
    """Weekly 15-20 random schedule: ~3 runs/day avg, but bound weekly."""
    now = datetime.datetime.now()
    # Only between 8AM-11PM (wider window)
    if now.hour < 8 or now.hour > 23:
        print("[SILENT] Off-hours")
        return False
    
    # Max 3 deploys per day (scatter across day; cron triggers 1x/d but gives us room)
    if get_todays_deploy_count() >= 3:
        print("[SILENT] Daily cap reached (3/day)")
        return False
    
    # 17.5/7 approx = 2.5x per day on avg. Each cron trigger has ~83% chance to run.
    if random.random() > 0.83:
        print("[SILENT] Random skip")
        return False
    
    return True


def phase_freshen_content():
    """Pick 1-2 random lore pages and add a freshness timestamp."""
    print("=== Phase 1: Content Freshening ===")
    count = random.randint(1, 2)
    selected = random.sample(LORES, min(count, len(LORES)))
    
    for slug in selected:
        lore_path = os.path.join(BASE_DIR, "content/lore", f"{slug}.md")
        if not os.path.exists(lore_path):
            continue
        
        with open(lore_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add/update freshness stamp in a comment format
        stamp = f"\n\n<!-- Last fresh: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')} -->"
        if "<!-- Last fresh:" in content:
            content = content.split("<!-- Last fresh:")[0].rstrip() + stamp
        else:
            content += stamp
        
        with open(lore_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"  ✓ Freshened: {slug}")


def phase_build():
    """Run the site builder."""
    print("\n=== Phase 2: Site Build ===\n")
    result = subprocess.run([sys.executable, BUILD_SCRIPT], capture_output=True, text=True, env=_ENV)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Build error: {result.stderr}")
        return False
    return True


def phase_deploy():
    """Git commit and push."""
    print("\n=== Phase 3: Git Deploy ===")
    ts = datetime.datetime.now().strftime('%Y-%m-%d-%H%M')
    
    try:
        subprocess.run([_GIT_CMD, "add", "."], cwd=BASE_DIR, check=True, env=_ENV)
        subprocess.run(
            [_GIT_CMD, "commit", "-m", f"Auto-GEO-v2-{ts}"],
            cwd=BASE_DIR, capture_output=True, env=_ENV
        )
        subprocess.run([_GIT_CMD, "push", "origin", "main"], cwd=BASE_DIR, check=True, env=_ENV)
        print("  ✓ Deployed to GitHub Pages")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Deploy error: {e}")
        return False


def phase_indexnow():
    """IndexNow 推送(2026-09-09 真实现:Bing/索引方即时爬取;无鉴权,POST urlList)。
    key 文件部署于 https://<host>/wasteland-webengine/indexnow-<KEY>.txt,
    用 keyLocation 指向该文件(GitHub Pages 项目页无法写 host 根)。"""
    print("\n=== Phase 3b: IndexNow Notify ===")
    urls = []
    smap = os.path.join(BASE_DIR, "sitemap.xml")
    try:
        txt = open(smap, encoding="utf-8").read()
        urls = re.findall(r"<loc>(.*?)</loc>", txt)
    except Exception as e:
        print(f"  sitemap read fail: {e}")
    if not urls:
        urls = [f"https://{SITE_HOST}{SITE_PATH}/", f"https://{SITE_HOST}{SITE_PATH}/book.html"]
    payload = {
        "host": SITE_HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://{SITE_HOST}{SITE_PATH}/indexnow-{INDEXNOW_KEY}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", "ignore")
            print(f"  IndexNow {r.status} OK · {len(urls)} URLs · resp={body[:80]}")
            with open(INDEXNOW_LOG, "a") as f:
                f.write(f"{datetime.datetime.now().isoformat()} status={r.status} urls={len(urls)}\n")
    except urllib.error.HTTPError as e:
        print(f"  IndexNow HTTP {e.code}: {e.read().decode('utf-8','ignore')[:120]}")
        with open(INDEXNOW_LOG, "a") as f:
            f.write(f"{datetime.datetime.now().isoformat()} HTTP {e.code} urls={len(urls)}\n")
    except Exception as e:
        print(f"  IndexNow error: {e}")
        with open(INDEXNOW_LOG, "a") as f:
            f.write(f"{datetime.datetime.now().isoformat()} error={e}\n")


def phase_nomad():
    """Nomad traffic: 每天部署后必跑(原 20% 概率已按 2026-09-09 决策改为必跑;
    google 搜索点击保底在 nomad_gui_agent.should_do_google_search 内保证 ≥1/天)。"""
    print("\n=== Phase 4: Nomad Traffic ===")
    result = subprocess.run([sys.executable, NOMAD_SCRIPT], capture_output=True, text=True, env=_ENV)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(f"  Nomad error: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Wasteland GEO Pipeline v2")
    parser.add_argument("--build-only", action="store_true", help="Build only, no deploy")
    parser.add_argument("--nomad-only", action="store_true", help="Nomad traffic only")
    args = parser.parse_args()
    
    if args.nomad_only:
        phase_nomad()
        return
    
    if args.build_only:
        phase_freshen_content()
        phase_build()
        return
    
    # Full pipeline with random gate
    if not should_run():
        print("[SILENT]")
        return
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"=== Wasteland GEO Pipeline v2 — {timestamp} ===\n")
    
    phase_freshen_content()
    if not phase_build():
        sys.exit(1)
    if not phase_deploy():
        sys.exit(1)
    
    phase_indexnow()
    
    # Small delay before nomad
    time.sleep(random.uniform(5, 30))
    phase_nomad()
    
    log_deploy()
    print("\n✅ GEO Pipeline complete.")


if __name__ == "__main__":
    main()
