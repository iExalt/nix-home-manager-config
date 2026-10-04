* Never add AI attribution, Co-authored-by trailers, or “Generated with” notices to commit messages or pull request descriptions unless explicitly requested to
* Always use conventional commits and conventional comments
* Use mise to manage and run CLI tools wherever possible
* Run tools that require internet access or elevated permissions outside the sandbox
* Always keep a checklist when tasked with an implementation task
* Avoid clobbering important shell variables such as `path` in zsh
* My GitHub username is iExalt
* Push to my repositories without requesting permission if my instructions explicitly or implicitly require commits or pushes
* Implement changes directly in the repository in question by default, creating a sibling directory as a worktree if the user asks
* Only place truly temporary files in /tmp
* Do not use /tmp as a staging ground for WIP changes
* Commit only a small number of reciepts directly inlined in documents/status updates
* When I request edits to skills, validate the changes, reload Home Manager if skills were added, removed, or renamed, then commit and push the scoped changes automatically unless I explicitly say otherwise.
* Treat wall-clock time as a cost: run fast checks before slow ones, rerun only the failing check or test after a fix and the full suite once at the end, keep long-running checks out of commit or push commands, and tell me when a routine check takes over a minute or keeps getting slower
* Maintain a testing pyramid: most behavioral coverage belongs in fast unit tests, fewer integration tests cover component contracts, and a small set of end-to-end tests covers critical journeys. Put detailed case matrices at the lowest reliable layer; justify repeating them higher up. Assess the pyramid by runtime as well as test count, without imposing fixed ratios.
* Every retained test should guard a distinct invariant or failure mode at the cheapest reliable layer. Prefer small fixtures and minimal setup; consolidate redundant coverage and keep investigative probes temporary unless they earn a regression test. Test count and coverage percentage are not goals. If ordinary logic requires a browser or full deployment to test, consider separating it from infrastructure.
* Treat routine-check latency as a maintained property. Use required runs to compare wall-clock time against the repository's budget and a stable accepted baseline under comparable machine, cache, and concurrency conditions. Do not reset the baseline after every change or hide growing work by saturating more cores. Investigate material or cumulative growth, repeat measurements only to resolve uncertainty, and address confirmed regressions within the change rather than merely reporting them or deferring cleanup to a milestone.
* Preserve required verification while making tests cheaper: shrinking fixtures, consolidating redundant tests, and moving logic checks down the pyramid are ordinary in-scope maintenance. Moving required checks out of the default suite must preserve an explicit execution gate. Explain necessary remaining runtime increases; do not silently raise budgets, replace proofs with weaker checks, or leave required tests optional.
* When asking me a question, explain the context and tradeoffs before the question, and ask at the point where the answer is needed rather than blocking unrelated work on it
* In technical contexts such as schedules, deadlines, runbooks, logs, and status updates, give times in UTC followed by my local time in parentheses and, for future times, roughly how far away they are, e.g. `Waiting until the 12:30 UTC pre-check (8:30 AM EDT, about 2 hours away)`. Get my local timezone and the current time from `date` rather than assuming them. Talk about time normally in other conversations.
