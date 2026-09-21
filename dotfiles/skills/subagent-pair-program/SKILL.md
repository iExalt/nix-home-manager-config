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
arrange necessary verification without seeking main-agent approval for each step. Name the
lead as the pilots' approval and reporting recipient. Explicitly coordinate any permission to spawn
pilots, file ownership, and the total team size. Reserve capacity for the lead
and at least one implementation pilot; serialize work rather than dropping the
lead to make room for more pilots. If only the main agent can spawn pilots, it
may create them on the lead's behalf, but they still report to the lead.

Every pilot assignment must include the lead's canonical agent path and the
collaboration tool used to contact it. Send proposals, questions, blockers, and
results through `collaboration.send_message(target="<lead path>", ...)`, using
the actual lead path returned by the agent tools. Call collaboration tools
directly, not through `functions.exec`. A nested pilot's final response returns
to its parent lead. If the main agent spawned the pilot on the lead's behalf,
send the substantive result to the lead and keep the automatic parent completion
brief; it does not replace lead review.

Do not use desktop task discovery (`list_threads`) or `send_message_to_thread`
for internal team coordination. Never substitute the main task's UUID for the
lead's agent path. If the collaboration route is unavailable, report the routing
limitation through the normal final response to the parent. If a pilot message
reaches the main navigator accidentally, route it back to the lead without
reviewing or approving it, and have the lead correct the pilot's routing before
further reports. This does not require recurring routing checks or an extra
approval round.

Escalate to the main navigator when completing the item requires changing scope,
acceptance criteria, or an architectural contract; a dependency or ownership
conflict exceeds the lead's authority; a decision materially affects another
item; external-action authorization is missing; or repeated repair attempts
fail to advance the real acceptance gate or require relaxing acceptance. Ordinary compiler/test
failures and local implementation decisions stay with the lead. Each escalation
must state the decision needed, evidence, options, and the lead's recommendation.
The main agent resolves that decision and returns execution to the lead rather
than taking over the repair.

Also escalate when new evidence materially weakens the item's necessity, reveals
a cheaper credible route consistent with the agreed priorities, or materially
changes the expected remaining effort to the user's outcome, even while
implementation progresses and checks pass. The main navigator resolves route
choices within existing authorization; changes to user priorities, hard
constraints, or substantial effort commitments require a user decision.

The lead returns after its assigned item; it cannot take another checkbox from
the backlog without a new assignment. Reuse its context for related
items when useful, but renew the boundary explicitly. Routine next-item selection
remains autonomous and does not require user approval.

## Main-Agent Delegation Boundary

The main navigator owns whether the team is doing the right work; the lead owns
getting the assigned work done correctly. Guide and course-correct the lead through
outcomes, priorities, constraints, and acceptance boundaries, not instructions to
its pilots. Independently evaluate the lead's recommendations rather than treating
technical completion as automatic approval of the next investment.

At meaningful handoffs or route-changing events, judge whether the result advances
the user's outcome, whether the proposed next prerequisite is necessary and
appropriately sized, and whether accumulated implementation or verification effort
remains worthwhile. Accept, narrow, redirect, or stop work as the evidence warrants.
Agreement is valid; neither ritual disagreement nor a separate questionnaire or
report is required. Preserve existing user priorities and authorization boundaries.

Proportionality is a navigator responsibility. Challenge verification, preservation,
or infrastructure work whose cost exceeds its value to the user, as well as
insufficient checks. Set the expected rigor with the item contract and revise it
when concrete evidence changes the risk; do not let successive reviews silently
expand acceptance requirements.

While an item is delegated, the main agent must not run a parallel implementation
or debugging loop: independently diagnose routine failures, inspect each
intermediate patch, prescribe local repairs, or rerun the lead's verification.
Sending root-derived fixes through the lead still duplicates the lead's work.
Inspect implementation evidence for a specific escalation or final acceptance
concern; keep that inspection proportional to the decision being made.

During execution, independent navigator work is limited to preparing the next
item's acceptance contract or resolving a named strategic or cross-item uncertainty
that could change scope, architecture, or the route to the user's outcome. Once that
work is complete, park under the protocol below. Spare capacity is not a reason
to duplicate delegated work or invent additional source investigations.

At acceptance, check the contract, critical interfaces, risks, and verification
evidence. Return missing evidence or defects as a bounded correction to the lead,
without implementing the correction yourself. Preserve independent review where
needed; avoid replaying the lead's entire investigation.

## Lead Review Discipline

