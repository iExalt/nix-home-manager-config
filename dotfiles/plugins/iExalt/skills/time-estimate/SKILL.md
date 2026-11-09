---
name: time-estimate
description: "Estimate the wall-clock time of agent-executed work from the user's measured history, and log estimate against actual when it finishes. Use before giving any time or effort estimate (a task, chunk, phase, plan, campaign or worker brief), when re-estimating after passing the high end, and at completion of estimated work."
---

# Time estimate

Estimate wall-clock time with agents doing the work. Aim for a midpoint that lands on the actual
and a range that contains it about half the time, narrowed only by what you have learned about this
task. History says agents' gut midpoints run about 1.6x high and the typical actual lands at the
bottom of the range, so the procedure corrects the gut with measured numbers instead of padding it.

```sh
te() { python3 -I "<this skill's directory>/scripts/estimates.py" "$@"; }   # zsh and bash
te stats              # current factor and 50% spread per kind; read before every estimate
te log < record.json  # append one validated record when estimated work finishes
te check              # validate the whole log
te stats --backtest   # how this procedure would have scored on past work
```

The log is private JSONL at `~/.local/state/agent-estimates.jsonl` (override with
`TIME_ESTIMATE_LOG`). `~/.local/state/agent-estimates.md` is the archive of entries before
2026-11-09, ported into the JSONL; search it for context but don't append to it.

## Kinds

| Kind | Work |
| --- | --- |
| `small-fix` | One small fix or feature in a codebase the agent knows; one PR |
| `existing-code` | A larger change on existing code, patterns or contracts; several increments |
| `multi-component` | Work spanning components, or a campaign phase or thread |
| `bounded-operation` | Operations with a known end: cleanups, installs, reloads, releases, data moves |
| `audit` | Read-only review, inventory or evidence audit |
| `investigation` | Debugging flakes or unknown failures, root-cause work |
| `planning` | Plans, designs and proposals without implementation |
| `docs` | Skill, doc and prose edits with no executable code |
| `eval` | Agent-driven evals, benchmarks, batch LLM runs and measurement experiments |

## Before estimating

1. Run `te stats` and pick the kind. Its median actual for that kind is your anchor.
2. Probe the biggest unknown first when the probe takes under five minutes: size the call sites,
   fixtures and caller inventory; check whether dependencies and builds are warm, and whether push,
   signing and CI access work. A quick probe beats padding.
3. Decide which phases the estimate includes (`impl`, `review`, `ci`, `publish`, `proof`) and price
   each one. Say which you included.

## Form the estimate

1. **Gut range.** Start from the anchor and adjust for what you know. Rules that hold across tasks:
   - Price at agent pace, not human pace: a trimmed rewrite from targeted reads takes minutes, not
     the hours a line-by-line port would.
   - A small one-PR task takes one review round. Multi-increment work takes about two per increment
     plus one or two integration rounds. Count work that runs in parallel once.
   - Price cold setup (dependency installs, cold builds, new worktrees) and CI separately; they
     dominate small changes.
   - For a performance or "make it faster" goal, price measurement and proof explicitly; it is often
     larger than the code change.
   - Debugging unknown failures takes the top of the range; profile before theorising.
   - Batch `claude -p` runs take seconds each; price evals by setup and mining, not by run count.
2. **Debias.** Midpoint = gut midpoint × the kind's factor from `te stats`, where the gut midpoint
   is the geometric mean √(low × high). Keep the gut range: you log it as `raw_low_h`/`raw_high_h`
   with the factor as `bias_factor`, so later fits measure your gut, not the correction.
3. **Width.** Range = midpoint × [low, high] from `te stats`. Narrow it only for an unknown a probe
   settled, and say which. Don't narrow a range to look precise, and don't widen it as padding.
4. **State it** in minutes under an hour and hours with one decimal above, never engineer-days,
   weeks or "sessions". Label any human-effort figure you cite from elsewhere as such. Give the
   range, review rounds, what bounds it and the phases included, for example: "20–35 min, one
   review round, bounded by the cold build; includes review, CI and merge."

## While working

- Count active time on the estimated scope. Track separately time blocked on the user (approvals,
  permissions, answers, and interruptions such as reboots or being asked to stop) and time spent on
  scope the user added or changed after the estimate.
- When active time passes the high end, stop and re-estimate what remains, with the reason. Log the
  original estimate at completion and put the revision in `reasoning`.

## At completion

1. Compare actual active time and review rounds with the estimate. When they differ materially,
   find which assumption failed and what probe would have caught it. Give a concrete suggestion for
   improving future estimates even when the actual falls inside the range.
2. Report the estimate next to the actual active, blocked and scope time, review rounds and context
   compactions.
3. Log one record, including for work that stopped or was abandoned (`outcome`), so the log isn't
   biased toward finished work:

```sh
te log <<'EOF'
{"task": "Add retry to the sync client", "repo": "owner/repo", "thread_id": "<your conversation or thread id>",
 "harness": "claude-code", "model": "claude-opus-5-5", "kind": "small-fix",
 "raw_low_h": 0.5, "raw_high_h": 1.0, "bias_factor": 0.6, "est_low_h": 0.3, "est_high_h": 0.6,
 "est_rounds_low": 1, "est_rounds_high": 1, "includes": ["impl", "review", "ci", "publish"],
 "probe": true, "probe_minutes": 2, "anchor": "small-fix median 25m",
 "est_at": "2026-11-09T15:40:00Z", "started_at": "2026-11-09T15:40:00Z", "ended_at": "2026-11-09T16:20:00Z",
 "actual_h": 0.4, "actual_rounds": 2, "blocked_h": 0.25, "scope_h": 0, "compactions": 0, "outcome": "done",
 "reasoning": "...", "cause": "...", "lesson": "...", "suggestion": "..."}
EOF
```

- Without debiasing, omit the `raw_*` fields and `bias_factor`.
- `actual_h` is active time; `blocked_h` and `scope_h` are 0 when nothing applies.
- In a campaign, each worker sets `parent_id` to the campaign's id, and the coordinator logs the
  campaign's own record with that id as its `thread_id`. Stats then count the campaign once.
- Keep thread ids and log contents out of public commits and PRs.
- Put a lesson that applies beyond the task in `lesson`; it stays searchable with
  `rg '"lesson"' ~/.local/state/agent-estimates.jsonl`. Change this skill's rules only on evidence
  from several records or `te stats --backtest`.
