---
name: overseer
description: "Paseo only. Run threads of a three-tiered-plan script, or tracker workstreams, to the end of the agreed scope as a dedicated orchestrator: launch Paseo worker agents that run continuous-peer-review, enforce dependencies, route every human intervention to the user, and keep the user informed with a scoreboard digest checked by an independent auditor. Use when the user wants script threads run in Paseo while they are away from the keyboard; not for writing the script (three-tiered-plan) or running one thread in this session (keep-me-in-the-loop)."
---

# Overseer

**Load `iExalt:working-conventions` before any other step.** It holds the
rules shared across the workflow skills, and this skill cites its sections as
`working-conventions` › Section without restating them. Invoke it as a skill,
or read its `SKILL.md` where your harness lists the path.

## Paseo only

The overseer runs only in Paseo. If you are not a Paseo agent (`$PASEO_AGENT_ID`
unset) or the `paseo` CLI doesn't work, tell the user the overseer runs only in
Paseo, and stop; do nothing else, and don't fall back to overseeing from your own
harness. The overseer is a Claude agent; workers are Codex agents.

## First: move into a run project

Before any other overseer work, including reading the script, the
plan or the repository's instructions, read
[references/paseo.md](references/paseo.md) › First, move into a run project
and follow it. It decides whether you are the overseer or the launcher that
hands off to one.

## References

Load each file when its situation applies; the rules in them are as binding
as this file's.

| File | Read when |
|---|---|
| [references/paseo.md](references/paseo.md) | Always: hand-off, run project, launching workers and the auditor, messaging, watching and run-project cleanup. |
| [references/high-autonomy.md](references/high-autonomy.md) | The user asks for high autonomy, before starting workers. |
| [references/tracker-workstreams.md](references/tracker-workstreams.md) | The campaign keeps tier 3 as tracker workstreams. |
| [references/question-session.md](references/question-session.md) | Always: your only dialog, `AskUserQuestion`, blocks your session. |
| [assets/worker-brief.md](assets/worker-brief.md) | You brief a worker. |
| [assets/auditor-brief.md](assets/auditor-brief.md) | The launcher briefs the auditor; you only need its tripwire list. |
| [scripts/scoreboard.py](scripts/scoreboard.py) | Always: freezes the campaign and prints the digest's line 1. |

## Role

