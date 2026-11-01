# /// script
# requires-python = ">=3.12"
# dependencies = ["websockets>=13"]
# ///
"""Run touch, throttled, and timed steps against a live agent-browser session.

agent-browser has no touch emulation or CPU throttling, and Chrome drops CDP
emulation when the client that set it detaches. This script speaks raw CDP to
the session's browser and sends only the commands below, so it leaves the
session's other emulation (colour scheme, viewport, pixel ratio) alone; a
Playwright client would reset them.

Usage (on the test host):
  uv run touch_probe.py WS steps.json [--url SUBSTR]
  uv run touch_probe.py WS - [--url SUBSTR] < steps.json
  uv run touch_probe.py WS hold [--url SUBSTR] [--cpu N]
where WS is `agent-browser --session S get cdp-url` and SUBSTR picks the tab
whose URL contains it (default: the only page tab; an error if several).
`hold` keeps touch emulation (and the CPU rate) on until the process is killed,
so agent-browser's own commands see a touch device; run it as a background
service on the test host.

steps.json is {"steps": [...]}, optionally with "touch": true and "cpu": N.
Leave those out while a hold is running: Chrome clears emulation when the
client that set it detaches, so a steps run that sets touch would switch the
hold's touch emulation off on exit. Taps still land without them. Set them only
for a standalone run with no hold. Each step is one of
  {"tap": [x, y]}
  {"drag": [x1, y1, x2, y2], "ms": 300}             one finger, 16 ms per move
  {"pinch": [cx, cy, start_gap, end_gap], "ms": 300}  two fingers, horizontal
  {"wheel": [x, y, delta_y], "ctrl": false}          ctrl=true stands in for trackpad pinch
  {"wait": ms}
  {"eval": "js expression"}                          result printed as JSON
  {"screenshot": "/path.png"}                        CSS-pixel size; use agent-browser's
                                                     screenshot for full resolution
  {"time_to_change": "js predicate", "after": <tap|drag|wheel step>, "timeout": 3000}
Coordinates are CSS pixels in the viewport. Each step prints one JSON line.
"""
import argparse
import base64
import itertools
import json
import sys
import time

from websockets.sync.client import connect

FRAME_MS = 16


class Cdp:
    """Minimal flat-session CDP client: one browser socket, one page session."""

    def __init__(self, ws):
        self.ws = ws
        self.ids = itertools.count(1)
        self.session = None

    def send(self, method, params=None, session=True):
        msg_id = next(self.ids)
        msg = {"id": msg_id, "method": method, "params": params or {}}
        if session and self.session:
            msg["sessionId"] = self.session
        self.ws.send(json.dumps(msg))
        while True:
            # A command Chrome never answers (as agent-browser's click does under
            # touch emulation) should fail loudly rather than hang the tester.
            reply = json.loads(self.ws.recv(timeout=15))
            if reply.get("id") == msg_id:
                if "error" in reply:
                    raise RuntimeError(f"{method}: {reply['error']}")
                return reply.get("result", {})

    def attach(self, url_part):
        pages = [t for t in self.send("Target.getTargets", session=False)["targetInfos"]
                 if t["type"] == "page" and not t["url"].startswith(("devtools", "chrome:"))]
        if url_part:
            pages = [t for t in pages if url_part in t["url"]]
        if len(pages) != 1:
            sys.exit(f"expected one matching tab, found {[t['url'] for t in pages]}; pass --url")
        self.session = self.send("Target.attachToTarget",
                                 {"targetId": pages[0]["targetId"], "flatten": True},
                                 session=False)["sessionId"]
        return pages[0]["url"]

    def evaluate(self, expr):
        res = self.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True,
                                             "returnByValue": True})
        if "exceptionDetails" in res:
            raise RuntimeError(res["exceptionDetails"].get("text", "evaluation failed"))
        return res["result"].get("value")


def touch(cdp, kind, points):
    cdp.send("Input.dispatchTouchEvent", {
        "type": kind,
        "touchPoints": [{"x": x, "y": y, "id": i} for i, (x, y) in enumerate(points)],
    })


