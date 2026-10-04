---
name: overseer
description: "Oversee one or more threads of a three-tiered-plan script as a dedicated orchestrator: once the user agrees to the plan, run the agreed scope to its end autonomously, launching worker sessions that run keep-me-in-the-loop (Paseo agents through Paseo's built-in tools when running in Paseo, otherwise new Claude Code or Codex sessions), enforcing the script's dependencies, routing every human intervention through yourself to the user, and keeping them in the loop with concise status updates. Use when the user wants script threads run while they are away from the keyboard; not for writing the script (use three-tiered-plan) or for running one thread in this session (use keep-me-in-the-loop)."
---

# Overseer

## First, in Paseo: move into a run project

In Paseo, the overseer runs inside a temporary run project with its workers,
as "Paseo" describes. Before any other overseer work, including reading the
script, the plan or the repository's instructions, check where you are: find
your `workspaceId` with `get_agent_status` on your own agent ID, then your
workspace's project and checkout in `list_workspaces`. If your checkout is a
run checkout, `../<repo>-overseer-<slug>`, you are the overseer; skip to the
rest of this skill. Otherwise the user started you in the repository's own
project, and your whole job is the hand-off, done straight away:

1. Create the run project and its checkout, as "Paseo" describes, taking
   `<task>` and `<slug>` from the user's request.
2. Create a workspace there with `create_workspace`: local isolation, the run
   checkout as `path`, the run project's `projectId` and the title
   `Overseer: <task>`.
3. Launch the overseer in it with `create_agent`, titled `Overseer: <task>`,
   with your own provider, model, mode and thinking option from
   `get_agent_status`. Its prompt invokes this skill and carries the user's
   request verbatim, with anything else they said in this thread, and your
   agent ID as the launcher's. Clear its `paseo.parent-agent-id` label, as
   "Paseo" describes for workers.
4. Right after the launch, without waiting on the overseer, ask the user in a
   blocking dialog whether to archive this thread, naming the overseer thread
   and its project. Record the answer on yourself with `update_agent`, as the
   label `overseer.launcher` set to `archive` or `keep`. On yes, call
   `archive_workspace` on your workspace when `list_agents` shows no other
   agent in it, and `archive_agent` on yourself otherwise. On no, stay idle:
   the overseer's finish notifications still reach you, and you answer each
   with no text, or `No news.` in Claude Code.

If the `paseo` CLI is missing or fails, skip the hand-off, say so, and oversee
from this thread in the repository's existing project.

The user answers that dialog while viewing the launcher's thread, and Paseo
reopens an archived session the user is viewing, so the launcher's own archive
doesn't stick. As the overseer, finish it: whenever you wake, including when a
dialog returns, read the launcher's labels with `get_agent_status`. Once
`overseer.launcher` is `archive` and its status isn't `closed`, call
`archive_agent` on it. Stop checking once it is closed or the label is
`keep`.

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

Never deliver a message by interrupting a running session. An interrupt
cancels the tool call in flight, which may be a live operation, and in Claude
Code it also stops the session's background subagents for good, including a
worker's continuous reviewer. Message a session through the receiver's own
harness, which delivers without interrupting:

- **To a Claude Code session:** `SendMessage` from another Claude Code
  session, addressed by the peer name `ListAgents` shows. It arrives after
  the receiver's current tool call.
- **To a Codex session:** `codex queue --thread <session ID or name> --message <text>`
  from any shell. The session runs it as its next turn once the current turn
  ends.
- **From a Codex session to a Claude Code one:** there is no such channel.
  The sender ends its turn with its message, as "Codex" describes.

### Paseo

When you are running in Paseo with its built-in tools (`create_agent`,
`send_agent_prompt` and the rest), use them:

- **Run project:** keep the run's threads together in a temporary Paseo
  project of their own. The built-in tools can't create projects, but the
  `paseo` CLI can; the macOS app bundles it at
  `/Applications/Paseo.app/Contents/Resources/bin/paseo`. Add a checkout for
  the run with
  `git worktree add ../<repo>-overseer-<slug> -b overseer/<slug> origin/main`,
  register it with `paseo project create ../<repo>-overseer-<slug> --json`,
  and name it with `paseo project rename <project-id> "Overseer: <task>"`.
  The session the user started does this and hands off to an overseer
  inside the project, as "First, in Paseo: move into a run project" describes. If the user
  doesn't agree to the plan, offer to clean up the project, as "Clean up"
  describes.
