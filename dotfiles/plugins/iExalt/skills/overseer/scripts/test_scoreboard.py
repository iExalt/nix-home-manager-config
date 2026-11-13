#!/usr/bin/env python3
"""Unit tests for scoreboard.py on fixtures shaped like `acyclic item list/show` and `doctor` output."""

import importlib.util
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = importlib.util.spec_from_file_location("scoreboard", os.path.join(HERE, "scoreboard.py"))
SB = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(SB)

T0 = "2026-11-07T02:00:00Z"


def at(hours, base=T0):
    return SB.parse_time(base) + SB.dt.timedelta(hours=hours)


def item(iid, parent="EPIC", state="open", title=None):
    return {"id": iid, "initiative": "INIT", "parent": parent, "state": state,
            "stage": state, "thread": None, "title": title or iid, "readiness": {"readiness": state}}


def shown(iid, commit="o/r@abc", done_at="2026-11-07T05:00:00Z", state="done"):
    return {"id": iid, "title": iid, "state": state, "done_at": done_at if state == "done" else None,
            "evidence": {"commit": commit, "text": None}, "role": "task"}


DOC_OK = {"unchecked": 0, "unmerged": {}, "unchecked_commits": {}}


def doc_of(unmerged=(), unchecked=(), legacy=False):
    """`doctor()` result for the given (item, reason) pairs; legacy omits unchecked_commits."""
    return {"unchecked": len(unchecked), "unmerged": dict(unmerged),
            "unchecked_commits": None if legacy else dict(unchecked)}


def campaign(**kw):
    c = {"name": "ci", "goal": "faster", "start": T0, "under": "EPIC", "tasks": ["a", "b", "c", "d"],
         "launch_tasks": ["a", "b", "c", "d"], "approved_added": [], "estimate_h": [8.0, 12.0],
         "task_estimates": {"a": [1.0, 2.0]}, "metric": None, "tripwires": dict(SB.DEFAULT_TRIPWIRES),
         "amendments": []}
    c.update(kw)
    return c


ITEMS = [item("EPIC", parent="INIT")] + [item(x) for x in "abcd"]


def run(c=None, state=None, items=None, shows=None, doc=DOC_OK, now=None):
    c = c or campaign()
    return SB.evaluate(c, state or {"tasks": {}, "forecasts": []}, items or ITEMS,
                       shows if shows is not None else [], doc, now or at(3))


def fired(r):
    return {t["name"] for t in r["tripwires"] if t["fired"]}


class Done(unittest.TestCase):
    def test_counts_only_verified_merge(self):
        r = run(shows=[shown("a"), shown("b", commit=None)], items=ITEMS[:1] + [item("a", state="done"), item("b", state="done"), item("c"), item("d")])
        self.assertEqual((r["done"], r["total"]), (1, 4))
        self.assertIn("unverified_done", fired(r))

    def test_unchecked_commit_carries_acyclic_reason(self):
        r = run(shows=[shown("a"), shown("b")], doc=doc_of(unchecked=[("a", "no clone of o/r known")]))
        self.assertEqual(r["done"], 1)
        self.assertEqual(r["tasks"]["a"]["unverified_done"], "unchecked: no clone of o/r known")
        self.assertNotIn("unverified_done", r["tasks"]["b"])
        self.assertIn("unverified_done", fired(r))

    def test_unmerged_detected_by_item(self):
        r = run(shows=[shown("a"), shown("b")], doc=doc_of(unmerged=[("a", "abc is not on main")]))
        self.assertEqual(r["done"], 1)
        self.assertEqual(r["tasks"]["a"]["unverified_done"], "unmerged: abc is not on main")

    def test_older_acyclic_without_unchecked_commits_fails_closed(self):
        r = run(shows=[shown("a"), shown("b")], doc={"unchecked": 1, "unmerged": {}, "unchecked_commits": None})
        self.assertEqual(r["done"], 0)
        self.assertIn("update acyclic", r["tasks"]["a"]["unverified_done"])
        short = mock.Mock(stdout='{"ok": true, "data": {"commits": {"checked": 0, "unchecked": 2, "unmerged": [], '
                                 '"unchecked_commits": [{"item": "a", "reason": "x"}]}}}', stderr="", returncode=0)
        with mock.patch.object(SB.subprocess, "run", return_value=short):
            self.assertIsNone(SB.doctor()["unchecked_commits"])

    def test_no_unverified_when_all_verified(self):
        r = run(shows=[shown("a")])
        self.assertEqual(r["done"], 1)
        self.assertNotIn("unverified_done", fired(r))

    def test_since_digest_and_age(self):
        st = {"tasks": {}, "forecasts": [], "last_digest": {"at": "2026-11-07T04:00:00Z", "done": 0}}
        r = run(state=st, shows=[shown("a", done_at="2026-11-07T03:00:00Z")], now=at(5))
        self.assertEqual(r["done_since_digest"], 1)
        self.assertEqual(r["last_done_age_s"], 4 * 3600)
        self.assertIn("1/4 done (+1 since 04:00) · last done 4h ago", SB.line1(r))

    def test_none_done_yet(self):
        self.assertIn("none done yet", SB.line1(run()))


class Elapsed(unittest.TestCase):
    def test_hours_round_near_integers(self):
        for hours, expected in ((0.96, "1"), (1.04, "1"), (0.5, "0.5"),
                                (1.5, "1.5"), (0, "0"), (2, "2")):
            with self.subTest(hours=hours):
                self.assertEqual(SB.fmt_hours(hours), expected)

    def test_high_end_flags(self):
        r = run(now=at(21))
        self.assertTrue(r["over_high"])
        self.assertIn("21h active of 8–12h ⚠", SB.line1(r))
        self.assertIn("campaign_over_high", fired(r))

    def test_within_range_no_flag(self):
        r = run(now=at(10))
        self.assertNotIn("⚠", SB.line1(r))
        self.assertNotIn("campaign_over_high", fired(r))

    def test_finished_campaign_does_not_fire(self):
        r = run(now=at(21), shows=[shown(x) for x in "abcd"])
        self.assertEqual(r["done"], 4)
        self.assertNotIn("campaign_over_high", fired(r))
        self.assertNotIn("⚠", SB.line1(r))


