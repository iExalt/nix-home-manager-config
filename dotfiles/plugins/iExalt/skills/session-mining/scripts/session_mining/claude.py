"""Claude Code transcript JSONL -> events (see events.py).

Trimmed from the October 2026 transcript audit's claude_norm.py: it keeps record selection, in-file
replay dedup, author classification (including user decisions recorded in tool results) and skill
invocation detection. It drops the audit's authority ledger, provenance index and rewind-branch
analysis: rewound turns are emitted like any other.

Cross-file duplicates (resumed or forked sessions copy earlier records into a new file) are not
removed here; callers dedup hits by (provider, uuid) with owner_rank().
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, Iterator, Optional, Set

from .events import PROSE_SKIP_BYTES, event, flatten, input_summary

SKIP_TYPES = (
    "api-request-blob", "api-request-shape", "api-request", "atis-latch", "file-history-snapshot",
    "file-history-delta", "cost-state", "tools-used", "pr-link", "mode", "permission-mode",
    "agent-name", "custom-title", "ai-title", "started", "launched", "result", "worktree-state",
    "continued-in", "summary", "last-prompt",
)
_SKIP_PREFIXES = tuple(('{"type":"%s"' % t).encode() for t in SKIP_TYPES)

SKIP_ATTACHMENTS = {
    "total_tokens_reminder", "deferred_tools_record", "deferred_tools_delta", "environment", "date",
    "model", "skill_listing", "agent_listing_delta", "mcp_instructions_delta", "prompt_snapshot",
    "session_context", "credential_org", "silent_turn_reminder", "thinking_drop", "edited_text_file",
    "file", "compact_file_reference", "auto_mode", "command_permissions", "task_reminder",
    "task_status", "read_truncation_notice", "already_read_file", "directory", "plan_file_reference",
    "session_cron_carry", "unknown_command_fallback",
}

BUILTIN_SLASH = {
    "compact", "model", "login", "logout", "clear", "help", "config", "resume", "context", "cost",
    "status", "init", "exit", "mcp", "permissions", "vim", "theme", "terminal-setup", "ide", "usage",
    "agents", "autocompact", "hooks", "memory", "doctor", "bug", "rewind", "export", "rename", "plan", "fast",
    "effort", "add-dir", "release-notes", "statusline", "output-style", "todos", "tasks", "bashes",
}

INTERRUPT = "[Request interrupted"
HARNESS_PREFIXES = (
    "<task-notification", "[SYSTEM NOTIFICATION", "<system-reminder", "<local-command-", "[Image:",
    "[handback-", "[Cross-session", "[Your previous response had no visible", "<command-stdout",
    "Caveat:", "<cross-session", "This session is being continued from a previous conversation",
)
AGENT_PREFIXES = (
    "[overseer]", "Another Claude session sent a message", "The coordinator sent a message",
    "[Workflow harness", "<agent-message",
)
SLASH_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
SHELL_TOOLS = ("Bash", "PowerShell")


def slash_command(text: str) -> Optional[str]:
    m = SLASH_RE.search(text[:2000])
    return m.group(1) if m else None


def classify_user_text(text: str, rec: dict, in_subagent: bool, first_prompt: bool, launched: Optional[bool]):
    """(author, basis). Ordered rules; the first match wins."""
    t = text.lstrip()
    o = rec.get("origin")
    origin = o.get("kind") if isinstance(o, dict) else None
    if origin == "human":
        return "human", "origin_human"
    if origin in ("peer", "coordinator"):
        return "agent", "origin_" + origin
    if origin == "task-notification":
        return "harness", "origin_task_notification"
    if rec.get("isCompactSummary"):
        return "harness", "compact_summary"
    if t.startswith(INTERRUPT):
        return "harness", "interrupt_marker"
    if t.startswith(HARNESS_PREFIXES):
        return "harness", "harness_prefix"
    if t.startswith("<paseo-system"):
        if 'kind="agent-message"' in t[:120]:
            return "agent", "paseo_agent_message"
        return "harness", "paseo_system"
    if t.startswith("Base directory for this skill"):
        return "injected", "skill_expansion"
    if t.startswith(AGENT_PREFIXES):
        return "agent", "agent_prefix"
    if rec.get("isMeta"):
        return "harness", "is_meta"
    if in_subagent:
        return "agent", "subagent_prompt"
    if t.startswith(("<command-name>", "<command-message>")):
        return "human", "slash_command"
    if first_prompt and rec.get("entrypoint") == "sdk-cli" and rec.get("promptSource") == "sdk":
        # An SDK session's first prompt: typed by the user in Paseo (record without a parent label),
        # written by another agent (parent or overseer label), or sent by a script (no Paseo record).
        if launched is None:
            return "agent", "sdk_first_prompt_without_paseo_record"
        if launched:
            return "agent", "paseo_launched_first_prompt"
    return "human", "plain_text"


def _decision(name: str, text: str, tur, is_error: bool) -> Optional[str]:
    """Text of a user decision recorded in a tool result, or None."""
    rejected = is_error and (text.startswith("The user doesn't want to proceed") or
                             text.startswith("User rejected tool use") or text.startswith("Dismissed by user"))
    if name == "AskUserQuestion" and isinstance(tur, dict) and tur.get("answers") is not None:
        ans = tur.get("answers") or {}
        return "answered: " + "; ".join("%s -> %s" % (q, a if not isinstance(a, list) else ", ".join(map(str, a)))
                                        for q, a in ans.items())
    if name == "ExitPlanMode" and not is_error and text.startswith("User has approved"):
        return "plan approved"
    if rejected:
        return "rejected %s: %s" % (name or "tool", text)
    return None


def iter_events(path: str, session: Optional[str] = None, in_subagent: Optional[bool] = None,
                prose: bool = False, launched: Optional[bool] = False,
                stats: Optional[Dict[str, int]] = None) -> Iterator[dict]:
    """Events of one Claude transcript file in file order.

    prose=True skips tool output: lines over PROSE_SKIP_BYTES that carry a tool result are not parsed
    and tool_result events are not emitted (user decisions in tool results still are).
    launched describes who started the session, for its SDK first prompt: True = another agent (Paseo
    parent or overseer label), False = the user in Paseo, None = no Paseo record (a script; agent).
    """
    if in_subagent is None:
        in_subagent = os.sep + "subagents" + os.sep in path
    if session is None:
        stem = os.path.basename(path)[:-6]
        session = stem[6:] if in_subagent and stem.startswith("agent-") else stem
    st = stats if stats is not None else {}
    calls: Dict[str, dict] = {}
    seen: Set[str] = set()
    seen_assistant = False

    def ev(d, ln, kind, author, text="", **kw):
        return event("claude", session, path, ln, d.get("timestamp"), kind, author, text,
                     uuid=d.get("uuid"), rec_session=d.get("sessionId"), **kw)

    with open(path, "rb") as fh:
        for ln, raw in enumerate(fh, 1):
            if raw.startswith(_SKIP_PREFIXES):
                continue
            if prose and len(raw) > PROSE_SKIP_BYTES and b'"tool_use_id"' in raw:
                st["skipped_tool_output"] = st.get("skipped_tool_output", 0) + 1
                continue
            try:
                d = json.loads(raw)
            except ValueError:
                st["unparsable"] = st.get("unparsable", 0) + 1     # e.g. a live file's partial last line
                continue
            if not isinstance(d, dict):
                continue
            t = d.get("type")
            if t not in ("user", "assistant", "attachment", "system"):
                continue
            u = d.get("uuid")
            if u:
                if u in seen:
                    continue                                    # replayed in the same file
                seen.add(u)
            if t == "assistant":
                seen_assistant = True
                msg = d.get("message") or {}
                content = msg.get("content")
                if isinstance(content, str):
                    content = [{"type": "text", "text": content}]
                for b in content or []:
                    if not isinstance(b, dict):
                        continue
                    bt = b.get("type")
                    if bt == "text" and b.get("text", "").strip():
                        yield ev(d, ln, "reply", "assistant", b["text"])
                    elif bt == "thinking" and b.get("thinking", "").strip():
                        yield ev(d, ln, "thinking", "assistant", b["thinking"])
                    elif bt == "tool_use":
                        name, inp = b.get("name"), b.get("input")
                        calls[b.get("id")] = {"name": name, "input": inp}
                        skill = (inp or {}).get("skill") if name == "Skill" and isinstance(inp, dict) else None
                        cmd = inp.get("command") if name in SHELL_TOOLS and isinstance(inp, dict) else None
                        yield ev(d, ln, "tool_call", "assistant", input_summary(inp), tool=name, command=cmd,
                                 skill=skill, call_id=b.get("id"))
            elif t == "user":
                content = (d.get("message") or {}).get("content")
                blocks = content if isinstance(content, list) else None
                results = [b for b in blocks or [] if isinstance(b, dict) and b.get("type") == "tool_result"]
                if results:
                    for b in results:
                        call = calls.get(b.get("tool_use_id"), {})
                        name = call.get("name")
                        text = flatten(b.get("content"))
                        dec = _decision(name, text, d.get("toolUseResult"), bool(b.get("is_error")))
                        if dec:
                            yield ev(d, ln, "decision", "human", dec, tool=name, basis="tool_result_decision")
                        elif not prose:
                            yield ev(d, ln, "tool_result", "tool", text, tool=name,
                                     is_error=bool(b.get("is_error")))
                    continue
                text = flatten(content)
                if not text.strip():
                    continue
                author, basis = classify_user_text(text, d, in_subagent, not seen_assistant, launched)
                cmd = slash_command(text) if author == "human" else None
                skill = cmd if cmd and cmd not in BUILTIN_SLASH else None
                yield ev(d, ln, "prompt", author, text, basis=basis, skill=skill)
            elif t == "attachment":
                a = d.get("attachment") or {}
                at = a.get("type")
                if at in SKIP_ATTACHMENTS:
                    continue
                if at == "queued_command":
                    p = a.get("prompt")
                    text = p if isinstance(p, str) else flatten(p)
                    dd = dict(d, origin=a.get("origin") or d.get("origin"))
                    author, basis = classify_user_text(text, dd, in_subagent, False, launched)
                    cmd = slash_command(text) if author == "human" else None
                    yield ev(d, ln, "prompt", author, text, basis="queued:" + basis,
                             skill=cmd if cmd and cmd not in BUILTIN_SLASH else None)
                elif at == "instructions":
                    files = a.get("files") or []
                    text = "\n\n".join("[%s %s]\n%s" % (f.get("type"), f.get("path"), f.get("content", ""))
                                       for f in files)
                    yield ev(d, ln, "prompt", "injected", text, basis="instructions_attachment")
                elif at == "nested_memory":
                    c = a.get("content") or {}
                    yield ev(d, ln, "prompt", "injected", "[%s %s]\n%s" % (c.get("type"), a.get("path"),
                                                                           c.get("content", "")),
                             basis="nested_memory")
                elif at == "invoked_skills":
                    sk = a.get("skills") or []
                    yield ev(d, ln, "prompt", "injected",
                             "\n\n".join("[skill %s]\n%s" % (s.get("name"), s.get("content", "")) for s in sk),
                             basis="invoked_skills")
                elif at == "hook_additional_context":
                    yield ev(d, ln, "prompt", "injected", flatten(a.get("content")), basis="hook_context")
            elif t == "system":
                stp = d.get("subtype")
                if stp == "compact_boundary":
                    yield ev(d, ln, "compaction", "harness", "compact_boundary")
                elif stp in ("local_command", "away_summary", "informational", "api_error"):
                    yield ev(d, ln, "system", "harness", "%s %s" % (stp, flatten(d.get("content"))))


def owner_rank(path: str, record_session: Optional[str], first_ts: Optional[str]) -> tuple:
    """Sort key choosing which file owns a uuid present in several files: the file named after the
    record's sessionId (for subagents, the parent session directory), then the earliest first
    timestamp, then the path. The audit's further 'earliest last timestamp' tie-break is dropped on
    purpose: two files with the same name match and the same first timestamp are fork copies whose
    content is identical up to the shared record."""
    parts = path.split(os.sep)
    name = parts[-1][:-6]
    owner_sid = parts[parts.index("subagents") - 1] if "subagents" in parts else name
    return (0 if record_session and owner_sid == record_session else 1, first_ts or "~", path)
