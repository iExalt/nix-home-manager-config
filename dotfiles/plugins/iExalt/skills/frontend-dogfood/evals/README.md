# frontend-dogfood evals

Each case checks out one of the user's projects just before a fix the user asked for, then asks for
a QA pass and grades whether the tester catches what the user caught, at the user's severity. The
repositories' local paths are in the user's environment file
(`~/.config/frontend-dogfood/environment.md` › Eval repositories). Create the worktrees (one per arm)
before a run; the prompts name the `-with` path, so give the baseline arm the `-without` one:

| Case | Repository | Revision | Worktree | User's complaint it reproduces |
|---|---|---|---|---|
| dark-canvas-in-dark-theme | bead-pattern editor | `d5f3589^` | `pattern-eval-dark-with` | Canvas "blindingly white/grey" in dark theme |
| phone-pinch-and-stacked-panes | bead-pattern editor | `588c004^` | `pattern-eval-phone-with` | No pinch-to-zoom ("P0"); stacked panes "not usable" |
| duplicated-needs-you-badge | Acyclic | `71f8938^` | `acyclic-eval-badge-with` | "the green 1 duplication" in Needs you |

```sh
git -C <repository> worktree add --detach ~/dev/Projects/pattern-eval-dark-with d5f3589^
```

Runs drive browsers on the browser host and serve apps on the laptop, so give each arm its own port
range and name prefix when running them in parallel. Remove the worktrees afterwards with
`git worktree remove`.
