---
name: overseer
description: "Oversee one or more threads of a three-tiered-plan script, or workstreams in the repository's tracker, as a dedicated orchestrator: once the user agrees to the plan, run the agreed scope to its end autonomously, launching worker sessions that run keep-me-in-the-loop (Paseo agents through Paseo's built-in tools when running in Paseo, otherwise new Claude Code or Codex sessions), enforcing the script's dependencies, routing every human intervention through yourself to the user, and keeping them in the loop with concise status updates. Use when the user wants script threads run while they are away from the keyboard; not for writing the script (use three-tiered-plan) or for running one thread in this session (use keep-me-in-the-loop)."
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

Run the whole agreed scope to its conclusion, using the autonomy level below
to decide when to involve the user. Record consequential judgment calls and
their reasoning in the script's revision log and report them in the next
update. Never weaken an acceptance check, exceed approved spending, take a
destructive or external action outside the user's authorization, or work
around a permission boundary.

## Choose autonomy and establish authority

Use **medium** when the user doesn't specify a level. State the level in the
opening plan and record it in the script and worker briefs. Autonomy governs
the overseer's decisions; workers still route requests through the overseer.

| Level | When to involve the user |
| --- | --- |
| **Low** | Invite the user into consequential choices within scope: meaningful implementation tradeoffs, phase direction, re-sequencing, and recovery options. Recommend an option before proceeding with the affected work. Handle routine execution and settled decisions yourself. |
| **Medium (default)** | Use best judgment, preserving this skill's usual behavior: approve phases within scope, choose routine implementation details, re-sequence work, and recover stalled workers. Consult when a tradeoff or uncertainty materially affects what the user agreed. |
| **High** | Minimize interruptions. Decide within scope, approve phases, and resolve recoverable issues yourself, reporting meaningful decisions afterward. Interrupt only for the mandatory consultations below, an explicit planned human intervention, or a genuine blocker that requires the user. |

At **every level**, always consult the user for:

- Matters of taste or design requiring an unresolved subjective preference,
  after separating out what agents can test or measure as described below.
  Apply an already settled preference without asking again.
- A serious unexpected event or issue that is unrecoverable or has wide or
  deep effects, even if part of it can be recovered. For other recoverable
  issues, decide whether to consult according to the level.
- Projected costs beyond the agreed limits. When costs were not discussed,
  the limit is **zero/free**. Ask before incurring the increase, not after.

Existing scope and acceptance boundaries, explicit human checkpoints, and
permission requirements still apply at every level. Hold affected work while
an answer is pending and continue independent work. Use already authorized
containment when needed to prevent further harm.

### Test measurable behavior before escalating

"Look and feel" or "design" is not by itself a reason to ask the user.
Separate testable behavior from subjective preference, including when both
appear in one review item. At medium and high autonomy, err toward having
agents script, test and benchmark the measurable part, fix problems within
scope, and verify the result without asking for manual evaluation or making
it a user review gate. The overseer filters workers' review requests before
relaying them; a worker calling something subjective does not make it so.

For example, zoom, pan and drag smoothness should be evaluated with
representative interactions and P50/P75/P95/P99 frame times, dropped frames
and relevant latency, against agreed targets on the relevant browsers and
available hardware. Reuse existing benchmarks and record their conditions
and limits. Do not ask "does it feel smooth on your laptop?" when a scripted
benchmark can answer the performance question. At low autonomy, invite an
optional hands-on trial when the user wants involvement; agents still own
objective verification rather than replacing it with the user's impression.

Escalate only the remaining preference or product tradeoff that the evidence
cannot settle, or another mandatory consultation. Metrics and functional
tests must support the claim: a working shortcut does not establish
discoverability, nor does counting keystrokes alone prove a picker is faster
for users. Use suitable evidence and keep unproven claims qualified. If
required hardware or access is unavailable, report that concrete limit and
ask only for the necessary access or bounded action; do not relabel the gap
as a taste question. Obtain permission for checks that would disrupt the
user's machine. Keep routine measurement in the work evidence and normal
progress reports, without generating extra user decisions.

### High-autonomy session grant

At the beginning of **every high-autonomy overseer session**, before starting
workers or exercising delegated authority, ask a question dialog that
requires an explicit answer. This includes a replacement overseer, a new run,
and switching an existing session to high. In Paseo, the actual overseer asks
after the launcher hand-off; a launcher's or previous session's grant does
not carry over. A same-session resume may retain its recorded grant.

