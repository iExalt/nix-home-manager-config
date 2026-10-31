# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.64.1"]  # after bumping, rerun --install-browser
# ///
"""Screenshot named UI states at several widths in headless Chromium.

Covers the repeatable part of browser verification: serving a static build,
capturing each state at desktop and narrow widths, reduced-motion and 200%-zoom
passes on the first (key) state (every state with --all-passes), a keyboard walk
to a target control, and HTTP, console, and horizontal-overflow problems. Script
app-specific interactions (click, submit, retry) separately; give transient
states a URL switch (for example ?latency=5000) so they can be captured here.

    mise exec -- uv run browser_check.py --install-browser   # once per machine
    mise exec -- uv run browser_check.py --serve dist --spa \\
        --state main=/ --state posting='/?latency=5000' \\
        --ready main='[data-loaded]' --ready posting='[aria-busy=true]' \\
        --tab-to '#primary-action' --out design/screenshots
"""

import argparse
import contextlib
import functools
import http.server
import pathlib
import re
import subprocess
import sys
import threading
import urllib.parse

from playwright.sync_api import Error as PlaywrightError
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
                        help="with --serve, answer page requests for unknown paths with index.html "
                             "(status 200, so client-rendered 404 pages need no --status)")
    parser.add_argument("--state", action="append", default=[], metavar="NAME=PATH",
                        help="named state and its path/query; repeatable")
    parser.add_argument("--widths", default="1440,375", help="comma-separated viewport widths")
    parser.add_argument("--out", type=pathlib.Path, help="screenshot directory (keep it in the project)")
    parser.add_argument("--full-page", action="store_true", help="capture the full scroll height")
    parser.add_argument("--ready", action="append", default=[], metavar="NAME=SELECTOR",
                        help="for state NAME, wait for this element instead of network idle; use it "
                             "for data loaded after the page and for transient states; repeatable")
    parser.add_argument("--status", action="append", default=[], metavar="NAME=CODE",
                        help="expected HTTP status for state NAME, e.g. notfound=404 for a designed "
                             "error page; other states must be below 400; repeatable")
    parser.add_argument("--all-passes", action="store_true",
                        help="run the reduced-motion and zoom passes on every state, not just the first")
    parser.add_argument("--idle-timeout", type=int, default=2000,
                        help="ms to wait for network idle on states without --ready; 0 skips it "
                             "(streaming and polling UIs never go idle)")
    parser.add_argument("--wait", type=int, default=300, help="extra ms to wait before each capture")
    parser.add_argument("--tab-to", action="append", default=[], metavar="[WIDTH=]SELECTOR",
                        help="press Tab from the first state until this element is focused; prefix "
                             "WIDTH= to limit it to one width (e.g. 1440='#save' and "
                             "375='#menu-button' when the control collapses on mobile); repeatable")
    parser.add_argument("--no-zoom", action="store_true", help="skip the 200%%-zoom pass")
    parser.add_argument("--no-reduced-motion", action="store_true",
                        help="skip the reduced-motion pass at each width")
    args = parser.parse_args()
    if not args.install_browser and not ((args.serve or args.url) and args.state and args.out):
        parser.error("--serve or --url, at least one --state, and --out are required")
    names = {state.split("=", 1)[0] for state in args.state}
    for option, metavar in (("ready", "NAME=SELECTOR"), ("status", "NAME=CODE")):
        pairs = [item.split("=", 1) for item in getattr(args, option)]
        if any(len(pair) != 2 for pair in pairs):
            parser.error(f"--{option} must look like {metavar}")
        unknown = {name for name, _ in pairs} - names
        if unknown:
            parser.error(f"--{option} names no --state: {', '.join(sorted(unknown))}")
        setattr(args, option, dict(pairs))
    if not all(code.isdigit() for code in args.status.values()):
        parser.error("--status codes must be numbers, e.g. notfound=404")
    args.status = {name: int(code) for name, code in args.status.items()}
    args.idle_hint_shown = False
    tab_targets = {}
    for item in args.tab_to:
        match = re.match(r"(\d+)=(.+)", item)
        width, selector = (int(match[1]), match[2]) if match else (None, item)
        tab_targets[width] = selector
    args.tab_to = tab_targets
    return args


