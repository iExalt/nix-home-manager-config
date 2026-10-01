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

Ask the reviewer to include proposed closure criteria and a counterexample batch
with discovery findings that need complex repairs. Before implementation, the
main agent and reviewer must explicitly agree through the facilitator on:

- The invariant that must hold, not just the reported failing example.
- The supported behavior, explicit boundaries, and treatment of unsupported or
  uncertain inputs; refusal may be simpler than extending a partial model.
- A batch of counterexamples and expected outcomes covering the failure class.
- The bounded correction and evidence needed to close the finding.

A complex repair changes a parser, semantic model, safety boundary, or behavior
across several callers, or admits materially different designs. The facilitator
may propose criteria but cannot supply the reviewer's agreement. Record the
reviewer response that establishes agreement and the main agent's acceptance.
If discovery already specifies the bounded correction and sufficient criteria,
the main agent can accept those without another call. Otherwise batch the proposed
design, boundaries, and counterexamples into one pre-repair clarification in the
same reviewer session. Do not label unconfirmed proposals "agreed" or defer this
agreement until review of the implemented repair. Simple fixes need no extra call.

Counterexamples must exercise the invariant across related representations,
not just repeat the reported examples. For identifier transformations, for
example, distinguish identifiers from literal values even when both occur inside
one expression. Prefer a bounded implementation or refusal where uncertain
inputs cannot be handled safely. The main agent implements and verifies the whole agreed batch, including
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

## Running long provider turns

Before dispatch, distinguish the helper's `--timeout` (seconds) from the outer
execution tool's process timeout and its foreground wait/yield interval. Give the
outer process a supported lifetime longer than the helper deadline, with shutdown
margin. Background mode alone does not guarantee that an outer timeout stops
killing the process. Do not assume a requested timeout above the tool's maximum
will be honored. Use a supported persistent execution session when the required
lifetime exceeds the tool's foreground limit; retain its task/session handle.

Use that handle's native completion notification or interruptible wait/poll tool.
A wait returning while the process is still running is not a failed provider turn;
resume waiting on the same handle. Avoid shell sleep loops or parallel waiters
watching an output file. Do not start a duplicate review because output is quiet.

After an interruption, inspect process status, captured output, and the provider
session before retrying. If still running, continue waiting. If terminated, resume
the same provider session with the unchanged revision and ask it to finish the
remaining coverage using its retained evidence. Start over only when the session
or evidence is unusable. Count interrupted attempts separately from completed
review rounds; helper registry records may be absent when the outer tool kills it.

## Consensus and measurements

Keep one compact, updated consensus record in the conversation or an existing
task document; do not create a receipt file for every turn. Include:

- Artifact/baseline/revision, provider session and turn IDs, and review stage
  (discovery, reconciliation, or repair verification).
- Coverage and verification limits; each finding's ID, first-seen turn,
  disposition, later-finding classification, closure criteria and their reviewer agreement, implementation
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
