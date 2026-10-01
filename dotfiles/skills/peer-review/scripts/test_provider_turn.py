"""Offline regression tests; providers and session state are isolated."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import provider_turn as helper


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cwd = Path(self.directory.name)
        self.state = self.cwd / "sessions.json"

    def args(self, *extra):
        return helper.build_parser().parse_args(
            [
                "--state-file",
                str(self.state),
                "turn",
                "--provider",
                "claude",
                "--topic",
                "repo: feature",
                "--cwd",
                str(self.cwd),
                "--artifact-revision",
                "snapshot-1",
                *extra,
            ]
        )

    def run_turn(self, args):
        output = io.StringIO()
        with (
            patch("sys.stdin", io.StringIO("Inspect the raw artifact.")),
            patch.object(helper, "require_mise", return_value="mise"),
            contextlib.redirect_stdout(output),
        ):
            helper.run_turn(args)
        return json.loads(output.getvalue())

    def provider_options(self, new=True):
        return {
            "mise": "mise",
            "cwd": self.cwd,
            "prompt": "review",
            "session_id": None if new else "existing",
            "new_session": new,
            "add_dirs": [self.cwd],
            "timeout": 20,
        }

    def test_provider_commands_new_resume_defaults_and_overrides(self):
        for provider in ("claude", "codex"):
            for new in (True, False):
                for override in (False, True):
                    with self.subTest(provider=provider, new=new, override=override):
                        captured = []

                        def run(
                            command, captured=captured, provider=provider, **kwargs
                        ):
                            captured.append(command)
                            self.assertEqual(kwargs["prompt"], "review")
                            if provider == "codex":
                                Path(command[command.index("-o") + 1]).write_text(
                                    "No findings."
                                )
                                stdout = json.dumps(
                                    {"type": "thread.started", "thread_id": "returned"}
                                )
                            else:
                                stdout = json.dumps(
                                    {"session_id": "returned", "result": "No findings."}
                                )
                            return subprocess.CompletedProcess(command, 0, stdout, "")

                        options = self.provider_options(new)
                        if override:
                            options.update(model="custom-model", effort="low")
                        with patch.object(helper, "run_command", side_effect=run):
                            result = (
                                helper.claude_turn(topic="feature", **options)
                                if provider == "claude"
                                else helper.codex_turn(**options)
                            )
                        self.assertEqual(result, ("returned", "No findings."))
                        command = captured[0]
                        expected_model = (
                            "custom-model"
                            if override
                            else (
                                "claude-opus-5-5"
                                if provider == "claude"
                                else "gpt-6-astra"
                            )
                        )
                        self.assertEqual(
                            command[command.index("--model") + 1], expected_model
                        )
                        self.assertEqual(
                            command[command.index("--add-dir") + 1], str(self.cwd)
                        )
                        if provider == "claude":
                            self.assertEqual(
                                command[command.index("--permission-mode") + 1], "plan"
                            )
                            self.assertEqual(
                                command[command.index("--effort") + 1],
                                "low" if override else "high",
                            )
                            self.assertIn(
                                "--session-id" if new else "--resume", command
                            )
                        else:
                            self.assertEqual(
                                command[command.index("--sandbox") + 1], "read-only"
                            )
                            self.assertEqual(
                                command[command.index("--ask-for-approval") + 1],
                                "never",
                            )
                            self.assertIn(
                                'model_reasoning_effort="low"'
                                if override
                                else 'model_reasoning_effort="medium"',
                                command,
                            )
                            self.assertEqual("resume" in command, not new)
                            self.assertFalse(
                                Path(command[command.index("-o") + 1]).exists()
                            )

    def test_claude_rejects_blank_malformed_and_error_responses(self):
        for payload in (
            {"result": ""},
            {"result": " \n\t"},
            {"result": None},
            [],
            {"result": "No findings", "is_error": True},
            {"result": "No findings", "session_id": 42},
        ):
            with (
                self.subTest(payload=payload),
                patch.object(
                    helper,
                    "run_command",
                    return_value=subprocess.CompletedProcess(
                        [], 0, json.dumps(payload), ""
                    ),
                ),
                self.assertRaises(RuntimeError),
            ):
                helper.claude_turn(topic="feature", **self.provider_options())
        with (
            patch.object(
                helper,
                "run_command",
                return_value=subprocess.CompletedProcess([], 0, "{", ""),
            ),
            self.assertRaises(ValueError),
        ):
            helper.claude_turn(topic="feature", **self.provider_options())

    def test_codex_blank_failure_and_timeout_remove_output(self):
        for failure in ("blank", "exit", "timeout"):
            with self.subTest(failure=failure):
                outputs = []

                def run(command, outputs=outputs, failure=failure, **kwargs):
                    outputs.append(Path(command[command.index("-o") + 1]))
                    if failure == "timeout":
                        raise subprocess.TimeoutExpired(command, 20)
                    return subprocess.CompletedProcess(
                        command,
                        1 if failure == "exit" else 0,
                        '{"type":"thread.started","thread_id":"returned"}',
                        "provider failed",
                    )

                with (
                    patch.object(helper, "run_command", side_effect=run),
                    self.assertRaises((RuntimeError, subprocess.TimeoutExpired)),
                ):
                    helper.codex_turn(**self.provider_options())
                self.assertFalse(outputs[0].exists())

    def test_success_records_metadata_and_injects_role_for_both_providers(self):
        for provider in ("claude", "codex"):
            for new in (True, False):
                args = (
                    self.args("--new")
                    if new
                    else self.args(
                        "--session-id",
                        "existing",
                        "--reuse-reason",
                        "Same PR remediation",
                    )
                )
                args.provider = provider
                with patch.object(
                    helper,
                    provider + "_turn",
                    return_value=("existing", "No findings."),
                ) as call:
                    result = self.run_turn(args)
                self.assertTrue(
                    call.call_args.kwargs["prompt"].startswith(
                        helper.REVIEWER_INSTRUCTIONS
                    )
                )
                self.assertTrue(
                    call.call_args.kwargs["prompt"].endswith(
                        "Inspect the raw artifact."
                    )
                )
                state = helper.load_state(self.state)
                turn = state["turns"][-1]
                self.assertEqual(turn["turn_id"], result["turn_id"])
                self.assertEqual(turn["artifact_revision"], "snapshot-1")
                self.assertEqual(turn["status"], "success")
                self.assertGreaterEqual(turn["duration_seconds"], 0)
                self.assertNotIn("dispositions", turn)
                self.assertNotIn("response", turn)
                self.assertNotIn("prompt", turn)
        self.assertEqual(len(state["sessions"]), 2)
        self.assertEqual(len(state["turns"]), 4)
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o600)

    def test_failure_record_does_not_register_session_or_store_error_body(self):
        for error in (
            RuntimeError("sensitive provider error"),
            subprocess.TimeoutExpired("provider", 20),
        ):
            with (
                patch.object(helper, "claude_turn", side_effect=error),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(type(error)),
            ):
                self.run_turn(self.args("--new"))
        state = helper.load_state(self.state)
        self.assertEqual(state["sessions"], [])
        self.assertEqual([t["status"] for t in state["turns"]], ["failed", "failed"])
        self.assertNotIn("sensitive provider error", self.state.read_text())

    def test_resume_requires_reason_before_provider_execution(self):
        with patch.object(helper, "claude_turn") as call:
            with self.assertRaisesRegex(ValueError, "reuse-reason"):
                self.run_turn(self.args("--session-id", "existing"))
            call.assert_not_called()
        self.assertFalse(self.state.exists())

    def test_record_updates_counts_without_inventing_verification(self):
        with patch.object(helper, "claude_turn", return_value=("existing", "Findings")):
            result = self.run_turn(self.args("--new"))
        base = [
            "--state-file",
            str(self.state),
            "record",
            "--turn-id",
            result["turn_id"],
            "--accepted",
            "2",
            "--rejected",
            "1",
            "--unresolved",
            "0",
        ]
        for extra in ([], ["--implemented", "2", "--verified", "1"]):
            with contextlib.redirect_stdout(io.StringIO()):
                helper.record_dispositions(
                    helper.build_parser().parse_args(base + extra)
                )
        turn = helper.load_state(self.state)["turns"][0]
        self.assertEqual(
            turn["dispositions"],
            {
                "accepted": 2,
                "rejected": 1,
                "unresolved": 0,
                "implemented": 2,
                "verified": 1,
            },
        )
        original = self.state.read_text()
        for extra in (
            ["--verified", "3"],
            ["--accepted", "-1"],
            ["--turn-id", "missing"],
        ):
            with self.assertRaises(ValueError):
                helper.record_dispositions(
                    helper.build_parser().parse_args(base + extra)
                )
            self.assertEqual(self.state.read_text(), original)

    def test_legacy_registry_and_concurrent_process_updates(self):
        helper.save_state(
            self.state,
            {
                "version": 1,
                "sessions": [
                    {
                        "provider": "claude",
                        "session_id": "old",
                        "topic": "legacy",
                        "cwd": str(self.cwd),
                        "artifact_kind": "code",
                        "created_at": "then",
                        "last_used_at": "then",
                    }
                ],
            },
        )
        script = """
