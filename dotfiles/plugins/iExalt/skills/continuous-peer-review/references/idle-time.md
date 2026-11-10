# Reviewer idle time

Idle work fills spare reviewer capacity, which exists to keep handoff turnaround
fast, so idle work must never delay a response. Inbound messages always take priority. Work in short,
interruptible steps without long-running commands so messages are handled at the
next tool boundary. Idle work may run read-only checks against live or shared
systems the session is already permitted to access, but must not change their
state or place noticeable load on them. Do not message the author just to report
idle activity; send actionable results in the normal design, finding, or
review-result messages.

In priority order, the reviewer may:

1. Read source affected by planned increments and challenge their designs before
   implementation starts.
2. Prepare counterexamples and probes for the agreed verification of the increment
   being implemented, then run them against its snapshot at handoff.
3. Review interactions between accepted increments so the final integration review
   covers only the remaining delta.
4. Inspect callers, dependencies, and pre-existing defects in code the milestone
   changes or relies on.
5. Review unrelated repository areas, only when the user authorized it.

Some harnesses, including Claude Code, end the reviewer's run after each reply and
resume it only for the next message, so the reviewer has no idle time of its own.
In those harnesses the author assigns bounded idle work from this list when it
acknowledges a review result and expects no request soon, naming the item and
its scope. The reviewer stops that work at the next inbound message and reports
only actionable results.

Keep idle-time probes, fixtures, and build outputs in the reviewer's session
verification environment; never add them to the author's tree. Prefer lightweight
scripts and targeted tests, building only when a probe requires it. Reviewer
probes stay independent evidence outside the author's test suite. Suggest a probe
worth retaining as a regression test in a finding or review result; the author
decides whether to adopt and write it.
