#!/usr/bin/env python3
"""
Wasteland GEO Pipeline v2 — Unified deployment command.
Phases:
  1. Random content update (pick 1-2 lore pages, add timestamp freshness)
  2. Build site (generate all pages + sitemap + robots)
  3. Git commit & push to GitHub Pages
  3b. IndexNow ping (Google + Bing) to trigger crawl
  4. Optional: Nomad traffic visit (2026-09-18 起默认关闭; 启用需 NOMAD_ENABLED=1, 且不含任何第三方商店自动化)
  
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


def phase_qa_inject(dry_run: bool = False):
    """[激进模式 2026-09-10] 把当日热门问题注入对应 lore 页(延伸问答 + FAQ schema)。
    幂等; 无当日 qa 文件时静默跳过, 不影响部署。

    🎯 [2026-09-11] 先由 pipeline/queue_top.py 从 QUEUE.md 当日段选出
    「权重 + 相关性」最高的一条作为**当日主推**，优先注入 + 交给 freshen 优先刷新。
    dry_run=True → 只走主推选题 + 注入器 --dry-run（不写任何文件，用于验证）。
    """
    print("=== Phase 1a: Hot-Question Q&A Injection (激进模式) ===")
    script = os.path.join(BASE_DIR, "pipeline/geo_qa_inject.py")
    if not os.path.exists(script):
        print("  (无注入器, 跳过)")
        return []

    # ── 🎯 当日主推选题（QUEUE.md 权重+相关性最高） ──────────────
    priority = None
    try:
        sel = os.path.join(BASE_DIR, "pipeline/queue_top.py")
        if os.path.exists(sel):
            sr = subprocess.run([sys.executable, sel, "--json"], capture_output=True,
                                text=True, env=_ENV, cwd=BASE_DIR, timeout=60)
            line = (sr.stdout or "").strip().splitlines()
            if sr.returncode == 0 and line:
                top = json.loads(line[-1])
                priority = top.get("slug")
                print(f"  🎯 当日主推(权重+相关性最高): [{priority}] "
                      f"score={top.get('score')} (权重 {top.get('weight')} + 相关性 {top.get('relevance')}) "
                      f"rank#{top.get('rank')} — {str(top.get('question'))[:56]}")
            else:
                print(f"  (选题器无输出 rc={sr.returncode})")
        else:
            print("  (无选题器 queue_top.py, 按队列默认顺序)")
    except Exception as e:
        print(f"  ⚠️ 主推选题失败(不影响注入): {e}")

    cmd = [sys.executable, script] + (["--priority", priority] if priority else []) \
        + (["--dry-run"] if dry_run else [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           env=_ENV, cwd=BASE_DIR, timeout=120)
        out = (r.stdout or "").strip()
        if out:
            print(out)
        if r.returncode != 0:
            print(f"  ⚠️ 注入器退出码 {r.returncode}: {(r.stderr or '')[:200]}")
        # 解析注入了哪些 slug, 供 freshen 阶段优先刷新；主推置顶
        slugs = re.findall(r"✓ 注入 (\S+)", out)
        if not slugs:
            # dry-run 形式: "[dry-run] 会注入 → content/lore/<slug>.md  Q: ..."
            slugs = re.findall(r"会注入 → content/lore/([^./]+)\.md", out)
        if priority and priority in slugs:
            slugs = [priority] + [s for s in slugs if s != priority]
        return slugs
    except Exception as e:
        print(f"  ⚠️ 注入器异常(不影响部署): {e}")
        return []


def phase_freshen_content(prefer_slugs=None):
    """Pick 1-2 random lore pages and add a freshness timestamp.
    prefer_slugs: 优先刷新这些页(通常是本轮刚注入问答的页, 让"内容真变了"的信号更强)。"""
    print("=== Phase 1: Content Freshening ===")
    count = random.randint(1, 2)
    picked = []
    for s in (prefer_slugs or []):
        if s in LORES and s not in picked:
            picked.append(s)
    while len(picked) < min(count, len(LORES)):
        cand = random.choice(LORES)
        if cand not in picked:
            picked.append(cand)
    selected = picked
    
    for slug in selected:
        lore_path = os.path.join(BASE_DIR, "content/lore", f"{slug}.md")
        if not os.path.exists(lore_path):
            continue
        
        with open(lore_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add/update freshness stamp in a comment format
        stamp = f"\n\n<!-- Last fresh: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')} -->"
        # ⚠️ [2026-09-10 修复] 旧实现用 content.split("<!-- Last fresh:")[0] 截断文件 —
        #    会把标记之后的**所有内容**(含 geo_qa_inject 追加的「延伸问答」块)一并删除。
        #    改为只替换时间戳本身, 保留正文与注入块。
        content = re.sub(r"\n*<!-- Last fresh:.*?-->", "", content, flags=re.S).rstrip()
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


# ═══════════════════════════════════════════
#  内容驱动部署（2026-09-18）
# ═══════════════════════════════════════════
#  背景：过去每天把同一批 14 个 URL 重复 commit+push+IndexNow，页面内容其实没变，
#  只是被刷新了 "Last fresh" 时间戳。既污染 git 历史，也让 IndexNow 推送失去意义
#  （无法表达"哪一页真的变了"）。现改为：本轮无实质内容变更 → 不部署、不推送。
_FRESH_RE = re.compile(r"<!--\s*Last fresh:.*?-->")


def _git(*args):
    return subprocess.run([_GIT_CMD, *args], cwd=BASE_DIR,
                          capture_output=True, text=True, env=_ENV)


def changed_files():
    """工作树中被改动的文件 [(status, path)]（排除 __pycache__）。"""
    out = _git("status", "--porcelain")
    items = []
    for line in out.stdout.splitlines():
        if len(line) < 4:
            continue
        status, path = line[:2].strip(), line[3:].strip()
        if "__pycache__" in path or path.endswith(".pyc"):
            continue
        items.append((status, path))
    return items


def _mask_freshness(text):
    return _FRESH_RE.sub("", text)


def is_freshness_only(path):
    """该文件相对 HEAD 只有 "Last fresh" 戳变化 → True（不算实质变更）。

    删除文件 / 新增文件 / 其它任何改动都算实质变更。
    """
    full = os.path.join(BASE_DIR, path)
    if not os.path.exists(full):
        return False
    head = _git("show", f"HEAD:{path}")
    if head.returncode != 0:
        return False
    try:
        current = open(full, encoding="utf-8", errors="replace").read()
    except Exception:
        return False
    return _mask_freshness(head.stdout) == _mask_freshness(current)


def substantive_changes():
    """返回 (全部改动, 实质改动)。"""
    ch = changed_files()
    return ch, [(s, p) for s, p in ch if not is_freshness_only(p)]


def changed_urls(subs):
    """把实质性改动的文件映射为站点 URL —— 只推送这些。

    新页面/站点结构变化会让 sitemap.xml 变化，此时把 sitemap 自身也推给引擎
    （IndexNow 接受 sitemap URL，等于告诉它"地图更新了"）。
    """
    urls = []
    for _, path in subs:
        if path == "index.html":
            urls.append(f"https://{SITE_HOST}{SITE_PATH}/")
        elif path == "book.html":
            urls.append(f"https://{SITE_HOST}{SITE_PATH}/book.html")
        elif path.startswith("pages/") and path.endswith(".html"):
            urls.append(f"https://{SITE_HOST}{SITE_PATH}/{path}")
        elif path == "sitemap.xml":
            urls.append(f"https://{SITE_HOST}{SITE_PATH}/sitemap.xml")
    return sorted(set(urls))


def log_deploy_skipped(n_freshness):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({
            "type": "deploy_skipped",
            "reason": "no_substantive_change",
            "timestamp": datetime.datetime.now().isoformat(),
            "freshness_only_files": n_freshness,
        }) + "\n")


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


def phase_indexnow(urls=None):
    """IndexNow 推送(2026-09-09 真实现:Bing/索引方即时爬取;无鉴权,POST urlList)。

    2026-09-18: 支持只推"本轮真正变更"的 URL —— 全量重复推送无法表达哪页变了。
      - urls=None  → 回退为 sitemap 全量（仅手动/调试用）
      - urls=[]    → 本轮变更不涉及页面，直接跳过（不再误推全量）
      - urls=[...] → 只推这些

    key 文件部署于 https://<host>/wasteland-webengine/indexnow-<KEY>.txt,
    用 keyLocation 指向该文件(GitHub Pages 项目页无法写 host 根)。"""
    print("\n=== Phase 3b: IndexNow Notify ===")
    if urls is None:
        smap = os.path.join(BASE_DIR, "sitemap.xml")
        try:
            txt = open(smap, encoding="utf-8").read()
            urls = re.findall(r"<loc>(.*?)</loc>", txt)
        except Exception as e:
            print(f"  sitemap read fail: {e}")
    elif not urls:
        print("  本轮变更不涉及页面 URL（如仅脚本/文档）→ 跳过 IndexNow 推送")
        return
    else:
        print(f"  仅推送本轮变更的 {len(urls)} 个 URL")
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
    """Nomad 流量模拟 — 2026-09-18 起默认关闭（P0-2）

    关闭理由：
      1. 自访 + 自点 Google 搜索结果属操纵信号，对排名非正向；对 Amazon/Apple
         的自动化点击另有明确条款风险（已物理删除）。
      2. 自访会被写进 ~/.wasteland_geo_log.jsonl，使"曝光"报告失真——历史周报/
         月报统计的正是这些自访。
    本阶段保留为显式可选项：只有 NOMAD_ENABLED=1 才执行，且永远不会再碰第三方页面。
    """
    print("\n=== Phase 4: Nomad Traffic ===")
    if os.environ.get("NOMAD_ENABLED", "0") != "1":
        print("  ⏭  跳过：NOMAD_ENABLED != 1（默认关闭，详见 phase_nomad docstring）")
        return
    # 2026-09-18: 显式透传 NOMAD_ENABLED，不用模块导入时的 _ENV 快照，
    # 避免"父进程判为启用、子进程却看不到该变量"的两层不一致。
    child_env = dict(_ENV)
    child_env["NOMAD_ENABLED"] = os.environ.get("NOMAD_ENABLED", "0")
    result = subprocess.run([sys.executable, NOMAD_SCRIPT], capture_output=True, text=True, env=child_env)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(f"  Nomad error: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Wasteland GEO Pipeline v2")
    parser.add_argument("--build-only", action="store_true", help="Build only, no deploy")
    parser.add_argument("--nomad-only", action="store_true", help="Nomad traffic only")
    parser.add_argument("--qa-dry-run", action="store_true",
                        help="只跑 Phase 1a 主推选题 + 注入器 dry-run（不写文件、不部署）")
    args = parser.parse_args()
    
    if args.nomad_only:
        phase_nomad()
        return

    if args.qa_dry_run:
        slugs = phase_qa_inject(dry_run=True)
        print(f"  (dry-run) 本会优先刷新的 slug 顺序: {slugs}")
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
    
    qa_slugs = phase_qa_inject()          # 激进模式: 先把当日热门问答注入 lore 页
    phase_freshen_content(prefer_slugs=qa_slugs)
    if not phase_build():
        sys.exit(1)

    # ── 内容驱动闸门（2026-09-18）─────────────────────────────
    all_ch, subs = substantive_changes()
    if not subs:
        fresh = [p for _, p in all_ch]
        print("\n=== Phase 3: Git Deploy ===")
        print(f"  ⏭  跳过部署：本轮无实质内容变更（{len(fresh)} 个文件只是新鲜度戳变化）")
        if fresh:
            _git("checkout", "--", *fresh)
            shown = ", ".join(fresh[:4]) + (" …" if len(fresh) > 4 else "")
            print(f"     已回滚新鲜度戳改动，工作树保持干净：{shown}")
        log_deploy_skipped(len(fresh))
        print("\n✅ GEO Pipeline complete（无变更，未部署）。")
        return
    print(f"\n  实质变更 {len(subs)} 个文件：" +
          ", ".join(p for _, p in subs[:6]) + (" …" if len(subs) > 6 else ""))

    if not phase_deploy():
        sys.exit(1)

    phase_indexnow(urls=changed_urls(subs))
    
    # Small delay before nomad
    time.sleep(random.uniform(5, 30))
    phase_nomad()
    
    log_deploy()
    print("\n✅ GEO Pipeline complete.")


if __name__ == "__main__":
    main()
