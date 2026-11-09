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


DOC_OK = {"unchecked": 0, "unmerged": []}


def campaign(**kw):
    c = {"name": "ci", "goal": "faster", "start": T0, "under": "EPIC", "tasks": ["a", "b", "c", "d"],
         "launch_tasks": ["a", "b", "c", "d"], "approved_added": [], "estimate_h": [8.0, 12.0],
         "task_estimates": {"a": [1.0, 2.0]}, "metric": None, "tripwires": dict(SB.DEFAULT_TRIPWIRES),
         "amendments": []}
    c.update(kw)
    return c


ITEMS = [item("EPIC", parent="INIT")] + [item(x) for x in "abcd"]


def run(c=None, state=None, items=None, shows=None, doc=DOC_OK, now=None, verify=lambda c: None):
    c = c or campaign()
    return SB.evaluate(c, state or {"tasks": {}, "forecasts": []}, items or ITEMS,
                       shows if shows is not None else [], doc, now or at(3), verify)


def fired(r):
    return {t["name"] for t in r["tripwires"] if t["fired"]}


class Done(unittest.TestCase):
    def test_counts_only_verified_merge(self):
        r = run(shows=[shown("a"), shown("b", commit=None)], items=ITEMS[:1] + [item("a", state="done"), item("b", state="done"), item("c"), item("d")])
        self.assertEqual((r["done"], r["total"]), (1, 4))
        self.assertIn("unverified_done", fired(r))

    def test_unchecked_commits_not_verified(self):
        r = run(shows=[shown("a")], doc={"unchecked": 1, "unmerged": []})
        self.assertEqual(r["done"], 0)
        self.assertIn("unverified_done", fired(r))

    def test_unchecked_elsewhere_rechecked_per_commit(self):
        r = run(shows=[shown("a")], doc={"unchecked": 1, "unmerged": []}, verify=lambda c: True)
        self.assertEqual(r["done"], 1)
        self.assertNotIn("unverified_done", fired(r))

    def test_unmerged_commit_not_verified(self):
        r = run(shows=[shown("a")], doc={"unchecked": 0, "unmerged": ["o/r@abc"]})
        self.assertEqual(r["done"], 0)

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
    def test_high_end_flags(self):
        r = run(now=at(21))
        self.assertTrue(r["over_high"])
        self.assertIn("21h of 8–12h ⚠", SB.line1(r))
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
        self.assertEqual(self.go("task-pause", "a", now="2026-11-07T03:00:00Z"), 0)
        self.assertEqual(self.go("task-pause", "a", now="2026-11-07T03:10:00Z"), 1)
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


if __name__ == "__main__":
    unittest.main()
