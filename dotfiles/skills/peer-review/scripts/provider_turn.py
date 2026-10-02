#!/usr/bin/env python3
"""Run persistent read-only review turns with Claude Code or Codex."""

from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REVIEWER_INSTRUCTIONS = """You are the downstream reviewer. Inspect and critique the
supplied artifact directly. Do not invoke peer-review, peer-review-loop, provider_turn.py,
or another review facilitator; do not delegate this review to other agents.
Keep the artifact unchanged. Return a self-contained review in your final response,
including findings with severity, evidence, impact, and proposed corrections, or
an explicit statement of no findings. Include verification limits. Do not return
only a plan-file reference or a promise to review later.

Review request:
"""


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


@contextmanager
def locked_state(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a", encoding="utf-8") as lock:
        lock_path.chmod(0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            state = load_state(path)
            yield state
            save_state(path, state)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def upsert_session(
    state: dict[str, Any],
    *,
    provider: str,
    session_id: str,
    topic: str,
    cwd: Path,
    artifact_kind: str,
) -> None:
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


def command_error(
    provider: str, result: subprocess.CompletedProcess[str]
) -> RuntimeError:
    details = result.stderr.strip() or result.stdout.strip() or "no output"
    return RuntimeError(
        f"{provider} review turn failed ({result.returncode}): {details}"
    )


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (normalized or "review")[:60]


def capture_metrics(raw: str, provider: str, metrics: dict[str, Any]) -> None:
    """Capture numeric provider counters with their scope; never retain bodies."""
    usage: dict[str, int | float] = {}
    compactions = None
    for line in ([raw] if provider == "claude" else raw.splitlines()):
        try:
            event = json.loads(line)
        except (ValueError, TypeError):
            continue
        if not isinstance(event, dict):
            continue
        if provider == "claude" or event.get("type") == "turn.completed":
            # Codex completion events are cumulative snapshots, not increments.
            usage = {}
            source = event.get("usage")
            if isinstance(source, dict):
                for key in ("input_tokens", "output_tokens", "cached_input_tokens",
                            "cache_read_input_tokens", "cache_creation_input_tokens"):
                    value = source.get(key)
                    if type(value) in (int, float) and math.isfinite(value) and value >= 0:
                        usage[key] = value
        # A positive observation is useful; absent events cannot establish zero.
        if event.get("type") in ("thread.compacted", "context.compacted"):
            compactions = (compactions or 0) + 1
    metrics.update(
        usage=usage or None,
        usage_scope="session_cumulative" if provider == "codex" else "call",
        usage_delta=None, usage_delta_scope=None, usage_baseline_turn_id=None,
        compaction_events_observed=compactions,
    )


def latest_session_turn(state: dict[str, Any], provider: str, session_id: str | None):
    if session_id is None:
        return None
    return next((t for t in reversed(state.get("turns", []))
                 if t.get("provider") == provider and t.get("session_id") == session_id), None)


def derive_usage_delta(turn: dict[str, Any], baseline, latest) -> None:
    """Derive snapshot intervals, rejecting known overlap and invalid baselines."""
    metrics = turn["provider_metrics"]
    usage = metrics.get("usage")
    if turn["status"] != "success" or not usage:
        return
    if metrics.get("usage_scope") == "call" or (
        turn["selection"] == "new" and latest is None
    ):
        metrics.update(usage_delta=dict(usage), usage_delta_scope="call")
        return
    if not baseline or latest != baseline or baseline.get("status") != "success":
        return
    previous = baseline.get("provider_metrics", {})
    old = previous.get("usage")
    if (previous.get("usage_scope") != "session_cumulative" or not old
            or baseline.get("finished_at", "~") > turn["started_at"]
            or old.keys() != usage.keys()
            or any(usage[k] < old[k] for k in usage)):
        return
    metrics.update(
        usage_delta={k: usage[k] - old[k] for k in usage},
        usage_delta_scope="recorded_interval",
        usage_baseline_turn_id=baseline["turn_id"],
    )


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
    model: str = "claude-opus-5-5",
    effort: str = "high",
    metrics: dict[str, Any] | None = None,
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
    command.extend(["--model", model, "--effort", effort])
    for add_dir in add_dirs:
        command.extend(["--add-dir", str(add_dir)])

    result = run_command(command, cwd=cwd, prompt=prompt, timeout=timeout)
    if metrics is not None:
        capture_metrics(result.stdout, "claude", metrics)
    if result.returncode != 0:
        raise command_error("claude", result)

    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError(  # noqa: TRY004 - a provider protocol failure, not a caller type error
            "Unexpected Claude Code JSON response: expected an object"
        )
    if payload.get("is_error"):
        raise RuntimeError(
            f"claude review turn failed: {payload.get('result', payload)}"
        )
    returned_session = payload.get("session_id", active_session)
    response = payload.get("result")
    if (
        not isinstance(returned_session, str)
        or not returned_session.strip()
        or not isinstance(response, str)
    ):
        raise RuntimeError(f"Unexpected Claude Code JSON response: {result.stdout}")
    if not response.strip():
        raise RuntimeError("Claude Code returned no final response")
    return returned_session, response.strip()


def extract_codex_session(events: str, fallback: str | None = None) -> str:
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
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
    model: str = "gpt-6-astra",
    effort: str = "medium",
    metrics: dict[str, Any] | None = None,
) -> tuple[str, str]:
    with tempfile.NamedTemporaryFile(
        prefix="peer-review-codex-", delete=False
    ) as handle:
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

        command.extend(["--model", model, "-c", f'model_reasoning_effort="{effort}"'])
        result = run_command(command, cwd=cwd, prompt=prompt, timeout=timeout)
        if metrics is not None:
            capture_metrics(result.stdout, "codex", metrics)
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


def summarize_turns(state: dict[str, Any], provider: str, session_id: str) -> dict[str, Any]:
    """Summarize recorded calls for an explicit session without inferring a campaign."""
    turns = [turn for turn in state.get("turns", [])
             if turn.get("provider") == provider and turn.get("session_id") == session_id]
    if not turns:
        raise ValueError("No recorded turns match this provider and session ID")

    def durations(records):
        known = []
        for record in records:
            value = record.get("duration_seconds")
            try:
                valid = type(value) in (int, float) and math.isfinite(value) and value >= 0
            except OverflowError:
                valid = False
            if valid:
                known.append(value)
        return {
            "calls": len(records),
            "recorded_seconds": round(sum(known), 3) if known else None,
            "timed_calls": len(known),
            "unknown_duration_calls": len(records) - len(known),
        }

    stages = {}
    statuses = {"success": 0, "failed": 0, "other": 0}
    intervals = []
    for turn in turns:
        stage = turn.get("stage")
        if not isinstance(stage, str) or not stage:
            stage = "unspecified"
        stages.setdefault(stage, []).append(turn)
        status = turn.get("status")
        statuses[status if status in ("success", "failed") else "other"] += 1
        try:
            start = datetime.fromisoformat(turn["started_at"])
            end = datetime.fromisoformat(turn["finished_at"])
            if start.utcoffset() is None or end.utcoffset() is None or end < start:
                continue
            intervals.append((start.astimezone(timezone.utc), end.astimezone(timezone.utc)))
        except (KeyError, TypeError, ValueError, OverflowError):
            continue

    first = min((start for start, _ in intervals), default=None)
    last = max((end for _, end in intervals), default=None)
    return {
        "provider": provider,
        "session_id": session_id,
        **durations(turns),
        "statuses": statuses,
        "stages": {stage: durations(records) for stage, records in sorted(stages.items())},
        "recorded_span": {
            "started_at": first.isoformat() if first is not None else None,
            "finished_at": last.isoformat() if last is not None else None,
            "elapsed_seconds": round((last - first).total_seconds(), 3) if intervals else None,
            "timed_calls": len(intervals),
            "unknown_timing_calls": len(turns) - len(intervals),
            "complete_for_recorded_calls": len(intervals) == len(turns),
        },
        "limits": [
            "Selection is a provider session, which may span multiple review campaigns.",
            "Call durations may overlap; their sum is not wall-clock elapsed time.",
            "Span covers valid recorded call intervals, not the full campaign or implementation time.",
            "Unrecorded attempts and failures without this session ID are not included.",
        ],
    }


def summarize_session(args: argparse.Namespace) -> int:
    summary = summarize_turns(load_state(args.state_file), args.provider, args.session_id)
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))
    return 0


