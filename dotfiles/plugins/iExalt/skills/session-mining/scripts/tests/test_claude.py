import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from fixtures import write_jsonl  # noqa: E402
from session_mining import claude  # noqa: E402
from session_mining.events import PROSE_SKIP_BYTES  # noqa: E402
from session_mining.reader import Filter, skill_matches  # noqa: E402

SID = "c1c1c1c1-0000-4000-8000-000000000001"


def u(uuid, content, **kw):
    d = {"type": "user", "uuid": uuid, "sessionId": SID, "timestamp": "2026-01-02T03:04:%02dZ" % (len(uuid) % 60),
         "message": {"role": "user", "content": content}}
    d.update(kw)
    return d


def a(uuid, blocks):
    return {"type": "assistant", "uuid": uuid, "sessionId": SID, "timestamp": "2026-01-02T03:05:00Z",
            "message": {"role": "assistant", "content": blocks}}


def result(uuid, call_id, text, is_error=False, tur=None):
    d = u(uuid, [{"type": "tool_result", "tool_use_id": call_id, "content": text, "is_error": is_error}])
    if tur is not None:
        d["toolUseResult"] = tur
    return d


class ClaudeEvents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sm-claude-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def events(self, records, name=SID + ".jsonl", sub=False, **kw):
        path = os.path.join(self.tmp, "proj", SID, "subagents", name) if sub else os.path.join(self.tmp, "proj", name)
        write_jsonl(path, records)
        return list(claude.iter_events(path, **kw))

    def test_authors_by_rule(self):
        recs = [
            {"type": "file-history-snapshot", "uuid": "skip"},
            u("u1", "first prompt typed by me", entrypoint="cli"),
            a("a1", [{"type": "text", "text": "ok"}]),
            u("u2", "<command-name>/iExalt:phone-debug</command-name><command-args>x</command-args>"),
            u("u3", "Base directory for this skill: /x\n# Phone Debug"),
            u("u4", '<paseo-system version="1" kind="agent-message" source-agent-id="x">hi</paseo-system>'),
            u("u5", "<task-notification>done</task-notification>"),
            u("u6", "[Request interrupted by user]"),
            u("u7", "summary", isCompactSummary=True),
            u("u8", "<command-name>/compact</command-name>"),
            u("u9", "typed later", origin={"kind": "human"}),
            u("u10", "from a peer", origin={"kind": "peer"}),
        ]
        got = [(e["uuid"], e["author"], e["kind"], e["skill"]) for e in self.events(recs)]
        self.assertEqual(got, [
            ("u1", "human", "prompt", None), ("a1", "assistant", "reply", None),
            ("u2", "human", "prompt", "iExalt:phone-debug"), ("u3", "injected", "prompt", None),
            ("u4", "agent", "prompt", None), ("u5", "harness", "prompt", None), ("u6", "harness", "prompt", None),
            ("u7", "harness", "prompt", None), ("u8", "human", "prompt", None), ("u9", "human", "prompt", None),
            ("u10", "agent", "prompt", None)])

    def test_subagent_prompt_is_agent(self):
        evs = self.events([u("s1", "Load the skill and review X")], name="agent-abc.jsonl", sub=True)
        self.assertEqual((evs[0]["author"], evs[0]["session"]), ("agent", "abc"))

    def test_launched_first_prompt_is_agent_but_later_prompts_are_human(self):
        recs = [u("l1", "brief from overseer", entrypoint="sdk-cli", promptSource="sdk"),
                a("l2", [{"type": "text", "text": "ok"}]),
                u("l3", "follow-up typed by me", entrypoint="sdk-cli", promptSource="sdk")]
        self.assertEqual([e["author"] for e in self.events(recs, launched=True)], ["agent", "assistant", "human"])
        self.assertEqual([e["author"] for e in self.events(recs, launched=False)], ["human", "assistant", "human"])
        self.assertEqual([e["basis"] for e in self.events(recs, launched=None)][0],
                         "sdk_first_prompt_without_paseo_record")

    def test_tool_calls_skills_and_decisions(self):
        recs = [
            a("t1", [{"type": "tool_use", "id": "c1", "name": "Bash", "input": {"command": "rg -l foo"}},
                     {"type": "tool_use", "id": "c2", "name": "Skill", "input": {"skill": "iExalt:prose-fix"}},
                     {"type": "tool_use", "id": "c3", "name": "AskUserQuestion", "input": {"questions": []}},
                     {"type": "tool_use", "id": "c4", "name": "ExitPlanMode", "input": {}},
                     {"type": "tool_use", "id": "c5", "name": "Bash", "input": {"command": "rm -rf x"}}]),
            result("r1", "c1", "a.txt"),
            result("r3", "c3", "User answered", tur={"answers": {"Which?": "Option B"}}),
            result("r4", "c4", "User has approved your plan."),
            result("r5", "c5", "The user doesn't want to proceed with this tool use.", is_error=True),
        ]
        evs = self.events(recs)
        calls = [e for e in evs if e["kind"] == "tool_call"]
        self.assertEqual(calls[0]["command"], "rg -l foo")
        self.assertEqual(calls[1]["skill"], "iExalt:prose-fix")
        dec = [(e["tool"], e["author"], e["text"]) for e in evs if e["kind"] == "decision"]
        self.assertEqual([d[0] for d in dec], ["AskUserQuestion", "ExitPlanMode", "Bash"])
        self.assertTrue(all(d[1] == "human" for d in dec))
        self.assertIn("Which? -> Option B", dec[0][2])
        self.assertEqual([e["tool"] for e in evs if e["kind"] == "tool_result"], ["Bash"])

    def test_prose_mode_skips_big_tool_output_but_keeps_decisions(self):
        big = "x" * (PROSE_SKIP_BYTES + 10)
        recs = [a("p1", [{"type": "tool_use", "id": "c1", "name": "Read", "input": {"file_path": "/f"}},
                         {"type": "tool_use", "id": "c2", "name": "Bash", "input": {"command": "x"}}]),
                result("p2", "c1", big),
                result("p3", "c2", "The user doesn't want to proceed", is_error=True)]
        stats = {}
        evs = self.events(recs, prose=True, stats=stats)
        self.assertEqual([e["kind"] for e in evs], ["tool_call", "tool_call", "decision"])
        self.assertEqual(stats.get("skipped_tool_output"), 1)

    def test_replay_dedup_partial_line_and_attachments(self):
        recs = [u("d1", "hello"), u("d1", "hello"),
                {"type": "attachment", "uuid": "q1", "attachment": {"type": "queued_command", "prompt": "queued msg"}},
                {"type": "attachment", "uuid": "i1", "attachment": {"type": "instructions",
                                                                     "files": [{"type": "Project", "path": "/AGENTS.md",
                                                                                "content": "rules"}]}},
                {"type": "attachment", "uuid": "e1", "attachment": {"type": "environment"}},
                {"type": "system", "uuid": "k1", "subtype": "compact_boundary"},
                '{"type":"user","uuid":"partial']
        stats = {}
        evs = self.events(recs, stats=stats)
        self.assertEqual([(e["uuid"], e["author"], e["kind"]) for e in evs],
                         [("d1", "human", "prompt"), ("q1", "human", "prompt"), ("i1", "injected", "prompt"),
                          ("k1", "harness", "compaction")])
        self.assertEqual(stats.get("unparsable"), 1)
        self.assertEqual(evs[0]["line"], 1)
        self.assertEqual(evs[1]["line"], 3)

    def test_owner_rank(self):
        own = os.path.join("p", SID + ".jsonl")
        fork = os.path.join("q", "ffff.jsonl")
        sub = os.path.join("p", SID, "subagents", "agent-x.jsonl")
        self.assertLess(claude.owner_rank(own, SID, "2026-01-02"), claude.owner_rank(fork, SID, "2026-01-01"))
        self.assertEqual(claude.owner_rank(sub, SID, None)[0], 0)
        self.assertLess(claude.owner_rank(fork, "z", "2026-01-01"), claude.owner_rank(own, "z", "2026-01-02"))

    def test_filter_and_skill_matching(self):
        self.assertTrue(skill_matches("iExalt:phone-debug", "phone-debug"))
        self.assertTrue(skill_matches("/phone-debug", "iExalt:phone-debug"))
        self.assertFalse(skill_matches("phone-debugger", "phone-debug"))
        e = {"author": "human", "kind": "prompt", "tool": None, "skill": None, "ts": "2026-01-02T00:00:00Z",
             "text": "Find the PHONE logs", "command": None}
        self.assertTrue(Filter(authors=["human"], regex="phone", since="2026-01-01")(e))
        self.assertFalse(Filter(until="2026-01-01")(e))
        self.assertFalse(Filter(kinds=["reply"])(e))


if __name__ == "__main__":
    unittest.main()
