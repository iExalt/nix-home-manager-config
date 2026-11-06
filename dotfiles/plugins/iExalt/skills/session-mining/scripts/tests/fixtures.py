"""Synthetic stores for tests. Every id, path and text here is invented."""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile

# UUIDv7-style ids that share a 13-character timestamp prefix, as real Codex ids do.
T1 = "01a00000-1111-7000-8000-000000000001"
T2 = "01a00000-1111-7000-8000-00000000c0de"
T1_SEG = "01a00000-2222-7000-8000-00000000000a"
T_ARCH = "01a00009-0000-7000-8000-0000000000aa"
T_GUARD = "01a00009-0000-7000-8000-0000000000bb"
C1 = "c1c1c1c1-0000-4000-8000-000000000001"
C2 = "c2c2c2c2-0000-4000-8000-000000000002"
C_PRUNED = "deadbeef-0000-4000-8000-000000000003"
AGENT = "a0123456789abcdef"
P1 = "e1e1e1e1-0000-4000-8000-000000000001"
P2 = "f2f2f2f2-0000-4000-8000-000000000002"

PROJ = "-tmp-demo-project"


def write_jsonl(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write((r if isinstance(r, str) else json.dumps(r)) + "\n")


def make_roots(tmp=None):
    """Build claude/, codex/ and paseo/ homes; returns (claude, codex, paseo) paths."""
    tmp = tmp or tempfile.mkdtemp(prefix="sm-test-")
    claude, codex, paseo = (os.path.join(tmp, n) for n in ("claude", "codex", "paseo"))
    proj = os.path.join(claude, "projects", PROJ)
    write_jsonl(os.path.join(proj, C1 + ".jsonl"), [{"type": "user", "sessionId": C1}])
    write_jsonl(os.path.join(proj, C2 + ".jsonl"), [{"type": "user", "sessionId": C2}])
    write_jsonl(os.path.join(proj, C1, "subagents", "agent-%s.jsonl" % AGENT), [{"type": "user"}])
    os.makedirs(os.path.join(proj, C1, "tool-results"), exist_ok=True)
    with open(os.path.join(proj, C1, "tool-results", "x.txt"), "w") as fh:
        fh.write(C2)
    os.makedirs(os.path.join(proj, C2), exist_ok=True)
    with open(os.path.join(proj, C2, "custom-title.json"), "w") as fh:
        json.dump({"customTitle": "Widget pipeline review"}, fh)
    os.makedirs(os.path.join(claude, "projects", PROJ, "memory"), exist_ok=True)

    day = os.path.join(codex, "sessions", "2026", "01", "02")
    f1 = os.path.join(day, "rollout-2026-01-02T03-04-05-%s.jsonl" % T1)
    write_jsonl(f1, [{"type": "session_meta", "payload": {"id": T1, "cwd": "/tmp/demo"}}])
    write_jsonl(os.path.join(day, "rollout-2026-01-02T03-05-05-%s_%s.jsonl" % (T1, T1_SEG)),
                [{"type": "session_meta", "payload": {"id": T1}}])
    f2 = os.path.join(day, "rollout-2026-01-02T03-04-06-%s.jsonl" % T2)
    write_jsonl(f2, [{"type": "session_meta", "payload": {"id": T2}}])
    fg = os.path.join(day, "rollout-2026-01-02T03-04-07-%s.jsonl" % T_GUARD)
    write_jsonl(fg, [{"type": "session_meta", "payload": {"id": T_GUARD}}])
    fa = os.path.join(codex, "archived_sessions", "rollout-2026-01-01T00-00-00-%s.jsonl" % T_ARCH)
    write_jsonl(fa, [{"type": "session_meta", "payload": {"id": T_ARCH}}])
    os.makedirs(os.path.join(codex, "sessions", "2026", "01", "03"), exist_ok=True)
    with open(os.path.join(codex, "sessions", "2026", "01", "03", "notes.txt"), "w") as fh:
        fh.write("not a rollout")

    con = sqlite3.connect(os.path.join(codex, "state_5.sqlite"))
    con.execute("create table threads (id text primary key, rollout_path text, title text, name text, "
                "first_user_message text, archived int, source text, cwd text)")
    con.execute("create table thread_spawn_edges (parent_thread_id text, child_thread_id text, status text)")
    rows = [
        (T1, f1, '<paseo-system version="1" kind="agent-message">Deploy the gadget</paseo-system>', None,
         "", 0, "vscode", "/tmp/demo"),
        (T2, f2, "Gadget teardown", None, "", 0, "cli", "/tmp/demo"),
        (T_GUARD, fg, "Guardian review gadget", None, "", 0, '{"subagent":{"other":"guardian"}}', "/tmp/demo"),
        (T_ARCH, fa, "Old archived thread", None, "", 1, "cli", "/tmp/demo"),
        ("01a0ffff-0000-7000-8000-000000000000", "/nowhere/rollout.jsonl", "Lost thread", None, "", 0, "cli", "/"),
    ]
    con.executemany("insert into threads values (?,?,?,?,?,?,?,?)", rows)
    con.execute("insert into thread_spawn_edges values (?,?,?)", (T1, T2, "open"))
    con.commit()
    con.close()

    for pid, prov, sess, title in ((P1, "claude", C1, "Worker: widgets"),
                                   (P2, "claude", C_PRUNED, "Old pruned worker")):
        d = os.path.join(paseo, "agents", PROJ)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, pid + ".json"), "w") as fh:
            json.dump({"id": pid, "provider": prov, "title": title, "cwd": "/tmp/demo",
                       "persistence": {"provider": prov, "sessionId": sess},
                       "labels": {"paseo.parent-agent-id": ""}}, fh)
    return claude, codex, paseo
