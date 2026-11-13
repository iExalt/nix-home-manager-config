#!/usr/bin/env python3
"""Campaign scoreboard for the overseer skill. Stdlib only, Python 3.9+.

Run as `python3 -I scoreboard.py [--campaign DIR] <command>`. DIR (default: the
current directory) is the run checkout; it holds `campaign.json` (frozen at plan
agreement, changed only by recorded amendments) and `scoreboard-state.json`
(task clocks, forecasts, last digest). Acyclic is only read, through its CLI.

Commands:
  freeze        write campaign.json (or, with --amend, append an approved amendment)
  show          print line 1 of the digest; --json prints every field and the
                tripwire evaluation; --digest also records the digest as sent
  forecast      record the overseer's "next done expected" for a task
  task-start    start a task's clock when its worker launches
  task-pause    stop the clock while the task waits on the user; --on <decision item>
                is required and the task must wait on that item in Acyclic
  task-resume   restart the clock
  decision      record an item as a decision the user owes: tasks waiting on it count as
                waiting on the user, and it never counts as scope growth
  mark          record the wait state now, so a quiet wake still bridges a long wait

The campaign clock is wall-clock minus waiting on the user. The overseer's writes
(show --digest, mark, decision, task-start, task-pause, task-resume, forecast) each record whether the
campaign is waiting; the interval between two writes counts as waiting only when both
saw it waiting, so time between writes, and any pause Acyclic doesn't back, counts as
active, except that a wait ends when the decisions it waited on close, not at the next
write. Waiting holds when no task runs and every ready, claimed or dependency-blocked
task is paused on an open decision item it waits for. A task never launched needs no
pause: it waits when everything it waits for is an open decision (cited by a pause or
recorded with `decision`) or a task that is itself waiting. A parked item outside the
campaign's tasks also counts as a decision, flagged as uncited until it is recorded.

A started task's clock (`running_h`) also excludes its blocked time, `blocked_h`: the
intervals where Acyclic reports the task `waiting` and every item it waits on, directly
or through waiting items, is an unfinished campaign task or a valid decision, with at
least one campaign task among them (`blocked_on` lists those campaign tasks now). It is
measured like the campaign wait, at the same writes, and a blocked interval ends at the
`done_at` of the blocking task. Only `waiting` readiness counts: Acyclic reports a
claimed task's waits only as `links.waits_for`, which also lists done items and isn't in
`item list`, and a claim means a worker holds the task, so claimed tasks keep their clock.
Campaign `active_h` and the campaign wait do not change with it.
"""

import argparse
import datetime as dt
import json
import os
import subprocess
import sys

DEFAULT_TRIPWIRES = {
    "campaign_over_high": True,
    "task_over_high": True,
    "scope_growth_pct": 25,
    "forecast_misses": 2,
    "unverified_done": True,
    "idle_ready": 1,          # hours a ready task may sit unlaunched
    "waiting_on_user": 6,     # hours the campaign may wait on the user
}
NUMERIC_TRIPWIRES = ("scope_growth_pct", "forecast_misses", "idle_ready", "waiting_on_user")
IGNORED_READINESS = ("done", "canceled", "parked", "parent")
CAMPAIGN_FILE = "campaign.json"
STATE_FILE = "scoreboard-state.json"


class ScoreboardError(Exception):
    pass


# ---------------------------------------------------------------- time helpers

def parse_time(text):
    s = text.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        t = dt.datetime.fromisoformat(s)
    except ValueError:
        raise ScoreboardError("bad time %r: use RFC 3339 such as 2026-11-07T16:00Z" % text)
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(dt.timezone.utc)


def parse_forecast(text, now):
    """ISO time, or HH:MM UTC meaning the next such time after now."""
    s = text.strip()
    if len(s) <= 5 and ":" in s:
        try:
            hh, mm = s.split(":")
            t = now.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        except ValueError:
            raise ScoreboardError("bad time %r" % text)
        return t if t > now else t + dt.timedelta(days=1)
    return parse_time(s)


def iso(t):
    return t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_range(text):
    s = text.lower().replace("h", "").replace("–", "-").replace(" ", "")
    try:
        lo, hi = [float(x) for x in s.split("-")]
    except ValueError:
        raise ScoreboardError("bad estimate %r: use LOW-HIGH hours, such as 8-12" % text)
    if lo <= 0 or hi < lo:
        raise ScoreboardError("bad estimate %r: need 0 < LOW <= HIGH" % text)
    return [lo, hi]


def fmt_hours(h):
    return ("%d" % round(h)) if abs(h - round(h)) < 0.05 else ("%.1f" % h)


