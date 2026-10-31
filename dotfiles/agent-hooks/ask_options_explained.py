#!/usr/bin/env python3
"""PreToolUse hook: require options to be explained in prose before a question.

Standing rule: "Before posing any multiple-choice question to the user, always
explain each option in prose, including its rationale and tradeoffs."

Works for Claude Code (AskUserQuestion) and Codex (request_user_input,
request_user_input_async); both send the same PreToolUse stdin shape and accept
the same deny output. The hook denies the call when an option label is not
named in the agent's visible text since the user's last message, or in the
question text itself. Option descriptions don't count: the audit found that
one-line descriptions alone are what the rule is meant to prevent.

The hook fails open (allows) whenever it cannot judge: unknown tool, no
options, unreadable transcript, or a transcript that never shows the call.
The interactive Claude Code CLI (CLAUDE_CODE_ENTRYPOINT=cli) writes the
assistant message only after PreToolUse hooks finish, so the hook can't see
its prose and allows at once; SDK hosts such as Paseo write it first.
Stdlib only and Python 3.9 compatible, so it runs under /usr/bin/python3.
"""

import json
import os
import re
import sys
import time

QUESTION_TOOLS = {"AskUserQuestion", "request_user_input", "request_user_input_async"}
# SDK hosts append the call to the transcript shortly after the hook starts
# (measured at ~0.1 s under Paseo), so wait briefly for it.
TRANSCRIPT_WAIT_S = 1.5
POLL_S = 0.05

_RECOMMENDED = re.compile(r"\s*\((recommended|default)\)\s*$", re.IGNORECASE)
_MARKUP = re.compile(r"[*`_~]")
_SPACE = re.compile(r"\s+")
_TRANSLATE = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                            "–": "-", "—": "-", " ": " "})


def normalize(text):
    text = text.translate(_TRANSLATE).lower()
    text = _MARKUP.sub("", text)
    return _SPACE.sub(" ", text).strip()


def normalize_label(label):
    label = _RECOMMENDED.sub("", label)
    return normalize(label).strip(" .,:;!?\"'()[]")


def extract_questions(tool_name, tool_input):
    """Return [(question_text, [labels])] for a question tool call."""
    questions = []
    for q in tool_input.get("questions") or []:
        if not isinstance(q, dict):
            continue
        text = q.get("question") or q.get("title") or ""
        labels = []
        for opt in q.get("options") or []:
            label = opt.get("label") if isinstance(opt, dict) else opt
            if isinstance(label, str) and label.strip():
                labels.append(label)
        questions.append((text, labels))
    return questions


VISIBLE = ("text", "output_text", "input_text")


def _text_blocks(content, kinds=VISIBLE):
    if isinstance(content, str):
        return [content] if kinds == VISIBLE else []
    out = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") in kinds:
            out.append(block.get("text") or block.get("thinking") or "")
    return out


def _is_claude_human_turn(record):
    if record.get("type") != "user" or record.get("isMeta") or record.get("isSidechain"):
        return False
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    blocks = [b for b in content or [] if isinstance(b, dict)]
    return bool(blocks) and not any(b.get("type") == "tool_result" for b in blocks)


def _record_has_call(record, tool_use_id):
    message = record.get("message") or {}
    for block in message.get("content") or []:
        if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("id") == tool_use_id:
            return True
    payload = record.get("payload") or {}
    return payload.get("type") == "function_call" and payload.get("call_id") == tool_use_id


def visible_prose(records, tool_use_id, kinds=VISIBLE):
    """Agent text since the user's last message, up to the call.

    Returns None when the call isn't in the records (transcript not yet
    written, or a format this hook doesn't know). kinds=("thinking",)
    collects the agent's hidden reasoning written since its last visible
    text instead: the explanation it meant to show before this call.
    """
    end = None
    for i in range(len(records) - 1, -1, -1):
        if _record_has_call(records[i], tool_use_id):
            end = i
            break
    if end is None:
        return None
    prose = []
    for record in reversed(records[:end + 1]):
        if _is_claude_human_turn(record):
            break
        payload = record.get("payload") or {}
        if record.get("type") == "event_msg" and payload.get("type") in ("task_started", "user_message"):
            break
        if record.get("type") == "assistant":
            content = (record.get("message") or {}).get("content")
        elif payload.get("type") == "message" and payload.get("role") == "assistant":
            content = payload.get("content")
        else:
            continue
        if kinds != VISIBLE and _text_blocks(content):
            break
        prose.extend(reversed(_text_blocks(content, kinds)))
    return "\n".join(reversed(prose))


_TOKEN = re.compile(r"[a-z0-9][a-z0-9.+#/-]*[a-z0-9]|[a-z0-9]")
_STOPWORDS = frozenset(
    "the and for with but not now then than this that from into onto only just all any "
    "use keep make let via per its our your you yes are was has have as is to on in of or no".split())


