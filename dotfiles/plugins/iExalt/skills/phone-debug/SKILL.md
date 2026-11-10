---
name: phone-debug
description: "Borrow the user's Android phone over adb, or their iPad over USB, to test or debug an app or web page without disrupting them: time-boxed, input-guarded and kept awake, with Expo push hand-offs and the device restored afterwards. Use when the user offers a phone or tablet for testing, or a task needs a real device."
---

# Phone Debug

The phone belongs to the user and they use it to talk to you, often through
the production Paseo app. Borrow it the way you'd borrow a colleague's laptop.
Agree on the time first, touch only the app under test, and hand it back the
way you found it.

## Standing permissions granted by invoking this skill

By invoking this skill, the user explicitly permits you to:

- **use their Expo push token**, through `scripts/push` only, to tell them
  about the debugging session before, during and after it: that you need
  the phone, how long for, that you need them (to unlock it, say), and that
  you're done. Never use the token for anything else;
- change the screen timeout, lock timeout, stay-awake, rotation and Do Not
  Disturb settings for the session, provided the original values are
  restored at the end;
- install and uninstall the debug build under test (for Paseo,
  `sh.paseo.debug`). Every other install still needs the user's approval.

Send pushes only through the bundled `scripts/push`, by its absolute path
under the skill directory (for example
`~/.claude/skills/iExalt/skills/phone-debug/scripts/push` or
`~/.codex/plugins/cache/iexalt/iExalt/1.0.0/skills/phone-debug/scripts/push`). The user's Claude and Codex
configs allow that exact command. It reads the token itself and never prints
it, so the token never enters your context. Don't read the token store
directly.

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
   5 minutes, against about 1 minute for a debug APK. Prove delivery works
   before changing any phone setting. If a wireless transfer stalls, cap the
   attempt and switch to the user's agreed fallback: serve the APK from the
   laptop over their private network for the phone to download, or use USB.
   Don't keep retrying while the phone sits in a modified state.
4. **Time estimate.** Tell the user how long you need the phone, broken
   into setup, the checks and teardown, and give the end time. If they set
   a time limit, it's a hard limit. Without one, plan for a stint of about
   10 minutes, and your estimate is the limit. If the work needs more than
   10 minutes, split it into several stints. Record the deadline and check
   `date` between steps. If you'll overrun, stop at a safe point, restore
   the phone, and ask for more time.
5. **Ask once for a device window.** Device go-aheads are among the user's
   most frequent and least consequential questions, so ask in one question
   for every stint the thread will need: how many, how long each, and the
   latest end time. Include the baseline install and anything else that
   needs the device. Inside a granted window, don't ask again. Send a push
   saying the stint is starting and how long it takes, then begin once the
   device is attached and unlocked and the focus check shows only the app
   under test or the home screen. If it isn't, push once saying what you need
   (attach, unlock, put the app away), wait a few minutes, then skip that stint
   rather than asking again. A new stint outside the window, or a change to
   what the window covers, needs a new ask.
6. **Ask for the phone.** Outside a window, if you need it attached, unlocked
   or plugged in, say exactly what and wait. If the user may be away from the
   keyboard, a push notification is a good way to ask. Don't stall silently.

## Connect

Read `~/.config/phone-debug/environment.md` first (see "This user's setup").

Call the adb binary directly, outside the sandbox. The mise shim fails with
"No version is set for shim: adb":

```zsh
A=~/.local/share/mise/installs/android-sdk/23.0/platform-tools/adb   # or: mise exec android-sdk@23.0 -- adb
$A connect <host>:<port>   # wireless only
$A devices -l
a() { $A -s <serial-or-host:port> "$@"; }
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
            "global stay_on_while_plugged_in" "system accelerometer_rotation" "system user_rotation" \
            "global zen_mode"; do
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
   deadline=$(( $(date +%s) + <stint seconds> ))
   ( while (( $(date +%s) < deadline )); do
       w=$(a shell dumpsys window) || break   # unreadable lock state: stop, don't wake
       [[ $w == *isKeyguardShowing=* && $w != *isKeyguardShowing=true* ]] &&
         a shell input keyevent KEYCODE_WAKEUP
       sleep 90
     done ) &
   print $! > <repo-or-scratch-dir>/keepalive.pid
   ```

   Set the deadline to the stint's end minus its teardown time; the loop
   stops by itself there. Kill it by its recorded PID at teardown, or as
   soon as the stint fails. If the phone locks anyway (`mCurrentFocus` shows
   `NotificationShade`, or `isKeyguardShowing=true`), you can't unlock a PIN.
   Ask the user to unlock it, by push notification if they may be away.
4. **Do Not Disturb.** Turn on priority-only DND with
   `a shell cmd notification set_dnd priority`, then read back
   `a shell settings get global zen_mode` and check for `1`. Change DND
   through the notification service: direct writes to `global zen_mode`
   can be overwritten by the service, even when `settings put` succeeds.
   Send your own pushes before you enable DND or
   after you restore it, because DND may suppress them.
