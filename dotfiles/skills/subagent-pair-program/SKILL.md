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

## Navigator Loop

1. Establish the user's goal, constraints, and completion criteria. Inspect the
   workspace, applicable instructions, relevant source, and existing changes.
   Maintain a checklist covering implementation, review, and verification.
2. Choose the smallest coherent increment that can be reviewed independently.
   Use one pilot for tightly coupled work. Add pilots when bounded tasks can run
   independently alongside useful navigator work; identify dependencies and file
   ownership before parallelizing.
3. Give each pilot a concrete assignment with:
   - The desired behavior and acceptance criteria.
   - Relevant source context, constraints, and applicable instructions.
   - The workspace or worktree and files or components it may change.
   - Known concurrent work and dependencies.
   - Expected verification and a requirement to propose its approach before edits.
   - An explicit instruction to address proposals and questions to you, the
     navigator, and wait for your approval before implementation.
4. Review the pilot's proposal against the source and overall design. Resolve
   tradeoffs yourself within the user's authorized scope. Approve the specific
   increment and verification, or send concrete revisions. An assignment that
   already supplies and explicitly approves a complete approach can serve as
   approval; do not require a redundant exchange.
5. While the pilot implements, inspect affected interfaces, resolve upcoming
   design questions, or review other independent increments. Keep implementation
   ownership with pilots rather than editing their assigned files concurrently.
6. Review the actual diff and verification evidence when the pilot returns.
   Require a proportional code walkthrough, investigate unsupported claims, and
   return actionable corrections to the responsible pilot. A pilot's completion
   message alone does not establish acceptance.
7. Accept the increment only when its behavior and checks satisfy the criteria.
   Update the checklist, release dependent work, and assign the next increment.
   Reuse pilots when their retained context is useful.
8. After the increments are accepted, inspect the combined result and run or
   direct appropriate integration checks. Resolve failures through the same
   review loop. Continue until the user's completion criteria are met or a
   concrete blocker prevents further authorized progress.

## Pilot Contract

Include these expectations in pilot assignments; do not assume pilots inherit
this skill or the navigator's full context:

- Inspect the assigned source before proposing behavior, affected files,
  implementation approach, tradeoffs, and verification.
- Wait for navigator approval before changing files. Before editing, recheck
  the relevant source and working-tree changes to preserve concurrent work.
- Implement only the approved increment. If findings materially change the
  scope, design, dependencies, or file ownership, bring a revised proposal to
  the navigator before proceeding.
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
