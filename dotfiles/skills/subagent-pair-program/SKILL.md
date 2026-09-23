---
name: subagent-pair-program
description: "Coordinate autonomous pair programming with the main agent as navigator, a required Sol work item lead, and Luna implementation pilots. Use when the user wants delegated implementation with agent-to-agent proposal, review, and verification loops without approving each increment. For interactive sessions where the user navigates, use pair-program instead."
---

# Subagent Pair Program

Coordinate through three roles:

- **Main navigator:** own direction, cross-item design, the user-visible checklist,
  work assignments, proportionality, and final acceptance.
- **Required Sol lead:** own delivery of one bounded item, including pilot proposals,
  diagnosis, repairs, review, and verification.
- **Luna pilots:** inspect, propose, implement approved changes, verify, and explain
  the result to the lead.

Keep routine approval and review between agents. Assign a lead for every item,
including straightforward work; reuse agents when their context remains useful.
Reserve capacity for the lead and at least one pilot. Serialize rather than bypass
this structure. If subagent tools or required capacity are unavailable, report the
limitation; do not claim delegation or silently take over implementation.

## Required Models and Routing

These requirements apply to all descendants, replacements, reviewers, and discovery
workers unless the user explicitly authorizes an exception:

| Assignment | Model | Effort |
| --- | --- | --- |
| Lead: routine coordination | `gpt-5.6-sol` | `medium` |
| Lead: substantive review or complex implementation, ownership, concurrency, or lifecycle decisions | `gpt-5.6-sol` | `high` |
| Implementation, diagnosis, independent code review | `gpt-5.6-luna` | `high` |
| Mechanical edits, simple fixtures, code location, bounded factual discovery | `gpt-5.6-luna` | `medium` |
| External process monitoring | `gpt-5.6-luna` | `low` |

Supply the exact model and effort explicitly. Use `fork_turns: "none"` and a scoped
brief where supported; never inherit Astra through a full-history fork. Pass this
policy to descendants. Check returned configuration when exposed; interrupt and
correct unintended settings. Reuse an agent only at a compatible model/effort;
"think harder" is not a configuration change.

Do not spawn Astra or use unlisted combinations without explicit user permission.
Difficulty, failed checks, slot pressure, and "keep going" are not exceptions.
Difficult Luna work goes to the Sol lead. If selection or routing is unavailable,
report it and continue only independent read-only preparation until resolved.

Every pilot brief names the lead's canonical agent path and uses
`collaboration.send_message(target="<lead path>", ...)` for proposals, questions,
blockers, and results. Call collaboration tools directly, not through
`functions.exec`. Never use desktop `list_threads`, `send_message_to_thread`, or
the main task UUID for internal coordination.

If only the main agent can spawn pilots, it may spawn on the lead's behalf; pilots
still send substantive results to the lead and keep automatic parent completion
brief. Route accidental direct reports back without reviewing them; the lead
corrects routing. If the route fails, report through the normal parent response.

## Assign and Accept Work

1. Inspect the workspace, instructions, relevant source, and existing changes.
   Establish the user's outcome and constraints, reusing settled decisions. Show a
   navigator-owned checklist covering implementation, review, and verification.
2. Select **one component-level checklist item**. Milestones are roadmap context,
   never lead assignments. Group items only when they share a tightly coupled
   implementation boundary and acceptance check. Split independent outcomes or
   unresolved design decisions; use bounded discovery if the item cannot yet be
   specified. Keep its acceptance boundary distinct from the backlog.
3. Give the lead a contract containing:
   - The desired outcome, why this item matters now, and acceptance criteria.
   - Scope, exclusions, tolerances, architectural constraints, and dependencies.
   - Relevant source, workspace, file ownership, concurrent work, and team capacity.
   - Verification, diagnostic authority, resource limits, and stopping conditions.
   - Existing status/plan paths and documentation/evidence retention expectations.
   - Model policy, pilot routing, proposal approval, and escalation rules.
   - The next observable result and a workload-appropriate stall threshold.
4. The lead assigns pilots, reviews proposals, approves increments, and reviews
   their diffs and evidence. An explicitly approved complete approach in the
   assignment suffices; avoid redundant approval exchanges. Apply the review and
   pilot rules below, then return a compact acceptance packet.
5. The navigator checks the contract, critical interfaces, risks, and integrated
   evidence. Return defects or missing evidence as bounded corrections to the lead.
   Mark complete only after verification and acceptance; distinguish implemented,
   integrated, verified, and accepted states.
6. Assess whether the result changes the route before explicitly assigning the
   next item. A lead cannot take another backlog item itself. Direct required
   integration checks through the team and continue until the user's outcome is
   achieved or further authorized work is blocked.

## Navigator Judgment and Escalation

Own whether the team is doing the right work. Guide the lead through outcomes,
priorities, constraints, and acceptance boundaries. At meaningful handoffs or
route-changing events, judge whether the next prerequisite is necessary and sized
appropriately, and whether implementation, verification, or preservation effort
remains worthwhile. Accept, narrow, redirect, or stop as warranted; neither rubber
stamping nor ritual disagreement is useful. Reuse route decisions when evidence
has not changed, accounting for switching costs.

