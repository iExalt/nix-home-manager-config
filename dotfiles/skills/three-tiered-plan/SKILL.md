---
name: three-tiered-plan
description: "Grill the user about a campaign that will span days or weeks, then write and maintain, with a continuous peer reviewer, three planning documents: a verbose, history-grounded plan (what and why), a concise roadmap of steps with proofs (how), and a script of literal keep-me-in-the-loop threads with explicit dependencies and human interventions. Use when starting or re-planning such a campaign, when deriving or revising its roadmap or script, or when closing a finished one; not for work one session can hold (use agentic-workflow) or for executing a script thread (use keep-me-in-the-loop)."
---

# Three-Tiered Plan

Shape a campaign that will steer days or weeks of agent work into three
documents, each more concise and more literal than the last:

| Tier | Answers | Shape |
| --- | --- | --- |
| **Plan** | What and why: north star, scope, exclusions, decisions, history, milestones and gates | Verbose; history and rationale are the point |
| **Roadmap** | How: steps, what each needs, what proves it, which plan boxes it ticks, where a human acts | A fraction of the plan |
| **Script** | Which implementation threads to open, with what prompt, after what, and when a human is needed | A page or two; literal |

Grill each tier out of the user, then write it with a continuous reviewer.
Draft and review the tiers in order, then ask the user to confirm the complete
set in one dialog. The user owns outcomes, scope and
tradeoffs, and holds history and expertise the repository doesn't record. You
find facts, propose, challenge and write; the reviewer challenges you.

## Start from the right tier

Read the repository's instructions and documentation conventions, any existing
plan, roadmap, status document and script, and the Git state. Start at the
first tier that is missing or invalidated:

- no plan: the plan;
- a plan without a roadmap: the roadmap;
- a roadmap without a script: the script;
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

- **Grounding:** the reviewer checks your summary against the sources and looks
  for history and constraints you missed or inferred.
- **Rounds:** send each round's questions before asking them. The reviewer
  challenges missing branches, questions that depend on another in the same
  round, facts posed as decisions, misrepresented options and unsupported
  recommendations. Brief agreement suffices for a routine round.
- **Drafts:** hand over each drafted section as a stable snapshot. The reviewer
  checks fidelity to the user's recorded answers, internal consistency,
  coverage of the tier above, evaluable gates, unstated assumptions, missing
  dependencies and human actions left unmarked.
- **Script:** shape the thread boundaries and dependencies with the reviewer
  before the user sees them, as `keep-me-in-the-loop` does for chunk plans.
- **The user's thinking time:** before asking a round, assign the reviewer
  bounded idle work for the wait, such as reading sources for the next branch,
  checking the draft's claims or preparing counterexamples to your leading
  recommendations, so the reviewer keeps working while a dialog blocks you.

Implementation keeps the same discipline: every script thread runs under
`keep-me-in-the-loop`, which brings its own continuous reviewer.

## Ground before the first question

History and the user's expertise ground a plan better than anything else.
Earlier attempts explain why the obvious route was already rejected. The user
knows which resources are irreplaceable, which credentials are shared, what the
budget is and how the domain behaves in practice. Gather what exists before
asking for the rest:

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
environment as you would your own, and raise disagreements. Learn early where
the user is expert and where they want explanation. Where they are expert, ask
before proposing; elsewhere, explain briefly and support recommendations with
evidence rather than authority.

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
- For each question, give the context, the options with their consequences for
  results, effort, risk and what gets postponed, and your recommendation with
  its evidence. Present the strongest alternative fairly.
- When a decision's tradeoffs exceed what a dialog option can carry, write its
  options table (option, for, against) and recommendation into the draft's
  decisions section first, then ask, pointing there.
- Challenge answers that conflict with the code, the evidence or an earlier
  answer. A session without disagreement probably asked questions below the
  fidelity the campaign needs.
- When talking can't settle a question because it needs evidence or something
  to react to, stop grilling it. Propose the smallest spike, following
  `agentic-workflow`'s spike guidance, and mark the decision Open pending it.
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
grouping related questions. Before each dialog, explain the context and
tradeoffs in commentary. Use free-text answers for open questions such as the
north star, history and expertise.

### Keep the draft as the ledger

Write each answer into the draft the moment it settles, not at the end of the
interview: decisions into the decisions table, constraints and exclusions into
scope, and history and expertise into the background. Keep the current frontier
as the draft's open questions. A fresh agent, or you after compaction, must be
able to resume the interview from the draft alone.

