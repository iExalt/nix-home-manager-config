---
name: three-tiered-plan
description: "Grill the user about a campaign spanning days or weeks, then write and maintain, with a continuous reviewer, a history-grounded plan, a roadmap of steps with proofs, and a script of threads, each a keep-me-in-the-loop run or an overseer worker (or tracker workstreams) with dependencies and human interventions. Use to start, re-plan, revise or close such a campaign; not for work one session can hold (agentic-workflow) or for running a thread (keep-me-in-the-loop)."
---

# Three-Tiered Plan

**Load `iExalt:working-conventions` before any other step.** It holds the
rules shared across the workflow skills, and this skill cites its sections as
`working-conventions` › Section without restating them. Invoke it as a skill,
or read its `SKILL.md` where your harness lists the path.

Shape a campaign that will steer days or weeks of agent work into three
documents, each more concise and more literal than the last:

| Tier | Answers | Shape |
| --- | --- | --- |
| **Plan** | What and why: north star, scope, exclusions, decisions, history, milestones and gates | Verbose; history and rationale are the point |
| **Roadmap** | How: steps, what each needs, what proves it, which plan boxes it ticks, where a human acts | A fraction of the plan |
| **Script** | Which implementation threads to open, with what prompt, after what, and when a human is needed | A page or two; literal |

Tier 3 can instead live in the repository's issue tracker as **workstreams**,
one issue per thread ("Keep tier 3 as tracker workstreams").

If the project already keeps plans and status in a canonical tracker, preserve
that home as `working-conventions` › Records describes. Apply the three tiers'
content and approval gates to its existing records instead of creating parallel
documents. For Acyclic, use the shared queue reference linked from Records.

Grill each tier out of the user and write it with a continuous reviewer, in
order, then ask the user to confirm the complete set in one dialog.

## Start from the right tier

Read the repository's instructions and documentation conventions, any existing
plan, roadmap, status document and script or workstream issues, and the Git
state. Start at the first tier that is missing or invalidated:

