# Pitfalls from past sessions

Agents testing about a dozen of the user's web, PWA, desktop and Android apps hit the failures
below repeatedly. Each entry gives the symptom, the usual cause, and what fixed it. Read the
categories that match your problem; the rules in [../SKILL.md](../SKILL.md) come from them.

## 1. Flakes that appear only under load

- **Symptom:** a test passes on an idle four-core machine and fails on two cores, a busy laptop or
  a loaded CI runner. Typical rates were 1 in 3 to 8 in 10.
- **Causes found:** the app kept working after its visible "done" cue (a camera pan starting
  about 110 ms after a panel appeared); a server blocked its event loop with CPU-heavy work; the
  default 5 s timeout was shorter than the real work under load (8 to 15 s); each fresh test
  worker's first page load took 4 to 9 s, and each failure restarted the worker cold.
- **Fixes:** a settled signal from the app; moving CPU work off the event loop; a per-worker
  warm-up; waits bounded by the app's own limits. About half the root-caused flakes were app
  bugs.

## 2. Sleeps instead of readiness

- **Symptom:** `waitForTimeout(4000)`, `sleep 15` between adb steps, screenshots of a half-loaded
  list, suites padded with waits.
- **Cause:** the app exposed no drawn, framed, connected or busy state to wait on.
- **Fix:** app-set attributes (`data-settled`, `aria-busy`, `data-drawn`) and waits on them.

## 3. Waiting on the wrong thing

- **Symptoms:** asserting a request count before the request was sent; reading pixels two
  animation frames after an action, before the repaint; dismissing a transient "Undoing…" notice
  that the write then raised again.
- **Cause:** the wait condition was already true before the action, or it described a transient
  state rather than the final one.
- **Fixes:** `expect.poll` on the count; waiting for the busy indicator to clear; waiting for the
  notice's final state.

## 4. Layout moving under a tap

- **Symptoms:** a tap opened the wrong item; a pen stroke painted three of five cells; the first
  tap in a bottom sheet did nothing.
- **Causes:** a loading list pushed a button 42 px down between measuring and tapping; a
  "Working…" label widened a grid column and moved the board; the soft keyboard moved a form 56
  to 80 px; a sheet was measured mid-slide, so rows were hundreds of pixels off.
- **Fixes:** a settled signal; reserving space for late content; re-measuring once a sheet
  settles; checking `elementFromPoint` before every coordinate tap.

## 5. Animation

- **Symptoms:** `uiautomator dump` failing with "could not get idle state"; a screenshot taken
  mid-animation contradicting the state it claimed; a still screenshot "passing" a spinner that
  didn't spin.
- **Causes:** indicators that animate forever at idle; screenshots used as proof of motion.
- **Fixes:** stop hidden or idle animations; reduced motion in tests; sample the computed
  `transform` over time to prove motion.

## 6. Brittle selectors

- **Symptoms:** a role-name lookup for "Send message" matched an error toast containing those
  words; a strict-mode violation on two matching elements; "Unknown ref" after a reload; a text
  lookup hit a label covered by a styled input and was "fixed" with `force: true` and sleeps.
- **Fixes:** `exact: true` names, test ids, container-scoped locators, and a fresh snapshot after
  every reload or re-render.

## 7. Tests that pass by accident

- **Symptoms:** a test passed because `boundingBox()` returned null; a colour check never matched
  and so never failed; a name filter selected zero tests and the run counted as green; an absence
  check had no positive control; a stability check was quietly swapped for a weaker one; a test
  expectation was rewritten to match observed behaviour.
- **Fixes:** assert preconditions; prove each test fails without the fix; fail on an empty
  selection; never weaken an assertion to get a green run.

## 8. Non-deterministic inputs

- **Symptoms:** two siblings swapping places between runs; audio output differing by one float
  ULP; fake queue entries in a test copy; fixtures that never displayed the feature under test.
- **Causes:** random UUIDv7 ids sorted naturally; summation order depending on scheduling; a test
  home directory missing the real configuration; unrealistic seed data.
