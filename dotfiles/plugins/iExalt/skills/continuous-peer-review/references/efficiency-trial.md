# Efficiency trial

For an efficiency trial, capture milestone start/end, review dispatch and acceptance times per revision, and
actual blocked intervals for either role with their cause.
Use native event timestamps where available, otherwise record them as events occur
in the existing ledger. Snapshot creation times do not establish dispatch,
acceptance, or blocking; pending review is not blocked time while other useful work
continues. Mark unavailable measurements as unknown instead of reconstructing them
from snapshots. Report elapsed milestone time, dispatch-to-acceptance turnaround,
blocking, peak outstanding increments, and rework attributable to late findings.
Do not add overlapping agent time to claim elapsed time saved. Distinguish actual
parallel work and early messages from capabilities the trial did not exercise.
Ordinary use needs only the compact coordination record, not trial instrumentation.
