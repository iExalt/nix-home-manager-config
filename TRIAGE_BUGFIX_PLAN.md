# Plan: triage-bugfix

Status: implemented and validated; publication is the final execution step. Incident-specific mutations still require their own task authorization.

## Outcome

Create a general skill that guides an agent from a reported failure to an evidence-backed diagnosis, a scoped fix, and practical recommendations to prevent recurrence. It should support both diagnosis-only requests and authorized implementation without inserting unnecessary approval gates.

The skill should improve decisions rather than prescribe a ceremony for every bug. Scale investigation and reporting to impact and uncertainty.

## Basis in prior requests

Three Luna High agents reviewed Claude Code and Codex conversations. Their qualitative sample repeatedly showed these intentions:

- Explain the exact operation that failed and the causal chain, beyond repeating the error message.
- Define success using concrete expected behavior and realistic operating conditions.
- Preserve existing guarantees while changing the implementation or removing unreliable dependencies.
- Consider related failures and previous incidents before declaring the fix complete.
- Distinguish a successful check from proof that the original failure mode is resolved, especially when failures can produce false success.
- Keep prevention economical: protect distinct invariants without accumulating redundant tests or slowing routine development.
- Respect explicit diagnosis-only, pause, and wait-for-other-results instructions.

These are synthesized directions, not universal rules copied from individual incidents. The research excluded TerminalO3 history. Raw conversations and private local history paths do not belong in the installed skill.

## Scope and routing

Proposed description:

> Diagnose reported software or operational failures, develop and verify a scoped fix, and recommend measures to prevent recurrence. Use for bug investigations and root-cause-driven repairs.

Keep normal automatic discovery enabled. Routine feature development, backlog prioritization, and mechanical merge-conflict resolution do not need this workflow unless they involve an actual failure investigation.

The skill must work independently of a particular tracker, infrastructure platform, review skill, or multi-agent setup. Delegation used to research this plan does not become a requirement for future bugfixes.

## Intended guidance

### Frame the issue

Establish observed versus expected behavior, impact, affected versions or environment, and the user's requested scope. Reuse available context and evidence before asking questions. Carry forward existing authorization and explicit stopping points.

### Diagnose the mechanism

Gather evidence and reproduce when practical. Choose checks that distinguish plausible explanations. Separate code defects, configuration, environmental failures, dependencies, and intended lifecycle behavior. Preserve useful diagnostic artifacts when doing so avoids repeated expensive collection.

Explain the causal chain with supporting evidence. Label hypotheses and unresolved links. If evidence is insufficient, identify the next discriminating check instead of inventing certainty. A mitigation may still be useful before the cause is fully established; label it accordingly.

### Develop a scoped fix

Connect the proposed changes to the diagnosed mechanism and explain material tradeoffs. Preserve intended behavior, correctness guarantees, and relevant performance bounds. Distinguish immediate mitigation from durable correction.

For diagnosis-only requests, provide findings and a proposed remedy. For authorized implementation, make and verify the change without a new blanket approval gate. Deployment, destructive actions, and other external mutations retain their existing authorization boundaries. Respect explicit instructions to pause or wait for related results.

### Verify the outcome

Exercise the original failure and relevant neighboring cases, using the cheapest reliable checks. Where practical, show that the check detects the original defect and passes after the change. Account for realistic workload and reliable success/failure signaling.

Distinguish local verification, CI results, deployment, and live-system proof. State remaining gaps precisely. Do not weaken checks or mask errors to obtain a green result.

### Recommend prevention

Name the failure class and explain why existing safeguards missed it. Recommend measures tied to that mechanism: enforcing an invariant, improving failure propagation, targeted regression coverage, better diagnostics, or a justified workflow change.

Explain expected benefit and ongoing cost. Separate measures included in the authorized fix from proposed follow-up work. Do not automatically turn prevention into a broad hardening project or a mandatory new test for every incident.

The closing report should make the diagnosis, evidence, fix status, verification, uncertainty, and prevention recommendations easy to find. No fixed report template is required for small issues.

## Implementation checklist

- [x] Draft `dotfiles/skills/triage-bugfix/SKILL.md` with concise frontmatter and the guidance above. Start self-contained; add references or scripts only if a demonstrated need emerges.
- [x] Review discovery boundaries, scope preservation, and wording. Remove generic advice already supplied by global instructions and incident-specific assumptions.
- [x] Validate frontmatter and scaffolding with skill-creator's `quick_validate.py`. If UI metadata is included, follow its metadata reference and validate consistency.
- [x] Run the behavioral checks below. Revise only for demonstrated gaps, then rerun affected checks.
- [x] Add the paired Codex and Claude Home Manager links in `home.nix`, following the existing `mkOutOfStoreSymlink` convention.
- [x] Run appropriate repository/Nix checks, then reload Home Manager using the repository's `reload.sh` workflow. Inspect the activation changes first; preserve unrelated work and avoid activating unrelated pending configuration without assessing it.
- [x] Verify both installed skill paths resolve to the intended source. Report any client discovery behavior that was not verified.
- [x] Review the scoped diff, commit with a conventional commit message, and push according to repository instructions. Preserve unrelated configuration and lockfile changes.

## Behavioral validation

Use isolated fixtures and realistic requests. If independent evaluators are used, give them the skill, request, and raw artifacts without the expected diagnosis or proposed solution. No live production mutations are necessary.

| Scenario | Required observable behavior |
| --- | --- |
| Ambiguous failure with incomplete logs | Separates facts from hypotheses, proposes a discriminating check, and avoids an unsupported root-cause claim. |
| Confirmed defect with implementation authorized | Produces a causal fix, verifies the original failure and relevant behavior, and proposes proportionate prevention without needless approval stops. |
| Live incident with an explicit diagnosis-only boundary | Performs only permitted investigation, reports evidence and uncertainty, and drafts remediation without applying it. |

Include a false-success condition or realistic performance constraint in the confirmed-defect fixture to exercise the strongest history-derived requirements. Judge outcomes and side effects, not matching headings or exact phrases. Keep investigative fixtures temporary unless retaining them guards a distinct reusable failure mode.

## Completion criteria

The skill is concise, discoverable in both clients, structurally valid, and demonstrated to handle all three scenarios within scope. Verification results and limitations are recorded in the implementation handoff. Scoped changes are committed and pushed after successful validation and Home Manager activation.

## Execution receipts

- Added a self-contained 38-line skill and paired Home Manager links; no scripts, references, UI metadata, or mandatory delegation were needed.
- Skill-creator validation passed using `mise exec -- uv run --with pyyaml python .../quick_validate.py dotfiles/skills/triage-bugfix`. The initial plain Python attempt lacked PyYAML; the dependency-equipped rerun passed.
- Three independent evaluators used isolated fixtures without the intended answers. Ambiguous logs produced hypotheses and a discriminating check; the diagnosis-only incident produced draft recovery without mutations; the implementation case corrected aggregate exit-status handling and added checks that rejected the original behavior. All three implementation-fixture tests passed on independent rerun in 0.088 seconds. Fixtures remained temporary.
- The native macOS Nix activation package built successfully. Comparing its activation script and home files to the active generation showed only the generation path and two added skill links changed. Existing configuration and lockfile edits were preserved.
- `bash reload.sh` completed successfully. Both installed skill paths resolve to this repository's skill directory. Fresh client UI discovery was not exercised. Activation skipped the unrelated root Ghostty terminfo installation because passwordless sudo was unavailable.
- Whitespace validation passed. No documentation/code inconsistencies were found in the inspected integration.