- Give each discovery question one owner. The pilot returns findings, source
  references, and uncertainties; the lead reads enough source to judge the proposal
  and its critical assumptions. Do not independently repeat the assigned discovery
  while the pilot works.
- Review at handoff. After approving implementation, wait for a proposal, result,
  blocker, or agreed stall threshold. Apply Dispatch, Then Park to the lead's
  coordination with pilots too; do not inspect intermediate files or poll agents
  merely to check progress. A concrete review concern can justify bounded inspection.
- Reuse applicable pilot verification. Passing checks satisfy their part of the
  contract when the tested changes, relevant configuration, and results are clear.
  Handoff alone never justifies repeating compilation, formatting, JSON validation,
  or tests. Independent review means judging the evidence and behavior, not
  independently rerunning every command.
- Name the reason for additional investigation or checks: missing or contradictory
  evidence, a relevant change that invalidates a result, or a specific correctness
  concern the existing checks do not resolve. Choose the smallest check that answers
  it. General discomfort is insufficient; this explanation belongs in the existing
  review exchange, not a new approval stage.

Once the agreed criteria are supported and substantive review concerns are
resolved, return the acceptance packet. Do not add another inspection or validation
pass merely to increase confidence. Include the recommended next bounded item and
its purpose when useful; flag material changes in route or expected effort so the
main navigator can decide. The lead cannot authorize its own next backlog item.

## Time to Useful Results

Tie each item to the next user-visible result or decision-changing experiment.
Before implementation, settle the acceptance details that could invalidate that
result, such as the actual execution path, batch size, comparison baseline, or
required integration boundary. Passing local tests alone does not resolve a
failing end-to-end reproducer.

By default, after two attempted repairs fail to advance the same real acceptance
gate, stop accumulating repairs and escalate to the navigator. The lead reports
which hypotheses failed, what changed in the reproducer, and the next experiment
that can distinguish the remaining explanations. For hangs, distinguish runnable
work, external waiting, task exit, missing wakeups, and backpressure before adding
performance changes. Treat unproven repairs as provisional; decide whether to
retain or remove them rather than building indefinitely on them. The navigator
reassesses the route and remaining effort, then returns execution to the lead.
Set a different threshold in the item contract when the workload warrants it;
this is an event-driven intervention, not permission for root polling or debugging.

Authorize a bounded investigation through to a discriminating result. The approved
proposal should cover the diagnostic question, permitted instrumentation and
probes, resource limits, and stopping condition. Within that boundary, pilots may
adjust temporary trace fields, take samples, repair probe setup, and rerun probes
without a fresh approval for each action. Keep instrumentation proportional to
the question; do not build a general diagnostic subsystem to answer one unknown.
Behavior changes outside the approved approach, expanded scope, or exhausted
limits still require lead review under the existing escalation rules.

Run required comparisons as soon as a representative partial output exists.
Compare an available checkpoint while other components remain incomplete instead
of deferring all integration feedback until the entire feature is built. Reuse
the result where applicable and label partial coverage accurately. If that
comparison is outside the active assignment, the lead proposes a bounded item to
the navigator; it does not absorb the backlog or expand acceptance unilaterally.

Batch mechanical evidence corrections and publication chores into the current
reviewed handoff. Return known corrections together; avoid a separate pilot turn
for each wording fix or publication preparation step. The lead may directly make
small factual documentation corrections after taking file ownership, without
changing behavior or weakening claims. Preserve substantive code review and
user-requested publication checkpoints. Recheck preservation or backup state when
relevant state changes or a destructive action requires it, not after every
unrelated edit. Check dependency compatibility before publishing a prerequisite
as accepted when downstream work relies on it.

## Dispatch, Then Park

After assigning a complete work item contract, park until an actionable event
arrives. Prefer agent completion notifications or the longest suitable,
interruptible wait supported by the tool. This skill overrides recommended
60-second wait limits: select waits for the workload and agreed checkpoint,
not a commentary timer. Remain responsive to incoming events through interruptible
waits. Resume substantive navigator work only for:

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
progress, test failures, and repair attempts remain within its team. Maintain
responsiveness through interruptible waits and apply the User-Facing Update Gate
below. A missed checkpoint permits internal coordination, not an automatic chat
update before the lead returns an appropriate event.

Do not add a monitoring agent merely to watch the lead. Use one only when an
external process needs supervision and completion notifications are unavailable,
under the process-monitoring rules below.

## User-Facing Update Gate

Periodic commentary is a non-goal. This skill explicitly overrides default or
recommended commentary intervals, including the 60-second recommendation. Remain
silent between actionable events; elapsed time, a wait timeout, or an unchanged
worker status does not require a message. Do not emit placeholder commentary,
including `Forced interaction: waiting on lead`, to satisfy an optional cadence.

