"""Codex rollout JSONL -> events (see events.py).

Trimmed from the October 2026 transcript audit's codex_norm.py. What it keeps:
  * user text: a response_item message with role user is human-typed only when Codex also logged it
    as a UserMessage item (its "twin") or marked it user_input_order; otherwise it is injected
    context (AGENTS.md, environment, skills). Paseo envelopes become agent or harness events.
  * forks: records inherited from the parent (between a second session_meta and the next
    thread_settings_applied, or marked inherited_user_message) are skipped.
  * guardian auto-review rollouts are skipped unless include_guardian=True: they re-quote whole
    transcripts of other sessions.
  * user decisions: async question replies, "Answers to your questions:", verified answers and
    interrupts become author=human, kind=decision.
  * skill invocations: an injected <skill><name>X</name> block marks skill X.
What it drops: guardian verdict joins, the provenance index and the authority ledger.

The file is read twice (twins first, then events), streaming, so memory stays flat on huge rollouts.
"""
from __future__ import annotations

import json
import re
from typing import Dict, Iterator, Optional

from .events import event, input_summary

INJECTED_PREFIXES = (
    "# AGENTS.md instructions", "<environment_context>", "<skill>", "<external_codex_apps_open_page>",
    "<recommended_plugins>", "<user_instructions>", "<permissions", "<collaboration_mode>",
    "<codex_internal_context>", "<turn_aborted>",
)
HARNESS_PREFIXES = ("<heartbeat>", "Automation:", "<chat-history-summary>")
PASEO_RE = re.compile(r"<paseo-system\s+([^>]*)>(.*?)</paseo-system>", re.S)
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
SKILL_RE = re.compile(r"\s*<skill>\s*<name>([^<]+)</name>")
CMD_ANY_RE = re.compile(r"""cmd:\s*(?:("(?:[^"\\]|\\.)*")|'((?:[^'\\]|\\.)*)'|`((?:[^`\\]|\\.)*)`)""")
TOOL_RE = re.compile(r"tools\.([A-Za-z_][\w]*)\s*\(")
# Record types prose mode never parses (tool output, reasoning), and types no mode emits.
PROSE_SKIP_TYPES = (b'"type":"function_call_output"', b'"type":"custom_tool_call_output"', b'"type":"reasoning"')
NEVER_TYPES = (b'"type":"token_count"', b'"type":"turn_context"', b'"type":"world_state"')


def _ctext(content) -> str:
    if isinstance(content, str):
        return content
    out = []
    for c in content or []:
        if not isinstance(c, dict):
            continue
        t = c.get("type")
        if t in ("input_text", "output_text", "text", "Text"):
            out.append(c.get("text", ""))
        elif t == "encrypted_content":
            out.append("[encrypted payload]")
        elif t in ("input_image", "local_image", "image"):
            out.append("[image]")
    return "\n".join(out)


def _key(t: str) -> str:
    return re.sub(r"\s+", "", t or "")[:120]


def _items_text(v) -> str:
    if not v:
        return ""
    if isinstance(v, str):
        return v
    return "\n".join((x if isinstance(x, str) else (x.get("text") or x.get("summary_text") or ""))
                     for x in v if isinstance(x, (str, dict)))


def _cmd_of(command) -> Optional[str]:
    if isinstance(command, list):
        if len(command) >= 3 and command[1] in ("-lc", "-c"):
            return command[2]
        return " ".join(str(c) for c in command)
    return command if isinstance(command, str) else None


def _js_string(m) -> str:
    """A cmd: "..." / '...' / `...` literal from a JavaScript exec script, unescaped best-effort."""
    if m.group(1):
        try:
            return json.loads(m.group(1))
        except ValueError:
            return m.group(1)[1:-1]
    return m.group(2) if m.group(2) is not None else (m.group(3) or "")


def is_guardian_meta(meta: dict) -> bool:
    src = meta.get("source")
    return isinstance(src, dict) and "guardian" in json.dumps(src)


def _twins(path: str):
    """Pass 1. Returns (twins, user_keys): twins maps a normalized text key to the client_id flags of
    UserMessage items with that text; user_keys counts response_item user messages per key, so
    UserMessage items without a response_item (orphans) can be emitted themselves."""
    twins: Dict[str, list] = {}
    user_keys: Dict[str, int] = {}
    with open(path, "rb") as fh:
        for raw in fh:
            head = raw[:400]
            is_um = b'"UserMessage"' in head or b'"user_message"' in head
            is_user = b'"role":"user"' in head and b'"response_item"' in head
            if not (is_um or is_user):
                continue
            try:
                d = json.loads(raw)
            except ValueError:
                continue
            p = d.get("payload") or {}
            if p.get("type") == "item_completed":
                it = p.get("item") or {}
                if it.get("type") == "UserMessage":
                    twins.setdefault(_key(_um_text(it)), []).append("client_id" in it)
            elif p.get("type") == "user_message":
                twins.setdefault(_key(p.get("message") or ""), []).append(False)
            elif p.get("type") == "message" and p.get("role") == "user":
                k = _key(_ctext(p.get("content")))
                user_keys[k] = user_keys.get(k, 0) + 1
    return twins, user_keys


