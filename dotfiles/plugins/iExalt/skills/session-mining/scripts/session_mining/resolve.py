"""Turn whatever reference an agent has (uuid, id prefix or suffix, codex://threads/<id>, a Paseo
agent id, a transcript path, or a title fragment) into sessions and their files.

Ambiguity is never resolved silently: every matching entity is returned, labelled with its type and
match kind. Codex ids are UUIDv7, so a short prefix is a ~minute-wide timestamp bucket and often
ambiguous; Paseo short ids are prefixes of the Paseo agent id, not of the provider session id.
"""
from __future__ import annotations

import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .stores import Roots, SessionFile, claude_files, claude_titles, codex_db, codex_files, db_columns, paseo_agents

HEXISH_RE = re.compile(r"^[0-9a-f][0-9a-f-]{3,35}$")


@dataclass
class Candidate:
    type: str                 # claude-session | claude-subagent | codex-thread | paseo-agent
    id: str
    match: str                # exact | prefix | suffix | title | path
    title: str = ""
    files: List[SessionFile] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    links: List["Candidate"] = field(default_factory=list)   # paseo-agent -> provider session


class Inventory:
    """Every transcript file plus the metadata stores, loaded once per command."""

    def __init__(self, roots: Roots):
        self.roots = roots
        self.claude: Dict[str, List[SessionFile]] = defaultdict(list)     # session id -> main files
        self.claude_sub: Dict[str, List[SessionFile]] = defaultdict(list)  # agent id -> files
        self.claude_children: Dict[str, int] = defaultdict(int)           # session id -> subagent files
        self.codex: Dict[str, List[SessionFile]] = defaultdict(list)       # thread id -> files
        self.codex_segment: Dict[str, str] = {}                           # segment id -> thread id
        for f in claude_files(roots):
            if f.kind == "main":
                self.claude[f.session].append(f)
            else:
                self.claude_sub[f.session].append(f)
                self.claude_children[f.parent or ""] += 1
        for f in codex_files(roots):
            self.codex[f.session].append(f)
            if f.segment:
                self.codex_segment[f.segment] = f.session
        self.titles = dict(claude_titles(roots))
        self.paseo = list(paseo_agents(roots))
        self.db = codex_db(roots)
        self.db_rows: Dict[str, dict] = {}
        self.spawn_children: Dict[str, List[str]] = defaultdict(list)
        if self.db is not None:
            cols = set(db_columns(self.db, "threads"))
            want = [c for c in ("id", "rollout_path", "title", "name", "first_user_message", "archived",
                                "source", "cwd", "agent_role", "agent_nickname") if c in cols]
            for r in self.db.execute("select %s from threads" % ", ".join(want)):
                self.db_rows[r["id"]] = dict(r)
            try:
                for r in self.db.execute("select parent_thread_id, child_thread_id from thread_spawn_edges"):
                    self.spawn_children[r[0]].append(r[1])
            except Exception:
                pass

    def counts(self) -> str:
        nc = sum(len(v) for v in self.claude.values()) + sum(len(v) for v in self.claude_sub.values())
        nx = sum(len(v) for v in self.codex.values())
        db = "%d threads" % len(self.db_rows) if self.db is not None else "unavailable"
        return "searched: claude %d files, codex %d files, codex db %s, paseo %d agents" % (
            nc, nx, db, len(self.paseo))

    # -- entity builders -------------------------------------------------------------------------
    def claude_session(self, sid: str, match: str) -> Candidate:
        c = Candidate("claude-session", sid, match, self.titles.get(sid, ""), list(self.claude.get(sid, [])))
        if len(c.files) > 1:
            c.notes.append("same session id in %d projects" % len(c.files))
        n = self.claude_children.get(sid, 0)
        if n:
            c.notes.append("%d subagent file(s)" % n)
        return c

    def claude_subagent(self, aid: str, match: str) -> Candidate:
        files = list(self.claude_sub.get(aid, []))
        c = Candidate("claude-subagent", aid, match, "", files)
        if files:
            c.notes.append("parent session %s" % files[0].parent)
        return c

    def codex_thread(self, tid: str, match: str) -> Candidate:
        row = self.db_rows.get(tid) or {}
        title = clean_title(row.get("name") or row.get("title") or row.get("first_user_message") or "")
        files = sorted(self.codex.get(tid, []), key=lambda f: (f.archived, f.segment or "", f.path))
        c = Candidate("codex-thread", tid, match, title, files)
        if not files and row:
            c.notes.append("in codex db but transcript missing (%s)" % (row.get("rollout_path") or "?"))
        if not row and files:
            c.notes.append("not in codex db")
        if "guardian" in str(row.get("source") or ""):
            c.notes.append("guardian auto-review thread")
        if any(f.archived for f in files):
            c.notes.append("archived")
        segs = [f for f in files if f.segment]
        if segs:
            c.notes.append("%d continuation segment(s)" % len(segs))
        kids = self.spawn_children.get(tid)
        if kids:
            c.notes.append("%d spawned child thread(s)" % len(kids))
        return c

    def paseo_agent(self, a, match: str) -> Candidate:
        c = Candidate("paseo-agent", a.id, match, a.title)
        c.notes.append("provider %s, session %s" % (a.provider or "?", a.session or "?"))
        if a.session:
            if a.provider == "claude":
                link = self.claude_session(a.session, "linked")
            elif a.provider == "codex":
                link = self.codex_thread(a.session, "linked")
            else:
                link = None
            if link is not None:
                if link.files:
                    c.links.append(link)
                else:
                    c.notes.append("Paseo record found, transcript pruned or not on this machine")
        return c


