# Acyclic work queue

Use this when the project already keeps work in Acyclic. Run `acyclic prime`
and follow the installed version's commands and semantics; don't copy a prior
session's state vocabulary. Use the configured tracker and a session-specific
actor as prime directs. A missing tracker mapping is not authorization to
initialize, migrate or select another project's tracker.

## Find and preserve the next action

Read the relevant initiatives, items, threads and `acyclic needs` before adding
work. Reuse the item covering the scope. Use the CLI's readiness and claim
rules, not a parallel queue derived from chat; never take another holder's work.
Claiming a thread leases it; it does not authorize work on siblings outside the
user's scope. Only `waits-for` establishes dependency order, not IDs or thread
membership. Stop at the approved scope and release only your own claim.

In the existing item or thread notes, retain acceptance criteria and decisions
and keep these facts current: next action, responsible party, PR/evidence link,
and wake-up condition. Update the relevant part without replacing unrelated
notes. Distinguish these situations using existing fields:

| Situation | Record |
| --- | --- |
| Work can proceed | Use `thread ready` and claim the thread under current prime rules. |
| A user decision blocks work | Record the exact question and owner. For a distinct prerequisite, use a decision item and `waits-for`; keep the unresolved decision out of runnable work by parking it. Do not mark it satisfied until the user answers. |
| Another item must finish first | Use `waits-for`, not a second informal dependency list. |
| Waiting on CI, review or a contributor | Keep work unfinished; notes name the PR, pending condition and responsible party. Park it if handing it back without an active owner, and record the resumption condition. |
| Intentionally deferred | Park it with its reason and resumption condition. |
| Scope verified and required publication complete | Record completion evidence as described below. |

A note is not a notification or scheduler. If follow-up must happen without
another user message, arm an authorized watcher or wake-up with a deadline and
record who owns it. On wake-up, recheck the condition and claim before resuming;
unpark only when the recorded condition is satisfied and within the agreed scope.
If no wake-up is available, report that limitation and the next responsible party.

## Finish with evidence

For code work, verify the item's acceptance criteria and the required merge,
then use `item done --commit` with the repository and actual landed commit as
current prime directs. A branch push, green CI or merge request is insufficient.
For a squash merge, use the squash commit on the default branch. Use `--evidence`
for non-commit outcomes, never to bypass missing merge proof for code work.

Check the write's result and read the item back. If it reports
`unchecked_commits`, the tracker has not verified merge ancestry: run an acyclic
command from inside the repository's clone so Acyclic learns it (for a github.com
origin; map any other clone in `~/.config/acyclic/clones.toml`), then re-check; otherwise keep the completion claim unverified and prevent dependents from being
launched on that unchecked result. Never force completion over
another holder or replace existing evidence without checking it first.

Release task-owned claims when the thread has no remaining ready work; sync
under the project's existing sharing policy. Preserve open acceptance gates
even when one contributing PR has merged. Do not archive chat or tracker items
as a substitute for reconciling their unfinished work.
