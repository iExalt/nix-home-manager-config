---
name: frontend-design
description: "Design, build, critique, and refine usable, accessible, good-looking frontends with the agent supplying the design judgment and the user supplying goals and feedback. Use whenever work touches a user interface: new apps, pages, dashboards, components, forms, settings, onboarding, empty or error states, and agent or chat UIs that show progress, approvals, cancel, and retry; also for UX review, accessibility or responsive audits, visual polish, UX copy, and recording design conventions in DESIGN.md. Use even when the request mentions only a feature and the UI is incidental. Merges Impeccable, Vercel's Web Interface Guidelines, and Anthropic's frontend-design."
---

# Frontend Design

Act as the design lead the user does not have. They know what they want to accomplish and can
react to what they see; you supply users-and-tasks thinking, interaction design, visual judgment,
accessibility, and the hundreds of small details they would not know to request. Ask them about
goals, priorities, and preferences. Decide technical design questions yourself and explain the
consequential ones in plain language.

Prioritize clarity, consistency, and task efficiency over novelty. A beautiful interface here is one
a first-time user understands in seconds, an expert operates quickly, and that looks deliberate
rather than templated.

## Ground rules

- **The brief wins.** Honor the user's stated aesthetics, fonts, palettes, and constraints, and
  follow an existing DESIGN.md or established look in the code. Redirecting a clear brief toward
  your taste is a failure.
- **Refinement preserves; redesign replaces.** A refinement keeps the existing identity, behavior,
  copy, and everything outside scope. Ask before replacing factual copy or adding claims.
- **Real content, never invented claims.** Use realistic data at real ranges. Label illustrative
  values as samples and never invent prices, customers, metrics, or capabilities.
- **Loaded symbols stay out of the decoration.** A subject's world does not license emblems tied
  to militarism, supremacy, or hate movements as motifs, badges, or ornament, such as the Rising
  Sun flag's rays, the Confederate battle flag, or Nazi-era insignia and their stylised variants;
  reach for that world's neutral forms instead. Content that documents such a symbol as fact stays
  as it is.
- **Verify by looking.** Code review alone is not verification. Inspect the rendered result at the
  sizes it ships at and exercise the interactions.
- **Finish the job.** Every state the flow can reach is designed, not just the happy path.

## Modes

The mode names what success looks like on this surface. Choose it per surface, not per product,
because a tool's landing page is Persuade while its settings screen is Operate.

- **Operate:** the user completes a task (app UI, dashboards, agent consoles, admin, settings,
  tools). Scanability, consistency, and familiar patterns outrank expression; brand lives in precise
  details. Most agentic projects are mainly this.
- **Read:** the user understands something (docs, reports, changelogs, run summaries). Structure
  for comprehension, then make reading pleasant.
- **Persuade:** the user decides and acts (landing pages, marketing, pricing). Earn attention with
  a distinct point of view.
- **Experience:** the user is inside the work (portfolios, galleries). Let the artifact lead.

Scale ambition to the mode. Persuade and Experience get bold, committed visual work. Operate and
Read show ambition through precision and restraint.

## Workflow

Track these steps in a short checklist for medium-sized work and above. For a narrow fix
inside an established design, start at step 3 with the existing conventions.

### 1. Establish users and tasks

Read DESIGN.md if it exists, then inspect the code, routes, components, tokens, and any data or
API the UI will show. Write down what you can infer, then ask the user to confirm or correct it
instead of interviewing from scratch. Use a structured question tool when one is available. Ask two
or three questions per round, usually one round:

- Who uses this, in what situation, and how often?
- What are the one to three things they must get done, and what does success look like?
- What must not change, and what would make a polished result feel wrong?
- Are there products they like using, or a look they want to avoid?

Do not ask for CSS values, component libraries, or other technical choices.

### 2. Propose the flow before implementing

Draft a compact brief: users and primary task, the flow step by step, layout as an ASCII wireframe,
the states that matter, and what is out of scope. Scale it to the work: a single Operate screen
needs a few bullets and one wireframe. Only a new project or a redesign gets the full token plan and
generic-defaults review from [references/visual-direction.md](references/visual-direction.md);
otherwise inherit the existing look.

Explain consequential choices in plain language, with the alternative and its tradeoff. Examples:
"inline editing (fast, but easy to change something by accident) vs. an edit page (safer, one more
click)", or "undo after delete vs. a confirmation dialog". Show two or three wireframe alternatives
when the layout is genuinely open, and recommend one. Get the user's go-ahead, then record the
agreed decisions in DESIGN.md ([references/design-record.md](references/design-record.md)).

