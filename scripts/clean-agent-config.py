#!/usr/bin/env python3
"""Keep only reviewed, portable preferences in Git; never write the input file."""

import json
import sys
import tomllib


# feat(config): unknown keys stay local until explicitly reviewed here.
CODEX = {
    key: None for key in (
        "approval_policy", "approvals_reviewer", "developer_instructions",
        "model", "model_reasoning_effort", "model_reasoning_summary",
        "sandbox_mode", "service_tier",
    )
}
CODEX.update({
    "desktop": {"dock-icon-preference": None, "followUpQueueMode": None},
    "features": {"goals": None, "memories": None},
    "memories": {"generate_memories": None, "use_memories": None},
    "plugins": {"*": {"enabled": None}},
    "tui": {"status_line": None, "status_line_use_colors": None},
})
CLAUDE = {
    key: None for key in (
        "model", "effortLevel", "tui", "skipDangerousModePermissionPrompt",
        "theme", "switchModelsOnFlag",
    )
}
CLAUDE.update({
    "attribution": {"commit": None, "pr": None},
    "permissions": {"defaultMode": None},
    "statusLine": {"type": None, "command": None, "padding": None},
    "enabledPlugins": {"*": None},
    "sandbox": {"enabled": None},
    "modelSettings": {"*": {"effortLevel": None}},
})


def portable(value):
    # fix(privacy): conservatively omit strings containing any path separator.
    if isinstance(value, str):
        return not any(part in value for part in ("/", "\\", "$HOME", "${HOME}", "~"))
    if isinstance(value, list):
        return all(portable(item) for item in value)
    return isinstance(value, (bool, int, float)) or value is None


def project(data, policy):
    result = {}
    for key in sorted(data):
        if not portable(key) or (key not in policy and "*" not in policy):
            continue
        rule = policy.get(key, policy.get("*"))
        value = data[key]
        if isinstance(rule, dict):
            if isinstance(value, dict):
                selected = project(value, rule)
                if selected:
                    result[key] = selected
        elif portable(value):
            result[key] = value
    return result


def toml_value(value):
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def toml_dump(data, prefix=()):
    lines = []
    if prefix:
        lines.append("[" + ".".join(json.dumps(key) for key in prefix) + "]")
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{json.dumps(key)} = {toml_value(value)}")
    for key, value in data.items():
        if isinstance(value, dict):
            lines.extend(["", toml_dump(value, (*prefix, key))])
    return "\n".join(lines)


def clean(text, kind):
    if kind == "codex":
        return toml_dump(project(tomllib.loads(text), CODEX)) + "\n"
    if kind == "claude":
        return json.dumps(project(json.loads(text), CLAUDE), indent=2, ensure_ascii=False) + "\n"
    raise ValueError("expected codex or claude")


if __name__ == "__main__":
    try:
        output = clean(sys.stdin.read(), sys.argv[1])
    except Exception:
        # fix(privacy): do not echo configuration contents on parse failures.
        sys.exit("Agent config clean filter failed; check syntax and filter policy.")
    sys.stdout.write(output)
