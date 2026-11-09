#!/usr/bin/env python3
"""Log time estimates and actuals, and compute calibration from them.

    estimates.py log < record.json       validate one record and append it
    estimates.py check                   validate every line of the log
    estimates.py estimate --kind K --low L --high H   turn a gut range into calibrated numbers
    estimates.py stats [--window N]      current bias factor and spread, overall and per kind
    estimates.py stats --backtest        score that procedure walk-forward on past records

The log is JSONL at $TIME_ESTIMATE_LOG, default ~/.local/state/agent-estimates.jsonl.
Stdlib only; Python 3.9+.
"""
import argparse
import datetime as dt
import json
import math
import os
import pathlib
import statistics as st
import sys

KINDS = ("small-fix", "existing-code", "multi-component", "bounded-operation", "audit",
         "investigation", "planning", "docs", "eval")
OUTCOMES = ("done", "partial", "stopped", "abandoned")
SOURCES = ("live", "md-port", "md-port-prose")
INCLUDES = ("impl", "review", "ci", "publish", "proof")
NUM = (int, float)
STR = (str,)
# key -> (allowed types, required for live records)
FIELDS = {
    "v": ((int,), False), "logged_at": (STR, False), "date": (STR, False),
    "source": (STR, False), "port_ref": ((int,), False), "port_kind": (STR, False),
    "thread_id": (STR, False), "parent_id": (STR, False), "repo": (STR, False),
    "task": (STR, True), "harness": (STR, False), "model": (STR, False),
    "kind": (STR, True),
    "est_low_h": (NUM, True), "est_high_h": (NUM, True),
    "est_rounds_low": (NUM, False), "est_rounds_high": (NUM, False),
    "raw_low_h": (NUM, False), "raw_high_h": (NUM, False), "bias_factor": (NUM, False),
    "anchor": (STR, False), "est_at": (STR, False), "includes": ((list,), False),
    "probe": ((bool,), False), "probe_minutes": (NUM, False),
    "actual_h": (NUM, False), "actual_rounds": (NUM, False), "blocked_h": (NUM, False),
    "scope_h": (NUM, False), "compactions": ((int,), False),
    "started_at": (STR, False), "ended_at": (STR, False), "outcome": (STR, True),
    "reasoning": (STR, False), "cause": (STR, False), "lesson": (STR, False),
    "suggestion": (STR, False), "narrative": (STR, False),
    # percentiles beyond the 50% band (est_low_h = p25, est_high_h = p75) and their drivers
    "est_median_h": (NUM, False), "est_p10_h": (NUM, False), "est_p90_h": (NUM, False),
    "why_low": (STR, False), "why_high": (STR, False),
    "revisions": ((list,), False),
}
REVISION_FIELDS = {"at": STR, "elapsed_h": NUM, "remaining_low_h": NUM,
                   "remaining_median_h": NUM, "remaining_high_h": NUM, "trigger": STR,
                   "reason": STR}
REVISION_REQUIRED = ("at", "elapsed_h", "remaining_low_h", "remaining_high_h")
TRIGGERS = ("probe", "round", "boundary", "overrun", "other")
MAX_REVISIONS = 50
PORTED_OPTIONAL = {"kind", "est_low_h", "est_high_h"}
MAX_RECORD_BYTES = 64 * 1024
HEADLINE_WINDOW = 60
PERCENTILE_MIN = 30  # below this many headline units, percentiles are noise
SHRINK_N = 8      # per-kind factor reaches full weight at this many units
SPREAD_N = 12     # per-kind quartiles used only from this many units
BACKTEST_START = 30


def log_path():
    return pathlib.Path(os.environ.get("TIME_ESTIMATE_LOG")
                        or pathlib.Path.home() / ".local/state/agent-estimates.jsonl")


