---
name: continuous-peer-review
description: Collaboratively design and implement small increments with a persistent native reviewer subagent, reviewing completed snapshots while implementation continues. Use when the user wants continuous, concurrent review with direct agent messaging throughout implementation.
---

# Continuous Peer Review

**Load `iExalt:working-conventions` before any other step.** It holds the
rules shared across the workflow skills, and this skill cites its sections as
`working-conventions` › Section without restating them. Invoke it as a skill,
or read its `SKILL.md` where your harness lists the path.

Use two roles: the main agent owns implementation and integration; one native
reviewer subagent jointly shapes increments and independently reviews their code.
Keep the reviewer involved through the milestone, with relevant goal, design, and
finding context. This workflow has no facilitator, external provider CLI, or
nested review team.

## Establish the collaboration

Inspect the task, repository rules, and existing work. Keep a visible checklist
of small, coherent behavioral increments and their dependencies. An increment
has an outcome and acceptance check, not an arbitrary file or line-count limit.
Agree increment boundaries with the reviewer before implementation, separating
independently verifiable behavior when it would otherwise delay useful feedback.

Brief the reviewer as `working-conventions` › Delegation describes, with the
author's native agent address as its return address (the ID or name the
messaging tool accepts, never a session title), and add milestone
boundaries, supported behavior, repository instructions, baseline, available
tests, deferred verification, whether the user authorized idle review of
unrelated repository areas, and these skill instructions. The reviewer reads
the relevant source independently and challenges shared design assumptions as
well as departures from the plan. Its first reply proves the return address
works; fix the route before sending the first review request.

The reviewer must be a native subagent with direct message delivery. If the
harness cannot provide one, handle it as `working-conventions` › Delegation
describes; never substitute an external CLI or pretend concurrent review
occurred. Do not spawn extra agents
unless separately authorized. The reviewer does not edit the author's files,
commit, publish, or launch another reviewer. It may inspect, suggest concrete
fixes, and run permitted isolated probes without changing the reviewed artifact.

## Joint design, risk-based overlap

Jointly shape each increment before implementation, focusing on unresolved
decisions, changed assumptions, and consequential failure cases. A routine
increment needs only a brief amendment to settled designs and agreement; expand
the proposal when behavior, interfaces, dependencies, or acceptance evidence
need discussion. Agree the design and closure criteria, batching upcoming
proposals so the reviewer can answer while reviewing the preceding increment.
Before agreeing a design that adds a new kind of dependency or boundary
(process, network, storage or trust), the reviewer checks it against the
repository's existing architectural rules and checks.

Agree on the discriminating verification before coding: what would distinguish
correct behavior from the plausible failure? For consequential execution paths,
name the real entry point, relevant clean-environment assumptions, and failure/retry
cases. Exercise that path end to end with safe fixtures or a rehearsal early;
helper tests alone do not cover orchestration. Before a consequential rollout,
review the actual command or script, canary target, stop condition, and recovery
plan. A concurrency limit does not establish a canary or stop-on-failure boundary.

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

Hand off each increment with a review request (see Messages and attention),
naming the comparison baseline and any changed dependencies. Give raw delta and
evidence references before your interpretation so the reviewer forms an
independent assessment. For complex or consequential changes, map agreed
criteria to expected and observed results and evidence locations. Include
relevant untracked artifacts. Keep one compact ledger in the conversation or an
existing task document.

Prefer existing exact commits and `git show REV:path` for source inspection; when
the commit supplies the review inputs, skip a separate snapshot copy or manifest.
Read the review SHA from `git rev-parse --verify 'HEAD^{commit}'` after the commit
exists; never predict it or substitute a proposed commit message for a revision.
The reviewer rejects a revision that doesn't resolve rather than reviewing HEAD.
A changing checkout, HEAD label, or diff alone is not a stable source snapshot.
For uncommitted work, freeze the relevant source and dependencies in an identified
read-only review snapshot; keep actual implementation in the original repository.
If probes need a filesystem, run them against that snapshot in an isolated test
location. Tests of a newer checkout do not establish results for an older
snapshot.

Keep one reviewer-owned verification environment for the session: a detached
worktree and build/output directory in a predictable sibling location such as
`../<repo>-review/`, never inside the author's tree. Move it between submitted
snapshots with `git checkout --detach REV` and rebuild incrementally; do not create
a fresh worktree or build cache per increment or revision. Keep mutable test outputs
separate. Rebuild affected artifacts; do not reuse results across changed inputs.
Use an empty build/output directory only when clean-checkout behavior is the
property under test, and remove it afterward. Preserve independent
counterexamples, but repeat expensive unchanged checks only when a changed
dependency, failure, or coverage gap warrants them. Name the snapshot and
environment for evidence carried forward.

Track increment states: planned, design-agreed, implementing, awaiting-review,
changes-requested, awaiting-verification, accepted. They refine
`working-conventions` › Work states: design-agreed is designed, implementing
through awaiting-verification are implemented, and accepted is reviewer-accepted.
Distinguish code review complete, ready for a bounded live validation, and ready
to publish. When closure needs live evidence, agree the permitted trial and its
bounds within the user's authorization, then keep the increment pending until
the evidence is reconciled. Publication requires the applicable review and
checks to be complete; needing live proof does not itself justify an early push.
Later changes invalidate acceptance only for their affected delta and dependencies,
which must be reviewed before completion. Pushing to an open PR, including a CI
fix, follows `working-conventions` › Review loops.

Allow at most **two completed increments awaiting acceptance**, counting the one
under review and any awaiting repairs, re-review, or required verification.
At the cap, prioritize repairs, tests, and reviewer questions rather than starting
more feature implementation.
Do not split an increment merely to evade the cap. Mark which later increments a
finding affects; invalidate dependent acceptance where its assumptions no longer
hold. Review revisions of an existing increment do not consume another slot.

