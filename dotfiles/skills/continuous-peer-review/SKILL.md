---
name: continuous-peer-review
description: Collaboratively design and implement small increments with a persistent native reviewer subagent, reviewing completed snapshots while implementation continues. Use when the user wants continuous, concurrent review with direct agent messaging throughout implementation. For a standalone cross-provider review or sequential repair loop, use peer-review or peer-review-loop instead.
---

# Continuous Peer Review

Use two roles: the main agent owns implementation and integration; one native
reviewer subagent jointly shapes increments and independently reviews their code.
Communicate directly through native agent messages. Keep the reviewer involved
through the milestone, with relevant goal, design, and finding context. There is
no facilitator, external provider CLI, or nested review team in this workflow.
Use the user's model preferences or the native tool's inherited/default model;
cross-provider review is not required.

## Establish the collaboration

Inspect the task, repository rules, and existing work. Keep a visible checklist
of small, coherent behavioral increments and their dependencies. An increment
has an outcome and acceptance check, not an arbitrary file or line-count limit.
Keep tightly coupled behavior together. Respect existing implementation and
publication authority; invoking this skill does not authorize unrelated work.

Spawn the reviewer with a scoped brief: goal, milestone boundaries, supported
behavior, non-goals, acceptance criteria, repository instructions, baseline,
available tests, deferred verification, and the author's native agent address.
Include these skill instructions. Give raw source/evidence locations as well as
prior decisions; distinguish constraints from claims that the code is correct.
The reviewer reads the relevant source independently and challenges shared design
assumptions as well as departures from the plan.

The reviewer must be a native subagent with direct message delivery. If the
harness cannot provide that, report the limitation instead of substituting an
external CLI or pretending concurrent review occurred. Do not spawn extra agents
unless separately authorized. The reviewer does not edit the author's files,
commit, publish, or launch another reviewer. It may inspect, suggest concrete
fixes, and run permitted isolated probes without changing the reviewed artifact.

## Joint design, risk-based overlap

Jointly shape each increment before implementation, focusing the exchange on
unresolved decisions, changed assumptions, and consequential failure cases. Refer
to settled designs and criteria; a brief amendment and agreement suffice for a
routine increment. Expand the proposal when behavior, interfaces, dependencies,
or acceptance evidence need discussion. Obtain agreement on the design and closure
criteria, batching upcoming proposals when useful so the reviewer can answer while
reviewing the preceding increment. Do not repeat a full brief or manufacture a
confirmation call when agreement is already explicit.

Classify dependencies together:

- Routine, reversible work may build on an implemented but unaccepted increment.
  Name that dependency and treat downstream work as speculative until accepted.
- Consequential interface changes, safety boundaries, and major designs require design
  agreement before implementation and acceptance of their implementation before
  dependent work proceeds. Independent work can continue during review.

If implementation exposes conflicting invariants, an unworkable proposal, or a
material boundary change, send the counterexample and proposed amendment to the
reviewer before implementing the replacement design. Continue independent work.
Ordinary implementation choices within the agreed design need no extra approval.

## Review stable increments while implementing

Default to a short handoff: increment ID, stable revision and raw delta reference,
behavior change, relevant tests/evidence and limits, and unresolved questions.
Identify the comparison baseline and any changed dependencies without repeating
settled context. Present raw delta/evidence references before the author's
interpretation so the reviewer can form an independent assessment. For complex or
consequential changes, map agreed criteria to expected and observed results and
evidence locations; do not require that ceremony for every routine increment.
Include relevant untracked artifacts. Keep one compact ledger in the conversation
or an existing task document, not a new receipt per message.

Prefer existing exact commits and `git show REV:path` for source inspection; a
separate snapshot copy or manifest is unnecessary when the commit supplies the
review inputs.
A changing checkout, HEAD label, or diff alone is not a stable source snapshot.
For uncommitted work, freeze the relevant source and dependencies in an identified
read-only review snapshot; keep actual implementation in the original repository.
If probes need a filesystem, run them against that snapshot in an isolated test
location. Do not check out old revisions in the author's active working tree.
If stable review inputs cannot be supplied, pause conflicting edits during review
and disclose the reduced parallelism. Tests of a newer checkout do not establish
results for an older snapshot.

Track increment states: planned, design-agreed, implementing, awaiting-review,
changes-requested, accepted. An accepted result names the reviewed snapshot.
Later changes invalidate acceptance only for their affected delta and dependencies,
which must be reviewed before completion.

Allow at most **two completed increments awaiting acceptance**, counting the one
under review and any awaiting repairs or re-review. At the cap, prioritize repairs,
tests, and reviewer questions rather than starting more feature implementation.
Do not split an increment merely to evade the cap. Mark which later increments a
finding affects; invalidate dependent acceptance where its assumptions no longer
hold. Review revisions of an existing increment do not consume another slot.

