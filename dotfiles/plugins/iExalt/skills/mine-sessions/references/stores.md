# Stores, formats and attribution

## Where history lives

| Store | Path | Notes |
| --- | --- | --- |
| Claude sessions | `~/.claude/projects/<project>/<session>.jsonl` | `<project>` is the cwd with `/` → `-`. Claude prunes old sessions. |
| Claude subagents | `~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl` | `tool-results/` and `memory/` beside them are not transcripts. |
| Codex rollouts | `~/.codex/sessions/YYYY/MM/DD/rollout-<ts>-<thread>.jsonl` | `rollout-<ts>-<thread>_<segment>.jsonl` continues the same thread. |
| Codex archive | `~/.codex/archived_sessions/` | Threads move here when archived; search both trees. |
| Codex state db | `~/.codex/state_<n>.sqlite` | `threads`: title, first prompt, cwd, archived, source (52% are guardian reviews); `thread_spawn_edges`: parent → child. Opened read-only. |
| Codex summaries | `~/.codex/memories/rollout_summaries/` | Short per-thread summaries; quick orientation. |
| Paseo agents | `~/.paseo/agents/<project>/<agent>.json` | Metadata only: title, cwd, labels, provider `sessionId`. Short Paseo ids are prefixes of the agent id, not of the session id. |

Codex ids are UUIDv7: an 8-character prefix is a roughly one-minute timestamp bucket, so `resolve`
lists every candidate and never picks one silently.

## How authors are decided

- **Claude.** User-role text is classified by its origin field and known prefixes:
  - Task notifications, interrupts, system reminders and compaction summaries are `harness`.
  - Skill bodies, CLAUDE.md/AGENTS.md attachments and hook context are `injected`.
  - Paseo agent messages, peers, coordinators and subagent briefs are `agent`.
  - Question answers, plan approvals and rejections recorded in tool results are `human` decisions.
- **Codex.** A user-role message is human only when Codex also logged it as a `UserMessage` item. A
  message without that item is injected context (AGENTS.md, environment, skills). Paseo envelopes
  are `agent`, or `harness` for agent notifications. Fork-inherited records and guardian
  auto-review rollouts are skipped; pass `--include-guardian` (direct reads only) to see guardian
  rollouts.
- **First prompts.** An SDK session's first prompt counts as `agent` when Paseo labels show another
  agent launched it, `harness` for a Paseo schedule, and `human` for a Paseo session the user
  started. With no Paseo record at all it counts as `agent`, because it was sent by a script.
- `--basis` on `show` and `grep` prints the rule behind each author.

## What transcripts do not contain

- Codex messages between agents are often sealed: their payload shows as `[encrypted payload]`, and
  `show` counts them in its footer. The sender's and receiver's own turns are still readable.
- Claude rewinds and edits leave the abandoned turns in the file.

## Known misattributions

- Scripted SDK prompts sent to a session with a Paseo record count as human.
- In codex-tui, a sub-agent's follow-up messages without `client_id` may come from the parent agent
  or from the user. They carry the basis `subagent_followup_maybe_agent`; Codex Desktop follow-ups
  without `client_id` count as agent.
- Rewound Claude turns are not marked, so an abandoned prompt still counts as human.
- An orphan Codex `UserMessage` (no response item) counts as human. Codex's built-in review prompt
  appears this way.
- A Paseo record whose transcript was pruned resolves to "transcript pruned". Its session is gone,
  not missing from the index.
- Events without a timestamp pass `--since` and `--until`.

## Citations

`file:line` is the physical line in the transcript file. Live sessions keep growing, so cite
promptly, and freeze a copy if you need stable line numbers across a long job. Claude records copied
into resumed or forked sessions are deduplicated to the owner's file: the file named after the
record's session id, then the earliest.
