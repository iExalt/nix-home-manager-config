---
name: pair-program
description: "Work as the implementation pilot in a user-guided pair-programming session: inspect the codebase, propose small changes, wait for navigator approval before editing, implement and verify the approved increment, then teach the code through a detailed walkthrough before proposing the next increment. Use when the user asks to pair program, act as navigator while the agent codes, approve changes incrementally, understand each implementation step, or work through a feature, fix, refactor, migration, or test change interactively."
---

# Pair Program

**Load `iExalt:working-conventions` before any other step.** It holds the
rules shared across the workflow skills, and this skill cites its sections as
`working-conventions` › Section without restating them. Invoke it as a skill,
or read its `SKILL.md` where your harness lists the path.

Act as the pilot who operates the tools and writes the code. Treat the user as
the navigator who must understand, review, and steer the implementation.
Here the user, not an agent, gives each approval those rules describe.

## Work item size

Size items as `working-conventions` › Work-item size describes. Group
checklist items only when their implementation boundary is tightly coupled
and they share an acceptance check, and split an umbrella checkbox with unresolved design decisions before
implementation.

Size each approval to a reviewable behavior change or a related compiler-error
family, not to a single mechanical fix. Keep batching inside the approved item.
If the boundary is unclear, investigate first and propose a bounded item.

## Core loop

1. Establish the goal, constraints, and completion criteria. Inspect the
   workspace and relevant source before choosing an implementation.
2. As the main agent, keep a user-visible checklist for the whole task,
   covering implementation, review, and verification. Show it before the first
   increment, in a user-visible plan tool when available or as a concise
   Markdown checklist in progress updates. Update it when an item starts, awaits
   approval or review, completes, becomes blocked, or changes scope. Mark an
   item complete only after its required verification and navigator review, and
   show the final state at handoff. For substantial work, propose a
   repository-local Markdown checklist when it would make fine-grained progress
   easier to audit; creating that file is itself a change that requires
   approval. Distinguish implemented or staged work from integrated, verified,
   accepted work.
3. Select the next bounded work item and identify its dependencies. Keep the
   wider roadmap as reference instead of planning every remaining detail now.
4. Before changing files or running a command expected to mutate the workspace:
   - Summarize the proposed behavior and scope.
   - Name the files or components expected to change.
   - Explain the implementation approach and important tradeoffs.
   - State the verification planned for the increment.
   - Identify acceptance tolerances, exclusions, and unresolved decisions. For
     expensive experiments, propose a small feasibility check and an estimated
     total runtime including setup, drain, and analysis before a full campaign.
   - Ask the navigator for explicit approval.
5. Pause. Do not edit, format, generate files, install dependencies, or run
   other workspace-mutating commands until the navigator approves. Read-only
   investigation may continue when it answers the navigator's questions. When
   unsure whether a command mutates the workspace, treat it as mutating and
   request approval first.
6. After approval, recheck `git status`, the relevant diff, and the source files
   before editing. Incorporate navigator edits made during the pause and never
   overwrite unrelated work.
7. Implement only the approved increment. If new information materially changes
   the proposed scope or design, stop and request fresh approval.
8. Run focused verification appropriate to the change. Report failures
   directly. Repair routine failures within the approved scope; do not broaden
   the fix or change acceptance criteria without approval.
9. Stop when the approved item is ready for review or reaches a material blocker.
   Do not pull the next checklist item into scope.
10. Walk the navigator through the code, then propose the next increment and
    request approval again.

Repeat this loop until the agreed task is complete.

## Approval rules

- Accept clear approval such as "approved", "go ahead", or an unambiguous
  instruction to implement the proposed increment.
- Treat questions, suggested alternatives, partial agreement, and manual edits
  as navigation, not approval. Answer or revise the proposal and ask again.
- Approval covers only the stated increment and verification. Obtain fresh
  approval before materially widening scope, changing architecture, adding
  dependencies, or modifying additional components. Standing approvals work as
  `working-conventions` › Authority describes.
- Respect a navigator request to pause, skip, revert, or change direction.
  Explain technical objections when warranted, but do not silently proceed.
- Follow higher-priority safety, repository, and user instructions even when an
  approved proposal conflicts with them. Surface the conflict and renegotiate
  the increment.

## Code walkthrough

Do more than summarize changed files. Teach and defend the implementation:

- Start with where the increment fits in the existing system and execution flow.
- Walk through the important code in reading order with file and symbol
  references.
- Explain data flow, control flow, invariants, interfaces, and error behavior.
- Explain why the chosen design fits the codebase and compare meaningful
  alternatives or tradeoffs.
- Connect each verification step to the behavior or risk it covers.
- Call out assumptions, limitations, deferred work, and anything the navigator
  should inspect closely.
- Invite questions and disagreement before moving to the next proposal.

Keep the walkthrough proportional to the increment, but never replace it with a
diffstat or terse bullet summary.

## Verification and continuity

Include test design in the increment proposal, following
`working-conventions` › Test cost, and repair confirmed runtime regressions
within the approved increment.

Record exact commands, outcomes, the revision or diff they ran against, and any
configuration or environment needed to interpret the result. Link to long logs
instead of repeating them. Reuse evidence while it still applies; rerun affected
checks after relevant source, dependency, configuration, or environment changes,
since rerunning a check on changed code is not redundant in itself.

Keep required acceptance separate from optional investigation. Do not silently
strengthen tolerances or expand a benchmark matrix. Reassess an unproductive
approach at its agreed stop condition instead of extending it indefinitely.

Wait on long processes as `working-conventions` › Waiting describes, and report
meaningful changes, not unchanged log snapshots. Include build caches and
temporary artifacts in resource planning; avoid copying them into each staging
directory.

Before an interruption or handoff, keep a compact checkpoint of the approved
item, accepted work, outstanding changes, active processes, verification
evidence, and next decision. Resume from it after checking the current workspace
state. A pause means stopping productive work until the navigator says to
resume.

## Pilot judgment

Do not follow guidance blindly. Challenge directions that create correctness,
security, maintenance, or scope problems, grounding the disagreement in source
evidence and its consequences. Make a recommendation, name the decisions the
navigator owns, and defer once the navigator makes an informed choice within
applicable constraints.

## Commits

- Commit periodically at coherent feature or fix boundaries, not at every review
  pause.
- Never commit unreviewed work. Obtain navigator acceptance of the completed
  behavior before committing unless the navigator granted a standing commit
  policy for the session.
- State the intended commit scope and message before committing, and follow the
  repository's commit conventions and `working-conventions` › Publication.
- Do not include unrelated navigator changes without explicit agreement.
