---
name: keep-me-in-the-loop
description: Execute an existing roadmap in coherent chunks with upfront phase approval, continuous peer review, project-status updates, and TL;DR progress reports. Use when the user wants sustained roadmap execution with control between substantial phases; not for a one-off task or initial open-ended project discovery.
---

# Keep Me in the Loop

**Load `iExalt:working-conventions` before any other step.** It holds the
rules shared across the workflow skills, and this skill cites its sections as
`working-conventions` › Section without restating them. Invoke it as a skill,
or read its `SKILL.md` where your harness lists the path.

Turn the next substantial phase of an existing plan into a few meaningful chunks.
Shape that chunk plan with the reviewer, obtain the user's approval once, then
implement, review, verify, and complete each chunk's authorized publication. Report
between chunks and continue; seek approval for the next phase after finishing
the current one, unless the user approved the remaining phases together.

## Establish the current boundary

Read the governing plan, roadmap/checklist, and canonical progress record
(tracker or project-status document, as `working-conventions` › Records describes).
Inspect current source, relevant verification evidence, Git state, and repository
instructions to establish what is complete and what remains.

When invoked for a workstream issue, such as `Run workstream #<N>`, the issue
is the phase's entry: its scope, proposed chunks, dependencies, human
interventions, live resources and done check. Claim it, work in the worktree
it implies, and finish it as the repository's instructions say. Record a
deviation that changes another workstream on that workstream's issue.

Use `maintain-project-status` for the durable progress record and
`continuous-peer-review` for implementation and review; status semantics and
reviewer mechanics belong to those skills.

Start the `continuous-peer-review` reviewer before drafting the first phase
proposal; it persists across chunks and phases as `working-conventions` ›
Review loops describes.

## Propose one substantial phase

After the TL;DR, briefly say what the phase or plan has accomplished so far,
including its verification boundary.

Propose roughly 2 to 4 coherent chunks; the range guides sizing and is not a
quota. Group related steps by a useful capability, evidence gate, or decision.
Split at consequential dependencies or where a checkpoint offers useful
feedback; avoid both approval per small task and one oversized uninterrupted
phase. Keep more distant phases coarse.

For each chunk, name:

- its outcome and covered roadmap steps;
- why the boundary is useful and what it depends on;
- its acceptance checks and any verification assigned to a named later gate;
- any scarce shared resource it occupies and for how long, batching the proofs
  that need it into as few named windows as the acceptance checks allow;
- material exclusions, risks, or external actions the user needs to assess.

Make the overall phase boundary and important decisions clear. State that
approval covers autonomous execution across these chunks, progress reports
between them, and committing and pushing each completed chunk after required
checks and review. Name any further authority needed, such as unrelated
external actions, destructive operations or spending.

Shape the proposal with the reviewer before presenting it: send the draft chunk
plan, acceptance checks, deferral gates, risks and requested authority with the
raw roadmap and evidence locations. Revise until you agree or the disagreement
is clear, and present the reviewer's position as `working-conventions` ›
Review loops describes.

Obtain phase approval before implementation unless the current instructions
already approve that concrete scope, asking as `working-conventions` › Ask the
user describes and respecting the dialog's restrictions on permission requests.
If outcomes or major tradeoffs are still unclear, use `agentic-workflow` to
resolve them before turning a speculative route into an implementation
commitment.

When the roadmap's later phases stay inside the agreed scope and hold no taste,
scope, cost or release decision, offer to approve them together with this
phase, and recommend it. List those phases coarsely, and name any decision you
already know will come back to the user. Offer approval of this phase alone as the
alternative. Under a multi-phase approval, shape each next phase with the
reviewer, describe it in the phase-completion report, and start it in the same
turn. Return to the user before a phase that departs from the approval or
reaches a decision it left to them.

## Execute approved chunks

Keep a visible checklist of phase chunks, with the current chunk and outstanding
checks clear. Work through the approved chunks in dependency order.

Within each chunk:

1. Use `continuous-peer-review` to jointly shape and review small implementation
   increments within the approved chunk plan. A user-facing chunk may contain
   several reviewer increments. Do not add a separate peer-review loop or
   duplicate the review skill's controls.
2. Run available discriminating checks now. Defer verification only to a named
   later roadmap gate the chunk's acceptance criteria allow, never merely to
   finish or publish the chunk; `working-conventions` › Evidence governs
   deferrals and unmet proofs.
3. Complete the review skill's milestone/integration closure and required checks
   for the chunk, using `working-conventions`' work states.
4. Complete authorized publication as `working-conventions` › Publication
   describes, including PR follow-through when required. Reconcile the
   plan/checklist and canonical progress record with the verified outcome.
5. Report the outcome and proceed directly to the next approved chunk. Do not
   append an approval question or end execution just because a report is due.

## Reassess when evidence changes

Follow `continuous-peer-review`'s backlog and disagreement controls, and
`working-conventions` › Authority for replanning. Surface a material stall with
its cause, impact, and a recommended adjustment. Never close required findings
to meet a time target.

## Update at increment outcomes

Between the phase proposal and chunk reports, send updates for the events
`working-conventions` › Updates lists, plus one when a chunk's increment
design is agreed and implementation starts. Before sending any text between
tool calls, check that it reports one of these events or is text the user's
instructions require; if not, send nothing, not even a note on what you're
about to do.

Check each reviewer message against these events when it arrives, including one
queued during a tool loop; report a qualifying event at the next tool boundary
rather than folding it into later work.

Write each update as a status prefix (the chunk and its accepted increments
out of those planned) followed by one sentence on what is now true and what
follows, such as
`Chunk B · 3/5 accepted — Ceph pools are now selected by node label; B4 next.`
Move anything longer into the chunk report.

Monitor a live operation only for failures, unexpected states and its
completion, keeping routine progress in a log read at decision points. When the
user asks for action-only updates, restart the monitor with a filter that
matches only events needing action, and check its first events against that
request.

## Report for quick reading

Use compact bullets by default; expand for consequential changes, surprises, or
decisions.

Use `working-conventions` › Completion for chunk and phase completion reports.
Include roadmap IDs when useful and state whether newly reported bugs are
fixed, still open, or explicitly deferred. The next action is the next approved
chunk or the decision needed when the approved route can no longer proceed.

At phase completion, reconcile the phase's full exit criteria with current
evidence and report results, accepted deferrals, and remaining boundaries.
Shape the next phase's chunks with the reviewer, propose them, and await
approval, unless a multi-phase approval already covers that phase. If the
roadmap is finished, report completion and remaining limitations without
inventing work.
