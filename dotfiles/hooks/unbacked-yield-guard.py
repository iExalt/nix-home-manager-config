#!/usr/bin/env python3
"""Stop hook for Codex: block a turn that ends while native subagents are working and nothing wakes the agent.

A Codex root agent is not woken when a native subagent finishes or messages it; the message waits,
queued, until the root's next turn. A root that ends its turn after `spawn_agent` or `followup_task`
with no later FINAL_ANSWER from that agent therefore stalls until the user nudges it. This hook reads
the rollout named by `transcript_path`, replays the collaboration calls and the agent messages the
root has received, and blocks once (never when `stop_hook_active`) while any agent is still outstanding,
unless a `paseo heartbeat create` ran after the last spawn or follow-up.

Claude Code needs no equivalent: finished background agents and tasks re-invoke the parent, and its
transcript has no collaboration calls, so this script would always allow. It is wired for Codex only.

Fails open: any parse error, missing file, unknown format or time-out allows the stop (exit 0, no
output). Python 3.9 standard library only.
"""
import json
import os
import sys
import time

DEADLINE_S = 2.0
SPAWNS = {"spawn_agent": "task_name", "followup_task": "target", "assign_agent_task": "target"}
ENDS = {"close_agent", "interrupt_agent"}
# send_message does not start a turn, so it neither starts nor ends outstanding work.
INTERESTING = (b'"collaboration"', b'"agent_message"', b"heartbeat create")


def _child(own, value):
    """Full path of `value` when it is a direct child of `own`, else None (only a parent gets FINAL_ANSWER)."""
    path = str(value).rstrip("/")
    if not path.startswith("/"):
        path = own + "/" + path
    return path if path.rsplit("/", 1)[0] == own else None


def outstanding_agents(lines):
    """Names of agents spawned or resumed with no later FINAL_ANSWER, close or abort; plus heartbeat state."""
    out, calls, last_start, armed_at, own_from, own = {}, {}, -1, -1, 0, "/root"
    started = time.monotonic()
    for index, raw in enumerate(lines):
        if time.monotonic() - started > DEADLINE_S:
            raise TimeoutError
        if index == 0:  # a forked subagent's rollout opens with its parent's history; skip it
            meta = (json.loads(raw).get("payload") or {})
            own_from = meta.get("subagent_history_start_ordinal") or 0
            own = meta.get("agent_path") or "/root"
        is_candidate = any(token in raw for token in INTERESTING)
        if not is_candidate and not (calls and b"_output" in raw and any(cid in raw for cid in calls)):
            continue
        doc = json.loads(raw)
        if (doc.get("ordinal") or own_from) < own_from:
            continue
        payload = doc.get("payload") or {}
        kind = payload.get("type")
        if kind in ("function_call", "custom_tool_call"):
            name = payload.get("name")
            body = payload.get("arguments") or payload.get("input") or ""
            if payload.get("namespace") == "collaboration":
                args = json.loads(body) if isinstance(body, str) and body else {}
                if name in SPAWNS and args.get(SPAWNS[name]):
                    agent = _child(own, args[SPAWNS[name]])
                    if agent:
                        out[agent] = True
                        last_start = index
                        calls[payload["call_id"].encode()] = agent
                elif name in ENDS and args.get("target"):
                    out.pop(_child(own, args["target"]), None)
            elif "paseo heartbeat create" in str(body) and "--help" not in str(body):
                armed_at = index
        elif kind in ("function_call_output", "custom_tool_call_output"):
            agent = calls.pop(str(payload.get("call_id")).encode(), None)
            text = str(payload.get("output"))
            if agent and (text.startswith("aborted") or '"error"' in text[:200]):
                out.pop(agent, None)
        elif kind == "agent_message":
            parts = payload.get("content") or []
            head = next((p.get("text", "") for p in parts if p.get("type") == "input_text"), "")
            if "Message Type: FINAL_ANSWER" in head[:80]:
                out.pop(_child(own, payload.get("author", "")), None)
    return sorted(a.rsplit("/", 1)[-1] for a in out), armed_at > last_start


def decide(event, lines=None):
    if event.get("stop_hook_active"):
        return None
    path = event.get("transcript_path")
    if lines is None:
        if not path or not os.path.isfile(path):
            return None
        with open(path, "rb") as handle:
            return decide(event, handle)
    pending, armed = outstanding_agents(lines)
    if not pending or armed:
        return None
    names = ", ".join(pending)
    heartbeat = (" or arm a heartbeat with `paseo heartbeat create ...` (you run under Paseo)"
                 if os.environ.get("PASEO_AGENT_ID") else "")
    return {"decision": "block", "reason": (
        f"Native subagents still outstanding: {names}. Codex does not wake an idle root when they "
        "finish or message you; their messages wait for your next turn, so ending now stalls the work "
        f"until the user nudges you. Block on `wait_agent` (call it again on each timeout){heartbeat}, "
        "then continue. If you truly mean to hand control back, say what you are leaving running and "
        "why nothing needs you; this block fires only once.")}


def main():
    try:
        result = decide(json.load(sys.stdin))
        if result:
            sys.stdout.write(json.dumps(result))
    except Exception:  # fail open on anything unexpected
        pass


if __name__ == "__main__":
    main()
