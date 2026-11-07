---
name: overseer
description: "Run threads of a three-tiered-plan script, or tracker workstreams, to the end of the agreed scope as a dedicated orchestrator: launch worker sessions that run keep-me-in-the-loop (Paseo agents in Paseo, otherwise Claude Code or Codex sessions), enforce dependencies, route every human intervention to the user and send concise updates. Use when the user wants script threads run while they are away from the keyboard; not for writing the script (three-tiered-plan) or running one thread in this session (keep-me-in-the-loop)."
---

# Overseer

**Load `iExalt:working-conventions` before any other step.** It holds the
rules shared across the workflow skills, and this skill cites its sections as
`working-conventions` › Section without restating them. Invoke it as a skill,
or read its `SKILL.md` where your harness lists the path.

## First, in Paseo: move into a run project

In Paseo, before any other overseer work, including reading the script, the
plan or the repository's instructions, read
[references/paseo.md](references/paseo.md) › First, move into a run project
and follow it. It decides whether you are the overseer or the launcher that
hands off to one.

## References

Load each file when its situation applies; the rules in them are as binding
as this file's.

| File | Read when |
|---|---|
| [references/paseo.md](references/paseo.md) | You run in Paseo: hand-off, run project, launching, messaging, watching and run-project cleanup. |
| [references/claude-code.md](references/claude-code.md) | You launch workers as Claude Code background sessions. |
| [references/codex.md](references/codex.md) | You launch workers with `codex exec`. |
| [references/high-autonomy.md](references/high-autonomy.md) | The user asks for high autonomy, before starting workers. |
| [references/tracker-workstreams.md](references/tracker-workstreams.md) | The campaign keeps tier 3 as tracker workstreams. |
| [references/question-session.md](references/question-session.md) | Your only dialog blocks your session, as Claude Code's does. |
| [assets/worker-brief.md](assets/worker-brief.md) | You brief a worker. |

## Role

Run script threads without implementing them. You launch **workers**, separate
top-level sessions that act as middle-tier thread leads and each run
`keep-me-in-the-loop`, usually one per thread. They delegate implementation
to cheaper native pilots within their own sessions. You brief them, enforce
the script's order, carry their requests for a human to the user, and keep
the user in the loop. The user and the workers both talk to you.

Run the whole agreed scope to its conclusion, using the autonomy level below
to decide when to involve the user. Record consequential judgment calls and
their reasoning in the script's revision log and report them in the next
update. Never weaken an acceptance check, exceed approved spending, or take a
destructive or external action outside the user's authorization. A release
needs the user's explicit approval naming it. Permission boundaries and
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
[references/paseo.md](references/paseo.md) describes, is one. The continuous
reviewer a worker starts inside its own session is part of that worker's job.

Keep a checklist of the threads you oversee, each with its worker and state:
waiting, ready, running, awaiting approval, awaiting a human, blocked, done.
Your status updates show it as a one-line roll call.

## Choose autonomy and establish authority

Set the autonomy level as `working-conventions` › Autonomy describes. At
every level you approve phases within scope, at low after consulting the
user on consequential choices. High autonomy takes effect only after the
session grant in
[references/high-autonomy.md](references/high-autonomy.md).

## Establish what you oversee

Read the script, the roadmap, the status document, the parts of the plan the
threads cite, the repository's instructions and `keep-me-in-the-loop`'s current
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

When the campaign keeps tier 3 as workstream issues, read
[references/tracker-workstreams.md](references/tracker-workstreams.md); where
this skill says script, it means the tracker.

## Agree on the plan

Before launching anything, send an opening message that starts with a
**TL;DR**. Say which threads you will run, in what order and with what
parallelism, which session mechanism you will use, and each thread's scope:
its roadmap steps, proposed chunks, live resources and spending, and the
decisions and authority its approval settles. List every known human
intervention in those threads, taken from their Human entries and the
roadmap's human interventions table, and say when you will ask for each, as
"Time each request for a human" describes. When the threads have no known
intervention, say so.

For compute-heavy work, include where it runs, its CPU and memory limits,
how many jobs may run at once across workers and reviewers, and budgets for
routine tests and expensive evidence checks, so the plan's approval covers
them. Ask before exceeding an agreed limit or changing a required check.

Give each thread an active-time estimate and the campaign a total, both
recorded in the script, so the stop-loss in "Keep work moving" has a baseline.

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

### Clear the run before the user leaves

