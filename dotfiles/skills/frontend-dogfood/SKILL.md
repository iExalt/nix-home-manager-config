---
name: frontend-dogfood
description: "QA a finished web or PWA interface the way this user would: a fresh tester subagent uses the running app like a person on desktop, tablet, and phone form factors, judges it against the user's recorded taste profile, measures feel instead of guessing, and reports evidence-backed findings; the main agent then verifies, fixes, and hands over only what needs human judgment. Use after a UI is built or changed and before showing it to the user, whenever asked to dogfood, QA, smoke-test, click through, try out, or 'use it like a user', and at the end of frontend-design work. Not for designing or building UI (frontend-design) or for CLIs."
---

# Frontend Dogfood

Find what the user would find before they have to. They review UIs by using them on real devices
and reliably catch the same kinds of problem: unreadable first views, dark themes that are not
dark, wasted space, states that cannot be told apart, duplicated or noisy details, controls hidden
by the keyboard, and clicks that do not land at once. Agents have repeatedly handed over work with
these defects, or seen them and filed them as cosmetic. This skill runs a QA pass between building
and handover, with a tester who judges by the user's recorded taste rather than generic heuristics.

Two roles keep the judgment honest:

- **You (the main agent)** scope the pass, prepare a safe environment, brief the tester, verify
  its findings, fix them, and hand over.
- **The tester** is a fresh subagent that has not seen your code or your conclusions. It uses the
  running app through the browser only, never fixes anything, and never talks to the user.

Read [references/qa-conduct.md](references/qa-conduct.md) before you start: it is how the user
expects agents to behave while testing, and it binds you and the tester alike.
[references/taste-profile.md](references/taste-profile.md) is the tester's yardstick; skim it so
you can judge its findings. [references/devices.md](references/devices.md) says where browsers run
and how to reach each form factor.

## Workflow

Keep a short checklist of these steps.

### 1. Scope the pass

Write down, from the project's docs (DESIGN.md, PRODUCT.md, README) and the change itself:

- **Surfaces:** the screens and flows that changed, then the ones they touch. Changed surfaces set
  the order of exploration, not the limit of what gets reported.
- **Primary tasks:** the one to three things a user comes to do, in the user's own words when the
  docs have them.
- **Target form factors and themes:** which of desktop, tablet, and phone the project supports,
  which is primary, and whether it has a dark theme.
- **Real data:** the realistic dataset the tester will use, at the sizes the user works with.

Pass the tester the product, not your opinion of it. Leave out known issues, what you already
checked, and why you think it works: anchoring makes testers confirm instead of explore.

### 2. Prepare the environment

Follow qa-conduct and [references/devices.md](references/devices.md):

- Serve a production build of the app (a dev or debug build makes every timing look slow) from a
  throwaway copy of real data on its own port, and record the PID. Real data matters: synthetic
  fixtures hide problems that only the user's data shows. A copy
  still talks to the outside world unless you cut it off: remove or blank git remotes and sync
  targets, turn sync off, and strip push subscriptions, tokens, and webhooks. Then confirm nothing
  leaves: run the server with outbound network blocked where the project supports it, and check the
  browser's `network requests` for third-party or real-backend calls during a first journey.
  Journeys must not raise real OS notifications or touch the user's own browser profile.
- Read the user's environment file (devices.md › The environment file) for their machines. If it
  is missing, settle it with the user now, because the tester can't ask; either way, put the host
  and tier facts the tester needs into the brief. Browsers run on the browser host it names, never
  on the laptop. If the host is unreachable, ask the user once instead of falling back to the
  laptop.
- Make sure agent-browser is installed on the test host (devices.md) and that the app is reachable
  from it. Open each tester's browser session with `scripts/dogfood.py init --open` (devices.md ›
  Drive the browser), so testers start testing instead of writing their own ssh wrappers.
- Create the local evidence directory, `<project>/design/dogfood/<YYYY-MM-DD>-<slug>/`, and keep it
  out of git (`.git/info/exclude`) unless the project commits its screenshots. Everything the tester
  cites must be a local path there, so you can show it in chat.

### 3. Brief and run the tester

