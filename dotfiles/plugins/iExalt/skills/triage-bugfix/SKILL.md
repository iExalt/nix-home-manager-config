---
name: triage-bugfix
description: Diagnose reported software or operational failures, develop and verify a scoped fix, and recommend measures to prevent recurrence. Use for bug investigations and root-cause-driven repairs.
---

# Triage and bugfix

Guide the work from symptom to mechanism, remedy, and recurrence prevention, scaled to impact and uncertainty.

## Establish the problem and scope

Identify observed and expected behavior, impact, the affected environment or version, and concrete success criteria. Reuse available context before asking questions. Determine whether the request authorizes diagnosis, a proposed fix, or implementation.

## Diagnose the mechanism

Collect evidence and reproduce when practical, preferring checks that distinguish competing explanations. Separate defects from configuration, environmental or dependency failures, and intended lifecycle behavior. Preserve diagnostic artifacts when that avoids repeated expensive collection. For a flaky or failing UI test, or a UI fix that needs an automated test, also follow `iExalt:frontend-testing`.

Trace the exact failing operation and the causal chain behind the symptom. Distinguish observations, supported conclusions, hypotheses, and missing links. Check related failures or prior incidents when they could change the diagnosis or remedy. If the cause remains uncertain, name the next discriminating check instead of claiming certainty. Call a mitigation a mitigation when it does not establish or remove the cause.

## Develop the fix

Tie each proposed change to the failure mechanism. Preserve intended behavior, correctness guarantees, and relevant performance bounds; explain material tradeoffs. Distinguish immediate recovery from durable correction.

For diagnosis-only requests, report findings and draft remediation. When implementation is authorized, make and verify the scoped change without adding a blanket approval gate. Respect explicit stopping points and existing authorization boundaries for deployment, destructive actions, and other external mutations. Bound retries by the operation and its risk, and surface terminal failure.

## Verify the outcome

Exercise the original failure and relevant neighboring cases at the cheapest reliable layer. Where practical, show that the check fails on the original defect and passes with the fix. Use realistic workloads where scale matters, and verify that failed or incomplete execution cannot pass as success. Do not weaken checks or suppress errors to get a green result.

Separate local verification, CI results, deployment, and live-system proof. State what remains unverified and what evidence would close the gap. Label each claim read, ran, or inferred, and cite the command and result for each check you report as run.

## Prevent recurrence

Name the failure class and explain why existing safeguards missed it, distinguishing evidence from inference. Recommend measures tied to that mechanism: an enforced invariant, reliable failure propagation, targeted regression coverage, better diagnostics, or a justified workflow change.

Explain the expected benefit and ongoing cost. Separate prevention included in the authorized fix from proposed follow-up work, and don't grow it into an unrelated hardening project.

Close with the diagnosis and evidence, fix status, what remains unverified, and prevention recommendations.
