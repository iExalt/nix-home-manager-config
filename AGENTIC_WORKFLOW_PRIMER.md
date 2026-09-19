# Agentic Workflow Primer

*A short guide to getting useful results from autonomous coding agents.*

You can delegate the typing, debugging, testing, and routine technical decisions.
Your most valuable contribution is choosing what matters: the outcome, the
tradeoffs, and when a different direction would be more useful. The agent should
explain those choices in terms you can assess without knowing the implementation.

Use this workflow when starting an uncertain project, expanding its scope, or
reconsidering a long campaign. A familiar, small fix usually needs only a clear
outcome and an appropriate check.

## 1. Decide what you want to get first

Describe something you could run, observe, or decide. “A native player can load
one movie and produce a frame” is easier to evaluate than “complete the native
architecture.” Both may be worthwhile, but they imply different first steps.

Ask the agent to separate **hard constraints**, **ranked preferences**, and
**later work**. For example, keeping a particular framework might be mandatory;
supporting every operation immediately might be negotiable. If several outcomes
compete, ask what each choice postpones. You choose the priorities; the agent
investigates the technical consequences.

## 2. Buy evidence before committing to a route

A **spike** is a small experiment that helps you make a decision. Ask: “What is
the cheapest experiment that could show this approach is unsuitable—or this
prerequisite unnecessary?” Let the agent inspect the real code and try the risky
part in an isolated, reversible form.

Agree on the question, a representative workload, an initial effort allowance,
and when to reassess. The result may be a working probe, a disproved assumption,
or a concrete explanation of why the experiment is more expensive than expected.
An unanswered question stays unanswered; it does not authorize an expanding
implementation campaign. A successful prototype still needs production validation.

## 3. Choose the route, then detail the next increment

Ask for a recommendation and the strongest credible alternative, with evidence,
remaining uncertainty, and the cost of reaching the first useful result. Estimates
should expose uncertainty and include builds, setup, execution, and analysis.

Keep the distant roadmap coarse. The next implementation item should name its
behavior, dependencies, acceptance check, and conditions for reconsideration.
Ask which dependencies are demonstrated necessities, chosen design constraints,
or assumptions. “We eventually want this” does not establish that it must happen
first. A fresh reviewer can help with an expensive or ambiguous route decision.

## 4. Let the team execute within that boundary

Once the outcome and boundaries are clear, let the agents handle proposals,
implementation, review, testing, and ordinary repairs. The
[subagent-pair-program skill](dotfiles/skills/subagent-pair-program/SKILL.md)
provides that execution loop. You do not need to approve every edit or attend
every code walkthrough.

Ask for progress in terms of new capabilities and resolved uncertainties:
“What can we now do or know? What remains between that and the goal?” A short
checklist plus the latest runnable demonstration or decisive experiment is more
useful to you than a stream of test counts. Infrastructure work should explain
which outcome it enables, without claiming that outcome is already delivered.

## 5. Reconsider when the evidence changes

Revisit the route when a key assumption fails, a new subsystem becomes a
prerequisite, effort grows materially, or repeated increments produce neither
the promised demonstration nor useful new evidence. Agree on those triggers
early; they are opportunities to decide, not instructions to abandon work.

Ask: “Given what we know now, what is the best remaining route, including the
cost of switching?” Preserve useful work. Keep correctness requirements explicit;
changing the route is not permission to weaken them. You need to participate
when the outcome, priorities, constraints, or substantial effort commitment
changes. Routine technical replanning can remain autonomous.

## Use it in a conversation

Invoke the [agentic-workflow skill](dotfiles/skills/agentic-workflow/SKILL.md):

> Use $agentic-workflow to help me plan this project. Guide me through the
> decisions using the Q&A dialog. I want to delegate implementation, but choose
> the outcome and tradeoffs myself.

