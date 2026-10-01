---
name: peer-review-loop
description: Repeatedly peer-review and fix a plan, code change, patch, branch, or pull request using a persistent reviewer from another provider until the main agent and reviewer agree there are no outstanding findings. Use when the user asks for a peer-review loop, iterative review and repair, or to fix review findings and re-review until clean. For a review without the automatic repair loop, use peer-review.
---

# Peer Review Loop

Use a facilitator subagent to conduct a read-only dialogue with a persistent
review-agent session. The main agent owns implementation and verification;
the facilitator and reviewer remain read-only. Invoking this skill authorizes
in-scope fixes and repeat reviews without asking whether to implement each
agreed finding. Keep a visible checklist of review, fixes, verification, and
re-review. Preserve the original task scope and acceptance criteria.

If you are already the downstream reviewer, review the artifact directly and
return findings; do not invoke peer-review or peer-review-loop, start this
workflow, or delegate another peer review.

## Workflow

1. Identify the artifact, authoring provider, repository or working directory,
   acceptance criteria, and relevant verification evidence.
   If an artifact is outside the working directory, record its parent as an
   additional read directory.
2. Select the review provider:
   - Codex-authored artifact: use Claude Code.
   - Claude Code-authored artifact: use Codex.
   - Other or unknown author: use Codex.
   Never select the authoring provider when the author is Codex or Claude Code.
3. Spawn one facilitator subagent. Tell it that it is not the reviewer and must
   use `scripts/provider_turn.py` to converse with the selected review provider.
   Give it the artifact location and raw task context, but do not preload it
   with expected findings.
4. Have the facilitator list prior sessions for that provider:

   ```bash
   mise exec -- python scripts/provider_turn.py list \
     --provider claude \
     --cwd /absolute/workspace
   ```

5. Reuse a session only when its artifact, feature, bug, or PR stack establishes
   continuity. Sharing a repository is insufficient. Explain the match with
   `--reuse-reason`; when relevance is uncertain, start a new session. If the
   provider reports that a session is unavailable, start a new one with the raw
   artifact and essential context. Preserve the old registry entry; do not
   treat authentication or other execution failures as a reason to retry new.
6. Conduct the dialogue in review rounds. Use `turn --session-id ID` to resume
   or `turn --new` when no relevant, available session exists. Send prompts on stdin.
   Pass each external artifact parent with `--add-dir /absolute/path`.
7. Require the facilitator to return a self-contained consensus record, session
   ID, and turn ID to the parent. Record disposition counts with `record` below.
   Do not let the facilitator edit the artifact.
8. The main agent resolves accepted findings, updates the plan or code, and
   runs relevant verification. Do not end the task with a list of fixes to make.
   Distinguish accepted findings, implemented fixes, and verified fixes; update
   recorded counts when those states change.
9. Send the revised artifact and the change/verification evidence to the same
   facilitator and provider session. Follow the repair loop below until both
   the main agent and reviewer agree there are no outstanding findings.

## Review Rounds

Before dispatch, read [the shared review protocol](references/review-protocol.md)
and give it to the facilitator. It governs discovery coverage, agreed repair
criteria, focused follow-up review, finding classification, design reassessment
after two incomplete repair reviews, and explicit closure accounting. Include
its applicable instructions in provider prompts; do not assume the external
reviewer has loaded this skill or can access the reference.

Start with a complete independent discovery pass and reconcile the batch of
findings. The facilitator may return an agreed record without another call to
restate it. That completes a review round, not proof that accepted fixes were
implemented or verified. Preserve accepted, rejected, and unresolved dispositions
separately from implementation and reviewer closure.

## Repair Loop and Completion

After each review round:

1. Reconcile findings using the shared protocol. Before complex repairs,
   agree on the invariant, boundaries, and counterexample batch. Keep stable
   IDs, dispositions, repair attempts, verification evidence, and closure.
   Send the main agent's objections back through the facilitator;
   unilateral rejection does not establish agreement.
