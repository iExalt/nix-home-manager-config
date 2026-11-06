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
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from session_mining.out import DEFAULT_MAX_BYTES, Out, clip, human_size  # noqa: E402
from session_mining.events import AUTHORS, KINDS, render  # noqa: E402
from session_mining.reader import Filter, file_events, paseo_launchers  # noqa: E402
from session_mining.resolve import Inventory, entity_keys, resolve  # noqa: E402
from session_mining.search import Query, grep, self_sessions  # noqa: E402
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
    sp.add_argument("--author", action="append", type=_choices(AUTHORS),
                    help="repeatable or comma-separated: %s" % ",".join(AUTHORS))
    sp.add_argument("--kind", action="append", type=_choices(KINDS),
                    help="repeatable or comma-separated: %s" % ",".join(KINDS))
    sp.add_argument("--tool", action="append", type=lambda v: v.split(","),
                    help="tool name, repeatable or comma-separated")
    sp.add_argument("--skill", help="only events invoking this skill (slash command, Skill call, Codex marker)")
    sp.add_argument("--match", help="regex over event text (case-insensitive)")
    sp.add_argument("--since", help="ISO date/time lower bound (UTC)")
    sp.add_argument("--until", help="ISO date/time upper bound (UTC, exclusive)")
    sp.add_argument("--width", type=int, default=160, help="characters per event line")


def _line_range(v: str):
    try:
        if ":" not in v:
            n = int(v)
            return (n, n)
        a, b = v.split(":", 1)
        return (int(a) if a else 1, int(b) if b else None)
    except ValueError:
        raise argparse.ArgumentTypeError("expected N, FROM:TO, FROM: or :TO, got %r" % v)


def _positive(v: str) -> int:
    n = int(v)
    if n < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return n


def _choices(allowed):
    def parse(v: str):
        vals = [x.strip() for x in v.split(",") if x.strip()]
        bad = [x for x in vals if x not in allowed]
        if bad:
            raise argparse.ArgumentTypeError("invalid %s; choose from %s" % (",".join(bad), ",".join(allowed)))
        return vals
    return parse


def _flat(v):
    return [x for group in v or [] for x in group]


def _filter(args) -> Filter:
    return Filter(_flat(args.author), _flat(args.kind), _flat(args.tool), args.skill, args.match, args.since,
                  args.until)


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
    stats = {}
    count = [0]

    def matching():
        for f in files:
            for e in file_events(f, prose=args.prose, launchers=launchers, stats=stats):
                if e["line"] >= lo and (hi is None or e["line"] <= hi) and flt(e):
                    count[0] += 1
                    yield e

    multi = len(files) > 1
    if args.last:
        tail = []
        for e in matching():
            tail.append(e)
            del tail[:-args.last]
        shown = render(tail, out, args.width, show_file=multi, basis=args.basis)
    else:
        gen = matching()
        shown = render(gen, out, args.width, show_file=multi, basis=args.basis)
        for _ in gen:                      # count the rest without rendering
            pass
    total = count[0]
    out.note("%s %s: %d matching event(s), %d shown; %d file(s)%s" % (
        c.type, c.id, total, shown, len(files),
        "" if multi else ": " + files[0].path))
    if stats:
        out.note("parse stats: %s" % ", ".join("%s=%d" % kv for kv in sorted(stats.items())))
    return 0


def _session_title(inv: Inventory, provider: str, sid: str) -> str:
    if provider == "codex":
        row = inv.db_rows.get(sid) or {}
        from session_mining.resolve import clean_title
        return clean_title(row.get("name") or row.get("title") or "")
    if sid in inv.titles:
        return inv.titles[sid]
    for a in inv.paseo:
        if a.session == sid:
            return a.title
    return ""


