---
name: friction-log
description: "Record agent friction and verified fixes in the private JSONL log; validate reports, append follow-ups, inspect current incidents, and losslessly migrate the Markdown archive. Use when an instruction or skill is wrong or ambiguous, a tool or environment failure needs a workaround, or the user corrects the agent."
---

# Friction log

Keep incident reports and their follow-ups in `~/.local/state/agent-friction.jsonl`
(override with `FRICTION_LOG` or `--log`). The Markdown file at
`~/.local/state/agent-friction.md` is the legacy archive; do not append to it.
Keep log contents, source references and thread IDs out of public commits and PRs.

```sh
fr() { python3 -I "<this skill's directory>/scripts/friction.py" "$@"; }
fr log < report.json       # validate, append, print the complete snapshot
fr check                   # validate every record and incident chain
fr check --actionable      # also require complete current incident reports
fr latest                  # current incident snapshots, as a JSON array
fr latest --include-context # also show archival context heads
```

Use the project's selected Mise Python. The script uses only the standard library.

## Report and follow up

Log only friction within the user's reporting rules, and give the same concise
account in the final reply: what happened, evidence, and a concrete improvement
suggestion. Preserve uncertainty. Do not invent a cause or claim a fix was verified
because the task finished.

A record is a complete snapshot of one incident. Each incident has a stable
`incident_id`; every report or follow-up has a unique `event_id`. For an update,
read `fr latest`, reuse the incident ID and original `origin`, and set
`previous_event_id` to its current event ID. Append the updated snapshot; never
rewrite an earlier record. The writer rejects stale updates. Re-read and reconcile
the evidence if another agent updated the incident first.

Use `open` for an established problem without a verified fix, `unverified` when the
problem or claimed fix needs confirmation, and `resolved` only with verified fix
evidence in `resolution`. A workaround belongs in `workaround`; it does not by
itself resolve the incident. Follow-ups may reopen an incident.

Use `canceled` when the user authorizes abandoning verification, including when
the necessary historical evidence is no longer available after a bounded audit.
Require `cancellation` with a concrete `reason` and nonempty `evidence` describing
the missing proof and checks performed. This is administrative closure, not a
verified fix; do not include `resolution` or convert the incident into context.
Keep issues with a feasible live verification path open or unverified. Canceled
incidents remain in `latest` and incident counts. To reopen one, append a new
snapshot with its new status and omit `cancellation`; retained history records
the earlier decision.

Use an existing incident ID when this is the same incident. Similar wording alone
does not establish identity. `latest` counts one snapshot per incident; raw line
counts include follow-ups and must not be reported as incident counts.

## Keep current reports actionable

Use a concise summary naming the complaint and its consequence, concrete evidence,
and a specific `suggestion`: the next command, source or proof needed for an open or
unverified report, or the prevention for a resolved one. A historical assertion of
resolution without independently checked fix evidence stays `unverified`. Preserve
partial fixes and remaining complaint components; do not close the whole report
because one component was repaired.

An imported heading, detached recommendation or explicit follow-up to another
incident is archival context, not another incident. Append a complete snapshot on
the fragment's existing chain with `record_type: "context"`, `kind: "other"`,
`status: null`, and `context_of: ["exact-existing-incident-id"]`. Preserve its
origin and cite the source establishing each link. Use `context_of: []` for
unattributed metadata; never invent a target from similar wording. Move meaningful
new evidence into a follow-up on the linked incident before archiving the fragment,
preserving uncertainty and each incident's original origin. Links must target
existing incident heads, never another context head or the fragment itself.

`latest` excludes context; `latest --include-context` retains access to every
chain head. `check` reports incident, context and total chain counts separately.
`check --actionable` also rejects incomplete current incidents and resolved heads
without fix proof. It leaves historical imports intact. This structural check
does not judge whether prose is useful or evidence actually proves a fix; read
both before accepting a cleanup. Existing records default to `record_type: "incident"`.

```json
{
  "incident_id": "cli-option-contract",
  "event_id": "cli-option-contract-report-1",
  "previous_event_id": null,
  "repo": null,
  "thread_id": "<reporting-thread-id>",
  "origin": {"thread_id": "<original-thread-id>", "event_ref": "<tool-call-reference>"},
  "kind": "tool",
  "subject": "example-cli search",
  "status": "open",
  "summary": "The documented option was rejected, requiring the query to be rerun.",
  "evidence": [{"ref": "<command-result>", "note": "The CLI returned unknown option."}],
  "workaround": "Used the supported option shown in help.",
  "suggestion": "Correct the skill example and verify it against the installed CLI."
}
```