def validate(rec):
    """Return (errors, warnings) for one record; no errors means valid."""
    if not isinstance(rec, dict):
        return ["record is not a JSON object"], []
    errs = [f"unknown key {k!r}" for k in rec if k not in FIELDS]
    warns = []
    source = rec.get("source", "live")
    ported = source in ("md-port", "md-port-prose")
    for k, (types, required) in FIELDS.items():
        val = rec.get(k)
        if val is None:
            # Ported entries keep numbers and kinds null where the Markdown never stated them.
            if required and not (ported and k in PORTED_OPTIONAL):
                errs.append(f"missing {k}")
            continue
        if not isinstance(val, types) or (isinstance(val, bool) and bool not in types):
            errs.append(f"{k} has type {type(val).__name__}")
    if errs:
        return errs, warns
    if rec.get("v", 1) != 1:
        errs.append(f"v {rec['v']} is not 1")
    if not rec["task"].strip():
        errs.append("task is empty")
    errs += [f"{k} is not finite" for k, v in rec.items()
             if isinstance(v, float) and not math.isfinite(v)]
    if rec.get("kind") is not None and rec["kind"] not in KINDS:
        errs.append(f"kind {rec['kind']!r} is not one of {', '.join(KINDS)}")
    if rec["outcome"] not in OUTCOMES:
        errs.append(f"outcome {rec['outcome']!r} is not one of {', '.join(OUTCOMES)}")
    if source not in SOURCES:
        errs.append(f"source {source!r} is not one of {', '.join(SOURCES)}")
    bad = [x for x in rec.get("includes") or [] if x not in INCLUDES]
    if bad:
        errs.append(f"includes has {bad}; allowed: {', '.join(INCLUDES)}")
    for lo, hi in (("est_low_h", "est_high_h"), ("raw_low_h", "raw_high_h"),
                   ("est_rounds_low", "est_rounds_high")):
        a, b = rec.get(lo), rec.get(hi)
        if (a is None) != (b is None):
            errs.append(f"{lo} and {hi} must be given together")
        elif a is not None and not (0 <= a <= b):
            errs.append(f"need 0 <= {lo} <= {hi}")
    chain = [(k, rec[k]) for k in ("est_p10_h", "est_low_h", "est_median_h", "est_high_h",
                                    "est_p90_h") if rec.get(k) is not None]
    if any(a[1] > b[1] for a, b in zip(chain, chain[1:])):
        errs.append("need est_p10_h <= est_low_h <= est_median_h <= est_high_h <= est_p90_h")
    errs += validate_revisions(rec.get("revisions"), rec.get("actual_h"))
    if not ported and rec.get("est_low_h") is not None and rec["est_low_h"] <= 0:
        errs.append("est_low_h must be above zero")
    for k in ("actual_h", "blocked_h", "scope_h", "probe_minutes", "actual_rounds"):
        if rec.get(k) is not None and rec[k] < 0:
            errs.append(f"{k} is negative")
    factor = rec.get("bias_factor")
    if factor is not None:
        if factor <= 0:
            errs.append("bias_factor must be above zero")
        elif factor != 1:
            if rec.get("raw_low_h") is None:
                errs.append("raw_low_h/raw_high_h are required when bias_factor is not 1")
            elif rec.get("est_low_h") is not None:
                # Compare midpoints: the width may change (stats spread, probe narrowing) and
                # rounding is fine, but a missing or inverted factor is not.
                want = gmid(rec["raw_low_h"], rec["raw_high_h"]) * factor
                got = rec.get("est_median_h") or gmid(rec["est_low_h"], rec["est_high_h"])
                off = abs(got - want) / want if want else 0
                if off > 0.25:
                    errs.append(f"estimate midpoint {got:.3g}h should be about raw midpoint x "
                                f"bias_factor = {want:.3g}h")
                elif off > 0.15:
                    warns.append(f"estimate midpoint {got:.3g}h is {off:.0%} from raw midpoint x "
                                 f"bias_factor = {want:.3g}h")
    if rec["outcome"] in ("done", "partial") and rec.get("actual_h") is None and not ported:
        errs.append(f"actual_h is required when outcome is {rec['outcome']}")
    times = {}
    for k in ("logged_at", "est_at", "started_at", "ended_at"):
        if rec.get(k):
            try:
                times[k] = dt.datetime.fromisoformat(rec[k].replace("Z", "+00:00"))
            except ValueError:
                errs.append(f"{k} is not an ISO 8601 time")
    if rec.get("date"):
        try:
            dt.date.fromisoformat(rec["date"])
        except ValueError:
            errs.append("date is not YYYY-MM-DD")
    if "started_at" in times and "ended_at" in times and rec.get("actual_h") is not None:
        try:
            elapsed = (times["ended_at"] - times["started_at"]).total_seconds() / 3600
        except TypeError:
            errs.append("started_at and ended_at must both carry a time zone, or neither")
        else:
            if rec["actual_h"] > elapsed * 1.05 + 0.02:
                warns.append(f"actual_h {rec['actual_h']} exceeds elapsed {elapsed:.2f}h")
    return errs, warns


