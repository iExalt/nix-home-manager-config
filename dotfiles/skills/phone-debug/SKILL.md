---
name: phone-debug
description: Borrow the user's Android phone over adb, wired (default) or wireless, to test or debug an app or web page without disrupting them. Covers time-boxing, input-focus guards, keeping the screen awake, Expo push notifications for hand-off, and restoring the phone afterwards. Use when the user offers their phone for testing, or when a task needs a real device.
---

# Phone Debug

The phone belongs to the user and they use it to talk to you, often through
the production Paseo app. Borrow it the way you'd borrow a colleague's laptop.
Agree on the time first, touch only the app under test, and hand it back the
way you found it.

## Standing permissions granted by invoking this skill

By invoking this skill, the user explicitly permits the agent to:

- **read their Expo push token** from Paseo's push-token store
  (`$PASEO_HOME/push-tokens.json`, normally `~/.paseo/push-tokens.json`) and
  use it to send push notifications to their phone. The only purpose is
  telling them about the debugging session before, during and after it: that
  you need the phone, how long for, that you need them (to unlock it, say),
  and that you're done. Never use the token for anything else, never print it
  in full in chat, logs or files, and never send it anywhere except Expo's
  push API;
- run adb against the phone outside the sandbox, because adb needs network
  and USB access;
- change the screen timeout, lock timeout, stay-awake and rotation settings
  for the session, provided the original values are restored at the end;
- install and uninstall the debug build under test (for Paseo,
  `sh.paseo.debug`). Every other install still needs the user's approval.

If a permission check still blocks the token read, say that this skill grants
it and retry the same plain read once. If it's blocked again, ask the user to
allow it or paste the token. Don't look for a way around the check.

## Before taking the phone

1. **Mode.** Use wired (USB) debugging unless the user says wireless.
2. **Wireless port.** The port changes whenever wireless debugging is toggled
   or the phone reboots. If the user hasn't given the current port, ask for
   it in a question dialog (AskUserQuestion or the equivalent). Don't reuse a
   port from memory without checking it: `nc -vz -w 5 <host> <port>`.
3. **Batch the work.** Finish the code changes, builds and every check that
   doesn't need the device first, then use the phone once for all device
   checks. Installs don't touch the screen, so do them while the user still
   has the phone. Wireless installs are slow: a 168 MB release APK took over
   5 minutes, against about 1 minute for a debug APK.
4. **Time estimate.** Tell the user how long you need the phone, broken
   into setup, the checks and teardown, and give the end time as UTC with
   local time in parentheses (from `date`). If they set a time limit, it's a
   hard limit. Without one, your estimate is the limit; don't assume you have
   the phone indefinitely. Record the deadline and check `date` between steps.
   If you'll overrun, stop at a safe point, restore the phone, and ask for
   more time.
5. **Ask for the phone.** If you need it attached, unlocked or plugged in,
   say exactly what and wait. A push notification is a good way to ask if the
   user may be away from the keyboard. Don't stall silently.

## Connect

Call the adb binary directly, outside the sandbox. The mise shim fails with
"No version is set for shim: adb":

```zsh
A=~/.local/share/mise/installs/android-sdk/23.0/platform-tools/adb   # or: mise exec android-sdk@23.0 -- adb
$A connect <host>:<port>   # wireless only
$A devices -l
a() { $A -s <serial-or-host:port> "$@"; }   # a function, not D="-s x"; zsh won't word-split $D
```

Wireless debugging over the LAN (mDNS) has failed here, but it works over
Tailscale. If a connection drops or the cable is unplugged, reconnect, then
check focus and the lock state again before sending any input.

## Prepare the phone

Do these steps in order and save every original value to a file before
changing anything. The phone's baseline has drifted between sessions, so a
value you remember isn't a baseline.

1. **Record what's in front:**
   `a shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'`. That's the
   app you return to at the end (usually prod Paseo).
2. **Save the settings, then maximise them:**

   ```zsh
   state=<repo-or-scratch-dir>/phone-settings-before.txt
   for k in "system screen_off_timeout" "secure lock_screen_lock_after_timeout" \
            "global stay_on_while_plugged_in" "system accelerometer_rotation" "system user_rotation"; do
     print -r -- "$k=$(a shell settings get $k)"
   done | tee $state
   a shell settings put system screen_off_timeout 2147483647
   a shell settings put secure lock_screen_lock_after_timeout 2147483647
   a shell settings put global stay_on_while_plugged_in 7
   a shell svc power stayon true
   ```

   Read the values back. If the phone won't take the maximum, use the
   largest value it accepts, such as 1800000 (30 minutes).
