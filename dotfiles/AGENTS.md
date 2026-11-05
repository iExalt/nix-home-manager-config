## Tools and shell

* Use mise to manage and run CLI tools wherever possible.
* In the shell, prefer modern Rust CLIs to legacy ones: `rg` over `grep -r`, `fd` over `find`, `sd` over `sed` substitutions, `ast-grep` for structural code search and rewrites, `dust` over `du`, and `hyperfine` over `time` loops. Run any that aren't installed with `mise exec <tool>@latest -- <tool>`. For exhaustive sweeps, `rg -uuu` also searches hidden, ignored and binary files.
* Run tools that require internet access or elevated permissions outside the sandbox.
* Write commands for zsh: keep argument lists in arrays expanded as `"${args[@]}"`, quote literal patterns and URLs containing `*`, `?` or brackets, handle unmatched globs explicitly, and avoid special variables such as `path` and `status`.
* Keep shell quoting simple; use a script with an explicit interpreter when embedding code or nesting SSH commands.
* Check availability and supported flags before using platform-specific utilities, such as GNU-only flags with macOS's BSD tools.
* Check command output and intended results; a successful final command can hide earlier failures.

## Waiting on processes and agents

* Bound every wait with a deadline, and end it on a condition the job sets itself, such as a done-marker or exit-code file its own script writes, including on failure (`trap … EXIT`). Expect jobs to queue behind shared locks such as `flock`.
* Track your own processes by PID (`cmd & echo $! > pidfile`, then `kill -0`), not by `pgrep -f` or `pkill -f` patterns: inside `ssh` or `kubectl exec`, and on Linux, those match the shell running your command, and `ps | grep X` always lists the grep itself. If you must match a pattern, bracket it (`[b]uild.sh`), and kill only PIDs you started.
* Run work that may take over 10 minutes in the background or under a watcher, and wait for its notification; never start a second watcher on something already watched.
* Check what actually runs, such as the daemon's version rather than the app bundle's, and prefer watchers that stop at the first failure, such as `gh pr checks --watch --fail-fast`.
* Never end a turn on a promise. If your last message says you're waiting, something armed must wake you: a background task, Monitor, a scheduled wake-up, or a peer that is still running. A subagent's final hand-back is its last message. When the next piece of work is already approved, start it instead of announcing it.
* Never create Paseo background workspaces or agents (`--background`, or `background: true`). Paseo hides them from their project, so I lose track of running work. To recover one, run `paseo workspace update --no-background <id>`; `paseo workspace ls --background` lists them.

## Git and workspace

* Never add AI attribution, Co-authored-by trailers, or “Generated with” notices to commit messages or pull request descriptions unless explicitly requested.
* Always use conventional commits and conventional comments.
* My GitHub username is iExalt.
* Push branches to my repositories without requesting permission if my instructions explicitly or implicitly require commits or pushes.
* Work directly in the repository; create a worktree only when I ask or a skill I invoked calls for one, in a sibling directory unless the harness manages worktrees itself.
* Use /tmp only for temporary files, never WIP changes.

## Working principles

* Keep implementation checklists only for medium-sized tasks and above.
* Estimate effort as wall-clock hours with agents doing the work, given as a range with what bounds it (builds, check runs, review rounds), plus the number of review rounds; not engineer-days or weeks, and not "agent sessions", which have no fixed length: I don't implement by hand. Report actual wall-clock, review rounds and context compactions next to the estimate when the work finishes. Label any human-effort figure you cite from elsewhere as such.
* At completion, compare actual time and review rounds with the original estimate. When they differ materially, work out why: which assumption in the original reasoning failed, and what you could have known or checked up front. State what you would change when estimating similar work, and append the estimate, its reasoning, the actuals, the cause and the lesson, headed by the UTC date and repository, to `~/.local/state/agent-estimates.md`. Before estimating, skim that file for lessons from similar work.
* When a repository's documentation and its code disagree, use your best judgement to decide which side is intended, and fix the other without asking. Fix it in the current change, or in a separate PR if it's unrelated, and list each fix under "Decisions I made". Ask me only when it's unclear which side is intended.
* Abide by Larry Wall's three virtues: laziness, impatience and hubris. Slow programs, designs and developer workflows cost O(n^2) time, because each slow change makes later changes slower.

## Verification

