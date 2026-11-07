#!/usr/bin/env python3
"""审计 build_site.py 里的 arXiv 引用是否真实（存在 + 标题对得上）。

背景（2026-11-07）：原有 58 条引用中只有 13 条标题与 arXiv 实际论文一致，
其余 45 条指向完全无关的论文（例如 Type-II 超晶格指向 GAN 图像生成），
等于让真实论文替小说设定背书。此后引用一律"先 API 实检再入站"。

用法：
    python3 pipeline/audit_refs.py           # 审计，正文失配/缺失即 exit 1
    python3 pipeline/audit_refs.py --json    # 同时输出 /tmp/arxiv_refs_audit.json

判定：按标题词集重合度 ≥0.60 视为同篇；分批请求 + 重试，避免 arXiv API 超时。
"""
import json
import os
import re
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(REPO, "pipeline", "build_site.py")
BATCH = 12
RETRIES = 3


def parse_refs():
    src = open(BUILDER, encoding="utf-8").read()
    block = src[src.index("ARXIV_REFS = {"):src.index("\ndef ", src.index("ARXIV_REFS = {"))]
    refs = re.findall(
        r'\{"id":\s*"([^"]+)",\s*"title":\s*"([^"]*)",\s*"authors":\s*"([^"]*)",\s*"year":\s*"([^"]*)"\}',
        block)
    uniq = {}
    for rid, title, authors, year in refs:
        uniq.setdefault(rid, {"title": title, "authors": authors, "year": year})
    return uniq


def fetch_batch(ids):
    url = ("http://export.arxiv.org/api/query?id_list=" + ",".join(ids) +
           f"&max_results={len(ids) + 10}")
    for _ in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ref-audit)"})
            with urllib.request.urlopen(req, timeout=90) as f:
                return f.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(5)
    return ""


def main():
    refs = parse_refs()
    ids = list(refs)
    found, batches = {}, 0
    for i in range(0, len(ids), BATCH):
        xml = fetch_batch(ids[i:i + BATCH])
        batches += 1
        for e in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
            aid = re.search(r"<id>http://arxiv.org/abs/([^<]+)</id>", e)
            t = re.search(r"<title>(.*?)</title>", e, re.S)
            if not (aid and t):
                continue
            found[re.sub(r"v\d+$", "", aid.group(1))] = re.sub(r"\s+", " ", t.group(1)).strip()
        time.sleep(3)

    def norm(s):
        return set(re.sub(r"[^a-z0-9 ]", " ", s.lower()).split())

    ok, mismatch, missing = [], [], []
    for rid, meta in refs.items():
        key = rid if rid in found else next(
            (k for k in found if k.endswith(rid.split("/")[-1])), None)
        if not key:
            missing.append((rid, meta["title"]))
            continue
        overlap = len(norm(meta["title"]) & norm(found[key])) / max(1, len(norm(meta["title"])))
        (ok if overlap >= 0.6 else mismatch).append(
            {"id": rid, "site_title": meta["title"], "api_title": found[key], "overlap": round(overlap, 2)})

    print(f"refs={len(refs)} batches={batches} | verified={len(ok)} mismatch={len(mismatch)} missing={len(missing)}")
    for rid, title in missing:
        print(f"  MISSING  {rid:16s} {title[:70]}")
    for r in mismatch:
        print(f"  MISMATCH {r['id']:16s} overlap={r['overlap']}\n      site: {r['site_title']}\n      api : {r['api_title']}")
    if "--json" in sys.argv:
        json.dump({"ok": ok, "mismatch": mismatch, "missing": missing},
                  open("/tmp/arxiv_refs_audit.json", "w"), ensure_ascii=False, indent=1)
    return 1 if (mismatch or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
