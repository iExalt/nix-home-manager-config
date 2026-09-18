---
name: subagent-pair-program
description: "Coordinate autonomous pair programming with the main agent as navigator, a required Sol work item lead, and Luna implementation pilots. Use when the user wants delegated implementation with agent-to-agent proposal, review, and verification loops without approving each increment. For interactive sessions where the user navigates, use pair-program instead."
---

# Subagent Pair Program

Act as the main navigator: own the design, task checklist, work item assignments,
and final acceptance. Every work item requires a Sol lead to coordinate Luna
implementation pilots. Pilots propose changes, implement approved increments,
verify them, and walk the lead through the result. The lead returns reviewed
evidence to you. Keep this loop between agents; do not ask the user to approve
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

## Required Work Item Lead

Assign a Sol lead before dispatching pilots for every work item, including
straightforward items. Do not bypass the lead with direct main-agent-to-pilot
coordination. The main agent must not absorb routine proposal approvals, repair
loops, or first-pass review. Reuse an existing lead under a new bounded assignment
when appropriate; a mandatory lead does not require a new spawn for every item.

The main navigator selects the item, defines its acceptance boundary, owns the
user-visible checklist and cross-item design, and makes final acceptance decisions.
The lead owns getting that item to acceptance: decompose it, approve routine
pilot proposals, review diffs, diagnose failures, direct in-scope repairs, and
repeat verification without seeking main-agent approval for each step. Name the
lead as the pilots' approval and reporting recipient. Explicitly coordinate any permission to spawn
pilots, file ownership, and the total team size. Reserve capacity for the lead
and at least one implementation pilot; serialize work rather than dropping the
lead to make room for more pilots. If only the main agent can spawn pilots, it
may create them on the lead's behalf, but they still report to the lead.

Escalate to the main navigator when completing the item requires changing scope,
acceptance criteria, or an architectural contract; a dependency or ownership
conflict exceeds the lead's authority; a decision materially affects another
item; external-action authorization is missing; or repeated repair attempts
produce no new evidence or require relaxing acceptance. Ordinary compiler/test
failures and local implementation decisions stay with the lead. Each escalation
must state the decision needed, evidence, options, and the lead's recommendation.
The main agent resolves that decision and returns execution to the lead rather
than taking over the repair.

The lead returns after its assigned item; it cannot take another checkbox from
the backlog without a new assignment. Reuse its context for related
items when useful, but renew the boundary explicitly. Routine next-item selection
remains autonomous and does not require user approval.

## Main-Agent Delegation Boundary

While an item is delegated, the main agent must not run a parallel implementation
or debugging loop: independently diagnose routine failures, inspect each
intermediate patch, prescribe local repairs, or rerun the lead's verification.
Sending root-derived fixes through the lead still duplicates the lead's work.
Inspect implementation evidence for a specific escalation or final acceptance
concern; keep that inspection proportional to the decision being made.

During execution, independent navigator work is limited to preparing the next
item's acceptance contract or resolving a known cross-item decision. Once that
work is complete, park under the protocol below. Spare capacity is not a reason
to duplicate delegated work or invent additional source investigations.

At acceptance, check the contract, critical interfaces, risks, and verification
evidence. Return missing evidence or defects as a bounded correction to the lead,
without implementing the correction yourself. Preserve independent review where
needed; avoid replaying the lead's entire investigation.

## Dispatch, Then Park

After assigning a complete work item contract, park until an actionable event
arrives. Prefer agent completion notifications or the longest suitable,
interruptible wait supported by the tool, subject to higher-priority
responsiveness requirements. Resume substantive navigator work only for:

- A lead escalation requiring a navigator decision.
- An acceptance packet ready for review, including another active item's packet.
- A material blocker, dependency change, or missed agreed checkpoint.
- New user instructions.

A wait timeout is not an actionable event. If it brings no new evidence and no
agreed checkpoint is overdue, wait again. Do not inspect worker logs, call
`list_agents`, request status, search the implementation, or repeat an unchanged
progress update merely because the wait returned. Do not acknowledge every
informational message; respond only when a decision or action is needed.

Before parking, have the lead identify its next observable result and a
workload-appropriate time or condition for escalating if that result does not
materialize. This is a stall threshold, not a recurring status-report deadline.
A missed checkpoint permits one bounded status inquiry to establish the blocker
and next checkpoint; it does not transfer debugging to the main agent or justify
repeated polling while the lead responds.

The lead sends an acceptance packet, a decision request with evidence and its
recommendation, or a material blocker/change to delivery expectations. Routine
progress, test failures, and repair attempts remain within its team. During
delegated execution, report meaningful state changes to the user; unchanged
worker progress does not require periodic commentary under this skill. Maintain
responsiveness through interruptible waits. Higher-priority instructions that
require periodic commentary or shorter waits still apply; satisfy them without
adding redundant inspection or status requests.

Do not add a monitoring agent merely to watch the lead. Use one only when an
external process needs supervision and completion notifications are unavailable,
under the process-monitoring rules below.

## Required Subagent Models and Effort

These are model-selection requirements, not suggestions. They apply to every
subagent in the workflow, including nested agents, replacements, reviewers, and
discovery workers. An explicit user model/effort instruction takes precedence;
otherwise use only the following combinations:

| Role or assignment | Model | Reasoning effort |
| --- | --- | --- |
| Work item lead: routine coordination | `gpt-5.6-sol` | `medium` |
| Work item lead: substantive review or complex ownership, concurrency, lifecycle, or implementation decisions | `gpt-5.6-sol` | `high` |
| Implementation, diagnosis, or independent code review pilot | `gpt-5.6-luna` | `high` |
| Mechanical edits, straightforward fixtures, code location, or bounded factual discovery | `gpt-5.6-luna` | `medium` |
| Process monitoring and completion/failure reporting | `gpt-5.6-luna` | `low` |

