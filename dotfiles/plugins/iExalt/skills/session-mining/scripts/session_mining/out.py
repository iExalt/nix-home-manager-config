"""Byte-capped output. Every subcommand writes through Out so no call can flood an agent's context:
the body stops at max_bytes with a truncation note, and the footer (coverage) is always printed."""
from __future__ import annotations

import sys
from typing import List, Optional

DEFAULT_MAX_BYTES = 8000


def clip(text: str, n: int) -> str:
    """One-line preview: whitespace collapsed, cut to n characters with an ellipsis."""
    t = " ".join((text or "").split())
    return t if len(t) <= n else t[: max(0, n - 1)] + "…"


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0
    return "%d B" % n


class Out:
    def __init__(self, max_bytes: int = DEFAULT_MAX_BYTES, stream=None):
        self.max_bytes = max(200, int(max_bytes))
        self.stream = stream or sys.stdout
        self.used = 0
        self.truncated = 0          # lines dropped after the cap
        self.footer: List[str] = []

    def line(self, text: str = "") -> bool:
        """Write one line; returns False once the cap is reached (callers may stop early)."""
        data = text + "\n"
        size = len(data.encode("utf-8", "replace"))
        if self.truncated or self.used + size > self.max_bytes:
            self.truncated += 1
            return False
        self.stream.write(data)
        self.used += size
        return True

    def note(self, text: str) -> None:
        self.footer.append(text)

    def close(self, extra: Optional[str] = None) -> None:
        if self.truncated:
            self.stream.write("[output capped at %d bytes; %d more line(s) not shown; narrow the query or "
                              "raise --max-bytes]\n" % (self.max_bytes, self.truncated))
        for f in self.footer + ([extra] if extra else []):
            self.stream.write("# " + f + "\n")
        self.stream.flush()
