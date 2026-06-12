---
name: peer-review
description: Run a critical peer review of a plan, code change, patch, branch, or pull request through a persistent session with an agent from another provider, then reconcile findings and propagate accepted changes back to the authoring agent. Use when the user asks for peer review, cross-provider review, second-agent validation, adversarial review, plan review, code review, or PR review. Select Claude Code when Codex authored the artifact, select Codex when Claude Code authored it, and default to Codex when neither provider authored it or authorship is unknown.
---

# Peer Review

Use a facilitator subagent to conduct a read-only dialogue with a persistent
review-agent session. Keep the authoring agent responsible for integrating the
consensus.

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

5. Reuse the most relevant session when the new artifact belongs to the same
   feature, bug, PR stack, repository workstream, or direct continuation. When
   uncertain, reuse it. Start a new session only when the topic is completely
   different. Do not delete old sessions merely because a new one is needed.
6. Conduct the dialogue in review rounds. Use `turn --session-id ID` to resume
   or `turn --new` for a completely different topic. Send prompts on stdin.
   Pass each external artifact parent with `--add-dir /absolute/path`.
7. Require the facilitator to return the consensus record and session ID to the
   parent agent. Do not let the facilitator edit the artifact.
8. Integrate accepted changes in the parent agent, update the plan or code,
   rerun relevant verification, and summarize rejected or unresolved findings.

## Review Rounds

Start with an independent review, then run additional rounds only when needed:

1. **Independent review**: Ask the reviewer to inspect the raw artifact and
   source evidence. Require findings ordered by severity, concrete evidence,
   impact, and a proposed correction. For a plan, check completeness,
   sequencing, assumptions, rollback, and verification. For code or a PR, check
   correctness, regressions, security, tests, and repository conventions.
2. **Challenge when needed**: Have the facilitator verify each finding against
   the actual artifact. Ask the reviewer to withdraw unsupported findings,
   answer objections, and distinguish required fixes from optional
   improvements.
3. **Reconciliation when needed**: Produce a final disposition for every
   finding: `accepted`, `rejected`, or `unresolved`, with a short rationale and
   the concrete change for accepted findings.

The facilitator may finish after the independent review when it verifies the
findings and agrees with the reviewer, when there are no findings, or when all
suggested changes are minor or optional. In that case, return the consensus
record directly without asking the reviewer to restate it.

Run challenge or reconciliation rounds only when a finding is disputed,
unsupported, unclear, or material to correctness, security, scope, architecture,
or user-visible behavior. Continue the same provider session until the agents
reach a stable disposition. Do not manufacture agreement. After three
substantive rounds without convergence, return the remaining disagreement to
the parent agent as `unresolved`.

## Provider Turns

Resolve this skill directory before invoking the helper. Typical commands:

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
  --topic "repository: feature or PR" \
  --artifact-kind code \
  --cwd /absolute/workspace

# Codex uses the same interface.
cat prompt.txt | mise exec -- python scripts/provider_turn.py turn \
  --provider codex \
  --session-id SESSION_UUID \
  --topic "repository: feature or PR" \
  --artifact-kind plan \
  --cwd /absolute/workspace
```

The helper stores session metadata under
`${CODEX_HOME:-~/.codex}/state/peer-review/sessions.json`. Treat session IDs as
opaque. Never hand-edit provider conversation files.

## Facilitator Prompt

Give the subagent a prompt with this structure:

```text
Act as the facilitator, not the reviewer. Use the peer-review skill's
scripts/provider_turn.py to converse with <provider> in read-only mode.

Artifact: <path, diff range, PR, or complete plan>
Original task: <task and acceptance criteria>
Workspace: <absolute path>
Authoring provider: <provider>

Inspect the prior session registry and reuse a related reviewer session unless
this topic is completely different. Run an independent review, verify its
claims against source, and finish after that round if the findings are agreed or
minor. Use challenge and reconciliation rounds only for disputed, unclear, or
material findings. Do not edit files. Return: review provider, session ID,
findings with final dispositions, consensus changes, unresolved disagreements,
and verification recommendations.
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
