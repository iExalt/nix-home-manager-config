# Devices and hosts

Where the browser runs, how it reaches the app, and how to cover each form factor. Use the lowest
tier that can answer the question.

**The environment file.** This file describes the kinds of machine. The user's actual machines are
in `~/.config/frontend-dogfood/environment.md`: the browser host's ssh name and quirks, how to reach
the virtual tablet and where its guide is, and which devices tier 3 means. Read it before preparing
the environment. If it is missing, ask the user once for those facts and offer to save them there.
Keep them out of this skill, project repositories, commits, and reports meant for publishing. Below,
`<host>` is the browser host's ssh name.

| Tier | Host | Covers | Can't cover |
|---|---|---|---|
| 1 | agent-browser on the browser host | Desktop at any viewport, phone and tablet viewports with emulated touch, light/dark, reduced motion, CPU throttling, timing | Real soft keyboards, Gboard, real GPU timing, Safari |
| 2 | Virtual Android tablet | Real Android layout, real touch, a real Android soft keyboard | What the environment file lists; typically phone size, Chrome-only behaviour, Gboard, push |
| 3 | Ask first: the user's laptop, phone, and tablet | iOS Safari (iOS Simulator on the laptop), Gboard, real phone timing, laptop GPU benchmarks | |

Report anything no reachable tier covers as untested, with the reason.

## Tier 1: agent-browser on the browser host

`<host>` is a Linux machine the user lets agents use freely. Never run browsers on the laptop
(SKILL.md step 2 covers an unreachable host).

**Setup, once per host.** If mise is only on a login shell's PATH there (the environment file
says), wrap commands in `bash -lc` and call `mise exec -- agent-browser`; the commands below assume
so:

```sh
ssh <host> 'bash -lc "mise use -g npm:agent-browser@latest uv && mise exec -- agent-browser install"'
ssh <host> 'loginctl show-user "$USER" -p Linger --value'
```

