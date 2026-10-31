import json
import os
import tempfile
import unittest
from unittest import mock

import ask_options_explained as hook


def claude_user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def claude_text(text):
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def claude_thinking(text):
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "thinking", "thinking": text}]}}


def claude_call(tool_use_id, tool_input):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "id": tool_use_id, "name": "AskUserQuestion", "input": tool_input}]}}


def claude_tool_result():
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "x", "content": "ok"}]}}


def codex_event(kind):
    return {"type": "event_msg", "payload": {"type": kind}}


def codex_text(text):
    return {"type": "response_item", "payload": {"type": "message", "role": "assistant",
                                                 "content": [{"type": "output_text", "text": text}]}}


def codex_call(call_id, name):
    return {"type": "response_item", "payload": {"type": "function_call", "call_id": call_id, "name": name}}


CLAUDE_INPUT = {"questions": [{"question": "Which approach?", "options": [
    {"label": "Rebase (Recommended)", "description": "Linear history."},
    {"label": "Merge", "description": "Keeps history."}]}]}


class DecideTest(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)

    def run_hook(self, tool_name, tool_input, records, tool_use_id="t1", write=True):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.jsonl")
            if write:
                with open(path, "w") as handle:
                    handle.writelines(json.dumps(r) + "\n" for r in records)
            event = {"tool_name": tool_name, "tool_input": tool_input,
                     "transcript_path": path, "tool_use_id": tool_use_id}
            return hook.decide(event, wait_s=0)

    def test_claude_allows_when_every_label_is_explained(self):
        records = [claude_user("fix it"), claude_text("**Rebase** keeps history linear; *merge* is safer."),
                   claude_call("t1", CLAUDE_INPUT)]
        self.assertIsNone(self.run_hook("AskUserQuestion", CLAUDE_INPUT, records))

    def test_claude_denies_and_names_unexplained_labels(self):
        records = [claude_user("fix it"), claude_text("Rebase keeps history linear."), claude_call("t1", CLAUDE_INPUT)]
        reason = self.run_hook("AskUserQuestion", CLAUDE_INPUT, records)
        self.assertIn('"Merge"', reason)
        self.assertNotIn("Rebase (Recommended)", reason)

    def test_retry_explained_only_in_thinking_is_denied_with_a_pointer(self):
        # Session 1a97f603: after a denial the agent "explained" the options in thinking and retried.
        records = [claude_user("fix it"), claude_thinking("Rebase or merge? Plan the reply."),
                   claude_text("Rebase keeps history linear."), claude_call("t0", CLAUDE_INPUT),
                   claude_tool_result(), claude_thinking("Merge keeps every commit; rebase is linear."),
                   claude_call("t1", CLAUDE_INPUT)]
        reason = self.run_hook("AskUserQuestion", CLAUDE_INPUT, records)
        self.assertIn('"Merge" (question "Which approach?")', reason)
        self.assertIn("thinking is hidden", reason)
        first = self.run_hook("AskUserQuestion", CLAUDE_INPUT, records[:4], tool_use_id="t0")
        self.assertNotIn("thinking", first)  # reasoning before the visible text isn't the explanation

    def test_option_descriptions_do_not_count(self):
        records = [claude_user("fix it"), claude_call("t1", CLAUDE_INPUT)]
        self.assertIsNotNone(self.run_hook("AskUserQuestion", CLAUDE_INPUT, records))

    def test_prose_before_the_last_human_turn_does_not_count(self):
        records = [claude_text("Rebase or merge?"), claude_user("ask me properly"),
                   claude_text("Here is the question."), claude_call("t1", CLAUDE_INPUT)]
        self.assertIsNotNone(self.run_hook("AskUserQuestion", CLAUDE_INPUT, records))

    def test_tool_results_are_not_a_human_turn(self):
        records = [claude_user("fix it"), claude_text("Rebase is linear; merge is safe."), claude_tool_result(),
                   claude_text("Checked."), claude_call("t1", CLAUDE_INPUT)]
        self.assertIsNone(self.run_hook("AskUserQuestion", CLAUDE_INPUT, records))

    def test_codex_async_question_text_can_carry_the_explanation(self):
        tool_input = {"questions": [{"title": "Use the SSO profile (fast) or static keys (works offline)?",
                                     "options": ["SSO profile", "static keys"]}]}
        records = [codex_event("task_started"), codex_call("c1", "request_user_input_async")]
        self.assertIsNone(self.run_hook("request_user_input_async", tool_input, records, "c1"))

    def test_codex_turn_boundary_and_commentary(self):
        tool_input = {"questions": [{"question": "Scope?", "options": [
            {"label": "End-to-end (Recommended)", "description": "x"}, {"label": "CI only", "description": "y"}]}]}
        records = [codex_text("CI only was covered earlier."), codex_event("task_started"),
                   codex_text("End-to-end covers the updater too."), codex_call("c1", "request_user_input")]
        reason = self.run_hook("request_user_input", tool_input, records, "c1")
        self.assertIn('"CI only"', reason)

    def test_label_matching_tolerates_paraphrase_but_not_bare_letters(self):
        questions = [("Which?", ["Exclude from Android", "Hold", "A"])]
        self.assertEqual(hook.missing_labels(questions, "Excluding it from Android keeps the code."), ["A"])
        self.assertEqual(hook.missing_labels(questions, "Excluding it from Android, or A."), [])
        self.assertEqual(hook.missing_labels([("?", ["Reuse acyclic's App"])], "A new app costs setup."),
                         ["Reuse acyclic's App"])
        self.assertEqual(hook.missing_labels([("?", ["Fix first: pause work whenever a finding arrives, then resume."])], ""), [])
        self.assertEqual(hook.missing_labels([("May I?", ["Yes, enable briefly", "No, wrap up", "Approve as proposed"])], ""), [])

    def test_fails_open_when_it_cannot_judge(self):
        no_options = {"questions": [{"question": "Anything else?"}]}
        self.assertIsNone(self.run_hook("AskUserQuestion", no_options, [claude_user("hi")]))
        self.assertIsNone(self.run_hook("Bash", CLAUDE_INPUT, []))
        self.assertIsNone(self.run_hook("AskUserQuestion", CLAUDE_INPUT, [], write=False))
        unseen_call = [claude_user("fix it"), claude_text("nothing")]
        self.assertIsNone(self.run_hook("AskUserQuestion", CLAUDE_INPUT, unseen_call))
        # The interactive CLI writes the turn after the hook, so it is never judged.
        os.environ["CLAUDE_CODE_ENTRYPOINT"] = "cli"
        self.assertIsNone(self.run_hook("AskUserQuestion", CLAUDE_INPUT, [claude_user("x"), claude_call("t1", CLAUDE_INPUT)]))


if __name__ == "__main__":
    unittest.main()
