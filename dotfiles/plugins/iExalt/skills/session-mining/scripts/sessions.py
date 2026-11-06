#!/usr/bin/env python3
"""session-mining CLI: search Claude Code and Codex session history without flooding context.

Run as:  python3 -I <skill>/scripts/sessions.py <command> ...   (Python 3.9+, stdlib only)
Every command caps its output at --max-bytes and ends with '# ' footer lines stating coverage.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from session_mining.out import DEFAULT_MAX_BYTES, Out, clip, human_size  # noqa: E402
from session_mining.resolve import Inventory, entity_keys, resolve  # noqa: E402
from session_mining.stores import (Roots, claude_files, codex_db, codex_db_path, codex_files,  # noqa: E402
                                   paseo_agents)


def _date(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


def cmd_stores(args, roots: Roots, out: Out) -> int:
    groups = {}
    for f in list(claude_files(roots)) + list(codex_files(roots)):
        key = {("claude", "main"): "claude sessions", ("claude", "subagent"): "claude subagents"}.get(
            (f.provider, f.kind)) or ("codex archived" if f.archived else "codex sessions")
        g = groups.setdefault(key, [0, 0, None, None])
        g[0] += 1
        g[1] += f.size
        g[2] = f.mtime if g[2] is None else min(g[2], f.mtime)
        g[3] = f.mtime if g[3] is None else max(g[3], f.mtime)
    places = {"claude sessions": os.path.join(roots.claude, "projects", "<project>", "<id>.jsonl"),
              "claude subagents": os.path.join(roots.claude, "projects", "<project>", "<id>", "subagents"),
              "codex sessions": os.path.join(roots.codex, "sessions", "YYYY", "MM", "DD"),
              "codex archived": os.path.join(roots.codex, "archived_sessions")}
    out.line("%-17s %7s %9s  %-23s  %s" % ("store", "files", "size", "modified (UTC)", "location"))
    for key in ("claude sessions", "claude subagents", "codex sessions", "codex archived"):
        g = groups.get(key)
        if g:
            out.line("%-17s %7d %9s  %s..%s  %s" % (key, g[0], human_size(g[1]), _date(g[2]), _date(g[3]),
                                                  places[key]))
        else:
            out.line("%-17s %7d %9s  %-23s  %s" % (key, 0, "-", "-", places[key]))
    con = codex_db(roots)
    if con is not None:
        n = con.execute("select count(*) from threads").fetchone()[0]
        guard = con.execute("select count(*) from threads where source like '%guardian%'").fetchone()[0]
        out.line("%-17s %7d %9s  %-23s  %s" % ("codex db threads", n, "", "%d guardian" % guard,
                                              codex_db_path(roots)))
    summ = os.path.join(roots.codex, "memories", "rollout_summaries")
    if os.path.isdir(summ):
        out.line("%-17s %7d %9s  %-23s  %s" % ("codex summaries", len(os.listdir(summ)), "", "", summ))
    agents = list(paseo_agents(roots))
    if agents:
        out.line("%-17s %7d %9s  %-23s  %s" % ("paseo agents", len(agents), "", "metadata only",
                                              os.path.join(roots.paseo, "agents")))
    out.note("transcripts: claude and codex JSONL; codex db and paseo records hold titles and ids, not text")
    return 0


def _cand_lines(out: Out, c, indent: str = "") -> None:
    head = "%s%-15s %s  [%s]" % (indent, c.type, c.id, c.match)
    if c.title:
        head += "  " + json.dumps(clip(c.title, 90), ensure_ascii=False)
    out.line(head)
    for n in c.notes:
        out.line("%s    - %s" % (indent, n))
    for f in c.files[:8]:
        out.line("%s    %s  (%s)" % (indent, f.path, human_size(f.size)))
    if len(c.files) > 8:
        out.line("%s    ... %d more file(s)" % (indent, len(c.files) - 8))
    for link in c.links:
        _cand_lines(out, link, indent + "    -> ")


def cmd_resolve(args, roots: Roots, out: Out) -> int:
    inv = Inventory(roots)
    cands = resolve(inv, args.ref)
    if args.json:
        for c in cands:
            out.line(json.dumps(_cand_json(c), ensure_ascii=False))
    else:
        for c in cands:
            _cand_lines(out, c)
    entities = entity_keys(cands)
    if not cands:
        out.note("no match for %r" % args.ref)
    elif len(entities) > 1:
        out.note("AMBIGUOUS: %d candidates; use a longer id or pick one explicitly" % len(entities))
    out.note(inv.counts())
    return 0 if cands else 1


def _cand_json(c) -> dict:
    return {"type": c.type, "id": c.id, "match": c.match, "title": c.title, "notes": c.notes,
            "files": [{"path": f.path, "size": f.size, "archived": f.archived, "segment": f.segment}
                      for f in c.files],
            "links": [_cand_json(x) for x in c.links]}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="sessions.py", description=__doc__.split("\n")[0])
    p.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="output cap (default %(default)s)")
    p.add_argument("--claude-home", help="default ~/.claude (or $SESSION_MINING_CLAUDE_HOME)")
    p.add_argument("--codex-home", help="default $CODEX_HOME or ~/.codex")
    p.add_argument("--paseo-home", help="default $PASEO_HOME or ~/.paseo")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stores", help="list transcript stores with counts, sizes and date ranges")
    r = sub.add_parser("resolve", help="map an id, id prefix/suffix, codex:// link, Paseo id, path or title "
                                       "fragment to sessions and files")
    r.add_argument("ref")
    r.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    roots = Roots.from_env(args.claude_home, args.codex_home, args.paseo_home)
    out = Out(args.max_bytes)
    try:
        return {"stores": cmd_stores, "resolve": cmd_resolve}[args.cmd](args, roots, out)
    except BrokenPipeError:
        return 0
    finally:
        out.close()


if __name__ == "__main__":
    sys.exit(main())
