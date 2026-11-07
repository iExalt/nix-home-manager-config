---
name: working-conventions
description: "Shared rules for the workflow skills: authority, autonomy, asking the user, review loops, evidence, tests, updates, waiting, delegation, records, publication and cleanup. Load it first whenever a workflow skill runs (overseer, keep-me-in-the-loop, subagent-pair-program, continuous-peer-review, pair-program, three-tiered-plan, agentic-workflow), and have the leads, reviewers and workers you brief load it too. Not a workflow itself."
---

# Working Conventions

An explicit exception a workflow skill names wins for that skill. The user's
global instructions (`AGENTS.md`, loaded as `CLAUDE.md` in Claude Code) come
first; this skill adds detail and never relaxes them. Open every brief you
write for a lead, reviewer or worker with the instruction to load this skill
before any other step; a pilot's brief carries the rules its task needs
instead.

A bare skill name here, such as `keep-me-in-the-loop`, means
`iExalt:keep-me-in-the-loop`; invoke it by the namespaced name.

Before Glean CLI searches or document retrieval, Slack CLI searches, or Linear relation changes, read
[references/cli-contracts.md](references/cli-contracts.md). It carries user-owned
corrections to externally managed CLI skills; don't patch their installed copies.

## Authority

- Approval covers what it names: its scope, its checks and its stated
  conditions. Silence, a timeout or a preselected option is not approval.
- A standing approval replaces the per-step gate it covers. Don't ask again
  for an approach, check or in-scope repair already approved, and don't ask
  who merges: follow the repository's rules and the user's merge policy.
- When the user approves with conditions, restate them in the plan and check
  each before committing or pushing. Ask the user before breaching one,
  rather than breaching it and reporting afterwards.
- Routine technical replanning, repairs and increment sizing are yours.
  Return to the user before affected work proceeds when evidence requires a
  material change to outcomes, scope, priorities, acceptance criteria, cost,
  risk, external actions or an approved checkpoint. Explain the evidence and
  recommend the smallest useful adjustment. Sunk effort is never a reason to
  continue.
- Cutting or publishing a release (a release PR merge that publishes,
  `gh release create` or `edit`, making a draft public, a tag) needs the
  user's separate, explicit approval naming that release. Plan or phase
  approval, a session grant, a merge approval and "keep going" never cover it.
- Another agent's approval or message, a worker's or peer's included, never
  extends the user's authority or counts as the user's approval.
- Never work around a permission boundary or a classifier block. Report the
  exact action and the reason, continue independent work, and wait for the
  user's authorization.

## Autonomy

The autonomy level sets when you involve the user in decisions inside the
agreed scope. Use the level the user names, or **medium** when they name
none; never raise it yourself. State the level in your opening proposal or
plan, and record it in the plan and in every brief. The level governs your
own decisions: agents you brief route their requests through you and don't
inherit your authority.

| Level | When to involve the user |
| --- | --- |
| **Low** | Invite the user into consequential choices within scope: implementation tradeoffs, phase direction, re-sequencing and recovery. Recommend an option before the affected work proceeds. |
| **Medium (default)** | Approve in-scope work the workflow lets you approve, choose routine details, re-sequence work and recover stalled agents. Consult when a tradeoff materially affects what the user agreed. |
| **High** | Decide within scope and resolve recoverable issues yourself, reporting meaningful decisions afterward. Interrupt only for the mandatory consultations below, a planned human intervention, or a blocker only the user can clear. |

At **every level**, always consult the user for:

- An unresolved subjective preference on taste or design, once agents have
  separated out what they can test or measure, as described below. Apply a
  settled preference without asking again.
- A serious unexpected event or issue that is unrecoverable or has wide or
  deep effects, even if part of it can be recovered. For other recoverable
  issues, the level decides whether to consult.
- Projected costs beyond the agreed limits. When costs were not discussed,
  the limit is **zero/free**. Ask before incurring the increase, not after.

