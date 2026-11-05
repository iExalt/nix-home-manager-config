# Parallel edits and shared hosts

- Before parallel edits, record file ownership; different regions of one file
  still overlap. Serialize shared edits or isolate worktrees with an integration
  owner/sequence.
- Review shared-workspace edits in place. Integrate accepted worktree patches once.
  Coordinate formatters, generators, dependency updates, and Git mutations to avoid
  races; give integration edits an owner and review them before acceptance.
- Schedule builds/measurements against host CPU/GPU, memory, disk, and cache
  contention, including other tasks. Serialize where contention distorts evidence
  or delays the critical path; independent source work may continue.