class Scope(unittest.TestCase):
    def more(self, n):
        return ITEMS + [item("n%d" % i) for i in range(n)]

    def test_scope_added_counts_and_line(self):
        r = run(items=self.more(2))
        self.assertEqual(r["scope_added"], 2)
        self.assertIn("scope +2 since launch", SB.line1(r))
        self.assertTrue(set(r["added_tasks"]) == {"n0", "n1"})

    def test_growth_over_25_percent_fires(self):
        self.assertIn("scope_growth", fired(run(items=self.more(2))))

    def test_growth_at_25_percent_does_not_fire(self):
        self.assertNotIn("scope_growth", fired(run(items=self.more(1))))

    def test_approved_growth_does_not_fire_but_counts_in_total(self):
        c = campaign(approved_added=["n0", "n1"])
        r = run(c=c, items=self.more(2), shows=[])
        self.assertNotIn("scope_growth", fired(r))
        self.assertEqual(r["total"], 6)
        self.assertEqual(r["scope_added"], 2)

    def test_canceled_added_task_ignored(self):
        its = ITEMS + [item("x", state="canceled")]
        self.assertEqual(run(items=its)["scope_added"], 0)

    def test_nested_epic_leaves(self):
        its = ITEMS + [item("sub"), item("leaf", parent="sub")]
        # "sub" has a child so it is a parent, not a task; "leaf" is the new task
        self.assertEqual(run(items=its)["added_tasks"], ["leaf"])

    def test_added_unapproved_lists_scope_but_not_decisions(self):
        # n0 is unapproved scope; n1 is approved; D is an open item the user owes, recorded as a decision
        r = run(c=campaign(approved_added=["n1"]), items=self.more(2) + [item("D")],
                state={"tasks": {}, "forecasts": [], "decisions": ["D"]}, shows=[])
        self.assertEqual(r["added_unapproved"], ["n0"])
        self.assertEqual(r["scope_added_unapproved"], 1)
        self.assertEqual(r["decisions"], ["D"])


class Clocks(unittest.TestCase):
    def state(self, segs):
        return {"tasks": {"a": {"segments": segs}}, "forecasts": []}

    def test_pause_excludes_wait(self):
        st = self.state([[iso(0), iso(1)], [iso(3), None]])
        r = run(state=st, now=at(4))
        self.assertAlmostEqual(r["tasks"]["a"]["running_h"], 2.0)
        self.assertNotIn("task_over_high", fired(r))

    def test_over_high_fires_when_running(self):
        r = run(state=self.state([[iso(0), None]]), now=at(2.5))
        self.assertIn("task_over_high", fired(r))

    def test_wait_time_would_have_fired_if_counted(self):
        r = run(state=self.state([[iso(0), iso(1)]]), now=at(9))
        self.assertAlmostEqual(r["tasks"]["a"]["running_h"], 1.0)
        self.assertNotIn("task_over_high", fired(r))

    def test_done_task_does_not_fire(self):
        r = run(state=self.state([[iso(0), None]]), now=at(9), shows=[shown("a")])
        self.assertNotIn("task_over_high", fired(r))

    def test_task_without_estimate_never_fires(self):
        st = {"tasks": {"b": {"segments": [[iso(0), None]]}}, "forecasts": []}
        self.assertNotIn("task_over_high", fired(run(state=st, now=at(50))))


def iso(h):
    return SB.iso(at(h))


class Forecasts(unittest.TestCase):
    def fc(self, *specs):
        return {"tasks": {}, "forecasts": [{"task": t, "at": iso(h), "made_at": T0} for t, h in specs]}

    def test_two_misses_fire(self):
        r = run(state=self.fc(("a", 1), ("a", 2)), now=at(3))
        self.assertEqual(r["missed_forecasts"], 2)
        self.assertIn("forecast_missed", fired(r))

    def test_repeated_identical_forecast_counts_once(self):
        r = run(state=self.fc(("a", 1), ("a", 1), ("a", 1)), now=at(3))
        self.assertEqual(r["missed_forecasts"], 1)
        self.assertNotIn("forecast_missed", fired(r))

    def test_one_miss_does_not_fire(self):
        self.assertNotIn("forecast_missed", fired(run(state=self.fc(("a", 1), ("a", 4)), now=at(3))))

    def test_met_forecast_is_not_missed(self):
        r = run(state=self.fc(("a", 4), ("b", 4)), shows=[shown("a", done_at=iso(3)), shown("b", done_at=iso(3.5))], now=at(5))
        self.assertEqual(r["missed_forecasts"], 0)

    def test_late_done_is_missed(self):
        r = run(state=self.fc(("a", 1)), shows=[shown("a", done_at=iso(2))], now=at(5))
        self.assertEqual(r["missed_forecasts"], 1)

    def test_next_done_is_earliest_pending(self):
        r = run(state=self.fc(("a", 6), ("b", 5)), now=at(3))
        self.assertEqual(r["next_done"]["task"], "b")

    def test_parse_hhmm_rolls_forward(self):
        now = at(3)  # 05:00
        self.assertEqual(SB.parse_forecast("16:00", now), at(14))
        self.assertEqual(SB.parse_forecast("04:00", now), at(26))


