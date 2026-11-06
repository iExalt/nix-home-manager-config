---
name: slow-ci
description: "Diagnose and reduce slow CI, tests, checks, builds and release pipelines without losing required proof. Use when checks exceed their latency budget, grow against a baseline, or slow the local development loop."
---

# Slow CI

Find where elapsed time goes, remove unnecessary work, and prove the same checks
finish sooner. Load `iExalt:working-conventions` for latency targets and test-cost
rules. Read [references/recipe.md](references/recipe.md) for the measurement recipe
and lessons from past runtime repairs; choose the parts the evidence supports.

## Establish the delay

Identify the exact command or workflow, trigger, revision, required proofs and
budget. Measure the feedback the developer waits for: command start to usable
local result, or CI trigger to all required results/artifacts. Separate queueing,
setup, build, test, reporting and artifact work. The slowest dependency chain
controls elapsed time; summed job durations describe compute cost instead.

Inspect a recent slow run and a stable comparable baseline before changing code.
Record environment, tool versions, CPU/memory limits, concurrency, cache state,
input size and test selection. Keep cold and warm results separate. A faster
machine or warm cache alone does not prove a code speedup.

## Repair the cause

Start with a bounded profile or per-phase timings, including harness and fixture
setup. Inspect callers when the measured wait exceeds the test or build body's
own cost. Prefer fixes to polling, unintended serial work, repeated setup,
duplicate builds, oversized fixtures and algorithms before adding concurrency.

Keep each required invariant at the cheapest reliable layer. Consolidate redundant
coverage while retaining distinct failure modes. Moving proof out of the routine
gate, narrowing supported platforms or making a check optional changes acceptance
and needs approval. Never meet the target by hiding failures, raising timeouts,
adding retries, dropping assertions or resetting a baseline.

Only then consider bounded parallelism or sharding. Measure on the constrained CI
runner, account for shared locks and memory, and preserve isolation and cleanup.
Spending or changing shared runners still follows the user's authorization rules.

## Prove and retain the improvement

Re-run the failing or slow path first, then the full affected gate once. Compare
before/after on equivalent inputs and conditions; repeat cheap measurements when
variance could explain the gain. For a flake repair, also exercise the failure
conditions, including fewer cores where relevant. A single successful run does
not establish reliability.

Report the cause, change, before/after elapsed time and conditions, retained proofs,
remaining bottleneck and budget gap. Separate local results from actual CI and
release evidence. Do not launch a release to benchmark it without explicit release
approval. Keep a small reproducible timing command and stable baseline in the
repository's existing check docs/config; avoid adding a benchmark framework for
one repair. Report unmeasured stages plainly.