- no plan: the plan;
- a plan without a roadmap: the roadmap;
- a roadmap without a script or workstreams: tier 3;
- all three: the highest tier that new evidence affects (see "Revise when
  evidence changes");
- all three, and the user has confirmed the final gate or closed the campaign:
  "Close a finished campaign".

Keep a visible checklist of the tiers and each one's state: grounding, grilling,
drafted, reviewer-accepted, confirmed, published.

If grounding shows the work fits a session or two, or holds no consequential
uncertainty, say so and ask how to proceed. `agentic-workflow` or direct
execution may serve better than three documents.

## Plan with a continuous reviewer

Use `continuous-peer-review` throughout, reading its current instructions from
the skill catalog or sibling skill directories. Start its reviewer when
grounding begins and reuse it across all three tiers while the harness supports
it. If the harness can't provide a native reviewer, explain the limitation and
settle the approach with the user before claiming the workflow can proceed.
Treat each tier as a milestone whose increments are the grounding summary, the
grilling rounds and the drafted sections, and leave review mechanics to that
skill.

Brief the reviewer with the north star as far as it is known, the tier
boundaries, raw source locations, the user's answers verbatim and these
instructions. The reviewer reads the sources independently and challenges you,
but never answers the user's decisions or addresses the user; take decisions
its findings raise to the user through the dialog.

- **Grounding:** check your summary against the sources.
- **Rounds:** send each round's questions before asking them, for missing
  branches, dependent questions, facts posed as decisions and unsupported
  recommendations.
- **Drafts:** hand over each section as a stable snapshot, checked against the
  user's recorded answers and the tier above.
- **Script:** shape thread boundaries and dependencies before the user sees
  them.
- **The user's thinking time:** give the reviewer bounded work while a round
  is out.

## Ground before the first question

Gather what exists before asking the user for the rest:

- Read prior plans and design documents, including related projects they cite;
  run records and incident notes; decision records; the Git history of the
  affected area; issues; and status documents. Read earlier agent sessions'
  transcripts when they are accessible and relevant. Fan wide reading out to
  subagents and keep only their conclusions.
- Inventory the present: live resources, what they cost, what can't be
  replaced, and work in flight in other sessions or worktrees.
- Draft what you believe, with sources, marking what you inferred.

Separate three kinds of input:

- **Facts** the environment can settle are yours to find. Never ask the user for
  one. A pending lookup blocks only the questions downstream of it.
- **Decisions** are the user's. Never answer them yourself, however much
  momentum the task has.
- **Knowledge only the user holds** is theirs to supply: earlier attempts and
  why they failed, constraints outside the repository (budgets, shared
  credentials, irreplaceable hardware, deadlines, people, their own
  availability) and domain expertise. Ask for it. Never infer a rule or
  constraint from an absence of evidence.

Memories on both sides can be wrong: check the user's recollections against the
environment as you would your own, and raise disagreements.

Open the first round with grounding: restate the north star in the user's words,
summarize what you found, and ask what history, constraints and expertise the
documents don't show.

## Grill in rounds

Model the campaign as a design tree: the north star branches into outcomes,
milestones and decisions, and each decision into the ones that depend on it. The
**frontier** is every open decision whose prerequisites are settled.

- Ask the whole frontier each round. Keep a question out of a round when it
  depends on another question in that round. Recompute the tree after each
  round, since answers move the frontier and can reopen settled branches.
- Shape each question as `working-conventions` › Ask the user describes, and
  present the strongest alternative fairly.
- When a decision's tradeoffs exceed what a dialog option can carry, write its
  options table (option, for, against) and recommendation into the draft's
  decisions section first, then ask, pointing there.
- Challenge answers that conflict with the code, the evidence or an earlier
  answer.
- When talking can't settle a question because it needs evidence or something
  to react to, stop grilling it. Propose the smallest spike, following
  `agentic-workflow`'s spike guidance, and mark the decision Open pending it.
  For an unfamiliar frontend choice, the spike is a quick prototype or mockup
  made with `frontend-design`.
  The roadmap schedules the spike before the work it de-risks. Planning
  authorizes read-only investigation; a spike that spends money, touches live
  systems or runs long needs the user's authorization.
- Treat "I don't know" as an answer: turn it into a spike, a deferral with a
  trigger, or a provisional assumption labelled as one.
- Don't cap the questions. If the tree outgrows one campaign, propose a
  narrower north star or separate campaigns.

A tier's grilling ends when the frontier is empty: every branch visited and
nothing silently assumed.

### Ask through the dialog

Route every question through a native structured question tool, following
`agentic-workflow`'s "Use the Q&A dialog" section, with one exception: ask the
whole frontier per round instead of one question at a time. When the frontier
exceeds the tool's per-call limit, split it across consecutive dialogs,
grouping related questions. Keep each dialog small enough to render whole; if
one renders incompletely or fails, keep the answers given and resend only the
unanswered questions, and switch to prose when the user asks. Name the object
and unit in any count or budget you ask about (threads, runs, workers, hours).
Use free-text answers for open questions such as the north star, history and
expertise.

### Keep the draft as the ledger

Write each answer into the draft the moment it settles, not at the end of the
interview: decisions into the decisions table, constraints and exclusions into
scope, and history and expertise into the background. Keep the current frontier
as the draft's open questions. A fresh agent, or you after compaction, must be
able to resume the interview from the draft alone.

- Attribute each decision as `(the user, <date>)`, or in the repository's
  own form, with the reason in the user's words when short, and record it as
  `working-conventions` › Record the user's decisions requires.
- Say who proposed what with the plan template's labels: **Decided**,
  **Agreed**, **Proposed**, **Open**, **Rejected** and **Verified**.
- Revise in place and keep the trail: "**Changed (the user, <date>):** …,
  replacing …". Record corrected and rejected ideas as lessons, so later agents
  don't propose them again. Keep the current plan readable without that trail:
  the decisions table shows each decision's current form, and superseded
  rationale moves to the decision's subsection or the rejected-ideas section
  rather than staying inline in the text agents read first.

## Tier 1: the plan

Grill breadth-first across the whole space, then deepen each branch: the north
star and the first useful result; hard constraints, ranked preferences and
later work; what is out of scope; milestones and their gates; the decisions;
the main uncertainties and their spikes; and the triggers for reassessment.

Write it from [assets/plan-template.md](assets/plan-template.md), adapted to
the project. Err toward verbosity: the plan is the context store that the
roadmap, the script and every implementing agent read. Give everything later
tiers cite a stable ID: decisions (D1…), work items (§5.3 item 2), milestone
boxes with distinctive opening words, and gates. Make each gate a check someone
can evaluate, not an intention.

Before review, check that every milestone has a gate; every decision is
Decided, Agreed, or Open with what settles it; exclusions are explicit; and the
history cites its sources.

## Tier 2: the roadmap

Derive the roadmap from the reviewer-accepted plan and the current state;
the plan's own status may be stale. Grill only what the plan leaves open about how:
ordering tradeoffs, grouping steps across milestones, live-resource lifetimes
and budgets, and which human interventions can be settled now.

For implementation campaigns, include a testing strategy that follows
`working-conventions` › Test cost, and attach expensive evidence checks to
explicit gates.

Every step ends in a deliverable: a mergeable change, a published artifact or
a written decision. When a step's goal is a measured improvement, such as
faster CI or a frame-time target, grill the user for its measurement method
(concretely, such as "1 cold run and 3 warm runs, median and range") and a
kill criterion (such as "no gain after two candidates or N active hours:
revert and report"), and record both in the step. Its Proof is the change
merged with the number measured by that method; a missed target is a result
to report, not a reason to keep the step open. Give the measurement its own
step with a time cap rather than leaving the method to be invented and
validated during the run.

Write it from [assets/roadmap-template.md](assets/roadmap-template.md), whose
"How to read it" defines steps, **Needs**, **Proof**, **Ticks** and the tick
rule:

- List steps in a workable order, spikes before the work they de-risk. Group
  steps from different milestones when that improves flow, such as steps that
  share one live environment.
- The script derives which threads can run in parallel from Needs, so never
  leave a dependency implied by the order.

Check coverage both ways: every open plan box and item maps to a step, and
every step ticks something or says what it enables. Check that the Needs graph
has no cycle. Fix gaps rather than listing them. Keep steps beyond the current
evidence coarse and marked provisional instead of inventing detail. Surface
what the roadmap had to add that the plan doesn't say, such as an ordering
hazard, a check that works before any host exists or a cost above budget, and
fold any resulting decision back into the plan.

### Make human interventions explicit

Plan for implementation that runs away from the keyboard. Mark every point
where a person must act:

- a decision only the user can make;
- access only they can grant, such as creating a token or an OAuth client;
- presence, such as a browser login or being online at a set time;
- a manual action, such as clicks in a web console;
- approval of spending, a destructive operation or an external publication.

Give each step that needs one a **Human** line naming the kind, what the user
does and when: before the step starts, at its thread's approval, or at a named
point mid-step, saying whether the step waits or continues around it. Never
bury a human action in a step's prose. A step without a Human line runs
without anyone once its thread is approved. Collect every intervention in the
roadmap's closing table.

Then grill the user to shrink that table: settle decisions now, provision
access ahead of time, and move mid-step interventions to the thread's
approval. Turn approvals the thread will repeat, such as one per release or
per credential use, into standing grants asked at that approval
(`working-conventions` › Standing grants). Record each answer in the table; what remains is the planned human
work.

Settle first any decision whose answer changes an invariant other steps rely
on, rather than leaving it open inside them. Give each dependent step a Needs
on it, and keep those steps provisional and out of ready threads until the
user decides.

## Tier 3: the script

The script lists the threads to open, each with a literal opening prompt, its
dependencies and its human interventions, so neither the user nor an
orchestrating agent has to guess the next grouping, what can run at once, or
when a person is needed.

Read the roadmap, the status document, `keep-me-in-the-loop`'s current
instructions and the live state: resources that are up, leases and their
dates, and other sessions or worktrees working on the roadmap. Read those
sessions' transcripts or status when accessible; their choices can reorder the
threads.

Group roadmap steps into threads:

- A thread is one agent's run and one approval: a `keep-me-in-the-loop`
  invocation when the user opens it, or a worker running `continuous-peer-review`
  under `overseer`, whose only approval is the user's agreement to the thread's
  scope. Size it to its substantial phase of about 2 to 4 chunks, which run in order. Front-load
  the thread's decisions, authority and spending to that approval so it can run
  to the end.
- Cut where the user must decide; where a live resource's life begins and ends,
  so it is brought up, used fully and torn down rather than left idle between
  threads; at external dates such as lease ends, quota windows and the user's
  availability; and at phase gates. A thread may cross a gate when both sides
  use one environment; say where to split it if the user wants to approve at
  the gate.
- Group across phases when steps share an environment or one fills another's
  wait, and keep each thread within reach of one context window.
- Keep steps that change one behavior or invariant in one thread, even when
  the plan files them under different milestones, such as layout, framing and
  selection on a shared canvas. Split across threads, the later thread
  rediscovers and breaks the earlier one's assumptions. When coupled steps are too large for one thread, cut where the
  first thread settles a contract and proves it with tests, and name that
  contract in the second thread's Depends on.
- Put steps that fit no thread in a deferred list with the reason and trigger.

### Order threads only by explicit dependencies

Threads run in parallel unless the script says otherwise. Give every thread a
**Depends on** entry, derived from its steps' Needs and the resources it
shares, with the reason for each dependency:

- **after** thread N: it needs that thread's outcome, which the entry names;
- **not alongside** thread N: both use a live resource, a quota, a credential's
  validity window, the user's attention, or files both edit heavily, so they
  can run in either order but not at once. A thread of another campaign that
  uses the same repository, tracker or compute host counts too: one overseer
  runs per repository and shared host;
- **not before** a date or external event, such as a lease ending.

Write "none: runs in parallel with any thread" when nothing applies. Check the
graph for cycles, and draw it at the top of the script with its critical path.

Cut threads so that as many as possible can run at once. A script where every
thread waits on the one before runs one worker at a time, and any stall stops
the whole campaign. When the graph is mostly a chain, test each link against a
real outcome the later thread needs or a resource both use. Drop links that
only reflect a preferred order, and split threads along independent surfaces
or contracts. Mark the threads that can run together in the graph. When the
critical path still covers most of the script, say so at the top with the
reason, so the user and the overseer know the campaign runs serially.

### List each thread's human interventions

Give every thread a **Human** entry, drawn from the roadmap's interventions
and grouped by timing as the script template's thread entry shows. The
approval is itself an intervention; list what it settles. Aim for nothing
mid-run, and write "none after approval" when that holds so the user knows the
thread runs away from the keyboard. Collect every intervention with a date, a
time or a mid-run point, in time order, into the script's "When a human is
needed" list.

Grill only what grouping needs from the user: their availability for the
listed interventions, how many threads they will run at once, spending pace,
and whether to approve at a gate.

Write it from [assets/script-template.md](assets/script-template.md), covering
every thread to the plan's final gate; threads past the current evidence stay
coarse and provisional. Keep each opening prompt short and stable, as the
template's prompt shows: point at the script's rules and the thread's entry
rather than restating facts that will go stale, and end with the obligation to
mark the thread done and record deviations that change other threads. When a
status document exists, make its recommended next sequence point at the
script's ready threads, those whose dependencies are met, instead of keeping a
second sequence.

### Keep tier 3 as tracker workstreams

When the repository's issue tracker can link issues as blocked by others, such
as GitHub issues in a Project, tier 3 can live there as workstreams instead of
a script document. For a new campaign, ask in tier 3's grilling round which
form to use. A script is one readable page and needs no tooling. Workstreams
let the tracker block, claim and close threads, and let a tool compute which
can start, but they need that tool to be read as a whole. Once workstreams
are chosen or in use, follow
[references/tracker-workstreams.md](references/tracker-workstreams.md).

## Confirm the tiers together

By default, derive the next tier from the reviewer-accepted draft without an
intermediate confirmation dialog. Keep unconfirmed tiers marked as drafts.
Ask unresolved user decisions when needed; batching confirmation does not
authorize you to settle them. If the user requests approval between tiers,
honor that cadence instead.

Present the complete set for confirmation only after the reviewer has checked
the final snapshots and their consistency across tiers, reporting its
position as `working-conventions` › Review loops describes.

Ask one confirmation question covering all three tiers in one dialog, with
links and a reading guide for each: which sections to check first, starting
with the summary and every Decided row. Offer confirmation of the complete set
or a request for revisions. When revising an existing set, identify which tiers changed and include those in
the same confirmation. If revisions affect an upstream tier, propagate them
downward and have the reviewer check the updated set before asking again.
Don't publish the tiers or start implementation until the user explicitly
confirms them, as `working-conventions` › Authority describes. Confirmation
covers the tiers only, never a release.

## Publish and link

Commit each confirmed tier on its own and push, following
`working-conventions` › Publication. When the user confirmed a mutually
consistent set and separate commits would only rerun the repository's hooks,
one commit for the set is fine. Other sessions may be editing the same
documents, so check the worktree and the remote first. Run the repository's
Markdown formatter and linter. Link the plan, roadmap, script and status
document to each other, and point the repository's agent instructions at the
roadmap's tick rule when nothing does yet.

## Revise when evidence changes

Revise the affected tier and propagate downward when a thread ends with
deviations, a parallel session changes a dependency, a gate fails or a decision
changes. Keep the decision history in the plan, update the roadmap's steps, and
re-derive the script's dependencies, ready threads and human interventions,
with a dated entry in its revision log. Return to the user with
a grilling round when outcomes, scope, priorities, acceptance criteria or
spending change; propose routine re-sequencing within confirmed decisions
directly. Never weaken a gate silently to finish.

## Close a finished campaign

Close a campaign only once the user confirms its final gate is met, or closes
it with a caveat they accept; never decide that yourself. Then follow
[references/close-campaign.md](references/close-campaign.md).

## Hand off the confirmed set

After the **TL;DR** (`working-conventions` › Updates), give each document's
path and publication state, how it is laid out, what it adds that the tier above
doesn't say, the reviewer's closing position, which decisions remain open and
who owns them, and the next action: any remaining tier, or the script's ready
threads with their prompts and when a human is next needed. For workstreams,
link the readiness summary and name the ones awaiting the user's approval.
Mention that `overseer` can run the ready threads as separate Paseo agents.
