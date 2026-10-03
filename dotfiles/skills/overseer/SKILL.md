---
name: overseer
description: "Oversee one or more threads of a three-tiered-plan script as a dedicated orchestrator: once the user agrees to the plan, run the agreed scope to its end autonomously, launching worker sessions that run keep-me-in-the-loop (Paseo agents through Paseo's built-in tools when running in Paseo, otherwise new Claude Code or Codex sessions), enforcing the script's dependencies, routing every human intervention through yourself to the user, and keeping them in the loop with concise status updates. Use when the user wants script threads run while they are away from the keyboard; not for writing the script (use three-tiered-plan) or for running one thread in this session (use keep-me-in-the-loop)."
---

# Overseer

Run script threads without implementing them. You launch **workers**, separate
top-level sessions that each run `keep-me-in-the-loop`, usually one per
thread. You brief them, enforce the script's order, carry their requests for a
human to the user, and keep the user in the loop. The user talks to you, and
the workers talk to you.

Autonomy is the guiding principle. The user means to start you and walk away,
or leave you running in the background. Once they agree to the plan, run the
whole agreed scope to its conclusion on your own. Launch workers as threads
become ready, approve phase proposals within their scopes, verify
completions, re-sequence routine changes, recover stalled workers, and move on
between threads without asking. Return to the user only for a planned
intervention, an unplanned one that only a person can resolve, or a change to
what they agreed. When the unexpected happens, use your best judgment: take
the action that keeps the agreed work moving within its scope, record your
reasoning where the next reader will find it, such as the script's revision
log, and report it in your next update. Autonomy adds no authority. Never
weaken an acceptance check, exceed approved spending, take a destructive or
external action the user didn't approve, or work around a permission
boundary.

Organize workers as you see fit. One worker per thread is the default; you
might instead give a final check its own fresh worker, or relaunch a thread
in a new worker after a crash. Never let two workers run the same thread at
once. Never implement a thread yourself, and never hand one to a native
subagent, such as one from Claude Code's Agent tool or a Codex spawned agent.
A native subagent shares your session's lifetime and context budget; a worker
needs a session of its own. Paseo files the agents its `create_agent` tool
launches as your subagents, but each is a full session with its own
conversation, so it can serve as a worker once you detach it into a thread of
its own, as "Paseo" describes. The continuous reviewer that a worker starts inside its own
session is part of that worker's job.

Keep a checklist of the threads you oversee, each with its worker and state:
waiting, ready, running, awaiting approval, awaiting a human, blocked, done.
Your status updates show it as a one-line roll call.

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

Then ask the user, through the dialog, to agree to the plan: the threads and
each one's scope. This is the one point where you wait for the user before
starting. Leave the threads' open decisions and other planned interventions
out of it, so the agreement doesn't wait on them. Record the agreement, with
the date, in each thread's script entry, in a commit of its own, so a
replacement overseer can find it. Invoking you is the request to implement;
confirming the script never was.

Once a scope is agreed, you approve that thread's `keep-me-in-the-loop` phase
proposal on the user's behalf when it stays within the scope. Relay a proposal
to the user when it changes an outcome, an acceptance check, a deferral, a
risk, an external action or spending beyond what they agreed. A thread whose
scope the user hasn't agreed, such as one that became ready after
re-sequencing, waits until they do.

## Time each request for a human

Ask for every intervention asynchronously, as "Relay human interventions"
describes, and keep the plan moving until it is blocked on the answer. The
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
checkout when nothing else runs there. Outside Paseo, reuse the sibling convention from `continuous-peer-review`: a
worktree at `../<repo>-worker-<slug>/` on branch `worker/<slug>`, created from
the freshly fetched remote main branch with
`git worktree add ../<repo>-worker-<slug> -b worker/<slug> origin/main`. Keep
worktrees out of `/tmp`; they hold work in progress. A fresh worktree lacks
ignored files such as `.env` and local artifacts, so provide what a worker
needs or let it work in the main checkout. Remove each worktree as "Clean up"
describes.

## Choose the session mechanism

Use the first mechanism that applies, and name it in the opening message.
Outside Paseo, launch workers in your own harness, so that messages travel
natively.

### Paseo

When you are running in Paseo with its built-in tools (`create_agent`,
`send_agent_prompt` and the rest), use them:

