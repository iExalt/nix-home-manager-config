# Launching Paseo agents

Follow this whenever you start another Paseo agent: a worker, an overseer, an
auditor, a question session or any other thread the user should see. `paseo`
means `"$PASEO_CLI"`, which Paseo sets in its agents' environment; your own
agent ID is `$PASEO_AGENT_ID`. Run `paseo prime` once per session and check a
command's `--help` before relying on a flag. The terms worker, Paseo subagent
and native subagent are defined in `SKILL.md` › Delegation.

A worker is a top-level thread in its own visible workspace, in the right
project, with settings you chose on purpose. Three Paseo defaults work against
that, so every step below is explicit:

- An agent-launched `paseo run` (alias `agent run`) without
  `--relationship detached` becomes your Paseo subagent, even in another
  workspace or project.
- `run --new-workspace` takes its project from the directory and copies your
  workspace's background setting; it has no `--project` or `--no-background`.
- A project is matched by its path, so a different path to the same checkout,
  or a cwd in another repository, can land the agent in another or a new
  project.

## 1. Find where you are

```bash
self=$(paseo agent status "$PASEO_AGENT_ID" --json) || exit 1
self_workspace=$(jq -er '.snapshot.workspaceId' <<< "$self") || exit 1
self_project=$(paseo workspace ls --json | jq -er --arg ws "$self_workspace" \
  '.[] | select(.workspaceId == $ws) | .workspace.projectId') || exit 1
```

`agent inspect` and `agent ls` show neither the workspace nor the project.

## 2. Choose the project

| New agent | Project |
| --- | --- |
| Worker or question session for work in your own repository | Yours (`$self_project`) |
| Overseer | A new run project, as `overseer` › [references/paseo.md](../../overseer/references/paseo.md) describes |
| Overseer's worker or auditor | The overseer's run project, whatever repository the worker changes |
| Work in another repository, outside an overseer run | That repository's registered project: match `realpath` of its checkout against `realpath` of each `path` in `paseo project ls --json`, since a symlinked path may be registered; ask the user if none matches |

Target the project by ID with `workspace create --project <id>`, which accepts
any checkout path. Never let the project follow from a `cd` or `--cwd`.
Reviewers stay native subagents (`SKILL.md` › Delegation), not Paseo agents.

## 3. Create the workspace and validate it

Never launch into your own workspace, and never use `run --new-workspace`.
Create the workspace, then gate the launch on its ID and an exact inventory
readback. Build `workspace_args` as a shell array, for example
`(--isolation worktree --no-background --path <checkout> --project "$project_id" --base origin/main --title "Worker: <subtask>")`
or `--isolation local` for a lone thread in an existing checkout, and set
`project_id` and `isolation` to match:

```bash
workspace_json=$(paseo workspace create "${workspace_args[@]}" --json) || exit 1
workspace_id=$(jq -er '
  .workspaceId | strings |
  select(length > 0 and . != "null" and . != "undefined" and (test("\\s") | not))
' <<< "$workspace_json") || exit 1
[ "$workspace_id" != "$self_workspace" ] || exit 1
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

The workspace's ID is the top-level `workspaceId`; never guess `.id`. For
worktree isolation, the returned `cwd` is the new worktree, not the source
checkout. Add `--notifications off` when you, not the user, should hear from
the agent.

## 4. Choose its settings

By default the new agent matches you. A workflow skill's model routing, the
brief's role or the user's choice overrides that default; a read-only role
doesn't need your full access.

- **Same provider:** copy `snapshot.model`, `snapshot.thinkingOptionId` and
  `snapshot.currentModeId` from `$self`.
- **Different provider:** model and thinking IDs don't carry over. Take the
  model from `paseo provider models <provider> --full --json` and a thinking
  option that model lists, matching your effort where it exists. Translate the
  mode to its closest match, using the IDs `paseo provider inspect <provider>
  --json` lists under `modes`:

  | Claude | Codex |
  | --- | --- |
  | `bypassPermissions` | `full-access` |
  | `auto` | `auto-review` |
  | `default` (`acceptEdits` maps here too) | `auto` |
  | `plan` | none: ask, or give a read-only brief |

  Read the table in either direction; from Codex, `auto` maps to `default`.

Pass IDs, never labels such as `"Full Access"`, and never invent a model.

## 5. Launch

```bash
paseo run --no-wait --json --relationship detached --workspace "$workspace_id" \
  --label task=<unique-key> --title "<title>" --provider <provider> \
  --model <model> --thinking <thinking> --mode <mode> --prompt-file <brief>
