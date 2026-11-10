# Workstreams in a tracker

For Acyclic, first read
[../../working-conventions/references/acyclic.md](../../working-conventions/references/acyclic.md).
Use its items, thread notes and `waits-for` fields for the outcomes below.
Record the user's approval with its source and scope in existing notes; don't
invent issue comments, signatures or an approval state the tracker lacks.
Finishing means satisfying acceptance and recording the required merged
evidence, not merely closing an issue. Preserve the user's authorized scope
when a claimed thread contains other work.

When the campaign keeps tier 3 as workstream issues (three-tiered-plan's
"Keep tier 3 as tracker workstreams"), each workstream is a thread and its
issue is the thread's entry. Where the overseer skill says script, read the tracker,
and follow the repository's instructions for its fields and commands:

- **Ready set:** run the repository's readiness tool, read-only where it has
  a dry run, rather than deriving readiness yourself. Propose workstreams it
  reports ready, or in flight with ready items, and take **not alongside**
  rules from their Depends on sections and the repository's exclusion table.
  A workstream the tool calls provisional waits for its refinement.
- **Agreement and approval:** in an issue tracker such as GitHub or Linear,
  record the user's agreement as a signed comment on each workstream issue
  that quotes the dialog answer. When the repository
  makes approval a tracker state, such as a status of Approved, set it from
  that agreement only where its instructions let an agent record the user's
  approval; otherwise ask the user to set it, as a planned any-time
  intervention. A workstream without its approval state doesn't launch.
- **Workers:** brief each with the workstream prompt, such as
  `/iExalt:continuous-peer-review Run workstream #<N>`, in place of the
  tracker's standalone `keep-me-in-the-loop` prompt. The worker claims the
  issue as the repository's instructions say and keeps the sibling worktree
  they name. Name it after the workstream, such as `Worker: <name> #<N>`.
- **Judgment calls and deviations:** in an issue tracker, record them as
  signed comments on the affected workstream issues, update those issues' bodies or links, and rerun
  the readiness tool before launching their dependents.
- **Scoreboard:** freeze the workstreams' tasks with `scoreboard.py freeze`,
  which reads Acyclic. For another tracker, write line 1 by hand marked
  "(self-reported)", as `SKILL.md` › Scoreboard and auditor describes.
- **Done:** besides the checks in `SKILL.md` › Run the threads, the workstream issue is
  closed, the readiness tool has run, and the summary shows its dependents
  unblocked. Report its drift check with the done check.

In Acyclic, record agreement and judgment calls in the items' thread notes
instead, as the opening paragraph says, with no comments or approval state,
and launch a workstream once that agreement is recorded.
