#!/usr/bin/env python3
"""PreToolUse hook for Claude Code and Codex: catch process probes that match their own shell.

A shell command runs inside a wrapper shell whose argv holds the command's text (Claude's
`zsh -c "<cmd>"`, Codex's `bash -lc`, ssh's remote `sh -c '<cmd>'`). A probe whose pattern
appears in that text can see the wrapper:

- Linux procps `pgrep`/`pkill` exclude only themselves. In a compound command the wrapper
  survives, so `while pgrep -f build.sh` never ends and `pkill -f build.sh` kills its own
  shell. A lone simple remote command is exec()'d without a wrapper and is fine.
- macOS `pgrep`/`pkill` exclude their ancestors unless given `-a`, so local `pgrep -f` is fine
  on macOS; on Linux the local wrapper matches too.
- `ps ... | grep PAT` lists the grep itself (and the wrapper) on every platform.

Decision: deny when the self-match makes the result wrong (`pkill -f`, or `pgrep -f` used as a
test or substitution); add non-blocking context for listings; stay silent otherwise. Heredoc
bodies are ignored, since they travel on stdin or into files. Any unexpected input or error
allows the call. Python 3.9 standard library only.
"""
import json
import re
import sys

_ARG = r"\s+(?:'([^']*)'|\"([^\"]*)\"|([^\s;|&)'\"]+))"
PGREP = re.compile(r"\b(pgrep|pkill)((?:\s+-[A-Za-z]+(?:\s+\d+)?)*)" + _ARG)
PS_GREP = re.compile(r"\bps\b[^|\n]*\|\s*(?:[^|\n]*\|\s*)*?\b(grep|rg|egrep)((?:\s+-[A-Za-z]+)*)" + _ARG)
GREP_V = re.compile(r"(?:grep|rg) -v\s+['\"]?(?:rg|grep)\b")
REMOTE = re.compile(r"\bssh\b|\bkubectl\b[^|;&\n]*\bexec\b|\bdocker\b[^|;&\n]*\bexec\b"
                    r"|\bpodman\b[^|;&\n]*\bexec\b|\badb\b[^|;&\n]*\bshell\b")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n.*?\n[ \t]*\2[ \t]*(?=\n|$)", re.S)
# Quoted strings these run as shell code: `sh -c`, eval, watch, and wrapper scripts like
# `run.sh '<cmd>'` that agents write to forward a command to another host.
RUNS_QUOTED = re.compile(r"(?:\b(?:ba|z|da|k)?sh\s+(?:-[A-Za-z]+\s+)*-[A-Za-z]*c|\beval|\bwatch(?:\s+-\S+)*"
                         r"|\S+\.sh(?:\s+[^\s'\"]+)*)\s*$")
COMPOUND = re.compile(r"[;&|\n`]|\$\(|\b(?:while|until|for|if)\b")
PREDICATE_BEFORE = re.compile(r"(?:\b(?:while|until|if)\s+(?:!\s*)?|!\s*|\bkill\b[^$;|&\n]*\$\(\s*|\bxargs\s+kill\b.*)$")
PREDICATE_AFTER = re.compile(r"^[^;|&\n]*?(?:&&|\|\|(?!\s*(?:true|:)\b)|\|\s*wc\b|\|\s*xargs\s+kill\b)")
SELF_FILTER = re.compile(r"^[^;&\n]*\|\s*(?:grep|rg) -v\s+['\"]?(?:pgrep|pkill|grep|rg|bash|zsh|sh)\b")
LINUX = sys.platform.startswith("linux")

FIX = ("Fix: use the bracket trick so the pattern no longer matches its own text "
       "(`pgrep -f '[b]uild.sh'`), or track the PID (`cmd & echo $! > pidfile`, then "
       "`kill -0 \"$(cat pidfile)\"`), or have the job write a done-marker file. "
       "Kill only PIDs you started; avoid `pkill -f` on shared hosts.")


def _matches(pattern, text):
    try:
        return re.search(pattern, text) is not None
    except re.error:
        return pattern in text


def _enclosing_quoted(text, at):
    """(start, body) of the quoted string that contains position `at`, or None."""
    quote, start = None, 0
    i = 0
    while i < at:
        ch = text[i]
        if quote is None and ch in "'\"":
            quote, start = ch, i + 1
        elif quote is not None and ch == quote and (quote == "'" or text[i - 1] != "\\"):
            quote = None
        i += 1
    if quote is None:
        return None
    end = text.find(quote, at)
    return start, text[start:end if end != -1 else len(text)]


