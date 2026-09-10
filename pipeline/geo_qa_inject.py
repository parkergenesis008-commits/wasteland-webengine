#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 激进模式 · 热门问题 → lore 页"延伸问答"注入器
====================================================
输入: ~/webengine/content/geo_hot_questions/qa_<YYYY-MM-DD>.json
      (由每日 08:30 的 cron「GEO 每日热门引流问题」产出 publish-ready 问答)
做什么:
  1) 把每条问答以带标记的块追加进 content/lore/<slug>.md
     <!-- GEO-QA-START id=... --> ... <!-- GEO-QA-END -->
     每个 lore 页最多保留 3 块(超出丢最旧), 保证页面不臃肿
  2) 生成 content/geo_hot_questions/qa_schema.json → 供 build_site.py 注入 FAQPage JSON-LD
  3) 记录 qa_injected.json 防重复注入(幂等)

⚠️ 内容红线:
  - 不编造可核实事实(评分/引用/统计); 回答只做"物理共识 + 本项目设定"两层表述
  - 每块必须带真实来源链接与"Original thread"
  - 本脚本不改写 qa_*.json 里的正文文字

用法:
  python3 pipeline/geo_qa_inject.py            # 注入今天(及未注入的历史)
  python3 pipeline/geo_qa_inject.py --dry-run  # 只看会做什么
