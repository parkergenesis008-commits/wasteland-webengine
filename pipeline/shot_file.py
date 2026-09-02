#!/usr/bin/env python3
"""Chrome CDP 截图任意 file:// URL — v2 用 Target.createTarget + attachToTarget [2026-09-02]"""
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
height = int(sys.argv[4]) if len(sys.argv) > 4 else 1500
width = int(sys.argv[5]) if len(sys.argv) > 5 else 1000

ws = websocket.create_connection(get_ws(port), timeout=60)
# 创建 target
r = cdp_call(ws, "Target.createTarget", {"url": "about:blank"}, mid=1)
tid = r["result"]["targetId"]
# 会话方式 attach
r = cdp_call(ws, "Target.attachToTarget", {"targetId": tid, "flatten": True}, mid=2)
sid = r["result"]["sessionId"]

def s_call(method, params=None, mid=100):
    ws.send(json.dumps({"id": mid, "method": method, "params": params or {}, "sessionId": sid}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == mid:
            return r

s_call("Page.enable", {}, 101)
s_call("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False}, 102)
s_call("Page.navigate", {"url": target}, 103)
time.sleep(5)
r = s_call("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False}, 104)
data = base64.b64decode(r["result"]["data"])
open(out, "wb").write(data)
print(f"SAVED {out} {len(data)} bytes")
ws.close()
