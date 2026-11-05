# Ask through a question session

A question session is a short-lived session whose only job is to put one
dialog to the user and carry the answer back. It blocks while the user
decides, and you keep working. Name it `Question: <topic>`.

- **Launch** it like a worker, but light: your permission mode and no
  worktree. On Claude, use the resolved Sonnet model, as
  `working-conventions` › Model routing describes; never a Haiku model, even
  though the session is short.
  - In Paseo, give it a local workspace on the run checkout, in the run
    project, even while workers use that checkout, and clear its
    `paseo.parent-agent-id` label as for workers, so the user sees it as a
    thread of its own. Paseo flags it as needing the user when its dialog
    opens.
  - In Claude Code, launch it from the main checkout with
    `claude --bg -n "Question: <topic>" --model <resolved-Sonnet-model> --permission-mode <your mode> "<prompt>"`.
    `claude agents` shows it as waiting for input, and the user answers with
    `claude attach <id>`, so put that command in your push notification.
- **Prompt** it with the finished dialog: each question, its options with
  their consequences, and your recommendation. It calls `AskUserQuestion`
  with exactly those, does nothing else, and sends you the answer verbatim
  with `SendMessage`, with any notes the user typed. Put questions that come
  due together in one session; its dialog takes up to four.
- **Archive** it once its answer arrives. In Paseo, it archives itself: its
  last action is `archive_workspace` on its own workspace, which archives the
  session with it. This is safe: it discards only the thread's agent and
  subagent state, never the directory, worktree or any change in it (the
  result reports `removedDirectory: false`), even when `list_workspaces` shows
  the workspace as `kind: worktree` and a worker is busy in the same run
  checkout. Don't skip it or fall back to `archive_agent` alone out of
  caution; that leaves a stale workspace in the run project. Paseo can reopen
  an archived session that the user is viewing, so check it with
  `get_agent_status` and call `archive_agent` if it is still active. In
  Claude Code, a session can't remove itself; run `claude stop <id>`, then
  `claude rm <id>`. If the user answers some other way, archive the question
  session yourself.
- **Fallback:** if a question session can't be launched or its dialog never
  appears, send the request as a message that leads with it, with a push
  notification, and open your own blocking dialog only when nothing useful
  remains that doesn't depend on the answer.