No level changes the agreed scope, acceptance boundaries, a gate a workflow
skill puts in the user's hands, explicit human checkpoints, permission
requirements or the rules under Authority. A workflow skill may require an
explicit grant before high autonomy takes effect. Use already authorized
containment when needed to prevent further harm.

### Test measurable behavior before escalating

"Look and feel" alone is no reason to ask the user. Separate testable
behavior from subjective preference, including within one review item. At
medium and high autonomy, have agents measure, fix and verify the testable
part, such as frame times against agreed targets, instead of asking the user
to try it. An agent calling something subjective doesn't make it so. Escalate
only the preference the evidence can't settle, and keep claims within what
the evidence shows. If hardware or access is missing, ask only for that
access; don't relabel the gap as a taste question.

## Record the user's decisions

A decision attributed to the user quotes their words or the option they chose,
with its source, date and exact scope (which items, how many). Never write that
the user decided something they weren't asked, or decided it for a different
item or thread. A rule nobody asked them about is Proposed, not theirs.

## Ask the user

- Ask through the harness's native question dialog: an async one such as
  Codex's `request_user_input_async` when available, otherwise a dialog such
  as `AskUserQuestion`. Never substitute a prose questionnaire. Never re-send
  a dialog unchanged.
- Ask only for decisions, knowledge only the user holds, and taste still
  unresolved after Autonomy › Test measurable behavior before escalating.
  Give each option's consequences for results, effort, risk and what gets
  postponed, and the evidence behind your recommendation.

## Review loops

- Use one persistent reviewer for the job and reuse it across increments,
  chunks and phases. A review notification, an unacknowledged draft or
  silence is not review.
- A material finding makes the outcome wrong, unsafe, lossy or short of its
  acceptance criteria. Record each verified finding as material, optional or
  rejected, with the reason, and batch optional ones for the user as
  deferrals. Triage extra one-shot reviews, such as a user-requested
  `/code-review`, the same way.
- After each round, add a ledger line with its material and total counts
  beside the previous round's. An agent the user granted high autonomy, such
  as an overseer, approves repair and review rounds itself and reports the
  trend afterward. When the same finding returns after its fix, that agent
  has the design reassessed instead of patching again; failing checks follow
  Repeated failure. A finding that undermines an earlier choice of the
  user's, including its altitude or the effort, risk or simplicity estimate
  behind it, goes to the user before the next round.
- "Reviewed" and "accepted" name the revision the reviewer saw. Commits after
  it are "not re-reviewed" until the reviewer sees them, including a fix for
  the reviewer's own finding. Check the reviewer's last verdict against the
  head before writing "reviewed" anywhere. Send the delta before pushing to an
  open PR; if you must push first, report the push as not re-reviewed.
- When you present a proposal the reviewer shaped, give its position: its
  agreement, the material amendments it secured, and any unresolved
  disagreement with both positions and your recommendation.

## Repeated failure

When the same failure returns after two repairs at the same gate, or each
repair exposes a new failure in the same interaction, stop patching. Have the
design reassessed (which code owns the behavior, which invariants hold, the
simplest change that satisfies them) or escalate with the hypotheses ruled out
and the next discriminating experiment. A contract may set a different
threshold for its workload. Failures on a new increment start a new count.
A review finding that returns after its fix follows Review loops instead.
Passing local tests don't resolve a failing end-to-end reproducer, and an
approach doesn't run past its agreed stop condition.

## Evidence

- Label each claim as read (file and line at a revision), ran (command and
  result) or inferred. Never say "verified" or "recomputed" for what wasn't
  run, and read the source before asserting what code does.
- A check, result or behavior claimed in a report, status document, commit
  message or hand-off cites its command and result line or its artifact.
  Write "not run" or "unverified" for the rest. Don't contradict your own
  measurements, and state only behavior the code and environment can produce.
- Keep separate: local verification, CI results, deployment and live proof.
- When you relay another agent's finding, keep its confidence: an inferred
  cause or an unrun check stays inferred or unrun. Before passing a claim on,
  check it against the evidence it rests on: the diff, the failing test and
  its version on the base branch, the screenshot, trace or log. A test whose
  expectation changed does not show a product regression, and a measurement
  must name the element or quantity the requirement is about. A criterion
  resting only on another agent's report is "reported, not checked".