def _content_words(text):
    """Content words, stemmed to five characters so "deleting" matches "delete"."""
    words = []
    for token in _TOKEN.findall(text):
        for part in token.split("-") if "-" in token else [token]:
            if (len(part) >= 3 or part.isdigit()) and part not in _STOPWORDS:
                words.append(part[:5])
    return words


# Options made only of these words (stop, defer, approve as proposed, change
# the plan, both) explain themselves once the alternatives are explained.
_GENERIC = frozenset(
    "approve approved proposed hold stop here wait pause later defer skip cancel none "
    "neither both either other revise change plan first leave it them yes".split())
# Option or chunk letters, such as "A" or "A-C" in "Approve A-C".
_LETTER_REF = re.compile(r"^[a-z0-9](-[a-z0-9])?$")


def is_explained(label, haystack, haystack_words):
    """True if the prose names the option, or the option needs no explanation.

    Self-explaining options pass: a label with its own gloss ("Name: what it
    does, at what cost"), a yes/no answer, and generic escape hatches such as
    "Hold" or "Approve as proposed". Agents paraphrase long labels ("A, a
    Start here section" for "A: Start here section"), so a label also counts
    as named when two thirds of its content words appear in the prose. Labels
    with no content words, such as "A", must appear verbatim.

    Calibrated on the audit's 51 post-rule Claude questions against a blind
    rater: 15 of 16 violations denied, and 10 of 25 denials were paraphrased
    explanations that don't name the label.
    """
    _, sep, gloss = normalize(label).partition(": ")
    if sep and len(gloss.split()) >= 6:
        return True  # the label carries its own explanation ("Name: what it does, at what cost")
    needle = normalize_label(label)
    if not needle or re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(needle), haystack):
        return True
    tokens = _TOKEN.findall(needle)
    if tokens[:1] in (["yes"], ["no"]):
        return True  # the question itself explains a yes/no option
    tokens = set(tokens)
    generic = {t for t in tokens if t in _GENERIC or t in _STOPWORDS}
    if generic and all(t in generic or _LETTER_REF.match(t) for t in tokens):
        return True
    words = set(_content_words(needle))
    if not words:
        return False
    return 3 * len(words & haystack_words) >= 2 * len(words)


def missing_by_question(questions, prose):
    """[(question text, [unexplained labels])] for questions with any."""
    out = []
    for text, labels in questions:
        haystack = normalize(prose + "\n" + text)
        haystack_words = set(_content_words(haystack))
        missing = [label for label in labels if not is_explained(label, haystack, haystack_words)]
        if missing:
            out.append((text, missing))
    return out


def missing_labels(questions, prose):
    missing = []
    for _, labels in missing_by_question(questions, prose):
        missing.extend(label for label in labels if label not in missing)
    return missing


def read_records(path):
    records = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    return records


def load_turn(path, tool_use_id, wait_s=TRANSCRIPT_WAIT_S):
    """(visible prose, thinking) for the call's turn, or (None, None) if the call never appears."""
    deadline = time.monotonic() + wait_s
    while True:
        try:
            records = read_records(path)
            prose = visible_prose(records, tool_use_id)
        except OSError:
            prose = None
        if prose is not None:
            return prose, visible_prose(records, tool_use_id, kinds=("thinking",))
        if time.monotonic() >= deadline:
            return None, None
        time.sleep(POLL_S)


def _short(text, limit=80):
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "\u2026"


def deny_reason(gaps, thinking):
    """Name each question's unexplained options, and say so when the explanation sits in thinking."""
    parts = []
    for text, labels in gaps:
        names = ", ".join('"%s"' % label for label in labels)
        parts.append('%s (question "%s")' % (names, _short(text)) if text else names)
    reason = (
        "Standing rule: before a multiple-choice question, explain each option in prose, with its "
        "rationale and tradeoffs, naming it by its label. Not yet explained: %s. " % "; ".join(parts))
    hidden = [label for _, labels in gaps for label in labels
              if thinking and not missing_labels([("", [label])], thinking)]
    if hidden:
        reason += ("Your thinking mentions %s, but thinking is hidden from the user; only text you write "
                   "outside thinking counts. " % ", ".join('"%s"' % label for label in hidden))
    return reason + ("Write the explanation as a visible message in this turn, then ask again. "
                     "Option descriptions in the dialog don't count.")


def decide(event, wait_s=TRANSCRIPT_WAIT_S):
    """Return a deny reason, or None to allow."""
    if event.get("tool_name") not in QUESTION_TOOLS:
        return None
    questions = extract_questions(event["tool_name"], event.get("tool_input") or {})
    if not any(labels for _, labels in questions):
        return None
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "cli":
        return None
    path, tool_use_id = event.get("transcript_path"), event.get("tool_use_id")
    if not path or not tool_use_id or not os.path.exists(path):
        return None
    prose, thinking = load_turn(path, tool_use_id, wait_s)
    if prose is None:
        return None
    gaps = missing_by_question(questions, prose)
    return deny_reason(gaps, thinking) if gaps else None


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    reason = decide(event)
    if reason:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