class Dropped(unittest.TestCase):
    def test_dropped_leaves_total_and_scope(self):
        c = campaign(dropped=["d", "n0"])
        its = ITEMS + [item("n0")]
        r = run(c=c, items=its, shows=[shown(x) for x in "abc"], now=at(30))
        self.assertEqual((r["done"], r["total"], r["scope_added"]), (3, 3, 0))
        self.assertNotIn("campaign_over_high", fired(r))

    def test_done_but_unverified_task_does_not_also_trip_clock(self):
        st = {"tasks": {"a": {"segments": [[iso(0), None]]}}, "forecasts": []}
        r = run(state=st, now=at(9), shows=[shown("a", commit=None)])
        self.assertNotIn("task_over_high", fired(r))
        self.assertIn("unverified_done", fired(r))

    def test_dropped_task_forecast_is_moot(self):
        c = campaign(dropped=["c"])
        st = {"tasks": {}, "forecasts": [{"task": "c", "at": iso(1), "made_at": T0}]}
        r = run(c=c, state=st, now=at(5))
        self.assertEqual(r["missed_forecasts"], 0)

    def test_paused_hours_reported(self):
        st = {"tasks": {"a": {"segments": [[iso(0), iso(1)], [iso(3), None]]}}, "forecasts": []}
        self.assertAlmostEqual(run(state=st, now=at(4))["tasks"]["a"]["paused_h"], 2.0)


class Tripwires(unittest.TestCase):
    def test_none_fire_on_healthy_run(self):
        r = run(shows=[shown("a")], now=at(3))
        self.assertEqual(fired(r), set())

    def test_disabled_tripwire_does_not_fire(self):
        c = campaign()
        c["tripwires"]["campaign_over_high"] = False
        self.assertNotIn("campaign_over_high", fired(run(c=c, now=at(30))))

    def test_threshold_override(self):
        c = campaign()
        c["tripwires"]["scope_growth_pct"] = 60
        its = ITEMS + [item("n0"), item("n1")]
        self.assertNotIn("scope_growth", fired(run(c=c, items=its)))


