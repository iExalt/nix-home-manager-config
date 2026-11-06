"""Provider dispatch: events for a SessionFile, plus filters shared by show and grep."""
from __future__ import annotations

import re
from typing import Dict, Iterable, Iterator, Optional

from . import claude
from .stores import PaseoAgent, SessionFile


def paseo_launchers(agents: Iterable[PaseoAgent]) -> Dict[str, str]:
    """Provider session id -> who wrote its first prompt, from Paseo agent records:
    "schedule" (a paseo.schedule-id label: an automation run), "agent" (a paseo.parent-agent-id label,
    blank too, which marks a top-level thread created by an agent, or an overseer label) or "human"
    (started by the user in Paseo). Sessions absent from the map have no Paseo record. When several
    records point at one session, schedule beats agent beats human."""
    rank = {"human": 0, "agent": 1, "schedule": 2}
    out: Dict[str, str] = {}
    for a in agents:
        if not a.session:
            continue
        if "paseo.schedule-id" in a.labels:
            who = "schedule"
        elif any(k == "paseo.parent-agent-id" or "overseer" in k.lower() or "overseer" in v.lower()
                 for k, v in a.labels.items()):
            who = "agent"
        else:
            who = "human"
        if rank[who] >= rank[out.get(a.session, "human")]:
            out[a.session] = who
    return out


def file_events(f: SessionFile, prose: bool = False, launchers: Optional[Dict[str, str]] = None,
                stats: Optional[Dict[str, int]] = None) -> Iterator[dict]:
    if f.provider == "claude":
        sid = f.parent if f.kind == "subagent" else f.session
        return claude.iter_events(f.path, session=f.session, in_subagent=f.kind == "subagent", prose=prose,
                                  launched=(launchers or {}).get(sid), stats=stats)
    from . import codex
    return codex.iter_events(f.path, prose=prose, launched=(launchers or {}).get(f.session), stats=stats)


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