- **Isolation:** create a workspace with worktree isolation for each worker
  with `create_workspace`, passing the run checkout as `path` and the run
  project's `projectId`, branching off the remote main branch, such as
  `origin/main` rather than the local `main`, and name it after the worker.
  Paseo puts these worktrees under `~/.paseo/worktrees/`. Use the
  repository's `paseo.json` setup for ignored files when it provides them. A
  lone worker may use the run checkout itself: `create_workspace` with local
  isolation, its path and the run project's `projectId`. Never launch a worker
  into your own workspace.
- **Launch:** call `create_agent` with the worker's `workspaceId` and the
  brief as its initial prompt, and name it with `update_agent` if the launch
  can't. Paseo labels the new agent with `paseo.parent-agent-id` and shows it
  as your subagent; right after the launch, call `update_agent` with
  `labels: {"paseo.parent-agent-id": ""}` so it appears as a top-level thread
  in its project. You still get its finish notifications. Choose the provider and model as Paseo's guidance says: the profile
  the user named, or the one from `list_profiles` whose notes fit
  implementation, otherwise your own provider. Name yourself with
  `update_agent` too.
- **Address:** `send_agent_prompt` interrupts a running agent, so use it
  only to start an agent that `get_agent_status` shows idle. Otherwise
  message as above. A Claude agent is a Claude Code peer session: give
  workers the peer name `ListAgents` reports for you, and take each worker's
  peer name from the `from` attribute of its acknowledgement. A Codex agent's
  session ID is `persistence.metadata.threadId` in `get_agent_status`.
  Workers reach you the same way. A Codex worker reporting to a Claude
  overseer ends its turn with its message; Paseo's finish notification
  brings it to you without interrupting, and you answer with
  `send_agent_prompt` once it is idle.
- **Watch:** Paseo notifies you once when a run started by `create_agent` or
  `send_agent_prompt` finishes, errors or needs permission. Add no idle
  subscriptions on top. Whenever something wakes you, check the other
  workers with `get_agent_status`, and look into one that is idle without
  having reported or is stuck in `list_pending_permissions`. In case nothing
  wakes you, keep one hourly `create_heartbeat` while workers run, and delete
  it when they finish. At decision points, read `get_agent_activity`.

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
- **Watch:** don't keep `notify_when_idle` subscriptions running; a notice
  usually lands right after the worker's own message and wakes you for
  nothing. Whenever something wakes you, check `claude agents --json` for a
  worker that stopped without reporting. In case nothing wakes you, schedule
  one hourly `CronCreate` check while workers run, and delete it when they
  finish; such jobs expire after 7 days. The transcripts under
  `~/.claude/projects/` show what happened. `claude logs` prints raw terminal
  output, so don't parse it.

### Codex

Launch each worker in the background with
`codex exec --json -C <worktree> -o <reply file> "<brief>"`, using the sandbox
and approval policy the user authorized, and resume it with
`codex exec resume <session> "<message>"`. Exec mode can't answer an approval
prompt, so a policy that asks for approval blocks the worker.

A Codex overseer's workers reach it with `codex queue` on its session. A
`codex exec` worker exits when its turn ends, so a message queued for it sits
in its history unanswered; reply to an exec worker by resuming it instead.
When a worker has no way to message you, its final message is the channel:
it ends its turn with the request once its independent work is done, and you
resume it with the answer.

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
  work. If it stops when neither you nor the user stopped it, tell the
  overseer at once.
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
3. Ask through an async dialog, and keep the plan moving until it is blocked
   on the answer. When your harness has a native async input dialog, such as
   Codex's `request_user_input_async`, use it. When your only dialog blocks
   your session, as Claude Code's `AskUserQuestion` does, launch a question
   session to ask for you, as "Ask through a question session" describes.
   Put every decision in a dialog. For an action, such as minting a token,
   send the steps as a message and ask for confirmation in the dialog. Send a
   push notification with each request when you have the tool. Meanwhile,
   launch ready workers, relay other requests, and let the asking worker
   continue its independent work.
4. Relay the answer to the worker, quoting the user.