"""
import argparse
import glob
import hashlib
import json
import os
import re
from datetime import datetime

BASE_DIR = os.path.expanduser("~/webengine")
QA_DIR = os.path.join(BASE_DIR, "content/geo_hot_questions")
LORE_DIR = os.path.join(BASE_DIR, "content/lore")
SCHEMA_FILE = os.path.join(QA_DIR, "qa_schema.json")
INJECTED_FILE = os.path.join(QA_DIR, "qa_injected.json")
MAX_BLOCKS_PER_PAGE = 3

START = "<!-- GEO-QA-START"
END = "<!-- GEO-QA-END -->"


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def _qa_id(entry):
    raw = f"{entry.get('slug','')}|{entry.get('question','')}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]


def _block(entry, lore_titles):
    """生成注入块(原生 HTML 链接, 因为 md_to_html 不支持 markdown 链接语法)"""
    q = (entry.get("question") or "").strip()
    a = (entry.get("answer_md") or "").strip()
    src = (entry.get("source") or "").strip()
    heat = (entry.get("heat") or "").strip()
    surl = (entry.get("source_url") or "").strip()
    links = entry.get("links") or []
    link_html = " · ".join(
        f'<a href="{l}.html">{lore_titles.get(l, l)}</a>' for l in links if l and l != "book"
    )
    book_link = '<a href="book.html">Read the full framework in the book</a>'
    parts = [f"{START} id={_qa_id(entry)} -->",
             "## Extended Q&A — Reader Question", "",
             f"**Q: {q}**"]
    meta = []
    if src:
        meta.append(f"asked on {src}")
    if heat:
        meta.append(heat)
    if meta:
        parts.append(f"<p><em>{' · '.join(meta)}</em></p>")
    parts += ["", a, ""]
    rel = " · ".join([x for x in [link_html, book_link] if x])
    if surl:
        rel += f' · <a href="{surl}" target="_blank" rel="noopener">Original thread</a>'
    parts += [f"<p><strong>Related:</strong> {rel}</p>", END, ""]
    return "\n".join(parts)


def _prune_old_blocks(md, keep=MAX_BLOCKS_PER_PAGE):
    """每页最多保留 keep 块, 超出丢最旧"""
    blocks = re.findall(r"<!-- GEO-QA-START.*?<!-- GEO-QA-END -->", md, flags=re.S)
    if len(blocks) <= keep:
        return md, 0
    for b in blocks[:len(blocks) - keep]:
        md = md.replace(b, "")
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md, len(blocks) - keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # lore 标题表(内链锚文本)
    lore_titles = {}
    for p in glob.glob(os.path.join(LORE_DIR, "*.md")):
        slug = os.path.splitext(os.path.basename(p))[0]
        try:
            with open(p, encoding="utf-8") as f:
                head = f.read(1200)
            m = re.search(r"^title:\s*(.+)$", head, flags=re.M)
            lore_titles[slug] = (m.group(1).strip() if m else slug)
        except Exception:
            lore_titles[slug] = slug

    injected = _load(INJECTED_FILE, {})
    schema = _load(SCHEMA_FILE, {})

    # 收集所有 qa_*.json 里未注入的条目(近 14 天)
    files = sorted(glob.glob(os.path.join(QA_DIR, "qa_*.json")))
    pending = []
    for fp in files:
        d = _load(fp, {})
        for e in (d.get("entries") or []):
            qid = _qa_id(e)
            if qid in injected:
                # 🛡️ 自愈: 状态文件记录已注入, 但 md 里已不存在(例如被 freshen 截断/手工编辑) → 重新注入
                _slug = e.get("slug")
                _mp = os.path.join(LORE_DIR, f"{_slug}.md")
                _md = ""
                try:
                    if os.path.exists(_mp):
                        with open(_mp, encoding="utf-8") as _f:
                            _md = _f.read()
                except Exception:
                    _md = ""
                if f"{START} id={qid}" in _md:
                    continue
                print(f"  ↩︎ 自愈: {_slug} 的问答块缺失 → 重新注入")
            if not e.get("slug") or not e.get("question") or not e.get("answer_md"):
                continue
            e["_qa_id"] = qid
            e["_srcfile"] = os.path.basename(fp)
            pending.append(e)

    if not pending:
        print("  QA 注入: 无待注入条目(幂等跳过)")
        return

    done, skipped = [], []
    for e in pending:
        slug = e["slug"]
        md_path = os.path.join(LORE_DIR, f"{slug}.md")
        if not os.path.exists(md_path):
            skipped.append(f"{slug}(无此 lore 页)")
            continue
        with open(md_path, encoding="utf-8") as f:
            md = f.read()
        if f"{START} id={e['_qa_id']}" in md:
            injected[e["_qa_id"]] = {"slug": slug, "ts": datetime.now().isoformat(), "note": "already"}
            continue
        new_md = md.rstrip() + "\n\n" + _block(e, lore_titles)
        # 🛡️ 注入位置: 若文件末尾已有 "<!-- Last fresh: -->" 时间戳, 插到它**之前**,
        #    避免被 run_geo 的 freshen 逻辑或任何"截断到时间戳"的实现抹掉。
        if new_md.count("<!-- Last fresh:") > 0:
            blk_start = new_md.rindex(START)
            blk_end = new_md.index(END, blk_start) + len(END)
            block_txt = new_md[blk_start:blk_end]
            head = new_md[:blk_start].rstrip()
            # 去掉末尾空的 "<!-- Last fresh: -->" 行(可能有多行历史戳)
            head = re.sub(r"(\n*<!-- Last fresh:.*?-->)+$", "", head, flags=re.S).rstrip()
            stamps = re.findall(r"<!-- Last fresh:.*?-->", new_md[blk_start:], flags=re.S)
            tail = ("\n\n" + stamps[-1]) if stamps else ""
            new_md = head + "\n\n" + block_txt + tail + "\n"
        new_md, pruned = _prune_old_blocks(new_md)
        if args.dry_run:
            print(f"  [dry-run] 会注入 → content/lore/{slug}.md  Q: {e['question'][:70]}")
            done.append(slug)
            continue
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(new_md)
        injected[e["_qa_id"]] = {"slug": slug, "ts": datetime.now().isoformat(),
                                 "question": e["question"][:120], "pruned": pruned,
                                 "src": e["_srcfile"]}
        schema.setdefault(slug, [])
        schema[slug].append({"q": e["question"], "a": e["answer_md"], "source_url": e.get("source_url", "")})
        done.append(slug)
        print(f"  ✓ 注入 {slug} ← 「{e['question'][:64]}」" + (f" (裁掉 {pruned} 个旧块)" if pruned else ""))

    if not args.dry_run:
        _save(INJECTED_FILE, injected)
        # 每页 FAQ schema 最多保留 3 条(与页面块数一致, 从底部取最新)
        for k in list(schema):
            schema[k] = schema[k][-MAX_BLOCKS_PER_PAGE:]
        _save(SCHEMA_FILE, schema)

    print(f"  QA 注入完成: {len(done)} 页" + (f", 跳过 {len(skipped)}: {', '.join(skipped)}" if skipped else ""))


if __name__ == "__main__":
    main()