- Use the repository's attribution form when it has one, such as
  `(you, 2026-09-29)` or `(the user, 2026-09-26)`; otherwise
  `(the user, <date>)`. Record the reason, in the user's words when short.
- Say who proposed what: **Decided** (the user's call), **Agreed** (your
  proposal, accepted), **Proposed**, **Open** (with its spike or trigger),
  **Rejected** (with why) and **Verified** (with evidence).
- Revise in place and keep the trail: "**Changed (the user, <date>):** …,
  replacing …". Record corrected and rejected ideas as lessons, so later agents
  don't propose them again.

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

For implementation campaigns, include a testing strategy with most behavioral
coverage in fast unit tests, fewer integration tests for contracts, and a small
end-to-end set for critical journeys. Define the routine-check command, runtime
budget, stable baseline and comparable execution conditions, using existing
evidence or a named early measurement. Keep expensive evidence checks attached
to explicit gates. Make suite-runtime maintenance part of each implementing
step; do not plan indefinite test growth followed by a cleanup milestone.

Write it from [assets/roadmap-template.md](assets/roadmap-template.md):

- A **step** is one unit of agent work: a few commits ending in its proof.
  List steps in a workable order, spikes before the work they de-risk. Group
  steps from different milestones when that improves flow, such as steps that
  share one live environment.
- Each step states what changes, its **Needs**, its **Proof** (offline, or live
  with named resources and a retained record) and its **Ticks** (the plan's
  boxes and items it closes). Agents tick a step and its plan boxes in the same
  commit.
- **Needs** names the steps, gates or decisions the step depends on, or
  "nothing". It is the constraint; list order is only a suggestion. The script
  derives which threads can run in parallel from it, so never leave a
  dependency implied by the order.
- Lead with a progress table, a table of the live runs where time and money go,
  and a point-form summary per phase whose bullets cite step numbers and end
  with the phase's gate. End with every human intervention.

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
approval. Record each answer in the table; what remains is the planned human
work.

## Tier 3: the script

The script turns the roadmap into the implementation threads to open, each
with a literal opening prompt, its dependencies and its human interventions,
so neither the user nor an orchestrating agent has to guess the next grouping,
what can run at once, or when a person is needed.

Read the roadmap, the status document, `keep-me-in-the-loop`'s current
instructions and the live state: resources that are up, leases and their
dates, and other sessions or worktrees working on the roadmap. Read those
sessions' transcripts or status when accessible; their choices can reorder the
threads.

Group roadmap steps into threads:

- A thread is one `keep-me-in-the-loop` invocation and one approval, sized to
  its substantial phase of about 2 to 4 chunks, which run in order. Front-load
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
- When a thread's work can't run inside the loop's own session, such as a final
  check that needs a fresh agent with only the docs, say how the loop session
  launches that agent, checks each attempt and fixes root causes between them.
- Put steps that fit no thread in a deferred list with the reason and trigger.

### Order threads only by explicit dependencies

Threads run in parallel unless the script says otherwise. Give every thread a
**Depends on** entry, derived from its steps' Needs and the resources it
shares, with the reason for each dependency:

- **after** thread N: it needs that thread's outcome, which the entry names;
- **not alongside** thread N: both use a live resource, a quota, a credential's
  validity window, the user's attention, or files both edit heavily, so they
  can run in either order but not at once;
- **not before** a date or external event, such as a lease ending.

Write "none: runs in parallel with any thread" when nothing applies. Check the
graph for cycles, and draw it at the top of the script with its critical path.
State how parallel threads stay isolated: each works in its own worktree,
rebases before every push, and reconciles shared documents (roadmap ticks,
status, the script) without overwriting another thread's entries.

### List each thread's human interventions

Give every thread a **Human** entry, drawn from the roadmap's interventions
and grouped by timing: before opening, at approval, mid-run at a named point
(saying whether the thread pauses affected work or continues around it), and
after. The approval is itself an intervention; list what it settles. Aim for
nothing mid-run, and write "none after approval" when that holds so the user
knows the thread runs away from the keyboard. Collect every intervention with
a date, a time or a mid-run point into the script's "when a human is needed"
list.

Grill only what grouping needs from the user: their availability for the
listed interventions, how many threads they will run at once, spending pace,
and whether to approve at a gate.