def _um_text(it: dict) -> str:
    return "\n".join(c.get("text", "") for c in it.get("content") or [] if isinstance(c, dict)
                     and c.get("type") == "text")


def iter_events(path: str, prose: bool = False, launched: Optional[str] = None,
                include_guardian: bool = False, stats: Optional[Dict[str, int]] = None) -> Iterator[dict]:
    """Events of one Codex rollout file in file order. launched says who wrote the first prompt, from
    reader.paseo_launchers(): "human", "agent", "schedule", or None for no Paseo record."""
    st = stats if stats is not None else {}
    with open(path, "rb") as fh:
        first = fh.readline()
    try:
        meta = (json.loads(first).get("payload") or {}) if first else {}
    except ValueError:
        meta = {}
    if is_guardian_meta(meta) and not include_guardian:
        st["guardian_skipped"] = st.get("guardian_skipped", 0) + 1
        return
    thread = meta.get("id") or meta.get("session_id")
    originator = meta.get("originator") or ""
    sub_source = isinstance(meta.get("source"), dict)
    twins, user_keys = _twins(path)
    user_inputs = 0
    calls: Dict[str, str] = {}
    open_calls = set()
    metas = 0
    inheriting = False

    def ev(d, ln, kind, author, text="", **kw):
        return event("codex", thread, path, ln, d.get("timestamp"), kind, author, text, **kw)

    with open(path, "rb") as fh:
        for ln, raw in enumerate(fh, 1):
            head = raw[:300]
            if prose and (any(t in head for t in PROSE_SKIP_TYPES) or
                          (b'"item_completed"' in head and b'"UserMessage"' not in head)):
                continue
            if any(t in head for t in NEVER_TYPES):
                continue
            try:
                d = json.loads(raw)
            except ValueError:
                st["unparsable"] = st.get("unparsable", 0) + 1
                continue
            if not isinstance(d, dict):
                continue
            t = d.get("type")
            p = d.get("payload") or {}
            pt = p.get("type") if isinstance(p, dict) else None
            if t == "session_meta":
                metas += 1
                if metas == 2:
                    inheriting = True              # a fork: the parent's history follows
                continue
            if inheriting:
                if t == "event_msg" and pt == "thread_settings_applied":
                    inheriting = False
                st["inherited_skipped"] = st.get("inherited_skipped", 0) + 1
                continue
            if (d.get("metadata") or {}).get("inherited_user_message"):
                continue
            if t == "compacted":
                yield ev(d, ln, "compaction", "harness", p.get("message") or "context compacted")
                continue
            if t == "retained_context" and pt == "verified_answer":
                qa = "; ".join("%s -> %s" % (q.get("question"), q.get("answer")) for q in p.get("questions", []))
                yield ev(d, ln, "decision", "human", "answered: " + qa, basis="verified_answer")
                continue
            if t == "event_msg":
                if pt == "turn_aborted" and p.get("reason") == "interrupted":
                    yield ev(d, ln, "decision", "human", "interrupted the turn", basis="turn_aborted")
                elif pt == "item_completed":
                    it = p.get("item") or {}
                    k = it.get("type")
                    if k == "UserMessage":
                        text = _um_text(it)
                        key = _key(text)
                        if user_keys.get(key):
                            user_keys[key] -= 1    # emitted with its response_item twin
                        else:
                            yield ev(d, ln, "prompt", "human", text, uuid=it.get("id"),
                                     basis="user_message_without_response_item")
                    elif k == "CommandExecution" and not prose and not open_calls:
                        # Inside an open exec/function call its output arrives as that call's result;
                        # emit CommandExecution only when no call is open (an orphan command).
                        yield ev(d, ln, "tool_result", "tool", it.get("aggregated_output") or "",
                                 tool="exec_command", command=_cmd_of(it.get("command")),
                                 is_error=it.get("status") == "failed" or bool(it.get("exit_code")))
                continue
            if t != "response_item":
                continue
            role = p.get("role")
            if pt == "message" and role == "assistant":
                yield ev(d, ln, "reply", "assistant", _ctext(p.get("content")), uuid=p.get("id"))
            elif pt == "message" and role == "developer":
                yield ev(d, ln, "prompt", "injected", _ctext(p.get("content")), uuid=p.get("id"),
                         basis="developer_role")
            elif pt == "message" and role == "user":
                text = _ctext(p.get("content"))
                lst = twins.get(_key(text))
                twin = lst.pop(0) if lst else None
                md = d.get("metadata") or {}
                if twin is not None or "user_input_order" in md:
                    user_inputs += 1
                for e in _user_events(ev, d, ln, p, text, twin, md, user_inputs == 1, originator, sub_source,
                                      launched):
                    yield e
            elif pt == "agent_message":
                yield ev(d, ln, "prompt", "agent", _ctext(p.get("content")), uuid=p.get("id"),
                         basis="inter_agent")
            elif pt == "reasoning":
                text = (_items_text(p.get("summary")) + "\n" + _items_text(p.get("content"))).strip()
                if text:
                    yield ev(d, ln, "thinking", "assistant", text, uuid=p.get("id"))
            elif pt in ("function_call", "custom_tool_call"):
                name = p.get("name")
                calls[p.get("call_id")] = name
                open_calls.add(p.get("call_id"))
                if pt == "function_call":
                    try:
                        args = json.loads(p.get("arguments") or "{}")
                    except ValueError:
                        args = p.get("arguments")
                    cmd = _cmd_of(args.get("cmd") or args.get("command")) if isinstance(args, dict) else None
                    yield ev(d, ln, "tool_call", "assistant", input_summary(args), tool=name, command=cmd,
                             uuid=p.get("id"))
                else:
                    script = p.get("input") or ""
                    cmds = [_js_string(m) for m in CMD_ANY_RE.finditer(script)]
                    tools = sorted(set(TOOL_RE.findall(script)))
                    tool = name if name != "exec" else (tools[0] if len(tools) == 1 else "exec")
                    calls[p.get("call_id")] = tool
                    yield ev(d, ln, "tool_call", "assistant", script, tool=tool,
                             command="\n".join(c for c in cmds if isinstance(c, str)) or None, uuid=p.get("id"))
            elif pt in ("function_call_output", "custom_tool_call_output"):
                open_calls.discard(p.get("call_id"))
                if prose:
                    continue
                out = p.get("output")
                text = _ctext(out) if isinstance(out, list) else (out if isinstance(out, str) else json.dumps(out))
                yield ev(d, ln, "tool_result", "tool", text, tool=calls.get(p.get("call_id")))


