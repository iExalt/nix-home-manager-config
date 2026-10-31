# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""Screenshot named UI states at several widths in headless Chromium.

Covers the repeatable part of browser verification: serving a static build,
capturing each state at desktop and narrow widths, a 200%-zoom and
reduced-motion pass, a keyboard walk to a target control, and console errors.
Script app-specific interactions (click, submit, retry) separately; give
transient states a URL switch (for example ?latency=5000) so they can be
captured here.

    uv run browser_check.py --serve dist --state main=/ --state empty='/?q=zzz' \
        --tab-to '#primary-action' --out /tmp/shots

Install the browser once with: uvx playwright install chromium
"""

import argparse
import contextlib
import functools
import http.server
import pathlib
import sys
import threading

from playwright.sync_api import sync_playwright


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--serve", type=pathlib.Path, help="static directory to serve on a free port")
    source.add_argument("--url", help="base URL of a running app, e.g. http://127.0.0.1:5173")
    parser.add_argument("--state", action="append", required=True, metavar="NAME=PATH",
                        help="named state and its path/query; repeatable")
    parser.add_argument("--widths", default="1440,375", help="comma-separated viewport widths")
    parser.add_argument("--out", type=pathlib.Path, required=True, help="screenshot directory")
    parser.add_argument("--full-page", action="store_true", help="capture the full scroll height")
    parser.add_argument("--wait", type=int, default=300, help="ms to wait after load")
    parser.add_argument("--tab-to", metavar="SELECTOR",
                        help="press Tab from the first state until this element is focused")
    parser.add_argument("--no-zoom", action="store_true", help="skip the 200%%-zoom/reduced-motion pass")
    return parser.parse_args()


@contextlib.contextmanager
def static_server(directory):
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

    handler = functools.partial(QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()


def capture(browser, base, states, label, context_options, args, errors):
    context = browser.new_context(**context_options)
    page = context.new_page()
    page.on("console", lambda m: m.type == "error" and errors.append(f"{label}: {m.text}"))
    page.on("pageerror", lambda e: errors.append(f"{label}: {e}"))
    for name, state_path in states:
        page.goto(base + state_path)
        page.wait_for_timeout(args.wait)
        overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        if overflow > 0:
            errors.append(f"{label}/{name}: horizontal overflow of {overflow}px")
        target = args.out / f"{label}-{name}.png"
        page.screenshot(path=str(target), full_page=args.full_page)
        print("saved", target)
    if args.tab_to:
        page.goto(base + states[0][1])
        page.wait_for_timeout(args.wait)
        presses = 0
        while not page.evaluate("s => document.activeElement?.matches(s)", args.tab_to) and presses < 100:
            page.keyboard.press("Tab")
            presses += 1
        if presses == 100:
            errors.append(f"{label}: {args.tab_to} not reachable within 100 Tab presses")
        else:
            print(f"{label}: {presses} Tab presses to {args.tab_to}")
            target = args.out / f"{label}-keyboard-focus.png"
            page.screenshot(path=str(target))
            print("saved", target)
    context.close()


def main():
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    states = [tuple(s.split("=", 1)) for s in args.state]
    if any(len(s) != 2 for s in states):
        sys.exit("--state must look like NAME=PATH")
    errors = []
    server = static_server(args.serve) if args.serve else contextlib.nullcontext(args.url.rstrip("/"))
    with server as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width in (int(w) for w in args.widths.split(",")):
            options = {"viewport": {"width": width, "height": 900 if width > 800 else 812},
                       "device_scale_factor": 1 if width > 800 else 2}
            capture(browser, base, states, str(width), options, args, errors)
        if not args.no_zoom:
            # 200% zoom at 1440 CSS px renders like a 720 CSS px viewport at 2x density.
            options = {"viewport": {"width": 720, "height": 450}, "device_scale_factor": 2,
                       "reduced_motion": "reduce"}
            capture(browser, base, states[:1], "zoom200-reduced-motion", options, args, errors)
        browser.close()
    print("problems:", *errors, sep="\n  ") if errors else print("problems: none")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