Fill in [references/tester-brief.md](references/tester-brief.md) and give it to a fresh subagent
verbatim, with the paths of taste-profile.md, qa-conduct.md, and devices.md. Set an explicit
budget (browser actions and minutes) sized to the change: about 40 actions for one changed screen,
about 120 for a new multi-screen flow across form factors. When several form factors are in scope
and the harness allows it, run one tester per form factor in parallel, each with its own browser
session name and evidence subdirectory. Wait for them in the foreground (start them together and
block until all return) rather than as background tasks: some harnesses deliver a background
subagent's completion to the top-level session instead of to you, and you'd wait forever.

If no subagent is available, run the brief yourself in a clean context and say in the report that
the tester was not independent.

### 4. Verify the report

Treat the report as claims to check, not results:

- Reproduce every P0 and P1 from its steps and evidence before acting on it.
- Check the interaction log: a pass that only screenshotted and never clicked, typed, dragged, or
  measured did not test. Send it back with the gap named.
- Drop findings that have neither evidence nor a reference (a profile principle, a reference app
  at the same viewport, another screen of the same app, or a measurement). Keep pre-existing
  defects: they are tagged, not out of scope.
- Fold duplicates into one finding with every place it occurs.

### 5. Agree the scope, fix, and re-run

The size of the verified list decides what happens next:

- **Small:** the pass covered one change, and the verified P0–P2 findings are about ten or fewer,
  need no design decision from the user, and stay inside the frontend. Fix them all yourself,
  using frontend-design for the design work; the user wants papercuts fixed in the same pass, not
  filed.
- **Larger:** an audit of an existing UI, or a list that needs several commits, design decisions,
  or changes outside the frontend. Stop after verification and report before fixing anything:
  verified counts per severity, the worst findings with screenshots, the decisions only the user
  can make, and what the fixing will cost (how many chunks or pull requests, which surfaces,
  anything outside the UI, and a rough duration). Offer scopes: P0 and P1 only; all of P0–P2; or
  the list as a handover. Fix only what they choose. In one audit, "fix all of it" became more
  than five hours of chunks, reviews, and CI before the second round could start.

P3 items go to the handover list. Then re-run with fresh testers and a new budget, narrower than
round one:

- the surfaces your fixes touched, walked again on the form factors where they changed;
- a first-glance sweep (brief step 1 only: cold load and screenshots in each theme) on every form
  factor in scope, to catch what your fixes broke elsewhere. One tester can sweep all form
  factors.

Don't repeat full walks of surfaces you didn't touch.

Stop on materiality, not on an empty report: a tester always finds something. Record each round's
counts (P0/P1 found, total). If a round's P0 + P1 count does not fall, or a fix creates new P0/P1
findings, stop and ask the user before another round.

### 6. Hand over

Show the user screenshots in chat (and a link they can open on their phone when that is how they
review), with a short plain-language summary. Give every file you mention as an absolute path: a
path relative to the project sent the user looking for it.

- what now works, and what you fixed from the dogfood pass;
- the questions only they can answer, which are look-and-feel judgments with the alternatives
  shown as images; never ask them to check something measurable;
- what was not tested and why (form factor not reachable, emulation limits, device-only probes);
- P3 items you left, in one line each.

Tear down what you started (qa-conduct): servers by PID, tunnels, browser sessions, test data,
guest settings you changed, and LOCK files.

### 7. Learn from the user's review

When the user reviews the UI after a dogfood pass, compare what they caught with what the tester
reported. For each thing they caught that the tester missed, propose an addition to
taste-profile.md: the principle with the user's words as the receipt, and a probe that would have
caught it. Show the proposed lines and edit the profile only after the user approves. Corrections
go the other way too: if the user waves off a finding the profile predicted, propose narrowing or
removing that rule.

## Severity

Use the scale in taste-profile.md › Severity calibration, which maps this user's reactions to
P0–P3. The short version: P0 blocks or makes the UI unusable on a target device; P1 is what they
notice at first look (agents have wrongly called these cosmetic); P2 is a papercut they still want
fixed now; P3 is noted and not pushed.

## References

| File | Read it when |
|---|---|
| [references/qa-conduct.md](references/qa-conduct.md) | Before starting; rules for both roles |
| [references/taste-profile.md](references/taste-profile.md) | Judging findings; the tester loads it in full |
| [references/tester-brief.md](references/tester-brief.md) | Briefing the tester (step 3) |
| [references/devices.md](references/devices.md) | Preparing hosts, browsers, and form factors (step 2) |
