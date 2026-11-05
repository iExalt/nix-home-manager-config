# Workstreams in a tracker

When the campaign keeps tier 3 as workstream issues (three-tiered-plan's
"Keep tier 3 as tracker workstreams"), each workstream is a thread and its
issue is the thread's entry. Where the overseer skill says script, read the tracker,
and follow the repository's instructions for its fields and commands:

- **Ready set:** run the repository's readiness tool, read-only where it has
  a dry run, rather than deriving readiness yourself. Propose workstreams it
  reports ready, or in flight with ready items, and take **not alongside**
  rules from their Depends on sections and the repository's exclusion table.
  A workstream the tool calls provisional waits for its refinement.
- **Agreement and approval:** record the user's agreement as a signed comment
  on each workstream issue that quotes the dialog answer. When the repository
  makes approval a tracker state, such as a status of Approved, set it from
  that agreement only where its instructions let an agent record the user's
  approval; otherwise ask the user to set it, as a planned any-time
  intervention. A workstream without its approval state doesn't launch.
- **Workers:** brief each with the workstream prompt, such as
  `/iExalt:keep-me-in-the-loop Run workstream #<N>`. The worker claims the
  issue as the repository's instructions say and keeps the sibling worktree
  they name. Name it after the workstream, such as `Worker: <name> #<N>`.
- **Judgment calls and deviations:** record them as signed comments on the
  affected workstream issues, update those issues' bodies or links, and rerun
  the readiness tool before launching their dependents.
- **Done:** besides the checks in `SKILL.md` › Run the threads, the workstream issue is
  closed, the readiness tool has run, and the summary shows its dependents
  unblocked. Report its drift check with the done check.