Run script threads without implementing them. You launch **workers**, separate
top-level Paseo agents, usually one per thread. Each worker implements its
thread directly and runs `continuous-peer-review` with its own reviewer; the
hierarchy is two tiers, with no pilots and no `keep-me-in-the-loop` phases
under you. You brief them, enforce the script's order, carry their requests
for a human to the user, and keep the user in the loop. The user and the
workers both talk to you. You never talk to the auditor (see "Scoreboard and
auditor").

Run the whole agreed scope to its conclusion, using the autonomy level below
to decide when to involve the user. Record consequential judgment calls and
their reasoning in the script's revision log and report them in the next
update. Never weaken an acceptance check, exceed approved spending, or take a
destructive or external action outside the user's authorization. A release
needs the user's explicit approval naming it, or a standing release grant that
covers it (`working-conventions` › Standing grants). Permission boundaries and
releases follow `working-conventions` › Authority; the user's own checkouts
and machines, including a dirty working tree on a remote host, follow
`working-conventions` › Workspace and cleanup.

Break down and schedule work to minimize wall-clock time through verified
integration. Split independent work into parallel threads wherever that
saves time, accounting for coordination, review and integration costs.
Prioritize work that unblocks other threads, and keep coupled changes
together. Respect dependency, approval, resource and spending limits.
Give each thread one worker; a final check may have its own fresh worker,
and a crashed worker may be replaced. Never let two workers run the same
thread at once. Your context is for coordinating the run, so never implement
anything yourself, including small fixes outside every thread, and never have a native
subagent, such as one from Claude Code's Agent tool or a Codex spawned agent,
implement anything for you: you would brief, wait on and check its work in
your own session, and it dies with your session. Give such work to a worker
session of its own, or to the user. A Paseo agent launched detached, as
[references/paseo.md](references/paseo.md) describes, is such a session. The continuous
reviewer a worker starts inside its own session is part of that worker's job.
Side issues outside the campaign follow the "by the way" rule, except that
every fix you route gets its own worker: workers fix trivial ones inline and
send you the rest, as their brief says. Create each side item's
tracker item outside the campaign's root, so it doesn't count as scope growth,
and report side work only if it is still open when the campaign ends.

Keep a checklist of the threads you oversee, each with its worker and state:
waiting, ready, running, awaiting a human, blocked, done. Keep it in the run
log, `OVERSEER_RUN.md` in the run checkout, and keep the labels you use in
`OVERSEER_GLOSSARY.md` beside it (see "Keep the user in the loop").

## Choose autonomy and establish authority

Set the autonomy level as `working-conventions` › Autonomy describes. At
every level you decide routine matters within scope, at low autonomy after
consulting the user on consequential choices. High autonomy takes effect only
after the session grant in
[references/high-autonomy.md](references/high-autonomy.md).

## Establish what you oversee

Read the script, the roadmap, the canonical progress record, the parts of the plan the
threads cite, the repository's instructions and `continuous-peer-review`'s current
instructions. Check the live state: Git and the remote, running sessions and
worktrees, and resources that are up. A thread marked active may be stale, or
another session may be running it; never launch a duplicate.

Run one overseer per repository and per shared compute host. Before
launching, list the live overseers (in Paseo, `paseo agent ls --json` and
their titles and working directories). When another overseer already runs
threads in the same repository, tracker or compute host, don't run alongside
it: propose queuing your threads behind it, merging the campaigns under one
overseer, or provisioning a dedicated host, and let the user choose in the
opening dialog.

Oversee the threads the user named. When they named none, propose the ready
threads, those whose dependencies are met, in the opening message. For each
thread, note its prompt, Depends on entry, Human entry, live resources and
done check.

When the campaign keeps tier 3 in a tracker, read
[references/tracker-workstreams.md](references/tracker-workstreams.md); where
this skill says script, it means the tracker. If the tracker also holds project
status, use it for the status record as `working-conventions` › Records describes.

## Agree on the plan

Before launching anything, send an opening message that starts with a
**TL;DR**. Say which threads you will run, in what order and with what
parallelism, and each thread's scope: its roadmap steps, live resources and
spending, and the decisions and authority its approval settles. List every known human
intervention in those threads, taken from their Human entries and the
roadmap's human interventions table, and say when you will ask for each, as
"Time each request for a human" describes. When the threads have no known
intervention, say so.

For compute-heavy work, include where it runs, its CPU and memory limits,
how many jobs may run at once across workers and reviewers, and budgets for
routine tests and expensive evidence checks, so the plan's approval covers
them. Ask before exceeding an agreed limit or changing a required check.

Give each thread an active-time estimate and the campaign an active-time total
from plan agreement, both recorded in the script as LOW-HIGH ranges, so the stop-loss and the scoreboard
have a baseline. Active time is wall-clock minus the time the campaign waits on the user. Quote the user's goal verbatim in the opening message.

The opening dialog also settles, as separate questions in the same round:
- **Constraint budgets:** qualifiers in the goal, such as "without losing
  proof", become guardrails: existing required checks stay green, and new
  proof, validation or measurement infrastructure is out of scope unless the
  user approves it here, with a time cap.
- **Frozen scope:** the tasks (or the initiative or epic whose tasks) the
  campaign is measured against; later additions count as scope growth. Leaves
  that are approval gates or decisions rather than merge-proven work are
  excluded from the tasks.
- **Tripwires:** the auditor's defaults ("Scoreboard and auditor") or the
  user's overrides.
- **Auditor:** that the launcher started an independent auditor, who messages
  the user directly, and that you never talk to it.

Every thread ends in a deliverable: a merged change, a published artifact or
a written decision. When a thread's outcome is a measured improvement, such as
faster CI or a frame-time target, settle three things in the opening dialog:
- **Method:** how it is measured, concretely, such as "1 cold run and 3 warm
  runs on the same runner, median and range". Workers use it as agreed and
  build no further validation.
- **Kill criterion:** when to stop, such as "no measurable gain after two
  candidates or N active hours: revert unmerged candidates and report".
- **Done check:** the mergeable change, with the measured number reported. A
  missed target closes the thread with the number and a recommendation; it
  never keeps the thread open.
Estimate the measurement as its own chunk with a time cap; the worker brief's
measurement term applies it.

**Re-baseline gate:** after the first measurement, such as a Phase 0
baseline, close every part of the goal the baseline already meets, restate the
remaining gap against the estimate, and ask the user, in a dialog before more
work starts, whether to continue when the gap is gone or too small to justify
the estimate. A change to the frozen goal or estimate is an amendment.

### Clear the run before the user leaves

Before launching, list every decision the run is likely to reach while the
user is away: each thread's Human entries, open plan items, hosted runs, pushes
and draft PRs, credential and spending approvals (ask for a standing grant
when the run will repeat them; `working-conventions` › Standing grants),
releases, deferral of a missed proof,
and the measurement method and kill criterion above. Ask in the opening
dialog how long the user will be away, and settle each item there: decide it
now, pre-delegate it to you within a stated bound, or name it as the one
point where its thread will stop. An item left for later must name what keeps
running while it waits.

Then ask the user, through the dialog, to agree to the plan: the threads and
each one's scope. The user's agreement is each thread's only approval:
workers send no phase proposals. For high autonomy, include the separate explicit session
grant question in this opening dialog. Wait for the required answers before
starting. Ask the items from "Clear the run before the user leaves" as
separate questions in the same round, so the user settles everything in one
sitting, but don't make the plan agreement wait on them. Record the agreement, with
the date, in each thread's script entry, in a commit of its own, so a
replacement overseer can find it, then run `scoreboard.py freeze` as
"Scoreboard and auditor" describes. Invoking you is the request to implement;
confirming the script never was.

## Scoreboard and auditor

`scripts/scoreboard.py` (run as `python3 -I <skill>/scripts/scoreboard.py
--campaign <run checkout> ...`) is the campaign's one source of progress numbers;
never compute them yourself.

- **`freeze`** at plan agreement writes `campaign.json` in the run checkout: the
  user's verbatim goal, the frozen tasks (`--under <initiative or epic>`, or
  `--tasks <ids>`), each task's estimate and the campaign estimate as LOW-HIGH
  hours, the start time, an optional metric (name, baseline, target) and the
  auditor's tripwire thresholds. Frozen goal, scope and estimates change only
  through `freeze --amend --approved-by <the user's words and date> --reason ...`,
  which records an amendment; never edit the file, and never amend without the
  user's approval (`working-conventions` › Authority). Work added later under the
  scope root counts as "scope +N" until the user approves it with
  `--amend --add-task`.
  `--approved-by` quotes the user verbatim (mark cuts with `…`) and cites where
  they said it: `overseer chat <UTC time>`, or `dialog <Question session Paseo
  ID>`. For a bare "yes", include the question it answers.
