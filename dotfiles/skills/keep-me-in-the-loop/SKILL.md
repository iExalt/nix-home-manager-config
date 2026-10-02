---
name: keep-me-in-the-loop
description: Execute an existing roadmap in coherent chunks with upfront phase approval, continuous peer review, project-status updates, and TL;DR progress reports. Use when the user wants sustained roadmap execution with control between substantial phases; not for a one-off task or initial open-ended project discovery.
---

# Keep Me in the Loop

Turn the next substantial phase of an existing plan into a few meaningful chunks.
Obtain approval for that phase's chunk plan once, then implement, review, verify,
commit, and push each chunk autonomously. Report between chunks and continue;
seek approval for the next phase after finishing the current one. Preserve explicit
user overrides and repository rules.

## Establish the current boundary

Read the governing plan, roadmap/checklist, and existing project-status document.
Inspect current source, relevant verification evidence, Git state, and repository
instructions to establish what is complete and what remains. Do not infer phase
completion from checked subtasks or prior summaries alone. Preserve unrelated work.

Use `maintain-project-status` for the durable progress record and
`continuous-peer-review` for implementation and review. Read their current
instructions; resolve them from the available skill catalog or sibling skill
directories. Keep this skill responsible for phase boundaries and user reports,
leaving status semantics and reviewer mechanics to those skills. If a required
skill or native review capability is unavailable, explain the limitation and
resolve the execution approach before claiming the workflow can proceed.

Reuse one project-wide status document and the active plan/checklist. Create a
status document through `maintain-project-status` when one is missing, using the
repository's documentation conventions. Keep only a few decisive receipts inline;
do not create per-chunk reports or commit raw execution logs.

## Propose one substantial phase

Start with a one- or two-line **TL;DR** stating the current outcome and proposed
next result. Briefly explain what has been accomplished in the phase or plan so
far, including its verification boundary.

Propose roughly **2–4 coherent chunks** for a substantial phase. This is a sizing
guide, not a quota. Group related steps by a useful capability, evidence gate, or
decision. Split at consequential dependencies or where a checkpoint offers useful
feedback; avoid both approval per small task and one oversized uninterrupted phase.
Keep more distant phases coarse.

For each chunk, name:

- its outcome and covered roadmap steps;
- why the boundary is useful and what it depends on;
- its acceptance checks and any verification assigned to a named later gate;
- material exclusions, risks, or external actions the user needs to assess.

Make the overall phase boundary and important decisions clear. State that approval
covers autonomous execution across these chunks, progress reports between them,
and committing/pushing each completed chunk after required checks and review.
Do not infer permission for unrelated external actions, destructive operations,
or infrastructure spending from the publication default. Carry forward existing
authorization and identify any additional authority actually needed.

Obtain phase approval before implementation unless the current instructions
already approve that concrete scope. Silence is not approval. Use a permitted
native dialog when available, respecting its restrictions on permission requests.
Do not repeat settled questions or request approval for every internal increment.
If outcomes or major tradeoffs are still unclear, use `agentic-workflow` to resolve
them before turning a speculative route into an implementation commitment.

## Execute approved chunks

Keep a visible checklist of phase chunks, with the current chunk and outstanding
checks clear. Work through the approved chunks in dependency order.

Within each chunk:

1. Use `continuous-peer-review` to jointly shape and review small implementation
   increments. A user-facing chunk may contain several reviewer increments.
   Reuse reviewer context across the phase when the harness supports it. Do not
   add a separate peer-review loop or duplicate the review skill's controls.
2. Implement and resolve routine technical decisions and necessary fixes
   autonomously within the approved outcome. Record unrelated improvements and
   pre-existing bugs for later; ask before materially expanding scope.
3. Run available discriminating checks now. Defer expensive or unavailable
   verification only when the chunk's acceptance criteria permit it. Attach each
   deferral to a specific later roadmap gate, naming what remains unproven and
   the evidence required there. Never silently move a required closure check to
   a later gate merely to finish or publish the chunk.
4. Complete the review skill's milestone/integration closure and required checks
   for the chunk. Distinguish implemented, verified, reviewer-accepted, and
   published states. A deferred live proof does not establish live correctness.
5. Reconcile the plan/checklist and project-status document with the evidence.
   Commit scoped changes using conventional commits and push after required
   checks and review pass, unless repository rules or explicit instructions
   override that default. Verify publication before reporting it as complete.
6. Report the outcome and proceed directly to the next approved chunk. Do not
   append an approval question or end execution just because a report is due.

If the user updates a supporting skill mid-phase, re-read it and communicate
relevant changes to the active reviewer before affected work continues. Preserve
accepted decisions, unresolved findings, and verification obligations across
context refreshes or session resumes; inspect current state before resuming.

## Reassess when evidence changes

Follow `continuous-peer-review`'s existing backlog and disagreement controls.
Surface a material stall with its cause, impact, and a recommended adjustment.
Do not impose an inherited two-round limit, launch extra review loops, or close
required findings to meet a time target. Keep affected work pending until the
required findings and checks are resolved; continue independent authorized work.

Routine technical replanning, repairs, and changes to internal increment size
remain autonomous. Return to the user when evidence requires a material change
to scope, priorities, acceptance criteria, cost, risk, or an approved checkpoint.
Explain the new evidence and recommend the smallest useful adjustment. Do not
silently weaken acceptance criteria or treat sunk effort as a reason to continue.

## Report for quick reading

Begin chunk reports and phase proposals with a **TL;DR** of one or two lines.
Use compact bullets by default; expand for consequential changes, surprises, or
decisions. Explain outcomes and what the user can now do or know before technical
details. Avoid replaying the implementation chronology or dumping test counts.

A typical chunk report covers:

- **Accomplished:** meaningful behavior or evidence gained, with roadmap IDs
  when useful.
- **Evidence and limits:** decisive checks, required review closure, and named
  deferred verification gates. State whether newly reported bugs are fixed,
  still open, or explicitly deferred.
- **Publication:** commit/push status with a useful revision reference; disclose
  any publication failure without claiming the chunk is fully delivered.
- **Next:** the next approved chunk and its outcome, or the specific decision
  needed if the approved route can no longer proceed.

This is a content guide, not a requirement for four headings in every update.
Keep detailed evidence in the project-status document. Follow the user's progress
cadence during execution; report meaningful progress and blockers, and use
interruptible waits without repeated unchanged-status updates.

At phase completion, reconcile the phase's full exit criteria with current
evidence and report results, accepted deferrals, and remaining boundaries.
Propose the next phase's chunks and await approval before implementing them,
unless the user has explicitly authorized that next phase already. If the roadmap
is finished, report completion and remaining limitations without inventing work.