def artifact_revision(cwd: Path) -> str:
    """Record a checkout hint; dirty work needs an explicit snapshot identifier."""
    try:
        options = {
            "cwd": cwd,
            "capture_output": True,
            "text": True,
            "timeout": 5,
            "env": {**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        }
        head = subprocess.run(["git", "rev-parse", "HEAD"], check=False, **options)
        status = subprocess.run(
            ["git", "status", "--porcelain"], check=False, **options
        )
        if head.returncode == 0 and status.returncode == 0:
            return head.stdout.strip() + ("+dirty" if status.stdout else "")
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


def record_dispositions(args: argparse.Namespace) -> int:
    counts = {
        key: getattr(args, key)
        for key in ("accepted", "rejected", "unresolved", "implemented", "verified")
    }
    if any(value < 0 for value in counts.values()):
        raise ValueError("Disposition counts must be nonnegative")
    if (
        counts["verified"] > counts["implemented"]
        or counts["implemented"] > counts["accepted"]
    ):
        raise ValueError("Require verified <= implemented <= accepted")
    with locked_state(args.state_file) as state:
        turn = next(
            (
                item
                for item in state.get("turns", [])
                if item["turn_id"] == args.turn_id
            ),
            None,
        )
        if turn is None:
            raise ValueError(f"Unknown turn ID: {args.turn_id}")
        if turn["status"] != "success":
            raise ValueError("Cannot record findings against a failed provider turn")
        turn["dispositions"] = counts
        turn["dispositions_updated_at"] = utc_now()
    print(json.dumps({"turn_id": args.turn_id, "dispositions": counts}, indent=2))
    return 0


def run_turn(args: argparse.Namespace) -> int:
    prompt = sys.stdin.read().strip()
    if not prompt:
        raise ValueError("Read an empty prompt from stdin")
    if args.session_id and not (args.reuse_reason and args.reuse_reason.strip()):
        raise ValueError(
            "Resuming requires --reuse-reason identifying the same review campaign"
        )
    if args.new and args.reuse_reason:
        raise ValueError("--reuse-reason only applies when resuming a session")
    if args.timeout <= 0:
        raise ValueError("--timeout must be positive")

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

    model = args.model or (
        "claude-opus-5-5" if args.provider == "claude" else "gpt-6-astra"
    )
    effort = args.effort or ("high" if args.provider == "claude" else "medium")
    turn = {
        "turn_id": str(uuid.uuid4()),
        "provider": args.provider,
        "session_id": args.session_id,
        "topic": args.topic,
        "cwd": str(cwd),
        "artifact_kind": args.artifact_kind,
        "artifact_revision": args.artifact_revision or artifact_revision(cwd),
        "model": model,
        "effort": effort,
        "stage": args.stage,
        "provider_metrics": {
            "usage": None,
            "usage_scope": "session_cumulative" if args.provider == "codex" else "call",
            "usage_delta": None, "usage_delta_scope": None,
            "usage_baseline_turn_id": None, "compaction_events_observed": None,
        },
        "started_at": utc_now(),
        "selection": "new" if args.new else "resume",
        "reuse_reason": args.reuse_reason,
        "status": "failed",
    }
    baseline = latest_session_turn(load_state(args.state_file), args.provider, args.session_id)
    started = time.monotonic()
    try:
        options = {
            "mise": require_mise(),
            "cwd": cwd,
            "prompt": REVIEWER_INSTRUCTIONS + prompt,
            "session_id": args.session_id,
            "new_session": args.new,
            "add_dirs": add_dirs,
            "timeout": args.timeout,
            "model": model,
            "effort": effort,
            "metrics": turn["provider_metrics"],
        }
        if args.provider == "claude":
            session_id, response = claude_turn(topic=args.topic, **options)
        else:
            session_id, response = codex_turn(**options)
        turn.update(session_id=session_id, status="success")
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        turn["error_type"] = type(error).__name__
        print(f"Failed review turn ID: {turn['turn_id']}", file=sys.stderr)
        raise
    finally:
        turn.update(
            finished_at=utc_now(), duration_seconds=round(time.monotonic() - started, 3)
        )
        with locked_state(args.state_file) as state:
            latest = latest_session_turn(state, args.provider, turn["session_id"])
            derive_usage_delta(turn, baseline, latest)
            if turn["status"] == "success":
                upsert_session(
                    state,
                    provider=args.provider,
                    session_id=session_id,
                    topic=args.topic,
                    cwd=cwd,
                    artifact_kind=args.artifact_kind,
                )
            state.setdefault("turns", []).append(turn)
    print(
        json.dumps(
            {
                "provider": args.provider,
                "session_id": session_id,
                "response": response,
                "turn_id": turn["turn_id"],
                "metrics": {key: turn[key] for key in (
                    "started_at", "finished_at", "duration_seconds",
                    "stage", "model", "effort", "provider_metrics"
                )},
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

    summary_parser = subparsers.add_parser(
        "summary", help="Summarize recorded timings for one provider session (read-only)."
    )
    summary_parser.add_argument("--provider", choices=("claude", "codex"), required=True)
    summary_parser.add_argument("--session-id", required=True)
    summary_parser.set_defaults(handler=summarize_session)

    turn_parser = subparsers.add_parser("turn", help="Run one provider review turn.")
    turn_parser.add_argument("--provider", choices=("claude", "codex"), required=True)
    turn_parser.add_argument(
        "--model",
        help="Reviewer model (default: Codex gpt-6-astra; Claude claude-opus-5-5).",
    )
    turn_parser.add_argument(
        "--effort",
        help="Reviewer reasoning effort (default: Codex medium; Claude high).",
    )
    selection = turn_parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--session-id", help="Resume this provider session.")
    selection.add_argument(
        "--new",
        action="store_true",
        help="Start a fresh session for an independently scoped review campaign.",
    )
    turn_parser.add_argument(
        "--reuse-reason",
        help="Why this is discussion or repair of the same review campaign.",
    )
    turn_parser.add_argument(
        "--artifact-revision",
        help="Commit or artifact snapshot ID (default: Git HEAD plus dirty marker, or unknown).",
    )
    turn_parser.add_argument(
        "--stage", choices=("discovery", "discussion", "verification", "unspecified"),
        default="unspecified", help="Review stage for latency accounting.",
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

    record_parser = subparsers.add_parser(
        "record", help="Record facilitator disposition counts for a completed turn."
    )
    record_parser.add_argument("--turn-id", required=True)
    for name in ("accepted", "rejected", "unresolved"):
        record_parser.add_argument(f"--{name}", type=int, required=True)
    for name in ("implemented", "verified"):
        record_parser.add_argument(f"--{name}", type=int, default=0)
    record_parser.set_defaults(handler=record_dispositions)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
