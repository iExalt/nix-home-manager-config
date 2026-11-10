---
name: maintain-project-status
description: "Create or maintain an evidence-backed project status document between strategic plans and implementation checklists. Use to reconstruct progress from plans, Git history, source, tests and artifacts; set outcome gates and dependencies; recommend the next sequence; track deferrals and risks; or audit unsupported completion claims."
---

# Maintain project status

Keep a durable project-status record that bridges governing strategy and
detailed implementation tasks, concise enough to guide current execution
without becoming a duplicate checklist.

When the project already uses a tracker as its canonical progress record,
apply this skill's evidence, boundary, dependency and update semantics there.
Do not create a parallel status document or export a duplicate checklist.
For Acyclic, read [../working-conventions/references/acyclic.md](../working-conventions/references/acyclic.md).
The document/template instructions below apply to document-based projects;
tracker-backed projects use existing notes and fields without inventing states.

Start a new document from
[assets/status-document-template.md](assets/status-document-template.md).
Adapt headings to the project, but preserve the evidence, boundary, dependency,
and update semantics.

## Core invariants

- Treat governing plans and contracts as authoritative for intent and milestone
  gates.
- Treat the detailed checklist as authoritative for exhaustive task coverage.
- Treat current source, tests, measurements, and artifacts as authoritative for
  present behavior.
- Use Git history to reconstruct when and why work landed, not as the sole
  proof that the current tree still satisfies a claim.
- Never infer milestone completion from partial implementation, checked
  subtasks, code existence, or a passing subset of tests.

## Documentation and evidence retention

For document-based projects, keep one project-wide status document and the active implementation plan,
which may hold its checklist. Don't create per-item reports, acceptance
receipts, benchmark writeups or hand-off documents; add a document only for a
distinct ongoing reader need the existing ones can't serve. Component READMEs
and `docs` directories hold durable usage, interface and design knowledge, not
run logs.

Retain the smallest useful representation:

- Inline short results and small tables, with a few decisive receipts and the
  conditions and limits needed to read them.
- Put moderately larger tables in an appendix to the same document, never raw
  logs or unbounded datasets.
- For larger output, keep the conclusion and the reproduction command or
  source reference, not the raw output. Say when exact raw results weren't
  retained, and never link disposable local files as durable evidence.
- Only when an explicit requirement or named future use needs exact files,
  consolidate them into the one benchmark/evidence `.tar.zstd` archive,
  updating the existing archive without losing members. Never keep one archive
  per run, or both an archive and its expanded contents. State in the status
  document why it's retained, what it holds and how to extract it, and check
  it's readable and complete before removing task-owned originals.

Keep reusable tests, benchmark harnesses and required fixtures as normal
source files; never hide source in the archive or weaken checks to shrink
evidence. Remove only task-owned disposable material, and don't turn a status
update into a repository-wide cleanup.

## Status model

Track workflow status separately from evidence state.

Workflow status is `complete` (the full exit condition has current evidence),
`active`, `next` (the highest-priority unopened outcome), `planned`, `blocked`
(named prerequisites are missing) or `later` (outside the current planning
horizon).

Evidence state:

- `designed`: a decision or contract exists, but implementation is not proven;
- `implemented`: relevant code or artifacts exist, but the required exit
  verification is incomplete;
- `verified`: the stated exit condition has current, reproducible evidence.

Use `complete` only with `verified`. An active goal may contain a mix of
designed, implemented, and verified deliverables; describe that mix instead of
promoting the whole goal.

## Workflow

### 1. Establish the document hierarchy

Identify the governing plans, contracts, milestone definitions and decision
records; the exhaustive checklist or issue tracker; the status document's path
and readers; and the baseline revision, relevant branches and worktree state.

When updating, read the existing status document first, then inspect its
linked sources and confirm the hierarchy is still accurate.

### 2. Inspect the evidence surface

Inspect before writing: `git status` with staged, unstaged and untracked
changes; the relevant Git log ranges and file history; current modules,
interfaces, schemas, configuration and generated outputs; scoped tests and
correctness corpora; benchmark definitions, retained results and artifacts;
and milestone exit gates, checked checklist items, dependencies and open
decisions. Prefer repository-managed tools and commands, and check each claim
against the current tree, not only its history.

Preserve unrelated worktree changes, and don't attribute pre-existing
uncommitted changes to a commit. If evidence is worktree-only, say so.

### 3. Reconstruct accomplishments

Group accomplishments by coherent outcome, not by commit chronology. For each
group:

- state what now exists or is proven;
- name the relevant concrete evidence, such as test names, commands and measured
  results, modules, or commit IDs; reference retained artifacts or hashes only
  when they serve the claim under the retention policy above;