2. Implement agreed fixes in the main agent, including in-scope findings found
   while fixing or testing. Preserve unrelated work. Verify the affected
   behavior; repair new failures before resubmitting when feasible. For a plan,
   revise and validate the plan rather than implementing the planned project.
3. Resubmit the current artifact for independent inspection, with the original
   review scope, a diff or exact revised content, a per-finding account of
   changes, verification results and limits, and any newly discovered issues.
   Identify the revision being reviewed; HEAD plus `+dirty` alone cannot
   distinguish successive uncommitted revisions. Supply the actual current
   diff/content and a distinct round identifier through `--artifact-revision`.
   Keep the artifact stable during the review. If it changes, resubmit it.
4. Ask the reviewer to check agreed closure criteria, the repair delta and
   affected dependencies, and introduced regressions. Follow the shared
   protocol for justified broader inspection and later-finding classification.
   After two incomplete repair reviews of one finding, reassess its design
   before editing again. Reconcile and fix findings, then repeat in the same
   session; do not restart broad discovery on every revision.
5. Finish successfully only when the reviewer explicitly reports no outstanding
   findings on the latest artifact and the main agent independently agrees.
   All accepted findings must be implemented and verified to the extent the
   task requires; unresolved findings or required failing checks block success.
   Rejected or optional findings need an agreed disposition and rationale;
   do not silently relabel a required fix to reach a clean result. A clean
   first review can finish immediately if the main agent agrees.

There is no fixed cap on productive repair cycles. If the same disagreement or
failed repair persists across three substantive attempts without new evidence
or progress, report the remaining blocker and mark the loop incomplete rather
than repeating unchanged work or manufacturing agreement. Also report incomplete
when a provider is unavailable, a necessary user decision or permission is
missing, or the user stops the work. Continue independent in-scope work where
possible. The skill does not itself authorize commits, pushes, deployment,
destructive actions, or expansion of the task.

Keep counts attached to the turn that introduced the findings; do not count
old findings as new in every round. Update that turn after implementation and
verification. Keep reopened finding links and reviewer closure in the consensus
record, since the registry counts do not encode those relationships.

The final response states whether agreement was reached, summarizes changes and
verification limits, identifies the final review session/turn and artifact,
and lists any blockers if incomplete. Do not claim runtime verification from
review agreement alone.

## Provider Turns

The helper defaults to GPT-6 Astra (`gpt-6-astra`) with `medium` reasoning
effort for Codex and Opus 5.5 (`claude-opus-5-5`) with `high` effort for Claude
Code. These defaults apply to both new and resumed sessions. Use `--model`
and `--effort` on `turn` when the user requests an override.

Every turn receives a direct-review instruction that prohibits recursive
peer-review delegation and requires findings in the final response. Check the
returned content: a successful provider call is not proof of a complete review.
If it only references a plan or promises future work, request a self-contained
record in the same session before accepting the review.

Resolve this skill directory before invoking the helper. Its `scripts` directory
links to `../peer-review/scripts`, sharing the implementation, regression tests,
and registry with peer-review. Its `references` directory likewise links to
`../peer-review/references`, keeping the review protocol identical. Install both
sibling skill directories together; no registry migration or copy is needed.
Typical commands:

```bash
# Start a new Claude Code review session.
cat prompt.txt | mise exec -- python scripts/provider_turn.py turn \
  --provider claude \
  --new \
  --topic "repository: feature or PR" \
  --artifact-kind code \
  --cwd /absolute/workspace \
  --add-dir /absolute/external-artifacts

# Resume that Claude Code session.
cat prompt.txt | mise exec -- python scripts/provider_turn.py turn \
  --provider claude \
  --session-id SESSION_UUID \
  --reuse-reason "Recheck fixes for the same PR" \
  --topic "repository: feature or PR" \
  --artifact-kind code \
  --cwd /absolute/workspace

# Codex uses the same interface.
cat prompt.txt | mise exec -- python scripts/provider_turn.py turn \
  --provider codex \
  --session-id SESSION_UUID \
  --reuse-reason "Reconcile findings for the same plan" \
  --topic "repository: feature or PR" \
  --artifact-kind plan \
  --cwd /absolute/workspace
```

