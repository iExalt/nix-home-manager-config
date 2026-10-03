# <Campaign> script

<!--
Tier 3 of three-tiered-plan: the implementation threads to open, in order, until the plan's final gate. A page or
two. Delete these comments.
-->

**TL;DR:** <n> threads from here to <the final gate>. <The shape of the sequence in a line.>

It groups the [roadmap](<ROADMAP>.md)'s steps; the [plan](<PLAN>.md) says why, and the
[status document](<STATUS>.md) holds the evidence.

## How to use it

- Open the threads in order. Each is one `/keep-me-in-the-loop` invocation and one approval, which settles the
  thread's decisions, authority and live spending up front, so it can run to the end with its continuous reviewer.
- Open a thread once its **Before opening** conditions hold: start a fresh chat and paste its prompt.
- When a thread finishes, its agent marks it done here and records any deviation that changes later threads.
- <Concurrency: one working tree and one thread at a time, or the named parallel lanes below.>
- <Standing hazards that apply to every thread.>

## Where things stand

<Verified position on <date>: finished steps, live resources, sessions in flight.>

## Threads

### 1. <Outcome>: roadmap <steps> (<done, active, next, planned or provisional>)

- **Prompt:**

  ```text
  /keep-me-in-the-loop Run thread 1 of <SCRIPT path>: roadmap steps <steps>. Read the thread's entry for its
  preconditions, chunks and approval items. When the phase is complete, mark thread 1 done in the script and record
  any deviation that changes later threads.
  ```

- **Before opening:** <what must be true, and what the user must have ready: tokens, logins, presence at a time>.
- **Chunks (proposed):** <2–4 chunks; the loop reshapes them with its reviewer>.
- **Live:** <resources, spending and teardown>.
- **At approval:** <the decisions and authority to settle>.
- **Mid-run returns:** <the only expected ones, or none>.
- **Done when:** <the exit check, and the gate it passes, if any>.

## Why the cuts fall there

<!-- One bullet per boundary: decisions, resource lifetimes, dates, gates, waits filled, fresh-agent runs. -->

## Parallel lanes

<!-- Threads that can run beside the sequence, and how they are isolated (a sibling worktree, for example). -->

## Deferred

<!-- Steps outside the sequence, with the reason and the trigger that brings each back. -->

## Revision log

- <date>: <what changed, and why>.
