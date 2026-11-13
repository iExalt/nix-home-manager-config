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

    def test_review_round_minutes_must_not_be_negative(self):
        self.assertEqual(self.errs(rec(review_round_minutes=6)), [])
        self.assertTrue(any("review_round_minutes" in e
                            for e in self.errs(rec(review_round_minutes=-1))))

    def test_actual_approx_must_be_a_boolean(self):
        self.assertEqual(self.errs(rec(actual_approx=True)), [])
        self.assertTrue(any("actual_approx" in e for e in self.errs(rec(actual_approx="yes"))))

    def test_percentiles_must_be_ordered(self):
        ok = rec(est_p10_h=0.1, est_median_h=0.3, est_p90_h=0.9)
        self.assertEqual(self.errs(ok), [])
        for bad in (dict(ok, est_median_h=0.6), dict(ok, est_p10_h=0.3), dict(ok, est_p90_h=0.4)):
            self.assertTrue(any("est_p10_h <= est_low_h" in e for e in self.errs(bad)), bad)

    def test_bias_check_uses_the_stated_median_when_given(self):
        gut = dict(raw_low_h=0.5, raw_high_h=1.0, bias_factor=0.6)
        self.assertEqual(self.errs(rec(est_low_h=0.26, est_median_h=0.42, est_high_h=0.73, **gut)), [])
        self.assertTrue(self.errs(rec(est_low_h=0.26, est_median_h=0.7, est_high_h=0.73, **gut)))

    def test_revisions_are_validated(self):
        rev = {"at": "2026-01-01T10:10:00Z", "elapsed_h": 0.1, "remaining_low_h": 0.2,
               "remaining_median_h": 0.3, "remaining_high_h": 0.5, "trigger": "probe", "reason": "r"}
        later = dict(rev, at="2026-01-01T10:30:00Z", elapsed_h=0.15, trigger="round")
        self.assertEqual(self.errs(rec(actual_h=0.4, revisions=[rev, later])), [])
        cases = {
            "earlier than": [later, dict(rev, elapsed_h=0.15)],
            "elapsed_h is lower": [dict(rev, elapsed_h=0.2), dict(later, elapsed_h=0.1)],
            "elapsed_h exceeds actual_h": [dict(rev, elapsed_h=0.9)],
            "remaining_low_h <= remaining_median_h": [dict(rev, remaining_median_h=0.6)],
            "trigger": [dict(rev, trigger="whim")],
            "bad keys ['when']": [dict(rev, when="x")],
            "missing ['at']": [{k: v for k, v in rev.items() if k != "at"}],
        }
        for want, revs in cases.items():
            self.assertTrue(any(want in e for e in self.errs(rec(actual_h=0.4, revisions=revs))), want)

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

    def test_estimate_roundtrips_through_log_with_skewed_and_mixed_history(self):
        histories = [
            unit_recs([0.01] + [1.0] * 31, kind="audit"),
            unit_recs([100.0] + [1.0] * 31, kind="audit"),
            unit_recs([1.0] * 120) + unit_recs([0.01, 100.0] * 6, kind="audit"),
        ]
        keys = ("est_p10_h", "est_low_h", "est_median_h", "est_high_h", "est_p90_h")
        self.path.parent.mkdir(parents=True)
        for history in histories:
            with self.subTest(actuals=[r["actual_h"] for r in history[-12:]]):
                self.path.write_text("".join(json.dumps(r) + "\n" for r in history))
                p = self.run_cli("estimate", "--kind", "audit", "--low", "0.5", "--high", "2")
                self.assertEqual(p.returncode, 0, p.stderr)
                fragment = json.loads(p.stdout.splitlines()[-1])
                values = [fragment[k] for k in keys]
                self.assertEqual(values, sorted(values))
                p = self.run_cli("log", stdin=json.dumps(dict(
                    fragment, task="roundtrip fixture", outcome="done", actual_h=1.0)))
                self.assertEqual(p.returncode, 0, p.stderr)
                logged = json.loads(self.path.read_text().splitlines()[-1])
                self.assertEqual({k: logged[k] for k in fragment}, fragment)
                self.assertEqual(self.run_cli("check").returncode, 0)

    def test_log_refuses_invalid_record_and_writes_nothing(self):
        for bad, why in ((rec(kind="nope"), "kind"), (rec(thread_id="/root/reviewer"), "agent path"),
                         (rec(parent_id="/root"), "agent path")):
            p = self.run_cli("log", stdin=json.dumps(bad))
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("not logged", p.stderr)
            self.assertIn(why, p.stderr)
            self.assertFalse(self.path.exists())

    def test_remaining_and_since_report_from_the_log(self):
        self.path.parent.mkdir(parents=True)
        def write(recs):
            self.path.write_text("".join(json.dumps(r) + "\n" for r in recs))
        rev = lambda gut: [{"at": "2026-11-09T16:00:00Z", "elapsed_h": 0.0, "remaining_low_h": gut,
                            "remaining_high_h": gut}]
        recs = [rec(actual_h=a, revisions=rev(0.25), logged_at="2026-11-09T17:00:00Z",
                    harness="codex") for a in (0.5, 0.4, 0.6) * 3]
        write(recs)
        p = self.run_cli("remaining", "--low", "0.25", "--high", "0.5")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("only 9 records", p.stderr)
        write(recs + [rec(actual_h=0.5, revisions=rev(0.25), logged_at="2026-11-10T09:00:00Z",
                          harness="claude-code")])
        p = self.run_cli("remaining", "--low", "0.25", "--high", "0.5")
        self.assertEqual(p.returncode, 0, p.stderr)
        frag = json.loads(p.stdout.splitlines()[-1])
        self.assertEqual((frag["raw_remaining_low_h"], frag["raw_remaining_high_h"]), (0.25, 0.5))
        self.assertLess(frag["remaining_low_h"], frag["remaining_median_h"])
        self.assertLess(frag["remaining_median_h"], frag["remaining_high_h"])
        self.assertAlmostEqual(frag["remaining_median_h"] / (0.125 ** 0.5), 2.0, places=1)
        p = self.run_cli("stats", "--since", "2026-11-10", "--by", "harness")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("# 1 finished records", p.stdout)
        self.assertRegex(p.stdout, r"harness: claude-code\s+1 ")
        self.assertNotIn("harness: codex", p.stdout)
        p = self.run_cli("stats", "--since", "2026-11-10T09:00Z", "--by", "harness")
        self.assertIn("# 1 finished records", p.stdout)  # a record logged at exactly that time
        for bad in (("stats", "--since", "last week"), ("remaining", "--low", "0", "--high", "inf")):
            self.assertNotEqual(self.run_cli(*bad).returncode, 0)

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


