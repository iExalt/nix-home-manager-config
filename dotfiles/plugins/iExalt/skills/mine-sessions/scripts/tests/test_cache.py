import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from fixtures import run_main, write_jsonl  # noqa: E402
from session_mining.cache import Cache, session_rows  # noqa: E402
from session_mining.reader import Filter  # noqa: E402
from session_mining.search import Query, grep  # noqa: E402
from session_mining.stores import Roots, claude_files, codex_files  # noqa: E402

CLI = os.path.join(os.path.dirname(HERE), "sessions.py")
OWNER = "0a0a0a0a-0000-4000-8000-000000000001"
FORK = "0b0b0b0b-0000-4000-8000-000000000002"


def cu(uuid, sid, text, ts, **kw):
    d = {"type": "user", "uuid": uuid, "sessionId": sid, "timestamp": ts, "entrypoint": "cli",
         "message": {"role": "user", "content": text}}
    d.update(kw)
    return d


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sm-cache-")
        self.roots = Roots(*(os.path.join(self.tmp, n) for n in ("claude", "codex", "paseo")))
        self.proj = os.path.join(self.roots.claude, "projects", "-work-alpha")
        self.owner = os.path.join(self.proj, OWNER + ".jsonl")
        write_jsonl(self.owner, [
            cu("r1", OWNER, "find the flaky widget test", "2026-01-01T00:00:00Z"),
            cu("r2", OWNER, "<command-name>/iExalt:phone-debug</command-name>", "2026-01-01T00:01:00Z"),
            {"type": "assistant", "uuid": "a1", "sessionId": OWNER, "timestamp": "2026-01-01T00:02:00Z",
             "message": {"content": [{"type": "tool_use", "id": "t1", "name": "Bash",
                                      "input": {"command": "rg -l " + "x" * 3000}}]}},
            {"type": "attachment", "uuid": "i1", "sessionId": OWNER,
             "attachment": {"type": "invoked_skills", "skills": [{"name": "s", "content": "y" * 5000}]}}])
        self.cache = Cache(os.path.join(self.tmp, "cache", "index.sqlite"))

    def tearDown(self):
        self.cache.con.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def files(self):
        return list(claude_files(self.roots)) + list(codex_files(self.roots))

    def hits(self, regex, **kw):
        q = Query(regex=regex, flt=Filter(regex=re.compile(regex, re.I), **kw), workers=2)
        return grep(self.roots, q, [], {}, include_live=True, cwd=self.tmp, cache=self.cache)

    def test_incremental_refresh_and_caps(self):
        self.assertEqual(self.cache.refresh(self.files(), {}), [])
        rows = dict(self.cache.con.execute("select kind || '/' || author, length(text) from events"))
        self.assertGreater(rows["tool_call/assistant"], 3000)        # commands kept whole
        self.assertEqual(rows["prompt/injected"], 300)               # injected text kept only as a stub
        self.assertEqual(self.cache.stale(self.files()), ([], []))
        write_jsonl(self.owner, [cu("r1", OWNER, "find the flaky widget test", "2026-01-01T00:00:00Z"),
                                 cu("r3", OWNER, "a changed file", "2026-01-01T00:05:00Z")])
        self.assertEqual(len(self.cache.stale(self.files())[0]), 1)
        self.cache.refresh(self.files(), {})
        texts = [r[0] for r in self.cache.con.execute("select text from events order by line")]
        self.assertEqual(texts, ["find the flaky widget test", "a changed file"])   # old rows replaced
        os.remove(self.owner)
        self.cache.refresh(self.files(), {})
        self.assertEqual(self.cache.status()["files"], 0)            # deleted file dropped

    def test_new_fork_after_build_and_owner_deletion(self):
        self.cache.refresh(self.files(), {})
        fork = os.path.join(self.roots.claude, "projects", "-work-beta", FORK + ".jsonl")
        write_jsonl(fork, [cu("r1", OWNER, "find the flaky widget test", "2026-01-01T00:00:00Z"),
                           cu("r9", FORK, "widget follow-up", "2026-01-02T00:00:00Z")])
        res = self.hits("widget")
        self.assertEqual(sorted((h["session"], h["text"][:6]) for h in res.hits),
                         [(OWNER, "find t"), (FORK, "widget")])          # the copy is deduped to the owner
        self.assertEqual(res.dedup_dropped, 1)
        self.assertEqual(res.cache_used, 2)
        os.remove(self.owner)
        res = self.hits("widget")
        self.assertEqual(sorted(h["session"] for h in res.hits), [FORK, FORK])   # the copy now stands alone

    def test_cache_and_direct_reads_agree(self):
        self.cache.refresh(self.files(), {})
        q = lambda cache: grep(self.roots, Query(regex="widget|rg", flt=Filter(regex=re.compile("widget|rg", re.I)),
                                                 workers=2), [], {}, include_live=True, cwd=self.tmp, cache=cache)
        key = lambda r: sorted((h["file"], h["line"], h["kind"], h["author"]) for h in r.hits)
        self.assertEqual(key(q(self.cache)), key(q(None)))

    def test_budget_leaves_stale_files_to_direct_reads(self):
        self.assertEqual(len(self.cache.refresh(self.files(), {}, deadline=0)), 1)
        res = self.hits("widget")
        self.assertEqual(len(res.hits), 1)

    def test_text_past_the_cap_is_read_directly(self):
        from session_mining import cache as cache_mod
        write_jsonl(self.owner, [{"type": "assistant", "uuid": "big", "sessionId": OWNER,
                                  "timestamp": "2026-01-01T00:00:00Z",
                                  "message": {"content": [{"type": "text",
                                                           "text": "x " * cache_mod.CAP + "needle at the end"}]}}])
        self.cache.refresh(self.files(), {})
        self.assertEqual(self.cache.con.execute("select sum(truncated) from events").fetchone()[0], 1)
        res = self.hits("needle")
        self.assertEqual(len(res.hits), 1)
        self.assertEqual(res.cache_truncated, 1)
        self.assertEqual(res.parsed, 1)

    def test_concurrent_refreshes_do_not_collide(self):
        other = Cache(self.cache.path)
        from session_mining.cache import _Lock
        held = _Lock(self.cache.path + ".lock")
        self.assertTrue(held.acquire(None))
        self.assertEqual(len(other.refresh(self.files(), {}, deadline=__import__("time").time() + 0.3)), 1)
        held.release()                                              # waited, gave up, reported stale
        self.assertEqual(other.refresh(self.files(), {}), [])
        self.assertEqual(self.cache.refresh(self.files(), {}), [])  # the second writer sees the first's rows
        self.assertEqual(self.cache.status()["files"], 1)
        other.con.close()

    def test_older_cache_shape_is_rebuilt(self):
        import sqlite3
        path = os.path.join(self.tmp, "old", "index.sqlite")
        os.makedirs(os.path.dirname(path))
        con = sqlite3.connect(path)
        con.executescript("create table meta (key text primary key, value text); insert into meta values "
                          "('version', '1'); create table files (id integer primary key, path text unique); "
                          "create table events (file_id integer, text text);")
        con.commit()
        con.close()
        c = Cache(path)
        self.assertEqual(c.refresh(self.files(), {}), [])
        self.assertGreater(c.status()["events"], 0)
        c.con.close()

    def test_session_rows(self):
        self.cache.refresh(self.files(), {})
        rows = session_rows(self.cache)
        self.assertEqual([(r["session"], r["project"]) for r in rows], [(OWNER, "-work-alpha")])

    def test_cli_find_manifest_recall(self):
        homes = ["--claude-home", self.roots.claude, "--codex-home", self.roots.codex, "--paseo-home",
                 self.roots.paseo, "--include-self", "--cache", self.cache.path]
        run = lambda *a: run_main(a)
        r = run("find", "flaky", *homes)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(OWNER, r.stdout)
        r = run("find", "--skill", "phone-debug", *homes)
        self.assertIn("1 matched", r.stdout)
        out = os.path.join(self.tmp, "m.tsv")
        r = run("manifest", "--shards", "2", "--out", out, *homes)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out) as fh:
            self.assertEqual(len(fh.read().splitlines()), 2)        # header + one session
        r = run("recall", "--session", OWNER, "--claude-home", self.roots.claude, "--codex-home", self.roots.codex,
                "--paseo-home", self.roots.paseo)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("find the flaky widget test", r.stdout)
        self.assertIn("skill:iExalt:phone-debug", r.stdout)


if __name__ == "__main__":
    unittest.main()
