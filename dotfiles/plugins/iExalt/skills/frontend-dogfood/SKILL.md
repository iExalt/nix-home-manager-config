---
name: frontend-dogfood
description: "QA a finished web or PWA interface the way this user would: a fresh tester subagent uses the running app on desktop, tablet and phone, judges it against the user's taste profile and reports evidence, and the main agent verifies, fixes and hands over only judgment calls. Focused by default; pedantic mode ('pedantic', 'thorough', 'find everything') hunts every defect. Use after a UI is built or changed and before showing it, when asked to dogfood, QA, smoke-test, click through or 'use it like a user', and at the end of frontend-design work. Not for building UI or for CLIs."
---

# Frontend Dogfood

Find what the user would find before they have to. This skill adds a QA pass between building and
handover, with a tester who judges by the user's recorded taste, not generic heuristics.

Two roles keep the judgment honest:

- **You (the main agent)** scope the pass, prepare a safe environment, brief the tester, verify
  its findings, fix them, and hand over.
- **The tester** is a fresh subagent that has not seen your code or your conclusions. It uses the
  running app through the browser only, never fixes anything, and never talks to the user.

## Modes

The modes differ in how wide the tester searches and how much gets fixed in the pass:

| | Focused (default) | Pedantic |
|---|---|---|
| Use when | Any pass, unless the user asks for pedantic | The user says "pedantic", "thorough", or "find everything" |
| Tester searches | Impression pass, task walks, then the probes what it saw calls for | Impression pass, task walks, then every applicable probe |
| Budget per form factor | About 60 browser actions and 10 minutes | About 120 actions and 25 minutes |
| Whole pass, to handover | About 45 minutes | About 90 minutes |

Pedantic mode trades time for breadth; use it before a release or when the user wants the
papercuts too.

When the user or campaign restricts the environment or data a pass may use, run a **restricted**
pass: follow the workflow within those limits, record which inputs and environments differ from
the user's real setup, and list every proof the limits rule out as untested. A restricted pass
never stands in for a normal pass's acceptance.

Read [references/qa-conduct.md](references/qa-conduct.md) before you start: it is how the user
expects agents to behave while testing. It binds you, and its sections 1, 2 and 4 bind the tester.
[references/taste-profile.md](references/taste-profile.md) is the tester's yardstick, which it
loads in full; skim it so you can judge its findings. [references/devices.md](references/devices.md)
says where browsers run and how to reach each form factor (step 2), and
[references/tester-brief.md](references/tester-brief.md) is the brief (step 3).

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
- **Device consistency:** the same look, terminology and features on every supported form factor.
  List documented viewport or input adaptations as claims to verify; small screens alone don't
  justify dropping a feature.

Pass the tester the product, not your opinion of it. Leave out known issues, what you already
checked, and why you think it works.

### 2. Prepare the environment

Follow qa-conduct and [references/devices.md](references/devices.md):

- Give the QA copy its own writable dependencies and caches. Install from the lockfile with the
  project's normal command, reusing its warm package store; never link another checkout's mutable
  `node_modules`. Retain project workspace links through the supported install.
- Keep isolation in one private wrapper or environment configuration used by setup, the server,
  probes and teardown. Include the task's home/config/data paths and runtime endpoints, including
  `KUBECONFIG` when used. A delete command with the default environment can mutate the user's real
  configuration even when creation was isolated. Record owned resource IDs for cleanup.