- Always supply both the exact model identifier and effort when spawning. Never
  rely on parent inheritance, configured defaults, or an implicit model alias.
  Include this policy and the named lead in assignments so descendants follow it.
- Use `fork_turns: "none"` with an explicit task brief where that parameter is
  supported. Never use a full-history fork that prevents the selected model and
  effort from taking effect. Check the actual tool schema in other environments.
- Do not spawn Astra subagents, or substitute another unlisted model or effort,
  without explicit user authorization. An Astra main navigator is allowed; its
  model must not propagate to children. Task difficulty, slot pressure, failed
  checks, and a request to "keep going" are not authorization for an exception.
- Escalate difficult Luna work to the existing Sol lead; involve the main
  navigator only under the escalation conditions above. Narrow the assignment
  as needed. Do not silently upgrade the pilot to Astra or increase effort beyond
  the table. Choose Sol high when its assigned
  duties include substantive review; medium is for routine coordination.
- Check returned configuration when exposed. Never reuse an agent whose model
  or effort is incompatible with its assignment. Use a supported explicit effort
  change or replace it with a concise handoff; a message saying "think harder"
  is not an effort-setting change. If an unintended model is detected, interrupt
  it and correct the configuration before further work.
- If the required model, explicit selection, lead/pilot routing, or capacity is
  unavailable, report the specific limitation. Continue independent read-only
  preparation, but do not silently fall back to Astra or omit the lead. Request
  an explicit exception only if needed to proceed with the affected work.

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
2. Select a bounded work item with an observable acceptance result. Show its
   active acceptance boundary separately from milestone context and the backlog.
   Assign its lead using the required model/effort policy. Have the lead use one
   pilot for tightly coupled work. Add pilots when bounded tasks can run
   independently alongside useful navigator work; identify dependencies and file
   ownership before parallelizing.
3. Give the lead a bounded contract covering the following points, with authority
   to complete the in-scope proposal, repair, review, and verification loops. Have
   it assign each pilot an appropriate subset:
   - The desired behavior and acceptance criteria.
   - The checklist item, exclusions, tolerances, and conditions for escalation.
   - Relevant source context, architectural decisions, constraints, and applicable
     instructions.
   - The workspace or worktree and files or components it may change.
   - Known concurrent work and dependencies.
   - Expected verification and a requirement to propose its approach before edits.
   - The required model/effort policy and the lead as reviewer/approver. Direct
     proposals and questions there and wait for approval before implementation.
4. Have the lead review the pilot's proposal against the source and approved item
   contract, resolving routine tradeoffs within scope. The lead approves the
   specific increment and verification, or sends concrete revisions. An assignment that
   already supplies and explicitly approves a complete approach can serve as
   approval; do not require a redundant exchange. The lead performs
   this routine review within the main navigator's approved boundary.
5. While the lead coordinates implementation, follow the Main-Agent Delegation
   Boundary and Dispatch, Then Park protocol above. Keep routine diagnosis and
   repair with the lead; a wait timeout alone creates no navigator work.
6. Have the lead review the actual diff and verification evidence when the pilot
   returns. The lead requires a proportional code walkthrough, investigates
   unsupported claims, and returns actionable corrections to the pilot. A pilot's
   completion message alone does not establish acceptance. Keep detailed
   walkthroughs and routine correction loops with the lead. The main navigator reviews
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
this skill or the navigator's full context. Here, navigator means the required
work item lead, who escalates decisions outside its contract to the main agent:

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
run handle. Any monitoring subagent must use Luna low under the model policy above.
Respect tool wait limits. The main agent should not duplicate polling or restart
finished pilots for unchanged status.

Keep a compact checkpoint for interruption or handoff: current item and acceptance
boundary, accepted revisions, outstanding diffs and owners, active processes,
validation receipts, next action, and unresolved decisions. Recheck current state
on resume instead of repeating broad discovery. Reset an agent with this brief
when obsolete context outweighs useful continuity.

## Concurrent Work and Integration

- Before approving parallel edits, the lead records a file-ownership table. Each
  file has one active pilot owner; different regions of the same file still
  overlap. Serialize shared-file edits or isolate them in worktrees with an
  explicit integration owner and sequence. Update ownership before reassignment,
  including generated files and shared configuration.
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

The work item lead supplies routine implementation approvals. Keep the user informed
of meaningful progress and outcomes without turning updates into approval gates.
Ask the user only when missing information or authorization actually prevents
progress; continue independent authorized work while waiting.

Navigator approval does not expand the user's scope or grant permission for
external actions. Honor existing permissions for publishing, deployment, and
other restricted actions. If a pilot repeatedly fails for the same reason, the
lead investigates and revises the assignment or approach, escalating under the
conditions above instead of retrying unchanged work indefinitely.

When committing is authorized, have one owner stage only accepted changes at
coherent boundaries and use conventional commits. Use conventional comments
for review feedback, such as `issue:`, `suggestion:`, and `question:`. Preserve
unrelated user changes.

End with a concise account of the completed behavior, verification, and any
remaining limitations. Keep detailed pilot walkthroughs within the agent loop
unless the user requests them.

When evaluating workflow changes, compare elapsed time and model usage per accepted
work item, including all agents, rework, and quality outcomes. Track main-agent
routine diagnostic interventions, rejected acceptance packets, and regressions
alongside tokens and time; fewer messages alone do not establish better delegation.
Separate cached input, uncached input, and output where available; do not infer savings from tool counts
or sum overlapping waits as elapsed time. Roll accepted items up to milestone
progress. Honor pauses by stopping productive work and retaining a checkpoint;
do not assume skill instructions can suppress runtime-generated wakeups.