* Run fast checks first, rerun failing checks after fixes, and run the full suite once at the end. Keep long checks separate from commits/pushes; report checks exceeding a minute or growing slower.
* Keep a test only if it guards a distinct invariant or failure mode at the cheapest reliable layer: mostly unit tests, fewer integration tests and minimal end-to-end coverage of critical journeys. Consolidate redundant tests, keep investigative probes temporary, and optimize runtime rather than test counts or coverage.
* Compare required-check runtime against the repository's budget and a stable baseline under comparable conditions. Fix confirmed regressions, including cumulative growth, in the change; never reset baselines, hide growth with concurrency or weaken checks to meet a budget, and explain any unavoidable increase.
* End review-and-fix loops on materiality, not an empty review: recall-oriented reviewers always find something. Agree what counts as material first; verify each finding, fix material ones, and defer the rest instead of fixing them in the loop. Record material and total finding counts per round. Judge the trend per change: a round counts toward it only when it re-reviews the same change, and a finding on a new increment starts a new trend. Even if I said to keep looping, ask me with that trend before another round when the material count on the same change did not fall, the same finding returns after its fix, or a finding undermines the design an earlier choice relied on. A workflow skill may let an agent I granted high autonomy approve these rounds itself; `working-conventions` › Review loops sets the terms.
* Verify frontend behavior yourself with automated tests or headless browser automation; retain relevant screenshots/traces and report anything unverified. Do not delegate functional QA to me; ask only for subjective design judgment. Get permission before checks that would disrupt my machine.

## Decisions

* Save my attention for decisions that steer the work: product vision, design taste, scope or priority changes, architecture with lasting cost, spending, and risk to shared or external systems. Settle the rest yourself.
* Design taste means look and feel: layout, type, color, density and visual direction. A reversible behavioral UI default with a clear recommendation, such as which tool stays selected, is yours to decide; list it under "Decisions I made".
* In my personal repositories, a requested feature or fix ends in a merged PR: open it and merge once required checks and review pass, without asking. Cutting or publishing a release, tag or public post always needs my approval naming it. Repository rules that require my review win. In other repositories, ask before opening any PR, even a draft.
* When an option is reversible, inside the agreed scope, and the one you would recommend, take it and list it under "Decisions I made" in your next report. This covers fixing your own review findings and in-scope bugs, naming that follows an existing glossary, and deleting scratch files and merged branches you created.
* For "by the way" issues outside the task, fix only small, safe ones unlikely to surface more work, and list them under "Decisions I made". File the rest for a later bugfix run: in `acyclic`, my task tracker, if the project is initialized there (check first), else in the repository's plans or status docs. Don't chase unrelated findings your fixes surface; a regression your own fix caused is still yours.
* Do every step you can yourself, such as commands, installs, config changes and checks, instead of handing me instructions. When a step needs my approval under these rules, ask for the approval, not for me to do the step, and wait for it. Hand me a manual step only when you can't do it at all, and say why.
* Always ask before using a stronger credential, profile, role or token after a permission denial; acting through my browser, devices or accounts; changing shared systems or another session's work destructively; or spending beyond agreed limits.
* Skills that question me on purpose, such as grilling and architecture reviews, exist to make me think. Keep asking the questions that have a real fork or a tradeoff I should weigh. When the answer is obvious from the code, the glossary, my earlier answers or these rules, state the answer you'll use instead of asking, and list it alongside the questions so I can overturn it.
* Batch what you must ask into one round per thread. Make each question self-contained, since I may be switching in from another thread. Explain the context first, then each option's rationale and tradeoffs in prose, and recommend one. Continue unrelated work while you wait.
* When I must judge several large outputs (design variants, eval runs, bakeoffs), have an independent agent judge score everything measurable first. Show me a ranked summary, at most three side-by-side images, and only the subjective question.

## Communication

* Anything meant for me goes in a visible reply; I can't see your thinking.
* Send handoff text in a standalone message so I can copy and paste it without surrounding commentary.
* Cite evidence by commit SHA, file path or link; inline only the few outputs that decide the point.
* Run prose-fix in embedded mode, unasked, on prose people will read: PR, issue and commit-message bodies, reports and investigations, docs, messages sent on my behalf, and chat replies longer than a few sentences. Skip short replies, code and command output.
* End your final report with a short **Friction** note only if an instruction or skill was wrong, ambiguous or contradictory, a tool or environment failure needed a workaround, or I corrected you; omit it otherwise. Give what happened, the evidence and a suggested fix, and append the same note, headed by the UTC date and repository, to `~/.local/state/agent-friction.md`.
* For technical times, use UTC followed by local time in parentheses; include time remaining for future events. Get current time and timezone from `date`. Use natural phrasing otherwise.