import sys, time
from pathlib import Path
import provider_turn as h
for i in range(8):
    with h.locked_state(Path(sys.argv[1])) as state:
        time.sleep(0.002)
        sid = sys.argv[2] + '-' + str(i)
        h.upsert_session(state, provider='codex', session_id=sid, topic='feature',
                         cwd=Path.cwd(), artifact_kind='code')
        state.setdefault('turns', []).append({'turn_id': sid})
"""
        processes = [
            subprocess.Popen(
                [sys.executable, "-B", "-c", script, str(self.state), str(i)],
                cwd=Path(helper.__file__).parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            for i in range(6)
        ]
        try:
            for process in processes:
                stdout, stderr = process.communicate(timeout=20)
                self.assertEqual(process.returncode, 0, (stdout, stderr))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
        state = helper.load_state(self.state)
        self.assertEqual(len(state["sessions"]), 49)
        self.assertEqual(len({t["turn_id"] for t in state["turns"]}), 48)
        self.assertEqual(state["sessions"][0]["topic"], "legacy")

    def test_checkout_revision_distinguishes_dirty_tree(self):
        with patch.object(
            helper.subprocess,
            "run",
            side_effect=[
                subprocess.CompletedProcess([], 0, "abc123\n", ""),
                subprocess.CompletedProcess([], 0, " M plan.md\n", ""),
            ],
        ):
            self.assertEqual(helper.artifact_revision(self.cwd), "abc123+dirty")


if __name__ == "__main__":
    unittest.main()
