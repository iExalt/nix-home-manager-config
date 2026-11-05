---
name: overseer
description: "Oversee one or more threads of a three-tiered-plan script, or workstreams in the repository's tracker, as a dedicated orchestrator: once the user agrees to the plan, run the agreed scope to its end autonomously, launching worker sessions that run keep-me-in-the-loop (Paseo agents through Paseo's built-in tools when running in Paseo, otherwise new Claude Code or Codex sessions), enforcing the script's dependencies, routing every human intervention through yourself to the user, and keeping them in the loop with concise status updates. Use when the user wants script threads run while they are away from the keyboard; not for writing the script (use three-tiered-plan) or for running one thread in this session (use keep-me-in-the-loop)."
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
| [references/paseo.md](references/paseo.md) | You run in Paseo: hand-off, run project, launching, messaging, watching, classifier relays and run-project cleanup. |
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

Organize workers as you see fit. One worker per thread is the default; you
might instead give a final check its own fresh worker, or relaunch a thread
in a new worker after a crash. Never let two workers run the same thread at
once. Never implement a thread yourself, and never hand one to a native
subagent, such as one from Claude Code's Agent tool or a Codex spawned agent:
it shares your session's lifetime and context budget, and a worker needs a
session of its own. Paseo files the agents `create_agent` launches as your
subagents, but each is a full session with its own conversation, so it can
serve as a worker once you detach it into a thread of its own, as
[references/paseo.md](references/paseo.md) describes. The continuous reviewer
a worker starts inside its own session is part of that worker's job.

Keep a checklist of the threads you oversee, each with its worker and state:
waiting, ready, running, awaiting approval, awaiting a human, blocked, done.
Your status updates show it as a one-line roll call.

## Choose autonomy and establish authority

Use the autonomy levels, mandatory consultations and measurable-first rule in
`working-conventions` › Autonomy, which says where to state the level;
record it in the script and worker briefs. At medium, the default, you
approve phases within scope; at high, you approve phases and resolve
recoverable issues yourself, reporting meaningful decisions afterward. High
autonomy takes effect only after the session grant in
[references/high-autonomy.md](references/high-autonomy.md).

## Establish what you oversee

Read the script, the roadmap, the status document, the parts of the plan the
threads cite, the repository's instructions and `keep-me-in-the-loop`'s current
instructions. Check the live state: Git and the remote, running sessions and
worktrees, and resources that are up. A thread marked active may be stale, or
another session may be running it; never launch a duplicate.

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

For compute-heavy work, include where it runs, CPU and memory limits, and
how many jobs may run together across workers and their reviewers. Propose
budgets for routine test runs and expensive evidence checks separately,
using existing timings where available. Reuse settled limits; include any
new limits in this plan's approval rather than adding a separate ceremony.
Have workers measure a baseline before expanding a workload. If a budget is
exceeded or sustained growth threatens it, reduce concurrency or optimize
within scope; ask before exceeding agreed limits or changing required checks.

Carry the terms in `working-conventions` › Test cost between workers, compared
across the whole run. Assign a test-runtime regression to the worker
introducing it while its change is still in progress.

Then ask the user, through the dialog, to agree to the plan: the threads and
each one's scope. For high autonomy, include the separate explicit session
grant question in this opening dialog. Wait for the required answers before
starting. Leave the threads' open decisions and other planned interventions
out of it, so the agreement doesn't wait on them. Record the agreement, with
the date, in each thread's script entry, in a commit of its own, so a
replacement overseer can find it. Invoking you is the request to implement;
confirming the script never was.

Once a scope is agreed, you approve that thread's `keep-me-in-the-loop` phase
proposal on the user's behalf when it stays within the scope, consulting on
consequential choices at low autonomy. Relay a proposal to the user when it
changes an outcome, an acceptance check, a deferral, a risk, an external
action or spending beyond what they agreed. A thread whose scope the user
hasn't agreed, such as one that became ready after re-sequencing, waits until
they do.

## Time each request for a human

Ask for every intervention as "Relay human interventions" describes. The
three kinds differ only in when you ask:

- **Planned, any time:** the user can act whenever they like, such as creating
  a token or an OAuth client, settling a decision, provisioning access,
  approving spending, or a login that persists. Ask for all of these as soon
  as the user agrees to the plan, before the threads start, then launch the
  workers without waiting. Verify each answer where you can without exposing
  a secret.
- **Planned, at a point in a thread:** the user can only act at a time or when
  a thread reaches a point, such as being online on a date, a login that
  expires, or confirming a destructive step. The opening message announced
  it. Ask for it as late as possible: when the worker is about to need it,
  allowing only the lead time the action itself needs, so the request is
  current when the user acts on it.
- **Unplanned:** anything a worker discovers that only a person can resolve.
  Ask as soon as you learn of it.

## Name sessions and give workers worktrees