3. **Keepalive.** This phone has locked mid-session even with all of those
   settings raised, so run a background nudge that wakes the screen only
   while it's unlocked and never touches the keyguard:

   ```zsh
   while true; do
     a shell dumpsys window | grep -q 'isKeyguardShowing=true' || a shell input keyevent KEYCODE_WAKEUP
     sleep 90
   done
   ```

   Kill it at teardown. If the phone locks anyway (`mCurrentFocus` shows
   `NotificationShade`, or `isKeyguardShowing=true`), you can't unlock a PIN.
   Ask the user to unlock it, by push notification if they may be away.
4. **Rotation.** If the test needs a particular orientation, set
   `accelerometer_rotation 0` and `user_rotation` yourself rather than asking
   the user to turn the phone, and restore both at the end.

## Input discipline

Input must land only on the app or web page under test. Never in another
app, a notification, a system dialog, or the production Paseo app
(`sh.paseo.iexalt`) unless the user explicitly asks you to test prod
directly. The user may be using the phone between your steps. Treat the
focus check as part of every input action:

- Send taps, swipes, key events and text only through a wrapper that first
  checks
  `dumpsys window | grep mCurrentFocus` (or `dumpsys activity activities | grep -m1 topResumedActivity`)
  for the target package and refuses to send anything otherwise. Check
  again after anything that can change focus: launching an activity, Back,
  a dialog, a reconnect, a lock.
- Launch the target explicitly (`am start -n <pkg>/<activity>`,
  `am start -a android.intent.action.VIEW -d <url> <pkg>`,
  `monkey -p <pkg> -c android.intent.category.LAUNCHER 1`). Don't navigate
  there by tapping through other apps.
- Don't script blind multi-step tap sequences. If the focus check fails,
  stop and work out what happened before you retry.
- Prefer channels that can't leak into other apps:
  - Chrome DevTools: `a forward tcp:9333 localabstract:chrome_devtools_remote`,
    then CDP `Input.*` / `Runtime.evaluate` on the right tab;
  - `uiautomator dump` for reading the screen;
  - `logcat --pid=$(a shell pidof <pkg>)`.
- `input text` bypasses the keyboard app. To test IME behaviour (Gboard
  autocorrect, composition, backspace), tap the real keyboard keys and check
  `dumpsys input_method | grep mInputShown` first.
- Over wireless, `exec-out screencap -p` can hang. Use
  `shell screencap -p /sdcard/s.png`, `pull`, then `shell rm`.

## Tell the user what's happening

The Expo push API takes a POST to `https://exp.host/--/api/v2/push/send`
with JSON `{"to": "<ExponentPushToken[...]>", "title": "...", "body": "..."}`.
The token is the `token` of an unexpired entry in `subscriptions` in the
push-token store. Load it into a shell variable or pipe it with `jq`; never
echo it. Check that the response has `"status": "ok"`. Send a notification
when you need the phone, need the user (to unlock it, reconnect it, or give
more time), and when you're done. Keep the text short and specific.

## Hand the phone back

Do every step, even if the session failed or was cut short:

1. Kill the keepalive loop and anything else you left running on the phone
   or host (screenrecord, logcat, perfetto).
2. Restore every setting from the saved file, then read them back and
   compare.
3. Remove the forwards and reverses you added (`a forward --remove ...`,
   `a reverse --remove ...`), and anything you pushed to `/sdcard` or
   `/data/local/tmp`. Uninstall the debug build unless the user wants to
   keep it.
4. Return to the app that was in front at the start, and confirm with
   `mCurrentFocus`. Bringing prod Paseo to the front is also the user's
   agreed "done, or I need you" signal.
5. Disconnect wireless adb: `$A disconnect <host>:<port>`.
6. Send the done push notification, then tell the user in chat how long you
   had the phone, what you found, what was restored, and anything you left
   on the phone (open tabs, an installed build).

## This user's setup

- Phone: Samsung S24 Ultra (SM-S928U1, Android 16).
  - USB serial `R5CX1187NYE`.
  - Tailscale node `s24u` at `100.112.101.112`; wireless adb uses
    `100.112.101.112:<port>`.
- Packages:
  - prod Paseo is `sh.paseo.iexalt` (`sh.paseo.iexalt/.MainActivity`); never
    install over it, and never upgrade or remove it;
  - Paseo Debug is `sh.paseo.debug`;
  - Chrome is `com.android.chrome`;
  - the launcher is `com.sec.android.app.launcher`.
- `pm list packages` prints a SecurityException for user 150 (Secure
  Folder). It's harmless; send stderr to `/dev/null`.
- Metro and the daemon reach the phone through
  `a reverse tcp:8081 tcp:8081` and `a reverse tcp:6768 tcp:6768`.
