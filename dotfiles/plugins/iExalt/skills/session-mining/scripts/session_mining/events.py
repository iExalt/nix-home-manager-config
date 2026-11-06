"""The normalized event shared by the Claude and Codex readers, and its compact rendering.

Event (plain dict):
  provider  "claude" | "codex"
  session   Claude session id (agent id for a subagent file) or Codex thread id
  file      absolute path of the transcript file; line is its 1-based physical line
  ts        ISO-8601 string or None
  kind      prompt | reply | thinking | tool_call | tool_result | decision | compaction | system
  author    human | agent | injected | harness | assistant | tool
            human     typed by the user, or a user decision recorded by the harness (question answers,
                      plan approval or rejection, permission rejection)
            agent     another agent's message: subagent brief, Paseo agent message, peer, relay
            injected  instructions the harness inserted: skill bodies, AGENTS.md/CLAUDE.md, hook context
            harness   notifications, reminders, interrupts, compaction summaries
  text      the event's text (tool_call: a one-line summary of the input)
  tool      tool name for tool_call / tool_result
  command   shell command for shell tool calls
  skill     skill name when the event invokes a skill (slash command, Skill tool call, Codex marker)
  uuid      provider record id when present (used for cross-file dedup)
  basis     why the author was chosen (rule name)
"""
from __future__ import annotations

import json
import time
from typing import Iterable, Optional

from .out import Out, clip

KINDS = ("prompt", "reply", "thinking", "tool_call", "tool_result", "decision", "compaction", "system")
AUTHORS = ("human", "agent", "injected", "harness", "assistant", "tool")

# Lines longer than this that carry tool output are skipped unparsed in prose mode.
PROSE_SKIP_BYTES = 64 * 1024


def event(provider, session, path, line, ts, kind, author, text="", **kw) -> dict:
    e = {"provider": provider, "session": session, "file": path, "line": line, "ts": ts, "kind": kind,
         "author": author, "text": text or "", "tool": None, "command": None, "skill": None, "uuid": None,
         "basis": None}
    e.update(kw)
    return e


def flatten(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if isinstance(b, dict):
                t = b.get("type")
                if t in ("text", "input_text", "output_text"):
                    out.append(b.get("text", ""))
                elif t in ("image", "input_image"):
                    out.append("[image]")
                elif t == "tool_reference":
                    out.append("[tool_reference %s]" % b.get("tool_name", ""))
                else:
                    out.append(json.dumps(b, ensure_ascii=False))
            else:
                out.append(str(b))
        return "\n".join(out)
    return "" if content is None else json.dumps(content, ensure_ascii=False)


def input_summary(inp) -> str:
    if isinstance(inp, dict):
        for k in ("command", "cmd", "file_path", "path", "pattern", "query", "url", "skill", "prompt",
                  "description"):
            v = inp.get(k)
            if isinstance(v, (str, list)) and v:
                return "%s=%s" % (k, v if isinstance(v, str) else " ".join(map(str, v)))
        return json.dumps(inp, ensure_ascii=False)
    return "" if inp is None else str(inp)


def _hhmm(ts: Optional[str]) -> str:
    return ts[5:16].replace("T", " ") if ts and len(ts) >= 16 else "--"


def render(events: Iterable[dict], out: Out, width: int = 160, show_file: bool = True) -> int:
    """One line per event: 'L<line> <MM-DD hh:mm> author/kind [tool|skill] text'. Returns count shown."""
    n = 0
    cur = None
    for e in events:
        if show_file and e["file"] != cur:
            cur = e["file"]
            if not out.line("== %s (%s %s)" % (cur, e["provider"], e["session"])):
                break
        tag = e.get("skill") and "skill:%s" % e["skill"] or e.get("tool") or ""
        head = "L%-6d %s %s/%s%s " % (e["line"], _hhmm(e.get("ts")), e["author"], e["kind"],
                                      " [%s]" % tag if tag else "")
        if not out.line(head + clip(e.get("command") or e["text"], max(20, width - len(head)))):
            break
        n += 1
    return n


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
