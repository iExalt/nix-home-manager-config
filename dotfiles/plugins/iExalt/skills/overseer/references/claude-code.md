# Overseer workers in Claude Code

Launch each worker as a background session from its worktree:

```sh
cd ../<repo>-worker-<slug>
claude --bg -n "Worker: <subtask>" --model <resolved-Sonnet-model> --effort <medium-or-high> --permission-mode <your mode> "<brief>"
```

- **Trust:** the launch fails with "Workspace not trusted" unless the
  worktree or a parent directory is trusted, as `~/Projects` may be. If it
  fails, launch from the main checkout with `claude --bg -w <slug>` instead,
  which creates a worktree inside the repository at `.claude/worktrees/<slug>`;
  never stage `.claude/` in the main checkout.
- **Address:** your session name, as `ListAgents` shows it. Workers message
  you with `SendMessage`, and you reach a worker by its name; it arrives after
  the receiver's current tool call. Use a session reference where supported,
  otherwise a peer name you verified is unique in `ListAgents`, and recheck
  it after a resume. A Codex session can't message a Claude Code one; see
  [codex.md](codex.md).
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
