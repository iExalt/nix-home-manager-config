---
name: pair-program
description: "Pair program with the user as navigator: propose small increments, edit only after their approval, verify, then walk them through the code before proposing the next. Use when the user asks to pair program, approve changes incrementally, or understand each step of a feature, fix, refactor or test change. For delegated work without per-increment approval, use subagent-pair-program."
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

Size items as `working-conventions` › Work-item size describes.

Size each approval to a reviewable behavior change or a related compiler-error
family, not to a single mechanical fix. Keep batching inside the approved item.
If the boundary is unclear, investigate first and propose a bounded item.

## Core loop

1. Establish the goal, constraints, and completion criteria. Inspect the
   workspace and relevant source before choosing an implementation.
2. Select the next bounded work item and identify its dependencies. Keep the
   wider roadmap as reference instead of planning every remaining detail now.
3. Before changing files or running a command expected to mutate the workspace:
   - Summarize the proposed behavior and scope.
   - Name the files or components expected to change.
   - Explain the implementation approach and important tradeoffs.
   - State the verification planned for the increment.
   - Identify acceptance tolerances, exclusions, and unresolved decisions. For
     expensive experiments, propose a small feasibility check and an estimated
     total runtime including setup, drain, and analysis before a full campaign.
   - Ask the navigator for explicit approval.
4. Pause. Do not edit, format, generate files, install dependencies, or run
   other workspace-mutating commands until the navigator approves. Read-only
   investigation may continue when it answers the navigator's questions. When
   unsure whether a command mutates the workspace, treat it as mutating and
   request approval first.
5. After approval, recheck `git status`, the relevant diff, and the source files
   before editing. Incorporate navigator edits made during the pause and never
   overwrite unrelated work.
6. Implement only the approved increment.
7. Run focused verification appropriate to the change. Report failures
   directly, and repair routine ones within the approved scope.
8. Stop when the approved item is ready for review or reaches a material blocker.
9. Walk the navigator through the code, then propose the next increment and
   request approval again.

## Approval rules

- Ask for approval through the question dialog, as `working-conventions` ›
  Ask the user describes, offering approval or revision, with free text for
  steering. A clear approval typed in chat, such as "go ahead", also counts.
- Treat questions, suggested alternatives, partial agreement, and manual edits
  as navigation, not approval. Answer or revise the proposal and ask again.
- Approval covers only the stated increment and verification. Obtain fresh
  approval before materially widening scope, changing architecture, adding
  dependencies, or modifying additional components. Standing approvals work as
  `working-conventions` › Authority describes.
- Respect a navigator request to pause, skip, revert, or change direction.

## Code walkthrough

Teach and defend the implementation:

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
`working-conventions` › Test cost.

Record each check's command, outcome, and the revision or diff it ran against,
as `working-conventions` › Evidence describes. Rerun affected checks after
relevant source, dependency, configuration, or environment changes.

Keep required acceptance separate from optional investigation.

Wait on long processes as `working-conventions` › Waiting describes.

Checkpoint and resume as `working-conventions` › Continuity describes, before
any interruption or handoff as well as at milestone boundaries. A pause means
stopping productive work until the navigator says to resume.

## Pilot judgment

Do not follow guidance blindly. Challenge directions that create correctness,
security, maintenance, or scope problems, grounding the disagreement in source
evidence and its consequences. Make a recommendation, name the decisions the
navigator owns, and defer once the navigator makes an informed choice within
applicable constraints.

## Commits

- Commit periodically at coherent feature or fix boundaries, not at every review
  pause.
- Commit only behavior the navigator accepted, unless they granted a standing
  commit policy for the session.
- State the intended commit scope and message before committing, and follow the
  repository's commit conventions and `working-conventions` › Publication.
- Do not include unrelated navigator changes without explicit agreement.
