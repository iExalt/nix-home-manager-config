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
  {"tap": [x, y]}                                    reports what the touch landed on
  {"tap": [x, y], "box": [x, y, w, h], "selector": css, "quiet": 150, "settle_timeout": 2000}
      waits until the element (the one `selector` matches, else the one filling the box that
      agent-browser's `get box` reported) has
      held still for `quiet` ms and is on top, taps its centre, and fails if the touch landed
      outside it. It sees only DOM rects: motion drawn inside a canvas is invisible to it.
  {"drag": [x1, y1, x2, y2], "ms": 300}             one finger, 16 ms per move
  {"pinch": [cx, cy, start_gap, end_gap], "ms": 300}  two fingers, horizontal
  {"wheel": [x, y, delta_y], "ctrl": false}          ctrl=true stands in for trackpad pinch
  {"wait": ms}
  {"eval": "js expression"}                          result printed as JSON
  {"screenshot": "/path.png"}                        CSS-pixel size; use agent-browser's
                                                     screenshot for full resolution
  {"time_to_change": "js predicate", "after": <tap|drag|wheel step>, "timeout": 3000}
Coordinates are CSS pixels in the viewport. Each step prints one JSON line. A tap that is
refused or misses prints a line with "error" and exits with status 3.
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


class TapError(Exception):
    """A tap that was refused before touching, or that landed outside its target."""


# Scripts below run as single expressions, never top-level declarations: every evaluation shares
# one realm, so a second `const` of the same name would throw.
DESCRIBE_JS = """(e => {
    if (!e) return "nothing";
    const label = (e.getAttribute?.("aria-label") || e.innerText || e.value || "").trim().slice(0, 40);
    return e.tagName.toLowerCase() + (e.id ? "#" + e.id : "") + (label ? ` "${label}"` : "");
})"""

# Find the element that fills the box agent-browser reported, then wait, frame by frame, until it
# has held still for `quiet` ms and nothing covers its centre. Falls back to timers when the tab
# is hidden and animation frames stop.
SETTLE_JS = """((describe, watchLanding, [bx, by, bw, bh], selector, quiet, timeout) => new Promise(resolve => {
    const near = (r) => Math.abs(r.x - bx) <= 1 && Math.abs(r.y - by) <= 1 &&
                        Math.abs(r.width - bw) <= 1 && Math.abs(r.height - bh) <= 1;
    const CONTROL = "a[href], button, input, select, textarea, summary, label, [role], [tabindex]";
    const same = (r) => Math.abs(r.width - bw) <= 1 && Math.abs(r.height - bh) <= 1;
    const stack = document.elementsFromPoint(bx + bw / 2, by + bh / 2);
    // The element that fills the box; if it has moved since the box was read, the topmost
    // element of the same size under the box's centre.
    const find = () => {
        // A CSS selector names the element exactly; @refs and other locators only have the box.
        if (selector) {
            try { const q = document.querySelectorAll(selector); if (q.length === 1) return q[0]; }
            catch (_) { selector = null; }
        }
        const here = document.elementsFromPoint(bx + bw / 2, by + bh / 2);
        // Prefer a control over a same-size layer above it, such as a transparent scrim.
        const pick = (test) => {
            const fits = here.filter(e => test(e.getBoundingClientRect()));
            return fits.find(e => e.matches(CONTROL)) || fits[0];
        };
        return pick(near) || pick(same);
    };
    let el = find();
    if (!el) {
        const top = stack[0], r = top && top.getBoundingClientRect();
        return resolve({error: `no element fills the box [${[bx, by, bw, bh].map(Math.round)}]` +
            (r ? `; topmost is ${describe(top)} at [${[r.x, r.y, r.width, r.height].map(Math.round)}]` : "") +
            "; it moved or was re-rendered after its box was read, so try again"});
    }
    const start = performance.now();
    let last = "", since = start;
    const tick = () => {
        const now = performance.now();
        if (!el.isConnected) {
            // A re-render replaced the node; follow its replacement if one fills the same box.
            const next = find();
            if (!next) return resolve({error: `${describe(el)} was removed before the tap`});
            el = next;
        }
        const r = el.getBoundingClientRect();
        const key = [r.x, r.y, r.width, r.height].join();
        if (key !== last) { last = key; since = now; }
        const x = r.x + r.width / 2, y = r.y + r.height / 2;
        const hit = document.elementFromPoint(x, y);
        if (now - since >= quiet && hit && el.contains(hit)) {
            if (!(x >= 0 && y >= 0 && x < innerWidth && y < innerHeight))
                return resolve({error: `${describe(el)} is outside the ${innerWidth}x${innerHeight} viewport`});
            window.__tapTarget = el;
            window.__tapRect = [r.x, r.y, r.width, r.height];
            watchLanding();  // in the same evaluation, so nothing runs between settling and arming
            return resolve({x, y, waited_ms: Math.round(now - start)});
        }
        if (now - start > timeout) return resolve({error: `${describe(el)} ` + (now - since < quiet
            ? `was still moving after ${timeout} ms` : `stayed covered by ${describe(hit)}`)});
        if (document.hidden) setTimeout(tick, 16); else requestAnimationFrame(tick);
    };
    tick();
}))(""" + DESCRIBE_JS.replace("%", "%%") + """, () => LANDING_JS, %s, %s, %s, %s)"""

# Record what the touch actually landed on, at the moment it landed.
LANDING_JS = """(describe => {
    const target = window.__tapTarget || null, box = window.__tapRect;
    window.__landed = null;
    // A re-render can swap the node between settling and the touch; a replacement in the same
    // place counts as the target.
    const replaced = (e) => {
        const r = e.getBoundingClientRect();
        return !target.isConnected && [r.x, r.y, r.width, r.height].every((v, i) => Math.abs(v - box[i]) <= 1);
    };
    const record = e => {
        if (window.__landed === null) window.__landed = {on: describe(e.target),
            inside: target ? target.contains(e.target) || replaced(e.target) : null};
    };
    for (const type of ["touchstart", "pointerdown"])
        addEventListener(type, record, {capture: true, once: true, passive: true});
    return true;
})(""" + DESCRIBE_JS + ")"


# Settling arms the landing record itself (see SETTLE_JS).
SETTLE_JS = SETTLE_JS.replace("LANDING_JS", LANDING_JS.replace("%", "%%"))


def run_tap(cdp, step):
    x, y = step["tap"]
    cdp.evaluate("window.__tapTarget = null, window.__tapRect = null")
    info = {}
    if "box" in step:
        settled = cdp.evaluate(SETTLE_JS % (json.dumps(step["box"]), json.dumps(step.get("selector")),
                                            step.get("quiet", 150), step.get("settle_timeout", 2000)))
        if "error" in settled:
            raise TapError("not tapped: " + settled["error"])
        x, y, info["waited_ms"] = settled["x"], settled["y"], settled["waited_ms"]
    else:
        w, h = cdp.evaluate("[innerWidth, innerHeight]")
        if not (0 <= x < w and 0 <= y < h):
            raise TapError(f"not tapped: {round(x)},{round(y)} is outside the {w}x{h} viewport")
        cdp.evaluate(LANDING_JS)
    touch(cdp, "touchStart", [(x, y)])
    touch(cdp, "touchEnd", [])
    landed = cdp.evaluate("window.__landed") or {"on": "nothing (no touchstart or pointerdown fired)",
                                                  "inside": False if "box" in step else None}
    info.update(tapped=[round(x), round(y)], landed=landed["on"])
    if landed["inside"] is False:
        raise TapError(f"tapped but missed: the touch at {round(x)},{round(y)} landed on {landed['on']}")
    return info


def run_gesture(cdp, step):
    if "tap" in step:
        return run_tap(cdp, step)
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
    return {}


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
        # The clock starts at the touch event's timestamp, so a tap's settle wait isn't counted.
        cdp.evaluate(TIMER_JS % json.dumps(step["time_to_change"]))
        out.update(run_gesture(cdp, step["after"]))
        deadline = time.time() + step.get("timeout", 3000) / 1000
        while time.time() < deadline and cdp.evaluate("window.__probe.dt") is None:
            time.sleep(0.01)
        out["ms"] = cdp.evaluate("window.__probe.dt")
    else:
        out.update(run_gesture(cdp, step))
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
        if args.src == "-":
            spec = json.load(sys.stdin)
        else:
            with open(args.src, encoding="utf-8") as fh:
                spec = json.load(fh)
        emulate(cdp, spec.get("touch", False), spec.get("cpu", 1))
        for step in spec["steps"]:
            try:
                print(json.dumps(run_step(cdp, step)), flush=True)
            except TapError as e:
                print(json.dumps({"step": step, "error": str(e)}), flush=True)
                sys.exit(3)


if __name__ == "__main__":
    main()