ENVELOPE_RE = re.compile(r"<(paseo-system|system-reminder|user_instructions|environment_context)[^>]*>", re.S)


def clean_title(t: str) -> str:
    """Codex derives titles from the first message, which may be an injected envelope."""
    return ENVELOPE_RE.sub("", t).replace("</paseo-system>", "").strip()


def entity_keys(cands: List[Candidate]) -> set:
    """Distinct underlying sessions: a Paseo agent counts as the session it links to."""
    keys = set()
    for c in cands:
        keys.add((c.links[0].type, c.links[0].id) if c.links else (c.type, c.id))
    return keys


def _id_match(key: str, ref: str) -> Optional[str]:
    if key == ref:
        return "exact"
    if key.startswith(ref):
        return "prefix"
    if key.endswith(ref):
        return "suffix"
    return None


def normalize_ref(ref: str) -> str:
    r = ref.strip()
    for p in ("codex://threads/", "codex://thread/"):
        if r.startswith(p):
            r = r[len(p):]
    r = r.split("?")[0].rstrip("/")
    return r


FULL_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def looks_like_path(r: str) -> bool:
    return r.startswith(("/", "~", "./", "../")) or r.endswith(".jsonl")


def resolve(inv: Inventory, ref: str, limit: int = 50) -> List[Candidate]:
    r = normalize_ref(ref)
    # A transcript path: report the session it belongs to.
    if looks_like_path(r):
        p = os.path.realpath(os.path.expanduser(r))
        for fs in list(inv.claude.values()) + list(inv.claude_sub.values()) + list(inv.codex.values()):
            for f in fs:
                if os.path.realpath(f.path) == p:
                    if f.provider == "codex":
                        return [inv.codex_thread(f.session, "path")]
                    if f.kind == "subagent":
                        return [inv.claude_subagent(f.session, "path")]
                    return [inv.claude_session(f.session, "path")]
        return []
    low = r.lower()
    out: List[Candidate] = []
    idref = low[6:] if low.startswith("agent-") else low
    if HEXISH_RE.match(idref):
        out = _id_search(inv, idref, limit)
    # Words such as "added" or "feed" and date fragments look like hex: unless the reference is a
    # whole uuid, titles are searched too and those matches are labelled "title".
    if not FULL_UUID_RE.match(idref):
        have = {(c.type, c.id) for c in out}
        out += [c for c in _title_search(inv, low, limit) if (c.type, c.id) not in have]
    # A Paseo agent and the provider session it links to are one entity: keep the agent (it carries
    # the Paseo title and nests the session) and drop the duplicate standalone session candidate.
    linked = {(l.type, l.id) for c in out for l in c.links}
    out = [c for c in out if c.type == "paseo-agent" or (c.type, c.id) not in linked]
    rank = {"exact": 0, "path": 0, "prefix": 1, "suffix": 2, "provider-session": 3, "title": 4}
    out.sort(key=lambda c: (rank.get(c.match.split(" ")[0], 5), c.type, c.id))
    return out


def _id_search(inv: Inventory, low: str, limit: int) -> List[Candidate]:
    out: List[Candidate] = []
    for sid in inv.claude:
        m = _id_match(sid, low)
        if m:
            out.append(inv.claude_session(sid, m))
    for aid in inv.claude_sub:
        m = _id_match(aid, low)
        if m:
            out.append(inv.claude_subagent(aid, m))
    for tid in set(inv.codex) | set(inv.db_rows):
        m = _id_match(tid, low)
        if m:
            out.append(inv.codex_thread(tid, m))
    for seg, tid in inv.codex_segment.items():
        m = _id_match(seg, low)
        if m and tid not in {c.id for c in out}:
            out.append(inv.codex_thread(tid, m + " (segment id)"))
    for a in inv.paseo:
        m = _id_match(a.id.lower(), low)
        if m:
            out.append(inv.paseo_agent(a, m))
    # Paseo records that point at a provider session we matched explain where that session came from.
    if len(out) <= limit:
        ids = {c.id for c in out}
        for a in inv.paseo:
            if a.session in ids and a.id not in ids:
                out.append(inv.paseo_agent(a, "provider-session"))
    return out


def _title_search(inv: Inventory, needle: str, limit: int) -> List[Candidate]:
    """Case-insensitive substring over Paseo titles, Codex db title/name/first prompt, and Claude
    custom titles. Claude first prompts need the cache (`find`)."""
    out: List[Candidate] = []
    for a in inv.paseo:
        if needle in a.title.lower():
            out.append(inv.paseo_agent(a, "title"))
    for tid, row in inv.db_rows.items():
        hay = " ".join(str(row.get(k) or "") for k in ("title", "name", "first_user_message")).lower()
        if needle in hay and "guardian" not in str(row.get("source") or ""):
            out.append(inv.codex_thread(tid, "title"))
    for sid, t in inv.titles.items():
        if needle in t.lower():
            out.append(inv.claude_session(sid, "title"))
    return out
