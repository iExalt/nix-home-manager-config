# Runtime repair recipe

## Capture a useful baseline

1. Write down the developer's wait, its target, and what must still be proved.
   Follow the workflow dependency chain through queueing and artifact delivery.
2. Reuse existing timing logs or CI step timestamps. If insufficient, add temporary
   monotonic timers around setup, execution and teardown. Bound the investigation
   by a deadline and retain its exit code; do not start overlapping benchmarks.
3. Reproduce on the same revision and workload under comparable CPU/memory limits.
   Record cold setup and warm iteration separately. Start with one run; repeat
   cheap runs to report median and spread when variation matters. Keep runner
   contention and cache restore/save overhead visible.
4. Rank elapsed costs and inspect the largest one first. Distinguish slow work
   from waiting for a lock, worker, child process, readiness or stale artifact.

## Choose a repair

| Evidence | Inspect or change | Proof to retain |
| --- | --- | --- |
| Fixed gaps with little CPU work | Readiness polling, nested timeouts, sleep-based helpers | Failure and timeout propagation; actual readiness condition |
| Setup costs more than assertions | Fixture size, server launches, compilation per case | Isolation and every distinct invariant |
| Same work appears in several stages | Build ownership, artifact reuse, repeated discovery | Artifacts match source, toolchain and configuration |
| Warm is fast, clean runner is slow | Dependency installation, cache keys and paths | Cold miss correctness and safe invalidation |
| One test drives most elapsed time | Harness callers, input scaling, algorithm | Same workload semantics and failure modes |
| More workers make it slower or flaky | CPU/memory pressure, shared locks/state | Fewer-core stability, unique resources, cleanup |
| Jobs are fast but feedback is late | Queueing and dependency chain | All required gates finish; compute cost reported separately |

Change the smallest causal component. Measure it before stacking optimizations.
Exhaust practical correctness, algorithm and structural fixes before parallelizing.
Avoid moving setup outside a timer and calling that a speedup: retain total latency.

Before declaring an environment or artifact reusable, check that tests behave
the same when run as the intended user or account and in the environment they
will run in, that binaries and helpers don't depend on where they were built, and
that shared fixtures keep the properties tests rely on. Have the whole plan
reviewed against the original objective before turning it into execution
threads.

## Close the loop

Record: revision; command/trigger; proof set; environment and resource limits;
cache/input state; before and after total time; phase breakdown; repetitions and
spread; budget result; CI evidence or the explicit remaining verification gap.
Compare against the original baseline across increments. A newly faster baseline
must not erase cumulative regression history.

## Lessons checked against past sessions

These are anonymized historical measurements, not current benchmarks or expected
speedups. Exact source pointers stay in the user's private evidence file at
`~/.config/slow-ci/evidence.md` when available; read it only to audit provenance.
It is optional for using this recipe. Do not copy transcript identifiers, private
repository names or machine details into a public change.

- **Application algorithms can dominate test time.** A local evidence gate fell
  from 65 seconds to two measured runs of 42.273 and 42.152 seconds after exact
  integer distance calculations and packed colour counting replaced repeated
  work. Import outputs remained byte-identical. Load differed slightly, and live
  text recognition still produced outliers. Profile application work before
  assuming the test runner is the bottleneck; bound vectorization memory too.
- **Fixture startup compounds across a suite.** Disabling unused plugins in a
  test daemon reduced startup from 1.36 to 0.54 seconds and a 110-test aggregate
  from 202 to 102 seconds. Refreshing stale shard weights alongside that repair
  took the hosted critical path from a typical 275 to 285 seconds to 234 seconds
  with a dependency-cache hit. Two pre-existing local hangs were excluded from
  both comparisons; the local result was not a clean full-suite pass.
- **Test timeout behavior without waiting through production deadlines.** Seven
  tests gained injectable timeout settings while keeping production defaults and
  cleanup assertions. One fell from 15.2 to 1.2 seconds; shutdown cases fell from
  about 10 seconds to under one. A separate boundary test was left intact because
  trimming it would leave only a 3% margin. Short test deadlines or a controlled
  clock must still exercise the real failure and cleanup contract.
- **Inspect browser harness return values.** Returning an entire graph from a
  zoom evaluation added serialization cost. On four cores, removing that return
  reduced a browser gate from 131 to 112 seconds; optimizing native dependencies
  reduced it to 92; four shards then reached 57. Final hosted runs took 60 to 78
  seconds with the original 120-second limit. Dependency optimization added about
  60 seconds to cold builds. The measured ladder supports fixing the harness
  first and accounting for cold-build cost separately.
- **Do not compile tooling on every cold runner.** Installing a pinned prebuilt
  test-runner release replaced a source-based tool install. The CI setup step
  fell from about four minutes on a cache miss to 13 seconds. The runner version
  stayed pinned; simultaneous test changes do not explain the setup-step delta.
  Check available release assets and integrity verification before introducing a
  tool cache or increasing runner size.
- **Cold build cost is different from warm test cost.** Switching a Rust dev
  profile to line-table debug information retained file/line backtraces and cut
  cold compilation CPU from 959 to 971 seconds to 757 to 761 seconds; output size
  fell from 22 to 9.7 GB. Alternating runs had variable host load, making CPU time
  stronger evidence than wall time. Warm suite runtime was essentially unchanged.
  Check debugger requirements before adopting that profile.
- **Parallelism trades compute for latency.** Sixteen independent lanes reduced
  one full check set from 40 minutes 53 seconds to 8 minutes 56 seconds cold, but
  total runner work grew from 41 to 75 minutes through repeated setup/builds.
  The aggregate gate rejected failures, cancellations and skipped lanes. A later
  faster routine gate used a narrower proof selection; it is not an equal-work
  comparison. Preserve the full proof set unless a gate change is authorized.
- **Release caches can help without meeting the budget.** Across two releases,
  dependency installation fell from 1,343 to 161 seconds and a Gradle build from
  21.5 to 10.5 minutes with 505 tasks restored. The full release fell from 53.7 to
  36.3 minutes, still above the target. These were different releases and cache
  states, not a controlled comparison; the next bottleneck was a 29-minute build.
  Measure the entire release chain and verify cache trust and invalidation.

Rejected or limited evidence also changes the decision:

- An install cache saved about 6 to 10 seconds but added an 8-second restore;
  the experiment did not establish a net gain, so the cache was removed.
- A local worker sweep found four workers faster and cheaper than six or eight
  under high load. Quiet-host confirmation remained outstanding. Tune worker
  counts under representative constraints and keep cache-sharing groups together.
- A release later reached 18.9 minutes after platforms and verification machinery
  were removed. That was a scope/security change, not a same-proof speedup.
  Never reproduce it without approval of the changed acceptance criteria.
- Reverted optimizations and proposed speedups were excluded from the positive
  examples. A passing run or a merged intermediate patch alone does not establish
  a retained fix.
