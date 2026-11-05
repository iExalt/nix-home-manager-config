# Model routing

| Role | Codex | Claude | Effort |
| --- | --- | --- | --- |
| Top orchestrator: an overseer, or the main navigator of a team | GPT Astra | Opus | `high` |
| Lead: phase or item coordination, integration decisions | GPT Sol | Sonnet (`developer-routine`) | `medium`; `high` for substantive review or complex decisions |
| Independent substantive reviewer | GPT Sol | Sonnet (`developer-routine` when it matches) | `high` |
| Pilot: implementation, diagnosis, bounded discovery | GPT Luna | Haiku (`developer-trivial` when its scope fits, otherwise explicit Haiku routing) | Codex `high`; Claude `medium` |
| Pilot: mechanical edits, lookups, monitoring | GPT Luna | Haiku (`developer-trivial`) | Codex `medium`, `low` for monitoring; Claude `medium` |

- Preserve the user's explicit provider, model and effort choices.
- Resolve each class to the latest model the provider advertises; never
  invent identifiers. Set model and effort explicitly at launch and at resume.
  For Codex native agents, pass `fork_turns: "none"` with a scoped brief so
  no pilot inherits a top-tier model through a full-history fork.
- Verify the effective model and effort where the harness shows them,
  including after a resume, and correct unintended routing before dependent
  work starts.
- Difficulty, failed checks, slot pressure, a long campaign or "keep going"
  never move an agent up a tier. Difficult pilot work returns to its lead.
  `developer-demanding` (Opus) belongs to the top tier unless a workflow skill
  names an exception or the user approves one.
- If the required route is unavailable, report it and hold the affected
  launches; never silently inherit a more expensive model or drop a tier.