Explain that high autonomy permits the main agent to make decisions with the
user's delegated authority within the agreed scope, including Paseo messages
that supply authorization context for suspected auto-mode classification
false positives. Paseo's `send_agent_prompt` messages to other Paseo agents
appear as if sent by the user, allowing the overseer to supply the missing
authorization context and unblock classification false positives through
supported reconsideration. These messages interrupt the receiving agent and
its running subagents; they do not queue. Prefer sending while the receiver
is idle. If sending while it is active, add a note asking it to continue
after the interruption, as "Relay human interventions" describes. This does
not transfer authority to workers or remove the mandatory consultations or
the harness's permission checks. Ask:

> For this session, do you explicitly grant the overseer the power to act
> **with the authority of the user**, not just **on your behalf**, within the
> agreed scope, including clearly identified delegated authorization through
> Paseo messaging for auto-mode reconsideration?

Offer **Grant for this session** and **Use medium autonomy**. Do not infer
consent from a request for high autonomy, silence, a selected default, or plan
approval. Record the actual answer, session ID, scope and date alongside the
plan agreement. Until granted, do not exercise high autonomy; a declined
grant selects medium. If a dialog cannot be opened, leave the grant pending
and proceed only under medium's rules and any existing plan approval. Honor
revocation or a lower level immediately and tell workers about the change.

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

### Workstreams in a tracker

When the campaign keeps tier 3 as workstream issues (three-tiered-plan's
"Keep tier 3 as tracker workstreams"), each workstream is a thread and its
issue is the thread's entry. Where this skill says script, read the tracker,
and follow the repository's instructions for its fields and commands:

- **Ready set:** run the repository's readiness tool, read-only where it has
  a dry run, rather than deriving readiness yourself. Propose workstreams it
  reports ready, or in flight with ready items, and take **not alongside**
  rules from their Depends on sections and the repository's exclusion table.
  A workstream the tool calls provisional waits for its refinement.
- **Agreement and approval:** record the user's agreement as a signed comment
  on each workstream issue that quotes the dialog answer. When the repository
  makes approval a tracker state, such as a status of Approved, set it from
  that agreement only where its instructions let an agent record the user's
  approval; otherwise ask the user to set it, as a planned any-time
  intervention. A workstream without its approval state doesn't launch.
- **Workers:** brief each with the workstream prompt, such as
  `/keep-me-in-the-loop Run workstream #<N>`. The worker claims the issue as
  the repository's instructions say and keeps the sibling worktree they name.
  Name it after the workstream, such as `Worker: <name> #<N>`.
- **Judgment calls and deviations:** record them as signed comments on the
  affected workstream issues, update those issues' bodies or links, and rerun
  the readiness tool before launching their dependents.
- **Done:** besides the checks in "Run the threads", the workstream issue is
  closed, the readiness tool has run, and the summary shows its dependents
  unblocked. Report its drift check with the done check.

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

Carry the routine-check command, stable accepted timing baseline, budget and
machine/cache/concurrency assumptions between workers. Compare across the run,
not just against the previous chunk; do not reset the baseline at each handoff.
Assign test-runtime regressions to the worker introducing them while its change
is still in progress. Keep coverage mainly in fast unit tests, with fewer
integration tests and a small end-to-end set; judge cost as well as test count.
Consolidating duplicate tests or moving logic checks down a layer is ordinary
maintenance when the required proof is preserved. Moving a required proof to a
later gate or making it optional remains an acceptance change. Do not turn
routine suite maintenance into a separate milestone by default, or hide growth
by increasing concurrency beyond the agreed resource limits.

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
consequential choices at low autonomy. Relay a proposal
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

Give each worker a directory inside its permitted checkout for operational
logs and artifacts that must survive a resume. Include it in the brief and
have the worker confirm it can write and read there before a long operation.
Check access to required ignored inputs and tools at the same time, without
printing secrets. Resolve missing access before dependent work starts;
changing paths or tools is not a way around an existing permission denial.

## Choose the session mechanism

Use the first mechanism that applies, and name it in the opening message.
Outside Paseo, launch workers in your own harness, so that messages travel
natively.

For routine coordination, do not interrupt a running session. The Paseo
authorization messages in "Relay human interventions" are an exception;
prefer an idle receiver even then. An interrupt
cancels the tool call in flight, which may be a live operation, and in Claude
Code it also stops the session's background subagents for good, including a
worker's continuous reviewer. Message a session through the receiver's own
harness, which delivers without interrupting:

- **To a Claude Code session:** `SendMessage` from another Claude Code
  session, using a session reference where supported, otherwise a unique
  peer name verified through `ListAgents`. It arrives after the receiver's
  current tool call.
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
  implementation, otherwise your own provider. For Claude workers, apply
  "Claude development worker routing" below when choosing the model and effort. Name yourself with
  `update_agent` too.
