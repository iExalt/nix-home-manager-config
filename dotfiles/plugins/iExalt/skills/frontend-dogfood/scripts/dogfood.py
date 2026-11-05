# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=10"]
# ///
"""Drive one agent-browser session on the browser host from the laptop.

Every command runs as one ssh call with its arguments quoted for you, so
JavaScript and selectors survive intact. Screenshots come back to the local
evidence directory with a CSS-pixel-size view copy, which is what to look at.

  uv run dogfood.py init S --host H --evidence DIR [--url-part P] [--open URL]
  uv run dogfood.py ab S ARGS...         one agent-browser command
  uv run dogfood.py ab S - < cmds        one agent-browser command per line (shell-style quoting)
  uv run dogfood.py eval S FILE|-        evaluate a JavaScript file (or stdin) in the page
  uv run dogfood.py shot S NAME [--full-page]
  uv run dogfood.py hold S [--cpu N]     touch emulation on (and CPU throttling), verified
  uv run dogfood.py release S            touch emulation and throttling off
  uv run dogfood.py tap S TARGET [--until JS] [--timeout MS]
  uv run dogfood.py steps S FILE|-       touch_probe steps (see touch_probe.py)
  uv run dogfood.py close S              stop the browser, the hold, and remove host files

S is the session name. TARGET is an @ref from `snapshot -i`, a CSS selector, or
X,Y in viewport CSS pixels. With --until, tap prints the milliseconds from the
touch to the first frame where the predicate holds.
"""
import argparse
import json
import pathlib
import re
import shlex
import subprocess
import sys
import time

STATE = pathlib.Path("/tmp/frontend-dogfood")
PROBE = pathlib.Path(__file__).with_name("touch_probe.py")
EOF_MARK = "DOGFOOD_EOF_7f3c"
# Under touch emulation these hang on a mouse event (click, check, mouse down/up/wheel, measured at
# 20 s and more) or do nothing (hover, mouse move), so a tester would misjudge the app.
MOUSE_ONLY = {"click", "dblclick", "drag", "check", "uncheck", "hover", "mouse"}


def load(session):
    path = STATE / f"{session}.json"
    if not path.exists():
        sys.exit(f"no session {session!r}: run `dogfood.py init {session} --host ... --evidence ...` first")
    return json.loads(path.read_text())


def save(cfg):
    (STATE / f"{cfg['session']}.json").write_text(json.dumps(cfg, indent=1))


def browser_alive(scope):
    """Shell test: the scope still holds a process other than its virtual display.

    Xvfb keeps a headed session's scope active after the browser exits (for example on its idle
    timeout), so an active scope alone doesn't mean the browser is there.
    """
    return (f'(cg=$(systemctl --user show -p ControlGroup --value {scope}.scope 2>/dev/null) && '
            f'pids=$(paste -sd, "/sys/fs/cgroup$cg/cgroup.procs" 2>/dev/null) && [ -n "$pids" ] && '
            'ps -o comm= -p "$pids" | grep -qvx Xvfb)')


def guards(cfg):
    """Shell checks that the browser scope and touch hold are still alive.

    Without lingering on the host, either can stop between calls. agent-browser would then start an
    uncapped browser with default settings, or the page would quietly lose touch, and the tester
    would judge the wrong app.
    """
    out = []
    if cfg.get("scope"):
        out.append(f"{browser_alive(cfg['scope'])} || {{ systemctl --user stop {cfg['scope']}.scope 2>/dev/null; "
                   "echo 'browser session gone (idle timeout, or lingering off on the host?). "
                   "Re-run dogfood.py init --open' >&2; exit 3; }")
    if cfg.get("hold"):
        out.append(f"systemctl --user is-active -q dogfood-{cfg['session']}-touch || {{ echo 'touch hold stopped: "
                   f"run dogfood.py hold {cfg['session']} again before judging touch sizes' >&2; exit 3; }}")
    return out