def _has_wrapper(command, at):
    """Whether a shell holding `command`'s text is an ancestor of the probe at `at`."""
    quoted = _enclosing_quoted(command, at)
    if quoted is not None:
        start, body = quoted
        if REMOTE.search(command[:start]) or re.search(r"\S+\.sh(?:\s+[^\s'\"]+)*\s*$", command[:start - 1]):
            return COMPOUND.search(body) is not None
        if not RUNS_QUOTED.search(command[:start - 1]):
            return False  # quoted text handed to some program, not run by a shell
    elif REMOTE.search(command[:at]):
        return False  # unquoted remote argv: no remote wrapper holds the text
    return LINUX  # macOS excludes ancestors; Linux sees the local wrapper


def _is_predicate(command, m):
    before = command[max(0, m.start() - 40):m.start()]
    after = command[m.end():m.end() + 80]
    return PREDICATE_BEFORE.search(before) is not None or PREDICATE_AFTER.search(after) is not None


def findings(command):
    """Return [(decision, tool, pattern)] with decision 'deny' or 'warn'."""
    text = HEREDOC.sub("<<heredoc", command)
    out = []
    for m in PGREP.finditer(text):
        flags = m.group(2) or ""
        if not re.search(r"-[A-Za-z]*f", flags):
            continue  # without -f, pgrep matches process names, not command lines
        pattern = next(g for g in m.group(3, 4, 5) if g is not None)
        if not pattern or not _matches(pattern, text):
            continue
        remote = REMOTE.search(text[:m.start()]) is not None
        # macOS -a includes ancestors; on Linux -a only prints the full command line.
        quoted = _enclosing_quoted(text, m.start())
        literal = quoted is not None and not (REMOTE.search(text[:quoted[0]])
                                              or RUNS_QUOTED.search(text[:quoted[0] - 1]))
        if literal:
            continue  # e.g. a prompt or commit message that mentions pgrep
        ancestors_flag = not LINUX and not remote and re.search(r"-[A-Za-z]*a", flags) is not None
        if not (ancestors_flag or _has_wrapper(text, m.start())):
            continue
        if SELF_FILTER.search(text[m.end():]):
            continue  # `pgrep -af X | grep -v pgrep` drops the wrapper line itself
        probe = m.group(1) + flags
        if m.group(1) == "pkill" or _is_predicate(text, m):
            out.append(("deny", probe, pattern))
        else:
            out.append(("warn", probe, pattern))
    if not GREP_V.search(text):
        for m in PS_GREP.finditer(text):
            pattern = next(g for g in m.group(3, 4, 5) if g is not None)
            if pattern and _matches(pattern, text):
                out.append(("warn", m.group(1), pattern))
    return out


def decide(command):
    """Hook output dict, or None to allow silently."""
    hits = findings(command or "")
    deny = [h for h in hits if h[0] == "deny"]
    if deny:
        _, tool, pattern = deny[0]
        reason = ("process-probe-guard blocked this: `%s %s` matches the shell that runs this very "
                  "command, so a wait on it never ends and a kill hits your own session. %s"
                  % (tool, pattern, FIX))
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                       "permissionDecision": "deny",
                                       "permissionDecisionReason": reason}}
    if hits:
        _, tool, pattern = hits[0]
        note = ("process-probe-guard: `%s %s` also matches the shell running this command%s, so a "
                "match doesn't prove the target is running. Use a bracket pattern like `[%s]%s`."
                % (tool, pattern, " and the grep itself" if not tool.startswith("pgrep") else "", pattern[:1], pattern[1:]))
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": note}}
    return None


CMD_IN_JS = re.compile(r"""\bcmd\s*:\s*("(?:[^"\\]|\\.)*")""")


def commands_of(tool_input):
    """Shell command strings from a Claude/Codex tool_input (dict, argv list, or JS source)."""
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return [" ".join(str(part) for part in value)]
        for key in ("code", "input", "script"):
            if isinstance(tool_input.get(key), str):
                return commands_of(tool_input[key])
        return []
    if isinstance(tool_input, str):
        found = []
        for literal in CMD_IN_JS.findall(tool_input):
            try:
                found.append(json.loads(literal))
            except ValueError:
                pass
        return found
    return []


def main():
    payload = json.load(sys.stdin)
    for command in commands_of(payload.get("tool_input")):
        result = decide(command)
        if result:
            json.dump(result, sys.stdout)
            return


if __name__ == "__main__":
    try:
        main()
    except BaseException:  # fail open: never block a tool call on a hook bug
        pass
    sys.exit(0)
