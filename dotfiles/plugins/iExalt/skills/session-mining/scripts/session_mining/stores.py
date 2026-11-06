"""Where Claude Code, Codex and Paseo keep session history, and cheap enumeration of it.

Nothing here parses transcript bodies. Enumeration reads directory listings, small JSON
records (Paseo agents, Claude custom titles) and the Codex state database, read-only.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sqlite3
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional

UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
CODEX_NAME_RE = re.compile(
    r"^rollout-(\d{4}-\d\d-\d\dT\d\d-\d\d-\d\d)-(" + UUID_RE.pattern + r")(?:_(" + UUID_RE.pattern + r"))?\.jsonl$")


@dataclass
class Roots:
    claude: str
    codex: str
    paseo: str

    @classmethod
    def from_env(cls, claude: Optional[str] = None, codex: Optional[str] = None,
                 paseo: Optional[str] = None) -> "Roots":
        env = os.environ
        return cls(
            claude=os.path.expanduser(claude or env.get("SESSION_MINING_CLAUDE_HOME") or "~/.claude"),
            codex=os.path.expanduser(codex or env.get("CODEX_HOME") or "~/.codex"),
            paseo=os.path.expanduser(paseo or env.get("PASEO_HOME") or "~/.paseo"),
        )


@dataclass
class SessionFile:
    """One transcript file. `session` is the id the file belongs to (Claude session or subagent
    agent id; Codex thread id); `parent` is the owning Claude session for subagent files."""
    provider: str            # "claude" | "codex"
    kind: str                # "main" | "subagent" | "rollout" | "segment"
    session: str
    path: str
    size: int
    mtime: float
    parent: Optional[str] = None
    project: Optional[str] = None
    segment: Optional[str] = None
    archived: bool = False


def _stat(path: str):
    try:
        st = os.stat(path)
        return st.st_size, st.st_mtime
    except OSError:
        return None


def claude_files(roots: Roots) -> Iterator[SessionFile]:
    """Main sessions are projects/<project>/<sid>.jsonl; subagents are
    projects/<project>/<sid>/subagents/agent-<id>.jsonl. tool-results/ and memory/ are skipped."""
    base = os.path.join(roots.claude, "projects")
    try:
        projects = sorted(os.scandir(base), key=lambda e: e.name)
    except OSError:
        return
    for proj in projects:
        if not proj.is_dir():
            continue
        try:
            entries = list(os.scandir(proj.path))
        except OSError:
            continue
        for e in entries:
            if e.is_file() and e.name.endswith(".jsonl"):
                st = _stat(e.path)
                if st:
                    yield SessionFile("claude", "main", e.name[:-6], e.path, st[0], st[1], project=proj.name)
            elif e.is_dir() and e.name != "memory":
                sub = os.path.join(e.path, "subagents")
                try:
                    subs = list(os.scandir(sub))
                except OSError:
                    continue
                for s in subs:
                    if s.is_file() and s.name.endswith(".jsonl"):
                        st = _stat(s.path)
                        if st:
                            aid = s.name[:-6]
                            aid = aid[6:] if aid.startswith("agent-") else aid
                            yield SessionFile("claude", "subagent", aid, s.path, st[0], st[1],
                                              parent=e.name, project=proj.name)


def codex_files(roots: Roots) -> Iterator[SessionFile]:
    """rollout-<ts>-<thread>.jsonl, or rollout-<ts>-<thread>_<segment>.jsonl for a continuation
    segment of the same thread, under sessions/YYYY/MM/DD/ or archived_sessions/."""
    for sub, archived in (("sessions", False), ("archived_sessions", True)):
        top = os.path.join(roots.codex, sub)
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames.sort()
            for name in sorted(filenames):
                m = CODEX_NAME_RE.match(name)
                if not m:
                    continue
                path = os.path.join(dirpath, name)
                st = _stat(path)
                if st:
                    yield SessionFile("codex", "segment" if m.group(3) else "rollout", m.group(2), path,
                                      st[0], st[1], segment=m.group(3), archived=archived)


def codex_db_path(roots: Roots) -> Optional[str]:
    """The newest state_<n>.sqlite (the schema number changes between Codex versions)."""
    cands = []
    for p in glob.glob(os.path.join(roots.codex, "state_*.sqlite")):
        m = re.search(r"state_(\d+)\.sqlite$", p)
        if m:
            cands.append((int(m.group(1)), p))
    return max(cands)[1] if cands else None


def codex_db(roots: Roots) -> Optional[sqlite3.Connection]:
    """Read-only connection to the live Codex state database, or None."""
    path = codex_db_path(roots)
    if not path:
        return None
    for mode in ("ro", None):
        try:
            base = "file:" + urllib.parse.quote(os.path.abspath(path))
            uri = base + ("?mode=ro" if mode else "?immutable=1")
            con = sqlite3.connect(uri, uri=True, timeout=2)
            con.row_factory = sqlite3.Row
            con.execute("select 1 from threads limit 1")
            return con
        except sqlite3.Error:
            continue
    return None


def db_columns(con: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in con.execute("pragma table_info(%s)" % table)]


@dataclass
class PaseoAgent:
    id: str
    provider: str
    session: Optional[str]
    title: str
    cwd: str
    created: str
    labels: Dict[str, str] = field(default_factory=dict)
    path: str = ""


def paseo_agents(roots: Roots) -> Iterator[PaseoAgent]:
    for path in sorted(glob.glob(os.path.join(roots.paseo, "agents", "*", "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                d = json.load(fh)
        except (OSError, ValueError):
            continue
        if not isinstance(d, dict) or not d.get("id"):
            continue
        sess = None
        for key in ("persistence", "runtimeInfo"):
            v = d.get(key)
            if isinstance(v, dict) and v.get("sessionId"):
                sess = v["sessionId"]
                break
        labels = d.get("labels") if isinstance(d.get("labels"), dict) else {}
        yield PaseoAgent(d["id"], d.get("provider") or "", sess, d.get("title") or "", d.get("cwd") or "",
                         d.get("createdAt") or "", {str(k): str(v) for k, v in labels.items()}, path)


def claude_titles(roots: Roots) -> Iterator[tuple]:
    """(session id, custom title) from projects/<project>/<sid>/custom-title.json."""
    for path in glob.glob(os.path.join(roots.claude, "projects", "*", "*", "custom-title.json")):
        try:
            with open(path, encoding="utf-8") as fh:
                t = json.load(fh).get("customTitle")
        except (OSError, ValueError, AttributeError):
            continue
        if t:
            yield os.path.basename(os.path.dirname(path)), t
