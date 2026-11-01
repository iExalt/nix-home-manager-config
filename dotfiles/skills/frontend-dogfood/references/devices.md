# Devices and hosts

Where the browser runs, how it reaches the app, and how to cover each form factor. Use the lowest
tier that can answer the question. Tier 3 needs the user's agreement, and the user has asked for
it only when absolutely necessary.

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

`<host>` is a Linux machine the user lets agents use freely. Never run browsers on the laptop. If
the host is unreachable, ask the user once instead of falling back.

**Setup, once per host.** If mise is only on a login shell's PATH there (the environment file
says), wrap commands in `bash -lc` and call `mise exec -- agent-browser`; the commands below assume
so:

```sh
ssh <host> 'bash -lc "mise use -g npm:agent-browser@latest && mise exec -- agent-browser install"'
```

The laptop gets the same `npm:agent-browser@latest` from this repo's `home.nix`; agent-browser is
installed there only so its version and docs match, never to run a browser. Compare
`agent-browser --version` on both hosts and update the older one if they differ. Testing needs real
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

**Sessions.** The daemon and its browser persist between `ssh` calls. Start each session inside a
systemd scope so it stays under the agreed cap of 7 vCPU and 16 GB, and give every parallel tester
its own session and unit name:

```sh
ssh <host> 'bash -lc "export AGENT_BROWSER_CONFIG=~/.agent-browser/dogfood.json
  systemd-run --user --scope -q --unit=dogfood-<session>-<unix-time> -p CPUQuota=700% -p MemoryMax=16G \
    mise exec -- agent-browser --session <session> open <url>"'
```

Later commands only need `AGENT_BROWSER_CONFIG` and `--session <session>`. `agent-browser
--session <session> close` stops the browser and the scope with it. Unit names can't be reused
while a unit is still loaded, hence the timestamp.

**Useful commands.** `snapshot -i` (interactive elements with `@e` refs), `click`, `fill`, `type`,
`press`, `drag`, `mouse move|down|up|wheel` (middle button supported), `scroll`, `screenshot
[--annotate] <path>`, `set viewport <w> <h> [scale]`, `set device "<name>"`, `set media
dark|light [reduced-motion]`, `get cdp-url`, `eval <js>`, `console`, `errors`, `network
requests`, `vitals`, `wait --load networkidle`. Run `mise exec -- agent-browser <command> --help`
for flags, and `agent-browser skills get core` for the tool's own usage guide at the installed
version.

**Phone and tablet sizes need touch, which agent-browser doesn't provide.** `set device` sets the
viewport and pixel ratio only: `navigator.maxTouchPoints` stays 0 and `(pointer: coarse)` is false,
so the app shows its desktop-pointer behaviour (hover states, fine-pointer layouts, mouse events).
Chrome also drops CDP emulation when the client that set it disconnects.
[../scripts/touch_probe.py](../scripts/touch_probe.py) fills the gap. Copy it to the host once:
`scp <skill-dir>/scripts/touch_probe.py <host>:/tmp/dogfood-<session>-touch_probe.py`. It
speaks raw CDP and sends only touch, throttling, input, evaluation, and screenshot commands, so the
session's colour scheme, viewport, and pixel ratio survive it.

1. After `set device` (or `set viewport` with a scale), start `hold` as a transient service. It
   keeps touch emulation on (and a CPU rate, if given) until stopped:

   ```sh
   ssh <host> 'bash -lc "export AGENT_BROWSER_CONFIG=~/.agent-browser/dogfood.json
     WS=\$(mise exec -- agent-browser --session <session> get cdp-url)
     systemd-run --user -q --collect --unit=<scope-unit>-touch \
       \$(mise which uv) run -q /tmp/dogfood-<session>-touch_probe.py \$WS hold --url <url-part>"'
   ```

2. Check it took: `eval "matchMedia('(pointer: coarse)').matches && navigator.maxTouchPoints > 0"`
   must be true before you judge anything at that size. Reload the page if the app reads the
   pointer type only at startup.
3. While it holds, keep using agent-browser for navigation, `snapshot`, `get box`, `fill`, `type`,
   `press`, `scroll`, `eval`, and `screenshot`, but **not `click` or `drag`**: under touch
   emulation they hang on a mouse event and never fire `click`. Do every tap, drag, and pinch with
   touch_probe steps instead, at coordinates from `get box <ref>`:

   ```sh
   ssh <host> 'bash -lc "WS=\$(... get cdp-url)
     mise exec -- uv run -q /tmp/dogfood-<session>-touch_probe.py \$WS - --url <url-part>"' < steps.json
   ```

   A tap fires the full sequence (`pointerdown:touch`, `touchstart`, `mousedown`, `click`).
4. Stop it with `systemctl --user stop <scope-unit>-touch` before switching back to a desktop size.

touch_probe's docstring lists the steps (`tap`, `drag`, `pinch`, `wheel` with `ctrl` for trackpad
pinch, `wait`, `eval`, `screenshot`, `time_to_change`). For a throttled run, pass `--cpu 4` to
`hold`. Don't put `"touch"` or `"cpu"` in a steps file while a hold runs: the steps run would clear
the hold's emulation when it exits (checked: touch went from 5 points to 0). `get box` returns
viewport coordinates, so taps stay accurate after scrolling. `--url` picks the tab when several are
open. `time_to_change` starts the clock at the input event's own timestamp and stops
on the first animation frame where a page predicate holds, so it includes rendering; it is the tool
for "should land in the same frame" checks. Headless frame timing approximates a real display, so
report these numbers as emulated.

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

**Evidence.** Screenshots land on the host. Write them under `/tmp/dogfood-<session>/` (session
names keep parallel testers from colliding), then copy them to the local evidence directory (`scp`
or `rsync`) before you read or cite them. Cite only local paths.

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
