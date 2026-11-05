# iOS tablet (iPad)

The rules in SKILL.md apply to the iPad too, with the page under test in
place of the app; tell the user what's happening through the Android phone's
push notifications. Only wired (USB) iPad debugging has been proven. The
user has one free port, so iPad and phone runs take turns. Say when the
iPad run is done so they can swap the cable.

Start from the worked iPad driver named in
`~/.config/phone-debug/environment.md` rather than writing a new one.

**One-time setup on the iPad, done by the user:** trust this Mac
("Trust This Computer?" plus the passcode, again after every replug that
reports `device is not paired`). Then, under Settings → Apps → Safari →
Advanced, turn on both **Remote Automation** (for safaridriver) and **Web
Inspector** (for pymobiledevice3). They are separate switches.

**What you can't do from the Mac, so ask the user:**
- Auto-Lock, Do Not Disturb, brightness and rotation have no programmatic
  control. Before the run, ask the user to set Auto-Lock to Never and
  turn on Do Not Disturb, and note their original values so you can remind
  them to set them back at the end.
- For orientation checks, have the script wait (poll
  `screen.orientation.type`) and ask the user to rotate once, rather than
  asking for one rotation per check.

**Check the iPad is there and unlocked** (run from `~`):

```zsh
xcrun devicectl list devices    # name, UDID, "available (paired)"
xcrun devicectl device info lockState --device <UDID>
```

**Drive Safari with the built-in safaridriver** (W3C WebDriver over HTTP):

- Before you start it, check the port with
  `lsof -nP -iTCP:4723 -sTCP:LISTEN`; if something you didn't start holds
  it, pick another port. Then run `/usr/bin/safaridriver -p 4723` (or your
  chosen port).
- `POST /session` with
  `{"capabilities":{"alwaysMatch":{"platformName":"iOS","browserName":"Safari","safari:deviceType":"iPad"}}}`.
  The response's `safari:deviceName`, `safari:platformVersion` and
  `browserVersion` belong in your receipts.
- To open a page, `POST /url` with the dev server's tailnet URL.
- To evaluate JS, `POST /execute/async`.
- For input, `POST /actions` with a single `pointerType: "touch"` pointer,
  then `DELETE /actions`.
- For screenshots, `GET /screenshot` (base64 PNG of the viewport only).
- Always finish with `DELETE /session`, even on failure. Otherwise Safari
  stays under the automation overlay and the user can't use it.

safaridriver opens its own automation tab with separate storage, so the
user's tabs are safe. Still check the target before each tap with
`document.elementFromPoint(x, y).closest(<selector>)`, and wait for the
app's ready signal before you interact.

**Its limits:** touch only and single finger (no pinch). Pen input arrives
as touch. Typed text never lands, so drive input by tapping. The lift
point of a synthetic touch is reported at (0, 0). There's nothing like
`uiautomator` and no capture outside Safari's viewport. Anything that needs
real touch, the Apple Pencil or multi-touch has to be done by the user.

**Reading the user's own tab** (for example after they draw with the
Pencil): pymobiledevice3 attaches to Safari's Web Inspector without the
automation overlay.

```zsh
mise install pipx:pymobiledevice3@latest   # PyPI install: ask first if it isn't installed
pymobiledevice3 usbmux list
pymobiledevice3 webinspector opened-tabs
```

For scripted reads, run the script under pymobiledevice3's own Python
(`"$(mise where pipx:pymobiledevice3)/pymobiledevice3/bin/python"`). Use
`WebinspectorService(...).get_open_application_pages()` and then
`runtime_evaluate(expr, return_by_value=True)`, and select exactly one tab
by URL. Only read from it; never navigate or evaluate side effects in the
user's tab.

**Failures seen:**
- `device is locked` (500): the iPad locked during the session. Ask the
  user to unlock it.
- `devices were found, but could not be used`: the iPad is unplugged or
  locked.
- A 408 timeout on `/execute/async`: transient, so rerun.

**Before relying on the iPad,** cover what you can with WebKit in
Playwright at the iPad's measured viewports (820×1106 and 1180×746 at
DPR 2), and save the device for what emulation can't show.