- **Fixes:** fixed ids and seeds (one journey went from 4/30 failures to 0/30); explicit
  ordering; copying real configuration with outbound effects cut; checking that the data shows
  the change.

## 9. Environment mistaken for results

- **Symptoms:** sandbox denials (`listen EPERM`, browser launch failures, no GPU) counted as test
  failures, once hiding a real assertion failure among 13 environment errors; a missing browser
  binary; `EADDRINUSE` on the user's own app port; a stale build or `tsbuildinfo`; a dev server
  hot-reloading a file edited mid-run; every Firefox test "failing" in 1 ms from a profile bug;
  the runner deleting its own output folder, and the evidence with it; debug builds inflating
  timings.
- **Fixes:** run browser tests outside the sandbox; use your own ports; check the build is fresh;
  smoke-launch each browser before timing runs; copy evidence out of the runner's output folder;
  time only production builds.

## 10. Emulation that isn't the device

- **Symptoms:** a headless "desktop" run showed the touch layout because headless Chrome reports
  no hover and no fine pointer; a tool's device preset set only the viewport and pixel ratio, so
  phone walks used a mouse; CDP emulation reset when its client detached; a blank WebGL canvas
  appeared only under emulation.
- **Fix:** check `matchMedia`, `maxTouchPoints` and `devicePixelRatio` in the page before judging.

## 11. Bugs only a real device shows

Found on real phones and tablets after emulated runs passed: the keyboard app sending a word
twice; a landscape viewport of 798×282 with the address bar at the bottom; 1 px borders drawn
thinner; page zoom-out at 360 px wide; a tablet browser reporting a finger lift at (0, 0); a
blurry canvas at fractional pixel ratios; native scroll anchoring; notifications arriving without
data while the app was closed; long-press menus and tap highlights.

## 12. Device chores

The user spent about fifty turns unlocking, rotating, re-plugging and re-enabling debugging, and
once a test's input landed in the user's real app. Batch device checks into one session, keep the
device awake, pre-grant permissions, and guard every input with a focus check
(`iExalt:phone-debug`).

## 13. Claims the evidence didn't support

- **Symptoms:** the user found a misstyled row, missing glyphs ("tofu"), an oversized UI, sticky
  hover and a missing icon after agents reported the work verified; a screenshot from an earlier
  commit nearly got cited; image audits reported "clean" and the user disagreed.
- **Causes:** screenshots treated as proof of behaviour; images downscaled before judging; one
  platform checked and all claimed; a font "loading" taken to mean its glyphs rendered.
- **Fixes:** show the user visual output; check each claimed platform; test glyph coverage;
  sample motion; name the commit for every screenshot.

## 14. Process

- **Symptoms:** a PR merged after the same head passed on its third attempt; a CI watcher
  reported a pass for a newer commit; flakes filed as noise until they blocked other PRs; review
  loops of 20 rounds; QA passes lasting 7 to 14 hours.
- **Fixes:** a statistical bar for "fixed"; watching CI by exact head SHA; known flakes block
  merges that touch their journey; review loops that end on materiality.

## 15. Slow harnesses

- **Symptoms:** a suite at 118 to 123 s against a 120 s limit; test setup timing out on a busy
  machine; a renderer crash.
- **Causes:** `page.evaluate` returning a graph library's object, costing 17 s of serialisation
  per run; heavy imports in test setup.
- **Fixes:** return plain data or nothing from `evaluate`; profile before raising limits; remove
  slow imports and keep the limit (one setup went from 10 s to under 0.5 s).

## What reliably worked

1. The app announces its state, and tests wait on that.
2. Holding one response to force a race: synthetic CPU load reproduced one flake 0 times in 50,
   while holding the response reproduced it every time.
3. Before-and-after counts under the same forced conditions, sized to the failure rate.
4. Every regression test shown to fail first.
5. Checking what the browser emulates before judging layout or input.
6. Measuring motion by sampling, not by screenshot.
7. Fixing slow tests instead of raising limits, and relative performance assertions.
8. One batched, focus-guarded real-device session with a checklist.
