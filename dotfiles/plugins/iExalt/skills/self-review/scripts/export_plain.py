#!/usr/bin/env python3
"""Export a Markdown review draft to paste-ready plain text, then check the result.

Drops HTML comments and horizontal rules, and everything from the last appendix heading on; strips
headings, emphasis, strikethrough, blockquote and code markup; turns "- " bullets into "• "; keeps
link and image text and drops their targets. Bare URLs stay so the check catches them for
rewording. Exits 1 if no appendix heading is found (unless --no-appendix), or if the output still
holds a URL, markup, an em or en dash, or an open marker.
"""

from __future__ import annotations

import argparse
import re
import sys

TARGET = r"\((?:[^()\s]|\([^()\s]*\))+(?:\s+\"[^\"]*\")?\)"
LINK = re.compile(r"!?\[((?:[^\[\]]|\[[^\[\]]*\])+)\]" + TARGET)
HEADING = re.compile(r"^#{1,6}\s+")
EMPHASIS = [
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),
    (re.compile(r"(?<![\w*])__(.+?)__(?![\w*])"), r"\1"),
    (re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])"), r"\1"),
    (re.compile(r"(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])"), r"\1"),
    (re.compile(r"~~(.+?)~~"), r"\1"),
    (re.compile(r"`([^`]*)`"), r"\1"),
]
CHECKS = {
    "URL": re.compile(r"https?://|www\."),
    "markdown": re.compile(
        r"\*\*|(?<!\w)__|__(?!\w)|~~|`|^#{1,6}\s|^\s*[-*+]\s|^\s*>|^\s*\||\]\(|\]\[|<!--",
        re.MULTILINE,
    ),
    "em or en dash": re.compile("[–—]|\\s--\\s"),
    "open marker": re.compile(r"\[(TK|confirm)", re.IGNORECASE),
}


class NoAppendixError(ValueError):
    pass


def convert(markdown: str, appendix: str | None = "Evidence appendix") -> str:
    body = re.sub(r"<!--.*?-->", "", markdown, flags=re.DOTALL)
    if appendix is not None:
        heads = list(re.finditer(rf"^#{{1,6}}\s+{re.escape(appendix)}\b.*$", body, re.MULTILINE | re.IGNORECASE))
        if not heads:
            raise NoAppendixError(f'no "{appendix}" heading found')
        body = body[: heads[-1].start()]
    out = []
    for line in body.splitlines():
        if re.fullmatch(r"\s*(-{3,}|\*{3,}|_{3,})\s*", line):
            continue
        line = HEADING.sub("", line)
        line = re.sub(r"^\s*>\s?", "", line)
        line = LINK.sub(r"\1", line)
        for pattern, repl in EMPHASIS:
            line = pattern.sub(repl, line)
        line = re.sub(r"^(\s*)[-*+] ", r"\1• ", line)
        out.append(line.rstrip())
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip() + "\n"


def problems(text: str) -> list[str]:
    found = []
    for name, pattern in CHECKS.items():
        for n, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                found.append(f"line {n}: {name}: {line.strip()[:80]}")
    return found


def words(text: str) -> int:
    return len(re.findall(r"[^\s•]+", text))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("draft")
    ap.add_argument("output")
    ap.add_argument("--appendix", default="Evidence appendix", help="text the appendix heading starts with")
    ap.add_argument("--no-appendix", action="store_true", help="the draft has no appendix")
    args = ap.parse_args()
    with open(args.draft, encoding="utf-8") as f:
        try:
            text = convert(f.read(), None if args.no_appendix else args.appendix)
        except NoAppendixError as e:
            print(f"{args.draft}: {e}; pass --no-appendix if that is intended", file=sys.stderr)
            return 1
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{args.output}: about {words(text)} words (the review tool may count differently)")
    found = problems(text)
    for p in found:
        print(p, file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
