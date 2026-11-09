#!/usr/bin/env python3
"""Exercise the unbacked-yield Stop guard against synthetic Codex rollouts and its hook I/O contract.

Rollout lines are synthetic; they mirror the record shapes of real rollouts (collaboration function
calls, `agent_message` items with a `Message Type:` header), not any real session.
"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "dotfiles/hooks/unbacked-yield-guard.py"
SPEC = importlib.util.spec_from_file_location("guard", SCRIPT)
GUARD = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(GUARD)


class Rollout:
    def __init__(self, **meta):
        self.own = meta.get("agent_path", "/root")
        self.lines = []
        self.add("session_meta", meta)

    def add(self, kind, payload):
        self.lines.append(json.dumps({"ordinal": len(self.lines), "type": kind, "payload": payload}))
        return self

    def call(self, name, namespace="collaboration", **args):
        cid = f"call{len(self.lines)}"
        return self.add("response_item", {"type": "function_call", "namespace": namespace, "name": name,
                                          "arguments": json.dumps(args), "call_id": cid}), cid

    def spawn(self, agent):
        return self.call("spawn_agent", task_name=agent, message="x")[0]

    def followup(self, agent):
        return self.call("followup_task", target=agent, message="x")[0]

    def message(self, agent, kind="FINAL_ANSWER"):
        head = f"Message Type: {kind}\nTask name: /root\nSender: /root/{agent}\nPayload:\n"
        return self.add("response_item", {"type": "agent_message", "author": f"{self.own}/{agent}", "recipient": "/root",
                                          "content": [{"type": "input_text", "text": head},
                                                      {"type": "encrypted_content", "encrypted_content": "x"}]})

    def shell(self, command):
        return self.add("response_item", {"type": "function_call", "name": "exec_command",
                                          "arguments": json.dumps({"cmd": command}), "call_id": "sh"})

    def output(self, cid, text):
        return self.add("response_item", {"type": "function_call_output", "call_id": cid, "output": text})

    def run(self, **event):
        raw = [line.encode() for line in self.lines]
        return GUARD.decide(event, raw)


class DecisionTests(unittest.TestCase):
    def blocked(self, result, *names):
        self.assertEqual(result["decision"], "block")
        for name in names:
            self.assertIn(name, result["reason"])

    def test_failure_case_is_blocked(self):
        r = Rollout().spawn("a").message("a").followup("a").spawn("b").followup("b")
        r.call("list_agents")
        self.blocked(r.run(), "a", "b")

    def test_finished_agents_allow(self):
        r = Rollout().spawn("a").spawn("b").message("a").message("b")
        self.assertIsNone(r.run())

    def test_intermediate_messages_do_not_finish_an_agent(self):
        self.blocked(Rollout().spawn("a").message("a", "MESSAGE").run(), "a")

    def test_followup_after_final_answer_is_outstanding_again(self):
        self.blocked(Rollout().spawn("a").message("a").followup("a").run(), "a")

    def test_full_path_target_matches_child(self):
        r = Rollout().call("followup_task", target="/root/a", message="x")[0].message("a")
        self.assertIsNone(r.run())

    def test_only_direct_children_count(self):
        sibling = Rollout(agent_path="/root/p").call("followup_task", target="/root/q", message="x")[0]
        self.assertIsNone(sibling.run())
        self.blocked(Rollout(agent_path="/root/p").spawn("r").run(), "r")
        # same short name under another parent must not clear this child's FINAL_ANSWER wait
        r = Rollout(agent_path="/root/p").spawn("r").message("r")
        r.add("response_item", {"type": "agent_message", "author": "/root/p/r/r", "recipient": "/root/p/r",
                                "content": [{"type": "input_text", "text": "Message Type: FINAL_ANSWER\n"}]})
        self.assertIsNone(r.run())

    def test_send_message_does_not_start_work(self):
        r = Rollout().spawn("a").message("a").call("send_message", target="a", message="x")[0]
        self.assertIsNone(r.run())

    def test_close_and_interrupt_end_work(self):
        self.assertIsNone(Rollout().spawn("a").call("close_agent", target="a")[0].run())
        self.assertIsNone(Rollout().spawn("a").call("interrupt_agent", target="a")[0].run())

    def test_failed_spawn_is_not_outstanding(self):
        r = Rollout()
        _, cid = r.call("spawn_agent", task_name="a", message="x")
        self.assertIsNone(r.output(cid, "aborted before dispatch").run())

    def test_heartbeat_after_last_start_allows(self):
        r = Rollout().spawn("a").shell("paseo heartbeat create --json --cron '*/5 * * * *' x")
        self.assertIsNone(r.run())

    def test_heartbeat_before_a_new_spawn_does_not_cover_it(self):
        r = Rollout().shell("paseo heartbeat create x").spawn("a")
        self.blocked(r.run(), "a")

    def test_stop_hook_active_never_blocks(self):
        self.assertIsNone(Rollout().spawn("a").run(stop_hook_active=True))

    def test_forked_parent_history_is_ignored(self):
        r = Rollout(subagent_history_start_ordinal=3).spawn("a")  # ordinals 1-2 are inherited
        r.add("event_msg", {"type": "task_started"})
        self.assertIsNone(r.run())
        self.blocked(Rollout(subagent_history_start_ordinal=1).spawn("a").run(), "a")

    def test_reason_offers_heartbeat_only_under_paseo(self):
        r = Rollout().spawn("a")
        old = os.environ.pop("PASEO_AGENT_ID", None)
        try:
            self.assertNotIn("heartbeat", r.run()["reason"])
            os.environ["PASEO_AGENT_ID"] = "x"
            self.assertIn("paseo heartbeat create", r.run()["reason"])
        finally:
            os.environ.pop("PASEO_AGENT_ID", None)
            if old is not None:
                os.environ["PASEO_AGENT_ID"] = old

    def test_non_codex_transcripts_allow(self):
        claude = [json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Agent", "input": {"run_in_background": True}}]}}).encode()]
        self.assertIsNone(GUARD.decide({}, claude))


class HookContractTests(unittest.TestCase):
    def invoke(self, stdin, path=None):
        env = dict(os.environ)
        env.pop("PASEO_AGENT_ID", None)
        return subprocess.run([sys.executable, "-I", "-S", str(SCRIPT)], input=stdin, text=True,
                              capture_output=True, env=env, check=False)

    def test_block_output_and_fail_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout.jsonl"
            path.write_text("\n".join(Rollout().spawn("a").lines) + "\n")
            result = self.invoke(json.dumps({"transcript_path": str(path), "stop_hook_active": False}))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")
            path.write_text("not json\n{broken\n")
            for stdin in (json.dumps({"transcript_path": str(path)}), json.dumps({"transcript_path": "/nonexistent"}),
                          "{}", "", "[1]", "garbage"):
                with self.subTest(stdin=stdin):
                    result = self.invoke(stdin)
                    self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_large_rollout_is_fast(self):
        filler = json.dumps({"type": "response_item", "payload": {"type": "function_call_output", "call_id": "z",
                                                                      "output": "y" * 2000}})
        rollout = Rollout().spawn("a")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout.jsonl"
            path.write_text("\n".join(rollout.lines[:1] + [filler] * 10000 + rollout.lines[1:]) + "\n")
            started = time.monotonic()
            result = self.invoke(json.dumps({"transcript_path": str(path)}))
            elapsed = time.monotonic() - started
        self.assertIn("block", result.stdout)
        self.assertLess(elapsed, 0.5, "20 MB rollout; interpreter start included (target ~0.1 s)")


if __name__ == "__main__":
    unittest.main()
