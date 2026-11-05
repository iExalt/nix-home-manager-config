---
name: subagent-pair-program
description: "Coordinate autonomous pair programming with the main agent as navigator, a required work item lead, and implementation pilots. Use when the user wants delegated implementation with agent-to-agent proposal, review, and verification loops without approving each increment. For interactive sessions where the user navigates, use pair-program instead."
---

# Subagent Pair Program

**Load `iExalt:working-conventions` before any other step.** It holds the
rules shared across the workflow skills, and this skill cites its sections as
`working-conventions` › Section without restating them. Invoke it as a skill,
or read its `SKILL.md` where your harness lists the path.

Coordinate through three roles:

- **Main navigator:** own direction, cross-item design, the user-visible checklist,
  work assignments, proportionality, and final acceptance.
- **Required work item lead:** own delivery of one bounded item, including pilot proposals,
  diagnosis, repairs, review, and verification.
- **Implementation pilots:** inspect, propose, implement approved changes, verify, and explain
  the result to the lead.

Keep routine approval and review between agents. Assign a lead for every item,
including straightforward work; reuse agents when their context remains useful.
Reserve capacity for the lead and at least one pilot. Serialize rather than bypass
this structure. If subagent tools or required capacity are unavailable, handle it
as `working-conventions` › Delegation describes.

## Required models and routing

Route every descendant, replacement, reviewer and discovery worker as
`working-conventions` › Model routing describes: the main navigator is the top
orchestrator, the work item lead is a lead, and implementation pilots are
pilots.

This skill names one exception. When no overseer sits above the run, the
navigator may give a lead `developer-demanding` in Claude Code, or GPT Sol at
`high` in Codex, when the item requires substantive review, complex diagnosis,
concurrency or lifecycle decisions, demanding integration, or explicitly
escalated implementation.

In Claude Code, select the profile through the Agent tool's `subagent_type`,
without a per-invocation model override that conflicts with it.

### Internal coordination

In Codex, every pilot brief names the lead's canonical agent path and uses
`collaboration.send_message(target="<lead path>", ...)` for proposals, questions,
blockers, and results. Call collaboration tools directly, not through
`functions.exec`. Never use desktop `list_threads`, `send_message_to_thread`, or
the main task UUID for internal coordination.

In Claude Code, use the native Agent and SendMessage tools with the lead's
actual returned agent identifier. Include that address and the required proposal,
approval, and result exchange in the pilot brief; do not invent Codex tool names
or substitute a separate session for a native subagent.

If only the main agent can spawn pilots, it may spawn on the lead's behalf; pilots
still send substantive results to the lead and keep automatic parent completion
brief. Route accidental direct reports back without reviewing them; the lead
corrects routing. If the route fails, report through the normal parent response.

## Assign and accept work

1. Inspect the workspace, instructions, relevant source, and existing changes.
   Establish the user's outcome and constraints, reusing settled decisions. Show a
   navigator-owned checklist covering implementation, review, and verification.
2. Select **one component-level checklist item**, sized as `working-conventions`
   › Work-item size describes. Use bounded discovery if the item cannot yet be
   specified, and keep its acceptance boundary distinct from the backlog.
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
   Mark complete only after verification and acceptance, in the states
   `working-conventions` › Work states names.
6. Assess whether the result changes the route before explicitly assigning the
   next item. A lead cannot take another backlog item itself. Direct required
   integration checks through the team and continue until the user's outcome is
   achieved or further authorized work is blocked.

## Navigator judgment and escalation

Own whether the team is doing the right work. At handoffs and route-changing
events, judge whether the next prerequisite is necessary and sized
appropriately, and whether remaining effort is worthwhile; accept, narrow,
redirect, or stop as warranted. Reuse route decisions while the evidence is
unchanged.

Set rigor proportional to the consequences of failure, challenging both
insufficient checks and effort that exceeds its value. Reviews must not
silently expand acceptance requirements.

Do not diagnose routine failures, inspect intermediate patches, prescribe or
derive repairs, or rerun delegated checks; inspect implementation only for a
specific escalation or acceptance concern. While execution is delegated, work
only on the next item's contract or a named cross-item uncertainty that could
change direction. Otherwise park.

The lead escalates when:

- Scope, acceptance, architecture, cross-item dependencies, ownership, or external
  authorization exceeds its contract.
- Evidence weakens the item's necessity, reveals a cheaper credible route, or
  materially changes expected effort or delivery.
- Repairs stop advancing the real acceptance gate, as `working-conventions` ›
  Repeated failure describes.

Return the decision needed, evidence, options, and recommendation; retain or
remove provisional repairs deliberately.

The navigator resolves the decision and returns execution to the lead, asking
the user only as `working-conventions` › Ask the user and Autonomy describe.

## Pilot and lead discipline

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
  is insufficient. Use the lead exchange, not new receipt documents. Check each
  per-item statement against the actual output before sending it.
