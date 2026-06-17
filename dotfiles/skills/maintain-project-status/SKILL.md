---
name: maintain-project-status
description: "Create or maintain an evidence-backed project status document that bridges strategic plans and exhaustive implementation checklists. Use when Codex must reconstruct current progress from plans, Git history, source, tests, benchmarks, artifacts, and worktree state; define intermediate outcome gates and dependencies; distinguish designed, implemented, verified, active, blocked, and future work; recommend the next sequence; track deferrals and risks; or audit unsupported milestone-completion claims."
---

# Maintain Project Status

Create a durable project-status bridge between governing strategy and detailed
implementation tasks. Keep it concise enough to guide current execution without
becoming a duplicate checklist.

Use [assets/status-document-template.md](assets/status-document-template.md) as
the starting structure when creating a document. Adapt headings to the project,
but preserve the evidence, boundary, dependency, and update semantics.

## Core Invariants

- Treat governing plans and contracts as authoritative for intent and milestone
  gates.
- Treat the detailed checklist as authoritative for exhaustive task coverage.
- Treat current source, tests, measurements, and artifacts as authoritative for
  present behavior.
- Use Git history to reconstruct when and why work landed, not as sole proof
  that the current tree still satisfies a claim.
- Never infer milestone completion from partial implementation, checked
  subtasks, code existence, or a passing subset of tests.
- Keep accomplishments evidence-backed and state the incomplete boundary
  explicitly.
- Keep intermediate goals outcome-oriented. Do not copy the low-level
  checklist into the status document.
- Give every final exit condition and cross-component decision exactly one
  owning intermediate goal. Other goals may contribute evidence.
- Preserve unrelated worktree changes and identify evidence that exists only in
  the uncommitted tree.

## Status Model

Track workflow status separately from evidence state.

Workflow status:

- `complete`: the full exit condition has current evidence;
- `active`: implementation or validation is underway;
- `next`: the highest-priority unopened outcome;
- `planned`: sequenced but not started;
- `blocked`: named prerequisites are missing;
- `later`: intentionally outside the current planning horizon.

Evidence state:

- `designed`: a decision or contract exists, but implementation is not proven;
- `implemented`: relevant code or artifacts exist, but the required exit
  verification is incomplete;
- `verified`: the stated exit condition has current, reproducible evidence.

Use `complete` only with `verified`. An active goal may contain a mix of
designed, implemented, and verified deliverables; describe that mix instead of
promoting the whole goal.

## Workflow

### 1. Establish The Document Hierarchy

Identify:

1. governing plans, contracts, milestone definitions, and decision records;
2. exhaustive checklists or issue trackers;
3. the intended status-document path and its readers;
4. repository instructions and the preferred tool runner;
5. the baseline revision, relevant branches, and worktree state.

Read the status document first when updating an existing one. Then inspect its
linked sources and verify that the hierarchy is still accurate.

### 2. Inspect The Evidence Surface

Inspect before writing:

- `git status`, staged and unstaged diffs, and untracked files;
- relevant Git log ranges, commit details, and file history;
- current modules, interfaces, schemas, configuration, and generated outputs;
- scoped tests, fixtures, property tests, and correctness corpora;
- benchmark definitions, retained results, profiles, and machine-readable
  artifacts;
- milestone exit gates, checked checklist items, dependencies, and open
  decisions.

Prefer repository-managed tools and commands. Keep a small evidence ledger:

| Claim | Evidence | Current-tree check | Classification |
| --- | --- | --- | --- |
| Outcome or behavior | Commit, test, module, artifact, or measurement | How it was verified now | designed, implemented, or verified |

Do not attribute pre-existing uncommitted changes to a commit. If evidence is
worktree-only, say so.

### 3. Reconstruct Accomplishments

Group accomplishments by coherent outcome, not by commit chronology. For each
group:

- state what now exists or is proven;
- name concrete evidence such as commit IDs, test names, modules, artifact
  paths, hashes, or benchmark result files;
- verify that referenced commits resolve and paths or symbols still exist;
- distinguish implementation evidence from verification evidence;
- describe a design as a design, not as implemented behavior.

Move an outcome into accomplishments only when the wording is no stronger than
its evidence.

### 4. State The Current Boundary

Write a direct list of what is not complete. Include:

