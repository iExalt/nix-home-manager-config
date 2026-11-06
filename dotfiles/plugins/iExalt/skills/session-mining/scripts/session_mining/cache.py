"""Incremental SQLite cache of prose events: prompts, replies, tool-call commands and decisions.

Tool output and thinking are not cached (most of the bytes, rarely what a miner wants); grep --full
reads transcripts directly. Injected instructions are kept only as a short stub with their skill name,
since their full text (skill bodies, AGENTS.md) repeats in every session and floods keyword search.

Files are keyed by path, size and mtime: a refresh parses only new or changed files and drops rows of
deleted ones. A refresh can stop at a deadline; the caller then reads the files still stale directly.
The cache copies transcript text, secrets included, so it lives in a user-only directory.
"""
from __future__ import annotations

import os
import sqlite3
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from typing import Dict, Iterable, List, Optional, Tuple

from .reader import file_events
from .stores import Roots, SessionFile, claude_files, codex_files

VERSION = 1     # bump when readers or the stored shape change: the cache rebuilds
CAPS = {"tool_call": 1000, "injected": 300, "human": 20000}
DEFAULT_CAP = 8000


def default_path() -> str:
    base = os.environ.get("SESSION_MINING_CACHE") or os.path.join(
        os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "session-mining")
    return os.path.join(base, "index.sqlite")


SCHEMA = """
create table if not exists meta (key text primary key, value text);
create table if not exists files (
    id integer primary key, path text unique, provider text, kind text, session text, parent text,
    project text, cwd text, size integer, mtime real, first_ts text, last_ts text, guardian integer,
    events integer);
create table if not exists events (
    file_id integer, line integer, ts text, kind text, author text, skill text, tool text, uuid text,
    rec_session text, basis text, call_id text, text text);
create index if not exists events_file on events(file_id);
create index if not exists events_author on events(author, kind);
create index if not exists events_skill on events(skill) where skill is not null;
create index if not exists files_session on files(session);
"""


class Cache:
    def __init__(self, path: Optional[str] = None):
        self.path = path or default_path()
        d = os.path.dirname(self.path)
        os.makedirs(d, mode=0o700, exist_ok=True)
        self.con = sqlite3.connect(self.path, timeout=30)
        os.chmod(self.path, 0o600)
        self.con.execute("pragma journal_mode=wal")
        self.con.execute("pragma synchronous=normal")
        self.con.executescript(SCHEMA)
        v = self.con.execute("select value from meta where key='version'").fetchone()
        if v is None or int(v[0]) != VERSION:
            self.con.executescript("delete from events; delete from files;")
            self.con.execute("insert or replace into meta values ('version', ?)", (str(VERSION),))
            self.con.commit()

    def purge(self) -> None:
        self.con.close()
        for suffix in ("", "-wal", "-shm"):
            try:
                os.remove(self.path + suffix)
            except OSError:
                pass

    # -- refresh ---------------------------------------------------------------------------------
    def stale(self, files: List[SessionFile]) -> Tuple[List[SessionFile], List[int]]:
        """(new or changed files, ids of indexed files that no longer exist)."""
        known = {r[0]: (r[1], r[2], r[3]) for r in self.con.execute("select path, id, size, mtime from files")}
        stale = [f for f in files if f.path not in known or known[f.path][1:] != (f.size, f.mtime)]
        live = {f.path for f in files}
        gone = [v[0] for p, v in known.items() if p not in live]
        return stale, gone

    def refresh(self, files: List[SessionFile], launchers: Dict[str, str], deadline: Optional[float] = None,
                workers: Optional[int] = None) -> List[SessionFile]:
        """Index stale files newest first until the deadline; returns the files still stale."""
        stale, gone = self.stale(files)
        if gone:
            self._delete(gone)
        if not stale:
            return []
        stale.sort(key=lambda f: -f.mtime)
        done_paths = set()
        if len(stale) <= 4:
            for f in stale:
                if deadline is not None and time.time() >= deadline:
                    break
                self._store(f, _extract((f, launchers)))
                done_paths.add(f.path)
        else:
            from .search import _stop
            ex = ProcessPoolExecutor(max_workers=workers)
            try:
                it = iter(stale)
                pending = {}
                for f in it:
                    pending[ex.submit(_extract, (f, launchers))] = f
                    if len(pending) >= (workers or os.cpu_count() or 4) * 2:
                        break
                while pending:
                    left = None if deadline is None else deadline - time.time()
                    if left is not None and left <= 0:
                        break
                    done, _ = wait(list(pending), timeout=left, return_when=FIRST_COMPLETED)
                    for fut in done:
                        f = pending.pop(fut)
                        self._store(f, fut.result())
                        done_paths.add(f.path)
                        nxt = next(it, None)
                        if nxt is not None:
                            pending[ex.submit(_extract, (nxt, launchers))] = nxt
            finally:
                _stop(ex)
        self.con.commit()
        return [f for f in stale if f.path not in done_paths]

    def _delete(self, ids: Iterable[int]) -> None:
        ids = list(ids)
        for i in range(0, len(ids), 500):
            chunk = ids[i:i + 500]
            q = ",".join("?" * len(chunk))
            self.con.execute("delete from events where file_id in (%s)" % q, chunk)
            self.con.execute("delete from files where id in (%s)" % q, chunk)

    def _store(self, f: SessionFile, extracted) -> None:
        rows, first_ts, last_ts, cwd, guardian = extracted
        old = self.con.execute("select id from files where path=?", (f.path,)).fetchone()
        if old:
            self._delete([old[0]])
        cur = self.con.execute(
            "insert into files (path, provider, kind, session, parent, project, cwd, size, mtime, first_ts, "
            "last_ts, guardian, events) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f.path, f.provider, f.kind, f.session, f.parent, f.project, cwd, f.size, f.mtime, first_ts, last_ts,
             int(guardian), len(rows)))
        fid = cur.lastrowid
        self.con.executemany("insert into events values (%s)" % ",".join("?" * 12), [(fid,) + r for r in rows])

    # -- reads -----------------------------------------------------------------------------------
    def status(self) -> dict:
        n_files, n_events = self.con.execute("select count(*), coalesce(sum(events),0) from files").fetchone()
        size = sum(os.path.getsize(self.path + s) for s in ("", "-wal") if os.path.exists(self.path + s))
        return {"path": self.path, "files": n_files, "events": n_events, "bytes": size}