def cmd_grep(args, roots: Roots, out: Out) -> int:
    inv = Inventory(roots)
    flt = _filter(args)
    if args.pattern:
        import re as _re
        try:
            flt.regex = _re.compile(args.pattern, _re.I)
        except _re.error as e:
            out.note("invalid pattern: %s" % e)
            return 2
    if not (args.pattern or args.skill or args.author or args.kind or args.tool):
        out.note("give a pattern or at least one of --skill/--author/--kind/--tool")
        return 2
    exclude = {} if args.include_self else self_sessions(inv.paseo)
    for sid in args.exclude_session or []:
        exclude[sid] = "--exclude-session"
    prose = not args.full and not (set(_flat(args.kind)) & {"tool_result", "thinking"})
    q = Query(regex=args.pattern, flt=flt, prose=prose, providers=tuple(_flat(args.provider)) or ("claude", "codex"),
              project=args.project, since=args.since, budget=args.budget, include_guardian=args.include_guardian,
              prefilter=not args.no_prefilter)
    cache = None
    if prose and not args.no_cache and not args.include_guardian:
        from session_mining.cache import Cache
        cache = Cache(args.cache)
    res = grep(roots, q, inv.paseo, exclude, include_live=args.include_self, cache=cache)
    sessions: Dict[tuple, list] = {}
    for h in res.hits:
        sessions.setdefault((h["provider"], h["session"]), []).append(h)
    shown_sessions = 0
    for (prov, sid), hits in sessions.items():
        title = _session_title(inv, prov, sid)
        files = sorted({h["file"] for h in hits})
        head = "== %s %s  %d hit(s)  %s%s" % (prov, sid, len(hits), (hits[0].get("ts") or "")[:16],
                                             "  " + json.dumps(clip(title, 70), ensure_ascii=False) if title else "")
        if not out.line(head):
            break
        shown_sessions += 1
        if args.sessions_only:
            continue
        if not out.line("   " + files[0] + ("  (+%d more file(s))" % (len(files) - 1) if len(files) > 1 else "")):
            break
        ordered = sorted(hits, key=lambda h: (h["file"], h["line"]))[: args.per_session]
        multi = len({h["file"] for h in ordered}) > 1
        render(_centered(ordered, flt.regex, args.width), out, args.width, show_file=multi, basis=args.basis)
        if len(hits) > args.per_session:
            out.line("   ... %d more hit(s) in this session (raise --per-session or use show)" % (len(hits) - args.per_session))
    out.note("hits: %d in %d session(s); %d session(s) shown; %.1f s" % (
        len(res.hits), len(sessions), shown_sessions, res.elapsed))
    cov = "files: %d considered" % res.files_considered
    if res.cache_used is not None:
        cov += ", %d answered from the cache" % res.cache_used
    if res.prefilter_kept is not None:
        cov += ", %d kept by rg prefilter" % res.prefilter_kept
    cov += ", %d parsed directly" % res.parsed
    if res.unparsed:
        cov += ", %d NOT PARSED (budget %.0f s spent; raise --budget or narrow with --since/--provider)" % (
            res.unparsed, args.budget)
    out.note(cov)
    if res.prefilter_note:
        out.note(res.prefilter_note)
    extra = []
    if res.stats.get("guardian_skipped"):
        extra.append("%d guardian rollouts skipped (--include-guardian)" % res.stats["guardian_skipped"])
    if res.dedup_dropped:
        extra.append("%d copied Claude record(s) deduped" % res.dedup_dropped)
    if res.project_dropped:
        extra.append("%d hit(s) outside --project" % res.project_dropped)
    if not prose:
        extra.append("full mode (tool output and thinking included)")
    else:
        extra.append("prose mode (no tool output or thinking; --full to include)")
    out.note("; ".join(extra))
    if res.excluded:
        out.note("excluded as the caller: %s" % ", ".join("%s (%s)" % kv for kv in sorted(res.excluded.items())))
    if res.live_candidates:
        out.note("several live Codex rollouts in this directory, none excluded; pass --exclude-session for "
                 "your own: %s" % ", ".join(res.live_candidates))
    return 0


