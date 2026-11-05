# Ask through a question session

A question session is a short-lived session whose only job is to put one
dialog to the user and carry the answer back. It blocks while the user
decides, and you keep working. Name it `Question: <topic>`.

- **Launch** it like a worker, but light: your permission mode and no
  worktree. On Claude, use the resolved Sonnet model, as
  `working-conventions` › Model routing describes; never a Haiku model, even
  though the session is short.
  - In Paseo, give it a local workspace on the run checkout, in the run
    project, even while workers use that checkout, and launch it with
    `--relationship detached` as for workers, so the user sees it as a
    thread of its own. Paseo flags it as needing the user when its dialog
    opens.
  - In Claude Code, launch it from the main checkout with
    `claude --bg -n "Question: <topic>" --model <resolved-Sonnet-model> --permission-mode <your mode> "<prompt>"`.
    `claude agents` shows it as waiting for input, and the user answers with
    `claude attach <id>`, so put that command in your push notification.
- **Prompt** it with the finished dialog: each question, its options with
  their consequences, and your recommendation. It calls `AskUserQuestion`
  with exactly those, does nothing else, and sends you the answer verbatim,
  with any notes the user typed: in Paseo with
  `paseo agent send --no-wait --if-running queue --no-notify-on-finish <your agent ID> "<answer>"`,
  otherwise with `SendMessage`. Put questions that come
  due together in one session; its dialog takes up to four.
- **Archive** it once its answer arrives. In Paseo, its last action is
  `paseo workspace archive <workspace-id>` on its own workspace, which keeps
  the directory. Then check it with `paseo agent status <agent-id>`, and if
  Paseo reopened it, run `paseo agent archive --force <agent-id>`. In Claude Code, run
  `claude stop <id>`, then `claude rm <id>`. If the user answers some other
  way, archive it yourself.
- **Fallback:** if a question session can't be launched or its dialog never
  appears, send the request as a message that leads with it, with a push
  notification, and open your own blocking dialog only when nothing useful
  remains that doesn't depend on the answer.
