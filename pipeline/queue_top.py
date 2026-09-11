#!/usr/bin/env python3
"""当日主推选题器 — 从 QUEUE.md 当日段里按「权重 + 相关性」选出唯一一条。

背景（2026-09-11）：
  QUEUE.md 每日列出最推荐 3 条，但 run_geo 的注入阶段对所有 qa 条目一视同仁，
  没有"当日主推"。本模块给出**可解释的确定性评分**，选出 1 条，供 run_geo 优先注入/优先刷新。

评分（满分 100，全部可解释）：
  权重 weight 0-60
    · 队列名次: rank1=30 / rank2=20 / rank3=10（QUEUE.md 本身已按推荐度排序）
    · 来源热度: ★N / N votes / Npts → 每点 +4，上限 +20
    · 商业意图: 来源属 book 类(booksuggestions/scifi 书单) 或 slug=book → +10
  相关性 relevance 0-40
    · 已有写好的问答(answer_md)         +15
    · 对应 lore 页存在                   +10
    · 答案里含站内内链 <a href='...'>     +8
    · 问题关键词与 lore 标题有交集         +7
返回: {slug, question, rank, source, score, weight, relevance, breakdown[], date}

CLI:
  python3 pipeline/queue_top.py                 # 今日
  python3 pipeline/queue_top.py --date 2026-09-11 --explain
  python3 pipeline/queue_top.py --json          # 给 run_geo / cron 消费
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime

BASE_DIR = os.path.expanduser("~/webengine")
QA_DIR = os.path.join(BASE_DIR, "content/geo_hot_questions")
LORE_DIR = os.path.join(BASE_DIR, "content/lore")
QUEUE = os.path.join(QA_DIR, "QUEUE.md")
PICK_FILE = os.path.join(QA_DIR, "queue_top_{date}.json")

# 购买意图较强的来源（"权重"里的商业维度）
COMMERCIAL_SOURCES = ("booksuggestions", "scifi", "books", "suggestmeabook")

_LINE_RE = re.compile(r"^\s*(\d+)\.\s*\*\*\[(?P<slug>[^\]]+)\]\s*(?P<title>.+?)\*\*\s*(?P<rest>.*)$")
_SCORE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:★|votes?|pts?|points?|c\b)", re.I)
_HEAD_RE = re.compile(r"^##\s*(\d{4}-\d{2}-\d{2})\s*$")


def _today() -> str:
    return os.environ.get("GEO_DATE") or datetime.now().strftime("%Y-%m-%d")


def parse_queue(path: str = QUEUE) -> dict[str, list[dict]]:
    """QUEUE.md → {date: [ {rank, slug, title, source, note, raw} ]}"""
    out: dict[str, list[dict]] = {}
    cur = None
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            m = _HEAD_RE.match(line.strip())
            if m:
                cur = m.group(1)
                out.setdefault(cur, [])
                continue
            if cur is None:
                continue
            lm = _LINE_RE.match(line)
            if not lm:
                continue
            rest = (lm.group("rest") or "").strip()
            src = ""
            sm = re.search(r"\(([^)]*)\)", rest)
            if sm:
                src = sm.group(1).strip()
            out[cur].append({
                "rank": int(lm.group(1)),
                "slug": lm.group("slug").strip(),
                "title": lm.group("title").strip(),
                "source": src,
                "note": rest,
                "raw": line.strip(),
            })
    return out


def _hot_slugs(date: str) -> dict[str, int]:
    """hot_<date>.json 的 top3_for_today → {slug: 位置(1-based)}，用于排序校正。"""
    p = os.path.join(QA_DIR, f"hot_{date}.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}
    out = {}
    for i, it in enumerate(d.get("top3_for_today") or [], 1):
        slug = (it or {}).get("map_to")
        if slug:
            out[str(slug)] = i
    return out


def _qa_entries(date: str) -> dict[str, dict]:
    """{slug: qa_entry}（当日）"""
    p = os.path.join(QA_DIR, f"qa_{date}.json")
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return {}
    return {str(e.get("slug")): e for e in (d.get("entries") or []) if e.get("slug")}


def _lore_slugs() -> set[str]:
    return {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(LORE_DIR, "*.md"))}


def _lore_titles() -> str:
    """所有 lore 页标题拼成一段小写文本，用于关键词交集判断。"""
    buf = []
    for p in glob.glob(os.path.join(LORE_DIR, "*.md")):
        try:
            head = open(p, encoding="utf-8").read(1200).lower()
        except Exception:
            continue
        m = re.search(r"^title:\s*(.+)$", head, flags=re.M)
        buf.append(m.group(1) if m else os.path.basename(p))
    return " ".join(buf).lower()


_STOP = set("the a an of to in on for and or is are what how why does do with without "
            "book books read reading recommend suggestion suggestions any some".split())


def score_entry(entry: dict, qa: dict[str, dict], lore: set[str], lore_text: str) -> dict:
    breakdown: list[str] = []
    slug = entry["slug"]

    # ── 权重 weight (0-60) ───────────────────────────────
    weight = max(0, 30 - 10 * (entry["rank"] - 1))
    breakdown.append(f"队列名次#{entry['rank']} +{weight}")

    heat = 0.0
    for m in _SCORE_RE.finditer(entry.get("source", "") + " " + entry.get("note", "")):
        try:
            heat = max(heat, float(m.group(1)))
        except Exception:
            pass
    hot_pts = int(min(heat * 4, 20))
    if hot_pts:
        weight += hot_pts
        breakdown.append(f"来源热度 {heat:g} → +{hot_pts}")

    src = (entry.get("source") or "").lower()
    if slug == "book" or any(c in src for c in COMMERCIAL_SOURCES):
        weight += 10
        breakdown.append("商业/购买意图 +10")
    weight = min(weight, 60)

    # ── 相关性 relevance (0-40) ──────────────────────────
    rel = 0
    e = qa.get(slug)
    if e and e.get("answer_md"):
        rel += 15
        breakdown.append("已有问答答案 +15")
    if slug in lore:
        rel += 10
        breakdown.append("lore 页存在 +10")
    ans = (e or {}).get("answer_md") or ""
    if "<a href=" in ans:
        rel += 8
        breakdown.append("答案含站内内链 +8")
    q = (entry.get("title") or "").lower()
    kws = [w for w in re.findall(r"[a-z]{4,}", q) if w not in _STOP]
    if kws and any(k in lore_text for k in kws):
        rel += 7
        breakdown.append(f"问题关键词命中 lore({','.join(kws[:3])}) +7")
    rel = min(rel, 40)

    return {
        "slug": slug,
        "question": ((e or {}).get("question") or entry.get("title") or "").strip(),
        "rank": entry["rank"],
        "source": entry.get("source", ""),
        "weight": weight,
        "relevance": rel,
        "score": weight + rel,
        "breakdown": breakdown,
        "has_answer": bool(e and e.get("answer_md")),
    }


def pick(date: str | None = None, write: bool = True) -> dict | None:
    """选出当日主推；返回 {..., date}；无数据返回 None。"""
    date = date or _today()
    sections = parse_queue()
    if not sections:
        return None
    # 优先当日；否则取最接近的最近一天（并标注 fallback）
    fallback = False
    if date not in sections:
        past = sorted([d for d in sections if d <= date])
        if not past:
            return None
        date = past[-1]
        fallback = True
    entries = sections.get(date) or []
    if not entries:
        return None

    # 用 hot json 的位置校正名次（collector 的排序更权威）
    hot = _hot_slugs(date)
    for e in entries:
        if e["slug"] in hot:
            e["rank"] = hot[e["slug"]]

    qa = _qa_entries(date)
    lore = _lore_slugs()
    lore_text = _lore_titles()
    scored = [score_entry(e, qa, lore, lore_text) for e in entries]
    scored.sort(key=lambda x: (-x["score"], x["rank"]))
    top = dict(scored[0])
    top.update({"date": date, "fallback_date": fallback, "candidates": len(scored),
                "all": [{k: s[k] for k in ("slug", "score", "weight", "relevance", "rank")} for s in scored]})
    if write:
        try:
            with open(PICK_FILE.format(date=date), "w", encoding="utf-8") as f:
                json.dump(top, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return top


def label(top: dict) -> str:
    return (f"🎯 当日主推: [{top['slug']}] score={top['score']} "
            f"(权重 {top['weight']} + 相关性 {top['relevance']}) rank#{top['rank']} "
            f"— {top['question'][:60]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--json", action="store_true", help="只输出 JSON（供脚本消费）")
    ap.add_argument("--explain", action="store_true", help="打印评分明细")
    args = ap.parse_args()

    top = pick(args.date)
    if not top:
        print("  ⚠️ 队列无当日条目（QUEUE.md 缺失或为空）")
        return 0
    if args.json:
        print(json.dumps(top, ensure_ascii=False))
        return 0
    print("  " + label(top))
    if top.get("fallback_date"):
        print(f"  ⚠️ 当日无条目 → 回退到 {top['date']}")
    if args.explain or True:
        print("  评分明细: " + " | ".join(top["breakdown"]))
        for c in top["all"]:
            print(f"    · [{c['slug']}] {c['score']} (权重 {c['weight']} + 相关性 {c['relevance']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
