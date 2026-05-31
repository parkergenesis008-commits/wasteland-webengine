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


def _ping_sitemap(url: str, name: str):
    """Ping a search engine's sitemap submission endpoint."""
    encoded = urllib.request.quote(SITEMAP_URL, safe="")
    ping_url = f"{url}{encoded}"
    try:
        req = urllib.request.Request(ping_url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"  ✓ {name} pinged (HTTP {resp.getcode()})")
    except urllib.error.URLError as e:
        print(f"  {name} ping error: {e}")


def phase_indexnow():
    """Ping Google and Bing IndexNow endpoints to trigger crawl after deploy."""
    print("\n=== Phase 3b: IndexNow Ping ===")
    _ping_sitemap("https://www.google.com/ping?sitemap=", "Google")
    _ping_sitemap("https://www.bing.com/ping?sitemap=", "Bing")


def phase_nomad():
    """Optionally run nomad traffic (20% probability per deploy)."""
    if random.random() > 0.20:
        print("\n=== Phase 4: Nomad Traffic (skipped) ===")
        return
    
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