The reviewer examines correctness, affected callers, failure paths, regressions,
and acceptance coverage proportional to the increment. Treat the author's checklist
as evidence, not the boundary of review: seek independent counterexamples to shared
assumptions and use targeted probes where they add confidence beyond rerunning the
author's tests. It sends an actionable
finding as soon as evidence establishes it, rather than waiting for a final batch;
then continues review and explicitly reports completion and coverage limits.
Silence or a preliminary finding is neither acceptance nor completed review.
Use targeted source reads, bounded output, and references to unchanged evidence.

## Messages and attention

Use native direct messaging (for example `collaboration.send_message` in Codex,
or the available equivalent in Claude). Use the harness's resume/follow-up tool
when a reviewer has finished its turn and needs new work; do not assume a message
to an idle agent starts execution. Reuse the same reviewer rather than spawning
one per increment. A native notification is delivery, not an acknowledgment.
Do not promise preemption of an in-flight tool call; process messages at the next
available boundary and before starting dependent or consequential actions.

Keep messages concise and distinguish these purposes:

- **Design:** increment, proposed behavior, dependencies/risk, concrete open question.
- **Review request:** increment ID, stable revision/delta, behavior change,
  evidence/limits, and unresolved questions; name affected pending work when relevant.
- **Finding:** stable ID, severity, evidence/revision, impact, affected increments,
  suggested repair and closure case; mark provisional uncertainty explicitly.
- **Decision:** accepted/challenged/deferred finding or amended design, with reasons.
- **Review result:** reviewed snapshot; open/closed/new IDs; coverage and limits;
  explicit acceptance or changes requested. Design agreement is not code acceptance.

Deliver findings immediately but interrupt work by impact. Safety issues and
invalidated assumptions redirect affected work as soon as delivered. Local fixes
wait for a convenient boundary; independent implementation can continue. The
main agent acknowledges material findings and names the affected work it paused
or the boundary at which it will repair. Do not stop unrelated work for every nit.

One reviewer has finite attention. Prioritize urgent findings/design blockers,
then the oldest outstanding review, then upcoming design proposals. The author
can prepare proposals and tests while waiting, but cannot count a pending proposal
as agreement. When only blocked work remains, use native interruptible waits or
completion notifications; avoid polling loops and unchanged-status messages.

## Resolve findings and retain context

Challenge findings and proposed remedies with evidence and bounded alternatives.
Neither role wins by authority. Use a focused probe when it can settle a dispute.
Escalate a material stalemate to the user when correctness, safety, scope, or
architecture remains unresolved; keep affected work blocked and continue
independent work. Defer optional improvements explicitly rather than making them
completion requirements. Do not silently relax acceptance criteria.

The author implements agreed fixes and exercises the full counterexample batch
before resubmission. For later findings, distinguish incomplete fixes, introduced
regressions, missed original defects, and scope expansion. Preserve IDs and trace
incomplete fixes to implementation deviations or flaws in the agreed proposal.
Reassess as soon as a design flaw is apparent instead of repeating partial fixes.

Maintain a compact shared record: goal and boundaries, settled designs and reasons,
current snapshots, dependencies, finding dispositions, closure evidence, pending
questions, and next reviewer work. Retain relevant context, not entire transcripts
or repeated source dumps. If a reviewer must be replaced or context refreshed,
transfer this record and evidence references, preserving all unresolved findings;
do not silently restart discovery or erase disagreements.

## Integration and completion

At a meaningful milestone boundary, drain the review backlog and obtain a focused
integration review of the final stable revision. Check interactions between
increments, shared invariants, affected dependencies, and outstanding findings.
Revisit settled code only for a concrete interaction, changed dependency, coverage
gap, or new evidence. Run the appropriate combined checks; passing increment tests
alone is not integration acceptance.

Finish only when the reviewer and main agent agree the final milestone satisfies
its criteria with no unresolved material findings. Identify accepted deferrals and
verification limits. Changes after acceptance need proportional delta review;
preserve the task's existing commit, push, and deployment authorization.

For an efficiency trial, capture milestone start/end, review dispatch and acceptance
times per revision, and actual blocked intervals for either role with their cause.
Use native event timestamps where available, otherwise record them as events occur
in the existing ledger. Snapshot creation times do not establish dispatch,
acceptance, or blocking; pending review is not blocked time while other useful work
continues. Mark unavailable measurements as unknown instead of reconstructing them
from snapshots. Report elapsed milestone time, dispatch-to-acceptance turnaround,
blocking, peak outstanding increments, and rework attributable to late findings.
Do not add overlapping agent time to claim elapsed time saved. Distinguish actual
parallel work and early messages from capabilities the trial did not exercise.
Ordinary use needs only the compact coordination record, not trial instrumentation.