- milestone gates not yet passed;
- missing correctness, measurement, reproducibility, or integration evidence;
- implemented work that remains unverified;
- decisions that remain provisional;
- downstream systems that have not started.

Use explicit negatives. Avoid vague phrases such as "mostly done" or
"essentially complete."

### 5. Define Intermediate Goals

Insert outcome gates between strategic milestones and low-level tasks. Give each
goal:

- a stable ID and outcome-oriented title;
- workflow status and evidence state;
- deliverables;
- dependencies expressed as goal IDs or external evidence prerequisites;
- exit conditions that can be evaluated;
- one decision owner and one exit-condition owner;
- evidence when complete or partially verified.

Keep intermediate goals large enough to represent meaningful outcomes and small
enough to unblock sequencing. A goal should normally combine related checklist
tasks that produce one reviewable capability, evidence package, or decision.

### 6. Audit Dependencies And Claims

Perform these checks before recommending work:

1. **Dependency cycles:** Build a directed graph from each goal to its
   prerequisites. A valid next goal must have all required incoming evidence.
   If no unfinished goal can become ready, report the cycle. Resolve it by
   splitting out a bounded spike, shared evidence prerequisite, or explicit
   decision gate; do not hide the cycle by changing labels.
2. **Exit ownership conflicts:** Map every exit condition and final decision to
   one owning goal. If two goals claim the same final selection or gate,
   designate one owner and make the other an evidence contributor.
3. **Unsupported completion:** For every `complete` or `verified` claim, locate
   current evidence for every exit-condition clause. Downgrade the claim when
   any clause is missing.
4. **Premature starts:** For every `active` goal, verify its evidence
   prerequisites. Mark it blocked when prerequisites are absent. Allow only
   explicitly bounded, discardable spikes to proceed early, and state the limit
   and the later decision gate.
5. **Checklist drift:** Compare status claims with checked tasks and milestone
   exit gates. Checked subtasks may support an accomplishment but cannot
   override an incomplete exit gate.

### 7. Recommend The Next Sequence

Recommend normally three to seven concrete steps. Order them by dependency and
evidence production, not by convenience. Explain any bounded parallelism or
early spike that intentionally crosses a milestone boundary.

List explicitly deferred work separately. Name the missing prerequisite or
intermediate exit condition for each deferred group.

### 8. Track Risks Without Duplicating Tasks

Track only active risks, provisional decisions, and evidence gaps that can
change sequencing or invalidate a claim. For each risk, state:

- the observed evidence or uncertainty;
- the consequence;
- mitigation or next evidence needed;
- decision owner when applicable.

Remove resolved risks or record their resolution in the progress log. Leave
exhaustive implementation tasks in the checklist.

### 9. Write Or Update The Document

When creating:

- establish the initial baseline revision and date;
- populate every template section;
- link to the governing plan and checklist;
- add reciprocal relative links from those documents when the status document
  is durable and belongs in their normal navigation.

When updating:

- inspect changes since the recorded baseline plus current worktree changes;
- update the snapshot and current boundary;
- move only newly evidenced outcomes into accomplishments;
- revise goal status, dependencies, and decisions;
- replace the recommended sequence and active risk set;
- append a dated progress-log entry;
- preserve prior log entries unless correcting a documented factual error.

Update after a meaningful implementation increment, changed decision, measured
result, newly discovered blocker, or invalidated claim. Do not churn the
document for inconsequential edits.

### 10. Verify Before Finishing

Verify:

- Markdown formatting with the repository's configured formatter or linter;
- every local link and referenced artifact path;
- commit IDs, baseline revision, test names, module names, counts, hashes, and
  measurement claims;
- each `complete` goal against every exit-condition clause;
- dependency acyclicity and unique exit-condition ownership;
- relevant scoped tests and benchmark/result validation;
- `git diff --check` and the final worktree diff.

Record exact commands and results in the handoff or progress log when useful.
If a relevant test or factual claim cannot be verified, state that limitation
and do not classify the affected outcome as verified.

## Output Standard

Finish with:

- the status-document path;
- the baseline and evidence sources inspected;
- the current boundary and recommended next sequence;
- verification performed and any unverified claims;
- any reciprocal plan or checklist links added.

Do not report a milestone as complete unless its authoritative exit gate is
fully satisfied with current evidence.