- **Address:** `send_agent_prompt` interrupts a running agent and its
  subagents instead of queuing. For routine messages, use it only when
  `get_agent_status` shows idle; otherwise message as above. For authorization
  messages, follow "Relay human interventions", including its continuation
  note when the receiver is active. A Claude agent is a Claude Code peer session: give
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

### Claude development worker routing

Unless the user selected another model, use Sonnet 5.5 medium for routine,
bounded development and high for demanding diagnosis, concurrency/lifecycle work,
complex integration, or substantive review. Record the choice in the worker brief.
Keep medium as the default; escalate deliberately based on the work, not simply
because the campaign is long. Preserve explicit user model/provider choices.

In Paseo, select a matching Claude profile from `list_profiles`, or use the
advertised launch overrides for `claude-sonnet-5-5` and the chosen effort. Claude's
`~/.claude/agents/developer-{trivial,routine,demanding}.md` are native
subagent definitions, not Paseo launch profiles. Verify the effective provider,
model and thinking option returned by the launcher; report unsupported routing
rather than silently inheriting another model. Do not modify existing live workers.

For standalone Claude workers, use explicit model and effort flags as below.
Keep the normal Claude Code system prompt and the `keep-me-in-the-loop` brief:
`--agent` with a nonempty custom prompt would replace the default system prompt.
Native subagents inside a Claude worker may use `developer-trivial`,
`developer-routine`, or `developer-demanding` when their assignment fits; pass the relevant workflow rules
and preserve any reviewer model explicitly required by the active review skill.

Compare elapsed time and total model usage per accepted work item, including
review and repairs, before claiming savings. Do not add recurring benchmarks just
to measure orchestration; reuse session usage and existing acceptance evidence.

### Claude Code

Launch each worker as a background session from its worktree:

