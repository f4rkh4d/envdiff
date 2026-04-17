"""Robust .env file parser.

Supports:
  - KEY=value
  - export KEY=value
  - KEY="double quoted" with escape sequences (\\n, \\t, \\", \\\\)
  - KEY='single quoted' (literal, no escapes)
  - # full-line comments
  - KEY=value # inline comments (only outside quotes)
  - blank lines
  - multi-line values inside quotes
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


class ParseError(ValueError):
    """Raised for malformed env content."""


@dataclass
class EnvEntry:
    key: str
    value: str
    line: int


_KEY_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
_KEY_REST = _KEY_START | set("0123456789")


def _is_valid_key(key: str) -> bool:
    if not key:
        return False
    if key[0] not in _KEY_START:
        return False
    return all(c in _KEY_REST for c in key[1:])


def _unescape_double(s: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            mapping = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "'": "'"}
            out.append(mapping.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _iter_logical_lines(text: str) -> Iterator[tuple[int, str]]:
    """Yield (starting_line_number, logical_line) handling quoted multiline values."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        start = i + 1
        line = lines[i]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            yield start, line
            i += 1
            continue
        # Find equals — if line has an opening quote after '=' that isn't closed,
        # keep appending following physical lines.
        eq = line.find("=")
        body = line[eq + 1 :] if eq != -1 else ""
        body_stripped = body.lstrip()
        quote = ""
        if body_stripped[:1] in ('"', "'"):
            quote = body_stripped[0]
        combined = line
        if quote:
            # Count unescaped closing quotes in rest after the opening quote.
            rest_index = body.index(quote) + 1
            rest = body[rest_index:]
            closed = _quote_closed(rest, quote)
            while not closed and i + 1 < len(lines):
                i += 1
                combined += "\n" + lines[i]
                rest += "\n" + lines[i]
                closed = _quote_closed(rest, quote)
        yield start, combined
        i += 1


def _quote_closed(s: str, quote: str) -> bool:
    """Return True if the closing quote appears in s (outside of escapes for ")."""
    i = 0
    while i < len(s):
        c = s[i]
        if quote == '"' and c == "\\" and i + 1 < len(s):
            i += 2
            continue
        if c == quote:
            return True
        i += 1
    return False


def _parse_value(raw: str) -> str:
    raw = raw.lstrip()
    if not raw:
        return ""
    if raw[0] == '"':
        # find closing unescaped "
        i = 1
        buf: list[str] = []
        while i < len(raw):
            c = raw[i]
            if c == "\\" and i + 1 < len(raw):
                buf.append(raw[i : i + 2])
                i += 2
                continue
            if c == '"':
                value = _unescape_double("".join(buf))
                # Ignore anything after closing quote except possibly a comment.
                tail = raw[i + 1 :].lstrip()
                if tail and not tail.startswith("#"):
                    # Be lenient — still accept.
                    pass
                return value
            buf.append(c)
            i += 1
        raise ParseError("Unterminated double-quoted value")
    if raw[0] == "'":
        i = 1
        buf = []
        while i < len(raw):
            c = raw[i]
            if c == "'":
                return "".join(buf)
            buf.append(c)
            i += 1
        raise ParseError("Unterminated single-quoted value")
    # unquoted — strip inline comment
    out: list[str] = []
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "#" and (i == 0 or raw[i - 1].isspace()):
            break
        out.append(c)
        i += 1
    return "".join(out).rstrip()


def parse_text(text: str) -> dict[str, str]:
    """Parse env text into an ordered dict of key -> value."""
    result: dict[str, str] = {}
    for lineno, logical in _iter_logical_lines(text):
        stripped = logical.strip()
        if not stripped or stripped.startswith("#"):
            continue
        working = logical.lstrip()
        if working.startswith("export ") or working.startswith("export\t"):
            working = working[len("export") :].lstrip()
        eq = working.find("=")
        if eq == -1:
            raise ParseError(f"Line {lineno}: missing '=' in: {logical!r}")
        key = working[:eq].strip()
        if not _is_valid_key(key):
            raise ParseError(f"Line {lineno}: invalid key {key!r}")
        value = _parse_value(working[eq + 1 :])
        result[key] = value
    return result


def parse_file(path: str | os.PathLike[str]) -> dict[str, str]:
    p = Path(path)
    return parse_text(p.read_text(encoding="utf-8"))
