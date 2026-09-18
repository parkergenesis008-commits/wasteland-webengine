#!/usr/bin/env python3
"""Wasteland GEO 周报 / 月报 — 只统计"可核实事实"（2026-09-18 重写）

⚠️ 旧版把 nomad 自访日志当成"曝光次数"统计，产出的数字没有意义：
   那些"曝光"是我们自己用浏览器访问自己网站记下来的。自访 ≠ 曝光。

本版只报告机器侧可验证的事实：
  1. 部署次数 / 部署间隔（来自 ~/.wasteland_geo_log.jsonl 的 deploy_time 行）
  2. IndexNow 推送结果（来自 ~/.wasteland_indexnow.log）
  3. 站点产物（sitemap URL 数、文章页数、最新页面文件时间）
  4. git 提交数
真实曝光 / 点击 / 平均排名本地未采集 —— 必须到 Google Search Console 看。

用法：
  python3 pipeline/generate_geo_report.py            # 周报（7 天）
  python3 pipeline/generate_geo_report.py monthly    # 月报（30 天）
"""
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
BASE_DIR = HOME / "webengine"
GEO_LOG = HOME / ".wasteland_geo_log.jsonl"
INDEXNOW_LOG = HOME / ".wasteland_indexnow.log"
SITEMAP = BASE_DIR / "sitemap.xml"
PAGES_DIR = BASE_DIR / "pages"


def _parse_iso(ts):
    try:
        return datetime.datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def collect_deploys(start):
    """返回 (部署时间列表, 日志行总数, 模拟自访行数)。"""
    deploys, total, self_visits = [], 0, 0
    if not GEO_LOG.exists():
        return deploys, total, self_visits
    with GEO_LOG.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            import json
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "deploy_time" in d:
                ts = _parse_iso(d["deploy_time"])
                if ts and ts >= start:
                    deploys.append(ts)
            elif d.get("type") in ("self_visit_simulated", "self", "google_search_click"):
                self_visits += 1
    return sorted(deploys), total, self_visits


def collect_indexnow(start):
    hits = []
    if not INDEXNOW_LOG.exists():
        return hits
    with INDEXNOW_LOG.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r"(\S+Z?|\d{4}-\d{2}-\d{2}T[\d:.]+)\s+status=(\d+)\s+urls=(\d+)", line.strip())
            if not m:
                continue
            ts = _parse_iso(m.group(1))
            if ts and ts >= start:
                hits.append((ts, m.group(2), m.group(3)))
    return hits


def collect_site():
    urls = 0
    if SITEMAP.exists():
        urls = len(re.findall(r"<loc>", SITEMAP.read_text(encoding="utf-8")))
    pages = sorted(PAGES_DIR.glob("*.html")) if PAGES_DIR.exists() else []
    newest = max((p.stat().st_mtime for p in pages), default=None)
    return urls, len(pages), newest


def collect_git(since_days):
    try:
        out = subprocess.run(
            ["git", "log", f"--since={since_days} days ago", "--oneline"],
            cwd=str(BASE_DIR), capture_output=True, text=True, timeout=30,
        )
        lines = [l for l in out.stdout.strip().splitlines() if l.strip()]
        return len(lines), (lines[0] if lines else None)
    except Exception:
        return 0, None


def generate_report(period_days, title):
    now = datetime.datetime.now()
    start = now - datetime.timedelta(days=period_days)

    deploys, log_lines, self_visits = collect_deploys(start)
    indexnow = collect_indexnow(start)
    urls, page_count, newest_mtime = collect_site()
    commits, last_commit = collect_git(period_days)

    print(f"### {title}")
    print(f"**统计周期：** {start:%Y-%m-%d} 至 {now:%Y-%m-%d}（{period_days} 天）\n")

    print("#### 【部署（可核实）】")
    print(f"- 部署次数：**{len(deploys)} 次**")
    if deploys:
        days = sorted({d.date() for d in deploys})
        print(f"- 覆盖天数：{len(days)} 天（最近一次 {deploys[-1]:%Y-%m-%d %H:%M}）")
        if len(days) > 1:
            gaps = [(b - a).days for a, b in zip(days, days[1:])]
            print(f"- 最长间隔：{max(gaps)} 天；平均间隔 {sum(gaps)/len(gaps):.1f} 天")
        print(f"- 本周期 git 提交：{commits} 条" + (f"（最新 {last_commit}）" if last_commit else ""))
    else:
        print("- ⚠️ 本周期无部署记录")

    print("\n#### 【索引推送（可核实）】")
    if indexnow:
        ok = sum(1 for _, s, _ in indexnow if s == "200")
        print(f"- IndexNow 推送 {len(indexnow)} 次，其中 status=200 共 **{ok} 次**")
        last = indexnow[-1]
        print(f"- 最近一次：{last[0]:%Y-%m-%d %H:%M} status={last[1]} urls={last[2]}")
    else:
        print("- ⚠️ 本周期无 IndexNow 推送记录")

    print("\n#### 【站点产物（可核实）】")
    print(f"- sitemap URL：{urls} 条")
    print(f"- pages/*.html：{page_count} 个")
    if newest_mtime:
        print(f"- 最新页面文件时间：{datetime.datetime.fromtimestamp(newest_mtime):%Y-%m-%d %H:%M}")

    print("\n#### 【真实效果数据：本地未采集】")
    print("- 曝光 / 点击 / 平均排名**必须**到 Google Search Console 查看（本地无 API 采集）。")
    print("- GA 属性 G-ERCP39C12Y（数据在 Google 后台）。")
    print(f"- 已停用的伪指标：本周期日志内自访/模拟搜索行 {self_visits} 条（2026-09-18 起 "
          f"nomad 默认关闭，不再产生新记录）。**自访不是曝光**，本报告不再据此出数。")
    print(f"- 日志总行数（含历史）：{log_lines}")


if __name__ == "__main__":
    period = sys.argv[1] if len(sys.argv) > 1 else "weekly"
    if period == "monthly":
        generate_report(30, "Wasteland GEO 月度报告（可核实事实）")
    else:
        generate_report(7, "Wasteland GEO 周度报告（可核实事实）")
