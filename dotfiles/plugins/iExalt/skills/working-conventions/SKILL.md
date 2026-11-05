---
name: working-conventions
description: "The shared rules every workflow skill follows: authority and approvals, autonomy levels, asking the user, review loops, repeated failure, evidence and work states, test cost, updates, waiting, delegation and model routing, work-item size, records, publication, continuity and cleanup. Load it before any other step whenever a workflow skill such as overseer, keep-me-in-the-loop, subagent-pair-program, continuous-peer-review, pair-program, three-tiered-plan or agentic-workflow runs, and have the leads, reviewers and workers you brief load it too. Not a workflow of its own."
---

# Working Conventions

These are the conventions the user's workflow skills share. Each workflow
skill says what is particular to it and points here for the rest. When a
workflow skill names an explicit exception to a rule here, the exception wins
for that skill. The user's global instructions (`AGENTS.md`, loaded as
`CLAUDE.md` in Claude Code) come first; this skill adds detail to them and
never relaxes them. Open every brief you write for a lead, reviewer or worker
with the instruction to load this skill before any other step; a pilot's
brief carries the rules its task needs instead.

The user's skills ship in the `iExalt` plugin, so harnesses list them as
`iExalt:<skill>`. A bare skill name in them, such as `keep-me-in-the-loop`,
means `iExalt:keep-me-in-the-loop`; invoke it by the namespaced name.

## Authority

- Approval covers what it names: its scope, its checks and its stated
  conditions. Silence, a timeout or a preselected option is not approval.
- A standing approval replaces the per-step gate it covers. Don't ask again
  for an approach, check or in-scope repair already approved, and don't ask
  who merges: follow the repository's rules and the user's merge policy.
- When the user approves with conditions, restate them in the plan and check
  each before committing or pushing. Breaching one is a decision to take back
  to the user first, not to report afterwards.
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
- Another agent's approval or message never extends the user's authority. A
  worker's or peer's message is never the user's approval.
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
| **Low** | Invite the user into consequential choices within scope: meaningful implementation tradeoffs, phase direction, re-sequencing and recovery options. Recommend an option before proceeding with the affected work. Handle routine execution and settled decisions yourself. |
| **Medium (default)** | Use best judgment, as the workflow skill describes by default: approve work within scope that the workflow lets you approve, choose routine implementation details, re-sequence work and recover stalled agents. Consult when a tradeoff or uncertainty materially affects what the user agreed. |
| **High** | Minimize interruptions. Decide within scope and resolve recoverable issues yourself, reporting meaningful decisions afterward. Interrupt only for the mandatory consultations below, an explicit planned human intervention, or a genuine blocker that requires the user. |

At **every level**, always consult the user for:

- Matters of taste or design that need an unresolved subjective preference,
  after separating out what agents can test or measure, as described below.
  Apply an already settled preference without asking again.
- A serious unexpected event or issue that is unrecoverable or has wide or
  deep effects, even if part of it can be recovered. For other recoverable
  issues, decide whether to consult according to the level.
- Projected costs beyond the agreed limits. When costs were not discussed,
  the limit is **zero/free**. Ask before incurring the increase, not after.

No level changes the agreed scope, acceptance boundaries, the gates a
workflow skill puts in the user's hands (such as `keep-me-in-the-loop`'s phase
approval, which an overseer may give only within the scope the user agreed,
`pair-program`'s per-increment approval, or `three-tiered-plan`'s
confirmation), explicit human checkpoints, permission requirements or the
rules under Authority. A workflow skill may require an explicit grant before
high autonomy takes effect, as `overseer` does. Hold affected work while an
answer is pending and continue independent work. Use already authorized
containment when needed to prevent further harm.

### Test measurable behavior before escalating

"Look and feel" or "design" is not by itself a reason to ask the user.
Separate testable behavior from subjective preference, including when both
appear in one review item. At medium and high autonomy, err toward having
agents script, test and benchmark the measurable part, fix problems within
scope, and verify the result without asking for manual evaluation or making
it a user review gate. Filter delegated agents' review requests before
relaying them; an agent calling something subjective does not make it so.