def _centered(hits, regex, width):
    """Hit events with text recentred on the first match so the matching words are visible."""
    for h in hits:
        if regex is not None:
            m = regex.search(h["text"])
            if m and m.start() > width // 3:
                h = dict(h, text="…" + h["text"][m.start() - width // 4:])
        yield h


def _open_cache(args, inv: Inventory, roots: Roots, out: Out, budget: float):
    """Open the cache and index changed files within the budget; notes how many stay unindexed."""
    from session_mining.cache import Cache
    cache = Cache(getattr(args, "cache", None))
    files = list(claude_files(roots)) + list(codex_files(roots))
    t = time.time()
    left = cache.refresh(files, paseo_launchers(inv.paseo), deadline=time.time() + budget)
    if left:
        out.note("INCOMPLETE: %d changed file(s) not indexed within %.0f s; results miss them. Run `cache refresh` "
                 "(cold build takes about 10-30 s) and repeat." % (len(left), budget))
    elif time.time() - t > 1:
        out.note("indexed changed files in %.1f s" % (time.time() - t))
    return cache


def _select_sessions(args, inv: Inventory, cache, out: Out):
    """Sessions matching find/manifest arguments, newest first, each with its matching prompt if any."""
    import re as _re
    from session_mining.cache import session_rows, session_skills
    providers = tuple(_flat(args.provider)) or ("claude", "codex")
    rows = session_rows(cache, providers, args.since, args.until)
    exclude = {} if args.include_self else self_sessions(inv.paseo)
    for sid in args.exclude_session or []:
        exclude[sid] = "--exclude-session"
    rows = [r for r in rows if r["session"] not in exclude]
    if args.project:
        needle = args.project.lower().replace("/", "-").strip("-")
        rows = [r for r in rows if needle in (r["project"] or r["cwd"] or "").lower().replace("/", "-")]
    if args.skill:
        from session_mining.reader import skill_matches
        skills = session_skills(cache)
        rows = [r for r in rows if any(skill_matches(x, args.skill) for x in skills.get((r["provider"], r["session"]), []))]
    authors = _flat(args.text_author) or ["human"]
    texts: Dict[int, list] = {}
    q = ("select file_id, line, text from events where kind in ('prompt', 'decision') and author in (%s) "
         "order by file_id, line" % ",".join("?" * len(authors)))
    for fid, line, text in cache.con.execute(q, authors):
        texts.setdefault(fid, []).append((line, text))
    rx = _re.compile(args.query, _re.I) if args.query else None
    out_rows = []
    for r in rows:
        prompts = [t for fid in r["file_ids"] for t in texts.get(fid, [])]
        r["title"] = _session_title(inv, r["provider"], r["session"])
        r["first"] = prompts[0][1] if prompts else ""
        r["prompts"] = len(prompts)
        r["match"] = None
        if rx is not None:
            if rx.search(r["title"] or ""):
                r["match"] = "title"
            else:
                hit = next((t for t in prompts if rx.search(t[1])), None)
                if hit is None:
                    continue
                r["match"] = hit[1]
        out_rows.append(r)
    out_rows.sort(key=lambda r: r["last_ts"] or "", reverse=True)
    if exclude:
        out.note("excluded as the caller: %s" % ", ".join(sorted(exclude)))
    return out_rows, len(rows)


def _find_args(sp) -> None:
    sp.add_argument("query", nargs="?", help="regex over session titles and prompt text (case-insensitive)")
    sp.add_argument("--text-author", action="append", type=_choices(AUTHORS),
                    help="whose prompts the query searches (default human; e.g. human,agent)")
    sp.add_argument("--skill", help="sessions that invoked this skill")
    sp.add_argument("--provider", action="append", type=_choices(("claude", "codex")))
    sp.add_argument("--project", help="substring of the Claude project dir or Codex cwd")
    sp.add_argument("--since", help="sessions active at or after this UTC date/time")
    sp.add_argument("--until", help="sessions started before this UTC date/time")
    sp.add_argument("--exclude-session", action="append")
    sp.add_argument("--include-self", action="store_true")
    sp.add_argument("--budget", type=float, default=8.0, help="seconds for indexing changed files (default 8)")
    sp.add_argument("--cache", help="cache file")
    sp.add_argument("--width", type=int, default=150)


def cmd_find(args, roots: Roots, out: Out) -> int:
    inv = Inventory(roots)
    cache = _open_cache(args, inv, roots, out, args.budget)
    rows, total = _select_sessions(args, inv, cache, out)
    for r in rows[: args.limit]:
        head = "== %s %s  %s..%s  %d prompt(s)  %s" % (r["provider"], r["session"], (r["first_ts"] or "")[:16],
                                                       (r["last_ts"] or "")[5:16], r["prompts"], human_size(r["bytes"]))
        if r["title"]:
            head += "  " + json.dumps(clip(r["title"], 60), ensure_ascii=False)
        if not out.line(head):
            break
        if r["first"]:
            out.line("   first: " + json.dumps(clip(r["first"], args.width - 12), ensure_ascii=False))
        if r["match"] and r["match"] != "title" and r["match"] != r["first"]:
            out.line("   match: " + json.dumps(clip(r["match"], args.width - 12), ensure_ascii=False))
    out.note("sessions: %d matched of %d; %d listed (--limit %d)" % (len(rows), total, min(len(rows), args.limit),
                                                                     args.limit))
    out.note("use `show <id>` to read one, `manifest` to split many across agents")
    return 0


def cmd_manifest(args, roots: Roots, out: Out) -> int:
    inv = Inventory(roots)
    cache = _open_cache(args, inv, roots, out, args.budget)
    rows, total = _select_sessions(args, inv, cache, out)
    if not rows:
        out.note("no sessions matched")
        return 1
    n = args.shards or max(1, min(12, -(-len(rows) // 15)))
    bins = [[0, []] for _ in range(n)]
    for r in sorted(rows, key=lambda r: -r["bytes"]):          # largest first into the lightest shard
        b = min(bins, key=lambda b: b[0])
        b[0] += r["bytes"]
        b[1].append(r)
    lines = ["shard\tprovider\tsession\tbytes\tfirst_ts\ttitle\tfiles"]
    for i, (_, rs) in enumerate(bins, 1):
        for r in sorted(rs, key=lambda r: r["first_ts"] or ""):
            lines.append("\t".join([str(i), r["provider"], r["session"], str(r["bytes"]), r["first_ts"] or "",
                                    clip(r["title"] or r["first"], 80).replace("\t", " "), ",".join(r["paths"])]))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    for i, (size, rs) in enumerate(bins, 1):
        out.line("shard %d: %d session(s), %s" % (i, len(rs), human_size(size)))
    if not args.out:
        for l in lines:
            if not out.line(l):
                break
    out.note("%d session(s) in %d shard(s)%s; hand each shard to one miner with references/miner-brief.md" % (
        len(rows), n, "; manifest written to %s" % args.out if args.out else ""))
    return 0


def cmd_recall(args, roots: Roots, out: Out) -> int:
    """State of one session for an agent recovering after compaction: what the human asked and decided,
    agents it spawned and messaged, skills, compactions and its latest tool calls."""
    import re as _re
    ref = args.session or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not ref:
        out.note("no session: pass --session <id> (Codex and other harnesses do not expose their own id)")
        return 2
    inv = Inventory(roots)
    cands = resolve(inv, ref)
    if len(entity_keys(cands)) != 1:
        out.note("%r matched %d sessions; pass a longer id" % (ref, len(entity_keys(cands))))
        return 1
    c = cands[0].links[0] if cands[0].links else cands[0]
    evs = [e for f in c.files for e in file_events(f, launchers=paseo_launchers(inv.paseo))]
    n = args.last
    human = [e for e in evs if e["author"] == "human" and e["kind"] in ("prompt", "decision")]
    spawn = [e for e in evs if e["kind"] == "tool_call" and (e.get("tool") or "") in (
        "Agent", "Task", "SendMessage", "spawn_agent", "send_message", "send_input", "followup_task")
        or (e["kind"] == "tool_call" and "create_agent" in (e.get("tool") or ""))]
    ids = {}
    for e in evs:
        if e["kind"] == "tool_result":
            m = _re.search(r"agentId: ([a-z0-9]+)", e["text"]) or _re.search(r'"agent_id"\s*:\s*"([^"]+)"', e["text"])
            if m:
                ids[e["line"]] = m.group(1)
    sections = [("human prompts and decisions (last %d of %d)" % (min(n, len(human)), len(human)), human[-n:]),
                ("agents spawned or messaged (last %d of %d)" % (min(n, len(spawn)), len(spawn)), spawn[-n:]),
                ("skills invoked", [e for e in evs if e.get("skill") and e["author"] != "injected"][-n:]),
                ("compactions", [e for e in evs if e["kind"] == "compaction"][-n:]),
                ("latest tool calls", [e for e in evs if e["kind"] == "tool_call"][-n:])]
    for title, items in sections:
        if not out.line("## " + title):
            break
        render(items, out, args.width, show_file=len(c.files) > 1)
    if ids:
        out.line("## agent ids returned by launches")
        out.line("   " + ", ".join("L%d %s" % kv for kv in sorted(ids.items())[-n:]))
    out.note("%s %s: %d events read from %d file(s)" % (c.type, c.id, len(evs), len(c.files)))
    return 0


def cmd_cache(args, roots: Roots, out: Out) -> int:
    from session_mining.cache import Cache
    cache = Cache(args.cache)
    if args.action == "purge":
        cache.purge()
        out.note("deleted %s" % cache.path)
        return 0
    if args.action == "refresh":
        inv = Inventory(roots)
        files = list(claude_files(roots)) + list(codex_files(roots))
        t = time.time()
        left = cache.refresh(files, paseo_launchers(inv.paseo), deadline=time.time() + args.budget if args.budget else None)
        out.note("refreshed in %.1f s; %d file(s) still unindexed" % (time.time() - t, len(left)))
    st = cache.status()
    out.line("cache %s: %d files, %d events, %s" % (st["path"], st["files"], st["events"], human_size(st["bytes"])))
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
                        help="output cap in bytes, footer included (default %d, minimum 400)" % DEFAULT_MAX_BYTES)
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
    sh.add_argument("--lines", type=_line_range, help="physical line range: N, FROM:TO, FROM: or :TO")
    sh.add_argument("--last", type=_positive, help="only the last N matching events")
    sh.add_argument("--basis", action="store_true", help="show why each event got its author")
    sh.add_argument("--prose", action="store_true", help="skip tool output (faster on huge files)")
    sh.add_argument("--subagents", action="store_true", help="include a Claude session's subagent files")
    g = sub.add_parser("grep", parents=[common], help="search every transcript; hits grouped by session, newest first")
    g.add_argument("pattern", nargs="?", help="regex over event text (case-insensitive); optional with --skill etc.")
    _add_filters(g)
    g.add_argument("--provider", action="append", type=_choices(("claude", "codex")), help="claude, codex")
    g.add_argument("--project", help="substring of the Claude project dir or Codex cwd ('/' and '-' are equal)")
    g.add_argument("--full", action="store_true", help="include tool output and thinking (slower)")
    g.add_argument("--budget", type=float, default=8.0, help="seconds to spend parsing (default 8)")
    g.add_argument("--per-session", type=int, default=3, help="hits shown per session (default 3)")
    g.add_argument("--sessions-only", action="store_true", help="one line per matching session")
    g.add_argument("--exclude-session", action="append", help="session id to leave out (repeatable)")
    g.add_argument("--include-self", action="store_true", help="do not exclude the calling session tree")
    g.add_argument("--include-guardian", action="store_true", help="include Codex guardian auto-review rollouts")
    g.add_argument("--no-prefilter", action="store_true", help="parse every file instead of rg -l candidates")
    g.add_argument("--basis", action="store_true", help="show why each hit got its author")
    g.add_argument("--no-cache", action="store_true", help="read transcripts directly instead of the prose cache")
    g.add_argument("--cache", help="cache file (default $SESSION_MINING_CACHE or ~/.cache/session-mining/index.sqlite)")
    fd = sub.add_parser("find", parents=[common], help="list sessions by title, prompt text, skill, project, date")
    _find_args(fd)
    fd.add_argument("--limit", type=int, default=30)
    mf = sub.add_parser("manifest", parents=[common], help="split matching sessions into byte-balanced shards")
    _find_args(mf)
    mf.add_argument("--shards", type=_positive, help="number of shards (default: about 15 sessions each, max 12)")
    mf.add_argument("--out", help="write the TSV manifest here")
    rc = sub.add_parser("recall", parents=[common], help="recover a session's state after compaction (default: own)")
    rc.add_argument("--session", help="session reference (default $CLAUDE_CODE_SESSION_ID)")
    rc.add_argument("--last", type=_positive, default=8)
    rc.add_argument("--width", type=int, default=150)
    ca = sub.add_parser("cache", parents=[common], help="status, refresh or purge the prose cache")
    ca.add_argument("action", choices=("status", "refresh", "purge"))
    ca.add_argument("--budget", type=float, default=0, help="refresh time limit in seconds (default none)")
    ca.add_argument("--cache", help="cache file")
    args = p.parse_args(argv)
    roots = Roots.from_env(getattr(args, "claude_home", None), getattr(args, "codex_home", None),
                           getattr(args, "paseo_home", None))
    out = Out(getattr(args, "max_bytes", DEFAULT_MAX_BYTES))
    try:
        return {"stores": cmd_stores, "resolve": cmd_resolve, "show": cmd_show, "grep": cmd_grep,
                "find": cmd_find, "manifest": cmd_manifest, "recall": cmd_recall, "cache": cmd_cache}[args.cmd](args, roots, out)
    except BrokenPipeError:
        return 0
    finally:
        out.close()


if __name__ == "__main__":
    sys.exit(main())
