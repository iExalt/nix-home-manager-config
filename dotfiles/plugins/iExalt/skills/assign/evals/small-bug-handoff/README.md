# Eval: small bug handoff

A trigger test for intake and routing with a reachable issue and a real checkout. The fixture is
a tiny Git repository with agent instructions and one small, clearly bounded bug, issue #7, given
as a local file so the run needs no tracker access. The issue is one behavior change with a clear
acceptance check, so the expected size is Small and the workflow `continuous-peer-review`.

## Running it

1. Create a fresh checkout per run: `./setup.sh <dir>` (it refuses an existing path).
2. Give the agent [prompt.md](prompt.md) with `DIR` replaced by that path, in a session where the
   `iExalt` plugin is installed. Don't name the skill: the run also checks that "take issue #7"
   triggers `assign`.
3. Read the transcript and grade it below, then delete the checkout.

**Pass** means all of these:
- `assign` is invoked without being named;
- the agent reads `ISSUE.md`, `AGENTS.md`, the Git state and `wc.py` before sizing;
- it gives a one-line TL;DR choosing Small and `continuous-peer-review`, with the deciding reason;
- it invokes `continuous-peer-review`;
- the brief carries the item reference and title, the acceptance criteria (a last line without a
  trailing newline counts; newline-terminated files keep their count), the non-goals (`--words`,
  new flags), the repository, and the publication rule from `AGENTS.md` (commit locally, never
  push);
- it edits no file and changes no Git state.

## Results

Not run yet.

Limits: the issue is a local file, so this doesn't exercise `gh`, Linear or Jira intake; it covers
only the Small route.