def remote(cfg, body, check=True, guard=True):
    """Run a bash script on the host with agent-browser as `ab`; return stdout."""
    script = "\n".join([
        'eval "$(mise env -s bash)"',
        f"export AGENT_BROWSER_CONFIG={cfg['config']}",
        f"ab() {{ agent-browser --session {shlex.quote(cfg['session'])} \"$@\"; }}",
        f"D=/tmp/dogfood-{cfg['session']}; mkdir -p \"$D\"",
        *(guards(cfg) if guard else []),
        body,
    ])
    res = subprocess.run(["ssh", "-T", "-o", "BatchMode=yes", cfg["host"], "bash -lc " + shlex.quote(script)],
                         check=False, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    err = "\n".join(l for l in res.stderr.splitlines() if "Pseudo-terminal" not in l)
    if err:
        print(err, file=sys.stderr)
    if check and res.returncode:
        print(res.stdout, end="")
        sys.exit(res.returncode)
    return res.stdout


def heredoc(path, text):
    return f"cat > {path} <<'{EOF_MARK}'\n{text}\n{EOF_MARK}"


def read_src(src):
    return sys.stdin.read() if src == "-" else pathlib.Path(src).read_text()


def probe_args(cfg):
    return '"$WS" "$D/steps.json"' + (f" --url {shlex.quote(cfg['url_part'])}" if cfg["url_part"] else "")


def cmd_init(a):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", a.session):
        sys.exit("session names may use only letters, digits, - and _")
    old = STATE / f"{a.session}.json"
    old_scope = json.loads(old.read_text()).get("scope") if old.exists() else None
    cfg = {"session": a.session, "host": a.host, "evidence": str(pathlib.Path(a.evidence).resolve()),
           "url_part": a.url_part, "config": a.config, "hold": False}
    STATE.mkdir(exist_ok=True)
    save(cfg)
    (pathlib.Path(cfg["evidence"]) / "view").mkdir(parents=True, exist_ok=True)
    xvfb = "" if a.headless else ('command -v Xvfb >/dev/null || { echo "Xvfb missing on the host: install it, '
                                  'or pass --headless and report hover untested"; exit 1; }\n')
    print(remote(cfg, """command -v agent-browser >/dev/null || { echo "agent-browser missing on the host; see devices.md › Tier 1 › Setup, once per host"; exit 1; }
command -v uv >/dev/null || { echo "uv missing on the host: mise use -g uv"; exit 1; }
""" + xvfb + """[ "$(loginctl show-user "$USER" -p Linger --value 2>/dev/null)" = yes ] ||
  echo "warning: lingering is off on the host, so the browser and touch hold stop if your last login session there ends (devices.md › Tier 1 › Setup, once per host)" """), end="")
    subprocess.run(["scp", "-q", str(PROBE), f"{a.host}:/tmp/dogfood-{a.session}/touch_probe.py"], check=True)
    if a.open:
        # A browser still running under this name would take the open and leave the new scope empty,
        # so the liveness guard would call the session dead. Start clean instead.
        # Stop the previous scope too, or its virtual display lingers on the host.
        stop_old = f"; systemctl --user stop {old_scope}.scope 2>/dev/null" if old_scope else ""
        remote(cfg, f"systemctl --user stop dogfood-{a.session}-touch 2>/dev/null; ab close >/dev/null 2>&1{stop_old}; true",
               check=False, guard=False)
        unit = f"dogfood-{a.session}-{int(time.time())}"
        cfg["scope"] = unit
        save(cfg)
        headed = "" if a.headless else " --headed"
        browser = f"agent-browser --session {shlex.quote(a.session)}{headed} open {shlex.quote(a.open)}"
        if not a.headless:
            # Headless Chrome reports no hover and no fine pointer, so apps that switch on
            # (hover: hover) or (pointer: fine) show desktop testers their touch layout. A headed
            # browser on a private virtual display reports a real mouse.
            browser = shlex.quote(
                'Xvfb -displayfd 3 -screen 0 2560x1600x24 -nolisten tcp 3>"$D/display" 2>/dev/null & '
                'for i in $(seq 50); do [ -s "$D/display" ] && break; sleep 0.1; done; '
                f'DISPLAY=:$(cat "$D/display") exec {browser}')
            browser = f'env D="$D" bash -c {browser}'
        # Check the browser is in the scope before any `ab` call, which would otherwise start an
        # uncapped headless browser; then that a headed one really sees a mouse.
        fail = f"systemctl --user stop {unit}.scope 2>/dev/null; ab close >/dev/null 2>&1; exit 1"
        need_mouse = "" if a.headless else \
            f'[ "$m" = true ] || {{ echo "headed browser reports no mouse; see devices.md" >&2; {fail}; }}'
        print(remote(cfg, guard=False, body=f"systemd-run --user --scope -q --unit={unit} -p CPUQuota={a.cpu_quota} "
                          f"-p MemoryMax={a.memory_max} {browser} >/dev/null\n"
                          f"{browser_alive(unit)} || {{ echo 'browser failed to start in its scope' >&2; {fail}; }}\n"
                          "m=$(ab eval \"matchMedia('(hover: hover)').matches && "
                          "matchMedia('(pointer: fine)').matches\"); echo \"mouse: $m\"\n" + need_mouse), end="")
    print(f"session {a.session} on {a.host}; evidence in {cfg['evidence']}")


def mouse_command(args):
    """The mouse command an agent-browser argument list would run, if any."""
    words, follows_option, skip = [], [], False
    for i, tok in enumerate(args):
        if skip:
            skip = False
        elif tok == "--name":  # find's only option that takes a value
            skip = True
        elif not tok.startswith("-"):
            words.append(tok)
            follows_option.append(i > 0 and args[i - 1].startswith("-") and "=" not in args[i - 1])
    for start in (0, 1):
        if start == 1 and not (words and follows_option[0]):
            break  # only skip the first word when it may be a global option's value, as in --timeout 5000
        w = words[start:]
        if w and w[0] in MOUSE_ONLY:
            return w[0]
        if w and w[0] == "find":
            # find <locator> <value> [action]; nth takes an index too, and the action defaults to click.
            n = 4 if len(w) > 1 and w[1] == "nth" else 3
            action = w[n] if len(w) > n else "click"
            if action in MOUSE_ONLY:
                return f"find ... {action}"
    return None


def refuse_mouse(cfg, args):
    command = mouse_command(args)
    if cfg.get("hold") and command:
        sys.exit(f"refused `{command}`: mouse input hangs or does nothing under touch emulation. Tap with "
                 "`dogfood.py tap`, drag, pinch, or wheel with `steps`, or `dogfood.py release` first.")


def cmd_ab(a):
    cfg = load(a.session)
    if a.args == ["-"]:
        lines = [l.strip() for l in sys.stdin if l.strip() and not l.lstrip().startswith("#")]
        for l in lines:
            refuse_mouse(cfg, shlex.split(l))
        body = "\n".join(f"printf '%s\\n' {shlex.quote('$ ' + l)}; ab {shlex.join(shlex.split(l))} || echo \"[exit $?]\""
                         for l in lines)
    else:
        refuse_mouse(cfg, a.args)
        body = f"ab {shlex.join(a.args)}"
    print(remote(cfg, body), end="")


def cmd_eval(a):
    cfg = load(a.session)
    print(remote(cfg, heredoc('"$D/eval.js"', read_src(a.src)) + '\nab eval --stdin < "$D/eval.js"'), end="")


def cmd_shot(a):
    from PIL import Image
    cfg = load(a.session)
    name = a.name.removesuffix(".png")
    out = remote(cfg, f"ab screenshot {'--full ' if a.full_page else ''}\"$D/{name}.png\" >/dev/null && "
                      "ab eval 'devicePixelRatio + \" \" + innerHeight'")
    dpr, screen_h = (float(v) for v in json.loads(out.strip().splitlines()[-1]).split())
    screen_h = int(screen_h)
    full = pathlib.Path(cfg["evidence"]) / f"{name}.png"
    full.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["scp", "-q", f"{cfg['host']}:/tmp/dogfood-{cfg['session']}/{name}.png", str(full)], check=True)
    view = full.parent / "view" / full.name
    view.parent.mkdir(exist_ok=True)
    with Image.open(full) as img:
        size = (round(img.width / dpr), round(img.height / dpr))
        small = img.resize(size, Image.LANCZOS) if dpr > 1 else img.copy()
    # A long full-page view would be shrunk again when read, until its text is illegible,
    # so cut it into screen-high tiles instead.
    tiles = [(0, size[1])] if size[1] <= screen_h * 1.5 else \
        [(top, min(top + screen_h, size[1])) for top in range(0, size[1], screen_h)]
    views = []
    for n, (top, bottom) in enumerate(tiles, 1):
        path = view if len(tiles) == 1 else view.with_name(f"{name}-{n}.png")
        small.crop((0, top, size[0], bottom)).save(path)
        views.append(path)
    for path in views:
        print(f"view {path}  (CSS pixels; read this one)")
    print(f"full {full}  ({size[0]}x{size[1]} CSS pixels at {dpr:g}x; for pixel checks and evidence)")


