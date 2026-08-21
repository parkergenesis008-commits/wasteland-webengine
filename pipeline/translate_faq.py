#!/usr/bin/env python3
"""翻译 faq.json → 英文（保持 JSON 结构，逐条翻译 Q/A 字段）"""
import json, os, re, time, urllib.request, sys

KEY = ""
for line in open(os.path.expanduser("~/.hermes/.env")):
    line = line.strip()
    if line.startswith("DEEPSEEK_API_KEY=") or line.startswith("Deepseek_API_KEY="):
        KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
if not KEY:
    print("NO KEY"); sys.exit(1)

API = "https://api.deepseek.com/chat/completions"

def translate(text):
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a professional translator. Translate the given Chinese text (book lore FAQ content for a hard sci-fi novel) to natural English. Keep proper nouns like 'Shepherd's Wasteland', 'Dimension-Shearing' as given or with their established English names. Output ONLY the translation."},
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
        "max_tokens": 1000,
    }
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.loads(r.read().decode())
            out = d["choices"][0]["message"]["content"].strip()
            if out and not re.search(r"[\u4e00-\u9fff]", out):
                return out
        except Exception as e:
            last = e
            time.sleep(2 ** attempt)
    return None

def translate_text_with_names(text):
    """把中文书名号/术语替换后翻译"""
    # 预替换：书名的中文括号注释保留为英文术语
    return translate(text)

def main():
    path = os.path.expanduser("~/webengine/content/faq.json")
    d = json.load(open(path))
    me = d.get("mainEntity", [])
    for item in me:
        q = item.get("name", "")
        a = item.get("acceptedAnswer", {}).get("text", "")
        if re.search(r"[\u4e00-\u9fff]", q):
            tq = translate(q)
            if tq:
                item["name"] = tq
                print("Q:", q[:40], "->", tq[:60])
            else:
                print("Q FAIL:", q[:50])
        if re.search(r"[\u4e00-\u9fff]", a):
            ta = translate(a)
            if ta:
                item["acceptedAnswer"]["text"] = ta
                print("A:", a[:40], "->", ta[:60])
            else:
                print("A FAIL:", a[:50])
        time.sleep(0.3)
    json.dump(d, open(path, "w"), ensure_ascii=False, indent=2)
    print("faq.json 已写回")

if __name__ == "__main__":
    main()