@contextlib.contextmanager
def static_server(directory, spa):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send_head(self):
            request_path = urllib.parse.urlsplit(self.path).path
            missing = not pathlib.Path(self.translate_path(request_path)).exists()
            # Browsers send Accept: text/html for page navigations; assets and fetches don't.
            if spa and missing and "text/html" in self.headers.get("Accept", ""):
                self.path = "/index.html"
            return super().send_head()

    handler = functools.partial(Handler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()


def load(page, url, name, label, args, problems):
    """Navigate and wait until the state is settled; return False if navigation failed."""
    try:
        response = page.goto(url)
    except PlaywrightError as error:
        problems.append(f"{label}: {url} failed to load: {error.message.splitlines()[0]}")
        return False
    # goto returns None for same-document navigations such as hash-route changes.
    if response is not None:
        expected = args.status.get(name)
        unexpected = response.status != expected if expected else response.status >= 400
        if unexpected:
            want = f" (expected {expected})" if expected else ""
            problems.append(f"{label}: {url} returned {response.status}{want}")
    ready = args.ready.get(name)
    if ready:
        try:
            page.wait_for_selector(ready, timeout=10000)
        except PlaywrightTimeout:
            problems.append(f"{label}: {ready} did not appear at {url}")
        except PlaywrightError as error:
            problems.append(f"{label}: --ready {ready!r} is not a valid selector: "
                            f"{error.message.splitlines()[0]}")
    elif args.idle_timeout:
        try:
            page.wait_for_load_state("networkidle", timeout=args.idle_timeout)
        except PlaywrightTimeout:
            if not args.idle_hint_shown:
                args.idle_hint_shown = True
                print(f"note: {url} never went network-idle; pass --idle-timeout 0 or --ready "
                      "NAME=SELECTOR for streaming or polling UIs to skip the wait")
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
    if is_main_document(request):
        return
    problems.append(f"{label}: HTTP {response.status} {response.url}")


def is_main_document(request):
    return request.resource_type == "document" and request.frame == request.frame.page.main_frame


def report_failure(request, label, problems):
    # Requests that never got a response: refused connections, DNS, CORS, aborted loads.
    # load() reports the page's own document; ERR_ABORTED is the app cancelling a request.
    if (request.failure != "net::ERR_ABORTED" and not is_favicon(request.url)
            and not is_main_document(request)):
        problems.append(f"{label}: request failed ({request.failure}) {request.url}")


def new_page(context, label, problems, listen=True):
    page = context.new_page()
    if not listen:
        return page
    page.on("console", lambda m: report_console(m, label, problems))
    page.on("response", lambda r: report_response(r, label, problems))
    page.on("requestfailed", lambda r: report_failure(r, label, problems))
    page.on("pageerror", lambda e: problems.append(f"{label}: {e}"))
    return page


def capture(browser, base, states, label, context_options, args, problems, tab_to=None):
    context = browser.new_context(**context_options)
    for name, state_path in states:
        # A fresh page per state, so hash-route states start from a clean load.
        page = new_page(context, f"{label}/{name}", problems)
        if not load(page, base + state_path, name, f"{label}/{name}", args, problems):
            page.close()
            continue
        screen_width = context_options["viewport"]["width"]
        if context_options.get("is_mobile"):
            # Mobile Chromium widens the layout viewport to fit content instead of scrolling, so
            # compare against the screen and say whether the meta tag or the content is at fault.
            meta = page.evaluate("document.querySelector('meta[name=viewport]')?.content ?? ''")
            if "width=device-width" not in meta.replace(" ", ""):
                problems.append(f"{label}/{name}: no width=device-width viewport meta tag; phones "
                                "render a zoomed-out desktop page")
            overflow = page.evaluate("document.documentElement.scrollWidth") - screen_width
        else:
            overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        if overflow > 0:
            problems.append(f"{label}/{name}: horizontal overflow of {overflow}px")
        target = args.out / f"{label}-{name}.png"
        page.screenshot(path=str(target), full_page=args.full_page)
        print("saved", target)
        page.close()
    if tab_to:
        tab_walk(context, base, states[0], label, tab_to, args, problems)
    context.close()


def tab_walk(context, base, state, label, selector, args, problems):
    name, state_path = state
    # The state's own capture already reported its load problems; don't report them twice.
    page = new_page(context, f"{label}/tab", problems, listen=False)
    if load(page, base + state_path, name, f"{label}/tab", args, []):
        def focused():
            return page.evaluate("s => !!document.activeElement?.matches(s)", selector)

        try:
            focused()
        except PlaywrightError as error:
            problems.append(f"{label}: --tab-to {selector!r} is not a valid selector: "
                            f"{error.message.splitlines()[0]}")
            page.close()
            return

        presses = 0
        while not focused() and presses < MAX_TABS:
            page.keyboard.press("Tab")
            presses += 1
        if focused():
            print(f"{label}: {presses} Tab presses to {selector}")
            target = args.out / f"{label}-keyboard-focus.png"
            page.screenshot(path=str(target))
            print("saved", target)
        else:
            problems.append(f"{label}: {selector} not reachable within {MAX_TABS} Tab presses")
    page.close()


def main():
    args = parse_args()
    if args.install_browser:
        sys.exit(subprocess.call([sys.executable, "-m", "playwright", "install", "chromium"]))
    args.out.mkdir(parents=True, exist_ok=True)
    states = [tuple(s.split("=", 1)) for s in args.state]
    if any(len(s) != 2 for s in states):
        sys.exit("--state must look like NAME=PATH")
    # Paths join the base URL directly, so give bare paths their leading slash.
    states = [(name, state_path if state_path.startswith(("/", "?", "#")) else "/" + state_path)
              for name, state_path in states]
    widths = [int(w) for w in args.widths.split(",")]
    problems = []
    server = static_server(args.serve, args.spa) if args.serve else contextlib.nullcontext(args.url.rstrip("/"))
    with server as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        # The extra passes cover the first (key) state unless --all-passes; the Tab walk runs
        # once per width, since reduced motion and zoom do not change focus order.
        extra_states = states if args.all_passes else states[:1]
        for width in widths:
            narrow = width <= 800
            # Narrow widths emulate a phone: the viewport meta tag, touch, and coarse pointer apply.
            options = {"viewport": {"width": width, "height": 812 if narrow else 900},
                       "device_scale_factor": 2 if narrow else 1, "is_mobile": narrow,
                       "has_touch": narrow}
            capture(browser, base, states, str(width), options, args, problems,
                    tab_to=args.tab_to.get(width, args.tab_to.get(None)))
            if not args.no_reduced_motion:
                capture(browser, base, extra_states, f"{width}-reduced-motion",
                        {**options, "reduced_motion": "reduce"}, args, problems)
        if not args.no_zoom:
            # Browser zoom at 200% halves the CSS viewport and doubles device pixels.
            zoom_width = max(widths) // 2
            options = {"viewport": {"width": zoom_width, "height": 450}, "device_scale_factor": 2}
            capture(browser, base, extra_states, f"zoom200-{zoom_width}", options, args, problems)
        browser.close()
    if problems:
        print("problems:", *problems, sep="\n  ")
    else:
        print("problems: none")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