def validate_revisions(revs, actual_h):
    if revs is None:
        return []
    errs = []
    if len(revs) > MAX_REVISIONS:
        errs.append(f"revisions has {len(revs)} entries; keep at most {MAX_REVISIONS}")
    prev_at, prev_el = None, -1.0
    for i, r in enumerate(revs):
        where = f"revisions[{i}]"
        if not isinstance(r, dict):
            errs.append(f"{where} is not an object")
            continue
        bad = [k for k in r if k not in REVISION_FIELDS]
        bad += [k for k, v in r.items() if k in REVISION_FIELDS and v is not None and
                (not isinstance(v, REVISION_FIELDS[k]) or isinstance(v, bool))]
        miss = [k for k in REVISION_REQUIRED if r.get(k) is None]
        if bad or miss:
            errs.append(f"{where}: bad keys {bad}, missing {miss}")
            continue
        try:
            at = dt.datetime.fromisoformat(r["at"].replace("Z", "+00:00"))
        except ValueError:
            errs.append(f"{where}.at is not an ISO 8601 time")
            continue
        try:
            if prev_at is not None and at < prev_at:
                errs.append(f"{where}.at is earlier than the revision before it")
        except TypeError:
            errs.append(f"{where}.at must match the time-zone style of the others")
        prev_at = at
        if r["elapsed_h"] < prev_el:
            errs.append(f"{where}.elapsed_h is lower than the revision before it")
        prev_el = r["elapsed_h"]
        if actual_h is not None and r["elapsed_h"] > actual_h * 1.05 + 0.02:
            errs.append(f"{where}.elapsed_h exceeds actual_h")
        trio = [r["remaining_low_h"], r.get("remaining_median_h", r["remaining_low_h"]),
                r["remaining_high_h"]]
        if not (0 <= trio[0] <= trio[1] <= trio[2]):
            errs.append(f"{where}: need 0 <= remaining_low_h <= remaining_median_h <= remaining_high_h")
        if any(isinstance(v, float) and not math.isfinite(v) for v in r.values()):
            errs.append(f"{where} has a non-finite number")
        if r.get("trigger") is not None and r["trigger"] not in TRIGGERS:
            errs.append(f"{where}.trigger is not one of {', '.join(TRIGGERS)}")
    return errs


def read_log(path):
    recs, bad = [], []
    if not path.exists():
        return recs, bad
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                bad.append((n, [f"invalid JSON: {e.msg}"]))
                continue
            errs, _ = validate(rec)
            if errs:
                bad.append((n, errs))
            else:
                recs.append(rec)
    return recs, bad


