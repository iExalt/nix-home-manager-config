"""Provider dispatch: events for a SessionFile, plus filters shared by show and grep."""
from __future__ import annotations

import re
from typing import Dict, Iterable, Iterator, Optional

from . import claude
from .stores import PaseoAgent, SessionFile


def paseo_launchers(agents: Iterable[PaseoAgent]) -> Dict[str, bool]:
    """Provider session id -> True when another agent wrote its first prompt (a paseo.parent-agent-id
    label, blank too: a top-level thread created by an agent, or an overseer label), False when the
    user started it in Paseo. Sessions absent from the map have no Paseo record."""
    out: Dict[str, bool] = {}
    for a in agents:
        if a.session:
            out[a.session] = any(k == "paseo.parent-agent-id" or "overseer" in k.lower() or "overseer" in v.lower()
                                 for k, v in a.labels.items())
    return out


def file_events(f: SessionFile, prose: bool = False, launchers: Optional[Dict[str, bool]] = None,
                stats: Optional[Dict[str, int]] = None) -> Iterator[dict]:
    if f.provider == "claude":
        sid = f.parent if f.kind == "subagent" else f.session
        return claude.iter_events(f.path, session=f.session, in_subagent=f.kind == "subagent", prose=prose,
                                  launched=(launchers or {}).get(sid), stats=stats)
    from . import codex
    return codex.iter_events(f.path, prose=prose, stats=stats)


def skill_matches(name: Optional[str], want: str) -> bool:
    """'phone-debug' matches 'phone-debug', '/phone-debug' and 'iExalt:phone-debug' (case-insensitive)."""
    if not name:
        return False
    n = name.lower().lstrip("/").strip()
    w = want.lower().lstrip("/").strip()
    return n == w or n.endswith(":" + w) or (":" in w and n == w.split(":", 1)[1])


class Filter:
    def __init__(self, authors=None, kinds=None, tools=None, skill=None, regex=None, since=None, until=None):
        self.authors = set(authors or [])
        self.kinds = set(kinds or [])
        self.tools = {t.lower() for t in tools or []}
        self.skill = skill
        self.regex = re.compile(regex, re.I) if isinstance(regex, str) else regex
        self.since, self.until = since, until

    def __call__(self, e: dict) -> bool:
        if self.authors and e["author"] not in self.authors:
            return False
        if self.kinds and e["kind"] not in self.kinds:
            return False
        if self.tools and (e.get("tool") or "").lower() not in self.tools:
            return False
        if self.skill and not skill_matches(e.get("skill"), self.skill):
            return False
        ts = e.get("ts") or ""
        if self.since and ts and ts < self.since:
            return False
        if self.until and ts and ts >= self.until:
            return False
        if self.regex is not None and not self.regex.search(e["text"] or ""):
            return False
        return True
