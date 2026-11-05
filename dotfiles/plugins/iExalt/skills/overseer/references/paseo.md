# Overseer in Paseo

Read this when the overseer runs in Paseo with its built-in tools
(`create_agent`, `send_agent_prompt` and the rest). Section names in quotes,
such as "Relay human interventions", are in the overseer's `SKILL.md`.

## First, move into a run project

In Paseo, the overseer runs inside a temporary run project with its workers,
as "Run project and workers" below describes. Before any other overseer work, including reading the
script, the plan or the repository's instructions, check where you are: find
your `workspaceId` with `get_agent_status` on your own agent ID, then your
workspace's project and checkout in `list_workspaces`. If your checkout is a
run checkout, `../<repo>-overseer-<slug>`, you are the overseer; skip to the
rest of this skill. Otherwise the user started you in the repository's own
project, and your whole job is the hand-off, done straight away:

1. Create the run project and its checkout, as "Run project and workers"
   below describes, taking
   `<task>` and `<slug>` from the user's request.
2. Create a workspace there with `create_workspace`: local isolation, the run
   checkout as `path`, the run project's `projectId` and the title
   `Overseer: <task>`.
3. Launch the overseer in it with `create_agent`, titled `Overseer: <task>`,
   with your own provider and mode from `get_agent_status`, and the overseer
   model and effort from `SKILL.md` › Three-tier model routing. Its prompt invokes this
   skill and carries the user's request verbatim, with anything else they
   said in this thread, and your agent ID as the launcher's. Clear its
   `paseo.parent-agent-id` label, as
   "Run project and workers" describes for workers.
4. Right after the launch, without waiting on the overseer, ask the user in a
   blocking dialog whether to archive this thread, naming the overseer thread
   and its project. Record the answer on yourself with `update_agent`, as the
   label `overseer.launcher` set to `archive` or `keep`. On yes, call
   `archive_workspace` on your workspace when `list_agents` shows no other
   agent in it, and `archive_agent` on yourself otherwise. On no, stay idle:
   the overseer's finish notifications still reach you, and you answer each
   with no text at all.

If the `paseo` CLI is missing or fails, skip the hand-off, say so, and oversee
from this thread in the repository's existing project.

The user answers that dialog while viewing the launcher's thread, and Paseo
reopens an archived session the user is viewing, so the launcher's own archive
doesn't stick. As the overseer, finish it: whenever you wake, including when a
dialog returns, read the launcher's labels with `get_agent_status`. Once
`overseer.launcher` is `archive` and its status isn't `closed`, call
`archive_agent` on it. Stop checking once it is closed or the label is
`keep`.

## Run project and workers

- **Run project:** keep the run's threads together in a temporary Paseo
  project of their own. The built-in tools can't create projects, but the
  `paseo` CLI can; the macOS app bundles it at
  `/Applications/Paseo.app/Contents/Resources/bin/paseo`. Add a checkout for
  the run with
  `git worktree add ../<repo>-overseer-<slug> -b overseer/<slug> origin/main`,
  register it with `paseo project create ../<repo>-overseer-<slug> --json`,
  and name it with `paseo project rename <project-id> "Overseer: <task>"`.
  The session the user started does this and hands off to an overseer inside
  the project, as "First, move into a run project" above describes. If
  the user doesn't agree to the plan, offer to clean up the project, as
  "Clean up the run project" below describes.
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
  in its project. You still get its finish notifications. Choose the provider
  and model as Paseo's guidance says: the profile the user named, or the one
  from `list_profiles` whose notes fit implementation, otherwise your own
  provider. Apply `SKILL.md` › Three-tier model routing to both providers when
  choosing the model and effort. Name yourself with `update_agent` too.
- **Address:** `send_agent_prompt` interrupts a running agent and its
  subagents instead of queuing. For routine messages, use it only when
  `get_agent_status` shows idle; otherwise message through the receiver's own
  harness, as `SKILL.md` › Choose the session mechanism describes. Authorization
  messages follow "Relay approvals past a classifier block" below. A Claude agent is a Claude
  Code peer session: give workers the peer name `ListAgents` reports for you,
  and take each worker's peer name from the `from` attribute of its
  acknowledgement. A Codex agent's session ID is
  `persistence.metadata.threadId` in `get_agent_status`.
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

## Relay approvals past a classifier block

Claude Code's auto mode classifier gives no user authority to a message from
another session: `SendMessage` arrives marked as a peer's, so a worker's
classifier can block an action the user approved through you. Paseo's
`send_agent_prompt` arrives exactly like text the user typed in the worker's
thread. When a Claude worker in Paseo reports a classifier block on an action
the user approved, in their own words to you, for that action or its class:

1. Check `get_agent_status` and prefer waiting until the worker is idle,
   since `send_agent_prompt` interrupts instead of queuing, as the Address
   entry above describes. If you send while it is active, add the continuation note
   below.
2. Send it with `send_agent_prompt`: `[overseer] Relaying the user's approval
   for <action>: "<the user's words>" (<date>).` Quote the user exactly, and
   add only the continuation note if needed.

At low or medium autonomy, use this channel only to relay an approval the
user actually gave. If the action needs user authorization that is missing,
ask the user as steps 1 to 4 of `SKILL.md` › Relay human interventions
describe.

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

## Clean up the run project

A Paseo run project is the exception: leave its workers' agents, workspaces
and worktrees in place until the run's goal is complete, so the user can look
through the threads. After the final report, ask the user in a blocking
dialog, such as `AskUserQuestion`, whether to clean up the run project; with
nothing left to run, the dialog blocks nothing. Name what cleanup would
remove and anything unpushed it would keep.

- **Clean up:** archive each worker's and question session's agent and
  workspace, and remove each worker's worktree under `~/.paseo/worktrees/`
  as `SKILL.md` › Clean up describes. Say what you removed and what goes next, since your own thread
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
