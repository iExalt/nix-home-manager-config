# <Campaign> roadmap

<!--
Tier 2 of three-tiered-plan: how agents get from here to the plan's gates. A fraction of the plan's length; detail
and rationale stay in the plan. Delete these comments.
-->

Status: **<progress in a line>, <date>.** The [plan](<PLAN>.md) says what the campaign delivers. This roadmap says how
agents get there: the steps, what each one needs, what proves it, which of the plan's boxes it ticks, and where a
person must act. The
[script](<SCRIPT>.md) groups the steps into threads, and the [status document](<STATUS>.md) tracks the evidence. It
starts from <the starting point>.

## How to read it

- A **step** is one unit of agent work: a few commits, ending with its proof. Steps are listed in a workable order,
  but only **Needs** constrains it.
- **Needs** names the steps, gates or decisions a step depends on, or "nothing". Steps that don't need each other can
  run in parallel.
- **Proof** is what must pass before the step is ticked. "Offline" needs no live resources. A live proof names its
  resources and leaves a record under `<records path>`.
- **Ticks** lists the plan's boxes, by phase and opening words (P2 "Make…"), and the plan items the step closes.
- **Human** says what a person must do for the step, and when. A step without one runs with nobody at the keyboard
  once its thread is approved. [Human interventions](#human-interventions) lists them all.
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
  - Needs: <steps, gates or decisions, or nothing>.
  - Proof: <the check, offline or live>.
  - Ticks: P1 "<opening words>…". Closes §5.1 item 2.
  - Human: <kind>: <what the user does>, <when: before the step, at its thread's approval, or at a named point
    mid-step, and whether the step waits or continues around it>.

## Side tracks

<!-- Spikes and optional work that run beside the phases, each with its Needs and what it decides. -->

## Human interventions

<!--
Every point where a person must act. Kinds: decision; access, such as a token or client only the user can create;
presence, such as a browser login or being online at a time; manual action; and approval of spending, destructive or
external operations. Shrink the list before implementation by settling decisions, provisioning access ahead of time
and moving mid-step interventions to approval.
-->

| Step | Kind | What the user does | When | Status |
| --- | --- | --- | --- | --- |
| 1.3 | Decision | <decision> | At approval | **Decided (the user, <date>):** <answer> |
| 2.2 | Presence | <browser login> | Mid-step, before <point>; the step waits | Planned |