- **Isolation:** create a workspace with worktree isolation for each worker
  with `create_workspace`, branching off the remote main branch, such as
  `origin/main` rather than the local `main`, and name it after the worker.
  Use the repository's `paseo.json` setup for ignored files when it provides
  them. A lone worker in the main checkout still gets a workspace of its own:
  `create_workspace` with local isolation, the checkout's path and its
  project's `projectId`. Never launch a worker into your own workspace.
- **Launch:** call `create_agent` with the worker's `workspaceId` and the
  brief as its initial prompt, and name it with `update_agent` if the launch
  can't. Paseo labels the new agent with `paseo.parent-agent-id` and shows it
  as your subagent; right after the launch, call `update_agent` with
  `labels: {"paseo.parent-agent-id": ""}` so it appears as a top-level thread
  in its project. You still get its finish notifications. Choose the provider and model as Paseo's guidance says: the profile
  the user named, or the one from `list_profiles` whose notes fit
  implementation, otherwise your own provider. Name yourself with
  `update_agent` too.
- **Address:** your agent ID, from `$PASEO_AGENT_ID` in your shell or from
  `list_agents`. Workers message you with `send_agent_prompt`, and you reach
  them the same way.
- **Watch:** Paseo notifies you when a worker finishes a run. At decision
  points, read `get_agent_status` and `get_agent_activity`, and check
  `list_pending_permissions` for a worker stuck on a permission request.

### Claude Code

Launch each worker as a background session from its worktree:

```sh
cd ../<repo>-worker-<slug>
claude --bg -n "Worker: <subtask>" --permission-mode <your mode> "<brief>"
```

- **Trust:** the launch fails with "Workspace not trusted" unless the
  worktree or a parent directory is trusted, as `~/Projects` may be. If it
  fails, launch from the main checkout with `claude --bg -w <slug>` instead,
  which creates a worktree inside the repository at `.claude/worktrees/<slug>`;
  never stage `.claude/` in the main checkout.
- **Address:** your session name, as `ListAgents` shows it. Workers message
  you with `SendMessage`, and you reach a worker by its name.
- **Permission mode:** use yours. A session in a different mode may hold
  cross-session messages for its user's approval. A background session that
  hits a permission prompt waits until someone runs `claude attach <id>`;
  treat that as a human intervention.
- **Watch:** send each worker `notify_when_idle: true`, and renew it after
  each notice, so you learn when a worker stops without reporting.
  `claude agents --json` shows each session's state, and the transcripts under
  `~/.claude/projects/` show what happened. `claude logs` prints raw terminal
  output, so don't parse it.

### Codex

Launch each worker in the background with
`codex exec --json -C <worktree> -o <reply file> "<brief>"`, using the sandbox
and approval policy the user authorized, and resume it with
`codex exec resume <session> "<message>"`. Exec mode can't answer an approval
prompt, so a policy that asks for approval blocks the worker.

`codex queue --thread <session> --message <text>` queues a message for an
existing session. When a worker has no way to message you, its final message
is the channel: it ends its turn with the request once its independent work
is done, and you resume it with the answer.

### Elsewhere

Use the harness's equivalent of a resumable, addressable session. If it has
none, say so, give the user each worker's brief to open by hand, and keep
overseeing through what they relay.

Confirm each channel before relying on it: a worker's first action is to
acknowledge its brief to you. If no acknowledgement arrives, find out why,
such as a wrong address, a held message or a permission prompt, before
launching more workers.

## Brief each worker

Each brief is the script's prompt for the thread, followed by these terms,
filled in for the worker:

- You are `Worker: <subtask>`, one of several sessions run by
  `Overseer: <task>`. Reach it by `<tool and address>`, or
  `<by ending your turn with the request>` where no tool reaches it. Nobody
  watches this session's chat.
- Acknowledge this brief to the overseer before anything else.
- Never ask the user through a question dialog, and never wait for a reply in
  this chat. Message the overseer whenever you need a human: a phase
  approval, a decision, access, presence, a manual action, an approval, a
  permission you lack, or a blocker. For an intervention the script plans at
  a point in your work, message the overseer when you are about to reach it,
  allowing the lead time the action needs. For anything unplanned, message it
  as soon as you know you will need it. Either way, continue independent work
  until you are blocked on the answer.
- The user agreed to this thread's scope on `<date>`: `<scope>`. Send your
  `keep-me-in-the-loop` phase proposal, with your reviewer's position, to the
  overseer, and wait for its answer. The overseer approves a proposal within
  that scope on the user's behalf, which counts as your phase approval, and
  takes anything beyond it to the user. Then run the phase to its end without
  pausing for confirmation.