When no user can answer (a delegated or autonomous run), record each assumption under DESIGN.md ›
Open decisions with the option you chose. Then build only if your instructions authorize
implementation; otherwise return the brief and stop. Either way, list the assumptions in your
report so the user can overturn them.

### 3. Build one complete task flow with realistic data

Build one flow end to end before broadening. Read the "Craft floor" in
[references/visual-direction.md](references/visual-direction.md) before editing UI.

- Seed realistic fixtures: long names, large datasets, empty results, slow responses, errors, and
  permission limits. Keep them reusable for later checks. See
  [references/states-and-edge-cases.md](references/states-and-edge-cases.md).
- Design every reachable state: loading, empty, error and recovery, success, disabled, partial.
- Use semantic HTML and the project's existing components and tokens. Use standard controls for
  standard tasks.
- Write the interface copy deliberately ([references/copy.md](references/copy.md)): specific
  action labels, errors that say how to recover, and one name per concept.
- Skim the matching section of
  [references/web-interface-guidelines.md](references/web-interface-guidelines.md) before building
  forms, animation, or navigation.

### 4. Verify in a browser

Run the app and drive it with browser automation: Playwright, a browser MCP, or the harness's
browser tools. [scripts/browser_check.py](scripts/browser_check.py) handles the repeatable part.
It serves a static build or targets a running URL, screenshots named states at each width, runs
reduced-motion and 200%-zoom passes on the first (key) state, counts Tab presses to a target
control, and reports HTTP errors, failed requests, console errors, and horizontal overflow. Install
its browser once with `mise exec -- uv run <skill-dir>/scripts/browser_check.py --install-browser`,
then see `--help`. Useful options: `--spa` for client-routed static builds; `--ready NAME=SELECTOR`
for a state whose data loads after the page or that is transient; `--status NAME=404` for error
pages the server returns with an error status (not client-rendered SPA 404s, which return 200);
`--idle-timeout 0` for streaming UIs; `--tab-to WIDTH=SELECTOR` when a control moves (into a menu
on phones, say); and `--all-passes` to run reduced motion and zoom on every state. Narrow widths
emulate a phone (viewport meta tag, touch, coarse pointer). Script the app-specific interactions separately. Give transient
states (posting, slow loads) a URL or fixture switch so they stay on screen long enough to capture.
Ask before anything that would disrupt the user's machine, such as installing system browsers,
taking over their open browser, or binding common ports.

- **Widths:** desktop (about 1440px) and narrow (about 375px), plus any width where the layout
  changes. Check 200% zoom on key screens (headless: half the CSS width at 2x density).
- **Keyboard:** Tab through the whole task. Focus must be visible, in a logical order, and never
  hidden behind sticky elements; check traps against Conflicts › Focus traps. Escape closes
  overlays, Enter submits, and focus moves sensibly when dialogs open and close.
- **Interactions and states:** actually click, type, submit, cancel, and retry, using the error,
  empty, and long-data fixtures. Watch the console for errors.
- **Preferences:** reduced motion, and dark mode if the product supports it.
- **Accessibility tree:** check that controls have names and roles. Run an automated checker such
  as axe if one is available; it catches only a subset of problems, so the manual pass still
  matters.

Look at every screenshot you take; a screenshot nobody inspected proves nothing. Batch your fixes
between looks. A visual fix, such as CSS added after a screenshot showed a problem, is not done
until a new screenshot shows it fixed; if you can't take one, say so in the report. Save screenshots
of the final states in the project (for example `design/screenshots/`), not only in /tmp, and report
what was not verified.

### 5. Critique, audit, and fix

Before asking for feedback, run [references/critique.md](references/critique.md) on the flow:
design review, cognitive load, Nielsen heuristics, two or three personas, and the
[web interface guidelines](references/web-interface-guidelines.md) as a checklist. Fix every P0
and P1 finding and re-verify in the browser. Report the remaining P2 and P3 items briefly instead
of burying the user in them.

### 6. Iterate and preserve consistency

Show the user the result as screenshots plus a short plain-language summary: what they can now do,
the main design decisions, and the questions only they can answer. Turn their feedback into
changes, and generalize it. A complaint about one button's label usually means a naming convention
should change everywhere. Record agreed conventions and the feedback behind them in DESIGN.md so
later sessions stay consistent. Before adding a new screen, reuse the established patterns rather
than inventing new ones.

## Agentic interfaces

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
- Requests for approval or input get a distinct, consistent treatment, and you can find them from
  anywhere: a badge, an attention list, or a notification when the user is elsewhere.
