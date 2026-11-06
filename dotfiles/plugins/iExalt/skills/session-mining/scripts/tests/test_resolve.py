import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import fixtures as fx  # noqa: E402
from session_mining.out import Out  # noqa: E402
from session_mining.resolve import Inventory, entity_keys, resolve  # noqa: E402
from session_mining.stores import Roots, claude_files, codex_files  # noqa: E402

CLI = os.path.join(os.path.dirname(HERE), "sessions.py")


class StoresAndResolve(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="sm-test-")
        cls.homes = fx.make_roots(cls.tmp)
        cls.roots = Roots(*cls.homes)
        cls.inv = Inventory(cls.roots)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def ids(self, ref):
        return [(c.type, c.id, c.match) for c in resolve(self.inv, ref)]

    def test_enumeration_kinds_and_skips(self):
        cf = list(claude_files(self.roots))
        self.assertEqual(sorted((f.kind, f.session) for f in cf),
                         sorted([("main", fx.C1), ("main", fx.C2), ("subagent", fx.AGENT)]))
        sub = [f for f in cf if f.kind == "subagent"][0]
        self.assertEqual(sub.parent, fx.C1)
        xf = list(codex_files(self.roots))
        self.assertEqual(len(xf), 5)                       # notes.txt ignored
        seg = [f for f in xf if f.segment]
        self.assertEqual([(f.session, f.segment) for f in seg], [(fx.T1, fx.T1_SEG)])
        self.assertTrue([f for f in xf if f.session == fx.T_ARCH][0].archived)

    def test_exact_and_codex_link(self):
        for ref in (fx.T1, "codex://threads/" + fx.T1):
            got = resolve(self.inv, ref)
            self.assertEqual(len(got), 1)
            c = got[0]
            self.assertEqual((c.type, c.id, c.match), ("codex-thread", fx.T1, "exact"))
            self.assertEqual(len(c.files), 2)               # rollout + continuation segment
            self.assertEqual(c.title, "Deploy the gadget")  # envelope stripped
            self.assertTrue(any(n.startswith("1 spawned child thread(s): " + fx.T2) for n in c.notes))

    def test_shared_timestamp_prefix_is_ambiguous(self):
        got = resolve(self.inv, fx.T1[:13])
        self.assertEqual({c.id for c in got}, {fx.T1, fx.T2})
        self.assertEqual(len(entity_keys(got)), 2)

    def test_suffix_and_segment_and_subagent(self):
        self.assertEqual(self.ids(fx.T2[-12:]), [("codex-thread", fx.T2, "suffix")])
        self.assertEqual(self.ids(fx.T1_SEG), [("codex-thread", fx.T1, "exact (segment id)")])
        self.assertEqual(self.ids("agent-" + fx.AGENT)[0][:2], ("claude-subagent", fx.AGENT))

    def test_db_row_without_transcript(self):
        c = resolve(self.inv, "01a0ffff")[0]
        self.assertFalse(c.files)
        self.assertTrue(any("transcript missing" in n for n in c.notes))

    def test_paseo_short_id_links_and_pruned(self):
        got = resolve(self.inv, fx.P1[:8])
        self.assertEqual([(c.type, c.id) for c in got], [("paseo-agent", fx.P1)])
        self.assertEqual([(l.type, l.id) for l in got[0].links], [("claude-session", fx.C1)])
        pr = resolve(self.inv, fx.P2[:8])[0]
        self.assertFalse(pr.links)
        self.assertTrue(any("pruned" in n for n in pr.notes))

    def test_provider_id_is_one_entity_with_its_paseo_agent(self):
        got = resolve(self.inv, fx.C1)
        self.assertEqual(len(entity_keys(got)), 1)
        self.assertEqual({c.type for c in got}, {"paseo-agent"})

    def test_title_search_excludes_guardian(self):
        got = self.ids("gadget")
        self.assertIn(("codex-thread", fx.T1, "title"), got)
        self.assertIn(("codex-thread", fx.T2, "title"), got)
        self.assertNotIn(fx.T_GUARD, [g[1] for g in got])
        self.assertEqual(self.ids("widget pipeline"), [("claude-session", fx.C2, "title")])

    def test_hex_looking_words_and_slashes_search_titles(self):
        self.assertIn(("codex-thread", fx.T2, "title"), self.ids("added"))
        self.assertIn(("codex-thread", fx.T2, "title"), self.ids("feed"))
        self.assertEqual(self.ids("nix/home"), [("codex-thread", fx.T2, "title")])

    def test_paseo_launchers(self):
        from session_mining.reader import paseo_launchers
        from session_mining.stores import PaseoAgent
        m = paseo_launchers(self.inv.paseo)
        self.assertEqual(m[fx.C1], "agent")                       # blank parent label: agent-created thread
        mk = lambda sess, labels: PaseoAgent("x", "claude", sess, "", "", "", labels)
        m = paseo_launchers([mk("s", {}), mk("s", {"paseo.schedule-id": "1"}), mk("s", {}), mk("t", {})])
        self.assertEqual(m, {"s": "schedule", "t": "human"})

    def test_path_resolves_to_owner(self):
        path = [f.path for f in claude_files(self.roots) if f.kind == "subagent"][0]
        self.assertEqual(self.ids(path), [("claude-subagent", fx.AGENT, "path")])

    def test_out_cap(self):
        buf = io.StringIO()
        o = Out(300, buf)
        for i in range(100):
            o.line("x" * 50)
        o.note("coverage line")
        o.close()
        text = buf.getvalue()
        self.assertLessEqual(len(text.encode()), 400)       # 400 is the floor
        self.assertIn("[output capped", text)
        self.assertTrue(text.endswith("# coverage line\n"))
        buf = io.StringIO()
        o = Out(500, buf)
        for i in range(20):
            o.line("y" * 30)
        for i in range(10):
            o.note("footer %d " % i + "z" * 60)              # footer-heavy: body yields, total holds
        o.close()
        self.assertLessEqual(len(buf.getvalue().encode()), 500)

    def run_cli(self, *args, python=None):
        homes = ["--claude-home", self.homes[0], "--codex-home", self.homes[1], "--paseo-home", self.homes[2]]
        if python is None:
            return fx.run_main(homes + list(args))
        return subprocess.run([python, "-I", CLI] + homes + list(args), capture_output=True, text=True, timeout=30)

    def test_cli_entry_under_isolated_mode(self):
        r = self.run_cli("resolve", fx.T1[:13], python=sys.executable)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("AMBIGUOUS: 2 candidates", r.stdout)
        for args in (("--max-bytes", "400", "stores"), ("stores", "--max-bytes", "400")):
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("output capped", r.stdout)
            self.assertLessEqual(len(r.stdout.encode()), 400)

    def test_show_line_ranges_and_file_headers(self):
        for rng, want in (("2", ["L2 "]), (":2", ["L1 ", "L2 "]), ("2:", ["L2 ", "L3 "]), ("1:1", ["L1 "])):
            r = self.run_cli("show", fx.C1, "--lines", rng)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual([l[:3] for l in r.stdout.splitlines() if l.startswith("L")], want, rng)
        r = self.run_cli("show", fx.C1, "--lines", "x")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--lines", r.stderr)
        r = self.run_cli("show", fx.C1, "--subagents")
        heads = [l for l in r.stdout.splitlines() if l.startswith("== ")]
        self.assertEqual(len(heads), 2, r.stdout)                  # each file is labelled before its lines
        self.assertIn("agent-" + fx.AGENT, heads[1])
        r = self.run_cli("show", fx.C1, "--subagents", "--last", "2")
        self.assertEqual(len([l for l in r.stdout.splitlines() if l.startswith("== ")]), 1)
        self.assertIn("6 matching event(s), 2 shown", r.stdout)

    def test_time_bounds(self):
        import sessions
        self.assertEqual(sessions._when("2026-11"), "2026-11-01T00:00:00")
        self.assertEqual(sessions._when("2026-11-02T03:04Z"), "2026-11-02T03:04:00")
        self.assertRegex(sessions._when("7d"), r"^\d{4}-\d\d-\d\dT")
        for bad in ("yesterday", "2026-13", "2026-11-02T3"):
            r = self.run_cli("grep", "x", "--since", bad)
            self.assertEqual(r.returncode, 2, bad)

    @unittest.skipUnless(os.path.exists("/usr/bin/python3"), "no system python")
    def test_cli_on_system_python(self):
        r = self.run_cli("resolve", fx.P1[:8], python="/usr/bin/python3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("paseo-agent", r.stdout)


if __name__ == "__main__":
    unittest.main()
