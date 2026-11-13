# Ask through a question session

The overseer is a Claude agent in Paseo, and Claude's `AskUserQuestion` blocks
its session until the user answers. A question session is a short-lived Paseo
agent whose only job is to put one dialog to the user and carry the answer
back. It blocks while the user decides, and you keep working. Name it
`Question: <topic>`.

- **Launch** it like a worker, but light: your permission mode, provider
  `claude`, the latest Sonnet model `paseo provider models` lists (never a
  Haiku model, even though the session is short), and no worktree. Give it a
  local workspace on the run checkout, in the run project, even while workers
  use that checkout, and launch it with `--relationship detached` as for
  workers, so the user sees it as a thread of its own. Paseo flags it as
  needing the user when its dialog opens. Fill the placeholders, then run:

  ```bash
  self_json=$("$PASEO_CLI" agent status "$PASEO_AGENT_ID" --json) || exit 1
  self_ws=$(jq -er '.snapshot.workspaceId | strings | select(length > 0)' <<< "$self_json") || exit 1
  workspace_json=$("$PASEO_CLI" workspace create --isolation local --no-background \
    --path "<run checkout>" --project "<run project>" --title "Question: <topic>" --json) || exit 1
  ws=$(jq -er '.workspaceId | strings | select(length > 0)' <<< "$workspace_json") || exit 1
  [ -n "$ws" ] && [ "$ws" != "$self_ws" ] || exit 1
  # Apply paseo.md's "Validate every launch" workspace gate before running.
  "$PASEO_CLI" agent run --no-wait --json --relationship detached --workspace "$ws" \
    --label "task=<unique-key>" --title "Question: <topic>" --provider claude --model "<latest Sonnet>" \
    --mode "<your mode>" --prompt-file "<finished dialog prompt file>"
  ```

  Read the agent back as "Validate every launch" requires. Never pipe workspace
  creation into a parser: a parser's success can hide creation's failure.
  Keep stdout and stderr separate when capturing JSON. If the run response is
  lost or unparseable, query `paseo agent ls -a -g --label "task=<unique-key>"
  --json` and reconcile the matching agent's status and workspace before any
  retry. List rows use `name`; the rich query uses `title`.
- **Prompt** it with the finished dialog: each question, its options with
  their consequences, and your recommendation. It calls `AskUserQuestion`
  with exactly those, does nothing else, and sends you the answer verbatim,
  with any notes the user typed, with
  `paseo agent send --no-wait --if-running queue --no-notify-on-finish <your agent ID> --prompt-file "<answer file>"`.
  Put questions that come due together in one session; its dialog takes up to
  four.
- **Archive** it once its answer arrives. Put this exact footer in its prompt.
  It archives its workspace only when no other unarchived agent holds it;
  shared workspaces or failed inventory checks fall back to its own agent:

  ```bash
  sole_workspace() {
    self_json=$("$PASEO_CLI" agent status "$PASEO_AGENT_ID" --json) || return 1
    ws=$(jq -er '.snapshot.workspaceId | strings | select(length > 0)' <<< "$self_json") || return 1
    agents=$("$PASEO_CLI" agent ls -g --background --json) || return 1
    ids=$(jq -er 'if type == "array" and length > 0 and
      all(.[]; .id | type == "string" and length > 0)
      then .[].id else error("invalid agent inventory") end' <<< "$agents") || return 1
    while IFS= read -r id; do
      [ "$id" = "$PASEO_AGENT_ID" ] && continue
      peer=$("$PASEO_CLI" agent status "$id" --json) || return 1
      peer_ws=$(jq -er '.snapshot.workspaceId | strings | select(length > 0)' <<< "$peer") || return 1
      [ "$peer_ws" != "$ws" ] || return 1
    done <<< "$ids"
  }
  if sole_workspace; then
    "$PASEO_CLI" workspace archive "$ws"
  else
    "$PASEO_CLI" agent archive --force "$PASEO_AGENT_ID"
  fi
  ```

  Archiving a workspace created with local isolation on the externally created,
  non-Paseo-owned run checkout keeps that directory. Then check the agent with
  `paseo agent status <agent-id>`, and if Paseo reopened it, run
  `paseo agent archive --force <agent-id>`. If the user answers some other
  way, archive only the question agent yourself.
- **Fallback:** if a question session can't be launched or its dialog never
  appears, send the request as a message that leads with it, with a push
  notification, and open your own blocking dialog only when nothing useful
  remains that doesn't depend on the answer.