def _extract(args):
    """Worker: prose events of one file as cache rows, plus file metadata."""
    f, launchers = args
    stats: Dict[str, int] = {}
    rows = []
    first_ts = last_ts = None
    cwd = None
    if f.provider == "codex":
        import json
        try:
            with open(f.path, "rb") as fh:
                cwd = (json.loads(fh.readline()).get("payload") or {}).get("cwd")
        except (OSError, ValueError):
            pass
    for e in file_events(f, prose=True, launchers=launchers, stats=stats):
        ts = e.get("ts")
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
        text = (e.get("command") or e["text"]) if e["kind"] == "tool_call" else e["text"]
        cap = CAPS.get(e["kind"]) or CAPS.get(e["author"]) or DEFAULT_CAP
        rows.append((e["line"], ts, e["kind"], e["author"], e.get("skill"), e.get("tool"), e.get("uuid"),
                     e.get("rec_session"), e.get("basis"), e.get("call_id"), (text or "")[:cap]))
    return rows, first_ts, last_ts, cwd, bool(stats.get("guardian_skipped"))


def session_rows(cache: "Cache", providers=("claude", "codex"), since: Optional[str] = None,
                 until: Optional[str] = None) -> List[dict]:
    """One row per session (a Claude session with its subagent files, or a Codex thread with its
    segments): files, bytes, first/last timestamps, human prompt count, first human prompt, skills."""
    q = ("select provider, coalesce(parent, session) as sess, group_concat(path, char(10)), sum(size), "
         "min(first_ts), max(last_ts), group_concat(id), max(cwd), max(project) from files where guardian = 0 "
         "and provider in (%s) group by provider, sess" % ",".join("?" * len(providers)))
    out = []
    for prov, sess, paths, size, fts, lts, ids, cwd, project in cache.con.execute(q, list(providers)):
        if since and (lts or "") < since:
            continue
        if until and (fts or "~") >= until:
            continue
        out.append({"provider": prov, "session": sess, "paths": paths.split("\n"), "bytes": size or 0,
                    "first_ts": fts, "last_ts": lts, "file_ids": [int(x) for x in ids.split(",")],
                    "cwd": cwd, "project": project})
    return out


def session_texts(cache: "Cache", file_ids: List[int], authors=("human",), kinds=("prompt",)) -> List[tuple]:
    """(path, line, ts, author, text) of the given files' events, in file order."""
    q = ("select f.path, e.line, e.ts, e.author, e.text from events e join files f on f.id = e.file_id "
         "where e.file_id in (%s) and e.author in (%s) and e.kind in (%s) order by f.mtime, e.file_id, e.line" % (
             ",".join("?" * len(file_ids)), ",".join("?" * len(authors)), ",".join("?" * len(kinds))))
    return list(cache.con.execute(q, list(file_ids) + list(authors) + list(kinds)))


def session_skills(cache: "Cache") -> Dict[Tuple[str, str], List[str]]:
    q = ("select f.provider, coalesce(f.parent, f.session), e.skill from events e join files f on f.id = e.file_id "
         "where e.skill is not null group by 1, 2, 3")
    out: Dict[Tuple[str, str], List[str]] = {}
    for prov, sess, skill in cache.con.execute(q):
        out.setdefault((prov, sess), []).append(skill)
    return out
