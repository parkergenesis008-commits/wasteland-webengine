#!/bin/bash
# 简单的基于git的发布回滚逻辑
git add .
git commit -m "Auto-deploy-snapshot-1778509457"
# 如果发布失败
# git reset --hard HEAD~1