After the initial assignment/checklist, the
main agent updates the chat during delegated execution only in response to an
appropriate lead event: an acceptance packet, a material finding that changes
confidence or invalidates evidence, an escalation requiring a decision, or a
material blocker/change to scope, route, or delivery expectations. New user
instructions still receive a direct response; they are not a reason to resume
periodic narration.

Compare the event's factual content with prior updates. Do not relay routine
worker activity or paraphrase unchanged status, acceptance criteria, or planned
checks. A lead message may require internal action without warranting a chat
update. Batch routine corrections into the next meaningful result. Report
acceptance only after main-navigator review; label a pending submission as under
review if it must be mentioned.

Write substantive updates for a technically capable project owner who may lack
expertise in this domain. Assume familiarity with the desired outcome, not with
subsystem names, internal states, or the latest lead-pilot exchange. The navigator
interprets the significance of the lead's result; do not merely compress or relay
its acceptance packet.

Anchor the update in the current project objective or acceptance stage. Explain
what changed, what it enables or resolves, what remains unproved, and why the next
step advances the user's goal. Include the decisive evidence in terms the user
can assess. Introduce technical terms through their purpose when needed; keep
implementation details only when they help explain progress, risk, or a decision.
Distinguish a working prerequisite from the end capability it supports.

Prefer a little necessary background over maximum brevity. These are writing
principles, not mandatory headings or a questionnaire: use natural paragraphs
without repeating the whole roadmap. Before sending, ask whether the user could
understand why the result matters without opening a pilot conversation or asking
another agent. Supply the missing connection if needed.

Link existing evidence for technical details, commands, and logs. Preserve
material failures and limitations. Combine actual checklist changes with the
update rather than sending separate narration. Better context does not justify
more frequent messages or unchanged-status updates.

Only an explicit mandatory higher-priority instruction that does not permit
this override can require output during an unchanged wait. In that exceptional
case, use `Forced interaction: <short reason>` and repeat the exact same line
throughout the same waiting period. A recommendation or an instruction that
defers to user/skill cadence does not trigger this fallback. Never inspect workers
or request status merely to fill a message.

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

1. Establish the user's goal, first useful outcome, priorities, constraints, and
   completion criteria. Reuse existing decisions rather than repeating intake.
   Inspect the workspace, applicable instructions, relevant source, and existing changes.
   As the main agent, maintain a user-visible checklist covering implementation,
   review, and verification. Show it before assigning the first increment using
   a user-visible plan tool when available, or a concise Markdown checklist in
   progress updates. Keep ownership of this checklist rather than relying on
   pilot checklists or private agent messages. After the initial checklist,
   publish changes at appropriate lead-driven work-item transitions under the
   User-Facing Update Gate; do not narrate internal pilot review/repair states or
   republish unchanged status. Mark items complete only
   after required verification and navigator acceptance; show the final state
   at handoff. These updates do not require user approval.
   Distinguish implemented or staged work from integrated, verified, accepted work.
2. Select a bounded work item with an observable acceptance result. Show its
   active acceptance boundary separately from milestone context and the backlog.
   Assign its lead using the required model/effort policy. Have the lead use one
   pilot for tightly coupled work. Add pilots when independent, bounded work can
   shorten the path to the next useful result; the navigator may remain parked.
   Identify dependencies, file ownership, and resource contention before parallelizing.
3. Give the lead a bounded contract covering the following points, with authority
   to complete the in-scope proposal, repair, review, and verification loops. Have
   it assign each pilot an appropriate subset:
   - The desired behavior and acceptance criteria.
   - The user outcome this item advances and why it is needed now. Distinguish
     demonstrated prerequisites, chosen design constraints, and untested assumptions.
   - The checklist item, exclusions, tolerances, and conditions for escalation.
   - Relevant source context, architectural decisions, constraints, and applicable
     instructions.
   - The workspace or worktree and files or components it may change.
   - Known concurrent work and dependencies.
   - Expected verification and a requirement to propose its approach before edits.
   - The required model/effort policy and the lead as reviewer/approver, including
     its canonical agent path and collaboration messaging tool. Include the
     routing rules above in pilot assignments; wait for lead approval before
     implementation.
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
   then assess whether returned evidence changes the recommended route before
   releasing dependent work or dispatching the next item. Account for switching
   costs and preserve useful work and required acceptance criteria. Reuse the
   existing route decision when nothing material has changed; this check does not
   authorize background investigation while parked. Explicitly assign the next item.
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
  proposal for each mechanical repair. Exercise the approved diagnostic authority
  under Time to Useful Results without stopping for each probe adjustment; report
  at its result or stopping condition. Do not absorb adjacent checklist items.