The helper stores session metadata under
`${CODEX_HOME:-~/.codex}/state/peer-review/sessions.json`. Treat session IDs as
opaque. Never hand-edit provider conversation files. Concurrent registry updates
are locked; provider calls run outside the lock.

The registry also stores compact per-turn records: status, timing, model/effort,
artifact revision, session selection, and failure type. It does not store prompt,
response, or error bodies. Use `--artifact-revision` for an external artifact or
an identifiable working-tree snapshot; the default Git HEAD plus `+dirty` marker
is only a checkout hint, not an exact snapshot. Failed calls are recorded but do
not create successful session entries. Interrupted processes may leave no record.

After reconciliation, record counts for that turn's findings (not cumulative
session totals); keep finding IDs, rationale, and evidence in the consensus:

```bash
mise exec -- python scripts/provider_turn.py record --turn-id TURN_UUID \
  --accepted 2 --rejected 1 --unresolved 0 --implemented 0 --verified 0
```

Repeat `record` for the same turn after fixes. `implemented` counts accepted
findings whose corrections were applied; `verified` counts those corrections
with relevant verification evidence. Keep findings on their first-seen turn;
reopened findings are not new findings. The shared protocol's consensus ledger
tracks open/reopened/closed IDs; the registry counts alone cannot establish
closure. Missing counts mean unrecorded, not zero.
For helper changes, run `mise exec -- python -B -m unittest discover -s
scripts -p 'test_*.py'` from this skill directory, then skill-creator validation.

## Facilitator Prompt

Give the subagent a prompt with this structure:

```text
Act as the facilitator, not the reviewer. Use the peer-review-loop skill's
scripts/provider_turn.py to converse with <provider> in read-only mode.

Artifact: <path, diff range, PR, or complete plan>
Original task: <task and acceptance criteria>
Workspace: <absolute path>
Authoring provider: <provider>

Inspect the registry; reuse only a session for the same artifact or workstream,
and give --reuse-reason. A repository match alone is insufficient. Otherwise
start new. Follow the supplied shared review protocol. Complete discovery
coverage and batch findings before returning; verify claims against source.
Agree on invariants, boundaries, and counterexamples before complex repairs.
Use focused repair verification for follow-ups, classify later findings, and
reassess the design after two incomplete repair reviews of the same finding.
Do not edit files. Record disposition counts and return the self-contained
consensus: coverage, findings and classifications, closure criteria, open/reopened/
closed/new IDs, repair attempt counts, session/turn/revision IDs, and verification
limits. Do not substitute a plan-file reference or zero new findings for closure.

The main agent will implement agreed fixes and send revised artifacts back to
you. Resume this same provider session for each revision. Give the reviewer the
current artifact/diff, per-finding changes, verification evidence, and new issues.
Require focused verification of closure criteria, affected dependencies, and
regressions, with reasons for broader inspection. Return explicit closure or
remaining findings for each revised artifact, even when there are no new IDs.
Do not declare the whole loop complete on the basis of an agreed list of fixes;
the reviewer and main agent must agree the latest artifact has no outstanding
findings. Do not edit files or start a nested repair loop.
```

## Guardrails

- Keep provider sessions read-only. The helper starts Claude Code in plan mode
  and Codex in a read-only sandbox, including resumed sessions.
- Pass repository paths, diffs, plans, and test output instead of paraphrasing
  when practical.
- Remove credentials, tokens, private keys, and unrelated sensitive context
  before sending prompts.
- Preserve reviewer independence in the first round. Do not include the
  authoring agent's defense or preferred answer until the challenge round.
- Treat severity as evidence-based. Reject style-only findings unless they
  violate an explicit repository rule or materially reduce maintainability.
- Propagate only accepted findings automatically. Surface unresolved findings
  to the user when they affect correctness, scope, security, or architecture.
- If subagent tools are unavailable, use the parent agent as facilitator while
  still using the external provider session. State this fallback explicitly.
- If the selected provider CLI is unavailable or unauthenticated, report the
  blocker; do not silently substitute the authoring provider.
