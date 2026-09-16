"""Offline ACT schema inspection. Not a production adapter or fire classifier."""
from dataclasses import dataclass
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class ActItem:
    """Raw source fields; dates and coordinates deliberately remain uninterpreted."""

    fields: tuple[tuple[str, str], ...]


class InvalidFeed(ValueError):
    """The input cannot be safely inspected as an ACT RSS envelope."""


def inspect_feed(payload: bytes, *, max_bytes=1_048_576, max_items=10_000):
    """Return immutable raw items; never turn an invalid feed into empty success.

    UTF-8 only. DTDs, entities, nested field markup, duplicate fields, deep trees
    and unexpected envelopes are rejected. No network, file writes or date guesses.
    """
    for limit in (max_bytes, max_items):
        if type(limit) is not int or limit <= 0:
            raise ValueError("Limits must be positive integers")
    if not isinstance(payload, bytes):
        raise TypeError("Payload must be bytes")
    if len(payload) > max_bytes:
        raise InvalidFeed("Feed exceeds byte limit")
    try:
        source = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise InvalidFeed("Feed must be UTF-8") from None
    # Reject UTF-16/32 and entity declarations before invoking the XML parser.
    if "\x00" in source or "<!DOCTYPE" in source.upper() or "<!ENTITY" in source.upper():
        raise InvalidFeed("Unsupported XML declarations")
    parser = ET.XMLPullParser(events=("start", "end"))
    depth = nodes = 0
    root = None
    try:
        for offset in range(0, len(source), 4096):
            parser.feed(source[offset:offset + 4096])
            for event, element in parser.read_events():
                if event == "start":
                    depth += 1
                    nodes += 1
                    if root is None:
                        root = element
                    if depth > 4 or nodes > 32 + max_items * 32:
                        raise InvalidFeed("XML structure exceeds limits")
                else:
                    depth -= 1
        parser.close()
    except (ET.ParseError, LookupError, ValueError) as exc:
        if isinstance(exc, InvalidFeed):
            raise
        raise InvalidFeed("Malformed XML") from None
    if root is None or root.tag != "rss" or root.get("version") != "2.0":
        raise InvalidFeed("Expected RSS 2.0")
    if len(root) != 1 or root[0].tag != "channel":
        raise InvalidFeed("Expected one channel")
    result = []
    for child in root[0]:
        if child.tag != "item":
            if len(child):
                raise InvalidFeed("Unexpected channel structure")
            continue
        if len(result) >= max_items:
            raise InvalidFeed("Too many items")
        fields = []
        seen = set()
        for field in child:
            if field.tag in seen or len(field):
                raise InvalidFeed("Duplicate or nested item field")
            seen.add(field.tag)
            fields.append((field.tag, field.text or ""))
        if not fields:
            raise InvalidFeed("Empty item")
        result.append(ActItem(tuple(fields)))
    return tuple(result)
