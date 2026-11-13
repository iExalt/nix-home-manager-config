---
name: time-estimate
description: "Estimate the wall-clock time of agent-executed work from the user's measured history, and log estimate against actual when it finishes. Use before starting any task expected to take more than a minute, before giving any time or effort estimate (a task, chunk, phase, plan, campaign or worker brief), when re-estimating after passing the high end, and at completion of estimated work."
---

# Time estimate

Estimate wall-clock time with agents doing the work. Aim for a likely time that lands on the actual
and a range that contains it about half the time, narrowed only by what you have learned about this
task. Durations are skewed: most outcomes cluster near the likely time with a long tail above it, so
give the likely time and the tail, not just two ends. Keep the estimate current while you work:
"how much longer?" matters more than the first guess. Before this skill, agents' gut midpoints ran
about 1.6x high and about half of actuals landed below the range, so the procedure corrects the gut
with measured numbers instead of padding it.

```sh
te() { python3 -I "<this skill's directory>/scripts/estimates.py" "$@"; }   # zsh and bash
te stats              # current factor and percentile multipliers per kind; read before every estimate
te estimate --kind small-fix --low 0.5 --high 1   # gut range in hours -> calibrated numbers + JSON
te remaining --low 0.25 --high 0.5   # mid-task remaining-time gut -> calibrated range + JSON
te log < record.json  # append one validated record when estimated work finishes
te check              # validate the whole log
te stats --backtest   # how this procedure would have scored on past work
te stats --since 2026-11-11 --by harness,model,kind   # how recent stated estimates did, per group
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
   each one. Say which you included, and whether it covers active time already spent: a probe
   is logged as `probe_minutes`, and `actual_h` covers the scope the estimate covers.

## Typical actuals

Typical wall-clock by kind of work, agents doing the work. Start the gut range from the matching
anchor, then adjust for size and for the phases you include; don't start from a human-paced guess.
There is no one-hour floor: a third of logged tasks finished in under 30 minutes.

- A small fix or feature in a codebase the agent knows, one PR with probe, review and CI: 10 to 30 min.
- A larger change to existing code with a concurrent reviewer (a new skill, CLI or feature across
  several files): 0.4 to 1.1 h, even at several hundred lines.
- Bounded operations (audits, cleanups, deletions): 5 to 20 min.
- A read-only inventory or document audit with working tools: 1 to 5 min; broader proof is separate.
- A settled single-file skill or doc edit, warm activation and no CI: 3 to 10 min.
- A campaign phase of independent items: 0.6 to 0.7 h; one with many components, harness and CI
  work: about 5 h.
- Debugging a flaky failure with several causes: about 3 h.

## Form the estimate

1. **Gut range.** Start from the anchor and adjust for what you know. Rules that hold across tasks:
   - Price at agent pace, not human pace: a trimmed rewrite from targeted reads takes minutes, not
     the hours a line-by-line port would.
   - A small one-PR task takes one review round. Multi-increment work takes about two per increment
     plus one or two integration rounds. A round costs the reviewer's latency: use the median
     `te stats` reports for the kind (overall when the kind has too few), else assume 4 to 9
     minutes. Count work that runs in parallel once.
   - Price cold setup (dependency installs, cold builds, new worktrees) and CI separately; they
     dominate small changes.
   - For a performance or "make it faster" goal, price measurement and proof explicitly; it is often
     larger than the code change.
   - Debugging unknown failures takes the top of the range; profile before theorising.
   - Batch `claude -p` runs take seconds each; price evals by setup and mining, not by run count.
2. **Calibrate.** Run `te estimate --kind <kind> --low <gut low> --high <gut high>` (hours). It
   multiplies the gut midpoint √(low × high) by the kind's factor to get the likely time (the
   median), then applies the measured multipliers for p10, p25, p75 and p90, and prints a JSON
   fragment for the record. Apply it even when your gut started from the anchor: the factor was
   fitted on guts formed that way. Logging the gut range as `raw_low_h`/`raw_high_h` lets later fits
   measure your gut, not the correction.
3. **Width.** The range is the p25 to p75 band: it should hold the actual half the time. Narrow it
   only for an unknown a probe settled, and say which. Don't narrow it to look precise, and don't
   widen it as padding. p10 and p90 describe the tails; they are not the range.
4. **Name the drivers.** Say what would put the work near p10 (`why_low`) and what would push it
   toward p90 (`why_high`): the unknowns, which are also what to probe. Take the numbers from the
   calibration, not by adding up delays; summing padded parts made estimates worse in evals.
5. **State it** in a reply the user sees before the work starts: a turn-ending reply, or a
   standalone message before your next tool call. An estimate only in thinking, tool output or the
   completion report doesn't count. Use minutes under an hour and hours with one decimal above,
   never engineer-days, weeks or "sessions". Label any human-effort figure you cite from elsewhere
   as such. Give the likely time, the range, the tails with their drivers, review rounds and the
   phases included, for example: "Likely 25 min, half the time 15 to 40 min; could be as low as 10 if
   the existing test covers the path, or reach about an hour if the dependency install is cold. One
   review round; includes review, CI and merge."

## While working

- Count active time on the estimated scope. Track separately time blocked on the user (approvals,
  permissions, answers, and interruptions such as reboots or being asked to stop) and time spent on
  scope the user added or changed after the estimate.
- Re-estimate the remaining time at checkpoints: after a probe, after each review round, at chunk
  boundaries, and whenever active time passes the high end (stop and re-estimate then). Form a
  remaining-time gut, run `te remaining --low <gut low> --high <gut high>`, and state its range
  as "about R remaining (R1–R2)" with the reason; remaining-time guts have run short. Answer
  "how much longer?" with the latest one.
- Keep each revision as stated at the time (`at`, active `elapsed_h` including added scope, the
  fields `te remaining` printed, `trigger`: probe, round, boundary, overrun or other, and
  `reason`). Keep `raw_remaining_*`: without it the fit corrects the corrected range again.
  Without calibration, log the gut as both `raw_remaining_*` and `remaining_*`. At completion copy
  them into `revisions` from the conversation; if a compaction lost them, omit them. A revision
  reconstructed in hindsight is worse than none. `te stats` reports how remaining-time estimates
  compare with the time that actually remained.
- Log the original estimate, not the latest revision.

## At completion

1. Compare actual active time and review rounds with the estimate; judge the estimate against
   active time alone. When they differ materially, find which assumption failed and what probe
   would have caught it. Give a concrete suggestion for improving future estimates even when the
   actual falls inside the range.
2. Report the estimate next to the actual active, blocked and scope time, review rounds and context
   compactions.
3. Log one record, including for work that stopped or was abandoned (`outcome`), so the log isn't
   biased toward finished work:

```sh
te log <<'EOF'
{"task": "Add retry to the sync client", "repo": "owner/repo", "thread_id": "<your conversation or thread id>",
 "harness": "claude-code", "model": "claude-opus-5-5", "kind": "small-fix",
 "raw_low_h": 0.5, "raw_high_h": 1.0, "bias_factor": 0.56, "est_p10_h": 0.17, "est_low_h": 0.25,
 "est_median_h": 0.39, "est_high_h": 0.68, "est_p90_h": 1.0,
 "why_low": "existing retry helper covers the client", "why_high": "cold install or a second review round",
 "est_rounds_low": 1, "est_rounds_high": 1, "includes": ["impl", "review", "ci", "publish"],
 "probe": true, "probe_minutes": 2, "anchor": "small-fix median 18 min",
 "est_at": "2026-11-09T15:40:00Z", "started_at": "2026-11-09T15:40:00Z", "ended_at": "2026-11-09T16:20:00Z",
 "revisions": [{"at": "2026-11-09T15:55:00Z", "elapsed_h": 0.2, "remaining_low_h": 0.1,
   "remaining_median_h": 0.15, "remaining_high_h": 0.25, "trigger": "round", "reason": "review asked for a jitter test"}],
 "actual_h": 0.4, "actual_rounds": 2, "review_round_minutes": 6, "blocked_h": 0.25, "scope_h": 0, "compactions": 0, "outcome": "done",
 "reasoning": "...", "cause": "...", "lesson": "...", "suggestion": "..."}