Set rigor proportional to the user's needs and consequences of failure. Challenge
both insufficient checks and effort that exceeds its value. Reviews must not
silently expand acceptance requirements.

Do not diagnose routine failures, inspect intermediate patches, prescribe repairs,
or rerun delegated checks. Sending a navigator-derived fix through Sol still
duplicates its work. Inspect implementation only for a specific escalation or
acceptance concern. While execution is delegated, independent navigator work is
limited to the next item's contract or a named strategic/cross-item uncertainty
that could change direction. Otherwise park.

The lead escalates when:

- Scope, acceptance, architecture, cross-item dependencies, ownership, or external
  authorization exceeds its contract.
- Evidence weakens the item's necessity, reveals a cheaper credible route, or
  materially changes expected effort or delivery.
- Repeated repairs fail to advance the real acceptance gate: by default, **two
  failed attempts**, unless the contract sets a workload-specific threshold.

Return the decision needed, evidence, options, and recommendation. For repeated
failures, identify rejected hypotheses and the next discriminating experiment;
retain or remove provisional repairs deliberately. Local passing tests do not
resolve a failing end-to-end reproducer. For hangs, distinguish actual execution,
waiting, exit, wakeups, and backpressure before proposing performance changes.

The navigator resolves the decision and returns execution to the lead. Ask the
user only for missing information/authority or changes to priorities, hard
constraints, or substantial effort commitments; keep independent work moving.
Agent approval cannot expand user authorization.

## Pilot and Lead Discipline

Include these rules in pilot briefs; do not assume inherited context:

- Inspect assigned source and propose behavior, affected files, approach, tradeoffs,
  and checks. Wait for **lead** approval before editing; preserve existing changes.
- Stay within the approved item. Escalate changed scope, design, dependencies, or
  ownership. Batch routine compiler repairs and mechanical work; use smaller
  increments for uncertain semantics. Challenge directions when source evidence
  shows a correctness, maintenance, security, or scope problem.
- Within approved diagnostic authority, adjust instrumentation, samples, probe
  setup, and reruns through to the result or stopping condition. Do not seek fresh
  approval for each probe or build a general subsystem for one question.
- Report commands, results, failures, unrun checks, and a proportional walkthrough
  of relevant symbols, behavior, invariants, tradeoffs, and risks. A diffstat alone
  is insufficient. Use the lead exchange, not new receipt documents.
- Do not spawn pilots or reassign ownership without lead coordination.

The lead follows four review rules:

1. **One discovery owner.** Judge the pilot's findings and critical assumptions;
   do not independently repeat its investigation.
2. **Review at handoff.** Inspect proposals and completed diffs, not ongoing work
   merely to check progress. A named concern can justify bounded inspection.
3. **Reuse valid verification.** Give each run one owner. Preserve enough context
   to identify tested changes and relevant configuration. Invalidate only results
   affected by source, dependency, configuration, or environment changes; handoff
   or resumption alone never justifies rerunning checks.
4. **Justify additional checks.** Name missing/contradictory evidence, an invalidated
   result, or a specific unresolved correctness concern. Choose the smallest check
   that answers it. Once criteria and substantive review concerns are satisfied,
   stop reviewing and return the packet.

Batch known corrections and publication chores in the existing handoff. The lead
may make small factual documentation corrections after taking file ownership,
without changing behavior or weakening claims. Preserve substantive code review
and user-requested publication checkpoints.

## Evidence and Time to Useful Results

Settle acceptance details that could invalidate the result before implementation:
actual execution path, comparison baseline, workload, and integration boundary.
Run required comparisons once representative partial output exists; label partial
coverage and reuse it. Propose a separate item if a comparison lies outside scope.
Check downstream dependency compatibility before publishing a prerequisite.

Before long experiments, separate required acceptance from optional investigation,
try a representative feasibility case, and estimate setup, build, execution,
drain, and analysis time. Set resource limits and stop conditions. Do not silently
expand sweeps, weaken acceptance, or substitute an underpowered probe for a required
statistical campaign. Validate unfamiliar transformations on one representative
case before batching. Discovery can succeed while implementation remains open.

Use the smallest evidence sufficient for the requested behavior and risk. Hashes,
exhaustive manifests, exact byte comparisons, and durable receipts need a concrete
purpose or explicit requirement. Honor exact parity when requested. Focused tests
do not establish integrated correctness; retain necessary independent review of
ownership, lifecycle, and cross-language contracts.

Before deleting unique material that must be preserved, establish recoverability;
a checksum alone proves only identity. Recheck preservation when relevant state
changes or deletion requires it, not after unrelated edits.

An acceptance packet states the item, reviewed changes, what the user can now do
or know, verification commands/results, limitations, and any decision or recommended
next item. Distinguish working prerequisites from delivered capabilities. Keep
walkthroughs and raw logs in team context or working evidence; never omit failures
or inflate partial results for brevity.