Before launching, list every decision the run is likely to reach while the
user is away: each thread's Human entries, open plan items, hosted runs, pushes
and draft PRs, credential and spending approvals, deferral of a missed proof,
and the measurement method and kill criterion above. Ask in the opening
dialog how long the user will be away, and settle each item there: decide it
now, pre-delegate it to you within a stated bound, or name it as the one
point where its thread will stop. An item left for later must name what keeps
running while it waits.

Then ask the user, through the dialog, to agree to the plan: the threads and
each one's scope. For high autonomy, include the separate explicit session
grant question in this opening dialog. Wait for the required answers before
starting. Ask the items from "Clear the run before the user leaves" as
separate questions in the same round, so the user settles everything in one
sitting, but don't make the plan agreement wait on them. Record the agreement, with
the date, in each thread's script entry, in a commit of its own, so a
replacement overseer can find it. Invoking you is the request to implement;
confirming the script never was.

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
such as `Worker: thread 2, station pilot`, wherever the harness supports names.
Where it doesn't, as with `codex exec`, keep the worker's name beside its
session ID in your checklist.

By default, give each worker its own worktree; a lone worker may use the
main checkout when nothing else runs there. Outside Paseo, use
`../<repo>-worker-<slug>/` on branch `worker/<slug>`, from the freshly fetched
remote main branch, per `working-conventions` › Workspace and cleanup. A fresh
worktree lacks ignored files such as `.env`, so provide what a worker needs.
Pick each worker's artifact directory for the brief, and resolve missing
access to ignored inputs or tools before dependent work starts.

## Choose the session mechanism

Use the first mechanism that applies, name it in the opening message, and
read its reference before launching workers:

1. **Paseo,** when you run in it and its `paseo` CLI works:
   [references/paseo.md](references/paseo.md) › Run project and workers.
2. **Your own harness,** so that messages travel natively: Claude Code
   ([references/claude-code.md](references/claude-code.md)) or Codex
   ([references/codex.md](references/codex.md)).
3. **Elsewhere:** the harness's equivalent of a resumable, addressable
   session. If it has none, say so, give the user each worker's brief to open
   by hand, and keep overseeing through what they relay.

Never interrupt a running session; message it through the channel your
mechanism's reference describes. A worker's first action is to acknowledge
its brief to you: record each worker's session ID and address in your
checklist, and if no acknowledgement arrives, find out why, such as a wrong
address, a held message or a permission prompt, before launching more
workers.

### Three-tier model routing

Route every session as `working-conventions` › Model routing describes: you
take the top-orchestrator row, each worker the lead row, and its pilots and
independent reviewer theirs. The `subagent-pair-program` exception for
standalone leads does not apply under an overseer. The user's explicit
choices and this policy, carried in every worker brief, override conflicting
model defaults in `keep-me-in-the-loop`, its review skill and other descendant
workflows, which keep their review and acceptance gates. Ask the user before
changing the hierarchy when it cannot deliver the required result.

In Paseo, a profile must match the assigned tier. Don't change a live
session's model; report a mismatch instead.

## Brief each worker

Build each brief from [assets/worker-brief.md](assets/worker-brief.md): the
load instruction, then the script's prompt for the thread, then the terms,
filled in for the worker. Workers paste nothing else from this skill, so keep
every term.

## Run the threads

Launch a worker for every thread whose dependencies are met, unless a **not
alongside** entry, a **not before** date or the user's limit on concurrent
workers holds it back. As threads finish, launch workers for the threads they
unblock.

Check each phase proposal against the scope the user agreed for its thread.
Approve it on the user's behalf when it fits and the autonomy rules allow you
to decide. At medium and high autonomy, approve every phase inside the agreed
scope at once, as `keep-me-in-the-loop`'s multi-phase approval, and add no
conditions beyond the agreed scope and limits. Never ask a worker to come back
for approval of a probe, experiment, re-run or repair inside them; when a
worker asks anyway, answer that it is already approved and remind it of the
brief. Relay one that changes an outcome, an acceptance check, a
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

A finished phase, chunk or thread is never a stopping point while agreed
scope remains. Before ending any turn, including a heartbeat turn, list the
ready work: threads whose dependencies are met, next phases inside an
approval, and independent work inside threads that wait on the user. Start or
resume all of it, except work the stop-loss below holds. A thread waiting on a decision keeps its worker on
independent work; a pending dialog never pauses the threads it doesn't
block. When every remaining item waits on the user, say so in an update
listing each item and what it waits on, and keep the heartbeat running.
When you find work that sat idle though it could have run, restart it and
report the idle time and its cause in your next update.