def _user_events(ev, d, ln, p, text, twin, md, first, originator, sub_source, launched):
    t = text.lstrip()
    if t.startswith("<send_user_message_question_reply>"):
        body = t.split(">", 1)[1].rsplit("</send_user_message_question_reply>", 1)[0].strip()
        try:
            items = json.loads(body)
            body = "; ".join("%s -> %s" % (i.get("question"), i.get("answer")) for i in items)
        except (ValueError, AttributeError):
            pass
        yield ev(d, ln, "decision", "human", "answered: " + body, uuid=p.get("id"), basis="question_reply")
        return
    if t.startswith("<paseo-system"):
        for attrs, body in PASEO_RE.findall(text) or [("", text)]:
            a = dict(ATTR_RE.findall(attrs))
            author = "harness" if a.get("kind") == "agent-notification" else "agent"
            yield ev(d, ln, "prompt", author, body.strip(), uuid=p.get("id"), basis="paseo_" + (a.get("kind") or "?"))
        return
    if t.startswith("Answers to your questions:"):
        yield ev(d, ln, "decision", "human", text, uuid=p.get("id"), basis="question_answers_text")
        return
    if t.startswith(INJECTED_PREFIXES):
        m = SKILL_RE.match(text)
        yield ev(d, ln, "prompt", "injected", text, uuid=p.get("id"), basis="injected_prefix",
                 skill=m.group(1).strip() if m else None)
        return
    if t.startswith(HARNESS_PREFIXES):
        yield ev(d, ln, "prompt", "harness", text, uuid=p.get("id"), basis="automation")
        return
    if twin is None and "user_input_order" not in md:
        yield ev(d, ln, "prompt", "injected", text, uuid=p.get("id"), basis="no_user_message_twin")
        return
    if twin:
        author, basis = "human", "client_id"
    elif originator == "codex_exec":
        author, basis = "agent", "codex_exec_prompt"
    elif first and launched == "schedule":
        author, basis = "harness", "paseo_scheduled_first_prompt"
    elif first and launched == "agent":
        author, basis = "agent", "paseo_launched_first_prompt"
    elif sub_source and launched is None and (first or originator == "Codex Desktop"):
        # A spawned sub-agent's messages come from its parent agent. Codex Desktop marks UI-typed
        # messages with client_id (handled above), so a Desktop follow-up without one is the parent's.
        author, basis = "agent", "subagent_first_message" if first else "subagent_followup"
    elif sub_source and launched is None:
        author, basis = "human", "subagent_followup_maybe_agent"     # codex-tui: either is possible
    else:
        author, basis = "human", "user_message_twin"
    yield ev(d, ln, "prompt", author, text, uuid=p.get("id"), basis=basis)