Name your own session `Overseer: <task>` and each worker `Worker: <subtask>`,
such as `Worker: thread 2, station pilot`, wherever the harness supports names.
Keep the name the user gave you at launch, such as
`claude --bg -n "Overseer: <task>"`. Otherwise, where you can't rename your
own session, as in Claude Code, ask the user to rename it (Claude Code's
`/rename`) as a planned any-time item. Send running workers your new address
if it changes. Where a harness has no session names, as with `codex exec`,
keep the worker's name beside its session ID in your checklist.

By default, give each worker its own worktree. A lone worker may use the main
checkout when nothing else runs there. Outside Paseo, use the sibling
convention in `working-conventions` › Workspace and cleanup: a worktree at
`../<repo>-worker-<slug>/` on branch `worker/<slug>`, created from the freshly
fetched remote main branch with
`git worktree add ../<repo>-worker-<slug> -b worker/<slug> origin/main`. A
fresh worktree lacks ignored files such as `.env` and local artifacts, so
provide what a worker needs or let it work in the main checkout. Remove each
worktree as "Clean up" describes.

Give each worker a directory inside its permitted checkout for operational
logs and artifacts that must survive a resume. Include it in the brief and
have the worker confirm it can write and read there before a long operation.
Check access to required ignored inputs and tools at the same time, without
printing secrets. Resolve missing access before dependent work starts;
changing paths or tools is not a way around an existing permission denial.

## Choose the session mechanism

Use the first mechanism that applies, name it in the opening message, and
read its reference before launching workers:

1. **Paseo,** when you run in it with its built-in tools:
   [references/paseo.md](references/paseo.md) › Run project and workers.
2. **Your own harness,** so that messages travel natively: Claude Code
   ([references/claude-code.md](references/claude-code.md)) or Codex
   ([references/codex.md](references/codex.md)).
3. **Elsewhere:** the harness's equivalent of a resumable, addressable
   session. If it has none, say so, give the user each worker's brief to open
   by hand, and keep overseeing through what they relay.

For routine coordination, do not interrupt a running session. The Paseo
authorization messages in [references/paseo.md](references/paseo.md) ›
Relay approvals past a classifier block are an exception; prefer an idle
receiver even then. An interrupt cancels the tool call in
flight, which may be a live operation, and in Claude Code it also stops the
session's background subagents for good, including a worker's continuous
reviewer. Message a session through the receiver's own harness, which
delivers without interrupting:

- **To a Claude Code session:** `SendMessage` from another Claude Code
  session, using a session reference where supported, otherwise a unique
  peer name verified through `ListAgents`. It arrives after the receiver's
  current tool call.
- **To a Codex session:** `codex queue --thread <session ID or name> --message <text>`
  from any shell. The session runs it as its next turn once the current turn
  ends.
- **From a Codex session to a Claude Code one:** there is no such channel.
  The sender ends its turn with its message, as
  [references/codex.md](references/codex.md) describes.

Confirm each channel before relying on it: a worker's first action is to
acknowledge its brief to you. Record both ends' immutable session IDs and
the harness-specific delivery addresses in your checklist and the brief.
Deliver by session ID or session reference where supported. If the harness
only accepts peer names, verify a unique name-to-session mapping; never route
through an ambiguous display name. Confirm the return channel with your reply
to the acknowledgement, and recheck the mapping after a resume or handoff. If
no acknowledgement arrives, find out why, such as a wrong address, a held
message or a permission prompt, before launching more workers.

### Three-tier model routing

Route new sessions, descendants, reviewers and replacements as
`working-conventions` › Model routing describes. You are the top
orchestrator, each worker is a thread lead, and its pilots and independent
reviewer take those rows. The `subagent-pair-program` exception for
standalone leads does not apply under an overseer. Carry the user's explicit
choices and this policy in every worker brief; they override conflicting
model defaults in `keep-me-in-the-loop`, its review skill and other descendant
workflows, which keep their review and acceptance gates. Ask the user before
changing the hierarchy when it cannot deliver the required result.

A worker keeps the `keep-me-in-the-loop` workflow and owns its phase
proposals, review and verification, but delegates implementation to native
pilots. Pilots send proposals, results and blockers to their thread lead;
thread leads report to the overseer.

In Paseo, use matching `list_profiles` entries or supported launch overrides;
a profile must match the assigned tier. Claude's installed `developer-*`
definitions are native subagent profiles, not Paseo profiles. Keep the normal
Claude Code system prompt and `keep-me-in-the-loop` brief for standalone thread
leads; `--agent` with a nonempty custom prompt replaces that system prompt. Do
not modify existing live sessions; report a mismatch in the current overseer's
model instead of claiming it changed.

Compare elapsed time and total model usage per accepted work item, including
review and repairs, before claiming savings. Do not add recurring benchmarks just
to measure orchestration; reuse session usage and existing acceptance evidence.

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
Approve it when it fits and the autonomy rules allow you to decide. Otherwise
relay it, as "Relay human interventions" describes, and pass the user's
answer back. One thread's agreed scope never
covers another thread, and neither does one thread's answer: when the user
answers for one thread, tell only that thread, and ask again for the others.