Write it from [assets/script-template.md](assets/script-template.md), covering
every thread to the plan's final gate; threads past the current evidence stay
coarse and provisional. Keep each opening prompt short and stable: invoke
`keep-me-in-the-loop`, point at the script's rules and the thread's entry
rather than restating facts that will go stale, and end with the obligation to
mark the thread done and record deviations that change other threads. When a
status document exists, make its recommended next sequence point at the
script's ready threads, those whose dependencies are met, instead of keeping a
second sequence.

## Confirm the tiers together

By default, derive the next tier from the reviewer-accepted draft without an
intermediate confirmation dialog. Keep unconfirmed tiers marked as drafts.
Ask unresolved user decisions when needed; batching confirmation does not
authorize you to settle them. If the user requests approval between tiers,
honor that cadence instead.

Present the complete set for confirmation only after the reviewer has reviewed
the final snapshots and their consistency across tiers, and you agree, or the
disagreement is clear. Present the reviewer's
position: its agreement, the material amendments it secured, and any
unresolved disagreement with both positions and your recommendation. A
reviewer notification or an unacknowledged draft does not count as review.

Ask one confirmation question covering all three tiers in one dialog, with
links and a reading guide for each: which sections to check first, starting
with the summary and every Decided row. Offer confirmation of the complete set
or a request for revisions; don't ask three separate approval questions. When
revising an existing set, identify which tiers changed and include those in
the same confirmation. If revisions affect an upstream tier, propagate them
downward and have the reviewer check the updated set before asking again.
Don't publish the tiers or start implementation until the user explicitly
confirms them. Silence, a timeout or a preselected option is not confirmation.
Offer a diagram-led
companion, such as a lifecycle with Mermaid diagrams, when the design is
cheaper to disagree with visually.

## Publish and link

Commit each confirmed tier on its own with a conventional commit, and push
unless repository rules or the user say otherwise. Other sessions may be
editing the same documents: check the worktree and the remote first, commit
only your files, and never amend or force-push over work that isn't yours. Run
the repository's Markdown formatter and linter. Link the plan, roadmap, script
and status document to each other, and point the repository's agent
instructions at the roadmap's tick rule when nothing does yet.

## Revise when evidence changes

Revise the affected tier and propagate downward when a thread ends with
deviations, a parallel session changes a dependency, a gate fails or a decision
changes. Keep the decision history in the plan, update the roadmap's steps, and
re-derive the script's dependencies, ready threads and human interventions,
with a dated entry in its revision log. Return to the user with a grilling
round when outcomes, scope, priorities, acceptance criteria or spending change;
propose routine re-sequencing within confirmed decisions directly. Never weaken
a gate silently to finish.

## Close a finished campaign

Close a campaign once the user confirms its final gate is met, or closes it with
a caveat they accept; never decide that yourself. Closing keeps the campaign's
working documents from crowding the repository's current docs:

1. Record the closure in the status document and the script's revision log:
   the date, the evidence or accepted caveat, and the user's words.
2. Fold what is still true into the repository's living docs. Write it as
   current-state reference: what the system does and why, without the
   campaign's play-by-play, step numbers, thread names or decision IDs. Re-read
   the living docs the campaign touched and align them with each other.
3. Move the plan, roadmap, script and status document to
   `docs/complete-campaigns/<campaign-name>/`, or the repository's own
   equivalent, and fix their relative links.
4. Delete the campaign's temporary records: dated run records, and the probe
   scripts and fixtures kept only as evidence. Before deleting, pin the last
   commit that has them and re-point every surviving link and code comment at
   that commit (a permalink, or `git show <commit>:<path>`) or at the living
   doc that now holds the fact. Ask before deleting anything the repository's
   instructions protect or a maintained check still reads.
5. If the repository's agent instructions don't say where finished campaigns
   go, add it. Remove instructions that point agents at the campaign's
   documents or tick rule.
6. Run the repository's checks, including link and Markdown checks, and
   publish as in "Publish and link": the move and deletion in one commit, the
   living-doc rewrite in another.

## Hand off the confirmed set

Begin with a one- or two-line **TL;DR**. Then give each document's path and
publication state, how it is laid out, what it adds that the tier above
doesn't say, the reviewer's closing position, which decisions remain open and
who owns them, and the next action: any remaining tier, or the script's ready
threads with their prompts and when a human is next needed. Mention that
`overseer` can run the ready threads as separate sessions.