EOF
```

- `te log` fills a missing `harness` and `thread_id` from the harness it runs under, and warns when
  `model` is missing or a standalone record skipped `te estimate` although it had data to use. A
  subagent still gives its own `<root thread id>/<agent path>`: the filled id is the session's.
- Paste the numeric fields from `te estimate` as it printed them. To cover another phase, rerun it
  with a gut range that includes the phase rather than editing its numbers. Without calibration,
  still log your gut range as `raw_low_h`/`raw_high_h` (the same as the stated range) and omit
  `bias_factor` and the percentile fields. Only records with a gut range count toward the factor,
  and once 30 calibrated records exist, only those that went through `te estimate`: guts logged
  without it run much closer to the actual, so pooling them leaves calibrated estimates high.
- When the work had review rounds, set `review_round_minutes` to the median minutes from sending a
  revision to receiving the reviewer's verdict; `te stats` reports it per kind once five records
  carry it. Omit it if the send and verdict times aren't in the transcript, since a reconstructed
  value is worse than none, and set it on worker and standalone records, not on a campaign's own.
- `actual_h` is active time; `blocked_h` and `scope_h` are 0 when nothing applies. In a campaign,
  `blocked_h` counts only intervals when no estimated work could advance; work that continued
  during a wait is active. Set `actual_approx` to true when the actual is reconstructed or
  approximate rather than measured.
- In a campaign, each worker sets `parent_id` to the campaign's id, and the coordinator logs the
  campaign's own record with that id as its `thread_id`. Stats then count the campaign once.
- Scope the user adds to a campaign gets one record per amendment, so the added work's estimate is
  scored on its own. Give it `thread_id` `<campaign id>#amend-<n>` and no `parent_id`, so stats count
  it as its own unit. Its stated range is the approved estimate for the tasks it added (the sum of
  their task estimates), and its gut range is the sum of the gut ranges behind them; omit the gut
  range when they weren't recorded. Its `actual_h` is the sum of those tasks' measured active time.
  All are task-hours.
- The campaign's own record keeps the estimate from plan agreement. Parallel tasks make the campaign's
  wall-clock split approximate, so set `scope_h` to its active time times the added tasks' share of
  all tasks' active time, `actual_h` to active time minus `scope_h`, and `actual_approx` to true.
  Log amendment records only when the campaign record counts in stats: `done`, with a gut range.
  Otherwise stats merge the campaign's worker records, which already include the added work, and
  the amendment records would count it twice.
- A subagent without a thread id of its own logs `<root thread id>/<agent path>`, such as
  `<root thread id>/reviewer`; a `parent_id` naming another subagent takes the same form. Bare
  agent paths like `/root/reviewer` repeat across sessions, so `te log` rejects them. When you
  brief a subagent that will log, give it your thread id.
- Keep thread ids and log contents out of public commits and PRs.
- Put a lesson that applies beyond the task in `lesson`; it stays searchable with
  `rg '"lesson"' ~/.local/state/agent-estimates.jsonl`. Change this skill's rules only on evidence
  from several records or `te stats --backtest`.
