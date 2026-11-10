---
name: agentic-workflow
description: "Guide a human through outcome choices, evidence-producing spikes, and bounded implementation planning using structured Q&A dialogs. Use when starting an uncertain agentic project or reassessing a campaign; not for routine implementation of an already settled task."
---

# Agentic Workflow

**Load `iExalt:working-conventions` before any other step.** It holds the
rules shared across the workflow skills, and this skill cites its sections as
`working-conventions` › Section without restating them. Invoke it as a skill,
or read its `SKILL.md` where your harness lists the path.

Facilitate the human decisions in the
[Agentic Workflow Primer](../../../../../AGENTIC_WORKFLOW_PRIMER.md).
This skill's dialog rules add to `working-conventions` › Ask the user. Two of
them deliberately override the user's global rules, which say to batch
questions and always recommend an option: ask one consequential question at a
time, and recommend only when evidence supports it. Here earlier answers
reshape later questions, and an unsupported recommendation anchors the user.

The primer restates this workflow for humans; don't load it. Point the user to
it when they want the background.

## Use the Q&A dialog

Ask every question through a native structured question tool. Commentary may
explain the tradeoff; the question belongs in the dialog.

- Use the synchronous `request_user_input` only when the current mode permits
  it. Follow the live tool schema and its restrictions, including any limits
  on permission requests. Don't claim to switch modes or invent a tool call.
- Ask one consequential question at a time by default; bundle up to three
  closely related questions when their answers are independent. Offer two or
  three concrete choices with their consequences, recommending one only when
  evidence supports it. Use a free-text field when the desired outcome is not
  yet known, and follow the tool's handling of custom answers instead of adding
  an `Other` choice. When a free-text answer is itself a question, answer it in
  commentary, with evidence where you can, then re-ask only if the choice still
  stands, revised in light of your answer.
- If the user skips an optional question, keep known preferences or state a
  provisional assumption within existing scope; don't re-ask it.
- If no permitted dialog tool exists, say the workflow needs one and give a
  provisional brief with the unresolved choices marked, not a prose interview.

## Guide the decisions

When several stages remain unresolved, keep a short visible checklist of them;
for a single remaining choice, state that choice instead. Start from the user's
current position: a new idea, a proposed route, or an ongoing campaign. Reuse
explicit answers and inspect only enough context to make the next decision
concrete. Don't replay a full intake or impose research on a routine,
well-understood change.

### 1. Establish the first useful outcome

Draft the outcome and first observable deliverable in plain language. Separate
hard constraints, ranked preferences, and deferred work. Resolve conflicts
through the dialog, explaining what each choice postpones. Keep independent
requirements as separate decisions.

Don't assume that faster initial delivery always outranks framework quality or
fidelity.

### 2. Identify the decision a spike would change

Inspect relevant source and evidence. Find the assumption most likely to make
the route costly or unnecessary, then propose the smallest representative probe
that could disprove it. Distinguish demonstrated prerequisites, chosen design
constraints, and untested assumptions.

State in one sentence the claim the probe can establish, at which layer or kind
of evidence, and its comparison criterion; treat approaches the user already
rejected as constraints. Define the question, workload, initial effort
allowance, reassessment point, success/failure observations, and resulting route
choices. Make setup, build, execution, and analysis costs visible. Resolve
material effort and priority tradeoffs through the dialog; retain budgets
already supplied by the user.

A request for guided planning permits preparation and read-only investigation;
it does not by itself authorize production changes or a long experiment. If a
bounded probe is already authorized, run it within that scope and the current
mode's permissions; otherwise return its concrete proposal as the next step.

A falsified assumption or an identified missing capability is a valid discovery
result. Record what ran and what remains unproven. A toy or stubbed probe must
disclose the production conditions it bypasses. Do not expand the spike into a
reusable subsystem to make it pass, or use it in place of required final
correctness or statistical validation.

### 3. Choose a route and bound the next item

Present the recommended route and the strongest credible alternative, grounded
in evidence and the user's priorities. Show uncertainty and the cost to the
first useful result. If evidence is missing, make the next item discovery
instead of presenting a speculative implementation plan as settled.

Keep later milestones coarse. Specify the next item's behavior, dependencies,
acceptance check, exclusions, and conditions for reconsideration. Optional ideas
go to the backlog unless the user raises their priority.

### 4. Hand off autonomous execution

Return a compact decision record: outcome, first deliverable, constraints and
priorities, scope and authorization, main uncertainty, probe/evidence, route,
next item and acceptance check, and reconsideration triggers. Keep it in the
conversation or an existing project document.

When implementation is requested, route it by size as `assign` does:
`continuous-peer-review` for a small one-shot task, `subagent-pair-program` for
medium work, and `keep-me-in-the-loop` for large, multi-phase work. Preserve
existing implementation authorization: do not add a final confirmation just
because this interview has ended. When the request is planning only, finish
with the next action and its boundary instead of silently starting a campaign.

### 5. Reassess when evidence changes

Agree on proportional route-level triggers: a falsified central assumption, an
unexpected subsystem on the critical path, materially increased remaining effort,
or repeated increments without the promised demonstration or new useful evidence.
Repeated repairs at one gate follow `working-conventions` › Repeated failure
instead.

For a campaign already underway, begin here: compare the best remaining routes,
including switching costs, and preserve useful completed work.