class Cli(unittest.TestCase):
    """freeze, amendments and clocks through main(), with Acyclic stubbed."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        p = [mock.patch.object(SB, "item_list", lambda: ITEMS),
             mock.patch.object(SB, "item_show", lambda ids: [shown(i) for i in ids if i == "a"]),
             mock.patch.object(SB, "doctor", lambda: DOC_OK)]
        for x in p:
            x.start()
            self.addCleanup(x.stop)

    def go(self, *args, now="2026-11-07T02:00:00Z"):
        return SB.main(["--campaign", self.d, "--now", now] + list(args))

    def test_freeze_refuses_rewrite_and_amend_records_approval(self):
        self.assertEqual(self.go("freeze", "--name", "ci", "--goal", "g", "--under", "EPIC",
                                 "--estimate", "8-12", "--task-estimate", "a=1-2"), 0)
        self.assertEqual(self.go("freeze", "--name", "ci", "--goal", "g2", "--under", "EPIC", "--estimate", "1-2"), 1)
        self.assertEqual(self.go("freeze", "--amend", "--estimate", "10-14"), 1)  # no approval
        self.assertEqual(self.go("freeze", "--amend", "--estimate", "10-14", "--approved-by",
                                 "user: ok, 2026-11-07", "--reason", "slip"), 0)
        c = SB.read_json(os.path.join(self.d, "campaign.json"), "c")
        self.assertEqual(c["estimate_h"], [10.0, 14.0])
        self.assertEqual(c["amendments"][0]["from"], {"estimate_h": [8.0, 12.0]})
        self.assertEqual(c["goal"], "g")

    def test_clock_lifecycle_and_digest(self):
        self.go("freeze", "--name", "ci", "--goal", "g", "--under", "EPIC", "--estimate", "8-12")
        self.assertEqual(self.go("task-start", "a"), 0)
        self.assertEqual(self.go("task-start", "a"), 1)
        self.assertEqual(self.go("task-pause", "a", now="2026-11-07T03:00:00Z"), 1)  # no --on
        self.assertEqual(self.go("task-pause", "a", "--on", "d", now="2026-11-07T03:00:00Z"), 0)
        self.assertEqual(self.go("task-pause", "a", "--on", "d", now="2026-11-07T03:10:00Z"), 1)
        self.assertEqual(self.go("task-resume", "a", now="2026-11-07T04:00:00Z"), 0)
        self.assertEqual(self.go("forecast", "a", "06:00", now="2026-11-07T04:00:00Z"), 0)
        self.assertEqual(self.go("show", "--digest", now="2026-11-07T05:00:00Z"), 0)
        st = SB.read_json(os.path.join(self.d, "scoreboard-state.json"), "s")
        self.assertEqual(st["last_digest"], {"at": "2026-11-07T05:00:00Z", "done": 1})

    def test_exclude_keeps_gates_out_of_tasks_and_scope(self):
        self.go("freeze", "--name", "ci", "--goal", "g", "--under", "EPIC", "--estimate", "8-12", "--exclude", "d")
        c = SB.read_json(os.path.join(self.d, "campaign.json"), "c")
        self.assertEqual(c["tasks"], ["a", "b", "c"])
        r = run(c=c)
        self.assertEqual((r["total"], r["scope_added"]), (3, 0))

    def test_bad_tripwire_values_rejected(self):
        for bad in ("forecast_misses=two", "forecast_misses=-1", "campaign_over_high=yes"):
            self.assertEqual(self.go("freeze", "--name", "ci", "--goal", "g", "--under", "EPIC",
                                     "--estimate", "8-12", "--tripwire", bad), 1)
        self.assertEqual(self.go("freeze", "--name", "ci", "--goal", "g", "--under", "EPIC", "--estimate", "8-12",
                                 "--tripwire", "scope_growth_pct=off", "campaign_over_high=off"), 0)

    def test_amend_drop_task(self):
        self.go("freeze", "--name", "ci", "--goal", "g", "--under", "EPIC", "--estimate", "8-12")
        self.assertEqual(self.go("freeze", "--amend", "--drop-task", "d", "--approved-by", "user", "--reason", "trim"), 0)
        self.assertEqual(SB.read_json(os.path.join(self.d, "campaign.json"), "c")["dropped"], ["d"])

    def test_missing_campaign_fails_loudly(self):
        self.assertEqual(self.go("show"), 1)


# ------------------------------------------------------ waiting on the user

def rd(it, readiness, waiting=None):
    it = dict(it)
    it["readiness"] = {"readiness": readiness}
    if waiting:
        it["readiness"]["waiting"] = {w: {"why": "open"} for w in waiting}
    return it


def decision(state="parked", iid="D"):
    return item(iid, parent="INIT", state=state)


def paused_state(tid, on="D", start=0, end=1):
    return {"segments": [[iso(start), iso(end)]], "pauses": [{"at": iso(end), "on": on}]}


def running_state(start=0):
    return {"segments": [[iso(start), None]]}


def wait_items(waits=("a", "b", "c", "d"), extra=()):
    """a..d wait for decision D (or sit ready when not in `waits`)."""
    out = [ITEMS[0], decision()]
    for x in "abcd":
        out.append(rd(item(x), "waiting", ["D"]) if x in waits else rd(item(x), "ready"))
    return out + list(extra)


def wait_state(tasks, **kw):
    st = {"tasks": tasks, "forecasts": []}
    st.update(kw)
    return st


def is_waiting(tasks, items):
    return SB.wait_status(campaign(), wait_state(tasks), items)["waiting"]


class WaitStatus(unittest.TestCase):
    ALL = {x: paused_state(x) for x in "abcd"}

    def test_every_task_paused_on_open_decision_waits(self):
        self.assertTrue(is_waiting(self.ALL, wait_items()))

    def test_one_never_started_ready_task_makes_it_active(self):
        tasks = {x: paused_state(x) for x in "abc"}
        self.assertFalse(is_waiting(tasks, wait_items(waits="abc")))

    def test_partial_pause_is_active(self):
        tasks = dict(self.ALL, b=running_state())
        self.assertFalse(is_waiting(tasks, wait_items()))

    def test_dependency_blocked_task_behind_paused_blocker_waits(self):
        its = wait_items(waits="abc", extra=[])
        its[5] = rd(item("d"), "waiting", ["a"])
        self.assertTrue(is_waiting({x: paused_state(x) for x in "abc"}, its))

    def test_dependency_blocked_task_behind_running_blocker_is_active(self):
        its = wait_items(waits="bc")
        its[2] = rd(item("a"), "claimed")
        its[5] = rd(item("d"), "waiting", ["a"])
        tasks = {"a": running_state(), "b": paused_state("b"), "c": paused_state("c")}
        self.assertFalse(is_waiting(tasks, its))

    def test_pause_on_item_the_task_does_not_wait_for_is_active(self):
        its = wait_items() + [decision(iid="E")]
        tasks = dict(self.ALL, a=paused_state("a", on="E"))
        self.assertFalse(is_waiting(tasks, its))

    def test_pause_on_closed_decision_is_active(self):
        for st in ("done", "canceled"):
            its = wait_items()
            its[1] = decision(state=st)
            self.assertFalse(is_waiting(self.ALL, its), st)

    def test_pause_without_recorded_decision_is_active(self):
        tasks = dict(self.ALL, a={"segments": [[iso(0), iso(1)]]})
        self.assertFalse(is_waiting(tasks, wait_items()))

    def test_transitive_wait_is_enough(self):
        its = wait_items()
        its[1] = rd(decision(), "waiting", ["E"])
        its.append(decision(iid="E"))
        its[2] = rd(item("a"), "waiting", ["D"])
        self.assertTrue(is_waiting(self.ALL, its[:2] + its[2:6] + [its[6]]))

    def test_unlaunched_task_blocked_directly_on_cited_decision_waits(self):
        its = wait_items(waits="abcd")
        self.assertTrue(is_waiting({x: paused_state(x) for x in "abc"}, its))

    def test_unlaunched_task_on_recorded_decision_waits_without_any_pause(self):
        its = wait_items(extra=[item("E", parent="INIT")])
        its[2:6] = [rd(item(x), "waiting", ["E"]) for x in "abcd"]
        ws = SB.wait_status(campaign(), wait_state({}, decisions=["E"]), its)
        self.assertTrue(ws["waiting"])
        self.assertEqual((ws["decisions"], ws["uncited"]), (["E"], []))

    def test_closed_recorded_decision_is_not_owed(self):
        its = wait_items(waits="abc", extra=[item("E", parent="INIT", state="done")])
        its[5] = rd(item("d"), "waiting", ["E"])
        tasks = {x: paused_state(x) for x in "abc"}
        self.assertFalse(SB.wait_status(campaign(), wait_state(tasks, decisions=["E"]), its)["waiting"])

    def test_uncited_parked_item_waits_and_is_flagged(self):
        its = wait_items(waits="abc", extra=[decision(iid="E")])
        its[5] = rd(item("d"), "waiting", ["E"])
        ws = SB.wait_status(campaign(), wait_state({x: paused_state(x) for x in "abc"}), its)
        self.assertTrue(ws["waiting"])
        self.assertEqual(ws["uncited"], ["E"])

    def test_unlaunched_task_on_open_unrecorded_item_is_active(self):
        its = wait_items(waits="abc", extra=[item("E", parent="INIT")])
        its[5] = rd(item("d"), "waiting", ["E"])
        self.assertFalse(is_waiting({x: paused_state(x) for x in "abc"}, its))

    def test_all_done_is_not_waiting(self):
        its = [ITEMS[0], decision()] + [rd(item(x, state="done"), "done") for x in "abcd"]
        self.assertFalse(is_waiting({}, its))


class Waiting(unittest.TestCase):
    """The clock through main(): wait_segments, active_h and the new tripwires."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.items = wait_items()
        self.shows = {}
        p = [mock.patch.object(SB, "item_list", lambda: self.items),
             mock.patch.object(SB, "item_show", lambda ids: [self.shows.get(i, shown(i, state="open")) for i in ids]),
             mock.patch.object(SB, "doctor", lambda: DOC_OK)]
        for x in p:
            x.start()
            self.addCleanup(x.stop)
        self.go(0, "freeze", "--name", "ci", "--goal", "g", "--under", "EPIC", "--estimate", "8-12")

    def go(self, h, *args):
        return SB.main(["--campaign", self.d, "--now", iso(h)] + list(args))

    def state(self):
        return SB.read_json(os.path.join(self.d, "scoreboard-state.json"), "s")

    def show(self, h):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            SB.main(["--campaign", self.d, "--now", iso(h), "show", "--json"])
        return SB.json.loads(out.getvalue())

    def park_all(self, h=1):
        for x in "abcd":
            self.assertEqual(self.go(0, "task-start", x), 0)
        for x in "abcd":
            self.assertEqual(self.go(h, "task-pause", x, "--on", "D"), 0)

    def test_pause_requires_on(self):
        self.go(0, "task-start", "a")
        self.assertEqual(self.go(1, "task-pause", "a"), 1)
        self.assertNotIn("pauses", self.state()["tasks"]["a"])

    def test_segments_accumulate_only_between_writes_that_both_saw_waiting(self):
        self.park_all(1)
        self.assertNotIn("wait_segments", self.state())  # the first waiting write only opens a mark
        self.go(3, "show", "--digest")
        self.assertEqual(self.state()["wait_segments"], [[iso(1), iso(3)]])
        self.go(4, "forecast", "a", "09:00")
        self.assertEqual(self.state()["wait_segments"], [[iso(1), iso(4)]])  # contiguous: extended
        self.go(5, "task-resume", "a")  # the pre-change write still saw waiting: bridged to 5
        self.assertEqual(self.state()["wait_segments"], [[iso(1), iso(5)]])
        self.go(7, "show", "--digest")
        self.assertEqual(self.state()["wait_segments"], [[iso(1), iso(5)]])  # 5..7 counts as active
        r = self.show(8)
        self.assertAlmostEqual(r["waiting_h"], 4.0)
        self.assertAlmostEqual(r["active_h"], 4.0)

    def test_unwritten_tail_counts_while_still_waiting(self):
        self.park_all(1)
        r = self.show(6)
        self.assertAlmostEqual(r["waiting_h"], 5.0)
        self.assertAlmostEqual(r["active_h"], 1.0)
        self.assertIn("1h active of 8–12h · 5h waiting on you", SB.line1(r))

    def test_no_waiting_part_when_none(self):
        self.go(0, "task-start", "a")
        self.assertNotIn("waiting on you", SB.line1(self.show(3)))
        self.assertEqual(self.show(3)["waiting_h"], 0)

    def test_pause_after_decision_closed_counts_as_active(self):
        self.park_all(1)
        self.go(2, "show", "--digest")  # waiting [1,2]
        for x in "abcd":
            self.items[2 + "abcd".index(x)] = rd(item(x), "ready")
        self.items[1] = decision(state="done")
        self.shows["D"] = dict(shown("D"), done_at=iso(2.5))
        self.assertAlmostEqual(self.show(2.8)["waiting_h"], 1.5)  # unwritten: still ends at D's close
        self.go(3, "forecast", "a", "09:00")  # D closed at 2.5: the wait ends there, not at the write
        self.assertEqual(self.state()["wait_segments"], [[iso(1), iso(2.5)]])
        self.go(6, "show", "--digest")
        r = self.show(7)
        self.assertAlmostEqual(r["waiting_h"], 1.5)  # nothing after D closed
        self.assertAlmostEqual(r["active_h"], 5.5)
        self.assertFalse(r["waiting_now"])
        self.assertGreater(r["waiting_unexplained_h"], 4.0)  # paused, but no decision behind it

    def test_decision_command_counts_waits_and_leaves_scope(self):
        self.items = wait_items(waits="abc") + [item("E", parent="EPIC", state="parked")]
        self.items[5] = rd(item("d"), "waiting", ["E"])
        self.park_all_but_d()
        self.assertEqual(self.go(1, "decision", "d"), 1)  # a campaign task is never a decision
        r = self.show(1)
        self.assertEqual((r["scope_added"], r["waiting_on_uncited"]), (1, ["E"]))  # growth, flagged
        self.assertEqual(self.go(1, "decision", "E"), 0)
        self.assertEqual(self.state()["decisions"], ["E"])
        r = self.show(3)
        self.assertEqual((r["scope_added"], r["waiting_on_uncited"], r["waiting_on"]), (0, [], ["D", "E"]))
        self.assertAlmostEqual(r["waiting_h"], 2.0)

    def test_closed_decision_can_be_recorded_to_leave_scope(self):
        self.items.append(item("E", parent="EPIC", state="done"))
        self.assertEqual(self.show(1)["scope_added"], 1)
        self.assertEqual(self.go(1, "decision", "E"), 0)
        self.assertEqual(self.show(1)["scope_added"], 0)

    def test_wait_ends_at_the_earliest_relied_on_decision_close(self):
        self.items.append(decision(iid="E"))
        self.items[5] = rd(item("d"), "waiting", ["E"])
        self.park_all_but_d()  # waits on D (pauses) and E (d, uncited); mark at 1
        self.assertEqual(self.state()["wait_mark"]["on"], ["D", "E"])
        self.items[1], self.items[-1] = decision(state="done"), decision(iid="E", state="done")
        self.items[2:6] = [rd(item(x), "ready") for x in "abcd"]
        self.shows["D"] = dict(shown("D"), done_at=iso(1.5))
        self.shows["E"] = dict(shown("E"), done_at=iso(5))
        self.go(6, "mark")
        self.assertEqual(self.state()["wait_segments"], [[iso(1), iso(1.5)]])

    def test_closing_an_unrelated_recorded_decision_does_not_end_the_wait(self):
        self.items.append(item("X", parent="INIT"))
        self.go(0, "decision", "X")
        self.park_all(1)
        self.assertEqual(self.state()["wait_mark"]["on"], ["D"])
        self.items[2:6] = [rd(item(x), "ready") for x in "abcd"]  # active for another reason
        self.items[-1] = item("X", parent="INIT", state="done")
        self.shows["X"] = dict(shown("X"), done_at=iso(4))
        self.go(5, "mark")
        self.assertNotIn("wait_segments", self.state())

    def park_all_but_d(self):
        for x in "abc":
            self.go(0, "task-start", x)
        for x in "abc":
            self.go(1, "task-pause", x, "--on", "D")

    def test_invalid_pause_is_active_and_warned(self):
        self.go(0, "task-start", "a")
        self.items.append(decision(iid="E"))
        self.assertEqual(self.go(1, "task-pause", "a", "--on", "E"), 0)
        self.go(2, "show", "--digest")
        self.assertEqual(self.show(5)["waiting_h"], 0)

    def test_high_end_uses_active_not_elapsed(self):
        self.park_all(1)
        r = self.show(21)  # 21h elapsed, 20h waiting
        self.assertFalse(r["over_high"])
        self.assertNotIn("campaign_over_high", fired(r))
        self.assertAlmostEqual(r["elapsed_h"], 21.0)
        self.items = wait_items(waits="")
        self.assertIn("campaign_over_high", fired(self.show(30)))

    def test_waiting_on_user_fires_with_decision_notes_and_not_before(self):
        self.shows["D"] = dict(shown("D", state="open"), title="Pick the cache backend", notes="Redis or SQLite?")
        self.park_all(1)
        self.go(2, "show", "--digest")
        self.assertNotIn("waiting_on_user", fired(self.show(7)))  # 6h of waiting is not more than 6h
        r = self.show(8)
        self.assertIn("waiting_on_user", fired(r))
        ev = [t for t in r["tripwires"] if t["name"] == "waiting_on_user"][0]["evidence"]
        self.assertIn("Pick the cache backend: Redis or SQLite?", ev)

    def test_waiting_on_user_override_and_off(self):
        self.park_all(1)
        self.go(2, "show", "--digest")
        c = SB.read_json(os.path.join(self.d, "campaign.json"), "c")
        c["tripwires"]["waiting_on_user"] = 2
        SB.write_json(os.path.join(self.d, "campaign.json"), c)
        self.assertIn("waiting_on_user", fired(self.show(5)))
        c["tripwires"]["waiting_on_user"] = None
        SB.write_json(os.path.join(self.d, "campaign.json"), c)
        self.assertNotIn("waiting_on_user", fired(self.show(30)))

    def test_idle_ready_fires_after_an_hour_not_before(self):
        self.items = wait_items(waits="abc")  # d is ready and never launched
        for x in "abc":
            self.go(0, "task-start", x)
        self.assertEqual(self.state()["ready_since"], {"d": iso(0)})
        self.assertNotIn("idle_ready", fired(self.show(1)))  # exactly 1h
        r = self.show(1.5)
        self.assertIn("idle_ready", fired(r))
        self.assertIn("d ready 1.5h, not launched", [t for t in r["tripwires"] if t["name"] == "idle_ready"][0]["evidence"])

    def test_claimed_unstarted_task_is_not_idle(self):
        self.items = wait_items(waits="abc")
        self.items[5] = rd(item("d"), "claimed")
        self.go(0, "task-start", "a")
        self.assertEqual(self.state()["ready_since"], {})

    def test_mark_bridges_a_quiet_wait_before_resume(self):
        self.park_all(1)
        self.assertEqual(self.go(5, "mark"), 0)
        self.assertEqual(self.state()["wait_segments"], [[iso(1), iso(5)]])
        self.items[1] = decision(state="done")
        for x in "abcd":
            self.items[2 + "abcd".index(x)] = rd(item(x), "ready")
        self.go(9, "task-resume", "a")  # pre-change write sees D closed: 5..9 is active
        r = self.show(10)
        self.assertAlmostEqual(r["waiting_h"], 4.0)

    def test_pre_change_write_bridges_wait_while_decision_still_open(self):
        self.park_all(1)
        self.go(9, "task-resume", "a")  # D still open: the wait up to the resume counts
        self.assertEqual(self.state()["wait_segments"], [[iso(1), iso(9)]])

    def test_idle_ready_clears_on_launch(self):
        self.items = wait_items(waits="abc")
        self.go(0, "task-start", "a")
        self.go(2, "task-start", "d")
        self.assertEqual(self.state()["ready_since"], {})
        self.assertNotIn("idle_ready", fired(self.show(9)))

    def test_idle_ready_unrecorded_task_does_not_fire(self):
        self.items = wait_items(waits="abc")  # no write has seen d ready yet
        self.assertNotIn("idle_ready", fired(self.show(9)))

    def test_new_tripwires_are_frozen_defaults_and_overridable(self):
        c = SB.read_json(os.path.join(self.d, "campaign.json"), "c")
        self.assertEqual((c["tripwires"]["idle_ready"], c["tripwires"]["waiting_on_user"]), (1, 6))
        d2 = tempfile.mkdtemp()
        self.assertEqual(SB.main(["--campaign", d2, "--now", iso(0), "freeze", "--name", "n", "--goal", "g",
                                  "--under", "EPIC", "--estimate", "8-12",
                                  "--tripwire", "idle_ready=2", "waiting_on_user=off"]), 0)
        c = SB.read_json(os.path.join(d2, "campaign.json"), "c")
        self.assertEqual((c["tripwires"]["idle_ready"], c["tripwires"]["waiting_on_user"]), (2, None))


