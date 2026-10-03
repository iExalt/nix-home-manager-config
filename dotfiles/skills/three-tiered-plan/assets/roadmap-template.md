# <Campaign> roadmap

<!--
Tier 2 of three-tiered-plan: how agents get from here to the plan's gates. A fraction of the plan's length; detail
and rationale stay in the plan. Delete these comments.
-->

Status: **<progress in a line>, <date>.** The [plan](<PLAN>.md) says what the campaign delivers. This roadmap says how
agents get there: the steps in order, what proves each one, and which of the plan's boxes each one ticks. The
[script](<SCRIPT>.md) groups the steps into threads, and the [status document](<STATUS>.md) tracks the evidence. It
starts from <the starting point>.

## How to read it

- A **step** is one unit of agent work: a few commits, ending with its proof. Steps run in order within a phase.
- **Proof** is what must pass before the step is ticked. "Offline" needs no live resources. A live proof names its
  resources and leaves a record under `<records path>`.
- **Ticks** lists the plan's boxes, by phase and opening words (P2 "Make…"), and the plan items the step closes.
- When a step finishes, the agent ticks it here and the plan's boxes in the same commit, citing the record or commits.
- A step marked *provisional* depends on earlier evidence; refine it when that evidence arrives.

## Progress

| Phase | Steps | Done | Exit (the plan's gate) |
| --- | --- | --- | --- |
| 1. <Name> | <n> | 0 | <gate> |

```text
Phase 1 ─> Phase 2 ─> Phase 3
<offline>  <one live run>  <...>
```

Live runs are where the time and money go:

| Run | Steps | Resources | Lasts, and what it costs |
| --- | --- | --- | --- |

## Summary

- **Phase 1: <name>** (<offline or live>)
  - <What happens> (1.1, 1.2).
  - **Gate:** <the check> (1.3).

## Phase 1: <name>

- [ ] **1.1 <Title>.** <What changes, including ordering hazards.>
  - Proof: <the check, offline or live>.
  - Ticks: P1 "<opening words>…". Closes §5.1 item 2.

## Side tracks

<!-- Spikes and optional work that run beside the phases, each with its earliest start and what it decides. -->

## Decisions agents will stop for

| Before | Decision |
| --- | --- |
| 1.3 | <decision>. **Decided (the user, <date>):** <answer> |
