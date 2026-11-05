# Tier 3 as tracker workstreams

Read this once the user chooses workstreams for tier 3, or when the
repository already uses them. Where `SKILL.md` says script or thread, read
workstream issues and workstreams. The repository's instructions settle the
issue type, fields, labels, approval state and commands; where they say
otherwise, they override this file.

## Shape

- **Threads:** one issue per thread, of a dedicated type, named after its main
  work rather than numbered, since workstreams open in whatever order their
  blockers clear. Its body holds the script entry: scope (the roadmap steps,
  whose proofs are its acceptance criteria), proposed chunks, Depends on,
  Human, Live and Done when. Use the repository's issue form for it, or derive
  one from the script template's thread entry. Its work items carry its name
  in a tracker field, so membership can be queried.
- **Order:** **after** becomes a blocked-by link: between workstream issues for
  whole-workstream order, and between the items themselves for a wait on part
  of another workstream's output. **Not alongside** and **not before** have no
  link form, so keep them in the Depends on section. Put exclusions that span
  many workstreams, such as a shared GPU, in a table in the repository's
  instructions. Links are the floor; Depends on may be stricter, never looser.
- **Readiness:** never draw the order graph or mark ready threads by hand. A
  readiness tool reads the links and membership. It writes what can start and
  what each workstream waits on into tracker fields, and a pinned summary
  issue, so the user sees what needs them. The summary replaces the script's
  Order, "When a human is needed" list and state markers, and the status
  document's recommended sequence points at it. Mark workstreams past the
  current evidence with a provisional label.
- **Prompt:** one stable form, such as `/iExalt:keep-me-in-the-loop Run workstream
  #<N>`, since the issue holds the entry and the repository's instructions
  hold the rules.
- **Approval and finish:** the user approves a workstream through the tracker
  state the repository names, such as a status of Approved. A finished
  workstream closes, with its roadmap ticks and status evidence in the same
  change. Write a deviation into the issue bodies of the workstreams it
  changes, with a comment on each saying what changed and why.
- **Revision log:** the issues' timelines and comments; also log a re-cut of
  workstreams in the status document.
- **Alignment:** the roadmap keeps a table from each step to its issues and
  workstream. A change on either side updates the other in the same change.
  Prefer a check that reports drift between them, such as one in the
  readiness tool, over memory.

Draft the workstreams in the conversation or a scratch file, not the tracker:
creating issues publishes them, so it waits for confirmation.

## Publish

Publish by creating the confirmed issues, their links, labels and membership
fields, then running the readiness tool and its drift check. Commit the
roadmap's mapping table with them. Leave approval to the user: confirming
the tiers doesn't approve a workstream.

## Revise

When a tier changes, update the affected issues' bodies and links and rerun
the readiness tool.