- Serve a production build of the app (a dev or debug build makes every timing look slow) from a
  throwaway copy of real data on its own port, and record the PID. A copy still talks to the
  outside world unless you cut it off: remove or blank git remotes and sync targets, turn sync off,
  and strip push subscriptions, tokens, and webhooks. Then confirm nothing leaves: run the server
  with outbound network blocked where the project supports it, and check the browser's `network
  requests` for third-party or real-backend calls during a first journey. Journeys must not raise
  real OS notifications or touch the user's own browser profile.
- Make the copy behave like the user's real setup, or testers report your setup. Copy the app's
  own config that changes what it shows (for example which local repositories it checks), with
  its outbound effects cut, rather than starting from an empty home. Before briefing, compare a
  summary the app derives (a queue, counts, statuses) between the copy and the real data; any
  difference is a setup defect to fix first.
- Read the user's environment file (devices.md › The environment file); if it is missing, settle
  it with the user now, because the tester can't ask. Put the host and tier facts the tester needs
  into the brief. If the browser host is unreachable, ask the user once instead of falling back to
  the laptop.
- Make sure agent-browser is installed on the test host (devices.md) and that the app is reachable
  from it. Open each tester's browser session with `scripts/dogfood.py init --open` (devices.md ›
  Drive the browser), so testers start testing instead of writing their own ssh wrappers.
- Before a batch, check host CPU/load and memory/swap, then run one representative journey and
  capture a screenshot through the supported helpers. Verify its result artifact and inspect the
  image. Resolve missing configuration, helper dependencies or a stale app build as setup defects;
  do not classify those failures as product findings. Use `uv run` for dogfood.py so its declared
  Pillow dependency is supplied. Keep timing comparisons on matched, quiet host conditions.
- Create the local evidence directory, `<project>/design/dogfood/<YYYY-MM-DD>-<slug>/`, and keep it
  out of git (`.git/info/exclude`) unless the project commits its screenshots. Everything the tester
  cites must be a local path there, so you can show it in chat.

### 3. Brief and run the tester

Fill in [references/tester-brief.md](references/tester-brief.md), including the mode, and give it to
a fresh subagent verbatim, with the paths of taste-profile.md, qa-conduct.md, and devices.md. Set
the mode's budget (Modes), halved when only one screen changed. When several form factors are in
scope and the harness allows it, run one tester per form factor in parallel, each with its own
browser session name and evidence subdirectory. Each browser's cap (devices.md) is per launch:
when the user sets an aggregate resource limit, the app server and every tester share it, so
run them inside one scope that enforces it or run testers one at a time. Name who owns the
server, each browser session and their teardown. Wait for them in the foreground, not as background
tasks: some harnesses deliver a background subagent's completion to the top-level session, not to
you.

If no subagent is available, run the brief yourself in a clean context and say in the report that
the tester was not independent.

### 4. Verify the report

Treat the report as claims to check, not results. The tester writes every finding to
`findings.md` in its evidence directory and returns the top five; read both.

- Reproduce every P0 and P1 from its steps and evidence before acting on it.
- Check the interaction log: a pass that only screenshotted and never clicked, typed, dragged, or
  measured did not test. Send it back with the gap named.
- Drop findings that have neither evidence nor a reference (a profile principle, a reference app
  at the same viewport, another screen of the same app, or a measurement). Keep pre-existing
  defects: they are tagged, not out of scope.
- Fold duplicates into one finding with every place it occurs.
- Re-measure any slow timing before it counts, with one browser on the host and no other tester or
  server running. Report the quiet number and how you got it.
- Treat a tap that landed elsewhere, or a result that changes between runs, as a possible race
  rather than a defect or noise, and diagnose it with `iExalt:frontend-testing` › When a test
  flakes. Write the regression test for a fix following that skill too.
- Compare matching screens, states, and task outcomes across form factors, with the same data and
  theme, reconciling separate testers' evidence yourself. Write a device comparison summary:
  justified adaptations, defects, and untested combinations.

### 5. Fix, re-check, and file

What gets fixed in the pass depends on the mode:

- **Focused:** fix every verified P0 and P1, and each P2 that is cheap: one component, no design
  decision, minutes rather than an hour. File the rest (below) without asking. If the P0 and P1
  fixes alone need several commits, design decisions, or changes outside the frontend, report and
  ask before fixing, as for a larger pedantic list.
- **Pedantic:** the size of the verified list decides.
  - **Small:** the verified P0 to P2 findings are about ten or fewer, need no design decision from
    the user, and stay inside the frontend. Fix them all yourself; the user wants papercuts fixed
    in the same pass, not filed.
  - **Larger:** anything else, such as an audit of an existing UI. Stop after verification and
    follow [references/follow-up.md](references/follow-up.md) › Larger pedantic lists before
    fixing anything.

Use frontend-design for the design work. Run independent fix chunks in parallel, each in its own
subagent and worktree, and merge them as they pass; keep chunks that edit the same files in one
sequence.

**File what you don't fix.** When the project's tracker is private to the user (a local tracker or
a private repository's issues), file each unfixed finding as an item without asking, grouped under
one thread named for the pass, with its severity and evidence path in the notes. A public tracker
needs the user's agreement first, and its items must not carry screenshots of or quotes from real
data. Otherwise, or until they agree, keep the findings in the git-excluded `<evidence-dir>/findings.md`. Leave out
anything on the "Already decided or filed" list and P3s the user has already declined. Don't list
filed findings in chat beyond a count and the link.

**Re-check, don't re-explore.** When the fixes are merged, check each fixed finding yourself by
its own steps, with a before-and-after screenshot, and run one first-glance sweep (cold load and
screenshots in each theme) on every form factor in scope to catch what the fixes broke elsewhere.
A regression your fix caused is yours to fix; if the second attempt fails too, revert that fix and
file the finding. There is no second exploratory round by default. Run another round only when the
user asks for one, usually after their own look (step 6). For that round, fill the brief's "Already
decided or filed" field. A request to fix filed findings starts a separate repair phase: re-check
those fixes as above; it does not authorize another exploratory round.

**Keep to the time budget.** Note the start time. If the pass reaches one and a half times its
mode's budget, stop fixing, file what's left, and hand over what is done, naming every P0 and P1
you didn't fix.

### 6. Hand over

Hand over as soon as step 5 is done; this is the user's early look, and their review decides whether
another round is worth it. Show screenshots in chat, with a short plain-language summary, and offer
a link they can open on their phone or laptop (over their private network, such as a tailnet, when
they have one). Serve that link from its own throwaway copy of the real data with remotes removed;
real data, the production app and its infrastructure stay untouched. Before sharing it, read back
the link server's data and config paths and confirm its outbound effects are cut, as in step 2. Say
which parts of the link's path you couldn't test yourself. Give every file you mention as an
absolute path.

- the top five problems, ranked, and what you did about each, plus every other P0 or P1 you didn't
  fix;
- the other fixes, in a few lines;
- the questions only they can answer, which are look-and-feel judgments with the alternatives
  shown as images; never ask them to check something measurable;
- what was not tested and why (form factor not reachable, emulation limits, device-only probes);
- how many findings you filed, and where;
- how long the pass took against its budget, and the mode it ran in;
- what this handover closes: the exploratory pass, fix verification, or a separately authorized
  repair phase.

Tear down what you started (qa-conduct): servers by PID, tunnels, browser sessions, test data,
guest settings you changed, and LOCK files.

### 7. Learn from the user's review

When the user reviews the UI after a pass, follow
[references/follow-up.md](references/follow-up.md) › Learning from the user's review.

## Severity

Use the scale in taste-profile.md › Severity calibration. P1 is what the user notices at first
look; agents have wrongly called these cosmetic.
