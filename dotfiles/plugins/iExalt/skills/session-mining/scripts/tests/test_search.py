import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from fixtures import run_main, write_jsonl  # noqa: E402
from session_mining.reader import Filter  # noqa: E402
from session_mining.search import Query, codex_live_candidates, grep, rg_pattern, self_sessions  # noqa: E402
from session_mining.stores import PaseoAgent, Roots, codex_files  # noqa: E402

CLI = os.path.join(os.path.dirname(HERE), "sessions.py")
OWNER = "0a0a0a0a-0000-4000-8000-000000000001"
FORK = "0b0b0b0b-0000-4000-8000-000000000002"
T1 = "01a00000-1111-7000-8000-0000000000c1"
T2 = "01a00000-1111-7000-8000-0000000000c2"


def cu(uuid, sid, text, ts):
    return {"type": "user", "uuid": uuid, "sessionId": sid, "timestamp": ts, "entrypoint": "cli",
            "message": {"role": "user", "content": text}}


class Search(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sm-search-")
        self.roots = Roots(*(os.path.join(self.tmp, n) for n in ("claude", "codex", "paseo")))
        p = os.path.join(self.roots.claude, "projects")
        # The owner session and a resumed copy in another project share the first record.
        write_jsonl(os.path.join(p, "-work-alpha", OWNER + ".jsonl"), [
            cu("r1", OWNER, "find the flaky widget test", "2026-01-01T00:00:00Z"),
            {"type": "assistant", "uuid": "a1", "sessionId": OWNER, "timestamp": "2026-01-01T00:00:01Z",
             "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "x"}},
                                     {"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "y"}}]}}])
        write_jsonl(os.path.join(p, "-work-beta", FORK + ".jsonl"), [
            cu("r1", OWNER, "find the flaky widget test", "2026-01-01T00:00:00Z"),
            cu("r2", FORK, "and the \"quoted\" widget\nnext line", "2026-01-03T00:00:00Z")])
        day = os.path.join(self.roots.codex, "sessions", "2026", "01", "02")
        for tid in (T1, T2):
            write_jsonl(os.path.join(day, "rollout-2026-01-02T00-00-00-%s.jsonl" % tid), [
                {"timestamp": "2026-01-02T00:00:00Z", "type": "session_meta",
                 "payload": {"id": tid, "cwd": "/work/gamma", "originator": "codex_cli_rs"}},
                {"timestamp": "2026-01-02T00:00:01Z", "type": "response_item",
                 "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "widget %s" % tid}]}},
                {"timestamp": "2026-01-02T00:00:01Z", "type": "event_msg", "payload": {"type": "item_completed",
                 "item": {"type": "UserMessage", "content": [{"type": "text", "text": "widget %s" % tid}]}}}])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_grep(self, regex="widget", **kw):
        exclude = kw.pop("exclude", {})
        q = Query(regex=regex, flt=Filter(regex=re.compile(regex, re.I), **kw.pop("flt", {})), workers=2, **kw)
        return grep(self.roots, q, [], exclude, include_live=True, cwd=self.tmp)

    def test_dedup_keeps_owner_and_project_filter_runs_after(self):
        res = self.run_grep(providers=("claude",))
        texts = sorted((h["session"], h["text"][:8]) for h in res.hits)
        self.assertEqual(texts, [(OWNER, "find the"), (FORK, "and the ")])
        self.assertEqual(res.dedup_dropped, 1)
        res = self.run_grep(providers=("claude",), project="work/beta")
        self.assertEqual([h["session"] for h in res.hits], [FORK])   # the copy does not stand in for the owner
        self.assertEqual(res.project_dropped, 1)
        res = self.run_grep(regex="Bash|x|y", providers=("claude",), flt={"kinds": ["tool_call"]})
        self.assertEqual(len(res.hits), 2)                           # two calls in one record are distinct

    def test_prefilter_handles_json_escapes(self):
        self.assertEqual(rg_pattern(r'"quoted"\swidget'), r'\\?"quoted\\?"(?:\s|\\[nrt])widget')
        for pat in (r'"quoted" widget', r'widget\snext'):
            res = self.run_grep(regex=pat, providers=("claude",))
            self.assertEqual(res.prefilter_kept, 1, pat)
            self.assertEqual([h["session"] for h in res.hits], [FORK], pat)

    def test_budget_reports_unparsed(self):
        res = self.run_grep(budget=0)
        self.assertEqual(res.parsed, 0)
        self.assertEqual(res.unparsed, res.prefilter_kept)
        self.assertGreater(res.unparsed, 0)

    def test_project_matches_codex_cwd_and_provider(self):
        res = self.run_grep(providers=("codex",), project="gamma")
        self.assertEqual(sorted(h["session"] for h in res.hits), [T1, T2])

    def test_self_exclusion(self):
        agents = [PaseoAgent("p-root", "claude", OWNER, "", "", "", {}),
                  PaseoAgent("p-kid", "codex", T1, "", "", "", {"paseo.parent-agent-id": "p-root"}),
                  PaseoAgent("p-grandkid", "codex", T2, "", "", "", {"paseo.parent-agent-id": "p-kid"}),
                  PaseoAgent("p-other", "claude", FORK, "", "", "", {"paseo.parent-agent-id": ""})]
        got = self_sessions(agents, env={"PASEO_AGENT_ID": "p-root"})
        self.assertEqual(sorted(got), sorted([OWNER, T1, T2]))
        res = self.run_grep(exclude=got)
        self.assertEqual([h["session"] for h in res.hits], [FORK])
        self.assertEqual(self_sessions([], env={"CLAUDE_CODE_SESSION_ID": "abc"}), {"abc": "caller (CLAUDE_CODE_SESSION_ID)"})

    def test_codex_live_candidates(self):
        files = list(codex_files(self.roots))
        now = time.time()
        for f in files:
            f.mtime = now
        self.assertEqual(len(codex_live_candidates(files, "/work/gamma", now)), 2)
        self.assertEqual(len(codex_live_candidates(files[:1], "/work/gamma", now)), 1)
        self.assertEqual(codex_live_candidates(files, "/elsewhere", now), [])
        q = Query(regex="widget", flt=Filter(regex=re.compile("widget")), providers=("codex",), workers=2)
        os.utime(files[0].path, None)
        os.utime(files[1].path, None)
        res = grep(self.roots, q, [], {}, cwd="/work/gamma")
        self.assertEqual(len(res.hits), 2)                          # two live: none excluded
        self.assertEqual(len(res.live_candidates), 2)
        os.utime(files[1].path, (now - 1000, now - 1000))
        res = grep(self.roots, q, [], {}, cwd="/work/gamma")
        self.assertEqual(len(res.hits), 1)                          # exactly one live: it is the caller
        self.assertIn(files[0].session, res.excluded)

    def test_cli_grep_footer_and_cap(self):
        homes = ["--claude-home", self.roots.claude, "--codex-home", self.roots.codex, "--paseo-home", self.roots.paseo]
        r = run_main(["grep", "widget", "--max-bytes", "600", "--include-self", "--no-cache"] + homes)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertLessEqual(len(r.stdout.encode()), 600)
        self.assertIn("# files:", r.stdout)
        r = run_main(["grep", "--author", "human,agent", "--sessions-only", "--include-self", "--no-cache"] + homes)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.count("== "), 4)


if __name__ == "__main__":
    unittest.main()