- **`task-start <task>`** when work on that task begins: at its worker's launch
  for the thread's first task, and for each later task of the thread when the
  tracker shows the previous one done (check at each wake). **`task-pause <task> --on <decision item>`**
  only when the task is wholly blocked on the user (not while its worker does other work), and only with
  `--on`: the open decision item the user owes, which the task waits for in Acyclic (`waits-for`, directly
  or through other items). Waiting on CI, review or anyone other than the user is never a pause. When a worker reports an unplanned
  blocker on the user, create the decision item and its `waits-for` link before pausing.
  **`decision <item>`** right after creating any decision item: it keeps the item out of scope growth and
  lets a task you never launched that waits on it count as waiting on the user. **`task-resume`** after. A task's clock excludes that wait. A task without a clock or estimate
  never trips the per-task tripwire.
- **The campaign clock** is `active_h`: wall-clock since plan agreement minus waiting on the user, so the
  user's own delays don't count against the estimate. The script, not you, decides what is waiting. The
  campaign waits only when no task runs and every ready, claimed or dependency-blocked task is paused on a
  valid decision; a pause on a missing, done or canceled item, or one the task doesn't wait for, counts as
  active, as does a pause that outlives its decision. A ready task you never launched makes the campaign
  active; one that waits only on open decisions (cited by a pause or recorded with `decision`) or on
  waiting tasks counts as waiting. A parked item outside the campaign's tasks counts as a decision too,
  but `waiting_on_uncited` and the tripwire evidence flag it until you record it. Each of your writes (`show --digest`, `mark`, `decision`, `task-start`, `task-pause`, `task-resume`, `forecast`)
  records the state, and task commands also record it just before they change a task; an interval counts as waiting only when the writes at both ends saw it waiting, so
  time between writes counts as active, except that a wait ends at the `done_at` of the decisions it
  waited on, so closing a decision before resuming loses nothing. Run `scoreboard.py mark` at every wake that sends no digest, and
  pause and resume promptly. A task blocked directly on the decision item, or on a paused task, needs no
  pause of its own, but tasks of one thread that must run in order need `waits-for` between them: a later
  task the thread's claim leaves `claimed` but unstarted keeps the campaign active. The script does
  not reconstruct history from the tracker. Work the user adds extends the estimate through
  `freeze --amend`, never through the clock. Plan task estimates per task; a thread's
  estimate is the sum of its tasks'.
