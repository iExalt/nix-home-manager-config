---
name: triage-bugfix
description: Diagnose reported software or operational failures, develop and verify a scoped fix, and recommend measures to prevent recurrence. Use for bug investigations and root-cause-driven repairs.
---

# Triage and bugfix

Guide the work from symptom to mechanism, remedy, and recurrence prevention. Scale the investigation to impact and uncertainty; a small bug does not need an incident ceremony. Routine feature work and mechanical repairs need this workflow only when they involve a failure investigation.

## Establish the problem and scope

Identify observed and expected behavior, impact, the affected environment or version, and concrete success criteria. Reuse available context before asking questions. Determine whether the request authorizes diagnosis, a proposed fix, or implementation; carry forward existing authorization and explicit pause or wait points.

## Diagnose the mechanism

Collect evidence and reproduce when practical, preferring checks that distinguish competing explanations. Separate defects from configuration, environmental or dependency failures, and intended lifecycle behavior. Preserve diagnostic artifacts when that avoids repeated expensive collection.

Trace the exact failing operation and the causal chain behind the symptom. Distinguish observations, supported conclusions, hypotheses, and missing links. Check related failures or prior incidents when they could change the diagnosis or remedy. If the cause remains uncertain, name the next discriminating check instead of claiming certainty. Call a mitigation a mitigation when it does not establish or remove the cause.

## Develop the fix

Tie each proposed change to the failure mechanism. Preserve intended behavior, correctness guarantees, and relevant performance bounds; explain material tradeoffs. Distinguish immediate recovery from durable correction.

For diagnosis-only requests, report findings and draft remediation. When implementation is authorized, make and verify the scoped change without adding a blanket approval gate. Respect explicit stopping points and existing authorization boundaries for deployment, destructive actions, and other external mutations. Bound retries by the operation and its risk, and surface terminal failure.

## Verify the outcome

Exercise the original failure and relevant neighboring cases at the cheapest reliable layer. Where practical, show that the check fails on the original defect and passes with the fix. Use realistic workloads where scale matters, and verify that failed or incomplete execution cannot pass as success. Do not weaken checks or suppress errors to get a green result.

Separate local verification, CI results, deployment, and live-system proof. State what remains unverified and what evidence would close the gap. Label each claim read, ran, or inferred, and cite the command and result for each check you report as run.

## Prevent recurrence

Name the failure class and explain why existing safeguards missed it, distinguishing evidence from inference. Recommend measures tied to that mechanism: an enforced invariant, reliable failure propagation, targeted regression coverage, better diagnostics, or a justified workflow change.

Explain the expected benefit and ongoing cost. Prefer distinct safeguards at the cheapest reliable layer, accounting for cumulative test runtime and maintenance. Do not require a new test for every incident or expand prevention into an unrelated hardening project. Separate prevention included in the authorized fix from proposed follow-up work.

Close with the diagnosis and evidence, fix status, verification and remaining uncertainty, and proportionate prevention recommendations, in the structure the task needs rather than a fixed report template.
