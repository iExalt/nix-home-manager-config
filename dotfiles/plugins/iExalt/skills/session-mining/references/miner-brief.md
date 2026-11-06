# Miner brief template

Fill in the brackets and send one brief per manifest shard. Keep the question and the match
definition identical across shards so the results can be merged.

---

You are a miner for one shard of a session-history search. Do not spawn agents. Do not write report
files: return your findings as text in your final reply.

**Question:** [what we want to learn]
**A match is:** [precise definition, with one positive and one negative example]
**Out of scope:** [what to ignore]

**Your sessions:** shard [N] of `[manifest path]` (rows where the first column is [N]). Read only
those sessions.

**Tools:** define `sm() { python3 -I "[skill dir]/scripts/sessions.py" "$@"; }` (works in zsh and
bash). Use `sm show <session> [filters]` to read a session, with `--author human`, `--kind`,
`--match <regex>`, `--lines A:B`, `--last N` and `--subagents` to narrow or widen it, and
`--width 5000` to quote a whole event. Do not `cat`, `head`, `jq` or `rg` the JSONL files
themselves: a single line can be megabytes.

**Scratch:** if you need files, use `[scratch dir]/shard-[N]/` only.

**Return, as text:**
1. For each match: session id, `file:line`, a quote of at most 2 lines, and one sentence on why it
   matches. Quote the user only from `human` events.
2. Coverage: sessions read in full, sessions sampled (and how), sessions skipped (and why).
3. Anything that looked like a match but was not, with the reason (it calibrates the definition).

Redact secrets, tokens and personal data in quotes.
