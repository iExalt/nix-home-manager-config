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
import shlex
import subprocess
import sys
import time

STATE = pathlib.Path("/tmp/frontend-dogfood")
PROBE = pathlib.Path(__file__).with_name("touch_probe.py")
EOF_MARK = "DOGFOOD_EOF_7f3c"


def load(session):
    path = STATE / f"{session}.json"
    if not path.exists():
        sys.exit(f"no session {session!r}: run `dogfood.py init {session} --host ... --evidence ...` first")
    return json.loads(path.read_text())


def remote(cfg, body, check=True):
    """Run a bash script on the host with agent-browser as `ab`; return stdout."""
    script = "\n".join([
        'eval "$(mise env -s bash)"',
        f"export AGENT_BROWSER_CONFIG={cfg['config']}",
        f"ab() {{ agent-browser --session {shlex.quote(cfg['session'])} \"$@\"; }}",
        f"D=/tmp/dogfood-{cfg['session']}; mkdir -p \"$D\"",
        body,
    ])
    res = subprocess.run(["ssh", "-T", "-o", "BatchMode=yes", cfg["host"], "bash -lc " + shlex.quote(script)],
                         check=False, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300)
    err = "\n".join(l for l in res.stderr.splitlines() if "Pseudo-terminal" not in l)
    if err:
        print(err, file=sys.stderr)
    if check and res.returncode:
        sys.exit(res.returncode)
    return res.stdout


def heredoc(path, text):
    return f"cat > {path} <<'{EOF_MARK}'\n{text}\n{EOF_MARK}"


def read_src(src):
    return sys.stdin.read() if src == "-" else pathlib.Path(src).read_text()


def probe_args(cfg):
    return '"$WS" "$D/steps.json"' + (f" --url {shlex.quote(cfg['url_part'])}" if cfg["url_part"] else "")


def cmd_init(a):
    cfg = {"session": a.session, "host": a.host, "evidence": str(pathlib.Path(a.evidence).resolve()),
           "url_part": a.url_part, "config": a.config}
    STATE.mkdir(exist_ok=True)
    (STATE / f"{a.session}.json").write_text(json.dumps(cfg, indent=1))
    (pathlib.Path(cfg["evidence"]) / "view").mkdir(parents=True, exist_ok=True)
    remote(cfg, "true")
    subprocess.run(["scp", "-q", str(PROBE), f"{a.host}:/tmp/dogfood-{a.session}/touch_probe.py"], check=True)
    if a.open:
        unit = f"dogfood-{a.session}-{int(time.time())}"
        print(remote(cfg, f"systemd-run --user --scope -q --unit={unit} -p CPUQuota={a.cpu_quota} "
                          f"-p MemoryMax={a.memory_max} agent-browser --session {shlex.quote(a.session)} "
                          f"open {shlex.quote(a.open)}"), end="")
    print(f"session {a.session} on {a.host}; evidence in {cfg['evidence']}")


def cmd_ab(a):
    cfg = load(a.session)
    if a.args == ["-"]:
        lines = [l.strip() for l in sys.stdin if l.strip() and not l.lstrip().startswith("#")]
        body = "\n".join(f"printf '%s\\n' {shlex.quote('$ ' + l)}; ab {shlex.join(shlex.split(l))} || echo \"[exit $?]\""
                         for l in lines)
    else:
        body = f"ab {shlex.join(a.args)}"
    print(remote(cfg, body), end="")


def cmd_eval(a):
    cfg = load(a.session)
    print(remote(cfg, heredoc('"$D/eval.js"', read_src(a.src)) + '\nab eval --stdin < "$D/eval.js"'), end="")


def cmd_shot(a):
    from PIL import Image
    cfg = load(a.session)
    name = a.name.removesuffix(".png")
    out = remote(cfg, f"ab screenshot {'--full ' if a.full_page else ''}\"$D/{name}.png\" >/dev/null && ab eval devicePixelRatio")
    dpr = float(out.strip().splitlines()[-1])
    full = pathlib.Path(cfg["evidence"]) / f"{name}.png"
    full.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["scp", "-q", f"{cfg['host']}:/tmp/dogfood-{cfg['session']}/{name}.png", str(full)], check=True)
    view = full.parent / "view" / full.name
    view.parent.mkdir(exist_ok=True)
    with Image.open(full) as img:
        size = (round(img.width / dpr), round(img.height / dpr))
        (img.resize(size, Image.LANCZOS) if dpr > 1 else img).save(view)
    print(f"view {view}  ({size[0]}x{size[1]}, CSS pixels; read this one)\nfull {full}  (device pixels, {dpr:g}x; for pixel checks and evidence)")


def cmd_hold(a):
    cfg = load(a.session)
    unit = f"dogfood-{a.session}-touch"
    url = f" --url {shlex.quote(cfg['url_part'])}" if cfg["url_part"] else ""
    cpu = f" --cpu {a.cpu:g}" if a.cpu != 1 else ""
    print(remote(cfg, f"""systemctl --user stop {unit} 2>/dev/null
WS=$(ab get cdp-url)
systemd-run --user -q --collect --unit={unit} "$(command -v uv)" run -q "$D/touch_probe.py" "$WS" hold{url}{cpu}
sleep 2
systemctl --user is-active {unit} >/dev/null || {{ journalctl --user -u {unit} -n 20 --no-pager; exit 1; }}
printf 'touch: '; ab eval "matchMedia('(pointer: coarse)').matches && navigator.maxTouchPoints > 0"
echo "reload the page if the app reads the pointer type only at start-up" """), end="")


def cmd_release(a):
    cfg = load(a.session)
    remote(cfg, f"systemctl --user stop dogfood-{a.session}-touch 2>/dev/null; true")
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
    print(run_steps(load(a.session), json.loads(read_src(a.src))), end="")


def cmd_close(a):
    cfg = load(a.session)
    print(remote(cfg, f"systemctl --user stop dogfood-{a.session}-touch 2>/dev/null; ab close; rm -rf \"$D\"", check=False), end="")
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
