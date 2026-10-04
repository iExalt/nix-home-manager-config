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
* When asking me a question, explain the context and tradeoffs before the question, and ask at the point where the answer is needed rather than blocking unrelated work on it
* In technical contexts such as schedules, deadlines, runbooks, logs, and status updates, give times in UTC followed by my local time in parentheses and, for future times, roughly how far away they are, e.g. `Waiting until the 12:30 UTC pre-check (8:30 AM EDT, about 2 hours away)`. Get my local timezone and the current time from `date` rather than assuming them. Talk about time normally in other conversations.
