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
from session_mining.events import AUTHORS, KINDS, render  # noqa: E402
from session_mining.reader import Filter, file_events, paseo_launchers  # noqa: E402
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


def _add_filters(sp) -> None:
    sp.add_argument("--author", action="append", choices=AUTHORS, help="repeatable")
    sp.add_argument("--kind", action="append", choices=KINDS, help="repeatable")
    sp.add_argument("--tool", action="append", help="tool name, repeatable")
    sp.add_argument("--skill", help="only events invoking this skill (slash command, Skill call, Codex marker)")
    sp.add_argument("--match", help="regex over event text (case-insensitive)")
    sp.add_argument("--since", help="ISO date/time lower bound (UTC)")
    sp.add_argument("--until", help="ISO date/time upper bound (UTC, exclusive)")
    sp.add_argument("--width", type=int, default=160, help="characters per event line")


def _filter(args) -> Filter:
    return Filter(args.author, args.kind, args.tool, args.skill, args.match, args.since, args.until)


def cmd_show(args, roots: Roots, out: Out) -> int:
    inv = Inventory(roots)
    cands = resolve(inv, args.ref)
    if len(entity_keys(cands)) != 1:
        for c in cands[:20]:
            _cand_lines(out, c)
        out.note("show needs exactly one session; %d matched %r. Use resolve to pick one."
                 % (len(entity_keys(cands)), args.ref))
        return 1
    c = cands[0].links[0] if cands[0].links else cands[0]
    files = list(c.files)
    if args.subagents and c.type == "claude-session":
        files += sorted((f for fs in inv.claude_sub.values() for f in fs if f.parent == c.id),
                        key=lambda f: f.mtime)
    if not files:
        out.note("no transcript file for %s %s" % (c.type, c.id))
        return 1
    flt = _filter(args)
    launchers = paseo_launchers(inv.paseo)
    lo, hi = args.lines or (1, None)
    shown = total = 0
    stats = {}
    tail = []
    for f in files:
        evs = (e for e in file_events(f, prose=args.prose, launchers=launchers, stats=stats)
               if e["line"] >= lo and (hi is None or e["line"] <= hi))
        for e in evs:
            if not flt(e):
                continue
            total += 1
            if args.last:
                tail.append(e)
                tail = tail[-args.last:]
            else:
                shown += render([e], out, args.width, show_file=False)
    if args.last:
        shown = render(tail, out, args.width, show_file=False)
    out.note("%s %s: %d matching event(s), %d shown; files: %s" % (
        c.type, c.id, total, shown, ", ".join("%s (%d B)" % (f.path, f.size) for f in files[:3])
        + (" +%d more" % (len(files) - 3) if len(files) > 3 else "")))
    if stats:
        out.note("parse stats: %s" % ", ".join("%s=%d" % kv for kv in sorted(stats.items())))
    return 0


def _cand_json(c) -> dict:
    return {"type": c.type, "id": c.id, "match": c.match, "title": c.title, "notes": c.notes,
            "files": [{"path": f.path, "size": f.size, "archived": f.archived, "segment": f.segment}
                      for f in c.files],
            "links": [_cand_json(x) for x in c.links]}


def main(argv=None) -> int:
    # Global options are accepted before or after the subcommand (agents tend to put them last).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--max-bytes", type=int, default=argparse.SUPPRESS,
                        help="output cap in bytes, footer included (default %d)" % DEFAULT_MAX_BYTES)
    common.add_argument("--claude-home", default=argparse.SUPPRESS, help="default ~/.claude "
                        "(or $SESSION_MINING_CLAUDE_HOME)")
    common.add_argument("--codex-home", default=argparse.SUPPRESS, help="default $CODEX_HOME or ~/.codex")
    common.add_argument("--paseo-home", default=argparse.SUPPRESS, help="default $PASEO_HOME or ~/.paseo")
    p = argparse.ArgumentParser(prog="sessions.py", description=__doc__.split("\n")[0], parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stores", parents=[common], help="list transcript stores with counts, sizes and date ranges")
    r = sub.add_parser("resolve", parents=[common], help="map an id, id prefix/suffix, codex:// link, Paseo id, path or title "
                                       "fragment to sessions and files")
    r.add_argument("ref")
    r.add_argument("--json", action="store_true")
    sh = sub.add_parser("show", parents=[common], help="compact view of one session: one line per event with its file line")
    sh.add_argument("ref")
    _add_filters(sh)
    sh.add_argument("--lines", type=lambda v: tuple(int(x) if x else None for x in v.split(":")),
                    help="physical line range FROM:TO in the transcript file(s)")
    sh.add_argument("--last", type=int, help="only the last N matching events")
    sh.add_argument("--prose", action="store_true", help="skip tool output (faster on huge files)")
    sh.add_argument("--subagents", action="store_true", help="include a Claude session's subagent files")
    args = p.parse_args(argv)
    roots = Roots.from_env(getattr(args, "claude_home", None), getattr(args, "codex_home", None),
                           getattr(args, "paseo_home", None))
    out = Out(getattr(args, "max_bytes", DEFAULT_MAX_BYTES))
    try:
        return {"stores": cmd_stores, "resolve": cmd_resolve, "show": cmd_show}[args.cmd](args, roots, out)
    except BrokenPipeError:
        return 0
    finally:
        out.close()


if __name__ == "__main__":
    sys.exit(main())