Headed sessions also need Xvfb on the host (Ubuntu's `xvfb` package; installing it needs the
user's say-so). dogfood.py's liveness check reads the unified cgroup v2 tree, which current
distributions use; on a cgroup v1 host it would report every session as gone. uv runs
touch_probe.py on the host. Lingering decides whether the browser and the touch hold, which run
under the user's systemd manager, survive when the last login session on the host ends. With
`Linger=no` they still work while any other session keeps the manager up, but can stop mid-run
without warning. `dogfood.py init` exits if agent-browser, uv, or (unless `--headless`) Xvfb is
missing, and only warns when lingering is off; it doesn't check the cgroup version. Every later
call checks that the browser (not just its virtual display) and any touch hold are still running,
including after the browser's idle timeout, failing with exit 3 if not: re-run `init --open` or
`hold` rather than carrying on, because a restarted browser has default settings and no touch.
Turning lingering on (`loginctl enable-linger`) changes the user's machine, so ask them first.

The laptop gets the same `npm:agent-browser@latest` from this repo's `home.nix`, only so its
version and docs match. Compare `agent-browser --version` on both hosts and update the older one
if they differ. Testing needs real
scrollbars, and Chrome needs `--no-sandbox` where AppArmor blocks its user-namespace sandbox (stock
Ubuntu does), so keep this config at `~/.agent-browser/dogfood.json` on the host and export
`AGENT_BROWSER_CONFIG` to point at it:

```json
{ "args": "--no-sandbox", "hideScrollbars": false, "screenshotFormat": "png", "idleTimeout": "30m" }
```

Without ffmpeg on the host, `record` (video) is unavailable; use step screenshots instead.

**Fonts.** Linux Chrome lacks the Mac's system fonts, so `system-ui` and `-apple-system` stacks fall
back to faces with different metrics. Before judging type, legibility, or pixel alignment (probes
3 and 29), check with `eval` that `getComputedStyle` on body text and headings names the intended
face and `document.fonts.check()` confirms it loaded. If it didn't, either serve the app's fonts or
tag type findings "rendered on Linux, intended face missing".

**Drive the browser with [../scripts/dogfood.py](../scripts/dogfood.py).** It runs on the laptop
and sends each command to the host in one ssh call, quoting its arguments for you, so JavaScript and
selectors survive. Testers who wrote their own wrappers spent turns on shell quoting instead of
testing. Run it with `uv run <skill-dir>/scripts/dogfood.py`; `--help` lists every command. The
host needs agent-browser, `uv` and a system `python3`.

```sh
dogfood.py init <session> --host <host> --evidence <evidence-dir> --url-part <port-or-path> --open <url>
dogfood.py ab <session> set viewport 412 915 3.5      # any agent-browser command
dogfood.py ab <session> - <<'CMDS'                    # several, one per line, in one round trip
set media dark
reload
wait --load networkidle
snapshot -i
CMDS
dogfood.py eval <session> probe.js                    # a JavaScript file (or - for stdin)
dogfood.py shot <session> 03-phone-dark               # screenshot, copied back with a view copy
dogfood.py close <session>                            # browser, touch hold, and host files
```

`init` copies touch_probe.py to the host every time. With `--open` it also starts the browser
headed, on a private virtual display (Xvfb), inside a systemd scope capped at the agreed 7 vCPU and
16 GB. Headed matters: headless Chrome reports `(hover: hover)` and `(pointer: fine)` as false,
so an app that switches on them shows a desktop tester its touch layout. `init` prints
`mouse: true` when the page sees a real mouse. Pass `--headless` only if the host lacks Xvfb, and
report hover- and pointer-dependent behaviour untested. `init` first closes any browser and touch
hold left under that session name, so a re-run starts clean. The daemon and browser persist between calls; give every
parallel tester its own session name. The main agent usually runs `init` and hands the session to
the tester; the tester leaves it open for the main agent to close.

**Screenshots.** `shot` writes two files into the evidence directory: the device-pixel original,
and a copy in `view/` scaled to CSS pixels, which is what a person sees at that size. Read the
view copy. A 3.5x phone original is 1442x3203 and costs several times the context of its
412x915 view; testers that read originals filled their context with images, and every later step
got slower. Open an original only for pixel-level checks (probes 3 and 29) or when the view copy
leaves a question open. Cite the original as evidence. A `--full-page` shot of a long page comes
back as screen-high view tiles (`view/<name>-1.png`, `-2`, …), because one tall image would be
shrunk until its text is unreadable; prefer viewport shots while scrolling when the order of
screens matters.

**Useful agent-browser commands.** `snapshot -i` (interactive elements with `@e` refs), `click`,
`fill`, `type`, `press`, `drag`, `mouse move|down|up|wheel` (middle button supported), `scroll`,
`set viewport <w> <h> [scale]`, `set device "<name>"`, `set media dark|light [reduced-motion]`,
`get box`, `get url`, `console`, `errors`, `network requests`, `vitals`, `wait --load
networkidle`. Run `dogfood.py ab <session> <command> --help` for flags, and `dogfood.py ab
<session> skills get core` for the tool's own guide at the installed version.

**Phone and tablet sizes need touch, which agent-browser doesn't provide.** `set device` sets the
viewport and pixel ratio only: `navigator.maxTouchPoints` stays 0 and `(pointer: coarse)` is false,
so the app shows its desktop-pointer behaviour (hover states, fine-pointer layouts, mouse events).
[../scripts/touch_probe.py](../scripts/touch_probe.py) fills the gap over raw CDP, leaving the
session's colour scheme, viewport, and pixel ratio alone; dogfood.py drives it:

1. After setting the viewport, run `dogfood.py hold <session>` (add `--cpu 4` for a throttled
   run). It keeps touch emulation on until released and prints `touch: true` once
   `(pointer: coarse)` matches; don't judge anything at that size until it does. Reload the page if
   the app reads the pointer type only at start-up.
2. While it holds, keep using agent-browser for navigation, `snapshot`, `fill`, `type`, `press`,
   `scroll`, `select`, and `eval`, but **no mouse commands** (`click`, `dblclick`, `drag`,
   `check`, `uncheck`, `hover`, `mouse ...`, and `find` with a click, check, or hover action or
   none, since it defaults to click; dogfood.py refuses them during a hold): under touch
   emulation they hang on a mouse event or do nothing. Tap with `dogfood.py tap <session> @e12`
   (an @ref, a CSS selector, or `X,Y`); drag, pinch, and wheel with `dogfood.py steps <session>
   steps.json`.
   `tap` scrolls an @ref or selector into view first, then waits until the target has held still
   for 150 ms and nothing covers it, taps its centre, and reports what the touch actually landed
   on. It exits non-zero without tapping when the target keeps moving, stays covered, moved after
   its box was read, or would be outside the viewport, and exits non-zero after tapping when the
   touch landed outside the target. Treat either as a finding to check (a layout that moves under
   the finger, an overlay), not as a tool error. A CSS selector identifies the target exactly; an
   @ref is matched by its box (preferring a control over a same-size layer above it; use a CSS
   selector when a same-size control, such as a stretched link, covers the target), so a target
   that never stops moving can be refused. `X,Y` taps aren't checked. The wait sees only
   element boxes, so motion drawn inside a canvas is invisible to it, and a quiet 150 ms can't
   foresee motion that starts later; for tests, the app's own settled signal is the fix
   (`iExalt:frontend-testing`). The wait adds at least 150 ms per tap, which `--until` timings
   exclude because they start at the touch event.
   A tap fires the full sequence (`pointerdown:touch`, `touchstart`, `mousedown`, `click`).
3. Run `dogfood.py release <session>` before switching back to a desktop size.

touch_probe's docstring lists the steps (`tap`, `drag`, `pinch`, `wheel` with `ctrl` for trackpad
pinch, `wait`, `eval`, `screenshot`, `time_to_change`). Don't put `"touch"` or `"cpu"` in a steps
file while a hold runs: the steps run would clear the hold's emulation when it exits, so
`dogfood.py steps` drops them during a hold. Coordinates are viewport CSS pixels, as `get box`
reports them, so taps stay accurate after scrolling.