def glide(cdp, starts, ends, ms):
    steps = max(1, ms // FRAME_MS)
    touch(cdp, "touchStart", starts)
    for n in range(1, steps + 1):
        f = n / steps
        touch(cdp, "touchMove", [(sx + (ex - sx) * f, sy + (ey - sy) * f)
                                 for (sx, sy), (ex, ey) in zip(starts, ends)])
        time.sleep(FRAME_MS / 1000)
    touch(cdp, "touchEnd", [])


def run_gesture(cdp, step):
    if "tap" in step:
        x, y = step["tap"]
        touch(cdp, "touchStart", [(x, y)])
        touch(cdp, "touchEnd", [])
    elif "drag" in step:
        x1, y1, x2, y2 = step["drag"]
        glide(cdp, [(x1, y1)], [(x2, y2)], step.get("ms", 300))
    elif "pinch" in step:
        cx, cy, g0, g1 = step["pinch"]
        glide(cdp, [(cx - g0 / 2, cy), (cx + g0 / 2, cy)],
              [(cx - g1 / 2, cy), (cx + g1 / 2, cy)], step.get("ms", 300))
    elif "wheel" in step:
        x, y, dy = step["wheel"]
        cdp.send("Input.dispatchMouseEvent", {"type": "mouseWheel", "x": x, "y": y,
                                              "deltaX": 0, "deltaY": dy,
                                              "modifiers": 2 if step.get("ctrl") else 0})
    else:
        raise ValueError(f"not a gesture: {step}")


def emulate(cdp, touch_on, cpu):
    if touch_on:
        cdp.send("Emulation.setTouchEmulationEnabled", {"enabled": True, "maxTouchPoints": 5})
        cdp.send("Emulation.setEmitTouchEventsForMouse", {"enabled": True, "configuration": "mobile"})
    if cpu != 1:
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu})


# Start the clock at the input event's own timestamp and poll the predicate on
# every animation frame, so the number covers the handler and the frame that
# shows the change.
TIMER_JS = """(pred => {
    const probe = window.__probe = {t0: null, dt: null};
    const start = e => { if (probe.t0 === null) probe.t0 = e.timeStamp; };
    for (const type of ["touchstart", "pointerdown", "wheel"])
        addEventListener(type, start, {capture: true, once: true, passive: true});
    const tick = now => {
        if (probe.t0 !== null && eval(pred)) probe.dt = now - probe.t0;
        else requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    return true; })(%s)"""


def run_step(cdp, step):
    out = {"step": step}
    if "wait" in step:
        time.sleep(step["wait"] / 1000)
    elif "eval" in step:
        out["result"] = cdp.evaluate(step["eval"])
    elif "screenshot" in step:
        data = cdp.send("Page.captureScreenshot", {"format": "png"})["data"]
        with open(step["screenshot"], "wb") as fh:
            fh.write(base64.b64decode(data))
    elif "time_to_change" in step:
        cdp.evaluate(TIMER_JS % json.dumps(step["time_to_change"]))
        run_gesture(cdp, step["after"])
        deadline = time.time() + step.get("timeout", 3000) / 1000
        while time.time() < deadline and cdp.evaluate("window.__probe.dt") is None:
            time.sleep(0.01)
        out["ms"] = cdp.evaluate("window.__probe.dt")
    else:
        run_gesture(cdp, step)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ws")
    ap.add_argument("src", help="steps file, - for stdin, or hold")
    ap.add_argument("--url", default="")
    ap.add_argument("--cpu", type=float, default=1)
    args = ap.parse_args()
    with connect(args.ws, max_size=None) as ws:
        cdp = Cdp(ws)
        url = cdp.attach(args.url)
        if args.src == "hold":
            emulate(cdp, True, args.cpu)
            print(json.dumps({"hold": url, "cpu": args.cpu}), flush=True)
            while True:
                time.sleep(3600)
        spec = json.load(sys.stdin if args.src == "-" else open(args.src, encoding="utf-8"))
        emulate(cdp, spec.get("touch", False), spec.get("cpu", 1))
        for step in spec["steps"]:
            print(json.dumps(run_step(cdp, step)), flush=True)


if __name__ == "__main__":
    main()