```

Paseo notifies you when an agent you launched finishes; pass
`--no-notify-on-finish` when you don't need that. Parse stdout only: `run` prints notices such as `Using workspace …` on stderr, so never pipe
`2>&1` into a JSON parser. If the response is lost or unparseable, the agent may
still exist: check `paseo agent ls -a -g --label task=<unique-key> --json`
before any retry.

## 6. Read it back

```bash
paseo agent status "$agent_id" --json | jq -e \
  --arg ws "$workspace_id" --arg model "$model" \
  --arg thinking "$thinking" --arg mode "$mode" '
  .snapshot
  | ((.labels // {})["paseo.parent-agent-id"] // null) == null
    and .workspaceId == $ws and .model == $model
    and .thinkingOptionId == $thinking and .currentModeId == $mode
' >/dev/null
```

A null `paseo.parent-agent-id` label means no parent. Step 3's gate already
checked the workspace's project. Fix any mismatch before you report the
launch. To make a Paseo subagent independent, run
`paseo agent detach <id>`; never edit its labels. If Paseo drops
`--relationship detached`, launch, then detach.

## Answer a worker's question

When a worker asks for input, inspect the pending request's
`input.questions` and answer every question by its displayed `header`. Pass a
nonblank string for each header: the chosen option label or free text. Use the
normalized `updatedInput` shape Paseo expects:

```bash
paseo permit allow <agent> <request> --input \
  '{"answers":{"Question 1":"chosen label or free text"}}'
```

Do not send Codex's raw `{id:{answers:[]}}` payload or a flat map keyed by
question ID. Never silently choose the first option. If a malformed answer is
rejected, the request should remain pending; correct the payload and retry.
If `paseo permit ls` shows no request, inspect the worker's current state
before retrying because another answer may have completed concurrently.

If the installed daemon predates async-question support, or `permit allow`
cannot safely answer the request, check `paseo send --help` and steer the
worker with `paseo send <agent> --behavior steer --prompt 'answer'`. Verify
that the worker received the message. A steer may not resolve the pending
async question, so do not report it as cleared without checking the request.

## 7. Tear down

You own every workspace you created in step 3; end it with its agents, unless
a workflow skill says to keep it for the user to review. `agent stop` and
`close` always leave the workspace behind. Archiving or deleting its last
unarchived agent also archives it when `paseo agent archive --help` says so;
older daemons leave an empty sidebar entry. Tearing down by workspace works on
both:

1. Target only a `workspace_id` you created and recorded. Target
   `$self_workspace` only when a workflow skill tells you to archive yourself,
   and then as your last action: it can end your shell mid-command, so send
   your handoff first and leave the readback in step 5 to whoever launched you.
2. Confirm the workspace holds only agents you launched, none still working:
   list candidates with `paseo agent query --cwd <workspace cwd> --json` and
   keep those whose `paseo agent status <id> --json` shows
   `.snapshot.workspaceId == $workspace_id`; each must have a `.snapshot.status`
   other than `running`. If it also holds agents you don't own, archive only
   your own with `paseo agent archive <id>` and leave the workspace.
3. For `worktree` isolation, inspect the worktree first: archiving deletes a
   Paseo-owned worktree directory that no other workspace uses, untracked and
   ignored files included. `git -C <cwd> status --porcelain --ignored` must
   show nothing but known-disposable paths, and `git -C <cwd> rev-list
   @{u}..HEAD` must be empty. Anything else blocks the archive until you have
   pushed it or confirmed it is disposable. `local` isolation never touches the
   checkout.
4. Run `paseo workspace archive "$workspace_id" --json`, which archives its
   agents too.
5. Confirm the ID is gone from `paseo workspace ls --json`.