Provide a stable event ID before the first attempt. Retrying the same completed
snapshot is a no-op; reusing its ID with a changed payload is rejected. Retain the
snapshot printed by `log`, including its generated timestamp, for retries. If a
write's acknowledgement was lost, inspect `latest` before retrying. The writer can
generate an event ID when omitted, but cannot make independently generated retries
share an identity.

## Version 1 schema

One UTF-8 JSON object per line. Unknown keys and wrong types are rejected, including
inside structured fields. New reports require the fields below unless marked
optional or generated. Omit unknown optional values or use null.

| Field | Type and meaning |
| --- | --- |
| `v` | Integer `1`; generated. |
| `event_id` | Nonempty string identifying this snapshot; generated if omitted. |
| `incident_id` | Nonempty stable incident ID. |
| `previous_event_id` | Prior event ID, or null for the first report; defaults to null. |
| `logged_at` | ISO 8601 UTC timestamp ending in `Z`; generated at append time. |
| `date` | UTC event date, `YYYY-MM-DD`; defaults to the logging date. Supply it for an earlier event. |
| `source` | `live` for new reports; generated. Only `port` produces `md-port`. |
| `repo` | Repository identity or null for work outside a repository. |
| `thread_id` | Reporting agent's conversation/thread ID. |
| `harness`, `model` | Optional nonempty strings identifying the reporter, when known. |
| `origin` | Object with original `thread_id` and `event_ref`; preserve on follow-up. Imported incidents may have an unknown original thread ID. |
| `kind` | `instructions`, `tool`, `environment`, `workflow`, or `other`. |
| `subject` | Optional specific skill, command, configuration, or workflow. |
| `status` | `open`, `resolved`, `unverified`, or `canceled`. |
| `summary` | Nonempty account of the event and its consequence. |
| `evidence` | Nonempty array of objects with nonempty `ref` and `note` strings. |
| `workaround` | Optional account of how the task proceeded despite the problem. |
| `resolution` | Object with `summary` and nonempty `evidence`, using the same reference format; required when a live report is resolved. |
| `cancellation` | Object with a nonempty `reason` and nonempty `evidence`; required only for canceled incidents and incompatible with `resolution`. Records why verification was abandoned, not a fix. |
| `suggestion` | Concrete improvement tied to the reported friction. |
| `record_type` | Optional `incident` (default) or `context` for archival fragments. |
| `context_of` | Required on context: distinct existing incident IDs, or an empty array for unattributed metadata. Forbidden on incidents. Context has `kind: "other"` and `status: null`. |
| `migration` | Imports only: source `file`, inclusive `line_start`/`line_end`, verbatim `original_text`, and a string array of extraction `notes`. |

The writer holds a stable sidecar lock through validation and append, flushes
writes, and refuses malformed or truncated existing logs. Individual records are
limited to 256 KiB. New files and content-addressed source snapshots are private
(mode 0600); keep archive directories private too. Consumers must respect the
sidecar lock if writing through another implementation.

## Markdown migration and late writers

```sh
fr port ~/.local/state/agent-friction.md \
  --archive-dir ~/.local/state/friction-migration/archive
fr check
# After an older session appends to Markdown:
fr port ~/.local/state/agent-friction.md \
  --archive-dir ~/.local/state/friction-migration/archive --reconcile
```

The source is left untouched. Each run retains its exact bytes in a
content-addressed Markdown snapshot. Every imported byte, including headings and
whitespace, belongs to a record's `original_text`. Its line range identifies the
original source location. Import IDs are deterministic from source position and
text; the first import's logging timestamp is reused for replay.

The conservative parser splits headings, explicit incident blocks, and clearly
independent prose bullets. Only explicit incident IDs link follow-ups. It extracts
unambiguous dates, reporter IDs, suggestions and statuses; other fields stay null
with extraction notes. It retains every claim in the original text. An imported
`resolved` status preserves a historical assertion, with an explicit note that its
fix proof has not been independently verified. Do not count unknown statuses as
open or resolved, or treat ambiguous generated IDs as proven distinct incidents.

Before live cutover, independently reconstruct the source from imported records,
compare the bytes and line ranges, inspect incident splitting/linking, run `check`,
and repeat the port to prove it changes nothing. Review the actual command and
recovery plan before executing. Recovery preserves both files and investigates;
never overwrite live events with a regenerated migration.

`--reconcile` preserves existing live records and historical boundaries, verifies
that the previous source is an unchanged byte prefix, and imports only appended
text. An appended fragment without its own heading retains an unknown date and
context in extraction notes; inspect it before interpreting it as a new incident.
A previous source ending mid-line, edits to old text, a changed source path, or a
legacy follow-up to an incident updated in JSONL is refused for explicit
reconciliation. Nothing is silently discarded. The source is checked again before
atomic destination replacement. A legacy writer may still append after that
check: keep the source and rerun reconciliation after known old writers finish;
a successful pass does not prove those sessions have stopped writing.