def cmd_log(_args):
    try:
        rec = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        sys.exit(f"invalid JSON on stdin: {e}")
    if isinstance(rec, dict):
        now = dt.datetime.now(dt.timezone.utc)
        rec.setdefault("v", 1)
        rec.setdefault("source", "live")
        rec.setdefault("logged_at", now.strftime("%Y-%m-%dT%H:%M:%SZ"))
        rec.setdefault("date", now.strftime("%Y-%m-%d"))
    errs, warns = validate(rec)
    if errs:
        sys.exit("not logged:\n  " + "\n  ".join(errs))
    data = (json.dumps(rec, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_RECORD_BYTES:
        sys.exit(f"not logged: record is {len(data)} bytes; keep it under {MAX_RECORD_BYTES}")
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        size = os.fstat(fd).st_size
        if size and os.pread(fd, 1, size - 1) != b"\n":
            data = b"\n" + data  # a crashed writer left a partial line; don't join it
        os.write(fd, data)  # one O_APPEND write, so concurrent writers don't interleave
    finally:
        os.close(fd)
    for w in warns:
        print(f"warning: {w}", file=sys.stderr)
    print(f"logged to {path}")


def cmd_check(_args):
    path = log_path()
    recs, bad = read_log(path)
    for n, errs in bad:
        print(f"{path}:{n}: " + "; ".join(errs))
    print(f"{len(recs)} valid, {len(bad)} invalid record(s) in {path}")
    sys.exit(1 if bad else 0)


# ---- calibration -------------------------------------------------------------

def gmid(lo, hi):
    return math.sqrt(lo * hi)


def units(recs):
    """Headline units in file order, one per standalone task or per unrecorded parent.

    Returns (units, exclusion counts)."""
    excluded = {"prose port": 0, "not done": 0, "no numbers": 0, "child of recorded parent": 0,
                "children merged into parent": 0}
    def why_not(r):
        if r.get("source") == "md-port-prose":
            return "prose port"
        if r["outcome"] != "done":
            return "not done"
        if not (r.get("est_low_h") and r.get("est_high_h") and r.get("actual_h")):
            return "no numbers"
        return None

    # Only a parent that itself counts can stand in for its children.
    parents = {r["thread_id"] for r in recs if r.get("thread_id") and why_not(r) is None}
    out, groups = [], {}
    for r in recs:
        reason = why_not(r)
        if reason:
            excluded[reason] += 1
            continue
        # Explicit nulls in raw_* fall back to the stated range.
        lo = r.get("raw_low_h") or r["est_low_h"]
        hi = r.get("raw_high_h") or r["est_high_h"]
        pid = r.get("parent_id")
        if pid and pid in parents:
            excluded["child of recorded parent"] += 1
            continue
        unit = {"kind": r.get("kind") or "other", "raw_lo": lo, "raw_hi": hi,
                "lo": r["est_low_h"], "hi": r["est_high_h"], "act": r["actual_h"],
                "med": r.get("est_median_h")}
        if pid:
            g = groups.get(pid)
            if g is not None:
                for k in ("raw_lo", "raw_hi", "lo", "hi", "act"):
                    g[k] += unit[k]
                g["med"] = None  # a sum of medians is not the campaign's median
                excluded["children merged into parent"] += 1
                continue
            groups[pid] = unit
        out.append(unit)
    return out, excluded


def quantile(xs, q):
    xs = sorted(xs)
    pos = (len(xs) - 1) * q
    i = int(pos)
    j = min(i + 1, len(xs) - 1)
    return xs[i] + (xs[j] - xs[i]) * (pos - i)


def fit(us):
    """Log bias and 50% spread overall and per kind, shrunk toward overall for small kinds."""
    logs = [math.log(u["act"] / gmid(u["raw_lo"], u["raw_hi"])) for u in us]
    overall = st.mean(logs)
    res = [lg - overall for lg in logs]
    model = {"_all": (overall, quantile(res, 0.25), quantile(res, 0.75), len(us))}
    by = {}
    for u, lg in zip(us, logs):
        by.setdefault(u["kind"], []).append(lg)
    for k, ls in by.items():
        w = min(1.0, len(ls) / SHRINK_N)
        b = w * st.mean(ls) + (1 - w) * overall
        q25, q75 = model["_all"][1:3]
        if len(ls) >= SPREAD_N:
            r = [lg - b for lg in ls]
            q25, q75 = quantile(r, 0.25), quantile(r, 0.75)
        model[k] = (b, q25, q75, len(ls))
    return model


def tails(us):
    """p10 and p90 multipliers pooled over all kinds and the given units (log offsets)."""
    logs = [math.log(u["act"] / gmid(u["raw_lo"], u["raw_hi"])) for u in us]
    b = st.mean(logs)
    res = [lg - b for lg in logs]
    return quantile(res, 0.10), quantile(res, 0.90)


def predict(model, u):
    b, q25, q75, _ = model.get(u["kind"], model["_all"])
    m = math.log(gmid(u["raw_lo"], u["raw_hi"])) + b
    return m, m + q25, m + q75


def fmt_h(h):
    return f"{h * 60:.0f} min" if h < 1 else f"{h:.1f} h"


def remaining_calibration(recs):
    """Per-record factor of actual remaining time over the stated remaining estimate."""
    per_rec, hits, n = [], 0, 0
    for r in recs:
        if r["outcome"] != "done" or not r.get("actual_h") or not r.get("revisions"):
            continue
        logs = []
        for v in r["revisions"]:
            left = r["actual_h"] - v["elapsed_h"]
            lo, hi = v["remaining_low_h"], v["remaining_high_h"]
            pred = v.get("remaining_median_h") or (gmid(lo, hi) if lo > 0 else hi / 2)
            if not (0 < left < math.inf and 0 < pred < math.inf):
                continue
            logs.append(math.log(left / pred))
            hits += lo <= left <= hi
            n += 1
        if logs:
            per_rec.append(st.mean(logs))  # each record counts once in the factor
    return per_rec, hits, n


def cmd_stats(args):
    recs, bad = read_log(log_path())
    us, excluded = units(recs)
    if args.backtest:
        return backtest(us, args.window)
    win = us[-args.window:]
    if not win:
        sys.exit("no headline records yet")
    model = fit(win)
    t10, t90 = tails(us) if len(us) >= PERCENTILE_MIN else (float("nan"), float("nan"))
    skipped = ", ".join(f"{v} {k}" for k, v in excluded.items() if v)
    print(f"# {len(recs)} records, {len(bad)} invalid; skipped: {skipped or 'none'}")
    print(f"# factor, p25, p75: last {len(win)} of {len(us)} headline units; "
          f"p10, p90: all {len(us)}, all kinds")
    print("# likely = gut midpoint x factor; each percentile = likely x its multiplier; "
          "`estimate` does the arithmetic")
    print(f"{'kind':18s} {'n':>3s} {'factor':>6s} {'p10':>5s} {'p25':>5s} {'p75':>5s} {'p90':>5s} "
          f"{'median actual':>13s} {'stated hit':>10s}")
    rows = [("all", win)] + sorted(((k, [u for u in win if u["kind"] == k])
                                    for k in KINDS + ("other",)), key=lambda kv: -len(kv[1]))
    for k, sub in rows:
        if not sub:
            continue
        b, q25, q75, n = model["_all" if k == "all" else k]
        hit = sum(u["lo"] <= u["act"] <= u["hi"] for u in sub) / len(sub)
        print(f"{k:18s} {n:3d} {math.exp(b):6.2f} {math.exp(t10):5.2f} {math.exp(q25):5.2f} "
              f"{math.exp(q75):5.2f} {math.exp(t90):5.2f} "
              f"{fmt_h(st.median(u['act'] for u in sub)):>13s} {hit:10.0%}")
    per_rec, hits, n = remaining_calibration(recs)
    if per_rec:
        print(f"# remaining-time revisions: {n} in {len(per_rec)} records; actual remaining = "
              f"stated x {math.exp(st.mean(per_rec)):.2f}; {hits / n:.0%} inside the stated range")


def cmd_estimate(args):
    recs, _ = read_log(log_path())
    us, _ = units(recs)
    win = us[-args.window:]
    if not win:
        sys.exit("no headline records yet; state your gut range uncorrected")
    if not 0 < args.low <= args.high:
        sys.exit("need 0 < --low <= --high (hours)")
    model = fit(win)
    b, q25, q75, n = model.get(args.kind, model["_all"])
    if len(us) < PERCENTILE_MIN:
        likely = gmid(args.low, args.high) * math.exp(b)
        sys.exit(f"only {len(us)} headline units: percentiles would be noise. Likely about "
                 f"{fmt_h(likely)}; state your gut range as the band and log it uncorrected.")
    t10, t90 = tails(us)
    likely = gmid(args.low, args.high) * math.exp(b)
    pts = {"p10": likely * math.exp(t10), "p25": likely * math.exp(q25), "likely": likely,
           "p75": likely * math.exp(q75), "p90": likely * math.exp(t90)}
    src = f"{args.kind}, n={n}" if args.kind in model else f"all kinds, n={model['_all'][3]}"
    print(f"# {src}: factor {math.exp(b):.2f}")
    print(f"Likely {fmt_h(pts['likely'])}; half the time {fmt_h(pts['p25'])} to {fmt_h(pts['p75'])}; "
          f"could be as low as {fmt_h(pts['p10'])} or reach about {fmt_h(pts['p90'])}.")
    r = lambda h: round(h, 3)
    print(json.dumps({"kind": args.kind, "raw_low_h": args.low, "raw_high_h": args.high,
                      "bias_factor": r(math.exp(b)), "est_p10_h": r(pts["p10"]),
                      "est_low_h": r(pts["p25"]), "est_median_h": r(pts["likely"]),
                      "est_high_h": r(pts["p75"]), "est_p90_h": r(pts["p90"])}))


def interval_score(lo, hi, y, alpha=0.5):
    """Gneiting-Raftery score of a central (1-alpha) interval, in log2 units; lower is better."""
    lo, hi, y = (v / math.log(2) for v in (lo, hi, y))
    return (hi - lo) + (2 / alpha) * max(0.0, lo - y) + (2 / alpha) * max(0.0, y - hi)


def backtest(us, window):
    if len(us) <= BACKTEST_START:
        sys.exit(f"need more than {BACKTEST_START} headline units; have {len(us)}")
    rows = {"stated": [], "raw": [], "fitted": []}
    p90_hits = 0
    for i in range(BACKTEST_START, len(us)):
        u = us[i]
        y = math.log(u["act"])
        for name, lo, hi, mid in (("stated", u["lo"], u["hi"], u.get("med")),
                                  ("raw", u["raw_lo"], u["raw_hi"], None)):
            lo, hi = math.log(lo), math.log(hi)
            m = math.log(mid) if mid else (lo + hi) / 2
            rows[name].append((abs(m - y), lo <= y <= hi, hi - lo, interval_score(lo, hi, y)))
        prior = us[max(0, i - window):i]
        m, lo, hi = predict(fit(prior), u)
        p90_hits += y <= m + tails(us[:i])[1]
        rows["fitted"].append((abs(m - y), lo <= y <= hi, hi - lo, interval_score(lo, hi, y)))
    n = len(rows["fitted"])
    print(f"# walk-forward over {n} units: factor and p25/p75 fitted on up to {window} earlier "
          f"units, p90 on all earlier units")
    print(f"{'ranges':8s} {'median error':>12s} {'p25-p75 hit':>11s} {'median width':>12s} "
          f"{'interval score':>14s} {'under p90':>9s}")
    for name, r in rows.items():
        p90 = f"{p90_hits / n:9.0%}" if name == "fitted" else f"{'-':>9s}"
        print(f"{name:8s} {math.exp(st.mean(x[0] for x in r)):11.2f}x {sum(x[1] for x in r) / n:11.0%} "
              f"{math.exp(st.median(x[2] for x in r)):12.1f} {st.mean(x[3] for x in r):14.2f} {p90}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("log", help="validate a JSON record on stdin and append it").set_defaults(fn=cmd_log)
    sub.add_parser("check", help="validate every record").set_defaults(fn=cmd_check)
    e = sub.add_parser("estimate", help="turn a gut range into calibrated percentiles")
    e.add_argument("--kind", required=True, choices=KINDS)
    e.add_argument("--low", type=float, required=True, help="gut low end, hours")
    e.add_argument("--high", type=float, required=True, help="gut high end, hours")
    e.add_argument("--window", type=int, default=HEADLINE_WINDOW)
    e.set_defaults(fn=cmd_estimate)
    p = sub.add_parser("stats", help="bias factor and spread, overall and per kind")
    p.add_argument("--window", type=int, default=HEADLINE_WINDOW,
                   help="most recent headline units to fit (default %(default)s)")
    p.add_argument("--backtest", action="store_true", help="score the procedure walk-forward")
    p.set_defaults(fn=cmd_stats)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