class BlockedOnTasks(unittest.TestCase):
    """A started task waiting on unfinished campaign tasks stops its clock; a wait on anything else doesn't."""

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.items = [ITEMS[0], rd(item("a"), "waiting", ["c"]), rd(item("b"), "ready"),
                      rd(item("c"), "ready"), rd(item("d"), "ready")]
        self.shows = {}
        p = [mock.patch.object(SB, "item_list", lambda: self.items),
             mock.patch.object(SB, "item_show", lambda ids: [self.shows.get(i, shown(i, state="open")) for i in ids]),
             mock.patch.object(SB, "doctor", lambda: DOC_OK)]
        for x in p:
            x.start()
            self.addCleanup(x.stop)
        self.assertEqual(self.go(0, "freeze", "--name", "ci", "--goal", "g", "--under", "EPIC", "--estimate", "8-12"), 0)

    def go(self, h, *args):
        return SB.main(["--campaign", self.d, "--now", iso(h)] + list(args))

    def state(self):
        return SB.read_json(os.path.join(self.d, "scoreboard-state.json"), "s")

    def show(self, h):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(SB.main(["--campaign", self.d, "--now", iso(h), "show", "--json"]), 0)
        return SB.json.loads(out.getvalue())

    def test_started_task_waiting_on_open_campaign_task_stops_and_resumes_at_its_done_at(self):
        self.assertEqual(self.go(0, "task-start", "a"), 0)
        self.assertEqual(self.go(2, "mark"), 0)
        r = self.show(2)  # c is still open: the blocked interval so far counts, unwritten
        self.assertEqual(r["tasks"]["a"]["running_h"], 0.0)
        self.assertEqual(r["tasks"]["a"]["blocked_h"], 2.0)
        self.assertEqual(r["tasks"]["a"]["blocked_on"], ["c"])
        # c closes at 3h and a is no longer waiting; nothing is written until 6h
        self.items[1] = rd(item("a"), "ready")
        self.items[3] = rd(item("c", state="done"), "done")
        self.shows["c"] = shown("c", done_at=iso(3))
        r = self.show(6)
        self.assertEqual(r["tasks"]["a"]["running_h"], 3.0)  # resumes at c's done_at, 3h, not at the write
        self.assertEqual(r["tasks"]["a"]["blocked_h"], 3.0)
        self.assertEqual(r["tasks"]["a"]["blocked_on"], [])
        self.assertEqual(self.go(6, "mark"), 0)
        self.assertEqual(self.state()["tasks"]["a"]["blocks"], [[iso(0), iso(3)]])

    def test_started_task_waiting_on_outside_item_that_is_no_decision_still_accrues(self):
        self.items.append(item("X", parent="INIT"))  # open, outside the campaign, not a decision
        self.items[1] = rd(item("a"), "waiting", ["X"])
        self.assertEqual(self.go(0, "task-start", "a"), 0)
        self.assertEqual(self.go(2, "mark"), 0)
        r = self.show(4)
        self.assertEqual(r["tasks"]["a"]["running_h"], 4.0)
        self.assertEqual(r["tasks"]["a"]["blocked_h"], 0.0)
        self.assertEqual(r["tasks"]["a"]["blocked_on"], [])

    def test_campaign_active_time_is_unchanged_by_a_task_waiting_on_campaign_tasks(self):
        self.assertEqual(self.go(0, "task-start", "a"), 0)
        self.assertEqual(self.go(2, "mark"), 0)
        r = self.show(8)  # c stays open: a is blocked 8h, past the 6h user tripwire, but the campaign is active
        self.assertEqual((r["active_h"], r["elapsed_h"], r["waiting_h"], r["waiting_now"]), (8.0, 8.0, 0.0, False))
        self.assertNotIn("waiting_on_user", {t["name"] for t in r["tripwires"] if t["fired"]})
        self.assertEqual(r["tasks"]["a"]["blocked_h"], 8.0)

    def test_claimed_task_with_waits_for_links_is_not_blocked(self):
        # Acyclic shows a claimed task's waits only in links.waits_for, so only `waiting` readiness counts;
        # the fixture also carries readiness.waiting, so the readiness guard is what keeps it unblocked
        claimed = rd(item("a"), "claimed", ["c"])
        claimed["links"] = {"waits_for": ["c"]}
        self.items[1] = claimed
        self.assertEqual(self.go(0, "task-start", "a"), 0)
        self.assertEqual(self.go(2, "mark"), 0)
        r = self.show(4)
        self.assertEqual(r["tasks"]["a"]["running_h"], 4.0)
        self.assertEqual(r["tasks"]["a"]["blocked_on"], [])
        self.assertEqual(r["tasks"]["a"]["blocked_h"], 0.0)

    def test_blocked_through_a_waiting_campaign_task(self):
        self.items[3] = rd(item("c"), "waiting", ["d"])  # a waits on c, and c waits on d
        self.assertEqual(self.go(0, "task-start", "a"), 0)
        self.assertEqual(self.show(1)["tasks"]["a"]["blocked_on"], ["c", "d"])

    def test_chain_blocked_interval_ends_at_the_last_blocker_done_at(self):
        # a waits on c, and c waits on d: a stays blocked until c, its last blocker, is done
        self.items[3] = rd(item("c"), "waiting", ["d"])
        self.assertEqual(self.go(0, "task-start", "a"), 0)
        self.assertEqual(self.go(1, "mark"), 0)
        self.assertEqual(self.state()["tasks"]["a"]["block_mark"]["on"], ["c", "d"])
        # d closes at 3h and c becomes ready; a still waits on c. c closes at 5h; nothing is written until 6h
        self.items[4] = rd(item("d", state="done"), "done")
        self.items[3] = rd(item("c"), "ready")
        self.shows["d"] = shown("d", done_at=iso(3))
        self.items[3] = rd(item("c", state="done"), "done")
        self.shows["c"] = shown("c", done_at=iso(5))
        self.items[1] = rd(item("a"), "ready")
        r = self.show(6)
        self.assertEqual((r["tasks"]["a"]["running_h"], r["tasks"]["a"]["blocked_h"]), (1.0, 5.0))
        self.assertEqual(self.go(6, "mark"), 0)
        self.assertEqual(self.state()["tasks"]["a"]["blocks"], [[iso(0), iso(5)]])

    def test_blocks_stop_at_pause_restart_at_resume_and_are_never_subtracted_twice(self):
        self.items[1] = rd(item("a"), "waiting", ["c", "D"])  # blocked by campaign task c; paused on decision D
        self.items.append(item("D", parent="INIT", state="parked"))
        self.assertEqual(self.go(0, "task-start", "a"), 0)
        self.assertEqual(self.go(1, "mark"), 0)
        self.assertEqual(self.go(2, "task-pause", "a", "--on", "D"), 0)  # blocked [0,2] while running, then paused
        self.assertEqual(self.state()["tasks"]["a"]["blocks"], [[iso(0), iso(2)]])
        r = self.show(3)  # paused: no blocked time is added, and none is taken from the pause
        self.assertEqual((r["tasks"]["a"]["running_h"], r["tasks"]["a"]["blocked_h"]), (0.0, 2.0))
        self.assertEqual(self.go(4, "task-resume", "a"), 0)  # the pause's write saw no block, so 2..4 doesn't bridge
        self.assertEqual(self.go(5, "mark"), 0)  # blocked again from 4
        self.assertEqual(self.state()["tasks"]["a"]["blocks"], [[iso(0), iso(2)], [iso(4), iso(5)]])
        self.shows["c"] = shown("c", done_at=iso(6))  # c closes at 6h; the block runs to there
        self.items[3] = rd(item("c", state="done"), "done")
        r = self.show(7)  # running 0-2 blocked, 4-7 running 6-7 only
        self.assertEqual((r["tasks"]["a"]["running_h"], r["tasks"]["a"]["blocked_h"]), (1.0, 4.0))


