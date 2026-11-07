# Glean, Slack and Linear CLI contracts

Read the relevant section before using these CLIs. These are user-owned
corrections to installed skill guidance. Glean and Slack skills are shipped
and managed by their CLI suite; the installed Linear skill comes from
`schpet/linear-cli` and generates its entrypoint from a template. Editing
those installed copies would be lost on reinstall or regeneration.

Check the installed command's `--help` for supported syntax. The Glean
requirements below come from observed backend errors; the installed help
does not document them. They are compatibility guidance, not a claim that
the CLI validates them. If the backend changes, use its current response
and report the difference.

## Glean

- Supply `--system` when retrieving a document with `get-file`. Choose the
  value from the document's datasource, such as `gdrive`, `sharepoint` or
  `confluence`; do not infer it from an unrelated search result. Omission
  has failed with `required flag(s) "system" not set`.
- Keep search `--limit` within the observed backend range of **3 through
  10**, inclusive. Larger values have failed with `page_size is out of
  range`. Use the returned cursor with `--cursor` for more results.

```bash
glean-cli search --query "release process" --limit 10 --output json
glean-cli get-file --system gdrive --file-url "https://docs.google.com/document/d/..."
```

## Slack

- Search with `slack-cli message search --output json`. Follow the returned
  pagination metadata: where `page_count` and the current page are
  supplied, request subsequent pages with `--page` until the last page;
  where normalized `metadata.pagination` is supplied, follow its
  continuation and exhaustion state. Inspect the actual response rather
  than assuming one fixed JSON nesting. A short page is not an exhaustion
  signal. If continuation is unclear, report incomplete coverage.
- Coordinate searches across workers using the same user account. Have
  one requester pace and dispatch that account's searches, sharing results
  with the other workers. Independent per-agent delays do not enforce a
  shared quota. Use returned `rate_limit` information rather than treating
  any historical numeric quota as permanent.
- On a retryable rate-limit error, pause the shared requester for the
  returned `retry_after_seconds` or `Retry-After` interval before retrying
  the same page. Keep retries bounded by the task's deadline; stop on a
  non-retryable error and retain the incomplete page range. Do not launch
  replacement searchers to evade the limit.

```bash
slack-cli message search --query "build failure" --limit 100 --page 1 --output json
```

## Linear

After a consequential mutation, read the entity back through a supported
read command before reporting success. A successful exit or creation
message alone has not proved that a requested relation exists.

- For issue fields, use `linear issue view <issue> --json` and compare the
  requested values with the returned values.
- For relations, use `linear issue relation list <issue>` and verify both
  issue endpoints, relation type and direction. For `A blocks B`, confirm
  that A blocks B; an edge in the reverse direction does not satisfy it.
- Use `linear api` for a read-only query only when the CLI read command
  omits the needed field, checking the supported schema first. Keep the
  same workspace and credentials for mutation and readback.

If the result is missing, contradictory or unreadable, report the mutation
as unverified and reconcile current state before retrying. A lost response
can follow a successful write; blind retries can duplicate it.
