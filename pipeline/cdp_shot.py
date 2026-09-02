#!/usr/bin/env python3
"""Screenshot local HTML files via Chrome CDP for visual verification."""
import json, subprocess, time, urllib.request, os, sys

def get_ws_url(port=9222):
    with urllib.request.urlopen(f"http://localhost:{port}/json/version") as r:
        return json.load(r)["webSocketDebuggerUrl"]

def cdp_screenshot(ws_url, target_url, out_path, wait_ms=1800):
    # Use chrome-remote-interface style via websocket — fall back to simple approach
    import asyncio, websockets

    async def main():
        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Target.createTarget", "params": {"url": "about:blank"}}))
            resp = json.loads(await ws.recv())
            target_id = resp["result"]["targetId"]
            await ws.send(json.dumps({"id": 2, "method": "Target.attachToTarget", "params": {"targetId": target_id, "flatten": True}}))
            await ws.recv()
            # Navigate
            await ws.send(json.dumps({"id": 3, "method": "Page.enable", "params": {}}))
            await ws.recv()
            await ws.send(json.dumps({"id": 4, "method": "Page.navigate", "params": {"url": target_url}}))
            await ws.recv()
            time.sleep(wait_ms / 1000)
            # Set device metrics for full-width desktop
            await ws.send(json.dumps({"id": 5, "method": "Emulation.setDeviceMetricsOverride",
                                      "params": {"width": 1000, "height": 1400, "deviceScaleFactor": 1, "mobile": False}}))
            await ws.recv()
            await ws.send(json.dumps({"id": 6, "method": "Page.captureScreenshot", "params": {"format": "png"}}))
            resp = json.loads(await ws.recv())
            # May need to read more messages
            while "result" not in resp or "data" not in resp.get("result", {}):
                resp = json.loads(await ws.recv())
            data = resp["result"]["data"]
            import base64
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"OK {out_path}")
            await ws.send(json.dumps({"id": 7, "method": "Target.closeTarget", "params": {"targetId": target_id}}))
            await ws.recv()

    asyncio.run(main())

if __name__ == "__main__":
    target = sys.argv[1]  # file:// URL
    out = sys.argv[2]
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 9222
    ws = get_ws_url(port)
    cdp_screenshot(ws, target, out)