class StoredBlocks(unittest.TestCase):
    """The clock as the state stores it: blocked time counts only inside running segments."""

    ITEMS_A_WAITS_C = [ITEMS[0], rd(item("a"), "waiting", ["c"]), item("b"), rd(item("c"), "ready"), item("d")]

    def test_stored_blocks_outside_running_segments_never_reduce_running_time(self):
        # blocks normally never overlap a pause; if one did, only its running part may be subtracted
        st = {"tasks": {"a": {"segments": [[iso(0), iso(2)], [iso(4), None]], "blocks": [[iso(1), iso(5)]]}},
              "forecasts": []}
        r = run(state=st, items=self.ITEMS_A_WAITS_C, now=at(6))
        self.assertEqual((r["tasks"]["a"]["running_h"], r["tasks"]["a"]["blocked_h"]), (2.0, 2.0))

    def test_open_blocked_tail_does_not_count_while_the_task_is_paused(self):
        # a stale mark, as if the pause's write were lost: the paused task's blocked tail must not extend
        st = {"tasks": {"a": {"segments": [[iso(0), iso(2)]],
                              "block_mark": {"at": iso(1), "blocked": True, "on": ["c"]}}}, "forecasts": []}
        r = run(state=st, items=self.ITEMS_A_WAITS_C, now=at(6))
        self.assertEqual((r["tasks"]["a"]["running_h"], r["tasks"]["a"]["blocked_h"]), (2.0, 0.0))