The skill uses short dialog rounds and carries forward what you have already
said. You can start with an uncertain idea or use it to reassess work in progress.
If the dialog is unavailable in the current environment, the agent will explain
that limitation instead of substituting a chat questionnaire. The repository
registers the skill for provisioning through the usual Home Manager activation.

Keep one question handy throughout:

> What is the next thing I will be able to run, observe, or decide—and what
> evidence says this work is necessary to get there?

---

## Appendix A: What the two campaigns taught us

### TerminalO3 and Burn Metal

“Use Burn” and “keep planning entirely on the GPU” describe separate requirements.
Rejecting custom model kernels did not imply accepting CPU-controlled planning.
A useful brief would preserve framework choice, data residency, and loop control
independently, then ask the agent to investigate routes satisfying all three.

The Metal investigation also grew through explicitly requested additions. A
reusable backend, broad operation coverage, and several optimization families
can be worthwhile goals themselves. The decision to surface is whether that
framework programme now takes priority over the first result that unblocks the
application. An increasing estimate helps, but so does saying what gets delayed.

### childhood-redux and DirPlayer

The initial native-player proposal included an early vertical slice. Adding
global-state removal led to a substantial session-ownership programme before
native delivery. That work was authorized and produced real engineering value;
its place on the critical path needed stronger justification.

A disposable single-session native probe could investigate which changes native
execution actually requires. It would not establish multi-session correctness
or eliminate that eventual requirement. The lesson is to separate evidence
needed to choose a route from evidence needed to accept the finished product.

## Appendix B: Prompts for common situations

### Starting an uncertain project

> Help me define the first useful result, hard constraints, ranked preferences,
> and deferred work. Explain the meaningful tradeoffs through the Q&A dialog.
> Investigate the most consequential uncertainty before drafting a detailed
> implementation plan. Recommend a bounded spike and show what decision its
> result would change.

### Adding an interesting idea

> Explore this as an option. Explain whether it helps the first deliverable,
> changes the critical path, or creates a separate project. Put optional ideas
> in the backlog until we decide their priority.

### Starting autonomous implementation

> Use the agreed brief and evidence to implement the next bounded outcome with
> subagent-pair-program. Keep routine coding, review, testing, and repairs within
> the agent team. Reassess when an assumption fails or the remaining work changes
> materially. Bring me product tradeoffs when my priorities or constraints need
> to change.

### Reconsidering a campaign

> Audit our route from the current state. Separate necessary dependencies from
> design choices and untested assumptions. Recommend the cheapest next
> experiment that could change the plan. Account for switching costs, preserve
> completed work, and retain required correctness guarantees.

## Appendix C: A compact decision record

Ask the agent to maintain this in the conversation or an existing project
document. It need not become another large plan, and you need not fill it out
yourself.

| Field | What you should be able to understand |
| --- | --- |
| Outcome and first deliverable | What you want and what becomes useful first. |
| Constraints and priorities | What cannot change, and how to choose between reasonable routes. |
| Scope boundary | What is included now, deferred, and explicitly authorized. |
| Key uncertainty | The assumption that could make the route unsuitable. |
| Experiment | The question, workload, effort allowance, and reassessment point. |
| Evidence | What ran, what it showed, and what remains unproven. |
| Route decision | The recommendation, alternative, and reason for choosing. |
| Next increment | The behavior to deliver and its acceptance check. |
| Reconsideration trigger | The evidence or effort change that warrants another decision. |

For exploratory work, “we identified the missing capability” can be a successful
result. For product delivery, it is an outstanding dependency. Keep those meanings
separate so a useful investigation does not become a premature completion claim.

## Appendix D: Keep the process economical

Use extra reasoning effort or an independent reviewer where a decision could
redirect substantial work. More reasoning does not resolve an incorrectly stated
goal, and more agents do not automatically reduce cost. Compare elapsed time and
total agent usage per accepted useful outcome, including review and rework.

Reuse decisions and valid verification evidence. Apply only the parts of this
workflow that remain uncertain. A longer plan, a second reviewer, or a new
document should earn its place by improving a decision.
