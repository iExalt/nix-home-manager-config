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
    """Buffers the body, then writes body + cap note + footer within max_bytes in total.
    Footer lines (coverage) are kept in preference to body lines; each is clipped to 400 bytes."""

    def __init__(self, max_bytes: int = DEFAULT_MAX_BYTES, stream=None):
        self.max_bytes = max(400, int(max_bytes))
        self.stream = stream or sys.stdout
        self.body: List[bytes] = []
        self.used = 0
        self.truncated = 0          # body lines dropped
        self.footer: List[str] = []

    def line(self, text: str = "") -> bool:
        """Buffer one line; returns False once the body alone exceeds the cap (callers may stop early)."""
        if self.truncated:
            self.truncated += 1
            return False
        data = (text + "\n").encode("utf-8", "replace")
        # Keep room for the cap note and a typical footer so close() rarely has to drop shown lines.
        if self.used + len(data) > self.max_bytes - min(500, self.max_bytes // 3):
            self.truncated += 1
            return False
        self.body.append(data)
        self.used += len(data)
        return True

    def note(self, text: str) -> None:
        self.footer.append(text)

    def close(self, extra: Optional[str] = None) -> None:
        foot = b"".join(_clip_bytes("# " + f, 400) for f in self.footer + ([extra] if extra else []))
        foot = foot[: self.max_bytes // 2]
        body = list(self.body)
        def cap_note(n):
            return ("[output capped at %d bytes; %d more line(s) not shown; narrow the query or raise "
                    "--max-bytes]\n" % (self.max_bytes, n)).encode()
        room = self.max_bytes - len(foot)
        dropped = self.truncated
        size = sum(map(len, body))
        while body and size + (len(cap_note(dropped)) if dropped else 0) > room:
            size -= len(body.pop())
            dropped += 1
        out = b"".join(body) + (cap_note(dropped) if dropped else b"") + foot
        self.truncated = dropped
        w = getattr(self.stream, "buffer", None)
        if w is not None:
            self.stream.flush()
            w.write(out)
            w.flush()
        else:
            self.stream.write(out.decode("utf-8", "replace"))
            self.stream.flush()


def _clip_bytes(text: str, n: int) -> bytes:
    b = text.encode("utf-8", "replace")
    if len(b) > n - 1:
        b = b[: n - 4].decode("utf-8", "ignore").encode() + "…".encode()
    return b + b"\n"
