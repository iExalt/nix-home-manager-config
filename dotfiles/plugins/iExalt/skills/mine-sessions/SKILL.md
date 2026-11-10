---
name: mine-sessions
description: "Search, mine, read or audit past Claude Code and Codex session history: find sessions where the user asked for something, used a skill or hit a problem; read a session from a uuid, codex://threads link, Paseo id or title; split many sessions across miner subagents; and recover your own session's state after compaction. Use whenever a task says past/previous/other sessions, transcripts, threads, chat history, \"search history\", \"mine\", or names a session to read."
---

# Mine sessions

Past sessions are 10+ GB of JSONL in several formats. Raw `rg`, `jq`, `head` and `sed` on them flood
context (one line can be megabytes), confuse injected text with what the user typed, and miss
archived or continued sessions. Use the bundled CLI instead; it is stdlib Python 3.9+:

```sh
sm() { python3 -I "<this skill's directory>/scripts/sessions.py" "$@"; }   # works in zsh and bash
sm stores                       # where history lives, sizes, date ranges
sm resolve <ref>                # uuid, id prefix/suffix, codex://threads/<id>, Paseo id, path or title words
sm find [regex] [--skill X]     # sessions by title or prompt text, newest first
sm grep <regex> [filters]       # events across all sessions, grouped by session
sm show <ref> [filters]         # one session, one line per event, with file:line
sm show <ref> --lines 240:285   # read events at physical lines 240 through 285
sm manifest [find args] --out m.tsv   # byte-balanced shards for miner subagents
sm recall                       # your own session after compaction
```

Every command caps its output (`--max-bytes`, default 8000, footer included) and ends with `#` lines
stating coverage. Read the footer before drawing a conclusion: it says what was not searched.

## Workflow

1. **Scope the question.** Write down what counts as a match, which sessions are in scope (dates,
   projects, providers) and whether the user's own words, agents' messages or tool output matter.
2. **Look before you pattern.** First search for the question itself (`grep '<key words>'
   --author human --sessions-only`): it may have been asked and answered before. Then run `find` or
   `grep --sessions-only` with a first guess, and `show` two or three hits to see how the thing you
   want actually appears. Refine the pattern and filters on what you saw, not on what you expected.
3. **Use the filters, not the raw text.**
   - `--author human` keeps what the user typed or decided (question answers, plan approvals,
     rejections). `agent`, `injected`, `harness`, `assistant` and `tool` are the other authors.
   - `--skill NAME` finds actual invocations (slash command, Skill tool call, Codex skill block).
     A skill's name appears in every session's skill list, so a keyword search for it is mostly noise.
     Invocations are mostly the assistant's tool calls, so don't combine `--skill` with `--author human`.
   - `--kind prompt|reply|tool_call|tool_result|decision|thinking|compaction`, `--tool`, `--since`,
     `--until`, `--project`, `--provider`. Lists can be comma-separated.
   - grep reads prompts, replies, tool-call commands and decisions from a cache by default. Add
     `--full` (or `--kind tool_result`) to search tool output and thinking; that reads transcripts
     directly and can hit the time budget.
   - `show` starts at the top of a session, which is mostly injected context. To see what happened,
     narrow it: `--author human,assistant --kind prompt,reply`, `--last N`, `--match <regex>`. Lines
     are clipped to `--width` (default 160); to quote a whole event, use `--lines N --width 5000` and
     a `--max-bytes` above the width.
   - Hits in spawned agents are labelled `subagent of <session>` (Claude) or `sub-agent of <thread>`
     (Codex). `show <ref> --subagents` reads a session together with the agents it spawned.
   - `resolve` and `find` titles are current, not as of a date; `find --until T` keeps sessions that
     started before T but shows their whole span. For "as of T" questions, check candidates with
     `show <id> --until T --last 5`. A `(sub-agent of …)` mark means a thread another agent spawned.
4. **Size the job.** Read sessions yourself with `show` when `find` returns about 20 or fewer. For
   more, run `manifest --out <file>` and give each shard to one miner subagent with
   [references/miner-brief.md](references/miner-brief.md). Do not let each miner rediscover stores or
   write its own extractor.
5. **Verify before reporting.** Single-pass miners have been 15 to 35% precise on judgment questions.
   For findings from miners, re-read each at its `file:line` with `show <ref> --lines N --width 5000`
   (or have a second agent do it) before it reaches the user. For your own reading, check each claim
   against the full event, not the clipped line you first saw.
6. **Report coverage.** State sessions matched, read, sampled and skipped, any footer marked
   `INCOMPLETE` or `NOT PARSED`, the caller exclusion, and the false-positive rate where measured.
   Quote the user only from `--author human` events.

## Your own session

The caller's session tree is excluded from `grep`, `find` and `manifest` by default (via
`CLAUDE_CODE_SESSION_ID`, Paseo labels, or the single live Codex rollout in the working directory).
Each command refreshes ancestry and excludes descendants across native and Paseo launches,
including sessions created after a cache build. `--include-self` disables automatic exclusion;
`--exclude-session <id>` still excludes that session and its descendants.
The footer names what was excluded; if it lists several live Codex rollouts, pass
`--exclude-session <id>` for yours. After compaction, run `recall` for the user's latest prompts and
decisions, the agents you spawned and messaged, skills invoked and your latest tool calls. Codex has
no session id in its environment: pass `recall --session <id>`.

## Budgets and the cache

Commands that read many files stop at `--budget` seconds (default 8, under Codex's 10 s command
yield) and report files left unread. The prose cache lives in `~/.cache/session-mining/`. It is
user-only because it copies transcript text, secrets included, and takes about 0.6 GB for 14 GB of
transcripts. A cold build takes 10 to 30 s, so run `cache refresh` once in the background before a
large job; later commands index only changed files. `cache purge` deletes it.

## Limits

Read [references/stores.md](references/stores.md) when a result looks wrong: it explains the formats,
how authors are decided and the known misattributions (scripted SDK prompts, codex-tui sub-agent
follow-ups, rewound Claude turns, pruned transcripts). For shell work outside the CLI, read
[references/shell-traps.md](references/shell-traps.md) first.
