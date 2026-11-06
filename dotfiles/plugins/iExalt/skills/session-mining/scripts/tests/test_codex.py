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
from session_mining import codex  # noqa: E402

TID = "01a00000-1111-7000-8000-000000000001"
PARENT = "01a00000-0000-7000-8000-0000000000ff"
TS = "2026-01-02T03:04:05Z"


def meta(tid=TID, **kw):
    p = {"id": tid, "cwd": "/tmp/demo", "originator": "codex_cli_rs"}
    p.update(kw)
    return {"timestamp": TS, "type": "session_meta", "payload": p}


def ri(payload, **kw):
    d = {"timestamp": TS, "type": "response_item", "payload": payload}
    d.update(kw)
    return d


def em(payload):
    return {"timestamp": TS, "type": "event_msg", "payload": payload}


def user(text, id_=None):
    return ri({"type": "message", "role": "user", "id": id_, "content": [{"type": "input_text", "text": text}]})


def twin(text, client=False):
    it = {"type": "UserMessage", "id": "um", "content": [{"type": "text", "text": text}]}
    if client:
        it["client_id"] = "c"
    return em({"type": "item_completed", "item": it})


class CodexEvents(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sm-codex-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def events(self, records, **kw):
        path = os.path.join(self.tmp, "rollout-2026-01-02T03-04-05-%s.jsonl" % TID)
        write_jsonl(path, records)
        return list(codex.iter_events(path, **kw))

    def test_user_text_injected_agent_and_skill(self):
        recs = [
            meta(),
            user("# AGENTS.md instructions for /tmp/demo\nrules"),
            user("<environment_context>cwd</environment_context>"),
            user("Context the harness added without a twin"),
            user("Please fix the flaky test"), twin("Please  fix the flaky test"),
            user('<paseo-system version="1" kind="agent-message" source-agent-id="x">do Y</paseo-system>'),
            user('<paseo-system version="1" kind="agent-notification">agent idle</paseo-system>'),
            user("<skill>\n<name>prose-fix</name>\nbody</skill>"),
            user("<chat-history-summary>earlier</chat-history-summary>"), twin("<chat-history-summary>earlier</chat-history-summary>"),
            ri({"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "dev"}]}),
            ri({"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "done"}]}),
        ]
        got = [(e["author"], e["kind"], e["skill"], e["basis"]) for e in self.events(recs)]
        self.assertEqual(got, [
            ("injected", "prompt", None, "injected_prefix"), ("injected", "prompt", None, "injected_prefix"),
            ("injected", "prompt", None, "no_user_message_twin"), ("human", "prompt", None, "user_message_twin"),
            ("agent", "prompt", None, "paseo_agent-message"), ("harness", "prompt", None, "paseo_agent-notification"),
            ("injected", "prompt", "prose-fix", "injected_prefix"), ("harness", "prompt", None, "automation"),
            ("injected", "prompt", None, "developer_role"),
            ("assistant", "reply", None, None)])

    def test_first_prompt_attribution(self):
        recs = [meta(), user("brief"), twin("brief"), user("later"), twin("later")]
        self.assertEqual([e["author"] for e in self.events(recs, launched="agent")], ["agent", "human"])
        self.assertEqual([e["author"] for e in self.events(recs, launched="human")], ["human", "human"])
        self.assertEqual([e["author"] for e in self.events(recs, launched="schedule")], ["harness", "human"])
        recs[0] = meta(originator="codex_exec")
        self.assertEqual([e["author"] for e in self.events(recs)], ["agent", "agent"])
        recs[0] = meta(source={"subagent": {"thread_spawn": {"parent_thread_id": PARENT}}})
        evs = self.events(recs)
        self.assertEqual([(e["author"], e["basis"]) for e in evs],
                         [("agent", "subagent_first_message"), ("human", "subagent_followup_maybe_agent")])
        recs[0] = meta(originator="Codex Desktop", source={"subagent": {"thread_spawn": {"parent_thread_id": PARENT}}})
        self.assertEqual([e["basis"] for e in self.events(recs)], ["subagent_first_message", "subagent_followup"])
        recs[4] = twin("later", client=True)
        self.assertEqual([e["author"] for e in self.events(recs)], ["agent", "human"])   # typed in the UI

    def test_decisions(self):
        reply = '<send_user_message_question_reply>[{"question": "Which?", "answer": "B"}]' \
                '</send_user_message_question_reply>'
        recs = [meta(), user(reply), twin(reply), user("Answers to your questions:\nWhich? B"),
                em({"type": "turn_aborted", "reason": "interrupted"}),
                em({"type": "turn_aborted", "reason": "replaced"}),
                {"timestamp": TS, "type": "retained_context",
                 "payload": {"type": "verified_answer", "questions": [{"question": "Q", "answer": "A"}]}}]
        evs = self.events(recs)
        self.assertEqual([(e["author"], e["kind"]) for e in evs], [("human", "decision")] * 4)
        self.assertIn("Which? -> B", evs[0]["text"])

    def test_tools_and_prose(self):
        script = 'const r = await tools.exec_command({cmd: "rg -l \\\\d foo", yield_time_ms: 1000});'
        recs = [
            meta(),
            ri({"type": "function_call", "name": "exec_command", "call_id": "c1",
                "arguments": json.dumps({"cmd": "ls -la"})}),
            ri({"type": "function_call_output", "call_id": "c1", "output": "total 0"}),
            ri({"type": "custom_tool_call", "name": "exec", "call_id": "c2", "input": script}),
            ri({"type": "custom_tool_call_output", "call_id": "c2", "output": "x" * 70000}),
            ri({"type": "reasoning", "summary": [{"type": "summary_text", "text": "thinking"}]}),
            # The real order: call, its output, then a CommandExecution item repeating it.
            ri({"type": "function_call", "name": "exec_command", "call_id": "c3", "arguments": "{}"}),
            ri({"type": "function_call_output", "call_id": "c3", "output": "dup"}),
            em({"type": "item_completed", "item": {"type": "CommandExecution", "command": ["zsh", "-lc", "ls"],
                                                    "aggregated_output": "dup", "exit_code": 0}}),
            {"timestamp": TS, "type": "event_msg", "payload": {"type": "token_count"}},
        ]
        full = self.events(recs)
        self.assertEqual([(e["kind"], e["tool"]) for e in full], [
            ("tool_call", "exec_command"), ("tool_result", "exec_command"), ("tool_call", "exec_command"),
            ("tool_result", "exec_command"), ("thinking", None), ("tool_call", "exec_command"),
            ("tool_result", "exec_command")])                    # one result per command
        self.assertEqual(full[0]["command"], "ls -la")
        self.assertIn("rg -l", full[2]["command"])         # invalid JSON escape tolerated
        prose = self.events(recs, prose=True)
        self.assertEqual([e["kind"] for e in prose], ["tool_call", "tool_call", "tool_call"])

    def test_fork_inherited_records_skipped(self):
        recs = [meta(forked_from_id=PARENT), meta(PARENT),
                user("parent prompt"), twin("parent prompt"),
                em({"type": "thread_settings_applied"}),
                user("my own prompt"), twin("my own prompt"),
                ri({"type": "message", "role": "user", "content": [{"type": "input_text", "text": "inh"}]},
                   metadata={"inherited_user_message": True})]
        stats = {}
        evs = self.events(recs, stats=stats)
        self.assertEqual([e["text"] for e in evs], ["my own prompt"])
        self.assertEqual(stats["inherited_skipped"], 3)      # parent prompt, its twin, the settings line
        self.assertEqual(evs[0]["line"], 6)

    def test_guardian_skipped_and_orphan_and_partial(self):
        stats = {}
        self.assertEqual(self.events([meta(source={"subagent": {"other": "guardian"}}), user("x")], stats=stats), [])
        self.assertEqual(stats, {"guardian_skipped": 1})
        self.assertEqual(len(self.events([meta(source={"subagent": {"other": "guardian"}}), user("x"), twin("x")],
                                         include_guardian=True)), 1)
        stats = {}
        evs = self.events([meta(), twin("typed with no response item"), '{"timestamp":"x","type":"resp'],
                          stats=stats)
        self.assertEqual([(e["author"], e["basis"]) for e in evs], [("human", "user_message_without_response_item")])
        self.assertEqual(stats["unparsable"], 1)


if __name__ == "__main__":
    unittest.main()