- Do not read held-out or sealed data, or run a sealed test, before the protocol
  covering it, including any amendment, is agreed with the lead.
- Do not spawn pilots or reassign ownership without lead coordination.
- If the lead has ended or been replaced, send the result to the navigator once
  and stop; do not idle waiting for a review that cannot come.

The lead does not implement its item itself, even when it looks small. If the
brief requires a pilot and none can be spawned, escalate to the navigator.

The lead follows four review rules:

1. **One discovery owner.** Judge the pilot's findings and critical assumptions;
   do not independently repeat its investigation.
2. **Review at handoff.** Inspect proposals and completed diffs, not ongoing work
   merely to check progress. A named concern can justify bounded inspection.
3. **Reuse valid verification.** Rerun a check only when a source, dependency,
   configuration, or environment change affects it; handoff or resumption alone
   never justifies it.
4. **Justify additional checks.** Name missing/contradictory evidence, an invalidated
   result, or a specific unresolved correctness concern. Choose the smallest check
   that answers it. Once criteria and substantive review concerns are satisfied,
   stop reviewing and return the packet.

When the navigator asks the lead to confirm conditions before a consequential
build or run, confirm each against the diff or evidence, or report which are
unconfirmed and wait.

Batch known corrections and publication chores in the existing handoff. The lead
may make small factual documentation corrections after taking file ownership,
without changing behavior or weakening claims. Preserve substantive code review
and user-requested publication checkpoints.

## Evidence and time to useful results

Settle acceptance details that could invalidate the result before implementation:
actual execution path, comparison baseline, workload, and integration boundary.
Run required comparisons once representative partial output exists; label partial
coverage and reuse it. Propose a separate item if a comparison lies outside scope.
Check downstream dependency compatibility before publishing a prerequisite.

Before long experiments or sweeps, or before deleting material that must be
preserved, read [references/experiments.md](references/experiments.md).

Use the smallest evidence sufficient for the requested behavior and risk. Hashes,
exhaustive manifests, exact byte comparisons, and durable receipts need a concrete
purpose or explicit requirement. Honor exact parity when requested. Focused tests
do not establish integrated correctness; retain necessary independent review of
ownership, lifecycle, and cross-language contracts.

An acceptance packet states the item, reviewed changes, what the user can now do
or know, verification commands/results, limitations, and any decision or recommended
next item. Distinguish working prerequisites from delivered capabilities. Keep
walkthroughs and raw logs in team context or working evidence; never omit failures
or inflate partial results for brevity.

## Dispatch, then park

The navigator follows these rules after dispatching to the lead, and the lead
follows them after dispatching to pilots. After dispatch and any permitted
independent work, use completion notifications or the longest suitable
interruptible wait. This skill overrides **recommended** 60-second wait limits;
respect mandatory tool limits and remain responsive to incoming events.

Resume for an acceptance packet, escalation, material blocker/dependency change,
missed agreed checkpoint, or new user instruction, and otherwise wait as
`working-conventions` › Waiting describes: don't read worker logs, poll
`list_agents`, search source, request status or acknowledge informational
messages, and don't take over the lead's debugging when it misses a checkpoint.

For external processes, designate one monitor, routed as `working-conventions`
› Model routing describes; don't add an agent just to watch the lead.

## User-facing updates

Update the user as `working-conventions` › Updates describes. After the initial
checklist, the qualifying events are lead events: reviewed acceptance, a
material finding, a decision request, or a changed scope, route, blocker or
delivery expectation. Never inspect workers just to fill a message.

Supply enough background to make sense without opening a pilot chat; do not
merely compress the lead's packet. Combine actual checklist changes with these
updates and show the final state at handoff. Report acceptance only after
navigator review, labelled as `working-conventions` › Review loops describes,
and keep the lead's and pilots' caveats in the user's report.

## Documentation footprint

Records follow `working-conventions` › Records and
[maintain-project-status](../maintain-project-status/SKILL.md). Component docs
explain durable usage and design; add a document only for a distinct ongoing
reader need. The navigator sets retention; the lead consolidates findings with
one document owner. Keep reusable source, harnesses, tests, and required
fixtures as normal files, and review the documentation footprint in the normal
publication diff.

## Parallel work, continuity, and publication

- Dependent work remains sequenced; independent checklist items need explicit
  navigator assignments.
- Before parallel edits, or builds and measurements on a shared host, read
  [references/parallel-work.md](references/parallel-work.md).
- On changed direction, pause affected pilots, reconcile outstanding edits, and
  update assignments. Honor user pauses by stopping work and retaining a
  checkpoint.
- For interruption or context reset, checkpoint and resume as
  `working-conventions` › Continuity describes, including outstanding diffs and
  their owners.
- When publication is authorized, one owner publishes accepted changes as
  `working-conventions` › Publication describes.
