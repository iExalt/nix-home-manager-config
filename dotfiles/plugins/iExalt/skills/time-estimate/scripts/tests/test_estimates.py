"""Tests for estimates.py. Run: python3 -I -m unittest discover -s <scripts>/tests"""
import json
import math
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
import estimates as E  # noqa: E402


def rec(**kw):
    base = {"task": "fixture task", "kind": "small-fix", "est_low_h": 0.25, "est_high_h": 0.5,
            "actual_h": 0.2, "outcome": "done"}
    base.update(kw)
    return base


class Validate(unittest.TestCase):
    def errs(self, r):
        return E.validate(r)[0]

    def test_minimal_live_record_is_valid(self):
        self.assertEqual(self.errs(rec()), [])

    def test_rejects_unknown_key_and_bad_enums(self):
        self.assertIn("unknown key 'kindd'", self.errs(rec(kindd="x")))
        self.assertTrue(any("kind 'small-fixes'" in e for e in self.errs(rec(kind="small-fixes"))))
        self.assertTrue(any("outcome" in e for e in self.errs(rec(outcome="finished"))))
        self.assertTrue(any("includes" in e for e in self.errs(rec(includes=["impl", "deploy"]))))

    def test_rejects_wrong_types_including_bool_for_number(self):
        self.assertIn("est_low_h has type str", self.errs(rec(est_low_h="0.2")))
        self.assertIn("compactions has type bool", self.errs(rec(compactions=True)))

    def test_ranges_must_be_ordered_and_paired(self):
        self.assertIn("need 0 <= est_low_h <= est_high_h", self.errs(rec(est_low_h=1, est_high_h=0.5)))
        self.assertIn("raw_low_h and raw_high_h must be given together", self.errs(rec(raw_low_h=1)))
        self.assertIn("est_low_h must be above zero", self.errs(rec(est_low_h=0)))

    def test_live_done_needs_actual_but_stopped_does_not(self):
        r = rec(); del r["actual_h"]
        self.assertTrue(any("actual_h is required" in e for e in self.errs(r)))
        self.assertEqual(self.errs(dict(r, outcome="stopped")), [])

    def test_ported_records_may_lack_estimate_and_kind(self):
        r = {"task": "old entry", "outcome": "done", "source": "md-port-prose", "port_ref": 200}
        self.assertEqual(self.errs(r), [])
        self.assertTrue(self.errs(dict(r, source="live")))
        self.assertEqual(self.errs(dict(r, source="md-port", est_low_h=0, est_high_h=0.5)), [])

    def test_bias_factor_must_match_raw_range(self):
        ok = rec(raw_low_h=0.4, raw_high_h=0.8, bias_factor=0.625, est_low_h=0.25, est_high_h=0.5)
        self.assertEqual(self.errs(ok), [])
        self.assertTrue(self.errs(dict(ok, est_low_h=0.4)))
        no_raw = rec(bias_factor=0.6)
        self.assertTrue(any("raw_low_h/raw_high_h are required" in e for e in self.errs(no_raw)))

    def test_debiased_ranges_of_any_width_validate_but_a_missing_factor_errors(self):
        gut = dict(raw_low_h=0.5, raw_high_h=1.0, bias_factor=0.6)
        # stats-width range, probe-narrowed range and rounded gut-width range: midpoint ~0.42h
        for lo, hi in ((0.212, 0.764), (0.34, 0.53), (0.33, 0.67)):
            self.assertEqual(E.validate(rec(est_low_h=lo, est_high_h=hi, **gut)), ([], []), (lo, hi))
        errs, warns = E.validate(rec(est_low_h=0.36, est_high_h=0.62, **gut))  # midpoint 0.47h, 12% off
        self.assertEqual(errs, [])
        errs, warns = E.validate(rec(est_low_h=0.4, est_high_h=0.7, **gut))  # 25% > off > 15%
        self.assertEqual(errs, [])
        self.assertTrue(warns)
        self.assertTrue(self.errs(rec(est_low_h=0.5, est_high_h=1.0, **gut)))  # factor not applied

    def test_rejects_other_versions_non_finite_numbers_and_empty_task(self):
        self.assertIn("v 2 is not 1", self.errs(rec(v=2)))
        self.assertIn("est_high_h is not finite", self.errs(rec(est_high_h=float("inf"))))
        self.assertIn("task is empty", self.errs(rec(task="  ")))

    def test_actual_above_elapsed_is_a_warning_not_an_error(self):
        r = rec(actual_h=2, started_at="2026-01-01T10:00:00Z", ended_at="2026-01-01T11:00:00Z")
        errs, warns = E.validate(r)
        self.assertEqual(errs, [])
        self.assertTrue(warns)
        self.assertTrue(E.validate(rec(started_at="yesterday"))[0])


class LogAndCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.tmp.name) / "sub" / "log.jsonl"
        self.env = dict(os.environ, TIME_ESTIMATE_LOG=str(self.path))

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, stdin=""):
        return subprocess.run([sys.executable, "-I", str(SCRIPTS / "estimates.py"), *args],
                              input=stdin, capture_output=True, text=True, env=self.env)

    def test_log_appends_defaults_and_check_passes(self):
        p = self.run_cli("log", stdin=json.dumps(rec(thread_id="fixture-thread")))
        self.assertEqual(p.returncode, 0, p.stderr)
        line = json.loads(self.path.read_text())
        self.assertEqual((line["v"], line["source"]), (1, "live"))
        self.assertRegex(line["logged_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(oct(self.path.stat().st_mode & 0o777), "0o600")
        self.assertEqual(self.run_cli("check").returncode, 0)

    def test_log_refuses_invalid_record_and_writes_nothing(self):
        p = self.run_cli("log", stdin=json.dumps(rec(kind="nope")))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("not logged", p.stderr)
        self.assertFalse(self.path.exists())

    def test_log_does_not_join_a_partial_last_line(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text('{"task": "crashed writer"')
        self.assertEqual(self.run_cli("log", stdin=json.dumps(rec())).returncode, 0)
        lines = self.path.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["task"], "fixture task")
        p = self.run_cli("check")
        self.assertEqual(p.returncode, 1)
        self.assertIn(":1: invalid JSON", p.stdout)


def unit_recs(ratios, kind="small-fix"):
    """Records with a 0.5-2h range (geometric midpoint 1h) and actual = ratio hours."""
    return [rec(kind=kind, est_low_h=0.5, est_high_h=2.0, actual_h=r) for r in ratios]


class Calibration(unittest.TestCase):
    def test_units_skip_prose_unfinished_and_numberless(self):
        rs = unit_recs([0.5]) + [
            dict(rec(), source="md-port-prose"), rec(outcome="stopped"),
            {"task": "t", "outcome": "done", "source": "md-port", "kind": None}]
        us, ex = E.units(rs)
        self.assertEqual(len(us), 1)
        self.assertEqual((ex["prose port"], ex["not done"], ex["no numbers"]), (1, 1, 1))

    def test_children_merge_into_unrecorded_parent_and_drop_under_recorded_one(self):
        kids = [rec(parent_id="camp", est_low_h=1, est_high_h=2, actual_h=1),
                rec(parent_id="camp", est_low_h=1, est_high_h=2, actual_h=2)]
        us, ex = E.units(kids)
        self.assertEqual(len(us), 1)
        self.assertEqual((us[0]["raw_lo"], us[0]["raw_hi"], us[0]["act"]), (2, 4, 3))
        self.assertEqual(ex["children merged into parent"], 1)
        us, ex = E.units(kids + [rec(thread_id="camp", actual_h=5)])
        self.assertEqual(len(us), 1)
        self.assertEqual(us[0]["act"], 5)
        self.assertEqual(ex["child of recorded parent"], 2)

    def test_an_excluded_parent_does_not_swallow_its_children(self):
        kids = [rec(parent_id="camp", actual_h=0.3), rec(parent_id="camp", actual_h=0.3)]
        for parent in (rec(thread_id="camp", outcome="stopped"),
                       dict(rec(thread_id="camp"), source="md-port-prose")):
            us, ex = E.units(kids + [parent])
            self.assertEqual(len(us), 1)
            self.assertAlmostEqual(us[0]["act"], 0.6)
            self.assertEqual(ex["child of recorded parent"], 0)

    def test_null_raw_falls_back_to_stated_and_missing_stated_is_excluded(self):
        us, _ = E.units([rec(raw_low_h=None, raw_high_h=None)])
        self.assertEqual((us[0]["raw_lo"], us[0]["raw_hi"]), (0.25, 0.5))
        ported = {"task": "t", "kind": "small-fix", "outcome": "done", "source": "md-port",
                  "raw_low_h": 0.2, "raw_high_h": 0.4, "actual_h": 0.3}
        us, ex = E.units([ported])
        self.assertEqual((len(us), ex["no numbers"]), (0, 1))

    def test_null_ids_never_link(self):
        us, _ = E.units([rec(thread_id=None, parent_id=None), rec(parent_id=None)])
        self.assertEqual(len(us), 2)

    def test_fit_recovers_bias_and_spread(self):
        model = E.fit(E.units(unit_recs([0.5, 0.5, 0.5, 0.5]))[0])
        b, q25, q75, n = model["_all"]
        self.assertAlmostEqual(math.exp(b), 0.5)
        self.assertAlmostEqual(q25, 0.0)
        self.assertEqual(n, 4)

    def test_small_kind_shrinks_toward_overall_and_borrows_spread(self):
        us = E.units(unit_recs([0.5] * 16) + unit_recs([2.0] * 2, kind="audit"))[0]
        model = E.fit(us)
        b_all = model["_all"][0]
        b_audit = model["audit"][0]
        self.assertAlmostEqual(b_audit, 0.25 * math.log(2) + 0.75 * b_all)
        self.assertEqual(model["audit"][1:3], model["_all"][1:3])

    def test_interval_score_penalises_width_and_misses(self):
        ln = math.log
        self.assertAlmostEqual(E.interval_score(ln(1), ln(2), ln(1.5)), 1.0)
        self.assertAlmostEqual(E.interval_score(ln(1), ln(2), ln(4)), 1.0 + 4 * 1.0)

    def test_backtest_beats_stated_ranges_on_biased_history(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = pathlib.Path(tmp.name) / "log.jsonl"
        ratios = [0.4, 0.5, 0.6, 0.7] * 15  # stated midpoint 1h; actuals well below it
        path.write_text("".join(json.dumps(r) + "\n" for r in unit_recs(ratios)))
        p = subprocess.run([sys.executable, "-I", str(SCRIPTS / "estimates.py"), "stats", "--backtest"],
                           capture_output=True, text=True,
                           env=dict(os.environ, TIME_ESTIMATE_LOG=str(path)))
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = {l.split()[0]: l.split() for l in p.stdout.splitlines() if not l.startswith("#")}
        self.assertLess(float(rows["fitted"][1].rstrip("x")), float(rows["stated"][1].rstrip("x")))
        self.assertLess(float(rows["fitted"][4]), float(rows["stated"][4]))
        p = subprocess.run([sys.executable, "-I", str(SCRIPTS / "estimates.py"), "stats"],
                           capture_output=True, text=True,
                           env=dict(os.environ, TIME_ESTIMATE_LOG=str(path)))
        self.assertIn("small-fix", p.stdout)
        self.assertLessEqual(len(p.stdout.splitlines()), 30)


if __name__ == "__main__":
    unittest.main()
