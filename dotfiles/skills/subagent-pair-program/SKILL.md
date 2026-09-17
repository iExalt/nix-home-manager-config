---
name: subagent-pair-program
description: "Coordinate autonomous pair programming with the main agent as navigator and one or more subagents as implementation pilots. Use when the user wants delegated implementation with agent-to-agent proposal, review, and verification loops without approving each increment. For interactive sessions where the user navigates, use pair-program instead."
---

# Subagent Pair Program

Act as the navigator: own the design, task checklist, pilot assignments, review,
and final acceptance. Delegate implementation to one or more subagent pilots.
Pilots propose changes, implement approved increments, verify them, and walk you
through the result. Keep this loop between agents; do not ask the user to approve
routine increments or attend code walkthroughs.

This workflow requires subagent tools. If they are unavailable, report the
limitation instead of claiming to have delegated or independently reviewed work.

## Work Item Size

Treat repository milestones as roadmap context, not assignments to either the
main agent or a delegated lead. Select one component-level checklist item for
active execution. Group a few only when they share a tightly coupled implementation
boundary and a common acceptance check; a shared milestone label is insufficient.
Split umbrella checkboxes with independent outcomes or unresolved design decisions.

Batch related compiler repairs and mechanical migrations within that item rather
than requiring one approval per error. Keep small increments for uncertain or
risky semantics. If the boundary cannot yet be specified, assign discovery that
returns a proposed item before authorizing implementation. Independent items may
run concurrently when dependencies, ownership, and available resources permit.

## Optional Work Item Lead

Use direct navigator-to-pilot coordination for straightforward items. When one
item needs substantial coordination or repair/review iteration, delegate its
local navigator duties to a GPT-5.6 Sol lead, with Luna high implementation
pilots, unless the user specifies otherwise. Start Sol at medium for routine
coordination; use high for substantive review or complex implementation decisions,
such as ownership, concurrency, and lifecycle reasoning. Verify model/tool
availability and honor current spawn semantics; use an explicit brief and limited context instead
of assuming a full-history fork supports model overrides. If unavailable, retain
direct coordination and disclose the limitation.

The main navigator selects the item, defines its acceptance boundary, owns the
user-visible checklist and cross-item design, and makes final acceptance decisions.
The lead may decompose that item, approve routine pilot proposals, review diffs,
direct in-scope repairs, and coordinate verification. Name the lead as the pilots'
approval and reporting recipient. Explicitly coordinate any permission to spawn
pilots, file ownership, and the total team size; a lead consumes a slot that could
otherwise hold a pilot. Do not add a management layer without useful work for it.

Escalate changed architecture, scope, acceptance criteria, ownership conflicts,
external-action authorization, or repeated failure of the approach to the main
navigator. The lead returns after its assigned item; it cannot take another
checkbox from the backlog without a new assignment. Reuse its context for related
items when useful, but renew the boundary explicitly. Routine next-item selection
remains autonomous and does not require user approval.

## Navigator Loop

1. Establish the user's goal, constraints, and completion criteria. Inspect the
   workspace, applicable instructions, relevant source, and existing changes.
   As the main agent, maintain a user-visible checklist covering implementation,
   review, and verification. Show it before assigning the first increment using
   a user-visible plan tool when available, or a concise Markdown checklist in
   progress updates. Keep ownership of this checklist rather than relying on
   pilot checklists or private agent messages. Update it when work starts, awaits
   review, completes, becomes blocked, or changes scope, so the user can see
   completed, current, and remaining work at a glance. Mark items complete only
   after required verification and navigator acceptance; show the final state
   at handoff. These updates do not require user approval.
   Distinguish implemented or staged work from integrated, verified, accepted work.
2. Select a bounded work item with an observable acceptance result.
   Use one pilot for tightly coupled work. Add pilots when bounded tasks can run
   independently alongside useful navigator work; identify dependencies and file
   ownership before parallelizing.
3. Give each pilot a concrete assignment with:
   - The desired behavior and acceptance criteria.
   - The checklist item, exclusions, tolerances, and conditions for escalation.
   - Relevant source context, constraints, and applicable instructions.
   - The workspace or worktree and files or components it may change.
   - Known concurrent work and dependencies.
   - Expected verification and a requirement to propose its approach before edits.
   - A named reviewer/approver: you or the delegated work item lead. Direct
     proposals and questions there and wait for approval before implementation.
4. Review the pilot's proposal against the source and overall design. Resolve
   tradeoffs yourself within the user's authorized scope. Approve the specific
   increment and verification, or send concrete revisions. An assignment that
   already supplies and explicitly approves a complete approach can serve as
   approval; do not require a redundant exchange. A delegated lead performs
   this routine review within the main navigator's approved boundary.
5. While the pilot implements, inspect affected interfaces, resolve upcoming
   design questions, or review other independent increments. Keep implementation
   ownership with pilots rather than editing their assigned files concurrently.
6. Review the actual diff and verification evidence when the pilot returns.
   Require a proportional code walkthrough, investigate unsupported claims, and
   return actionable corrections to the responsible pilot. A pilot's completion
   message alone does not establish acceptance. With a lead, keep detailed pilot
   walkthroughs and routine correction loops there. The main navigator reviews
   the acceptance packet, critical interfaces and risks, and relevant integrated
   diff/evidence without repeating the entire delegated review by default.
7. The main navigator accepts the work item only when its behavior and checks
   satisfy the criteria, including any required integration. Update the checklist,
   release dependent work, and explicitly assign the next item.
   Reuse pilots when their retained context is useful.
