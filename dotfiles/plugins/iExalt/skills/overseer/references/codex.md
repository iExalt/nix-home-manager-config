# Overseer workers in Codex

Launch each worker in the background with
`codex exec --json --model <resolved-Sol-model> -c 'model_reasoning_effort="<medium-or-high>"' -C <worktree> -o <reply file> "<brief>"`, using the sandbox
and approval policy the user authorized, and resume it with
`codex exec resume --model <resolved-Sol-model> -c 'model_reasoning_effort="<medium-or-high>"' <session> "<message>"`. Exec mode can't answer an approval
prompt, so a policy that asks for approval blocks the worker.

A Codex overseer's workers reach it with `codex queue` on its session. A
`codex exec` worker exits when its turn ends, so a message queued for it sits
in its history unanswered; reply to an exec worker by resuming it instead.
When a worker has no way to message you, its final message is the channel:
it ends its turn with the request once its independent work is done, and you
resume it with the answer.