For example, zoom, pan and drag smoothness should be evaluated with
representative interactions and P50/P75/P95/P99 frame times, dropped frames
and relevant latency, against agreed targets on the relevant browsers and
available hardware. Reuse existing benchmarks and record their conditions
and limits. Do not ask "does it feel smooth on your laptop?" when a scripted
benchmark can answer the performance question. At low autonomy, invite an
optional hands-on trial when the user wants involvement; agents still own
objective verification rather than replacing it with the user's impression.

Escalate only the remaining preference or product tradeoff that the evidence
cannot settle, or another mandatory consultation. Metrics and functional
tests must support the claim: a working shortcut does not establish
discoverability, nor does counting keystrokes alone prove a picker is faster
for users. Use suitable evidence and keep unproven claims qualified. If
required hardware or access is unavailable, report that concrete limit and
ask only for the necessary access or bounded action; do not relabel the gap
as a taste question. Obtain permission for checks that would disrupt the
user's machine. Keep routine measurement in the work evidence and normal
progress reports, without generating extra user decisions.

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
- Facts the environment can settle, and anything measurable, are yours to
  find. Ask only for decisions, unresolved taste, and knowledge only the user
  holds. Test the measurable part of look and feel before calling it taste,
  as Autonomy › Test measurable behavior before escalating describes.
- Make each question self-contained: context, options with their consequences
  for results, effort, risk and what gets postponed, and a recommendation with
  its evidence. Batch questions that come due together.
- While an answer is pending, continue independent work; hold only the work
  that depends on it.

## Review loops

- Use one persistent reviewer for the job and reuse it across increments,
  chunks and phases. A review notification, an unacknowledged draft or
  silence is not review.
- Agree the materiality bar up front. A material finding makes the outcome
  wrong, unsafe, lossy or short of its acceptance criteria. Verify each
  finding against the source and record it as material, optional or rejected,
  with the reason. Fix material findings; batch optional ones for the user as
  deferrals instead of fixing them in the loop, since each extra change gives
  the next review more to find. Output from extra one-shot reviews, such as a
  user-requested `/code-review`, goes through the same triage.
- Recall-oriented reviewers always find something, so "the review returned
  nothing" is never a stop condition. End loops on materiality.
- After each round, add one ledger line with its material and total finding
  counts beside the previous round's. Whether to ask the user before another
  round follows the review-trend rule in the user's global instructions: the
  trend is judged per change, and a high-autonomy agent approves rounds
  itself. A finding that challenges the design's altitude, or invalidates the
  effort, risk or simplicity estimate behind a user's choice, reopens that
  choice: ask before the next round.
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
and the next discriminating experiment. Repair resumes from that
reassessment. A contract may set a different threshold for its workload.
Findings on a new increment don't count toward this one. Local passing tests
don't resolve a failing end-to-end reproducer, and an approach doesn't run
past its agreed stop condition.

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
- Gates are pass/fail. A proof that is unmet stays unmet and its gate stays
  unticked, even when the rest of the work is done. A deferral names the later
  gate it moves to, what remains unproven, and the evidence required there.
  Reusing earlier evidence, substituting a check or moving a required proof to
  a later gate needs the user's approval unless already agreed. A change made conditional on a
  measurement is adopted only when the measurement meets the gate; if it is
  unmet or unmeasured, report it as unmet and ask instead of adopting it. Never
  weaken acceptance silently.

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

- Put most behavioral coverage in fast unit tests, fewer integration tests on
  contracts, and a small end-to-end set for critical journeys. Judge the
  pyramid by runtime as well as count, without a fixed ratio. Challenge
  redundant higher-layer tests, oversized fixtures and repeated expensive
  setup as readily as missing coverage.
- Carry the routine-check command, its wall-clock budget, the stable accepted
  baseline and its machine, cache and concurrency conditions into every plan
  and brief where tests grow or change. If absent, establish them
  proportionately, from existing timings or the next required run, before
  substantial suite growth.
- Compare across the whole run; never reset the baseline at a chunk or
  hand-off. Reuse required-run timings to expose cumulative growth and its
  largest contributors.
