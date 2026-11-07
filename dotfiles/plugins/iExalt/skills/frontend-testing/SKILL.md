---
name: frontend-testing
description: "Write, fix and prove automated UI tests that don't flake: web end-to-end and Playwright tests, phone-viewport journeys, and native UI tests driven over adb. Use when writing or changing a UI test, when a UI test is flaky, slow, or passes locally but fails in CI or on fewer cores, when a tap or click lands on the wrong element or must hit a moving or canvas-drawn target, when tempted to add a sleep, raise a timeout or retry, and before claiming a UI fix or flake fix is verified."
---

# Frontend Testing

A UI test is deterministic when every step waits for a state the app announces and every
assertion names the outcome the user cares about. Flaky tests come from guessing: a sleep, a
quiet-window heuristic, a tap at a target that is still moving, a check that reads once. Past
sessions traced about half of their root-caused flakes to real app bugs that load merely
exposed, so treat a flake as a defect report, not noise.

[references/pitfalls.md](references/pitfalls.md) catalogs the failures behind these rules;
[references/patterns.md](references/patterns.md) has code for each technique.

## Use the project's test harness

Inspect the supported runner and shared fixtures/helpers before writing a probe. Run a selected case
through that entrypoint so its environment, data bootstrap and result reporting stay intact; confirm
the case ran and wrote its expected artifact before an expensive batch. A journey whose reporting
failed is incomplete. Keep isolated checkouts' writable dependencies private, installed from the
lockfile using the warm package store, rather than linked to another checkout's mutable tree.

## Make the app announce when it has settled

- Wait on a condition the app sets, never on time. Where a test needs to know an async
  transition finished (data drawn, camera framed, layout measured, write saved, animation
  done), expose it on the DOM: `aria-busy`, or a `data-` attribute such as `data-settled`,
  `data-framed` or `data-drawn`, set after the last visual change, not at the first visible cue.
  Add the attribute to the app when it's missing; that is part of the test work.
- Clear the signal synchronously in the input handler that starts the work, before any timer,
  `await` or fetch, so a test waiting right after the action can't see the old value. Tie it to
  the work that sets it (a generation counter, or `data-framed-for="<id>"`) so a stale callback
  can't mark newer work done.
- Wait for the final state, not a transient one. A "Saving…" notice, a spinner appearing, or a
  request being sent can all precede the change that matters.
- Wait only on conditions the action itself changes. A condition that was already true before
  the action passes immediately and proves nothing.
- A quiet-window wait (no movement for N ms) is a heuristic. Use one only when the app can't
  expose a signal, label it as a heuristic in the code, and record its margin.
- Put readiness waits in the shared interaction helper when journeys use it. A renderer can insert
  a hidden child before revealing it: wait for target visibility and the app-owned settled signal
  before centering or scrolling, then wait again after that action before reading coordinates and
  tapping. Existence alone cannot establish clickability. Reuse the app's actual readiness API.

## Write tests that can't pass by accident

- Find elements by role and accessible name (`getByRole('button', { name: 'Save', exact: true })`)
  or a test id, scoped to their container. Avoid text and CSS-structure selectors, positional
  `nth()`, and substring name matches, which can hit a toast or a covered label.
- Use retrying assertions (`expect(locator).toHaveText(...)`, `expect.poll(...)`). Never read a
  value once and compare it for anything async.
- Never use `force: true`, `dispatchEvent`, or coordinate clicks and taps to get past an
  actionability error; the error is the finding. When a coordinate tap is unavoidable (canvas,
  native views), first check that the target is stable and is what `elementFromPoint` or a fresh
  UI dump reports at that point. On a canvas that check sees only the canvas, so wait for the
  app's settled signal, then read the position from the app's API and tap at once. Polling
  positions until they match is only a quiet-window heuristic: it passes before a late move
  starts.
- Take a fresh snapshot or UI dump after every navigation, reload or re-render; element refs
  from an earlier snapshot go stale.
- Make the inputs deterministic: fixed ids and seeds wherever order or geometry depends on them,
  a mocked or held network, a controlled clock, and animations off (reduced motion or a test-only
  stylesheet). Check that the fixtures actually show the feature under test.
