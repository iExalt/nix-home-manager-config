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
  needing the user when its dialog opens.
- **Prompt** it with the finished dialog: each question, its options with
  their consequences, and your recommendation. It calls `AskUserQuestion`
  with exactly those, does nothing else, and sends you the answer verbatim,
  with any notes the user typed, with
  `paseo agent send --no-wait --if-running queue --no-notify-on-finish <your agent ID> "<answer>"`.
  Put questions that come due together in one session; its dialog takes up to
  four.
- **Archive** it once its answer arrives. Its last action archives its own
  workspace, which keeps the directory. Paseo gives an agent no workspace
  variable, so put this exact command in its prompt rather than a placeholder:
  `"$PASEO_CLI" workspace archive "$("$PASEO_CLI" agent status "$PASEO_AGENT_ID" --json | jq -r .snapshot.workspaceId)"`.
  Then check it with `paseo agent status <agent-id>`, and if
  Paseo reopened it, run `paseo agent archive --force <agent-id>`. If the user
  answers some other way, archive it yourself.
- **Fallback:** if a question session can't be launched or its dialog never
  appears, send the request as a message that leads with it, with a push
  notification, and open your own blocking dialog only when nothing useful
  remains that doesn't depend on the answer.
