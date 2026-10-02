---
name: peer-review
description: Run a critical peer review of a plan, code change, patch, branch, or pull request through a persistent session with an agent from another provider, then reconcile findings and propagate accepted changes back to the authoring agent. Use when the user asks for peer review, cross-provider review, second-agent validation, adversarial review, plan review, code review, or PR review. Select Claude Code when Codex authored the artifact, select Codex when Claude Code authored it, and default to Codex when neither provider authored it or authorship is unknown.
---

# Peer Review

Use a facilitator subagent to conduct a read-only dialogue with a persistent
review-agent session. Keep the authoring agent responsible for integrating the
consensus. This skill does not automatically repeat repair/review cycles until
clean; use peer-review-loop for that. Apply the shared follow-up protocol when
a revised artifact is submitted. Keep a visible checklist when implementing.

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

5. Start a fresh reviewer session for each independently scoped milestone or
   review campaign. A shared repository, roadmap, feature, or PR stack alone
   does not justify carrying an old conversation forward. Carry only a compact
   summary of relevant prior decisions, constraints, and evidence references.
   Reuse the session for discussion and repair verification within this campaign;
   explain that continuity with `--reuse-reason`. If the session is unavailable,
   start new with the artifact and compact ledger, preserving the old entry.
   Authentication or execution failures alone do not justify a new session.
6. Use `turn --new` for discovery of a new campaign and `turn --session-id ID`
   for its follow-ups. Pass `--stage discovery`, `--stage discussion`, or
   `--stage verification` as appropriate. Send prompts on stdin.
   Pass each external artifact parent with `--add-dir /absolute/path`.
7. Require the facilitator to return a self-contained consensus record, session
   ID, and turn ID to the parent. Record disposition counts with `record` below.
   Do not let the facilitator edit the artifact.
8. Integrate accepted changes in the parent agent, update the plan or code,
   rerun relevant verification, and summarize rejected or unresolved findings.
   Distinguish accepted findings, implemented fixes, and verified fixes; update
   the recorded counts when those states change.

## Review Rounds

Before dispatch, read [the shared review protocol](references/review-protocol.md)
and give it to the facilitator. It governs discovery coverage, repair
proposals and facilitator challenges, agreed criteria, focused follow-up review,
finding classification, design reassessment
after two incomplete repair reviews, reliable execution of long provider turns,
and explicit closure accounting. Include
its applicable instructions in provider prompts; do not assume the external
reviewer has loaded this skill or can access the reference.

Start with a complete independent discovery pass and reconcile the batch of
findings. The facilitator may return an agreed record without another call to
restate it. That completes a review round, not proof that accepted fixes were
implemented or verified. Preserve accepted, rejected, and unresolved dispositions
separately from implementation and reviewer closure.

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

Resolve this skill directory before invoking the helper. Typical commands:

```bash
# Start a new Claude Code review session.
cat prompt.txt | mise exec -- python scripts/provider_turn.py turn \
  --provider claude \
  --new \
  --stage discovery \
  --topic "repository: feature or PR" \
  --artifact-kind code \
  --cwd /absolute/workspace \
  --add-dir /absolute/external-artifacts

# Resume that Claude Code session.
cat prompt.txt | mise exec -- python scripts/provider_turn.py turn \
  --provider claude \
  --session-id SESSION_UUID \
  --reuse-reason "Recheck fixes for the same PR" \
  --stage verification \
  --topic "repository: feature or PR" \
  --artifact-kind code \
  --cwd /absolute/workspace

# Codex uses the same interface.
cat prompt.txt | mise exec -- python scripts/provider_turn.py turn \
  --provider codex \
  --session-id SESSION_UUID \
  --reuse-reason "Reconcile findings for the same plan" \
  --stage discussion \
  --topic "repository: feature or PR" \
  --artifact-kind plan \
  --cwd /absolute/workspace
```

The helper stores session metadata under
`${CODEX_HOME:-~/.codex}/state/peer-review/sessions.json`. Treat session IDs as
opaque. Never hand-edit provider conversation files. Concurrent registry updates
are locked; provider calls run outside the lock.

The registry also stores compact per-turn records: status, timing, model/effort,
artifact revision, session selection, stage, and failure type. Successful output
also includes these metrics, including elapsed seconds and available provider
usage. Missing provider metrics are null, not zero; see the shared protocol. It does not store prompt,
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
Act as the facilitator, not the reviewer. Use the peer-review skill's
scripts/provider_turn.py to converse with <provider> in read-only mode.

Artifact: <path, diff range, PR, or complete plan>
Original task: <task and acceptance criteria>
Boundaries: <supported configurations, explicit exclusions, unresolved scope decisions>
Verification: <available harnesses, feasible probes, deferred live checks>
Workspace: <absolute path>
Authoring provider: <provider>

Start a fresh session for this independently scoped campaign; reuse only for
its discussion and repairs, with --reuse-reason. Carry relevant prior decisions
in a compact brief rather than resuming an entire roadmap's conversation.
Pass --stage discovery/discussion/verification. Follow the shared protocol's
brief, early scope escalation, and concise response rules. Complete discovery
coverage and batch findings before returning; verify claims against source.
Require actionable repair proposals: a suggested diff for easy fixes, a bounded
sketch and counterexamples for complex ones, with checked versus untested claims.
Challenge proposed remedies as well as findings; accepting a finding does not mean
accepting its fix. Resolve substantive objections with the reviewer in the inner
dialogue, then return the settled proposal for the main agent's acceptance.
Before a complex repair, obtain explicit reviewer agreement on its bounded design, invariants, boundaries,
and counterexamples; facilitator proposals alone are not agreement. Follow the
shared protocol's execution guidance: align helper and outer process deadlines,
retain the execution handle, and resume interrupted work without duplicate reviews.
Use focused repair verification for follow-ups, classify later findings, and
reassess the design after two incomplete repair reviews of the same finding.
Do not edit files. Record disposition counts and return the self-contained
consensus: coverage, findings and classifications, closure criteria, open/reopened/
closed/new IDs, repair attempt counts, session/turn/revision IDs, and verification
limits. Do not substitute a plan-file reference or zero new findings for closure.
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