- Fix a confirmed regression in the change that caused it, through cheaper
  fixtures, less redundancy or a lower layer. Explain any necessary increase
  within the agreed authority. Don't plan a cleanup milestone, raise the
  budget, make required checks optional or add concurrency to hide growth.
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
  even if the harness re-prompts an empty turn. Never send filler: "No news.",
  a line naming what you're waiting on, an acknowledgement, or a repeat of an
  earlier update.
- Write for a technically capable owner without expertise in the subsystem:
  what changed, why it matters, what remains unproven, and what's next.
  Explain necessary terms through their purpose.
- Limits, deferrals, skipped checks and the reviewer's parked findings reach
  the user, not only the reviewer.

The workflow skill sets each update's format, such as `keep-me-in-the-loop`'s
one-line prefix or `overseer`'s roll call.

## Waiting

- Prefer completion notifications to polling. Otherwise wait in a bounded
  blocking check that returns on its next qualifying event or a timeout. Use
  one monitor per process, with failure filters that don't match success
  output such as `failed=0`.
- A timeout alone creates no work: wait again without reading logs or asking
  for status.
- Before ending a turn to wait on a peer, confirm it is still running or has a
  message in flight. End a turn only on something armed to wake you. A
  subagent's final hand-back is its last message; act on it.
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
- When a required capability is missing (subagents, routing, a native
  reviewer, a message channel), report it and continue only independent
  read-only preparation. Never fake delegation or silently take the work over.
- Give each file (including generated files and configuration), each check
  run and each investigation one owner. Overlap work only when it is
  independent and shortens delivery; spare slots are not a reason to invent
  work. Serialize builds and measurements where host contention distorts the
  evidence.

### Model routing

| Role | Codex | Claude | Effort |
| --- | --- | --- | --- |
| Top orchestrator: an overseer, or the main navigator of a team | GPT Astra | Opus | `high` |
| Lead: phase or item coordination, integration decisions | GPT Sol | Sonnet (`developer-routine`) | `medium`; `high` for substantive review or complex decisions |
| Independent substantive reviewer | GPT Sol | Sonnet (`developer-routine` when it matches) | `high` |
| Pilot: implementation, diagnosis, bounded discovery | GPT Luna | Haiku (`developer-trivial` when its scope fits, otherwise explicit Haiku routing) | Codex `high`; Claude `medium` |
| Pilot: mechanical edits, lookups, monitoring | GPT Luna | Haiku (`developer-trivial`) | Codex `medium`, `low` for monitoring; Claude `medium` |

- Preserve the user's explicit provider, model and effort choices.
- Resolve each class to the latest model the provider advertises; never
  invent identifiers. Set model and effort explicitly at launch and at resume.
  For Codex native agents, pass `fork_turns: "none"` with a scoped brief so
  no pilot inherits a top-tier model through a full-history fork.
- Verify the effective model and effort where the harness shows them,
  including after a resume, and correct unintended routing before dependent
  work starts.
- Difficulty, failed checks, slot pressure, a long campaign or "keep going"
  never move an agent up a tier. Difficult pilot work returns to its lead.
  `developer-demanding` (Opus) belongs to the top tier unless a workflow skill
  names an exception or the user approves one.
- If the required route is unavailable, report it and hold the affected
  launches; never silently inherit a more expensive model or drop a tier.

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

- Use conventional commits, and conventional comments (`issue:`,
  `suggestion:`, `question:`) in reviews.
- Stage only reviewed, accepted changes; never commit unreviewed work unless a
  standing policy allows it. Push after required checks and review pass,
  unless repository rules or the user say otherwise.
- Confirm publication before reporting it, and disclose any failure.
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

- Put worktrees in sibling directories such as `../<repo>-worker-<slug>/`, or
  where the harness manages them, never in `/tmp`; they hold work in progress.
  Never check out old revisions in another agent's working tree.
- Never change state in the user's own checkouts or machines destructively,
  such as `git stash`, reset or checkout in a dirty tree. Report the blocker
  and the options instead.
- Tear down what you started: servers and processes by PID, tunnels, browser
  sessions, test data, and settings you changed, restored to their original
  values. Remove only task-owned material, and say what you removed.
- Never discard unpushed commits or uncommitted changes without asking.