def cmd_hold(a):
    cfg = load(a.session)
    unit = f"dogfood-{a.session}-touch"
    url = f" --url {shlex.quote(cfg['url_part'])}" if cfg["url_part"] else ""
    cpu = f" --cpu {a.cpu:g}" if a.cpu != 1 else ""
    print(remote(dict(cfg, hold=False), f"""systemctl --user stop {unit} 2>/dev/null
WS=$(ab get cdp-url)
systemd-run --user -q --collect --unit={unit} "$(command -v uv)" run -q "$D/touch_probe.py" "$WS" hold{url}{cpu}
sleep 2
systemctl --user is-active {unit} >/dev/null || {{ journalctl --user -u {unit} -n 20 --no-pager; exit 1; }}
printf 'touch: '; ab eval "matchMedia('(pointer: coarse)').matches && navigator.maxTouchPoints > 0"
echo "reload the page if the app reads the pointer type only at start-up" """), end="")
    cfg["hold"] = True
    save(cfg)


def cmd_release(a):
    cfg = load(a.session)
    remote(cfg, f"systemctl --user stop dogfood-{a.session}-touch 2>/dev/null; true", guard=False)
    cfg["hold"] = False
    save(cfg)
    print("touch emulation and throttling off")


def run_steps(cfg, steps):
    return remote(cfg, heredoc('"$D/steps.json"', json.dumps(steps)) +
                  f'\nWS=$(ab get cdp-url)\nuv run -q "$D/touch_probe.py" {probe_args(cfg)}')