5. **Rotation.** If the test needs a particular orientation, set
   `accelerometer_rotation 0` and `user_rotation` yourself rather than asking
   the user to turn the phone, and restore both at the end.
6. **Debug-app data.** After installing the debug build and before this
   session's first launch, run `a shell pm clear <debug package>`: Android may
   have restored a backed-up production host into it. Skip this only if the
   user asked to keep its data. Clearing also resets runtime permissions, so
   re-grant any the test needs. Before pairing, check the app shows no saved hosts, and
   never edit production token stores.

## Input discipline

Input must land only on the app or web page under test, never on another
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
    then CDP `Input.*` / `Runtime.evaluate` on the right tab. Never attach
    Playwright or another framework that scripts every tab (it injects into
    the user's own open pages); list targets over raw CDP and open a tab of
    your own to drive;
  - `uiautomator dump` for reading the screen;
  - `logcat --pid=$(a shell pidof <pkg>)`.
- `input text` bypasses the keyboard app. To test IME behaviour (Gboard
  autocorrect, composition, backspace), tap the real keyboard keys and check
  `dumpsys input_method | grep mInputShown` first.
- Over wireless, `exec-out screencap -p` can hang. Use
  `shell screencap -p /sdcard/s.png`, `pull`, then `shell rm`.
- `input tap` sends down and up with no hold. For a press that needs one,
  use `input swipe X Y X Y 120`.
- `uiautomator dump` fails with `could not get idle state` while the app is
  animating (lists loading, an agent running). Wait and retry; fall back to
  a screenshot only for that read.

For Paseo, read `docs/agent-testing.md` on the fork's `dev` branch first: package names,
which deep links work cold and warm, and how to read the selected tab from a
dump. Open screens by deep link instead of tapping through the app.

Drive Paseo with `python3 scripts/android/agent-adb.py --package <pkg>` from a
fork checkout (`AGENT_ADB` names the adb command, e.g. with `-s <serial>`)
rather than writing one-off scripts. Its `tap`, `type` and `key` are the
focus-checked wrapper above; `dump` keeps ids and the selected/focused flags;
`wait-turn` waits for an agent's turn to finish without clearing logcat; and
every command that drives the app (`tap`, `type`, `key`, `open`, `switch`)
refuses `sh.paseo.iexalt` unless `--allow-user-app` is passed, which you do
only with the user's go-ahead.

## Tell the user what's happening

Run `<skill-dir>/scripts/push "<title>" "<body>"`; it exits non-zero
unless Expo accepts the push. Keep the text short and specific, for example
`push "Phone free" "Done after 8 min; restored settings, back on Paseo."`.

## Hand the phone back

Do every step, even if the session failed or was cut short:

1. Kill the keepalive loop by its recorded PID, and anything else you left
   running on the phone or host (screenrecord, logcat, perfetto).
2. Restore every setting from the saved file. Restore Do Not Disturb through
   `a shell cmd notification set_dnd <mode>`, using the saved `global zen_mode`
   value to choose the mode:

   | Saved `zen_mode` | `set_dnd` mode |
   | --- | --- |
   | `0` (off) | `all` |
   | `1` (priority only) | `priority` |
   | `2` (no interruptions) | `none` |
   | `3` (alarms only) | `alarms` |

   For example, a saved `0` needs `a shell cmd notification set_dnd all`.
   `none` enables total silence; it does not turn DND off. If the saved value
   is missing or unrecognized, report that restoration is unresolved instead
   of guessing. Read every restored setting back and compare it with the
   saved file, including `a shell settings get global zen_mode`. A successful
   command alone does not prove restoration. If any value differs, investigate
   within the remaining device window and report any unresolved mismatch;
   don't claim the phone was restored until all saved values match.
3. Remove the forwards and reverses you added (`a forward --remove ...`,
   `a reverse --remove ...`), and anything you pushed to `/sdcard` or
   `/data/local/tmp`. Uninstall the debug build unless the user wants to
   keep it.
4. Return to the app that was in front at the start, and confirm with
   `mCurrentFocus`. The closing push in step 6 is the "done" signal. When
   the starting app was prod Paseo, bringing it to the front is also the
   user's agreed "done, or I need you" signal.
5. Disconnect wireless adb: `$A disconnect <host>:<port>`.
6. Send the done push notification, then, before any unrelated work, tell
   the user in a visible chat reply how long you had the phone, what you
   found, what was restored, and anything you left on the phone (open tabs,
   an installed build), and repeat it in the turn's final message if you
   keep working. Do this even when the push succeeded. If the user asks
   whether you're done with the phone, answer the same way.

## iOS tablet (iPad)

When the device is the iPad, follow [references/ipad.md](references/ipad.md).

## This user's setup

The user's device identities (models, USB serial, Tailscale address, iPad
UDID) and the path to a worked iPad driver live in
`~/.config/phone-debug/environment.md`, outside this public repository. If
it's missing, ask the user once for those details and write the file.

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
