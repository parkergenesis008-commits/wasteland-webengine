#!/usr/bin/env python3
"""回归检查：重新生成全站，与本仓库已提交的成品逐文件比对。

用途（2026-11-07 模板并回后的保险丝）：
    任何人跑完 pipeline/build_site.py 之后，或改完 templates/ 之后，先跑这个脚本，
    确认"重新生成 = 线上定稿页"，而不是把页面回退成旧文案。

判定口径：
    · index.html / book.html / author.html / llms.txt / robots.txt 必须逐字节一致；
    · pages/*.html 允许 dateModified 变化（同一天生成时连它也应一致）；
    · sitemap.xml 允许 <lastmod> 变化（取决于 git 历史）；
    · 其余任何差异 → 打印 unified diff 摘要并 exit 1。

用法：
    python3 pipeline/check_render_parity.py            # 检查，退出码 = 结果
    python3 pipeline/check_render_parity.py --diff     # 同时打印 diff 前 40 行
"""
import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDER = os.path.join(REPO, "pipeline", "build_site.py")
STRICT = ["index.html", "book.html", "author.html", "llms.txt", "robots.txt"]
DATE_PATTERNS = [
    re.compile(r'"dateModified":\s*"\d{4}-\d{2}-\d{2}"'),
    re.compile(r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>"),
]


def normalize(text):
    for pat in DATE_PATTERNS:
        text = pat.sub('"dateModified": "XXXX-XX-XX"' if pat.pattern.startswith('"dateModified')
                       else "<lastmod>XXXX-XX-XX</lastmod>", text)
    return text


def build_into(tmp):
    os.symlink(os.path.join(REPO, "content"), os.path.join(tmp, "content"))
    env = dict(os.environ, WASTELAND_BASE_DIR=tmp)
    r = subprocess.run([sys.executable, BUILDER], env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print("BUILD FAILED\n" + r.stdout + r.stderr)
        sys.exit(2)


def main():
    show_diff = "--diff" in sys.argv
    tmp = tempfile.mkdtemp(prefix="wasteland_parity_")
    try:
        build_into(tmp)
        files = list(STRICT)
        live_pages = sorted(os.listdir(os.path.join(REPO, "pages")))
        files += [os.path.join("pages", p) for p in live_pages if p.endswith(".html")]
        files.append("sitemap.xml")

        bad = []
        for rel in files:
            a = os.path.join(REPO, rel)
            b = os.path.join(tmp, rel)
            if not os.path.exists(b):
                bad.append((rel, "MISSING in regenerated output"))
                continue
            if not os.path.exists(a):
                bad.append((rel, "MISSING in repo"))
                continue
            left = normalize(open(a, encoding="utf-8").read())
            right = normalize(open(b, encoding="utf-8").read())
            if left == right:
                print(f"OK    {rel} ({len(right)} chars)")
                continue
            d = list(difflib.unified_diff(left.splitlines(), right.splitlines(),
                                          fromfile=f"repo/{rel}", tofile=f"regen/{rel}",
                                          n=1, lineterm=""))
            changed = sum(1 for l in d if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))
            bad.append((rel, f"{changed} changed lines"))
            print(f"DIFF  {rel} ({changed} changed lines)")
            if show_diff:
                print("\n".join(d[:80]))
        print()
        if bad:
            print(f"❌ PARITY FAIL: {len(bad)}/{len(files)} files differ")
            for rel, why in bad:
                print(f"   - {rel}: {why}")
            print("   生成器与仓库成品不一致 → 先修模板/代码，别直接发布。")
            return 1
        print(f"✅ PARITY PASS: {len(files)}/{len(files)} files identical (dates normalized)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