- Make each new test fail first: run it against the code before the fix, or break the fix, and
  watch it fail for the right reason. Assert its preconditions, so a null box, an empty list or a
  filter that selected zero tests fails instead of passing vacuously. Give an absence check a
  positive control in the same run.
- Compare geometry with sub-pixel tolerance (±0.5 px). Make performance assertions relative to a
  reference measured in the same run, not fixed milliseconds on a shared runner.
- Keep the harness cheap: `page.evaluate` returns plain data or nothing, never a library object;
  move heavy imports out of test setup instead of raising its timeout.

## When a test flakes

1. Classify the environment first. Sandbox denials (`EPERM` on a port, browser launch failures),
   a missing browser binary, a cold dev server, a stale build, or files edited mid-run are
   setup failures, not results. Fix the setup, then count.
2. Capture evidence on failure: a screenshot, the DOM or UI dump, console and page errors, and a
   trace. A timeout without them hides the real error.
3. If the suite or a step is slow, profile it (a trace or CPU profile of the call sites) before
   theorising about load.
4. Reproduce the suspected race on purpose instead of rerunning and hoping:
   - hold the specific response or event the race depends on (Playwright `page.route`, a delayed
     fixture) so the bad interleaving happens every time;
   - starve the CPU below what CI has: pin the run to fewer cores (`taskset -c 0,1` on Linux)
     or throttle Chrome (`Emulation.setCPUThrottlingRate`);
   - run the test repeatedly (`--repeat-each`) with more parallel workers than cores;
   - run the same test on the base branch to tell a regression from an existing flake.
   Generic load can miss a race that a held response hits every time.
5. Find the mechanism: what moved, what the test waited for, and what the app was still doing.
   Fix the app when it is wrong (blocking work, a repaint that shouldn't happen, layout that
   shifts when content arrives) and add the settled signal the test needs.

## Prove the fix

- **Forced race:** when a held response or event makes the old code fail every time, that
  deterministic failure before the fix and a pass after it, with the race still forced, is the
  proof.
- **Unforced flake:** report counts before and after under matched conditions (same machine,
  cores, throttle and fresh runs), such as 3/9 failures before and 0/10 after on two pinned
  cores. Measure the baseline under those conditions too.
- Size an unforced run to the failure rate: to show a failure rate p is gone, run about 3/p times
  with zero failures. Zero failures in 20 runs only shows the rate is below about 14%. More green
  runs on CI's faster machines don't prove a fix that failed under load.
- None of these is a fix: a sleep, a raised timeout, a retry, `force`, a loosened or swapped
  assertion, a skipped test, or a rerun that passed. If one is needed as a stopgap, say so and
  keep the flake open.
- Don't merge a change that touches a journey with an open flake on the strength of a rerun;
  fix the flake or get the owner's agreement first.

## Emulation and real devices

- Before judging layout or input in a browser, check in the page what it actually emulates:
  `matchMedia('(hover: hover)')`, `matchMedia('(pointer: coarse)')`, `navigator.maxTouchPoints`
  and `devicePixelRatio`. Headless Chromium has reported no hover and no fine pointer in past
  runs, and some tools' device presets set only viewport and pixel ratio.
- Emulated input and timing are slower and coarser than a device's. Don't hold an emulated run to
  a one-frame deadline; move frame-level checks to a real device.
- Emulation can't prove the soft keyboard and IME, the browser's own chrome and real viewport,
  fractional pixel ratios, native scroll anchoring, notifications, or frame timing. Confirm those
  on a real device with `iExalt:phone-debug`, batched into one session with a checklist.
- On native screens driven over adb, tap by `resource-id` from a fresh UI dump, and dump again
  after anything that moves layout (focus, the keyboard, a sheet opening).

## Claims about UI behavior

- A screenshot proves static layout at one moment. Prove motion by sampling over time (computed
  `transform`, frame captures), and prove a state by the DOM or accessibility tree.
- Name the commit, platform and build for every UI claim. Keep test output per run and per
  commit; test runners can clear their output folder between runs.
- Before reporting CI as green, check that the run belongs to the exact head commit and that it
  ran the specs you rely on.
- A timing helper that returns nothing means unknown, not "no change": the tap may have missed
  or the predicate may be wrong. Calibrate a new measurement helper on a page with a known answer
  first.
- Never report a check as passed that you didn't run on the current revision. Say which
  platforms and behaviours you did not check.
