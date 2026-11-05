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
[Agentic Workflow Primer](../../../../../AGENTIC_WORKFLOW_PRIMER.md). The user chooses
outcomes and tradeoffs; the agent investigates technical options and owns routine
execution. Finish with a concise decision record and a concrete next step.
This skill's dialog rules add to `working-conventions` › Ask the user. Two of
them deliberately override the user's global rules to batch questions and
always recommend one: ask one consequential question at a time, and recommend
only when evidence supports it. Here earlier answers reshape later questions,
and an unsupported recommendation anchors the user.

The primer is written for humans; do not treat it as another instruction file.
In a Home Manager installation, resolve this `SKILL.md` through its symlinks
before following the relative link. Read the primer's main body for context and
its appendices only when useful. Without the primer, the workflow below stands
alone.

## Use the Q&A dialog

Ask every question through a native structured question tool, never in
commentary, a numbered chat questionnaire, or a request to reply in prose.
Commentary may explain the tradeoff; the question belongs in the dialog.

- Prefer `request_user_input_async` when available. Otherwise use
  `request_user_input` only when the current mode permits it, or an equivalent
  native dialog such as `AskUserQuestion` when the harness exposes it. Follow
  the live tool schema and its restrictions, including any limits on permission
  requests. Do not claim to switch modes or invent a tool call.
- Ask one consequential question at a time by default; bundle up to three
  closely related questions when their answers are independent. Offer two or
  three concrete choices with their consequences, recommending one only when
  evidence supports it. Use a free-text field when the desired outcome is not
  yet known, and follow the tool's handling of custom answers instead of adding
  an `Other` choice. When a free-text answer is itself a question, answer it in
  commentary, with evidence where you can, then re-ask only if the choice still
  stands, revised in light of your answer.
- Phrase choices by results, effort, fidelity, maintainability, and what gets
  postponed. Do not ask a nonexpert user to select an API or architecture whose
  consequences you have not explained.
- While asynchronous answers are pending, continue independent read-only
  discovery, and do no work that depends on a required answer. A preselected
  option, timeout, or silence is neither an answer nor authorization. If the
  user skips an optional question, keep known preferences or state a
  provisional assumption within existing scope; do not keep re-asking it.
- If no permitted dialog tool exists, explain that the interactive workflow
  needs a dialog-capable environment or mode. Provide a provisional brief from
  known facts with the unresolved choices marked. Do not fall back to a prose
  interview or claim those choices are settled.

## Guide the decisions

Keep a short visible checklist of the unresolved stages. Start from the user's
current position: a new idea, a proposed route, or an ongoing campaign. Reuse
explicit answers and inspect only enough context to make the next decision
concrete. Don't replay a full intake or impose research on a routine,
well-understood change.

### 1. Establish the first useful outcome

Draft the outcome and first observable deliverable in plain language. Separate
hard constraints, ranked preferences, and deferred work. Resolve conflicts
through the dialog, explaining what each choice postpones. Keep independent
requirements separate: choosing a framework, keeping data on a device, and
controlling iteration on that device are distinct decisions.

For example, ask whether the user prioritizes a working single-session player
with later ownership work, or session isolation before native delivery. Do not
assume that faster initial delivery always outranks framework quality or fidelity.

### 2. Identify the decision a spike would change

Inspect relevant source and evidence. Find the assumption most likely to make
the route costly or unnecessary, then propose the smallest representative probe
that could disprove it. Distinguish demonstrated prerequisites, chosen design
constraints, and untested assumptions.

Define the question, workload, initial effort allowance, reassessment point,
success/failure observations, and resulting route choices. Make setup, build,
execution, and analysis costs visible. Resolve material effort and priority
tradeoffs through the dialog; retain budgets already supplied by the user.

A request for guided planning permits preparation and read-only investigation;
it does not by itself authorize production changes or a long experiment. If a
bounded probe is already authorized, run it within that scope and the current
mode's permissions; otherwise return its concrete proposal as the next step. Ask
for authorization through a permitted dialog tool, not one that forbids
permission requests.

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
go to the backlog unless the user raises their priority. If an expensive or
ambiguous choice warrants independent review, scope that review to the route
decision and delegate it only when authorized. Do not require independent
review for every item.

### 4. Hand off autonomous execution

Return a compact decision record: outcome, first deliverable, constraints and
priorities, scope and authorization, main uncertainty, probe/evidence, route,
next item and acceptance check, and reconsideration triggers. Distinguish
proposed work from executed and verified results. Use the conversation or an
existing project document; create a new document only when requested or needed.

When implementation is requested, use `subagent-pair-program` if available and
appropriate, reading its current instructions at handoff; don't duplicate its
team hierarchy here. Preserve existing implementation authorization: do not add
a final confirmation just because this interview has ended. When the request is
planning only, finish with the next action and its boundary instead of silently
starting a campaign.

Ask for progress reported as capabilities and uncertainties as well as checklist
items: what the user can now run, observe, or decide, and what remains. Routine
technical proposals, reviews, tests, and repairs stay within the agent team.

### 5. Reassess when evidence changes

Agree on proportional route-level triggers: a falsified central assumption, an
unexpected subsystem on the critical path, materially increased remaining effort,
or repeated increments without the promised demonstration or new useful evidence.
Avoid mandatory recurring review meetings. Repeated repairs at one gate follow
`working-conventions` › Repeated failure instead.

For a campaign already underway, begin here: compare the best remaining routes,
including switching costs, and preserve useful completed work. Return product
tradeoffs to the user through the dialog when outcomes, priorities, constraints,
or substantial effort commitments change; resolve routine technical replanning
yourself within existing authorization. Never silently relax acceptance
criteria to end the campaign or treat sunk effort as a reason to continue it.