- Run focused checks and report exact commands, outcomes, and any checks that
  could not run. Explain failures without silently broadening the fix.
- Return a walkthrough with file and symbol references, important control and
  data flow, invariants, error behavior, design tradeoffs, and remaining risks.
  Scale the explanation to the change; a diffstat is not a review handoff.
- Challenge navigator directions when source evidence indicates correctness,
  security, maintenance, or scope problems. Recommend an alternative and let
  the navigator resolve the decision within applicable constraints.
- Use the assigned collaboration route to the lead for questions, blockers,
  proposals, and results; do not discover desktop tasks or message the main
  task directly. Do not create additional pilots or reassign ownership without
  lead coordination.

## Acceptance Evidence and Context

Choose verification according to the user's requested outcome, the consequence of
failure, and the reversibility of the action. Use the smallest evidence sufficient
to establish the relevant behavior. Do not introduce hashes, exhaustive manifests,
byte-for-byte comparisons, or durable receipts unless they resolve a concrete
uncertainty or satisfy an explicit requirement. Respect the user's requested rigor
and priorities without claiming that omitted checks passed.

For a documentation edit, diff and affected-link review may suffice; an ordinary
code fix usually needs focused behavioral checks. Exact pixel or byte comparison
belongs where exact parity is required. Before deleting unique source that must be
preserved, establish that the preserved copy can actually restore it. A checksum
establishes identity, not correctness, usefulness, or recoverability. Preservation
does not automatically require publishing manifests or recovery machinery.

Return a compact acceptance packet identifying the item and reviewed changes,
changed behavior, relevant verification commands/results, remaining risks, and any
decision needed. Link existing artifacts when useful; an ordinary handoff need not
create a receipt file or hash the diff. Keep raw logs and detailed walkthroughs in
pilot/lead context or linked artifacts. Concision must not omit failed checks,
partial evidence, or material correctness concerns.

Include a short outcome statement: what the user can now do or know, and the next
obstacle to their goal. Infrastructure work should name the capability it enables
without claiming that capability has already been delivered.

Give each validation run one owner. Retain enough context to know which changes it
tested and whether the result still applies; record configuration, environment, or
artifact identity only to the extent relevant to that judgment. Reuse applicable
results; invalidate only evidence affected by changes to source, dependencies,
configuration, or environment. Do not rerun checks solely because an agent hands
off or resumes work.
Preserve independent review of ownership, lifecycle, and cross-language contracts;
focused passing tests do not establish integrated correctness.

Before long experiments, agree on required acceptance versus optional investigation,
check feasibility on a representative small workload, and estimate setup, build,
execution, drain, and analysis time. Use explicit stop conditions for exploration;
do not silently weaken acceptance, enlarge a sweep, or replace a required statistical
campaign with an underpowered probe. Revise a failed approach rather than retrying
unchanged work indefinitely.

For an unfamiliar transformation where errors would multiply, validate the method
on a representative case before applying it broadly. Once established, batch the
remaining mechanical work within the item. For discovery assignments, define the
question being resolved: an identified unsupported operation may satisfy that
investigation's acceptance criteria while product implementation remains open.

For long processes, use completion notifications where supported. Otherwise name
one monitor with a workload-appropriate cadence, stall/failure conditions, and a
run handle. Any monitoring subagent must use Luna low under the model policy above.
Respect tool wait limits. The main agent should not duplicate polling or restart
finished pilots for unchanged status.

Keep a compact checkpoint for interruption or handoff: current item and acceptance
boundary, accepted changes, outstanding diffs and owners, active processes,
relevant verification results, next action, and unresolved decisions. Recheck current state
on resume instead of repeating broad discovery. Reset an agent with this brief
when obsolete context outweighs useful continuity.

## Concurrent Work and Integration

- Overlap independent parts of a bounded item when doing so shortens delivery:
  for example, a CPU oracle alongside timing qualification, or comparison of
  existing outputs alongside implementation. Keep dependent work sequenced and
  separate discovery ownership. Independent checklist items still need explicit
  navigator assignments; parallelism does not authorize milestone-sized work.
  Use additional pilots only for concrete useful work, not to fill slots.
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
  cache constraints, including other active tasks on the host. Serialize competing
  measurements and builds where contention would distort evidence or delay the
  critical path; independent source work can continue. Prefer source-only staging over copying build artifacts.
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