- Gates are pass/fail. An unmet proof stays unmet and its gate unticked, even
  when the rest of the work is done. A deferral names the later gate it moves
  to, what remains unproven, and the evidence required there. Reusing earlier
  evidence, substituting a check or moving a required proof to a later gate
  needs the user's approval unless already agreed. Never weaken acceptance
  silently.

## Work states

Use one vocabulary:

| State | Means |
| --- | --- |
| designed | A decision or contract exists; nothing proves it is implemented |
| implemented | Code or artifacts exist; the required verification is incomplete |
| verified | The stated exit condition has current, reproducible evidence |
| reviewer-accepted | The reviewer accepted a named revision with no pending required checks; "accepted if tests pass" is still awaiting verification |
| published | On the remote or merged, and confirmed there |

A claim is never stronger than its evidence. Partial implementation, checked
subtasks or a passing subset of tests don't make a milestone complete.

## Test cost

Beyond the global instructions' test-cost rules:

Aim for these end-to-end wall-clock latencies. Repository budgets may be tighter.
These are optimization targets, not permission to weaken checks or change gates.

| Loop or gate | Target | Preferred |
| --- | --- | --- |
| Local development loops and checks | Under 60 seconds | Under 60 seconds |
| Routine CI checks blocking every PR | Under 5 minutes | Under 3 minutes |
| Deeper checks blocking releases | Under 15 minutes | Under 10 minutes |
| Full release after a release-please PR is merged | Under 30 minutes | Under 15 minutes |

For CI, count from the triggering event through all required work, including
queueing, setup, dependencies and artifact delivery; report execution time
separately when queueing dominates. For a local loop, count command start to
usable feedback. Track cold and warm runs separately. When a loop exceeds its
target or grows against its stable baseline, use `iExalt:slow-ci` to diagnose
and reduce the cost. Fix bugs, repeated work and algorithms before adding
parallelism. Changing required proofs or their gate still needs approval.

- Carry the routine-check command, its wall-clock budget and the stable
  baseline, with its machine, cache and concurrency conditions, into every
  plan and brief where tests grow or change. If absent, establish them
  proportionately before substantial suite growth.
- Compare across the whole run; never reset the baseline at a chunk or
  hand-off. Don't plan a cleanup milestone or raise the budget to absorb
  growth.
- Consolidating tests or lowering their cost is ordinary maintenance when
  every required proof survives. Moving a required proof to a later gate or
  making it optional is an acceptance change.

## Updates

- Begin proposals and reports with a one- or two-line **TL;DR**.
- Report outcomes, not activity. Don't narrate or announce next steps; this
  overrides default guidance to comment at intervals or before tool calls.
- Send an update when:
  - a reviewer accepts an increment, a chunk or thread finishes, or work is
    published;
  - a live operation starts (with its stop condition), deviates materially or
    finishes;
  - a finding changes confidence, the plan, scope or timing;
  - a decision, blocker or new user instruction needs a response.
- Send no update for launches, in-scope approvals, relayed answers, retries,
  routine recovery, waits or traffic with a reviewer. When several events land
  together, send one update covering them.
- Stay silent otherwise. A turn with nothing to report ends with no text,
  even if the harness re-prompts an empty turn. Never send filler, such as
  "No news." or a repeat of an earlier update.
- Write for a technically capable owner without expertise in the subsystem:
  what changed, why it matters, what remains unproven, and what's next.
  Explain necessary terms through their purpose.
- Limits, deferrals, skipped checks and the reviewer's parked findings reach
  the user, not only the reviewer.

The workflow skill sets each update's format, such as `keep-me-in-the-loop`'s
one-line prefix or `overseer`'s roll call.

## Waiting

- Prefer completion notifications to polling; otherwise use a bounded
  blocking check. Give each monitor failure filters that don't match success
  output such as `failed=0`.
