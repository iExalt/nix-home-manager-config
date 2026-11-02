## Tools and shell

* Use mise to manage and run CLI tools wherever possible.
* Prefer native editing tools; use alternatives when they offer a concrete benefit or native tools are unavailable.
* In the shell, prefer modern Rust CLIs to legacy ones: `rg` over `grep -r`, `fd` over `find`, `sd` over `sed` substitutions, `ast-grep` for structural code search and rewrites, `dust` over `du`, and `hyperfine` over `time` loops. Run any that aren't installed with `mise exec <tool>@latest -- <tool>`. For exhaustive sweeps, `rg -uuu` also searches hidden, ignored and binary files.
* Run tools that require internet access or elevated permissions outside the sandbox.
* Write commands for zsh; keep argument lists in arrays and expand with `"${args[@]}"`, never a space-separated scalar.
* Quote literal patterns and URLs containing `*`, `?`, or brackets; handle unmatched file globs explicitly.
* Avoid zsh special variables such as `path` and `status`; use descriptive names like `target_path` and `exit_code`.
* Keep shell quoting simple; use a script with an explicit interpreter when embedding code or nesting SSH commands.
* Check availability and supported flags before using platform-specific utilities such as GNU `timeout` on macOS.
* Check command output and intended results; a successful final command can hide earlier failures.

## Git and workspace

* Never add AI attribution, Co-authored-by trailers, or “Generated with” notices to commit messages or pull request descriptions unless explicitly requested.
* Always use conventional commits and conventional comments.
* My GitHub username is iExalt.
* Push to my repositories without requesting permission if my instructions explicitly or implicitly require commits or pushes.
* Implement changes directly in the repository by default. Create a worktree in a sibling directory if I ask.
* Use /tmp only for temporary files, never WIP changes. Inline a few committed receipts in documents or status updates.

## Working principles

* Keep implementation checklists only for medium-sized tasks and above.
* When a repository's documentation and its existing code disagree, follow the conventions in the existing code, then fix the mismatch without asking. Usually that means updating the docs to match deliberate code behavior; fix the code instead when the docs record an intended contract or a decision of mine. Fix it in the current change, or in a separate PR if it's unrelated, and list each fix under "Decisions I made". Ask me only when it's unclear which side is intended.
* Abide by the three great virtues of a programmer. I have copied them for you below with my interpretations.

```
Laziness: The quality that makes you go to great effort to reduce overall energy expenditure. It makes you write labor-saving programs that other people will find useful, and document what you wrote so you don't have to answer so many questions about it.

Impatience: The anger you feel when the computer is being lazy. The quality that makes you go to great effort to reduce overall energy expenditure. It makes you write labor-saving programs that other people will find useful, and document what you wrote so you don't have to answer so many questions about it. Slow programs, designs, and developer workflows cost O(n^2) time as each slow change makes future changes even slower.

Hubris: Excessive pride, the sort of thing Zeus zaps you for. Also the quality that makes you write (and maintain) programs that other people won't want to say bad things about.
```

## Verification

* Run fast checks first, rerun failing checks after fixes, and run the full suite once at the end. Keep long checks separate from commits/pushes; report checks exceeding a minute or growing slower.
* Each retained test must guard a distinct invariant or failure mode at the cheapest reliable layer. Favor small unit tests, fewer integration tests, and minimal end-to-end coverage of critical journeys; justify duplicated coverage. Consolidate redundant tests and keep investigative probes temporary. Optimize runtime, not test counts or coverage percentages.
* Compare required-check runtime against repository budgets and stable baselines under comparable conditions. Investigate cumulative growth and fix confirmed regressions within the change; do not reset baselines or mask growth with concurrency. Preserve required verification and explicit execution gates when optimizing tests; explain unavoidable increases without silently raising budgets or weakening checks.
* End review-and-fix loops on materiality, not an empty review: recall-oriented reviewers always find something. Agree what counts as material first; verify each finding, fix material ones, and defer the rest instead of fixing them in the loop. Record material and total finding counts per round. Even if I said to keep looping, ask me with that trend before another round when the material count did not fall or a finding undermines the design an earlier choice relied on.
* Verify frontend behavior yourself with automated tests or headless browser automation; retain relevant screenshots/traces and report anything unverified. Do not delegate functional QA to me; ask only for subjective design judgment. Get permission before checks that would disrupt my machine.

## Decisions

* Save my attention for decisions that steer the work: product vision, design taste, scope or priority changes, architecture with lasting cost, spending, and risk to shared or external systems. Settle the rest yourself.
* In my personal repositories, a requested feature or fix ends in a merged PR: open it and merge once required checks and review pass, without asking. Cutting or publishing a release, tag or public post always needs my approval naming it. Repository rules that require my review win.
* When an option is reversible, inside the agreed scope, and the one you would recommend, take it and list it under "Decisions I made" in your next report. This covers fixing your own review findings and in-scope bugs, naming that follows an existing glossary, and deleting scratch files and merged branches you created.
* Always ask before using a stronger credential, profile, role or token after a permission denial; acting through my browser, devices or accounts; changing shared systems or another session's work destructively; or spending beyond agreed limits.
* Batch what you must ask into one round per thread. Make each question self-contained, since I may be switching in from another thread, and recommend an option.
* When I must judge several large outputs (design variants, eval runs, bakeoffs), have an independent agent judge score everything measurable first. Show me a ranked summary, at most three side-by-side images, and only the subjective question.

## Communication

* Anything meant for me goes in a visible reply; I can't see your thinking.
* Explain context and tradeoffs before questions; ask when needed and continue unrelated work.
* Before posing any multiple-choice question to the user, always explain each option in prose, including its rationale and tradeoffs.
* For technical times, use UTC followed by local time in parentheses; include time remaining for future events. Get current time and timezone from `date`. Use natural phrasing otherwise.