- distinguish implementation evidence from verification evidence;
- describe a design as a design, not as implemented behavior.

Move an outcome into accomplishments only when the wording is no stronger than
its evidence.

### 4. State the current boundary

Write a direct list of what is not complete. Include:

- milestone gates not yet passed;
- missing correctness, measurement, reproducibility, or integration evidence;
- implemented work that remains unverified;
- decisions that remain provisional;
- downstream systems that have not started.

Use explicit negatives. Avoid vague phrases such as "mostly done" or
"essentially complete."

### 5. Define intermediate goals

Insert outcome gates between strategic milestones and low-level tasks. Give each
goal:

- a stable ID and outcome-oriented title;
- workflow status and evidence state;
- deliverables;
- dependencies expressed as goal IDs or external evidence prerequisites;
- exit conditions that can be evaluated;
- one decision owner and one exit-condition owner;
- evidence when complete or partially verified.

Size each goal to a meaningful outcome that is still small enough to unblock
sequencing; it normally combines related checklist tasks that produce one
reviewable capability, evidence package, or decision.

### 6. Audit dependencies and claims

Before recommending work, check:

1. **Dependency cycles:** Build a directed graph from each goal to its
   prerequisites. A valid next goal must have the evidence from all its
   prerequisites. Report a cycle only when you find one, naming its goal IDs,
   and resolve it by splitting out a bounded spike, shared evidence
   prerequisite, or explicit decision gate; do not hide the cycle by changing
   labels. If no goal is ready and there is no cycle, report each unmet
   external prerequisite or pending decision and its owner instead.
2. **Exit ownership conflicts:** Map every exit condition and final decision to
   one owning goal. If two goals claim the same final selection or gate,
   designate one owner and make the other an evidence contributor.
3. **Unsupported completion:** For every `complete` or `verified` claim, locate
   current evidence for every exit-condition clause. Downgrade the claim when
   any clause is missing.
4. **Premature starts:** For every `active` goal, verify its evidence
   prerequisites. Mark it blocked when prerequisites are absent. Allow only
   explicitly bounded, discardable spikes to proceed early, and state the limit
   and the later decision gate.
5. **Checklist drift:** Compare status claims with checked tasks and milestone
   exit gates. Checked subtasks may support an accomplishment but cannot
   override an incomplete exit gate.

### 7. Recommend the next sequence

Normally recommend three to seven concrete steps, ordered by dependency and
evidence production, not convenience. Explain any bounded parallelism or early
spike that intentionally crosses a milestone boundary.

List explicitly deferred work separately, naming the missing prerequisite or
intermediate exit condition for each deferred group.

### 8. Track risks without duplicating tasks

Track only active risks, provisional decisions, and evidence gaps that can
change sequencing or invalidate a claim. For each risk, state:

- the observed evidence or uncertainty;
- the consequence;
- mitigation or next evidence needed;
- decision owner when applicable.

Remove resolved risks or record their resolution in the progress log. Leave
exhaustive implementation tasks in the checklist.

### 9. Write or update the document

When creating:

- establish the initial baseline revision and date;
- populate applicable template sections; omit the optional appendix when unused;
- link to the governing plan and checklist;
- add reciprocal relative links from those documents when the status document
  is durable and belongs in their normal navigation.

When updating:

- inspect changes since the recorded baseline plus current worktree changes;
- update the snapshot and current boundary;
- move only newly evidenced outcomes into accomplishments;
- revise goal status, dependencies, and decisions;
- replace the recommended sequence and active risk set;
- append a concise dated progress-log entry for the meaningful outcome, not each
  agent exchange or validation run; link an existing result instead of duplicating it;
- preserve prior log entries unless correcting a documented factual error.

Update after a meaningful implementation increment, changed decision, measured
result, newly discovered blocker, or invalidated claim, not for inconsequential
edits.

### 10. Verify before finishing

Verify:

- Markdown formatting with the repository's configured formatter or linter;
- every local link and referenced artifact path;
- commit IDs, baseline revision, test names, module names, counts, hashes, and
  measurement claims;
- relevant scoped tests and benchmark/result validation;
- `git diff --check` and the final worktree diff.

Record exact commands and results in the handoff or progress log when useful.
If a relevant test or factual claim cannot be verified, say so and do not
classify the affected outcome as verified.

## Output standard

Finish with:

- the canonical record: the tracker item(s) or the status-document path;
- the baseline and evidence sources inspected;
- the current boundary and recommended next sequence;
- verification performed and any unverified claims;
- any reciprocal plan or checklist links added.
