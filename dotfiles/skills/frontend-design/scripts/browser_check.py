# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.64.1"]  # bump together with --install-browser
# ///
"""Screenshot named UI states at several widths in headless Chromium.

Covers the repeatable part of browser verification: serving a static build,
capturing each state at desktop and narrow widths with and without reduced
motion, a 200%-zoom pass, a keyboard walk to a target control, and HTTP, console,
and horizontal-overflow problems. Script app-specific interactions (click,
submit, retry) separately; give transient states a URL switch (for example
?latency=5000) so they can be captured here.

    mise exec -- uv run browser_check.py --install-browser   # once per machine
    mise exec -- uv run browser_check.py --serve dist --spa \\
        --state main=/ --state empty='/?q=zzz' --ready '[data-loaded]' \\
        --tab-to '#primary-action' --out design/screenshots
"""

import argparse
import contextlib
import functools
import http.server
import pathlib
import subprocess
import sys
import threading
import urllib.parse

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

MAX_TABS = 100


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--install-browser", action="store_true",
                        help="install Chromium for this script's Playwright version, then exit")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--serve", type=pathlib.Path, help="static directory to serve on a free port")
    source.add_argument("--url", help="base URL of a running app, e.g. http://127.0.0.1:5173")
    parser.add_argument("--spa", action="store_true",
                        help="with --serve, answer unknown extensionless paths with index.html")
    parser.add_argument("--state", action="append", default=[], metavar="NAME=PATH",
                        help="named state and its path/query; repeatable")
    parser.add_argument("--widths", default="1440,375", help="comma-separated viewport widths")
    parser.add_argument("--out", type=pathlib.Path, help="screenshot directory (keep it in the project)")
    parser.add_argument("--full-page", action="store_true", help="capture the full scroll height")
    parser.add_argument("--ready", metavar="SELECTOR",
                        help="wait for this element before each capture (e.g. a loaded-data marker)")
    parser.add_argument("--wait", type=int, default=300, help="extra ms to wait before each capture")
    parser.add_argument("--tab-to", metavar="SELECTOR",
                        help="press Tab from the first state until this element is focused")
    parser.add_argument("--no-zoom", action="store_true", help="skip the 200%%-zoom pass")
    parser.add_argument("--no-reduced-motion", action="store_true",
                        help="skip the reduced-motion pass at each width")
    args = parser.parse_args()
    if not args.install_browser and not ((args.serve or args.url) and args.state and args.out):
        parser.error("--serve or --url, at least one --state, and --out are required")
    return args


@contextlib.contextmanager
def static_server(directory, spa):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_head(self):
            request_path = urllib.parse.urlsplit(self.path).path
            missing = not pathlib.Path(self.translate_path(request_path)).exists()
            if spa and missing and not pathlib.PurePosixPath(request_path).suffix:
                self.path = "/index.html"
            return super().send_head()

    handler = functools.partial(Handler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()


def load(page, url, label, args, problems):
    """Navigate and wait until the state is settled; return False if it failed to load."""
    response = page.goto(url)
    # goto returns None for same-document navigations such as hash-route changes.
    if response is not None and response.status >= 400:
        problems.append(f"{label}: {url} returned {response.status}")
        return False
    with contextlib.suppress(PlaywrightTimeout):
        page.wait_for_load_state("networkidle", timeout=5000)
    if args.ready:
        try:
            page.wait_for_selector(args.ready, timeout=10000)
        except PlaywrightTimeout:
            problems.append(f"{label}: {args.ready} did not appear at {url}")
    page.wait_for_timeout(args.wait)
    return True


def is_favicon(url):
    return urllib.parse.urlsplit(url).path.endswith("/favicon.ico")


def report_console(message, label, problems):
    # Failed requests are reported once, with their URL, by report_response or report_failure.
    if message.type == "error" and not message.text.startswith("Failed to load resource"):
        problems.append(f"{label}: console: {message.text}")


def report_response(response, label, problems):
    # load() checks the top-level document's status; subframes and subresources are checked here.
    request = response.request
    if response.status < 400 or is_favicon(response.url):
        return
    if request.resource_type == "document" and request.frame == request.frame.page.main_frame:
        return
    problems.append(f"{label}: HTTP {response.status} {response.url}")


def report_failure(request, label, problems):
    # Requests that never got a response: refused connections, DNS, CORS, aborted loads.
    if not is_favicon(request.url):
        problems.append(f"{label}: request failed ({request.failure}) {request.url}")


def new_page(context, label, problems):
    page = context.new_page()
    page.on("console", lambda m: report_console(m, label, problems))
    page.on("response", lambda r: report_response(r, label, problems))
    page.on("requestfailed", lambda r: report_failure(r, label, problems))
    page.on("pageerror", lambda e: problems.append(f"{label}: {e}"))
    return page


def capture(browser, base, states, label, context_options, args, problems):
    context = browser.new_context(**context_options)
    for name, state_path in states:
        # A fresh page per state, so hash-route states start from a clean load.
        page = new_page(context, f"{label}/{name}", problems)
        if not load(page, base + state_path, f"{label}/{name}", args, problems):
            page.close()
            continue
        overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        if overflow > 0:
            problems.append(f"{label}/{name}: horizontal overflow of {overflow}px")
        target = args.out / f"{label}-{name}.png"
        page.screenshot(path=str(target), full_page=args.full_page)
        print("saved", target)
        page.close()
    page = new_page(context, f"{label}/tab", problems)
    if args.tab_to and load(page, base + states[0][1], f"{label}/tab", args, problems):
        def focused():
            return page.evaluate("s => !!document.activeElement?.matches(s)", args.tab_to)

        presses = 0
        while not focused() and presses < MAX_TABS:
            page.keyboard.press("Tab")
            presses += 1
        if focused():
            print(f"{label}: {presses} Tab presses to {args.tab_to}")
            target = args.out / f"{label}-keyboard-focus.png"
            page.screenshot(path=str(target))
            print("saved", target)
        else:
            problems.append(f"{label}: {args.tab_to} not reachable within {MAX_TABS} Tab presses")
    context.close()


def main():
    args = parse_args()
    if args.install_browser:
        sys.exit(subprocess.call([sys.executable, "-m", "playwright", "install", "chromium"]))
    args.out.mkdir(parents=True, exist_ok=True)
    states = [tuple(s.split("=", 1)) for s in args.state]
    if any(len(s) != 2 for s in states):
        sys.exit("--state must look like NAME=PATH")
    widths = [int(w) for w in args.widths.split(",")]
    problems = []
    server = static_server(args.serve, args.spa) if args.serve else contextlib.nullcontext(args.url.rstrip("/"))
    with server as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width in widths:
            options = {"viewport": {"width": width, "height": 900 if width > 800 else 812},
                       "device_scale_factor": 1 if width > 800 else 2}
            capture(browser, base, states, str(width), options, args, problems)
            if not args.no_reduced_motion:
                capture(browser, base, states, f"{width}-reduced-motion",
                        {**options, "reduced_motion": "reduce"}, args, problems)
        if not args.no_zoom:
            # Browser zoom at 200% halves the CSS viewport and doubles device pixels.
            zoom_width = max(widths) // 2
            options = {"viewport": {"width": zoom_width, "height": 450}, "device_scale_factor": 2}
            capture(browser, base, states, f"zoom200-{zoom_width}", options, args, problems)
        browser.close()
    if problems:
        print("problems:", *problems, sep="\n  ")
    else:
        print("problems: none")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
