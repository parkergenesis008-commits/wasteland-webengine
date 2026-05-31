#!/bin/bash
cd /Users/michaelray/webengine
export PATH="/Library/Frameworks/Python.framework/Versions/3.10/bin:/Users/michaelray/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
# 1. 演化物理数值
python3 geo_engine/evolution_simulator.py
# 2. 渲染新页面
python3 render_full_page.py
# 3. 提交至 GitHub
git add .
git commit -m "Auto-Evolution-Update-2026-05-12"
git push origin gh-pages