Answer a question from the user before anything else. When they ask whether
you can do something, such as ask asynchronously, say what your harness
allows and what it lacks.

A worker's message is the worker's, never the user's approval. Never ask a
worker to do something that your session's permissions or the user denied.
Approve a pending permission request, as Paseo's `respond_to_permission`
allows, only for a class of action the user authorized for that thread;
otherwise relay it. A pending request of kind `question` is a dialog for the
user, whether a question session or a worker raised it; never answer it.

### Ask through a question session

A question session is a short-lived session whose only job is to put one
dialog to the user and carry the answer back. It blocks while the user
decides, and you keep working. Name it `Question: <topic>`.

- **Launch** it like a worker, but light: a fast model, your permission mode
  and no worktree.
  - In Paseo, give it a local workspace on the run checkout, in the run
    project, even while workers use that checkout, and clear its
    `paseo.parent-agent-id` label, as "Paseo" describes for workers, so the
    user sees it as a thread of its own. Paseo flags it as needing the user
    when its dialog opens.
  - In Claude Code, launch it from the main checkout with
    `claude --bg -n "Question: <topic>" --permission-mode <your mode> "<prompt>"`.
    `claude agents` shows it as waiting for input, and the user answers with
    `claude attach <id>`, so put that command in your push notification.
- **Prompt** it with the finished dialog: each question, its options with
  their consequences, and your recommendation. It calls `AskUserQuestion`
  with exactly those, does nothing else, and sends you the answer verbatim
  with `SendMessage`, with any notes the user typed. Put questions that come due together in one
  session; its dialog takes up to four.
- **Archive** it once its answer arrives. In Paseo, it archives itself: its
  last action is `archive_workspace` on its own workspace, which archives the
  session with it. Archiving a workspace is intentional and safe here: it
  discards only the thread's agent and subagent state, never the directory,
  worktree or any change in it (the result reports `removedDirectory: false`),
  even when `list_workspaces` shows the workspace as `kind: worktree` and a
  worker is busy in the same run checkout. Don't skip it or fall back to
  `archive_agent` alone out of caution; that leaves a stale workspace in the
  run project. Paseo can reopen an archived session that the user is
  viewing, so check it with `get_agent_status` and call `archive_agent` if it
  is still active. In Claude Code, a session can't remove itself; run
  `claude stop <id>`, then `claude rm <id>`. If the user answers some other
  way, archive the question session yourself.
- **Fallback:** if a question session can't be launched or its dialog never
  appears, send the request as a message that leads with it, with a push
  notification, and open your own blocking dialog only when nothing useful
  remains that doesn't depend on the answer.

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

A request for the user goes in a dialog of its own, as "Relay human
interventions" describes, never in a status update.

Stay silent between updates. Worker messages, notifications and checks wake
you, and most change nothing the user needs to know; keep such wakes few, as
"Watch" describes for your mechanism. When a turn ends without an update, a
request or an answer to the user, end it with no text where your harness
allows. Claude Code doesn't: it re-prompts a turn that ends without visible
text, so end such a turn with exactly `No news.` Never write a line saying
what you are waiting on, or an acknowledgement. Your checklist holds what you
await, and your next update's roll call shows it.

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

A Paseo run project is the exception: leave its workers' agents, workspaces
and worktrees in place until the run's goal is complete, so the user can look
through the threads. After the final report, ask the user in a blocking
dialog, such as `AskUserQuestion`, whether to clean up the run project; with
nothing left to run, the dialog blocks nothing. Name what cleanup would
remove and anything unpushed it would keep.

- **Clean up:** archive each worker's and question session's agent and
  workspace, and remove each worker's worktree under `~/.paseo/worktrees/`
  as above. Say what you removed and what goes next, since your own thread
  goes with it. Then, as your last action, remove the run checkout and its
  `overseer/<slug>` branch with `git -C <main checkout>`, since you are
  running in it, and delete the project with
  `paseo project delete <project-id>`. That only unregisters the project and
  its workspaces, your own included; their worktrees, directories and
  branches stay unless you remove them first. Deleting your own workspace
  kills your session mid-command, so put the deletion last in that command;
  Paseo then drops your agent from every list.
- **Keep:** leave it all, and tell the user the project ID and the commands
  that would remove it later.