### Stop-loss

At each heartbeat and phase completion, compare each thread's active time and
delivered outcomes with its estimate. When a thread reaches 1.5× its estimate
with its done check unmet, or the campaign reaches 1.5× its total, start no new
work in it. Let running chunks reach a safe stopping point, and ask the user
in one dialog, with what has landed, what remains and a fresh estimate:
continue with a new estimate, trim the scope to what has landed, or abandon
and revert unmerged work. Recommend one. Workers keep finishing safe
in-flight work while the dialog waits. A kill criterion the user agreed acts
without a dialog: apply it and report.

When a worker reports its thread done, verify the claims before launching
dependents: the script marks the thread done, its commits are on the remote,
the status document is updated, and its done check passed.

When a worker reports a deviation that changes other threads, hold the
affected threads that haven't launched. Re-sequence routine changes yourself,
following three-tiered-plan's "Revise when evidence changes", and report them
in your next update. Take any change to outcomes, scope, acceptance checks,
spending or risk to the user before the affected work proceeds.

An unavailable or permission-blocked proof stays unmet, with its gate open
in the script and status document, as `working-conventions` › Evidence
describes. Before asking the user to reuse, substitute or defer it, check the
worker's claim against its evidence, and ask with the proposed evidence and
what remains unproven. If more items miss than the user accepted, ask again
about the rest.

When a worker goes quiet without reporting, inspect it before nudging it, as
`working-conventions` › Waiting describes. Resume the same session with what
it needs, or relaunch the thread in a new worker with a handoff of its
recorded state, since `keep-me-in-the-loop` resumes from the documents and
Git. When a worker fails the same way twice, report it with what you are doing
about it, and ask the user only if the remedy needs them.

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
   on the answer. Use a native async input dialog, such as Codex's
   `request_user_input_async`, when your harness has one. When your only
   dialog blocks your session, as Claude Code's `AskUserQuestion` does,
   launch a question session to ask for you, as
   [references/question-session.md](references/question-session.md)
   describes. Put every decision in a dialog. For an action, such as
   minting a token, send the steps as a message and ask for confirmation in
   the dialog. Send a push notification with each request when you have the
   tool. Meanwhile, launch ready workers, relay other requests, and let the
   asking worker continue its independent work.
4. Relay the answer to the worker, quoting the user and saying what they chose
   and for which thread or item, as `working-conventions` › Record the user's
   decisions describes.

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
to open the thread, such as its Paseo title or `claude attach <id>`. Never
try to supply that authorization yourself, at any autonomy level.

## Keep the user in the loop

Every status update looks like this: a few lines, ending with the roll call.

```text
**Done:** thread 2 (station pilot) published chunk 2 of 3: the driver handoff works on the dev host.
**Next:** thread 2 tests the relay fallback; thread 4 starts when thread 2 finishes.
**Unexpected:** a rate limit slowed thread 3's host listing; it retried and carried on.
Threads: 1 done · 2 chunk 3/3 · 3 chunk 1/2 · 4 waiting on 2
```

Each update answers what did we just accomplish, what happens next, and did
anything unexpected occur; leave the third out when nothing did. Name threads
by number and outcome, not by number alone (workstreams by name and issue
number). The roll call is required in every update, and each update must
read on its own after hours away.

Send status updates for the events `working-conventions` › Updates lists,
and for anything unexpected, batching events from all threads.

A request for the user goes in a dialog of its own, as "Relay human
interventions" describes, never in a status update.

When the threads you oversee finish, report with a **TL;DR**: each thread's
outcome and publication, evidence limits and deferrals, the judgment calls
and human interventions that happened, the script's state, and the threads
now ready.

## Clean up

Archive a worker's Paseo agent and workspace, remove its Claude background
session with `claude rm`, or end its Codex session, only after its work is
pushed and verified. Inspect a worktree before removing it, and force a
removal only when nothing in it is work, such as a file a Git filter
normalized. Delete a `worker/<slug>` branch once its commits are on the
remote main branch. Say what you removed in the final report. Unpushed work
follows `working-conventions` › Workspace and cleanup.

A Paseo run project is the exception: follow
[references/paseo.md](references/paseo.md) › Clean up the run project.
