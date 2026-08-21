#!/usr/bin/env python3
"""批量翻译 wasteland geo 站点的中文 lore MD → 英文（DeepSeek API，保持 markdown/frontmatter 结构）"""
import os, re, sys, json, time, urllib.request, concurrent.futures

# --- 读 key ---
KEY = ""
env_path = os.path.expanduser("~/.hermes/.env")
if os.path.exists(env_path):
    for line in open(env_path):
        line = line.strip()
        if line.startswith("DEEPSEEK_API_KEY=") or line.startswith("Deepseek_API_KEY="):
            KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
if not KEY:
    print("NO DEEPSEEK KEY"); sys.exit(1)

BASE = os.path.expanduser("~/webengine")
API_URL = "https://api.deepseek.com/chat/completions"

SYSTEM = """You are a professional scientific translator. Translate the Chinese markdown document to ENGLISH.
Rules:
1. Output ONLY the translated markdown document, nothing else.
2. Preserve the YAML frontmatter structure (--- ... ---), translating any Chinese values inside it to English.
3. Preserve ALL markdown syntax, LaTeX math, URLs, citation formats (e.g. "Li et al. (Nature 653, 1052)"), arXiv IDs, and English technical terms exactly.
4. Translate technical Chinese terms to their standard English physics equivalents (e.g. 大白话比喻 → Plain-language analogy).
5. Keep the overall structure: headings, lists, bold/italic, code blocks.
6. The output must contain NO Chinese characters."""

def translate_file(path):
    txt = open(path, encoding="utf-8").read()
    # 快速检查是否真的需要翻译
    if not re.search(r"[\u4e00-\u9fff]", txt):
        return path, "SKIP (already English)"
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": txt},
        ],
        "temperature": 0.2,
        "max_tokens": 8000,
    }
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    last_err = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.loads(r.read().decode())
            out = d["choices"][0]["message"]["content"].strip()
            if not out:
                raise ValueError("empty output")
            # 防御：如果输出还是中文，拒绝写回
            if re.search(r"[\u4e00-\u9fff]", out):
                raise ValueError("output still contains Chinese")
            with open(path, "w", encoding="utf-8") as f:
                f.write(out + "\n")
            return path, f"OK ({len(out)} chars)"
        except Exception as e:
            last_err = e
            time.sleep(2 ** attempt)
    return path, f"FAIL: {last_err}"

def main():
    files = []
    for d in ["content/lore", "lore"]:
        dp = os.path.join(BASE, d)
        for f in sorted(os.listdir(dp)):
            if f.endswith(".md"):
                p = os.path.join(dp, f)
                txt = open(p, encoding="utf-8").read()
                if re.search(r"[\u4e00-\u9fff]", txt):
                    files.append(p)
    print(f"待翻译: {len(files)} 个文件", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(translate_file, p): p for p in files}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            done += 1
            p, msg = fut.result()
            results.append((p, msg))
            print(f"[{done}/{len(files)}] {os.path.basename(p)}: {msg}", flush=True)
    fails = [r for r in results if r[1].startswith("FAIL")]
    print(f"\n完成: {len(results)-len(fails)} OK, {len(fails)} FAIL")
    for p, m in fails:
        print(f"  {p}: {m}")

if __name__ == "__main__":
    main()