- An approval states exactly what will happen, what it affects, and whether it can be undone, with
  specific action labels ("Delete 12 files", "Send email to 3 recipients"). Approve and deny are
  keyboard-reachable, with default focus on the safe choice (Conflicts › Destructive actions).
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

## Conflicts

This section is the single authority wherever the sources or references disagree. References keep
upstream wording and point here with a one-line `Override: see SKILL.md › Conflicts › <rule>` note.
Change a rule here, not at the pointer.

- **Contrast:** WCAG 2.2 AA (4.5:1 text, 3:1 large text and UI components) is the pass/fail floor.
  APCA is optional extra guidance.
- **Destructive actions:** prefer Undo when recovery is safe; otherwise confirm, naming the action
  and the object. The destructive choice is never pre-focused.
- **Focus traps:** modal dialogs trap focus while open, including drawers and sheets that block
  the page behind them; closing one returns focus to the control that opened it. Non-modal
  popovers, menus, and side panels never trap.
- **Case:** sentence case unless the project already uses Title Case consistently.
- **Zoom:** never disable zoom (no `maximum-scale=1` or `user-scalable=no`). Prevent iOS auto-zoom
  with input font sizes of at least 16px.
- **Native controls:** on task surfaces keep standard affordances, including scrollbars. Theme their
  color to the palette, but don't reinvent their behavior.
- **Motion:** on Persuade and Experience surfaces, at most one authored moment such as a page-load
  sequence. On Operate and Read surfaces, no page-load choreography: motion answers user actions
  and shows state changes in 150–250 ms. Default to `transform` and `opacity`; blur, clip-path,
  mask, and shadow are fine for an authored moment when they stay smooth. Never animate layout
  properties or use `transition: all`.
- **Line length:** 65–75 characters for body prose (Anthropic's "under 80" is the outer limit);
  tables and dense UI may run wider.
- **Monospace:** use `font-variant-numeric: tabular-nums` for numbers that are compared, including
  metrics and measurements. Reserve monospace for code, IDs, hashes, and paths.
- **Typefaces:** on Persuade and Experience surfaces, choose faces specific to the brief rather
  than defaults. On Operate and Read surfaces, a well-tuned system or familiar sans is a deliberate
  choice, and display faces stay out of UI labels, buttons, and data.
- **Elevation:** pair a shadow only with a subtle semi-transparent border for edge clarity. An
  opaque 1px border under a wide soft shadow reads as a ghost card.
- **Placeholders:** show an example value or pattern (`+1 (123) 456-7890`), never the label. An
  ellipsis marks only an open-ended prompt or a truncated example (`Search…`, `sk-012345679…`).
- **Help and onboarding:** inline help first; tooltips are a last resort; tours are optional,
  skippable, and contextual, never an upfront gate. Score Nielsen's "Help and documentation"
  against that standard, not by counting tooltips or tours.
- **Cards:** cards are not the default page structure. Nesting is legitimate only when the
  structure really is nested (a card inside a kanban column), never as decoration.
- **Generated-look defaults:** these five are defaults to avoid: eyebrow labels above headings, a
  system face as the display voice of a Persuade or Experience page, sketch-style SVG illustration,
  decorative stripe or grid backgrounds, and geometric masks standing in for a subject's real
  outline. Use one only when the user's brief names it, or when the established design (DESIGN.md
  or the existing code) already uses it, which includes a world the user chose, such as
  neobrutalism or a blueprint canvas. Never introduce one because the subject suggests it. This
  relaxes Impeccable's outright eyebrow ban and makes its Codex-only sketch-SVG and stripe/grid
  rules apply everywhere. Anthropic's calibration traits (cream and terracotta, near-black with one
  acid accent, and the rest) remain what that list says: legitimate for some briefs, but never the
  way to spend a free axis.
- **Distinctiveness:** on Operate and Read surfaces, familiarity wins. Spend boldness on one
  memorable detail, not on unfamiliar controls.

## References

| File | Load when |
|---|---|
| [references/visual-direction.md](references/visual-direction.md) | Choosing or changing a visual direction; skim "Craft floor" before UI edits |
| [references/states-and-edge-cases.md](references/states-and-edge-cases.md) | Building or hardening a flow; seeding fixtures |
| [references/copy.md](references/copy.md) | Writing labels, errors, empty states, or any UI text |
| [references/web-interface-guidelines.md](references/web-interface-guidelines.md) | Building forms, motion, or navigation; reviewing finished UI |
| [references/critique.md](references/critique.md) | Step 5, or whenever the user asks for a review or audit |
| [references/design-record.md](references/design-record.md) | Creating or updating DESIGN.md |

Sources and licenses are listed in [NOTICE.md](NOTICE.md).