def fmt_age(seconds):
    m = int(seconds // 60)
    if m < 60:
        return "%dm" % m
    return "%dh" % (m // 60)


# ------------------------------------------------------------------ Acyclic IO

def acyclic(*args):
    cmd = ["acyclic"] + list(args) + ["-o", "json"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ScoreboardError("cannot run %s: %s" % (" ".join(cmd), e))
    try:
        out = json.loads(p.stdout)
    except ValueError:
        raise ScoreboardError("%s gave non-JSON output (exit %d): %s"
                              % (" ".join(cmd), p.returncode, (p.stderr or p.stdout)[:300]))
    if not isinstance(out, dict) or not out.get("ok"):
        err = (out or {}).get("error") or {}
        raise ScoreboardError("%s failed: %s: %s" % (" ".join(cmd), err.get("code"), err.get("message")))
    return out["data"]


def item_list():
    data = acyclic("item", "list")
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ScoreboardError("unexpected `acyclic item list` schema: no data.items list")
    return data["items"]


def item_show(ids):
    if not ids:
        return []
    data = acyclic("item", "show", *ids)
    if not isinstance(data, list):
        raise ScoreboardError("unexpected `acyclic item show` schema: data is not a list")
    return data


def doctor():
    """Commit findings from `acyclic doctor`, keyed by item id with Acyclic's reason.
    `unchecked_commits` is None when this acyclic predates the field."""
    data = acyclic("doctor")
    try:
        c = data["commits"]
        def by_item(rows):
            out = {}
            for x in rows:
                out.setdefault(str(x["item"]), []).append(str(x.get("reason") or "no reason given"))
            return {k: "; ".join(v) for k, v in out.items()}
        n = int(c["unchecked"])
        listed = by_item(c["unchecked_commits"]) if "unchecked_commits" in c else None
        # Fewer rows than the count: the list is incomplete, so treat it like an older acyclic.
        if listed is not None and n > len(c["unchecked_commits"]):
            listed = None
        return {"unchecked": n, "unmerged": by_item(c["unmerged"]), "unchecked_commits": listed}
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ScoreboardError("unexpected `acyclic doctor` schema: no data.commits.unchecked/unmerged")


def resolve_root(items, ref):
    """Find the initiative or item named by id, id ending or exact title."""
    hits = [i for i in items if i["id"] == ref or i["id"].endswith(ref) and len(ref) >= 6]
    if not hits:
        hits = [i for i in items if i.get("title") == ref]
    if not hits:
        inits = acyclic("initiative", "list")["initiatives"]
        hits = [i for i in inits if i["id"] == ref or i["title"] == ref
                or (len(ref) >= 6 and i["id"].endswith(ref))]
    if len(hits) != 1:
        raise ScoreboardError("%r names %d records; give a unique title or id ending" % (ref, len(hits)))
    return hits[0]["id"]


def leaves_under(items, root_id):
    """Non-canceled leaf items below root (any depth)."""
    kids = {}
    for i in items:
        kids.setdefault(i.get("parent"), []).append(i)
    out, stack = [], [root_id]
    while stack:
        for c in kids.get(stack.pop(), []):
            if c["id"] in kids:
                stack.append(c["id"])
            elif c.get("state") != "canceled":
                out.append(c["id"])
    return sorted(out)


# ------------------------------------------------------------------- core math

def running_seconds(task_state, now):
    total = 0.0
    for start, end in (task_state or {}).get("segments", []):
        s = parse_time(start)
        e = parse_time(end) if end else now
        total += max(0.0, (e - s).total_seconds())
    return total


def live_ids(campaign):
    return (set(campaign["tasks"]) | set(campaign.get("approved_added", []))) - set(campaign.get("dropped", []))


def waits_closure(by_id, tid):
    """Every item `tid` waits for, directly or transitively, per Acyclic readiness."""
    seen, stack = set(), [tid]
    while stack:
        for k in ((by_id.get(stack.pop()) or {}).get("readiness") or {}).get("waiting") or {}:
            if k not in seen:
                seen.add(k)
                stack.append(k)
    return seen


def pause_of(state, tid):
    """The task's open pause {'at','on'}, or None when it is running or never started."""
    ts = (state.get("tasks") or {}).get(tid) or {}
    segs = ts.get("segments") or []
    if not segs or segs[-1][1] is None:
        return None
    pauses = ts.get("pauses") or []
    return pauses[-1] if pauses else {"at": segs[-1][1], "on": None}


def pause_valid(state, by_id, tid):
    """True when the task is paused on a decision item that exists, is neither done nor canceled,
    and that the task waits for in Acyclic."""
    p = pause_of(state, tid)
    d = by_id.get(p["on"]) if p and p.get("on") else None
    return bool(d) and d.get("state") not in ("done", "canceled") and d["id"] in waits_closure(by_id, tid)


def readiness_of(by_id, tid):
    return ((by_id.get(tid) or {}).get("readiness") or {}).get("readiness")


def decisions_owed(live, state, by_id):
    """Open items the user owes: cited by a valid pause of an open task, or recorded with `decision`."""
    open_tasks = [t for t in sorted(live) if readiness_of(by_id, t) not in IGNORED_READINESS]
    decisions = {pause_of(state, t)["on"] for t in open_tasks if pause_valid(state, by_id, t)}
    decisions |= {k for k in state.get("decisions") or []
                  if k not in live and k in by_id and by_id[k].get("state") not in ("done", "canceled")}
    return decisions


def task_blockers(campaign, state, by_id, tid, decisions):
    """The unfinished live campaign tasks that block `tid` now, or [] when it isn't blocked on them.

    Blocked: Acyclic reports `tid` waiting, and every item it waits on, directly or through waiting
    items, is an unfinished campaign task or a valid decision, with at least one campaign task. Says
    nothing about whether `tid` runs; the clock also requires that. Claimed tasks are never blocked
    here (see the module docstring)."""
    live = live_ids(campaign)
    if tid not in live or readiness_of(by_id, tid) != "waiting":
        return []
    blockers = []
    for k in waits_closure(by_id, tid):
        if k in live and k in by_id and by_id[k].get("state") not in ("done", "canceled"):
            blockers.append(k)
        elif k in decisions or (k in by_id and k not in live and by_id[k].get("state") == "parked"):
            continue  # a valid decision, or a parked outside item the campaign wait treats as one
        else:
            return []
    return sorted(blockers)


def is_running(ts):
    segs = (ts or {}).get("segments") or []
    return bool(segs) and segs[-1][1] is None


def blocked_seconds(ts, now, tail):
    """Blocked time inside the task's running segments; `tail` is the open blocked interval, if any."""
    running = [[parse_time(a), parse_time(b) if b else now] for a, b in (ts or {}).get("segments", [])]
    blocked = merged([[parse_time(a), parse_time(b)] for a, b in (ts or {}).get("blocks", [])] + tail)
    total = 0.0
    for rs, re_ in running:
        for bs, be in blocked:
            total += max(0.0, (min(re_, be) - max(rs, bs)).total_seconds())
    return total


def wait_status(campaign, state, items):
    """Is the campaign waiting on the user right now, and which tasks sit ready but never launched."""
    by_id = {i["id"]: i for i in items}
    live = live_ids(campaign)
    tasks = state.get("tasks") or {}

    def rd(tid):
        return readiness_of(by_id, tid)

    def on_user(tid, seen=()):
        if tid in seen or tid not in live:
            return False
        segs = (tasks.get(tid) or {}).get("segments") or []
        if segs and segs[-1][1] is None:
            return False  # running
        if pause_valid(state, by_id, tid):
            relied.add(pause_of(state, tid)["on"])
            return True
        waiting = ((by_id.get(tid) or {}).get("readiness") or {}).get("waiting") or {}
        fresh = not segs  # a started task needs its own valid pause; an unlaunched one can't have one
        return rd(tid) == "waiting" and bool(waiting) and all(
            (fresh and owed(k)) or on_user(k, seen + (tid,)) for k in waiting)

    def owed(k):
        if k in decisions:
            relied.add(k)
            return True
        if k not in live and (by_id.get(k) or {}).get("state") == "parked":
            uncited.add(k)  # likely a decision nobody recorded; flagged so the auditor can check
            relied.add(k)
            return True
        return False

    open_tasks = [t for t in sorted(live) if rd(t) not in IGNORED_READINESS]
    # a thread claim makes its later tasks `claimed` while the overseer holds them back, so only `ready` is idle
    idle = [t for t in open_tasks if rd(t) == "ready" and not (tasks.get(t) or {}).get("segments")]
    decisions = decisions_owed(live, state, by_id)
    uncited, relied = set(), set()
    flags = [on_user(t) for t in open_tasks]  # no short circuit: collect every item relied on
    waiting = bool(open_tasks) and all(flags)
    return {"waiting": waiting, "idle": idle, "decisions": sorted(decisions),
            "uncited": sorted(uncited) if waiting else [], "on": sorted(relied) if waiting else []}


def wait_closed_at(mark, rows, now):
    """When a marked wait ended because a decision it relied on closed: the earliest such done_at,
    capped at now. Earliest can undercount when a redundant decision closes first; that errs
    toward active time."""
    on = set(mark.get("on") or [])
    times = [parse_time(r["done_at"]) for r in rows
             if r.get("id") in on and r.get("state") == "done" and r.get("done_at")]
    return min(min(times), now) if times else None


def task_closed_at(mark, rows, now):
    """When a blocked interval ended because its blockers closed: the latest of their done_at, capped
    at now, but only once every blocker is done. A task stays blocked until its last blocker finishes;
    while one is still open, no time after the last write counts."""
    on = set(mark.get("on") or [])
    done = {r["id"]: parse_time(r["done_at"]) for r in rows
            if r.get("id") in on and r.get("state") == "done" and r.get("done_at")}
    if not on or set(done) != on:
        return None
    return min(max(done.values()), now)


def record_write(campaign, state, items, now):
    """Fold the current wait status into the state at an overseer write: the campaign's wait (marked by
    `wait_mark`), and each started task's blocked intervals (`blocks`, marked by its `block_mark`)."""
    ws = wait_status(campaign, state, items)
    by_id = {i["id"]: i for i in items}
    tasks = state.get("tasks") or {}
    decisions = set(ws["decisions"])
    now_blocked = {tid: task_blockers(campaign, state, by_id, tid, decisions) if is_running(ts) else []
                   for tid, ts in tasks.items()}
    mark = state.get("wait_mark")
    closing = set(mark.get("on") or []) if mark and mark["waiting"] and not ws["waiting"] else set()
    for tid, ts in tasks.items():
        bm = ts.get("block_mark") or {}
        if bm.get("blocked") and not now_blocked[tid]:
            closing |= set(bm.get("on") or [])
    # the blockers that closed decide where a wait ends; an id deleted from Acyclic would fail `item show`
    rows = item_show(sorted(k for k in closing if k in by_id))
    end = None
    if mark and mark["waiting"]:
        # still waiting: up to now; the wait ended: up to when its decisions closed, if they did
        end = now if ws["waiting"] else wait_closed_at(mark, rows, now)
    if end and end > parse_time(mark["at"]):
        segs = state.setdefault("wait_segments", [])
        if segs and segs[-1][1] == mark["at"]:
            segs[-1][1] = iso(end)
        else:
            segs.append([mark["at"], iso(end)])
    state["wait_mark"] = {"at": iso(now), "waiting": ws["waiting"]}
    if ws["waiting"]:
        state["wait_mark"]["on"] = ws["on"]
    for tid, ts in tasks.items():
        bm = ts.get("block_mark") or {}
        end = None
        if bm.get("blocked"):
            end = now if now_blocked[tid] else task_closed_at(bm, rows, now)
        if end and end > parse_time(bm["at"]):
            blocks = ts.setdefault("blocks", [])
            if blocks and blocks[-1][1] == bm["at"]:
                blocks[-1][1] = iso(end)
            else:
                blocks.append([bm["at"], iso(end)])
        ts["block_mark"] = {"at": iso(now), "blocked": bool(now_blocked[tid]), "on": now_blocked[tid]}
    rs = state.setdefault("ready_since", {})
    for t in ws["idle"]:
        rs.setdefault(t, iso(now))
    for t in [t for t in rs if t not in ws["idle"]]:
        del rs[t]


def merged(intervals):
    out = []
    for s_, e_ in sorted(intervals):
        if out and s_ <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e_)
        else:
            out.append([s_, e_])
    return out


def evaluate(campaign, state, items, shown, doc, now):
    """Pure function: all scoreboard fields from frozen campaign, state and Acyclic data."""
    start = parse_time(campaign["start"])
    frozen = list(campaign["tasks"])
    approved = set(campaign.get("approved_added", []))
    launch = set(campaign["launch_tasks"])
    dropped = set(campaign.get("dropped", []))
    total_ids = sorted((set(frozen) | approved) - dropped)

    shown_by = {s["id"]: s for s in shown}
    by_id = {i["id"]: i for i in items}
    decisions = decisions_owed(live_ids(campaign), state, by_id)
    unmerged = doc["unmerged"]
    unchecked = doc["unchecked_commits"]

    tasks = {}
    done_times = []
    unverified = []
    for tid in total_ids:
        it = shown_by.get(tid) or by_id.get(tid)
        if it is None:
            raise ScoreboardError("frozen task %s is missing from Acyclic" % tid)
        row = {"id": tid, "title": it.get("title"), "state": it.get("state"), "done": False}
        if it.get("state") == "done":
            ev = (it.get("evidence") or {})
            commit = ev.get("commit")
            done_at = it.get("done_at")
            reason = None
            if not commit:
                reason = "no merge commit recorded"
            elif tid in unmerged:
                reason = "unmerged: %s" % unmerged[tid]
            elif unchecked is None and doc["unchecked"] > 0:
                reason = "unchecked: this acyclic doesn't say which commits; update acyclic"
            elif unchecked and tid in unchecked:
                reason = "unchecked: %s" % unchecked[tid]
            ok = reason is None
            if ok:
                row["done"] = True
                row["done_at"] = done_at
                if done_at:
                    done_times.append(parse_time(done_at))
            else:
                row["unverified_done"] = reason
                unverified.append({"task": tid, "title": it.get("title"), "reason": reason})
        ts = (state.get("tasks") or {}).get(tid)
        est = (campaign.get("task_estimates") or {}).get(tid)
        row["estimate_h"] = est
        blockers = [] if it.get("state") in ("done", "canceled") else task_blockers(
            campaign, state, by_id, tid, decisions)
        row["blocked_on"] = blockers
        row["blocked_h"] = 0.0
        if ts:
            # the open blocked interval counts while the task still runs blocked, as the campaign's tail does
            tail = []
            bm = ts.get("block_mark") or {}
            if bm.get("blocked"):
                end = now if blockers and is_running(ts) else task_closed_at(bm, shown, now)
                if end and end > parse_time(bm["at"]):
                    tail = [[parse_time(bm["at"]), end]]
            blocked_s = blocked_seconds(ts, now, tail)
            row["blocked_h"] = round(blocked_s / 3600.0, 2)
            row["running_h"] = round((running_seconds(ts, now) - blocked_s) / 3600.0, 2)
            row["paused"] = bool(ts["segments"]) and ts["segments"][-1][1] is not None
            first = parse_time(ts["segments"][0][0])
            row["paused_h"] = round(max(0.0, (now - first).total_seconds() - running_seconds(ts, now)) / 3600.0, 2)
            pz = pause_of(state, tid)
            if pz:
                row["pause"] = {"on": pz.get("on"), "valid": pause_valid(state, by_id, tid)}
            row["over_high"] = bool(est) and it.get("state") != "done" and row["running_h"] > est[1]
        tasks[tid] = row

    done = sum(1 for r in tasks.values() if r["done"])
    last_digest = state.get("last_digest") or {"at": campaign["start"], "done": 0}
    since = done - last_digest["done"]
    last_done = max(done_times) if done_times else None

    elapsed_h = (now - start).total_seconds() / 3600.0
    ws = wait_status(campaign, state, items)
    mark = state.get("wait_mark")
    segs = [[parse_time(a), parse_time(b)] for a, b in state.get("wait_segments", [])]
    tail = stretch = 0.0
    if mark and mark["waiting"]:
        end = now if ws["waiting"] else wait_closed_at(mark, shown, now)
        tail = max(0.0, (end - parse_time(mark["at"])).total_seconds()) if end else 0.0
    if ws["waiting"]:
        stretch = tail
    if tail and segs and segs[-1][1] == parse_time(mark["at"]):
        stretch += (segs[-1][1] - segs[-1][0]).total_seconds()
    waiting_s = sum(max(0.0, (min(b, now) - max(a, start)).total_seconds()) for a, b in segs) + tail
    paused_iv = []
    for ts in (state.get("tasks") or {}).values():
        ss = ts.get("segments") or []
        for k, (_, end) in enumerate(ss):
            if end:
                nxt = parse_time(ss[k + 1][0]) if k + 1 < len(ss) else now
                paused_iv.append([parse_time(end), nxt])
    paused_s = sum((b - a).total_seconds() for a, b in merged(paused_iv))
    waiting_h = min(waiting_s, elapsed_h * 3600.0) / 3600.0
    unexplained_h = max(0.0, paused_s - waiting_s) / 3600.0
    active_h = elapsed_h - waiting_h
    lo, hi = campaign["estimate_h"]

    root = campaign.get("under")
    if root:
        current = (set(leaves_under(items, root)) - set(campaign.get("excluded", []))
                   - dropped - set(state.get("decisions") or []))
        extra = sorted(current - launch)
    else:
        extra = []
    unapproved = [t for t in extra if t not in approved]
    base = max(1, len(launch))
    growth_pct = 100.0 * len(unapproved) / base

    forecasts, seen = [], set()
    for f in state.get("forecasts", []):
        if (f["task"], f["at"]) in seen or f["task"] not in tasks:
            continue  # a repeated forecast is not a new one; a dropped task's forecast is moot
        seen.add((f["task"], f["at"]))
        at = parse_time(f["at"])
        t = tasks.get(f["task"])
        done_at = parse_time(t["done_at"]) if t and t.get("done_at") else None
        met = done_at is not None and done_at <= at
        missed = (not met) and at < now
        forecasts.append({"task": f["task"], "at": f["at"], "made_at": f["made_at"],
                          "met": met, "missed": missed})
    misses = sum(1 for f in forecasts if f["missed"])
    pending = sorted((f for f in forecasts if not f["met"] and not f["missed"]),
                     key=lambda f: f["at"])

    cfg = dict(DEFAULT_TRIPWIRES)
    cfg.update(campaign.get("tripwires") or {})
    over_tasks = [r for r in tasks.values() if r.get("over_high")]

    def by_title(i):
        return ((shown_by.get(i) or by_id.get(i) or {}).get("title")) or i

    ready_since = state.get("ready_since") or {}
    idle_ready = sorted(((t, (now - parse_time(ready_since[t])).total_seconds() / 3600.0)
                         for t in ws["idle"] if t in ready_since), key=lambda x: -x[1])
    tripwires = [
        {"name": "campaign_over_high", "enabled": bool(cfg["campaign_over_high"]),
         "fired": bool(cfg["campaign_over_high"]) and done < len(total_ids) and active_h > hi,
         "value": round(active_h, 1), "limit": hi,
         "evidence": "active %.1fh of %s-%sh estimate (%.1fh elapsed, %.1fh waiting on the user), %d/%d done" % (
             active_h, fmt_hours(lo), fmt_hours(hi), elapsed_h, waiting_h, done, len(total_ids))},
        {"name": "task_over_high", "enabled": bool(cfg["task_over_high"]),
         "fired": bool(cfg["task_over_high"]) and bool(over_tasks),
         "value": max([r["running_h"] / r["estimate_h"][1] for r in over_tasks] or [0]),
         "limit": 1,
         "evidence": "; ".join("%s running %.1fh, estimate high end %sh" % (
             r["title"] or r["id"], r["running_h"], fmt_hours(r["estimate_h"][1])) for r in over_tasks)},
        {"name": "scope_growth", "enabled": cfg["scope_growth_pct"] is not None,
         "fired": cfg["scope_growth_pct"] is not None and growth_pct > cfg["scope_growth_pct"],
         "value": round(growth_pct, 1), "limit": cfg["scope_growth_pct"],
         "evidence": "%d unapproved task(s) added to %d launch tasks (%.0f%%)" % (
             len(unapproved), len(launch), growth_pct)},
        {"name": "forecast_missed", "enabled": cfg["forecast_misses"] is not None,
         "fired": cfg["forecast_misses"] is not None and misses >= cfg["forecast_misses"],
         "value": misses, "limit": cfg["forecast_misses"],
         "evidence": "%d forecast(s) missed: %s" % (
             misses, ", ".join("%s due %s" % (f["task"], f["at"]) for f in forecasts if f["missed"]))},
        {"name": "idle_ready", "enabled": cfg["idle_ready"] is not None,
         "fired": cfg["idle_ready"] is not None and bool(idle_ready) and idle_ready[0][1] > cfg["idle_ready"],
         "value": round(idle_ready[0][1], 1) if idle_ready else 0, "limit": cfg["idle_ready"],
         "evidence": "; ".join("%s ready %.1fh, not launched" % (by_title(t), h) for t, h in idle_ready)},
        {"name": "waiting_on_user", "enabled": cfg["waiting_on_user"] is not None,
         "fired": cfg["waiting_on_user"] is not None and stretch / 3600.0 > cfg["waiting_on_user"],
         "value": round(stretch / 3600.0, 1), "limit": cfg["waiting_on_user"],
         "evidence": "campaign waiting on the user %.1fh: %s" % (stretch / 3600.0, "; ".join(
             "%s%s: %s" % (by_title(d), " (uncited parked item %s)" % d if d in ws["uncited"] else "",
                           ((shown_by.get(d) or {}).get("notes") or "no notes").strip())
             for d in ws["on"]))},
        {"name": "unverified_done", "enabled": bool(cfg["unverified_done"]),
         "fired": bool(cfg["unverified_done"]) and bool(unverified),
         "value": len(unverified), "limit": 0,
         "evidence": "; ".join("%s: %s" % (u["title"] or u["task"], u["reason"]) for u in unverified)},
    ]

    return {
        "name": campaign["name"], "goal": campaign["goal"], "metric": campaign.get("metric"),
        "start": campaign["start"], "now": iso(now),
        "done": done, "total": len(total_ids), "done_since_digest": since,
        "last_digest_at": last_digest["at"],
        "last_done_at": iso(last_done) if last_done else None,
        "last_done_age_s": int((now - last_done).total_seconds()) if last_done else None,
        "elapsed_h": round(elapsed_h, 2), "active_h": round(active_h, 2),
        "waiting_h": round(waiting_h, 2), "waiting_unexplained_h": round(unexplained_h, 2),
        "waiting_now": ws["waiting"], "waiting_on": ws["on"] if ws["waiting"] else ws["decisions"],
        "waiting_on_uncited": ws["uncited"], "estimate_h": [lo, hi],
        "over_high": active_h > hi and done < len(total_ids),
        "scope_added": len(extra), "scope_added_unapproved": len(unapproved),
        "scope_growth_pct": round(growth_pct, 1), "added_tasks": extra,
        "added_unapproved": unapproved, "decisions": sorted(state.get("decisions") or []),
        "tasks": tasks, "forecasts": forecasts, "missed_forecasts": misses,
        "next_done": pending[0] if pending else None,
        "amendments": campaign.get("amendments", []),
        "tripwires": tripwires,
    }


def line1(r):
    since_t = parse_time(r["last_digest_at"]).strftime("%H:%M")
    age = ("last done %s ago" % fmt_age(r["last_done_age_s"])
           if r["last_done_age_s"] is not None else "none done yet")
    lo, hi = r["estimate_h"]
    warn = " ⚠" if r["over_high"] else ""
    waiting = (" · %sh waiting on you" % fmt_hours(r["waiting_h"])) if r["waiting_h"] >= 0.05 else ""
    return "%s · %d/%d done (%+d since %s) · %s · %sh active of %s–%sh%s%s · scope +%d since launch" % (
        r["name"], r["done"], r["total"], r["done_since_digest"], since_t, age,
        fmt_hours(r["active_h"]), fmt_hours(lo), fmt_hours(hi), warn, waiting, r["scope_added"])


# -------------------------------------------------------------------- file IO

def read_json(path, what):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise ScoreboardError("%s not found at %s" % (what, path))
    except ValueError as e:
        raise ScoreboardError("%s at %s is not valid JSON: %s" % (what, path, e))


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def load_state(d):
    p = os.path.join(d, STATE_FILE)
    return read_json(p, "state") if os.path.exists(p) else {"tasks": {}, "forecasts": []}


# ------------------------------------------------------------------- commands

def resolve_tasks(items, refs):
    out = []
    for ref in refs:
        hits = [i["id"] for i in items if i["id"] == ref or (len(ref) >= 6 and i["id"].endswith(ref))
                or i.get("title") == ref]
        if len(hits) != 1:
            raise ScoreboardError("task %r names %d items" % (ref, len(hits)))
        out.append(hits[0])
    return out


def parse_tripwire(k, v):
    numeric = k in NUMERIC_TRIPWIRES
    if numeric:
        if v == "off":
            return None
        try:
            n = float(v)
        except ValueError:
            n = -1
        if n < 0:
            raise ScoreboardError("tripwire %s takes a number >= 0 or off, not %r" % (k, v))
        return int(n) if n == int(n) else n
    if v.lower() not in ("true", "false", "on", "off"):
        raise ScoreboardError("tripwire %s takes on or off, not %r" % (k, v))
    return v.lower() in ("true", "on")


def cmd_freeze(a, d, now):
    path = os.path.join(d, CAMPAIGN_FILE)
    items = item_list()
    est_map = {}
    for kv in a.task_estimate or []:
        k, _, v = kv.partition("=")
        est_map[resolve_tasks(items, [k])[0]] = parse_range(v)
    if a.amend:
        c = read_json(path, "campaign")
        if not (a.approved_by and a.reason):
            raise ScoreboardError("--amend needs --approved-by and --reason: amendments need the user's approval")
        change = {}
        if a.goal:
            change["goal"] = a.goal
        if a.estimate:
            change["estimate_h"] = parse_range(a.estimate)
        if est_map:
            change["task_estimates"] = est_map
        added = resolve_tasks(items, a.add_task or [])
        if added:
            change["approved_added"] = added
        dropped = resolve_tasks(items, a.drop_task or [])
        if dropped:
            change["dropped"] = dropped
        if not change:
            raise ScoreboardError("--amend changed nothing: give --goal, --estimate, --task-estimate, --add-task or --drop-task")
        c.setdefault("amendments", []).append({
            "at": iso(now), "approved_by": a.approved_by, "reason": a.reason,
            "from": {k: c.get(k) for k in change}, "to": change})
        for k, v in change.items():
            if k in ("approved_added", "dropped"):
                c[k] = sorted(set(c.get(k, [])) | set(v))
            elif k == "task_estimates":
                c.setdefault(k, {}).update(v)
            else:
                c[k] = v
        write_json(path, c)
        print("amended %s (approved by %s)" % (CAMPAIGN_FILE, a.approved_by))
        return
    if os.path.exists(path):
        raise ScoreboardError("%s exists; frozen scope changes only through --amend with the user's approval" % path)
    if not (a.name and a.goal and a.estimate):
        raise ScoreboardError("freeze needs --name, --goal (the user's words, verbatim) and --estimate")
    if bool(a.under) == bool(a.tasks):
        raise ScoreboardError("freeze needs exactly one of --under (initiative or epic) or --tasks")
    root = None
    if a.under:
        root = resolve_root(items, a.under)
        excluded = resolve_tasks(items, a.exclude or [])
        tasks = [t for t in leaves_under(items, root) if t not in excluded]
    else:
        excluded = []
        tasks = resolve_tasks(items, a.tasks)
    if not tasks:
        raise ScoreboardError("no open tasks to freeze")
    for t in est_map:
        if t not in tasks:
            raise ScoreboardError("--task-estimate names %s, which is not a frozen task" % t)
    c = {
        "name": a.name, "goal": a.goal, "start": iso(parse_time(a.start) if a.start else now),
        "under": root, "excluded": excluded, "tasks": tasks, "launch_tasks": tasks, "approved_added": [],
        "estimate_h": parse_range(a.estimate), "task_estimates": est_map,
        "metric": ({"name": a.metric[0], "baseline": a.metric[1], "target": a.metric[2]}
                   if a.metric else None),
        "tripwires": dict(DEFAULT_TRIPWIRES), "amendments": [],
    }
    for kv in a.tripwire or []:
        k, _, v = kv.partition("=")
        if k not in DEFAULT_TRIPWIRES:
            raise ScoreboardError("unknown tripwire %r; known: %s" % (k, ", ".join(sorted(DEFAULT_TRIPWIRES))))
        c["tripwires"][k] = parse_tripwire(k, v)
    write_json(path, c)
    print("froze %d task(s) in %s" % (len(tasks), path))


def snapshot(d, now):
    campaign = read_json(os.path.join(d, CAMPAIGN_FILE), "campaign")
    state = load_state(d)
    items = item_list()
    ids = set(campaign["tasks"]) | set(campaign.get("approved_added", []))
    ids |= {ts["pauses"][-1]["on"] for ts in (state.get("tasks") or {}).values() if ts.get("pauses")}
    ws = wait_status(campaign, state, items)
    ids |= set(state.get("decisions") or []) | set(ws["uncited"]) | set((state.get("wait_mark") or {}).get("on") or [])
    ids |= {k for ts in (state.get("tasks") or {}).values() for k in (ts.get("block_mark") or {}).get("on") or []}
    ids &= {i["id"] for i in items}  # an id deleted from Acyclic would make `item show` fail
    return campaign, state, items, evaluate(campaign, state, items, item_show(sorted(ids)), doctor(), now)


def cmd_show(a, d, now):
    campaign, state, items, r = snapshot(d, now)
    if a.digest:
        record_write(campaign, state, items, now)
        state["last_digest"] = {"at": iso(now), "done": r["done"]}
        write_json(os.path.join(d, STATE_FILE), state)
    if a.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        print(line1(r))


def _task(items, ref):
    return resolve_tasks(items, [ref])[0]


def live_tasks(campaign):
    return live_ids(campaign)


def cmd_forecast(a, d, now):
    campaign = read_json(os.path.join(d, CAMPAIGN_FILE), "campaign")
    items = item_list()
    tid = _task(items, a.task)
    if tid not in live_tasks(campaign):
        raise ScoreboardError("%s is not a frozen task" % tid)
    state = load_state(d)
    when = iso(parse_forecast(a.time, now))
    if any(f["task"] == tid and f["at"] == when for f in state.get("forecasts", [])):
        print("forecast %s done by %s (already recorded)" % (tid, when))
        return
    state.setdefault("forecasts", []).append({"task": tid, "at": when, "made_at": iso(now)})
    record_write(campaign, state, items, now)
    write_json(os.path.join(d, STATE_FILE), state)
    print("forecast %s done by %s" % (tid, state["forecasts"][-1]["at"]))


def cmd_mark(a, d, now):
    campaign = read_json(os.path.join(d, CAMPAIGN_FILE), "campaign")
    state = load_state(d)
    record_write(campaign, state, item_list(), now)
    write_json(os.path.join(d, STATE_FILE), state)
    print("marked: %s" % ("waiting" if state["wait_mark"]["waiting"] else "active"))


def cmd_decision(a, d, now):
    campaign = read_json(os.path.join(d, CAMPAIGN_FILE), "campaign")
    items = item_list()
    did = _task(items, a.item)
    if did in live_tasks(campaign):
        raise ScoreboardError("%s is a campaign task, not a decision the user owes" % did)
    state = load_state(d)
    known = state.setdefault("decisions", [])
    if did not in known:
        known.append(did)
    record_write(campaign, state, items, now)
    write_json(os.path.join(d, STATE_FILE), state)
    print("decision: %s" % did)


def cmd_task_clock(a, d, now):
    campaign = read_json(os.path.join(d, CAMPAIGN_FILE), "campaign")
    items = item_list()
    tid = _task(items, a.task)
    if tid not in live_tasks(campaign):
        raise ScoreboardError("%s is not a frozen task" % tid)
    if a.cmd == "task-pause" and not a.on:
        raise ScoreboardError("task-pause needs --on <decision item>: pause only for a decision the user owes, "
                              "which the task waits for in Acyclic")
    state = load_state(d)
    record_write(campaign, state, items, now)  # bridge the wait up to this change
    t = state.setdefault("tasks", {}).get(tid)
    if a.cmd == "task-start":
        if t:
            raise ScoreboardError("%s already started; use task-resume after a pause" % tid)
        state["tasks"][tid] = {"segments": [[iso(now), None]]}
    else:
        if not t:
            raise ScoreboardError("%s was never started" % tid)
        open_seg = t["segments"][-1][1] is None
        if a.cmd == "task-pause":
            if not open_seg:
                raise ScoreboardError("%s is already paused" % tid)
            on = _task(items, a.on)
            t["segments"][-1][1] = iso(now)
            t.setdefault("pauses", []).append({"at": iso(now), "on": on})
            if not pause_valid(state, {i["id"]: i for i in items}, tid):
                print("warning: %s does not wait for open item %s in Acyclic; this pause counts as active time"
                      % (tid, on), file=sys.stderr)
        else:
            if open_seg:
                raise ScoreboardError("%s is already running" % tid)
            t["segments"].append([iso(now), None])
    record_write(campaign, state, items, now)
    write_json(os.path.join(d, STATE_FILE), state)
    print("%s: %s" % (a.cmd, tid))


def build_parser():
    p = argparse.ArgumentParser(prog="scoreboard.py", description=__doc__.split("\n\n")[0])
    p.add_argument("--campaign", default=".", metavar="DIR", help="run checkout holding campaign.json")
    p.add_argument("--now", help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--name")
    f.add_argument("--goal", help="the user's goal, verbatim")
    f.add_argument("--under", help="initiative or epic whose leaf tasks are frozen")
    f.add_argument("--tasks", nargs="+", help="explicit task ids, id endings or titles")
    f.add_argument("--exclude", nargs="+", help="with --under: leaves that are not merge-proven tasks "
                   "(approval gates, decisions); they count neither as tasks nor as scope")
    f.add_argument("--estimate", help="campaign hours, LOW-HIGH")
    f.add_argument("--task-estimate", nargs="+", metavar="TASK=LOW-HIGH")
    f.add_argument("--start", help="RFC 3339; default now")
    f.add_argument("--metric", nargs=3, metavar=("NAME", "BASELINE", "TARGET"))
    f.add_argument("--tripwire", nargs="+", metavar="NAME=VALUE",
                   help="override a default; scope_growth_pct, forecast_misses, idle_ready and waiting_on_user take numbers or off")
    f.add_argument("--amend", action="store_true", help="record an approved change to frozen fields")
    f.add_argument("--approved-by")
    f.add_argument("--reason")
    f.add_argument("--add-task", nargs="+", help="approve these added tasks into the frozen scope")
    f.add_argument("--drop-task", nargs="+", help="remove these tasks from the scope (trimmed, canceled, "
                   "or an added gate that is not merge-proven work)")
    s = sub.add_parser("show")
    s.add_argument("--json", action="store_true")
    s.add_argument("--digest", action="store_true", help="record this digest as sent (overseer only)")
    fc = sub.add_parser("forecast")
    fc.add_argument("task")
    fc.add_argument("time", help="RFC 3339, or HH:MM UTC (the next such time)")
    sub.add_parser("mark")
    dc = sub.add_parser("decision")
    dc.add_argument("item", help="the open decision item the user owes")
    for name in ("task-start", "task-pause", "task-resume"):
        tp = sub.add_parser(name)
        tp.add_argument("task")
        if name == "task-pause":
            tp.add_argument("--on", metavar="DECISION", help="the decision item the user owes (required); "
                            "the task must wait for it in Acyclic")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    now = parse_time(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    try:
        {"freeze": cmd_freeze, "show": cmd_show, "forecast": cmd_forecast, "mark": cmd_mark,
         "decision": cmd_decision}.get(
            a.cmd, cmd_task_clock)(a, a.campaign, now)
    except ScoreboardError as e:
        print("scoreboard: %s" % e, file=sys.stderr)
        return 1
    except (KeyError, TypeError) as e:
        print("scoreboard: unexpected data shape (%s: %s); check campaign.json and `acyclic prime`"
              % (type(e).__name__, e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