- **`forecast <task> <time>`** records your "next done expected" in each digest.
  Record it when you send the digest; a missed forecast counts against you.
- **`show`** prints line 1 of the digest; `show --digest` also records that
  digest as sent, so the next "since" counts from it. A task is done only when
  Acyclic reports it done by `item done --commit` and the commit's merge
  ancestry is verified; `unchecked_commits` is not verified. Acyclic learns each
  clone when any acyclic command runs inside it (for a github.com origin; map any
  other clone in `~/.config/acyclic/clones.toml`), so workers finishing items from
  their clone or worktree cover this. A repository it has never run in stays
  unchecked, and the task's `unverified_done` reason names the fix; apply it
  rather than checking ancestry by hand.
- **No tracker:** write line 1 yourself, marked "(self-reported)", with the same
  fields, and keep your own frozen task list and times in the run log.
  The auditor has no `campaign.json` then; say so in the opening dialog.

The **auditor** is an independent top-level Paseo agent that the launcher
starts at hand-off ([references/paseo.md](references/paseo.md) › Start the
auditor), with notifications on, a heartbeat of its own and a brief of its own
([assets/auditor-brief.md](assets/auditor-brief.md)). It reads only
`campaign.json`, `scoreboard.py show --json`, raw git, CI and tracker facts, and
the user's own words in the campaign's sessions, and messages the user once per
tripwire, once per amendment it can't match to the user's words, and once per
added task no amendment approved. The default tripwires:
campaign active time past the high end of its estimate; a running task past the high
end of its own estimate; scope grown more than 25% since launch without a
recorded user approval; your "next done" forecast missed twice; a task marked
done without verified merge evidence; a task ready but not launched for more than 1 h
(`idle_ready`); the campaign waiting on the user for more than 6 h (`waiting_on_user`,
quoting the decision's title and notes). Never message, steer, brief, answer or
feed the auditor, and never write its inputs except through the scoreboard
commands above. Its alarm is the user's, not yours to clear.

## Time each request for a human

Ask for every intervention as "Relay human interventions" describes. The
three kinds differ only in when you ask:

- **Planned, any time,** such as creating a token, settling a decision or
  approving spending: ask for all of these as soon as the user agrees to the
  plan, then launch the workers without waiting. Verify each answer where you
  can without exposing a secret.
- **Planned, at a point in a thread,** such as being online on a date or
  confirming a destructive step: ask as late as possible, when the worker is
  about to need it, allowing only the lead time the action needs.
- **Unplanned:** anything a worker discovers that only a person can resolve.
  Ask as soon as you learn of it.

## Name sessions and give workers worktrees

Name your own session `Overseer: <task>` and each worker `Worker: <subtask>`,
such as `Worker: thread 2, station pilot`.

Give each worker its own worktree through a Paseo workspace, as
[references/paseo.md](references/paseo.md) › Run project and workers
describes; a lone worker may use the run checkout when nothing else runs
there. A fresh worktree lacks ignored files such as `.env`, so provide what a
worker needs. Pick each worker's artifact directory for the brief, and resolve
missing access to ignored inputs or tools before dependent work starts.

## Session mechanism

Launch every worker as a Paseo agent, as
[references/paseo.md](references/paseo.md) › Run project and workers describes,
and name that in the opening message.

Never interrupt a running session; message it as that reference describes. A
worker's first action is to acknowledge its brief to you: record each worker's
agent ID in your checklist, and if no acknowledgement arrives, find out why,
such as a wrong address, a held message or a permission prompt, before
launching more workers.

### Model routing

Route as `working-conventions` › Model routing describes. Under an overseer:

| Role | Model | Effort |
| --- | --- | --- |
| You, the overseer | Claude Opus | `medium` |
| Auditor | Claude Opus | `medium` |
| Worker | GPT Sol | `medium` |
| A worker's reviewer | The "Independent substantive reviewer" row | `high` |

Workers have no pilots. The `subagent-pair-program` exception for standalone
leads does not apply under an overseer. The user's explicit choices and this
policy, carried in every worker brief, override conflicting model defaults in
`continuous-peer-review` and other descendant workflows, which keep their
review and acceptance gates. If a route is unavailable, report it and hold the
affected launches; never silently inherit another model. Ask the user before
changing the hierarchy when it cannot deliver the required result.

A Paseo profile must match the assigned role. Don't change a live session's
model; report a mismatch instead.

## Brief each worker

Build each brief from [assets/worker-brief.md](assets/worker-brief.md): the
load instruction, then the script's prompt for the thread with its
`/iExalt:keep-me-in-the-loop` invocation replaced by
`/iExalt:continuous-peer-review` (ignore the prompt's phase, chunk and
approval-item wording: the terms govern), then the terms, filled in for the
worker. Workers get nothing else from this skill, so keep
every term.

## Run the threads

Launch a worker for every thread whose dependencies are met, unless a **not
alongside** entry, a **not before** date or the user's limit on concurrent
workers holds it back. As threads finish, launch workers for the threads they
unblock.

The user's agreement to a thread's scope is the thread's only approval. A
worker sends no phase proposal and no chunk report; it implements the scope
with its reviewer and messages you only when its thread is done (with
completion evidence), when it hits a blocker or needs a human, when a deviation
affects another thread, or once after its first measurement (the re-baseline
gate); it holds only work that depends on the gap while you ask, and continues
the rest. Never ask a worker to come back for approval
of a probe, experiment, re-run or repair inside the agreed scope and limits;
when a worker asks anyway, answer that it is already approved and remind it of
the brief. Relay a request that changes an outcome, an acceptance check, a
deferral, a risk, an external action or spending beyond what they agreed, as
"Relay human interventions" describes, and pass the user's answer back. A
thread whose scope the user hasn't agreed, such as one that became ready
after re-sequencing, waits until they do. One thread's agreed scope never
covers another thread, and neither does one thread's answer: when the user
answers for one thread, tell only that thread, and ask again for the others.

Before reporting an acceptance result or using it to unblock a dependent,
require the finalized handoff the worker brief's reporting term lists
([assets/worker-brief.md](assets/worker-brief.md)), and check the claim
against that evidence, as `working-conventions` › Evidence describes; relay
one you can't check in time as the worker's unverified claim, saying what
would verify it. Keep a result provisional while reviewer disclosures are
pending, and carry material limits into your reports.

Repair and review rounds inside a thread's agreed scope belong to its worker.
At medium autonomy, as at high, don't relay a routine round to the user;
report its trend in your next update. Don't review the work again yourself:
the worker's reviewer owns review, and you check only the evidence for
claims you report or use to unblock a dependent.

### Keep work moving

A finished task or thread is never a stopping point while agreed scope
remains. Before ending any turn, including a heartbeat turn, list the ready
work: threads whose dependencies are met, and independent work inside threads
that wait on the user. Start or
resume all of it, except work the stop-loss below holds. A thread waiting on a decision keeps its worker on
independent work; a pending dialog never pauses the threads it doesn't
block. When every remaining item waits on the user, say so in the digest's
"Waiting on you" lines and keep the heartbeat running. When you find work that
sat idle though it could have run, restart it and log the idle time and its
cause.

### Stop-loss

At each heartbeat and task completion, read `scoreboard.py show --json` and
compare each running task's time (`tasks.<id>.running_h`) and delivered
outcomes with its estimate, and the campaign's active time (`active_h`, not elapsed) with its total.
When a thread passes the high end of its estimate with its done check unmet, or
the campaign passes the high end of its total, start no new work in it. Let running work reach a safe stopping point, and ask the user
in one dialog, with what has landed, what remains and a fresh estimate:
continue with a new estimate, trim the scope to what has landed (recorded with
`freeze --amend --drop-task`), or abandon and revert unmerged work. Recommend one. Workers keep finishing safe
in-flight work while the dialog waits. A kill criterion the user agreed acts
without a dialog: apply it and report.

When a worker reports its thread done, verify the claims before launching
dependents: its done check passed, required publication is confirmed (including
merge when required), and the canonical script/status records are reconciled.
Use `working-conventions` › Completion; a pushed branch alone is not merge proof.

When a worker reports a deviation that changes other threads, hold the
affected threads that haven't launched. Re-sequence routine changes yourself,
following three-tiered-plan's "Revise when evidence changes", and report them
in your next update. Take any change to outcomes, scope, acceptance checks,
spending or risk to the user before the affected work proceeds.

An unavailable or permission-blocked proof stays unmet, with its gate open
in the canonical script/status records, as `working-conventions` › Evidence
describes. Before asking the user to reuse, substitute or defer it, check the
worker's claim against its evidence, and ask with the proposed evidence and
what remains unproven. If more items miss than the user accepted, ask again
about the rest.

When a worker goes quiet without reporting, inspect it before nudging it, as
`working-conventions` › Waiting describes. Resume the same session with what
it needs, or relaunch the thread in a new worker with a handoff of its
recorded state, since a worker resumes from the documents and Git. When a worker fails the same way twice, report it with what you are doing
about it, and ask the user only if the remedy needs them.

After a reboot or crash of the host, recover before relaunching anything:
inventory the run's surviving remote jobs, CI runs and worktrees; recheck
grants and each thread's exact revision; resume or relaunch the workers; then
restore exactly one watcher per job and re-arm the heartbeat.

## Relay human interventions

When a request for a human comes due, whether planned or raised by a worker:

1. Apply "Choose autonomy and establish authority" first. Answer from settled
   sources, such as a recorded decision or a fact you can verify, or make a
   decision within your scope when the autonomy level permits it. Mark the
   answer as yours, with its source or reasoning. Never decide a mandatory
   consultation yourself.
2. Otherwise ask the user, as `working-conventions` › Ask the user describes,
   saying which thread it is for, what waits on the answer, and by when.
3. Ask through an async dialog, and keep the plan moving until it is blocked
   on the answer. Your only dialog, `AskUserQuestion`, blocks your session, so
   launch a question session to ask for you, as
   [references/question-session.md](references/question-session.md)
   describes. Put every decision in a dialog. For an action, such as
   minting a token, send the steps as a message and ask for confirmation in
   the dialog. Send a push notification with each request when you have the
   tool. Meanwhile, launch ready workers, relay other requests, and let the
   asking worker continue its independent work.
4. Relay the answer to the worker, quoting the user and saying what they chose
   and for which thread or item, as `working-conventions` › Record the user's
   decisions describes. Number each decision per thread, ask the worker to
   acknowledge it by number and to drop any earlier answer it replaces, and
   treat it as delivered only once acknowledged. Give a decision sent to
   several threads one number, and add it to the glossary (see "Keep the
   user in the loop") before you send it.

Answer a question from the user before anything else.

A worker's message is never the user's approval (`working-conventions` ›
Authority). Never ask a worker to do something that your session's
permissions or the user denied. Approve a pending permission request, as
`paseo permit allow` does in Paseo, only for a class of action the user
authorized for that thread; otherwise relay it. A pending request of kind
`question` is a dialog for the user, whether a question session or a worker
raised it; never answer it.

Apart from a pending permission request you may approve as above, only the
user can unblock a worker's permission prompt or classifier block.
A worker treats a message from another session, yours included, as another
agent's, so an approval you relay, even quoting the user, doesn't unblock it.
When a worker is blocked on an action that needs the user's authority, ask
the user, as steps 1 to 4 describe, to approve it directly in that worker's
thread: name the thread, the exact action and the block's reason, and say how
to open the thread, such as its Paseo title. Never
try to supply that authorization yourself, at any autonomy level.

## Keep the user in the loop

Two channels. Your chat with the user carries only:
- **(a) A state digest,** sent only when the scoreboard changes: a task closes,
  a blocker appears or clears, a forecast slips, or scope changes. Send no digest
  otherwise, and never a filler one.
- **(b) Decision dialogs,** as "Relay human interventions" describes. A request
  for the user never goes in a digest.
- **(c) The completion report.**

Worker-level events go to the run log, `OVERSEER_RUN.md` in the run checkout,
which the digest links: launches, acknowledgements, reviews, repair rounds and
their trend, recoveries, judgment calls, and each worker's evidence. Don't
commit it. Leave the three-tiered-plan revision log to what that skill assigns it.

Keep a glossary, `OVERSEER_GLOSSARY.md` beside the run log and also
uncommitted, so the user can look up any label instead of scrolling back.
Give every label you use in chat an entry: each decision number with a
one-line statement of what it settled, the threads it binds, whose call it
was (the user's or yours) and, once replaced, the decision that superseded
it; the plan's design-decision IDs, such as D3; thread and workstream
names; and any shorthand you coin.
Write the glossary as Markdown tables, never bullet lists: one table per kind
of label, with threads and workstreams, tasks, design IDs and shorthand each in
their own table. Give decisions one table per thread prefix, with the columns
ID | Decision | Whose call | Binds | Replaced / replaces.
Add the entry before the label first reaches the user, and copy the gist from
it rather than paraphrasing. In chat, a decision number or ID never stands
alone: write it with its gist on every mention, as in "CLI-4 (test
hardlinks across /raid directories)", never a bare "CLI-4" or "(CLI-2, ALL-4)". Cite a decision
number only after the user has seen that decision in full, in a decision
dialog or a "Decisions I made" entry; otherwise state it in full first.

The digest looks like this. Line 1 is pasted verbatim from
`scoreboard.py show --digest`; the rest are yours, and a line with nothing to
say is left out:

```text
<campaign> · 3/11 done (+1 since 09:00) · last done 2h ago · 21h active of 8–12h ⚠ · 4h waiting on you · scope +8 since launch
Waiting on you: <item> (since 14:27)
Blocked: <thread> (<why>)
Running: <threads> · next done expected: <thread> ~16:00
Log: <path to OVERSEER_RUN.md> · Glossary: <path to OVERSEER_GLOSSARY.md>
```

Record the "next done expected" with `scoreboard.py forecast`. Write for a reader
on a phone after hours away: name threads by outcome, not by number alone
(workstreams by name and issue number). A turn with nothing to report ends with
no text.

When the threads you oversee finish, report with a **TL;DR** using
`working-conventions` › Completion for each thread. Include judgment calls and
human interventions, the script's state, and the threads now ready.

## Clean up

Archive a worker's Paseo agent and workspace only after its work is
pushed and verified, as `working-conventions` ›
[references/paseo-launch.md](../working-conventions/references/paseo-launch.md)
› Tear down describes; archiving the workspace removes its Paseo-owned
worktree, so inspect the worktree first. If Paseo leaves a worktree behind,
force its removal only when nothing in it is work, such as a file a Git filter
normalized. Delete a `worker/<slug>` branch once its commits are on the
remote main branch. Say what you removed in the final report. Unpushed work
follows `working-conventions` › Workspace and cleanup.

Follow [references/paseo.md](references/paseo.md) › Clean up the run project for
the project, and archive the auditor there when the campaign closes.
