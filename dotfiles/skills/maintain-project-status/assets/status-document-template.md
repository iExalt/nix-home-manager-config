# [Project Or Workstream] Status

Last updated: [YYYY-MM-DD]

## Purpose

This document is the working bridge between:

- governing plan or contract: `[replace with a relative Markdown link]`, and
- detailed implementation checklist: `[replace with a relative Markdown link]`.

It records the evidence-backed current state, incomplete boundary, intermediate
outcome gates, dependencies, next sequence, deferrals, and active risks. It is
not a second exhaustive checklist.

## Current Snapshot

| Field | Status |
| --- | --- |
| Baseline | `[revision, release, or dated artifact]` |
| Current phase | [milestone plus any explicitly bounded overlap] |
| Overall state | [one evidence-calibrated sentence] |
| Immediate focus | [highest-priority outcome] |
| Product or release readiness | [explicitly state which claims are not yet justified] |
| Worktree state | [clean, or summarize relevant staged, unstaged, and untracked evidence] |

[Summarize the transition from established foundations to the largest remaining
gap. Do not imply that partial progress passes a milestone gate.]

## Accomplishments With Evidence

### [Outcome Group]

Evidence state: verified.

- [Implemented or proven outcome.]
- [Important scope or invariant.]

Evidence:

- Commit: `[commit ID and subject]`
- Current source: `[module, symbol, or path]`
- Verification: `[test, command, artifact, hash, or measured result]`

### [Designed Or Implemented But Not Fully Verified Outcome]

Evidence state: designed | implemented.

- [State exactly what exists.]
- [State the verification that remains.]

Evidence:

- [Decision record, source path, partial test, or worktree-only artifact]

## Current Boundary

The following are not complete:

- [Authoritative milestone exit gate has not passed.]
- [Implemented capability lacks named verification.]
- [Required artifact, profile, fixture, or measurement is missing.]
- [Decision remains provisional.]
- [Downstream subsystem has not started.]

## Intermediate Goals

### I0 - [Outcome-Oriented Goal]

Workflow status: complete | active | next | planned | blocked | later.

Evidence state: designed | implemented | verified.

Decision owner: [person, team, role, or governing document].

Exit-condition owner: I0.

Dependencies:

- [Goal ID or external evidence prerequisite.]

Deliverables:

- [Reviewable capability, artifact, or decision.]
- [Required correctness or measurement evidence.]

Exit conditions:

- [Binary, evidence-backed condition.]
- [Binary, evidence-backed condition.]

Evidence:

- [Required when complete; include partial evidence for active goals.]

### I1 - [Next Outcome-Oriented Goal]

Workflow status: next.

Evidence state: designed.

Decision owner: [owner].

Exit-condition owner: I1.

Dependencies:

- I0: [specific evidence required, not merely "completion"].

Deliverables:

- [Deliverable.]

Exit conditions:

- [Condition.]

Evidence:

- None yet.

## Recommended Next Sequence

1. [Produce the first missing prerequisite or verification evidence.]
2. [Complete the next dependency-ready outcome.]
3. [Freeze or record the resulting decision.]
4. [Run the next integrated or milestone gate.]

[Explain bounded parallel work or an intentionally early, discardable spike.]

## Explicitly Deferred

Do not start these until their named prerequisites exist:

- **[Deferred work]:** blocked on [goal ID, artifact, decision, or exit
  condition].
- **[Deferred work]:** blocked on [prerequisite].

## Active Risks And Decisions

| Risk or decision | Evidence or uncertainty | Consequence | Mitigation or next evidence | Owner |
| --- | --- | --- | --- | --- |
| [Risk] | [Observed fact or missing evidence] | [Impact on correctness, sequence, or feasibility] | [Concrete validation or decision] | [Owner] |

## Update Protocol

Update this document after a meaningful implementation increment, changed
decision, measured result, newly discovered blocker, or invalidated claim.

For each update:

1. change the date, baseline, worktree state, and current snapshot;
2. move outcomes into accomplishments only when the wording matches evidence;
3. update workflow status and evidence state independently;
4. recheck dependencies, cycles, exit-condition ownership, and prerequisites;
5. replace the recommended sequence with three to seven concrete steps;
6. update deferrals, active risks, blocked decisions, and measured results;
7. append a dated progress-log entry; and
8. keep low-level tasks in the detailed checklist.

Status terms:

- **complete:** the full exit condition has current evidence;
- **active:** implementation or validation is underway;
- **next:** the highest-priority unopened outcome;
- **planned:** sequenced but not started;
- **blocked:** named prerequisites are missing;
- **later:** outside the current planning horizon;
- **designed:** a decision or contract exists without proven implementation;
- **implemented:** code or artifacts exist without full exit verification; and
- **verified:** the exit condition has current, reproducible evidence.

## Progress Log

### [YYYY-MM-DD]

- [Established or updated baseline through revision or artifact.]
- [Newly verified accomplishment with evidence.]
- [Changed boundary, decision, dependency, or risk.]
- [Verification commands and concise results.]
