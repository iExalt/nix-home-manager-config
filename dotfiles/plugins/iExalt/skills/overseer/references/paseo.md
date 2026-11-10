# Overseer in Paseo

The overseer runs only in Paseo. Drive Paseo through its CLI, not
built-in agent tools: `paseo` below means `"$PASEO_CLI"`, which Paseo sets in
its agents' environment, and the macOS app bundles it at
`/Applications/Paseo.app/Contents/Resources/bin/paseo`. Your own agent ID is
`$PASEO_AGENT_ID`. Add `--json` to a command whose output you parse. Section
names in quotes, such as "Relay human interventions", are in the overseer's
`SKILL.md`.

## First, move into a run project

In Paseo, the overseer runs inside a temporary run project with its workers,
as "Run project and workers" below describes. Before any other overseer work,
including reading the script, the plan or the repository's instructions,
check where you are: find your `workspaceId` with
`paseo agent status "$PASEO_AGENT_ID" --json`, then your workspace's project
and checkout in `paseo workspace ls --json`. If your checkout is a run
checkout, `../<repo>-overseer-<slug>`, you are the overseer; skip to the rest
of this skill. Otherwise the user started you in the repository's own
project, and your whole job is the hand-off, done straight away:

1. Create the run project and its checkout, as "Run project and workers"
   below describes, taking `<task>` and `<slug>` from the user's request.
2. Create a workspace there:
   `paseo workspace create --isolation local --no-background --path <run checkout> --project <project-id> --title "Overseer: <task>" --json`.
   Apply "Validate every launch" below.
3. Launch the overseer in it with
   `paseo agent run --no-wait --relationship detached --no-notify-on-finish --workspace <workspace-id> --title "Overseer: <task>" --provider claude --mode <mode> --model <Opus> --thinking medium "<prompt>"`,
   with your own mode translated as `working-conventions` ›
   [references/paseo-launch.md](../../working-conventions/references/paseo-launch.md)
   step 4 describes, and the latest Opus model
   `paseo provider models` lists for the overseer route in
   `SKILL.md` › Model routing, whatever your own provider. If that route is
   unavailable, report it and stop. Its prompt invokes this skill and
   carries the user's request verbatim, with anything else they said in this
   thread, and your agent ID as the launcher's.