Before reporting an acceptance result or using it to unblock a dependent,
require a finalized handoff: the check and revision tested, the result and
evidence location, the reviewer's acceptance, and the limitations or unmet
checks. For statistical claims, include what was counted, its denominator,
exclusions or abstentions, and what the sample represents. Check the claim
against that evidence; a passing gate does not establish broader accuracy
or coverage. If reviewer disclosures are still pending, keep the result
provisional. Carry material limits into the user-facing report and correct
any overstatement promptly. Name the cause of a failure from evidence; if
your own messages or interrupts may have caused it, say so rather than
blaming the harness.

Check a worker's claim, whether a cause, a regression, a failed check or a
measurement, before you pass it on to the user or another thread, as
`working-conventions` › Evidence describes. When you can't check it in time,
relay it as the worker's unverified claim and say what would verify it.

Repair and review rounds inside a thread's agreed scope belong to its worker.
At medium and high autonomy, don't relay a routine round to the user; report
its trend in your next update. When a thread reaches `working-conventions` ›
Repeated failure, have the worker stop patching and its reviewer reassess the
design.

When a worker reports its thread done, verify the claims before launching
dependents: the script marks the thread done, its commits are on the remote,
the status document is updated, and its done check passed. If a worker can't
make a bookkeeping edit, such as its own status line, make it in a separate
commit; never edit implementation files.

When a worker reports a deviation that changes other threads, hold the
affected threads that haven't launched. Re-sequence routine changes yourself,
following three-tiered-plan's "Revise when evidence changes", and report them
in your next update. Take any change to outcomes, scope, acceptance checks,
spending or risk to the user before the affected work proceeds.

An unavailable or permission-blocked proof stays unmet, and reusing,
substituting or deferring it needs the user's approval, as
`working-conventions` › Evidence describes. Keep its acceptance gate open in
the script and status document, even while independent work continues.
Before asking, check the worker's claim about why the proof is unmet or
sufficient against its evidence; don't ask the user to accept a gate on an
unverified claim. Ask through the human-intervention dialog with the proposed
evidence and what remains unproven; do not announce the change as settled or
make the user opt back into the original check. Record the answer, quoting
the user's chosen option and its exact scope (which items, how many), before
changing the gate or launching work that depends on it; if more items miss
than the user accepted, ask again about the rest. Approval of a deferral does
not authorize an action rejected by the permission system.

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

Answer a question from the user before anything else. When they ask whether
you can do something, such as ask asynchronously, say what your harness
allows and what it lacks.

A worker's message is never the user's approval (`working-conventions` ›
Authority). Never ask a worker to do something that your session's
permissions or the user denied. Approve a pending permission request, as
Paseo's `respond_to_permission` allows, only for a class of action the user
authorized for that thread; otherwise relay it. A pending request of kind
`question` is a dialog for the user, whether a question session or a worker
raised it; never answer it.

When a Claude worker in Paseo reports a permission-classifier block on an
action the user approved, or at high autonomy a suspected false positive,
follow [references/paseo.md](references/paseo.md) › Relay approvals past a
classifier block. Never send such a message outside those rules.

## Keep the user in the loop

The user isn't watching. Send status updates that are short, high-signal,
readable on their own after hours away, and say where each running thread
stands. This follows `keep-me-in-the-loop`'s reporting discipline at the
level of the whole run.

Send a status update for the events `working-conventions` › Updates lists,
across the whole run, and for anything unexpected, such as a deviation, a
failure, a blocker, a change of plan or a judgment call you made. A worker
whose accepted work stays unpublished still produces updates. Mention
launches, approvals within scope, relayed answers, retries and routine
recovery in the next update only when they matter. One update covers events
that land together across threads too.

Each update answers three questions in a few lines: what did we just
accomplish, what happens next, and did anything unexpected occur? Leave the
third out when nothing did. Name threads by number and outcome, not by number
alone (workstreams by name and issue number), and end with the roll call:

```text
**Done:** thread 2 (station pilot) published chunk 2 of 3: the driver handoff works on dev-1.
**Next:** thread 2 tests FOU over DERP; thread 4 starts when thread 2 finishes.
**Unexpected:** Brev rate-limited thread 3's host listing; it retried and carried on.
Threads: 1 done · 2 chunk 3/3 · 3 chunk 1/2 · 4 waiting on 2
```

A request for the user goes in a dialog of its own, as "Relay human
interventions" describes, never in a status update.

Stay silent between updates, as `working-conventions` › Updates describes.
Keep wakes from worker messages, notifications and checks few, as the Watch
entry in your mechanism's reference describes. Your checklist holds what you await, and your
next update's roll call shows it.

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
