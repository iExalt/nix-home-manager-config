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
  task-pause    stop the clock while the task waits on the user
  task-resume   restart the clock
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
}
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
    return ("%d" % h) if abs(h - round(h)) < 0.05 else ("%.1f" % h)


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
    data = acyclic("doctor")
    try:
        c = data["commits"]
        return {"unchecked": int(c["unchecked"]), "unmerged": [str(x) for x in c["unmerged"]]}
    except (KeyError, TypeError, ValueError):
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


def evaluate(campaign, state, items, shown, doc, now):
    """Pure function: all scoreboard fields from frozen campaign, state and Acyclic data."""
    start = parse_time(campaign["start"])
    frozen = list(campaign["tasks"])
    approved = set(campaign.get("approved_added", []))
    launch = set(campaign["launch_tasks"])
    total_ids = sorted(set(frozen) | approved)

    shown_by = {s["id"]: s for s in shown}
    by_id = {i["id"]: i for i in items}
    unmerged = set(doc["unmerged"])

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
            if commit and commit not in unmerged and doc["unchecked"] == 0:
                row["done"] = True
                row["done_at"] = done_at
                if done_at:
                    done_times.append(parse_time(done_at))
            else:
                reason = ("no merge commit recorded" if not commit
                          else "commit unmerged" if commit in unmerged
                          else "tracker reports %d unchecked commit(s)" % doc["unchecked"])
                row["unverified_done"] = reason
                unverified.append({"task": tid, "title": it.get("title"), "reason": reason})
        ts = (state.get("tasks") or {}).get(tid)
        est = (campaign.get("task_estimates") or {}).get(tid)
        row["estimate_h"] = est
        if ts:
            row["running_h"] = round(running_seconds(ts, now) / 3600.0, 2)
            row["paused"] = bool(ts["segments"]) and ts["segments"][-1][1] is not None
            row["over_high"] = bool(est) and not row["done"] and row["running_h"] > est[1]
        tasks[tid] = row

    done = sum(1 for r in tasks.values() if r["done"])
    last_digest = state.get("last_digest") or {"at": campaign["start"], "done": 0}
    since = done - last_digest["done"]
    last_done = max(done_times) if done_times else None

    elapsed_h = (now - start).total_seconds() / 3600.0
    lo, hi = campaign["estimate_h"]

    root = campaign.get("under")
    if root:
        current = set(leaves_under(items, root)) - set(campaign.get("excluded", []))
        extra = sorted(current - launch)
    else:
        extra = []
    unapproved = [t for t in extra if t not in approved]
    base = max(1, len(launch))
    growth_pct = 100.0 * len(unapproved) / base

    forecasts = []
    for f in state.get("forecasts", []):
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
    tripwires = [
        {"name": "campaign_over_high", "enabled": bool(cfg["campaign_over_high"]),
         "fired": bool(cfg["campaign_over_high"]) and done < len(total_ids) and elapsed_h > hi,
         "value": round(elapsed_h, 1), "limit": hi,
         "evidence": "elapsed %.1fh of %s-%sh estimate, %d/%d done" % (
             elapsed_h, fmt_hours(lo), fmt_hours(hi), done, len(total_ids))},
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
        "elapsed_h": round(elapsed_h, 2), "estimate_h": [lo, hi],
        "over_high": elapsed_h > hi and done < len(total_ids),
        "scope_added": len(extra), "scope_added_unapproved": len(unapproved),
        "scope_growth_pct": round(growth_pct, 1), "added_tasks": extra,
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
    return "%s · %d/%d done (%+d since %s) · %s · %sh of %s–%sh%s · scope +%d since launch" % (
        r["name"], r["done"], r["total"], r["done_since_digest"], since_t, age,
        fmt_hours(r["elapsed_h"]), fmt_hours(lo), fmt_hours(hi), warn, r["scope_added"])


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
        if not change:
            raise ScoreboardError("--amend changed nothing: give --goal, --estimate, --task-estimate or --add-task")
        c.setdefault("amendments", []).append({
            "at": iso(now), "approved_by": a.approved_by, "reason": a.reason,
            "from": {k: c.get(k) for k in change}, "to": change})
        for k, v in change.items():
            if k == "approved_added":
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
        c["tripwires"][k] = (None if v == "off" else
                             (float(v) if "." in v else int(v)) if v.replace(".", "").isdigit()
                             else v.lower() == "true")
    write_json(path, c)
    print("froze %d task(s) in %s" % (len(tasks), path))


def snapshot(d, now):
    campaign = read_json(os.path.join(d, CAMPAIGN_FILE), "campaign")
    state = load_state(d)
    items = item_list()
    ids = sorted(set(campaign["tasks"]) | set(campaign.get("approved_added", [])))
    return campaign, state, evaluate(campaign, state, items, item_show(ids), doctor(), now)


def cmd_show(a, d, now):
    _, state, r = snapshot(d, now)
    if a.digest:
        state["last_digest"] = {"at": iso(now), "done": r["done"]}
        write_json(os.path.join(d, STATE_FILE), state)
    if a.json:
        print(json.dumps(r, indent=2, sort_keys=True))
    else:
        print(line1(r))


def _task(items, ref):
    return resolve_tasks(items, [ref])[0]


def cmd_forecast(a, d, now):
    campaign = read_json(os.path.join(d, CAMPAIGN_FILE), "campaign")
    tid = _task(item_list(), a.task)
    if tid not in set(campaign["tasks"]) | set(campaign.get("approved_added", [])):
        raise ScoreboardError("%s is not a frozen task" % tid)
    state = load_state(d)
    state.setdefault("forecasts", []).append(
        {"task": tid, "at": iso(parse_forecast(a.time, now)), "made_at": iso(now)})
    write_json(os.path.join(d, STATE_FILE), state)
    print("forecast %s done by %s" % (tid, state["forecasts"][-1]["at"]))


def cmd_task_clock(a, d, now):
    campaign = read_json(os.path.join(d, CAMPAIGN_FILE), "campaign")
    tid = _task(item_list(), a.task)
    if tid not in set(campaign["tasks"]) | set(campaign.get("approved_added", [])):
        raise ScoreboardError("%s is not a frozen task" % tid)
    state = load_state(d)
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
            t["segments"][-1][1] = iso(now)
        else:
            if open_seg:
                raise ScoreboardError("%s is already running" % tid)
            t["segments"].append([iso(now), None])
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
                   help="override a default; scope_growth_pct and forecast_misses take numbers or off")
    f.add_argument("--amend", action="store_true", help="record an approved change to frozen fields")
    f.add_argument("--approved-by")
    f.add_argument("--reason")
    f.add_argument("--add-task", nargs="+", help="approve these added tasks into the frozen scope")
    s = sub.add_parser("show")
    s.add_argument("--json", action="store_true")
    s.add_argument("--digest", action="store_true", help="record this digest as sent (overseer only)")
    fc = sub.add_parser("forecast")
    fc.add_argument("task")
    fc.add_argument("time", help="RFC 3339, or HH:MM UTC (the next such time)")
    for name in ("task-start", "task-pause", "task-resume"):
        sub.add_parser(name).add_argument("task")
    return p


def main(argv=None):
    a = build_parser().parse_args(argv)
    now = parse_time(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    try:
        {"freeze": cmd_freeze, "show": cmd_show, "forecast": cmd_forecast}.get(
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