4. Start the auditor, as "Start the auditor" below describes.
5. Right after the launches, tell the user in one line where the overseer
   and the auditor run (their threads and project), then archive yourself: with
   `paseo workspace archive <your workspace-id>` when you are the only agent
   in your workspace (`paseo agent status <agent-id> --json` shows each
   agent's `snapshot.workspaceId`), otherwise with
   `paseo agent archive --force "$PASEO_AGENT_ID"`.

If the `paseo` CLI is missing or fails, say so and stop; the overseer runs only
in Paseo.

Paseo reopens an archived session the user is viewing, so the launcher's own
archive may not stick. As the overseer, finish it: whenever you wake, check
`paseo agent status <launcher-id> --json`, and if it isn't `closed`, run
`paseo agent archive --force <launcher-id>`. Stop checking once it is
closed.

## Start the auditor

The launcher, never the overseer, starts the auditor, so the overseer cannot
shape its inputs or instructions. Do it in the hand-off, after the overseer's
launch, with the run checkout and project as the overseer's:

1. Create a workspace in the run project with notifications on:
   `paseo workspace create --isolation local --no-background --notifications on --path <run checkout> --project <project-id> --title "Auditor: <task>" --json`.
   Apply "Validate every launch".
2. Launch it with
   `paseo agent run --no-wait --relationship detached --no-notify-on-finish --workspace <workspace-id> --title "Auditor: <task>" --provider claude --mode <mode> --model <Opus> --thinking medium "<brief>"`,
   with the mode chosen as for the overseer, and its brief being
   [../assets/auditor-brief.md](../assets/auditor-brief.md) with
   the run checkout path, the scoreboard script path and the repository filled in.
   Unlike a worker's workspace, leave notifications on: the auditor is the one
   agent that messages the user. Don't add `--notify-on-finish`; the launcher is
   about to archive itself.
3. Tell the overseer only that an auditor exists and that its alarms go to the
   user, in the overseer's prompt. Never give it the auditor's agent ID or a way
   to message it.

The auditor creates its own heartbeat (`paseo heartbeat create` is per calling
agent) as its first action. Its heartbeat ends when it is archived: the overseer
archives the auditor in "Clean up the run project" and the halt procedure archives
it with the run's other agents.

## Validate every launch

Launch every agent of the run as `working-conventions` ›
[references/paseo-launch.md](../../working-conventions/references/paseo-launch.md)
describes: gate each launch on its workspace validation (step 3) and read the
agent back (step 6) before you report it. The commands in this file fill in
that recipe's project, isolation, settings and title for each role. If
creation times out, its response can't be parsed or readback disagrees, stop
and reconcile the inventory before retrying; the first request may already
have succeeded.

## Run project and workers

- **Run project:** keep the run's threads together in a temporary Paseo
  project of their own. Add a checkout for the run with
  `git worktree add ../<repo>-overseer-<slug> -b overseer/<slug> origin/main`,
  register it with `paseo project create ../<repo>-overseer-<slug> --json`,
  and name it with `paseo project rename <project-id> "Overseer: <task>"`.
  The session the user started does this and hands off to an overseer inside
  the project, as "First, move into a run project" above describes. If
  the user doesn't agree to the plan, offer to clean up the project, as
  "Clean up the run project" below describes.
- **Isolation:** give each worker a workspace with worktree isolation in the
  run project, branching off the remote main branch rather than the local
  `main`, named after the worker:
  `paseo workspace create --isolation worktree --no-background --notifications off --path <run checkout> --project <project-id> --base origin/main --title "Worker: <subtask>" --json`.
  Paseo puts these worktrees under `~/.paseo/worktrees/`. Use the
  repository's `paseo.json` setup for ignored files when it provides them. A
  lone worker may use the run checkout itself, through a workspace created
  with `--isolation local --notifications off` and the same path and project.
  Mute notifications for every worker workspace so the overseer handles
  user-facing updates. Keep `--notify-on-finish` on worker launches and
  messages so workers still wake the overseer. Never launch a worker into
  your own workspace.
- **Launch:** start each worker as a top-level thread in its workspace, with
  the brief as its initial prompt:
  `paseo agent run --no-wait --relationship detached --notify-on-finish --workspace <workspace-id> --title "Worker: <subtask>" --provider codex --mode <mode> --model <GPT Sol> --thinking medium "<brief>"`,
  with the latest GPT Sol model `paseo provider models` lists, as
  `SKILL.md` › Model routing requires, unless the user named another route.
  If the route is unavailable, report it and hold the launch. Name
  yourself with `paseo agent update "$PASEO_AGENT_ID" --name "<name>"`.
- **Address:** reach every agent by its Paseo agent ID, which survives a
  restart, with
  `paseo agent send --no-wait --notify-on-finish --if-running queue <agent-id> "[overseer] <message>"`;
  a queued message runs once the receiver is idle, so it never cuts into a
  turn. Start every message with `[overseer]`; Paseo also marks it as another
  agent's message, so never word it as if the user wrote it. Give workers your agent ID in the brief. They send to you the same
  way, adding `--no-notify-on-finish` so your turns don't wake them. Never
  send with `--if-running interrupt`: it cancels the receiver's turn in
  flight and its subagents.
- **Watch:** Paseo notifies you once when a run you started with
  `paseo agent run` or `paseo agent send` finishes, errors or needs
  permission. Add no idle subscriptions on top. Whenever something wakes you,
  check the other workers with `paseo agent ls --json` or
  `paseo agent status <agent-id> --json`, and look into one that is idle
  without having reported or is stuck in `paseo permit ls`. In case nothing
  wakes you, keep one hourly heartbeat until the agreed scope is complete,
  including while every remaining item waits on the user:
  `paseo heartbeat create --json --cron "0 * * * *" --name overseer-watch --replace "<prompt>"`.
  Its prompt says to check the workers and pending permissions, act on what
  changed, start any ready work as the skill's "Keep work moving" describes,
  and end the turn with no text only when nothing changed and no work that
  could run is idle. It also reads `scoreboard.py show --json` for the stop-loss
  and sends a digest only when the scoreboard changed. Record the ID it returns in your checklist, and delete
  it with `paseo heartbeat delete <heartbeat-id>` when the agreed scope is
  complete or the user stops the run. At decision
  points, read `paseo agent activity <agent-id>`.

## Clean up the run project

A Paseo run project is the exception: leave its workers' agents, workspaces
and worktrees in place until the run's goal is complete, so the user can look
through the threads. After the final report, ask the user in a blocking
dialog, such as `AskUserQuestion`, whether to clean up the run project; with
nothing left to run, the dialog blocks nothing. Name what cleanup would
remove and anything unpushed it would keep.

- **Clean up:** archive each worker's, the auditor's and each question
  session's workspace as `SKILL.md` › Clean up describes; that archives their
  agents and removes each worker's Paseo-owned worktree. Say what you removed and what goes next, since your own thread
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

## Halt a run

When the user asks to stop a run, or any session must halt one from outside,
`paseo agent stop` is not enough: each stopped worker's completion
notification wakes its overseer, which can resume the workers. Instead:

1. Archive the overseer first with `paseo agent archive --force <id>`, so no
   notification can wake it. Archiving also completes its heartbeats.
2. Then archive every worker, reviewer, question session and the auditor of the run.
3. After about 30 seconds, check `paseo agent ls --json` again and re-archive
   any agent of the run that is live.
4. Confirm each heartbeat under `~/.paseo/schedules/` that targets the run's
   agents shows `completed`. Check for in-flight CI runs and remote jobs the
   run started, and report them.

Archiving agents keeps transcripts and pushed branches, so the user can still
review or revert the work. When `paseo agent archive --help` says the workspace
goes with its last agent, halting also archives the run's workspaces and
removes their clean Paseo-owned worktrees, keeping any with uncommitted or
unpushed work; older daemons keep all workspaces and worktrees. Run cleanup
stays a separate decision.
