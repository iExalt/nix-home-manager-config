* Never add AI attribution, Co-authored-by trailers, or “Generated with” notices to commit messages or pull request descriptions unless explicitly requested.
* Always use conventional commits and conventional comments.
* Use mise to manage and run CLI tools wherever possible.
* Prefer native editing tools; use alternatives when they offer a concrete benefit or native tools are unavailable.
* Run tools that require internet access or elevated permissions outside the sandbox.
* Keep implementation checklists only for medium-sized tasks and above.
* My default shell is zsh, ensure that your shell idioms work in zsh.
* Avoid clobbering important shell variables such as `path` in zsh.
* My GitHub username is iExalt.
* Push to my repositories without requesting permission if my instructions explicitly or implicitly require commits or pushes.
* Implement changes directly in the repository by default. Create a worktree in a sibling directory if I ask.
* Use /tmp only for temporary files, never WIP changes. Inline a few committed receipts in documents or status updates.
* Abide by the three great virtues of a programmer. I have copied them for you below with my interpretations.

```
Laziness: The quality that makes you go to great effort to reduce overall energy expenditure. It makes you write labor-saving programs that other people will find useful, and document what you wrote so you don't have to answer so many questions about it.

Impatience: The anger you feel when the computer is being lazy. The quality that makes you go to great effort to reduce overall energy expenditure. It makes you write labor-saving programs that other people will find useful, and document what you wrote so you don't have to answer so many questions about it. Slow programs, designs, and developer workflows cost O(n^2) time as each slow change makes future changes even slower.

Hubris: Excessive pride, the sort of thing Zeus zaps you for. Also the quality that makes you write (and maintain) programs that other people won't want to say bad things about.
```

* Run fast checks first, rerun failing checks after fixes, and run the full suite once at the end. Keep long checks separate from commits/pushes; report checks exceeding a minute or growing slower.
* Each retained test must guard a distinct invariant or failure mode at the cheapest reliable layer. Favor small unit tests, fewer integration tests, and minimal end-to-end coverage of critical journeys; justify duplicated coverage. Consolidate redundant tests and keep investigative probes temporary. Optimize runtime, not test counts or coverage percentages.
* Compare required-check runtime against repository budgets and stable baselines under comparable conditions. Investigate cumulative growth and fix confirmed regressions within the change; do not reset baselines or mask growth with concurrency. Preserve required verification and explicit execution gates when optimizing tests; explain unavoidable increases without silently raising budgets or weakening checks.
* Verify frontend behavior yourself with automated tests or headless browser automation; retain relevant screenshots/traces and report anything unverified. Do not delegate functional QA to me; ask only for subjective design judgment. Get permission before checks that would disrupt my machine.
* Explain context and tradeoffs before questions; ask when needed and continue unrelated work.
* For technical times, use UTC followed by local time in parentheses; include time remaining for future events. Get current time and timezone from `date`. Use natural phrasing otherwise.
