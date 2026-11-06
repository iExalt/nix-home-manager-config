# Configuration

`~/.config/self-review/config.json` is private. Every value below is an example.

```json
{
  "name": "Sam Example",
  "handles": {
    "chat": "U000EXAMPLE",
    "email": "sam@example.com",
    "code_host": "sam-example",
    "tracker": "sam"
  },
  "chain": ["Manager Name", "Skip-level Name"],
  "output_dir": "~/work/reviews",
  "miner_model": "haiku",
  "sources": [
    {"name": "code", "how": "gh search prs --author sam-example; reviews with --reviewed-by"},
    {"name": "tracker", "how": "tracker CLI or MCP; issues created, assigned, closed"},
    {"name": "chat", "how": "chat search MCP; from:me, mentions of me, thanks and praise"},
    {"name": "email", "how": "mail CLI; commendations, forwards up the chain"},
    {"name": "meetings", "how": "meeting CLI; recordings and transcripts of talks and demos"},
    {"name": "docs", "how": "drive and wiki CLIs; slides, design docs, decision records"},
    {"name": "sessions", "how": "session-mining skill; what the user built with agents"}
  ],
  "forms": {
    "self": {
      "tool": "the review tool's name",
      "questions": ["What are your key contributions?", "What are your challenges?", "What are your goals?"],
      "word_limit": null,
      "export": "plain"
    },
    "peer": {
      "tool": "the review tool's name",
      "questions": ["What does this person do well?", "What could they do more of or differently?"],
      "word_limit": null,
      "export": "plain"
    }
  }
}
```

- `sources[].how` tells miners which CLI, MCP tool or skill to use and any flags that matter. Add
  notes the miners need, such as a CLI's JSON path or a known output quirk.
- `forms` holds the questions exactly as the tool shows them. Ask the user to paste them the first
  time a form is used.
- `chain` is the user's management chain; email and chat miners use it to spot commendations
  forwarded upward.
- `export` is `plain`, the only format the exporter writes. If a tool accepts Markdown, paste the
  draft body above the appendix instead.
