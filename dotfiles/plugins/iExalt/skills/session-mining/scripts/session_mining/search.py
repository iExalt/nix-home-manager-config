"""grep across every transcript: select files, prefilter with rg, parse candidates in a process pool
under a time budget, dedup copied Claude records, then apply file-level filters and self-exclusion.

Coverage is always reported: files considered, kept by the prefilter, parsed, left unparsed when the
budget ran out, and excluded (self, guardian). Partial results never look complete.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from . import claude
from .reader import Filter, file_events, paseo_launchers
from .stores import PaseoAgent, Roots, SessionFile, claude_files, codex_files

LIVE_SECONDS = 120
SERIAL_JOBS = 4
HIT_TEXT_CAP = 2000            # characters of event text carried back from a worker


@dataclass
class Query:
    regex: Optional[str] = None
    flt: Filter = field(default_factory=Filter)
    prose: bool = True
    providers: Tuple[str, ...] = ("claude", "codex")
    project: Optional[str] = None
    since: Optional[str] = None
    budget: float = 8.0
    include_guardian: bool = False
    prefilter: bool = True
    workers: Optional[int] = None


@dataclass
class Result:
    hits: List[dict]
    files_considered: int = 0
    prefilter_kept: Optional[int] = None
    prefilter_note: str = ""
    parsed: int = 0
    unparsed: int = 0
    dedup_dropped: int = 0
    project_dropped: int = 0
    stats: Dict[str, int] = field(default_factory=dict)
    excluded: Dict[str, str] = field(default_factory=dict)       # session -> reason
    live_candidates: List[str] = field(default_factory=list)
    cache_used: Optional[int] = None
    prefilter_checked: Optional[int] = None
    unparsed_prefilter: int = 0
    failures: List[str] = field(default_factory=list)
    elapsed: float = 0.0


# -- self-exclusion ------------------------------------------------------------------------------

def self_sessions(agents: List[PaseoAgent], env=None) -> Dict[str, str]:
    """Sessions belonging to the caller: its own Claude session and, through Paseo labels, every
    agent it launched (transitively). Returns session id -> reason."""
    env = os.environ if env is None else env
    out: Dict[str, str] = {}
    sid = env.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        out[sid] = "caller (CLAUDE_CODE_SESSION_ID)"
    pid = env.get("PASEO_AGENT_ID")
    if pid:
        by_id = {a.id: a for a in agents}
        kids: Dict[str, List[PaseoAgent]] = {}
        for a in agents:
            parent = a.labels.get("paseo.parent-agent-id")
            if parent:
                kids.setdefault(parent, []).append(a)
        stack, seen = [pid], set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            a = by_id.get(cur)
            if a and a.session:
                out.setdefault(a.session, "caller (PASEO_AGENT_ID)" if cur == pid else "launched by caller")
            stack.extend(k.id for k in kids.get(cur, []))
    return out


def codex_live_candidates(files: List[SessionFile], cwd: str, now: float) -> List[SessionFile]:
    """Codex rollouts in the caller's directory written in the last LIVE_SECONDS: the caller's own
    rollout is among them when the caller is a Codex session without Paseo."""
    out = []
    for f in files:
        if f.provider != "codex" or now - f.mtime > LIVE_SECONDS:
            continue
        try:
            with open(f.path, "rb") as fh:
                meta = json.loads(fh.readline()).get("payload") or {}
        except (OSError, ValueError):
            continue
        if os.path.realpath(meta.get("cwd") or "") == os.path.realpath(cwd):
            out.append(f)
    return out


# -- prefilter -----------------------------------------------------------------------------------

def rg_pattern(regex: str) -> str:
    """Adapt a pattern over event text to the JSON-escaped file text: quotes and backslashes are
    escaped there, and line breaks and tabs appear as \\n and \\t."""
    p = regex.replace(r"\s", r"(?:\s|\\[nrt])")
    p = re.sub(r'(?<!\\)"', r'\\\\?"', p)
    return p


def prefilter(paths: List[str], regex: Optional[str], literal: Optional[str], deadline: Optional[float] = None
              ) -> Tuple[Optional[Set[str]], int, str]:
    """Paths whose raw text may match, via rg -l over batches in the given (newest first) order, until
    the deadline. Returns (kept paths or None when rg is unavailable or rejects the pattern, number of
    paths checked, note). Paths not checked are neither kept nor ruled out."""
    rg = shutil.which("rg")
    if not rg:
        return None, 0, "rg not found; parsed every file"
    if literal:
        args = [rg, "-l", "-i", "-F", "--no-messages", "-e", literal]
    elif regex:
        args = [rg, "-l", "-i", "--no-messages", "-e", rg_pattern(regex)]
    else:
        return None, 0, ""
    keep: Set[str] = set()
    checked = 0
    for i in range(0, len(paths), 200):
        left = None if deadline is None else deadline - time.time()
        if left is not None and left <= 0:
            break
        batch = paths[i:i + 200]
        try:
            r = subprocess.run(args + ["--"] + batch, capture_output=True, text=True, timeout=left)
        except subprocess.TimeoutExpired:
            break
        if r.returncode == 2 and not r.stdout:
            return None, 0, "rg rejected the pattern (%s); parsed every file" % (r.stderr.strip()[:120] or "error")
        keep.update(x for x in r.stdout.splitlines() if x)
        checked += len(batch)
    return keep, checked, ""


# -- worker --------------------------------------------------------------------------------------

def _scan(args):
    """Worker: hits of one file. Never raises: a file that cannot be read is reported, not fatal."""
    try:
        return _scan_file(*args)
    except Exception as e:                              # noqa: BLE001 - one odd file must not end the search
        f = args[0]
        return f.path, [], {"failed": 1}, None, None, "%s: %s: %s" % (f.path, type(e).__name__, str(e)[:120])


def _scan_file(f, prose, launchers, flt, include_guardian):
    stats: Dict[str, int] = {}
    hits = []
    first_ts = None
    cwd = None
    if f.provider == "codex":
        try:
            with open(f.path, "rb") as fh:
                cwd = (json.loads(fh.readline()).get("payload") or {}).get("cwd")
        except (OSError, ValueError):
            pass
        from . import codex
        evs = codex.iter_events(f.path, prose=prose, launched=(launchers or {}).get(f.session),
                                include_guardian=include_guardian, stats=stats)
    else:
        evs = file_events(f, prose=prose, launchers=launchers, stats=stats)
    for e in evs:
        if first_ts is None and e.get("ts"):
            first_ts = e["ts"]
        if flt(e):
            e = dict(e)
            if len(e["text"]) > HIT_TEXT_CAP:
                m = flt.regex.search(e["text"]) if flt.regex is not None else None
                start = max(0, (m.start() if m else 0) - HIT_TEXT_CAP // 2)
                e["text"] = e["text"][start:start + HIT_TEXT_CAP]
            hits.append(e)
    return f.path, hits, stats, first_ts, cwd, None


def cache_hits(cache, flt: Filter, paths: Set[str]):
    """(event, path, file first_ts, file cwd) for cached events of the given files that pass flt."""
    sql = ("select f.path, f.provider, f.session, f.first_ts, f.cwd, e.line, e.ts, e.kind, e.author, e.skill, "
           "e.tool, e.uuid, e.rec_session, e.basis, e.call_id, e.text from events e join files f on f.id = e.file_id")
    where, args = [], []
    if flt.authors:
        where.append("e.author in (%s)" % ",".join("?" * len(flt.authors)))
        args += sorted(flt.authors)
    if flt.kinds:
        where.append("e.kind in (%s)" % ",".join("?" * len(flt.kinds)))
        args += sorted(flt.kinds)
    if flt.skill:
        where.append("e.skill is not null")
    if where:
        sql += " where " + " and ".join(where)
    for (path, prov, sess, fts, cwd, line, ts, kind, author, skill, tool, uuid, rec, basis, cid,
         text) in cache.con.execute(sql, args):
        if path not in paths or (flt.regex is not None and not flt.regex.search(text or "")):
            continue
        e = {"provider": prov, "session": sess, "file": path, "line": line, "ts": ts, "kind": kind,
             "author": author, "text": text or "", "tool": tool, "command": text if kind == "tool_call" else None,
             "skill": skill, "uuid": uuid, "rec_session": rec, "basis": basis, "call_id": cid}
        if flt(e):
            yield e, path, fts, cwd


# -- main ----------------------------------------------------------------------------------------

def grep(roots: Roots, q: Query, agents: List[PaseoAgent], exclude: Dict[str, str],
         include_live: bool = False, now: Optional[float] = None, cwd: Optional[str] = None,
         cache=None) -> Result:
    """cache: a cache.Cache, used for prose queries; None reads every candidate file directly."""
    t0 = time.time()
    now = now or time.time()
    files: List[SessionFile] = []
    if "claude" in q.providers:
        files += list(claude_files(roots))
    if "codex" in q.providers:
        files += list(codex_files(roots))
    all_files = list(files)
    res = Result(hits=[], excluded=dict(exclude))
    if q.since:
        cutoff = _iso_to_epoch(q.since)
        if cutoff is not None:
            files = [f for f in files if f.mtime >= cutoff]       # a file is never older than its events

    # Codex without Paseo has no session id in its environment: exclude the one live rollout in the
    # caller's directory; with several, exclude none and list them.
    if not exclude and not include_live:
        live = codex_live_candidates(files, cwd or os.getcwd(), now)
        if len(live) == 1:
            res.excluded[live[0].session] = "caller (only live Codex rollout in this directory)"
        elif len(live) > 1:
            res.live_candidates = sorted({f.session for f in live})

    def excluded(f: SessionFile) -> bool:
        return f.session in res.excluded or (f.parent is not None and f.parent in res.excluded)

    files = [f for f in files if not excluded(f)]
    res.files_considered = len(files)
    by_path = {f.path: f for f in files}
    files.sort(key=lambda f: -f.mtime)                         # recent first: deterministic and useful
    launchers = paseo_launchers(agents)
    raw_hits: List[Tuple[dict, str]] = []
    first_ts: Dict[str, Optional[str]] = {}
    cwds: Dict[str, Optional[str]] = {}
    deadline = t0 + q.budget
    to_parse = files
    if cache is not None and q.prose and not q.include_guardian:
        # Index what changed (bounded), answer indexed files from the cache, parse the rest directly.
        stale = cache.refresh(all_files, launchers, deadline=t0 + q.budget * 0.6, workers=q.workers)
        stale_paths = {f.path for f in stale}
        wanted = {f.path for f in files}
        cached_paths = wanted - stale_paths
        res.cache_used = len(cached_paths)
        for h, path, fts, cwd_ in cache_hits(cache, q.flt, cached_paths):
            raw_hits.append((h, path))
            first_ts[path] = fts
            cwds[path] = cwd_
        to_parse = [f for f in files if f.path in stale_paths]
    if to_parse and q.prefilter and (q.regex or q.flt.skill):
        keep, checked, note = prefilter([f.path for f in to_parse], None if q.flt.skill else q.regex,
                                        q.flt.skill.split(":")[-1] if q.flt.skill else None,
                                        time.time() + max(0.0, deadline - time.time()) * 0.7)
        res.prefilter_note = note
        if keep is not None:
            res.prefilter_checked = checked
            unchecked = len(to_parse) - checked
            to_parse = [f for f in to_parse[:checked] if f.path in keep]
            res.prefilter_kept = len(to_parse)
            res.unparsed_prefilter = unchecked
    jobs = [(f, q.prose, launchers, q.flt, q.include_guardian) for f in to_parse]

    def take(result):
        path, hits, stats, fts, cwd_, err = result
        if err:
            res.failures.append(err)
        res.parsed += 1
        first_ts[path] = fts
        cwds[path] = cwd_
        for k, v in stats.items():
            res.stats[k] = res.stats.get(k, 0) + v
        raw_hits.extend((h, path) for h in hits)

    if len(jobs) <= SERIAL_JOBS:             # a pool costs more to start than a few small files take
        for job in jobs:
            if time.time() >= deadline:
                break
            take(_scan(job))
        jobs = []
    ex = ProcessPoolExecutor(max_workers=q.workers)
    try:
        pending = set()
        it = iter(jobs)
        for job in it:
            pending.add(ex.submit(_scan, job))
            if len(pending) >= (q.workers or os.cpu_count() or 4) * 2:
                break
        while pending:
            left = deadline - time.time()
            if left <= 0:
                break
            done, pending = wait(pending, timeout=left, return_when=FIRST_COMPLETED)
            for fut in done:
                try:
                    take(fut.result())
                except Exception as e:          # noqa: BLE001 - e.g. a worker killed by the OS
                    res.failures.append("worker: %s: %s" % (type(e).__name__, str(e)[:120]))
                nxt = next(it, None)
                if nxt is not None:
                    pending.add(ex.submit(_scan, nxt))
    finally:
        _stop(ex)
    res.unparsed = len(to_parse) - res.parsed + res.unparsed_prefilter

    # Dedup copies of one Claude record (resumed or forked sessions) by uuid; keep the owner's copy.
    best: Dict[Tuple[str, str], Tuple[tuple, dict]] = {}
    out: List[dict] = []
    for h, path in raw_hits:
        if h.get("rec_session") in res.excluded:
            continue                       # a resumed copy of an excluded (caller's) record
        if h["provider"] == "claude" and h.get("uuid"):
            # One record can yield several events (e.g. two tool calls): key on the event, not the record.
            key = ("claude", "%s|%s|%s|%s" % (h["uuid"], h["kind"], h.get("call_id") or h.get("tool"),
                                             hash(h["text"][:300])))
            rank = claude.owner_rank(path, h.get("rec_session"), first_ts.get(path))
            cur = best.get(key)
            if cur is None or rank < cur[0]:
                if cur is not None:
                    res.dedup_dropped += 1
                best[key] = (rank, h)
            else:
                res.dedup_dropped += 1
        else:
            out.append(h)
    out += [h for _, h in best.values()]

    # File-level filters run after dedup so a copy cannot stand in for a filtered-out owner.
    if q.project:
        needle = q.project.lower().replace("/", "-").strip("-")
        kept = []
        for h in out:
            f = by_path.get(h["file"])
            hay = (f.project or "") if f and f.provider == "claude" else (cwds.get(h["file"]) or "")
            if needle in hay.lower().replace("/", "-"):
                kept.append(h)
        res.project_dropped = len(out) - len(kept)
        out = kept
    out.sort(key=lambda h: (h.get("ts") or "", h["file"], h["line"]), reverse=True)
    res.hits = out
    res.elapsed = time.time() - t0
    return res


def _stop(ex: ProcessPoolExecutor) -> None:
    """Shut the pool down without waiting: on a spent budget, workers still parsing are killed so the
    command returns on time."""
    # _processes is private; if it ever disappears, shutdown(wait=False) still returns and exit waits
    # only for the files in flight.
    procs = list((getattr(ex, "_processes", None) or {}).values())
    ex.shutdown(wait=False, cancel_futures=True)
    for p in procs:
        if p.is_alive():
            p.terminate()


def _iso_to_epoch(s: str) -> Optional[float]:
    import calendar
    s = s.strip().rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return calendar.timegm(time.strptime(s[:19], fmt))
        except ValueError:
            continue
    return None