# What a tap at (x, y) would land on, so a tap that hits an overlay or misses is visible.
HIT_JS = """(([x, y]) => {
    const e = document.elementFromPoint(x, y);
    if (!e) return "nothing";
    const label = (e.getAttribute("aria-label") || e.innerText || e.value || "").trim().slice(0, 40);
    return e.tagName.toLowerCase() + (e.id ? "#" + e.id : "") + (label ? ` "${label}"` : "");
})(%s)"""


def cmd_tap(a):
    cfg = load(a.session)
    try:
        x, y = (float(v) for v in a.target.split(","))
    except ValueError:
        # get box reports viewport coordinates without scrolling, so bring the target into view first.
        t = shlex.quote(a.target)
        out = remote(cfg, f"ab scrollintoview {t} >/dev/null; ab --json get box {t}").strip().splitlines()
        box = json.loads(out[-1])
        if not box.get("success"):
            sys.exit(f"no box for {a.target}: {box.get('error')}")
        b = box["data"]
        x, y = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
    tap = {"tap": [round(x), round(y)]}
    step = {"time_to_change": a.until, "after": tap, "timeout": a.timeout} if a.until else tap
    check = {"eval": "[innerWidth, innerHeight]"}
    hit = {"eval": HIT_JS % json.dumps(tap["tap"])}
    lines = [json.loads(l) for l in run_steps(cfg, {"steps": [check, hit]}).splitlines() if l.startswith("{")]
    (w, h), landed = lines[0]["result"], lines[1]["result"]
    if not (0 <= x < w and 0 <= y < h):
        sys.exit(f"not tapped: {a.target} centre {tap['tap']} is outside the {w}x{h} viewport")
    last = json.loads(run_steps(cfg, {"steps": [step]}).strip().splitlines()[-1])
    ms = last.get("ms")
    took = f"; change after {ms:.0f} ms" if ms is not None else f"; no change within {a.timeout} ms"
    print(f"tapped {a.target} at {tap['tap'][0]},{tap['tap'][1]}, landing on {landed}" + (took if a.until else ""))


def cmd_steps(a):
    cfg = load(a.session)
    spec = json.loads(read_src(a.src))
    # A steps run that sets emulation clears the hold's when it exits.
    if cfg.get("hold") and {"touch", "cpu"} & spec.keys():
        print("ignoring \"touch\"/\"cpu\" in the steps: the hold already sets them", file=sys.stderr)
        spec = {k: v for k, v in spec.items() if k not in ("touch", "cpu")}
    print(run_steps(cfg, spec), end="")


def cmd_close(a):
    cfg = load(a.session)
    scope = f"; systemctl --user stop {cfg['scope']}.scope 2>/dev/null" if cfg.get("scope") else ""
    print(remote(cfg, f"systemctl --user stop dogfood-{a.session}-touch 2>/dev/null; ab close{scope}; rm -rf \"$D\"",
                 check=False, guard=False), end="")
    (STATE / f"{a.session}.json").unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init")
    p.add_argument("session"); p.add_argument("--host", required=True); p.add_argument("--evidence", required=True)
    p.add_argument("--url-part", default="", help="substring of the app's URL, to pick its tab")
    p.add_argument("--open", help="start the browser in a capped systemd scope and open this URL")
    p.add_argument("--config", default="~/.agent-browser/dogfood.json")
    p.add_argument("--cpu-quota", default="700%"); p.add_argument("--memory-max", default="16G")
    p.add_argument("--headless", action="store_true", help="no virtual display; hover and fine pointer go untested")
    p = sub.add_parser("ab"); p.add_argument("session"); p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("eval"); p.add_argument("session"); p.add_argument("src")
    p = sub.add_parser("shot"); p.add_argument("session"); p.add_argument("name"); p.add_argument("--full-page", action="store_true")
    p = sub.add_parser("hold"); p.add_argument("session"); p.add_argument("--cpu", type=float, default=1)
    p = sub.add_parser("release"); p.add_argument("session")
    p = sub.add_parser("tap"); p.add_argument("session"); p.add_argument("target")
    p.add_argument("--until"); p.add_argument("--timeout", type=int, default=3000)
    p = sub.add_parser("steps"); p.add_argument("session"); p.add_argument("src")
    p = sub.add_parser("close"); p.add_argument("session")
    a = ap.parse_args()
    globals()[f"cmd_{a.cmd}"](a)


if __name__ == "__main__":
    main()
