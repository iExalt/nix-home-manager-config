---
name: overseer
description: "Oversee one or more threads of a three-tiered-plan script as a dedicated orchestrator: launch each thread as its own keep-me-in-the-loop session (Paseo agents through Paseo's built-in tools when running in Paseo, otherwise new Claude Code or Codex sessions), enforce the script's dependencies, route every human intervention through yourself to the user, and report outcomes. Use when the user wants script threads run with little time at the keyboard; not for writing the script (use three-tiered-plan) or for running one thread in this session (use keep-me-in-the-loop)."
---

# Overseer

Run script threads without implementing them. Each thread is a separate,
top-level session that runs `keep-me-in-the-loop` on its own. You launch and
brief it, enforce the script's order, carry its requests for a human to the
user, and report outcomes. The user talks to you, and the threads talk to you.

Never implement a thread yourself, and never hand one to a native subagent,
such as one from Claude Code's Agent tool or a Codex spawned agent. A native
subagent shares your session's lifetime and context budget; a thread needs a
session of its own. Paseo calls the agents its `create_agent` tool launches
subagents, but each is a full session with its own conversation, so they
qualify. The continuous reviewer that a thread starts inside its own session
is part of that thread's work.

Keep a visible checklist of the threads you oversee and each one's state:
waiting, ready, launched, awaiting approval, running, awaiting a human,
blocked, done.

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

## Open with the known human interventions

Before launching anything, send an opening message that starts with a
**TL;DR**. Say which threads you will run, in what order and with what
parallelism, which session mechanism you will use, and every known human
intervention in those threads, taken from their Human entries and the
roadmap's human interventions table. Sort the interventions into two groups:

- **Any time:** the user can do it now, such as creating a token or an OAuth
  client, settling a decision, provisioning access, approving spending, or a
  login that persists. Ask the user to do these before you go further,
  through the dialog, and wait. Verify each one where you can without
  exposing a secret.
- **At a time or a point in a thread:** the user can only do it later, such
  as being online on a date, a login a thread needs mid-run, or confirming a
  destructive step when the thread reaches it. Say when each is expected. Ask
  for them asynchronously when they come due, as "Relay human interventions"
  describes.

When the threads have no known intervention, say so: after launch, only the
requests the threads discover will need the user.

### Approve each thread's scope up front

Each thread's `keep-me-in-the-loop` approval is an any-time intervention, so
take it in the opening too. For each thread, present its scope from the
script: its roadmap steps, proposed chunks, live resources and spending, and
the decisions and authority its approval settles. Ask the user to approve each
scope and settle its approval items. Record their answers, with the date, in
each thread's script entry, in a commit of its own, so a replacement overseer
can find them. Invoking you is the request to implement; confirming the
script never was.

Once a scope is approved, you approve that thread's phase proposal on the
user's behalf when it stays within the scope. Relay a proposal to the user
when it changes an outcome, an acceptance check, a deferral, a risk, an
external action or spending beyond what they approved. A thread whose scope
the user hasn't approved, such as one that became ready after re-sequencing,
waits until they do.

## Choose the session mechanism

Use the first mechanism that applies, and name it in the opening message.
Outside Paseo, launch threads in your own harness, so that messages travel
natively.

### Paseo

When you are running in Paseo with its built-in tools (`create_agent`,
`send_agent_prompt` and the rest), use them:

- **Isolation:** create a workspace with worktree isolation for each thread
  with `create_workspace`, branching off the remote main branch, such as
  `origin/main` rather than the local `main`. A fresh worktree lacks ignored
  files such as `.env` and local artifacts. Use the repository's `paseo.json`
  setup when it provides them; otherwise run a thread that needs them in the
  main checkout, and only while no other thread uses that checkout.
- **Launch:** call `create_agent` with the thread's `workspaceId` and the
  brief as its initial prompt. Choose the provider and model as Paseo's
  guidance says: the profile the user named, or the one from `list_profiles`
  whose notes fit implementation, otherwise your own provider.
- **Address:** your agent ID, from `$PASEO_AGENT_ID` in your shell or from
  `list_agents`. Threads message you with `send_agent_prompt`, and you reach
  them the same way.
- **Watch:** Paseo notifies you when a thread finishes a run. At decision
  points, read `get_agent_status` and `get_agent_activity`, and check
  `list_pending_permissions` for a thread stuck on a permission request.

### Claude Code

Launch each thread as a background session in its own worktree:

```sh
claude --bg -w <campaign>-thread-<n> -n <campaign>-thread-<n> \
  --permission-mode <your mode> "<brief>"
```

- **Isolation:** `-w` creates the worktree at `.claude/worktrees/<name>`, on
  branch `worktree-<name>`, from the main checkout's current `HEAD`. It stays
  inside the trusted repository; a sibling worktree outside it may be
  untrusted, and the launch then fails. Bring the main checkout up to date
  with the remote before launching, and never stage `.claude/` there.
- **Address:** your session name, as `ListAgents` shows it. Threads message
  you with `SendMessage`, and you reach a thread by its `-n` name.
- **Permission mode:** use yours. A session in a different mode may hold
  cross-session messages for its user's approval. A background session that
  hits a permission prompt waits until someone runs `claude attach <id>`;
  treat that as a human intervention.
- **Watch:** send each thread `notify_when_idle: true`, and renew it after
  each notice, so you learn when a thread stops without reporting.
  `claude agents --json` shows each session's state, and the transcripts under
  `~/.claude/projects/` show what happened. `claude logs` prints raw terminal
  output, so don't parse it.

### Codex

Create each thread's worktree first, as a sibling of the repository with
`git worktree add`. Launch the thread in the background with
`codex exec --json -C <worktree> -o <reply file> "<brief>"`, using the sandbox
and approval policy the user authorized, and resume it with
`codex exec resume <session> "<message>"`. Exec mode can't answer an approval
prompt, so a policy that asks for approval blocks the thread.