The reviewer examines correctness, affected callers, failure paths, regressions,
and acceptance coverage proportional to the increment. The author's checklist is
evidence and does not bound the review: seek independent counterexamples to shared
assumptions and use targeted probes where they add confidence beyond rerunning the
author's tests. The reviewer sends findings as Messages and attention describes,
then explicitly reports completion and coverage limits; silence or a preliminary
finding is neither acceptance nor completed review. Re-review a revision from its
delta against the previously reviewed snapshot, limited to affected paths.

When tests change, author and reviewer assess their cost as
`working-conventions` › Test cost describes. Ordinary logic that requires a
browser or deployment to test may need a cleaner boundary.

## Messages and attention

Use native direct messaging (for example `collaboration.send_message` in Codex,
or `SendMessage` in Claude Code). Apply `working-conventions` › Delegation's
state check: in Codex, resume a completed reviewer with
`collaboration.followup_task`; message a running reviewer with
`collaboration.send_message`. The request carries the review content; end a
reviewer turn with a one-line final response naming what was sent rather than
restating it.
Process messages at the next available boundary and before starting dependent or
consequential actions. Send urgent messages in a separate completed tool step
before starting a long operation; batching them together can delay delivery.

Keep messages concise and distinguish these purposes:

- **Design:** increment, proposed behavior, dependencies/risk, concrete open question.
- **Review request:** increment ID, stable revision/delta, behavior change,
  evidence/limits, and unresolved questions; name affected pending work when relevant.
- **Finding:** stable ID, severity, evidence/revision, impact, affected increments,
  suggested repair and closure case; mark provisional uncertainty explicitly.
- **Decision:** accepted/challenged/deferred finding or amended design, with reasons.
- **Review result:** reviewed snapshot; changed finding dispositions; coverage and
  limits; explicit acceptance, pending verification, or changes requested. Name
  remaining checks and any agreed live-validation bounds.

Deliver findings immediately but interrupt work by impact. Safety issues and
invalidated assumptions redirect affected work as soon as delivered. Local fixes
wait for a convenient boundary; independent implementation can continue. The
main agent acknowledges material findings and names the affected work it paused
or the boundary at which it will repair. Do not stop unrelated work for every nit.

One reviewer has finite attention. Prioritize urgent findings/design blockers,
then the oldest outstanding review, then upcoming design proposals. The author
can prepare proposals and tests while waiting, but cannot count a pending proposal
as agreement.

## Reviewer idle time

The reviewer spends spare capacity on the prioritized idle work in
[references/idle-time.md](references/idle-time.md); inbound messages always take
priority. Where the harness ends the reviewer's run after each reply, as Claude
Code does, the author reads that file to assign bounded idle work.

Pre-existing defects that affect the milestone are ordinary findings. Park the
rest as `working-conventions` › Work-item size describes; the author relays the
list to the user and does not act on it without separate authorization.

## Resolve findings and retain context

Challenge findings and proposed remedies with evidence and bounded alternatives.
Neither role wins by authority. Use a focused probe when it can settle a dispute.
Escalate a material stalemate to the user when correctness, safety, scope, or
architecture remains unresolved; keep affected work blocked and continue
independent work. Defer optional improvements explicitly rather than making them
completion requirements.

If a proposed repair adds substantial behavior, treat it as a design delta before
coding: agree its boundaries, affected dependencies, and discriminating tests,
and use a separate increment when independently reviewable, subject to the same
backlog cap. Preserve the original finding's closure conditions.

The author implements agreed fixes and exercises the affected counterexamples and
any newly added execution paths before resubmission, preserving finding IDs.
Reassess as soon as a design flaw is apparent instead of repeating partial fixes;
`working-conventions` › Repeated failure sets the default threshold.

Run review rounds as `working-conventions` › Review loops describes, against
the materiality bar agreed in the brief; output from extra one-shot reviewers is
triaged but is not the completion gate. When the loop calls for the user, stop
and ask, showing the ledger lines, and offer accepting with deferrals, a
redesign, or an agreed number of further rounds; don't leave it for the final
report.

Maintain a compact shared record: the checkpoint contents `working-conventions`
› Continuity lists, plus dependencies, closure evidence and next reviewer work.
Messages report changes to this record instead of repeating it. At milestone
boundaries, consolidate it into that checkpoint with evidence references. When
the harness allows requesting compaction, compact after the checkpoint rather
than waiting for automatic compaction. If the reviewer must be replaced,
transfer this record and evidence references; do not silently restart
discovery. When a durable campaign outlives its native reviewer, as when a
resumed session finds it gone, start a new native reviewer with the record.
Earlier verdicts stay acceptances of the revisions they named; the
replacement's verdict covers only what it reviewed itself.

## Integration and completion

At a meaningful milestone boundary, drain the review backlog and obtain a focused
integration review of the final stable revision. Check interactions between
increments, shared invariants, affected dependencies, and outstanding findings.
Revisit settled code only for a concrete interaction, changed dependency, coverage
gap, or new evidence. Run the appropriate combined checks; passing increment tests
alone is not integration acceptance.

Complete authorized publication through `working-conventions` › Publication,
then report with its Completion contract and reconcile the canonical progress
record. A pending PR remains pending when merge is part of the approved outcome.

Finish only when the reviewer and main agent agree the final milestone satisfies
its criteria with no unresolved material findings under the agreed bar; deferred
optional findings do not block. At session end, the reviewer removes its
verification environment and reports the space freed; if it cannot, the author
removes it.

For an efficiency trial, record what
[references/efficiency-trial.md](references/efficiency-trial.md) lists.