8. After the increments are accepted, inspect the combined result and run or
   direct appropriate integration checks. Resolve failures through the same
   review loop. Continue until the user's completion criteria are met or a
   concrete blocker prevents further authorized progress.

## Pilot Contract

Include these expectations in pilot assignments; do not assume pilots inherit
this skill or the navigator's full context. Here, navigator means the named
approver for the assignment, including a delegated lead when designated:

- Inspect the assigned source before proposing behavior, affected files,
  implementation approach, tradeoffs, and verification.
- Wait for navigator approval before changing files. Before editing, recheck
  the relevant source and working-tree changes to preserve concurrent work.
- Implement only the approved increment. If findings materially change the
  scope, design, dependencies, or file ownership, bring a revised proposal to
  the navigator before proceeding.
- Fix routine compiler/test failures within the approved item without a new
  proposal for each mechanical repair. Do not absorb adjacent checklist items.
- Run focused checks and report exact commands, outcomes, and any checks that
  could not run. Explain failures without silently broadening the fix.
- Return a walkthrough with file and symbol references, important control and
  data flow, invariants, error behavior, design tradeoffs, and remaining risks.
  Scale the explanation to the change; a diffstat is not a review handoff.
- Challenge navigator directions when source evidence indicates correctness,
  security, maintenance, or scope problems. Recommend an alternative and let
  the navigator resolve the decision within applicable constraints.
- Send questions and blockers to the navigator, not the user. Do not create
  additional pilots or reassign ownership without navigator coordination.

## Acceptance Evidence and Context

Return a compact acceptance packet: checklist item, revision or diff identity,
changed behavior and interfaces, verification commands/results and artifact paths,
remaining risks, and any decision needed. Keep raw logs and detailed walkthroughs
in pilot/lead context or linked artifacts. Concision must not omit failed checks,
partial evidence, or material correctness concerns.

Give each validation run one owner. Record its source identity, configuration,
environment, result, and evidence location. Reuse applicable receipts; invalidate
affected evidence when source, dependencies, configuration, or environment changes.
Do not rerun a broad suite solely because an agent hands off or resumes work.
Preserve independent review of ownership, lifecycle, and cross-language contracts;
focused passing tests do not establish integrated correctness.

Before long experiments, agree on required acceptance versus optional investigation,
check feasibility on a representative small workload, and estimate setup, build,
execution, drain, and analysis time. Use explicit stop conditions for exploration;
do not silently weaken acceptance, enlarge a sweep, or replace a required statistical
campaign with an underpowered probe. Revise a failed approach rather than retrying
unchanged work indefinitely.

For long processes, use completion notifications where supported. Otherwise name
one monitor with a workload-appropriate cadence, stall/failure conditions, and a
run handle. A Luna low watcher can handle routine monitoring when available and
consistent with the user's model choices. Respect tool wait limits. The main agent
should not duplicate polling or restart finished pilots for unchanged status.

Keep a compact checkpoint for interruption or handoff: current item and acceptance
boundary, accepted revisions, outstanding diffs and owners, active processes,
validation receipts, next action, and unresolved decisions. Recheck current state
on resume instead of repeating broad discovery. Reset an agent with this brief
when obsolete context outweighs useful continuity.

## Concurrent Work and Integration

- Give shared files one active writer. Serialize overlapping changes or isolate
  them in worktrees with an explicit integration owner and sequence. Include
  generated files and shared configuration when assessing overlap.
- In a shared workspace, pilot edits are already visible; review them in place.
  For isolated worktrees, identify the accepted patch or commits and integrate
  them deliberately. Do not apply the same changes twice.
- Coordinate broad formatters, generators, dependency updates, and Git mutations
  so they cannot race with another pilot's work. Assign integration edits to a
  pilot with clear ownership and review them before acceptance.
- When the design or user direction changes, pause affected pilots, reconcile
  their in-progress edits, and send updated assignments before resuming.
- Schedule builds and benchmarks against actual CPU/GPU, memory, disk, and shared
  cache constraints. Prefer source-only staging over copying build artifacts.
  Track temporary artifact ownership and retention; clean only task-owned
  disposable data within applicable authorization.

## Autonomy and Completion

The navigator supplies routine implementation approvals. Keep the user informed
of meaningful progress and outcomes without turning updates into approval gates.
Ask the user only when missing information or authorization actually prevents
progress; continue independent authorized work while waiting.

Navigator approval does not expand the user's scope or grant permission for
external actions. Honor existing permissions for publishing, deployment, and
other restricted actions. If a pilot repeatedly fails for the same reason,
inspect the cause and revise the assignment or approach instead of retrying
unchanged work indefinitely.

When committing is authorized, have one owner stage only accepted changes at
coherent boundaries and use conventional commits. Use conventional comments
for review feedback, such as `issue:`, `suggestion:`, and `question:`. Preserve
unrelated user changes.

End with a concise account of the completed behavior, verification, and any
remaining limitations. Keep detailed pilot walkthroughs within the agent loop
unless the user requests them.

When evaluating workflow changes, compare elapsed time and model usage per accepted
work item, including all agents, rework, and quality outcomes. Separate cached input,
uncached input, and output where available; do not infer savings from tool counts
or sum overlapping waits as elapsed time. Roll accepted items up to milestone
progress. Honor pauses by stopping productive work and retaining a checkpoint;
do not assume skill instructions can suppress runtime-generated wakeups.