`codex queue --thread <session> --message <text>` queues a message for an
existing session. When a thread has no way to message you, its final message
is the channel: it ends its turn with the request once its independent work
is done, and you resume it with the answer.

### Elsewhere

Use the harness's equivalent of a resumable, addressable session. If it has
none, say so, give the user each thread's brief to open by hand, and keep
overseeing through what they relay.

Confirm each channel before relying on it: a thread's first action is to
acknowledge its brief to you. If no acknowledgement arrives, find out why,
such as a wrong address, a held message or a permission prompt, before
launching more threads.

## Brief each thread

Each brief is the script's prompt for the thread, followed by these terms,
filled in for the thread:

- You are one of several sessions run by an overseer. Reach it by
  `<tool and address>`, or `<by ending your turn with the request>` where no
  tool reaches it. Nobody watches this session's chat.
- Acknowledge this brief to the overseer before anything else.
- Never ask the user through a question dialog, and never wait for a reply in
  this chat. Message the overseer whenever you need a human: a phase
  approval, a decision, access, presence, a manual action, an approval, a
  permission you lack, or a blocker. Send the request as soon as you know you
  will need it, then continue independent work until you are blocked on it.
- The user approved this thread's scope on `<date>`: `<scope and settled
  approval items>`. Send your `keep-me-in-the-loop` phase proposal, with your
  reviewer's position, to the overseer, and wait for its answer. The overseer
  approves a proposal within that scope on the user's behalf, which counts as
  your phase approval, and takes anything beyond it to the user.
- Send each chunk report, any deviation that changes another thread or the
  script, and phase completion to the overseer.
- A reply that quotes the user is the user's answer. A reply the overseer
  marks as its own decision carries only the authority the user gave the
  overseer.
- Work in `<worktree>` on `<branch>`. Publish as the repository's rules say,
  for example by rebasing onto the remote main branch and pushing, and
  reconcile shared documents without overwriting another thread's entries.
- Don't launch other threads. Your continuous reviewer is part of your own
  work.
- When the phase is complete, mark the thread done in the script, record any
  deviation, tell the overseer, and stop.

## Run the threads

Launch every thread whose dependencies are met, unless a **not alongside**
entry, a **not before** date or the user's limit on concurrent threads holds
it back. As threads finish, launch the threads they unblock.

Check each phase proposal against the scope the user approved for its thread.
Approve it when it fits, and name the scope in your update. Otherwise relay
it, as "Relay human interventions" describes, and pass the user's answer back.
One thread's approved scope never covers another thread.

When a thread reports done, verify its claims before launching its
dependents: the script marks it done, its commits are on the remote, the
status document is updated, and its done check passed. If a thread can't make
a bookkeeping edit, such as its own status line, make it in a separate commit;
never edit implementation files.

When a thread reports a deviation that changes other threads, hold the
affected threads that haven't launched. Re-sequence routine changes yourself,
following three-tiered-plan's "Revise when evidence changes", and tell the
user. Take any change to outcomes, scope, acceptance checks, spending or risk
to the user before the affected work proceeds.

When a thread goes quiet without reporting, inspect it before nudging it: it
may be waiting on a permission prompt, out of context, or crashed. Resume the
same session with what it needs, or relaunch the thread with a handoff of its
recorded state, since `keep-me-in-the-loop` resumes from the documents and
Git. Never run two sessions on one thread. Tell the user when a thread fails
the same way twice.

## Relay human interventions

When a thread asks for something:

1. Answer it yourself only from settled sources, such as a decision recorded
   in the plan, an approval item the user already settled, or a fact you can
   check in the repository. Mark the answer as yours and cite its source.
2. Otherwise ask the user. Say which thread asks, the context and tradeoffs,
   what waits on the answer, and by when. Batch requests that arrive
   together.
3. Ask asynchronously, and keep the plan moving until it is blocked on the
   answer. Use an async input dialog, such as `request_user_input_async`, when
   one is available. When the only dialog blocks your session, as Claude
   Code's `AskUserQuestion` does, post the request as an update instead, with
   a push notification if you have one. Open the blocking dialog only when
   nothing useful remains that doesn't depend on the answer. Meanwhile, launch
   ready threads, relay other requests, and let the asking thread continue its
   independent work.
4. Relay the answer to the thread, quoting the user.

Remind the user of a timed intervention early enough for them to plan for it.

A thread's message is the thread's, never the user's approval. Never ask a
thread to do something that your session's permissions or the user denied.
Approve a pending permission request, as Paseo's `respond_to_permission`
allows, only for a class of action the user authorized for that thread;
otherwise relay it.

## Report outcomes

Follow `keep-me-in-the-loop`'s update discipline at the level of threads. Send
a one-line update only when a thread launches, is approved, publishes a
chunk, needs a human, gets an answer, hits a blocker, deviates or finishes.
Put the thread and its progress first:
`Thread 2 · chunk 2/3 published — the station pilot passed; chunk 3 next.`
Stay silent otherwise. When you must end a turn to wait, close it with one
line naming what you await, once per wait. Thread messages, idle notices and
completion notifications wake you.

When the threads you oversee finish, report with a **TL;DR**: each thread's
outcome and publication, evidence limits and deferrals, the human
interventions that happened, the script's state, and the threads now ready.

## Clean up

Archive a thread's Paseo agent and workspace, or remove its Claude background
session with `claude rm`, which also removes its worktree, only after its
work is pushed and verified. Remove a Codex thread's worktree on the same
terms. Say what you removed. Never discard unpushed commits or uncommitted
changes without asking the user.