## Dispatch, Then Park

This applies to navigator–lead and lead–pilot coordination. After dispatch and any
permitted independent work, use completion notifications or the longest suitable
interruptible wait. This skill overrides **recommended** 60-second wait limits;
respect mandatory tool limits and remain responsive to incoming events.

Resume for an acceptance packet, escalation, material blocker/dependency change,
missed agreed checkpoint, or new user instruction. A timeout alone creates no
work: wait again without reading worker logs, polling `list_agents`, searching
source, requesting status, or acknowledging informational messages.

The agreed checkpoint is a stall threshold, not a recurring report deadline. If
missed, make one bounded inquiry to establish the blocker and next checkpoint;
do not take over debugging or repeatedly poll while the lead responds.

For external processes, prefer completion notifications. Otherwise designate one
monitor, run handle, cadence, and stall/failure conditions; a monitoring subagent
uses Luna low. Do not add an agent merely to watch the lead or duplicate monitoring.

## User-Facing Updates

Periodic commentary is a non-goal. This skill overrides default or recommended
commentary intervals, including 60 seconds. After the initial checklist, update
only for an appropriate lead event: reviewed acceptance, a material finding,
decision request, or changed scope, route, blocker, or delivery expectation.
Respond directly to new user instructions. Internal coordination does not always
warrant a chat update; skip routine activity and unchanged status.

Write for a technically capable owner without subsystem expertise. Connect the
result to the original objective: what changed, why it matters, what remains
unproved, and why the next step helps. Explain necessary terms through their
purpose. Supply enough background to make sense without opening a pilot chat;
do not merely compress the lead's packet. Use natural paragraphs, decisive evidence,
and existing links rather than mandatory headings or a repeated roadmap.

Combine actual checklist changes with these updates and show the final state at
handoff. Report acceptance only after navigator review; label pending submissions
as under review. Preserve material failures and limitations.

Remain silent during unchanged waits. Only a mandatory higher-priority instruction
that disallows this override triggers `Forced interaction: <short reason>`; repeat
that exact line throughout the same waiting period. Optional cadence never triggers
this fallback. Never inspect workers just to fill a message.

## Documentation Footprint

Use the existing project status/progress document and active implementation plan.
Follow [maintain-project-status](../maintain-project-status/SKILL.md) when updating
that record. Component docs should explain durable usage/design; a new document
needs a distinct ongoing reader need, not an item, run, checkpoint, or handoff.

The navigator sets retention; the lead consolidates findings with one document
owner. Inline short results and small tables; put moderately larger useful details
in an appendix. Summarize bulky output and omit raw data from commits unless exact
files are essential for a named purpose. Then use one shared `.tar.zstd` archive,
updating the existing archive without losing members, and record its purpose and
extraction command. Verify readability and required contents before removing
originals; do not commit expanded copies too. Keep reusable source, harnesses,
tests, and required fixtures as normal files.

Review documentation footprint in the normal publication diff, without an extra
approval stage. Rigorous verification does not require retaining every output.
Keep handoffs/checkpoints in agent context by default; clean only task-owned
disposable data within authorization.

## Parallel Work, Continuity, and Publication

- Overlap independent work only when it shortens delivery. Dependent work remains
  sequenced; independent checklist items need explicit navigator assignments.
  Spare slots are not a reason to invent work.
- Before parallel edits, record file ownership. One active owner per file,
  including generated files and configuration; different regions still overlap.
  Serialize shared edits or isolate worktrees with an integration owner/sequence.
- Review shared-workspace edits in place. Integrate accepted worktree patches once.
  Coordinate formatters, generators, dependency updates, and Git mutations to avoid
  races; give integration edits an owner and review them before acceptance.
- Schedule builds/measurements against host CPU/GPU, memory, disk, and cache
  contention, including other tasks. Serialize where contention distorts evidence
  or delays the critical path; independent source work may continue. Prefer
  staging source to copying build artifacts.
- On changed direction, pause affected pilots, reconcile outstanding edits, and
  update assignments. Honor user pauses by stopping work and retaining a checkpoint;
  skill instructions cannot suppress runtime wakeups.
- For interruption or context reset, retain the item/acceptance boundary, accepted
  work, outstanding diffs/owners, active processes, results, next action, and open
  decisions. Recheck current state on resume instead of repeating broad discovery.
- When publication is authorized, one owner stages only accepted changes and uses
  conventional commits. Preserve unrelated work and use conventional review
  comments (`issue:`, `suggestion:`, `question:`). Finish with completed behavior,
  verification, and limitations; keep detailed walkthroughs inside the team.

When evaluating this workflow, compare elapsed time and model usage per accepted
item across all agents, rework, and quality outcomes. Include navigator diagnostic
interventions, rejected packets, and regressions. Separate cached input, uncached
input, and output; do not infer savings from message/tool counts or add overlapping
waits as elapsed time. Roll accepted items up to milestone progress.