def grec(**kw):
    """A record that logged its gut range; by default the same as its stated range."""
    r = rec(**kw)
    r.setdefault("raw_low_h", r.get("est_low_h"))
    r.setdefault("raw_high_h", r.get("est_high_h"))
    return r


def unit_recs(ratios, kind="small-fix"):
    """Records with a 0.5-2h range (geometric midpoint 1h) and actual = ratio hours."""
    return [grec(kind=kind, est_low_h=0.5, est_high_h=2.0, actual_h=r) for r in ratios]


class Calibration(unittest.TestCase):
    def test_units_skip_prose_unfinished_and_numberless(self):
        rs = unit_recs([0.5]) + [
            dict(grec(), source="md-port-prose"), grec(outcome="stopped"),
            {"task": "t", "outcome": "done", "source": "md-port", "kind": None}]
        us, ex = E.units(rs)
        self.assertEqual(len(us), 1)
        self.assertEqual((ex["prose port"], ex["not done"], ex["no numbers"]), (1, 1, 1))

    def test_children_merge_into_unrecorded_parent_and_drop_under_recorded_one(self):
        kids = [grec(parent_id="camp", est_low_h=1, est_high_h=2, actual_h=1),
                grec(parent_id="camp", est_low_h=1, est_high_h=2, actual_h=2)]
        us, ex = E.units(kids)
        self.assertEqual(len(us), 1)
        self.assertEqual((us[0]["raw_lo"], us[0]["raw_hi"], us[0]["act"]), (2, 4, 3))
        self.assertEqual(ex["children merged into parent"], 1)
        us, ex = E.units(kids + [grec(thread_id="camp", actual_h=5)])
        self.assertEqual(len(us), 1)
        self.assertEqual(us[0]["act"], 5)
        self.assertEqual(ex["child of recorded parent"], 2)

    def test_an_excluded_parent_does_not_swallow_its_children(self):
        kids = [grec(parent_id="camp", actual_h=0.3), grec(parent_id="camp", actual_h=0.3)]
        for parent in (grec(thread_id="camp", outcome="stopped"),
                       dict(grec(thread_id="camp"), source="md-port-prose")):
            us, ex = E.units(kids + [parent])
            self.assertEqual(len(us), 1)
            self.assertAlmostEqual(us[0]["act"], 0.6)
            self.assertEqual(ex["child of recorded parent"], 0)

    def test_records_without_a_gut_range_do_not_fit_the_factor(self):
        # A stated range may already be corrected by hand; only a logged gut can be debiased.
        us, ex = E.units([grec(raw_low_h=None, raw_high_h=None), grec(raw_low_h=0.5, raw_high_h=1.0)])
        self.assertEqual((len(us), ex["no gut range"]), (1, 1))
        self.assertEqual((us[0]["raw_lo"], us[0]["raw_hi"]), (0.5, 1.0))
        # A parent without a gut range can't stand in for its children, so they merge instead.
        kids = [grec(parent_id="camp", actual_h=0.3), grec(parent_id="camp", actual_h=0.3)]
        us, ex = E.units(kids + [grec(thread_id="camp", raw_low_h=None, raw_high_h=None)])
        self.assertEqual((len(us), ex["no gut range"], ex["child of recorded parent"]), (1, 1, 0))
        self.assertAlmostEqual(us[0]["act"], 0.6)
        ported = {"task": "t", "kind": "small-fix", "outcome": "done", "source": "md-port",
                  "raw_low_h": 0.2, "raw_high_h": 0.4, "actual_h": 0.3}
        us, ex = E.units([ported])
        self.assertEqual((len(us), ex["no numbers"]), (0, 1))

    def test_null_and_agent_path_ids_never_link(self):
        us, _ = E.units([grec(thread_id=None, parent_id=None), grec(parent_id=None)])
        self.assertEqual(len(us), 2)
        # Agent paths repeat across sessions: neither merge nor drop records that share one.
        us, _ = E.units([grec(parent_id="/root"), grec(parent_id="/root"), grec(thread_id="/root")])
        self.assertEqual(len(us), 3)

    def test_uncalibrated_guts_stop_fitting_once_enough_calibrated_units_exist(self):
        cal = lambda n: [grec(bias_factor=0.5) for _ in range(n)]
        gut_only = [grec(actual_h=1.0) for _ in range(5)]
        us, ex = E.units(cal(E.CALIBRATED_MIN) + gut_only)
        self.assertEqual((len(us), ex["not calibrated"]), (E.CALIBRATED_MIN, 5))
        us, ex = E.units(cal(E.CALIBRATED_MIN - 1) + gut_only)
        self.assertEqual((len(us), ex["not calibrated"]), (E.CALIBRATED_MIN + 4, 0))

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

    def test_skewed_quartiles_and_pooled_tails_stay_ordered(self):
        for ratios in ([0.01] + [1.0] * 31, [100.0] + [1.0] * 31):
            us = E.units(unit_recs(ratios, kind="audit"))[0]
            model = E.fit(us)
            for b, q25, q75, _ in model.values():
                self.assertAlmostEqual(b, sum(math.log(r) for r in ratios) / len(ratios))
                self.assertLessEqual(q25, 0)
                self.assertGreaterEqual(q75, 0)
        us = E.units(unit_recs([1.0] * 120) +
                     unit_recs([0.01, 100.0] * 6, kind="audit"))[0]
        b, q25, q75, _ = E.fit(us[-60:])["audit"]
        t10, t90 = E.tails(us, q25, q75)
        self.assertLessEqual(t10, q25)
        self.assertGreaterEqual(t90, q75)

    def test_revisions_run_on_active_time_including_added_scope(self):
        # A campaign's actual_h leaves out scope_h, but its revisions were stated on the full clock.
        r = rec(actual_h=1.0, scope_h=3.0, revisions=[
            {"at": "2026-11-09T16:00:00Z", "elapsed_h": 3.5, "remaining_low_h": 0.25,
             "remaining_high_h": 1.0}])
        self.assertEqual(E.validate(r)[0], [])
        self.assertTrue(E.validate(dict(r, scope_h=0))[0])
        per_rec, hits, n, _ = E.remaining_calibration([r])
        self.assertEqual((hits, n), (1, 1))
        self.assertAlmostEqual(math.exp(per_rec[0]), 1.0)  # 0.5 h left, as predicted

    def test_remaining_time_factor_weights_each_record_once(self):
        def revs(*preds):
            return [{"at": f"2026-01-01T10:{i:02d}:00Z", "elapsed_h": 0.0, "remaining_low_h": p / 2,
                     "remaining_median_h": p, "remaining_high_h": p * 2} for i, p in enumerate(preds)]
        recs = [grec(actual_h=1.0, revisions=revs(0.5, 0.5, 0.5, 0.5)),  # actual 2x stated, 4 times
                grec(actual_h=1.0, revisions=revs(2.0))]                # actual 0.5x stated, once
        per_rec, hits, n, _ = E.remaining_calibration(recs)
        self.assertEqual((len(per_rec), n), (2, 5))
        self.assertAlmostEqual(math.exp(sum(per_rec) / 2), 1.0)
        self.assertEqual(hits, 5)
        broken = [dict(r, remaining_high_h=float("inf")) for r in revs(0.5)]
        self.assertIn("revisions[0] has a non-finite number",
                      " ".join(E.validate(grec(actual_h=1.0, revisions=broken))[0]))
        self.assertEqual(E.remaining_calibration([grec(actual_h=1.0, revisions=broken)])[2], 1)

    def test_remaining_factor_fits_the_logged_remaining_gut_not_the_corrected_range(self):
        v = {"at": "2026-01-01T10:00:00Z", "elapsed_h": 0.0, "raw_remaining_low_h": 0.25,
             "raw_remaining_high_h": 0.25, "remaining_low_h": 0.25, "remaining_median_h": 0.5,
             "remaining_high_h": 1.0}
        r = grec(actual_h=0.5, revisions=[v])
        self.assertEqual(E.validate(r)[0], [])
        per_rec, hits, _, _ = E.remaining_calibration([r])
        self.assertAlmostEqual(math.exp(per_rec[0]), 2.0)  # 0.5 h left over a 0.25 h gut
        self.assertEqual(hits, 1)
        for bad in ({"raw_remaining_low_h": 0.25, "raw_remaining_high_h": None},
                    {"raw_remaining_low_h": 0.5, "raw_remaining_high_h": 0.25}):
            self.assertIn("raw_remaining", " ".join(E.validate(grec(actual_h=0.5, revisions=[
                {k: x for k, x in dict(v, **bad).items() if x is not None}]))[0]))

    def test_autofill_adds_only_missing_harness_and_matching_thread(self):
        r = rec(); E.autofill(r, ("claude-code", "t1"))
        self.assertEqual((r["harness"], r["thread_id"]), ("claude-code", "t1"))
        r = rec(harness="codex", thread_id="given"); E.autofill(r, ("claude-code", "t1"))
        self.assertEqual((r["harness"], r["thread_id"]), ("codex", "given"))
        r = rec(harness="codex"); E.autofill(r, ("claude-code", "t1"))
        self.assertNotIn("thread_id", r)  # another harness's id would mislabel the record
        r = rec(); E.autofill(r, None)
        self.assertNotIn("harness", r)

    def test_log_warns_on_missing_model_and_skipped_calibration(self):
        history = unit_recs([1.0] * E.PERCENTILE_MIN)
        uncal = grec(model="m")
        self.assertIn("no bias_factor", " ".join(E.log_warnings(uncal, history)))
        for quiet in (dict(uncal, bias_factor=0.5), dict(uncal, parent_id="camp"),
                      dict(uncal, thread_id="camp#amend-1")):
            self.assertEqual(E.log_warnings(quiet, history), [])
        self.assertEqual(E.log_warnings(uncal, history[:5]), [])
        self.assertIn("model is missing", " ".join(E.log_warnings(rec(), [])))

    def test_review_latency_reports_only_groups_with_enough_records(self):
        recs = ([rec(kind="audit", review_round_minutes=m) for m in (2, 3, 4, 5, 6)] +
                [rec(kind="docs", review_round_minutes=20)] + [rec()])
        self.assertEqual(E.review_latency(recs), {"all": (4.5, 6), "audit": (4, 5)})
        kindless = [{"review_round_minutes": m} for m in (1, 2, 3, 4, 5)]
        self.assertEqual(E.review_latency(kindless)["other"], (3, 5))
        self.assertEqual(E.review_latency(recs[:4]), {})

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
        self.assertRegex(rows["fitted"][-1], r"^\d+%$")  # share of actuals under the fitted p90
        env = dict(os.environ, TIME_ESTIMATE_LOG=str(path))
        p = subprocess.run([sys.executable, "-I", str(SCRIPTS / "estimates.py"), "estimate",
                            "--kind", "small-fix", "--low", "0.5", "--high", "2"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Likely", p.stdout)
        fragment = json.loads(p.stdout.splitlines()[-1])
        full = dict(fragment, task="fixture task", outcome="done", actual_h=0.5)
        self.assertEqual(E.validate(full), ([], []))  # the printed numbers log cleanly
        self.assertAlmostEqual(fragment["est_median_h"], 0.55, delta=0.05)


if __name__ == "__main__":
    unittest.main()