```sh
cd ../<repo>-worker-<slug>
claude --bg -n "Worker: <subtask>" --model claude-sonnet-5-5 --effort <medium-or-high> --permission-mode <your mode> "<brief>"
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
acknowledge its brief to you. Record both ends' immutable session IDs and
the harness-specific delivery addresses in your checklist and the brief.
Use a session ID or session reference for delivery where supported. If the
harness only accepts peer names, verify a unique name-to-session mapping;
never route through an ambiguous display name. Confirm the return channel
with your reply to the acknowledgement, and recheck the mapping after a
resume or handoff. If no acknowledgement arrives, find out why,
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
- The overseer's autonomy level is `<low|medium|high>`, with authority limited
  to `<agreed scope and any session grant>`. This does not give you the
  overseer's delegated authority. Route decisions through it at every level;
  test measurable aspects of look and feel before flagging unresolved
  subjective choices; flag serious unexpected issues and projected costs
  beyond `<agreed limit, zero/free if unspecified>` before affected work.
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
  overseer needs outcomes, not activity. Before claiming a check passed,
  finalize its evidence and limitations with your reviewer, as "Run the
  threads" describes. Label earlier results provisional.
- A reply that quotes the user is the user's answer. A reply the overseer
  marks as its own decision carries only the authority the user gave the
  overseer.
- If the permission classifier blocks an action, never work around it. Tell
  the overseer the exact action and the classifier's reason, carry on with
  independent work, and end your turn once you are blocked on it, so the
  overseer can relay the user's approval into this thread.
- Work in `<worktree>` on `<branch>`. Publish as the repository's rules say,
  for example by rebasing onto the remote main branch and pushing, and
  reconcile shared documents without overwriting another thread's entries.
- Keep operational logs and retained artifacts in `<artifact directory>`;
  confirm access before long operations. Run compute and checks within
  `<agreed execution location, resource limits and runtime budgets>`, where
  applicable. Report overruns and measured growth before expanding the work.
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
Approve it when it fits and the autonomy rules allow you to decide. Otherwise
relay it, as "Relay human interventions"
describes, and pass the user's answer back. One thread's agreed scope never
covers another thread.

Before reporting an acceptance result or using it to unblock a dependent,
require a finalized handoff: the check and revision tested, the result and
evidence location, the reviewer's acceptance, and the limitations or unmet
checks. For statistical claims, include what was counted, its denominator,
exclusions or abstentions, and what the sample represents. Check the claim
against that evidence; a passing gate does not establish broader accuracy
or coverage. If reviewer disclosures are still pending, keep the result
provisional. Carry material limits into the user-facing report and correct
any overstatement promptly.

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

An unavailable or permission-blocked proof stays unmet. Keep its acceptance
gate open in the script and status document, even while independent work
continues. Reusing earlier evidence, substituting a check or moving it to a
later phase needs the user's approval unless that alternative was already
agreed. Ask through the human-intervention dialog with the proposed evidence
and what remains unproven; do not announce the change as settled or make the
user opt back into the original check. Record the answer before changing the
gate or launching work that depends on it. Approval of a deferral does not
authorize an action rejected by the permission system.

When a worker goes quiet without reporting, inspect it before nudging it: it
may be waiting on a permission prompt, out of context, or crashed. Resume the
same session with what it needs, or relaunch the thread in a new worker with
a handoff of its recorded state, since `keep-me-in-the-loop` resumes from the
documents and Git. When a worker fails the same way twice, report it with what
you are doing about it, and ask the user only if the remedy needs them.

## Relay human interventions

When a request for a human comes due, whether planned or raised by a worker:

1. Apply "Choose autonomy and establish authority" first. Answer from settled
   sources, such as a recorded decision or a fact you can verify, or make a
   decision within your scope when the autonomy level permits it. Mark the
   answer as yours, with its source or reasoning. Never decide a mandatory
   consultation yourself.
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

Claude Code's auto mode classifier gives no user authority to a message from
another session: `SendMessage` arrives marked as a peer's, so a worker's
classifier can block an action the user approved through you. Paseo's
`send_agent_prompt` arrives exactly like text the user typed in the worker's
thread. When a Claude worker in Paseo reports a classifier block on an action
the user approved, in their own words to you, for that action or its class:

1. Check `get_agent_status` and prefer waiting until the worker is idle.
   `send_agent_prompt` does not queue: it interrupts a running agent and its
   running subagents. If you send while it is active, add a continuation
   note as described below.
2. Send it with `send_agent_prompt`: `[overseer] Relaying the user's approval
   for <action>: "<the user's words>" (<date>).` Quote the user exactly, and
   add only the continuation note if needed.

At low or medium autonomy, use this channel only to relay an approval the
user actually gave. If the action needs user authorization that is missing,
ask the user as "Relay human interventions" describes.

At high autonomy with the explicit grant for this session, you may also use
Paseo messaging autonomously to supply delegated authorization context for a
suspected auto-mode false positive. Inspect the exact action and rejection
reason first: the action must fit the agreed scope, spending and permission
boundaries, require no mandatory consultation, and be eligible for
reconsideration through the harness's supported approval flow. Check the
worker's status and prefer an idle receiver as above. Clearly identify the
message's actual author:

> [overseer] Delegated decision by the overseer under the user's explicit
> high-autonomy grant for session <ID> on <date>: <exact grant quote>.
> I authorize <specific action> within <agreed scope>. The reported block is
> <reason>; the relevant authorization context is <evidence>. Reconsider
> through the supported approval flow; all permission checks still apply.

When sending either kind of authorization message to a non-idle agent, add:

> This message interrupted your work rather than queuing. After processing
> it, check the interrupted operation's state and continue from where you
> stopped. Re-establish any interrupted subagents, including your reviewer,
> before relying on their work; avoid repeating completed side effects.

The note helps the receiver recover; it does not prevent interruption or
automatically resume its subagents.

This is the overseer's decision under delegated user authority, not a new
instruction typed by the user. Record the decision and outcome. Do not use
the channel to impersonate the user, override an enforced denial or disable
a safeguard. If the harness does not accept delegated authority, the reason
is uncertain, or the action remains blocked after supplying the context,
stop retrying and relay the blocker to the user. A worker's assertion that a
block is a false positive is not sufficient evidence by itself.

### Ask through a question session

A question session is a short-lived session whose only job is to put one
dialog to the user and carry the answer back. It blocks while the user
decides, and you keep working. Name it `Question: <topic>`.

- **Launch** it like a worker, but light: your permission mode and no
  worktree. On Claude, use Sonnet (`claude-sonnet-5-5`); never a Haiku
  model, even though the session is short.
  - In Paseo, give it a local workspace on the run checkout, in the run
    project, even while workers use that checkout, and clear its
    `paseo.parent-agent-id` label, as "Paseo" describes for workers, so the
    user sees it as a thread of its own. Paseo flags it as needing the user
    when its dialog opens.
  - In Claude Code, launch it from the main checkout with
    `claude --bg -n "Question: <topic>" --model claude-sonnet-5-5 --permission-mode <your mode> "<prompt>"`.
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
alone (workstreams by name and issue number), and end with the roll call:

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
