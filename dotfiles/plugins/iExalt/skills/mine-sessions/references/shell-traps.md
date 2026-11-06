# Shell traps when touching transcripts directly

Past miners lost time to each of these. Prefer the CLI; when you must use the shell:

- **Lines, not bytes.** `head`, `tail`, `sed -n` and `rg -n` limit lines, and one JSONL line can be
  several megabytes. Cap bytes instead: `cut -c1-300`, `rg -o '.{0,120}pattern.{0,120}'`, or `rg -l`.
- **zsh.** A word starting with `=` expands (`= not found`); quote it. An unmatched glob aborts the
  command (`no matches found`); use `fd` or `(N)` glob qualifiers. Keep argument lists in arrays.
- **BSD tools on macOS.** `stat -c`, `date -d` and `sed -i ''` differ from GNU. Claude project
  directories start with `-`, so pass `--` before paths (`stat -- -Users-...` fails otherwise).
- **rg flags.** `rg -E` sets the encoding, not extended regex. Use `-g '*.jsonl'` to skip
  `tool-results/*.txt` and `memory/*.md`, which also contain session ids.
- **JSON escaping.** In the raw file, quotes are `\"`, newlines are `\n` and tabs `\t`. A pattern that
  spans a line break or a quote matches the parsed text, not the raw line.
- **jq on NDJSON.** Use `jq -c 'select(...)'` per line; `jq '.[]'` on a JSONL file prints nothing.
- **Python.** Run with `-I` and stream line by line; never `read()` a rollout (some exceed 500 MB).
  f-strings cannot contain backslashes before Python 3.12. `glob` does not expand `{a,b}` braces and
  returns nothing silently.
- **Live files.** Sessions still running grow while you read them; snapshot (`cp`) a file before
  citing line numbers across a long job.
