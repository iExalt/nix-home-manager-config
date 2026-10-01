# Review Protocol

Use this protocol in both peer-review and peer-review-loop. The invoking skill
controls whether the main agent automatically repairs and repeats review.

## Discovery before repair

Fix the artifact revision, scope, acceptance criteria, and verification limits
before review. The facilitator gives the reviewer raw artifacts and criteria,
without the author's preferred conclusions. Ask for a complete discovery pass
across the agreed scope before returning findings; do not stop at the first
counterexample or an arbitrary finding count.

Choose coverage areas from the artifact's risks. For code, inspect correctness,
affected callers, boundary and failure paths, regressions, security, tests, and
repository conventions. For plans, inspect completeness, sequencing,
assumptions, rollback, and verification. Investigate related variants of a
failure together. Return a compact coverage record: area, evidence inspected,
checks/probes performed, and gaps or limits. Unchecked areas are not clean.
Resolve material coverage gaps before calling discovery complete; if blocked,
return a partial review rather than starting repairs under a false clean claim.

Batch findings with stable IDs, severity, location/evidence, impact, and proposed
correction. The facilitator verifies them against source. Challenge unsupported
claims and distinguish required fixes from optional improvements. Assign each
finding an accepted, rejected, or unresolved disposition with rationale.
Avoid a separate reconciliation call merely to restate agreed findings.

## Agree on the repair's acceptance criteria

For a complex fix, the main agent and reviewer agree through the facilitator on:

- The invariant that must hold, not just the reported failing example.
- The supported behavior, explicit boundaries, and treatment of unsupported or
  uncertain inputs; refusal may be simpler than extending a partial model.
- A batch of counterexamples and expected outcomes covering the failure class.
- The bounded correction and evidence needed to close the finding.

Do this before implementing a complex repair. Batch related decisions into an
existing dialogue when possible; a straightforward fix needs no extra planning
call. The main agent implements and verifies the whole agreed batch, including
related cases found locally, before resubmission. Do not weaken original task
requirements or safety guarantees to manufacture agreement. Existing defects,
new guarantees introduced by a repair, and optional future hardening are distinct.

## Verify revisions without restarting discovery

For a follow-up, provide the initial review baseline, previous reviewed revision,
current artifact, incremental diff, per-finding corrections, and test evidence.
Include untracked files or external artifacts when relevant. Keep the artifact
stable during review; changes after review require verification of that delta.

Focus subsequent review on agreed closure criteria, changed code and affected
callers/dependencies, and regressions introduced by the repair. Inspect unchanged
areas when a concrete dependency, previously uncovered area, or new evidence
justifies it, and state that reason. Do not repeat a broad discovery pass over
unchanged code by default. Still report material defects discovered late.

Classify each finding raised after discovery, with evidence for its origin:

| Classification | Meaning |
| --- | --- |
| Incomplete fix | The original invariant still fails; keep the original ID. |
| Introduced regression | The repair created a defect; identify the responsible delta. |
| Missed original defect | Present in the initial artifact; identify the baseline evidence and coverage gap. |
| Scope expansion | A new requirement or optional improvement; separate from in-scope blockers. |

If origin cannot be established, say so and obtain the missing comparison;
do not guess or silently label the defect a regression. Batch all discovered
cases before returning. Report a result for each agreed counterexample and
explicitly identify findings closed, still open, or reopened. A correction can
be implemented yet remain open pending verification. Reopen a closed finding
only with new evidence, not a repeated preference or already-settled objection.

## Break repeated partial repairs

After the same finding returns as incomplete in two repair reviews, stop
incremental patching and reassess the design agent-to-agent, even if each attempt
made some progress. Review the failure class and counterexample matrix together;
choose a coherent correction, a simpler design, or a justified refusal boundary
before further implementation. Preserve the finding ID and attempt history.

This is a design checkpoint, not a request for routine user approval or an
automatic end to the loop. If three substantive discussion rounds cannot settle
the same disagreement, report it as unresolved. If reassessment cannot produce
a viable in-scope repair, report the blocker instead of repeating unchanged work.
Never hide a serious missed defect to satisfy a round limit.

## Consensus and measurements

Keep one compact, updated consensus record in the conversation or an existing
task document; do not create a receipt file for every turn. Include:

- Artifact/baseline/revision, provider session and turn IDs, and review stage
  (discovery, reconciliation, or repair verification).
- Coverage and verification limits; each finding's ID, first-seen turn,
  disposition, later-finding classification, closure criteria, implementation
  and verification evidence, and count of unsuccessful repair reviews.
- Explicit open IDs, reopened IDs, closed IDs, and new IDs for this turn.
  Use empty lists explicitly; zero new findings does not mean zero open findings.
- At completion, discovery findings, later missed defects, introduced
  regressions, incomplete-fix returns, repair rounds, and provider calls.
  Count reconciliation calls separately from artifact review rounds.

The helper's registry stores per-turn disposition counts, not this finding
ledger. Keep counts on the turn that introduced each finding, update that turn
as implementation/verification changes, and avoid counting old findings again.
A zero-count registry turn is not a closure signal; use the explicit open IDs
and reviewer verdict in the consensus. Missing counts mean unrecorded, not zero.
