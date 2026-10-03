# <Campaign> script

<!--
Tier 3 of three-tiered-plan: the implementation threads to open until the plan's final gate, what orders them, and
when a human is needed. A page or two. Delete these comments.
-->

**TL;DR:** <n> threads from here to <the final gate>. <The critical path, and what runs alongside it.>

This script groups the [roadmap](<ROADMAP>.md)'s steps; the [plan](<PLAN>.md) says why, and the
[status document](<STATUS>.md) holds the evidence.

## How to use it

- Each thread is one `/keep-me-in-the-loop` invocation and one approval, which settles the thread's decisions,
  authority and live spending up front, so it can run to the end with its continuous reviewer. Its chunks run in
  order.
- **Threads run in parallel unless their Depends on entry says otherwise.** Open any thread whose dependencies are
  met: start a fresh chat and paste its prompt, or have `/overseer` run the ready threads as separate sessions.
- A thread running beside another works in its own worktree (`/overseer` uses a sibling
  `../<repo>-worker-<slug>/`), rebases before every push, and reconciles shared documents (roadmap ticks, status, this
  script) without overwriting another thread's entries.
- **Human** lists every planned intervention. "None after approval" means the thread runs with nobody at the keyboard
  once it is approved.
- When a thread finishes, its agent marks it done here, records any deviation that changes other threads, and marks
  the threads it unblocks ready.
- <Standing hazards that apply to every thread.>

## Where things stand

<Verified position on <date>: finished steps, live resources, sessions in flight.>

## Order

```text
1 ──> 3 ──> 5      critical path
2 ──┘              2 runs beside 1
4                  independent, but not alongside 3: both use <resource>
```

## When a human is needed

<!-- Every Human entry with a date, a time or a mid-run point, in time order, so the user can plan around them. -->

- <Date, or thread and point>: <what the user does> (thread <n>).

## Threads

### 1. <Outcome>: roadmap <steps> (<done, active, ready, waiting on <dependency>, or provisional>)

- **Prompt:**

  ```text
  /keep-me-in-the-loop Run thread 1 of <SCRIPT path>: roadmap steps <steps>. Read the script's "How to use it" and
  the thread's entry for its dependencies, human interventions, chunks and approval items. When the phase is complete,
  mark thread 1 done in the script and record any deviation that changes other threads.
  ```

- **Depends on:** <none: runs in parallel with any thread | after thread <n>, which <provides what this needs> | not
  alongside thread <n>, since both <use what> | not before <date or event>>.
- **Human:**
  - Before opening: <what the user must have ready, such as a token, a login or presence at a time>.
  - At approval: <the decisions and authority the approval settles>.
  - Mid-run: <none, or the point, what the user does, and whether the thread pauses affected work or continues>.
  - After: <none, or the check or action, such as a post-run confirmation>.
  - <When nothing is needed mid-run or after, replace those two lines with "None after approval.">.
- **Chunks (proposed):** <2–4 chunks; the loop reshapes them with its reviewer>.
- **Live:** <resources, spending and teardown>.
- **Done when:** <the exit check, and the gate it passes, if any>.

## Why the cuts fall there

<!-- One bullet per boundary or dependency: decisions, resource lifetimes, dates, gates, waits filled, fresh-agent
runs. -->

## Deferred

<!-- Steps outside the threads, with the reason and the trigger that brings each back. -->

## Revision log

- <date>: <what changed, and why>.
