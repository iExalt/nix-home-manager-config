# States and edge cases

Adapted from Impeccable's `harden` and `onboard` commands
([pbakaus/impeccable](https://github.com/pbakaus/impeccable/tree/b7a89176e4e87422b40f98adabceb051dbb5448b/skill/reference),
Apache-2.0), with state rules from Vercel's Web Interface Guidelines (MIT). Sentences are copied or
lightly trimmed; code examples are shortened.

Designs that only work with perfect data aren't production-ready. Build every flow against the
inputs, errors, languages, and network conditions real users will bring, and design those states
before the happy path looks finished.

## Realistic data

Seed fixtures that exercise the ranges, not just the average:

- **Text:** very long names, titles, and descriptions (100+ characters, unbroken strings such as
  URLs and hashes), a single character, empty strings, emoji, accents, RTL (Arabic, Hebrew), and
  CJK.
- **Numbers:** zero, negatives, millions and billions, many decimal places, currencies.
- **Collections:** 0, 1, a typical handful, and 1000+ items; 50+ options in a select.
- **Time:** just now, years ago, future dates, timezones, durations from milliseconds to days.
- **People and permissions:** missing avatar, duplicate names, read-only and no-access users.

Keep the fixtures in the project (a seed file or a `?fixture=` switch) so the next iteration and the
browser checks can reuse them. Add switches for latency and frozen simulation (`?latency=5000`) so
transient states such as "Posting…" can be captured and inspected.

## The states to design

Every component and screen gets these where they can occur: default, hover, focus, active,
disabled, loading, empty, error, success, and partial or permission-limited.

- **Loading.** Name the real operation ("Loading your projects…"). Use skeletons that mirror the
  final layout exactly instead of a spinner in the middle of content. Add a short show-delay
  (~150–300 ms) and a minimum visible time (~300–500 ms) so fast responses do not flicker. Show
  determinate progress when it is available; never invent progress. Time estimates for long
  operations.
- **Empty.** Distinguish first use, no results, filtered-to-nothing, no permission, and failure.
  Each explains what will be here, why it matters, and the next useful action. "Nothing here" is a
  dead end.
- **Error.** Say what failed, why when known and useful, and how to recover. Keep the user's input.
  Offer retry where retry can work. Show errors next to their source, and never block the whole
  interface because one component failed.
- **Success.** Confirm the completed outcome briefly; mention the next consequence only when it
  changes what the user should do.
- **Disabled and permission-limited.** Explain why something is unavailable and how to get access,
  rather than silently greying it out.
- **No dead ends.** Every screen offers a next step or recovery path.

## Overflow and layout

- Text containers handle long content: truncate with an ellipsis, clamp lines, or wrap with
  `overflow-wrap: break-word`. Truncated text needs a way to see the full value (title, tooltip, or
  detail view).
- Flex and grid children need `min-width: 0` (and `min-height: 0` in grids) so they can shrink.
- Avoid fixed widths on text; budget 30–40% expansion for translations.
- Use logical properties (`margin-inline-start`, `padding-inline`) so RTL works.
- Large lists: paginate or virtualize; provide search and filters; do not load 10,000 rows at once.

## Errors by source

- **Network:** offline, slow, and timeout states with a clear message and retry.
- **Validation:** inline next to fields, specific, preserving input; on submit, focus the first
  error. Do not block typing or pre-disable submit; let users submit to see what is missing.
- **API status:** 400 shows validation errors; 401 sends to sign-in and returns afterward; 403
  explains the missing permission; 404 shows a not-found state with a way back; 429 explains the
  rate limit and when to retry; 5xx shows a generic error with retry or support.
- **Never trust client-side validation alone,** and never expose internal codes or stack traces as
  the primary message.

## Concurrency and interruption

- Prevent double submission: keep submit enabled until the request starts, then disable it, show a
  spinner beside the original label, and send an idempotency key.
- Optimistic updates when success is likely; on failure, roll back and say so, or offer Undo.
- Handle races and conflicts (two tabs editing the same record).
- Warn before navigation when unsaved work would be lost; preserve state across refresh where users
  will expect it.
- Interrupted gestures (custom sliders, drag surfaces): on `pointercancel`, lost capture, release
  outside the control, or window blur, clear the dragging state so the next drag works without a
  reload.

## Internationalization

- Format dates, times, numbers, and currencies with `Intl.DateTimeFormat` and `Intl.NumberFormat`
  for the user's locale; detect language from `navigator.languages` or `Accept-Language`, never IP.
- Pluralize with an i18n library, not `count !== 1 ? 's' : ''`.
- Write complete translatable messages rather than concatenated fragments.
- Wrap brand names, code tokens, and identifiers in `translate="no"`.

## First run and onboarding

- **Time to value.** Get the user to their first meaningful result as fast as possible; teach
  through the task, not walls of text.
- **Make it optional.** Power users skip tours; never force an unskippable walkthrough.
- **Context over ceremony.** Explain a feature where and when it is used, not in an upfront tour.
- **Empty states teach.** The first empty state is often the best onboarding surface: show what will
  appear, why it matters, and one clear action to start.

## Verify

Exercise these in the browser, not just in code:

- 100+ character names, emoji in every text field, an RTL string.
- Offline and throttled network; forced API errors for each state above.
- Empty data and 1000+ items.
- Clicking submit ten times rapidly; refresh mid-flow; Back and Forward.
- Interrupted drags where custom gestures exist.

Say what produced the evidence (viewport, emulation, synthesized input, real device) and name what
stayed untested.
