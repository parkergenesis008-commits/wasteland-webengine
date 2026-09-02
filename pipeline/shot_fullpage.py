#!/usr/bin/env python3
"""Chrome CDP 整页截图 — captureBeyondViewport=True + 文档全高 [2026-09-02]"""
import json, time, base64, websocket, urllib.request, sys

def cdp_call(ws, method, params=None, mid=1):
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid:
            return r

def get_ws(port):
    with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=10) as r:
        return json.load(r)["webSocketDebuggerUrl"]

target = sys.argv[1]
out = sys.argv[2]
port = sys.argv[3] if len(sys.argv) > 3 else "9222"
max_h = int(sys.argv[4]) if len(sys.argv) > 4 else 4000

ws = websocket.create_connection(get_ws(port), timeout=60)
r = cdp_call(ws, "Target.createTarget", {"url": "about:blank"}, mid=1)
tid = r["result"]["targetId"]
r = cdp_call(ws, "Target.attachToTarget", {"targetId": tid, "flatten": True}, mid=2)
sid = r["result"]["sessionId"]

def s_call(method, params=None, mid=100):
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}, "sessionId": sid}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid:
            return r

s_call("Page.enable", {}, 101)
s_call("Page.navigate", {"url": target}, 102)
time.sleep(5)
# 获取文档实际高度
r = s_call("Runtime.evaluate", {"expression": "Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)", "returnByValue": True}, 103)
doc_h = int(r["result"]["result"]["value"])
h = min(doc_h, max_h)
print(f"文档高度 {doc_h}px, 截取 {h}px")
s_call("Emulation.setDeviceMetricsOverride", {"width": 1000, "height": h, "deviceScaleFactor": 1, "mobile": False}, 104)
time.sleep(1)
r = s_call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True}, 105)
data = base64.b64decode(r["result"]["data"])
open(out, "wb").write(data)
print(f"SAVED {out} {len(data)} bytes ({h}px)")
ws.close()
