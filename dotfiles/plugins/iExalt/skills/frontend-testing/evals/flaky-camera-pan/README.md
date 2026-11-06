# Eval: flaky camera pan

A seeded race modelled on a real phone-journey flake. In the fixture app, tapping a node shows the
inspector at once. The app then fetches the node's details (the backend answers after a random
100 to 600 ms) and glides the camera for 200 ms. The journey test runs at a 6× CPU slowdown. It reads
the next node's position, hovers it until a tooltip appears (150 ms), then clicks. When the pan lands
in that window, the test fails with one of the two errors in [prompt.md](prompt.md). On a laptop
the unchanged fixture failed 6 times in 20 runs.

A good fix keeps the product's behaviour (the camera frames the node after its details load). It
gives the test a state to wait on: a settled signal the app clears synchronously when a node is
selected and sets when the pan ends. It also guards stale responses. Dodges remove the race by
changing the product (panning before the details load, or changing the tooltip delay) or hide it
with sleeps, retries or longer timeouts. The prompt doesn't tell agents to keep the behaviour;
the rule rests on the app's own comment ("centres the camera on the node once its details have
loaded"), so a dodge here is a product change made without asking, not an unstable fix.

## Running it

Needs zsh, `rg`, `mise` with `uv`, and a Chromium for Playwright
(`mise exec -- uv run --with playwright playwright install chromium`).

1. Copy `fixture/` once per arm. Give each agent [prompt.md](prompt.md) with `DIR` replaced by its
   copy. For the with-skill arm, prefix: "Before starting, read the skill at
   `<plugin>/skills/frontend-testing/SKILL.md` and follow it; its references are in the same
   directory."
2. Run the baseline arm in a session where the skill isn't installed. Otherwise, check its
   transcript for any read of `frontend-testing`.
3. Grade each arm with `./grade.sh <arm-dir>`, one arm at a time on a quiet machine. Each arm takes
   about 10 minutes. It copies the arm's `app.js`, `index.html` and `test_select.py` into a fresh
   fixture (the original backend delays and throttle), then runs 30 times at the default delay
   and 30 at a holdout delay of 300 to 3000 ms. The holdout catches sleeps tuned to the default.

**Pass** means all of these:
- 0/30 failures under both delays;
- no flagged test lines, other than a timeout on a condition wait;
- all three assertions kept;
- no dodge, judged from the app lines the grader prints;
- no change to the throttle, viewport or hover step.

**Process** is scored separately: whether the agent measured or forced the failure before fixing
it, and whether it reported before-and-after counts with a bound sized to the failure rate.

## Results, 2026-11-06

Three Sonnet agents per arm. The machine's load average was 5 to 15 while grading, so it wasn't
quiet. Three runs per arm is indicative only.

| Arm | Stress (default, holdout) | Fix | Pass | Measured before fixing (as the agent reported) |
|---|---|---|---|---|
| baseline 1 | 0/30, 0/30 | panned before the details load (dodge), plus a one-frame position poll | no | no |
| baseline 2 | 0/30, 0/30 | `busy()` app state, waited on; behaviour kept | yes | no |
| baseline 3 | 0/30, 0/30 | panned before the details load (dodge), plus an `isPanning()` state | no | no |
| skill 1 | 0/30, 0/30 | `data-settled` cleared synchronously, plus a generation guard | yes | yes, 3/15 before and 0/30 after, with the bound stated |
| skill 2 | 0/30, 0/30 | same design; a 15 s timeout on the condition wait | yes | no; bound stated |
| skill 3 | 0/30, 0/30 | same design | yes | yes, 4/12 before and 0/27 after, with the bound stated |

Every arm removed the flake, the two dodging baselines included, so the difference is in how
they fixed it and what they proved, not in the stress counts. With the skill, all three kept the product's behaviour and used the
settled-signal design; without it, two of three changed the product to avoid the race. Two of
three skill arms measured the failure before fixing it, against none of the baseline arms. No arm
forced the race with a held response; at a 30% failure rate, plain reruns reproduced it.

Limits:
- The with-skill arms started before a revision of `references/patterns.md` that only changed the
  canvas tap pattern.
- The arms were told to read the skill, so this tests the skill's content, not whether its
  description triggers.
- The grader wasn't checked against a quiet-window variant before scoring. No arm relied on one
  without also removing the late pan.
- The committed `grade.sh` is a path-portable rewrite of the script used for these results, with
  the same checks; the rewrite's own full run is still to come.
