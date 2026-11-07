# Overseer in Paseo

Read this when the overseer runs in Paseo. Drive Paseo through its CLI, not
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
   Apply "Validate the workspace before launch" below before launching.
3. Launch the overseer in it with
   `paseo agent run --no-wait --relationship detached --no-notify-on-finish --workspace <workspace-id> --title "Overseer: <task>" --provider <provider> --mode <mode> --model <model> --thinking <effort> "<prompt>"`,
   with your own provider and mode from `paseo agent status`, and the
   overseer model and effort from `SKILL.md` › Three-tier model routing. Its
   prompt invokes this skill and carries the user's request verbatim, with
   anything else they said in this thread, and your agent ID as the
   launcher's.
4. Right after the launch, tell the user in one line where the overseer
   runs (its thread and project), then archive yourself: with
   `paseo workspace archive <your workspace-id>` when you are the only agent
   in your workspace (`paseo agent status <agent-id> --json` shows each
   agent's `snapshot.workspaceId`), otherwise with
   `paseo agent archive --force "$PASEO_AGENT_ID"`.

If the `paseo` CLI is missing or fails, skip the hand-off, say so, and oversee
from this thread in the repository's existing project.

Paseo reopens an archived session the user is viewing, so the launcher's own
archive may not stick. As the overseer, finish it: whenever you wake, check
`paseo agent status <launcher-id> --json`, and if it isn't `closed`, run
`paseo agent archive --force <launcher-id>`. Stop checking once it is
closed.

## Validate the workspace before launch

Run `paseo prime` and inspect the installed command's help before parsing
its output. Capture stdout separately from stderr. Workspace creation
returns a top-level `workspaceId`; the list command returns an array whose
entries have `workspaceId`, `cwd`, `isolation` and `workspace.projectId`.
Do not substitute a guessed `.id` key or launch with an empty, whitespace,
`null` or `undefined` identifier.

Build `workspace_args` as a shell array from the chosen creation command,
including `--no-background`, and set `project_id` and `isolation` to the
planned project and isolation. Gate the launch on creation, ID validation
and an exact inventory readback:

```bash
workspace_json=$(paseo workspace create "${workspace_args[@]}" --json) || exit 1
workspace_id=$(jq -er '
  .workspaceId | strings |
  select(length > 0 and . != "null" and . != "undefined" and (test("\\s") | not))
' <<< "$workspace_json") || exit 1
workspace_list=$(paseo workspace ls --json) || exit 1
jq -e --arg id "$workspace_id" --arg project "$project_id" \
  --arg isolation "$isolation" --argjson created "$workspace_json" '
  [.[] | select(.workspaceId == $id
    and .workspace.projectId == $project
    and .isolation == $isolation
    and (.cwd | type == "string")
    and (.cwd | length > 0)
    and .cwd == $created.cwd
    and .background == false)] | length == 1
' <<< "$workspace_list" >/dev/null || exit 1
```

Confirm that the returned `cwd` is the intended checkout before passing
`"$workspace_id"` to `agent run --workspace`. For worktree isolation, this
is the new worker checkout, not the source checkout. If creation times out,
its response cannot be parsed, or readback disagrees, stop the launch and
reconcile the workspace inventory before retrying creation; the first
request may already have succeeded. Apply this gate to overseer hand-offs
and every worker launch.

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
  `paseo agent run --no-wait --relationship detached --notify-on-finish --workspace <workspace-id> --title "Worker: <subtask>" --provider <provider> --mode <mode> --model <model> --thinking <effort> "<brief>"`.
  Choose the provider and model as Paseo's guidance says: the profile the
  user named, or the one from `paseo profile ls` whose notes fit
  implementation, otherwise your own provider. Apply `SKILL.md` › Three-tier
  model routing to both providers when choosing the model and effort. Name
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
  could run is idle. Record the ID it returns in your checklist, and delete
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

## Halt a run

When the user asks to stop a run, or any session must halt one from outside,
`paseo agent stop` is not enough: each stopped worker's completion
notification wakes its overseer, which can resume the workers. Instead:

1. Archive the overseer first with `paseo agent archive --force <id>`, so no
   notification can wake it. Archiving also completes its heartbeats.
2. Then archive every worker, reviewer and question session of the run.
3. After about 30 seconds, check `paseo agent ls --json` again and re-archive
   any agent of the run that is live.
4. Confirm each heartbeat under `~/.paseo/schedules/` that targets the run's
   agents shows `completed`. Check for in-flight CI runs and remote jobs the
   run started, and report them.

Archiving keeps transcripts, workspaces, worktrees and branches, so the user
can still review or revert the work. Run cleanup stays a separate decision.