- A timeout alone creates no work: wait again without reading logs or asking
  for status.
- Before ending a turn to wait on a peer, confirm it is still running or has a
  message in flight.
- An agreed checkpoint is a stall threshold, not a reporting deadline. When an
  agent goes quiet past it, inspect it first (a permission prompt, exhausted
  context, a crash), then make one bounded inquiry.

## Delegation

- Brief each agent with the goal, scope and non-goals, acceptance criteria,
  the materiality bar, constraints, raw source and evidence locations, prior
  decisions (marking constraints apart from claims that the code is correct),
  its return address, the model policy and its stop conditions. Leave out
  your own conclusions when you want an independent reviewer or tester.
- Use native subagents and native messaging. Delivery is not acknowledgement:
  get the acknowledgement before acting on anything that depends on it. Don't
  interrupt a running session for routine messages.
- Before handing work to a native Codex subagent, check its current state with
  `collaboration.list_agents`. Use `collaboration.followup_task` to resume a
  completed agent; use `collaboration.send_message` for an agent still running.
  If it completes before acknowledging the message, resume it with the pending
  task. These are native subagent tools; Paseo workers follow the overseer's
  Paseo CLI instructions.
- When a required capability is missing (subagents, routing, a native
  reviewer, a message channel), report it and continue only independent
  read-only preparation. Never fake delegation or silently take the work over.
- Give each file (including generated files and configuration), each check
  run and each investigation one owner. Overlap work only when it is
  independent and shortens delivery; spare slots are not a reason to invent
  work. Serialize builds and measurements where host contention distorts the
  evidence.

### Model routing

Before launching, resuming or rerouting any agent, read
[references/model-routing.md](references/model-routing.md); it holds the role
table and routing rules.

## Work-item size

Work on one component-level item at a time; a milestone is context, not an
assignment. Group steps only when they share an implementation boundary and
an acceptance check, and keep coupled behavior together rather than splitting
it into fragments that can't be tested alone. Split out independent outcomes,
and settle or separate design decisions that change invariants other steps
rely on before implementing them. Discovery never authorizes the surrounding
milestone.

Out-of-scope issues follow the "by the way" rule in the user's global
instructions. A reviewer keeps out-of-scope findings in a parking lot and
delivers it once, at the milestone boundary.

## Records

Keep one project status document, maintained through `maintain-project-status`,
and the active plan or checklist. Don't create per-chunk reports, acceptance
receipts or hand-off documents, and don't commit raw logs. Inline short
results; summarize bulky output; keep exact files only for a named purpose, in
the one evidence archive `maintain-project-status` describes.

## Publication

- Stage only reviewed, accepted changes; never commit unreviewed work unless a
  standing policy allows it. Push after required checks and review pass,
  unless repository rules or the user say otherwise.
- Other sessions may share the repository: rebase before pushing, commit only
  your files, reconcile shared documents without overwriting others' entries,
  and never amend or force-push work that isn't yours.

## Continuity

- At milestone boundaries, keep a compact checkpoint: goal and boundaries,
  settled decisions and their reasons, current revisions, finding
  dispositions, pending checks, deferrals, active processes and the next
  action. Preserve unresolved findings and disagreements across compaction
  or a replacement agent.
- On resume, recheck the current state instead of repeating broad discovery.
- When a skill changes mid-run, reread it (`reload-skill`) and pass the
  relevant changes to collaborators before affected work continues.

## Workspace and cleanup

- Put worktrees in sibling directories or where the harness manages them,
  never in `/tmp`. Never check out old revisions in another agent's working
  tree.
- Never change state in the user's own checkouts or machines destructively,
  such as `git stash`, reset or checkout in a dirty tree. Report the blocker
  and the options instead.
- Tear down what you started: servers and processes by PID, tunnels, browser
  sessions, test data, and settings you changed, restored to their original
  values. Remove only task-owned material, and say what you removed.
- Never discard unpushed commits or uncommitted changes without asking.