**Timing.** `dogfood.py tap <session> @e12 --until "<js predicate>"` prints the milliseconds from
the touch to the first animation frame where the predicate holds, so it includes rendering; it is
the tool for "should land in the same frame" checks. For mouse input, use a `time_to_change` step
with a `wheel` or `tap`, or time in the page with `eval`. Frame timing on the host's virtual display
(Xvfb) only approximates a real display, so report these numbers as emulated.

**Reaching the app.** Two routes; the project brief decides:

- *App on the laptop (default for a first pass).* Serve it on its own high port, then tunnel it
  with its own connection, so the PID you record really owns the forward (with ssh connection
  sharing, a plain `ssh -R` hands the forward to a shared master and exits, and killing it leaves
  the port open on the host):
  `ssh -o ControlMaster=no -o ControlPath=none -o ExitOnForwardFailure=yes -N -R <port>:127.0.0.1:<port> <host> &`.
  At teardown, kill that PID and confirm with `ssh <host> 'ss -ltn'` that the port is gone.
  Nothing leaves the laptop, but the tunnel adds latency, so treat load and write timings (probes
  14 and 15) as upper bounds.
- *App on the host.* Run it there from a worktree and a copy of the data. Timings are realistic,
  but private data leaves the laptop; delete the copy at teardown.

**Evidence.** `shot` copies each screenshot to the local evidence directory as it takes it. If
you capture anything else on the host, copy it there (`scp`) before you read or cite it. Cite only
local absolute paths.

## Tier 2: the virtual Android tablet

An Android virtual device on a shared machine. The environment file says how to reach it, what it
is (size, density, Android version), and where its guide is; read the guide before the first use
in a session. The commands below are adb commands run wherever the guide says.

It is shared with other sessions, which have installed apps and flipped settings in the middle of
someone else's run:

- Check the guide's lock files first. If another session holds one, agree turns with it over
  agent messaging instead of proceeding. Create your own lock while you drive, delete it when done,
  and leave the guest running.
- Before every tap, swipe, or key event, check that `adb shell dumpsys window | grep mCurrentFocus`
  names the browser you opened; if it doesn't, stop and find out why rather than sending input into
  someone else's app.
- Restore every setting you change (for example `show_ime_with_hard_keyboard`, rotation, `wm size`).

What it gives a web dogfood pass:

- **Browser:** check what is installed. A guest without Chrome may have only the system WebView
  and its test shell; open a URL there with `adb shell am start -a android.intent.action.VIEW -n
  org.chromium.webview_shell/.WebViewBrowserActivity -d <url>`, and report Chrome-only behaviour
  (address-bar collapse, `interactive-widget`, PWA install) as untested.
- **Input:** real single-finger touch via `adb shell input tap|swipe` and any gesture helper the
  guide provides (helpers kept in `/tmp` vanish on restart, so check it exists). Neither does
  multi-touch, so pinch stays in tier 1 or is reported untested. Soft keyboard via `adb shell
  settings put secure show_ime_with_hard_keyboard 1` (restore to 0). An AOSP keyboard has a
  suggestion strip but is not Gboard.
- **Evidence:** screenshots with `adb exec-out screencap -p`, element bounds with uiautomator dumps.
- **Phone size:** only by `wm size` and `wm density` under your lock, restored afterwards;
  otherwise report phone-on-Android as untested.
- **Reaching the app:** the guest is not on the laptop's or the browser host's loopback. Check a
  route before relying on it: the guest may have internet access, and `adb reverse tcp:<port>
  tcp:<port>` maps the guest's port to the same port where adb runs. If no route reaches the app,
  report this tier as unavailable rather than exposing the app publicly.

## Tier 3: ask first

The user's own laptop, phone, and tablet (the environment file names them) are for what tiers 1
and 2 can't answer, and only with the user's agreement. Gather everything that needs a device into
one request, say what each check is for and how long it takes, then use the `phone-debug` skill for
the phone or tablet. The iOS Simulator (`agent-browser -p ios`, needs Xcode and Appium) runs on the
laptop, so it is tier 3 as well.
