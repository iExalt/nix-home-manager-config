# Agentic interfaces

When the UI fronts an agent or any long-running automated work, the user must always be able to
answer five questions at a glance.

**What is the agent doing?**
- Show a clear run state: queued, running, waiting for you, done, failed, cancelled. Use text and
  icon, not color alone.
- Show the current step in plain language ("Reading 3 files", not a tool name or raw JSON), with
  elapsed time. Show determinate progress only when it is real.
- Stream meaningful progress, but keep raw logs, tool calls, and reasoning one click away. Don't
  put them in the main path.
- Announce state changes politely to assistive tech (`aria-live="polite"`) without announcing every
  token.
- Run state survives reload and navigation. A long run must not depend on the tab staying open.

**What needs my attention?**
- Requests for approval or input get a distinct, consistent treatment, and the user can find them
  from anywhere: a badge, an attention list, or a notification when the user is elsewhere.
- An approval states exactly what will happen, what it affects, and whether it can be undone, with
  specific action labels ("Delete 12 files", "Send email to 3 recipients"). Approve and deny are
  keyboard-reachable, with default focus on the safe choice (SKILL.md › Conflicts › Destructive
  actions).
- Separate "needs you" from "FYI". Too many interruptions train users to approve without reading.

**How do I stop it?**
- Cancel or Stop is visible and reachable by keyboard whenever work is in progress, never hidden in
  a menu.
- Stopping takes effect right away in the UI ("Stopping…" then "Stopped") and reports honestly what
  already happened and what did not, especially side effects that cannot be reversed.

**What changed?**
- End each run with a summary of outcomes: files changed, records created, messages sent, cost or
  usage where relevant. Link to the details (diffs, artifacts, logs).
- Show changes as diffs or before/after comparisons when the user must review them. Offer undo or
  revert where the system supports it.
- Distinguish agent-made changes from user-made ones, and show when each happened.

**What happens if I retry?**
- Say whether retry resumes, starts over, or repeats side effects ("Retry will send the email
  again"). Preserve the user's input and prior output across retries.
- Errors say what failed, what was completed before the failure, and the safe next action.
- When retry, edit-and-rerun, and branch all exist, name them distinctly and keep earlier runs
  inspectable.

Prefer purpose-built views (status lists, review queues, diff viewers, forms) over making the chat
transcript the only interface for structured work. Avoid anthropomorphic filler ("I'm thinking
really hard!"). Precise status builds more trust than personality.
