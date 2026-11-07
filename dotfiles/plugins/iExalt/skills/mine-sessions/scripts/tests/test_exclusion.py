"""Caller ancestry is independent of cache age, provider filters and launcher type."""
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(HERE), HERE]

import sessions
from fixtures import run_main, write_jsonl
from session_mining.cache import Cache
from session_mining.reader import Filter
from session_mining.resolve import Inventory
from session_mining.search import Query, caller_exclusions, grep
from session_mining.stores import Roots, claude_files, codex_files

ROOT = "11111111-0000-4000-8000-000000000001"
CHILD = "22222222-0000-4000-8000-000000000002"
GRANDCHILD = "33333333-0000-4000-8000-000000000003"
OTHER = "44444444-0000-4000-8000-000000000004"
CLAUDE_CHILD = "worker"
CLAUDE_GRANDCHILD = "nested-worker"


class CallerExclusion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sm-exclusion-")
        self.roots = Roots(*(os.path.join(self.tmp, n) for n in ("claude", "codex", "paseo")))
        self.cache = Cache(os.path.join(self.tmp, "index.sqlite"))
        os.makedirs(self.roots.codex)
        self.db = sqlite3.connect(os.path.join(self.roots.codex, "state_5.sqlite"))
        self.db.executescript("create table threads (id text); create table thread_spawn_edges "
                              "(parent_thread_id text, child_thread_id text);")
        self.write_claude(ROOT)
        self.write_codex(OTHER)
        self.agent("caller", "claude", ROOT)
        self.env = patch.dict(os.environ, {"PASEO_AGENT_ID": "caller", "CLAUDE_CODE_SESSION_ID": ""})
        self.env.start()
        self.inv = Inventory(self.roots)
        self.cache.refresh(self.files(), {})

    def tearDown(self):
        self.env.stop()
        self.inv.db.close()
        self.db.close()
        self.cache.con.close()
        shutil.rmtree(self.tmp)

    def files(self):
        return list(claude_files(self.roots)) + list(codex_files(self.roots))

    def write_claude(self, sid, parent=None):
        parts = [self.roots.claude, "projects", "-demo"]
        parts += [parent, "subagents", "agent-" + sid + ".jsonl"] if parent else [sid + ".jsonl"]
        write_jsonl(os.path.join(*parts), [{"type": "user", "uuid": sid, "sessionId": parent or sid,
                     "timestamp": "2026-01-01T00:00:00Z", "entrypoint": "cli",
                     "message": {"role": "user", "content": "research " + sid}}])

    def write_codex(self, sid):
        write_jsonl(os.path.join(self.roots.codex, "sessions", "rollout-2026-01-01T00-00-00-" + sid + ".jsonl"), [
            {"type": "session_meta", "payload": {"id": sid, "cwd": "/demo"}},
            {"type": "response_item", "timestamp": "2026-01-01T00:00:00Z",
             "payload": {"type": "message", "role": "user",
                         "content": [{"type": "input_text", "text": "research " + sid}]}},
            {"type": "event_msg", "timestamp": "2026-01-01T00:00:00Z",
             "payload": {"type": "item_completed", "item": {"type": "UserMessage",
                         "content": [{"type": "text", "text": "research " + sid}]}}}])

    def agent(self, aid, provider, sid, parent=""):
        directory = os.path.join(self.roots.paseo, "agents", "demo")
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, aid + ".json"), "w") as fh:
            json.dump({"id": aid, "provider": provider, "persistence": {"sessionId": sid},
                       "labels": {"paseo.parent-agent-id": parent}}, fh)

    def add_descendants(self):
        # Added after both the inventory and prose cache were built.
        self.agent("native-worker", "claude", CLAUDE_CHILD)
        self.agent("launcher", "codex", None, "native-worker")
        self.agent("child", "codex", CHILD, "launcher")
        self.write_codex(CHILD)
        self.write_codex(GRANDCHILD)
        self.db.execute("insert into thread_spawn_edges values (?,?)", (CHILD, GRANDCHILD))
        self.db.commit()
        self.write_claude(CLAUDE_CHILD, ROOT)
        self.write_claude(CLAUDE_GRANDCHILD, CLAUDE_CHILD)

    def test_late_descendants_excluded_from_cached_and_direct_grep(self):
        self.add_descendants()
        query = Query(regex="research", flt=Filter(regex=re.compile("research")), workers=2)
        for cache in (None, self.cache):
            with self.subTest(cached=cache is not None):
                result = grep(self.roots, query, self.inv.paseo, {}, cache=cache, inventory=self.inv)
                self.assertEqual({h["session"] for h in result.hits}, {OTHER})
                self.assertTrue({ROOT, CHILD, GRANDCHILD, CLAUDE_CHILD, CLAUDE_GRANDCHILD} <= set(result.excluded))
                self.assertFalse(result.failures)
        # A provider filter must not hide the Claude caller that identifies its Codex descendants.
        query.providers = ("codex",)
        result = grep(self.roots, query, [], {}, cache=self.cache, inventory=self.inv)
        self.assertEqual({h["session"] for h in result.hits}, {OTHER})

    def test_find_and_manifest_refresh_after_inventory_and_cache(self):
        original = sessions._open_cache
        added = False

        def open_cache(*args, **kwargs):
            nonlocal added
            if not added:
                self.add_descendants()
                added = True
            return original(*args, **kwargs)

        homes = ["--claude-home", self.roots.claude, "--codex-home", self.roots.codex,
                 "--paseo-home", self.roots.paseo, "--cache", self.cache.path]
        with patch.object(sessions, "_open_cache", open_cache):
            for command in ("find", "manifest"):
                with self.subTest(command=command):
                    result = run_main([command, "research", *homes])
                    self.assertEqual(result.returncode, 0, result.stderr)
                    body = "\n".join(line for line in result.stdout.splitlines() if not line.startswith("#"))
                    self.assertIn(OTHER, body)
                    for sid in (ROOT, CHILD, GRANDCHILD, CLAUDE_CHILD, CLAUDE_GRANDCHILD):
                        self.assertNotIn(sid, body)

    def test_include_self_and_explicit_exclusion_are_independent(self):
        self.add_descendants()
        files = self.files()
        excluded, _ = caller_exclusions(self.inv, files, {}, include_self=True)
        self.assertEqual(excluded, {})
        excluded, _ = caller_exclusions(self.inv, files, {ROOT: "explicit"}, include_self=True)
        self.assertEqual(set(excluded), {ROOT, CHILD, GRANDCHILD, CLAUDE_CHILD, CLAUDE_GRANDCHILD})
        self.assertEqual(excluded[ROOT], "explicit")

    def test_live_codex_root_expands_native_descendants(self):
        self.add_descendants()
        with patch.dict(os.environ, {"PASEO_AGENT_ID": "", "CLAUDE_CODE_SESSION_ID": ""}):
            files = self.files()
            now = time.time()
            for f in files:
                if f.session != CHILD:
                    f.mtime = now - 1000
            excluded, candidates = caller_exclusions(self.inv, files, {}, cwd="/demo", now=now)
            self.assertEqual(set(excluded), {CHILD, GRANDCHILD})
            self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