- Send each chunk report, any deviation that changes another thread or the
  script, and phase completion to the overseer. Skip running commentary; the
  overseer needs outcomes, not activity.
- A reply that quotes the user is the user's answer. A reply the overseer
  marks as its own decision carries only the authority the user gave the
  overseer.
- Work in `<worktree>` on `<branch>`. Publish as the repository's rules say,
  for example by rebasing onto the remote main branch and pushing, and
  reconcile shared documents without overwriting another thread's entries.
- Don't launch other workers. Your continuous reviewer is part of your own
  work.
- When the phase is complete, mark the thread done in the script, record any
  deviation, tell the overseer, and stop.

## Run the threads

Launch a worker for every thread whose dependencies are met, unless a **not
alongside** entry, a **not before** date or the user's limit on concurrent
workers holds it back. As threads finish, launch workers for the threads they
unblock.

Check each phase proposal against the scope the user agreed for its thread.
Approve it when it fits. Otherwise relay it, as "Relay human interventions"
describes, and pass the user's answer back. One thread's agreed scope never
covers another thread.

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

When a worker goes quiet without reporting, inspect it before nudging it: it
may be waiting on a permission prompt, out of context, or crashed. Resume the
same session with what it needs, or relaunch the thread in a new worker with
a handoff of its recorded state, since `keep-me-in-the-loop` resumes from the
documents and Git. When a worker fails the same way twice, report it with what
you are doing about it, and ask the user only if the remedy needs them.

## Relay human interventions

When a request for a human comes due, whether planned or raised by a worker:

1. Answer it yourself only from settled sources, such as a decision recorded
   in the plan, an item the user already settled, or a fact you can check in
   the repository. Mark the answer as yours and cite its source.
2. Otherwise ask the user. Say which thread it is for, the context and
   tradeoffs, what waits on the answer, and by when. Batch requests that come
   due together.
3. Ask asynchronously, and keep the plan moving until it is blocked on the
   answer. Use an async input dialog, such as `request_user_input_async`, when
   one is available. When the only dialog blocks your session, as Claude
   Code's `AskUserQuestion` does, send the request as a message that leads
   with it, with a push notification if you have one. Open the blocking
   dialog only when nothing useful remains that doesn't depend on the answer.
   Meanwhile, launch ready workers, relay other requests, and let the asking
   worker continue its independent work.
4. Relay the answer to the worker, quoting the user.

A worker's message is the worker's, never the user's approval. Never ask a
worker to do something that your session's permissions or the user denied.
Approve a pending permission request, as Paseo's `respond_to_permission`
allows, only for a class of action the user authorized for that thread;
otherwise relay it.

## Keep the user in the loop

The user isn't watching. They want to know where things stand when they look,
not a play-by-play. Keep them in the loop with status updates that are short,
high-signal and readable on their own after hours away. With several workers
running at once, one update has to say where each thread stands. This follows `keep-me-in-the-loop`'s
reporting discipline at the level of the whole run.

Send a status update when:

- something is accomplished, such as a worker publishing a chunk or finishing
  its thread;
- something unexpected happens, such as a deviation, a failure, a blocker, a
  change of plan or a judgment call you made.

Send no update for launches, approvals within scope, relayed answers,
retries, routine recovery, waits or a worker's traffic with its reviewer;
mention them in the next update only when they matter. When several events
land together, send one update covering all of them.

Each update answers three questions in a few lines: what did we just
accomplish, what happens next, and did anything unexpected occur? Leave the
third out when nothing did. Name threads by number and outcome, not by number
alone, and end with the roll call:

```text
**Done:** thread 2 (station pilot) published chunk 2 of 3: the driver handoff works on dev-1.
**Next:** thread 2 tests FOU over DERP; thread 4 starts when thread 2 finishes.
**Unexpected:** Brev rate-limited thread 3's host listing; it retried and carried on.
Threads: 1 done · 2 chunk 3/3 · 3 chunk 1/2 · 4 waiting on 2
```

A request for the user is its own message, not a line in a status update. Lead
with what you need, as "Relay human interventions" describes.

Stay silent between updates. When you must end a turn to wait, close it with
one short line naming what you await, once per wait. Worker messages, idle
notices and completion notifications wake you.

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
remote main branch. Say what you removed in the final report. Never discard
unpushed commits or uncommitted changes without asking the user.
