#!/usr/bin/env python3
"""Run persistent read-only review turns with Claude Code or Codex."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_state_file() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "state" / "peer-review" / "sessions.json"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "sessions": []}
    with path.open(encoding="utf-8") as handle:
        state = json.load(handle)
    if state.get("version") != 1 or not isinstance(state.get("sessions"), list):
        raise ValueError(f"Unsupported session registry format: {path}")
    return state


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.chmod(0o600)
    temporary.replace(path)


def upsert_session(
    path: Path,
    *,
    provider: str,
    session_id: str,
    topic: str,
    cwd: Path,
    artifact_kind: str,
) -> None:
    state = load_state(path)
    now = utc_now()
    for session in state["sessions"]:
        if session["provider"] == provider and session["session_id"] == session_id:
            session.update(
                {
                    "topic": topic,
                    "cwd": str(cwd),
                    "artifact_kind": artifact_kind,
                    "last_used_at": now,
                }
            )
            break
    else:
        state["sessions"].append(
            {
                "provider": provider,
                "session_id": session_id,
                "topic": topic,
                "cwd": str(cwd),
                "artifact_kind": artifact_kind,
                "created_at": now,
                "last_used_at": now,
            }
        )
    save_state(path, state)


def require_mise() -> str:
    mise = shutil.which("mise")
    if mise is None:
        raise RuntimeError("mise is required but was not found on PATH")
    return mise


def run_command(
    command: list[str], *, cwd: Path, prompt: str, timeout: int
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def command_error(provider: str, result: subprocess.CompletedProcess[str]) -> RuntimeError:
    details = result.stderr.strip() or result.stdout.strip() or "no output"
    return RuntimeError(f"{provider} review turn failed ({result.returncode}): {details}")


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (normalized or "review")[:60]


def claude_turn(
    *,
    mise: str,
    cwd: Path,
    prompt: str,
    session_id: str | None,
    new_session: bool,
    topic: str,
    add_dirs: list[Path],
    timeout: int,
) -> tuple[str, str]:
    if new_session:
        active_session = str(uuid.uuid4())
        command = [
            mise,
            "exec",
            "--",
            "claude",
            "-p",
            "--output-format",
            "json",
            "--permission-mode",
            "plan",
            "--session-id",
            active_session,
            "--name",
            f"peer-review-{slug(topic)}",
        ]
    else:
        active_session = session_id or ""
        command = [
            mise,
            "exec",
            "--",
            "claude",
            "-p",
            "--output-format",
            "json",
            "--permission-mode",
            "plan",
            "--resume",
            active_session,
        ]
    for add_dir in add_dirs:
        command.extend(["--add-dir", str(add_dir)])

    result = run_command(command, cwd=cwd, prompt=prompt, timeout=timeout)
    if result.returncode != 0:
        raise command_error("claude", result)

    payload = json.loads(result.stdout)
    if payload.get("is_error"):
        raise RuntimeError(f"claude review turn failed: {payload.get('result', payload)}")
    returned_session = payload.get("session_id", active_session)
    response = payload.get("result")
    if not returned_session or not isinstance(response, str):
        raise RuntimeError(f"Unexpected Claude Code JSON response: {result.stdout}")
    return returned_session, response


def extract_codex_session(events: str, fallback: str | None = None) -> str:
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started" and event.get("thread_id"):
            return str(event["thread_id"])
        if event.get("thread_id"):
            return str(event["thread_id"])
    if fallback:
        return fallback
    raise RuntimeError(f"Codex did not return a session ID: {events}")


def codex_turn(
    *,
    mise: str,
    cwd: Path,
    prompt: str,
    session_id: str | None,
    new_session: bool,
    add_dirs: list[Path],
    timeout: int,
) -> tuple[str, str]:
    with tempfile.NamedTemporaryFile(prefix="peer-review-codex-", delete=False) as handle:
        output_path = Path(handle.name)
    try:
        command = [
            mise,
            "exec",
            "--",
            "codex",
            "--ask-for-approval",
            "never",
            "--sandbox",
            "read-only",
        ]
        for add_dir in add_dirs:
            command.extend(["--add-dir", str(add_dir)])
        if new_session:
            command.extend(
                [
                    "exec",
                    "-C",
                    str(cwd),
                    "--json",
                    "-o",
                    str(output_path),
                    "-",
                ]
            )
        else:
            command.extend(
                [
                    "exec",
                    "resume",
                    "--json",
                    "-o",
                    str(output_path),
                    session_id or "",
                    "-",
                ]
            )

        result = run_command(command, cwd=cwd, prompt=prompt, timeout=timeout)
        if result.returncode != 0:
            raise command_error("codex", result)
        active_session = extract_codex_session(result.stdout, fallback=session_id)
        response = output_path.read_text(encoding="utf-8").strip()
        if not response:
            raise RuntimeError(f"Codex returned no final response: {result.stdout}")
        return active_session, response
    finally:
        output_path.unlink(missing_ok=True)


def list_sessions(args: argparse.Namespace) -> int:
    state = load_state(args.state_file)
    sessions = state["sessions"]
    if args.provider:
        sessions = [item for item in sessions if item["provider"] == args.provider]
    if args.cwd:
        requested_cwd = str(args.cwd.resolve())
        sessions = [item for item in sessions if item["cwd"] == requested_cwd]
    sessions = sorted(sessions, key=lambda item: item["last_used_at"], reverse=True)
    print(json.dumps(sessions, indent=2, sort_keys=True))
    return 0


def run_turn(args: argparse.Namespace) -> int:
    prompt = sys.stdin.read().strip()
    if not prompt:
        raise ValueError("Read an empty prompt from stdin")

    cwd = args.cwd.resolve()
    if not cwd.is_dir():
        raise ValueError(f"Workspace does not exist or is not a directory: {cwd}")
    add_dirs = [path.resolve() for path in args.add_dir]
    invalid_dirs = [path for path in add_dirs if not path.is_dir()]
    if invalid_dirs:
        raise ValueError(
            "Additional read path does not exist or is not a directory: "
            + ", ".join(str(path) for path in invalid_dirs)
        )

    mise = require_mise()
    if args.provider == "claude":
        session_id, response = claude_turn(
            mise=mise,
            cwd=cwd,
            prompt=prompt,
            session_id=args.session_id,
            new_session=args.new,
            topic=args.topic,
            add_dirs=add_dirs,
            timeout=args.timeout,
        )
    else:
        session_id, response = codex_turn(
            mise=mise,
            cwd=cwd,
            prompt=prompt,
            session_id=args.session_id,
            new_session=args.new,
            add_dirs=add_dirs,
            timeout=args.timeout,
        )

    upsert_session(
        args.state_file,
        provider=args.provider,
        session_id=session_id,
        topic=args.topic,
        cwd=cwd,
        artifact_kind=args.artifact_kind,
    )
    print(
        json.dumps(
            {
                "provider": args.provider,
                "session_id": session_id,
                "response": response,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run and track persistent peer-review provider sessions."
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=default_state_file(),
        help="Session registry path.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List reusable review sessions.")
    list_parser.add_argument("--provider", choices=("claude", "codex"))
    list_parser.add_argument("--cwd", type=Path)
    list_parser.set_defaults(handler=list_sessions)

    turn_parser = subparsers.add_parser("turn", help="Run one provider review turn.")
    turn_parser.add_argument("--provider", choices=("claude", "codex"), required=True)
    selection = turn_parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--session-id", help="Resume this provider session.")
    selection.add_argument(
        "--new",
        action="store_true",
        help="Start a new session because the topic is completely different.",
    )
    turn_parser.add_argument("--topic", required=True)
    turn_parser.add_argument(
        "--artifact-kind",
        choices=("plan", "code", "pr", "other"),
        default="other",
    )
    turn_parser.add_argument("--cwd", type=Path, required=True)
    turn_parser.add_argument(
        "--add-dir",
        action="append",
        type=Path,
        default=[],
        help="Additional directory the review provider may read; repeat as needed.",
    )
    turn_parser.add_argument("--timeout", type=int, default=1800)
    turn_parser.set_defaults(handler=run_turn)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