class Acyclic(unittest.TestCase):
    def test_cli_error_and_bad_schema_fail_loudly(self):
        bad = mock.Mock(stdout='{"ok": false, "error": {"code": "not-set-up", "message": "no tracker"}}',
                        stderr="", returncode=5)
        with mock.patch.object(SB.subprocess, "run", return_value=bad):
            with self.assertRaisesRegex(SB.ScoreboardError, "not-set-up"):
                SB.acyclic("item", "list")
        junk = mock.Mock(stdout='{"ok": true, "data": {"nope": 1}}', stderr="", returncode=0)
        with mock.patch.object(SB.subprocess, "run", return_value=junk):
            with self.assertRaisesRegex(SB.ScoreboardError, "schema"):
                SB.item_list()
            with self.assertRaisesRegex(SB.ScoreboardError, "schema"):
                SB.doctor()
        real = mock.Mock(stdout='{"ok": true, "data": {"commits": {"checked": 1, "unchecked": 1, '
                                '"unmerged": [{"item": "a", "repository": "o/r", "commit": "abc", "reason": "x"}, '
                                '{"item": "a", "repository": "o/r", "commit": "abd", "reason": "z"}], '
                                '"unchecked_commits": [{"item": "b", "repository": "o/r", "commit": "def", "reason": "y"}]}}}',
                         stderr="", returncode=0)
        with mock.patch.object(SB.subprocess, "run", return_value=real):
            self.assertEqual(SB.doctor(), {"unchecked": 1, "unmerged": {"a": "x; z"}, "unchecked_commits": {"b": "y"}})


if __name__ == "__main__":
    unittest.main()
